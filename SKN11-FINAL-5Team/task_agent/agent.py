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
            
            # 캐시 매니저는 utils에서 가져옴
            self.cache_manager = task_cache
            
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
            
            # 캐시 확인
            cache_key = f"query_{hash(query.message)}_{query.persona.value}"
            cached_response = self.cache_manager.get_conversation_context(cache_key)
            
            if cached_response and isinstance(cached_response, dict):
                # 캐시된 응답이 있으면 conversation_id만 업데이트하고 반환
                cached_response["conversation_id"] = query.conversation_id or ""
                TaskAgentLogger.log_user_interaction(
                    user_id=query.user_id,
                    action="cache_hit",
                    details=f"cache_key: {cache_key}"
                )
                routing_decision = RoutingDecision(
                    agent_type=AgentType.TASK_AUTOMATION,
                    confidence=cached_response.get("confidence", 0.8),
                    reasoning="Cached response",
                    keywords=[],
                    priority=Priority.MEDIUM
                )
                
                return UnifiedResponse(
                    conversation_id=int(query.conversation_id) if query.conversation_id else 0,
                    agent_type=AgentType.TASK_AUTOMATION,
                    response=cached_response.get("response", ""),
                    confidence=cached_response.get("confidence", 0.8),
                    routing_decision=routing_decision,
                    sources=None,
                    metadata=cached_response.get("metadata", {}),
                    processing_time=0.0,
                    timestamp=datetime.now(),
                    alternatives=[]                    
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
            automation_type = None
            if (
                intent_analysis["intent"] == IntentType.TASK_AUTOMATION or
                any(keyword in query.message for keyword in ["자동화", "자동", "등록", "생성", "업로드"])
            ):
                automation_type = await self.llm_handler.classify_automation_intent(query.message)
            
            # 자동화 완료 데이터 확인 (포맷에 맞게 입력된 데이터인지 확인)
            is_automation_data = self._check_if_automation_data(query.message, conversation_history)
            
            # 워크플로우 결정
            if automation_type:
                # 자동화 타입이 감지되면 포맷 제공
                response = await self._provide_automation_format(
                    query, automation_type, intent_analysis
                )
            elif is_automation_data:
                # 포맷에 맞는 데이터가 입력되면 DB 저장
                response = await self._save_automation_task(
                    query, intent_analysis, conversation_history
                )
            else:
                response = await self._handle_consultation_workflow(
                    query, intent_analysis, conversation_history
                )
            
            # 캐시 저장 - UnifiedResponse 형식으로 변환
            cache_data = {
                "response": response.response,
                "confidence": response.confidence,
                "metadata": response.metadata,
                "routing_decision": response.routing_decision.dict() if response.routing_decision else None
            }
            self.cache_manager.set_conversation_context(cache_key, cache_data)
            
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
            actions = self._generate_follow_up_actions(intent_analysis["intent"], query.persona)
            
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
                sources=search_result.sources if search_result else None,
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
            # 백업 응답 생성
            return self._create_fallback_response(query, intent_analysis)

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
            # 자동화 타입에 따른 포맷 제공
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
            return self._create_fallback_response(query, intent_analysis)
    
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
                "publish_sns": ["SNS", "소셜", "게시", "트위터", "페이스북"],
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

    async def _handle_automation_workflow(self, query: UserQuery, automation_type: str, 
                                        intent_analysis: Dict, conversation_history: List[Dict] = None) -> UnifiedResponse:
        """자동화 워크플로우 처리 (기존 로직 유지 - 호환성을 위해)"""
        try:
            # 정보 추출
            extraction_type = self._map_automation_to_extraction(automation_type)
            extracted_info = await self.llm_handler.extract_information(
                query.message, extraction_type, conversation_history
            )
            
            if extracted_info and self._validate_extracted_info(extracted_info, automation_type):
                # 자동화 작업 생성
                automation_request = AutomationRequest(
                    user_id=int(query.user_id),
                    task_type=automation_type,
                    title=self._generate_automation_title(automation_type, extracted_info),
                    task_data=extracted_info
                )
                
                automation_response = await self.automation_manager.create_automation_task(automation_request)
                
                routing_decision = RoutingDecision(
                    agent_type=AgentType.TASK_AUTOMATION,
                    confidence=intent_analysis.get("confidence", 0.5),
                    reasoning="자동화 작업 생성 성공",
                    keywords=[automation_type],
                    priority=intent_analysis.get("urgency", "medium")
                )
                
                return UnifiedResponse(
                    conversation_id=int(query.conversation_id) if query.conversation_id else 0,
                    agent_type=AgentType.TASK_AUTOMATION,
                    response=automation_response.message,
                    confidence=intent_analysis.get("confidence", 0.5),
                    routing_decision=routing_decision,
                    sources=None,
                    metadata={
                        "intent": intent_analysis["intent"],
                        "task_id": automation_response.task_id,
                        "automation_type": automation_type,
                        "action": "automation_created"
                    },
                    processing_time=0.0,
                    timestamp=datetime.now(),
                    alternatives=[]
                )
            else:
                # 템플릿 제공
                template = self._get_automation_template(automation_type)
                routing_decision = RoutingDecision(
                    agent_type=AgentType.TASK_AUTOMATION,
                    confidence=intent_analysis.get("confidence", 0.3),
                    reasoning="템플릿 제공 필요",
                    keywords=[automation_type],
                    priority=intent_analysis.get("urgency", "medium")
                )
                
                return UnifiedResponse(
                    conversation_id=int(query.conversation_id) if query.conversation_id else 0,
                    agent_type=AgentType.TASK_AUTOMATION,
                    response=template,
                    confidence=intent_analysis.get("confidence", 0.3),
                    routing_decision=routing_decision,
                    sources=None,
                    metadata={
                        "intent": intent_analysis["intent"],
                        "automation_type": automation_type,
                        "action": "template_provided"
                    },
                    processing_time=0.0,
                    timestamp=datetime.now(),
                    alternatives=[])
                
        except Exception as e:
            logger.error(f"자동화 워크플로우 처리 실패: {e}")
            return self._create_fallback_response(query, intent_analysis)

    def _create_fallback_response(self, query: UserQuery, intent_analysis: Dict) -> UnifiedResponse:
        """백업 응답 생성"""
        routing_decision = RoutingDecision(
            agent_type=AgentType.TASK_AUTOMATION,
            confidence=0.3,
            reasoning="의도 파악 실패",
            keywords=[],
            priority=intent_analysis.get("urgency", "medium")
        )
        
        return UnifiedResponse(
            conversation_id=int(query.conversation_id) if query.conversation_id else 0,
            agent_type=AgentType.TASK_AUTOMATION,
            response=f"{query.persona.value} 관련 업무를 도와드리고 싶지만, 현재 시스템에 일시적인 문제가 있습니다. 좀 더 구체적으로 말씀해주시면 더 나은 도움을 드릴 수 있습니다.",
            confidence=0.3,
            routing_decision=routing_decision,
            sources=None,
            metadata={
                "intent": intent_analysis.get("intent", IntentType.GENERAL_INQUIRY),
                "action": "fallback"
            },
            processing_time=0.0,
            timestamp=datetime.now(),
            alternatives=[]
        )

    def _validate_extracted_info(self, extracted_info: Dict[str, Any], automation_type: str) -> bool:
        """추출된 정보 검증"""
        try:
            if automation_type == "schedule_calendar":
                return bool(extracted_info.get("title") and extracted_info.get("start_time"))
            elif automation_type == "send_email":
                return bool(extracted_info.get("to_emails") and 
                          extracted_info.get("subject") and 
                          extracted_info.get("body"))
            elif automation_type == "publish_sns":
                return bool(extracted_info.get("platform") and extracted_info.get("content"))
            elif automation_type == "send_reminder":
                return bool(extracted_info.get("title") and extracted_info.get("remind_time"))
            elif automation_type == "send_message":
                return bool(extracted_info.get("platform") and extracted_info.get("content"))
            else:
                return True  # 기타 타입은 기본적으로 통과
        except Exception as e:
            logger.error(f"정보 검증 실패: {e}")
            return False

    def _map_automation_to_extraction(self, automation_type: str) -> str:
        """자동화 타입을 정보 추출 타입으로 매핑"""
        mapping = {
            "schedule_calendar": "schedule",
            "send_email": "email",
            "publish_sns": "sns",
            "send_reminder": "reminder",
            "send_message": "message"
        }
        return mapping.get(automation_type, "general")

    def _generate_automation_title(self, automation_type: str, extracted_info: Dict[str, Any]) -> str:
        """자동화 작업 제목 생성"""
        try:
            if automation_type == "schedule_calendar":
                return f"일정 등록: {extracted_info.get('title', '제목 없음')}"
            elif automation_type == "send_email":
                subject = extracted_info.get('subject', '제목 없음')
                recipients = extracted_info.get('to_emails', [])
                if recipients:
                    return f"이메일 발송: {subject} (to: {len(recipients)}명)"
                return f"이메일 발송: {subject}"
            elif automation_type == "publish_sns":
                content = extracted_info.get('content', '')
                platform = extracted_info.get('platform', 'SNS')
                preview = content[:30] + "..." if len(content) > 30 else content
                return f"{platform} 발행: {preview}"
            elif automation_type == "send_reminder":
                return f"리마인더: {extracted_info.get('title', '제목 없음')}"
            elif automation_type == "send_message":
                platform = extracted_info.get('platform', '메시지')
                content = extracted_info.get('content', '')
                preview = content[:30] + "..." if len(content) > 30 else content
                return f"{platform} 메시지: {preview}"
            else:
                return f"{automation_type} 자동화 작업"
        except Exception as e:
            logger.error(f"자동화 제목 생성 실패: {e}")
            return f"{automation_type} 자동화 작업"

    def _generate_follow_up_actions(self, intent: str, persona: PersonaType) -> List[Dict[str, Any]]:
        """후속 액션 생성"""
        actions = []
        
        try:
            if intent == "schedule_management":
                actions.append({
                    "type": "calendar_integration",
                    "description": "캘린더 연동을 설정하시겠습니까?",
                    "data": {"persona": persona.value}
                })
                
        except Exception as e:
            logger.error(f"후속 액션 생성 실패: {e}")
        
        return actions

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
            
            "publish_sns": """
📱 **SNS 발행을 위한 정보를 알려주세요:**

• 플랫폼: [Twitter, Facebook, Instagram, LinkedIn 등]
• 내용: [게시물 내용]
• 예약시간: [YYYY-MM-DD HH:MM] (선택사항)
• 해시태그: [#태그1 #태그2] (선택사항)
• 이미지: [이미지 경로] (선택사항)

예시: "트위터에 '새로운 프로젝트 출시!' 내용으로 #프로젝트 #출시 태그와 함께 게시"
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
            
            # 캐시 상태
            cache_stats = self.cache_manager.get_stats()
            
            return {
                "agent_version": "4.0.0",
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "llm_handler": llm_status,
                    "rag_manager": rag_status,
                    "automation_manager": "active",
                    "cache_manager": cache_stats
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

    async def cleanup_resources(self):
        """리소스 정리"""
        try:
            # 캐시 정리
            expired_count = self.cache_manager.cleanup_expired()
            logger.info(f"만료된 캐시 {expired_count}개 정리 완료")
            
            # 자동화 매니저 종료
            if hasattr(self.automation_manager, 'shutdown'):
                await self.automation_manager.shutdown()
            
            logger.info("Task Agent 리소스 정리 완료")
            
        except Exception as e:
            logger.error(f"리소스 정리 실패: {e}")

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
            
            # 캐시에서 사용자 활동 정보 조회 시도
            user_cache_key = f"user_stats_{user_id}"
            cached_stats = self.cache_manager.get_user_preferences(user_id)
            
            if cached_stats:
                stats.update(cached_stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"사용자 통계 조회 실패: {e}")
            return {"error": str(e)}
