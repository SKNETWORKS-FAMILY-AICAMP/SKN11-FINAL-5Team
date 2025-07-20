"""
마케팅 워크플로우 유틸리티 함수들
공통으로 사용되는 헬퍼 함수와 유틸리티 클래스
"""

import re
import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import yaml


# 로깅 설정
logger = logging.getLogger(__name__)


class ContentValidator:
    """콘텐츠 유효성 검증 클래스"""
    
    @staticmethod
    def validate_instagram_content(content: str, hashtags: List[str] = None) -> Dict[str, Any]:
        """인스타그램 콘텐츠 유효성 검증"""
        errors = []
        warnings = []
        
        # 글자 수 체크 (2200자 제한)
        if len(content) > 2200:
            errors.append(f"콘텐츠가 너무 깁니다. ({len(content)}/2200자)")
        
        # 해시태그 수 체크 (30개 제한)
        if hashtags and len(hashtags) > 30:
            warnings.append(f"해시태그가 많습니다. ({len(hashtags)}/30개)")
        
        # 필수 요소 체크
        if not content.strip():
            errors.append("콘텐츠가 비어있습니다.")
        
        # 첫 문장 길이 체크 (훅 효과)
        first_sentence = content.split('.')[0] if '.' in content else content.split('\n')[0]
        if len(first_sentence) > 100:
            warnings.append("첫 문장이 너무 깁니다. 훅 효과를 위해 짧게 수정하세요.")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "character_count": len(content),
            "hashtag_count": len(hashtags) if hashtags else 0
        }
    
    @staticmethod
    def validate_blog_content(content: str, keywords: List[str] = None) -> Dict[str, Any]:
        """블로그 콘텐츠 유효성 검증"""
        errors = []
        warnings = []
        
        # 최소 글자 수 체크 (1000자 권장)
        if len(content) < 1000:
            warnings.append(f"콘텐츠가 짧습니다. SEO를 위해 1000자 이상 권장 ({len(content)}자)")
        
        # 키워드 밀도 체크
        if keywords:
            total_words = len(content.split())
            for keyword in keywords:
                keyword_count = content.lower().count(keyword.lower())
                density = (keyword_count / total_words) * 100 if total_words > 0 else 0
                
                if density > 5:
                    warnings.append(f"'{keyword}' 키워드 밀도가 높습니다. ({density:.1f}%)")
                elif density < 1:
                    warnings.append(f"'{keyword}' 키워드가 부족합니다. ({density:.1f}%)")
        
        # HTML 태그 체크
        if '<h1>' not in content and '<h2>' not in content:
            warnings.append("소제목(H2, H3 태그)을 추가하여 구조화하세요.")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "character_count": len(content),
            "word_count": len(content.split()),
            "keyword_density": ContentValidator._calculate_keyword_density(content, keywords)
        }
    
    @staticmethod
    def _calculate_keyword_density(content: str, keywords: List[str]) -> Dict[str, float]:
        """키워드 밀도 계산"""
        if not keywords:
            return {}
        
        total_words = len(content.split())
        density_map = {}
        
        for keyword in keywords:
            keyword_count = content.lower().count(keyword.lower())
            density = (keyword_count / total_words) * 100 if total_words > 0 else 0
            density_map[keyword] = round(density, 2)
        
        return density_map


class TextProcessor:
    """텍스트 처리 유틸리티"""
    
    @staticmethod
    def extract_hashtags(text: str) -> List[str]:
        """텍스트에서 해시태그 추출"""
        hashtag_pattern = r'#[\w가-힣]+'
        hashtags = re.findall(hashtag_pattern, text)
        return [tag.replace('#', '') for tag in hashtags]
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """텍스트에서 주요 키워드 추출 (간단한 빈도 기반)"""
        # 불용어 제거 (간단한 버전)
        stopwords = {'을', '를', '이', '가', '에', '의', '는', '은', '와', '과', '로', '으로', 
                    '에서', '부터', '까지', '하고', '그리고', '그런데', '하지만', '그러나'}
        
        # 단어 분리 및 정제
        words = re.findall(r'[\w가-힣]+', text.lower())
        words = [word for word in words if len(word) > 1 and word not in stopwords]
        
        # 빈도 계산
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 빈도순 정렬
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, freq in sorted_words[:max_keywords]]
    
    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """텍스트 길이 제한"""
        if len(text) <= max_length:
            return text
        
        truncated = text[:max_length - len(suffix)]
        return truncated + suffix
    
    @staticmethod
    def clean_html(text: str) -> str:
        """HTML 태그 제거"""
        html_pattern = r'<[^>]+>'
        return re.sub(html_pattern, '', text)
    
    @staticmethod
    def format_for_platform(text: str, platform: str) -> str:
        """플랫폼별 텍스트 포맷팅"""
        if platform.lower() == 'instagram':
            # 인스타그램: 이모지 강화, 줄바꿈 최적화
            text = TextProcessor._add_line_breaks(text)
            text = TextProcessor._enhance_emojis(text)
        
        elif platform.lower() == 'naver-blog':
            # 네이버 블로그: HTML 태그 추가, 단락 구조화
            text = TextProcessor._add_html_structure(text)
        
        return text
    
    @staticmethod
    def _add_line_breaks(text: str) -> str:
        """인스타그램용 줄바꿈 추가"""
        sentences = text.split('. ')
        formatted_sentences = []
        
        for i, sentence in enumerate(sentences):
            formatted_sentences.append(sentence.strip())
            
            # 2-3문장마다 줄바꿈 추가
            if (i + 1) % 2 == 0 and i < len(sentences) - 1:
                formatted_sentences.append('\n')
        
        return '. '.join(formatted_sentences)
    
    @staticmethod
    def _enhance_emojis(text: str) -> str:
        """이모지 강화 (간단한 키워드 기반)"""
        emoji_map = {
            '좋은': '👍',
            '최고': '🔝',
            '추천': '💡',
            '새로운': '✨',
            '특별한': '⭐',
            '완벽한': '💯'
        }
        
        for keyword, emoji in emoji_map.items():
            if keyword in text and emoji not in text:
                text = text.replace(keyword, f"{keyword} {emoji}")
        
        return text
    
    @staticmethod
    def _add_html_structure(text: str) -> str:
        """HTML 구조 추가"""
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 제목처럼 보이는 라인을 H2로 변환
            if len(line) < 50 and (line.endswith('?') or line.endswith(':')):
                formatted_lines.append(f"<h2>{line}</h2>")
            else:
                formatted_lines.append(f"<p>{line}</p>")
        
        return '\n'.join(formatted_lines)


