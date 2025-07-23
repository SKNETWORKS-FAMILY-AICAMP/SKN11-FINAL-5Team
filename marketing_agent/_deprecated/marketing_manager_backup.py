"""
LLM 기반 유연한 4단계 마케팅 에이전트 매니저 (리팩토링된 버전)
- 순서 무관 즉시 응답
- 중간 단계부터 시작
- 단계 건너뛰기
- 모든 의도 분석 LLM 기반
- 마케팅 툴 자동 활용
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

# 공통 모듈 임포트 (안전한 import)
try:
    from shared_modules import (
        get_config,
        get_llm_manager,
        get_vector_manager,
        get_or_create_conversation_session,
        create_message,
        insert_message_raw,
        get_session_context,
        create_marketing_response,
        create_error_response
    )
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"shared_modules import 실패: {e}")

# 분리된 모듈들 임포트
from .enums import MarketingStage, ResponseType
from .conversation_state import FlexibleConversationState
from .intent_analyzer import IntentAnalyzer
from .response_generator import ResponseGenerator
from .tool_manager import ToolManager
from .flow_controller import FlowController
from .information_collector import InformationCollector

logger = logging.getLogger(__name__)


class Enhanced4StageMarketingManager:
    """LLM 기반 유연한 4단계 마케팅 에이전트 관리자"""
    
    def __init__(self):
        """마케팅 매니저 초기화"""
        self.config = get_config()
        self.llm_manager = get_llm_manager()
        self.vector_manager = get_vector_manager()
        
        # 프롬프트 디렉토리 설정
        self.prompts_dir = Path(__file__).parent.parent / 'prompts'
        
        # 대화 상태 관리 (메모리 기반)
        self.conversation_states: Dict[int, FlexibleConversationState] = {}
        
        # 분리된 모듈들 초기화
        self.intent_analyzer = IntentAnalyzer()
        self.response_generator = ResponseGenerator(self.prompts_dir)
        self.tool_manager = ToolManager()
        self.flow_controller = FlowController()
        self.information_collector = InformationCollector()

    def get_or_create_conversation_state(self, conversation_id: int, user_id: int) -> FlexibleConversationState:
        """대화 상태 조회 또는 생성"""
        if conversation_id not in self.conversation_states:
            self.conversation_states[conversation_id] = FlexibleConversationState(conversation_id, user_id)
        return self.conversation_states[conversation_id]

    async def process_user_query(self, user_input: str, user_id: int, 
                          conversation_id: Optional[int] = None) -> Dict[str, Any]:
        """메인 쿼리 처리 함수"""
        return await self._process_user_query_async(user_input, user_id, conversation_id)

    async def _process_user_query_async(self, user_input: str, user_id: int, 
                                      conversation_id: Optional[int] = None) -> Dict[str, Any]:
        """비동기 사용자 쿼리 처리"""
        
        try:
            logger.info(f"[단계 로그] === 마케팅 쿼리 처리 시작 ===\n사용자 입력: {user_input[:50]}...\n사용자 ID: {user_id}\n대화 ID: {conversation_id}")
            
            # 대화 세션 처리
            logger.info("[단계 로그] 1. 대화 세션 처리 시작")
            session_info = get_or_create_conversation_session(user_id, conversation_id)
            conversation_id = session_info["conversation_id"]
            logger.info(f"[단계 로그] - 세션 처리 완료: {conversation_id}")
            
            # 대화 상태 조회/생성
            logger.info("[단계 로그] 2. 대화 상태 조회/생성")
            state = self.get_or_create_conversation_state(conversation_id, user_id)
            logger.info(f"[단계 로그] - 현재 단계: {state.current_stage.value}")
            
            # 사용자 메시지 저장
            with get_session_context() as db:
                create_message(db, conversation_id, "user", "marketing", user_input)
            
            # 대화 컨텍스트 준비
            logger.info("[단계 로그] 3. 대화 컨텍스트 준비")
            context = self.information_collector.prepare_conversation_context(
                user_id, conversation_id, self.conversation_states
            )
            logger.info(f"[단계 로그] - 컨텍스트 준비 완료: {context.get('business_type')}, {context.get('current_stage')}")
            
            # 1. LLM 기반 의도 분석
            logger.info("[단계 로그] 4. LLM 의도 분석 시작")
            intent_analysis = self.intent_analyzer.analyze_user_intent_with_llm(user_input, context)
            logger.info(f"[단계 로그] - 의도 분석 완료: {intent_analysis.get('response_type', '알 수 없음')}")
            
            # 2. 업종 감지 (필요시) 및 정보 업데이트
            logger.info("[단계 로그] 5. 업종 감지 및 정보 업데이트")
            
            # 첫 번째 대화에서 업종 감지 및 저장
            if context.get("business_type") and context["business_type"] != "일반":
                state.detected_business_type = context["business_type"]
                state.add_information("business_info_business_type", context["business_type"], "auto_detected")
                logger.info(f"[단계 로그] - 업종 정보 저장: {context['business_type']}")
            
            # 추가 추출 또는 LLM 기반 감지
            if intent_analysis.get("context_needs", {}).get("business_type_detection"):
                detected_type = self.intent_analyzer.detect_business_type_with_llm(user_input, context)
                if detected_type != "일반" and detected_type != state.detected_business_type:
                    state.detected_business_type = detected_type
                    state.add_information("business_info_business_type", detected_type, "llm_detected")
                    context["business_type"] = detected_type
            
            # 3. 진행 제어 명령 처리
            logger.info("[단계 로그] 6. 진행 제어 명령 처리")
            flow_control = intent_analysis.get("flow_control", {})
            control_command = flow_control.get("control_command", "none")
            stage_preference = flow_control.get("stage_preference")
            auto_stage_jump = flow_control.get("auto_stage_jump", False)
            
            logger.info(f"[단계 로그] - 제어 명령: {control_command}, 자동 단계 이동: {auto_stage_jump}")
            
            # 1. 진행 제어 명령 처리
            if control_command != "none":
                control_result = self.flow_controller.handle_flow_control(control_command, state, user_input)
                response_content = control_result["message"]
                
                if control_command == "skip" and "options" in control_result:
                    response_content += "\n\n선택 가능한 단계:\n" + "\n".join([f"• {opt}" for opt in control_result["options"]])
                
                return response_content
            
            # 2. 마케팅 툴 사용 필요성 검사 및 자동 단계 이동
            elif intent_analysis.get("response_type") == "tool_required" or intent_analysis.get("tool_requirements", {}).get("needs_tool"):
                logger.info("[단계 로그] 마케팅 툴 요청 처리 시작")
                
                tool_requirements = intent_analysis.get("tool_requirements", {})
                tool_type = tool_requirements.get("tool_type", "none")
                current_stage = context.get("current_stage", "any_question")
                
                # 콘텐츠 생성이 필요하고 현재 4단계가 아니면서 자동 이동 플래그가 true인 경우
                if tool_type == "content_generation" and current_stage != "stage_4_execution" and auto_stage_jump:
                    logger.info(f"[단계 로그] 콘텐츠 생성을 위해 4단계로 자동 이동: {current_stage} -> stage_4_execution")
                    
                    # 4단계로 이동
                    jump_result = self.flow_controller.jump_to_stage("4", state)
                    
                    if jump_result["success"]:
                        # 단계 이동 성공 후 툴 실행
                        logger.info("[단계 로그] 4단계 이동 성공, 툴 실행 진행")
                        context["current_stage"] = "stage_4_execution"  # 컨텍스트 업데이트
                        
                        tool_result = await self.tool_manager.execute_marketing_tool(user_input, intent_analysis, context)
                        logger.info(f"[단계 로그] 툴 실행 완료: {tool_result.get('success', False)}")
                        
                        # 자연스러운 단계 이동 메시지 생성
                        content_type_kr = {
                            "instagram": "인스타그램 콘텐츠",
                            "blog": "블로그 콘텐츠", 
                            "general": "마케팅 콘텐츠"
                        }.get(tool_requirements.get("content_type", "general"), "콘텐츠")
                        
                        stage_move_msg = f"🚀 **마케팅 실행 단계로 이동!**\n\n"
                        stage_move_msg += f"'{user_input}'에 대한 요청을 처리하기 위해 4단계(실행 계획)로 이동했습니다.\n\n"
                        stage_move_msg += f"이제 {content_type_kr} 생성을 시작하겠습니다!\n\n"
                        
                        # 툴 결과를 포함한 응답 생성
                        tool_response = await self.tool_manager.generate_response_with_tool_result(
                            user_input, intent_analysis, context, tool_result
                        )
                        
                        return stage_move_msg + tool_response
                    else:
                        # 단계 이동 실패
                        return f"🚫 단계 이동에 실패했습니다: {jump_result.get('message', '알 수 없는 오류')}"
                else:
                    # 일반 툴 실행 (단계 이동 불필요)
                    logger.info("[단계 로그] 일반 마케팅 툴 실행")
                    tool_result = await self.tool_manager.execute_marketing_tool(user_input, intent_analysis, context)
                    logger.info(f"[단계 로그] 툴 실행 완료: {tool_result.get('success', False)}")
                    
                    # 툴 결과를 포함한 응답 생성
                    return await self.tool_manager.generate_response_with_tool_result(
                        user_input, intent_analysis, context, tool_result
                    )
                    
            # 3. 수동 단계 이동 처리
            elif stage_preference and stage_preference != "any" and stage_preference != "none":
                logger.info("[단계 로그] 수동 단계 이동 처리")
                jump_result = self.flow_controller.jump_to_stage(stage_preference, state)
                
                if jump_result["success"]:
                    return jump_result["message"]
                else:
                    return jump_result["message"]
            
            # 4. 일반 응답 생성
            else:
                try:
                    logger.info("[단계 로그] 일반 응답 생성 시작")
                    response_content = self.response_generator.generate_contextual_response(
                        user_input, intent_analysis, context
                    )
                    logger.info("[단계 로그] 응답 생성 완료")
                    
                    # 다음 액션 결정
                    next_action = self.response_generator.determine_next_action(
                        user_input, intent_analysis, context
                    )
                    
                    # 사용자 옵션 추가
                    if next_action and next_action.get("user_options"):
                        options_text = "\n\n💡 **다음 옵션:**\n" + "\n".join([f"• {opt}" for opt in next_action["user_options"]])
                        response_content += options_text
                        
                except Exception as e:
                    logger.error(f"응답 생성 중 오류 발생: {e}")
                    response_content = "마케팅 질문에 대한 조언을 준비 중입니다. 조금 더 구체적으로 알려주시면 도움을 드릴 수 있습니다."
            
            # 정보 수집 및 업데이트
            logger.info("[단계 로그] 10. 정보 수집 및 업데이트")
            self.information_collector.update_collected_information(user_input, intent_analysis, state)
            logger.info(f"[단계 로그] - 수집된 정보 수: {len(state.collected_info)}")
            
            # 응답 메시지 저장
            insert_message_raw(
                conversation_id=conversation_id,
                sender_type="agent",
                agent_type="marketing",
                content=response_content
            )
            
            # 표준 응답 형식으로 반환
            logger.info("[단계 로그] === 마케팅 쿼리 처리 완료 ===")
            return create_marketing_response(
                conversation_id=conversation_id,
                answer=response_content,
                topics=[],
                sources="LLM 기반 유연한 마케팅 시스템",
                intent=intent_analysis.get("response_type", "flexible"),
                confidence=0.9,
                conversation_stage=state.current_stage.value,
                completion_rate=state.get_overall_completion_rate(),
                collected_info=state.collected_info,
                mcp_results={},
                multiturn_flow=True,
                flexible_mode=True,
                intent_analysis=intent_analysis
            )
            
        except Exception as e:
            logger.error(f"LLM 기반 마케팅 쿼리 처리 실패: {e}")
            return create_error_response(
                error_message=f"마케팅 상담 처리 중 오류가 발생했습니다: {str(e)}",
                error_code="LLM_MARKETING_ERROR"
            )

    def get_conversation_status(self, conversation_id: int) -> Dict[str, Any]:
        """대화 상태 조회"""
        if conversation_id in self.conversation_states:
            state = self.conversation_states[conversation_id]
            return {
                "conversation_id": conversation_id,
                "current_stage": state.current_stage.value,
                "overall_completion": state.get_overall_completion_rate(),
                "collected_info_count": len(state.collected_info),
                "detected_business_type": state.detected_business_type,
                "is_paused": getattr(state, 'is_paused', False),
                "is_completed": state.current_stage == MarketingStage.COMPLETED,
                "last_updated": state.updated_at.isoformat(),
                "flexible_mode": True
            }
        else:
            return {"error": "대화를 찾을 수 없습니다"}

    def reset_conversation(self, conversation_id: int) -> bool:
        """대화 초기화"""
        if conversation_id in self.conversation_states:
            del self.conversation_states[conversation_id]
            return True
        return False

    def get_agent_status(self) -> Dict[str, Any]:
        """마케팅 에이전트 상태 반환"""
        return {
            "agent_type": "llm_based_flexible_marketing",
            "version": "6.0.0",
            "conversation_system": "llm_powered_flexible",
            "features": [
                "순서 무관 즉시 응답",
                "중간 단계부터 시작", 
                "단계 건너뛰기",
                "LLM 기반 의도 분석",
                "컨텍스트 기반 개인화",
                "마케팅 툴 자동 활용"
            ],
            "active_conversations": len(self.conversation_states),
            "conversation_stages": {
                conv_id: state.current_stage.value 
                for conv_id, state in self.conversation_states.items()
            },
            "llm_status": self.llm_manager.get_status() if hasattr(self.llm_manager, 'get_status') else "active",
            "vector_store_status": self.vector_manager.get_status() if hasattr(self.vector_manager, 'get_status') else "active",
            "flexible_features": {
                "immediate_response": True,
                "stage_jumping": True,
                "flow_control": True,
                "context_awareness": True,
                "marketing_tools": bool(self.tool_manager.analysis_tools)
            },
            "architecture": {
                "modules": [
                    "IntentAnalyzer",
                    "ResponseGenerator", 
                    "ToolManager",
                    "FlowController",
                    "InformationCollector"
                ],
                "modular_design": True,
                "separation_of_concerns": True
            },
            "available_tools": {
                "trend_analysis": {
                    "description": "네이버 검색 트렌드 분석",
                    "stage_requirement": "모든 단계"
                },
                "hashtag_analysis": {
                    "description": "인스타그램 해시태그 분석",
                    "stage_requirement": "모든 단계"
                },
                "content_generation": {
                    "description": "블로그/SNS 콘텐츠 생성",
                    "stage_requirement": "4단계(실행 계획)만"
                },
                "keyword_research": {
                    "description": "SEO 키워드 연구",
                    "stage_requirement": "모든 단계"
                }
            },
            "tool_stage_restrictions": {
                "content_generation": "stage_4_execution",
                "reason": "콘텐츠 생성은 마케팅 전략 및 타겟이 명확해진 후 실행 단계에서 수행되어야 함"
            }
        }


# 전역 인스턴스
_enhanced_marketing_manager = None

def get_enhanced_4stage_marketing_manager() -> Enhanced4StageMarketingManager:
    """개선된 4단계 마케팅 매니저 인스턴스 반환"""
    global _enhanced_marketing_manager
    if _enhanced_marketing_manager is None:
        _enhanced_marketing_manager = Enhanced4StageMarketingManager()
    return _enhanced_marketing_manager
