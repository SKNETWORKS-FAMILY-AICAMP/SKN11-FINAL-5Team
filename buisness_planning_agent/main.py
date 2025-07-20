"""
Business Planning Agent - 리팩토링된 메인 진입점
마케팅 에이전트의 구조를 참고하여 멀티턴 대화 시스템으로 업그레이드
"""

import logging
import time
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 공통 모듈 임포트
from shared_modules import (
    get_config,
    setup_logging,
    create_success_response,
    create_error_response,
    get_current_timestamp
)

# 새로운 비즈니스 기획 매니저 임포트
from buisness_planning_agent.core.business_planning_manager import BusinessPlanningAgentManager

# 로깅 설정
logger = setup_logging("business_planning_v3", log_file="logs/business_planning.log")

# 설정 로드
config = get_config()

# FastAPI 초기화
app = FastAPI(
    title="Business Planning Agent v3.0",
    description="멀티턴 대화 기반 1인 창업 전문 컨설팅 에이전트",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 비즈니스 기획 매니저 인스턴스
business_manager = BusinessPlanningAgentManager()

# 요청 모델
class UserQuery(BaseModel):
    """사용자 쿼리 요청"""
    user_id: int = Field(..., description="사용자 ID")
    conversation_id: Optional[int] = Field(None, description="대화 ID (멀티턴)")
    message: str = Field(..., description="사용자 메시지")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "conversation_id": 456,
                "message": "창업 아이디어를 검증하고 싶습니다",
            }
        }

# API 엔드포인트
@app.post("/agent/query")
async def process_user_query(request: UserQuery):
    """멀티턴 대화 기반 사용자 쿼리 처리"""
    try:
        start_time = time.time()
        logger.info(f"멀티턴 쿼리 처리 시작 - user_id: {request.user_id}, message: {request.message[:50]}...")
        
        # 비즈니스 기획 매니저로 처리
        result = business_manager.process_user_query(
            user_input=request.message,
            user_id=request.user_id,
            conversation_id=request.conversation_id
        )
        
        # 처리 시간 추가
        result["processing_time"] = time.time() - start_time
        
        logger.info(f"멀티턴 쿼리 처리 완료 - 시간: {result['processing_time']:.2f}초")
        return result
        
    except Exception as e:
        logger.error(f"멀티턴 쿼리 처리 중 오류 발생: {e}")
        return create_error_response(
            error_message=f"쿼리 처리 중 오류가 발생했습니다: {str(e)}",
            error_code="MULTITURN_QUERY_ERROR"
        )

@app.get("/agent/status")
def get_agent_status():
    """에이전트 상태 조회"""
    try:
        status = business_manager.get_agent_status()
        return create_success_response(status)
        
    except Exception as e:
        logger.error(f"상태 조회 실패: {e}")
        return create_error_response(f"상태 조회 실패: {str(e)}", "STATUS_ERROR")

@app.get("/conversation/{conversation_id}/status")
def get_conversation_status(conversation_id: int):
    """특정 대화 상태 조회"""
    try:
        status = business_manager.get_conversation_status(conversation_id)
        return create_success_response(status)
        
    except Exception as e:
        logger.error(f"대화 상태 조회 실패: {e}")
        return create_error_response(f"대화 상태 조회 실패: {str(e)}", "CONVERSATION_STATUS_ERROR")

@app.delete("/conversation/{conversation_id}")
def reset_conversation(conversation_id: int):
    """대화 초기화"""
    try:
        success = business_manager.reset_conversation(conversation_id)
        if success:
            return create_success_response({"message": "대화가 초기화되었습니다", "conversation_id": conversation_id})
        else:
            return create_error_response("대화를 찾을 수 없습니다", "CONVERSATION_NOT_FOUND")
        
    except Exception as e:
        logger.error(f"대화 초기화 실패: {e}")
        return create_error_response(f"대화 초기화 실패: {str(e)}", "CONVERSATION_RESET_ERROR")

@app.get("/health")
def health_check():
    """상태 확인 엔드포인트"""
    try:
        health_data = {
            "service": "business_planning_agent_v3",
            "status": "healthy",
            "timestamp": get_current_timestamp(),
            "version": "3.0.0",
            "features": [
                "멀티턴 대화",
                "단계별 정보 수집",
                "맞춤형 비즈니스 분석",
                "린캔버스 지원",
                "전문가 페르소나"
            ]
        }
        
        return create_success_response(health_data)
        
    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        return create_error_response(f"헬스체크 실패: {str(e)}", "HEALTH_CHECK_ERROR")

# 이전 버전 호환성을 위한 엔드포인트 (Deprecated)
@app.post("/query")
async def legacy_query(request: UserQuery):
    """이전 버전 호환성 엔드포인트 (Deprecated)"""
    logger.warning("Deprecated API 사용: /query -> /agent/query 사용을 권장합니다")
    return await process_user_query(request)

# 메인 실행
if __name__ == "__main__":
    import uvicorn
    
    logger.info("=== Business Planning Agent v3.0 시작 ===")
    logger.info("✅ 마케팅 에이전트 구조 기반 리팩토링 완료")
    logger.info("✅ 멀티턴 대화 시스템 적용")
    logger.info("✅ 공통 모듈 최대 활용")
    logger.info("✅ 구조화된 디렉토리 구성")
    
    uvicorn.run(
        app, 
        host=config.HOST, 
        port=config.PORT,
        log_level=config.LOG_LEVEL.lower()
    )