class PerformanceTracker:
    """성과 추적 유틸리티"""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = datetime.now(timezone.utc)
    
    def start_timer(self, operation: str):
        """작업 시간 측정 시작"""
        self.metrics[f"{operation}_start"] = datetime.now(timezone.utc)
    
    def end_timer(self, operation: str):
        """작업 시간 측정 종료"""
        if f"{operation}_start" in self.metrics:
            start_time = self.metrics[f"{operation}_start"]
            duration = datetime.now(timezone.utc) - start_time
            self.metrics[f"{operation}_duration"] = duration.total_seconds()
    
    def increment_counter(self, metric: str, value: int = 1):
        """카운터 증가"""
        self.metrics[metric] = self.metrics.get(metric, 0) + value
    
    def set_metric(self, metric: str, value: Any):
        """메트릭 설정"""
        self.metrics[metric] = value
    
    def get_summary(self) -> Dict[str, Any]:
        """성과 요약 반환"""
        total_duration = datetime.now(timezone.utc) - self.start_time
        
        return {
            "total_duration_seconds": total_duration.total_seconds(),
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now(timezone.utc).isoformat(),
            "metrics": self.metrics
        }


class CacheManager:
    """간단한 캐시 관리자"""
    
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
        self.access_times = {}
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        if key in self.cache:
            self.access_times[key] = datetime.now()
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """캐시에 값 저장"""
        # 캐시 크기 제한
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        self.cache[key] = {
            "value": value,
            "created_at": datetime.now(),
            "ttl": ttl
        }
        self.access_times[key] = datetime.now()
    
    def _evict_oldest(self):
        """가장 오래된 항목 제거"""
        if self.access_times:
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
    
    def clear_expired(self):
        """만료된 항목 정리"""
        now = datetime.now()
        expired_keys = []
        
        for key, data in self.cache.items():
            if isinstance(data, dict) and "created_at" in data and "ttl" in data:
                age = (now - data["created_at"]).total_seconds()
                if age > data["ttl"]:
                    expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
    
    def generate_cache_key(self, *args, **kwargs) -> str:
        """캐시 키 생성"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()


class ConfigValidator:
    """설정 유효성 검증"""
    
    @staticmethod
    def validate_workflow_config(config_path: str) -> Tuple[bool, List[str]]:
        """워크플로우 설정 유효성 검증"""
        errors = []
        
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                errors.append(f"설정 파일이 존재하지 않습니다: {config_path}")
                return False, errors
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 필수 섹션 확인
            required_sections = ['workflow', 'mcp_servers', 'platform_configs']
            for section in required_sections:
                if section not in config:
                    errors.append(f"필수 섹션이 누락되었습니다: {section}")
            
            # MCP 서버 URL 확인
            if 'mcp_servers' in config:
                for server_name, server_config in config['mcp_servers'].items():
                    if 'url' not in server_config:
                        errors.append(f"MCP 서버 URL이 누락되었습니다: {server_name}")
                    
                    if 'tools' not in server_config or not server_config['tools']:
                        errors.append(f"MCP 서버 도구가 누락되었습니다: {server_name}")
            
            # 플랫폼 설정 확인
            if 'platform_configs' in config:
                required_platforms = ['instagram', 'naver_blog']
                for platform in required_platforms:
                    if platform not in config['platform_configs']:
                        errors.append(f"플랫폼 설정이 누락되었습니다: {platform}")
            
        except yaml.YAMLError as e:
            errors.append(f"YAML 파싱 오류: {e}")
        except Exception as e:
            errors.append(f"설정 검증 중 오류: {e}")
        
        return len(errors) == 0, errors


class Logger:
    """마케팅 에이전트용 로거"""
    
    @staticmethod
    def setup_logging(log_dir: str = "logs", log_level: str = "INFO"):
        """로깅 설정"""
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # 로그 포맷 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 파일 핸들러
        file_handler = logging.FileHandler(log_path / "marketing_agent.log")
        file_handler.setFormatter(formatter)
        
        # 에러 파일 핸들러
        error_handler = logging.FileHandler(log_path / "error.log")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        # 루트 로거 설정
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)
        
        # 콘솔 핸들러 (개발 시)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)


# 전역 캐시 매니저 인스턴스
_cache_manager = CacheManager()

def get_cache_manager() -> CacheManager:
    """전역 캐시 매니저 반환"""
    return _cache_manager
