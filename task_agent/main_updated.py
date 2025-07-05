"""
Task Agent - 공통 모듈 사용 버전
기존 설정 파일들을 shared_modules로 대체
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared_modules import (
    get_config,
    get_llm_manager,
    get_db_session,
    get_session_context,
    setup_logging
)

import asyncio
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

# 기존 모듈들 (공통 모듈로 대체되지 않는 것들)
from models import PersonaType, TaskRequest, TaskResponse
from llm_handler import LLMHandler
from automation import AutomationManager
from rag import RAGManager

# 로깅 설정
logger = setup_logging("task_agent", log_file="../logs/task_automation.log")

# 설정 로드
config = get_config()

# FastAPI 앱 초기화
app = FastAPI(
    title="Task Automation Agent",
    description="개인화된 업무 자동화 AI 에이전트",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 매니저 인스턴스들
llm_handler: Optional[LLMHandler] = None
automation_manager: Optional[AutomationManager] = None
rag_manager: Optional[RAGManager] = None

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 초기화"""
    global llm_handler, automation_manager, rag_manager
    
    try:
        logger.info("Task Agent 초기화 시작")
        
        # 설정 검증
        validation = config.validate_config()
        if not validation["is_valid"]:
            logger.error(f"설정 검증 실패: {validation['issues']}")
            raise Exception(f"설정 오류: {validation['issues']}")
        
        if validation["warnings"]:
            for warning in validation["warnings"]:
                logger.warning(warning)
        
        # 매니저들 초기화
        llm_handler = LLMHandler()
        automation_manager = AutomationManager()
        rag_manager = RAGManager()
        
        logger.info("Task Agent 초기화 완료")
        
    except Exception as e:
        logger.error(f"Task Agent 초기화 실패: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 정리"""
    logger.info("Task Agent 종료")

# 의존성 함수들
def get_llm_handler() -> LLMHandler:
    """LLM 핸들러 의존성"""
    if llm_handler is None:
        raise HTTPException(status_code=500, detail="LLM 핸들러가 초기화되지 않았습니다")
    return llm_handler

def get_automation_manager() -> AutomationManager:
    """자동화 매니저 의존성"""
    if automation_manager is None:
        raise HTTPException(status_code=500, detail="자동화 매니저가 초기화되지 않았습니다")
    return automation_manager

def get_rag_manager() -> RAGManager:
    """RAG 매니저 의존성"""
    if rag_manager is None:
        raise HTTPException(status_code=500, detail="RAG 매니저가 초기화되지 않았습니다")
    return rag_manager

# 요청/응답 모델들
class ChatRequest(BaseModel):
    message: str
    persona: PersonaType = PersonaType.ENTREPRENEUR
    conversation_history: Optional[List[Dict[str, str]]] = None
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    urgency: str = "medium"
    confidence: float = 0.0
    automation_suggestions: List[str] = []
    timestamp: datetime

class AutomationRequest(BaseModel):
    message: str
    persona: PersonaType = PersonaType.ENTREPRENEUR
    conversation_history: Optional[List[Dict[str, str]]] = None

class AutomationResponse(BaseModel):
    task_type: str
    status: str
    details: Dict[str, Any]
    message: str

# API 엔드포인트들
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    llm: LLMHandler = Depends(get_llm_handler),
    rag: RAGManager = Depends(get_rag_manager)
):
    """일반 대화 엔드포인트"""
    try:
        logger.info(f"대화 요청 수신: {request.message[:100]}...")
        
        # 의도 분석
        intent_result = await llm.analyze_intent(
            request.message, 
            request.persona,
            request.conversation_history
        )
        
        # RAG를 통한 컨텍스트 검색
        context = await rag.search_relevant_documents(
            request.message,
            request.persona,
            max_results=3
        )
        
        # 최종 컨텍스트 구성
        final_context = request.context or ""
        if context:
            final_context += f"\n\n=== 관련 정보 ===\n{context}"
        
        # 응답 생성
        response_text = await llm.generate_response(
            request.message,
            request.persona,
            final_context,
            request.conversation_history
        )
        
        # 자동화 제안 생성
        automation_suggestions = []
        automation_intent = await llm.classify_automation_intent(request.message)
        if automation_intent:
            automation_suggestions.append(f"'{automation_intent}' 자동화를 설정해드릴까요?")
        
        return ChatResponse(
            response=response_text,
            intent=intent_result.get("intent"),
            urgency=intent_result.get("urgency", "medium"),
            confidence=intent_result.get("confidence", 0.0),
            automation_suggestions=automation_suggestions,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"대화 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/automation", response_model=AutomationResponse)
