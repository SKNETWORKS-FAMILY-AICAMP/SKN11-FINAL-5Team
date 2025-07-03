"""
TinkerBell 프로젝트 - 피드백 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional

from ..core.dependencies import validate_user_id, validate_conversation_id, validate_pagination
from ..core.response import ResponseFormatter
from ..core.exceptions import to_http_exception, TinkerBellException, validation_error
from ..schemas.base import TimestampedSchema

from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

# 피드백 관련 스키마
class FeedbackCreate(BaseModel):
    """피드백 생성 요청"""
    user_id: int = Field(..., gt=0, description="사용자 ID")
    conversation_id: Optional[int] = Field(None, description="대화 세션 ID")
    rating: Optional[int] = Field(None, ge=1, le=5, description="평점 (1-5)")
    comment: Optional[str] = Field(None, max_length=1000, description="피드백 내용")
    category: Optional[str] = Field("general", description="피드백 카테고리")

class FeedbackResponse(TimestampedSchema):
    """피드백 응답"""
    feedback_id: int = Field(description="피드백 ID")
    user_id: int = Field(description="사용자 ID")
    conversation_id: Optional[int] = Field(description="대화 세션 ID")
    rating: Optional[int] = Field(description="평점")
    comment: Optional[str] = Field(description="피드백 내용")
    category: str = Field(description="피드백 카테고리")

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])

@router.post("", response_model=Dict[str, Any])
async def create_feedback(feedback_data: FeedbackCreate):
    """피드백 생성"""
    try:
        # 사용자 ID 검증
        validate_user_id(str(feedback_data.user_id))
        
        # 대화 ID 검증 (있는 경우)
        if feedback_data.conversation_id:
            validate_conversation_id(str(feedback_data.conversation_id))
        
        # 평점과 코멘트 중 하나는 필수
        if not feedback_data.rating and not feedback_data.comment:
            raise validation_error("평점 또는 피드백 내용 중 하나는 필수입니다.")
        
        # 기존 서비스 사용 (추후 리팩토링)
        from ..core.db.db_services import feedback_service
        
        with feedback_service as service:
            feedback = service.create_feedback(
                user_id=feedback_data.user_id,
                conversation_id=feedback_data.conversation_id,
                rating=feedback_data.rating,
                comment=feedback_data.comment
            )
            
            feedback_response = FeedbackResponse(
                feedback_id=feedback.feedback_id,
                user_id=feedback.user_id,
                conversation_id=feedback.conversation_id,
                rating=feedback.rating,
                comment=feedback.comment,
                category=feedback_data.category,
                created_at=feedback.created_at
            )
            
            return ResponseFormatter.success(
                data=feedback_response.dict(),
                message="피드백이 성공적으로 등록되었습니다."
            )
            
    except TinkerBellException as e:
        logger.error(f"피드백 생성 실패: {e}")
        raise to_http_exception(e)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="피드백 등록 중 오류가 발생했습니다.")

@router.get("/conversation/{conversation_id}", response_model=Dict[str, Any])
async def get_conversation_feedback(
    conversation_id: int,
    page: int = Query(1, ge=1, description="페이지 번호"),
    per_page: int = Query(20, ge=1, le=100, description="페이지당 항목 수")
):
    """대화 세션의 피드백 목록 조회"""
    try:
        # 대화 ID 검증
        validate_conversation_id(str(conversation_id))
        
        # 페이지네이션 검증
        page, per_page = validate_pagination(page, per_page)
        
        # 기존 서비스 사용
        from ..core.db.db_services import feedback_service
        
        with feedback_service as service:
            feedbacks = service.get_conversation_feedbacks(conversation_id)
            
            # 페이지네이션 적용
            total = len(feedbacks)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_feedbacks = feedbacks[start_idx:end_idx]
            
            feedback_list = []
            for fb in paginated_feedbacks:
                feedback_list.append({
                    "feedback_id": fb.feedback_id,
                    "user_id": fb.user_id,
                    "rating": fb.rating,
                    "comment": fb.comment,
                    "created_at": fb.created_at.isoformat()
                })
            
            return ResponseFormatter.paginated(
                items=feedback_list,
                page=page,
                per_page=per_page,
                total=total
            )
            
    except TinkerBellException as e:
        logger.error(f"대화 피드백 조회 실패: {e}")
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="피드백 조회 중 오류가 발생했습니다.")

@router.get("/user/{user_id}", response_model=Dict[str, Any])
async def get_user_feedback(
    user_id: int,
    category: Optional[str] = Query(None, description="피드백 카테고리"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    per_page: int = Query(20, ge=1, le=100, description="페이지당 항목 수")
):
    """사용자의 피드백 목록 조회"""
    try:
        # 사용자 ID 검증
        validate_user_id(str(user_id))
        
        # 페이지네이션 검증
        page, per_page = validate_pagination(page, per_page)
        
        # 실제 구현 필요 - 현재는 빈 리스트 반환
        logger.info(f"사용자 피드백 조회: user_id={user_id}, category={category}")
        
        return ResponseFormatter.paginated(
            items=[],
            page=page,
            per_page=per_page,
            total=0
        )
        
    except TinkerBellException as e:
        logger.error(f"사용자 피드백 조회 실패: {e}")
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="사용자 피드백 조회 중 오류가 발생했습니다.")

@router.get("/analytics", response_model=Dict[str, Any])
async def get_feedback_analytics(
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="피드백 카테고리")
):
    """피드백 분석 (관리자 전용)"""
    try:
        # 실제 구현 필요 - 현재는 샘플 데이터 반환
        analytics = {
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "category": category
            },
            "summary": {
                "total_feedback": 0,
                "average_rating": 0.0,
                "rating_distribution": {
                    "1": 0, "2": 0, "3": 0, "4": 0, "5": 0
                }
            },
            "trends": {
                "daily_counts": [],
                "satisfaction_trend": []
            },
            "categories": {
                "general": {"count": 0, "avg_rating": 0.0},
                "feature_request": {"count": 0, "avg_rating": 0.0},
                "bug_report": {"count": 0, "avg_rating": 0.0}
            },
            "top_issues": [],
            "improvement_suggestions": []
        }
        
        logger.info(f"피드백 분석: {start_date} ~ {end_date}, category={category}")
        
        return ResponseFormatter.success(
            data=analytics,
            message="피드백 분석 완료"
        )
        
    except Exception as e:
        logger.error(f"피드백 분석 실패: {e}")
        raise HTTPException(status_code=500, detail="피드백 분석 중 오류가 발생했습니다.")

@router.get("/categories", response_model=Dict[str, Any])
async def get_feedback_categories():
    """피드백 카테고리 목록"""
    try:
        categories = [
            {
                "key": "general",
                "name": "일반 피드백",
                "description": "서비스 전반에 대한 의견"
            },
            {
                "key": "feature_request",
                "name": "기능 요청",
                "description": "새로운 기능에 대한 제안"
            },
            {
                "key": "bug_report",
                "name": "버그 신고",
                "description": "서비스 오류 및 문제점 신고"
            },
            {
                "key": "ui_ux",
                "name": "UI/UX 개선",
                "description": "사용자 인터페이스 개선 제안"
            },
            {
                "key": "performance",
                "name": "성능 관련",
                "description": "서비스 속도 및 성능에 대한 피드백"
            },
            {
                "key": "automation",
                "name": "자동화 기능",
                "description": "자동화 기능에 대한 피드백"
            }
        ]
        
        return ResponseFormatter.success(
            data=categories,
            message="피드백 카테고리 목록 조회 완료"
        )
        
    except Exception as e:
        logger.error(f"피드백 카테고리 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="피드백 카테고리 조회 중 오류가 발생했습니다.")

@router.post("/batch", response_model=Dict[str, Any])
async def create_batch_feedback(
    feedbacks: list[FeedbackCreate]
):
    """일괄 피드백 생성"""
    try:
        # 피드백 리스트 검증
        if not feedbacks or len(feedbacks) == 0:
            raise validation_error("최소 1개의 피드백이 필요합니다.")
        if len(feedbacks) > 10:
            raise validation_error("최대 10개의 피드백만 처리할 수 있습니다.")
            
        created_feedbacks = []
        failed_feedbacks = []
        
        for feedback_data in feedbacks:
            try:
                # 개별 피드백 생성
                result = await create_feedback(feedback_data)
                created_feedbacks.append(result["data"])
            except Exception as e:
                failed_feedbacks.append({
                    "feedback_data": feedback_data.dict(),
                    "error": str(e)
                })
        
        return ResponseFormatter.success(
            data={
                "successful": created_feedbacks,
                "failed": failed_feedbacks,
                "summary": {
                    "total": len(feedbacks),
                    "successful": len(created_feedbacks),
                    "failed": len(failed_feedbacks)
                }
            },
            message="일괄 피드백 생성 완료"
        )
        
    except Exception as e:
        logger.error(f"일괄 피드백 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="일괄 피드백 생성 중 오류가 발생했습니다.")

@router.get("/export", response_model=Dict[str, Any])
async def export_feedback(
    start_date: Optional[str] = Query(None, description="시작 날짜"),
    end_date: Optional[str] = Query(None, description="종료 날짜"),
    format: str = Query("json", description="내보내기 형식 (json, csv)")
):
    """피드백 데이터 내보내기 (관리자 전용)"""
    try:
        # 실제 구현 필요
        export_info = {
            "export_id": "export_123",
            "format": format,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "status": "generating",
            "download_url": None,
            "expires_at": None
        }
        
        logger.info(f"피드백 내보내기: {start_date} ~ {end_date}, format={format}")
        
        return ResponseFormatter.success(
            data=export_info,
            message="피드백 내보내기가 시작되었습니다."
        )
        
    except Exception as e:
        logger.error(f"피드백 내보내기 실패: {e}")
        raise HTTPException(status_code=500, detail="피드백 내보내기 중 오류가 발생했습니다.")
