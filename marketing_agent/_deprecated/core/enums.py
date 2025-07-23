"""
마케팅 에이전트 열거형 정의
"""

from enum import Enum

class MarketingStage(Enum):
    """4단계 마케팅 프로세스"""
    ANY_QUESTION = "any_question"                   # 순서 무관 즉시 응답
    STAGE_1_GOAL = "stage_1_goal"                   # 1단계: 목표 정의
    STAGE_2_TARGET = "stage_2_target"               # 2단계: 타겟 분석
    STAGE_3_STRATEGY = "stage_3_strategy"           # 3단계: 전략 기획
    STAGE_4_EXECUTION = "stage_4_execution"         # 4단계: 실행 계획
    COMPLETED = "completed"                         # 완료

class ResponseType(Enum):
    """응답 타입"""
    IMMEDIATE_ANSWER = "immediate_answer"           # 즉시 응답
    STAGE_PROGRESS = "stage_progress"               # 단계 진행
    FLOW_CONTROL = "flow_control"                   # 진행 제어
    COMPREHENSIVE = "comprehensive"                 # 종합 전략
    CLARIFICATION = "clarification"                 # 명확화 필요
    TOOL_REQUIRED = "tool_required"                 # 마케팅 툴 필요


# 업종별 프롬프트 파일 매핑
BUSINESS_PROMPT_MAPPING = {
    "뷰티": [
        "personal_branding.md", "social_media_marketing.md", "local_marketing.md",
        "content_marketing.md", "influencer_marketing.md", "blog_marketing.md"
    ],
    "음식점": [
        "local_marketing.md", "social_media_marketing.md", "content_marketing.md",
        "email_marketing.md", "blog_marketing.md", "marketing_fundamentals.md"
    ],
    "온라인쇼핑몰": [
        "digital_advertising.md", "content_marketing.md", "conversion_optimization.md",
        "marketing_automation.md", "email_marketing.md", "marketing_metrics.md"
    ],
    "서비스업": [
        "personal_branding.md", "content_marketing.md", "blog_marketing.md",
        "marketing_fundamentals.md", "marketing_metrics.md"
    ],
    "앱": [
        "viral_marketing.md", "email_marketing.md", "marketing_metrics.md",
        "content_marketing.md"
    ],
    "크리에이터": [
        "personal_branding.md",
        "content_marketing.md", "blog_marketing.md", "social_media_marketing.md",
        "influencer_marketing.md"
    ]
}

# 모든 프롬프트 파일 리스트
ALL_PROMPT_FILES = [
    "marketing_fundamentals.md",
    "marketing_metrics.md", 
    "personal_branding.md",
    "social_media_marketing.md",
    "influencer_marketing.md",
    "local_marketing.md",
    "digital_advertising.md",
    "content_marketing.md",
    "blog_marketing.md",
    "viral_marketing.md",
    "conversion_optimization.md",
    "email_marketing.md",
    "marketing_automation.md"
]

# 단계별 안내 메시지
STAGE_MESSAGES = {
    MarketingStage.STAGE_1_GOAL: "🎯비즈니스의 마케팅 목표를 명확히 해보세요! 구체적으로 어떤 결과를 얻고 싶으신가요? (예: 매출 증대, 브랜드 인지도 향상, 고객 유치 등)",
    MarketingStage.STAGE_2_TARGET: "🎯타겟 고객 분석을 시작합니다! 주요 타겟 고객은 누구인가요? 연령대, 성별, 관심사, 라이프스타일 등을 알려주세요.",
    MarketingStage.STAGE_3_STRATEGY: "📊 마케팅 전략 기획 단계입니다! 어떤 마케팅 채널에 집중하고 싶으신가요?(예: SNS, 블로그, 광고, 이벤트 등) 예산과 목표도 함께 알려주세요.",
    MarketingStage.STAGE_4_EXECUTION: "🚀 마케팅 실행 단계입니다! 이제 구체적인 콘텐츠나 캐페인을 만들어보세요. 블로그 글, 인스타그램 포스트, 광고 콘텐츠 중 무엇을 만들고 싶으신가요?",
    MarketingStage.ANY_QUESTION: "자유롭게 마케팅 질문을 해주세요. 바로 답변드리겠습니다!"
}

# 단계별 질문 템플릿
STAGE_QUESTIONS = {
    MarketingStage.STAGE_1_GOAL: "🎯 비즈니스의 마케팅 목표를 명확히 해보세요! 구체적으로 어떤 결과를 얻고 싶으신가요? (예: 매출 증대, 브랜드 인지도 향상, 고객 유치 등)",
    MarketingStage.STAGE_2_TARGET: "🎯 타겟 고객 분석을 시작합니다! 주요 타겟 고객은 누구인가요? 연령대, 성별, 관심사, 라이프스타일 등을 알려주세요.",
    MarketingStage.STAGE_3_STRATEGY: "📊 마케팅 전략 기획 단계입니다! 어떤 마케팅 채널에 집중하고 싶으신가요? (예: SNS, 블로그, 광고, 이벤트 등) 예산과 목표도 함께 알려주세요.",
    MarketingStage.STAGE_4_EXECUTION: "🚀 마케팅 실행 단계입니다! 이제 구체적인 콘텐츠나 캠페인을 만들어보세요. 블로그 글, 인스타그램 포스트, 광고 콘텐츠 중 무엇을 만들고 싶으신가요?"
}
