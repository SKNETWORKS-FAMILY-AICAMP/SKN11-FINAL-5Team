from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.output_parsers import StrOutputParser
import os
import sys
import logging
import pathlib  # 추가: 경로 처리를 위해 필요

# 로거 설정
logger = logging.getLogger(__name__)

# 경로 설정: 현재 파일 위치 → 프로젝트 루트
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# 절대경로로 임포트

from config.env_config import llm, vectorstore
from customer_agent.prompts_config import PROMPT_META
from MYSQL.queries import get_templates_by_type 

# 경로 처리를 위한 베이스 디렉토리 설정
BASE_DIR = pathlib.Path(__file__).parent.resolve()  # 추가

# 관련 토픽 추론
TOPIC_CLASSIFY_SYSTEM_PROMPT = """
너는 고객 질문을 분석해서 관련된 고객관리 토픽을 골라주는 역할이야.

아래의 토픽 중에서 질문과 관련된 키워드를 **가장 밀접한 키워드 1개만** 골라줘.
키만 출력하고, 설명은 하지마. (예: customer_service)
토픽이 없을 시 customer_etc 출력해.

가능한 토픽:
- customer_service – 응대, 클레임
- customer_retention – 재방문, 단골 전략
- customer_satisfaction – 만족도, 여정
- customer_feedback – 고객의 의견 수집 및 개선
- customer_segmentation – 타겟 분류, 페르소나
- community_building – 팬, 팬덤, 커뮤니티
- customer_data – 고객DB, CRM
- privacy_compliance – 개인정보, 동의 관리
- customer_message – 고객에게 보낼 메시지,문구,알림,템플릿 추천 및 작성
- customer_etc - 그 외의 토픽
"""

# 템플릿 주제 추론
TEMPLATE_TYPE_EXTRACT_PROMPT = """
다음은 고객 메시지 템플릿 유형 목록이야.
- 생일/기념일
- 구매 후 안내 (출고 완료, 배송 시작, 배송 안내 등 포함)
- 재구매 유도
- 고객 맞춤 메시지 (VIP, 가입 고객 등 포함)
- 리뷰 요청
- 설문 요청
- 이벤트 안내
- 예약
- 재방문
- 해당사항 없음

아래 질문에서 가장 잘 맞는 템플릿 유형을 한글로 정확히 1개만 골라줘.
설명 없이 키워드만 출력해. (예: 생일/기념일)
질문: {input}
"""


def classify_topics(user_input: str) -> list:
    # 수정: 변수화된 템플릿 사용
    classify_prompt = ChatPromptTemplate.from_messages([
        ("system", TOPIC_CLASSIFY_SYSTEM_PROMPT),
        ("human", "사용자 질문: {input}")  # 고정 문자열 → 변수
    ])
    
    chain = classify_prompt | llm | StrOutputParser()
    result = chain.invoke({"input": user_input}).strip()
    
    # 수정: 단일 토픽 반환 (시스템 지침에 따라)
    return [result.strip()] if result.strip() in PROMPT_META else []

# 에이전트 프롬프트 구성 함수
def build_agent_prompt(topics: list, persona: str):  
    merged_prompts = []
    for topic in topics:
        file_name = PROMPT_META[topic]["file"]  # 파일명만 사용
        prompt_text = load_prompt_text(file_name)
        merged_prompts.append(f"# {topic}\n{prompt_text}")
    
    role_descriptions = [PROMPT_META[topic]["role"] for topic in topics]
    
    if persona == "common":
        system_template = f"""#역할\n너는 1인 창업 전문 컨설턴트로서 {', '.join(role_descriptions)}야. 목표와 출력포맷에 맞게 응답해줘."""
    else:
        system_template = f"""#역할\n너는 {persona} 1인 창업 전문 컨설턴트로서 {', '.join(role_descriptions)}야. 목표와 출력포맷에 맞게 응답해줘."""

    system_template += " 제공된 문서가 비어있거나, 질문과 전혀 관련 없는 내용일 경우, 문서를 무시하고 너의 일반적인 지식을 기반으로 답변해줘."

    # 수정: 동적 변수 사용 (input, context)
    human_template = f"""
    {chr(10).join(merged_prompts)}
    
    #참고 문서
    {{context}}
    
    #사용자 입력
    {{input}}
    """
    
    return ChatPromptTemplate.from_messages([
        ("system", system_template),
        MessagesPlaceholder(variable_name="history"), # 추가
        ("human", human_template)
    ])


