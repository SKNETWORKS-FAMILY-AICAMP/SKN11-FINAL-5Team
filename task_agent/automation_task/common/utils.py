"""
공통 유틸리티 함수들
"""

import re
import json
import hashlib
import secrets
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
import logging

logger = logging.getLogger(__name__)


class ValidationUtils:
    """데이터 검증 유틸리티"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """이메일 주소 형식 검증"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_valid_phone(phone: str, country_code: str = "KR") -> bool:
        """전화번호 형식 검증"""
        # 한국 전화번호 패턴
        if country_code.upper() == "KR":
            # 010-1234-5678, 02-123-4567, +82-10-1234-5678 등
            patterns = [
                r'^010-\d{4}-\d{4}$',
                r'^0\d{1,2}-\d{3,4}-\d{4}$',
                r'^\+82-10-\d{4}-\d{4}$',
                r'^\+82-\d{1,2}-\d{3,4}-\d{4}$'
            ]
            return any(re.match(pattern, phone) for pattern in patterns)
        
        # 국제 전화번호 기본 패턴
        pattern = r'^\+\d{1,3}-\d{1,14}$'
        return re.match(pattern, phone) is not None
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """URL 형식 검증"""
        pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
        return re.match(pattern, url) is not None
    
    @staticmethod
    def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
        """입력 텍스트 정리"""
        if not text:
            return ""
        
        # 기본 정리
        text = text.strip()
        
        # HTML 태그 제거 (기본적인 XSS 방지)
        text = re.sub(r'<[^>]+>', '', text)
        
        # 길이 제한
        if max_length and len(text) > max_length:
            text = text[:max_length]
        
        return text


class DateTimeUtils:
    """날짜/시간 처리 유틸리티"""
    
    @staticmethod
    def parse_datetime(date_string: str, formats: List[str] = None) -> Optional[datetime]:
        """다양한 형식의 날짜 문자열을 datetime으로 변환"""
        if not formats:
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%dT%H:%M",
                "%Y-%m-%d",
                "%m/%d/%Y %H:%M:%S",
                "%m/%d/%Y %H:%M",
                "%m/%d/%Y",
                "%d/%m/%Y %H:%M:%S",
                "%d/%m/%Y %H:%M",
                "%d/%m/%Y"
            ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        logger.warning(f"날짜 파싱 실패: {date_string}")
        return None
    
    @staticmethod
    def format_datetime(dt: datetime, format_type: str = "iso") -> str:
        """datetime을 지정된 형식으로 포맷"""
        if format_type == "iso":
            return dt.isoformat()
        elif format_type == "korean":
            return dt.strftime("%Y년 %m월 %d일 %H시 %M분")
        elif format_type == "short":
            return dt.strftime("%Y-%m-%d %H:%M")
        elif format_type == "date_only":
            return dt.strftime("%Y-%m-%d")
        elif format_type == "time_only":
            return dt.strftime("%H:%M:%S")
        else:
            return dt.strftime(format_type)
    
    @staticmethod
    def add_time_delta(dt: datetime, **kwargs) -> datetime:
        """datetime에 시간 추가"""
        return dt + timedelta(**kwargs)
    
    @staticmethod
    def get_timezone_offset(timezone: str = "Asia/Seoul") -> int:
        """타임존 오프셋 반환 (시간 단위)"""
        try:
            import pytz
            tz = pytz.timezone(timezone)
            now = datetime.now()
            offset = tz.utcoffset(now)
            return int(offset.total_seconds() / 3600)
        except ImportError:
            logger.warning("pytz 라이브러리가 설치되지 않았습니다")
            return 9  # 기본값: KST (+9)
        except Exception as e:
            logger.error(f"타임존 오프셋 계산 실패: {e}")
            return 9


class SecurityUtils:
    """보안 관련 유틸리티"""
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """안전한 랜덤 토큰 생성"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_api_key(prefix: str = "", length: int = 32) -> str:
        """API 키 생성"""
        token = secrets.token_hex(length)
        return f"{prefix}_{token}" if prefix else token
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Dict[str, str]:
        """패스워드 해싱"""
        if not salt:
            salt = secrets.token_hex(16)
        
        # PBKDF2를 사용한 해싱
        import hashlib
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        
        return {
            "hash": hashed.hex(),
            "salt": salt
        }
    
    @staticmethod
    def verify_password(password: str, hash_data: Dict[str, str]) -> bool:
        """패스워드 검증"""
        try:
            salt = hash_data["salt"]
            stored_hash = hash_data["hash"]
            
            import hashlib
            computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            
            return computed_hash.hex() == stored_hash
        except Exception as e:
            logger.error(f"패스워드 검증 실패: {e}")
            return False
    
    @staticmethod
    def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
        """민감한 데이터 마스킹"""
        if len(data) <= visible_chars:
            return mask_char * len(data)
        
        visible_part = data[:visible_chars]
        masked_part = mask_char * (len(data) - visible_chars)
        return visible_part + masked_part


class DataUtils:
    """데이터 처리 유틸리티"""
    
    @staticmethod
    def safe_json_loads(json_string: str, default: Any = None) -> Any:
        """안전한 JSON 파싱"""
        try:
            return json.loads(json_string)
        except (json.JSONDecodeError, TypeError):
            return default
    
    @staticmethod
    def safe_json_dumps(data: Any, default: str = "{}") -> str:
        """안전한 JSON 직렬화"""
        try:
            return json.dumps(data, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return default
    
    @staticmethod
    def deep_merge_dict(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """딕셔너리 깊은 병합"""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = DataUtils.deep_merge_dict(result[key], value)
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """중첩된 딕셔너리 평탄화"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(DataUtils.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    @staticmethod
    def get_nested_value(data: Dict[str, Any], key_path: str, default: Any = None, sep: str = '.') -> Any:
        """중첩된 딕셔너리에서 값 가져오기"""
        keys = key_path.split(sep)
        current = data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    @staticmethod
    def set_nested_value(data: Dict[str, Any], key_path: str, value: Any, sep: str = '.') -> Dict[str, Any]:
        """중첩된 딕셔너리에 값 설정"""
        keys = key_path.split(sep)
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        return data
    
    @staticmethod
    def remove_none_values(data: Union[Dict, List], recursive: bool = True) -> Union[Dict, List]:
        """None 값 제거"""
        if isinstance(data, dict):
            result = {}
            for k, v in data.items():
                if v is not None:
                    if recursive and isinstance(v, (dict, list)):
                        result[k] = DataUtils.remove_none_values(v, recursive)
                    else:
                        result[k] = v
            return result
        elif isinstance(data, list):
            result = []
            for item in data:
                if item is not None:
                    if recursive and isinstance(item, (dict, list)):
                        result.append(DataUtils.remove_none_values(item, recursive))
                    else:
                        result.append(item)
            return result
        else:
            return data


