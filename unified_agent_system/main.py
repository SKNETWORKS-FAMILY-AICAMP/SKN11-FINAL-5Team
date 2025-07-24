"""
통합 에이전트 시스템 메인 FastAPI 애플리케이션
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Body, Depends, Request
from fastapi import APIRouter
from fastapi import Form
from fastapi import UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import requests
import uvicorn
import sys
import os
import shutil
from typing import Optional
import traceback


# 공통 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 공통 모듈 import
from shared_modules import (
    get_config,
    get_session_context,
    setup_logging,
    create_conversation, 
    create_message, 
    get_conversation_by_id, 
    get_recent_messages,
    get_user_by_social,
    create_user_social,
    get_template_by_title,
    get_template,
    get_templates_by_type,
    save_or_update_phq9_result,
    get_latest_phq9_by_user,
    create_success_response,
    create_error_response,
    get_current_timestamp,
    get_templates_by_user_and_type,
    update_template_message,
    create_template_message,
    recommend_templates_core,
    get_user_template_by_title

)


from core.models import (
    UnifiedRequest, UnifiedResponse, HealthCheck, 
    AgentType, RoutingDecision
)
from core.workflow import get_workflow
from core.config import (
    SERVER_HOST, SERVER_PORT, DEBUG_MODE, 
    LOG_LEVEL, LOG_FORMAT
)
from shared_modules.database import  get_db_dependency
from shared_modules.queries import get_conversation_history
from shared_modules.utils import get_or_create_conversation_session, create_success_response as unified_create_success_response
from pydantic import BaseModel
from shared_modules.db_models import Template
from shared_modules.db_models import User
from shared_modules.db_models import TemplateMessage
from shared_modules.db_models import  Project
from shared_modules.db_models import ProjectDocument
from shared_modules.db_models import Conversation
from shared_modules.db_models import FAQ

# 로깅 설정
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# 설정 로드
config = get_config()
router = APIRouter()

class TemplateUpdateRequest(BaseModel):
    title: str
    content: str
    category: Optional[str] = None
    description: Optional[str] = None
    user_id: Optional[int] = None  # ✅ 이거 추가

# ===== 공통 요청/응답 모델 =====

class ConversationCreate(BaseModel):
    user_id: int
    title: Optional[str] = None

class SocialLoginRequest(BaseModel):
    provider: str
    social_id: str
    username: str
    email: str

class PHQ9StartRequest(BaseModel):
    user_id: int
    conversation_id: int

class PHQ9SubmitRequest(BaseModel):
    user_id: int
    conversation_id: int
    scores: List[int]

class EmergencyRequest(BaseModel):
    user_id: int
    conversation_id: int
    message: str

class AutomationRequest(BaseModel):
    user_id: int
    task_type: str
    parameters: Dict[str, Any] = {}


class TemplateCreateRequest(BaseModel):
    user_id: int
    title: str
    content: str
    template_type: str
    channel_type: str
    content_type: Optional[str] = "text"
    is_custom: bool
    description: Optional[str] = None
    conversation_id: Optional[int] = None

class ProjectCreate(BaseModel):
    user_id: int
    title: str
    description: str = ""
    category: str = "general"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 라이프사이클 함수"""
    # 시작 시
    logger.info("통합 에이전트 시스템 시작")
    workflow = get_workflow()
    
    # 에이전트 상태 확인
    status = await workflow.get_workflow_status()
    logger.info(f"활성 에이전트: {status['active_agents']}/{status['total_agents']}")
    
    yield
    
    # 종료 시
    logger.info("통합 에이전트 시스템 종료")
    await workflow.cleanup()


# FastAPI 앱 생성
app = FastAPI(
    title="통합 에이전트 시스템",
    description="5개의 전문 에이전트를 통합한 AI 상담 시스템",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.0.200:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from api.admin import router as admin_router

app.include_router(admin_router, prefix="/admin")


# ===== 공통 대화 관리 API =====

@app.post("/conversations")
async def create_conversation_endpoint(req: ConversationCreate):
    """대화 세션 생성"""
    try:
        session_info = get_or_create_conversation_session(req.user_id)
        
        response_data = {
            "conversation_id": session_info["conversation_id"],
            "user_id": req.user_id,
            "title": req.title or "새 대화",
            "created_at": get_current_timestamp(),
            "is_new": session_info["is_new"]
        }
        
        return create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"대화 세션 생성 오류: {e}")
        return create_error_response("대화 세션 생성에 실패했습니다", "CONVERSATION_CREATE_ERROR")

@app.get("/conversations/{user_id}")
async def get_user_conversations(user_id: int):
    """사용자의 대화 세션 목록 조회"""
    try:
        with get_session_context() as db:
            from shared_modules.queries import get_user_conversations
            conversations = get_user_conversations(db, user_id, visible_only=True)
            
            conversation_list = []
            for conv in conversations:
                conversation_list.append({
                    "conversation_id": conv.conversation_id,
                    "started_at": conv.started_at.isoformat() if conv.started_at else None,
                    "ended_at": conv.ended_at.isoformat() if conv.ended_at else None,
                    "title": "대화"
                })
            
            return create_success_response(conversation_list)
            
    except Exception as e:
        logger.error(f"대화 목록 조회 실패: {e}")
        return create_error_response("대화 목록 조회에 실패했습니다", "CONVERSATION_LIST_ERROR")

@app.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: int, limit: int = 50):
    """대화의 메시지 목록 조회"""
    try:
        with get_session_context() as db:
            messages = get_recent_messages(db, conversation_id, limit)
            
            message_list = []
            for msg in reversed(messages):  # 시간순 정렬
                message_list.append({
                    "message_id": msg.message_id,
                    "role": "user" if msg.sender_type.lower() == "user" else "assistant",
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat() if msg.created_at else None,
                    "agent_type": msg.agent_type
                })
            
            return create_success_response(message_list)
            
    except Exception as e:
        logger.error(f"메시지 목록 조회 실패: {e}")
        return create_error_response("메시지 목록 조회에 실패했습니다", "MESSAGE_LIST_ERROR")

# ===== 사용자 관리 API =====
import requests
from fastapi import Request
from sqlalchemy.orm import Session

