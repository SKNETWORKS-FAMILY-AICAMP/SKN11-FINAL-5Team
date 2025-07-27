"""
Task Agent 핵심 에이전트 v4
공통 모듈을 활용한 업무지원 에이전트
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# 공통 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "../shared_modules"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../unified_agent_system"))

from models import UserQuery, AutomationRequest, AutomationResponse, PersonaType, IntentType
from core.models import UnifiedResponse, AgentType, RoutingDecision, Priority
from llm_handler import TaskAgentLLMHandler
from rag import TaskAgentRAGManager
from automation import AutomationManager
from utils import task_cache, generate_conversation_id, TaskAgentLogger, TaskAgentResponseFormatter

# 공통 모듈 import
from utils import create_success_response, create_error_response

logger = logging.getLogger(__name__)

class TaskAgent:
    """Task Agent 핵심 클래스 (공통 모듈 기반)"""
    
    def __init__(self):
        """에이전트 초기화"""
        try:
            # 핵심 컴포넌트 초기화
            self.llm_handler = TaskAgentLLMHandler()
            self.rag_manager = TaskAgentRAGManager()
            self.automation_manager = AutomationManager()
            
            logger.info("Task Agent v4 초기화 완료 (공통 모듈 기반)")
            
        except Exception as e:
            logger.error(f"Task Agent 초기화 실패: {e}")
            raise

    async def process_query(self, query: UserQuery, conversation_history: List[Dict] = None) -> UnifiedResponse:
        """사용자 쿼리 처리"""
        try:
            TaskAgentLogger.log_user_interaction(
                user_id=query.user_id,
                action="query_processing_start",
                details=f"persona: {query.persona}, message_length: {len(query.message)}"
            )
            
            # 의도 분석
            intent_analysis = await self.llm_handler.analyze_intent(
                query.message, query.persona, conversation_history
            )
            
            TaskAgentLogger.log_user_interaction(
                user_id=query.user_id,
                action="intent_analyzed",
                details=f"intent: {intent_analysis['intent']}, confidence: {intent_analysis['confidence']}"
            )
            
            # 자동화 요청인지 확인
            automation_type = await self.llm_handler.classify_automation_intent(query.message)
            
            # 워크플로우 결정 - 개선된 로직
            if automation_type:
                # 자동화 타입이 감지되면 스마트 처리
                response = await self._handle_smart_automation_workflow(
                    query, automation_type, intent_analysis, conversation_history
                )
            else:
                response = await self._handle_consultation_workflow(
                    query, intent_analysis, conversation_history
                )
            
            TaskAgentLogger.log_user_interaction(
                user_id=query.user_id,
                action="query_processing_completed",
                details=f"response_length: {len(response.response)}, intent: {response.metadata.get('intent', 'unknown')}"
            )
            
            return response
                
        except Exception as e:
            logger.error(f"쿼리 처리 실패: {e}")
            TaskAgentLogger.log_user_interaction(
                user_id=query.user_id,
                action="query_processing_failed",
                details=f"error: {str(e)}"
            )
            
            # UnifiedResponse 형식으로 에러 응답 생성
            routing_decision = RoutingDecision(
                agent_type=AgentType.TASK_AUTOMATION,
                confidence=0.0,
                reasoning="Error occurred during processing",
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
                metadata={"error": str(e)},
                processing_time=0.0,
                timestamp=datetime.now(),
                alternatives=[]
            )

    async def _handle_consultation_workflow(self, query: UserQuery, intent_analysis: Dict, 
                                          conversation_history: List[Dict] = None) -> UnifiedResponse:
        """상담 워크플로우 처리"""
        try:
            # 지식 검색
            search_result = await self.rag_manager.search_knowledge(
                query.message, query.persona, intent_analysis.get("intent")
            )
            
            # 컨텍스트 구성
            context = ""
            if search_result.chunks:
                context_chunks = []
                for chunk in search_result.chunks[:3]:  # 최대 3개 청크 사용
                    context_chunks.append(chunk.content)
                context = "\n\n".join(context_chunks)
            
            # 응답 생성
            response_text = await self.llm_handler.generate_response(
                query.message, query.persona, intent_analysis["intent"], context, conversation_history
            )
            
            # 후속 액션 생성
            # actions = self._generate_follow_up_actions(intent_analysis["intent"], query.persona)
            
            # UnifiedResponse 형식으로 응답 생성
            routing_decision = RoutingDecision(
                agent_type=AgentType.TASK_AUTOMATION,
                confidence=intent_analysis.get("confidence", 0.5),
                reasoning=f"Intent: {intent_analysis['intent']}",
                keywords=intent_analysis.get("keywords", []),
                priority=Priority.MEDIUM
            )
            
            return UnifiedResponse(
                conversation_id=int(query.conversation_id) if query.conversation_id else 0,
                agent_type=AgentType.TASK_AUTOMATION,
                response=response_text,
                confidence=intent_analysis.get("confidence", 0.5),
                routing_decision=routing_decision,
                sources=", ".join(search_result.sources) if search_result and search_result.sources else None,
                metadata={
                    "actions": actions,
                    "intent": intent_analysis["intent"],
                    "persona": query.persona.value
                },
                processing_time=0.0,
                timestamp=datetime.now(),
                alternatives=[]
            )
            
        except Exception as e:
            logger.error(f"상담 워크플로우 처리 실패: {e}")
            
    def _check_if_automation_data(self, message: str, conversation_history: List[Dict] = None) -> bool:
        """입력된 데이터가 자동화 포맷에 맞는지 확인"""
        try:
            # 대화 이력에서 마지막 메시지가 포맷 제공이었는지 확인
            if not conversation_history:
                return False
                
            # 마지막 어시스턴트 응답에서 포맷 제공 여부 확인
            last_assistant_message = None
            for msg in reversed(conversation_history):
                if msg.get('role') == 'assistant':
                    last_assistant_message = msg.get('content', '')
                    break
            
            if not last_assistant_message:
                return False
                
            # 포맷 제공 메시지인지 확인
            format_indicators = [
                "정보를 알려주세요",
                "탬플릿",
                "예시:",
                "제목:",
                "날짜:",
                "시간:",
                "내용:",
                "플랫폼:",
                "받는사람:"
            ]
            
            has_format_in_last_message = any(indicator in last_assistant_message for indicator in format_indicators)
            
            if not has_format_in_last_message:
                return False
                
            # 현재 메시지가 포맷에 맞는 데이터인지 확인
            structured_data_patterns = [
                r'제목[:\s]*(.+)',
                r'날짜[:\s]*(.+)',
                r'시간[:\s]*(.+)',
                r'내용[:\s]*(.+)',
                r'플랫폼[:\s]*(.+)',
                r'받는사람[:\s]*(.+)',
                r'주제[:\s]*(.+)'
            ]
            
            import re
            for pattern in structured_data_patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return True
                    
            # 일정 등록 패턴 확인 ("내일 오후 2시에 회의" 같은 형태)
            time_patterns = [
                r'\d{1,2}시',
                r'\d{1,2}:\d{2}',
                r'내일|모레|다음주',
                r'\d{4}-\d{2}-\d{2}',
                r'오전|오후'
            ]
            
            has_time_info = any(re.search(pattern, message) for pattern in time_patterns)
            
            # 이메일 패턴 확인
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            has_email = re.search(email_pattern, message)
            
            return has_time_info or bool(has_email)
            
        except Exception as e:
            logger.error(f"자동화 데이터 확인 실패: {e}")
            return False
    
    async def _provide_automation_format(self, query: UserQuery, automation_type: str, 
                                       intent_analysis: Dict) -> UnifiedResponse:
        """자동화 타입에 따른 포맷 제공"""
        try:
            # publish_sns 타입인 경우 마케팅 페이지로 리다이렉션
            if automation_type == "publish_sns":
                routing_decision = RoutingDecision(
                    agent_type=AgentType.TASK_AUTOMATION,
                    confidence=1.0,
                    reasoning="Redirecting to marketing page for SNS publishing",
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
                        "automation_type": automation_type,
                        "intent": intent_analysis["intent"]
                    },
                    processing_time=0.0,
                    timestamp=datetime.now(),
                    alternatives=[]
                )
            
            # 다른 자동화 타입에 대한 기존 로직
            template = self._get_automation_template(automation_type)
            
            # 사용자 컨텍스트에 맞는 안내 메시지 추가
            context_message = f"안녕하세요! {automation_type} 자동화를 설정해드리겠습니다. \n\n"
            context_message += "아래 포맷에 맞춰 정보를 입력해주세요:\n\n"
            
            full_response = context_message + template
            
            routing_decision = RoutingDecision(
                agent_type=AgentType.TASK_AUTOMATION,
                confidence=intent_analysis.get("confidence", 0.8),
                reasoning=f"Providing automation format for: {automation_type}",
                keywords=intent_analysis.get("keywords", []),
                priority=Priority.MEDIUM
            )
            
            return UnifiedResponse(
                conversation_id=int(query.conversation_id) if query.conversation_id else 0,
                agent_type=AgentType.TASK_AUTOMATION,
                response=full_response,
                confidence=intent_analysis.get("confidence", 0.8),
                routing_decision=routing_decision,
                sources=None,
                metadata={
                    "automation_type": automation_type,
                    "intent": intent_analysis["intent"],
                    "actions": [{
                        "type": "automation_format_provided",
                        "data": {"automation_type": automation_type},
                        "description": f"{automation_type} 자동화 포맷이 제공되었습니다."
                    }]
                },
                processing_time=0.0,
                timestamp=datetime.now(),
                alternatives=[])
            
        except Exception as e:
            logger.error(f"자동화 포맷 제공 실패: {e}")
    
    async def _save_automation_task(self, query: UserQuery, intent_analysis: Dict,
                                  conversation_history: List[Dict] = None) -> UnifiedResponse:
        """포맷에 맞는 데이터를 DB에 저장"""
        try:
            # 대화 이력에서 자동화 타입 추출
            automation_type = self._extract_automation_type_from_history(conversation_history)
            
            if not automation_type:
                # 자동화 타입을 다시 추출 시도
                automation_type = await self.llm_handler.classify_automation_intent(query.message)
            
            if not automation_type:
                routing_decision = RoutingDecision(
                    agent_type=AgentType.TASK_AUTOMATION,
                    confidence=0.3,
                    reasoning="자동화 타입 파악 실패",
                    keywords=[],
                    priority="medium"
                )
                
                return UnifiedResponse(
                    conversation_id=int(query.conversation_id) if query.conversation_id else 0,
                    agent_type=AgentType.TASK_AUTOMATION,
                    response="자동화 타입을 파악할 수 없습니다. 다시 시도해주세요.",
                    confidence=0.3,
                    routing_decision=routing_decision,
                    sources=None,
                    metadata={"intent": intent_analysis["intent"]},
                    processing_time=0.0,
                    timestamp=datetime.now(),
                    alternatives=[]
                )
            
            # 정보 추출
            extraction_type = self._map_automation_to_extraction(automation_type)
            extracted_info = await self.llm_handler.extract_information(
                query.message, extraction_type, conversation_history
            )
            
            if not extracted_info or not self._validate_extracted_info(extracted_info, automation_type):
                routing_decision = RoutingDecision(
                    agent_type=AgentType.TASK_AUTOMATION,
                    confidence=0.4,
                    reasoning="필수 정보 누락",
                    keywords=[],
                    priority="medium"
                )
                
                return UnifiedResponse(
                    conversation_id=int(query.conversation_id) if query.conversation_id else 0,
                    agent_type=AgentType.TASK_AUTOMATION,
                    response="제공해주신 정보가 부족합니다. 필수 정보를 모두 입력해주세요.",
                    confidence=0.4,
                    routing_decision=routing_decision,
                    sources=None,
                    metadata={"intent": intent_analysis["intent"]},
                    processing_time=0.0,
                    timestamp=datetime.now(),
                    alternatives=[]
                )
            
            # 자동화 작업 생성 및 DB 저장
            automation_request = AutomationRequest(
                user_id=int(query.user_id),
                task_type=automation_type,
                title=self._generate_automation_title(automation_type, extracted_info),
                task_data=extracted_info
            )
            
            automation_response = await self.automation_manager.create_automation_task(automation_request)
            
            # 성공 메시지 생성
            success_message = f"✅ {automation_type} 자동화 작업이 성공적으로 등록되었습니다!\n\n"
            success_message += f"작업 ID: {automation_response.task_id}\n"
            success_message += f"제목: {automation_request.title}\n\n"
            success_message += "자동화 작업이 예약된 시간에 실행됩니다."
            
            routing_decision = RoutingDecision(
                agent_type=AgentType.TASK_AUTOMATION,
                confidence=intent_analysis.get("confidence", 0.9),
                reasoning="자동화 작업 저장 성공",
                keywords=[automation_type],
                priority=intent_analysis.get("urgency", "medium")
            )
            
            return UnifiedResponse(
                conversation_id=int(query.conversation_id) if query.conversation_id else 0,
                agent_type=AgentType.TASK_AUTOMATION,
                response=success_message,
                confidence=intent_analysis.get("confidence", 0.9),
                routing_decision=routing_decision,
                sources=None,
                metadata={
                    "intent": intent_analysis["intent"],
                    "task_id": automation_response.task_id,
                    "automation_type": automation_type,
                    "title": automation_request.title,
                    "action": "automation_saved"
                },
                processing_time=0.0,
                timestamp=datetime.now(),
                alternatives=[]
            )
            
        except Exception as e:
            logger.error(f"자동화 작업 저장 실패: {e}")
            routing_decision = RoutingDecision(
                agent_type=AgentType.TASK_AUTOMATION,
                confidence=0.3,
                reasoning="자동화 작업 저장 실패",
                keywords=[],
                priority="medium"
            )
            
            return UnifiedResponse(
                conversation_id=int(query.conversation_id) if query.conversation_id else 0,
                agent_type=AgentType.TASK_AUTOMATION,
                response="자동화 작업 저장 중 오류가 발생했습니다. 다시 시도해주세요.",
                confidence=0.3,
                routing_decision=routing_decision,
                sources=None,
                metadata={
                    "intent": intent_analysis["intent"],
                    "error": str(e)
                },
                processing_time=0.0,
                timestamp=datetime.now(),
                alternatives=[]
            )
    
    def _extract_automation_type_from_history(self, conversation_history: List[Dict] = None) -> str:
        """대화 이력에서 자동화 타입 추출"""
        try:
            if not conversation_history:
                return None
                
            # 마지막 몇 개 메시지에서 자동화 타입 찾기
            automation_types = {
                "schedule_calendar": ["일정", "캘린더", "회의", "예약"],
                "send_email": ["이메일", "메일", "발송"],
                "publish_sns": ["SNS", "소셜", "게시", "블로그", "인스타그램","포스팅", "컨텐츠", "키워드", "마케팅"],
                "send_reminder": ["리마인더", "알림", "알려주기"],
                "send_message": ["메시지", "슬랙", "Slack", "팀즈", "Teams"]
            }
            
            for msg in reversed(conversation_history[-5:]):  # 마지막 5개 메시지만 확인
                content = msg.get('content', '')
                for auto_type, keywords in automation_types.items():
                    if any(keyword in content for keyword in keywords):
                        return auto_type
                        
            return None
            
        except Exception as e:
            logger.error(f"자동화 타입 추출 실패: {e}")
            return None

    async def _handle_smart_automation_workflow(self, query: UserQuery, automation_type: str, 
                                              intent_analysis: Dict, conversation_history: List[Dict] = None) -> UnifiedResponse:
        """스마트 자동화 워크플로우 처리 - 개선된 로직"""
        try:
            # publish_sns 타입인 경우 마케팅 페이지로 리다이렉션
            if automation_type == "publish_sns":
                routing_decision = RoutingDecision(
                    agent_type=AgentType.TASK_AUTOMATION,
                    confidence=1.0,
                    reasoning="Redirecting to marketing page for SNS publishing",
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
                        "automation_type": automation_type,
                        "intent": intent_analysis["intent"]
                    },
                    processing_time=0.0,
                    timestamp=datetime.now(),
                    alternatives=[]
                )
            
            # 1. 현재 메시지와 대화 이력에서 정보 추출
            extraction_type = self._map_automation_to_extraction(automation_type)
            extracted_info = await self.llm_handler.extract_information(
                query.message, extraction_type, conversation_history
            )
            
            # 2. 대화 이력에서 추가 정보 수집
            if conversation_history:
                historical_info = await self._extract_info_from_history(
                    conversation_history, automation_type
                )
                # 기존 정보와 병합 (현재 메시지 우선)
                extracted_info = self._merge_extracted_info(extracted_info, historical_info)
            
            # 3. 필수 정보 확인 및 부족한 정보 식별
            missing_fields = self._identify_missing_fields(extracted_info, automation_type)
            
            if not missing_fields:
                # 모든 정보가 충족되면 자동화 작업 생성
                return await self._create_automation_task_directly(
                    query, automation_type, extracted_info, intent_analysis
                )
            else:
                # 부족한 정보만 요청
                return await self._request_missing_information(
                    query, automation_type, extracted_info, missing_fields, intent_analysis
                )
            
        except Exception as e:
            logger.error(f"스마트 자동화 워크플로우 처리 실패: {e}")
            return self._create_fallback_response(query, intent_analysis)

    async def _extract_info_from_history(self, conversation_history: List[Dict], automation_type: str) -> Dict[str, Any]:
        """대화 이력에서 자동화 관련 정보 추출"""
        try:
            # 전체 대화 내용을 하나의 텍스트로 결합
            full_conversation = ""
            for msg in conversation_history:
                if msg.get('role') == 'user':
                    full_conversation += msg.get('content', '') + " "
            
            # LLM을 사용하여 대화 이력에서 정보 추출
            extraction_type = self._map_automation_to_extraction(automation_type)
            historical_info = await self.llm_handler.extract_information(
                full_conversation, extraction_type, None
            )
            
            return historical_info or {}
            
        except Exception as e:
            logger.error(f"대화 이력 정보 추출 실패: {e}")
            return {}

    def _merge_extracted_info(self, current_info: Dict[str, Any], historical_info: Dict[str, Any]) -> Dict[str, Any]:
        """현재 정보와 이력 정보 병합 (현재 정보 우선)"""
        try:
            merged_info = historical_info.copy() if historical_info else {}
            
            # 현재 정보로 덮어쓰기 (현재 정보가 우선)
            if current_info:
                for key, value in current_info.items():
                    if value:  # 값이 있는 경우만 덮어쓰기
                        merged_info[key] = value
            
            return merged_info
            
        except Exception as e:
            logger.error(f"정보 병합 실패: {e}")
            return current_info or {}

    def _identify_missing_fields(self, extracted_info: Dict[str, Any], automation_type: str) -> List[str]:
        """부족한 필수 정보 식별"""
        try:
            required_fields = self._get_required_fields(automation_type)
            missing_fields = []
            
            for field in required_fields:
                if not extracted_info.get(field):
                    missing_fields.append(field)
            
            return missing_fields
            
        except Exception as e:
            logger.error(f"부족한 정보 식별 실패: {e}")
            return []

    def _get_required_fields(self, automation_type: str) -> List[str]:
        """자동화 타입별 필수 필드 반환"""
        required_fields_map = {
            "schedule_calendar": ["title", "start_time"],
            "send_email": ["to_emails", "subject", "body"],
            "send_reminder": ["title", "remind_time"],
            "send_message": ["platform", "content"],
            "blog_marketing": ["base_keyword"]
        }
        
        return required_fields_map.get(automation_type, [])

    async def _create_automation_task_directly(self, query: UserQuery, automation_type: str, 
                                             extracted_info: Dict[str, Any], intent_analysis: Dict) -> UnifiedResponse:
        """모든 정보가 충족된 경우 자동화 작업 직접 생성"""
        try:
            # 자동화 작업 생성 및 DB 저장
            automation_request = AutomationRequest(
                user_id=int(query.user_id),
                task_type=automation_type,
                title=self._generate_automation_title(automation_type, extracted_info),
                task_data=extracted_info
            )
            
            automation_response = await self.automation_manager.create_automation_task(automation_request)
            
            # 성공 메시지 생성
            success_message = f"✅ {automation_type} 자동화 작업이 성공적으로 등록되었습니다!\n\n"
            success_message += f"작업 ID: {automation_response.task_id}\n"
            success_message += f"제목: {automation_request.title}\n\n"
            success_message += "📋 **등록된 정보:**\n"
            success_message += self._format_extracted_info_display(extracted_info, automation_type)
            success_message += "\n\n자동화 작업이 예약된 시간에 실행됩니다."
            
            routing_decision = RoutingDecision(
                agent_type=AgentType.TASK_AUTOMATION,
                confidence=intent_analysis.get("confidence", 0.9),
                reasoning="자동화 작업 저장 성공",
                keywords=[automation_type],
                priority=intent_analysis.get("urgency", "medium")
            )
            
            return UnifiedResponse(
                conversation_id=int(query.conversation_id) if query.conversation_id else 0,
                agent_type=AgentType.TASK_AUTOMATION,
                response=success_message,
                confidence=intent_analysis.get("confidence", 0.9),
                routing_decision=routing_decision,
                sources=None,
                metadata={
                    "intent": intent_analysis["intent"],
                    "task_id": automation_response.task_id,
                    "automation_type": automation_type,
                    "title": automation_request.title,
                    "action": "automation_saved"
                },
                processing_time=0.0,
                timestamp=datetime.now(),
                alternatives=[]
            )
            
        except Exception as e:
            logger.error(f"자동화 작업 직접 생성 실패: {e}")

    async def _request_missing_information(self, query: UserQuery, automation_type: str, 
                                         extracted_info: Dict[str, Any], missing_fields: List[str], 
                                         intent_analysis: Dict) -> UnifiedResponse:
        """부족한 정보만 요청"""
        try:
            # 이미 입력된 정보 표시
            response_message = f"안녕하세요! {automation_type} 자동화를 설정해드리겠습니다.\n\n"
            
            if extracted_info:
                response_message += "📋 **이미 입력된 정보:**\n"
                response_message += self._format_extracted_info_display(extracted_info, automation_type)
                response_message += "\n\n"
            
            # 부족한 정보만 요청
            response_message += "❓ **추가로 필요한 정보:**\n"
            response_message += self._generate_missing_fields_template(missing_fields, automation_type)
            
            routing_decision = RoutingDecision(
                agent_type=AgentType.TASK_AUTOMATION,
                confidence=intent_analysis.get("confidence", 0.8),
                reasoning=f"부족한 정보 요청: {', '.join(missing_fields)}",
                keywords=intent_analysis.get("keywords", []),
                priority=Priority.MEDIUM
            )
            
            return UnifiedResponse(
                conversation_id=int(query.conversation_id) if query.conversation_id else 0,
                agent_type=AgentType.TASK_AUTOMATION,
                response=response_message,
                confidence=intent_analysis.get("confidence", 0.8),
                routing_decision=routing_decision,
                sources=None,
                metadata={
                    "automation_type": automation_type,
                    "intent": intent_analysis["intent"],
                    "extracted_info": extracted_info,
                    "missing_fields": missing_fields,
                    "actions": [{
                        "type": "partial_automation_info",
                        "data": {"automation_type": automation_type, "missing_fields": missing_fields},
                        "description": f"부족한 정보 요청: {', '.join(missing_fields)}"
                    }]
                },
                processing_time=0.0,
                timestamp=datetime.now(),
                alternatives=[]
            )
            
        except Exception as e:
            logger.error(f"부족한 정보 요청 실패: {e}")

    def _format_extracted_info_display(self, extracted_info: Dict[str, Any], automation_type: str) -> str:
        """추출된 정보를 사용자에게 보여주기 위한 포맷"""
        try:
            display_text = ""
            field_labels = self._get_field_labels(automation_type)
            
            for field, value in extracted_info.items():
                if value:
                    label = field_labels.get(field, field)
                    if isinstance(value, list):
                        value_str = ", ".join(str(v) for v in value)
                    else:
                        value_str = str(value)
                    display_text += f"• {label}: {value_str}\n"
            
            return display_text
            
        except Exception as e:
            logger.error(f"정보 표시 포맷 생성 실패: {e}")
            return "정보 표시 중 오류가 발생했습니다."

    def _generate_missing_fields_template(self, missing_fields: List[str], automation_type: str) -> str:
        """부족한 필드에 대한 템플릿 생성"""
        try:
            field_labels = self._get_field_labels(automation_type)
            field_examples = self._get_field_examples(automation_type)
            
            template = ""
            for field in missing_fields:
                label = field_labels.get(field, field)
                example = field_examples.get(field, "")
                template += f"• {label}: {example}\n"
            
            template += "\n💡 **팁:** 위 정보를 자연스럽게 말씀해주시면 자동으로 인식하여 등록해드립니다."
            
            return template
            
        except Exception as e:
            logger.error(f"부족한 필드 템플릿 생성 실패: {e}")
            return "추가 정보를 입력해주세요."

    def _get_field_labels(self, automation_type: str) -> Dict[str, str]:
        """필드별 한국어 라벨 반환"""
        labels_map = {
            "schedule_calendar": {
                "title": "제목",
                "start_time": "시작시간",
                "end_time": "종료시간",
                "description": "설명",
                "attendees": "참석자"
            },
            "send_email": {
                "to_emails": "받는사람",
                "subject": "제목",
                "body": "내용",
                "scheduled_time": "예약시간",
                "attachments": "첨부파일"
            },
            "send_reminder": {
                "title": "제목",
                "remind_time": "알림시간",
                "description": "내용",
                "repeat": "반복설정"
            },
            "send_message": {
                "platform": "플랫폼",
                "channel": "채널/수신자",
                "content": "내용",
                "scheduled_time": "예약시간"
            }
        }
        
        return labels_map.get(automation_type, {})

    def _get_field_examples(self, automation_type: str) -> Dict[str, str]:
        """필드별 예시 반환"""
        examples_map = {
            "schedule_calendar": {
                "title": "[예: 팀 미팅, 고객 미팅]",
                "start_time": "[예: 내일 오후 2시, 2024-01-15 14:00]",
                "end_time": "[예: 오후 3시, 15:00]",
                "description": "[예: 월간 진행상황 공유]",
                "attendees": "[예: john@company.com, jane@company.com]"
            },
            "send_email": {
                "to_emails": "[예: john@company.com]",
                "subject": "[예: 월간 보고서]",
                "body": "[예: 안녕하세요. 월간 보고서를 첨부합니다.]",
                "scheduled_time": "[예: 내일 오전 9시]",
                "attachments": "[예: /path/to/report.pdf]"
            },
            "send_reminder": {
                "title": "[예: 회의 준비]",
                "remind_time": "[예: 내일 오전 9시]",
                "description": "[예: 발표 자료 준비하기]",
                "repeat": "[예: 매일, 매주, 매월]"
            },
            "send_message": {
                "platform": "[예: Slack, Teams, Discord]",
                "channel": "[예: #dev-team, @john]",
                "content": "[예: 배포가 완료되었습니다.]",
                "scheduled_time": "[예: 오후 5시]"
            }
        }
        
        return examples_map.get(automation_type, {})

    def _get_automation_template(self, automation_type: str) -> str:
        """자동화 템플릿 반환"""
        templates = {
            "schedule_calendar": """
