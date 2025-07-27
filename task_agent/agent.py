"""
Task Agent 핵심 에이전트 v5
리팩토링된 업무지원 에이전트
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# 공통 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "../shared_modules"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../unified_agent_system"))

from models import UserQuery, AutomationRequest, PersonaType
try:
    from core.models import UnifiedResponse, AgentType, RoutingDecision, Priority
except ImportError:
    # 공통 모듈이 없는 경우 더미 클래스들
    class AgentType:
        TASK_AUTOMATION = "task_automation"
    
    class Priority:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
    
    class RoutingDecision:
        def __init__(self, agent_type, confidence, reasoning, keywords, priority):
            self.agent_type = agent_type
            self.confidence = confidence
            self.reasoning = reasoning
            self.keywords = keywords
            self.priority = priority
    
    class UnifiedResponse:
        def __init__(self, conversation_id, agent_type, response, confidence, 
                     routing_decision, sources, metadata, processing_time, timestamp, alternatives):
            self.conversation_id = conversation_id
            self.agent_type = agent_type
            self.response = response
            self.confidence = confidence
            self.routing_decision = routing_decision
            self.sources = sources
            self.metadata = metadata
            self.processing_time = processing_time
            self.timestamp = timestamp
            self.alternatives = alternatives

from utils import TaskAgentLogger

# 공통 모듈 import
try:
    from utils import create_success_response, create_error_response
    from utils import get_or_create_conversation_session
except ImportError:
    def create_success_response(data, message="Success"):
        return {"success": True, "data": data, "message": message}
    
    def create_error_response(message, error_code="ERROR"):
        return {"success": False, "error": message, "error_code": error_code}
        
    def get_or_create_conversation_session(user_id, conversation_id):
        return {"conversation_id": conversation_id or 1}

# 서비스 레이어 import
from services.llm_service import LLMService
from services.rag_service import RAGService
from services.automation_service import AutomationService
from services.conversation_service import ConversationService

logger = logging.getLogger(__name__)

class TaskAgent:
    """Task Agent 핵심 클래스 (리팩토링됨)"""
    
    def __init__(self, llm_service: LLMService, rag_service: RAGService, 
                 automation_service: AutomationService, conversation_service: ConversationService):
        """에이전트 초기화 - 의존성 주입"""
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.automation_service = automation_service
        self.conversation_service = conversation_service
        
        logger.info("Task Agent v5 초기화 완료 (의존성 주입)")

    async def process_query(self, query: UserQuery) -> UnifiedResponse:
        """사용자 쿼리 처리 - 단순화된 워크플로우"""
        try:
            TaskAgentLogger.log_user_interaction(
                user_id=query.user_id,
                action="query_processing_start",
                details=f"persona: {query.persona}, message_length: {len(query.message)}"
            )
            
            # 1. 대화 세션 처리
            session_info = await self._ensure_conversation_session(query)
            query.conversation_id = session_info["conversation_id"]
            
            # 2. 대화 히스토리 조회
            conversation_history = await self.conversation_service.get_history(query.conversation_id)
            
            # 3. 사용자 메시지 저장
            await self.conversation_service.save_message(
                query.conversation_id, query.message, "user"
            )
            
            # 4. 의도 분석
            intent_analysis = await self.llm_service.analyze_intent(
                query.message, query.persona, conversation_history
            )
            
            # 5. 워크플로우 결정 및 처리
            response = await self._route_and_process(query, intent_analysis, conversation_history)
            
            # 6. 에이전트 응답 저장
            await self.conversation_service.save_message(
                query.conversation_id, response.response, "agent", "task_agent"
            )
            
            TaskAgentLogger.log_user_interaction(
                user_id=query.user_id,
                action="query_processing_completed",
                details=f"intent: {response.metadata.get('intent', 'unknown')}"
            )
            
            return response
                
        except Exception as e:
            logger.error(f"쿼리 처리 실패: {e}")
            return self._create_error_response(query, str(e))

    async def _ensure_conversation_session(self, query: UserQuery) -> Dict[str, Any]:
        """대화 세션 확보"""
        try:
            user_id_int = int(query.user_id)
            session_info = get_or_create_conversation_session(
                user_id_int, query.conversation_id
            )
            return session_info
        except Exception as e:
            logger.error(f"대화 세션 처리 실패: {e}")
            raise Exception("대화 세션 생성에 실패했습니다")

    async def _route_and_process(self, query: UserQuery, intent_analysis: Dict, 
                                conversation_history: List[Dict] = None) -> UnifiedResponse:
        """워크플로우 라우팅 및 처리"""
        try:
            # 자동화 의도 확인
            automation_intent = await self.llm_service.analyze_automation_intent(
                query.message, conversation_history
            )
            
            if automation_intent["is_automation"]:
                # 자동화 워크플로우
                return await self._handle_automation_workflow(
                    query, automation_intent, intent_analysis, conversation_history
                )
            else:
                # 일반 상담 워크플로우
                return await self._handle_consultation_workflow(
                    query, intent_analysis, conversation_history
                )
                
        except Exception as e:
            logger.error(f"워크플로우 라우팅 실패: {e}")
            return self._create_error_response(query, str(e))

    async def _handle_automation_workflow(self, query: UserQuery, automation_intent: Dict,
                                        intent_analysis: Dict, conversation_history: List[Dict] = None) -> UnifiedResponse:
        """자동화 워크플로우 처리"""
        try:
            automation_type = automation_intent["automation_type"]
            
            # publish_sns 타입은 마케팅 페이지로 리다이렉션
            if automation_type == "publish_sns":
                return self._create_marketing_redirect_response(query, intent_analysis)
            
            # 현재 메시지에서 자동화 정보 추출
            extracted_info = await self.llm_service.extract_automation_info(
                query.message, automation_type, conversation_history
            )
            
            # 필수 정보 체크
            missing_fields = self._check_missing_fields(extracted_info, automation_type)
            
            if not missing_fields:
                # 모든 정보가 있으면 자동화 작업 등록
                return await self._register_automation_task(
                    query, automation_type, extracted_info, intent_analysis
                )
            else:
                # 부족한 정보 요청
                return self._request_missing_info(
                    query, automation_type, extracted_info, missing_fields, intent_analysis
                )
            
        except Exception as e:
            logger.error(f"자동화 워크플로우 처리 실패: {e}")
            return self._create_error_response(query, str(e))

    async def _handle_consultation_workflow(self, query: UserQuery, intent_analysis: Dict,
                                          conversation_history: List[Dict] = None) -> UnifiedResponse:
        """일반 상담 워크플로우 처리"""
        try:
            # 지식 검색
            search_result = await self.rag_service.search_knowledge(
                query.message, query.persona, intent_analysis.get("intent")
            )
            
            # 응답 생성
            response_text = await self.llm_service.generate_response(
                query.message, query.persona, intent_analysis["intent"], 
                search_result.get("context", ""), conversation_history
            )
            
            # 응답 생성
            return self._create_consultation_response(
                query, response_text, intent_analysis, search_result
            )
            
        except Exception as e:
            logger.error(f"상담 워크플로우 처리 실패: {e}")
            return self._create_error_response(query, str(e))

    async def _register_automation_task(self, query: UserQuery, automation_type: str,
                                      extracted_info: Dict[str, Any], intent_analysis: Dict) -> UnifiedResponse:
        """자동화 작업 등록"""
        try:
            # 자동화 요청 생성
            automation_request = AutomationRequest(
                user_id=int(query.user_id),
                task_type=automation_type,
                title=self._generate_automation_title(automation_type, extracted_info),
                task_data=extracted_info,
                scheduled_at=extracted_info.get("scheduled_at")
            )
            
            # 자동화 서비스를 통해 작업 등록 (스케쥴링 포함)
            automation_response = await self.automation_service.create_task(automation_request)
            
            # 성공 응답 생성
            success_message = self._create_automation_success_message(
                automation_type, automation_response, extracted_info
            )
            
            return self._create_automation_response(
                query, success_message, intent_analysis, 
                automation_response.task_id, automation_type, True
            )
            
        except Exception as e:
            logger.error(f"자동화 작업 등록 실패: {e}")
            return self._create_error_response(query, f"자동화 작업 등록 실패: {str(e)}")

    def _check_missing_fields(self, extracted_info: Dict[str, Any], automation_type: str) -> List[str]:
        """필수 필드 체크"""
        required_fields = {
            "schedule_calendar": ["title", "start_time"],
            "send_email": ["to_emails", "subject", "body"],
            "send_reminder": ["message", "remind_time"],
            "send_message": ["platform", "content"]
        }
        
        required = required_fields.get(automation_type, [])
        missing = []
        
        for field in required:
            if not extracted_info.get(field):
                missing.append(field)
        
        return missing

    def _generate_automation_title(self, automation_type: str, extracted_info: Dict[str, Any]) -> str:
        """자동화 작업 제목 생성"""
        titles = {
            "schedule_calendar": lambda info: info.get("title", "일정 등록"),
            "send_email": lambda info: f"이메일: {info.get('subject', '제목 없음')}",
            "send_reminder": lambda info: f"리마인더: {info.get('message', '알림')}",
            "send_message": lambda info: f"{info.get('platform', '메시지')} 발송"
        }
        
        title_func = titles.get(automation_type, lambda info: "자동화 작업")
        return title_func(extracted_info)

    def _create_automation_success_message(self, automation_type: str, 
                                         automation_response, extracted_info: Dict[str, Any]) -> str:
        """자동화 성공 메시지 생성"""
        type_names = {
            "schedule_calendar": "일정 등록",
            "send_email": "이메일 발송",
            "send_reminder": "리마인더",
            "send_message": "메시지 발송"
        }
        
        type_name = type_names.get(automation_type, "자동화 작업")
        
        message = f"✅ {type_name} 자동화가 성공적으로 등록되었습니다!\n\n"
        message += f"📋 **작업 정보:**\n"
        message += f"• 작업 ID: {automation_response.task_id}\n"
        message += f"• 상태: {automation_response.status.value}\n"
        
        if hasattr(automation_response, 'scheduled_time') and automation_response.scheduled_time:
            message += f"• 예약 시간: {automation_response.scheduled_time.strftime('%Y-%m-%d %H:%M')}\n"
        
        message += f"\n📝 **등록된 내용:**\n"
        message += self._format_extracted_info(extracted_info, automation_type)
        
        if hasattr(automation_response, 'scheduled_time') and automation_response.scheduled_time:
            message += f"\n⏰ 예약된 시간에 자동으로 실행됩니다."
        else:
            message += f"\n🚀 즉시 실행됩니다."
        
        return message

    def _format_extracted_info(self, extracted_info: Dict[str, Any], automation_type: str) -> str:
        """추출된 정보 포맷팅"""
        field_labels = {
            "schedule_calendar": {
                "title": "제목", "start_time": "시작시간", "end_time": "종료시간",
                "description": "설명", "attendees": "참석자"
            },
            "send_email": {
                "to_emails": "받는사람", "subject": "제목", "body": "내용",
                "attachments": "첨부파일"
            },
            "send_reminder": {
                "message": "메시지", "remind_time": "알림시간"
            },
            "send_message": {
                "platform": "플랫폼", "channel": "채널", "content": "내용"
            }
        }
        
        labels = field_labels.get(automation_type, {})
        formatted = ""
        
        for field, value in extracted_info.items():
            if value and field in labels:
                label = labels[field]
                if isinstance(value, list):
                    value_str = ", ".join(str(v) for v in value)
                else:
                    value_str = str(value)
                formatted += f"• {label}: {value_str}\n"
        
        return formatted

    def _request_missing_info(self, query: UserQuery, automation_type: str,
                            extracted_info: Dict[str, Any], missing_fields: List[str],
                            intent_analysis: Dict) -> UnifiedResponse:
        """부족한 정보 요청"""
        type_names = {
            "schedule_calendar": "일정 등록",
            "send_email": "이메일 발송", 
            "send_reminder": "리마인더",
            "send_message": "메시지 발송"
        }
        
        type_name = type_names.get(automation_type, "자동화")
        
        message = f"📝 {type_name} 설정을 도와드리겠습니다.\n\n"
        
        # 이미 입력된 정보가 있으면 표시
        if extracted_info:
            message += "✅ **확인된 정보:**\n"
            message += self._format_extracted_info(extracted_info, automation_type)
            message += "\n"
        
        # 부족한 정보 요청
        message += "❓ **추가로 필요한 정보:**\n"
        message += self._get_missing_fields_template(automation_type, missing_fields)
        
        return self._create_automation_response(
            query, message, intent_analysis, None, automation_type, False
        )

    def _get_missing_fields_template(self, automation_type: str, missing_fields: List[str]) -> str:
        """부족한 필드 템플릿"""
        templates = {
            "schedule_calendar": {
                "title": "• 일정 제목을 알려주세요",
                "start_time": "• 시작 시간을 알려주세요 (예: 내일 오후 2시, 2024-01-15 14:00)"
            },
            "send_email": {
                "to_emails": "• 받는 사람 이메일을 알려주세요",
                "subject": "• 이메일 제목을 알려주세요", 
                "body": "• 이메일 내용을 알려주세요"
            },
            "send_reminder": {
                "message": "• 리마인더 메시지를 알려주세요",
                "remind_time": "• 알림 시간을 알려주세요"
            },
            "send_message": {
                "platform": "• 플랫폼을 알려주세요 (Slack, Teams 등)",
                "content": "• 메시지 내용을 알려주세요"
            }
        }
        
        type_templates = templates.get(automation_type, {})
        
        result = ""
        for field in missing_fields:
            if field in type_templates:
                result += type_templates[field] + "\n"
        
        result += "\n💡 자연스럽게 말씀해주시면 자동으로 인식합니다!"
        return result

    # ===== 응답 생성 메서드들 =====

    def _create_marketing_redirect_response(self, query: UserQuery, intent_analysis: Dict) -> UnifiedResponse:
        """마케팅 페이지 리다이렉션 응답"""
        routing_decision = RoutingDecision(
            agent_type=AgentType.TASK_AUTOMATION,
            confidence=1.0,
            reasoning="SNS 마케팅 페이지로 리다이렉션",
            keywords=["marketing", "sns"],
            priority=Priority.HIGH
        )
        
        return UnifiedResponse(
            conversation_id=int(query.conversation_id) if query.conversation_id else 0,
            agent_type=AgentType.TASK_AUTOMATION,
            response="SNS 마케팅 기능을 이용하시려면 마케팅 페이지로 이동해주세요.\n\n[마케팅 페이지로 이동하기](/marketing)",
            confidence=1.0,
            routing_decision=routing_decision,
            sources=None,
            metadata={
                "redirect": "/marketing",
                "automation_type": "publish_sns",
                "intent": intent_analysis["intent"],
                "automation_created": False
            },
            processing_time=0.0,
            timestamp=datetime.now(),
            alternatives=[]
        )

    def _create_consultation_response(self, query: UserQuery, response_text: str,
                                    intent_analysis: Dict, search_result: Dict) -> UnifiedResponse:
        """일반 상담 응답"""
        routing_decision = RoutingDecision(
            agent_type=AgentType.TASK_AUTOMATION,
            confidence=intent_analysis.get("confidence", 0.8),
            reasoning=f"일반 상담: {intent_analysis['intent']}",
            keywords=intent_analysis.get("keywords", []),
            priority=Priority.MEDIUM
        )
        
        return UnifiedResponse(
            conversation_id=int(query.conversation_id) if query.conversation_id else 0,
            agent_type=AgentType.TASK_AUTOMATION,
            response=response_text,
            confidence=intent_analysis.get("confidence", 0.8),
            routing_decision=routing_decision,
            sources=search_result.get("sources", ""),
            metadata={
                "intent": intent_analysis["intent"],
                "persona": query.persona.value,
                "automation_created": False
            },
            processing_time=0.0,
            timestamp=datetime.now(),
            alternatives=[]
        )

    def _create_automation_response(self, query: UserQuery, message: str, intent_analysis: Dict,
                                  task_id: Optional[int], automation_type: str, 
                                  automation_created: bool) -> UnifiedResponse:
        """자동화 관련 응답"""
        routing_decision = RoutingDecision(
            agent_type=AgentType.TASK_AUTOMATION,
            confidence=intent_analysis.get("confidence", 0.9),
            reasoning=f"자동화 처리: {automation_type}",
            keywords=[automation_type],
            priority=Priority.HIGH if automation_created else Priority.MEDIUM
        )
        
        metadata = {
            "intent": intent_analysis["intent"],
            "automation_type": automation_type,
            "automation_created": automation_created
        }
        
        if task_id:
            metadata["task_id"] = task_id
        
        return UnifiedResponse(
            conversation_id=int(query.conversation_id) if query.conversation_id else 0,
            agent_type=AgentType.TASK_AUTOMATION,
            response=message,
            confidence=intent_analysis.get("confidence", 0.9),
            routing_decision=routing_decision,
            sources=None,
            metadata=metadata,
            processing_time=0.0,
            timestamp=datetime.now(),
            alternatives=[]
        )

    def _create_error_response(self, query: UserQuery, error_message: str) -> UnifiedResponse:
        """에러 응답"""
        routing_decision = RoutingDecision(
            agent_type=AgentType.TASK_AUTOMATION,
            confidence=0.0,
            reasoning="처리 중 오류 발생",
            keywords=[],
            priority=Priority.MEDIUM
        )
        
        return UnifiedResponse(
            conversation_id=int(query.conversation_id) if query.conversation_id else 0,
            agent_type=AgentType.TASK_AUTOMATION,
            response="죄송합니다. 요청을 처리하는 중에 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            confidence=0.0,
            routing_decision=routing_decision,
            sources=None,
            metadata={"error": error_message, "automation_created": False},
            processing_time=0.0,
            timestamp=datetime.now(),
            alternatives=[]
        )

    # ===== 시스템 관리 =====

    async def get_status(self) -> Dict[str, Any]:
        """에이전트 상태 조회"""
        try:
            return {
                "agent_version": "5.0.0",
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "llm_service": await self.llm_service.get_status(),
                    "rag_service": await self.rag_service.get_status(),
                    "automation_service": await self.automation_service.get_status(),
                    "conversation_service": await self.conversation_service.get_status()
                }
            }
        except Exception as e:
            logger.error(f"상태 조회 실패: {e}")
            return {
                "agent_version": "5.0.0",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def cleanup_resources(self):
        """리소스 정리"""
        try:
            await self.automation_service.cleanup()
            await self.rag_service.cleanup()
            await self.llm_service.cleanup()
            logger.info("Task Agent 리소스 정리 완료")
        except Exception as e:
            logger.error(f"리소스 정리 실패: {e}")