async def automation_endpoint(
    request: AutomationRequest,
    llm: LLMHandler = Depends(get_llm_handler),
    auto_mgr: AutomationManager = Depends(get_automation_manager)
):
    """자동화 작업 실행 엔드포인트"""
    try:
        logger.info(f"자동화 요청 수신: {request.message[:100]}...")
        
        # 자동화 의도 분류
        automation_type = await llm.classify_automation_intent(request.message)
        
        if not automation_type:
            return AutomationResponse(
                task_type="none",
                status="no_automation_detected",
                details={},
                message="자동화 가능한 작업을 찾지 못했습니다."
            )
        
        # 정보 추출
        extracted_info = await llm.extract_information(
            request.message,
            automation_type,
            request.conversation_history
        )
        
        if not extracted_info:
            return AutomationResponse(
                task_type=automation_type,
                status="insufficient_information",
                details={},
                message="자동화 실행에 필요한 정보가 부족합니다. 더 구체적으로 말씀해주세요."
            )
        
        # 자동화 실행
        result = await auto_mgr.execute_automation(automation_type, extracted_info)
        
        return AutomationResponse(
            task_type=automation_type,
            status=result.get("status", "unknown"),
            details=result.get("details", {}),
            message=result.get("message", "자동화가 실행되었습니다.")
        )
        
    except Exception as e:
        logger.error(f"자동화 실행 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """시스템 상태 조회"""
    try:
        from shared_modules import get_llm_manager, get_db_manager, get_vector_manager
        
        # 서비스 상태 확인
        db_connected = bool(get_db_session())
        
        return {
            "status": "healthy",
            "agent": "task_automation",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": "connected" if db_connected else "disconnected",
                "llm": "available" if llm_handler else "unavailable",
                "automation": "available" if automation_manager else "unavailable",
                "rag": "available" if rag_manager else "unavailable"
            },
            "config_validation": config.validate_config(),
            "managers": {
                "llm": get_llm_manager().get_status() if llm_handler else None,
                "db": get_db_manager().get_engine_info(),
                "vector": get_vector_manager().get_status()
            }
        }
        
    except Exception as e:
        logger.error(f"상태 조회 오류: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/health")
def health_check():
    """간단한 헬스 체크"""
    return {
        "status": "healthy",
        "agent": "task_automation",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/personas")
def get_personas():
    """사용 가능한 페르소나 목록"""
    return {
        "personas": [persona.value for persona in PersonaType],
        "default": PersonaType.ENTREPRENEUR.value
    }

@app.post("/validate-config")
def validate_configuration():
    """설정 검증"""
    validation = config.validate_config()
    return {
        "validation": validation,
        "config_summary": config.to_dict()
    }

# 개발용 엔드포인트
@app.get("/debug/llm-test")
async def test_llm():
    """LLM 연결 테스트"""
    try:
        from shared_modules import test_llm_connection
        result = test_llm_connection()
        return {"llm_test": "passed" if result else "failed"}
    except Exception as e:
        return {"llm_test": "failed", "error": str(e)}

@app.get("/debug/db-test")
def test_database():
    """데이터베이스 연결 테스트"""
    try:
        from shared_modules import test_db_connection
        result = test_db_connection()
        return {"db_test": "passed" if result else "failed"}
    except Exception as e:
        return {"db_test": "failed", "error": str(e)}

# 메인 실행
if __name__ == "__main__":
    import uvicorn
    
    logger.info("Task Agent 서버 시작")
    
    # 설정 검증
    validation = config.validate_config()
    if not validation["is_valid"]:
        logger.error(f"설정 검증 실패: {validation}")
        exit(1)
    
    # 서버 실행
    uvicorn.run(
        app,
        host=config.HOST,
        port=8003,
        log_level=config.LOG_LEVEL.lower()
    )

# uvicorn main:app --reload --host 0.0.0.0 --port 8003