📅 **일정 등록을 위한 정보를 알려주세요:**

• 제목: [일정 제목]
• 날짜: [YYYY-MM-DD]
• 시작시간: [HH:MM]
• 종료시간: [HH:MM] (선택사항)
• 설명: [상세 내용] (선택사항)
• 참석자: [이메일 주소들] (선택사항)

예시: "내일 오후 2시에 팀 미팅 예약해줘"
""",
            
            "send_email": """
📧 **이메일 발송을 위한 정보를 알려주세요:**

• 받는사람: [이메일 주소]
• 제목: [이메일 제목]
• 내용: [이메일 본문]
• 예약시간: [YYYY-MM-DD HH:MM] (선택사항)
• 첨부파일: [파일 경로] (선택사항)

예시: "john@company.com에게 '월간 보고서' 제목으로 보고서 첨부해서 보내줘"
""",
            
            "send_reminder": """
⏰ **리마인더 설정을 위한 정보를 알려주세요:**

• 제목: [리마인더 제목]
• 알림시간: [YYYY-MM-DD HH:MM]
• 내용: [상세 내용] (선택사항)
• 반복설정: [매일/매주/매월] (선택사항)

예시: "내일 오전 9시에 '회의 준비' 리마인더 설정해줘"
""",
            
            "send_message": """
