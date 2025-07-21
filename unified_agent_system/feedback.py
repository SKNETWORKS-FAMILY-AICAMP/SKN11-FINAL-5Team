import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Body, Depends, APIRouter, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, conint
import uvicorn
import sys
import os
from sqlalchemy.orm import Session
from datetime import datetime, timezone

# 공통 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared_modules.utils import utc_to_kst


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
    get_current_timestamp
)

from unified_agent_system.core.models import (
    UnifiedRequest, UnifiedResponse, HealthCheck, 
    AgentType, RoutingDecision
)
from unified_agent_system.core.workflow import get_workflow
from unified_agent_system.core.config import (
    SERVER_HOST, SERVER_PORT, DEBUG_MODE, 
    LOG_LEVEL, LOG_FORMAT
)
from shared_modules.database import get_session_context as unified_get_session_context
from shared_modules.queries import get_conversation_history
from shared_modules.utils import get_or_create_conversation_session, create_success_response as unified_create_success_response
from shared_modules.db_models import FAQ, Feedback

app = FastAPI()
router = APIRouter()


class FeedbackConvCreate(BaseModel):
    user_id: int
    conversation_id: int
    rating: conint(ge=1, le=5)
    comment: Optional[str] = None

# 메시지에 대한 피드백
class FeedbackChatCreate(BaseModel):
    user_id: int
    conversation_id: int
    message_id: int
    rating: conint(ge=1, le=5)
    comment: Optional[str] = None

@router.post("/create_conv", status_code=201)
def create_feedback_conv(feedback: FeedbackConvCreate):
    with get_session_context() as db:
        new_feedback = Feedback(
            user_id=feedback.user_id,
            conversation_id=feedback.conversation_id,
            rating=feedback.rating,
            comment=feedback.comment,
            created_at=utc_to_kst(datetime.utcnow())
        )
        db.add(new_feedback)
        db.commit()
        return {
            "success": True,
            "message": "채팅 피드백이 등록되었습니다"
        }


@router.post("/create_chat", status_code=201)
def create_feedback_chat(feedback: FeedbackChatCreate):
    with get_session_context() as db:
        new_feedback = Feedback(
            user_id=feedback.user_id,
            conversation_id=feedback.conversation_id,
            message_id=feedback.message_id,
            rating=feedback.rating,
            comment=feedback.comment,
            created_at=utc_to_kst(datetime.utcnow())
        )
        db.add(new_feedback)
        db.commit()
        return {
            "success": True,
            "message": "메시지 피드백이 등록되었습니다"
        }

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("feedback:app", host="127.0.0.1", port=8080, reload=True)
