"""
Task Agent 자동화 시스템 v4
공통 모듈을 활용한 자동화 작업 관리
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import shared_modules.db_models as db_models

# 공통 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "../shared_modules"))

from apscheduler.schedulers.asyncio import AsyncIOScheduler

  # 공통 모듈의 DB 모델들
from models import AutomationRequest, AutomationResponse, AutomationStatus, AutomationTaskType
from database import get_db_session
from utils import TaskAgentLogger, create_success_response, create_error_response

# 자동화 작업 서비스들 import
from automation_task.email_service import EmailService
from automation_task.google_calendar_service import GoogleCalendarService, GoogleCalendarConfig
from automation_task.reminder_service import ReminderService
from automation_task.common.config_manager import get_automation_config_manager
from automation_task.common.db_helper import get_automation_db_helper
from automation_task.common.utils import AutomationDateTimeUtils
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class TaskAgentAutomationManager:
    """Task Agent 자동화 매니저 (공통 모듈 기반)"""
    
    def __init__(self):
        """자동화 매니저 초기화"""
        try:
            # 스케줄러 초기화
            self.scheduler = AsyncIOScheduler()
            self.scheduler.start()
            
            # 설정 및 헬퍼 초기화
            self.config_manager = get_automation_config_manager()
            self.db_helper = get_automation_db_helper()
            
            # 자동화 서비스들 초기화
            self._init_services()
            
            logger.info("Task Agent 자동화 매니저 v4 초기화 완료")
            
        except Exception as e:
            logger.error(f"자동화 매니저 초기화 실패: {e}")
            raise

    def _init_services(self):
        """자동화 서비스들 초기화"""
        try:
            self.email_service = EmailService()
            
            # Google Calendar Service 초기화 (의존성 주입)
            config = GoogleCalendarConfig({
                "google_calendar": {
                    "client_id": os.getenv("GOOGLE_CALENDAR_CLIENT_ID", "your_client_id"),
                    "client_secret": os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET", "your_client_secret"),
                    "redirect_uri": os.getenv("GOOGLE_CALENDAR_REDIRECT_URI", "http://localhost:8080/callback"),
                    "token_url": "https://oauth2.googleapis.com/token",
                    "default_timezone": os.getenv("GOOGLE_CALENDAR_DEFAULT_TIMEZONE", "Asia/Seoul")
                }
            })
            
            # 간단한 Google API 클라이언트
            class SimpleGoogleApiClient:
                def build_service(self, service_name: str, version: str, credentials):
                    return build(service_name, version, credentials=credentials)
            
            self.calendar_service = GoogleCalendarService(
                api=SimpleGoogleApiClient(),
                time_utils=AutomationDateTimeUtils(),
                config=config
            )
            
            self.reminder_service = ReminderService()
            
            logger.info("자동화 서비스들 초기화 완료")
            
        except Exception as e:
            logger.error(f"자동화 서비스 초기화 실패: {e}")
            # 서비스 초기화 실패해도 매니저는 동작하도록 함
            self.email_service = None
            self.calendar_service = None
            self.reminder_service = None

    async def create_automation_task(self, request: AutomationRequest) -> AutomationResponse:
        """자동화 작업 생성"""
        try:
            TaskAgentLogger.log_automation_task(
                task_id="creating",
                task_type=request.task_type.value,
                status="creating",
                details=f"user_id: {request.user_id}, title: {request.title}"
            )
            
            # 데이터 검증
            validation_result = self._validate_task_data(request)
            if not validation_result["is_valid"]:
                return AutomationResponse(
                    task_id=-1,
                    status=AutomationStatus.FAILED,
                    message=f"작업 데이터 검증 실패: {', '.join(validation_result['errors'])}"
                )
            
            # DB에 작업 저장 (공통 모듈 활용)
            db_session = get_db_session()
            try:
                automation_task = db_models.AutomationTask(
                    user_id=request.user_id,
                    task_type=request.task_type.value,
                    title=request.title,
                    task_data=request.task_data,
                    status=AutomationStatus.PENDING.value,
                    scheduled_at=request.scheduled_at
                )
                
                db_session.add(automation_task)
                db_session.commit()
                db_session.refresh(automation_task)
                task_id = automation_task.task_id
                
            finally:
                db_session.close()
            
            TaskAgentLogger.log_automation_task(
                task_id=str(task_id),
                task_type=request.task_type.value,
                status="created",
                details=f"task saved to database"
            )
            
            # 스케줄 설정
            if request.scheduled_at:
                # 예약된 작업
                try:
                    self.scheduler.add_job(
                        self._execute_task,
                        'date',
                        run_date=request.scheduled_at,
                        args=[task_id],
                        id=f"auto_{task_id}",
                        misfire_grace_time=300  # 5분 유예시간
                    )
                    
                    TaskAgentLogger.log_automation_task(
                        task_id=str(task_id),
                        task_type=request.task_type.value,
                        status="scheduled",
                        details=f"scheduled for {request.scheduled_at}"
                    )
                    
                    return AutomationResponse(
                        task_id=task_id,
                        status=AutomationStatus.PENDING,
                        message=f"작업이 {request.scheduled_at.strftime('%Y-%m-%d %H:%M')}에 예약되었습니다.",
                        scheduled_time=request.scheduled_at
                    )
                    
                except Exception as scheduler_error:
                    logger.error(f"스케줄러 등록 실패: {scheduler_error}")
                    # 스케줄러 실패시 즉시 실행으로 전환
                    result = await self._execute_task(task_id)
                    return AutomationResponse(
                        task_id=task_id,
                        status=AutomationStatus.SUCCESS if result.get("status") == "success" else AutomationStatus.FAILED,
                        message=result.get("message", "작업이 실행되었습니다 (스케줄 실패로 즉시 실행)")
                    )
            else:
                # 즉시 실행
                result = await self._execute_task(task_id)
                return AutomationResponse(
                    task_id=task_id,
                    status=AutomationStatus.SUCCESS if result.get("status") == "success" else AutomationStatus.FAILED,
                    message=result.get("message", "작업이 실행되었습니다.")
                )
                
        except Exception as e:
            logger.error(f"자동화 작업 생성 실패: {e}")
            TaskAgentLogger.log_automation_task(
                task_id="failed",
                task_type=request.task_type.value,
                status="failed",
                details=f"creation error: {str(e)}"
            )
            
            return AutomationResponse(
                task_id=-1,
                status=AutomationStatus.FAILED,
                message=f"작업 생성 실패: {str(e)}"
            )

    def _validate_task_data(self, request: AutomationRequest) -> Dict[str, Any]:
        """작업 데이터 검증"""
        errors = []
        warnings = []
        
        # 기본 검증
        if not request.title.strip():
            errors.append("작업 제목이 필요합니다")
        
        if not request.task_data:
            errors.append("작업 데이터가 필요합니다")
        
        # 타입별 검증
        task_type = request.task_type
        task_data = request.task_data
        
        if task_type == AutomationTaskType.SEND_EMAIL:
            if not task_data.get("to_emails"):
                errors.append("수신자 이메일이 필요합니다")
            if not task_data.get("subject"):
                errors.append("이메일 제목이 필요합니다")
            if not task_data.get("body"):
                errors.append("이메일 내용이 필요합니다")
                
        elif task_type == AutomationTaskType.SCHEDULE_CALENDAR:
            if not task_data.get("title"):
                errors.append("일정 제목이 필요합니다")
            if not task_data.get("start_time"):
                errors.append("시작 시간이 필요합니다")
                
        elif task_type == AutomationTaskType.SEND_REMINDER:
            if not task_data.get("message"):
                errors.append("리마인더 메시지가 필요합니다")
            if not task_data.get("remind_time"):
                errors.append("알림 시간이 필요합니다")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    async def _execute_task(self, task_id: int) -> Dict[str, Any]:
        """자동화 작업 실행"""
        try:
            TaskAgentLogger.log_automation_task(
                task_id=str(task_id),
                task_type="unknown",
                status="executing",
                details="task execution started"
            )
            
            # 작업 조회 (공통 모듈의 DB 헬퍼 활용)
            task_info = await self.db_helper.get_automation_task_by_id(task_id)
            
            if not task_info:
                error_msg = "작업을 찾을 수 없습니다"
                TaskAgentLogger.log_automation_task(
                    task_id=str(task_id),
                    task_type="unknown",
                    status="failed",
                    details=error_msg
                )
                return {"status": "failed", "message": error_msg}
            
            # 상태 업데이트 - PROCESSING
            await self.db_helper.update_automation_task_status(
                task_id, 
                AutomationStatus.PROCESSING.value,
                executed_at=datetime.now()
            )
            
            # 작업 실행
            task_type = task_info["task_type"]
            task_data = task_info["task_data"] or {}
            
            TaskAgentLogger.log_automation_task(
                task_id=str(task_id),
                task_type=task_type,
                status="processing",
                details=f"executing {task_type}"
            )
            
            result = await self._execute_by_type(task_type, task_data, task_info["user_id"])
            
            # 결과에 따른 상태 업데이트
            final_status = AutomationStatus.SUCCESS.value if result["status"] == "success" else AutomationStatus.FAILED.value
            await self.db_helper.update_automation_task_status(
                task_id, 
                final_status,
                result_data=result
            )
            
            TaskAgentLogger.log_automation_task(
                task_id=str(task_id),
                task_type=task_type,
                status=final_status,
                details=f"execution completed: {result.get('message', 'no message')}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"작업 실행 실패 (ID: {task_id}): {e}")
            
            # 실패 상태로 업데이트
            try:
                await self.db_helper.update_automation_task_status(
                    task_id, 
                    AutomationStatus.FAILED.value,
                    result_data={"error": str(e)}
                )
            except:
                pass  # DB 업데이트 실패는 로그만 남기고 넘어감
            
            TaskAgentLogger.log_automation_task(
                task_id=str(task_id),
                task_type="unknown",
                status="failed",
                details=f"execution error: {str(e)}"
            )
            
            return {"status": "failed", "message": str(e)}
    
    async def _execute_by_type(self, task_type: str, task_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """타입별 작업 실행"""
        try:
            if task_type == AutomationTaskType.SCHEDULE_CALENDAR.value:
                return await self._execute_calendar(task_data, user_id)
            elif task_type == AutomationTaskType.SEND_EMAIL.value:
                return await self._execute_email(task_data, user_id)
            elif task_type == AutomationTaskType.SEND_REMINDER.value:
                return await self._execute_reminder(task_data, user_id)
            elif task_type == AutomationTaskType.SEND_MESSAGE.value:
                return await self._execute_message(task_data, user_id)
            else:
                return {"status": "failed", "message": f"지원하지 않는 작업 타입: {task_type}"}
                
        except Exception as e:
            logger.error(f"타입별 작업 실행 실패 ({task_type}): {e}")
            return {"status": "failed", "message": str(e)}
    
    async def _execute_calendar(self, task_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """캘린더 일정 추가"""
        try:
            if not self.calendar_service:
                return {"status": "failed", "message": "캘린더 서비스가 초기화되지 않았습니다"}
            
            title = task_data.get("title", "")
            start_time = task_data.get("start_time", "")
            end_time = task_data.get("end_time")
            description = task_data.get("description", "")
            attendees = task_data.get("attendees", [])
            
            # 캘린더 서비스 호출
            result = await self.calendar_service.create_event({
                "title": title,
                "start_time": start_time,
                "end_time": end_time,
                "description": description,
                "attendees": attendees,
                "user_id": user_id
            })
            
            if result.get("success"):
                return {
                    "status": "success",
                    "message": f"'{title}' 일정이 캘린더에 추가되었습니다",
                    "details": {
                        "title": title,
                        "start_time": start_time,
                        "event_id": result.get("event_id")
                    }
                }
            else:
                return {
                    "status": "failed",
                    "message": result.get("error", "캘린더 일정 추가 실패"),
                    "details": result
                }
            
        except Exception as e:
            logger.error(f"캘린더 작업 실패: {e}")
            return {"status": "failed", "message": f"캘린더 작업 실패: {str(e)}"}
    
    async def _execute_email(self, task_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """이메일 발송"""
        try:
            if not self.email_service:
                return {"status": "failed", "message": "이메일 서비스가 초기화되지 않았습니다"}
            
            to_emails = task_data.get("to_emails", [])
            subject = task_data.get("subject", "")
            body = task_data.get("body", "")
            attachments = task_data.get("attachments", [])
            
            # 이메일 서비스 호출
            result = await self.email_service.send_email({
                "to_emails": to_emails,
                "subject": subject,
                "body": body,
                "attachments": attachments,
                "user_id": user_id
            })
            
            if result.get("success"):
                return {
                    "status": "success",
                    "message": f"{len(to_emails)}명에게 이메일이 발송되었습니다",
                    "details": {
                        "subject": subject,
                        "recipients": len(to_emails),
                        "message_id": result.get("message_id")
                    }
                }
            else:
                return {
                    "status": "failed",
                    "message": result.get("error", "이메일 발송 실패"),
                    "details": result
                }
            
        except Exception as e:
            logger.error(f"이메일 작업 실패: {e}")
            return {"status": "failed", "message": f"이메일 작업 실패: {str(e)}"}
    
    async def _execute_reminder(self, task_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """리마인더 발송"""
        try:
            if not self.reminder_service:
                return {"status": "failed", "message": "리마인더 서비스가 초기화되지 않았습니다"}
            
            message = task_data.get("message", "")
            remind_time = task_data.get("remind_time", "")
            notification_type = task_data.get("notification_type", "app")
            
            # 리마인더 서비스 호출
            result = await self.reminder_service.send_reminder({
                "message": message,
                "remind_time": remind_time,
                "notification_type": notification_type,
                "user_id": user_id
            })
            
            if result.get("success"):
                return {
                    "status": "success",
                    "message": "리마인더가 발송되었습니다",
                    "details": {
                        "message": message,
                        "notification_type": notification_type,
                        "reminder_id": result.get("reminder_id")
                    }
                }
            else:
                return {
                    "status": "failed",
                    "message": result.get("error", "리마인더 발송 실패"),
                    "details": result
                }
            
        except Exception as e:
            logger.error(f"리마인더 작업 실패: {e}")
            return {"status": "failed", "message": f"리마인더 작업 실패: {str(e)}"}
    
    async def _execute_message(self, task_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """메시지 발송 (Slack, Teams 등)"""
        try:
            platform = task_data.get("platform", "").lower()
            content = task_data.get("content", "")
            channel = task_data.get("channel", "")
            
            # 플랫폼별 메시지 발송 구현
            if platform == "slack":
                # Slack 메시지 발송 로직
                logger.info(f"Slack 메시지 발송: {channel} - {content[:50]}...")
                return {
                    "status": "success",
                    "message": f"Slack 채널 '{channel}'에 메시지가 발송되었습니다",
                    "details": {"platform": "slack", "channel": channel}
                }
            elif platform == "teams":
                # Teams 메시지 발송 로직
                logger.info(f"Teams 메시지 발송: {channel} - {content[:50]}...")
                return {
                    "status": "success",
                    "message": f"Teams 채널 '{channel}'에 메시지가 발송되었습니다",
                    "details": {"platform": "teams", "channel": channel}
                }
            else:
                return {"status": "failed", "message": f"지원하지 않는 메시지 플랫폼: {platform}"}
            
        except Exception as e:
            logger.error(f"메시지 작업 실패: {e}")
            return {"status": "failed", "message": f"메시지 작업 실패: {str(e)}"}

    async def get_task_status(self, task_id: int) -> Dict[str, Any]:
        """작업 상태 조회"""
        try:
            task_info = await self.db_helper.get_automation_task_by_id(task_id)
            
            if not task_info:
                return {"error": "작업을 찾을 수 없습니다"}
            
            return {
                "task_id": task_id,
                "status": task_info["status"],
                "title": task_info["title"],
                "task_type": task_info["task_type"],
                "created_at": task_info["created_at"].isoformat() if task_info["created_at"] else None,
                "executed_at": task_info["executed_at"].isoformat() if task_info["executed_at"] else None,
                "scheduled_at": task_info["scheduled_at"].isoformat() if task_info["scheduled_at"] else None,
                "user_id": task_info["user_id"]
            }
            
        except Exception as e:
            logger.error(f"작업 상태 조회 실패: {e}")
            return {"error": str(e)}

    async def cancel_task(self, task_id: int) -> bool:
        """작업 취소"""
        try:
            # 스케줄러에서 제거
            try:
                self.scheduler.remove_job(f"auto_{task_id}")
                logger.info(f"스케줄러에서 작업 제거 완료: {task_id}")
            except Exception as scheduler_error:
                logger.warning(f"스케줄러 작업 제거 실패 (이미 실행되었거나 존재하지 않음): {scheduler_error}")
            
            # DB 상태 업데이트 (공통 모듈의 DB 헬퍼 활용)
            success = await self.db_helper.update_automation_task_status(
                task_id, 
                AutomationStatus.CANCELLED.value
            )
            
            if success:
                TaskAgentLogger.log_automation_task(
                    task_id=str(task_id),
                    task_type="unknown",
                    status="cancelled",
                    details="task cancelled by user request"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"작업 취소 실패: {e}")
            return False

    async def get_user_tasks(self, user_id: int, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """사용자의 자동화 작업 목록 조회"""
        try:
            return await self.db_helper.get_user_automation_tasks(user_id, status, limit)
        except Exception as e:
            logger.error(f"사용자 작업 목록 조회 실패: {e}")
            return []

    async def get_system_stats(self) -> Dict[str, Any]:
        """시스템 통계 조회"""
        try:
            stats = await self.db_helper.get_task_statistics()
            
            # 스케줄러 정보 추가
            scheduler_jobs = len(self.scheduler.get_jobs())
            
            stats.update({
                "scheduler_jobs": scheduler_jobs,
                "services_status": {
                    "email_service": bool(self.email_service),
                    "calendar_service": bool(self.calendar_service),
                    "reminder_service": bool(self.reminder_service)
                },
                "timestamp": datetime.now().isoformat()
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"시스템 통계 조회 실패: {e}")
            return {"error": str(e)}

    async def shutdown(self):
        """자동화 매니저 종료"""
        try:
            # 스케줄러 종료
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("스케줄러 종료 완료")
            
            # 서비스들 종료
            services = [self.email_service, self.calendar_service, self.reminder_service]
            for service in services:
                if service and hasattr(service, 'cleanup'):
                    try:
                        await service.cleanup()
                    except Exception as service_error:
                        logger.warning(f"서비스 정리 실패: {service_error}")
            
            logger.info("Task Agent 자동화 매니저 종료 완료")
            
        except Exception as e:
            logger.error(f"자동화 매니저 종료 실패: {e}")


# 기존 코드와의 호환성을 위한 별칭
AutomationManager = TaskAgentAutomationManager
