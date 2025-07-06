"""
Customer Service Agent - 공통 모듈 사용 버전
기존 설정 파일들을 shared_modules로 대체
"""

import sys
import os

# 텔레메트리 비활성화 (ChromaDB 오류 방지)
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY'] = 'False' 
os.environ['DO_NOT_TRACK'] = '1'

from fastapi.responses import HTMLResponse
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared_modules.queries import get_business_type, get_template, insert_message_raw
from shared_modules import (
    get_config,
    get_llm,
    get_vectorstore,
    get_retriever,
    get_db_session
)

from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from customer_agent.agent_runner import run_customer_service_with_rag

from langchain_core.messages import HumanMessage,AIMessage
from customer_agent.graph import customer_workflow, CustomerAgentState 

# 로깅 설정
from shared_modules.logging_utils import setup_logging
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
class AgentQueryRequest(BaseModel):
    question: str
    customer_id: str = None
    conversation_id: int = None
    persona: str = None

class CustomerQueryResponse(BaseModel):
    answer: str
    intent: str = None
    confidence: float = None
    sources: str = None

# main.py
@app.post("/agent/query")
async def query_agent(request: AgentQueryRequest = Body(...)):
    try:
        # 1. 클라이언트에서 history를 받아옴 (DB X)
        history = []
        for msg in request.history:
            if msg["type"] == "human":
                history.append(HumanMessage(content=msg["content"]))
            elif msg["type"] == "ai":
                history.append(AIMessage(content=msg["content"]))
        
        business_type = get_business_type(request.user_id) or "common"
        logger.info(f"Business type for user {request.user_id}: {business_type}")

        insert_success = insert_message_raw(
            conversation_id=request.conversation_id,
            sender_type="user",
            agent_type="customer_agent",
            content=request.question
        )
        if not insert_success:
            logger.warning(f"Failed to insert user message for conversation {request.conversation_id}")


        # 2. 현재 질문 추가
        history.append(HumanMessage(content=request.question))

        # 3. 워크플로우 실행
        initial_state: CustomerAgentState = {
            "user_id": request.user_id,
            "conversation_id": request.conversation_id,
            "user_input": request.question,
            "business_type": business_type,
            "mode": "owner",
            "inquiry_type": "",
            "topics": [],
            "answer": "",
            "sources": "",
            "a2a_data": {},
            "history": history
        }
        final_state = customer_workflow.invoke(initial_state)

        # 4. 답변을 history에 추가
        history.append(AIMessage(content=final_state["answer"]))

        # 4. 에이전트 답변 저장
        insert_success = insert_message_raw(
            conversation_id=request.conversation_id,
            sender_type="agent",
            agent_type="customer_agent",
            content=final_state["answer"]
        )
        if not insert_success:
            logger.warning(f"Failed to insert agent response for conversation {request.conversation_id}")

        # 5. 결과 반환 (history도 함께 반환)
        return {
            "topics": final_state.get("topics", []),  
            "answer": final_state["answer"],
            "history": [
                {"type": "human" if isinstance(m, HumanMessage) else "ai", "content": m.content}
                for m in history
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/preview/{template_id}", response_class=HTMLResponse)
def preview_template(template_id: int):
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template["content_type"] != "html":
        raise HTTPException(status_code=400, detail="Not an HTML template")
    return HTMLResponse(content=template["content"])

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