# 소셜 로그인 인증 URL 생성 엔드포인트
@app.get("/auth/{provider}")
async def get_auth_url(provider: str, request: Request, intent: str = "login"):
    """소셜 로그인 인증 URL 생성"""
    try:
        # intent를 세션에 저장하여 콜백에서 사용
        import uuid
        state = str(uuid.uuid4())
        
        # 메모리에 intent 정보 저장 (실제 운영 환경에서는 Redis 등 사용 권장)
        if not hasattr(app, 'social_sessions'):
            app.social_sessions = {}
        app.social_sessions[state] = {
            'intent': intent,
            'provider': provider
        }
        
        if provider == "google":
            auth_url = (
                "https://accounts.google.com/o/oauth2/v2/auth?"
                f"client_id={os.getenv('GOOGLE_CLIENT_ID')}&"
                f"redirect_uri={os.getenv('GOOGLE_REDIRECT_URI')}&"
                "response_type=code&"
                "scope=openid email profile&"
                f"state={state}"
            )
        elif provider == "kakao":
            auth_url = (
                "https://kauth.kakao.com/oauth/authorize?"
                f"client_id={os.getenv('KAKAO_CLIENT_ID')}&"
                f"redirect_uri={os.getenv('KAKAO_REDIRECT_URI')}&"
                "response_type=code&"
                f"state={state}"
            )
        elif provider == "naver":
            auth_url = (
                "https://nid.naver.com/oauth2.0/authorize?"
                f"client_id={os.getenv('NAVER_CLIENT_ID')}&"
                f"redirect_uri={os.getenv('NAVER_REDIRECT_URI')}&"
                "response_type=code&"
                f"state={state}"
            )
        else:
            return create_error_response("지원하지 않는 소셜 로그인 제공자입니다", "INVALID_PROVIDER")
        
        return create_success_response({"auth_url": auth_url})
        
    except Exception as e:
        logger.error(f"인증 URL 생성 오류: {e}")
        return create_error_response("인증 URL 생성에 실패했습니다", "AUTH_URL_ERROR")

# 회원가입용 소셜 로그인 인증 URL 생성 엔드포인트
@app.post("/auth/{provider}")
async def get_signup_auth_url(provider: str, request: Request, body: dict = Body(...)):
    """소셜 회원가입 인증 URL 생성"""
    try:
        intent = body.get('intent', 'signup')
        user_data = body.get('user_data', {})
        
        # state 생성 및 세션 저장
        import uuid
        state = str(uuid.uuid4())
        
        if not hasattr(app, 'social_sessions'):
            app.social_sessions = {}
        app.social_sessions[state] = {
            'intent': intent,
            'provider': provider,
            'user_data': user_data
        }
        
        if provider == "google":
            auth_url = (
                "https://accounts.google.com/o/oauth2/v2/auth?"
                f"client_id={os.getenv('GOOGLE_CLIENT_ID')}&"
                f"redirect_uri={os.getenv('GOOGLE_REDIRECT_URI')}&"
                "response_type=code&"
                "scope=openid email profile&"
                f"state={state}"
            )
        elif provider == "kakao":
            auth_url = (
                "https://kauth.kakao.com/oauth/authorize?"
                f"client_id={os.getenv('KAKAO_CLIENT_ID')}&"
                f"redirect_uri={os.getenv('KAKAO_REDIRECT_URI')}&"
                "response_type=code&"
                f"state={state}"
            )
        elif provider == "naver":
            auth_url = (
                "https://nid.naver.com/oauth2.0/authorize?"
                f"client_id={os.getenv('NAVER_CLIENT_ID')}&"
                f"redirect_uri={os.getenv('NAVER_REDIRECT_URI')}&"
                "response_type=code&"
                f"state={state}"
            )
        else:
            return create_error_response("지원하지 않는 소셜 로그인 제공자입니다", "INVALID_PROVIDER")
        
        return create_success_response({"auth_url": auth_url})
        
    except Exception as e:
        logger.error(f"회원가입 인증 URL 생성 오류: {e}")
        return create_error_response("인증 URL 생성에 실패했습니다", "AUTH_URL_ERROR")

# 구글 소셜 로그인
@app.get("/login/oauth2/code/google")
async def google_login(request: Request, code: str, state: str = None):
    try:
        # state로 세션 정보 조회
        session_info = None
        if state and hasattr(app, 'social_sessions') and state in app.social_sessions:
            session_info = app.social_sessions.pop(state)  # 사용 후 삭제
        
        intent = session_info.get('intent', 'login') if session_info else 'login'
        user_data = session_info.get('user_data', {}) if session_info else {}
        
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
            "grant_type": "authorization_code",
        }
        resp = requests.post(token_url, data=data)
        if not resp.ok:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="http://localhost:3000/login?error=google_token_failed")

        token_info = resp.json()
        access_token = token_info["access_token"]
        refresh_token = token_info.get("refresh_token")

        userinfo = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()
        
        provider = "google"
        social_id = userinfo["id"]
        email = userinfo.get("email")
        nickname = userinfo.get("name", "")
        
        with get_session_context() as db:
            existing_user = get_user_by_social(db, provider, social_id)
            
            # intent에 따른 처리
            if intent == 'login':
                if existing_user:
                    # 기존 사용자 - 로그인 처리
                    existing_user.access_token = access_token
                    if refresh_token:
                        existing_user.refresh_token = refresh_token
                    db.commit()
                    
                    user_data_response = {
                        "user_id": existing_user.user_id,
                        "provider": provider,
                        "email": existing_user.email,
                        "username": nickname
                    }
                else:
                    # 계정이 없음 - 회원가입 페이지로 리디렉션
                    from fastapi.responses import RedirectResponse
                    from urllib.parse import urlencode
                    signup_params = urlencode({
                        "provider": provider,
                        "social_id": social_id,
                        "email": email or "",
                        "username": nickname,
                        "action": "signup_required"
                    })
                    return RedirectResponse(url=f"http://localhost:3000/signup?{signup_params}")
                    
            elif intent == 'signup':
                if existing_user:
                    # 이미 가입된 사용자 - 바로 로그인
                    existing_user.access_token = access_token
                    if refresh_token:
                        existing_user.refresh_token = refresh_token
                    db.commit()
                    
                    user_data_response = {
                        "user_id": existing_user.user_id,
                        "provider": provider,
                        "email": existing_user.email,
                        "username": nickname
                    }
                else:
                    # 새 사용자 생성
                    new_user = create_user_social(
                        db, provider, social_id, email, nickname,
                        access_token=access_token, refresh_token=refresh_token
                    )
                    
                    # 추가 사용자 정보가 있으면 업데이트
                    if user_data:
                        # 여기에 추가 사용자 정보 처리 로직 추가 가능
                        pass
                    
                    user_data_response = {
                        "user_id": new_user.user_id,
                        "provider": provider,
                        "email": new_user.email,
                        "username": nickname
                    }
        
        # 성공 시 채팅 페이지로 리디렉션
        from fastapi.responses import RedirectResponse
        from urllib.parse import urlencode
        query_params = urlencode(user_data_response)
        return RedirectResponse(url=f"http://localhost:3000/chat?{query_params}")
        
    except Exception as e:
        logger.error(f"구글 로그인 처리 중 오류: {e}")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="http://localhost:3000/login?error=google_process_failed")

