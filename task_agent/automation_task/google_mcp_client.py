from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
import requests
import json

# --- MCP 서버 설정 ---
# IMPORTANT: 여기에 실제 MCP 서버의 IP 주소와 포트를 입력하세요.
# 예시: "http://localhost:8080" 또는 "http://your.mcp.server.com:8080"
MCP_SERVER_BASE_URL = "http://YOUR_MCP_SERVER_IP:PORT"

if MCP_SERVER_BASE_URL == "http://YOUR_MCP_SERVER_IP:PORT":
    print("경고: MCP_SERVER_BASE_URL을 실제 MCP 서버 주소로 업데이트해야 합니다.")
    print("     그렇지 않으면 API 호출이 실패할 수 있습니다.")

app = FastAPI(
    title="Google Calendar & Gmail Proxy API (via MCP Server)",
    description="FastAPI application to proxy requests to an internal MCP server "
                "for Google Calendar and Gmail operations.",
    version="1.0.0"
)

# --- 공통 MCP API 호출 함수 ---
async def _call_mcp_api(endpoint: str, method: str = "POST", payload: Optional[dict] = None, params: Optional[dict] = None):
    """
    MCP 서버로 HTTP 요청을 보내고 응답을 처리하는 내부 함수입니다.
    """
    url = f"{MCP_SERVER_BASE_URL}{endpoint}"
    
    try:
        response = requests.request(method, url, json=payload, params=params)
        response.raise_for_status() # 4xx/5xx HTTP 에러 시 예외 발생

        # MCP 서버의 응답을 그대로 반환
        return response.json()
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail=f"MCP 서버 ({MCP_SERVER_BASE_URL})에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요."
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="MCP 서버로부터 응답을 받는 데 시간이 너무 오래 걸렸습니다."
        )
    except requests.exceptions.RequestException as e:
        # MCP 서버에서 받은 HTTP 에러를 클라이언트에게 전달
        status_code = e.response.status_code if e.response is not None else 500
        detail = f"MCP 서버 오류: {e}"
        if e.response is not None:
            detail += f" - {e.response.text}"
        raise HTTPException(status_code=status_code, detail=detail)


# --- Pydantic 모델 정의 (Request Body 검증용) ---

# Gmail 모델
class GmailListRequest(BaseModel):
    maxResults: int = Field(5, ge=1, le=100)
    query: Optional[str] = None

class GmailSearchRequest(BaseModel):
    query: str
    maxResults: int = Field(10, ge=1, le=100)

class GmailSendRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    cc: Optional[EmailStr] = None
    bcc: Optional[EmailStr] = None

class GmailModifyRequest(BaseModel):
    id: str = Field(..., description="Gmail Message ID")
    addLabels: Optional[List[str]] = None
    removeLabels: Optional[List[str]] = None

# Calendar 모델
class CalendarListRequest(BaseModel):
    maxResults: int = Field(10, ge=1, le=250)
    # ISO 8601 UTC 형식 (예: "2024-01-01T00:00:00Z")
    timeMin: Optional[str] = Field(None, example="2024-07-01T00:00:00Z")
    timeMax: Optional[str] = Field(None, example="2024-07-31T23:59:59Z")

class CalendarCreateEventRequest(BaseModel):
    summary: str
    location: Optional[str] = None
    description: Optional[str] = None
    # ISO 8601 UTC 형식 (예: "2024-07-25T10:00:00Z")
    start: str = Field(..., example="2024-07-25T10:00:00Z")
    end: str = Field(..., example="2024-07-25T11:00:00Z")
    attendees: Optional[List[EmailStr]] = None

class CalendarUpdateEventRequest(BaseModel):
    eventId: str = Field(..., description="Google Calendar Event ID")
    summary: Optional[str] = None
    location: Optional[str] = None
    # ISO 8601 UTC 형식
    start: Optional[str] = Field(None, example="2024-07-25T11:00:00Z")
    end: Optional[str] = Field(None, example="2024-07-25T12:00:00Z")

class CalendarDeleteEventRequest(BaseModel):
    eventId: str = Field(..., description="Google Calendar Event ID")


# --- FastAPI 엔드포인트 ---

@app.get("/")
async def root():
    return {"message": "Welcome to the Google Calendar & Gmail Proxy API"}

## Gmail Operations
@app.post("/gmail/list", summary="List Recent Emails")
async def list_recent_emails_api(request_body: GmailListRequest):
    return await _call_mcp_api("/gmail/list", payload=request_body.dict(exclude_unset=True))

@app.post("/gmail/search", summary="Search Emails")
async def search_emails_api(request_body: GmailSearchRequest):
    return await _call_mcp_api("/gmail/search", payload=request_body.dict())

@app.post("/gmail/send", summary="Send Email")
async def send_email_api(request_body: GmailSendRequest):
    return await _call_mcp_api("/gmail/send", payload=request_body.dict(exclude_unset=True))

@app.post("/gmail/modify", summary="Modify Email (Add/Remove Labels)")
async def modify_email_api(request_body: GmailModifyRequest):
    return await _call_mcp_api("/gmail/modify", payload=request_body.dict(exclude_unset=True))

## Calendar Operations
@app.post("/calendar/list", summary="List Events")
async def list_events_api(request_body: CalendarListRequest):
    return await _call_mcp_api("/calendar/list", payload=request_body.dict(exclude_unset=True))

@app.post("/calendar/create", summary="Create Event")
async def create_event_api(request_body: CalendarCreateEventRequest):
    return await _call_mcp_api("/calendar/create", payload=request_body.dict(exclude_unset=True))

@app.post("/calendar/update", summary="Update Event")
async def update_event_api(request_body: CalendarUpdateEventRequest):
    return await _call_mcp_api("/calendar/update", payload=request_body.dict(exclude_unset=True))

@app.post("/calendar/delete", summary="Delete Event")
async def delete_event_api(request_body: CalendarDeleteEventRequest):
    return await _call_mcp_api("/calendar/delete", payload=request_body.dict())