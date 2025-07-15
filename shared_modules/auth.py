"""
인증 관련 유틸리티 함수들
"""

import logging
from fastapi import HTTPException, Header
from typing import Optional
from .queries import get_user_by_access_token
from .database import get_session_context

logger = logging.getLogger(__name__)

def verify_token_and_get_user_id(authorization: str = Header(None)) -> int:
    """
    JWT 토큰 검증 및 사용자 ID 반환
    
    Args:
        authorization: Authorization 헤더 값
        
    Returns:
        int: 사용자 ID
        
    Raises:
        HTTPException: 토큰이 유효하지 않은 경우
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Bearer 토큰 형식 확인
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        # 토큰 추출
        token = authorization.replace("Bearer ", "")
        
        # 데이터베이스에서 토큰으로 사용자 조회
        with get_session_context() as db:
            user = get_user_by_access_token(db, token)
            
            if not user:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            logger.info(f"사용자 인증 성공: {user.user_id}")
            return user.user_id
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"토큰 검증 오류: {e}")
        raise HTTPException(status_code=401, detail="Token verification failed")

def get_user_from_token(token: str) -> Optional[dict]:
    """
    토큰으로부터 사용자 정보 조회
    
    Args:
        token: 액세스 토큰
        
    Returns:
        dict: 사용자 정보 또는 None
    """
    try:
        with get_session_context() as db:
            user = get_user_by_access_token(db, token)
            
            if user:
                return {
                    "user_id": user.user_id,
                    "email": user.email,
                    "nickname": user.nickname,
                    "provider": user.provider,
                    "business_type": user.business_type
                }
            return None
            
    except Exception as e:
        logger.error(f"사용자 정보 조회 오류: {e}")
        return None

def create_session_token(user_id: int) -> str:
    """
    간단한 세션 토큰 생성 (개발용)
    실제 운영환경에서는 JWT나 다른 안전한 방식 사용 권장
    
    Args:
        user_id: 사용자 ID
        
    Returns:
        str: 세션 토큰
    """
    import hashlib
    import time
    
    # 간단한 토큰 생성 (실제로는 더 안전한 방식 사용)
    timestamp = str(int(time.time()))
    token_data = f"{user_id}:{timestamp}"
    token = hashlib.md5(token_data.encode()).hexdigest()
    
    return f"session_{token}"

def validate_business_access(user_id: int, required_business_type: str = None) -> bool:
    """
    비즈니스 타입별 접근 권한 확인
    
    Args:
        user_id: 사용자 ID
        required_business_type: 필요한 비즈니스 타입
        
    Returns:
        bool: 접근 권한 여부
    """
    try:
        with get_session_context() as db:
            from .queries import get_user_by_id
            user = get_user_by_id(db, user_id)
            
            if not user:
                return False
            
            # 관리자는 모든 접근 허용
            if user.admin:
                return True
            
            # 특정 비즈니스 타입이 요구되는 경우
            if required_business_type:
                return user.business_type == required_business_type
            
            return True
            
    except Exception as e:
        logger.error(f"비즈니스 접근 권한 확인 오류: {e}")
        return False