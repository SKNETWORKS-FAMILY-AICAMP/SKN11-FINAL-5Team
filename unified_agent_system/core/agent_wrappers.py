"""
각 에이전트를 래핑하여 통일된 인터페이스 제공
"""

import asyncio
import time
import logging
import httpx
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from .models import AgentType, AgentResponse, UnifiedRequest
from .config import get_system_config

from shared_modules.database import get_connection
import shared_modules.queries as queries

logger = logging.getLogger(__name__)

def extract_template_keyword(text: str) -> str:
    """기존 키워드 매핑 함수 (그대로 사용)"""
    text_lower = text.lower()
    mapping = {
        "생일": "생일/기념일", 
        "기념일": "생일/기념일",
        "축하": "생일/기념일",
        "리뷰": "리뷰 요청", 
        "후기": "리뷰 요청",
        "평가": "리뷰 요청",
        "예약": "예약",
        "설문": "설문 요청",
        "감사": "구매 후 안내", 
        "출고": "구매 후 안내", 
        "배송": "구매 후 안내",
        "발송": "구매 후 안내",
        "재구매": "재구매 유도", 
        "재방문": "재방문",
        "다시": "재구매 유도",
        "VIP": "고객 맞춤 메시지", 
        "맞춤": "고객 맞춤 메시지",
        "특별": "고객 맞춤 메시지",
        "이벤트": "이벤트 안내", 
        "할인": "이벤트 안내", 
        "프로모션": "이벤트 안내",
        "세일": "이벤트 안내"
    }
    
    for keyword, category in mapping.items():
        if keyword in text_lower:
            return category
    return None

async def auto_save_templates_for_user(user_id: int, keyword_category: str) -> list:
    """키워드 카테고리에 맞는 템플릿을 자동 저장"""
    try:
        with get_connection() as db:
            # 해당 카테고리의 기본 템플릿들 조회 (user_id=3)
            default_templates = queries.get_templates_by_type(keyword_category)
            saved_templates = []
            
            for template in default_templates[:2]:  # 최대 2개만 자동 저장
                # 이미 사용자가 저장한 템플릿인지 확인
                existing = queries.get_templates_by_user(
                    db, user_id, 
                    template_type=template['template_type'],
                    channel_type=template['channel_type']
                )
                
                if not existing:  # 중복이 아니면 저장
                    new_template = queries.create_template_message(
                        db=db,
                        user_id=user_id,
                        template_type=template['template_type'],
                        channel_type=template['channel_type'],
                        title=f"{template['title']} (AI 추천)",
                        content=template['content'],
                        content_type=template.get('content_type')
                    )
                    
                    if new_template:
                        saved_templates.append({
                            'title': new_template.title,
                            'template_type': new_template.template_type
                        })
                        logger.info(f"✅ 자동 저장: {new_template.title} (user: {user_id})")
            
            return saved_templates
            
    except Exception as e:
        logger.error(f"❌ 템플릿 자동 저장 실패: {e}")
        return []


