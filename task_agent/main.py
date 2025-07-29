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

import uuid
import httpx
from fastapi import Request  # 추가
from fastapi.encoders import jsonable_encoder
# Add these imports if not already present
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from models import (UserQuery, AutomationRequest, EmailRequest, 
                    InstagramPostRequest, EventCreate, EventUpdate, EventResponse, AiContentSaveRequest,
                    CalendarListResponse, QuickEventCreate, BaseContentRequest,  ManualContentRequest, GenerateContentRequest)
from utils import TaskAgentLogger, TaskAgentResponseFormatter
from agent import TaskAgent
from config import config
from pydantic import BaseModel

from automation_task.email_service import get_email_service
from automation_task.instagram_service import InstagramPostingService
from shared_modules.queries import create_automation_task 

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from shared_modules.database import get_db_dependency as get_db
from models import AutomationTask  # 자동화 테이블
from sqlalchemy import text 

from fastapi import APIRouter
router = APIRouter()

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


# 관리자 템플릿 조회
@app.get("/api/email/templates")
def get_email_templates(user_id: int = Query(...), db: Session = Depends(get_db)):
    try:
        rows = db.execute(
            text("""
                SELECT * FROM template_message
                WHERE user_id = :user_id OR user_id = 3
                ORDER BY created_at DESC
            """),
            {"user_id": user_id}
        ).fetchall()

        templates = [dict(row._mapping) for row in rows]
        return {"success": True, "templates": templates}
    except Exception as e:
        return {"success": False, "error": str(e)}

class EmailTemplateCreateRequest(BaseModel):
    user_id: int
    title: str
    content: str
    template_type: str  # 예: "user_made"
    channel_type: Optional[str] = "email"
    content_type: Optional[str] = "default"

@app.post("/api/email/templates")
def create_email_template(req: EmailTemplateCreateRequest, db: Session = Depends(get_db)):
    try:
        db.execute(
            text("""  # ← 이 부분 감싸기!
                INSERT INTO template_message 
                (user_id, title, content, template_type, channel_type, content_type, created_at)
                VALUES (:user_id, :title, :content, :template_type, :channel_type, :content_type, NOW())
            """),
            {
                "user_id": req.user_id,
                "title": req.title,
                "content": req.content,
                "template_type": req.template_type,
                "channel_type": req.channel_type,
                "content_type": req.content_type,
            }
        )
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

# ===== Instagram OAuth 인증 API =====
agent = None
instagram_service = InstagramPostingService()  

@app.get("/instagram/auth")
async def get_instagram_auth_url():
    """Instagram OAuth 인증 URL 생성"""
    try:
        auth_url = instagram_service.get_instagram_auth_url()
        return create_success_response({
            "auth_url": auth_url,
            "message": "이 URL로 이동하여 Instagram 계정을 연결하세요."
        })
    except Exception as e:
        logger.error(f"Instagram 인증 URL 생성 실패: {str(e)}")
        return create_error_response(
            f"Instagram 인증 URL 생성에 실패했습니다: {str(e)}",
            "INSTAGRAM_AUTH_URL_ERROR"
        )

