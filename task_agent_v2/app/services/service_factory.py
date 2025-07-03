# /app/services/service_factory.py
"""
서비스 팩토리 및 의존성 주입 컨테이너
"""

import os
import logging
from typing import Dict, Any, Optional, Type, TypeVar, Generic
from sqlalchemy.orm import Session
from contextlib import contextmanager

from .common.base_service import BaseService
from .common.user_service import UserService
from .common.config_service import ConfigService
from .common.notification_service import NotificationService
from .email_service import EmailService
from .sms_service import SMSService
from .google_calendar_service import GoogleCalendarService
from .reminder_service import ReminderService
from .improved_automation_service import ImprovedAutomationService

# 타입 변수
T = TypeVar('T', bound=BaseService)

logger = logging.getLogger(__name__)

class ServiceContainer:
    """서비스 의존성 주입 컨테이너"""
    
    def __init__(self, db_session: Session, config: Optional[Dict[str, Any]] = None):
        self.db_session = db_session
        self.config = config or {}
        self._services: Dict[str, BaseService] = {}
        self._service_classes: Dict[str, Type[BaseService]] = {}
        self._initialized = False
        
        # 서비스 클래스들 등록
        self._register_service_classes()
        
        logger.info("서비스 컨테이너 초기화 완료")
    
    def _register_service_classes(self):
        """서비스 클래스들을 컨테이너에 등록"""
        self._service_classes = {
            'user_service': UserService,
            'config_service': ConfigService,
            'notification_service': NotificationService,
            'email_service': EmailService,
            'sms_service': SMSService,
            'google_calendar_service': GoogleCalendarService,
            'reminder_service': ReminderService,
            'automation_service': ImprovedAutomationService
        }
    
    def get_service(self, service_name: str) -> BaseService:
        """서비스 인스턴스 가져오기 (싱글톤)"""
        if service_name not in self._services:
            if service_name not in self._service_classes:
                raise ValueError(f"알 수 없는 서비스: {service_name}")
            
            service_class = self._service_classes[service_name]
            self._services[service_name] = service_class(self.db_session, self.config)
            
            logger.debug(f"서비스 인스턴스 생성: {service_name}")
        
        return self._services[service_name]
    
    def get_user_service(self) -> UserService:
        """사용자 서비스 가져오기"""
        return self.get_service('user_service')
    
    def get_config_service(self) -> ConfigService:
        """설정 서비스 가져오기"""
        return self.get_service('config_service')
    
    def get_notification_service(self) -> NotificationService:
        """알림 서비스 가져오기"""
        return self.get_service('notification_service')
    
    def get_email_service(self) -> EmailService:
        """이메일 서비스 가져오기"""
        return self.get_service('email_service')
    
    def get_sms_service(self) -> SMSService:
        """SMS 서비스 가져오기"""
        return self.get_service('sms_service')
    
    def get_google_calendar_service(self) -> GoogleCalendarService:
        """구글 캘린더 서비스 가져오기"""
        return self.get_service('google_calendar_service')
    
    def get_reminder_service(self) -> ReminderService:
        """리마인더 서비스 가져오기"""
        return self.get_service('reminder_service')
    
    def get_automation_service(self) -> ImprovedAutomationService:
        """자동화 서비스 가져오기"""
        return self.get_service('automation_service')
    
    async def get_all_service_status(self) -> Dict[str, Any]:
        """모든 서비스 상태 조회"""
        status_results = {}
        
        for service_name in self._service_classes.keys():
            try:
                service = self.get_service(service_name)
                status = await service.get_service_status()
                status_results[service_name] = status
            except Exception as e:
                logger.error(f"서비스 상태 조회 실패 ({service_name}): {e}")
                status_results[service_name] = {
                    "service": service_name,
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "container_status": "healthy",
            "total_services": len(self._service_classes),
            "initialized_services": len(self._services),
            "services": status_results
        }
    
    async def cleanup_all_services(self):
        """모든 서비스 정리"""
        for service_name, service in self._services.items():
            try:
                await service.cleanup()
                logger.info(f"서비스 정리 완료: {service_name}")
            except Exception as e:
                logger.error(f"서비스 정리 실패 ({service_name}): {e}")
        
        self._services.clear()
        logger.info("모든 서비스 정리 완료")
    
    def register_custom_service(self, service_name: str, service_class: Type[BaseService]):
        """커스텀 서비스 등록"""
        self._service_classes[service_name] = service_class
        logger.info(f"커스텀 서비스 등록: {service_name}")
    
    def is_service_available(self, service_name: str) -> bool:
        """서비스 사용 가능 여부 확인"""
        try:
            service = self.get_service(service_name)
            return True
        except Exception:
            return False


class ServiceFactory:
    """서비스 팩토리 (컨테이너의 상위 레벨 인터페이스)"""
    
    _instance: Optional['ServiceFactory'] = None
    _containers: Dict[str, ServiceContainer] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def create_container(
        cls, 
        container_name: str, 
        db_session: Session, 
        config: Optional[Dict[str, Any]] = None
    ) -> ServiceContainer:
        """새로운 서비스 컨테이너 생성"""
        if container_name in cls._containers:
            logger.warning(f"컨테이너 {container_name}가 이미 존재합니다. 기존 컨테이너를 반환합니다.")
            return cls._containers[container_name]
        
        container = ServiceContainer(db_session, config)
        cls._containers[container_name] = container
        
        logger.info(f"서비스 컨테이너 생성: {container_name}")
        return container
    
    @classmethod
    def get_container(cls, container_name: str) -> Optional[ServiceContainer]:
        """기존 컨테이너 가져오기"""
        return cls._containers.get(container_name)
    
    @classmethod
    def remove_container(cls, container_name: str) -> bool:
        """컨테이너 제거"""
        if container_name in cls._containers:
            container = cls._containers.pop(container_name)
            # 정리 작업은 비동기이므로 별도로 호출해야 함
            logger.info(f"서비스 컨테이너 제거: {container_name}")
            return True
        return False
    
    @classmethod
    async def cleanup_all_containers(cls):
        """모든 컨테이너 정리"""
        for container_name, container in cls._containers.items():
            try:
                await container.cleanup_all_services()
                logger.info(f"컨테이너 정리 완료: {container_name}")
            except Exception as e:
                logger.error(f"컨테이너 정리 실패 ({container_name}): {e}")
        
        cls._containers.clear()
        logger.info("모든 컨테이너 정리 완료")
    
    @classmethod
    def list_containers(cls) -> List[str]:
        """등록된 컨테이너 목록"""
        return list(cls._containers.keys())