💬 **메시지 발송을 위한 정보를 알려주세요:**

• 플랫폼: [Slack, Teams, Discord 등]
• 채널/수신자: [채널명 또는 사용자명]
• 내용: [메시지 내용]
• 예약시간: [YYYY-MM-DD HH:MM] (선택사항)

예시: "Slack #dev-team 채널에 '배포 완료' 메시지 보내줘"
"""
        }
        
        template = templates.get(automation_type, "자동화 설정을 위한 추가 정보가 필요합니다.")
        
        # 페르소나별 추가 가이드 (예시)
        template += "\n\n💡 **팁:** 더 자세한 정보를 제공할수록 정확한 자동화를 설정할 수 있습니다."
        
        return template

    # ===== 자동화 관리 =====

    async def create_automation_task(self, request: AutomationRequest) -> AutomationResponse:
        """자동화 작업 생성"""
        try:
            TaskAgentLogger.log_automation_task(
                task_id="creating",
                task_type=request.task_type.value,
                status="creating",
                details=f"user_id: {request.user_id}"
            )
            
            response = await self.automation_manager.create_automation_task(request)
            
            TaskAgentLogger.log_automation_task(
                task_id=str(response.task_id),
                task_type=request.task_type.value,
                status=response.status.value,
                details="automation task created via agent"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"자동화 작업 생성 실패: {e}")
            raise

    async def get_automation_status(self, task_id: int) -> Dict[str, Any]:
        """자동화 작업 상태 조회"""
        try:
            return await self.automation_manager.get_task_status(task_id)
        except Exception as e:
            logger.error(f"자동화 상태 조회 실패: {e}")
            return {"error": f"작업 상태를 조회할 수 없습니다: {str(e)}"}

    async def cancel_automation_task(self, task_id: int) -> bool:
        """자동화 작업 취소"""
        try:
            result = await self.automation_manager.cancel_task(task_id)
            
            TaskAgentLogger.log_automation_task(
                task_id=str(task_id),
                task_type="unknown",
                status="cancelled" if result else "cancel_failed",
                details="cancellation requested via agent"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"자동화 작업 취소 실패: {e}")
            return False

    # ===== 시스템 관리 =====

    async def get_status(self) -> Dict[str, Any]:
        """에이전트 상태 조회"""
        try:
            # LLM 핸들러 상태
            llm_status = self.llm_handler.get_status()
            
            # RAG 매니저 상태
            rag_status = self.rag_manager.get_status()
            
            return {
                "agent_version": "4.0.0",
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "llm_handler": llm_status,
                    "rag_manager": rag_status,
                    "automation_manager": "active"
                },
                "memory_usage": {
                    "cache_entries": cache_stats.get("general_cache_size", 0) + cache_stats.get("conversation_cache_size", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"상태 조회 실패: {e}")
            return {
                "agent_version": "4.0.0",
                "status": "error", 
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """사용자 통계 조회"""
        try:
            stats = {
                "user_id": user_id,
                "total_queries": 0,
                "automation_tasks": 0,
                "last_interaction": None,
                "preferred_persona": PersonaType.COMMON.value
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"사용자 통계 조회 실패: {e}")
            return {"error": str(e)}

    async def _handle_confirmation_response(self, query: UserQuery, is_confirmed: bool, 
                                      intent_analysis: Dict, conversation_history: List[Dict] = None) -> UnifiedResponse:
        """사용자 확인 응답 처리"""
        try:
            if is_confirmed:
                # 긍정 응답 - 자동화 작업 등록
                return await self._process_confirmed_automation(
                    query, intent_analysis, conversation_history
                )
            else:
                # 부정 응답 - 등록 취소
                return await self._process_cancelled_automation(
                    query, intent_analysis
                )
                
        except Exception as e:
            logger.error(f"확인 응답 처리 실패: {e}")

    async def _process_confirmed_automation(self, query: UserQuery, intent_analysis: Dict, 
                                      conversation_history: List[Dict] = None) -> UnifiedResponse:
        """확인된 자동화 작업 등록 처리"""
        try:
            # 대화 이력에서 자동화 정보 추출
            automation_type = self._extract_automation_type_from_history(conversation_history)
            extracted_info = self._extract_confirmed_info_from_history(conversation_history)
            
            if not automation_type or not extracted_info:
                routing_decision = RoutingDecision(
                    agent_type=AgentType.TASK_AUTOMATION,
                    confidence=0.3,
                    reasoning="자동화 정보 추출 실패",
                    keywords=[],
                    priority=Priority.MEDIUM
                )
                
                return UnifiedResponse(
                    conversation_id=int(query.conversation_id) if query.conversation_id else 0,
                    agent_type=AgentType.TASK_AUTOMATION,
                    response="죄송합니다. 등록할 정보를 찾을 수 없습니다. 다시 시도해주세요.",
                    confidence=0.3,
                    routing_decision=routing_decision,
                    sources=None,
                    metadata={"intent": intent_analysis["intent"], "error": "정보 추출 실패"},
                    processing_time=0.0,
                    timestamp=datetime.now(),
                    alternatives=[]
                )
            
            # 자동화 작업 생성 및 DB 저장
            automation_request = AutomationRequest(
                user_id=int(query.user_id),
                task_type=automation_type,
                title=self._generate_automation_title(automation_type, extracted_info),
                task_data=extracted_info
            )
            
            automation_response = await self.automation_manager.create_automation_task(automation_request)
            
            # 성공 메시지 생성
            success_message = f"🎉 {automation_type} 자동화 작업이 성공적으로 등록되었습니다!\n\n"
            success_message += f"📝 **작업 정보:**\n"
            success_message += f"• 작업 ID: {automation_response.task_id}\n"
            success_message += f"• 제목: {automation_request.title}\n\n"
            success_message += "📋 **등록된 세부 정보:**\n"
            success_message += self._format_extracted_info_display(extracted_info, automation_type)
            success_message += "\n\n⏰ 자동화 작업이 예약된 시간에 실행됩니다."
            
            routing_decision = RoutingDecision(
                agent_type=AgentType.TASK_AUTOMATION,
                confidence=intent_analysis.get("confidence", 0.95),
                reasoning="자동화 작업 등록 완료",
                keywords=[automation_type],
                priority=Priority.HIGH
            )
            
            return UnifiedResponse(
                conversation_id=int(query.conversation_id) if query.conversation_id else 0,
                agent_type=AgentType.TASK_AUTOMATION,
                response=success_message,
                confidence=intent_analysis.get("confidence", 0.95),
                routing_decision=routing_decision,
                sources=None,
                metadata={
                    "intent": intent_analysis["intent"],
                    "task_id": automation_response.task_id,
                    "automation_type": automation_type,
                    "title": automation_request.title,
                    "action": "automation_registered",
                    "status": "completed"
                },
                processing_time=0.0,
                timestamp=datetime.now(),
                alternatives=[]
            )
            
        except Exception as e:
            logger.error(f"확인된 자동화 작업 등록 실패: {e}")
            routing_decision = RoutingDecision(
                agent_type=AgentType.TASK_AUTOMATION,
                confidence=0.3,
                reasoning="자동화 작업 등록 실패",
                keywords=[],
                priority=Priority.MEDIUM
            )
            
            return UnifiedResponse(
                conversation_id=int(query.conversation_id) if query.conversation_id else 0,
                agent_type=AgentType.TASK_AUTOMATION,
                response="자동화 작업 등록 중 오류가 발생했습니다. 다시 시도해주세요.",
                confidence=0.3,
                routing_decision=routing_decision,
                sources=None,
                metadata={
                    "intent": intent_analysis["intent"],
                    "error": str(e),
                    "action": "registration_failed"
                },
                processing_time=0.0,
                timestamp=datetime.now(),
                alternatives=[]
            )

    async def _process_cancelled_automation(self, query: UserQuery, intent_analysis: Dict) -> UnifiedResponse:
        """취소된 자동화 작업 처리"""
        try:
            cancel_message = "❌ 자동화 작업 등록이 취소되었습니다.\n\n"
            cancel_message += "💡 언제든지 다시 자동화 설정을 요청하실 수 있습니다.\n"
            cancel_message += "다른 도움이 필요하시면 말씀해주세요!"
            
            routing_decision = RoutingDecision(
                agent_type=AgentType.TASK_AUTOMATION,
                confidence=intent_analysis.get("confidence", 0.9),
                reasoning="자동화 작업 취소",
                keywords=[],
                priority=Priority.MEDIUM
            )
            
            return UnifiedResponse(
                conversation_id=int(query.conversation_id) if query.conversation_id else 0,
                agent_type=AgentType.TASK_AUTOMATION,
                response=cancel_message,
                confidence=intent_analysis.get("confidence", 0.9),
                routing_decision=routing_decision,
                sources=None,
                metadata={
                    "intent": intent_analysis["intent"],
                    "action": "automation_cancelled",
                    "status": "cancelled"
                },
                processing_time=0.0,
                timestamp=datetime.now(),
                alternatives=[]
            )
            
        except Exception as e:
            logger.error(f"취소된 자동화 작업 처리 실패: {e}")

    def _extract_confirmed_info_from_history(self, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """대화 이력에서 확인된 자동화 정보 추출"""
        try:
            if not conversation_history:
                return {}
            
            # 마지막 확인 요청 메시지에서 extracted_info 찾기
            for msg in reversed(conversation_history):
                if msg.get('role') == 'assistant':
                    content = msg.get('content', '')
                    # 확인 요청 메시지인지 확인
                    if "업무를 등록하시겠습니까" in content or "등록될 정보" in content:
                        # 메타데이터에서 extracted_info 추출 (실제 구현에서는 메타데이터 저장 방식에 따라 조정)
                        # 여기서는 대화 이력 전체에서 정보를 다시 추출
                        break
            
            # 전체 대화에서 정보 재추출
            full_conversation = ""
            for msg in conversation_history:
                if msg.get('role') == 'user':
                    full_conversation += msg.get('content', '') + " "
            
            # 자동화 타입별로 정보 추출 (간단한 예시)
            extracted_info = {}
            
            # 일정 관련 정보 추출
            import re
            if re.search(r'일정|회의|미팅', full_conversation):
                title_match = re.search(r'(팀 미팅|회의|미팅|일정)([^\n]*)', full_conversation)
                if title_match:
                    extracted_info['title'] = title_match.group(0).strip()
                
                time_match = re.search(r'(내일|모레|\d{1,2}시|\d{1,2}:\d{2}|오전|오후)', full_conversation)
                if time_match:
                    extracted_info['start_time'] = time_match.group(0).strip()
            
            # 이메일 관련 정보 추출
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', full_conversation)
            if email_match:
                extracted_info['to_emails'] = [email_match.group(0)]
            
            return extracted_info
            
        except Exception as e:
            logger.error(f"확인된 정보 추출 실패: {e}")
            return {}
