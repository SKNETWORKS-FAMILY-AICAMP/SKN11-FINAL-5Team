"""
TinkerBell 프로젝트 - 대화 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional

from ..core.dependencies import get_conversation_service, validate_user_id, validate_conversation_id, validate_pagination
from ..core.response import ResponseFormatter
from ..core.exceptions import to_http_exception, TinkerBellException
from ..schemas.base import ConversationCreate, ConversationResponse, MessageCreate, MessageResponse
from ..services.conversation_service import ConversationService

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])

@router.post("", response_model=Dict[str, Any])
async def create_conversation(
    conversation_data: ConversationCreate,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """대화 세션 생성"""
    try:
        # 사용자 ID 검증
        validate_user_id(str(conversation_data.user_id))
        
        # 대화 세션 생성
        conversation = await conversation_service.create_conversation(
            user_id=conversation_data.user_id
        )
        
        return ResponseFormatter.success(
            data=conversation.dict(),
            message="대화 세션이 생성되었습니다."
        )
        
    except TinkerBellException as e:
        logger.error(f"대화 세션 생성 실패: {e}")
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="대화 세션 생성 중 오류가 발생했습니다.")

@router.get("/{conversation_id}", response_model=Dict[str, Any])
async def get_conversation(
    conversation_id: int,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """대화 세션 조회"""
    try:
        # 대화 ID 검증
        validate_conversation_id(str(conversation_id))
        
        # 대화 세션 조회
        conversation = await conversation_service.get_conversation(conversation_id)
        
        return ResponseFormatter.success(
            data=conversation.dict(),
            message="대화 세션 조회 완료"
        )
        
    except TinkerBellException as e:
        logger.error(f"대화 세션 조회 실패: {e}")
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="대화 세션 조회 중 오류가 발생했습니다.")

@router.get("", response_model=Dict[str, Any])
async def get_user_conversations(
    user_id: int = Query(..., description="사용자 ID"),
    visible_only: bool = Query(True, description="표시된 대화만 조회"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    per_page: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """사용자의 대화 세션 목록 조회"""
    try:
        # 사용자 ID 검증
        validate_user_id(str(user_id))
        
        # 페이지네이션 검증
        page, per_page = validate_pagination(page, per_page)
        
        # 대화 세션 목록 조회
        conversations = await conversation_service.get_user_conversations(
            user_id, visible_only
        )
        
        # 페이지네이션 적용 (실제로는 DB 레벨에서 처리해야 함)
        total = len(conversations)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_conversations = conversations[start_idx:end_idx]
        
        return ResponseFormatter.paginated(
            items=[conv.dict() for conv in paginated_conversations],
            page=page,
            per_page=per_page,
            total=total
        )
        
    except TinkerBellException as e:
        logger.error(f"대화 세션 목록 조회 실패: {e}")
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="대화 세션 목록 조회 중 오류가 발생했습니다.")

@router.patch("/{conversation_id}/end", response_model=Dict[str, Any])
async def end_conversation(
    conversation_id: int,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """대화 세션 종료"""
    try:
        # 대화 ID 검증
        validate_conversation_id(str(conversation_id))
        
        # 대화 세션 종료
        success = await conversation_service.end_conversation(conversation_id)
        
        return ResponseFormatter.success(
            data={"ended": success},
            message="대화 세션이 종료되었습니다."
        )
        
    except TinkerBellException as e:
        logger.error(f"대화 세션 종료 실패: {e}")
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="대화 세션 종료 중 오류가 발생했습니다.")

@router.patch("/{conversation_id}/hide", response_model=Dict[str, Any])
async def hide_conversation(
    conversation_id: int,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """대화 세션 숨기기"""
    try:
        # 대화 ID 검증
        validate_conversation_id(str(conversation_id))
        
        # 대화 세션 숨기기
        success = await conversation_service.hide_conversation(conversation_id)
        
        return ResponseFormatter.success(
            data={"hidden": success},
            message="대화 세션이 숨겨졌습니다."
        )
        
    except TinkerBellException as e:
        logger.error(f"대화 세션 숨기기 실패: {e}")
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="대화 세션 숨기기 중 오류가 발생했습니다.")

@router.post("/{conversation_id}/messages", response_model=Dict[str, Any])
async def create_message(
    conversation_id: int,
    message_data: MessageCreate,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """메시지 생성"""
    try:
        # 대화 ID 검증
        validate_conversation_id(str(conversation_id))
        
        # conversation_id 일치 확인
        if message_data.conversation_id != conversation_id:
            raise HTTPException(status_code=400, detail="대화 ID가 일치하지 않습니다.")
        
        # 메시지 생성
        message = await conversation_service.create_message(
            conversation_id=conversation_id,
            sender_type=message_data.sender_type,
            content=message_data.content,
            agent_type=message_data.agent_type
        )
        
        return ResponseFormatter.success(
            data=message.dict(),
            message="메시지가 생성되었습니다."
        )
        
    except TinkerBellException as e:
        logger.error(f"메시지 생성 실패: {e}")
        raise to_http_exception(e)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="메시지 생성 중 오류가 발생했습니다.")

@router.get("/{conversation_id}/messages", response_model=Dict[str, Any])
async def get_conversation_messages(
    conversation_id: int,
    page: int = Query(1, ge=1, description="페이지 번호"),
    per_page: int = Query(50, ge=1, le=100, description="페이지당 항목 수"),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """대화 세션의 메시지 목록 조회"""
    try:
        # 대화 ID 검증
        validate_conversation_id(str(conversation_id))
        
        # 페이지네이션 검증
        page, per_page = validate_pagination(page, per_page)
        
        # 메시지 목록 조회
        offset = (page - 1) * per_page
        messages = await conversation_service.get_conversation_messages(
            conversation_id, per_page, offset
        )
        
        return ResponseFormatter.paginated(
            items=[msg.dict() for msg in messages],
            page=page,
            per_page=per_page,
            total=len(messages)  # 실제로는 총 개수를 별도로 조회해야 함
        )
        
    except TinkerBellException as e:
        logger.error(f"메시지 목록 조회 실패: {e}")
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"예상치 못한 오료: {e}")
        raise HTTPException(status_code=500, detail="메시지 목록 조회 중 오류가 발생했습니다.")

@router.get("/{conversation_id}/history", response_model=Dict[str, Any])
async def get_conversation_history(
    conversation_id: int,
    limit: int = Query(10, ge=1, le=50, description="조회할 메시지 수"),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """대화 히스토리 조회 (에이전트용 포맷)"""
    try:
        # 대화 ID 검증
        validate_conversation_id(str(conversation_id))
        
        # 대화 히스토리 조회
        history = await conversation_service.get_conversation_history(
            conversation_id, limit
        )
        
        return ResponseFormatter.success(
            data=history,
            message="대화 히스토리 조회 완료"
        )
        
    except TinkerBellException as e:
        logger.error(f"대화 히스토리 조회 실패: {e}")
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="대화 히스토리 조회 중 오류가 발생했습니다.")

@router.get("/user/{user_id}/stats", response_model=Dict[str, Any])
async def get_user_conversation_stats(
    user_id: int,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """사용자의 대화 통계"""
    try:
        # 사용자 ID 검증
        validate_user_id(str(user_id))
        
        # 대화 통계 조회
        stats = await conversation_service.get_conversation_stats(user_id)
        
        return ResponseFormatter.success(
            data=stats,
            message="대화 통계 조회 완료"
        )
        
    except TinkerBellException as e:
        logger.error(f"대화 통계 조회 실패: {e}")
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="대화 통계 조회 중 오류가 발생했습니다.")
