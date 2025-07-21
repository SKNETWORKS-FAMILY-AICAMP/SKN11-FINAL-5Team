"""
기본 마케팅 에이전트 클래스 (Base)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseMarketingAgent(ABC):
    """모든 마케팅 에이전트의 기본 클래스"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        self.specialization = config.get("specialization", "마케팅")

    @abstractmethod
    def generate_response(self, query: str, context: Dict[str, Any] = None) -> str:
        """에이전트별 응답 생성"""
        pass

    @abstractmethod
    def get_persona_prompt(self) -> str:
        """에이전트별 페르소나 프롬프트"""
        pass

    # --- 공통 유틸 메서드 ---
    
    def validate_query(self, query: str) -> bool:
        """쿼리 유효성 검사"""
        return bool(query and query.strip())

    def log_interaction(self, query: str, response: str):
        """상호작용 로깅"""
        self.logger.info(f"[{self.name}] Query: {query[:100]}...")
        self.logger.info(f"[{self.name}] Response: {response[:100]}...")

    def preprocess_query(self, query: str) -> str:
        """쿼리 전처리"""
        return query.strip()

    def postprocess_response(self, response: str) -> str:
        """응답 후처리"""
        return response.strip()

    def get_agent_info(self) -> Dict[str, Any]:
        """에이전트 메타 정보"""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "specialization": self.specialization,
            "config": self.config
        }

    def handle_error(self, error: Exception, query: str = "") -> str:
        """에러 처리"""
        self.logger.error(f"[{self.name}] Error processing query '{query}': {str(error)}")
        return f"❗ 죄송합니다. 처리 중 오류가 발생했습니다.\n\n{str(error)}"
