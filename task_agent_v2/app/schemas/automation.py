"""
TinkerBell 프로젝트 - 자동화 관련 스키마
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

from .base import BaseSchema, TimestampedSchema
from .enums import AutomationTaskType, AutomationStatus

class AutomationTaskCreate(BaseSchema):
    """자동화 작업 생성 요청"""
    user_id: int = Field(..., gt=0, description="사용자 ID")
    conversation_id: Optional[int] = Field(None, description="대화 세션 ID")
    task_type: AutomationTaskType = Field(description="자동화 작업 타입")
    title: str = Field(..., min_length=1, max_length=200, description="작업 제목")
    task_data: Dict[str, Any] = Field(description="작업 데이터")
    scheduled_at: Optional[datetime] = Field(None, description="예약 실행 시간")
    
    @validator('scheduled_at')
    def validate_scheduled_at(cls, v):
        if v and v < datetime.now():
            raise ValueError('예약 시간은 현재 시간보다 이후여야 합니다.')
        return v

class AutomationTaskResponse(TimestampedSchema):
    """자동화 작업 응답"""
    task_id: int = Field(description="작업 ID")
    user_id: int = Field(description="사용자 ID")
    conversation_id: Optional[int] = Field(description="대화 세션 ID")
    task_type: AutomationTaskType = Field(description="작업 타입")
    title: str = Field(description="작업 제목")
    status: AutomationStatus = Field(description="작업 상태")
    scheduled_at: Optional[datetime] = Field(description="예약 실행 시간")
    started_at: Optional[datetime] = Field(description="시작 시간")
    completed_at: Optional[datetime] = Field(description="완료 시간")
    error_message: Optional[str] = Field(description="오류 메시지")
    task_data: Optional[Dict[str, Any]] = Field(description="작업 데이터")
    execution_details: Optional[Dict[str, Any]] = Field(description="실행 상세")

class ScheduleInfo(BaseSchema):
    """일정 정보 스키마"""
    title: str = Field(..., description="일정 제목")
    start_time: str = Field(..., description="시작 시간 (ISO 형식)")
    end_time: Optional[str] = Field(None, description="종료 시간 (ISO 형식)")
    description: Optional[str] = Field(None, description="일정 설명")
    location: Optional[str] = Field(None, description="장소")
    calendar_id: str = Field(default="primary", description="캘린더 ID")
    timezone: str = Field(default="Asia/Seoul", description="시간대")
    reminders: List[Dict[str, Union[str, int]]] = Field(
        default_factory=lambda: [{"method": "popup", "minutes": 15}],
        description="리마인더 설정"
    )
    recurrence: Optional[List[str]] = Field(None, description="반복 설정")

class SNSInfo(BaseSchema):
    """SNS 발행 정보 스키마"""
    platform: str = Field(..., description="SNS 플랫폼")
    content: str = Field(..., min_length=1, max_length=2000, description="발행 내용")
    scheduled_time: Optional[str] = Field(None, description="예약 시간")
    hashtags: Optional[str] = Field(None, description="해시태그")
    image_url: Optional[str] = Field(None, description="이미지 URL")

class EmailInfo(BaseSchema):
    """이메일 정보 스키마"""
    to: str = Field(..., description="받는사람 이메일")
    subject: str = Field(..., min_length=1, max_length=200, description="제목")
    body: str = Field(..., min_length=1, description="본문")
    scheduled_time: Optional[str] = Field(None, description="예약 시간")
    cc: Optional[List[str]] = Field(None, description="참조")
    attachments: Optional[List[str]] = Field(None, description="첨부파일")

class ReminderInfo(BaseSchema):
    """리마인더 정보 스키마"""
    title: str = Field(..., min_length=1, max_length=200, description="제목")
    reminder_time: str = Field(..., description="알림 시간")
    description: Optional[str] = Field(None, description="내용")
    repeat: Optional[str] = Field("once", description="반복 설정")
    advance_notice: Optional[int] = Field(0, description="사전 알림(분)")

class MessageInfo(BaseSchema):
    """메시지 정보 스키마"""
    platform: str = Field(..., description="메시지 플랫폼")
    recipient: str = Field(..., description="받는사람")
    content: str = Field(..., min_length=1, max_length=1000, description="메시지 내용")
    scheduled_time: Optional[str] = Field(None, description="예약 시간")
    priority: Optional[str] = Field("medium", description="우선순위")

class AutomationTaskUpdate(BaseSchema):
    """자동화 작업 업데이트"""
    status: Optional[AutomationStatus] = Field(None, description="상태")
    scheduled_at: Optional[datetime] = Field(None, description="예약 시간")
    execution_details: Optional[Dict[str, Any]] = Field(None, description="실행 상세")

class AutomationTaskFilter(BaseSchema):
    """자동화 작업 필터"""
    task_type: Optional[List[AutomationTaskType]] = Field(None, description="작업 타입 목록")
    status: Optional[List[AutomationStatus]] = Field(None, description="상태 목록")
    conversation_id: Optional[int] = Field(None, description="대화 세션 ID")
    start_date: Optional[datetime] = Field(None, description="생성일 시작")
    end_date: Optional[datetime] = Field(None, description="생성일 종료")
    scheduled_from: Optional[datetime] = Field(None, description="예약 시간 시작")
    scheduled_to: Optional[datetime] = Field(None, description="예약 시간 종료")
    search: Optional[str] = Field(None, max_length=100, description="검색 키워드")

class AutomationAnalytics(BaseSchema):
    """자동화 분석"""
    total_tasks: int = Field(description="전체 작업 수")
    completed_tasks: int = Field(description="완료된 작업 수")
    failed_tasks: int = Field(description="실패한 작업 수")
    pending_tasks: int = Field(description="대기 중인 작업 수")
    success_rate: float = Field(ge=0.0, le=100.0, description="성공률")
    task_type_stats: Dict[str, Dict[str, int]] = Field(description="타입별 통계")

class AutomationBatchCreate(BaseSchema):
    """자동화 작업 일괄 생성"""
    tasks: List[AutomationTaskCreate] = Field(..., min_items=1, max_items=50, description="작업 목록")

class AutomationBatchResponse(BaseSchema):
    """자동화 작업 일괄 응답"""
    successful_tasks: List[AutomationTaskResponse] = Field(description="성공한 작업")
    failed_tasks: List[Dict[str, Any]] = Field(description="실패한 작업")
    summary: Dict[str, int] = Field(description="요약 정보")
