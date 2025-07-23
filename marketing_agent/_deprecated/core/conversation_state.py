"""
마케팅 에이전트 대화 상태 관리
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from .enums import MarketingStage


class FlexibleConversationState:
    """유연한 대화 상태 관리 클래스"""
    
    def __init__(self, conversation_id: int, user_id: int):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.current_stage = MarketingStage.ANY_QUESTION
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # 유연한 정보 수집 (단계 구분 없이)
        self.collected_info: Dict[str, Any] = {}
        
        # 대화 히스토리
        self.conversation_history: List[Dict[str, Any]] = []
        
        # 상태 플래그
        self.is_paused = False
        self.detected_business_type = "일반"
        
        # 사용자 선호도
        self.user_preferences = {
            "prefers_structured": False,
            "wants_immediate_answers": True,
            "communication_style": "friendly"
        }
    
    def add_information(self, key: str, value: Any, source: str = "user_input"):
        """정보 추가"""
        self.collected_info[key] = {
            "value": value,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "confidence": 1.0
        }
        self.updated_at = datetime.now()
    
    def get_information(self, key: str) -> Any:
        """정보 조회"""
        info = self.collected_info.get(key)
        return info["value"] if info else None
    
    def get_overall_completion_rate(self) -> float:
        """전체 완료율 계산"""
        # 수집된 정보 기반으로 완료율 계산
        essential_info_count = len([
            info for key, info in self.collected_info.items()
            if any(keyword in key.lower() for keyword in [
                "business_type", "main_goal", "target", "budget", "timeline"
            ])
        ])
        
        return min(essential_info_count / 10.0, 1.0)  # 10개 필수 정보 기준
    
    def get_next_stage(self) -> Optional[MarketingStage]:
        """다음 단계 반환"""
        stage_order = [
            MarketingStage.STAGE_1_GOAL,
            MarketingStage.STAGE_2_TARGET,
            MarketingStage.STAGE_3_STRATEGY,
            MarketingStage.STAGE_4_EXECUTION
        ]
        
        if self.current_stage in stage_order:
            current_index = stage_order.index(self.current_stage)
            if current_index < len(stage_order) - 1:
                return stage_order[current_index + 1]
        
        return None
    
    def reset_conversation(self):
        """대화 초기화"""
        self.current_stage = MarketingStage.ANY_QUESTION
        self.collected_info = {}
        self.conversation_history = []
        self.is_paused = False
        self.updated_at = datetime.now()
