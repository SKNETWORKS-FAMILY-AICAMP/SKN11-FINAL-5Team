"""
솔로프리너를 위한 페르소나 특화 마케팅 AI 에이전트 시스템

주요 구성요소:
- BrandingAgent: 브랜딩 및 포지셔닝 전략
- ContentAgent: 콘텐츠 마케팅 및 카피라이팅  
- TargetingAgent: 고객 세분화 및 타겟팅
- MarketingAgentManager: 통합 관리 시스템

지원 페르소나:
- personacreator: 퍼스널 브랜드 크리에이터
- beautyshop: 뷰티샵 사장
- e_commerce: 이커머스 사업자
"""

__version__ = "1.0.0"
__author__ = "Marketing AI Team"
__email__ = "support@marketing-ai.com"

# 패키지 레벨 imports
from rag import MarketingAgentManager
from config.persona_config import PERSONA_CONFIGS, PERSONA_STRATEGIES
from config.prompts_config import PROMPT_META, PERSONA_QUICK_GUIDE

# 편의를 위한 단축 imports
from agents.branding_agent import BrandingAgent
from agents.content_agent import ContentAgent  
from agents.targeting_agent import TargetingAgent

__all__ = [
    "MarketingAgentManager",
    "BrandingAgent", 
    "ContentAgent",
    "TargetingAgent",
    "PERSONA_CONFIGS",
    "PERSONA_STRATEGIES", 
    "PROMPT_META",
    "PERSONA_QUICK_GUIDE"
]

# 패키지 레벨 설정
DEFAULT_PERSONA = "personacreator"
SUPPORTED_PERSONAS = ["personacreator", "beautyshop", "e_commerce"]
SUPPORTED_AGENTS = ["branding", "content", "targeting"]

def get_version() -> str:
    """패키지 버전 반환"""
    return __version__

def list_personas() -> list:
    """지원되는 페르소나 목록 반환"""
    return SUPPORTED_PERSONAS.copy()

def list_agents() -> list:
    """지원되는 에이전트 목록 반환"""
    return SUPPORTED_AGENTS.copy()

# 패키지 초기화 시 환경 확인
def _check_environment():
    """필수 환경 변수 및 의존성 확인"""
    import os
    import warnings
    
    # OpenAI API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        warnings.warn(
            "OPENAI_API_KEY가 설정되지 않았습니다. "
            ".env 파일에 API 키를 설정해주세요.",
            UserWarning
        )
    
    # ChromaDB 디렉토리 확인
    chroma_dir = os.getenv("CHROMA_DIR", "./vector_db")
    if not os.path.exists(chroma_dir):
        os.makedirs(chroma_dir, exist_ok=True)
        print(f"📁 ChromaDB 디렉토리 생성: {chroma_dir}")

# 패키지 로드 시 환경 확인 실행
_check_environment()