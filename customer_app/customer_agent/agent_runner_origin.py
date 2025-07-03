from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import RetrievalQA
from fastapi.middleware.cors import CORSMiddleware
from prompts_config import PROMPT_META
from fastapi import FastAPI, Body
from pydantic import BaseModel
from ..config.env_config import llm, retriever, embedding, vectorstore
from langchain_core.output_parsers import StrOutputParser
import os

# ✅ FastAPI 초기화
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (개발용)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# persona
persona = "e-commerce"  # 나중에 userdb의 business_type가져오기
# from MYSQL.queries import get_business_type
# persona = get_business_type_by_user_id(request.user_id)

# ✅ 프롬프트 파일 로드 함수
def load_prompt_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

# ✅ 관련 토픽 추론
TOPIC_CLASSIFY_SYSTEM_PROMPT = """
너는 고객 질문을 분석해서 관련된 고객관리 토픽을 모두 골라주는 역할이야.

아래의 토픽 중에서 질문과 관련된 키워드를 **가장 밀접한 키워드 1개만** 골라줘.
키만 출력하고, 설명은 하지마. (예: customer_service)

가능한 토픽:
- customer_service – 응대, 클레임
- customer_retention – 재방문, 단골 전략
- customer_satisfaction – 만족도, 여정
- customer_feedback – 의견 수집 및 개선
- customer_segmentation – 타겟 분류, 페르소나
- community_building – 팬, 팬덤, 커뮤니티
- customer_data – 고객DB, CRM
- privacy_compliance – 개인정보, 동의 관리
"""

def classify_topics(user_input: str) -> list:
    classify_prompt = ChatPromptTemplate.from_messages([
        ("system", TOPIC_CLASSIFY_SYSTEM_PROMPT),
        ("human", f"사용자 질문: {user_input}")
    ])
    chain = classify_prompt | llm | StrOutputParser()
    result = chain.invoke({"input": user_input}).strip()
    return [t.strip() for t in result.split(",") if t.strip() in PROMPT_META]

# ✅ 에이전트 프롬프트 구성 함수 (여러 프롬프트 병합)
def build_agent_prompt(topics: list, user_input: str, persona: str):
    merged_prompts = []
    print(f"선택된 토픽: {topics}")
    for topic in topics:
        file_path = PROMPT_META[topic]["file"]
        prompt_text = load_prompt_text(file_path)
        merged_prompts.append(f"# {topic}\n{prompt_text}")

    role_descriptions = [PROMPT_META[topic]["role"] for topic in topics]
    
    if persona == "common":
        system_template = f"""#역할\n너는 1인 창업 전문 컨설턴트로서 {', '.join(role_descriptions)}야. 목표와 출력포맷에 맞게 응답해줘."""
    else:
        system_template = f"""#역할\n너는 {persona} 1인 창업 전문 컨설턴트로서 {', '.join(role_descriptions)}야. 목표,출력포맷,응답방식에 맞게 응답해줘."""

    system_template += "제공된 문서가 질문과 전혀 관련 없는 내용일 경우, 문서를 무시하고 너의 일반적인 지식을 기반으로 답변해줘."

    human_template = f"""
    {chr(10).join(merged_prompts)}

    #참고 문서
    {{context}}

    #사용자 입력
    {user_input}
    """

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template)
    ])
    return prompt


def run_customer_agent_with_rag(user_input: str, use_retriever: bool = True, persona: str = "common"):
    topics = classify_topics(user_input)
    prompt = build_agent_prompt(topics, user_input, persona)

    # topic 없을 때도 category 필터는 항상 유지
    base_filter = {"category": "customer_management"}
    if topics:
        topic_filter = {
            "$and": [
                base_filter,
                {"topic": {"$in": topics}}
            ]
        }
    else:
        topic_filter = base_filter

    topic_retriever = vectorstore.as_retriever(
        search_kwargs={"k": 5, "filter": topic_filter}
    )

    # result = topic_retriever.get_relevant_documents(user_input)
    result = topic_retriever.invoke(user_input)
    # 여러 chunk의 'content'를 합쳐서 하나의 'context'로 설정
    context = "\n\n".join([doc.page_content for doc in result])

    # qa_chain에서 context 변수 설정
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=topic_retriever if use_retriever else None,
        chain_type_kwargs={"prompt": prompt},  # input_variables 제거
        return_source_documents=True
    )

    result = qa_chain.invoke(user_input)

    # 문서 내용 출력
    sources = [
        {
            "source": doc.metadata.get("source", "❌ 없음"),
            "metadata": doc.metadata,
            "length": len(doc.page_content),
            "snippet": doc.page_content # [:300]  # 문서의 첫 300자만 preview
        }
        for doc in result.get('source_documents', [])
    ]

    # 문서 내용 포맷팅하여 # 문서 형태로 출력
    formatted_sources = "\n\n".join(
        [f"# 문서\n{doc['snippet']}\n" for doc in sources]
    )

    return {
        "topics": topics,
        "answer": result['result'],
        "sources": formatted_sources
    }


# ✅ 요청 모델 정의
class AgentQueryRequest(BaseModel):
    question: str


# ✅ FastAPI 라우터
@app.post("/agent/query")
def query_agent(request: AgentQueryRequest = Body(...)):
    result = run_customer_agent_with_rag(request.question, use_retriever=True, persona=persona)
    print(result)
    return result



# 배송이 너무 늦어서 별점1개가 달렸어. 어떻게 답변 달아야 할까?

# uvicorn agent_runner:app --reload 

# curl -X POST "http://127.0.0.1:8000/agent/query" ^
# -H "Content-Type: application/json" ^
# -d "{\"question\": \"고객과의 장기적인 관계 유지를 위해 어떤 전략을 추천해줄 수 있나요?\"}"
