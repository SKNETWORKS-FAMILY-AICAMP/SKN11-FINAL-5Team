"""
솔로프리너를 위한 통합 마케팅 AI 에이전트 시스템

주요 구성요소:
- MarketingAgentManager: 통합 마케팅 에이전트 관리자
- 공통 모듈 활용으로 코드 중복 최소화
- RAG 기반 전문 마케팅 상담 시스템
"""

__version__ = "2.0.0"
__author__ = "SKN Marketing AI Team"

import os
import sys

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# 공통 모듈 임포트
from shared_modules import (
    get_config,
    get_llm_manager,
    get_vector_manager,
    get_db_manager,
    setup_logging,
    create_success_response,
    create_error_response
)

# 마케팅 관련 설정
from marketing_agent.config.persona_config import PERSONA_CONFIG, SPECIALIZED_CONFIG
from marketing_agent.config.prompts_config import PROMPT_META

__all__ = [
    "PERSONA_CONFIG",
    "SPECIALIZED_CONFIG", 
    "PROMPT_META",
    "get_version",
    "list_personas",
    "get_marketing_manager"
]

# 마케팅 상수
DEFAULT_PERSONA = "content"
SUPPORTED_PERSONAS = ["branding", "content", "targeting"]

def get_version() -> str:
    """패키지 버전 반환"""
    return __version__

def list_personas() -> list:
    """지원되는 페르소나 목록 반환"""
    return SUPPORTED_PERSONAS.copy()

def get_marketing_manager():
    """통합 마케팅 매니저 반환"""
    from marketing_agent.core.marketing_manager_old import MarketingAgentManager
    return MarketingAgentManager()

# 패키지 초기화
def _initialize_package():
    """패키지 초기화 - 환경 설정 및 로깅 설정"""
    try:
        # 설정 로드
        config = get_config()
        
        # 로깅 설정
        setup_logging("marketing_agent", config.LOG_LEVEL)
        
        # ChromaDB 디렉토리 확인
        if not os.path.exists(config.CHROMA_DIR):
            os.makedirs(config.CHROMA_DIR, exist_ok=True)
        
        print(f"✅ 마케팅 에이전트 v{__version__} 초기화 완료")
        
    except Exception as e:
        print(f"⚠️ 마케팅 에이전트 초기화 중 오류: {e}")

# 패키지 로드 시 초기화 실행
_initialize_package()
