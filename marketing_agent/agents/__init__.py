"""
마케팅 에이전트 모듈
공통 모듈을 활용한 전문 마케팅 에이전트들
"""

from .base_agent import BaseMarketingAgent
from .branding_agent import BrandingAgent
from .content_agent import ContentAgent
from .targeting_agent import TargetingAgent

__all__ = [
    "BaseMarketingAgent",
    "BrandingAgent", 
    "ContentAgent",
    "TargetingAgent"
]

# 에이전트 팩토리
def create_agent(agent_type: str, name: str = None, config: dict = None):
    """에이전트 타입에 따른 에이전트 생성"""
    agent_classes = {
        "branding": BrandingAgent,
        "content": ContentAgent,
        "targeting": TargetingAgent
    }
    
    agent_class = agent_classes.get(agent_type.lower())
    if not agent_class:
        raise ValueError(f"지원하지 않는 에이전트 타입: {agent_type}")
    
    return agent_class(name=name, config=config)

def get_available_agent_types():
    """사용 가능한 에이전트 타입 목록 반환"""
    return ["branding", "content", "targeting"]
