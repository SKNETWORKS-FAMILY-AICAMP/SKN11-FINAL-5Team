"""
Mental Health Agent - 공통 모듈 사용 버전
기존 설정 파일들을 shared_modules로 대체
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared_modules import (
    get_config,
    get_db_session,
    get_session_context
)

from fastapi import FastAPI, Depends, HTTPException, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import requests

# 기존 모듈들
from shared_modules.database import SessionLocal
from models import Conversation
from schemas import ChatRequest, ChatResponse, ConversationCreate, UserCreate, SocialLoginRequest
from mental_agent_graph import build_mental_graph
from shared_modules.queries import create_message, create_user, get_user_by_social, create_user_social

# 로깅 설정
from shared_modules.logging_utils import setup_logging
logger = setup_logging("mental_health", log_file="../logs/mental_health.log")

# 설정 로드
config = get_config()

# FastAPI 앱 초기화
app = FastAPI(
    title="Mental Health Agent",
    description="정신건강 상담 AI 에이전트",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

def get_db():
    """데이터베이스 세션 의존성 (기존 호환성 유지)"""
    db = SessionLocal()
    try:
        yield db  
    finally:
        db.close()

def get_db_shared():
    """공통 모듈의 데이터베이스 세션 사용"""
    return get_db_session()

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """채팅 엔드포인트"""
    try:
        logger.info(f"Mental health chat request: {req.user_input[:100]}...")
        
        # 대화 세션 확인
        conv = db.query(Conversation).filter_by(
            conversation_id=req.conversation_id, 
            user_id=req.user_id
        ).first()
        
        if not conv:
            logger.error(f"대화 세션을 찾을 수 없습니다: conversation_id={req.conversation_id}, user_id={req.user_id}")
            raise HTTPException(status_code=404, detail="대화 세션을 찾을 수 없습니다.")
        
        # 사용자 메시지 저장
        create_message(
            db,
            conversation_id=req.conversation_id,
            sender_type="user",
            agent_type="mental_health",
            content=req.user_input
        )

        # 정신건강 그래프 실행
        g = build_mental_graph()
        runnable = g.compile()
        
        state = {
            "user_id": req.user_id,
            "conversation_id": req.conversation_id,
            "user_input": req.user_input,
            "phq9_suggested": False,
            "db": db, 
        }
        
        result = runnable.invoke(state)
        
        logger.info(f"Mental health response generated for user {req.user_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mental health chat error: {e}")
        raise HTTPException(status_code=500, detail="정신건강 상담 처리 중 오류가 발생했습니다.")

@app.post("/create_conversation")
def create_conversation(req: ConversationCreate, db: Session = Depends(get_db)):
    """대화 세션 생성"""
    try:
        # 새 대화 세션 생성
        new_conv = Conversation(
            user_id=req.user_id,
            agent_type="mental_health",
            title=req.title or "정신건강 상담"
        )
        
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        
        logger.info(f"새 대화 세션 생성: conversation_id={new_conv.conversation_id}, user_id={req.user_id}")
        
        return {
            "conversation_id": new_conv.conversation_id,
            "user_id": new_conv.user_id,
            "title": new_conv.title,
            "created_at": new_conv.created_at
        }
        
    except Exception as e:
        logger.error(f"대화 세션 생성 오류: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="대화 세션 생성에 실패했습니다.")

@app.post("/create_user")
def create_user_endpoint(req: UserCreate, db: Session = Depends(get_db)):
    """사용자 생성"""
    try:
        user = create_user(db, req)
        logger.info(f"새 사용자 생성: user_id={user.user_id}")
        
        return {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at
        }
        
    except Exception as e:
        logger.error(f"사용자 생성 오류: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="사용자 생성에 실패했습니다.")

@app.post("/social_login")
def social_login(req: SocialLoginRequest, db: Session = Depends(get_db)):
    """소셜 로그인"""
    try:
        # 기존 사용자 확인
        user = get_user_by_social(db, req.provider, req.social_id)
        
        if user:
            logger.info(f"기존 사용자 로그인: user_id={user.user_id}, provider={req.provider}")
            return {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "is_new_user": False
            }
        
        # 새 사용자 생성
        user = create_user_social(
            db,
            provider=req.provider,
            social_id=req.social_id,
            username=req.username,
            email=req.email
        )
        
        logger.info(f"새 소셜 사용자 생성: user_id={user.user_id}, provider={req.provider}")
        
        return {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "is_new_user": True
        }
        
    except Exception as e:
        logger.error(f"소셜 로그인 오류: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="소셜 로그인에 실패했습니다.")

@app.get("/conversations/{user_id}")
def get_user_conversations(user_id: str, db: Session = Depends(get_db)):
    """사용자의 대화 세션 목록 조회"""
    try:
        conversations = db.query(Conversation).filter_by(user_id=user_id).all()
        
        return [
            {
                "conversation_id": conv.conversation_id,
                "title": conv.title,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at
            }
            for conv in conversations
        ]
        
    except Exception as e:
        logger.error(f"대화 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="대화 목록 조회에 실패했습니다.")

@app.get("/health")
def health_check():
    """서비스 상태 확인"""
    try:
        # 데이터베이스 연결 확인
        db_connected = bool(get_db_session())
        
        return {
            "status": "healthy",
            "agent": "mental_health",
            "services": {
                "database": "connected" if db_connected else "disconnected",
                "mental_graph": "available"
            },
            "config_validation": config.validate_config()
        }
        
    except Exception as e:
        logger.error(f"Health check 오류: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/status")
def get_detailed_status():
    """상세 상태 정보"""
    try:
        from shared_modules import get_db_manager
        
        return {
            "status": "operational",
            "agent": "mental_health",
            "database": get_db_manager().get_engine_info(),
            "configuration": config.to_dict()
        }
        
    except Exception as e:
        logger.error(f"상태 조회 오류: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

# PHQ-9 관련 엔드포인트 (기존 기능 유지)
@app.post("/phq9/start")
def start_phq9_assessment(user_id: str, conversation_id: str, db: Session = Depends(get_db)):
    """PHQ-9 평가 시작"""
    try:
        # PHQ-9 평가 로직 구현
        logger.info(f"PHQ-9 평가 시작: user_id={user_id}, conversation_id={conversation_id}")
        
        return {
            "message": "PHQ-9 우울증 선별검사를 시작합니다.",
            "assessment_type": "phq9",
            "status": "started"
        }
        
    except Exception as e:
        logger.error(f"PHQ-9 시작 오류: {e}")
        raise HTTPException(status_code=500, detail="PHQ-9 평가 시작에 실패했습니다.")

# 긴급상황 처리 엔드포인트
@app.post("/emergency")
def handle_emergency(user_id: str, conversation_id: str, message: str, db: Session = Depends(get_db)):
    """긴급상황 처리"""
    try:
        logger.warning(f"긴급상황 감지: user_id={user_id}, message={message[:100]}")
        
        # 긴급 메시지 저장
        create_message(
            db,
            conversation_id=conversation_id,
            sender_type="system",
            agent_type="mental_health",
            content=f"긴급상황 감지: {message}"
        )
        
        # 긴급 응답 생성
        emergency_response = """
