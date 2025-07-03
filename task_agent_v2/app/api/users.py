"""
TinkerBell 프로젝트 - 사용자 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any

from ..core.dependencies import validate_user_id
from ..core.response import ResponseFormatter
from ..core.exceptions import to_http_exception, TinkerBellException, validation_error
from ..schemas.base import UserCreate, UserLogin, UserResponse

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.post("/register", response_model=Dict[str, Any])
async def register_user(user_data: UserCreate):
    """사용자 등록"""
    try:
        # 기존 서비스 사용 (추후 리팩토링)
        from ...db_services import user_service
        
        with user_service as service:
            # 이메일 중복 검사
            existing_user = service.get_user_by_email(user_data.email)
            if existing_user:
                raise validation_error("이미 등록된 이메일입니다.", "email")
            
            # 사용자 생성
            user = service.create_user(
                email=user_data.email,
                password=user_data.password,
                nickname=user_data.nickname,
                business_type=user_data.business_type
            )
            
            # 응답 데이터 구성
            user_response = UserResponse(
                user_id=user.user_id,
                email=user.email,
                nickname=user.nickname,
                business_type=user.business_type,
                admin=user.admin,
                created_at=user.created_at
            )
            
            return ResponseFormatter.success(
                data=user_response.dict(),
                message="사용자 등록이 완료되었습니다."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 등록 실패: {e}")
        raise HTTPException(status_code=500, detail="사용자 등록 중 오류가 발생했습니다.")

@router.post("/login", response_model=Dict[str, Any])
async def login_user(login_data: UserLogin):
    """사용자 로그인"""
    try:
        from ...db_services import user_service
        
        with user_service as service:
            # 비밀번호 검증
            user = service.verify_password(login_data.email, login_data.password)
            if not user:
                raise HTTPException(
                    status_code=401, 
                    detail="이메일 또는 비밀번호가 올바르지 않습니다."
                )
            
            # 응답 데이터 구성
            user_response = UserResponse(
                user_id=user.user_id,
                email=user.email,
                nickname=user.nickname,
                business_type=user.business_type,
                admin=user.admin,
                created_at=user.created_at
            )
            
            return ResponseFormatter.success(
                data=user_response.dict(),
                message="로그인이 성공했습니다."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그인 실패: {e}")
        raise HTTPException(status_code=500, detail="로그인 중 오류가 발생했습니다.")

@router.get("/{user_id}", response_model=Dict[str, Any])
async def get_user(user_id: int):
    """사용자 정보 조회"""
    try:
        from ...db_services import user_service
        
        with user_service as service:
            user = service.get_user_by_id(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
            
            # 응답 데이터 구성
            user_response = UserResponse(
                user_id=user.user_id,
                email=user.email,
                nickname=user.nickname,
                business_type=user.business_type,
                admin=user.admin,
                created_at=user.created_at
            )
            
            return ResponseFormatter.success(
                data=user_response.dict(),
                message="사용자 정보 조회 완료"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="사용자 조회 중 오류가 발생했습니다.")

@router.put("/{user_id}", response_model=Dict[str, Any])
async def update_user(
    user_id: int,
    nickname: str = Query(None, description="닉네임"),
    business_type: str = Query(None, description="사업 타입")
):
    """사용자 정보 업데이트"""
    try:
        from ...db_services import user_service
        
        with user_service as service:
            user = service.get_user_by_id(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
            
            # 업데이트할 필드가 있는지 확인
            if not nickname and not business_type:
                raise validation_error("업데이트할 정보를 제공해주세요.")
            
            # 업데이트 로직 (실제 구현 필요)
            logger.info(f"사용자 정보 업데이트: {user_id}, nickname={nickname}, business_type={business_type}")
            
            # 업데이트된 사용자 정보 반환
            user_response = UserResponse(
                user_id=user.user_id,
                email=user.email,
                nickname=nickname or user.nickname,
                business_type=business_type or user.business_type,
                admin=user.admin,
                created_at=user.created_at
            )
            
            return ResponseFormatter.success(
                data=user_response.dict(),
                message="사용자 정보가 업데이트되었습니다."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 정보 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail="사용자 정보 업데이트 중 오류가 발생했습니다.")

@router.delete("/{user_id}", response_model=Dict[str, Any])
async def delete_user(user_id: int):
    """사용자 삭제 (탈퇴)"""
    try:
        from ...db_services import user_service
        
        with user_service as service:
            user = service.get_user_by_id(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
            
            # 사용자 삭제 로직 (실제 구현 필요)
            logger.info(f"사용자 삭제: {user_id}")
            
            return ResponseFormatter.success(
                data={"deleted": True},
                message="사용자 탈퇴가 완료되었습니다."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail="사용자 삭제 중 오류가 발생했습니다.")

@router.get("/{user_id}/profile", response_model=Dict[str, Any])
async def get_user_profile(user_id: int):
    """사용자 프로필 조회 (통계 포함)"""
    try:
        # 기본 사용자 정보
        user_info = await get_user(user_id)
        
        # 추가 통계 정보 (실제 구현 필요)
        from ...services.conversation_service import ConversationService
        from ...services.task_service import TaskService
        
        # 임시로 빈 세션 생성
        from sqlalchemy.orm import Session
        
        conv_service = ConversationService(None)
        task_service = TaskService()
        
        # 대화 통계
        try:
            conv_stats = await conv_service.get_conversation_stats(user_id)
        except:
            conv_stats = {"total_conversations": 0, "active_conversations": 0, "today_conversations": 0}
        
        # 작업 통계
        try:
            task_stats = await task_service.get_task_statistics(str(user_id))
        except:
            task_stats = {"total_tasks": 0, "completion_rate": 0}
        
        # 프로필 데이터 구성
        profile_data = {
            **user_info["data"],
            "statistics": {
                "conversations": conv_stats,
                "tasks": task_stats
            }
        }
        
        return ResponseFormatter.success(
            data=profile_data,
            message="사용자 프로필 조회 완료"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 프로필 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="사용자 프로필 조회 중 오류가 발생했습니다.")

@router.post("/{user_id}/password/change", response_model=Dict[str, Any])
async def change_password(
    user_id: int,
    current_password: str = Query(..., description="현재 비밀번호"),
    new_password: str = Query(..., min_length=8, description="새 비밀번호")
):
    """비밀번호 변경"""
    try:
        from ...db_services import user_service
        
        with user_service as service:
            user = service.get_user_by_id(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
            
            # 현재 비밀번호 검증
            if not service.verify_password(user.email, current_password):
                raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다.")
            
            # 새 비밀번호 업데이트 로직 (실제 구현 필요)
            logger.info(f"비밀번호 변경: {user_id}")
            
            return ResponseFormatter.success(
                message="비밀번호가 성공적으로 변경되었습니다."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"비밀번호 변경 실패: {e}")
        raise HTTPException(status_code=500, detail="비밀번호 변경 중 오류가 발생했습니다.")
