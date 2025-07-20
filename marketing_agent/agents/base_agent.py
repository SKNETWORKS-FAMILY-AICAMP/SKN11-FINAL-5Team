"""
기본 마케팅 에이전트 클래스 (Base)
공통 모듈을 활용한 개선된 구조
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

# 공통 모듈 임포트
from shared_modules import (
    get_llm_manager,
    PromptTemplate,
    create_error_response
)

logger = logging.getLogger(__name__)

class BaseMarketingAgent(ABC):
    """모든 마케팅 에이전트의 기본 클래스"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """기본 에이전트 초기화"""
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        self.specialization = config.get("specialization", "마케팅")
        
        # 공통 LLM 매니저 사용
        self.llm_manager = get_llm_manager()
    
    @abstractmethod
    async def generate_response(self, query: str, context: Dict[str, Any] = None) -> str:
        """에이전트별 응답 생성 (하위 클래스에서 구현 필요)"""
        pass
    
    @abstractmethod
    def get_persona_prompt(self) -> str:
        """에이전트별 페르소나 프롬프트 (하위 클래스에서 구현 필요)"""
        pass
    
    # 공통 유틸리티 메서드
    
    def validate_query(self, query: str) -> bool:
        """쿼리 유효성 검사"""
        return bool(query and query.strip() and len(query.strip()) > 0)
    
    def preprocess_query(self, query: str) -> str:
        """쿼리 전처리"""
        return query.strip()
    
    def postprocess_response(self, response: str) -> str:
        """응답 후처리"""
        if not response:
            return "죄송합니다. 응답을 생성할 수 없습니다."
        return response.strip()
    
    def create_prompt_template(self, template_str: str) -> PromptTemplate:
        """프롬프트 템플릿 생성"""
        return PromptTemplate(template_str)
    
    async def generate_llm_response(self, messages: list, **kwargs) -> str:
        """LLM 응답 생성 (공통 메서드)"""
        try:
            response = await self.llm_manager.generate_response(messages, **kwargs)
            return self.postprocess_response(response)
            
        except Exception as e:
            self.logger.error(f"LLM 응답 생성 실패: {e}")
            return self.handle_error(e)
    
    def generate_llm_response_sync(self, messages: list, **kwargs) -> str:
        """LLM 응답 생성 동기 버전"""
        try:
            response = self.llm_manager.generate_response_sync(messages, **kwargs)
            return self.postprocess_response(response)
            
        except Exception as e:
            self.logger.error(f"LLM 응답 생성 실패: {e}")
            return self.handle_error(e)
    
    def log_interaction(self, query: str, response: str):
        """상호작용 로깅"""
        self.logger.info(f"[{self.name}] Query: {query[:100]}...")
        self.logger.info(f"[{self.name}] Response: {response[:100]}...")
    
    def get_agent_info(self) -> Dict[str, Any]:
        """에이전트 메타 정보"""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "specialization": self.specialization,
            "config": self.config,
            "llm_available": bool(self.llm_manager.get_available_models())
        }
    
    def handle_error(self, error: Exception, query: str = "") -> str:
        """에러 처리"""
        self.logger.error(f"[{self.name}] Error processing query '{query}': {str(error)}")
        return f"죄송합니다. {self.specialization} 상담 중 오류가 발생했습니다. 다시 시도해 주세요."
    
    def analyze_keywords(self, text: str, keywords_list: list) -> list:
        """키워드 분석 공통 메서드"""
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in keywords_list:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def get_relevance_score(self, query: str, topic_keywords: list) -> float:
        """토픽 관련성 점수 계산"""
        if not topic_keywords:
            return 0.0
        
        found_keywords = self.analyze_keywords(query, topic_keywords)
        return len(found_keywords) / len(topic_keywords)
