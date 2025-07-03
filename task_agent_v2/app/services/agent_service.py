"""
TinkerBell 프로젝트 - 에이전트 서비스
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..core.exceptions import LLMError, ValidationError, TinkerBellException
from ..core.config import config
from ..schemas.base import UserQueryRequest, UserQueryResponse
from ..schemas.enums import AutomationTaskType, PersonaType, TaskTopic, IntentType, UrgencyLevel

# 기존 모듈들 import (추후 리팩토링)
from ..core.llm_handler import LLMHandler
from ..core.rag import RAGManager
from ..services.automation_service import AutomationService
from ..schemas.automation import AutomationTaskCreate
from ..core.utils import CacheManager
from ..core.db.database import get_db_session

logger = logging.getLogger(__name__)

class AgentService:
    """에이전트 서비스 - 핵심 AI 처리 담당"""
    
    def __init__(self, db_session=None, automation_config=None):
        """서비스 초기화"""
        try:
            self.llm_handler = LLMHandler()
            self.rag_manager = RAGManager()
            
            # DB 세션 초기화
            self.db_session = db_session or get_db_session()
            
            # 자동화 서비스 초기화
            self.automation_manager = AutomationService(
                db_session=self.db_session,
                service_config=automation_config or {}
            )
            
            self.cache_manager = CacheManager(default_ttl=1800)
            
            logger.info("에이전트 서비스 초기화 완료")
            
        except Exception as e:
            logger.error(f"에이전트 서비스 초기화 실패: {e}")
            raise TinkerBellException(f"에이전트 서비스 초기화 실패: {e}")
    
    async def process_query(
        self, 
        query: UserQueryRequest, 
        conversation_history: List[Dict[str, Any]] = None
    ) -> UserQueryResponse:
        """사용자 쿼리 처리"""
        start_time = datetime.now()
        
        try:
            # 캐시 확인
            cache_key = self._generate_cache_key(query, conversation_history)
            cached_response = self.cache_manager.get(cache_key)
            
            if cached_response:
                logger.info(f"캐시에서 응답 반환: {query.user_id}")
                return UserQueryResponse(**cached_response)
            
            # 의도 분석
            intent_analysis = await self._analyze_intent(query, conversation_history)
            
            # 자동화 요청 확인
            automation_type = await self._check_automation_request(query, intent_analysis)
            
            # 워크플로우 결정 및 실행
            if automation_type:
                response = await self._handle_automation_workflow(
                    query, automation_type, intent_analysis, conversation_history
                )
            else:
                response = await self._handle_consultation_workflow(
                    query, intent_analysis, conversation_history
                )
            
            # 처리 시간 계산
            processing_time = (datetime.now() - start_time).total_seconds()
            response.processing_time = processing_time
            
            # 캐시 저장
            self.cache_manager.set(cache_key, response.dict())
            
            logger.info(f"쿼리 처리 완료: {query.user_id}, 시간: {processing_time:.2f}초")
            
            return response
            
        except Exception as e:
            logger.error(f"쿼리 처리 실패: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return UserQueryResponse(
                status="error",
                response="죄송합니다. 요청을 처리하는 중에 오류가 발생했습니다.",
                conversation_id=query.conversation_id or "",
                intent=IntentType.GENERAL_INQUIRY,
                urgency=UrgencyLevel.MEDIUM,
                confidence=0.0,
                processing_time=processing_time
            )
    
    async def _analyze_intent(
        self, 
        query: UserQueryRequest, 
        conversation_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """사용자 의도 분석"""
        try:
            if query.intent:
                # 명시적 의도가 있는 경우
                intent_value = query.intent.value if hasattr(query.intent, 'value') else str(query.intent)
                return {
                    "intent": intent_value,
                    "urgency": "medium",
                    "confidence": 1.0
                }
            
            # PersonaType으로 변환 (문자열인 경우)
            from ..schemas.enums import PersonaType
            if isinstance(query.persona, str):
                try:
                    persona_enum = PersonaType(query.persona)
                except ValueError:
                    persona_enum = PersonaType.COMMON
            else:
                persona_enum = query.persona
            
            # LLM을 통한 의도 분석
            intent_analysis = await self.llm_handler.analyze_intent(
                query.message, persona_enum
            )
            
            return intent_analysis
            
        except Exception as e:
            logger.error(f"의도 분석 실패: {e}")
            # 폴백 분석
            return self._fallback_intent_analysis(query.message)
    
    async def _check_automation_request(
        self, 
        query: UserQueryRequest, 
        intent_analysis: Dict[str, Any]
    ) -> Optional[str]:
        """자동화 요청 확인"""
        try:
            from ..schemas.enums import AutomationTaskType
            
            # 키워드 기반 1차 필터링
            automation_keywords = [
                "자동화", "자동", "예약", "스케줄", "반복",
                "알림", "리마인더", "발송", "전송", "등록"
            ]
            
            is_automation_request = any(
                keyword in query.message for keyword in automation_keywords
            )
            
            if intent_analysis.get("intent") == "task_automation" or is_automation_request:
                # LLM을 통한 자동화 유형 분류
                automation_type_str = await self.llm_handler.classify_automation_intent(
                    query.message
                )
                return automation_type_str
                
            return None
            
        except Exception as e:
            logger.error(f"자동화 요청 확인 실패: {e}")
            return None
    
    async def _handle_consultation_workflow(
        self,
        query: UserQueryRequest,
        intent_analysis: Dict[str, Any],
        conversation_history: List[Dict[str, Any]] = None
    ) -> UserQueryResponse:
        """상담 워크플로우 처리"""
        try:
            # enum 변환 처리
            from ..schemas.enums import PersonaType, TaskTopic, IntentType, UrgencyLevel
            
            if isinstance(query.persona, str):
                try:
                    persona_enum = PersonaType(query.persona)
                except ValueError:
                    persona_enum = PersonaType.COMMON
            else:
                persona_enum = query.persona
            
            try:
                topic_enum = TaskTopic(intent_analysis["intent"])
            except (ValueError, KeyError):
                topic_enum = TaskTopic.GENERAL_INQUIRY
            
            try:
                intent_enum = IntentType(intent_analysis["intent"])
            except (ValueError, KeyError):
                intent_enum = IntentType.GENERAL_INQUIRY
                
            try:
                urgency_enum = UrgencyLevel(intent_analysis["urgency"])
            except (ValueError, KeyError):
                urgency_enum = UrgencyLevel.MEDIUM
            
            # 지식 검색
            search_query = self._enhance_search_query(query.message, conversation_history)
            search_result = await self.rag_manager.search_knowledge(
                search_query, persona_enum, topic=intent_analysis["intent"]
            )
            
            # 컨텍스트 구성
            context = ""
            knowledge_sources = []
            
            if search_result:
                context = "\n\n".join([
                    chunk.content for chunk in search_result.chunks[:3]
                ])
                knowledge_sources = search_result.sources
            
            # 개인화된 응답 생성
            if conversation_history:
                response_text = await self.llm_handler.generate_response(
                    query.message, persona_enum, topic_enum, 
                    context, conversation_history
                )
            else:
                response_text = await self.llm_handler.generate_personalized_response(
                    query.message, persona_enum, topic_enum, context
                )
            
            # 후속 액션 생성
            actions = self._generate_follow_up_actions(
                intent_analysis["intent"], persona_enum
            )
            
            return UserQueryResponse(
                status="success",
                response=response_text,
                conversation_id=query.conversation_id or "",
                intent=intent_enum,
                urgency=urgency_enum,
                confidence=intent_analysis["confidence"],
                actions=actions,
                knowledge_sources=knowledge_sources
            )
            
        except Exception as e:
            logger.error(f"상담 워크플로우 처리 실패: {e}")
            raise LLMError(f"상담 처리 중 오류 발생: {e}")
    
    async def _handle_automation_workflow(
        self,
        query: UserQueryRequest,
        automation_type: str,
        intent_analysis: Dict[str, Any],
        conversation_history: List[Dict[str, Any]] = None
    ) -> UserQueryResponse:
        """자동화 워크플로우 처리"""
        try:
            # enum 변환 처리
            from ..schemas.enums import AutomationTaskType, IntentType, UrgencyLevel
            
            try:
                intent_enum = IntentType(intent_analysis["intent"])
            except (ValueError, KeyError):
                intent_enum = IntentType.GENERAL_INQUIRY
                
            try:
                urgency_enum = UrgencyLevel(intent_analysis["urgency"])
            except (ValueError, KeyError):
                urgency_enum = UrgencyLevel.MEDIUM
            
            # automation_type을 enum으로 변환
            try:
                automation_type_enum = AutomationTaskType(automation_type)
            except ValueError:
                logger.error(f"지원하지 않는 자동화 타입: {automation_type}")
                return UserQueryResponse(
                    status="error",
                    response=f"지원하지 않는 자동화 타입입니다: {automation_type}",
                    conversation_id=query.conversation_id or "",
                    intent=intent_enum,
                    urgency=urgency_enum,
                    confidence=intent_analysis["confidence"]
                )
            
            # 자동화 타입별 필수 필드 정의 (automation_service.py 참조)
            required_fields_map = {
                AutomationTaskType.SCHEDULE_CALENDAR: ["title", "start_time"],
                AutomationTaskType.PUBLISH_SNS: ["platform", "content"],
                AutomationTaskType.SEND_EMAIL: ["to", "subject", "body"],
                AutomationTaskType.SEND_REMINDER: ["title"],
                AutomationTaskType.SEND_MESSAGE: ["platform", "content"]
            }
            
            required_fields = required_fields_map.get(automation_type_enum, [])
            
            # 히스토리에서 추가 컨텍스트 추출
            context_from_history = self._extract_automation_context_from_history(
                conversation_history
            ) if conversation_history else ""
            
            # 자동화 타입별 정보 추출
            automation_info = await self._extract_automation_info(
                automation_type_enum, query.message, conversation_history, context_from_history
            )
            
            # 필수 정보 검증
            missing_fields = []
            if automation_info and automation_info.get("task_data"):
                task_data = automation_info["task_data"]
                
                for field in required_fields:
                    if field not in task_data or not task_data[field]:
                        missing_fields.append(field)
            else:
                # automation_info가 없거나 task_data가 없으면 모든 필드가 누락
                missing_fields = required_fields
            
            # 필수 정보가 모두 있는 경우 자동화 작업 생성
            if not missing_fields:
                try:
                    # AutomationTaskCreate 스키마 생성
                    task_create_data = AutomationTaskCreate(
                        user_id=query.user_id,
                        conversation_id=query.conversation_id,
                        task_type=automation_type_enum,
                        title=automation_info.get("title", "자동화 작업"),
                        task_data=automation_info.get("task_data", {}),
                        scheduled_at=automation_info.get("scheduled_at")
                    )
                    
                    # 자동화 작업 생성
                    automation_response = await self.automation_manager.create_task(task_create_data)
                    
                    return UserQueryResponse(
                        status="success",
                        response=f"자동화 작업이 성공적으로 생성되었습니다. (작업 ID: {automation_response.task_id})",
                        conversation_id=query.conversation_id or "",
                        intent=intent_enum,
                        urgency=urgency_enum,
                        confidence=intent_analysis["confidence"],
                        actions=[{
                            "type": "automation_created",
                            "data": {
                                "task_id": automation_response.task_id,
                                "task_type": automation_response.task_type,
                                "status": automation_response.status
                            },
                            "description": "자동화 작업이 생성되었습니다."
                        }]
                    )
                    
                except Exception as automation_error:
                    logger.error(f"자동화 작업 생성 실패: {automation_error}")
                    return UserQueryResponse(
                        status="error",
                        response=f"자동화 작업 생성 중 오류가 발생했습니다: {str(automation_error)}",
                        conversation_id=query.conversation_id or "",
                        intent=intent_enum,
                        urgency=urgency_enum,
                        confidence=intent_analysis["confidence"]
                    )
            else:
                # 필수 정보가 부족한 경우 상세한 템플릿 제공
                template = self._get_detailed_automation_template(
                    automation_type_enum, missing_fields, automation_info, conversation_history
                )
                
                return UserQueryResponse(
                    status="template_needed",
                    response=template,
                    conversation_id=query.conversation_id or "",
                    intent=intent_enum,
                    urgency=urgency_enum,
                    confidence=intent_analysis["confidence"],
                    actions=[{
                        "type": "template_provided",
                        "data": {
                            "automation_type": automation_type_enum.value,
                            "missing_fields": missing_fields,
                            "required_fields": required_fields
                        },
                        "description": "추가 정보가 필요한 자동화 작업 템플릿"
                    }]
                )
                
        except Exception as e:
            logger.error(f"자동화 워크플로우 처리 실패: {e}")
            raise LLMError(f"자동화 처리 중 오류 발생: {e}")
    
    async def _extract_automation_info(
        self,
        automation_type: str,
        message: str,
        conversation_history: List[Dict[str, Any]] = None,
        context_from_history: str = ""
    ) -> Optional[Dict[str, Any]]:
        """자동화 정보 추출"""
        try:
            from ..schemas.enums import AutomationTaskType
            
            # automation_type이 이미 AutomationTaskType enum인지 확인
            if isinstance(automation_type, AutomationTaskType):
                task_type_enum = automation_type
            elif isinstance(automation_type, str):
                try:
                    task_type_enum = AutomationTaskType(automation_type)
                except ValueError:
                    logger.warning(f"지원하지 않는 자동화 타입: {automation_type}")
                    return None
            else:
                logger.warning(f"알 수 없는 자동화 타입 형식: {type(automation_type)}")
                return None
            
            extraction_methods = {
                AutomationTaskType.SCHEDULE_CALENDAR: self.llm_handler.extract_schedule_info,
                AutomationTaskType.PUBLISH_SNS: self.llm_handler.extract_sns_info,
                AutomationTaskType.SEND_EMAIL: self.llm_handler.extract_email_info,
                AutomationTaskType.SEND_REMINDER: self.llm_handler.extract_reminder_info,
                AutomationTaskType.SEND_MESSAGE: self.llm_handler.extract_message_info
            }
            
            extraction_method = extraction_methods.get(task_type_enum)
            if not extraction_method:
                logger.warning(f"추출 메서드가 없는 자동화 타입: {task_type_enum}")
                return None
            
            # LLM을 통한 정보 추출
            if conversation_history:
                extracted_info = await extraction_method(
                    message, conversation_history, context_from_history
                )
            else:
                extracted_info = await extraction_method(message)
            
            if not extracted_info:
                return None
            
            # 응답 구조를 AutomationTaskCreate에 맞게 변환
            return {
                "title": extracted_info.get("title", "자동화 작업"),
                "task_data": extracted_info,
                "scheduled_at": extracted_info.get("scheduled_at") or extracted_info.get("scheduled_time")
            }
                
        except Exception as e:
            logger.error(f"자동화 정보 추출 실패: {e}")
            return None
    
    def _generate_cache_key(
        self, 
        query: UserQueryRequest, 
        conversation_history: List[Dict[str, Any]] = None
    ) -> str:
        """캐시 키 생성"""
        history_hash = ""
        if conversation_history:
            history_hash = str(hash(str(conversation_history[-3:])))  # 최근 3개 메시지만
        
        return f"query_{hash(query.message)}_{query.persona}_{history_hash}"
    
    def _enhance_search_query(
        self, 
        current_message: str, 
        conversation_history: List[Dict[str, Any]] = None
    ) -> str:
        """히스토리를 고려한 검색 쿼리 향상"""
        if not conversation_history:
            return current_message
        
        # 최근 2-3개 메시지에서 키워드 추출
        recent_messages = conversation_history[-3:]
        keywords = []
        
        for msg in recent_messages:
            if msg["role"] == "user":
                words = msg["content"].split()
                keywords.extend([word for word in words if len(word) > 2])
        
        if keywords:
            return f"{current_message} {' '.join(keywords[:5])}"
        
        return current_message
    
    def _extract_automation_context_from_history(
        self, 
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """히스토리에서 자동화 관련 컨텍스트 추출"""
        automation_keywords = ["시간", "날짜", "일정", "회의", "미팅", "마감일", "알림"]
        context_parts = []
        
        for msg in conversation_history:
            content = msg["content"]
            for keyword in automation_keywords:
                if keyword in content:
                    context_parts.append(content)
                    break
        
        return "; ".join(context_parts[-3:])  # 최근 3개만
    
    def _generate_follow_up_actions(
        self, 
        intent: str, 
        persona: PersonaType
    ) -> List[Dict[str, Any]]:
        """후속 액션 생성"""
        actions = []
        
        if intent == "task_prioritization":
            actions.append({
                "type": "priority_matrix",
                "description": "우선순위 매트릭스 생성을 도와드릴까요?"
            })
        elif intent == "schedule_management":
            actions.append({
                "type": "calendar_integration",
                "description": "캘린더 연동 설정을 도와드릴까요?"
            })
        elif intent == "tool_stack":
            actions.append({
                "type": "tool_recommendation",
                "description": "추천 도구 설정 가이드를 제공해드릴까요?"
            })
        
        return actions
    
    def _get_detailed_automation_template(
        self, 
        automation_type: AutomationTaskType, 
        missing_fields: List[str],
        automation_info: Optional[Dict[str, Any]] = None,
        conversation_history: List[Dict[str, Any]] = None
    ) -> str:
        """상세한 자동화 템플릿 반환 (누락된 필드 기반)"""
        from ..schemas.enums import AutomationTaskType
        
        # 자동화 타입별 이름 매핑
        type_names = {
            AutomationTaskType.SCHEDULE_CALENDAR: "일정 등록",
            AutomationTaskType.PUBLISH_SNS: "SNS 게시물 발행",
            AutomationTaskType.SEND_EMAIL: "이메일 발송",
            AutomationTaskType.SEND_REMINDER: "리마인더 설정",
            AutomationTaskType.SEND_MESSAGE: "메시지 발송"
        }
        
        type_name = type_names.get(automation_type, "자동화 작업")
        
        # 기본 메시지
        template = f"🤖 **{type_name} 자동화 설정**\n\n"
        
        # 이미 제공된 정보 표시
        if automation_info and automation_info.get("task_data"):
            task_data = automation_info["task_data"]
            provided_fields = [field for field in task_data.keys() if task_data[field]]
            
            if provided_fields:
                template += "✅ **이미 제공된 정보:**\n"
                for field in provided_fields:
                    field_korean = self._get_field_korean_name(field)
                    value = task_data[field]
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    template += f"- {field_korean}: {value}\n"
                template += "\n"
        
        # 누락된 필수 정보 표시
        if missing_fields:
            template += "❌ **추가로 필요한 정보:**\n"
            for field in missing_fields:
                field_korean = self._get_field_korean_name(field)
                field_example = self._get_field_example(automation_type, field)
                template += f"- {field_korean}: {field_example}\n"
            template += "\n"
        
        # 사용 예시 제공
        template += self._get_usage_example(automation_type, missing_fields)
        
        # 히스토리 컨텍스트 추가
        if conversation_history:
            history_context = self._extract_automation_context_from_history(conversation_history)
            if history_context:
                template += f"\n\n📝 **이전 대화에서 확인된 정보:**\n{history_context}"
        
        template += "\n\n💬 **다음 메시지에서 누락된 정보를 포함하여 다시 요청해주세요!**"
        
        return template
    
    def _get_field_korean_name(self, field: str) -> str:
        """필드명을 한글로 변환"""
        field_names = {
            "title": "제목",
            "start_time": "시작 시간",
            "end_time": "종료 시간",
            "platform": "플랫폼",
            "content": "내용",
            "to": "받는사람",
            "subject": "제목",
            "body": "본문",
            "recipient": "받는사람",
            "reminder_time": "알림 시간",
            "description": "설명",
            "location": "장소"
        }
        return field_names.get(field, field)
    
    def _get_field_example(self, automation_type: AutomationTaskType, field: str) -> str:
        """필드별 예시 값 제공"""
        examples = {
            AutomationTaskType.SCHEDULE_CALENDAR: {
                "title": "주간 팀 미팅",
                "start_time": "2024-01-15 14:00",
                "end_time": "2024-01-15 15:30"
            },
            AutomationTaskType.PUBLISH_SNS: {
                "platform": "Twitter 또는 Facebook",
                "content": "오늘의 제품 소개..."
            },
            AutomationTaskType.SEND_EMAIL: {
                "to": "example@email.com",
                "subject": "회의 일정 안내",
                "body": "안녕하세요. 다음 주 회의에 대해..."
            },
            AutomationTaskType.SEND_REMINDER: {
                "title": "마감일 리마인더",
                "reminder_time": "2024-01-15 09:00"
            },
            AutomationTaskType.SEND_MESSAGE: {
                "platform": "Slack 또는 Teams",
                "content": "작업 완료 알림",
                "recipient": "@username 또는 #channel"
            }
        }
        
        type_examples = examples.get(automation_type, {})
        return type_examples.get(field, "(예시 값)")
    
    def _get_usage_example(self, automation_type: AutomationTaskType, missing_fields: List[str]) -> str:
        """사용 예시 제공"""
        examples = {
            AutomationTaskType.SCHEDULE_CALENDAR: {
                "example": "내일 오후 2시에 주간 팀 미팅 일정을 등록해주세요. 3시 30분까지 예정입니다.",
                "key_points": ["제목", "날짜", "시간"]
            },
            AutomationTaskType.PUBLISH_SNS: {
                "example": "Twitter에 '오늘의 신제품 소개! 혁신적인 기능으로 더 나은 경험을 제공합니다.' 라는 내용으로 게시해주세요.",
                "key_points": ["플랫폼", "게시 내용"]
            },
            AutomationTaskType.SEND_EMAIL: {
                "example": "kim@company.com에게 '회의 일정 안내'라는 제목으로 내일 회의 일정을 알리는 이메일을 보내주세요.",
                "key_points": ["받는사람", "제목", "본문"]
            },
            AutomationTaskType.SEND_REMINDER: {
                "example": "내일 오전 9시에 '마감일 리마인더' 알림을 설정해주세요.",
                "key_points": ["알림 제목", "시간"]
            },
            AutomationTaskType.SEND_MESSAGE: {
                "example": "Slack에서 #팀채널에 '작업 완료 알림: 주간 보고서 작성이 완료되었습니다.'라는 메시지를 보내주세요.",
                "key_points": ["플랫폼", "받는사람/채널", "메시지 내용"]
            }
        }
        
        example_data = examples.get(automation_type, {})
        example_text = example_data.get("example", "")
        key_points = example_data.get("key_points", [])
        
        if example_text:
            template = f"📝 **사용 예시:**\n{example_text}\n\n"
            
            if missing_fields:
                template += "❗ **주의사항:** "
                missing_korean = [self._get_field_korean_name(field) for field in missing_fields]
                template += f"{', '.join(missing_korean)}을(를) 명확히 알려주세요."
            
            return template
        
        return ""
    
    def _get_schedule_template(self) -> str:
        """일정 템플릿"""
        return """
