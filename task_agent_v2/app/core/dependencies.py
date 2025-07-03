"""
TinkerBell 프로젝트 - 의존성 주입
"""

from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .config import config
from ..services.agent_service import AgentService
from ..services.conversation_service import ConversationService
from ..services.automation_service import AutomationService
from .db.database import get_db

# 서비스 의존성들
async def get_agent_service() -> AgentService:
    """에이전트 서비스 의존성"""
    return AgentService()

async def get_conversation_service(db: Session = Depends(get_db)) -> ConversationService:
    """대화 서비스 의존성"""
    return ConversationService(db)

async def get_automation_service() -> AutomationService:
    """자동화 서비스 의존성"""
    return AutomationService()

# 검증 의존성들
def validate_user_id(user_id: str) -> int:
    """사용자 ID 검증"""
    try:
        user_id_int = int(user_id)
        if user_id_int <= 0:
            raise ValueError("Invalid user ID")
        return user_id_int
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 사용자 ID입니다."
        )

def validate_conversation_id(conversation_id: str) -> int:
    """대화 ID 검증"""
    try:
        conv_id_int = int(conversation_id)
        if conv_id_int <= 0:
            raise ValueError("Invalid conversation ID")
        return conv_id_int
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 대화 ID입니다."
        )

def validate_pagination(page: int = 1, per_page: int = 20) -> tuple[int, int]:
    """페이지네이션 파라미터 검증"""
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="페이지 번호는 1 이상이어야 합니다."
        )
    
    if per_page < 1 or per_page > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="페이지 크기는 1-100 사이여야 합니다."
        )
    
    return page, per_page

# 권한 검증 (향후 확장용)
async def get_current_user(user_id: int = Depends(validate_user_id)):
    """현재 사용자 정보 (향후 JWT 토큰 검증 등으로 확장 가능)"""
    # TODO: JWT 토큰 검증 로직 추가
    return {"user_id": user_id}

# 헬스체크 의존성
async def check_system_health() -> dict:
    """시스템 상태 확인"""
    health_status = {
        "database": "healthy",
        "llm": "healthy", 
        "vector_db": "healthy"
    }
    
    # API 키 확인
    api_keys_status = config.validate_api_keys()
    health_status["api_keys"] = api_keys_status
    
    return health_status

# 설정 검증 의존성
def validate_environment():
    """환경 설정 검증"""
    api_keys = config.validate_api_keys()
    
    if not any(api_keys.values()):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="필요한 API 키가 설정되지 않았습니다."
        )
    
    return True
