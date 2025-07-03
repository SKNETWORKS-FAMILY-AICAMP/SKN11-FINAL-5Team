"""
TinkerBell 프로젝트 - 기본 Enum 정의
"""

from enum import Enum

class PersonaType(str, Enum):
    """사용자 페르소나 타입"""
    CREATOR = "creator"
    BEAUTYSHOP = "beautyshop"
    E_COMMERCE = "e_commerce"
    SELF_EMPLOYMENT = "self_employment"
    DEVELOPER = "developer"
    COMMON = "common"

class TaskPriority(str, Enum):
    """작업 우선순위"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TaskStatus(str, Enum):
    """작업 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskTopic(str, Enum):
    """작업 주제"""
    TOOL_STACK = "tool_stack"
    SCHEDULE_MANAGEMENT = "schedule_management"
    TASK_PRIORITIZATION = "task_prioritization"
    TASK_AUTOMATION = "task_automation"
    GENERAL_INQUIRY = "general_inquiry"

class AutomationTaskType(str, Enum):
    """자동화 작업 타입"""
    SCHEDULE_CALENDAR = "schedule_calendar"
    PUBLISH_SNS = "publish_sns"
    SEND_EMAIL = "send_email"
    SEND_REMINDER = "send_reminder"
    SEND_MESSAGE = "send_message"

class AutomationStatus(str, Enum):
    """자동화 상태"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class IntentType(str, Enum):
    """사용자 의도 타입"""
    TOOL_STACK = "tool_stack"
    SCHEDULE_MANAGEMENT = "schedule_management"
    TASK_PRIORITIZATION = "task_prioritization"
    TASK_AUTOMATION = "task_automation"
    GENERAL_INQUIRY = "general_inquiry"

class UrgencyLevel(str, Enum):
    """긴급도 레벨"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
