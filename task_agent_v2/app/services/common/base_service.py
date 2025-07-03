# /app/services/common/base_service.py
"""
공통 서비스 기반 클래스
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class BaseService(ABC):
    """모든 서비스의 기반 클래스"""
    
    def __init__(self, db_session: Session, config: Optional[Dict[str, Any]] = None):
        self.db = db_session
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abstractmethod
    async def get_service_status(self) -> Dict[str, Any]:
        """서비스 상태 조회"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """서비스 정리"""
        pass
