
"""
통합 알림 서비스
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from .base_service import BaseService
from .user_service import UserService
from .config_service import ConfigService

class NotificationService(BaseService):
    """통합 알림 관리 서비스"""
    
    def __init__(self, db_session, config: Optional[Dict[str, Any]] = None):
        super().__init__(db_session, config)
        self.user_service = UserService(db_session, config)
        self.config_service = ConfigService(db_session, config)
    
    async def send_notification(
        self, 
        user_id: int, 
        message: str, 
        notification_types: List[str] = None,
        urgency: str = "medium",
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """통합 알림 발송"""
        try:
            if notification_types is None:
                notification_types = ["app"]
            
            results = []
            
            # 각 알림 타입별로 발송
            for notification_type in notification_types:
                # 사용자 알림 설정 확인
                enabled = await self.user_service.check_notification_enabled(
                    user_id, f"{notification_type}_notification"
                )
                
                if not enabled:
                    results.append({
                        "type": notification_type,
                        "success": False,
                        "reason": "disabled_by_user"
                    })
                    continue
                
                # 타입별 알림 발송
                if notification_type == "app":
                    result = await self._send_app_notification(user_id, message, urgency)
                elif notification_type == "email":
                    result = await self._send_email_notification(user_id, message, additional_data)
                elif notification_type == "sms":
                    result = await self._send_sms_notification(user_id, message)
                elif notification_type == "push":
                    result = await self._send_push_notification(user_id, message, urgency)
                else:
                    result = {"success": False, "error": f"지원하지 않는 알림 타입: {notification_type}"}
                
                results.append({
                    "type": notification_type,
                    **result
                })
            
            # 결과 집계
            successful = [r for r in results if r.get("success")]
            failed = [r for r in results if not r.get("success")]
            
            return {
                "success": len(successful) > 0,
                "sent_count": len(successful),
                "failed_count": len(failed),
                "results": results,
                "message": f"알림이 {len(successful)}개 채널로 발송되었습니다."
            }
            
        except Exception as e:
            self.logger.error(f"통합 알림 발송 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_message(
        self,
        platform: str,
        message: str,
        channel: Optional[str] = None,
        recipients: List[str] = None,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """메시징 플랫폼으로 메시지 발송"""
        try:
            if platform == "slack":
                return await self._send_slack_message(message, channel, recipients or [])
            elif platform == "teams":
                return await self._send_teams_message(message, channel, webhook_url)
            else:
                return {"success": False, "error": f"지원하지 않는 플랫폼: {platform}"}
                
        except Exception as e:
            self.logger.error(f"메시지 발송 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_app_notification(self, user_id: int, message: str, urgency: str) -> Dict[str, Any]:
        """앱 내 알림 발송"""
        try:
            # 알림 데이터 구성
            notification_data = {
                "user_id": user_id,
                "message": message,
                "urgency": urgency,
                "type": "notification",
                "timestamp": datetime.now().isoformat(),
                "read": False
            }
            
            # 실시간 알림 전송
            success = await self._send_realtime_notification(user_id, notification_data)
            
            # 데이터베이스에 알림 기록 저장
            await self._save_notification_to_db(user_id, notification_data)
            
            if success:
                return {"success": True, "notification_id": notification_data.get("id")}
            else:
                return {"success": False, "reason": "delivery_failed"}
                
        except Exception as e:
            self.logger.error(f"앱 알림 발송 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_email_notification(self, user_id: int, message: str, additional_data: Optional[Dict]) -> Dict[str, Any]:
        """이메일 알림 발송"""
        try:
            # EmailService를 여기서 임포트 (순환 참조 방지)
            from ..email_service import EmailService
            
            user_email = await self.user_service.get_user_email(user_id)
            if not user_email:
                return {"success": False, "reason": "no_email"}
            
            email_config = self.config_service.get_email_config()
            email_service = EmailService(self.db, {"email": email_config})
            
            subject = additional_data.get("subject", "📋 알림") if additional_data else "📋 알림"
            html_body = self._create_notification_email_template(message, additional_data)
            
            result = await email_service.send_email(
                to_emails=[user_email],
                subject=subject,
                body=message,
                html_body=html_body
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"이메일 알림 발송 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_sms_notification(self, user_id: int, message: str) -> Dict[str, Any]:
        """SMS 알림 발송"""
        try:
            # SMSService를 여기서 임포트 (순환 참조 방지)
            from ..sms_service import SMSService
            
            user_phone = await self.user_service.get_user_phone(user_id)
            if not user_phone:
                return {"success": False, "reason": "no_phone"}
            
            sms_config = self.config_service.get_sms_config()
            sms_service = SMSService(self.db, {"sms": sms_config})
            
            # SMS 메시지 길이 제한 (160자)
            if len(message) > 160:
                message = message[:157] + "..."
            
            result = await sms_service.send_sms(user_phone, message)
            return result
            
        except Exception as e:
            self.logger.error(f"SMS 알림 발송 실패: {e}")
            return {"success": False, "error": str(e)}

    async def _send_slack_message(self, message: str, channel: Optional[str], recipients: List[str]) -> Dict[str, Any]:
        """Slack 메시지 발송"""
        try:
            import aiohttp
            
            messaging_config = self.config_service.get_messaging_config()
            slack_token = messaging_config.get("slack", {}).get("bot_token")
            
            if not slack_token:
                return {"success": False, "reason": "no_token"}
            
            slack_url = "https://slack.com/api/chat.postMessage"
            headers = {
                "Authorization": f"Bearer {slack_token}",
                "Content-Type": "application/json"
            }
            
            results = []
            
            # 채널에 메시지 발송
            if channel:
                payload = {"channel": channel, "text": message, "as_user": True}
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(slack_url, headers=headers, json=payload) as response:
                        result = await response.json()
                        if result.get("ok"):
                            results.append({"target": channel, "success": True})
                        else:
                            results.append({"target": channel, "success": False, "error": result.get("error")})
            
            # 개별 사용자에게 DM 발송
            for recipient in recipients:
                payload = {"channel": recipient, "text": message, "as_user": True}
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(slack_url, headers=headers, json=payload) as response:
                        result = await response.json()
                        if result.get("ok"):
                            results.append({"target": recipient, "success": True})
                        else:
                            results.append({"target": recipient, "success": False, "error": result.get("error")})
            
            success_count = sum(1 for r in results if r["success"])
            return {
                "success": success_count > 0,
                "total_sent": len(results),
                "success_count": success_count,
                "results": results
            }
            
        except Exception as e:
            self.logger.error(f"Slack 메시지 발송 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_teams_message(self, message: str, channel: Optional[str], webhook_url: Optional[str]) -> Dict[str, Any]:
        """Teams 메시지 발송"""
        try:
            import aiohttp
            
            messaging_config = self.config_service.get_messaging_config()
            teams_webhook = webhook_url or messaging_config.get("teams", {}).get("webhook_url")
            
            if not teams_webhook:
                return {"success": False, "reason": "no_webhook"}
            
            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "0076D7",
                "summary": "알림",
                "sections": [{
                    "activityTitle": "📋 알림",
                    "activitySubtitle": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "markdown": True,
                    "text": message
                }]
            }
            
            headers = {"Content-Type": "application/json"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(teams_webhook, headers=headers, json=payload) as response:
                    if response.status == 200:
                        return {"success": True, "status_code": response.status}
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
            
        except Exception as e:
            self.logger.error(f"Teams 메시지 발송 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_realtime_notification(self, user_id: int, notification_data: Dict) -> bool:
        """실시간 알림 전송"""
        try:
            realtime_config = self.config_service.get_realtime_config()
            redis_url = realtime_config.get("redis_url")
            
            if redis_url:
                import redis.asyncio as redis
                redis_client = redis.from_url(redis_url)
                
                channel = f"user_notifications_{user_id}"
                message = json.dumps(notification_data)
                
                await redis_client.publish(channel, message)
                await redis_client.close()
                
                return True
            
            # Redis가 없는 경우 로컬 메모리나 다른 방식 사용
            self.logger.info(f"실시간 알림 시뮬레이션: User {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"실시간 알림 전송 실패: {e}")
            return False
    
    async def _save_notification_to_db(self, user_id: int, notification_data: Dict):
        """알림을 데이터베이스에 저장"""
        try:
            # 알림 기록 저장 로직 구현
            self.logger.info(f"알림 DB 저장: User {user_id} - {notification_data}")
            
        except Exception as e:
            self.logger.error(f"알림 DB 저장 실패: {e}")
    
    def _create_notification_email_template(self, message: str, additional_data: Optional[Dict] = None) -> str:
        """알림 이메일 HTML 템플릿 생성"""
        current_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>알림</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff;">
                <h2 style="color: #007bff; margin-top: 0;">📋 알림</h2>
                <p style="font-size: 16px; margin: 15px 0;">{message}</p>
                
                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">
                
                <p style="font-size: 14px; color: #666; margin: 10px 0;">
                    <strong>알림 시간:</strong> {current_time}
                </p>
                
                <div style="margin-top: 20px; padding: 15px; background-color: #e9ecef; border-radius: 5px;">
                    <p style="font-size: 14px; color: #666; margin: 0;">
                        이 이메일은 자동으로 발송된 알림입니다. 
                        더 이상 받고 싶지 않으시면 알림 설정에서 이메일 알림을 비활성화해주세요.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    async def get_service_status(self) -> Dict[str, Any]:
        """서비스 상태 조회"""
        return {
            "service": "notification_service",
            "status": "healthy",
            "components": {
                "user_service": (await self.user_service.get_service_status())["status"],
                "config_service": (await self.config_service.get_service_status())["status"]
            }
        }
    
    async def cleanup(self):
        """서비스 정리"""
        await self.user_service.cleanup()
        await self.config_service.cleanup()
        self.logger.info("알림 서비스 정리 완료")