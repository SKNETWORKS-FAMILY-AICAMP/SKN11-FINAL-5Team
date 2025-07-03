"""
TinkerBell 프로젝트 - 간소화된 유틸리티
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from app.core.config import CHROMA_PERSIST_DIR, GOOGLE_API_KEY, OPENAI_API_KEY

logger = logging.getLogger(__name__)

# ===== ID 생성 =====

def generate_id(prefix: str = "item") -> str:
    """ID 생성"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

# ===== 캐시 관리 =====

class CacheManager:
    """간단한 캐시 관리"""
    
    def __init__(self, default_ttl: int = 3600):
        self._cache = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Any:
        """캐시에서 값 조회"""
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.now() < expiry:
                return value
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """캐시에 값 저장"""
        ttl = ttl or self.default_ttl
        expiry = datetime.now() + timedelta(seconds=ttl)
        self._cache[key] = (value, expiry)
    
    def clear(self) -> None:
        """캐시 전체 삭제"""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """만료된 캐시 정리"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if now >= expiry
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)

# ===== 응답 포맷터 =====

class ResponseFormatter:
    """응답 포맷 유틸리티"""
    
    @staticmethod
    def success_response(data: Any = None, message: str = "성공") -> Dict[str, Any]:
        """성공 응답 포맷"""
        response = {
            "status": "success",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if data is not None:
            response["data"] = data
        
        return response
    
    @staticmethod
    def error_response(error: str, code: str = "GENERAL_ERROR") -> Dict[str, Any]:
        """에러 응답 포맷"""
        return {
            "status": "error",
            "error": {
                "code": code,
                "message": error
            },
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def paginated_response(items: List[Any], page: int = 1, 
                          per_page: int = 20, total: int = None) -> Dict[str, Any]:
        """페이지네이션 응답 포맷"""
        total = total or len(items)
        total_pages = (total + per_page - 1) // per_page
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_items = items[start_idx:end_idx]
        
        return {
            "status": "success",
            "data": {
                "items": page_items,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            },
            "timestamp": datetime.now().isoformat()
        }

# ===== 로깅 유틸리티 =====

class LoggingUtils:
    """로깅 유틸리티"""
    
    @staticmethod
    def setup_logging(log_level: str = "INFO"):
        """로깅 설정"""
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('task_agent.log')
            ]
        )
    
    @staticmethod
    def log_api_request(endpoint: str, user_id: str, data: Dict[str, Any] = None):
        """API 요청 로깅"""
        logger.info(f"API 요청: {endpoint} | 사용자: {user_id}")
        if data:
            logger.debug(f"요청 데이터: {data}")
    
    @staticmethod
    def log_performance(function_name: str, execution_time: float):
        """성능 로깅"""
        logger.info(f"성능: {function_name} 실행시간: {execution_time:.3f}초")

# ===== 데이터 검증 =====

class DataValidator:
    """데이터 검증 유틸리티"""
    
    @staticmethod
    def validate_task_data(task_data: Dict[str, Any]) -> Dict[str, Any]:
        """업무 데이터 검증"""
        errors = []
        
        # 필수 필드 검증
        if not task_data.get("title"):
            errors.append("제목은 필수입니다")
        
        # 우선순위 검증
        valid_priorities = ["high", "medium", "low"]
        priority = task_data.get("priority", "medium")
        if priority not in valid_priorities:
            errors.append(f"잘못된 우선순위: {priority}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }

# ===== 시간 유틸리티 =====

class TimeUtils:
    """시간 관련 유틸리티"""
    
    @staticmethod
    def parse_datetime(dt_str: str) -> Optional[datetime]:
        """문자열을 datetime으로 파싱"""
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            try:
                return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            except:
                logger.warning(f"날짜 파싱 실패: {dt_str}")
                return None
    
    @staticmethod
    def get_time_until_deadline(due_date: datetime) -> Dict[str, Any]:
        """마감일까지 남은 시간 계산"""
        now = datetime.now()
        time_diff = due_date - now
        
        if time_diff.total_seconds() < 0:
            return {
                "is_overdue": True,
                "days": abs(time_diff.days),
                "urgency": "overdue"
            }
        
        days = time_diff.days
        
        # 긴급도 판정
        if days == 0:
            urgency = "critical"
        elif days <= 1:
            urgency = "urgent"
        elif days <= 7:
            urgency = "high"
        else:
            urgency = "medium"
        
        return {
            "is_overdue": False,
            "days": days,
            "urgency": urgency
        }

# ===== 설정 검증 =====

class ConfigValidator:
    """설정 검증 유틸리티"""
    
    @staticmethod
    def validate_environment() -> Dict[str, Any]:
        """환경 설정 검증"""
        from .config import config
        
        issues = []
        warnings = []
        
        # API 키 검증
        if not OPENAI_API_KEY:
            issues.append("OPENAI_API_KEY가 설정되지 않았습니다")
        
        if not GOOGLE_API_KEY:
            warnings.append("GOOGLE_API_KEY가 설정되지 않았습니다")
        
        # 디렉토리 검증
        import os
        if not os.path.exists(CHROMA_PERSIST_DIR):
            warnings.append(f"Chroma 저장 디렉토리가 없습니다: {CHROMA_PERSIST_DIR}")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }
