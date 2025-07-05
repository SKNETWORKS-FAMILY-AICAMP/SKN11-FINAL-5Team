"""
간소화된 업무지원 에이전트 v3
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from models import UserQuery, QueryResponse, AutomationRequest, AutomationResponse, PersonaType
from llm_handler import LLMHandler
from rag import RAGManager
from automation import AutomationManager
from utils import CacheManager, generate_id

logger = logging.getLogger(__name__)

class TaskAgent:
    """간소화된 업무지원 에이전트"""
    
    def __init__(self):
        """에이전트 초기화"""
        self.llm_handler = LLMHandler()
        self.rag_manager = RAGManager()
        self.automation_manager = AutomationManager()
        self.cache_manager = CacheManager()
        
        logger.info("업무지원 에이전트 v3 초기화 완료")

    async def process_query(self, query: UserQuery, conversation_history: List[Dict] = None) -> QueryResponse:
        """사용자 쿼리 처리"""
        try:
            # 캐시 확인
            cache_key = f"query_{hash(query.message)}_{query.persona.value}"
            cached_response = self.cache_manager.get(cache_key)
            if cached_response:
                cached_response["conversation_id"] = query.conversation_id or ""
                return QueryResponse(**cached_response)
            
            # 의도 분석
            intent_analysis = await self.llm_handler.analyze_intent(
                query.message, query.persona, conversation_history
            )
            
            # 자동화 요청인지 확인
            automation_type = await self.llm_handler.classify_automation_intent(query.message)
            
            # 워크플로우 결정
            if automation_type:
                response = await self._handle_automation_workflow(
                    query, automation_type, intent_analysis, conversation_history
                )
            else:
                response = await self._handle_consultation_workflow(
                    query, intent_analysis, conversation_history
                )
            
            # 캐시 저장
            self.cache_manager.set(cache_key, response.dict())
            
            return response
                
        except Exception as e:
            logger.error(f"쿼리 처리 실패: {e}")
            return QueryResponse(
                status="error",
                response="죄송합니다. 요청을 처리하는 중에 오류가 발생했습니다.",
                conversation_id=query.conversation_id or "",
                intent="general_inquiry"
            )

    async def _handle_consultation_workflow(self, query: UserQuery, intent_analysis: Dict, 
                                          conversation_history: List[Dict] = None) -> QueryResponse:
        """상담 워크플로우 처리"""
        # 지식 검색
        search_result = await self.rag_manager.search_knowledge(
            query.message, query.persona, intent_analysis["intent"]
        )
        
        # 컨텍스트 구성
        context = ""
        if search_result.chunks:
            context = "\n\n".join([chunk.content for chunk in search_result.chunks[:3]])
        
        # 응답 생성
        response_text = await self.llm_handler.generate_response(
            query.message, query.persona, context, conversation_history
        )
        
        # 후속 액션 생성
        actions = self._generate_follow_up_actions(intent_analysis["intent"], query.persona)
        
        return QueryResponse(
            status="success",
            response=response_text,
            conversation_id=query.conversation_id or "",
            intent=intent_analysis["intent"],
            urgency=intent_analysis["urgency"],
            confidence=intent_analysis["confidence"],
            actions=actions,
            sources=search_result.sources
        )

    async def _handle_automation_workflow(self, query: UserQuery, automation_type: str, 
                                        intent_analysis: Dict, conversation_history: List[Dict] = None) -> QueryResponse:
        """자동화 워크플로우 처리"""
        # 정보 추출
        extraction_type = self._map_automation_to_extraction(automation_type)
        extracted_info = await self.llm_handler.extract_information(
            query.message, extraction_type, conversation_history
        )
        
        if extracted_info:
            # 자동화 작업 생성
            automation_request = AutomationRequest(
                user_id=int(query.user_id),
                task_type=automation_type,
                title=self._generate_automation_title(automation_type, extracted_info),
                task_data=extracted_info
            )
            
            automation_response = await self.automation_manager.create_automation_task(automation_request)
            
            return QueryResponse(
                status="success",
                response=automation_response.message,
                conversation_id=query.conversation_id or "",
                intent=intent_analysis["intent"],
                urgency=intent_analysis["urgency"],
                confidence=intent_analysis["confidence"],
                actions=[{
                    "type": "automation_created",
                    "data": {"task_id": automation_response.task_id},
                    "description": "자동화 작업이 생성되었습니다."
                }]
            )
        else:
            # 템플릿 제공
            template = self._get_automation_template(automation_type)
            return QueryResponse(
                status="template_needed",
                response=template,
                conversation_id=query.conversation_id or "",
                intent=intent_analysis["intent"],
                urgency=intent_analysis["urgency"],
                confidence=intent_analysis["confidence"]
            )

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
        if automation_type == "schedule_calendar":
            return f"일정 등록: {extracted_info.get('title', '제목 없음')}"
        elif automation_type == "send_email":
            return f"이메일 발송: {extracted_info.get('subject', '제목 없음')}"
        elif automation_type == "publish_sns":
            content = extracted_info.get('content', '')
            return f"SNS 발행: {content[:30]}..." if len(content) > 30 else f"SNS 발행: {content}"
        elif automation_type == "send_reminder":
            return f"리마인더: {extracted_info.get('title', '제목 없음')}"
        else:
            return f"{automation_type} 자동화 작업"

    def _generate_follow_up_actions(self, intent: str, persona: PersonaType) -> List[Dict[str, Any]]:
        """후속 액션 생성"""
        actions = []
        
        if intent == "task_automation":
            actions.append({
                "type": "automation_guide",
                "description": "자동화 설정 가이드를 확인하시겠습니까?"
            })
        elif intent == "schedule_management":
            actions.append({
                "type": "calendar_integration",
                "description": "캘린더 연동을 설정하시겠습니까?"
            })
        elif intent == "tool_recommendation":
            actions.append({
                "type": "tool_setup",
                "description": "추천 도구 설정을 도와드릴까요?"
            })
        
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

예시: "내일 오후 2시에 팀 미팅"
""",
            
            "send_email": """
📧 **이메일 발송을 위한 정보를 알려주세요:**

• 받는사람: [이메일 주소]
• 제목: [이메일 제목]
• 내용: [이메일 본문]
• 예약시간: [YYYY-MM-DD HH:MM] (선택사항)

예시: "john@company.com에게 '월간 보고서' 제목으로 보고서 첨부해서 보내줘"
""",
            
            "publish_sns": """
📱 **SNS 발행을 위한 정보를 알려주세요:**

• 플랫폼: [Twitter, Facebook, Instagram 등]
• 내용: [게시물 내용]
• 예약시간: [YYYY-MM-DD HH:MM] (선택사항)
• 해시태그: [#태그1 #태그2] (선택사항)

예시: "트위터에 '새로운 프로젝트 출시!' 내용으로 #프로젝트 #출시 태그와 함께 게시"
""",
            
            "send_reminder": """
⏰ **리마인더 설정을 위한 정보를 알려주세요:**

• 제목: [리마인더 제목]
• 알림시간: [YYYY-MM-DD HH:MM]
• 내용: [상세 내용] (선택사항)

예시: "내일 오전 9시에 '회의 준비' 리마인더 설정해줘"
"""
        }
        
        return templates.get(automation_type, "자동화 설정을 위한 추가 정보가 필요합니다.")

    # ===== 자동화 관리 =====

    async def create_automation_task(self, request: AutomationRequest) -> AutomationResponse:
        """자동화 작업 생성"""
        return await self.automation_manager.create_automation_task(request)

    async def get_automation_status(self, task_id: int) -> Dict[str, Any]:
        """자동화 작업 상태 조회"""
        return await self.automation_manager.get_task_status(task_id)

    async def cancel_automation_task(self, task_id: int) -> bool:
        """자동화 작업 취소"""
        return await self.automation_manager.cancel_task(task_id)

    # ===== 시스템 관리 =====

    async def get_status(self) -> Dict[str, Any]:
        """에이전트 상태 조회"""
        try:
            return {
                "agent_version": "3.0.0",
                "status": "healthy",
                "cache_size": len(self.cache_manager._cache),
                "components": {
                    "llm_handler": "active",
                    "rag_manager": "active",
                    "automation_manager": "active"
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"상태 조회 실패: {e}")
            return {"status": "error", "error": str(e)}

    async def cleanup_resources(self):
        """리소스 정리"""
        try:
            self.cache_manager.cleanup_expired()
            await self.automation_manager.shutdown()
            logger.info("리소스 정리 완료")
        except Exception as e:
            logger.error(f"리소스 정리 실패: {e}")
