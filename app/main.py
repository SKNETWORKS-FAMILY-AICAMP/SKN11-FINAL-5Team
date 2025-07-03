from fastapi import FastAPI, Depends, HTTPException, APIRouter, Request
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Conversation
from app.schemas import ChatRequest, ChatResponse, ConversationCreate, UserCreate, SocialLoginRequest
from app.mental_agent_graph import build_mental_graph
from app.crud import create_message, create_user, get_user_by_social, create_user_social
import requests
import os

app = FastAPI()
router = APIRouter()

from dotenv import load_dotenv
load_dotenv()

def get_db():
    db = SessionLocal()
    try:
        yield db  
    finally:
        db.close()

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter_by(conversation_id=req.conversation_id, user_id=req.user_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="대화 세션을 찾을 수 없습니다.")
    
    create_message(
        db,
        conversation_id=req.conversation_id,
        sender_type="user",
        agent_type="TBD(router)",
        content=req.user_input
    )

    g = build_mental_graph()
    runnable = g.compile()
    state = {
        "user_id": req.user_id,
        "conversation_id": req.conversation_id,
        "user_input": req.user_input,
        "phq9_suggested": False,
        "db": db,  # db session을 state에 추가!
    }
    result = runnable.invoke(state)
    return result

@app.post("/create_conversation")
def create_conversation(req: ConversationCreate, db: Session = Depends(get_db)):
    from app.models import Conversation
    from datetime import datetime
    conv = Conversation(
        user_id=req.user_id, started_at=datetime.now()
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return {"conversation_id": conv.conversation_id}

@app.post("/signup")
def signup(req: UserCreate, db: Session = Depends(get_db)):
    user = create_user(
        db,
        email=req.email,
        password=req.password,
        nickname=req.nickname,
        business_type=req.business_type
    )
    return {"user_id": user.user_id}

# 1. 구글 소셜 로그인
@router.api_route("/login/oauth2/code/google", methods=["GET", "POST"])
def google_login(request: Request, code: str, db: Session = Depends(get_db)):
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
        raise HTTPException(400, "구글 토큰 요청 실패")
    token = resp.json()["access_token"]

    userinfo = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {token}"}
    ).json()
    provider = "google"
    social_id = userinfo["id"]
    email = userinfo.get("email")
    nickname = userinfo.get("name", "")

    user = get_user_by_social(db, provider, social_id)
    if not user:
        user = create_user_social(db, provider, social_id, email, nickname, access_token=token)
    return {"user_id": user.user_id, "provider": provider, "email": user.email}


# 2. 카카오 소셜 로그인
@router.api_route("/login/oauth2/code/kakao", methods=["GET", "POST"])
def kakao_login(code: str, db: Session = Depends(get_db)):
    token_url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": os.getenv("KAKAO_CLIENT_ID"),
        "redirect_uri": os.getenv("KAKAO_REDIRECT_URI"),
        "code": code,
    }
    resp = requests.post(token_url, data=data)
    if not resp.ok:
        raise HTTPException(400, "카카오 토큰 요청 실패")
    token = resp.json()["access_token"] 

    userinfo = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {token}"}
    ).json()
    provider = "kakao"
    social_id = str(userinfo["id"])
    kakao_account = userinfo.get("kakao_account", {})
    email = kakao_account.get("email", None)
    nickname = kakao_account.get("profile", {}).get("nickname", "")

    user = get_user_by_social(db, provider, social_id)
    if not user:
        user = create_user_social(db, provider, social_id, email, nickname, access_token=token)
    return {"user_id": user.user_id, "provider": provider, "email": user.email}


# 3. 네이버 소셜 로그인
@router.api_route("/login/oauth2/code/naver", methods=["GET", "POST"])
def naver_login(code: str, state: str, db: Session = Depends(get_db)):
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
        raise HTTPException(400, "네이버 토큰 요청 실패")
    token = resp.json()["access_token"]

    userinfo = requests.get(
        "https://openapi.naver.com/v1/nid/me",
        headers={"Authorization": f"Bearer {token}"}
    ).json()["response"]
    provider = "naver"
    social_id = userinfo["id"]
    email = userinfo.get("email", None)
    nickname = userinfo.get("nickname", "")

    user = get_user_by_social(db, provider, social_id)
    if not user:
        user = create_user_social(db, provider, social_id, email, nickname, access_token=token)
    return {"user_id": user.user_id, "provider": provider, "email": user.email}

app.include_router(router)