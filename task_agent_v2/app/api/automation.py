"""
TinkerBell 프로젝트 - 자동화 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional

from ..core.dependencies import get_automation_service, validate_user_id, validate_pagination
from ..core.response import ResponseFormatter
from ..core.exceptions import to_http_exception, TinkerBellException
from ..schemas.automation import (
    AutomationTaskCreate, AutomationTaskResponse, AutomationTaskUpdate,
    AutomationTaskFilter, AutomationAnalytics
)
from ..schemas.enums import AutomationTaskType, AutomationStatus
from ..services.automation_service import AutomationService

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/automation", tags=["automation"])

@router.post("/tasks", response_model=Dict[str, Any])
async def create_automation_task(
    automation_task: AutomationTaskCreate,
    automation_service: AutomationService = Depends(get_automation_service)
):
    """자동화 작업 생성"""
    try:
        # 사용자 ID 검증
        validate_user_id(str(automation_task.user_id))
        
        # 자동화 작업 생성
        created_task = await automation_service.create_task(automation_task)
        
        return ResponseFormatter.automation_response(
            task_id=created_task.task_id,
            task_type=created_task.task_type,
            status=created_task.status.value,
            message="자동화 작업이 성공적으로 생성되었습니다."
        )
        
    except TinkerBellException as e:
        logger.error(f"자동화 작업 생성 실패: {e}")
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="자동화 작업 생성 중 오류가 발생했습니다.")

@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_automation_task(
    task_id: int,
    automation_service: AutomationService = Depends(get_automation_service)
):
    """자동화 작업 조회"""
    try:
        # 자동화 작업 조회
        task = await automation_service.get_task(task_id)
        
        return ResponseFormatter.success(
            data=task.dict(),
            message="자동화 작업 조회 완료"
        )
        
    except TinkerBellException as e:
        logger.error(f"자동화 작업 조회 실패: {e}")
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="자동화 작업 조회 중 오류가 발생했습니다.")

@router.put("/tasks/{task_id}", response_model=Dict[str, Any])
async def update_automation_task(
    task_id: int,
    task_update: AutomationTaskUpdate,
    automation_service: AutomationService = Depends(get_automation_service)
):
    """자동화 작업 업데이트"""
    try:
        # 자동화 작업 업데이트
        updated_task = await automation_service.update_task(task_id, task_update)
        
        return ResponseFormatter.success(
            data=updated_task.dict(),
            message="자동화 작업이 성공적으로 업데이트되었습니다."
        )
        
    except TinkerBellException as e:
        logger.error(f"자동화 작업 업데이트 실패: {e}")
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="자동화 작업 업데이트 중 오류가 발생했습니다.")

@router.delete("/tasks/{task_id}", response_model=Dict[str, Any])
async def cancel_automation_task(
    task_id: int,
    automation_service: AutomationService = Depends(get_automation_service)
):
    """자동화 작업 취소"""
    try:
        # 자동화 작업 취소
        success = await automation_service.cancel_task(task_id)
        
        return ResponseFormatter.success(
            data={"cancelled": success},
            message="자동화 작업이 성공적으로 취소되었습니다."
        )
        
    except TinkerBellException as e:
        logger.error(f"자동화 작업 취소 실패: {e}")
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="자동화 작업 취소 중 오류가 발생했습니다.")

@router.get("/tasks", response_model=Dict[str, Any])
async def get_user_automation_tasks(
    user_id: int = Query(..., description="사용자 ID"),
    task_type: Optional[AutomationTaskType] = Query(None, description="작업 타입 필터"),
    status: Optional[AutomationStatus] = Query(None, description="상태 필터"),
    search: Optional[str] = Query(None, description="검색 키워드"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    per_page: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    automation_service: AutomationService = Depends(get_automation_service)
):
    """사용자 자동화 작업 목록 조회"""
    try:
        # 사용자 ID 검증
        validate_user_id(str(user_id))
        
        # 페이지네이션 검증
        page, per_page = validate_pagination(page, per_page)
        
        # 필터 구성
        task_filter = AutomationTaskFilter(
            task_type=task_type,
            status=status,
            search=search
        ) if any([task_type, status, search]) else None
        
        # 자동화 작업 목록 조회
        offset = (page - 1) * per_page
        tasks = await automation_service.get_user_tasks(
            user_id, task_filter, per_page, offset
        )
        
        return ResponseFormatter.paginated(
            items=[task.dict() for task in tasks],
            page=page,
            per_page=per_page,
            total=len(tasks)  # 실제로는 총 개수를 별도로 조회해야 함
        )
        
    except TinkerBellException as e:
        logger.error(f"자동화 작업 목록 조회 실패: {e}")
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="자동화 작업 목록 조회 중 오류가 발생했습니다.")

@router.post("/tasks/{task_id}/execute", response_model=Dict[str, Any])
async def execute_automation_task(
    task_id: int,
    automation_service: AutomationService = Depends(get_automation_service)
):
    """자동화 작업 즉시 실행"""
    try:
        # 자동화 작업 실행
        result = await automation_service.execute_task(task_id)
        
        return ResponseFormatter.success(
            data=result,
            message="자동화 작업이 실행되었습니다."
        )
        
    except TinkerBellException as e:
        logger.error(f"자동화 작업 실행 실패: {e}")
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="자동화 작업 실행 중 오류가 발생했습니다.")

@router.get("/tasks/status/{task_id}", response_model=Dict[str, Any])
async def get_automation_task_status(
    task_id: int,
    automation_service: AutomationService = Depends(get_automation_service)
):
    """자동화 작업 상태 조회"""
    try:
        # 자동화 작업 상태 조회
        task = await automation_service.get_task(task_id)
        
        status_info = {
            "task_id": task.task_id,
            "status": task.status.value,
            "title": task.title,
            "task_type": task.task_type,
            "scheduled_at": task.scheduled_at.isoformat() if task.scheduled_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message,
            "execution_details": task.execution_details
        }
        
        return ResponseFormatter.success(
            data=status_info,
            message="자동화 작업 상태 조회 완료"
        )
        
    except TinkerBellException as e:
        logger.error(f"자동화 작업 상태 조회 실패: {e}")
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="자동화 작업 상태 조회 중 오류가 발생했습니다.")

@router.get("/types", response_model=Dict[str, Any])
async def get_automation_types():
    """지원하는 자동화 타입 목록"""
    try:
        types = [
            {
                "type": AutomationTaskType.SCHEDULE_CALENDAR.value,
                "name": "일정 등록",
                "description": "Google Calendar에 일정을 자동으로 등록합니다.",
                "required_fields": ["title", "start_time"]
            },
            {
                "type": AutomationTaskType.PUBLISH_SNS.value,
                "name": "SNS 발행",
                "description": "소셜 미디어에 게시물을 자동으로 발행합니다.",
                "required_fields": ["platform", "content"]
            },
            {
                "type": AutomationTaskType.SEND_EMAIL.value,
                "name": "이메일 발송",
                "description": "이메일을 자동으로 발송합니다.",
                "required_fields": ["to", "subject", "body"]
            },
            {
                "type": AutomationTaskType.SEND_REMINDER.value,
                "name": "리마인더",
                "description": "지정된 시간에 알림을 발송합니다.",
                "required_fields": ["title", "reminder_time"]
            },
            {
                "type": AutomationTaskType.SEND_MESSAGE.value,
                "name": "메시지 발송",
                "description": "메시징 플랫폼에 메시지를 자동으로 발송합니다.",
                "required_fields": ["platform", "recipient", "content"]
            }
        ]
        
        return ResponseFormatter.success(
            data=types,
            message="자동화 타입 목록 조회 완료"
        )
        
    except Exception as e:
        logger.error(f"자동화 타입 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="자동화 타입 조회 중 오류가 발생했습니다.")

@router.get("/status", response_model=Dict[str, Any])
async def get_automation_service_status(
    automation_service: AutomationService = Depends(get_automation_service)
):
    """자동화 서비스 상태 조회"""
    try:
        status = await automation_service.get_service_status()
        
        return ResponseFormatter.success(
            data=status,
            message="자동화 서비스 상태 조회 완료"
        )
        
    except Exception as e:
        logger.error(f"자동화 서비스 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