# 카카오 소셜 로그인
@app.get("/login/oauth2/code/kakao")
def kakao_login(code: str, state: str = None):
    try:
        # state로 세션 정보 조회
        session_info = None
        if state and hasattr(app, 'social_sessions') and state in app.social_sessions:
            session_info = app.social_sessions.pop(state)
        
        intent = session_info.get('intent', 'login') if session_info else 'login'
        user_data = session_info.get('user_data', {}) if session_info else {}
        
        token_url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": os.getenv("KAKAO_CLIENT_ID"),
            "redirect_uri": os.getenv("KAKAO_REDIRECT_URI"),
            "code": code,
        }
        resp = requests.post(token_url, data=data)
        if not resp.ok:
            logger.error(f"카카오 토큰 요청 실패: {resp.text}")
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="http://localhost:3000/login?error=kakao_token_failed")
            
        token_json = resp.json()
        if "error" in token_json:
            logger.error(f"카카오 토큰 응답 오류: {token_json}")
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="http://localhost:3000/login?error=kakao_token_error")
            
        access_token = token_json["access_token"]
        refresh_token = token_json.get("refresh_token", None)

        userinfo_resp = requests.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if not userinfo_resp.ok:
            logger.error(f"카카오 사용자 정보 요청 실패: {userinfo_resp.text}")
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="http://localhost:3000/login?error=kakao_userinfo_failed")
            
        userinfo = userinfo_resp.json()
        if "id" not in userinfo:
            logger.error(f"카카오 사용자 정보 응답 오류: {userinfo}")
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="http://localhost:3000/login?error=kakao_userinfo_error")
            
        provider = "kakao"
        social_id = str(userinfo["id"])
        kakao_account = userinfo.get("kakao_account", {})
        email = kakao_account.get("email", None)
        nickname = kakao_account.get("profile", {}).get("nickname", "")
        
        with get_session_context() as db:
            existing_user = get_user_by_social(db, provider, social_id)
            
            # intent에 따른 처리
            if intent == 'login':
                if existing_user:
                    # 기존 사용자 - 로그인 처리
                    existing_user.access_token = access_token
                    if refresh_token:
                        existing_user.refresh_token = refresh_token
                    db.commit()
                    
                    user_data_response = {
                        "user_id": existing_user.user_id,
                        "provider": provider,
                        "email": existing_user.email or "",
                        "username": nickname
                    }
                else:
                    # 계정이 없음 - 회원가입 페이지로 리디렉션
                    from fastapi.responses import RedirectResponse
                    from urllib.parse import urlencode
                    signup_params = urlencode({
                        "provider": provider,
                        "social_id": social_id,
                        "email": email or "",
                        "username": nickname,
                        "action": "signup_required"
                    })
                    return RedirectResponse(url=f"http://localhost:3000/signup?{signup_params}")
                    
            elif intent == 'signup':
                if existing_user:
                    # 이미 가입된 사용자 - 바로 로그인
                    existing_user.access_token = access_token
                    if refresh_token:
                        existing_user.refresh_token = refresh_token
                    db.commit()
                    
                    user_data_response = {
                        "user_id": existing_user.user_id,
                        "provider": provider,
                        "email": existing_user.email or "",
                        "username": nickname
                    }
                else:
                    # 새 사용자 생성
                    new_user = create_user_social(
                        db, provider, social_id, email, nickname,
                        access_token=access_token,
                        refresh_token=refresh_token
                    )
                    
                    # 추가 사용자 정보가 있으면 업데이트
                    if user_data:
                        # 여기에 추가 사용자 정보 처리 로직 추가 가능
                        pass
                    
                    user_data_response = {
                        "user_id": new_user.user_id,
                        "provider": provider,
                        "email": new_user.email or "",
                        "username": nickname
                    }
        
        # 성공 시 채팅 페이지로 리디렉션
        from fastapi.responses import RedirectResponse
        from urllib.parse import urlencode
        query_params = urlencode(user_data_response)
        return RedirectResponse(url=f"http://localhost:3000/chat?{query_params}")
        
    except Exception as e:
        logger.error(f"카카오 로그인 처리 중 오류: {e}")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="http://localhost:3000/login?error=kakao_process_failed")

# 네이버 소셜 로그인
@app.get("/login/oauth2/code/naver")
def naver_login(code: str, state: str):
    try:
        # state로 세션 정보 조회
        session_info = None
        if state and hasattr(app, 'social_sessions') and state in app.social_sessions:
            session_info = app.social_sessions.pop(state)
        
        intent = session_info.get('intent', 'login') if session_info else 'login'
        user_data = session_info.get('user_data', {}) if session_info else {}
        
        token_url = "https://nid.naver.com/oauth2.0/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": os.getenv("NAVER_CLIENT_ID"),
            "client_secret": os.getenv("NAVER_CLIENT_SECRET"),
            "code": code,
            "state": state,
            "redirect_uri": os.getenv("NAVER_REDIRECT_URI")
        }
        resp = requests.post(token_url, data=data)
        if not resp.ok:
            logger.error(f"네이버 토큰 요청 실패: {resp.text}")
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="http://localhost:3000/login?error=naver_token_failed")
            
        token_json = resp.json()
        if "error" in token_json:
            logger.error(f"네이버 토큰 응답 오류: {token_json}")
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="http://localhost:3000/login?error=naver_token_error")
            
        access_token = token_json["access_token"]
        refresh_token = token_json.get("refresh_token", None)

        userinfo_resp = requests.get(
            "https://openapi.naver.com/v1/nid/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if not userinfo_resp.ok:
            logger.error(f"네이버 사용자 정보 요청 실패: {userinfo_resp.text}")
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="http://localhost:3000/login?error=naver_userinfo_failed")
            
        userinfo_json = userinfo_resp.json()
        if "resultcode" not in userinfo_json or userinfo_json["resultcode"] != "00":
            logger.error(f"네이버 사용자 정보 응답 오류: {userinfo_json}")
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="http://localhost:3000/login?error=naver_userinfo_error")
            
        userinfo = userinfo_json["response"]
        provider = "naver"
        social_id = userinfo["id"]
        email = userinfo.get("email", None)
        nickname = userinfo.get("nickname", "")
        
        with get_session_context() as db:
            existing_user = get_user_by_social(db, provider, social_id)
            
            # intent에 따른 처리
            if intent == 'login':
                if existing_user:
                    # 기존 사용자 - 로그인 처리
                    existing_user.access_token = access_token
                    if refresh_token:
                        existing_user.refresh_token = refresh_token
                    db.commit()
                    
                    user_data_response = {
                        "user_id": existing_user.user_id,
                        "provider": provider,
                        "email": existing_user.email or "",
                        "username": nickname
                    }
                else:
                    # 계정이 없음 - 회원가입 페이지로 리디렉션
                    from fastapi.responses import RedirectResponse
                    from urllib.parse import urlencode
                    signup_params = urlencode({
                        "provider": provider,
                        "social_id": social_id,
                        "email": email or "",
                        "username": nickname,
                        "action": "signup_required"
                    })
                    return RedirectResponse(url=f"http://localhost:3000/signup?{signup_params}")
                    
            elif intent == 'signup':
                if existing_user:
                    # 이미 가입된 사용자 - 바로 로그인
                    existing_user.access_token = access_token
                    if refresh_token:
                        existing_user.refresh_token = refresh_token
                    db.commit()
                    
                    user_data_response = {
                        "user_id": existing_user.user_id,
                        "provider": provider,
                        "email": existing_user.email or "",
                        "username": nickname
                    }
                else:
                    # 새 사용자 생성
                    new_user = create_user_social(
                        db, provider, social_id, email, nickname,
                        access_token=access_token,
                        refresh_token=refresh_token
                    )
                    
                    # 추가 사용자 정보가 있으면 업데이트
                    if user_data:
                        # 여기에 추가 사용자 정보 처리 로직 추가 가능
                        pass
                    
                    user_data_response = {
                        "user_id": new_user.user_id,
                        "provider": provider,
                        "email": new_user.email or "",
                        "username": nickname
                    }
        
        # 성공 시 채팅 페이지로 리디렉션
        from fastapi.responses import RedirectResponse
        from urllib.parse import urlencode
        query_params = urlencode(user_data_response)
        return RedirectResponse(url=f"http://localhost:3000/chat?{query_params}")
        
    except Exception as e:
        logger.error(f"네이버 로그인 처리 중 오류: {e}")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="http://localhost:3000/login?error=naver_process_failed")


