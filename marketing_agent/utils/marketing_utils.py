"""
마케팅 전용 유틸리티 함수들
shared_modules에 없는 마케팅 특화 기능만 포함
"""

import re
from typing import Dict, List, Any
from shared_modules import get_current_timestamp, sanitize_filename

class MarketingContentValidator:
    """마케팅 콘텐츠 유효성 검증"""
    
    @staticmethod
    def validate_instagram_content(content: str, hashtags: List[str] = None) -> Dict[str, Any]:
        """인스타그램 콘텐츠 유효성 검증"""
        errors = []
        warnings = []
        
        # 글자 수 체크
        if len(content) > 2200:
            errors.append(f"콘텐츠가 너무 깁니다. ({len(content)}/2200자)")
        elif len(content) < 50:
            warnings.append("콘텐츠가 너무 짧습니다. 더 자세한 설명을 추가해보세요.")
        
        # 해시태그 수 체크
        if hashtags and len(hashtags) > 30:
            warnings.append(f"해시태그가 많습니다. ({len(hashtags)}/30개)")
        
        # 첫 문장 길이 체크
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
    def extract_hashtags(text: str) -> List[str]:
        """텍스트에서 해시태그 추출"""
        hashtag_pattern = r'#[\w가-힣]+'
        hashtags = re.findall(hashtag_pattern, text)
        return [tag.replace('#', '') for tag in hashtags]
    
    @staticmethod
    def suggest_improvements(content: str, platform: str = "instagram") -> List[str]:
        """콘텐츠 개선 제안"""
        suggestions = []
        
        # 이모지 체크
        if not re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF]', content):
            suggestions.append("이모지를 추가하여 더 친근한 느낌을 주세요")
        
        # 줄바꿈 체크
        if '\n' not in content and len(content) > 100:
            suggestions.append("적절한 줄바꿈으로 가독성을 높여보세요")
        
        # 플랫폼별 제안
        if platform == "instagram":
            if "#" not in content:
                suggestions.append("해시태그를 추가하여 발견 가능성을 높이세요")
            if "?" not in content and "!" not in content:
                suggestions.append("질문이나 감탄사로 참여를 유도해보세요")
        
        return suggestions

class MarketingKeywordExtractor:
    """마케팅 키워드 추출기"""
    
    MARKETING_CATEGORIES = {
        "제품_특징": ["품질", "디자인", "기능", "효과", "성분", "소재"],
        "감정_어필": ["사랑", "행복", "만족", "특별", "완벽", "최고"],
        "행동_유도": ["지금", "바로", "즉시", "오늘", "한정", "마지막"],
        "신뢰_구축": ["보장", "인증", "검증", "후기", "리뷰", "추천"],
        "가격_혜택": ["할인", "세일", "무료", "적립", "쿠폰", "이벤트"]
    }
    
    @classmethod
    def extract_marketing_keywords(cls, text: str) -> Dict[str, List[str]]:
        """마케팅 키워드 카테고리별 추출"""
        found_keywords = {}
        text_lower = text.lower()
        
        for category, keywords in cls.MARKETING_CATEGORIES.items():
            found = [keyword for keyword in keywords if keyword in text_lower]
            if found:
                found_keywords[category] = found
        
        return found_keywords
    
    @classmethod
    def suggest_missing_keywords(cls, text: str, business_type: str = "일반") -> List[str]:
        """부족한 키워드 제안"""
        found_keywords = cls.extract_marketing_keywords(text)
        suggestions = []
        
        # 카테고리별 확인
        if "감정_어필" not in found_keywords:
            suggestions.append("감정에 어필하는 단어 추가 (특별한, 완벽한 등)")
        
        if "행동_유도" not in found_keywords:
            suggestions.append("행동을 유도하는 단어 추가 (지금, 바로 등)")
        
        if "신뢰_구축" not in found_keywords:
            suggestions.append("신뢰도를 높이는 단어 추가 (보장, 인증 등)")
        
        return suggestions

def generate_content_filename(content: str, platform: str = "general") -> str:
    """콘텐츠 기반 파일명 생성"""
    # 첫 10단어 추출
    words = content.split()[:10]
    base_name = "_".join(words)
    
    # 파일명 정리
    clean_name = sanitize_filename(base_name, max_length=50)
    
    # 타임스탬프와 플랫폼 추가
    timestamp = get_current_timestamp("%Y%m%d_%H%M")
    
    return f"{platform}_{clean_name}_{timestamp}"

def calculate_engagement_prediction(content_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """콘텐츠 참여도 예측"""
    # 간단한 점수 기반 예측
    score = 0
    factors = []
    
    # 길이 체크
    content_length = content_metrics.get("character_count", 0)
    if 100 <= content_length <= 500:
        score += 2
        factors.append("적절한 길이")
    elif content_length > 500:
        score += 1
        factors.append("충분한 내용")
    
    # 해시태그 체크
    hashtag_count = content_metrics.get("hashtag_count", 0)
    if 5 <= hashtag_count <= 15:
        score += 2
        factors.append("적절한 해시태그")
    elif hashtag_count > 0:
        score += 1
        factors.append("해시태그 사용")
    
    # 경고사항 체크
    warning_count = len(content_metrics.get("warnings", []))
    if warning_count == 0:
        score += 1
        factors.append("검증 통과")
    
    # 예측 등급
    if score >= 4:
        prediction = "높음"
    elif score >= 2:
        prediction = "보통"
    else:
        prediction = "낮음"
    
    return {
        "engagement_prediction": prediction,
        "score": score,
        "max_score": 5,
        "positive_factors": factors,
        "confidence": min(score / 5 * 100, 90)  # 최대 90%
    }