긴급한 상황인 것 같습니다. 즉시 도움을 받으실 것을 강력히 권합니다.

🆘 **긴급 연락처**
- 생명의전화: 1588-9191
- 청소년전화: 1388
- 정신건강위기상담전화: 1577-0199
- 응급실: 119

당신의 생명은 소중합니다. 혼자 견디지 마시고 전문가의 도움을 받아주세요.
"""
        
        # 응답 저장
        create_message(
            db,
            conversation_id=conversation_id,
            sender_type="agent",
            agent_type="mental_health",
            content=emergency_response
        )
        
        return {
            "type": "emergency",
            "response": emergency_response,
            "emergency_contacts": [
                {"name": "생명의전화", "number": "1588-9191"},
                {"name": "청소년전화", "number": "1388"},
                {"name": "정신건강위기상담전화", "number": "1577-0199"},
                {"name": "응급실", "number": "119"}
            ]
        }
        
    except Exception as e:
        logger.error(f"긴급상황 처리 오류: {e}")
        raise HTTPException(status_code=500, detail="긴급상황 처리에 실패했습니다.")

# 앱에 라우터 포함
app.include_router(router)

# 메인 실행
if __name__ == "__main__":
    import uvicorn
    
    logger.info("Mental Health Agent 서버 시작")
    
    # 설정 검증
    validation = config.validate_config()
    if validation["warnings"]:
        for warning in validation["warnings"]:
            logger.warning(warning)
    
    # 서버 실행
    uvicorn.run(
        app,
        host=config.HOST,
        port=8004,
        log_level=config.LOG_LEVEL.lower()
    )

# uvicorn main:app --reload --host 0.0.0.0 --port 8004