@app.post("/social_login")
async def social_login(req: SocialLoginRequest):
    """소셜 로그인"""
    try:
        with get_session_context() as db:
            # 기존 사용자 확인
            user = get_user_by_social(db, req.provider, req.social_id)
            
            if user:
                logger.info(f"기존 사용자 로그인: user_id={user.user_id}, provider={req.provider}")
                response_data = {
                    "user_id": user.user_id,
                    "username": req.username,
                    "email": req.email,
                    "is_new_user": False
                }
            else:
                # 새 사용자 생성
                user = create_user_social(
                    db,
                    provider=req.provider,
                    social_id=req.social_id,
                    email=req.email,
                    nickname=req.username
                )
                
                logger.info(f"새 소셜 사용자 생성: user_id={user.user_id}, provider={req.provider}")
                
                response_data = {
                    "user_id": user.user_id,
                    "username": req.username,
                    "email": req.email,
                    "is_new_user": True
                }
            
            return create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"소셜 로그인 오류: {e}")
        return create_error_response("소셜 로그인에 실패했습니다", "SOCIAL_LOGIN_ERROR")

# ===== 템플릿 관리 API =====

@app.get("/lean_canvas/{title}")
async def preview_lean_canvas(title: str):
    """린캔버스 템플릿 미리보기"""
    try:
        from shared_modules.utils import sanitize_filename
        safe_title = sanitize_filename(title)
        
        template = get_template_by_title(safe_title)
        html = template["content"] if template else "<p>템플릿 없음</p>"
        
        return Response(content=html, media_type="text/html")
        
    except Exception as e:
        logger.error(f"린캔버스 템플릿 조회 실패: {e}")
        return Response(content="<p>템플릿을 로드할 수 없습니다</p>", media_type="text/html")

@app.get("/preview/{template_id}")
async def preview_template(template_id: int):
    """템플릿 미리보기"""
    try:
        template = get_template(template_id)
        if not template:
            return Response(content="<p>템플릿을 찾을 수 없습니다</p>", status_code=404, media_type="text/html")
        
        if template.get("content_type") != "html":
            return Response(content="<p>HTML 템플릿이 아닙니다</p>", status_code=400, media_type="text/html")
        
        return Response(content=template["content"], media_type="text/html")
        
    except Exception as e:
        logger.error(f"템플릿 미리보기 실패: {e}")
        return Response(content="<p>템플릿을 로드할 수 없습니다</p>", status_code=500, media_type="text/html")

@app.get("/templates")
def get_templates(user_id: int, db: Session = Depends(get_db_dependency)):
    try:
        templates = get_templates_by_user_and_type(db=db, user_id=user_id)
        return {
            "success": True,
            "data": {
                "templates": [t.to_dict() for t in templates],
                "count": len(templates)
            }
        }
    except Exception as e:
        logger.error(f"[TEMPLATE_LIST_ERROR] {str(e)}")
        traceback.print_exc()
        return {
            "success": False,
            "error": "템플릿 목록 조회에 실패했습니다.",
            "error_code": "TEMPLATE_LIST_ERROR"
        }

@app.get("/user/templates")
async def get_user_templates(user_id: int):
    """사용자 개인 템플릿 목록"""
    try:
        with get_session_context() as db:
            templates = get_templates_by_user_and_type(db, user_id)
            return create_success_response({
                "templates": [t.to_dict() for t in templates],
                "count": len(templates)
            })
    except Exception as e:
        logger.error(f"사용자 템플릿 목록 조회 실패: {e}")
        return create_error_response("템플릿 목록 조회에 실패했습니다", "USER_TEMPLATE_LIST_ERROR")
    
@app.put("/templates/{template_id}")
async def update_user_template(template_id: int, data: dict = Body(...)):
    """사용자 템플릿 수정"""
    try:
        with get_session_context() as db:
            success = update_template_message(db, template_id, **data)
            if not success:
                return create_error_response("템플릿이 존재하지 않거나 수정에 실패했습니다", "TEMPLATE_UPDATE_FAILED")
            return create_success_response({"template_id": template_id})
    except Exception as e:
        logger.error(f"템플릿 수정 실패: {e}")
        return create_error_response("템플릿 수정 중 오류가 발생했습니다", "TEMPLATE_UPDATE_ERROR")
    
@app.post("/templates")
async def create_template(req: TemplateCreateRequest):
    try:
        with get_session_context() as db:
            template = create_template_message(
                db=db,
                user_id=req.user_id,
                template_type=req.template_type,
                channel_type=req.channel_type,
                title=req.title,
                content=req.content,
                content_type=req.content_type
            )
            if template:
                return create_success_response({"template_id": template.template_id})
            else:
                return create_error_response("템플릿 저장 실패", "TEMPLATE_CREATE_ERROR")
    except Exception as e:
        logger.error(f"템플릿 저장 오류: {e}")
        return create_error_response("템플릿 저장 중 오류 발생", "TEMPLATE_CREATE_EXCEPTION")
    

