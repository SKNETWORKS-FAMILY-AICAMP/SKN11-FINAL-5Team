from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser,StrOutputParser  # PydanticOutputParser 대신 사용
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from .state import CustomerAgentState
from customer_agent.agent_runner import run_customer_agent_with_rag
import logging
import os
import sys
import re  # 정규식 사용

# 로거 설정
logger = logging.getLogger(__name__)

# 경로 설정: 현재 파일 위치 → 프로젝트 루트
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# 절대경로로 임포트
from config.env_config import llm,llm_gemini

# 1. 분류 모델 정의 (Pydantic 대신 간소화)
class InquiryClassification(BaseModel):
    inquiry_type: str = Field(..., enum=["인사", "상담", "잡담"])

def analyze_inquiry_node(state: CustomerAgentState) -> dict:
    """문의 분류 노드 (JSON 파서 사용)"""
    # 2. 도메인 특화 프롬프트
    system_prompt = """
    **사장님의 고객 관리 문제 해결을 위한 문의 분류 시스템**
    
    **반드시 다음 3개 유형 중 하나로 분류하세요:**
    - 인사: 순수 인사/감사 표현 (예: "안녕하세요", "감사합니다")
    - 상담: 사장님의 고객 관리 관련 문의  
      (예: "단골 고객 유지 방법", "고객 불만 해결법", "리뷰 관리 전략","답변 템플릿/메세지 추천")
    - 잡담: 업무와 무관한 대화 (예: "오늘 날씨 좋네요")
    
    **출력 형식:**
    {format_instructions}
    """
    
    # 3. JSON 파서 설정
    parser = JsonOutputParser(pydantic_object=InquiryClassification)
    
    # 4. 프롬프트 구성
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt + "\n\n{format_instructions}"),
        ("human", "문의 내용: {input}")
    ]).partial(format_instructions=parser.get_format_instructions())
    
    # 5. 체인 구성
    chain = prompt | llm | parser
    
    # 6. 분류 실행
    try:
        result = chain.invoke({"input": state["user_input"]})
        inquiry_type = result.get("inquiry_type", "상담")
        logger.info(f"분류 결과: {inquiry_type}")
        return {"inquiry_type": inquiry_type}
    except Exception as e:
        logger.error(f"분류 오류: {str(e)}")
        return {"inquiry_type": "상담"}


def small_talk_node(state: CustomerAgentState) -> dict:
    # 기존 히스토리 로그 찍기 (디버깅용)
    logger.info(f"[SmallTalk 히스토리] { [msg.content for msg in state['history']] }")
    logger.info(f"[SmallTalk 입력] {state['user_input']}")

    # 답변 생성 (룰 기반 + LLM)
    user_input = state["user_input"].lower()
    if "안녕" in user_input:
        response = "안녕하세요! 고객 관리에 대해 궁금하신 점이 있으신가요?"
    elif "감사" in user_input:
        response = "감사합니다! 더 나은 서비스로 보답하겠습니다."
    else:
        prompt = ChatPromptTemplate.from_template(
            "사용자의 인사나 잡담에 1-2문장으로 정중한 어투로 답변하세요: {input}"
        )
        chain = prompt | llm_gemini | StrOutputParser()
        #chain = prompt | llm | StrOutputParser()
        response = chain.invoke({"input": state["user_input"]})

    # 새 메시지 생성 (history에 append)
    new_user_msg = HumanMessage(content=state["user_input"])
    new_ai_msg = AIMessage(content=response)
    updated_history = (state["history"] + [new_user_msg, new_ai_msg])[-6:]  # 최근 6개만 유지

    return {
        "answer": response,
        "history": updated_history
    }

def rag_node(state: CustomerAgentState) -> dict:
    logger.info(f"[RAG 히스토리] 대화 ID {state['conversation_id']} 히스토리: {[msg.content for msg in state['history']]}")
    logger.info(f"[RAG 입력] {state['user_input']}")

    # 히스토리 포함 실행
    result = run_customer_agent_with_rag(
        user_input=state["user_input"],
        persona=state["business_type"],
        chat_history=state["history"]
    )

    # 새 메시지 생성
    new_user_msg = HumanMessage(content=state["user_input"])
    new_ai_msg = AIMessage(content=result["answer"])
    updated_history = (state["history"] + [new_user_msg, new_ai_msg])[-6:]

    return {
        "topics": result["topics"],
        "answer": result["answer"],
        "sources": result["sources"],
        "history": updated_history
    }