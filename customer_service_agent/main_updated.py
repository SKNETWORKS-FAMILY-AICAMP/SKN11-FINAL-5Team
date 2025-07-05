"""
Customer Service Agent - 공통 모듈 사용 버전
기존 설정 파일들을 shared_modules로 대체
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared_modules import (
    get_config,
    get_llm,
    get_vectorstore,
    get_retriever,
    get_db_session,
    setup_logging
)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from customer_agent.agent_runner import run_customer_service_with_rag

# 로깅 설정
logger = setup_logging("customer_service", log_file="../logs/customer_service.log")

# 설정 로드
config = get_config()

# FastAPI 초기화
app = FastAPI(title="Customer Service Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청/응답 모델
class CustomerQueryRequest(BaseModel):
    question: str
    customer_id: str = None
    conversation_id: int = None

class CustomerQueryResponse(BaseModel):
    answer: str
    intent: str = None
    confidence: float = None
    sources: str = None

@app.post("/agent/query", response_model=CustomerQueryResponse)
async def query_customer_service(request: CustomerQueryRequest):
    """고객 서비스 쿼리 처리"""
    try:
        logger.info(f"고객 서비스 쿼리 수신: {request.question[:100]}...")
        
        # 공통 모듈의 LLM 사용
        result = run_customer_service_with_rag(
            user_input=request.question,
            customer_id=request.customer_id,
            conversation_id=request.conversation_id or 1
        )
        
        return CustomerQueryResponse(
            answer=result.get("answer", "죄송합니다. 응답을 생성할 수 없습니다."),
            intent=result.get("intent"),
            confidence=result.get("confidence"),
            sources=result.get("sources")
        )
        
    except Exception as e:
        logger.error(f"고객 서비스 쿼리 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    """서비스 상태 확인"""
    return {
        "status": "healthy",
        "agent": "customer_service",
        "config_validation": config.validate_config(),
        "services": {
            "database": "connected" if get_db_session() else "disconnected",
            "llm": "available" if get_llm() else "unavailable",
            "vectorstore": "available" if get_vectorstore() else "unavailable"
        }
    }

@app.get("/status")
def get_status():
    """상세 상태 정보"""
    from shared_modules import get_llm_manager, get_vector_manager, get_db_manager
    
    return {
        "llm_status": get_llm_manager().get_status(),
        "vector_status": get_vector_manager().get_status(),
        "db_status": get_db_manager().get_engine_info()
    }

# 메인 실행
if __name__ == "__main__":
    import uvicorn
    logger.info("Customer Service Agent 시작")
    uvicorn.run(app, host=config.HOST, port=8001)
