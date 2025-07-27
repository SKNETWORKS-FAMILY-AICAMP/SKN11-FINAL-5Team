"""
TinkerBell 업무지원 에이전트 v5 - 메인 애플리케이션
리팩토링된 FastAPI 애플리케이션
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from contextlib import asynccontextmanager

# 텔레메트리 비활성화
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY'] = 'False' 
os.environ['DO_NOT_TRACK'] = '1'

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 로컬 모델 import
from models import (
    UserQuery, AutomationRequest, EmailRequest, 
    InstagramPostRequest, EventCreate, EventResponse, 
    CalendarListResponse, QuickEventCreate
)

# 공통 모듈 import
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
try:
    from shared_modules import (
        create_success_response, 
        create_error_response,
        create_task_response
    )
    from shared_modules.logging_utils import setup_logging
except ImportError:
    # 공통 모듈이 없는 경우 기본 함수들 정의
    def create_success_response(data, message="Success"):
        return {"success": True, "data": data, "message": message}
    
    def create_error_response(message, error_code="ERROR"):
        return {"success": False, "error": message, "error_code": error_code}
        
    def create_task_response(**kwargs):
        return kwargs
    
    def setup_logging(name, log_file=None):
        return logging.getLogger(name)

# 서비스 레이어 import
from services.task_agent_service import TaskAgentService
from services.automation_service import AutomationService  
from automation_task.email_service import EmailService
from automation_task.instagram_service import InstagramPostingService
from automation_task.google_calendar_service import GoogleCalendarService

# 설정 및 의존성
from config import config
from dependencies import get_services

# 로깅 설정
logger = setup_logging("task", log_file="logs/task.log")

# 글로벌 서비스 컨테이너
services = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global services
    
    # 시작
    logger.info("TinkerBell 업무지원 에이전트 v5 시작")
    
    # 환경 설정 검증
    validation = config.validate()
    if not validation["is_valid"]:
        logger.error(f"환경 설정 오류: {validation['issues']}")
        raise RuntimeError("환경 설정이 올바르지 않습니다.")
    
    # 서비스 컨테이너 초기화
    try:
        services = await get_services()
        logger.info("서비스 컨테이너 초기화 완료")
    except Exception as e:
        logger.error(f"서비스 초기화 실패: {e}")
        raise RuntimeError("서비스 초기화 실패")
    
    yield
    
    # 종료
    logger.info("TinkerBell 업무지원 에이전트 v5 종료")
    if services:
        await services.cleanup()

# FastAPI 앱 생성
app = FastAPI(
    title="TinkerBell 업무지원 에이전트 v5",
    description="리팩토링된 AI 기반 업무지원 시스템",
    version="5.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 의존성 주입 =====

def get_task_agent_service() -> TaskAgentService:
    """TaskAgentService 의존성"""
    if not services:
        raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다.")
    return services.task_agent_service

def get_automation_service() -> AutomationService:
    """AutomationService 의존성"""
    if not services:
        raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다.")
    return services.automation_service

def get_email_service() -> EmailService:
    """EmailService 의존성"""
    if not services:
        raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다.")
    return services.email_service

def get_calendar_service() -> GoogleCalendarService:
    """CalendarService 의존성"""
    if not services:
        raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다.")
    return services.calendar_service

def get_instagram_service() -> InstagramPostingService:
    """InstagramService 의존성"""
    if not services:
        raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다.")
    return services.instagram_service

# ===== 핵심 API 엔드포인트 =====

@app.post("/agent/query")
async def process_user_query(
    query: UserQuery,
    task_service: TaskAgentService = Depends(get_task_agent_service)
):
    """사용자 쿼리 처리 - 자동화 업무 등록 포함"""
    try:
        # 쿼리 처리 및 자동화 작업 등록
        response = await task_service.process_query(query)
        
        # 표준 응답 형식으로 변환
        response_data = create_task_response(
            conversation_id=response.conversation_id,
            answer=response.response,
            topics=[response.metadata.get('intent', 'general_inquiry')],
            sources=response.sources or "",
            intent=response.metadata.get('intent', 'general_inquiry'),
            urgency=getattr(response, 'urgency', 'medium'),
            actions=response.metadata.get('actions', []),
            automation_created=response.metadata.get('automation_created', False)
        )
        
        return create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"쿼리 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/automation/task")
async def create_automation_task(
    request: AutomationRequest,
    automation_service: AutomationService = Depends(get_automation_service)
):
    """자동화 작업 직접 생성"""
    try:
        response = await automation_service.create_task(request)
        return create_success_response(response.dict())
    except Exception as e:
        logger.error(f"자동화 작업 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/automation/task/{task_id}")
async def get_automation_task_status(
    task_id: int,
    automation_service: AutomationService = Depends(get_automation_service)
):
    """자동화 작업 상태 조회"""
    try:
        status = await automation_service.get_task_status(task_id)
        return create_success_response(status)
    except Exception as e:
        logger.error(f"자동화 작업 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/automation/task/{task_id}")
async def cancel_automation_task(
    task_id: int,
    automation_service: AutomationService = Depends(get_automation_service)
):
    """자동화 작업 취소"""
    try:
        result = await automation_service.cancel_task(task_id)
        if result:
            return create_success_response({"message": "작업이 취소되었습니다."})
        else:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    except Exception as e:
        logger.error(f"자동화 작업 취소 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/automation/tasks")
async def get_user_automation_tasks(
    user_id: int = Query(..., description="사용자 ID"),
    status: Optional[str] = Query(None, description="작업 상태 필터"),
    limit: int = Query(50, ge=1, le=100, description="최대 조회 수"),
    automation_service: AutomationService = Depends(get_automation_service)
):
    """사용자 자동화 작업 목록 조회"""
    try:
        tasks = await automation_service.get_user_tasks(user_id, status, limit)
        return create_success_response({"tasks": tasks, "count": len(tasks)})
    except Exception as e:
        logger.error(f"사용자 자동화 작업 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== 이메일 API =====

@app.post("/email/send")
async def send_email(
    req: EmailRequest,
    email_service: EmailService = Depends(get_email_service)
):
    """이메일 발송"""
    try:
        result = await email_service.send_email(req.dict())
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "이메일 발송 실패"))
        return create_success_response(result)
    except Exception as e:
        logger.error(f"이메일 발송 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== 시스템 API =====

@app.get("/health")
async def health_check():
    """헬스 체크"""
    try:
        if services:
            status = await services.get_health_status()
            return create_success_response(status, "시스템 상태 정상")
        else:
            return create_error_response("서비스가 초기화되지 않았습니다.", "SERVICE_NOT_INITIALIZED")
    except Exception as e:
        logger.error(f"헬스 체크 실패: {e}")
        return create_error_response(str(e), "HEALTH_CHECK_ERROR")

@app.get("/status")
async def get_system_status():
    """시스템 상태 조회"""
    try:
        base_status = {
            "service": "TinkerBell Task Agent v5",
            "version": "5.0.0",
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "openai_configured": bool(config.OPENAI_API_KEY),
                "google_configured": bool(config.GOOGLE_API_KEY),
                "mysql_configured": bool(config.MYSQL_URL),
                "chroma_configured": bool(config.CHROMA_PERSIST_DIR)
            },
            "config_validation": config.validate()
        }
        
        if services:
            service_status = await services.get_detailed_status()
            base_status.update(service_status)
            base_status["status"] = "healthy"
        else:
            base_status["status"] = "error"
            base_status["message"] = "서비스가 초기화되지 않았습니다."
        
        return base_status
        
    except Exception as e:
        logger.error(f"시스템 상태 조회 실패: {e}")
        return {
            "service": "TinkerBell Task Agent v5",
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


# ===== Instagram OAuth 인증 API =====
instagram_service = InstagramPostingService()  
from shared_modules import get_session_context
from shared_modules.db_models import InstagramToken

INSTAGRAM_APP_ID = os.getenv("INSTAGRAM_APP_ID", "YOUR_APP_ID")
INSTAGRAM_APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET", "YOUR_APP_SECRET")
REDIRECT_URI = os.getenv("INSTAGRAM_REDIRECT_URI", "https://localhost:8005/auth/instagram/callback")

@app.get("/auth/instagram")
def instagram_login(user_id: int):
    auth_url = (
        f"https://www.instagram.com/oauth/authorize"
        f"?client_id={INSTAGRAM_APP_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=business_basic,business_content_publish"
        f"&response_type=code"
        f"&state={user_id}"  # user_id를 state로 넘김
    )
    return auth_url

# ======== OAuth Callback ========
@app.get("/auth/instagram/callback")
async def instagram_callback(code: str, state: str):
    user_id = int(state)  # state 파라미터로 user_id를 복원

    # Access Token 교환
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://api.instagram.com/oauth/access_token",
            data={
                "client_id": INSTAGRAM_APP_ID,
                "client_secret": INSTAGRAM_APP_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI,
                "code": code,
            },
        )
    token_data = res.json()
    access_token = token_data.get("access_token")

    if not access_token:
        return JSONResponse({"error": "토큰 발급 실패", "details": token_data}, status_code=400)

    # 계정 정보 가져오기 (graph_id, username)
    async with httpx.AsyncClient() as client:
        me_res = await client.get(
            "https://graph.instagram.com/me",
            params={"fields": "id,username", "access_token": access_token},
        )
    me_data = me_res.json()

    if "id" not in me_data:
        return JSONResponse({"error": "계정 정보 조회 실패", "details": me_data}, status_code=400)

    # DB 저장 (faq.py 스타일)
    with get_session_context() as db:
        account = InstagramToken(
            user_id=user_id,
            access_token=access_token,
            graph_id=me_data["id"],
            username=me_data.get("username"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(account)
        db.commit()
        db.refresh(account)

    return JSONResponse({"message": "Instagram 계정 연동 성공", "data": me_data})

# ======== 포스팅 API ========
@app.post("/instagram/post")
async def instagram_post(request: Request):
    body = await request.json()
    caption = body.get("caption")
    image_url = body.get("image_url")

    with get_session_context() as db:
        account = db.query(InstagramToken).first()
        if not account:
            return JSONResponse({"error": "Instagram 계정이 등록되지 않았습니다. 계정을 등록해주세요."}, status_code=400)

        # 1. 미디어 생성
        async with httpx.AsyncClient() as client:
            create_res = await client.post(
                f"https://graph.instagram.com/{account.graph_id}/media",
                params={
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": account.access_token,
                },
            )
        create_data = create_res.json()
        creation_id = create_data.get("id")

        if not creation_id:
            return JSONResponse({"error": "미디어 생성 실패", "details": create_data}, status_code=400)

        # 2. 게시 요청
        async with httpx.AsyncClient() as client:
            publish_res = await client.post(
                f"https://graph.instagram.com/{account.graph_id}/media_publish",
                params={
                    "creation_id": creation_id,
                    "access_token": account.access_token,
                },
            )
    return publish_res.json()

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
