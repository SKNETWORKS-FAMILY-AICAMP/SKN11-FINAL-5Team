"""
TinkerBell 업무지원 에이전트 v4 - 메인 애플리케이션
공통 모듈을 활용한 FastAPI 애플리케이션
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any, List

# 공통 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "../shared_modules"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 공통 모듈 import
from utils import create_success_response, create_error_response

from models import UserQuery, AutomationRequest
from agent import TaskAgent
from shared_modules.queries import create_conversation, create_message, create_user, get_conversation_by_id, get_recent_messages, get_user_by_email 
from utils import TaskAgentLogger, TaskAgentResponseFormatter, generate_conversation_id
from config import config

# 로깅 설정
TaskAgentLogger.setup(config.LOG_LEVEL)
logger = logging.getLogger("task_agent")

# FastAPI 앱 생성
app = FastAPI(
    title="TinkerBell 업무지원 에이전트 v4",
    description="공통 모듈을 활용한 AI 기반 업무지원 시스템",
    version="4.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 글로벌 에이전트 인스턴스
agent = None

# ===== 대화 관리 함수 =====

async def get_or_create_conversation(user_id: int, conversation_id: str = None) -> Dict[str, Any]:
    """대화 세션 조회 또는 생성"""
    try:
        if conversation_id:
            conversation = get_conversation_by_id(int(conversation_id))
            if conversation and conversation.user_id == user_id:
                return {
                    "conversation_id": conversation.conversation_id,
                    "is_new": False
                }
        
        # 새 대화 세션 생성
        conversation = create_conversation(user_id)
        return {
            "conversation_id": conversation.conversation_id,
            "is_new": True
        }
    except Exception as e:
        logger.error(f"대화 세션 처리 실패: {e}")
        raise

async def get_conversation_history(conversation_id: int, limit: int = 10) -> List[Dict]:
    """대화 히스토리 조회"""
    try:
        messages = get_recent_messages(conversation_id, limit)
        
        history = []
        for msg in reversed(messages):  # 시간순 정렬
            history.append({
                "role": "user" if msg.sender_type == "user" else "assistant",
                "content": msg.content,
                "timestamp": msg.created_at.isoformat() if msg.created_at else None,
                "agent_type": msg.agent_type
            })
        
        return history
    except Exception as e:
        logger.error(f"대화 히스토리 조회 실패: {e}")
        return []

async def save_message(conversation_id: int, content: str, sender_type: str, 
                      agent_type: str = None) -> Dict[str, Any]:
    """메시지 저장"""
    try:
        message = create_message(conversation_id, sender_type, content, agent_type)
        
        TaskAgentLogger.log_user_interaction(
            user_id=str(conversation_id), 
            action="message_saved",
            details=f"sender: {sender_type}, agent: {agent_type}"
        )
        
        return {
            "message_id": message.message_id,
            "created_at": message.created_at.isoformat() if message.created_at else None
        }
    except Exception as e:
        logger.error(f"메시지 저장 실패: {e}")
        raise

# ===== 애플리케이션 이벤트 =====

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작"""
    global agent
    
    logger.info("TinkerBell 업무지원 에이전트 v4 시작")
    
    # 환경 설정 검증
    validation = config.validate()
    if not validation["is_valid"]:
        logger.error(f"환경 설정 오류: {validation['issues']}")
        raise RuntimeError("환경 설정이 올바르지 않습니다.")
    
    for warning in validation["warnings"]:
        logger.warning(warning)
    
    # 에이전트 초기화
    try:
        agent = TaskAgent()
        logger.info("Task Agent 초기화 완료")
    except Exception as e:
        logger.error(f"에이전트 초기화 실패: {e}")
        raise RuntimeError("에이전트 초기화 실패")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료"""
    logger.info("TinkerBell 업무지원 에이전트 v4 종료")
    if agent:
        try:
            await agent.cleanup_resources()
        except Exception as e:
            logger.error(f"에이전트 정리 실패: {e}")

# ===== 핵심 API 엔드포인트 =====

@app.post("/agent/query")
async def process_user_query(query: UserQuery):
    """사용자 쿼리 처리"""
    try:
        TaskAgentLogger.log_user_interaction(
            user_id=query.user_id, 
            action="query_received",
            details=f"persona: {query.persona}, message_length: {len(query.message)}"
        )
        
        # 1. 대화 세션 처리
        user_id_int = int(query.user_id)
        conversation_info = await get_or_create_conversation(user_id_int, query.conversation_id)
        conversation_id = conversation_info["conversation_id"]
        
        # 2. 대화 히스토리 조회
        history = await get_conversation_history(conversation_id)
        
        # 3. 사용자 메시지 저장
        await save_message(conversation_id, query.message, "user")
        
        # 4. 쿼리 업데이트
        query.conversation_id = str(conversation_id)
        
        # 5. 에이전트 처리
        response = await agent.process_query(query, history)
        
        # 6. 에이전트 응답 저장
        await save_message(conversation_id, response.response, "agent", "task_agent")
        
        TaskAgentLogger.log_user_interaction(
            user_id=query.user_id,
            action="query_completed",
            details=f"conversation_id: {conversation_id}, intent: {response.intent}"
        )
        
        return response.dict()
        
    except Exception as e:
        logger.error(f"쿼리 처리 실패: {e}")
        error_response = TaskAgentResponseFormatter.error_response(
            error_message=str(e),
            error_code="QUERY_PROCESSING_ERROR",
            conversation_id=query.conversation_id
        )
        raise HTTPException(status_code=500, detail=error_response)

@app.post("/api/v4/automation")
async def create_automation_task(request: AutomationRequest):
    """자동화 작업 생성"""
    try:
        TaskAgentLogger.log_automation_task(
            task_id="pending",
            task_type=request.task_type.value,
            status="creating",
            details=f"user_id: {request.user_id}"
        )
        
        response = await agent.create_automation_task(request)
        
        TaskAgentLogger.log_automation_task(
            task_id=str(response.task_id),
            task_type=request.task_type.value,
            status=response.status.value,
            details="automation task created successfully"
        )
        
        return create_success_response(
            data=response.dict(),
            message="자동화 작업이 생성되었습니다."
        )
        
    except Exception as e:
        logger.error(f"자동화 작업 생성 실패: {e}")
        TaskAgentLogger.log_automation_task(
            task_id="failed",
            task_type=request.task_type.value,
            status="failed",
            details=f"error: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v4/automation/{task_id}/status")
async def get_automation_status(task_id: int):
    """자동화 작업 상태 조회"""
    try:
        status = await agent.get_automation_status(task_id)
        
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        
        return create_success_response(data=status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"자동화 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v4/automation/{task_id}")
async def cancel_automation_task(task_id: int):
    """자동화 작업 취소"""
    try:
        success = await agent.cancel_automation_task(task_id)
        
        if success:
            TaskAgentLogger.log_automation_task(
                task_id=str(task_id),
                task_type="unknown",
                status="cancelled",
                details="cancelled by user request"
            )
            return create_success_response(message="자동화 작업이 취소되었습니다.")
        else:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없거나 취소할 수 없습니다.")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"자동화 작업 취소 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== 사용자 관리 API =====

@app.post("/api/v4/users/register")
async def register_user(email: str, password: str, nickname: str = None, business_type: str = None):
    """사용자 등록"""
    try:
        # 이메일 검증 (공통 모듈 활용)
        from utils import validate_email
        if not validate_email(email):
            raise HTTPException(status_code=400, detail="유효하지 않은 이메일 형식입니다.")
        
        # 중복 검사
        existing_user = get_user_by_email(email)
        if existing_user:
            raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
        
        user = create_user(email, password, nickname, business_type)
        
        TaskAgentLogger.log_user_interaction(
            user_id=str(user.user_id),
            action="user_registered",
            details=f"email: {email}, business_type: {business_type}"
        )
        
        return create_success_response(
            data={
                "user_id": user.user_id,
                "email": user.email,
                "nickname": user.nickname,
                "business_type": user.business_type,
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            message="사용자 등록이 완료되었습니다."
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 등록 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== 대화 관리 API =====

@app.get("/api/v4/conversations/{user_id}")
async def get_user_conversations(user_id: int):
    """사용자의 대화 세션 목록 조회"""
    try:
        from shared_modules.queries import get_user_conversations as get_conversations_query
        conversations = get_conversations_query(user_id, visible_only=True)
        
        conversation_list = []
        for conv in conversations:
            conversation_list.append({
                "conversation_id": conv.conversation_id,
                "conversation_type": conv.conversation_type,
                "started_at": conv.started_at.isoformat() if conv.started_at else None,
                "ended_at": conv.ended_at.isoformat() if conv.ended_at else None
            })
        
        return create_success_response(data=conversation_list)
            
    except Exception as e:
        logger.error(f"대화 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v4/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: int, limit: int = 50):
    """대화의 메시지 목록 조회"""
    try:
        history = await get_conversation_history(conversation_id, limit)
        return create_success_response(data=history)
        
    except Exception as e:
        logger.error(f"메시지 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== 시스템 API =====

@app.get("/api/v4/health")
async def health_check():
    """헬스 체크"""
    try:
        if agent:
            status = await agent.get_status()
            return create_success_response(data=status, message="시스템 상태 정상")
        else:
            return create_error_response("에이전트가 초기화되지 않았습니다.", "AGENT_NOT_INITIALIZED")
        
    except Exception as e:
        logger.error(f"헬스 체크 실패: {e}")
        return create_error_response(str(e), "HEALTH_CHECK_ERROR")

@app.get("/api/v4/status")
async def get_system_status():
    """시스템 상태 조회"""
    try:
        base_status = {
            "service": "TinkerBell Task Agent v4",
            "version": "4.0.0",
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "openai_configured": bool(config.OPENAI_API_KEY),
                "google_configured": bool(config.GOOGLE_API_KEY),
                "mysql_configured": bool(config.MYSQL_URL),
                "chroma_configured": bool(config.CHROMA_PERSIST_DIR)
            },
            "config_validation": config.validate()
        }
        
        if agent:
            agent_status = await agent.get_status()
            base_status.update(agent_status)
            base_status["status"] = "healthy"
        else:
            base_status["status"] = "error"
            base_status["message"] = "에이전트가 초기화되지 않았습니다."
        
        return base_status
        
    except Exception as e:
        logger.error(f"시스템 상태 조회 실패: {e}")
        return {
            "service": "TinkerBell Task Agent v4",
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ===== 에러 핸들러 =====

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 예외 처리"""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc.detail, f"HTTP_{exc.status_code}")
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """일반 예외 처리"""
    logger.error(f"처리되지 않은 예외: {exc}")
    return JSONResponse(
        status_code=500,
        content=create_error_response("내부 서버 오류가 발생했습니다.", "INTERNAL_ERROR")
    )

# ===== 개발/관리용 API =====

@app.get("/api/v4/dev/cache/clear")
async def clear_cache():
    """캐시 클리어"""
    try:
        if agent:
            # Task Agent 캐시 클리어
            from utils import task_cache
            task_cache.clear_all()
            
            return create_success_response(message="캐시가 클리어되었습니다.")
        else:
            return create_error_response("에이전트가 초기화되지 않았습니다.", "AGENT_NOT_INITIALIZED")
    except Exception as e:
        logger.error(f"캐시 클리어 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v4/dev/cache/stats")
async def get_cache_stats():
    """캐시 통계 조회"""
    try:
        from utils import task_cache
        stats = task_cache.get_stats()
        return create_success_response(data=stats)
    except Exception as e:
        logger.error(f"캐시 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v4/dev/config")
async def get_config_info():
    """설정 정보 조회 (개발용)"""
    try:
        config_dict = config.get_config_dict()
        return create_success_response(data=config_dict)
    except Exception as e:
        logger.error(f"설정 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
        log_level=config.LOG_LEVEL.lower()
    )
