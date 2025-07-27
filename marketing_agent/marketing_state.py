"""
LangGraph 기반 마케팅 에이전트 State 관리
"""

import logging
from typing import Dict, Any, List, Optional, Literal
from typing_extensions import TypedDict, NotRequired
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class MarketingStage(Enum):
    """마케팅 단계 정의"""
    INITIAL = "initial"
    GOAL_SETTING = "goal_setting"
    TARGET_ANALYSIS = "target_analysis"
    STRATEGY_PLANNING = "strategy_planning"
    CONTENT_CREATION = "content_creation"
    EXECUTION = "execution"
    COMPLETED = "completed"

class ContentType(Enum):
    """컨텐츠 타입"""
    INSTAGRAM_POST = "instagram_post"
    BLOG_POST = "blog_post"
    MARKETING_STRATEGY = "marketing_strategy"
    CAMPAIGN_PLAN = "campaign_plan"

# LangGraph State 정의
class MarketingAgentState(TypedDict):
    """마케팅 에이전트의 전체 상태를 관리하는 TypedDict"""
    
    # 기본 정보
    user_id: int
    conversation_id: int
    user_input: str
    current_stage: MarketingStage
    
    # 대화 상태
    messages: List[Dict[str, Any]]
    response: NotRequired[str]
    
    # 수집된 비즈니스 정보
    business_type: NotRequired[str]
    product: NotRequired[str]
    target_audience: NotRequired[str]
    main_goal: NotRequired[str]
    budget: NotRequired[str]
    preferred_channels: NotRequired[List[str]]
    pain_points: NotRequired[str]
    
    # 분석 결과
    keywords: NotRequired[List[str]]
    trend_data: NotRequired[Dict[str, Any]]
    market_analysis: NotRequired[Dict[str, Any]]
    
    # 컨텐츠 생성 관련
    content_type: NotRequired[ContentType]
    generated_content: NotRequired[Dict[str, Any]]
    content_history: NotRequired[List[Dict[str, Any]]]
    
    # 사용자 피드백 및 상태
    user_engagement_level: NotRequired[Literal["high", "medium", "low"]]
    negative_response_count: NotRequired[int]
    iteration_count: NotRequired[int]
    
    # 메타데이터
    created_at: NotRequired[datetime]
    last_activity: NotRequired[datetime]
    completion_rate: NotRequired[float]
    
    # 라우팅 제어
    next_action: NotRequired[str]
    should_end: NotRequired[bool]
    
    # 에러 처리
    error: NotRequired[str]
    retry_count: NotRequired[int]