class BaseAgentWrapper(ABC):
    """에이전트 래퍼 기본 클래스"""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.config = get_system_config().agents[agent_type]
        self.client = httpx.AsyncClient(timeout=self.config.timeout)
    
    @abstractmethod
    async def process_request(self, request: UnifiedRequest) -> AgentResponse:
        """요청 처리 (각 에이전트별로 구현)"""
        pass
    
    async def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """HTTP 요청 실행"""
        try:
            response = await self.client.post(
                self.config.endpoint,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()
            
            # create_success_response로 래핑된 응답인 경우 data 부분만 추출
            if isinstance(result, dict) and "success" in result and "data" in result:
                if result.get("success"):
                    return result["data"]
                else:
                    # 에러 응답인 경우
                    error_msg = result.get("error", "알 수 없는 오류")
                    raise Exception(f"Agent error: {error_msg}")
            
            # 직접 응답인 경우 그대로 반환
            return result
            
        except httpx.TimeoutException:
            logger.error(f"{self.agent_type} 타임아웃")
            raise Exception(f"{self.agent_type} 응답 시간 초과")
        except httpx.HTTPStatusError as e:
            logger.error(f"{self.agent_type} HTTP 오류: {e.response.status_code}")
            raise Exception(f"{self.agent_type} 서비스 오류: {e.response.status_code}")
        except Exception as e:
            logger.error(f"{self.agent_type} 요청 실패: {e}")
            raise Exception(f"{self.agent_type} 서비스 연결 실패")
    
    async def health_check(self) -> bool:
        """에이전트 상태 확인"""
        try:
            # 다양한 health endpoint 패턴 지원
            health_url = self.config.endpoint
            if "/agent/query" in health_url:
                health_url = health_url.replace("/agent/query", "/health")
            elif "/query" in health_url:
                health_url = health_url.replace("/query", "/health")
            else:
                # 기본 health endpoint 추가
                health_url = health_url.rstrip('/') + "/health"
            
            response = await self.client.get(health_url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """리소스 정리"""
        await self.client.aclose()


class BusinessPlanningAgentWrapper(BaseAgentWrapper):
    """비즈니스 플래닝 에이전트 래퍼"""
    
    def __init__(self):
        super().__init__(AgentType.BUSINESS_PLANNING)
    
    async def process_request(self, request: UnifiedRequest) -> AgentResponse:
        start_time = time.time()
        
        try:
            # 비즈니스 플래닝 에이전트 API 형식에 맞게 변환
            payload = {
                "user_id": request.user_id,
                "conversation_id": request.conversation_id,
                "message": request.message,
                "persona": "common"  # 기본 페르소나 설정
            }
            
            result = await self._make_request(payload)
            
            processing_time = time.time() - start_time
            
            return AgentResponse(
                agent_type=self.agent_type,
                response=result.get("response") or result.get("answer", "응답을 받지 못했습니다."),
                confidence=0.85,  # 기본값
                sources=result.get("sources", ""),
                metadata={
                    "topics": result.get("topics", []),
                    "type": result.get("type", "general"),
                    "title": result.get("title", ""),
                    "content": result.get("content", "")
                },
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"비즈니스 플래닝 에이전트 처리 실패: {e}")
            return AgentResponse(
                agent_type=self.agent_type,
                response=f"비즈니스 플래닝 서비스에 일시적인 문제가 발생했습니다: {str(e)}",
                confidence=0.0,
                processing_time=time.time() - start_time
            )


class CustomerServiceAgentWrapper(BaseAgentWrapper):
    """고객 서비스 에이전트 래퍼"""
    
    def __init__(self):
        super().__init__(AgentType.CUSTOMER_SERVICE)
    
    async def process_request(self, request: UnifiedRequest) -> AgentResponse:
        start_time = time.time()
        
        try:
            # 🆕 키워드 감지 및 자동 저장
            keyword_category = extract_template_keyword(request.message)
            saved_templates = []
            
            # 고객 서비스 관련 키워드만 처리
            cs_keywords = ["리뷰 요청", "구매 후 안내", "예약", "설문 요청", "고객 맞춤 메시지"]
            if keyword_category and keyword_category in cs_keywords:
                logger.info(f"🔍 CS 키워드 감지: {keyword_category} (user: {request.user_id})")
                saved_templates = await auto_save_templates_for_user(request.user_id, keyword_category)
            
            # 고객 서비스 에이전트 API 형식에 맞게 변환
            payload = {
                "user_id": request.user_id,
                "conversation_id": request.conversation_id,
                "message": request.message,
                "persona": "common"  # 기본 페르소나 설정
            }
            
            result = await self._make_request(payload)
            processing_time = time.time() - start_time
            
            # 🆕 응답에 자동 저장 정보 추가
            response_text = result.get("answer", "응답을 받지 못했습니다.")
            
            if saved_templates:
                template_info = "\n\n💾 **관련 템플릿 저장됨**:\n"
                for template in saved_templates:
                    template_info += f"• {template['title']}\n"
                template_info += "\n📋 마이페이지에서 확인하고 수정하세요!"
                response_text += template_info
            
            return AgentResponse(
                agent_type=self.agent_type,
                response=result.get("answer") or result.get("response", "응답을 받지 못했습니다."),
                confidence=0.85,
                sources="",  # 고객 서비스 에이전트는 sources를 따로 반환하지 않음
                metadata={
                    "topics": result.get("topics", []),
                    "history": result.get("history", []),
                    # 🆕 자동 저장 정보 추가
                    "auto_saved_templates": saved_templates,
                    "keyword_category": keyword_category
                },
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"고객 서비스 에이전트 처리 실패: {e}")
            return AgentResponse(
                agent_type=self.agent_type,
                response=f"고객 서비스에 일시적인 문제가 발생했습니다: {str(e)}",
                confidence=0.0,
                processing_time=time.time() - start_time
            )


class MarketingAgentWrapper(BaseAgentWrapper):
    """마케팅 에이전트 래퍼"""
    
    def __init__(self):
        super().__init__(AgentType.MARKETING)
    
    async def process_request(self, request: UnifiedRequest) -> AgentResponse:
        start_time = time.time()
        
        try:
            # 🆕 키워드 감지 및 자동 저장
            keyword_category = extract_template_keyword(request.message)
            saved_templates = []
            
            if keyword_category:
                logger.info(f"🔍 키워드 감지: {keyword_category} (user: {request.user_id})")
                saved_templates = await auto_save_templates_for_user(request.user_id, keyword_category)
            
            # 마케팅 에이전트 API 형식에 맞게 변환
            payload = {
                "user_id": request.user_id,
                "conversation_id": request.conversation_id,
                "message": request.message,
                "persona": "common"  # 기본 페르소나 설정
            }
            
            result = await self._make_request(payload)
            processing_time = time.time() - start_time

            # 🆕 응답에 자동 저장 정보 추가
            response_text = result.get("answer", "응답을 받지 못했습니다.")
            
            if saved_templates:
                template_info = "\n\n💾 **템플릿 자동 저장 완료**:\n"
                for template in saved_templates:
                    template_info += f"• {template['title']}\n"
                template_info += "\n📋 마이페이지 > 내 템플릿에서 확인하고 수정하세요!"
                response_text += template_info
            
            return AgentResponse(
                agent_type=self.agent_type,
                response=result.get("answer") or result.get("response", "응답을 받지 못했습니다."),
                confidence=0.85,
                sources=result.get("sources", ""),
                metadata={
                    "topics": result.get("topics", []),
                    "conversation_id": result.get("conversation_id"),
                    "templates": result.get("templates", []),
                    "debug_info": result.get("debug_info", {}),
                    # 🆕 자동 저장 정보 추가
                    "auto_saved_templates": saved_templates,
                    "keyword_category": keyword_category
                },
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"마케팅 에이전트 처리 실패: {e}")
            return AgentResponse(
                agent_type=self.agent_type,
                response=f"마케팅 서비스에 일시적인 문제가 발생했습니다: {str(e)}",
                confidence=0.0,
                processing_time=time.time() - start_time
            )


class MentalHealthAgentWrapper(BaseAgentWrapper):
    """멘탈 헬스 에이전트 래퍼"""
    
    def __init__(self):
        super().__init__(AgentType.MENTAL_HEALTH)
    
    async def process_request(self, request: UnifiedRequest) -> AgentResponse:
        start_time = time.time()
        
        try:
            # 멘탈 헬스 에이전트 API 형식에 맞게 변환
            payload = {
                "user_id": request.user_id,
                "conversation_id": request.conversation_id,
                "message": request.message,
                "persona": "common"  # 기본 페르소나 설정
            }
            
            result = await self._make_request(payload)
            
            processing_time = time.time() - start_time
            
            return AgentResponse(
                agent_type=self.agent_type,
                response=result.get("response") or result.get("answer", "응답을 받지 못했습니다."),
                confidence=0.9,  # 멘탈 헬스는 높은 신뢰도
                sources="",
                metadata={
                    "emotion": result.get("emotion", "중립"),
                    "phq9_score": result.get("phq9_score"),
                    "phq9_level": result.get("phq9_level"),
                    "suggestions": result.get("suggestions", [])
                },
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"멘탈 헬스 에이전트 처리 실패: {e}")
            return AgentResponse(
                agent_type=self.agent_type,
                response=f"멘탈 헬스 서비스에 일시적인 문제가 발생했습니다: {str(e)}",
                confidence=0.0,
                processing_time=time.time() - start_time
            )


class TaskAutomationAgentWrapper(BaseAgentWrapper):
    """업무 자동화 에이전트 래퍼"""
    
    def __init__(self):
        super().__init__(AgentType.TASK_AUTOMATION)
    
    async def process_request(self, request: UnifiedRequest) -> AgentResponse:
        start_time = time.time()
        
        try:
            # 🆕 키워드 감지 및 자동 저장
            keyword_category = extract_template_keyword(request.message)
            saved_templates = []
            
            # 업무 자동화 관련 키워드만 처리
            automation_keywords = ["예약", "발송", "출고", "배송", "재구매 유도", "이벤트 안내"]
            if keyword_category and keyword_category in automation_keywords:
                logger.info(f"🔍 자동화 키워드 감지: {keyword_category} (user: {request.user_id})")
                saved_templates = await auto_save_templates_for_user(request.user_id, keyword_category)
            
            # 업무 자동화 에이전트 API 형식에 맞게 변환
            payload = {
                "user_id": request.user_id,
                "conversation_id": request.conversation_id,
                "message": request.message,
                "persona": "common"  # 기본 페르소나 설정
            }
            
            result = await self._make_request(payload)
            processing_time = time.time() - start_time
            
            # 🆕 응답에 자동 저장 정보 추가
            response_text = result.get("response", "응답을 받지 못했습니다.")
            
            if saved_templates:
                template_info = "\n\n💾 **자동화 템플릿 저장됨**:\n"
                for template in saved_templates:
                    template_info += f"• {template['title']}\n"
                template_info += "\n📋 마이페이지에서 확인하고 자동화에 활용하세요!"
                response_text += template_info
            
            return AgentResponse(
                agent_type=self.agent_type,
                response=result.get("response") or result.get("answer", "응답을 받지 못했습니다."),
                confidence=0.85,
                sources="",
                metadata={
                    "status": result.get("status", "success"),
                    "intent": result.get("intent", "general_inquiry"),
                    "urgency": result.get("urgency", "medium"),
                    "actions": result.get("actions", []),
                    "automation_created": result.get("automation_created", False),
                    # 🆕 자동 저장 정보 추가
                    "auto_saved_templates": saved_templates,
                    "keyword_category": keyword_category
                },
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"업무 자동화 에이전트 처리 실패: {e}")
            return AgentResponse(
                agent_type=self.agent_type,
                response=f"업무 자동화 서비스에 일시적인 문제가 발생했습니다: {str(e)}",
                confidence=0.0,
                processing_time=time.time() - start_time
            )


class AgentManager:
    """에이전트들을 관리하는 매니저 클래스"""
    
    def __init__(self):
        self.agents = {
            AgentType.BUSINESS_PLANNING: BusinessPlanningAgentWrapper(),
            AgentType.CUSTOMER_SERVICE: CustomerServiceAgentWrapper(),
            AgentType.MARKETING: MarketingAgentWrapper(),
            AgentType.MENTAL_HEALTH: MentalHealthAgentWrapper(),
            AgentType.TASK_AUTOMATION: TaskAutomationAgentWrapper()
        }
    
    async def process_request(self, agent_type: AgentType, request: UnifiedRequest) -> AgentResponse:
        """지정된 에이전트로 요청 처리"""
        if agent_type not in self.agents:
            raise ValueError(f"지원하지 않는 에이전트 타입: {agent_type}")
        
        agent = self.agents[agent_type]
        
        if not agent.config.enabled:
            raise Exception(f"{agent_type} 에이전트가 비활성화 상태입니다")
        
        return await agent.process_request(request)
    
    async def process_multiple_requests(self, agent_types: list, request: UnifiedRequest) -> Dict[AgentType, AgentResponse]:
        """여러 에이전트로 동시 요청 처리"""
        tasks = []
        valid_agents = []
        
        for agent_type in agent_types:
            if agent_type in self.agents and self.agents[agent_type].config.enabled:
                tasks.append(self.process_request(agent_type, request))
                valid_agents.append(agent_type)
        
        if not tasks:
            raise Exception("활성화된 에이전트가 없습니다")
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        response_dict = {}
        for i, result in enumerate(results):
            agent_type = valid_agents[i]
            if isinstance(result, Exception):
                logger.error(f"{agent_type} 처리 실패: {result}")
                response_dict[agent_type] = AgentResponse(
                    agent_type=agent_type,
                    response=f"서비스 오류: {str(result)}",
                    confidence=0.0,
                    processing_time=0.0
                )
            else:
                response_dict[agent_type] = result
        
        return response_dict
    
    async def health_check_all(self) -> Dict[AgentType, bool]:
        """모든 에이전트 상태 확인"""
        tasks = []
        agent_types = []
        
        for agent_type, agent in self.agents.items():
            tasks.append(agent.health_check())
            agent_types.append(agent_type)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        health_status = {}
        for i, result in enumerate(results):
            agent_type = agent_types[i]
            health_status[agent_type] = result if isinstance(result, bool) else False
        
        return health_status
    
    async def close_all(self):
        """모든 에이전트 리소스 정리"""
        tasks = [agent.close() for agent in self.agents.values()]
        await asyncio.gather(*tasks, return_exceptions=True)