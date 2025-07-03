"""
사용자 정보 관리 공통 서비스
"""

from asyncio.log import logger
import os
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from .base_service import BaseService

try:
    from ...core.db.database import get_db_session
    from ...schemas.db_models import User, NotificationSettings
except ImportError:
    logger.warning("데이터베이스 모듈을 가져올 수 없습니다.")
    get_db_session = None
    User = None
    NotificationSettings = None

class UserService(BaseService):
    """사용자 정보 관리 서비스"""
    
    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """사용자 기본 정보 조회"""
        try:
            if not User:
                return None
                
            user = self.db.query(User).filter(User.user_id == user_id).first()
            if not user:
                return None
                
            return {
                "user_id": user.user_id,
                "email": user.email,
                "phone_number": getattr(user, 'phone_number', None),
                "name": getattr(user, 'name', None),
                "timezone": getattr(user, 'timezone', 'Asia/Seoul')
            }
        except Exception as e:
            self.logger.error(f"사용자 정보 조회 실패: {e}")
            return None
    
    async def get_user_email(self, user_id: int) -> Optional[str]:
        """사용자 이메일 조회"""
        user_info = await self.get_user_info(user_id)
        return user_info.get("email") if user_info else None
    
    async def get_user_phone(self, user_id: int) -> Optional[str]:
        """사용자 전화번호 조회"""
        user_info = await self.get_user_info(user_id)
        return user_info.get("phone_number") if user_info else None
    
    async def get_notification_settings(self, user_id: int) -> Dict[str, bool]:
        """사용자 알림 설정 조회"""
        try:
            if not NotificationSettings:
                return {
                    "app_notification": True,
                    "email_notification": True,
                    "sms_notification": True,
                    "push_notification": True
                }
            
            settings = self.db.query(NotificationSettings).filter(
                NotificationSettings.user_id == user_id
            ).first()
            
            if not settings:
                return {
                    "app_notification": True,
                    "email_notification": True,
                    "sms_notification": True,
                    "push_notification": True
                }
            
            return {
                "app_notification": getattr(settings, 'app_notification', True),
                "email_notification": getattr(settings, 'email_notification', True),
                "sms_notification": getattr(settings, 'sms_notification', True),
                "push_notification": getattr(settings, 'push_notification', True)
            }
            
        except Exception as e:
            self.logger.error(f"알림 설정 조회 실패: {e}")
            return {
                "app_notification": True,
                "email_notification": True,
                "sms_notification": True,
                "push_notification": True
            }
    
    async def update_notification_settings(self, user_id: int, settings: Dict[str, bool]) -> bool:
        """사용자 알림 설정 업데이트"""
        try:
            if not NotificationSettings:
                self.logger.warning("데이터베이스 모듈이 없어 알림 설정을 저장할 수 없습니다.")
                return False
            
            # 기존 설정 조회 또는 새로 생성
            notification_settings = self.db.query(NotificationSettings).filter(
                NotificationSettings.user_id == user_id
            ).first()
            
            if not notification_settings:
                notification_settings = NotificationSettings(user_id=user_id)
                self.db.add(notification_settings)
            
            # 설정 업데이트
            for setting_name, value in settings.items():
                if hasattr(notification_settings, setting_name):
                    setattr(notification_settings, setting_name, value)
            
            self.db.commit()
            self.logger.info(f"사용자 {user_id}의 알림 설정이 업데이트되었습니다: {settings}")
            return True
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"알림 설정 업데이트 실패: {e}")
            return False
    
    async def check_notification_enabled(self, user_id: int, notification_type: str) -> bool:
        """특정 알림 타입이 활성화되어 있는지 확인"""
        settings = await self.get_notification_settings(user_id)
        return settings.get(notification_type, True)
    
    async def get_service_status(self) -> Dict[str, Any]:
        """서비스 상태 조회"""
        return {
            "service": "user_service",
            "status": "healthy",
            "database_connected": User is not None
        }
    
    async def cleanup(self):
        """서비스 정리"""
        # DB 세션은 상위에서 관리
        self.logger.info("사용자 서비스 정리 완료")