
# /app/services/improved_automation_service.py
"""
개선된 자동화 서비스 (중복 제거 및 통합)
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.exceptions import AutomationError, ValidationError, not_found_error
from ..schemas.automation import (
    AutomationTaskCreate, AutomationTaskResponse, AutomationTaskUpdate,
    AutomationTaskFilter, AutomationAnalytics
)
from ..schemas.enums import AutomationStatus, AutomationTaskType
from ..schemas.db_models import AutomationTask, User, Conversation

from .common.base_service import BaseService
from .google_calendar_service import GoogleCalendarService
from .reminder_service import ReminderService
from .email_service import EmailService
from .sms_service import SMSService

class ImprovedAutomationService(BaseService):
    """개선된 자동화 관리 서비스"""
    
    def __init__(self, db_session: Session, service_config: Optional[Dict[str, Any]] = None):
        super().__init__(db_session, service_config or {})
        
        # 통합 서비스들 초기화
        self._init_services()
        
        self.logger.info("개선된 자동화 서비스 초기화 완료")
    
    def _init_services(self):
        """통합 서비스들 초기화"""
        try:
            # Google Calendar 서비스
            self.calendar_service = GoogleCalendarService(self.db, self.config)
            
            # 리마인더 서비스 (통합 알림 포함)
            self.reminder_service = ReminderService(self.db, self.config)
            
            # 이메일 서비스
            self.email_service = EmailService(self.db, self.config)
            
            # SMS 서비스
            self.sms_service = SMSService(self.db, self.config)
            
            self.logger.info("모든 서비스 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"서비스 초기화 중 오류: {e}")
            # 실패해도 계속 진행 (개별 서비스에서 사용 가능 여부 확인)
    
    async def create_task(self, task_data: AutomationTaskCreate) -> AutomationTaskResponse:
        """자동화 작업 생성"""
        try:
            # 입력 데이터 검증
            self._validate_task_data(task_data)
            
            # 사용자 존재 확인
            user = self.db.query(User).filter(User.user_id == task_data.user_id).first()
            if not user:
                raise not_found_error("사용자", str(task_data.user_id))
            
            # DB에 자동화 작업 생성
            db_task = AutomationTask(
                user_id=task_data.user_id,
                conversation_id=task_data.conversation_id,
                task_type=task_data.task_type,
                title=task_data.title,
                task_data=task_data.task_data,
                status=AutomationStatus.PENDING.value,
                scheduled_at=task_data.scheduled_at
            )
            
            self.db.add(db_task)
            self.db.commit()
            self.db.refresh(db_task)
            
            return self._task_to_response(db_task)
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"자동화 작업 생성 실패: {e}")
            if "not found" in str(e).lower():
                raise
            raise AutomationError(f"자동화 작업 생성 중 오류 발생: {e}", getattr(task_data, 'task_type', 'unknown'))
    
    async def execute_task(self, task_id: int) -> Dict[str, Any]:
        """자동화 작업 즉시 실행"""
        try:
            # 작업 정보 조회
            db_task = self.db.query(AutomationTask).filter(
                AutomationTask.task_id == task_id
            ).first()
            
            if not db_task:
                raise not_found_error("자동화 작업", str(task_id))
            
            # 실행 가능한 상태인지 확인
            current_status = AutomationStatus(db_task.status)
            if current_status not in [AutomationStatus.PENDING, AutomationStatus.SCHEDULED]:
                raise AutomationError("실행할 수 없는 작업 상태입니다.")
            
            # 상태를 RUNNING으로 변경
            db_task.status = AutomationStatus.RUNNING.value
            db_task.executed_at = datetime.now()
            self.db.commit()
            
            # task_type에 따른 실제 실행 로직
            task_type = AutomationTaskType(db_task.task_type)
            task_data = db_task.task_data or {}
            
            try:
                if task_type == AutomationTaskType.SCHEDULE_CALENDAR:
                    execution_result = await self._execute_calendar_task(db_task.user_id, task_data)
                
                elif task_type == AutomationTaskType.SEND_EMAIL:
                    execution_result = await self._execute_email_task(task_data)
                
                elif task_type == AutomationTaskType.SEND_REMINDER:
                    execution_result = await self._execute_reminder_task(db_task.user_id, task_data)
                
                elif task_type == AutomationTaskType.SEND_MESSAGE:
                    execution_result = await self._execute_message_task(task_data)
                
                else:
                    execution_result = {
                        "success": False,
                        "error": f"지원하지 않는 작업 타입: {task_type}"
                    }
                
                # 실행 결과에 따른 상태 업데이트
                if execution_result.get("success"):
                    db_task.status = AutomationStatus.COMPLETED.value
                    final_status = "completed"
                else:
                    db_task.status = AutomationStatus.FAILED.value
                    final_status = "failed"
                
                # 실행 상세 정보 저장
                if db_task.task_data is None:
                    db_task.task_data = {}
                db_task.task_data["execution_details"] = execution_result
                db_task.task_data["executed_at"] = datetime.now().isoformat()
                
                self.db.commit()
                
                self.logger.info(f"자동화 작업 실행 완료: {task_id} - {final_status}")
                
                return {
                    "task_id": task_id,
                    "status": final_status,
                    "message": "작업이 실행되었습니다." if execution_result.get("success") else "작업 실행에 실패했습니다.",
                    "execution_details": execution_result
                }
                
            except Exception as execution_error:
                # 실행 중 오류 발생
                db_task.status = AutomationStatus.FAILED.value
                if db_task.task_data is None:
                    db_task.task_data = {}
                db_task.task_data["execution_details"] = {
                    "success": False,
                    "error": str(execution_error),
                    "executed_at": datetime.now().isoformat()
                }
                self.db.commit()
                
                self.logger.error(f"자동화 작업 실행 중 오류: {task_id} - {execution_error}")
                
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "message": "작업 실행 중 오류가 발생했습니다.",
                    "execution_details": {
                        "success": False,
                        "error": str(execution_error)
                    }
                }
            
        except (AutomationError, Exception) as e:
            self.db.rollback()
            if "not found" in str(e).lower() or isinstance(e, AutomationError):
                raise
            self.logger.error(f"자동화 작업 실행 실패: {e}")
            raise AutomationError(f"작업 실행 중 오류 발생: {e}")
    
    # ===== Task Type별 실행 메서드들 (통합 서비스 사용) =====
    
    async def _execute_calendar_task(self, user_id: int, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """구글 캘린더 일정 생성 (개선된 서비스 사용)"""
        try:
            # 필수 필드 검증
            required_fields = ["title", "start_time"]
            for field in required_fields:
                if field not in task_data:
                    return {"success": False, "error": f"필수 필드가 누락되었습니다: {field}"}
            
            # 리마인더 설정이 있는 경우
            reminder_settings = task_data.get("reminder_settings")
            
            if reminder_settings:
                # 리마인더가 포함된 이벤트 생성
                result = await self.calendar_service.create_event_with_reminder(
                    user_id, task_data, reminder_settings
                )
            else:
                # 기본 이벤트 생성
                result = await self.calendar_service.create_event(user_id, task_data)
            
            if result.get("success"):
                return {
                    "success": True,
                    "event_id": result.get("event_id"),
                    "event_link": result.get("event_link"),
                    "message": "구글 캘린더 일정이 성공적으로 생성되었습니다."
                }
            else:
                return {"success": False, "error": result.get("error", "알 수 없는 오류")}
                
        except Exception as e:
            self.logger.error(f"캘린더 작업 실행 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_email_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """이메일 발송 (통합 이메일 서비스 사용)"""
        try:
            # 필수 필드 검증
            required_fields = ["to", "subject", "body"]
            for field in required_fields:
                if field not in task_data:
                    return {"success": False, "error": f"필수 필드가 누락되었습니다: {field}"}
            
            # 이메일 발송
            result = await self.email_service.send_email(
                to_emails=[task_data["to"]] if isinstance(task_data["to"], str) else task_data["to"],
                subject=task_data["subject"],
                body=task_data["body"],
                html_body=task_data.get("html_body"),
                attachments=task_data.get("attachments"),
                cc_emails=task_data.get("cc"),
                bcc_emails=task_data.get("bcc"),
                from_email=task_data.get("from_email"),
                from_name=task_data.get("from_name")
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "message_id": result.get("message_id"),
                    "recipients_count": result.get("recipients_count"),
                    "message": "이메일이 성공적으로 발송되었습니다."
                }
            else:
                return {"success": False, "error": result.get("error", "알 수 없는 오류")}
                
        except Exception as e:
            self.logger.error(f"이메일 작업 실행 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_reminder_task(self, user_id: int, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """리마인더 발송 (통합 리마인더 서비스 사용)"""
        try:
            # 필수 필드 검증
            required_fields = ["title"]
            for field in required_fields:
                if field not in task_data:
                    return {"success": False, "error": f"필수 필드가 누락되었습니다: {field}"}
            
            title = task_data["title"]
            reminder_types = task_data.get("types", ["app"])  # 기본값: 앱 알림
            urgency = task_data.get("urgency", "medium")
            task_id = task_data.get("task_id")
            
            # 통합 리마인더 서비스 사용
            result = await self.reminder_service.send_reminder(
                user_id=user_id,
                message=title,
                reminder_types=reminder_types,
                urgency=urgency,
                task_id=task_id,
                additional_data=task_data
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "sent_count": result.get("sent_count"),
                    "failed_count": result.get("failed_count"),
                    "message": f"리마인더가 {result.get('sent_count')}개 채널로 발송되었습니다."
                }
            else:
                return {"success": False, "error": result.get("error", "알 수 없는 오류")}
                
        except Exception as e:
            self.logger.error(f"리마인더 작업 실행 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_message_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """메시지 발송 (통합 리마인더 서비스의 메시징 기능 사용)"""
        try:
            # 필수 필드 검증
            required_fields = ["platform", "content"]
            for field in required_fields:
                if field not in task_data:
                    return {"success": False, "error": f"필수 필드가 누락되었습니다: {field}"}
            
            platform = task_data["platform"].lower()
            content = task_data["content"]
            channel = task_data.get("channel")
            recipients = task_data.get("recipients", [])
            webhook_url = task_data.get("webhook_url")
            
            # 통합 리마인더 서비스의 메시징 기능 사용
            result = await self.reminder_service.send_message_to_platform(
                platform=platform,
                message=content,
                channel=channel,
                recipients=recipients,
                webhook_url=webhook_url
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "platform": platform,
                    "message": f"{platform} 메시지가 성공적으로 발송되었습니다.",
                    "details": result
                }
            else:
                return {"success": False, "error": result.get("error", "알 수 없는 오류")}
                
        except Exception as e:
            self.logger.error(f"메시지 작업 실행 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def _validate_task_data(self, task_data: AutomationTaskCreate):
        """자동화 작업 데이터 검증"""
        # 작업 타입별 필수 데이터 검증
        required_fields = {
            AutomationTaskType.SCHEDULE_CALENDAR: ["title", "start_time"],
            AutomationTaskType.SEND_EMAIL: ["to", "subject", "body"],
            AutomationTaskType.SEND_REMINDER: ["title"],
            AutomationTaskType.SEND_MESSAGE: ["platform", "content"]
        }
        
        task_required_fields = required_fields.get(task_data.task_type, [])
        
        for field in task_required_fields:
            if field not in task_data.task_data or not task_data.task_data[field]:
                raise ValidationError(
                    f"{task_data.task_type} 작업에는 '{field}' 필드가 필요합니다.",
                    field=field
                )
        
        # 날짜/시간 형식 검증
        if task_data.task_type == AutomationTaskType.SCHEDULE_CALENDAR:
            start_time = task_data.task_data.get("start_time")
            if start_time:
                try:
                    datetime.fromisoformat(start_time.replace("T", " "))
                except ValueError:
                    raise ValidationError("start_time은 유효한 ISO 형식이어야 합니다.", field="start_time")
    
    def _task_to_response(self, db_task: AutomationTask) -> AutomationTaskResponse:
        """DB 모델을 응답 스키마로 변환"""
        execution_details = None
        if db_task.task_data and "execution_details" in db_task.task_data:
            execution_details = db_task.task_data["execution_details"]
        
        # 오류 메시지 추출
        error_message = None
        if db_task.status == AutomationStatus.FAILED.value:
            if db_task.task_data:
                if "error" in db_task.task_data:
                    error_message = db_task.task_data["error"]
                elif execution_details and "error" in execution_details:
                    error_message = execution_details["error"]
        
        return AutomationTaskResponse(
            task_id=db_task.task_id,
            user_id=db_task.user_id,
            conversation_id=db_task.conversation_id,
            task_type=AutomationTaskType(db_task.task_type),
            title=db_task.title,
            status=AutomationStatus(db_task.status),
            scheduled_at=db_task.scheduled_at,
            started_at=db_task.executed_at,
            completed_at=db_task.executed_at if db_task.status in ['completed', 'failed'] else None,
            error_message=error_message,
            created_at=db_task.created_at,
            task_data=db_task.task_data,
            execution_details=execution_details
        )
    
    async def get_service_status(self) -> Dict[str, Any]:
        """전체 서비스 상태 조회"""
        try:
            calendar_status = await self.calendar_service.get_service_status()
            reminder_status = await self.reminder_service.get_service_status()
            email_status = await self.email_service.get_service_status()
            sms_status = await self.sms_service.get_service_status()
            
            return {
                "service": "improved_automation_service",
                "status": "healthy",
                "components": {
                    "calendar_service": calendar_status["status"],
                    "reminder_service": reminder_status["status"],
                    "email_service": email_status["status"],
                    "sms_service": sms_status["status"]
                }
            }
        except Exception as e:
            self.logger.error(f"자동화 서비스 상태 조회 실패: {e}")
            return {"service": "improved_automation_service", "status": "error", "error": str(e)}
    
    async def cleanup(self):
        """서비스 정리"""
        try:
            await self.calendar_service.cleanup()
            await self.reminder_service.cleanup()
            await self.email_service.cleanup()
            await self.sms_service.cleanup()
            self.logger.info("개선된 자동화 서비스 정리 완료")
        except Exception as e:
            self.logger.error(f"자동화 서비스 정리 실패: {e}")