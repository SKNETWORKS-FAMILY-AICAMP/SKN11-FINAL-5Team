"""
마케팅 에이전트 코어 모듈
"""

from .marketing_manager import Enhanced4StageMarketingManager, get_enhanced_4stage_marketing_manager
from .enums import MarketingStage, ResponseType
from .conversation_state import FlexibleConversationState
from .intent_analyzer import IntentAnalyzer
from .response_generator import ResponseGenerator
from .tool_manager import ToolManager
from .flow_controller import FlowController
from .information_collector import InformationCollector
from .utils import clean_json_response, create_default_intent_analysis, create_default_action_result

__all__ = [
    # 메인 클래스
    'Enhanced4StageMarketingManager',
    'get_enhanced_4stage_marketing_manager',
    
    # 열거형
    'MarketingStage',
    'ResponseType',
    
    # 모듈 클래스들
    'FlexibleConversationState',
    'IntentAnalyzer',
    'ResponseGenerator',
    'ToolManager',
    'FlowController',
    'InformationCollector',
    
    # 유틸리티 함수들
    'clean_json_response',
    'create_default_intent_analysis',
    'create_default_action_result'
]