@app.get("/instagram/auth/callback")
async def instagram_callback(
    code: str = Query(..., description="Instagram에서 받은 인증 코드"),
    state: Optional[str] = Query(None, description="CSRF 보호용 state 파라미터")
):
    """Instagram OAuth 콜백 처리 및 토큰 발급"""
    try:
        # 인증 코드로 토큰 발급
        token_data = await instagram_service.get_access_token(code, state)
        
        logger.info(f"Instagram 토큰 발급 성공: 사용자 {token_data['user_id']}")
        
        return create_success_response({
            "access_token": token_data["access_token"],
            "user_id": token_data["user_id"],
            "token_type": token_data["token_type"],
            "expires_in": token_data["expires_in"],
            "message": "Instagram 계정이 성공적으로 연결되었습니다."
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Instagram 콜백 처리 실패: {str(e)}")
        return create_error_response(
            f"Instagram 인증 처리 중 오류가 발생했습니다: {str(e)}",
            "INSTAGRAM_CALLBACK_ERROR"
        )

@app.post("/instagram/tokens/refresh")
async def refresh_instagram_token(
    user_id: str = Query(..., description="사용자 ID")
):
    """Instagram 토큰 갱신"""
    try:
        # 현재 토큰 로드
        token_data = await instagram_service.load_tokens(user_id)
        if not token_data:
            return create_error_response(
                "저장된 토큰을 찾을 수 없습니다.",
                "TOKEN_NOT_FOUND"
            )
        
        # 토큰 갱신
        refreshed_data = await instagram_service.refresh_long_lived_token(
            token_data["access_token"]
        )
        
        # 갱신된 토큰 저장
        await instagram_service.save_tokens(user_id, refreshed_data)
        
        return create_success_response({
            "message": "Instagram 토큰이 성공적으로 갱신되었습니다.",
            "expires_in": refreshed_data["expires_in"],
            "user_id": user_id
        })
        
    except Exception as e:
        logger.error(f"Instagram 토큰 갱신 실패: {str(e)}")
        return create_error_response(
            f"Instagram 토큰 갱신 중 오류가 발생했습니다: {str(e)}",
            "TOKEN_REFRESH_ERROR"
        )

@app.get("/instagram/tokens/status/{user_id}")
async def get_instagram_token_status(user_id: str):
    """Instagram 토큰 상태 확인"""
    try:
        token_data = await instagram_service.load_tokens(user_id)
        if not token_data:
            return create_success_response({
                "user_id": user_id,
                "has_token": False,
                "message": "저장된 토큰이 없습니다."
            })
        
        from datetime import datetime
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        now = datetime.now()
        days_until_expiry = (expires_at - now).days
        
        return create_success_response({
            "user_id": user_id,
            "has_token": True,
            "expires_at": token_data["expires_at"],
            "days_until_expiry": days_until_expiry,
            "needs_refresh": days_until_expiry < 7,
            "message": f"토큰이 {days_until_expiry}일 후 만료됩니다."
        })
        
    except Exception as e:
        logger.error(f"Instagram 토큰 상태 확인 실패: {str(e)}")
        return create_error_response(
            f"Instagram 토큰 상태 확인 중 오류가 발생했습니다: {str(e)}",
            "TOKEN_STATUS_ERROR"
        )

@app.post("/instagram/post")
async def post_to_instagram_enhanced(req: InstagramPostRequest):
    """Instagram 게시글 업로드 (자동 토큰 관리 포함)"""
    try:
        # 유효한 토큰 가져오기 (자동 갱신 포함)
        access_token = await instagram_service.get_valid_access_token(req.instagram_id)
        if not access_token:
            return create_error_response(
                "유효한 Instagram 토큰이 없습니다. 먼저 Instagram 계정을 연결하세요.",
                "INVALID_TOKEN"
            )
        
        # Instagram에 게시글 업로드
        result = await instagram_service.post_to_instagram(
            instagram_id=req.instagram_id,
            access_token=access_token,
            image_url=req.image_url,
            caption=req.caption or ""
        )
        
        return create_success_response({
            "success": True,
            "post_id": result.get("id"),
            "post_url": result.get("permalink"),
            "message": "Instagram에 게시글이 성공적으로 업로드되었습니다."
        })
        
    except Exception as e:
        logger.error(f"Instagram 게시글 업로드 실패: {str(e)}")
        return create_error_response(
            f"Instagram 게시글 업로드 중 오류가 발생했습니다: {str(e)}",
            "INSTAGRAM_POST_ERROR"
        )

@app.delete("/instagram/tokens/{user_id}")
async def revoke_instagram_token(user_id: str):
    """Instagram 토큰 취소 및 삭제"""
    try:
        success = await instagram_service.revoke_access_token(user_id)
        if success:
            return create_success_response({
                "message": f"사용자 {user_id}의 Instagram 토큰이 성공적으로 삭제되었습니다.",
                "user_id": user_id
            })
        else:
            return create_error_response(
                "삭제할 Instagram 토큰을 찾을 수 없습니다.",
                "TOKEN_NOT_FOUND"
            )
            
    except Exception as e:
        logger.error(f"Instagram 토큰 삭제 실패: {str(e)}")
        return create_error_response(
            f"Instagram 토큰 삭제 중 오류가 발생했습니다: {str(e)}",
            "TOKEN_DELETE_ERROR"
        )

@app.get("/instagram/posts/{user_id}")
async def get_instagram_user_posts(
    user_id: str,
    limit: int = Query(10, ge=1, le=50, description="가져올 게시글 수")
):
    """사용자의 Instagram 게시글 목록 조회"""
    try:
        # 유효한 토큰 가져오기
        access_token = await instagram_service.get_valid_access_token(user_id)
        if not access_token:
            return create_error_response(
                "유효한 Instagram 토큰이 없습니다.",
                "INVALID_TOKEN"
            )
        
        # 게시글 목록 조회
        posts = await instagram_service.get_user_instagram_posts(
            access_token=access_token,
            instagram_id=user_id,
            limit=limit
        )
        
        return create_success_response({
            "user_id": user_id,
            "posts": posts,
            "message": f"{len(posts.get('data', []))}개의 게시글을 조회했습니다."
        })
        
    except Exception as e:
        logger.error(f"Instagram 게시글 조회 실패: {str(e)}")
        return create_error_response(
            f"Instagram 게시글 조회 중 오류가 발생했습니다: {str(e)}",
            "INSTAGRAM_POSTS_ERROR"
        )


# ===== 간단한 Google API 클라이언트 구현 =====

# 리팩토링된 서비스 클래스들 import
from task_agent.automation_task.google_calendar_service import (
    GoogleCalendarService, GoogleCalendarConfig
)

# 실제 구현체들
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# 공통 모듈에서 실제 구현체들 import
from task_agent.automation_task.common.auth_manager import AuthManager
from task_agent.automation_task.common.http_client import HttpClient
from task_agent.automation_task.common.utils import AutomationDateTimeUtils
import urllib.parse

class SimpleGoogleApiClient:
    def __init__(self):
        pass
    
    def build_service(self, service_name: str, version: str, credentials):
        # 올바른 Google API 클라이언트 사용
        from googleapiclient.discovery import build
        return build(service_name, version, credentials=credentials)

# 글로벌 캘린더 서비스 인스턴스
_calendar_service = None

def get_calendar_service() -> GoogleCalendarService:
    """Google Calendar Service 의존성 주입"""
    global _calendar_service
    if _calendar_service is None:
        # 설정 로드
        config = GoogleCalendarConfig({
            "google_calendar": {
                "client_id": os.getenv("GOOGLE_CALENDAR_CLIENT_ID", "your_client_id"),
                "client_secret": os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET", "your_client_secret"),
                "redirect_uri": os.getenv("GOOGLE_CALENDAR_REDIRECT_URI", "http://localhost:8080/callback"),
                "token_url": "https://oauth2.googleapis.com/token",
                "default_timezone": os.getenv("GOOGLE_CALENDAR_DEFAULT_TIMEZONE", "Asia/Seoul")
            }
        })
        
        # 의존성들 생성 (auth 파라미터 제거)
        _calendar_service = GoogleCalendarService(
            api=SimpleGoogleApiClient(),
            time_utils=AutomationDateTimeUtils(),
            config=config
        )
    
    return _calendar_service

@app.get("/calendars", response_model=CalendarListResponse)
async def get_calendars(
    user_id: int = Query(..., description="사용자 ID"),
    calendar_service: GoogleCalendarService = Depends(get_calendar_service)
):
    """사용자의 캘린더 목록 조회"""
    try:
        service = calendar_service._get_service(user_id)
        calendars_result = service.calendarList().list().execute()
        calendars = calendars_result.get('items', [])
        
        return CalendarListResponse(
            calendars=calendars,
            count=len(calendars)
        )
    except Exception as e:
        logger.error(f"캘린더 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/events", response_model=Dict[str, Any])
async def create_event(
    user_id: int = Query(..., description="사용자 ID"),
    event_data: EventCreate = ...,
    calendar_service: GoogleCalendarService = Depends(get_calendar_service)
):
    """이벤트 생성"""
    try:
        result = await calendar_service.create_event(
            user_id=user_id,
            event_data=event_data.dict()
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Extract event data and ID from the result
        event_data = result.get("data", {})
        event_id = event_data.get("id") if event_data else None
        
        return {
            "success": True,
            "event_id": event_id,
            "event_data": event_data,
            "message": "이벤트가 성공적으로 생성되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이벤트 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/events")
async def get_events(
    user_id: int = Query(..., description="사용자 ID"),
    start_date: str = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료 날짜 (YYYY-MM-DD)"),
    calendar_id: str = Query("primary", description="캘린더 ID"),
    calendar_service: GoogleCalendarService = Depends(get_calendar_service)
):
    """이벤트 목록 조회"""
    try:
        # 날짜 파싱
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # 파라미터 이름 수정: start_date, end_date -> start, end
        result = await calendar_service.get_events(
            user_id=user_id,
            start=start_dt,
            end=end_dt,
            calendar_id=calendar_id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이벤트 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 구체적인 경로들을 먼저 정의
@app.get("/events/search")
async def search_events(
    user_id: int = Query(..., description="사용자 ID"),
    query: str = Query(..., description="검색어"),
    calendar_id: str = Query("primary", description="캘린더 ID"),
    max_results: int = Query(25, description="최대 결과 수"),
    calendar_service: GoogleCalendarService = Depends(get_calendar_service)
):
    """이벤트 검색"""
    try:
        # Use the calendar service search_events method instead of direct API call
        result = await calendar_service.search_events(
            user_id=user_id,
            query=query,
            calendar_id=calendar_id,
            max_results=max_results
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        events = result["data"].get('items', [])
        
        return {
            "success": True,
            "events": events,
            "count": len(events),
            "query": query
        }
    except Exception as e:
        logger.error(f"이벤트 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/events/quick")
async def create_quick_event(
    user_id: int = Query(..., description="사용자 ID"),
    quick_event: QuickEventCreate = ...,
    calendar_service: GoogleCalendarService = Depends(get_calendar_service)
):
    """빠른 이벤트 생성 (자연어 입력)"""
    try:
        service = calendar_service._get_service(user_id)
        
        # Google의 Quick Add 기능 사용
        event = service.events().quickAdd(
            calendarId=quick_event.calendar_id,
            text=quick_event.text
        ).execute()
        
        return {
            "success": True,
            "event_id": event.get('id'),
            "event_link": event.get('htmlLink'),
            "event_data": event
        }
    except Exception as e:
        logger.error(f"빠른 이벤트 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/upcoming")
async def get_upcoming_events(
    user_id: int = Query(..., description="사용자 ID"),
    days: int = Query(7, description="조회할 일수"),
    calendar_id: str = Query("primary", description="캘린더 ID"),
    calendar_service: GoogleCalendarService = Depends(get_calendar_service)
):
    """다가오는 이벤트 조회"""
    try:
        from datetime import datetime, timedelta
        start_time = datetime.now()
        end_time = start_time + timedelta(days=days)
        
        result = await calendar_service.get_events(
            user_id=user_id,
            start=start_time,
            end=end_time,
            calendar_id=calendar_id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        events = result["data"].get("items", [])
        
        return {
            "success": True,
            "events": events,
            "count": len(events),
            "start_date": start_time.strftime("%Y-%m-%d"),
            "end_date": end_time.strftime("%Y-%m-%d"),
            "days": days
        }
    except Exception as e:
        logger.error(f"다가오는 이벤트 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== google task =====
# 기존 import 섹션에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "../shared_modules"))
from shared_modules.queries import get_user_tokens
from shared_modules.database import get_session_context
GOOGLE_TASKS_BASE = os.getenv("GOOGLE_TASKS_BASE", "https://tasks.googleapis.com/tasks/v1")

@app.post("/google/tasks/lists")
async def create_tasklist(
    title: str,
    user_id: int = Query(..., description="사용자 ID")
):
    """Google Tasks에 새로운 작업 목록(Tasklist) 생성"""
    try:
        with get_session_context() as db:
            token_data = get_user_tokens(db, user_id)
            if not token_data or not token_data.get('access_token'):
                return JSONResponse({"error": "Google 로그인 필요"}, status_code=401)

            url = f"{GOOGLE_TASKS_BASE}/users/@me/lists"
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            payload = {"title": title}

            async with httpx.AsyncClient() as client:
                res = await client.post(url, headers=headers, json=payload)
            return res.json()
    except Exception as e:
        logger.error(f"Google Tasks 목록 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/google/tasks")
async def list_tasks(user_id: int = Query(..., description="사용자 ID")):
    """Google Tasks 목록 조회"""
    try:
        with get_session_context() as db:
            token_data = get_user_tokens(db, user_id)
            if not token_data or not token_data.get('access_token'):
                return JSONResponse({"error": "Google 로그인 필요"}, status_code=401)

            url = f"{GOOGLE_TASKS_BASE}/users/@me/lists"
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            async with httpx.AsyncClient() as client:
                res = await client.get(url, headers=headers)
            return res.json()
    except Exception as e:
        logger.error(f"Google Tasks 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/google/tasks")
async def create_task(
    tasklist_id: str,
    title: str,
    user_id: int = Query(..., description="사용자 ID"),
    notes: str = None,
    due: str = None  # ISO 8601 형식: YYYY-MM-DDTHH:MM:SSZ
):
    """Google Tasks에 작업(Task) 등록 (시간 설정 지원)"""
    try:
        with get_session_context() as db:
            token_data = get_user_tokens(db, user_id)
            if not token_data or not token_data.get('access_token'):
                return JSONResponse({"error": "Google 로그인 필요"}, status_code=401)

            url = f"{GOOGLE_TASKS_BASE}/lists/{tasklist_id}/tasks"
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}

            payload = {"title": title}
            if notes:
                payload["notes"] = notes
            if due:
                payload["due"] = due  # e.g., "2025-07-28T09:00:00Z" (UTC 시간)

            async with httpx.AsyncClient() as client:
                res = await client.post(url, headers=headers, json=payload)
            return res.json()
    except Exception as e:
        logger.error(f"Google Tasks 작업 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/google/tasks/{tasklist_id}")
async def list_tasks_in_list(
    tasklist_id: str,
    user_id: int = Query(..., description="사용자 ID")
):
    """특정 목록에 있는 Task 조회"""
    try:
        with get_session_context() as db:
            token_data = get_user_tokens(db, user_id)
            if not token_data or not token_data.get('access_token'):
                return JSONResponse({"error": "Google 로그인 필요"}, status_code=401)

            url = f"{GOOGLE_TASKS_BASE}/lists/{tasklist_id}/tasks"
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            async with httpx.AsyncClient() as client:
                res = await client.get(url, headers=headers)
            return res.json()
    except Exception as e:
        logger.error(f"Google Tasks 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
        log_level=config.LOG_LEVEL.lower()
    )

class ContentSaveRequest(BaseModel):
    user_id: int
    title: str
    content: str
    task_type: str      # 예: sns_publish_instagram
    platform: str       # 예: instagram / blog
    scheduled_at: Optional[datetime] = None

# @app.post("/workspace/automation/ai")
# async def save_ai_generated_content(req: BaseContentRequest):
#     """
#     AI 자동 생성 콘텐츠 저장 API
#     """
#     try:
#         logger.info(f"📨 [AI] 저장 요청: {req.task_type=} {req.task_data=}")

#         with get_session_context() as db:
#             task = create_automation_task(
#                 db=db,
#                 user_id=req.user_id,
#                 title=req.title,
#                 task_type=req.task_type,
#                 task_data=req.task_data,
#                 status=req.status
#             )
#             # ✅ 세션 닫히기 전에 필요한 필드만 복사
#             task_result = {
#                 "task_id": task.task_id,
#                 "user_id": task.user_id,
#                 "task_type": task.task_type,
#                 "title": task.title,
#                 "task_data": task.task_data,
#                 "status": task.status,
#                 "created_at": task.created_at,
#             }

#         return {
#             "success": True,
#             "message": "AI 콘텐츠가 성공적으로 저장되었습니다.",
#             **task_result,
#         }

#     except Exception as e:
#         logger.error(f"❌ AI 콘텐츠 저장 실패: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail="AI 콘텐츠 저장 중 오류 발생")
    

@app.post("/workspace/automation/manual")
async def save_manual_content(req: ManualContentRequest):
    """
    수동 작성 콘텐츠 저장 API
    """
    try:
        logger.info(f"📨 [Manual] 저장 요청: {req.task_type=} {req.task_data=}")

        with get_session_context() as db:
            task = create_automation_task(
                db=db,
                user_id=req.user_id,
                title=req.title,
                task_type=req.task_type,
                task_data={
                    "platform": req.platform,
                    "full_content": req.content,
                    **req.task_data
                },
                status=req.status,
                scheduled_at=req.scheduled_at
            )

            # ✅ 세션 닫히기 전에 필요한 필드만 복사
            task_result = {
                "task_id": task.task_id,
                "user_id": task.user_id,
                "task_type": task.task_type,
                "title": task.title,
                "task_data": task.task_data,
                "status": task.status,
                "created_at": task.created_at,
            }

        return {
            "success": True,
            "message": "수동 콘텐츠가 성공적으로 저장되었습니다.",
            **task_result
        }

    except Exception as e:
        logger.error(f"❌ 수동 콘텐츠 저장 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="수동 콘텐츠 저장 중 오류 발생")

@app.get("/workspace/automation")
def get_user_automation_tasks(user_id: int = Query(...), db: Session = Depends(get_db)):
    try:
        tasks = db.query(AutomationTask).filter(
            AutomationTask.user_id == user_id,
            AutomationTask.task_type.in_([
                "sns_publish_instagram",
                "sns_publish_blog"
            ])
        ).order_by(AutomationTask.created_at.desc()).all()

        return {
            "success": True,
            "data": {
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "title": task.title,
                        "task_type": task.task_type,
                        "task_data": task.task_data,
                        "status": task.status,
                        "created_at": task.created_at,
                    }
                    for task in tasks
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/workspace/automation/{task_id}")
def delete_automation_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(AutomationTask).filter(AutomationTask.task_id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Automation task not found")

    db.delete(task)
    db.commit()
    return {"success": True, "message": f"Task {task_id} deleted"}
    