@app.put("/templates/{template_id}")
def update_template(template_id: int, request: TemplateUpdateRequest, db: Session = Depends(get_db_dependency)):
    template = db.query(Template).filter(Template.template_id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # ✅ 공용 템플릿은 복제해서 저장 (user_id 3은 공용)
    if template.user_id == 3:
        new_template = Template(
            user_id=request.user_id,  # request에서 전달받아야 함
            title=request.title,
            category=request.category,
            description=request.description,
            content=request.content,
            template_type=template.template_type,
            channel_type=template.channel_type,
            is_custom=True
        )
        db.add(new_template)
        db.commit()
        db.refresh(new_template)

        return {
            "success": True,
            "data": {
                "template_id": new_template.template_id,
                "title": new_template.title,
                "category": new_template.category,
                "description": new_template.description,
                "content": new_template.content
            }
        }

    # ✅ 일반 유저 템플릿은 수정
    template.title = request.title
    template.category = request.category
    template.description = request.description
    template.content = request.content
    db.commit()
    db.refresh(template)

    return {
        "success": True,
        "data": {
            "template_id": template.template_id,
            "title": template.title,
            "category": template.category,
            "description": template.description,
            "content": template.content
        }
    }

@app.delete("/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db_dependency)):
    template = db.query(TemplateMessage).filter(TemplateMessage.template_id == template_id).first()
    if not template:
        return {"success": False, "error": "템플릿을 찾을 수 없습니다."}
    
    db.delete(template)
    db.commit()
    return {"success": True}


# ===== 마이페이지 =====
@app.put("/user/{user_id}")
def update_user(user_id: int, data: dict = Body(...)):
    try:
        with get_session_context() as db:
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            user.nickname = data.get("nickname", user.nickname)
            user.business_type = data.get("business_type", user.business_type)
            user.experience = data.get("experience", user.experience)
            db.commit()
            return create_success_response({"user_id": user_id})
    except Exception as e:
        logger.error(f"사용자 정보 수정 오류: {e}")
        return create_error_response("사용자 정보 수정 실패", "USER_UPDATE_ERROR")


# ===== 정신건강 전용 API =====

@app.post("/phq9/start")
async def start_phq9_assessment(req: PHQ9StartRequest):
    """PHQ-9 평가 시작"""
    try:
        logger.info(f"PHQ-9 평가 시작: user_id={req.user_id}, conversation_id={req.conversation_id}")
        
        response_data = {
            "message": "PHQ-9 우울증 선별검사를 시작합니다. 다음 질문들에 솔직하게 답변해주세요.",
            "assessment_type": "phq9",
            "status": "started",
            "questions": [
                "지난 2주 동안, 일 또는 여가활동을 하는데 흥미나 즐거움을 느끼지 못함",
                "지난 2주 동안, 기분이 가라앉거나, 우울하거나, 희망이 없다고 느낌",
                "지난 2주 동안, 잠이 들거나 계속 잠을 자는 것이 어려움, 또는 잠을 너무 많이 잠",
                "지난 2주 동안, 피곤하다고 느끼거나 기운이 거의 없음",
                "지난 2주 동안, 입맛이 없거나 과식을 함",
                "지난 2주 동안, 자신을 부정적으로 봄 — 혹은 자신이 실패자라고 느끼거나 자신 또는 가족을 실망시켰다고 느낌",
                "지난 2주 동안, 신문을 읽거나 텔레비전 보는 것과 같은 일에 집중하는 것이 어려움",
                "지난 2주 동안, 다른 사람들이 주목할 정도로 너무 느리게 움직이거나 말을 함. 또는 그 반대로 평상시보다 많이 움직여서 가만히 앉아 있을 수 없었음",
                "지난 2주 동안, 자신이 죽는 것이 더 낫다고 생각하거나 어떤 식으로든 자신을 해칠 것이라고 생각함"
            ]
        }
        
        return create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"PHQ-9 시작 오류: {e}")
        return create_error_response("PHQ-9 평가 시작에 실패했습니다", "PHQ9_START_ERROR")

@app.post("/phq9/submit")
async def submit_phq9_assessment(req: PHQ9SubmitRequest):
    """PHQ-9 평가 결과 제출"""
    try:
        if len(req.scores) != 9:
            return create_error_response("9개의 응답이 필요합니다", "INVALID_SCORES")
        
        total_score = sum(req.scores)
        
        # 우울증 수준 판정
        if total_score <= 4:
            level = 1  # 최소
            level_text = "최소 우울"
        elif total_score <= 9:
            level = 2  # 경미
            level_text = "경미한 우울"
        elif total_score <= 14:
            level = 3  # 중등도
            level_text = "중등도 우울"
        elif total_score <= 19:
            level = 4  # 중증
            level_text = "중증 우울"
        else:
            level = 5  # 최중증
            level_text = "최중증 우울"
        
        # DB에 결과 저장
        with get_session_context() as db:
            result = save_or_update_phq9_result(db, req.user_id, total_score, level)
            
            # 상담 메시지 저장
            phq9_message = f"PHQ-9 평가 완료: 총점 {total_score}점 ({level_text})"
            create_message(db, req.conversation_id, "system", "mental_health", phq9_message)
        
        # 권장사항 생성
        if total_score >= 15:
            recommendation = "전문의 상담을 강력히 권합니다. 정신건강의학과 방문을 고려해보세요."
        elif total_score >= 10:
            recommendation = "전문가 상담을 권합니다. 상담센터나 정신건강의학과 방문을 고려해보세요."
        elif total_score >= 5:
            recommendation = "경미한 우울 증상이 있습니다. 생활 습관 개선과 함께 지속적인 관찰이 필요합니다."
        else:
            recommendation = "현재 우울 증상은 최소 수준입니다. 현재 상태를 잘 유지하세요."
        
        logger.info(f"PHQ-9 평가 완료: user_id={req.user_id}, score={total_score}, level={level}")
        
        response_data = {
            "total_score": total_score,
            "level": level,
            "level_text": level_text,
            "recommendation": recommendation,
            "assessment_date": get_current_timestamp()
        }
        
        return create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"PHQ-9 제출 오류: {e}")
        return create_error_response("PHQ-9 평가 제출에 실패했습니다", "PHQ9_SUBMIT_ERROR")

@app.post("/emergency")
async def handle_emergency(req: EmergencyRequest):
    """긴급상황 처리"""
    try:
        logger.warning(f"긴급상황 감지: user_id={req.user_id}, message={req.message[:100]}")
        
        emergency_response = {
            "type": "emergency",
            "message": """😢 지금 많이 힘드신 것 같습니다. 당신의 고통이 느껴집니다.

하지만 당신은 혼자가 아닙니다. 즉시 전문가의 도움을 받으실 것을 강력히 권합니다.

🆘 **긴급 연락처**
• 생명의전화: 1588-9191 (24시간)
• 청소년전화: 1388 (24시간)  
• 정신건강위기상담전화: 1577-0199 (24시간)
• 응급실: 119

💝 **기억해주세요**
- 당신의 생명은 매우 소중합니다
- 지금의 고통은 영원하지 않습니다  
- 전문가가 반드시 도움을 줄 수 있습니다
- 많은 사람들이 당신을 아끼고 있습니다

지금 당장 위의 번호로 전화해주세요. 24시간 누군가 당신을 기다리고 있습니다.""",
            "emergency_contacts": [
                {"name": "생명의전화", "number": "1588-9191"},
                {"name": "청소년전화", "number": "1388"},
                {"name": "정신건강위기상담전화", "number": "1577-0199"},
                {"name": "응급실", "number": "119"}
            ]
        }
        
        # 긴급 메시지 저장
        with get_session_context() as db:
            create_message(
                db,
                req.conversation_id,
                "system",
                "mental_health",
                f"긴급상황 감지: {req.message}"
            )
            
            create_message(
                db,
                req.conversation_id,
                "agent",
                "mental_health",
                emergency_response["message"]
            )
        
        return create_success_response(emergency_response)
        
    except Exception as e:
        logger.error(f"긴급상황 처리 오류: {e}")
        return create_error_response("긴급상황 처리에 실패했습니다", "EMERGENCY_HANDLING_ERROR")

