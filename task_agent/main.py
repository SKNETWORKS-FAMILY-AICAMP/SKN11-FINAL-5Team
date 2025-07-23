"""
TinkerBell 업무지원 에이전트 v4 - 메인 애플리케이션
공통 모듈을 활용한 FastAPI 애플리케이션
"""

import sys
import os

# 텔레메트리 비활성화 (ChromaDB 오류 방지)
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY'] = 'False' 
os.environ['DO_NOT_TRACK'] = '1'

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from models import UserQuery, AutomationRequest, EmailRequest, InstagramPostRequest
from utils import TaskAgentLogger, TaskAgentResponseFormatter
from agent import TaskAgent
from config import config
from pydantic import BaseModel, EmailStr
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from automation_task.email_service import get_email_service
from automation_task.instagram_service import InstagramPostingService

# 공통 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# 공통 모듈 import
from shared_modules import (
    create_success_response, 
    create_error_response,
    create_conversation, 
    create_message, 
    get_conversation_by_id, 
    get_recent_messages,
    get_session_context,
    insert_message_raw,
    get_current_timestamp,
    create_task_response  # 표준 응답 생성 함수 추가
)
from shared_modules.utils import get_or_create_conversation_session
from shared_modules.logging_utils import setup_logging

# 로깅 설정
logger = setup_logging("task", log_file="logs/task.log")

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

async def get_conversation_history(conversation_id: int, limit: int = 10) -> List[Dict]:
    """대화 히스토리 조회"""
    try:
        with get_session_context() as db:
            messages = get_recent_messages(db, conversation_id, limit)
            
            history = []
            for msg in reversed(messages):  # 시간순 정렬
                # Handle both dict and object types
                if isinstance(msg, dict):
                    # If msg is a dictionary
                    history.append({
                        "role": "user" if msg.get("sender_type") == "user" else "assistant",
                        "content": msg.get("content", ""),
                        "timestamp": msg.get("created_at").isoformat() if msg.get("created_at") else None,
                        "agent_type": msg.get("agent_type")
                    })
                else:
                    # If msg is an object (ORM model)
                    history.append({
                        "role": "user" if getattr(msg, "sender_type", None) == "user" else "assistant",
                        "content": getattr(msg, "content", ""),
                        "timestamp": getattr(msg, "created_at", None).isoformat() if getattr(msg, "created_at", None) else None,
                        "agent_type": getattr(msg, "agent_type", None)
                    })
            
            return history
    except Exception as e:
        logger.error(f"대화 히스토리 조회 실패: {e}")
        return []

async def save_message(conversation_id: int, content: str, sender_type: str, 
                      agent_type: str = None) -> Dict[str, Any]:
    """메시지 저장"""
    try:
        with get_session_context() as db:
            message = create_message(db, conversation_id, sender_type, agent_type, content)
            
            if not message:
                logger.error(f"메시지 저장 실패 - conversation_id: {conversation_id}")
                raise Exception("메시지 저장에 실패했습니다")
            
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
        
        # 1. 대화 세션 처리 - 통일된 로직 사용
        user_id_int = int(query.user_id)
        try:
            session_info = get_or_create_conversation_session(user_id_int, query.conversation_id)
            conversation_id = session_info["conversation_id"]
        except Exception as e:
            logger.error(f"대화 세션 처리 실패: {e}")
            return create_error_response("대화 세션 생성에 실패했습니다", "SESSION_CREATE_ERROR")
        
        # 2. 대화 히스토리 조회
        history = await get_conversation_history(conversation_id)
        
        # 3. 사용자 메시지 저장
        await save_message(conversation_id, query.message, "user")
        
        # 4. 쿼리 업데이트
        query.conversation_id = conversation_id
        
        # 5. 에이전트 처리
        response = await agent.process_query(query, history)
        
        # 6. 에이전트 응답 저장
        try:
            insert_message_raw(
                conversation_id=conversation_id,
                sender_type="agent",
                agent_type="task_agent",
                content=response.response
            )
        except Exception as e:
            logger.warning(f"에이전트 메시지 저장 실패: {e}")
        
        TaskAgentLogger.log_user_interaction(
            user_id=query.user_id,
            action="query_completed",
            details=f"conversation_id: {conversation_id}, intent: {response.metadata.get('intent', 'unknown')}"
        )
        
        # 7. 표준 응답 생성
        # First, get all attributes we want to exclude
        excluded_keys = {
            'response', 'conversation_id', 'topics', 'sources', 
            'intent', 'urgency', 'actions', 'automation_created', 'response_type'
        }
        
        # Get additional attributes from response, excluding the ones we handle explicitly
        additional_attrs = {}
        if hasattr(response, 'dict') and callable(response.dict):
            additional_attrs = {
                k: v for k, v in response.dict().items() 
                if k not in excluded_keys
            }
        
        response_data = create_task_response(
            conversation_id=conversation_id,
            answer=response.response or "",
            topics=[response.metadata.get('intent', 'general_inquiry')],
            sources=getattr(response, 'sources', "") or "",
            intent=response.metadata.get('intent', 'general_inquiry') or 'general_inquiry',
            urgency=getattr(response, 'urgency', 'medium') or 'medium',
            actions=getattr(response, 'actions', []) or [],
            automation_created=getattr(response, 'automation_created', False) or False,
            **additional_attrs
        )
        
        return create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"쿼리 처리 실패: {e}")
        error_response = TaskAgentResponseFormatter.error_response(
            error_message=str(e),
            error_code="QUERY_PROCESSING_ERROR",
            conversation_id=query.conversation_id
        )
        raise HTTPException(status_code=500, detail=error_response)

# ===== 시스템 API =====

@app.get("/health")
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

@app.get("/status")
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

# ==== Email & Instagram API ====

@app.post("/email/send")
async def send_email(req: EmailRequest):
    email_service = get_email_service()
    result = await email_service.send_email(
        to_emails=req.to_emails,
        subject=req.subject,
        body=req.body,
        html_body=req.html_body,
        attachments=req.attachments,
        cc_emails=req.cc_emails,
        bcc_emails=req.bcc_emails,
        from_email=req.from_email,
        from_name=req.from_name,
        service=req.service,
    )
    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("error", "이메일 발송 실패"))
    return result


@app.post("/instagram/post")
async def post_to_instagram(req: InstagramPostRequest):
    insta_service = InstagramPostingService()
    result = await insta_service.post_to_instagram(
        instagram_id=req.instagram_id,
        access_token=req.access_token,
        image_url=req.image_url,
        caption=req.caption or ""
    )
    return result



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

@app.get("/dev/cache/clear")
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

@app.get("/dev/cache/stats")
async def get_cache_stats():
    """캐시 통계 조회"""
    try:
        from utils import task_cache
        stats = task_cache.get_stats()
        return create_success_response(data=stats)
    except Exception as e:
        logger.error(f"캐시 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dev/config")
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