📅 **일정 등록 템플릿**

다음 형식에 맞게 일정 정보를 입력해주세요:

**필수 정보:**
- 제목: [일정 제목]
- 날짜: [YYYY-MM-DD 형식]
- 시작시간: [HH:MM 형식]

**선택 정보:**
- 종료시간: [HH:MM 형식]
- 설명: [상세 내용]
- 알림: [숫자]분 전

**예시:**
제목: 주간 팀 미팅
날짜: 2024-01-15
시작시간: 14:00
종료시간: 15:30
설명: Q4 성과 논의
알림: 15분 전
        """
    
    def _get_sns_template(self) -> str:
        """SNS 템플릿"""
        return """
📱 **SNS 발행 템플릿**

다음 형식에 맞게 SNS 발행 정보를 입력해주세요:

**필수 정보:**
- 플랫폼: [Twitter, Facebook, Instagram, LinkedIn 등]
- 내용: [발행할 내용]

**선택 정보:**
- 예약시간: [YYYY-MM-DD HH:MM 형식]
- 해시태그: [관련 태그들]
- 이미지: [첨부할 이미지 경로]
        """
    
    def _get_email_template(self) -> str:
        """이메일 템플릿"""
        return """
📧 **이메일 발송 템플릿**

다음 형식에 맞게 이메일 정보를 입력해주세요:

