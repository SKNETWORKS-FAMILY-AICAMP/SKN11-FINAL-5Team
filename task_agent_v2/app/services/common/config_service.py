
# /app/services/common/config_service.py
"""
설정 관리 공통 서비스
"""

import os
from typing import Dict, Any, Optional
from .base_service import BaseService

class ConfigService(BaseService):
    """설정 관리 서비스"""
    
    def __init__(self, db_session, config: Optional[Dict[str, Any]] = None):
        super().__init__(db_session, config)
        self._load_default_config()
    
    def _load_default_config(self):
        """기본 설정 로드"""
        self.default_config = {
            "google_calendar": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
                "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/login/oauth2/code/google"),
                "scopes": ["https://www.googleapis.com/auth/calendar"]
            },
            "email": {
                "service": os.getenv("EMAIL_SERVICE", "smtp"),
                "smtp": {
                    "server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                    "port": int(os.getenv("SMTP_PORT", "587")),
                    "username": os.getenv("SMTP_USERNAME", ""),
                    "password": os.getenv("SMTP_PASSWORD", ""),
                    "from_email": os.getenv("FROM_EMAIL", "")
                },
                "aws_ses": {
                    "region": os.getenv("AWS_REGION", "us-east-1"),
                    "from_email": os.getenv("FROM_EMAIL", "")
                },
                "sendgrid": {
                    "api_key": os.getenv("SENDGRID_API_KEY", ""),
                    "from_email": os.getenv("FROM_EMAIL", "")
                }
            },
            "sms": {
                "service": os.getenv("SMS_SERVICE", "aws_sns"),
                "aws_sns": {
                    "region": os.getenv("AWS_REGION", "us-east-1")
                }
            },
            "messaging": {
                "slack": {
                    "bot_token": os.getenv("SLACK_BOT_TOKEN", "")
                },
                "teams": {
                    "webhook_url": os.getenv("TEAMS_WEBHOOK_URL", "")
                }
            },
            "realtime": {
                "redis_url": os.getenv("REDIS_URL", "")
            }
        }
    
    def get_config(self, service: str, fallback: Optional[Dict] = None) -> Dict[str, Any]:
        """서비스별 설정 조회"""
        config = self.config.get(service, self.default_config.get(service, fallback or {}))
        return config
    
    def get_email_config(self) -> Dict[str, Any]:
        """이메일 서비스 설정 조회"""
        return self.get_config("email")
    
    def get_sms_config(self) -> Dict[str, Any]:
        """SMS 서비스 설정 조회"""
        return self.get_config("sms")
    
    def get_messaging_config(self) -> Dict[str, Any]:
        """메시징 서비스 설정 조회"""
        return self.get_config("messaging")
    
    def get_google_calendar_config(self) -> Dict[str, Any]:
        """구글 캘린더 설정 조회"""
        return self.get_config("google_calendar")
    
    def get_realtime_config(self) -> Dict[str, Any]:
        """실시간 알림 설정 조회"""
        return self.get_config("realtime")
    
    def is_service_enabled(self, service: str) -> bool:
        """서비스가 활성화되어 있는지 확인"""
        config = self.get_config(service)
        
        if service == "email":
            email_service = config.get("service", "smtp")
            if email_service == "smtp":
                return bool(config.get("smtp", {}).get("username"))
            elif email_service == "aws_ses":
                return bool(config.get("aws_ses", {}).get("from_email"))
            elif email_service == "sendgrid":
                return bool(config.get("sendgrid", {}).get("api_key"))
                
        elif service == "sms":
            return bool(config.get("aws_sns", {}).get("region"))
            
        elif service == "slack":
            return bool(config.get("slack", {}).get("bot_token"))
            
        elif service == "teams":
            return bool(config.get("teams", {}).get("webhook_url"))
            
        elif service == "google_calendar":
            return bool(config.get("client_id") and config.get("client_secret"))
        
        return False
    
    async def get_service_status(self) -> Dict[str, Any]:
        """서비스 상태 조회"""
        return {
            "service": "config_service",
            "status": "healthy",
            "enabled_services": {
                "email": self.is_service_enabled("email"),
                "sms": self.is_service_enabled("sms"),
                "slack": self.is_service_enabled("slack"),
                "teams": self.is_service_enabled("teams"),
                "google_calendar": self.is_service_enabled("google_calendar")
            }
        }
    
    async def cleanup(self):
        """서비스 정리"""
        self.logger.info("설정 서비스 정리 완료")