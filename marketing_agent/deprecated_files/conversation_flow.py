"""
⚠️ DEPRECATED - 이 파일은 더 이상 사용되지 않습니다.

새로운 멀티턴 대화 시스템은 marketing_manager.py에 구현되어 있습니다.
더 향상된 기능들을 제공합니다:

- 정보 수집 → 분석 → 제안 → 피드백 → 수정 → 최종 결과 플로우
- LLM 기반 의도 분석
- MCP 도구 통합 (해시태그 분석, 트렌드 분석, 콘텐츠 생성)
- 벡터 스토어 기반 전문 지식 검색 (RAG)
- 토픽별 전문 프롬프트
- 실시간 피드백 수집 및 전략 수정

새로운 시스템 사용법:
```python
from marketing_agent.core.marketing_manager import MarketingAgentManager

manager = MarketingAgentManager()
response = manager.process_user_query(
    user_input="카페 마케팅 도움이 필요해요",
    user_id=123,
    conversation_id=None  # 새로운 대화 시작
)
```

자세한 사용법은 example_multiturn_usage.py를 참고하세요.
"""

# 이전 버전 호환성을 위한 임시 wrapper
import warnings
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import json

warnings.warn(
    "conversation_flow.py는 deprecated되었습니다. "
    "marketing_manager.py의 새로운 멀티턴 시스템을 사용하세요.",
    DeprecationWarning,
    stacklevel=2
)

class ConversationStage(Enum):
    """대화 단계 정의 - DEPRECATED"""
    INITIAL = "initial"                    
    BUSINESS_INFO = "business_info"        
    GOAL_SETTING = "goal_setting"          
    PLATFORM_SELECTION = "platform_selection"  
    ANALYSIS_EXECUTION = "analysis_execution"   
    STRATEGY_PROPOSAL = "strategy_proposal"     
    CONTENT_CREATION = "content_creation"       
    FEEDBACK_COLLECTION = "feedback_collection" 
    REFINEMENT = "refinement"                   
    FINAL_DELIVERY = "final_delivery"           
    COMPLETED = "completed"                     

class MultiTurnConversationManager:
    """DEPRECATED - 새로운 MarketingAgentManager를 사용하세요"""
    
    def __init__(self):
        warnings.warn(
            "MultiTurnConversationManager는 deprecated되었습니다. "
            "MarketingAgentManager를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        self.conversations = {}
    
    def get_conversation_state(self, conversation_id: int) -> Dict[str, Any]:
        """DEPRECATED - 새로운 시스템으로 마이그레이션하세요"""
        return {"error": "DEPRECATED - MarketingAgentManager.get_conversation_status() 사용"}
    
    def analyze_user_response_for_stage(self, *args, **kwargs) -> Dict[str, Any]:
        """DEPRECATED"""
        return {"error": "DEPRECATED - MarketingAgentManager.analyze_user_intent_and_stage() 사용"}
    
    def generate_stage_response(self, *args, **kwargs) -> Tuple[str, ConversationStage]:
        """DEPRECATED"""
        return "DEPRECATED - MarketingAgentManager.process_user_query() 사용", ConversationStage.COMPLETED