**필수 정보:**
- 받는사람: [이메일 주소]
- 제목: [이메일 제목]
- 내용: [이메일 본문]

**선택 정보:**
- 예약시간: [YYYY-MM-DD HH:MM 형식]
- 참조: [CC 이메일 주소들]
- 첨부파일: [첨부할 파일 경로]
        """
    
    def _get_reminder_template(self) -> str:
        """리마인더 템플릿"""
        return """
⏰ **리마인더 설정 템플릿**

다음 형식에 맞게 리마인더 정보를 입력해주세요:

**필수 정보:**
- 제목: [리마인더 제목]
- 알림시간: [YYYY-MM-DD HH:MM 형식]

**선택 정보:**
- 내용: [상세 내용]
- 반복: [한번만, 매일, 매주, 매월]
- 사전알림: [10분 전, 1시간 전, 1일 전]
        """
    
    def _get_message_template(self) -> str:
        """메시지 템플릿"""
        return """
💬 **메시지 발송 템플릿**

다음 형식에 맞게 메시지 정보를 입력해주세요:

**필수 정보:**
- 플랫폼: [SMS, Slack, Teams, KakaoTalk 등]
- 받는사람: [전화번호 또는 사용자명]
- 내용: [메시지 내용]

**선택 정보:**
- 예약시간: [YYYY-MM-DD HH:MM 형식]
- 우선순위: [높음, 보통, 낮음]
        """
    
    def _fallback_intent_analysis(self, message: str) -> Dict[str, Any]:
        """백업 의도 분석"""
        message_lower = message.lower()
        
        # 긴급도 분석
        urgency = "medium"
        if any(keyword in message_lower for keyword in ["긴급", "즉시", "오늘", "지금"]):
            urgency = "high"
        elif any(keyword in message_lower for keyword in ["언젠가", "나중에", "여유"]):
            urgency = "low"
        
        # 의도 분석
        intent = "general_inquiry"
        if any(keyword in message_lower for keyword in ["일정", "스케줄", "미팅"]):
            intent = "schedule_management"
        elif any(keyword in message_lower for keyword in ["자동화", "자동", "반복"]):
            intent = "task_automation"
        elif any(keyword in message_lower for keyword in ["우선순위", "중요도"]):
            intent = "task_prioritization"
        elif any(keyword in message_lower for keyword in ["도구", "프로그램", "AI"]):
            intent = "tool_stack"
        
        return {
            "intent": intent,
            "urgency": urgency,
            "confidence": 0.3
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """서비스 상태 조회"""
        try:
            return {
                "service": "agent",
                "status": "healthy",
                "cache_size": len(self.cache_manager._cache),
                "components": {
                    "llm_handler": "active",
                    "rag_manager": "active", 
                    "automation_manager": "active"
                }
            }
        except Exception as e:
            logger.error(f"상태 조회 실패: {e}")
            return {"service": "agent", "status": "error", "error": str(e)}
    
    async def cleanup(self):
        """리소스 정리"""
        try:
            expired_count = self.cache_manager.cleanup_expired()
            
            # DB 세션 정리
            if hasattr(self, 'db_session') and self.db_session:
                self.db_session.close()
                
            # 자동화 서비스 정리
            if hasattr(self, 'automation_manager'):
                await self.automation_manager.cleanup()
                
            logger.info(f"에이전트 서비스 정리 완료 - 만료된 캐시 {expired_count}개 정리")
        except Exception as e:
            logger.error(f"에이전트 서비스 정리 실패: {e}")
