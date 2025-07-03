"""
개선된 리마인더 서비스 (통합 알림 기능)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .common.base_service import BaseService
from .common.notification_service import NotificationService
from .common.user_service import UserService

class ReminderService(BaseService):
    """통합 리마인더 관리 서비스"""
    
    def __init__(self, db_session, config: Optional[Dict[str, Any]] = None):
        super().__init__(db_session, config)
        self.notification_service = NotificationService(db_session, config)
        self.user_service = UserService(db_session, config)
    
    async def send_reminder(
        self,
        user_id: int,
        message: str,
        reminder_types: List[str] = None,
        urgency: str = "medium",
        task_id: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """리마인더 발송"""
        try:
            if reminder_types is None:
                reminder_types = ["app"]
            
            # 사용자 정보 확인
            user_info = await self.user_service.get_user_info(user_id)
            if not user_info:
                return {"success": False, "error": "사용자를 찾을 수 없습니다"}
            
            # 추가 데이터 준비
            if additional_data is None:
                additional_data = {}
            
            if task_id:
                additional_data["task_id"] = task_id
            
            additional_data["subject"] = f"📋 리마인더: {message}"
            
            # 통합 알림 서비스를 통해 발송
            result = await self.notification_service.send_notification(
                user_id=user_id,
                message=message,
                notification_types=reminder_types,
                urgency=urgency,
                additional_data=additional_data
            )
            
            self.logger.info(f"리마인더 발송 완료: User {user_id} - {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"리마인더 발송 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_calendar_reminder(
        self,
        user_id: int,
        event_data: Dict[str, Any],
        reminder_minutes_before: int = 15
    ) -> Dict[str, Any]:
        """캘린더 이벤트 리마인더 발송"""
        try:
            event_title = event_data.get("title", "일정")
            start_time = event_data.get("start_time")
            location = event_data.get("location", "")
            
            # 리마인더 메시지 구성
            message = f"일정 알림: {event_title}"
            if start_time:
                start_dt = datetime.fromisoformat(start_time.replace('T', ' '))
                message += f" ({start_dt.strftime('%H:%M')})"
            if location:
                message += f" @ {location}"
            
            # 사용자 알림 설정에 따라 리마인더 타입 결정
            notification_settings = await self.user_service.get_notification_settings(user_id)
            reminder_types = []
            
            if notification_settings.get("app_notification", True):
                reminder_types.append("app")
            if notification_settings.get("email_notification", True):
                reminder_types.append("email")
            if notification_settings.get("sms_notification", False):  # SMS는 기본 비활성화
                reminder_types.append("sms")
            
            # 추가 데이터
            additional_data = {
                "event_title": event_title,
                "start_time": start_time,
                "location": location,
                "reminder_minutes": reminder_minutes_before,
                "subject": f"📅 일정 알림: {event_title}"
            }
            
            return await self.send_reminder(
                user_id=user_id,
                message=message,
                reminder_types=reminder_types,
                urgency="high",
                additional_data=additional_data
            )
            
        except Exception as e:
            self.logger.error(f"캘린더 리마인더 발송 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_task_reminder(
        self,
        user_id: int,
        task_data: Dict[str, Any],
        reminder_types: List[str] = None
    ) -> Dict[str, Any]:
        """작업 리마인더 발송"""
        try:
            task_title = task_data.get("title", "작업")
            due_date = task_data.get("due_date")
            priority = task_data.get("priority", "medium")
            
            # 리마인더 메시지 구성
            message = f"작업 알림: {task_title}"
            if due_date:
                due_dt = datetime.fromisoformat(due_date.replace('T', ' '))
                message += f" (마감: {due_dt.strftime('%m월 %d일 %H:%M')})"
            
            # 우선순위에 따른 urgency 설정
            urgency_map = {
                "high": "high",
                "medium": "medium", 
                "low": "low"
            }
            urgency = urgency_map.get(priority, "medium")
            
            # 추가 데이터
            additional_data = {
                "task_title": task_title,
                "due_date": due_date,
                "priority": priority,
                "subject": f"📋 작업 알림: {task_title}"
            }
            
            return await self.send_reminder(
                user_id=user_id,
                message=message,
                reminder_types=reminder_types or ["app", "email"],
                urgency=urgency,
                task_id=task_data.get("task_id"),
                additional_data=additional_data
            )
            
        except Exception as e:
            self.logger.error(f"작업 리마인더 발송 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_message_to_platform(
        self,
        platform: str,
        message: str,
        channel: Optional[str] = None,
        recipients: List[str] = None,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """특정 플랫폼으로 메시지 발송 (Slack, Teams)"""
        try:
            return await self.notification_service.send_message(
                platform=platform,
                message=message,
                channel=channel,
                recipients=recipients or [],
                webhook_url=webhook_url
            )
            
        except Exception as e:
            self.logger.error(f"플랫폼 메시지 발송 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def schedule_reminder(
        self,
        user_id: int,
        message: str,
        scheduled_time: datetime,
        reminder_types: List[str] = None
    ) -> Dict[str, Any]:
        """리마인더 스케줄링 (추후 스케줄러와 연동)"""
        try:
            # 스케줄러에 리마인더 등록
            # 현재는 로깅으로 시뮬레이션
            self.logger.info(
                f"리마인더 스케줄링: User {user_id}, "
                f"Message: {message}, Time: {scheduled_time}, Types: {reminder_types}"
            )
            
            return {
                "success": True,
                "message": "리마인더가 스케줄링되었습니다",
                "scheduled_time": scheduled_time.isoformat(),
                "user_id": user_id
            }
            
        except Exception as e:
            self.logger.error(f"리마인더 스케줄링 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_notification_history(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """사용자 알림 기록 조회"""
        try:
            # 추후 DB에서 알림 기록 조회 구현
            self.logger.info(f"알림 기록 조회: User {user_id}, Limit: {limit}, Offset: {offset}")
            
            return {
                "success": True,
                "notifications": [],  # 추후 실제 데이터 반환
                "total_count": 0,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            self.logger.error(f"알림 기록 조회 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_user_notification_settings(
        self,
        user_id: int,
        settings: Dict[str, bool]
    ) -> Dict[str, Any]:
        """사용자 알림 설정 업데이트"""
        try:
            result = await self.user_service.update_notification_settings(user_id, settings)
            
            if result:
                return {
                    "success": True,
                    "message": "알림 설정이 업데이트되었습니다",
                    "settings": settings
                }
            else:
                return {
                    "success": False,
                    "error": "알림 설정 업데이트에 실패했습니다"
                }
                
        except Exception as e:
            self.logger.error(f"알림 설정 업데이트 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_service_status(self) -> Dict[str, Any]:
        """서비스 상태 조회"""
        notification_status = await self.notification_service.get_service_status()
        user_status = await self.user_service.get_service_status()
        
        return {
            "service": "reminder_service",
            "status": "healthy",
            "components": {
                "notification_service": notification_status["status"],
                "user_service": user_status["status"]
            }
        }
    
    async def cleanup(self):
        """서비스 정리"""
        await self.notification_service.cleanup()
        await self.user_service.cleanup()
        self.logger.info("리마인더 서비스 정리 완료")