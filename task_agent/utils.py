"""
간소화된 유틸리티 함수들 v3
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List
from functools import lru_cache

# ===== ID 생성 =====

def generate_id(prefix: str = "id") -> str:
    """고유 ID 생성"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

# ===== 로깅 유틸리티 =====

class Logger:
    """간소화된 로깅 유틸리티"""
    
    @staticmethod
    def setup(level: str = "INFO"):
        """로깅 설정"""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    @staticmethod
    def log_api_request(endpoint: str, user_id: str):
        """API 요청 로깅"""
        logger = logging.getLogger(__name__)
        logger.info(f"API 요청: {endpoint} - 사용자: {user_id}")

# ===== 응답 포맷터 =====

class ResponseFormatter:
    """API 응답 포맷터"""
    
    @staticmethod
    def success(data: Any = None, message: str = "성공") -> Dict[str, Any]:
        """성공 응답"""
        return {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def error(error: str, code: str = "ERROR") -> Dict[str, Any]:
        """오류 응답"""
        return {
            "success": False,
            "error": error,
            "code": code,
            "timestamp": datetime.now().isoformat()
        }

# ===== 캐시 매니저 =====

class CacheManager:
    """간소화된 캐시 매니저"""
    
    def __init__(self, ttl: int = 1800):
        self._cache = {}
        self._ttl = ttl
    
    def get(self, key: str) -> Any:
        """캐시에서 값 조회"""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if (datetime.now() - timestamp).seconds < self._ttl:
                return value
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """캐시에 값 저장"""
        self._cache[key] = (value, datetime.now())
    
    def clear(self):
        """캐시 클리어"""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """만료된 캐시 정리"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if (now - timestamp).seconds >= self._ttl
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)

# ===== 텍스트 처리 =====

@lru_cache(maxsize=128)
def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """키워드 추출 (간단한 버전)"""
    # 간단한 키워드 추출 로직
    words = text.split()
    keywords = [word for word in words if len(word) > 2]
    return keywords[:max_keywords]

def truncate_text(text: str, max_length: int = 100) -> str:
    """텍스트 자르기"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
