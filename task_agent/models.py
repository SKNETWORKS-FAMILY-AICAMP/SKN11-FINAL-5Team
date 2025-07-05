"""
간소화된 데이터 모델 v3
"""

from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

# ===== 기본 Enum =====

class PersonaType(str, Enum):
    CREATOR = "creator"
    BEAUTYSHOP = "beautyshop"
    E_COMMERCE = "e_commerce"
    SELF_EMPLOYMENT = "self_employment" 
    DEVELOPER = "developer"
    COMMON = "common"

class TaskPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class AutomationTaskType(str, Enum):
    SCHEDULE_CALENDAR = "schedule_calendar"
    PUBLISH_SNS = "publish_sns"
    SEND_EMAIL = "send_email"
    SEND_REMINDER = "send_reminder"
    SEND_MESSAGE = "send_message"

class AutomationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

# ===== 요청/응답 모델 =====

class UserQuery(BaseModel):
    user_id: str
    conversation_id: Optional[str] = None
    message: str
    persona: PersonaType = PersonaType.COMMON

class QueryResponse(BaseModel):
    status: str
    response: str
    conversation_id: str
    intent: str
    urgency: str = "medium"
    confidence: float = 0.5
    actions: List[Dict[str, Any]] = []
    sources: List[str] = []

class TaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None

class AutomationRequest(BaseModel):
    user_id: int
    task_type: AutomationTaskType
    title: str
    task_data: Dict[str, Any]
    scheduled_at: Optional[datetime] = None

class AutomationResponse(BaseModel):
    task_id: int
    status: str
    message: str
    scheduled_time: Optional[datetime] = None

# ===== 내부 모델 =====

class KnowledgeChunk(BaseModel):
    content: str
    metadata: Dict[str, Any]
    relevance_score: float

class SearchResult(BaseModel):
    chunks: List[KnowledgeChunk]
    sources: List[str]
    total_results: int
