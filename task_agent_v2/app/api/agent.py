"""
TinkerBell 프로젝트 - 에이전트 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from ..core.dependencies import get_agent_service, get_conversation_service, validate_user_id
from ..core.response import ResponseFormatter
from ..core.exceptions import to_http_exception, TinkerBellException
from ..schemas.base import UserQueryRequest, UserQueryResponse
from ..services.agent_service import AgentService
from ..services.conversation_service import ConversationService

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["agent"])

@router.post("/query", response_model=Dict[str, Any])
async def process_query(
    query: UserQueryRequest,
    agent_service: AgentService = Depends(get_agent_service),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """사용자 쿼리 처리 (대화 히스토리 포함)"""
    try:
        # 1. 사용자 ID 검증
        user_id_int = validate_user_id(query.user_id)
        
        # 2. 대화 세션 처리
        conversation = await conversation_service.get_or_create_conversation(
            user_id=user_id_int,
            conversation_id=query.conversation_id
        )
        
        # 3. 대화 히스토리 조회
        history = await conversation_service.get_conversation_history(
            conversation.conversation_id, limit=10
        )
        
        logger.info(f"대화 히스토리 조회: {len(history)}개 메시지")
        
        # 4. 사용자 메시지 저장
        await conversation_service.save_user_message(
            conversation.conversation_id, query.message
        )
        
        # 5. 쿼리에 conversation_id 설정
        query.conversation_id = str(conversation.conversation_id)
        
        # 6. 에이전트 쿼리 처리
        response = await agent_service.process_query(query, history)
        
        # 7. 에이전트 응답 저장
        await conversation_service.save_agent_message(
            conversation_id=conversation.conversation_id,
            content=response.response,
            agent_type="task_agent"
        )
        
        # 8. 응답에 conversation_id 설정
        response.conversation_id = str(conversation.conversation_id)
        
        logger.info(f"쿼리 처리 완료: conversation_id={conversation.conversation_id}")
        
        return ResponseFormatter.success(
            data=response.dict(),
            message="쿼리가 성공적으로 처리되었습니다."
        )
        
    except TinkerBellException as e:
        logger.error(f"쿼리 처리 실패: {e}")
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류가 발생했습니다.")

@router.get("/status")
async def get_agent_status(
    agent_service: AgentService = Depends(get_agent_service)
):
    """에이전트 상태 조회"""
    try:
        status = await agent_service.get_status()
        
        return ResponseFormatter.success(
            data=status,
            message="에이전트 상태 조회 완료"
        )
        
    except Exception as e:
        logger.error(f"에이전트 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/clear")
async def clear_cache(
    agent_service: AgentService = Depends(get_agent_service)
):
    """캐시 클리어 (개발용)"""
    try:
        # 캐시 클리어 로직
        if hasattr(agent_service, 'cache_manager'):
            agent_service.cache_manager.clear()
            
        return ResponseFormatter.success(
            message="캐시가 클리어되었습니다."
        )
        
    except Exception as e:
        logger.error(f"캐시 클리어 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check(
    agent_service: AgentService = Depends(get_agent_service)
):
    """헬스 체크"""
    try:
        status = await agent_service.get_status()
        
        return ResponseFormatter.health_response(
            status="healthy" if status.get("status") == "healthy" else "unhealthy",
            components=status
        )
        
    except Exception as e:
        logger.error(f"헬스 체크 실패: {e}")
        return ResponseFormatter.health_response(
            status="unhealthy",
            components={"error": str(e)}
        )
