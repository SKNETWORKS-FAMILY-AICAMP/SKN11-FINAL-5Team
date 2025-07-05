"""
TinkerBell 업무지원 에이전트 v3 - 메인 애플리케이션
간소화된 FastAPI 애플리케이션
"""

import logging
from datetime import datetime
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import UserQuery, AutomationRequest
from agent import TaskAgent
from database import init_database
from db_services import user_service, conversation_service, message_service
from utils import Logger, ResponseFormatter, generate_id
from config import config

# 로깅 설정
Logger.setup(config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="TinkerBell 업무지원 에이전트 v3",
    description="간소화된 AI 기반 업무지원 시스템",
    version="3.0.0"
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
    with conversation_service() as service:
        if conversation_id:
            conversation = service.get_conversation_by_id(int(conversation_id))
            if conversation and conversation.user_id == user_id:
                return {
                    "conversation_id": conversation.conversation_id,
                    "is_new": False
                }
        
        # 새 대화 세션 생성
        conversation = service.create_conversation(user_id)
        return {
            "conversation_id": conversation.conversation_id,
            "is_new": True
        }

async def get_conversation_history(conversation_id: int, limit: int = 10) -> List[Dict]:
    """대화 히스토리 조회"""
    with message_service() as service:
        messages = service.get_recent_messages(conversation_id, limit)
        
        history = []
        for msg in reversed(messages):  # 시간순 정렬
            history.append({
                "role": "user" if msg.sender_type == "user" else "assistant",
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
                "agent_type": msg.agent_type
            })
        
        return history

async def save_message(conversation_id: int, content: str, sender_type: str, 
                      agent_type: str = None) -> Dict[str, Any]:
    """메시지 저장"""
    with message_service() as service:
        message = service.create_message(conversation_id, sender_type, content, agent_type)
        return {
            "message_id": message.message_id,
            "created_at": message.created_at.isoformat()
        }

# ===== 애플리케이션 이벤트 =====

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작"""
    global agent
    
    logger.info("TinkerBell 업무지원 에이전트 v3 시작")
    
    # 환경 설정 검증
    validation = config.validate()
    if not validation["is_valid"]:
        logger.error(f"환경 설정 오류: {validation['issues']}")
        raise RuntimeError("환경 설정이 올바르지 않습니다.")
    
    for warning in validation["warnings"]:
        logger.warning(warning)
    
    # 데이터베이스 초기화
    try:
        init_database()
        logger.info("데이터베이스 초기화 완료")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        raise RuntimeError("데이터베이스 초기화 실패")
    
    # 에이전트 초기화
    try:
        agent = TaskAgent()
        logger.info("에이전트 초기화 완료")
    except Exception as e:
        logger.error(f"에이전트 초기화 실패: {e}")
        raise RuntimeError("에이전트 초기화 실패")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료"""
    logger.info("TinkerBell 업무지원 에이전트 v3 종료")
    if agent:
        await agent.cleanup_resources()

# ===== 핵심 API 엔드포인트 =====

@app.post("/agent/query")
async def process_user_query(query: UserQuery):
    """사용자 쿼리 처리"""
    try:
        Logger.log_api_request("/agent/query", query.user_id)
        
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
        
        logger.info(f"쿼리 처리 완료: conversation_id={conversation_id}")
        
        return response.dict()
        
    except Exception as e:
        logger.error(f"쿼리 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v3/automation")
async def create_automation_task(request: AutomationRequest):
    """자동화 작업 생성"""
    try:
        Logger.log_api_request("/api/v3/automation", str(request.user_id))
        
        response = await agent.create_automation_task(request)
        
        return ResponseFormatter.success(
            data=response.dict(),
            message="자동화 작업이 생성되었습니다."
        )
        
    except Exception as e:
        logger.error(f"자동화 작업 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v3/automation/{task_id}/status")
async def get_automation_status(task_id: int):
    """자동화 작업 상태 조회"""
    try:
        status = await agent.get_automation_status(task_id)
        
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        
        return ResponseFormatter.success(data=status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"자동화 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v3/automation/{task_id}")
async def cancel_automation_task(task_id: int):
    """자동화 작업 취소"""
    try:
        success = await agent.cancel_automation_task(task_id)
        
        if success:
            return ResponseFormatter.success(message="자동화 작업이 취소되었습니다.")
        else:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없거나 취소할 수 없습니다.")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"자동화 작업 취소 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== 사용자 관리 API =====

@app.post("/api/v3/users/register")
async def register_user(email: str, password: str, nickname: str = None, business_type: str = None):
    """사용자 등록"""
    try:
        with user_service() as service:
            # 중복 검사
            existing_user = service.get_user_by_email(email)
            if existing_user:
                raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
            
            user = service.create_user(email, password, nickname, business_type)
            
            return ResponseFormatter.success(
                data={
                    "user_id": user.user_id,
                    "email": user.email,
                    "nickname": user.nickname,
                    "business_type": user.business_type,
                    "created_at": user.created_at.isoformat()
                },
                message="사용자 등록이 완료되었습니다."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 등록 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v3/users/login")
async def login_user(email: str, password: str):
    """사용자 로그인"""
    try:
        with user_service() as service:
            user = service.verify_password(email, password)
            if not user:
                raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
            
            return ResponseFormatter.success(
                data={
                    "user_id": user.user_id,
                    "email": user.email,
                    "nickname": user.nickname,
                    "business_type": user.business_type
                },
                message="로그인이 성공했습니다."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그인 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== 대화 관리 API =====

@app.get("/api/v3/conversations/{user_id}")
async def get_user_conversations(user_id: int):
    """사용자의 대화 세션 목록 조회"""
    try:
        with conversation_service() as service:
            conversations = service.get_user_conversations(user_id, visible_only=True)
            
            conversation_list = []
            for conv in conversations:
                conversation_list.append({
                    "conversation_id": conv.conversation_id,
                    "conversation_type": conv.conversation_type,
                    "started_at": conv.started_at.isoformat() if conv.started_at else None,
                    "ended_at": conv.ended_at.isoformat() if conv.ended_at else None
                })
            
            return ResponseFormatter.success(data=conversation_list)
            
    except Exception as e:
        logger.error(f"대화 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v3/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: int, limit: int = 50):
    """대화의 메시지 목록 조회"""
    try:
        history = await get_conversation_history(conversation_id, limit)
        return ResponseFormatter.success(data=history)
        
    except Exception as e:
        logger.error(f"메시지 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== 시스템 API =====

@app.get("/api/v3/health")
async def health_check():
    """헬스 체크"""
    try:
        if agent:
            status = await agent.get_status()
            return ResponseFormatter.success(data=status, message="시스템 상태 정상")
        else:
            return ResponseFormatter.error("에이전트가 초기화되지 않았습니다.")
        
    except Exception as e:
        logger.error(f"헬스 체크 실패: {e}")
        return ResponseFormatter.error(str(e))

@app.get("/api/v3/status")
async def get_system_status():
    """시스템 상태 조회"""
    try:
        base_status = {
            "service": "TinkerBell Task Agent v3",
            "version": "3.0.0",
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "openai_configured": bool(config.OPENAI_API_KEY),
                "google_configured": bool(config.GOOGLE_API_KEY)
            }
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
            "service": "TinkerBell Task Agent v3",
            "status": "error",
            "error": str(e)
        }

# ===== 에러 핸들러 =====

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 예외 처리"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseFormatter.error(exc.detail, f"HTTP_{exc.status_code}")
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """일반 예외 처리"""
    logger.error(f"처리되지 않은 예외: {exc}")
    return JSONResponse(
        status_code=500,
        content=ResponseFormatter.error("내부 서버 오류가 발생했습니다.", "INTERNAL_ERROR")
    )

# ===== 개발용 API =====

@app.get("/api/v3/dev/cache/clear")
async def clear_cache():
    """캐시 클리어"""
    try:
        if agent:
            agent.cache_manager.clear()
            return ResponseFormatter.success(message="캐시가 클리어되었습니다.")
        else:
            return ResponseFormatter.error("에이전트가 초기화되지 않았습니다.")
    except Exception as e:
        logger.error(f"캐시 클리어 실패: {e}")
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
