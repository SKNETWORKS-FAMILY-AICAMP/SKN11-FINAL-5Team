"""
Marketing Agent - 공통 모듈 사용 버전
기존 설정 파일들을 shared_modules로 대체
"""

import sys
import os

# 텔레메트리 비활성화 (ChromaDB 오류 방지)
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY'] = 'False' 
os.environ['DO_NOT_TRACK'] = '1'

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared_modules import (
    get_config,
    get_llm,
    get_vectorstore,
    get_retriever,
    get_db_session,
    get_llm_manager
)

from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import RetrievalQA
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Body
from pydantic import BaseModel
from langchain_core.output_parsers import StrOutputParser
from fastapi.responses import FileResponse

from config.prompts_config import PROMPT_META
from typing import Optional
from config.persona_config import get_persona_by_type, get_specialized_config
from datetime import datetime as dt
from shared_modules.database import get_db_session, DatabaseManager
import shared_modules.queries as db

# 로깅 설정
from shared_modules.logging_utils import setup_logging
logger = setup_logging("marketing_agent", log_file="../logs/marketing.log")

# 설정 로드
config = get_config()

# FastAPI 초기화
app = FastAPI(title="Marketing Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LLM 상태 관리 (로드 밸런싱용)
llm_state = {
    "current": "openai",
    "counter": 0,
    "fallback_active": False
}

def get_llm_with_fallback():
    """자동 LLM 전환 및 폴백 지원"""
    try:
        # 기본: OpenAI 사용
        if llm_state["current"] == "openai":
            llm = get_llm("openai")
            if llm:
                return llm
            else:
                # OpenAI 실패 시 Gemini로 폴백
                logger.warning("OpenAI 사용 불가, Gemini로 폴백")
                llm_state["current"] = "gemini"
                llm_state["fallback_active"] = True
                return get_llm("gemini")
        
        # Gemini 사용
        elif llm_state["current"] == "gemini":
            llm = get_llm("gemini")
            if llm:
                return llm
            else:
                # Gemini 실패 시 OpenAI로 폴백
                logger.warning("Gemini 사용 불가, OpenAI로 폴백")
                llm_state["current"] = "openai"
                llm_state["fallback_active"] = True
                return get_llm("openai")
        
        # 기본값
        return get_llm()
        
    except Exception as e:
        logger.error(f"LLM 가져오기 실패: {e}")
        return get_llm()  # 기본 LLM 반환

def switch_llm_provider():
    """LLM 프로바이더 수동 전환"""
    llm_state["current"] = "gemini" if llm_state["current"] == "openai" else "openai"
    llm_state["fallback_active"] = False
    logger.info(f"LLM 프로바이더 변경: {llm_state['current']}")

# 프롬프트 파일 로드 함수
def load_prompt_text(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"프롬프트 파일 로드 실패 ({file_path}): {e}")
        return ""

# 토픽 분류
TOPIC_CLASSIFY_SYSTEM_PROMPT = """
너는 마케팅 질문을 분석해서 관련된 마케팅 토픽을 골라주는 역할이야.

아래의 토픽 중에서 질문과 관련된 키워드를 **최대 2개까지** 골라줘.
콤마(,)로 구분된 키만 출력하고, 설명은 하지마.

가능한 토픽:
1. marketing_fundamentals(마케팅 기초, 전략)
2. digital_advertising(광고, PPC, 소셜미디어 광고)
3. content_marketing(콘텐츠 제작, 블로그, 영상)
4. social_media_marketing(SNS 마케팅, 소셜미디어)
5. email_marketing(이메일 마케팅, 뉴스레터)
6. influencer_marketing(인플루언서, 협업 마케팅)
7. local_marketing(지역 마케팅, 오프라인)
8. conversion_optimization(전환율, CRO, 최적화)
9. marketing_automation(자동화, 마케팅 툴)
10. marketing_metrics(성과 측정, 분석, KPI)
11. viral_marketing(바이럴, 입소문)
12. personal_branding(개인 브랜딩, 퍼스널 브랜드)
13. blog_marketing(블로그 마케팅, SEO)

**출력 예시**: marketing_fundamentals, digital_advertising
"""

def classify_topics(user_input: str) -> list:
    """토픽 분류"""
    try:
        classify_prompt = ChatPromptTemplate.from_messages([
            ("system", TOPIC_CLASSIFY_SYSTEM_PROMPT),
            ("human", f"사용자 질문: {user_input}")
        ])
        
        llm = get_llm_with_fallback()
        chain = classify_prompt | llm | StrOutputParser()
        result = chain.invoke({"input": user_input}).strip()
        
        topics = [t.strip() for t in result.split(",") if t.strip() in PROMPT_META]
        logger.info(f"분류된 토픽: {topics}")
        return topics
        
    except Exception as e:
        logger.error(f"토픽 분류 실패: {e}")
        return []

# 에이전트 프롬프트 구성
def build_agent_prompt(topics: list, user_input: str, persona_type: str, history: str, user_info: dict):
    """마케팅 에이전트 프롬프트 구성"""
    merged_prompts = []
    
    for topic in topics:
        if topic in PROMPT_META:
            file_path = PROMPT_META[topic]["file"]
            prompt_text = load_prompt_text(file_path)
            merged_prompts.append(prompt_text)

    role_descriptions = [PROMPT_META[topic]["role"] for topic in topics]
    
    # 페르소나 설정 적용
    persona_config = get_specialized_config(persona_type, user_info)
    persona_context = f"전문 분야: {persona_config.get('expertise', '일반')}, " \
                     f"관심사: {persona_config.get('interests', '일반적인 비즈니스')}"
    
    system_context = f"""당신은 {persona_type} 전문 마케팅 컨설턴트입니다. 
{', '.join(role_descriptions)}

페르소나 정보: {persona_context}

사용자 정보:
- 사업 유형: {user_info.get('business_type', '미지정')}
- 타겟 고객: {user_info.get('target_audience', '미지정')}
- 예산 범위: {user_info.get('budget_range', '미지정')}
"""

    template = f"""{system_context}

다음 지침을 따라 답변하세요:
{chr(10).join(merged_prompts)}

최근 대화:
{history}

참고 문서:
{{context}}

사용자 질문: "{user_input}"

위 지침에 따라 구체적이고 실용적인 마케팅 조언을 제공하세요."""

    from langchain.prompts import PromptTemplate
    return PromptTemplate(
        input_variables=["context"],
        template=template
    )

def run_marketing_rag_with_persona(
    user_input: str, 
    persona_type: str = "solopreneur",
    use_retriever: bool = True,
    user_info: dict = None
):
    """페르소나 기반 마케팅 RAG 실행"""
    try:
        if user_info is None:
            user_info = {}
        
        # LLM 가져오기
        selected_llm = get_llm_with_fallback()
        
        # 토픽 분류
        topics = classify_topics(user_input)
        
        # 히스토리 가져오기 (DB에서)
        conversation_id = user_info.get('conversation_id', 1)
        try:
            history_rows = db.get_recent_messages(conversation_id)
            history_text = ""
            for msg in reversed(history_rows):
                role = "User" if msg["sender_type"] == "USER" else "Agent"
                history_text += f"{role}: {msg['content']}\n"
        except Exception as e:
            logger.warning(f"히스토리 로드 실패: {e}")
            history_text = ""
        
        # 프롬프트 생성
        prompt = build_agent_prompt(topics, user_input, persona_type, history_text, user_info)
        
        # 필터 설정
        if topics:
            topic_filter = {
                "$and": [
                    {"category": "marketing"},
                    {"topic": {"$in": topics}}
                ]
            }
        else:
            topic_filter = {"category": "marketing"}

        # 벡터 스토어 및 검색기
        vectorstore = get_vectorstore("global-documents")
        if not vectorstore:
            logger.error("벡터스토어를 사용할 수 없습니다")
            return {
                "topics": topics,
                "answer": "죄송합니다. 현재 서비스에 접속할 수 없습니다.",
                "sources": "",
                "persona_used": persona_type
            }

        topic_retriever = vectorstore.as_retriever(
            search_kwargs={"k": 5, "filter": topic_filter}
        )

        # RetrievalQA 체인 생성
        qa_chain = RetrievalQA.from_chain_type(
            llm=selected_llm,
            chain_type="stuff",
            retriever=topic_retriever if use_retriever else None,
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
            "sources": formatted_sources,
            "persona_used": persona_type,
            "llm_provider": llm_state["current"]
        }
        
    except Exception as e:
        logger.error(f"마케팅 RAG 실행 실패: {e}")
        return {
            "topics": [],
            "answer": "죄송합니다. 요청을 처리하는 중 오류가 발생했습니다.",
            "sources": "",
            "persona_used": persona_type
        }

# 요청 모델들
class MarketingQueryRequest(BaseModel):
    question: str
    persona_type: str = "solopreneur"
    business_type: Optional[str] = None
    target_audience: Optional[str] = None
    budget_range: Optional[str] = None
    conversation_id: Optional[int] = 1

class PersonaRequest(BaseModel):
    persona_type: str

# API 엔드포인트들
@app.post("/agent/query")
def query_marketing_agent(request: MarketingQueryRequest = Body(...)):
    """마케팅 에이전트 쿼리"""
    try:
        user_info = {
            "business_type": request.business_type,
            "target_audience": request.target_audience,
            "budget_range": request.budget_range,
            "conversation_id": request.conversation_id
        }
        
        result = run_marketing_rag_with_persona(
            user_input=request.question,
            persona_type=request.persona_type,
            use_retriever=True,
            user_info=user_info
        )
        
        # DB에 대화 저장
        try:
            db.insert_message(
                conversation_id=request.conversation_id,
                sender_type="USER",
                content=request.question
            )
            
            db.insert_message(
                conversation_id=request.conversation_id,
                sender_type="AGENT",
                content=result['answer'],
                agent_type="marketing"
            )
        except Exception as e:
            logger.warning(f"DB 저장 실패: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"마케팅 쿼리 처리 오류: {e}")
        return {
            "topics": [],
            "answer": "죄송합니다. 요청을 처리할 수 없습니다.",
            "sources": "",
            "error": str(e)
        }

@app.post("/switch-llm")
def switch_llm():
    """LLM 프로바이더 수동 전환"""
    switch_llm_provider()
    return {
        "current_provider": llm_state["current"],
        "status": "switched"
    }

@app.get("/llm-status")
def get_llm_status():
    """LLM 상태 조회"""
    llm_manager = get_llm_manager()
    return {
        "current_state": llm_state,
        "manager_status": llm_manager.get_status(),
        "available_models": llm_manager.get_available_models()
    }

@app.post("/persona")
def get_persona_config(request: PersonaRequest = Body(...)):
    """페르소나 설정 조회"""
    try:
        persona_config = get_persona_by_type(request.persona_type)
        specialized_config = get_specialized_config(request.persona_type, {})
        
        return {
            "persona_type": request.persona_type,
            "base_config": persona_config,
            "specialized_config": specialized_config
        }
    except Exception as e:
        logger.error(f"페르소나 설정 조회 오류: {e}")
        return {"error": str(e)}

@app.get("/health")
def health_check():
    """서비스 상태 확인"""
    return {
        "status": "healthy",
        "agent": "marketing",
        "config_validation": config.validate_config(),
        "services": {
            "database": "connected" if get_db_session() else "disconnected",
            "llm": "available" if get_llm() else "unavailable",
            "vectorstore": "available" if get_vectorstore() else "unavailable"
        },
        "llm_state": llm_state
    }

# 정적 파일 서빙 (기존 기능 유지)
@app.get("/download/template/{filename}")
def download_template(filename: str):
    """마케팅 템플릿 다운로드"""
    file_path = f"./templates/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    else:
        return {"error": "파일을 찾을 수 없습니다"}

# 메인 실행
if __name__ == "__main__":
    import uvicorn
    logger.info("Marketing Agent 시작")
    uvicorn.run(app, host=config.HOST, port=8002)

# uvicorn rag:app --reload --host 0.0.0.0 --port 8002