class URLUtils:
    """URL 처리 유틸리티"""
    
    @staticmethod
    def build_url(base_url: str, path: str = "", params: Optional[Dict[str, Any]] = None) -> str:
        """URL 구성"""
        # 기본 URL 정리
        base_url = base_url.rstrip('/')
        
        # 경로 추가
        if path:
            path = path.lstrip('/')
            url = f"{base_url}/{path}"
        else:
            url = base_url
        
        # 쿼리 파라미터 추가
        if params:
            # None 값 제거
            filtered_params = {k: v for k, v in params.items() if v is not None}
            if filtered_params:
                query_string = urllib.parse.urlencode(filtered_params)
                url = f"{url}?{query_string}"
        
        return url
    
    @staticmethod
    def parse_url(url: str) -> Dict[str, Any]:
        """URL 파싱"""
        parsed = urllib.parse.urlparse(url)
        
        return {
            "scheme": parsed.scheme,
            "netloc": parsed.netloc,
            "hostname": parsed.hostname,
            "port": parsed.port,
            "path": parsed.path,
            "params": parsed.params,
            "query": parsed.query,
            "fragment": parsed.fragment,
            "query_dict": dict(urllib.parse.parse_qsl(parsed.query))
        }
    
    @staticmethod
    def encode_url_component(component: str) -> str:
        """URL 컴포넌트 인코딩"""
        return urllib.parse.quote(component, safe='')
    
    @staticmethod
    def decode_url_component(component: str) -> str:
        """URL 컴포넌트 디코딩"""
        return urllib.parse.unquote(component)


class RetryUtils:
    """재시도 유틸리티"""
    
    @staticmethod
    async def retry_async(func, *args, max_retries: int = 3, delay: float = 1.0, 
                         backoff: float = 2.0, exceptions: tuple = (Exception,), **kwargs):
        """비동기 함수 재시도"""
        import asyncio
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if attempt == max_retries:
                    break
                
                wait_time = delay * (backoff ** attempt)
                logger.warning(f"함수 실행 실패 (시도 {attempt + 1}/{max_retries + 1}): {e}. {wait_time}초 후 재시도...")
                await asyncio.sleep(wait_time)
        
        raise last_exception
    
    @staticmethod
    def retry_sync(func, *args, max_retries: int = 3, delay: float = 1.0,
                  backoff: float = 2.0, exceptions: tuple = (Exception,), **kwargs):
        """동기 함수 재시도"""
        import time
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if attempt == max_retries:
                    break
                
                wait_time = delay * (backoff ** attempt)
                logger.warning(f"함수 실행 실패 (시도 {attempt + 1}/{max_retries + 1}): {e}. {wait_time}초 후 재시도...")
                time.sleep(wait_time)
        
        raise last_exception


class LogUtils:
    """로깅 유틸리티"""
    
    @staticmethod
    def setup_logger(name: str, level: str = "INFO", format_string: Optional[str] = None) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger(name)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            
            if not format_string:
                format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            
            formatter = logging.Formatter(format_string)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        logger.setLevel(getattr(logging, level.upper()))
        return logger
    
    @staticmethod
    def mask_sensitive_logs(data: Dict[str, Any], sensitive_keys: List[str] = None) -> Dict[str, Any]:
        """로그에서 민감한 정보 마스킹"""
        if not sensitive_keys:
            sensitive_keys = [
                "password", "token", "secret", "key", "auth", "credential",
                "api_key", "access_token", "refresh_token", "private_key"
            ]
        
        result = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive_key in key_lower for sensitive_key in sensitive_keys):
                result[key] = SecurityUtils.mask_sensitive_data(str(value))
            elif isinstance(value, dict):
                result[key] = LogUtils.mask_sensitive_logs(value, sensitive_keys)
            else:
                result[key] = value
        
        return result


# 편의 함수들
def generate_uuid() -> str:
    """UUID 생성"""
    import uuid
    return str(uuid.uuid4())

def get_current_timestamp() -> int:
    """현재 타임스탬프 반환"""
    return int(datetime.now().timestamp())

def format_file_size(size_bytes: int) -> str:
    """파일 크기를 읽기 쉬운 형태로 포맷"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """문자열 자르기"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
