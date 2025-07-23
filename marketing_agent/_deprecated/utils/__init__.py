"""마케팅 유틸리티 모듈 (업데이트)"""

from .analysis_tools import MarketingAnalysisTools

def get_marketing_analysis_tools() -> MarketingAnalysisTools:
    """마케팅 분석 도구 인스턴스를 반환합니다."""
    return MarketingAnalysisTools()
