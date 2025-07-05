"""
데이터베이스 헬퍼 공통 모듈
"""

import os
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# 데이터베이스 관련 import 시도
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.ext.declarative import declarative_base
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Session = None
    declarative_base = None

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

try:
    import aiomysql
    AIOMYSQL_AVAILABLE = True
except ImportError:
    AIOMYSQL_AVAILABLE = False


class DatabaseHelper:
    """데이터베이스 작업을 위한 공통 헬퍼 클래스"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        self.engine = None
        self.SessionLocal = None
        
        if SQLALCHEMY_AVAILABLE and self.database_url:
            self._setup_sqlalchemy()
    
    def _setup_sqlalchemy(self):
        """SQLAlchemy 설정"""
        try:
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=300
            )
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            logger.info("SQLAlchemy 데이터베이스 연결 설정 완료")
        except Exception as e:
            logger.error(f"SQLAlchemy 설정 실패: {e}")
    
    def get_session(self) -> Optional[Session]:
        """데이터베이스 세션 반환"""
        if not SQLALCHEMY_AVAILABLE or not self.SessionLocal:
            logger.warning("SQLAlchemy가 설정되지 않았습니다")
            return None
        
        try:
            return self.SessionLocal()
        except Exception as e:
            logger.error(f"데이터베이스 세션 생성 실패: {e}")
            return None
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """사용자 ID로 사용자 정보 조회"""
        if not SQLALCHEMY_AVAILABLE:
            return None
        
        session = self.get_session()
        if not session:
            return None
        
        try:
            result = session.execute(
                text("SELECT * FROM users WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None
        except Exception as e:
            logger.error(f"사용자 조회 실패: {e}")
            return None
        finally:
            session.close()
    
    async def get_user_email(self, user_id: int) -> Optional[str]:
        """사용자 이메일 주소 조회"""
        user = await self.get_user_by_id(user_id)
        return user.get("email") if user else None
    
    async def get_user_phone(self, user_id: int) -> Optional[str]:
        """사용자 전화번호 조회"""
        user = await self.get_user_by_id(user_id)
        return user.get("phone_number") if user else None
    
    async def get_notification_settings(self, user_id: int) -> Dict[str, bool]:
        """사용자 알림 설정 조회"""
        if not SQLALCHEMY_AVAILABLE:
            return {
                "app_notification": True,
                "email_notification": True,
                "sms_notification": True
            }
        
        session = self.get_session()
        if not session:
            return {
                "app_notification": True,
                "email_notification": True,
                "sms_notification": True
            }
        
        try:
            result = session.execute(
                text("SELECT * FROM notification_settings WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            if row:
                settings = dict(row._mapping)
                return {
                    "app_notification": settings.get("app_notification", True),
                    "email_notification": settings.get("email_notification", True),
                    "sms_notification": settings.get("sms_notification", True)
                }
            else:
                return {
                    "app_notification": True,
                    "email_notification": True,
                    "sms_notification": True
                }
        except Exception as e:
            logger.error(f"알림 설정 조회 실패: {e}")
            return {
                "app_notification": True,
                "email_notification": True,
                "sms_notification": True
            }
        finally:
            session.close()
    
    async def update_notification_settings(self, user_id: int, settings: Dict[str, bool]) -> bool:
        """사용자 알림 설정 업데이트"""
        if not SQLALCHEMY_AVAILABLE:
            return False
        
        session = self.get_session()
        if not session:
            return False
        
        try:
            # 기존 설정 확인
            result = session.execute(
                text("SELECT user_id FROM notification_settings WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            exists = result.fetchone() is not None
            
            if exists:
                # 업데이트
                update_fields = []
                params = {"user_id": user_id}
                
                for key, value in settings.items():
                    if key in ["app_notification", "email_notification", "sms_notification"]:
                        update_fields.append(f"{key} = :{key}")
                        params[key] = value
                
                if update_fields:
                    query = f"UPDATE notification_settings SET {', '.join(update_fields)} WHERE user_id = :user_id"
                    session.execute(text(query), params)
            else:
                # 새로 생성
                params = {
                    "user_id": user_id,
                    "app_notification": settings.get("app_notification", True),
                    "email_notification": settings.get("email_notification", True),
                    "sms_notification": settings.get("sms_notification", True)
                }
                session.execute(
                    text("""
                        INSERT INTO notification_settings 
                        (user_id, app_notification, email_notification, sms_notification)
                        VALUES (:user_id, :app_notification, :email_notification, :sms_notification)
                    """),
                    params
                )
            
            session.commit()
            return True
        except Exception as e:
            logger.error(f"알림 설정 업데이트 실패: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    async def save_notification_log(self, user_id: int, notification_type: str, 
                                   message: str, success: bool, error_message: Optional[str] = None) -> bool:
        """알림 로그 저장"""
        if not SQLALCHEMY_AVAILABLE:
            return False
        
        session = self.get_session()
        if not session:
            return False
        
        try:
            from datetime import datetime
            params = {
                "user_id": user_id,
                "notification_type": notification_type,
                "message": message,
                "success": success,
                "error_message": error_message,
                "created_at": datetime.now()
            }
            
            session.execute(
                text("""
                    INSERT INTO notification_logs 
                    (user_id, notification_type, message, success, error_message, created_at)
                    VALUES (:user_id, :notification_type, :message, :success, :error_message, :created_at)
                """),
                params
            )
            session.commit()
            return True
        except Exception as e:
            logger.error(f"알림 로그 저장 실패: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    async def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """작업 ID로 작업 정보 조회"""
        if not SQLALCHEMY_AVAILABLE:
            return None
        
        session = self.get_session()
        if not session:
            return None
        
        try:
            result = session.execute(
                text("SELECT * FROM tasks WHERE task_id = :task_id"),
                {"task_id": task_id}
            )
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None
        except Exception as e:
            logger.error(f"작업 조회 실패: {e}")
            return None
        finally:
            session.close()
    
    async def update_task_status(self, task_id: str, status: str, 
                                result_data: Optional[Dict[str, Any]] = None) -> bool:
        """작업 상태 업데이트"""
        if not SQLALCHEMY_AVAILABLE:
            return False
        
        session = self.get_session()
        if not session:
            return False
        
        try:
            from datetime import datetime
            import json
            
            params = {
                "task_id": task_id,
                "status": status,
                "updated_at": datetime.now()
            }
            
            update_fields = ["status = :status", "updated_at = :updated_at"]
            
            if result_data:
                params["result_data"] = json.dumps(result_data)
                update_fields.append("result_data = :result_data")
            
            query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE task_id = :task_id"
            result = session.execute(text(query), params)
            session.commit()
            
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"작업 상태 업데이트 실패: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    async def execute_raw_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[List[Dict[str, Any]]]:
        """원시 SQL 쿼리 실행"""
        if not SQLALCHEMY_AVAILABLE:
            return None
        
        session = self.get_session()
        if not session:
            return None
        
        try:
            result = session.execute(text(query), params or {})
            if result.returns_rows:
                return [dict(row._mapping) for row in result.fetchall()]
            else:
                session.commit()
                return []
        except Exception as e:
            logger.error(f"SQL 쿼리 실행 실패: {e}")
            session.rollback()
            return None
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """데이터베이스 연결 상태 확인"""
        if not SQLALCHEMY_AVAILABLE or not self.engine:
            return False
        
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"데이터베이스 연결 확인 실패: {e}")
            return False


# 전역 인스턴스
_db_helper = None
_redis_helper = None

def get_db_helper(database_url: Optional[str] = None) -> DatabaseHelper:
    """DatabaseHelper 싱글톤 인스턴스 반환"""
    global _db_helper
    if _db_helper is None:
        _db_helper = DatabaseHelper(database_url)
    return _db_helper

def get_db_session() -> Optional[Session]:
    """데이터베이스 세션 반환 (편의 함수)"""
    return get_db_helper().get_session()
