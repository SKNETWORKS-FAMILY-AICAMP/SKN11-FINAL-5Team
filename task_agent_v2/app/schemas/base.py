"""
TinkerBell 프로젝트 - 기본 스키마
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Any, Dict, List
from datetime import datetime

from .enums import PersonaType, IntentType, TaskTopic, UrgencyLevel

class BaseSchema(BaseModel):
    """기본 스키마"""
    
    class Config:
        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True

class TimestampedSchema(BaseSchema):
    """타임스탬프가 포함된 스키마"""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

class UserQueryRequest(BaseSchema):
    """사용자 쿼리 요청"""
    user_id: str = Field(..., description="사용자 ID")
    conversation_id: Optional[str] = Field(None, description="대화 세션 ID")
    message: str = Field(..., min_length=1, max_length=2000, description="사용자 메시지")
    persona: PersonaType = Field(default=PersonaType.COMMON, description="사용자 페르소나")
    intent: Optional[IntentType] = Field(None, description="사용자 의도 (선택)")
    
    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('메시지는 빈 값일 수 없습니다.')
        return v.strip()

class UserQueryResponse(BaseSchema):
    """사용자 쿼리 응답"""
    status: str = Field(description="응답 상태")
    response: str = Field(description="응답 내용")
    conversation_id: str = Field(description="대화 세션 ID")
    intent: IntentType = Field(description="분석된 사용자 의도")
    urgency: UrgencyLevel = Field(description="긴급도")
    confidence: float = Field(ge=0.0, le=1.0, description="신뢰도")
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="후속 액션")
    knowledge_sources: List[str] = Field(default_factory=list, description="지식 소스")
    processing_time: Optional[float] = Field(None, description="처리 시간(초)")

class ConversationCreate(BaseSchema):
    """대화 세션 생성"""
    user_id: int = Field(..., gt=0, description="사용자 ID")

class ConversationResponse(TimestampedSchema):
    """대화 세션 응답"""
    conversation_id: int = Field(description="대화 세션 ID")
    user_id: int = Field(description="사용자 ID")
    started_at: datetime = Field(description="시작 시간")
    ended_at: Optional[datetime] = Field(None, description="종료 시간")
    is_visible: bool = Field(default=True, description="표시 여부")

class MessageCreate(BaseSchema):
    """메시지 생성"""
    conversation_id: int = Field(..., gt=0, description="대화 세션 ID")
    sender_type: str = Field(..., pattern="^(user|agent)$", description="발신자 타입")
    content: str = Field(..., min_length=1, max_length=5000, description="메시지 내용")
    agent_type: Optional[str] = Field(None, description="에이전트 타입")

class MessageResponse(TimestampedSchema):
    """메시지 응답"""
    message_id: int = Field(description="메시지 ID")
    conversation_id: int = Field(description="대화 세션 ID")
    sender_type: str = Field(description="발신자 타입")
    agent_type: Optional[str] = Field(description="에이전트 타입")
    content: str = Field(description="메시지 내용")

class UserCreate(BaseSchema):
    """사용자 생성"""
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$', description="이메일")
    password: str = Field(..., min_length=8, description="비밀번호")
    nickname: Optional[str] = Field(None, max_length=50, description="닉네임")
    business_type: Optional[str] = Field(None, max_length=100, description="사업 타입")

class UserLogin(BaseSchema):
    """사용자 로그인"""
    email: str = Field(..., description="이메일")
    password: str = Field(..., description="비밀번호")

class UserResponse(TimestampedSchema):
    """사용자 응답"""
    user_id: int = Field(description="사용자 ID")
    email: str = Field(description="이메일")
    nickname: Optional[str] = Field(description="닉네임")
    business_type: Optional[str] = Field(description="사업 타입")
    admin: bool = Field(description="관리자 여부")

class PaginationParams(BaseSchema):
    """페이지네이션 파라미터"""
    page: int = Field(default=1, ge=1, description="페이지 번호")
    per_page: int = Field(default=20, ge=1, le=100, description="페이지당 항목 수")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page

    @property 
    def limit(self) -> int:
        return self.per_page

class HealthResponse(BaseSchema):
    """헬스체크 응답"""
    service: str = Field(description="서비스 이름")
    version: str = Field(description="버전")
    status: str = Field(description="상태")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")
    components: Dict[str, Any] = Field(default_factory=dict, description="컴포넌트 상태")
    environment: Dict[str, Any] = Field(default_factory=dict, description="환경 정보")


# ===== RAG 데이터 모델 =====

class DocumentMetadata(BaseModel):
    doc_id: str
    chunk_id: int
    persona: PersonaType
    category: str
    topic: TaskTopic
    source: str
    last_updated: str

class KnowledgeChunk(BaseModel):
    content: str
    metadata: Dict[str, Any]
    relevance_score: float
    rank: int

class SearchResult(BaseModel):
    chunks: List[KnowledgeChunk]
    sources: List[str]
    total_results: int
