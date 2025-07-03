
# /app/services/service_manager.py
"""
서비스 매니저 (애플리케이션 레벨에서 서비스들을 통합 관리)
"""

import asyncio
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from .service_factory import ServiceFactory, ServiceContainer
from .common.config_service import ConfigService

class ServiceManager:
    """애플리케이션 서비스 통합 관리자"""
    
    def __init__(self, default_config: Optional[Dict[str, Any]] = None):
        self.default_config = default_config or self._load_default_config()
        self.factory = ServiceFactory()
        self.default_container_name = "default"
        
    def _load_default_config(self) -> Dict[str, Any]:
        """기본 설정 로드"""
        return {
            "google_calendar": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
                "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/login/oauth2/code/google")
            },
            "email": {
                "service": os.getenv("EMAIL_SERVICE", "smtp"),
                "smtp": {
                    "server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                    "port": int(os.getenv("SMTP_PORT", "587")),
                    "username": os.getenv("SMTP_USERNAME", ""),
                    "password": os.getenv("SMTP_PASSWORD", ""),
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
            }
        }
    
    @asynccontextmanager
    async def get_service_container(
        self, 
        db_session: Session, 
        container_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """서비스 컨테이너 컨텍스트 매니저"""
        container_name = container_name or self.default_container_name
        merged_config = {**self.default_config, **(config or {})}
        
        # 컨테이너 생성 또는 가져오기
        container = self.factory.get_container(container_name)
        if container is None:
            container = self.factory.create_container(
                container_name, db_session, merged_config
            )
        
        try:
            yield container
        finally:
            # 컨텍스트 종료 시 정리 (선택적)
            # await container.cleanup_all_services()
            pass
    
    async def initialize_services(
        self, 
        db_session: Session, 
        services: List[str] = None,
        container_name: Optional[str] = None
    ) -> ServiceContainer:
        """특정 서비스들만 초기화"""
        container_name = container_name or self.default_container_name
        
        container = self.factory.create_container(
            container_name, db_session, self.default_config
        )
        
        if services:
            for service_name in services:
                try:
                    container.get_service(service_name)
                    logger.info(f"서비스 초기화 완료: {service_name}")
                except Exception as e:
                    logger.error(f"서비스 초기화 실패 ({service_name}): {e}")
        
        return container
    
    async def get_service_health_check(
        self, 
        db_session: Session,
        container_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """서비스 헬스 체크"""
        container_name = container_name or self.default_container_name
        
        async with self.get_service_container(db_session, container_name) as container:
            return await container.get_all_service_status()
    
    async def reload_config(
        self, 
        new_config: Dict[str, Any],
        container_name: Optional[str] = None
    ):
        """설정 리로드"""
        container_name = container_name or self.default_container_name
        
        # 기존 컨테이너 정리
        if self.factory.get_container(container_name):
            container = self.factory.get_container(container_name)
            await container.cleanup_all_services()
            self.factory.remove_container(container_name)
        
        # 새 설정 적용
        self.default_config = {**self.default_config, **new_config}
        logger.info(f"설정 리로드 완료: {container_name}")
    
    async def shutdown(self):
        """모든 서비스 종료"""
        await self.factory.cleanup_all_containers()
        logger.info("서비스 매니저 종료 완료")


# 전역 서비스 매니저 인스턴스
_service_manager: Optional[ServiceManager] = None

def get_service_manager(config: Optional[Dict[str, Any]] = None) -> ServiceManager:
    """전역 서비스 매니저 가져오기"""
    global _service_manager
    if _service_manager is None:
        _service_manager = ServiceManager(config)
    return _service_manager

async def initialize_global_services(
    db_session: Session,
    config: Optional[Dict[str, Any]] = None,
    services: List[str] = None
) -> ServiceContainer:
    """전역 서비스 초기화"""
    manager = get_service_manager(config)
    return await manager.initialize_services(db_session, services)

async def get_global_service_container(
    db_session: Session,
    config: Optional[Dict[str, Any]] = None
):
    """전역 서비스 컨테이너 컨텍스트 매니저"""
    manager = get_service_manager(config)
    async with manager.get_service_container(db_session, config=config) as container:
        yield container

async def shutdown_global_services():
    """전역 서비스 종료"""
    global _service_manager
    if _service_manager:
        await _service_manager.shutdown()
        _service_manager = None