"""
설정 모듈 초기화
"""

# 설정 관련 함수들을 lazy import로 제공
def get_env_config():
    """환경 설정을 lazy import로 가져오기"""
    from .env_config import get_config
    return get_config()

def get_persona_config():
    """페르소나 설정을 lazy import로 가져오기"""
    from .persona_config import PERSONA_CONFIG
    return PERSONA_CONFIG

def get_prompts_config():
    """프롬프트 설정을 lazy import로 가져오기"""
    from .prompts_config import PROMPTS_CONFIG
    return PROMPTS_CONFIG

def get_llm_client():
    """LLM 클라이언트를 lazy import로 가져오기"""
    from .env_config import get_llm_client
    return get_llm_client()

__all__ = [
    'get_env_config',
    'get_persona_config', 
    'get_prompts_config',
    'get_llm_client'
]