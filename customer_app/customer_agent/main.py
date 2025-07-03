
import sys
import os
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage,AIMessage
from typing import Dict, Any
from fastapi.responses import HTMLResponse
# 로거 설정
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 프로젝트 루트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from MYSQL.queries import get_business_type, insert_message, get_messages_by_conversation, get_template_by_id
from customer_agent.graph import customer_workflow, CustomerAgentState  # LangGraph 임포트

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 요청 모델
class AgentQueryRequest(BaseModel):
    user_id: int
    conversation_id: int
    question: str
    history: List[Dict[str, Any]] = []  # 반드시 추가!


def load_initial_history(conversation_id: int, recent_turns: int = 5) -> list:
    db_messages = get_messages_by_conversation(conversation_id, recent_turns)
    langchain_messages = []
    for msg in db_messages:
        if msg["sender_type"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        elif msg["sender_type"] == "agent":
            langchain_messages.append(AIMessage(content=msg["content"]))
    return langchain_messages


# 헬스 체크 엔드포인트
@app.get("/health")
async def health_check():
    return {"status": "ok", "agent": "customer_agent"}


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

        insert_success = insert_message(
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
        insert_success = insert_message(
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
    template = get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template["content_type"] != "html":
        raise HTTPException(status_code=400, detail="Not an HTML template")
    return HTMLResponse(content=template["content"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "customer_agent.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,
        reload_dirs=["."]
    )
