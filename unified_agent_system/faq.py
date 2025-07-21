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

class FAQCreate(BaseModel):
    category: str
    question: str
    answer: str

@router.post("/create")
def create_faq(data: FAQCreate, db: Session = Depends(unified_get_session_context)):
    new_faq = FAQ(
        category=data.category,
        question=data.question,
        answer=data.answer,
        view_count=0,
        is_active=True,
        created_at=utc_to_kst(datetime.utcnow())
    )
    db.add(new_faq)
    db.commit()
    db.refresh(new_faq)
    return {"success": True, "message": "FAQ가 등록되었습니다", "faq_id": new_faq.faq_id}

@router.get("/get")
def get_faq_list(
    category: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    db: Session = Depends(unified_get_session_context)
):
    query = db.query(FAQ)

    if category:
        query = query.filter(FAQ.category == category)
    if search:
        search_term = f"%{search}%"
        query = query.filter(FAQ.question.ilike(search_term))

    total = query.count()
    faqs = query.offset((page - 1) * limit).limit(limit).all()

    # FAQ 카테고리 목록 추출 (distinct)
    categories = db.query(FAQ.category).distinct().all()
    categories = [c[0] for c in categories]

    return {
        "success": True,
        "data": {
            "faqs": [
                {
                    "faq_id": f.faq_id,
                    "category": f.category,
                    "question": f.question,
                    "answer": f.answer,
                    "view_count": f.view_count,
                    "is_helpful": f.is_helpful
                } for f in faqs
            ],
            "categories": categories,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total
            }
        }
    }
    