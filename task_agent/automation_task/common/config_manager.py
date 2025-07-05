"""
설정 관리 공통 모듈
"""

import os
import json
from typing import Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """설정 관리를 위한 공통 클래스"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.getenv('CONFIG_FILE', 'config.json')
        self._config_cache = {}
        self._load_config()
    
    def _load_config(self):
        """설정 파일 로드"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config_cache = json.load(f)
                logger.info(f"설정 파일 로드 완료: {self.config_file}")
            else:
                logger.warning(f"설정 파일이 없습니다: {self.config_file}")
                self._config_cache = {}
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            self._config_cache = {}
    
    def get(self, key: str, default: Any = None, env_var: Optional[str] = None) -> Any:
        """설정 값 가져오기 (환경변수 우선)"""
        # 1. 환경변수 확인
        if env_var:
            env_value = os.getenv(env_var)
            if env_value is not None:
                return self._convert_type(env_value, default)
        
        # 2. 키에 해당하는 환경변수 확인 (대문자 변환)
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._convert_type(env_value, default)
        
        # 3. 설정 파일에서 가져오기 (중첩 키 지원)
        keys = key.split('.')
        value = self._config_cache
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def _convert_type(self, value: str, default: Any) -> Any:
        """문자열 값을 기본값 타입에 맞게 변환"""
        if default is None:
            return value
        
        if isinstance(default, bool):
            return value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(default, int):
            try:
                return int(value)
            except ValueError:
                return default
        elif isinstance(default, float):
            try:
                return float(value)
            except ValueError:
                return default
        elif isinstance(default, list):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value.split(',')
        elif isinstance(default, dict):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return default
        else:
            return value
    
    def set(self, key: str, value: Any, save_to_file: bool = True):
        """설정 값 저장"""
        keys = key.split('.')
        config = self._config_cache
        
        # 중첩 딕셔너리 생성
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        
        if save_to_file:
            self._save_config()
    
    def _save_config(self):
        """설정 파일 저장"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config_cache, f, indent=2, ensure_ascii=False)
            logger.info(f"설정 파일 저장 완료: {self.config_file}")
        except Exception as e:
            logger.error(f"설정 파일 저장 실패: {e}")
    
    def reload(self):
        """설정 파일 다시 로드"""
        self._load_config()
    
    def get_all(self) -> Dict[str, Any]:
        """모든 설정 반환"""
        return self._config_cache.copy()
    
    # 자주 사용하는 설정들을 위한 편의 메서드들
    
    def get_database_config(self) -> Dict[str, Any]:
        """데이터베이스 설정 가져오기"""
        return {
            "host": self.get("database.host", env_var="DB_HOST"),
            "port": self.get("database.port", 5432, env_var="DB_PORT"),
            "name": self.get("database.name", env_var="DB_NAME"),
            "user": self.get("database.user", env_var="DB_USER"),
            "password": self.get("database.password", env_var="DB_PASSWORD"),
            "url": self.get("database.url", env_var="DATABASE_URL")
        }
        
    def get_email_config(self, service: str = None) -> Dict[str, Any]:
        """이메일 설정 가져오기"""
        base_config = {
            "service": self.get("email.service", "smtp", env_var="EMAIL_SERVICE"),
            "from_email": self.get("email.from_email", env_var="FROM_EMAIL"),
            "from_name": self.get("email.from_name", "자동 이메일 시스템", env_var="FROM_NAME")
        }
        
        service = service or base_config["service"]
        
        if service.lower() == "smtp":
            base_config.update({
                "smtp_host": self.get("email.smtp.host", "smtp.gmail.com", env_var="SMTP_HOST"),
                "smtp_port": self.get("email.smtp.port", 587, env_var="SMTP_PORT"),
                "smtp_user": self.get("email.smtp.user", env_var="SMTP_USER"),
                "smtp_password": self.get("email.smtp.password", env_var="SMTP_PASSWORD"),
                "smtp_use_tls": self.get("email.smtp.use_tls", True, env_var="SMTP_USE_TLS")
            })
        elif service.lower() == "sendgrid":
            base_config.update({
                "api_key": self.get("email.sendgrid.api_key", env_var="SENDGRID_API_KEY"),
                "from_email": self.get("email.sendgrid.from_email", env_var="SENDGRID_FROM_EMAIL"),
                "from_name": self.get("email.sendgrid.from_name", env_var="SENDGRID_FROM_NAME")
            })
        elif service.lower() == "aws_ses":
            base_config.update({
                "aws_access_key": self.get("aws.access_key_id", env_var="AWS_ACCESS_KEY_ID"),
                "aws_secret_key": self.get("aws.secret_access_key", env_var="AWS_SECRET_ACCESS_KEY"),
                "aws_region": self.get("aws.region", "us-east-1", env_var="AWS_DEFAULT_REGION"),
                "from_email": self.get("email.ses.from_email", env_var="SES_FROM_EMAIL"),
                "from_name": self.get("email.ses.from_name", env_var="SES_FROM_NAME")
            })
        
        return base_config
    
    def get_sms_config(self, service: str = None) -> Dict[str, Any]:
        """SMS 설정 가져오기"""
        base_config = {
            "service": self.get("sms.service", "aws_sns", env_var="SMS_SERVICE")
        }
        
        service = service or base_config["service"]
        
        if service.lower() == "aws_sns":
            base_config.update({
                "aws_access_key": self.get("aws.access_key_id", env_var="AWS_ACCESS_KEY_ID"),
                "aws_secret_key": self.get("aws.secret_access_key", env_var="AWS_SECRET_ACCESS_KEY"),
                "aws_region": self.get("aws.region", "us-east-1", env_var="AWS_DEFAULT_REGION")
            })
        elif service.lower() == "twilio":
            base_config.update({
                "account_sid": self.get("sms.twilio.account_sid", env_var="TWILIO_ACCOUNT_SID"),
                "auth_token": self.get("sms.twilio.auth_token", env_var="TWILIO_AUTH_TOKEN"),
                "from_number": self.get("sms.twilio.from_number", env_var="TWILIO_PHONE_NUMBER")
            })
        
        return base_config
    
    def get_oauth_config(self, platform: str) -> Dict[str, Any]:
        """OAuth 설정 가져오기"""
        return {
            "client_id": self.get(f"oauth.{platform}.client_id", env_var=f"{platform.upper()}_CLIENT_ID"),
            "client_secret": self.get(f"oauth.{platform}.client_secret", env_var=f"{platform.upper()}_CLIENT_SECRET"),
            "redirect_uri": self.get(f"oauth.{platform}.redirect_uri", env_var=f"{platform.upper()}_REDIRECT_URI"),
            "scopes": self.get(f"oauth.{platform}.scopes", [], env_var=f"{platform.upper()}_SCOPES")
        }
    
    def get_slack_config(self) -> Dict[str, Any]:
        """Slack 설정 가져오기"""
        return {
            "bot_token": self.get("slack.bot_token", env_var="SLACK_BOT_TOKEN"),
            "app_token": self.get("slack.app_token", env_var="SLACK_APP_TOKEN"),
            "signing_secret": self.get("slack.signing_secret", env_var="SLACK_SIGNING_SECRET"),
            "webhook_url": self.get("slack.webhook_url", env_var="SLACK_WEBHOOK_URL")
        }
    
    def get_teams_config(self) -> Dict[str, Any]:
        """Teams 설정 가져오기"""
        return {
            "webhook_url": self.get("teams.webhook_url", env_var="TEAMS_WEBHOOK_URL"),
            "tenant_id": self.get("teams.tenant_id", env_var="TEAMS_TENANT_ID"),
            "client_id": self.get("teams.client_id", env_var="TEAMS_CLIENT_ID"),
            "client_secret": self.get("teams.client_secret", env_var="TEAMS_CLIENT_SECRET")
        }


# 전역 인스턴스
_config_manager = None

def get_config_manager(config_file: Optional[str] = None) -> ConfigManager:
    """ConfigManager 싱글톤 인스턴스 반환"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    return _config_manager

def get_config(key: str, default: Any = None, env_var: Optional[str] = None) -> Any:
    """설정 값 가져오기 (편의 함수)"""
    return get_config_manager().get(key, default, env_var)