def load_prompt_text(file_name: str) -> str:
    # 수정: pathlib를 사용한 강화된 경로 처리
    prompt_dir = BASE_DIR / "prompt"
    full_path = prompt_dir / file_name
    
    try:
        # 수정: pathlib로 파일 읽기
        return full_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {full_path}")
        return ""
    except Exception as e:
        logger.error(f"Error loading prompt: {str(e)}")
        return ""

def extract_template_type(user_input: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", TEMPLATE_TYPE_EXTRACT_PROMPT),
        ("human", "{input}")
    ])
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"input": user_input}).strip()

def filter_templates_by_query(templates, query):
    query_lower = query.lower()
    filtered = []
    for t in templates:
        title = t.get('title', '')
        title_lower = title.lower()
        # VIP/단골 그룹
        if ('vip' in query_lower or '단골' in query_lower) and ('vip' in title_lower or '단골' in title_lower):
            filtered.append(t)
        # 휴면/장기미구매 그룹
        elif ('휴면' in query_lower or '장기미구매' in query_lower) and '휴면' in title:
            filtered.append(t)
        # 가입, 회원가입 그룹
        elif ('가입' in query_lower or '회원가입' in query_lower) and ('가입' in title_lower or '회원가입' in title_lower):
            filtered.append(t)
        # 최근 구매, 최근구매 그룹
        elif ('최근 구매' in query_lower or '최근구매' in query_lower) and ('최근 구매' in title_lower or '최근구매' in title_lower):
            filtered.append(t)
    return filtered


def run_rag_chain(user_input, topics, persona, chat_history):
    prompt = build_agent_prompt(topics, persona)
    base_filter = {"category": "customer_management"}

    if topics == ["customer_etc"]:
        search_kwargs = {"k": 5, "filter": base_filter}
    elif topics:
        topic_filter = {"$and": [base_filter, {"topic": {"$in": topics}}]}
        search_kwargs = {"k": 5, "filter": topic_filter}
    else:
        search_kwargs = {"k": 5, "filter": base_filter}

    retriever = vectorstore.as_retriever(
        search_kwargs=search_kwargs
    )
    document_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=prompt
    )
    retrieval_chain = create_retrieval_chain(
        retriever=retriever,
        combine_docs_chain=document_chain
    )
    result = retrieval_chain.invoke({
        "input": user_input,
        "history": chat_history or []
    })
    sources = "\n\n".join(
        [f"# 문서\n{doc.page_content}\n" for doc in result["context"]]
    )
    return result["answer"], sources

def run_customer_agent_with_rag(
    user_input: str,
    persona: str = "common",
    chat_history: list = None
):
    topics = classify_topics(user_input)
    logger.info(f"Classified topics: {topics}")

    if "customer_message" in topics:
        template_type = extract_template_type(user_input)
        logger.info(f"Extracted template_type: {template_type}")
        templates = get_templates_by_type(template_type)

        if template_type == "고객 맞춤 메시지" and templates:
            filtered_templates = filter_templates_by_query(templates, user_input)
        else:
            filtered_templates = templates

        if filtered_templates:
            answer_blocks = []
            for t in filtered_templates:
                if t.get("content_type") == "html":
                    preview_url = f"http://localhost:8000/preview/{t['template_id']}"
                    answer_blocks.append(f"제목: {t['title']}\n\n[HTML 미리보기]({preview_url})")

                else:
                    answer_blocks.append(f"제목: {t['title']}\n\n{t['content']}")
            #answer = "\n\n\n".join(answer_blocks)
            answer = "\n\n---\n\n".join(answer_blocks)
            answer += f"\n\n 위와 같은 메시지 템플릿을 활용해보세요."
            sources = ""
        else:
            answer, sources = run_rag_chain(user_input, topics, persona, chat_history)
        return {
            "topics": topics,
            "answer": answer,
            "sources": sources
        }

    # customer_message가 아닌 경우도 공통 RAG 실행
    answer, sources = run_rag_chain(user_input, topics, persona, chat_history)
    return {
        "topics": topics,
        "answer": answer,
        "sources": sources
    }