# # ===== 업무지원 전용 API (예시) =====
# # 주의: 실제 업무지원 에이전트가 없어 목 구현체를 제공합니다

# @app.post("/automation")
# async def create_automation_task(req: AutomationRequest):
#     """자동화 작업 생성 (목 구현)"""
#     try:
#         logger.info(f"자동화 작업 생성 요청: user_id={req.user_id}, task_type={req.task_type}")
        
#         # 목 응답 (실제 업무지원 에이전트가 있어야 구현됨)
#         response_data = {
#             "task_id": 12345,  # 목 ID
#             "task_type": req.task_type,
#             "status": "created",
#             "message": "자동화 작업이 생성되었습니다 (목 구현)",
#             "parameters": req.parameters,
#             "created_at": get_current_timestamp()
#         }
        
#         return create_success_response(response_data)
        
#     except Exception as e:
#         logger.error(f"자동화 작업 생성 오류: {e}")
#         return create_error_response("자동화 작업 생성에 실패했습니다", "AUTOMATION_CREATE_ERROR")

# @app.get("/automation/{task_id}/status")
# async def get_automation_status(task_id: int):
#     """자동화 작업 상태 조회 (목 구현)"""
#     try:
#         logger.info(f"자동화 상태 조회: task_id={task_id}")
        
#         # 목 응답
#         status_data = {
#             "task_id": task_id,
#             "status": "running",
#             "progress": 75,
#             "message": "작업이 진행 중입니다 (목 구현)",
#             "created_at": get_current_timestamp(),
#             "updated_at": get_current_timestamp()
#         }
        
#         return create_success_response(status_data)
        
#     except Exception as e:
#         logger.error(f"자동화 상태 조회 오류: {e}")
#         return create_error_response("자동화 상태 조회에 실패했습니다", "AUTOMATION_STATUS_ERROR")

# @app.delete("/automation/{task_id}")
# async def cancel_automation_task(task_id: int):
#     """자동화 작업 취소 (목 구현)"""
#     try:
#         logger.info(f"자동화 작업 취소: task_id={task_id}")
        
#         # 목 응답
#         response_data = {
#             "task_id": task_id,
#             "status": "cancelled",
#             "message": "자동화 작업이 취소되었습니다 (목 구현)",
#             "cancelled_at": get_current_timestamp()
#         }
        
#         return create_success_response(response_data)
        
#     except Exception as e:
#         logger.error(f"자동화 작업 취소 오류: {e}")
#         return create_error_response("자동화 작업 취소에 실패했습니다", "AUTOMATION_CANCEL_ERROR")

# @app.get("/automation")
# async def list_automation_tasks(user_id: Optional[int] = None, status: Optional[str] = None):
#     """자동화 작업 목록 조회 (목 구현)"""
#     try:
#         logger.info(f"자동화 작업 목록 조회: user_id={user_id}, status={status}")
        
#         # 목 데이터
#         tasks = [
#             {
#                 "task_id": 12345,
#                 "task_type": "email_send",
#                 "status": "completed",
#                 "user_id": user_id or 1,
#                 "created_at": get_current_timestamp()
#             },
#             {
#                 "task_id": 12346,
#                 "task_type": "schedule_meeting",
#                 "status": "running",
#                 "user_id": user_id or 1,
#                 "created_at": get_current_timestamp()
#             }
#         ]
        
#         # 상태 필터링
#         if status:
#             tasks = [t for t in tasks if t["status"] == status]
        
#         response_data = {
#             "tasks": tasks,
#             "total": len(tasks),
#             "filter": {
#                 "user_id": user_id,
#                 "status": status
#             }
#         }
        
#         return create_success_response(response_data)
        
#     except Exception as e:
#         logger.error(f"자동화 작업 목록 조회 오류: {e}")
#         return create_error_response("자동화 작업 목록 조회에 실패했습니다", "AUTOMATION_LIST_ERROR")


@app.get("/test-ui")
async def test_ui():
    """테스트 웹 인터페이스 제공"""
    return FileResponse("web_interface.html")

@app.get("/", response_class=HTMLResponse)
async def root():
    """루트 페이지"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>통합 에이전트 시스템</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .agent { 
                border: 1px solid #ddd; 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 8px;
                background: #f9f9f9;
            }
            .status { color: green; font-weight: bold; }
            .endpoint { font-family: monospace; background: #f0f0f0; padding: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 통합 에이전트 시스템</h1>
            <p>5개의 전문 에이전트를 통합한 AI 상담 시스템입니다.</p>
            
            <h2>📋 지원하는 에이전트</h2>
            <div class="agent">
                <h3>💼 비즈니스 플래닝 에이전트</h3>
                <p>창업 준비, 사업 계획, 시장 조사, 투자 유치 등</p>
            </div>
            
            <div class="agent">
                <h3>🤝 고객 서비스 에이전트</h3>
                <p>고객 관리, 서비스 개선, 고객 만족도 향상 등</p>
            </div>
            
            <div class="agent">
                <h3>📢 마케팅 에이전트</h3>
                <p>마케팅 전략, SNS 마케팅, 브랜딩, 광고 등</p>
            </div>
            
            <div class="agent">
                <h3>🧠 멘탈 헬스 에이전트</h3>
                <p>스트레스 관리, 심리 상담, 멘탈 케어 등</p>
            </div>
            
            <div class="agent">
                <h3>⚡ 업무 자동화 에이전트</h3>
                <p>일정 관리, 이메일 자동화, 생산성 도구 등</p>
            </div>
            
            <h2>🔗 주요 API 엔드포인트</h2>
            <p><span class="endpoint">POST /query</span> - 통합 질의 처리</p>
            <p><span class="endpoint">GET /health</span> - 시스템 상태 확인</p>
            <p><span class="endpoint">GET /docs</span> - API 문서</p>
            <p><span class="endpoint">GET /test-ui</span> - 웹 테스트 인터페이스</p>
            
            <h2>📊 시스템 상태</h2>
            <p class="status">✅ 서비스 정상 운영 중</p>
        </div>
    </body>
    </html>
    """


def map_frontend_agent_to_backend(frontend_agent: str) -> Optional[AgentType]:
    """프론트엔드 에이전트 타입을 백엔드 AgentType으로 매핑"""
    agent_mapping = {
        "unified_agent": None,  # 통합 에이전트는 라우팅에 맡김
        "planner": AgentType.BUSINESS_PLANNING,
        "marketing": AgentType.MARKETING,
        "crm": AgentType.CUSTOMER_SERVICE,
        "task": AgentType.TASK_AUTOMATION,
        "mentalcare": AgentType.MENTAL_HEALTH
    }
    return agent_mapping.get(frontend_agent)