# State 관리 헬퍼 클래스
class StateManager:
    """State 조작을 위한 헬퍼 메서드들"""
    
    @staticmethod
    def initialize_state(user_id: int, conversation_id: int, user_input: str) -> MarketingAgentState:
        """새 상태 초기화"""
        return MarketingAgentState(
            user_id=user_id,
            conversation_id=conversation_id,
            user_input=user_input,
            current_stage=MarketingStage.INITIAL,
            messages=[],
            user_engagement_level="high",
            negative_response_count=0,
            iteration_count=0,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            completion_rate=0.0,
            should_end=False,
            retry_count=0
        )
    
    @staticmethod
    def add_message(state: MarketingAgentState, role: str, content: str) -> MarketingAgentState:
        """메시지 추가"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "stage": state["current_stage"].value
        }
        
        messages = state.get("messages", [])
        messages.append(message)
        
        # 최대 메시지 수 제한
        if len(messages) > 20:
            messages = messages[-20:]
        
        return {**state, "messages": messages, "last_activity": datetime.now()}
    
    @staticmethod
    def update_business_info(state: MarketingAgentState, **kwargs) -> MarketingAgentState:
        """비즈니스 정보 업데이트"""
        updated_state = {**state}
        
        for key, value in kwargs.items():
            if key in ["business_type", "product", "target_audience", "main_goal", 
                      "budget", "preferred_channels", "pain_points"]:
                updated_state[key] = value
        
        # 완료율 계산
        completion_rate = StateManager.calculate_completion_rate(updated_state)
        updated_state["completion_rate"] = completion_rate
        
        return updated_state
    
    @staticmethod
    def calculate_completion_rate(state: MarketingAgentState) -> float:
        """완료율 계산"""
        required_fields = ["business_type", "product", "target_audience", "main_goal", "budget"]
        completed_fields = sum(1 for field in required_fields if state.get(field))
        return completed_fields / len(required_fields)
    
    @staticmethod
    def advance_stage(state: MarketingAgentState, next_stage: MarketingStage) -> MarketingAgentState:
        """다음 단계로 진행"""
        return {**state, "current_stage": next_stage, "iteration_count": 0}
    
    @staticmethod
    def record_negative_response(state: MarketingAgentState) -> MarketingAgentState:
        """부정적 응답 기록"""
        negative_count = state.get("negative_response_count", 0) + 1
        engagement_level = "low" if negative_count >= 3 else "medium" if negative_count >= 2 else "high"
        
        return {
            **state, 
            "negative_response_count": negative_count,
            "user_engagement_level": engagement_level
        }
    
    @staticmethod
    def reset_negative_responses(state: MarketingAgentState) -> MarketingAgentState:
        """부정적 응답 리셋"""
        return {
            **state, 
            "negative_response_count": 0,
            "user_engagement_level": "high"
        }
    
    @staticmethod
    def set_content_creation(state: MarketingAgentState, content_type: ContentType) -> MarketingAgentState:
        """컨텐츠 생성 모드 설정"""
        return {
            **state,
            "current_stage": MarketingStage.CONTENT_CREATION,
            "content_type": content_type
        }
    
    @staticmethod
    def save_generated_content(state: MarketingAgentState, content: Dict[str, Any]) -> MarketingAgentState:
        """생성된 컨텐츠 저장"""
        content_history = state.get("content_history", [])
        content_history.append({
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "type": state.get("content_type", ContentType.INSTAGRAM_POST).value
        })
        
        return {
            **state,
            "generated_content": content,
            "content_history": content_history
        }
    
    @staticmethod
    def set_error(state: MarketingAgentState, error_message: str) -> MarketingAgentState:
        """에러 상태 설정"""
        retry_count = state.get("retry_count", 0) + 1
        return {
            **state,
            "error": error_message,
            "retry_count": retry_count
        }
    
    @staticmethod
    def clear_error(state: MarketingAgentState) -> MarketingAgentState:
        """에러 상태 클리어"""
        updated_state = {**state}
        if "error" in updated_state:
            del updated_state["error"]
        updated_state["retry_count"] = 0
        return updated_state
    
    @staticmethod
    def should_continue_conversation(state: MarketingAgentState) -> bool:
        """대화를 계속해야 하는지 판단"""
        return (
            not state.get("should_end", False) and
            state.get("retry_count", 0) < 3 and
            state.get("iteration_count", 0) < 10
        )
    
    @staticmethod
    def get_missing_info(state: MarketingAgentState) -> List[str]:
        """부족한 정보 목록"""
        required_fields = ["business_type", "product", "target_audience", "main_goal"]
        return [field for field in required_fields if not state.get(field)]
    
    @staticmethod
    def get_stage_context(state: MarketingAgentState) -> str:
        """현재 단계 컨텍스트 생성"""
        stage = state["current_stage"]
        completion_rate = state.get("completion_rate", 0.0)
        
        context_parts = [
            f"현재 단계: {stage.value}",
            f"완료율: {completion_rate:.0%}",
            f"참여도: {state.get('user_engagement_level', 'high')}"
        ]
        
        # 비즈니스 정보
        if state.get("business_type"):
            context_parts.append(f"업종: {state['business_type']}")
        if state.get("product"):
            context_parts.append(f"제품: {state['product']}")
        if state.get("target_audience"):
            context_parts.append(f"타겟: {state['target_audience']}")
        
        return "\n".join(context_parts)
    
    @staticmethod
    def can_proceed_to_content_creation(state: MarketingAgentState) -> bool:
        """컨텐츠 생성 단계로 진행 가능한지 확인"""
        return (
            state.get("business_type") and
            state.get("product") and
            state.get("completion_rate", 0.0) > 0.4
        )
