#  상태 객체 정의
from typing import TypedDict, Literal
from langchain_core.messages import BaseMessage

class CustomerAgentState(TypedDict):
    user_id: int  
    conversation_id: int 
    user_input: str
    business_type: str
    mode: Literal["owner", "customer"]
    inquiry_type: Literal["인사", "상담", "잡담"]
    topics: list[str]
    answer: str
    sources: str
    a2a_data: dict  # A2A 통신용 데이터
    history: list   # 대화 이력