"""
Business Planning Agent - 공통 모듈 사용 버전
기존 설정 파일들을 shared_modules로 대체
"""

# 공통 모듈에서 필요한 것들 import
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared_modules import (
    get_config, 
    get_llm, 
    get_vectorstore, 
    get_retriever,
    get_db_session,
    get_session_context
)

from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import RetrievalQA
from fastapi.middleware.cors import CORSMiddleware
from config.prompts_config import PROMPT_META
from fastapi import FastAPI, Body
from pydantic import BaseModel
from langchain_core.output_parsers import StrOutputParser

# 로깅 설정
from shared_modules.logging_utils import setup_logging
logger = setup_logging("business_planning", log_file="logs/business_planning.log")

# 설정 로드
config = get_config()

# API 호출 카운트 (로드 밸런싱용)
CALL_COUNT = 0

def get_llm_with_balancing():
    """로드 밸런싱된 LLM 반환"""
    global CALL_COUNT
    CALL_COUNT += 1

    if CALL_COUNT <= 10:
        return get_llm("openai")
    elif CALL_COUNT <= 20:
        return get_llm("gemini")
    else:
        CALL_COUNT = 1
        return get_llm("openai")

# FastAPI 초기화
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# persona
persona = "common"    

# 프롬프트 파일 로드 함수
def load_prompt_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

# 관련 토픽 추론
TOPIC_CLASSIFY_SYSTEM_PROMPT = """
너는 고객 질문을 분석해서 관련된 사업기획 topic을 모두 골라주는 역할이야.
소괄호 안은 topic에 대한 부가 설명이야. 부가 설명을 참고해서

아래의 토픽 중에서 질문과 관련된 키워드를 **복수 개까지** 골라줘.

콤마(,)로 구분된 키만 출력하고, 설명은 하지마.

가능한 토픽:
1. startup_preparation(창업 준비, 체크리스트)
2. idea_validation(아이디어 검증, 시장성 분석, 타겟 분석)
3. business_model(린캔버스, 수익 구조)
4. market_research(시장/경쟁 분석, 시장규모)
5. mvp_development(MVP 기획, 초기 제품 설계)
6. funding_strategy(투자유치, 정부지원, 자금 조달)
7. business_registration(사업자등록, 면허, 신고 절차)
8. financial_planning(예산, 매출, 세무)
9. growth_strategy(사업 확장, 스케일업)
10. risk_management(리스크 관리, 위기 대응)

**출력 예시**: startup_preparation, idea_validation
"""

def classify_topics(user_input: str) -> list:
    classify_prompt = ChatPromptTemplate.from_messages([
        ("system", TOPIC_CLASSIFY_SYSTEM_PROMPT),
        ("human", f"사용자 질문: {user_input}")
    ])
    
    llm = get_llm("openai")  # 분류에는 OpenAI 사용
    chain = classify_prompt | llm | StrOutputParser()
    result = chain.invoke({"input": user_input}).strip()
    return [t.strip() for t in result.split(",") if t.strip() in PROMPT_META]

# 에이전트 프롬프트 구성 함수 (여러 프롬프트 병합)
def build_agent_prompt(topics: list, user_input: str, persona: str, history: str):
    merged_prompts = []
    for topic in topics:
        if topic in PROMPT_META:
            file_path = PROMPT_META[topic]["file"]
            prompt_text = load_prompt_text(file_path)
            merged_prompts.append(prompt_text)

    role_descriptions = [PROMPT_META[topic]["role"] for topic in topics]
    
    if persona == "common":
        system_context = f"당신은 1인 창업 전문 컨설턴트입니다. {', '.join(role_descriptions)}"
    else:
        system_context = f"당신은 {persona} 전문 1인 창업 컨설턴트입니다. {', '.join(role_descriptions)}"

    template = f"""{system_context}

다음 지침을 따라 답변하세요:
{chr(10).join(merged_prompts)}

최근 대화:
{history}

참고 문서:
{{context}}

사용자 질문: "{user_input}"

위 지침에 따라 사용자의 질문에 대해 구체적이고 실용적인 답변을 제공하세요. 지침 내용을 그대로 반복하지 말고, 실제 답변만 작성하세요."""

    from langchain.prompts import PromptTemplate
    return PromptTemplate(
        input_variables=["context"],
        template=template
    )

