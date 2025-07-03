"""
TinkerBell 프로젝트 - 통합된 자동화 서비스
기존 코드의 비즈니스 로직을 유지하면서 새로운 통합 구조를 적용
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.exceptions import AutomationError, ValidationError, not_found_error
from ..schemas.automation import (
    AutomationTaskCreate, AutomationTaskResponse, AutomationTaskUpdate,
    AutomationTaskFilter, AutomationAnalytics
)
from ..schemas.enums import AutomationStatus, AutomationTaskType
from ..schemas.db_models import AutomationTask, User, Conversation

# 새로운 통합 서비스들 import
from .common.base_service import BaseService
from .common.user_service import UserService
from .common.config_service import ConfigService
from .common.notification_service import NotificationService
from .email_service import EmailService
from .sms_service import SMSService
from .google_calendar_service import GoogleCalendarService
from .reminder_service import ReminderService

logger = logging.getLogger(__name__)

class AutomationService(BaseService):
    """자동화 관리 서비스 (통합 구조 적용)"""
    
    def __init__(self, db_session: Session, service_config: Optional[Dict[str, Any]] = None):
        """서비스 초기화"""
        super().__init__(db_session, service_config)
        
        # 통합 서비스들 초기화
        self._init_integrated_services()
        
        self.logger.info("자동화 서비스 초기화 완료 (통합 구조)")
    
    def _init_integrated_services(self):
        """통합 서비스들 초기화"""
        try:
            # 공통 서비스들
            self.user_service = UserService(self.db, self.config)
            self.config_service = ConfigService(self.db, self.config)
            self.notification_service = NotificationService(self.db, self.config)
            
            # 특화 서비스들
            self.email_service = EmailService(self.db, self.config)
            self.sms_service = SMSService(self.db, self.config)
            self.reminder_service = ReminderService(self.db, self.config)
            
            # Google Calendar 서비스 (조건부 초기화)
            if self.config_service.is_service_enabled("google_calendar"):
                self.calendar_service = GoogleCalendarService(self.db, self.config)
            else:
                self.calendar_service = None
                self.logger.warning("Google Calendar 서비스가 비활성화되어 있습니다.")
            
            # SNS 서비스는 별도 구현이 필요한 경우에만 추가
            self.sns_service = None  # 추후 구현 시 추가
                
        except Exception as e:
            self.logger.error(f"통합 서비스 초기화 중 오류: {e}")
            # 실패해도 계속 진행 (개별 서비스에서 사용 가능 여부 확인)
    
    async def create_task(self, task_data: AutomationTaskCreate) -> AutomationTaskResponse:
        """자동화 작업 생성"""
        try:
            # 입력 데이터 검증
            self._validate_task_data(task_data)
            
            # 사용자 존재 확인 (통합 서비스 사용)
            user_info = await self.user_service.get_user_info(task_data.user_id)
            if not user_info:
                raise not_found_error("사용자", str(task_data.user_id))
            
            # 대화 세션 존재 확인 (선택적)
            if task_data.conversation_id:
                conversation = self.db.query(Conversation).filter(
                    Conversation.conversation_id == task_data.conversation_id
                ).first()
                if not conversation:
                    raise not_found_error("대화 세션", str(task_data.conversation_id))
            
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
    
    async def get_task(self, task_id: int) -> AutomationTaskResponse:
        """자동화 작업 조회"""
        try:
            db_task = self.db.query(AutomationTask).filter(
                AutomationTask.task_id == task_id
            ).first()
            
            if not db_task:
                raise not_found_error("자동화 작업", str(task_id))
            
            return self._task_to_response(db_task)
            
        except Exception as e:
            if "not found" in str(e).lower():
                raise
            self.logger.error(f"자동화 작업 조회 실패: {e}")
            raise AutomationError(f"자동화 작업 조회 중 오류 발생: {e}")
    
    async def update_task(self, task_id: int, update_data: AutomationTaskUpdate) -> AutomationTaskResponse:
        """자동화 작업 업데이트"""
        try:
            # 기존 작업 조회
            db_task = self.db.query(AutomationTask).filter(
                AutomationTask.task_id == task_id
            ).first()
            
            if not db_task:
                raise not_found_error("자동화 작업", str(task_id))
            
            # 업데이트 가능한 필드들만 처리
            updated = False
            if update_data.status:
                db_task.status = update_data.status.value
                updated = True
                
                # 상태에 따른 실행 시간 업데이트
                if update_data.status == AutomationStatus.RUNNING and not db_task.executed_at:
                    db_task.executed_at = datetime.now()
                elif update_data.status in [AutomationStatus.COMPLETED, AutomationStatus.FAILED]:
                    if not db_task.executed_at:
                        db_task.executed_at = datetime.now()
            
            if update_data.scheduled_at:
                db_task.scheduled_at = update_data.scheduled_at
                updated = True
            
            if update_data.execution_details:
                # task_data에 execution_details 추가
                if db_task.task_data is None:
                    db_task.task_data = {}
                db_task.task_data["execution_details"] = update_data.execution_details
                updated = True
            
            if updated:
                self.db.commit()
                self.db.refresh(db_task)
            
            return self._task_to_response(db_task)
            
        except Exception as e:
            self.db.rollback()
            if "not found" in str(e).lower():
                raise
            self.logger.error(f"자동화 작업 업데이트 실패: {e}")
            raise AutomationError(f"자동화 작업 업데이트 중 오류 발생: {e}")
    
    async def cancel_task(self, task_id: int) -> bool:
        """자동화 작업 취소"""
        try:
            db_task = self.db.query(AutomationTask).filter(
                AutomationTask.task_id == task_id
            ).first()
            
            if not db_task:
                raise not_found_error("자동화 작업", str(task_id))
            
            # 취소 가능한 상태인지 확인
            current_status = AutomationStatus(db_task.status)
            if current_status not in [AutomationStatus.PENDING, AutomationStatus.SCHEDULED]:
                raise AutomationError("작업을 취소할 수 없습니다. 이미 실행 중이거나 완료된 작업입니다.")
            
            # 상태를 CANCELLED로 변경
            db_task.status = AutomationStatus.CANCELLED.value
            self.db.commit()
            
            return True
            
        except (AutomationError, Exception) as e:
            self.db.rollback()
            if "not found" in str(e).lower() or isinstance(e, AutomationError):
                raise
            self.logger.error(f"자동화 작업 취소 실패: {e}")
            raise AutomationError(f"자동화 작업 취소 중 오류 발생: {e}")
    
    async def get_user_tasks(
        self, 
        user_id: int, 
        task_filter: Optional[AutomationTaskFilter] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[AutomationTaskResponse]:
        """사용자의 자동화 작업 목록 조회"""
        try:
            # 기본 쿼리
            query = self.db.query(AutomationTask).filter(
                AutomationTask.user_id == user_id
            )
            
            # 필터 적용
            if task_filter:
                if task_filter.status:
                    query = query.filter(
                        AutomationTask.status.in_([s.value for s in task_filter.status])
                    )
                
                if task_filter.task_type:
                    query = query.filter(
                        AutomationTask.task_type.in_([t.value for t in task_filter.task_type])
                    )
                
                if task_filter.conversation_id:
                    query = query.filter(
                        AutomationTask.conversation_id == task_filter.conversation_id
                    )
                
                if task_filter.start_date:
                    query = query.filter(
                        AutomationTask.created_at >= task_filter.start_date
                    )
                
                if task_filter.end_date:
                    query = query.filter(
                        AutomationTask.created_at <= task_filter.end_date
                    )
            
            # 정렬 및 페이징
            tasks = query.order_by(
                AutomationTask.created_at.desc()
            ).offset(offset).limit(limit).all()
            
            return [self._task_to_response(task) for task in tasks]
            
        except Exception as e:
            self.logger.error(f"사용자 자동화 작업 목록 조회 실패: {e}")
            raise AutomationError(f"작업 목록 조회 중 오류 발생: {e}")
    
    async def execute_task(self, task_id: int) -> Dict[str, Any]:
        """자동화 작업 즉시 실행 (통합 서비스 사용)"""
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
            
            # task_type에 따른 실제 실행 로직 (통합 서비스 사용)
            task_type = AutomationTaskType(db_task.task_type)
            task_data = db_task.task_data or {}
            
            try:
                if task_type == AutomationTaskType.SCHEDULE_CALENDAR:
                    execution_result = await self._execute_calendar_task(db_task.user_id, task_data)
                
                elif task_type == AutomationTaskType.SEND_EMAIL:
                    execution_result = await self._execute_email_task(task_data)
                
                elif task_type == AutomationTaskType.PUBLISH_SNS:
                    execution_result = await self._execute_sns_task(db_task.user_id, task_data)
                
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
    
    async def schedule_task(self, task_id: int, scheduled_at: datetime) -> bool:
        """자동화 작업 스케줄링"""
        try:
            # 작업 정보 조회
            db_task = self.db.query(AutomationTask).filter(
                AutomationTask.task_id == task_id
            ).first()
            
            if not db_task:
                raise not_found_error("자동화 작업", str(task_id))
            
            # 스케줄링 가능한 상태인지 확인
            current_status = AutomationStatus(db_task.status)
            if current_status != AutomationStatus.PENDING:
                raise AutomationError("스케줄링할 수 없는 작업 상태입니다.")
            
            # 미래 시간인지 확인
            if scheduled_at <= datetime.now():
                raise ValidationError("스케줄 시간은 현재 시간보다 이후여야 합니다.")
            
            # 스케줄 정보 업데이트
            db_task.scheduled_at = scheduled_at
            db_task.status = AutomationStatus.SCHEDULED.value
            self.db.commit()
            
            self.logger.info(f"자동화 작업 스케줄링 완료: {task_id}, {scheduled_at}")
            
            return True
            
        except (AutomationError, ValidationError, Exception) as e:
            self.db.rollback()
            if "not found" in str(e).lower() or isinstance(e, (AutomationError, ValidationError)):
                raise
            self.logger.error(f"자동화 작업 스케줄링 실패: {e}")
            raise AutomationError(f"작업 스케줄링 중 오류 발생: {e}")
    
    # ===== Task Type별 실행 메서드들 (통합 서비스 사용) =====
    
    async def _execute_calendar_task(self, user_id: int, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """구글 캘린더 일정 생성 (통합 서비스 사용)"""
        try:
            if not self.calendar_service:
                return {
                    "success": False,
                    "error": "Google Calendar 서비스가 설정되지 않았습니다."
                }
            
            # 필수 필드 검증
            required_fields = ["title", "start_time"]
            for field in required_fields:
                if field not in task_data:
                    return {
                        "success": False,
                        "error": f"필수 필드가 누락되었습니다: {field}"
                    }
            
            # 리마인더 설정이 있는 경우 고급 이벤트 생성 사용
            reminder_settings = task_data.get("reminder_settings")
            
            if reminder_settings:
                # 리마인더가 포함된 이벤트 생성 (통합 서비스 활용)
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
                return {
                    "success": False,
                    "error": result.get("error", "알 수 없는 오류")
                }
                
        except Exception as e:
            self.logger.error(f"캘린더 작업 실행 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_email_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """이메일 발송 (통합 이메일 서비스 사용)"""
        try:
            # 필수 필드 검증
            required_fields = ["to", "subject", "body"]
            for field in required_fields:
                if field not in task_data:
                    return {
                        "success": False,
                        "error": f"필수 필드가 누락되었습니다: {field}"
                    }
            
            # 통합 이메일 서비스 사용
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
                    "service": result.get("service", "email"),
                    "message": "이메일이 성공적으로 발송되었습니다."
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "알 수 없는 오류")
                }
                
        except Exception as e:
            self.logger.error(f"이메일 작업 실행 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_sns_task(self, user_id: int, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """SNS 게시물 발행 (추후 SNS 서비스 통합 시 업데이트)"""
        try:
            if not self.sns_service:
                return {
                    "success": False,
                    "error": "SNS 서비스가 구현되지 않았습니다. 추후 업데이트 예정입니다."
                }
            
            # 필수 필드 검증
            required_fields = ["platform", "content"]
            for field in required_fields:
                if field not in task_data:
                    return {
                        "success": False,
                        "error": f"필수 필드가 누락되었습니다: {field}"
                    }
            
            # SNS 서비스 로직 (추후 구현)
            # platform = task_data["platform"]
            # content = task_data["content"]
            # ... SNS 발행 로직
            
            return {
                "success": False,
                "error": "SNS 게시물 발행 기능은 현재 개발 중입니다."
            }
                
        except Exception as e:
            self.logger.error(f"SNS 작업 실행 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_reminder_task(self, user_id: int, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """리마인더 발송 (통합 리마인더 서비스 사용)"""
        try:
            # 필수 필드 검증
            required_fields = ["title"]
            for field in required_fields:
                if field not in task_data:
                    return {
                        "success": False,
                        "error": f"필수 필드가 누락되었습니다: {field}"
                    }
            
            title = task_data["title"]
            reminder_types = task_data.get("types", task_data.get("type", ["app"]))
            
            # 타입이 단일 문자열인 경우 리스트로 변환
            if isinstance(reminder_types, str):
                if reminder_types == "all":
                    reminder_types = ["app", "email", "sms"]
                else:
                    reminder_types = [reminder_types]
            
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
                    "results": result.get("results", []),
                    "message": f"리마인더가 {result.get('sent_count')}개 채널로 발송되었습니다."
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "리마인더 발송에 실패했습니다."),
                    "results": result.get("results", [])
                }
                
        except Exception as e:
            self.logger.error(f"리마인더 작업 실행 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_message_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """메시지 발송 (통합 리마인더 서비스의 메시징 기능 사용)"""
        try:
            # 필수 필드 검증
            required_fields = ["platform", "content"]
            for field in required_fields:
                if field not in task_data:
                    return {
                        "success": False,
                        "error": f"필수 필드가 누락되었습니다: {field}"
                    }
            
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
                return {
                    "success": False,
                    "error": result.get("error", "알 수 없는 오류")
                }
                
        except Exception as e:
            self.logger.error(f"메시지 작업 실행 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_task_data(self, task_data: AutomationTaskCreate):
        """자동화 작업 데이터 검증"""
        # 작업 타입별 필수 데이터 검증
        required_fields = {
            AutomationTaskType.SCHEDULE_CALENDAR: ["title", "start_time"],
            AutomationTaskType.PUBLISH_SNS: ["platform", "content"],
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
        
        # 오류 메시지 추출 (task_data나 execution_details에서)
        error_message = None
        if db_task.status == AutomationStatus.FAILED.value:
            if db_task.task_data:
                if "error" in db_task.task_data:
                    error_message = db_task.task_data["error"]
                elif execution_details and "error" in execution_details:
                    error_message = execution_details["error"]
                elif "execution_details" in db_task.task_data and isinstance(db_task.task_data["execution_details"], dict):
                    error_message = db_task.task_data["execution_details"].get("error")
        
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
    
    async def get_task_analytics(self, user_id: int) -> AutomationAnalytics:
        """자동화 작업 분석 데이터 조회"""
        try:
            # 사용자의 모든 작업 조회
            tasks = self.db.query(AutomationTask).filter(
                AutomationTask.user_id == user_id
            ).all()
            
            # 통계 계산
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.status == AutomationStatus.COMPLETED.value])
            failed_tasks = len([t for t in tasks if t.status == AutomationStatus.FAILED.value])
            pending_tasks = len([t for t in tasks if t.status == AutomationStatus.PENDING.value])
            
            # 타입별 통계
            task_type_stats = {}
            for task in tasks:
                task_type = task.task_type
                if task_type not in task_type_stats:
                    task_type_stats[task_type] = {"total": 0, "completed": 0, "failed": 0}
                task_type_stats[task_type]["total"] += 1
                if task.status == AutomationStatus.COMPLETED.value:
                    task_type_stats[task_type]["completed"] += 1
                elif task.status == AutomationStatus.FAILED.value:
                    task_type_stats[task_type]["failed"] += 1
            
            success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            return AutomationAnalytics(
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
                pending_tasks=pending_tasks,
                success_rate=round(success_rate, 2),
                task_type_stats=task_type_stats
            )
            
        except Exception as e:
            self.logger.error(f"자동화 작업 분석 조회 실패: {e}")
            raise AutomationError(f"분석 데이터 조회 중 오류 발생: {e}")
    
    async def get_service_status(self) -> Dict[str, Any]:
        """서비스 상태 조회 (통합 서비스들 포함)"""
        try:
            # 각 통합 서비스의 상태 확인
            components_status = {}
            
            try:
                user_status = await self.user_service.get_service_status()
                components_status["user_service"] = user_status["status"]
            except:
                components_status["user_service"] = "error"
            
            try:
                config_status = await self.config_service.get_service_status()
                components_status["config_service"] = config_status["status"]
            except:
                components_status["config_service"] = "error"
            
            try:
                notification_status = await self.notification_service.get_service_status()
                components_status["notification_service"] = notification_status["status"]
            except:
                components_status["notification_service"] = "error"
            
            try:
                email_status = await self.email_service.get_service_status()
                components_status["email_service"] = email_status["status"]
            except:
                components_status["email_service"] = "error"
            
            try:
                reminder_status = await self.reminder_service.get_service_status()
                components_status["reminder_service"] = reminder_status["status"]
            except:
                components_status["reminder_service"] = "error"
            
            if self.calendar_service:
                try:
                    calendar_status = await self.calendar_service.get_service_status()
                    components_status["calendar_service"] = calendar_status["status"]
                except:
                    components_status["calendar_service"] = "error"
            else:
                components_status["calendar_service"] = "disabled"
            
            return {
                "service": "automation_service",
                "status": "healthy",
                "components": {
                    "database": "active",
                    "task_scheduler": "active",
                    **components_status
                },
                "integrated_services": True,
                "version": "2.0"
            }
        except Exception as e:
            self.logger.error(f"자동화 서비스 상태 조회 실패: {e}")
            return {"service": "automation_service", "status": "error", "error": str(e)}
    
    async def cleanup(self):
        """서비스 정리 (통합 서비스들 포함)"""
        try:
            # 모든 통합 서비스 정리
            cleanup_tasks = []
            
            if hasattr(self, 'user_service'):
                cleanup_tasks.append(self.user_service.cleanup())
            if hasattr(self, 'config_service'):
                cleanup_tasks.append(self.config_service.cleanup())
            if hasattr(self, 'notification_service'):
                cleanup_tasks.append(self.notification_service.cleanup())
            if hasattr(self, 'email_service'):
                cleanup_tasks.append(self.email_service.cleanup())
            if hasattr(self, 'sms_service'):
                cleanup_tasks.append(self.sms_service.cleanup())
            if hasattr(self, 'reminder_service'):
                cleanup_tasks.append(self.reminder_service.cleanup())
            if hasattr(self, 'calendar_service') and self.calendar_service:
                cleanup_tasks.append(self.calendar_service.cleanup())
            
            # 모든 정리 작업을 병렬로 실행
            import asyncio
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            
            self.logger.info("자동화 서비스 정리 완료 (통합 구조)")
        except Exception as e:
            self.logger.error(f"자동화 서비스 정리 실패: {e}")


# ===== 하위 호환성을 위한 팩토리 함수 =====

def create_automation_service(
    db_session: Session, 
    service_config: Optional[Dict[str, Any]] = None
) -> AutomationService:
    """자동화 서비스 인스턴스 생성 (하위 호환성)"""
    return AutomationService(db_session, service_config)

# 전역 인스턴스 관리 (필요한 경우)
_automation_service_instance = None

def get_automation_service(
    db_session: Session = None, 
    service_config: Optional[Dict[str, Any]] = None
) -> AutomationService:
    """자동화 서비스 인스턴스 가져오기 (싱글톤, 선택적)"""
    global _automation_service_instance
    
    if _automation_service_instance is None and db_session:
        _automation_service_instance = AutomationService(db_session, service_config)
    
    return _automation_service_instance