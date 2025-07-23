"""
마케팅 에이전트 진행 제어 모듈
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from .enums import MarketingStage, STAGE_MESSAGES, STAGE_QUESTIONS
from .conversation_state import FlexibleConversationState

logger = logging.getLogger(__name__)


class FlowController:
    """진행 제어 관리 클래스"""
    
    def handle_flow_control(self, command: str, state: FlexibleConversationState, 
                           user_input: str) -> Dict[str, Any]:
        """진행 제어 처리"""
        logger.info(f"[단계 로그] 진행 제어 처리 - 명령: {command}, 현재 단계: {state.current_stage.value}")

        if command == "pause":
            state.is_paused = True
            return {
                "action": "paused",
                "message": f"🛑 대화를 일시 중단했습니다.\n\n현재 진행 상황을 저장했습니다. '재개'라고 말씀하시면 이어서 진행하겠습니다.",
                "pause_info": {
                    "stage": state.current_stage.value,
                    "completion": state.get_overall_completion_rate(),
                    "paused_at": datetime.now().isoformat()
                }
            }
        
        elif command == "resume":
            state.is_paused = False
            return {
                "action": "resumed", 
                "message": f"▶️ 대화를 재개합니다!\n\n현재 {state.current_stage.value} 단계에서 계속 진행하겠습니다.",
                "current_stage": state.current_stage.value
            }
        
        elif command == "skip":
            available_stages = [s for s in MarketingStage if s != state.current_stage and s not in [MarketingStage.ANY_QUESTION, MarketingStage.COMPLETED]]
            return {
                "action": "stage_selection",
                "message": "어떤 단계로 이동하시겠습니까?",
                "options": [s.value for s in available_stages]
            }
        
        elif command == "restart":
            state.reset_conversation()
            return {
                "action": "restarted",
                "message": "🔄 처음부터 다시 시작합니다!\n\n어떤 방식으로 진행하시겠습니까?",
                "options": ["체계적 4단계 진행", "즉시 질문 응답", "특정 단계로 이동"]
            }
        
        elif command == "next":
            next_stage = state.get_next_stage()
            if next_stage:
                state.current_stage = next_stage
                
                # 단계 이동 후 해당 단계의 질문 자동 생성
                stage_message = f"⏭️ {next_stage.value} 단계로 이동했습니다.\n\n"
                stage_question = STAGE_QUESTIONS.get(next_stage, "새로운 단계에서 어떤 도움이 필요하신가요?")
                
                return {
                    "action": "next_stage",
                    "message": stage_message + stage_question,
                    "new_stage": next_stage.value,
                    "include_question": True
                }
            else:
                return {
                    "action": "no_next_stage",
                    "message": "더 이상 진행할 단계가 없습니다. 현재 단계를 완료해주세요."
                }
        
        return {"action": "unknown_command", "message": f"'{command}' 명령을 인식할 수 없습니다."}

    def jump_to_stage(self, target_stage: str, state: FlexibleConversationState) -> Dict[str, Any]:
        """특정 단계로 이동"""
        
        stage_mapping = {
            "1": MarketingStage.STAGE_1_GOAL,
            "2": MarketingStage.STAGE_2_TARGET,
            "3": MarketingStage.STAGE_3_STRATEGY,
            "4": MarketingStage.STAGE_4_EXECUTION,
            "목표": MarketingStage.STAGE_1_GOAL,
            "타겟": MarketingStage.STAGE_2_TARGET,
            "전략": MarketingStage.STAGE_3_STRATEGY,
            "실행": MarketingStage.STAGE_4_EXECUTION,
            "any": MarketingStage.ANY_QUESTION
        }
        
        if target_stage not in stage_mapping:
            return {
                "success": False,
                "message": f"'{target_stage}' 단계를 찾을 수 없습니다.",
                "available_stages": list(stage_mapping.keys())
            }
        
        target_stage_enum = stage_mapping[target_stage]
        state.current_stage = target_stage_enum
        state.updated_at = datetime.now()
        
        return {
            "success": True,
            "message": STAGE_MESSAGES[target_stage_enum],
            "new_stage": target_stage_enum.value
        }
