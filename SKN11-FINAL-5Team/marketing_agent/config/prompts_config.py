"""
마케팅 전문 프롬프트 메타데이터 설정 (토픽별 개별 프롬프트 파일 사용)
"""

# 14개 토픽 각각에 대해 직접 프롬프트 파일 경로 지정
TOPICS = [
    "marketing_fundamentals",
    "social_media_marketing",
    "email_marketing",
    "content_marketing",
    "personal_branding",
    "digital_advertising",
    "conversion_optimization",
    "influencer_marketing",
    "local_marketing",
    "marketing_automation",
    "viral_marketing",
    "blog_marketing",
    "marketing_metrics"
]

TOPIC_TO_AGENT_TYPE = {
    "personal_branding": "branding",
    "brand_storytelling": "branding",
    "content_marketing": "content",
    "viral_marketing": "content",
    "influencer_marketing": "content",
    "marketing_metrics": "targeting",
    "conversion_optimization": "targeting",
    "seo_optimization": "targeting",
    "target_audience": "targeting"
    # 필요 시 확장
}


PROMPT_META = {
    topic: {
        "file": f"prompts/{topic}.md",
        "role": f"{topic.replace('_', ' ').title()} 전문가",
        "description": "마케팅 전략 지원"
    }
    for topic in TOPICS
}

# 카테고리별 토픽 분류 (옵션: UI 그룹핑, 필터링 등에 활용)
MARKETING_CATEGORIES = {
    "기초_이론": ["marketing_fundamentals"],
    "소셜미디어": ["social_media_marketing"],
    "콘텐츠_브랜딩": ["content_marketing", "personal_branding", "viral_marketing", "blog_marketing"],
    "디지털_광고": ["digital_advertising", "email_marketing"],
    "최적화_분석": ["conversion_optimization", "marketing_metrics"],
    "제휴_확장": ["influencer_marketing", "local_marketing", "marketing_automation"]
}

# ✅ 유틸 함수
def get_topics_by_category(category: str) -> list:
    """카테고리 이름으로 관련 토픽 목록 반환"""
    return MARKETING_CATEGORIES.get(category, [])

def get_all_topics() -> list:
    """전체 토픽 목록 반환"""
    return list(PROMPT_META.keys())

def get_topic_info(topic: str) -> dict:
    """단일 토픽의 메타 정보 반환"""
    return PROMPT_META.get(topic, {})