@app.post("/query")
async def process_query(request: UnifiedRequest):
    """통합 질의 처리"""
    try:
        logger.info(f"사용자 {request.user_id}: {request.message[:50]}...")
        
        # 프론트엔드 에이전트 타입을 백엔드 타입으로 매핑
        if request.preferred_agent and isinstance(request.preferred_agent, str):
            mapped_agent = map_frontend_agent_to_backend(request.preferred_agent)
            request.preferred_agent = mapped_agent
        
        # 대화 세션이 없으면 생성
        if not request.conversation_id:
            with get_session_context() as db:
                conversation = create_conversation(db, request.user_id)
                request.conversation_id = conversation.conversation_id
        
        # 사용자 메시지 저장
        with get_session_context() as db:
            create_message(
                db, 
                request.conversation_id, 
                "user", 
                "unified", 
                request.message
            )
        
        workflow = get_workflow()
        response = await workflow.process_request(request)
        
        # 에이전트 응답 저장
        with get_session_context() as db:
            create_message(
                db,
                response.conversation_id,
                "agent",
                response.agent_type.value,
                response.response
            )
        
        logger.info(f"응답 완료: {response.agent_type} (신뢰도: {response.confidence:.2f})")
        
        # UnifiedResponse를 직접 반환 (FastAPI가 자동으로 JSON 직렬화)
        return response
        
    except Exception as e:
        logger.error(f"질의 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"처리 중 오류가 발생했습니다: {str(e)}")



# ===== 대화 관리 API =====

@app.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: int, limit: int = 50):
    """대화의 메시지 목록 조회"""
    try:
        history = await get_conversation_history(conversation_id, limit)
        return create_success_response(data=history)
        
    except Exception as e:
        logger.error(f"메시지 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# === 프로젝트 ====
UPLOAD_DIR = "uploads/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/projects")
def create_project(project: ProjectCreate, db: Session = Depends(get_db_dependency)):
    new_project = Project(
        user_id=project.user_id,
        title=project.title,
        description=project.description,
        category=project.category,
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return {
        "success": True,
        "data": {
            "project": {
                "id": new_project.id,
                "title": new_project.title,
                "description": new_project.description,
                "category": new_project.category,
                "createdAt": str(new_project.created_at),
                "updatedAt": str(new_project.updated_at),
                "documentCount": 0,
                "chatCount": 0,
            }
        },
    }

@app.get("/projects")
def get_projects(user_id: int, db: Session = Depends(get_db_dependency)):
    projects = db.query(Project).filter(Project.user_id == user_id).all()
    return {
        "success": True,
        "data": [
            {
                "id": p.id,
                "user_id": p.user_id,
                "title": p.title,
                "description": p.description,
                "category": p.category,
                "createdAt": str(p.created_at),
                "updatedAt": str(p.updated_at),
            }
            for p in projects
        ]
    }

@app.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db_dependency)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()
    return {"success": True, "message": "Project deleted"}

@app.put("/projects/{project_id}")
def update_project(project_id: int, data: dict = Body(...), db: Session = Depends(get_db_dependency)):
    """프로젝트 정보 수정"""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 프로젝트 정보 업데이트
        if "title" in data:
            project.title = data["title"]
        if "description" in data:
            project.description = data["description"]
        if "category" in data:
            project.category = data["category"]
        
        # updated_at은 자동으로 업데이트됨 (DB 설정에 따라)
        db.commit()
        db.refresh(project)

        return {
            "success": True,
            "data": {
                "id": project.id,
                "title": project.title,
                "description": project.description,
                "category": project.category,
                "createdAt": str(project.created_at),
                "updatedAt": str(project.updated_at),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"프로젝트 수정 실패: {e}")
        return create_error_response("프로젝트 수정에 실패했습니다", "PROJECT_UPDATE_ERROR")

@app.post("/projects/{project_id}/documents")
async def upload_project_document(
    project_id: int,
    conversation_id: Optional[int] = Form(None),
    user_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db_dependency),
):
    try:
        conv_id = int(conversation_id) if conversation_id and conversation_id.isdigit() else None
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        document = ProjectDocument(
            project_id=project_id,
            conversation_id=conversation_id,
            user_id=user_id,
            file_name=file.filename,
            file_path=file_path,
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        return {
            "success": True,
            "data": {
                "document_id": document.document_id,
                "file_name": document.file_name,
                "file_path": document.file_path,
                "uploaded_at": str(document.uploaded_at),
            },
        }
    except Exception as e:
        logger.error(f"파일 업로드 실패: {e}")
        return create_error_response("파일 업로드 실패", "DOCUMENT_UPLOAD_ERROR")

    
@app.get("/projects/{project_id}/documents")
def get_documents_by_project(project_id: int, db: Session = Depends(get_db_dependency)):
    try:
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.file_path != "/virtual/chat_link"  # 채팅 링크 제외
        ).all()
        return {
            "success": True,
            "data": [
                {
                    "document_id": d.document_id,
                    "project_id":project_id, 
                    "file_name": d.file_name,
                    "file_path": d.file_path,
                    "uploaded_at": str(d.uploaded_at),
                }
                for d in documents
            ]
        }
    except Exception as e:
        logger.error(f"문서 조회 실패: {e}")
        return create_error_response("문서 조회 실패", "DOCUMENT_LIST_ERROR")

@app.delete("/projects/{project_id}/documents/{document_id}")
def delete_document(
    project_id: int,
    document_id: int,
    db: Session = Depends(get_db_dependency),
):
    try:
        document = db.query(ProjectDocument).filter_by(project_id=project_id, document_id=document_id).first()

        if not document:
            return {"success": False, "error": "문서를 찾을 수 없습니다."}

        db.delete(document)
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        print("문서 삭제 실패:", e)
        return {"success": False, "error": "문서 삭제 중 오류 발생"}

@app.get("/projects/{project_id}/chats")
async def get_project_chats(project_id: int, db: Session = Depends(get_db_dependency)):
    """특정 프로젝트의 채팅 목록 조회 (project_document 테이블 기반)"""
    try:
        # project_document 테이블에서 해당 프로젝트의 conversation_id들 조회
        project_docs = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.conversation_id.isnot(None)
        ).all()
        
        # conversation_id별로 그룹화
        conversation_ids = list(set([doc.conversation_id for doc in project_docs if doc.conversation_id]))
        
        chat_list = []
        for conv_id in conversation_ids:
            try:
                # 대화 정보 조회
                conversation = db.query(Conversation).filter(
                    Conversation.conversation_id == conv_id
                ).first()
                
                if not conversation:
                    continue
                
                # 마지막 메시지 조회
                from shared_modules.db_models import Message
                last_message = db.query(Message).filter(
                    Message.conversation_id == conv_id
                ).order_by(Message.created_at.desc()).first()
                
                # 메시지 수 조회
                message_count = db.query(Message).filter(
                    Message.conversation_id == conv_id
                ).count()
                
                chat_list.append({
                    "conversation_id": conv_id,
                    "title": f"채팅 {conv_id}",
                    "lastMessage": last_message.content if last_message else "메시지 없음",
                    "lastMessageTime": last_message.created_at.isoformat() if last_message else conversation.started_at.isoformat(),
                    "messageCount": message_count,
                    "createdAt": conversation.started_at.isoformat() if conversation.started_at else None
                })
                
            except Exception as e:
                logger.error(f"채팅 {conv_id} 정보 조회 실패: {e}")
                continue
        
        # 최신순 정렬
        chat_list.sort(key=lambda x: x["lastMessageTime"], reverse=True)
        
        return create_success_response(chat_list)
        
    except Exception as e:
        logger.error(f"프로젝트 채팅 목록 조회 실패: {e}")
        return create_error_response("채팅 목록 조회에 실패했습니다", "PROJECT_CHAT_LIST_ERROR")