def run_business_planning_with_rag(user_input: str, use_retriever: bool = True, persona: str = "common"):
    selected_llm = get_llm_with_balancing()
    topics = classify_topics(user_input)

    # 히스토리 불러오기
    from shared_modules.queries import get_recent_messages 
    conversation_id = 4
    history_rows = get_recent_messages(conversation_id)

    # 텍스트로 변환
    history_text = ""
    for msg in reversed(history_rows):
        role = "User" if msg["sender_type"] == "USER" else "Agent"
        history_text += f"{role}: {msg['content']}\n"

    # 프롬프트 생성
    prompt = build_agent_prompt(topics, user_input, persona, history_text)

    # 필터 설정
    if topics:
        topic_filter = {
            "$and": [
                {"category": "business_planning"},
                {"topic": {"$in": topics}}
            ]
        }
    else:
        topic_filter = {}

    # 벡터 스토어 및 검색기 가져오기
    vectorstore = get_vectorstore("global-documents")
    topic_retriever = vectorstore.as_retriever(
        search_kwargs={"k": 5, "filter": topic_filter}
    ) if vectorstore else None

    # RetrievalQA 체인 생성
    qa_chain = RetrievalQA.from_chain_type(
        llm=selected_llm,
        chain_type="stuff",
        retriever=topic_retriever if use_retriever and topic_retriever else None,
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )

    result = qa_chain.invoke(user_input)

    sources = [
        {
            "source": doc.metadata.get("source", "❌ 없음"),
            "metadata": doc.metadata,
            "length": len(doc.page_content),
            "snippet": doc.page_content[:300]
        }
        for doc in result.get('source_documents', [])
    ]

    formatted_sources = "\n\n".join(
        [f"# 문서\n{doc['snippet']}\n" for doc in sources]
    )

    return {
        "topics": topics,
        "answer": result['result'],
        "sources": formatted_sources
    }

# 요청 모델 정의
class AgentQueryRequest(BaseModel):
    question: str

# FastAPI 라우터
@app.post("/agent/query")
def query_agent(request: AgentQueryRequest = Body(...)):
    user_question = request.question

    # 린캔버스 요청 분기 처리
    if "린캔버스" in user_question:
        from shared_modules.queries import get_template_by_title

        # 기본값: Common
        template_title = "린 캔버스_common"

        # 세부 키워드에 따라 타이틀 지정
        if "네일" in user_question:
            template_title = "린 캔버스_nail"
        elif "속눈썹" in user_question:
            template_title = "린 캔버스_eyelash"
        elif "쇼핑몰" in user_question:
            template_title = "린 캔버스_ecommers"
        elif "유튜버" in user_question or "크리에이터" in user_question:
            template_title = "린 캔버스_creator"

        # DB에서 꺼내기
        template = get_template_by_title(template_title)

        return {
            "type": "lean_canvas",
            "title": template_title,
            "content": template["content"] if template else "<p>템플릿 없음</p>"
        }

    # 아니면 평소대로 RAG 흐름
    result = run_business_planning_with_rag(
        user_question,
        use_retriever=True,
        persona=persona
    )

    from shared_modules.queries import insert_message

    conversation_id = 4  # 예시 고정 ID

    insert_message(
        conversation_id=conversation_id,
        sender_type="USER",
        content=user_question
    )

    insert_message(
        conversation_id=conversation_id,
        sender_type="AGENT",
        content=result['answer'],
        agent_type="business_planning"
    )

    return result

from fastapi.responses import Response

@app.get("/lean_canvas/{title}")
def preview_template(title: str):
    from shared_modules.queries import get_template_by_title
    template = get_template_by_title(title)
    html = template["content"] if template else "<p>템플릿 없음</p>"
    return Response(content=html, media_type="text/html")

# 상태 확인 엔드포인트
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "config_validation": config.validate_config(),
        "services": {
            "database": "connected" if get_db_session() else "disconnected",
            "llm": "available" if get_llm() else "unavailable",
            "vectorstore": "available" if get_vectorstore() else "unavailable"
        }
    }

# 메인 실행
if __name__ == "__main__":
    import uvicorn
    logger.info("Business Planning Agent 시작")
    uvicorn.run(app, host=config.HOST, port=config.PORT)

# uvicorn business_planning:app --reload --host 0.0.0.0 --port 8000
# http://127.0.0.1:8000/docs
