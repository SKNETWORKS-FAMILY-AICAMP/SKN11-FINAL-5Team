# agents/__init__.py
"""
에이전트 모듈 초기화
순환 import를 방지하기 위해 lazy import 사용
"""

def get_base_agent():
    """BaseMarketingAgent를 lazy import로 가져오기"""
    from base_agent import BaseMarketingAgent
    return BaseMarketingAgent

def get_branding_agent():
    """BrandingAgent를 lazy import로 가져오기"""
    from branding_agent import BrandingAgent
    return BrandingAgent

def get_content_agent():
    """ContentAgent를 lazy import로 가져오기"""
    from content_agent import ContentAgent
    return ContentAgent

def get_targeting_agent():
    """TargetingAgent를 lazy import로 가져오기"""
    from targeting_agent import TargetingAgent
    return TargetingAgent

# 필요시에만 import하도록 함수로 제공
__all__ = [
    'get_base_agent',
    'get_branding_agent', 
    'get_content_agent',
    'get_targeting_agent'
]