# 2. 프로젝트에 새 채팅 생성 (기존 conversation 생성 + project_document 연결)
@app.post("/projects/{project_id}/chats")
async def create_project_chat(
    project_id: int, 
    data: dict = Body(...), 
    db: Session = Depends(get_db_dependency)
):
    """프로젝트에 새 채팅 생성"""
    try:
        user_id = data.get("user_id")
        title = data.get("title", "새 채팅")
        
        if not user_id:
            return create_error_response("사용자 ID가 필요합니다", "MISSING_USER_ID")
        
        # 새 대화 생성
        conversation = create_conversation(db, user_id)
        
        # project_document 테이블에 연결 정보 생성 (더미 문서로)
        # 실제 파일 없이도 프로젝트와 대화를 연결하기 위함
        dummy_doc = ProjectDocument(
            project_id=project_id,
            conversation_id=conversation.conversation_id,
            user_id=user_id,
            file_name=f"chat_link_{conversation.conversation_id}",
            file_path="/virtual/chat_link"  # 가상 경로
        )
        db.add(dummy_doc)
        db.commit()
        
        response_data = {
            "conversation_id": conversation.conversation_id,
            "project_id": project_id,
            "title": title,
            "created_at": conversation.started_at.isoformat() if conversation.started_at else None
        }
        
        return create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"프로젝트 채팅 생성 실패: {e}")
        return create_error_response("채팅 생성에 실패했습니다", "PROJECT_CHAT_CREATE_ERROR")


# ===== 시스템 관리 API ===== 

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """시스템 상태 확인"""
    try:
        workflow = get_workflow()
        status = await workflow.get_workflow_status()
        
        return HealthCheck(
            status="healthy",
            agents=status["agent_health"],
            system_info={
                "active_agents": status["active_agents"],
                "total_agents": status["total_agents"],
                "workflow_version": status["workflow_version"],
                "multi_agent_enabled": status["config"]["enable_multi_agent"]
            }
        )
        
    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        raise HTTPException(status_code=503, detail=f"시스템 상태 확인 실패: {str(e)}")


@app.get("/agents", response_model=Dict[str, Any])
async def get_agents_info():
    """에이전트 정보 조회"""
    try:
        workflow = get_workflow()
        status = await workflow.get_workflow_status()
        
        return {
            "total_agents": status["total_agents"],
            "active_agents": status["active_agents"],
            "agent_status": status["agent_health"],
            "agent_types": [agent.value for agent in AgentType if agent != AgentType.UNKNOWN]
        }
        
    except Exception as e:
        logger.error(f"에이전트 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/route", response_model=RoutingDecision)
async def route_query(message: str, user_id: int = 1):
    """질의 라우팅 테스트 (디버깅용)"""
    try:
        request = UnifiedRequest(user_id=user_id, message=message)
        workflow = get_workflow()
        routing_decision = await workflow.router.route_query(request)
        
        return routing_decision
        
    except Exception as e:
        logger.error(f"라우팅 테스트 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/{agent_type}/health")
async def check_agent_health(agent_type: AgentType):
    """특정 에이전트 상태 확인"""
    try:
        workflow = get_workflow()
        agent_health = await workflow.agent_manager.health_check_all()
        
        if agent_type not in agent_health:
            raise HTTPException(status_code=404, detail="에이전트를 찾을 수 없습니다")
        
        return {
            "agent_type": agent_type.value,
            "status": "healthy" if agent_health[agent_type] else "unhealthy",
            "available": agent_health[agent_type]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"에이전트 상태 확인 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test")
async def test_system():
    """시스템 통합 테스트"""
    test_queries = [
        ("사업계획서 작성 방법을 알려주세요", AgentType.BUSINESS_PLANNING),
        ("고객 불만 처리 방법은?", AgentType.CUSTOMER_SERVICE),
        ("SNS 마케팅 전략을 추천해주세요", AgentType.MARKETING),
        ("요즘 스트레스가 심해요", AgentType.MENTAL_HEALTH),
        ("회의 일정을 자동으로 잡아주세요", AgentType.TASK_AUTOMATION)
    ]
    
    results = []
    
    for query, expected_agent in test_queries:
        try:
            request = UnifiedRequest(user_id=999, message=query)
            workflow = get_workflow()
            routing_decision = await workflow.router.route_query(request)
            
            results.append({
                "query": query,
                "expected_agent": expected_agent.value,
                "routed_agent": routing_decision.agent_type.value,
                "confidence": routing_decision.confidence,
                "correct": routing_decision.agent_type == expected_agent
            })
            
        except Exception as e:
            results.append({
                "query": query,
                "expected_agent": expected_agent.value,
                "error": str(e),
                "correct": False
            })
    
    accuracy = sum(1 for r in results if r.get("correct", False)) / len(results)
    
    return {
        "test_results": results,
        "accuracy": accuracy,
        "total_tests": len(results)
    }

# ===faq===

@app.get("/faq")
def get_faqs(
    category: Optional[str] = None, 
    search: Optional[str] = None, 
    db: Session = Depends(get_db_dependency)
):
    """FAQ 목록 조회"""
    try:
        query = db.query(FAQ).filter(FAQ.is_active == True)
        if category:
            query = query.filter(FAQ.category == category)
        if search:
            query = query.filter(FAQ.question.ilike(f"%{search}%"))
        faqs = query.order_by(FAQ.view_count.desc()).all()

        return create_success_response([{
            "faq_id": f.faq_id,
            "category": f.category,
            "question": f.question,
            "answer": f.answer,
            "view_count": f.view_count,
            "created_at": f.created_at.isoformat() if f.created_at else None
        } for f in faqs])
    except Exception as e:
        logger.error(f"FAQ 조회 오류: {e}")
        return create_error_response("FAQ 조회 실패", "FAQ_LIST_ERROR")


@app.patch("/faq/{faq_id}/view")
def increase_faq_view(faq_id: int, db: Session = Depends(get_db_dependency)):
    """FAQ 조회수 증가"""
    try:
        faq = db.query(FAQ).filter(FAQ.faq_id == faq_id).first()
        if not faq:
            return create_error_response("FAQ를 찾을 수 없습니다", "FAQ_NOT_FOUND")
        faq.view_count += 1
        db.commit()
        return create_success_response({"faq_id": faq_id, "view_count": faq.view_count})
    except Exception as e:
        logger.error(f"FAQ 조회수 증가 오류: {e}")
        return create_error_response("FAQ 조회수 업데이트 실패", "FAQ_VIEW_ERROR")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=DEBUG_MODE,
        log_level=LOG_LEVEL.lower()
    )
