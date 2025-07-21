"""
데이터베이스 헬퍼 공통 모듈 v2
공통 모듈의 database를 활용하여 데이터베이스 작업 수행
"""

import sys
import os
from typing import Dict, Any, Optional, List
import logging

from shared_modules.database import get_session, engine
from shared_modules.db_models import User, Conversation, Message, AutomationTask
from shared_modules.env_config import get_config

logger = logging.getLogger(__name__)

class AutomationDatabaseHelper:
    """자동화 작업을 위한 데이터베이스 헬퍼 클래스 (공통 모듈 기반)"""
    
    def __init__(self):
        """데이터베이스 헬퍼 초기화"""
        self.config = get_config()
        
    def get_session(self):
        """데이터베이스 세션 반환 (공통 모듈 활용)"""
        try:
            return get_session()
        except Exception as e:
            logger.error(f"데이터베이스 세션 생성 실패: {e}")
            return None
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """사용자 ID로 사용자 정보 조회"""
        session = self.get_session()
        if not session:
            return None
        
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                return {
                    "user_id": user.user_id,
                    "email": user.email,
                    "nickname": user.nickname,
                    "business_type": user.business_type,
                    "created_at": user.created_at,
                    "admin": user.admin
                }
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
    
    async def get_automation_task_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """자동화 작업 ID로 작업 정보 조회"""
        session = self.get_session()
        if not session:
            return None
        
        try:
            task = session.query(AutomationTask).filter(AutomationTask.task_id == task_id).first()
            if task:
                return {
                    "task_id": task.task_id,
                    "user_id": task.user_id,
                    "conversation_id": task.conversation_id,
                    "task_type": task.task_type,
                    "title": task.title,
                    "task_data": task.task_data,
                    "status": task.status,
                    "scheduled_at": task.scheduled_at,
                    "executed_at": task.executed_at,
                    "created_at": task.created_at
                }
            return None
        except Exception as e:
            logger.error(f"자동화 작업 조회 실패: {e}")
            return None
        finally:
            session.close()
    
    async def update_automation_task_status(self, task_id: int, status: str, 
                                          executed_at: Optional[Any] = None,
                                          result_data: Optional[Dict[str, Any]] = None) -> bool:
        """자동화 작업 상태 업데이트"""
        session = self.get_session()
        if not session:
            return False
        
        try:
            task = session.query(AutomationTask).filter(AutomationTask.task_id == task_id).first()
            if not task:
                logger.warning(f"자동화 작업을 찾을 수 없음: {task_id}")
                return False
            
            # 상태 업데이트
            task.status = status
            
            if executed_at:
                task.executed_at = executed_at
            
            # 결과 데이터가 있으면 task_data에 추가
            if result_data:
                if task.task_data is None:
                    task.task_data = {}
                task.task_data.update({"result": result_data})
            
            session.commit()
            logger.info(f"자동화 작업 상태 업데이트 완료: task_id={task_id}, status={status}")
            return True
            
        except Exception as e:
            logger.error(f"자동화 작업 상태 업데이트 실패: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    async def get_pending_automation_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """대기 중인 자동화 작업 목록 조회"""
        session = self.get_session()
        if not session:
            return []
        
        try:
            tasks = session.query(AutomationTask)\
                          .filter(AutomationTask.status == 'pending')\
                          .order_by(AutomationTask.created_at.asc())\
                          .limit(limit)\
                          .all()
            
            result = []
            for task in tasks:
                result.append({
                    "task_id": task.task_id,
                    "user_id": task.user_id,
                    "conversation_id": task.conversation_id,
                    "task_type": task.task_type,
                    "title": task.title,
                    "task_data": task.task_data,
                    "status": task.status,
                    "scheduled_at": task.scheduled_at,
                    "created_at": task.created_at
                })
            
            return result
            
        except Exception as e:
            logger.error(f"대기 중인 자동화 작업 조회 실패: {e}")
            return []
        finally:
            session.close()
    
    async def get_user_automation_tasks(self, user_id: int, status: Optional[str] = None, 
                                      limit: int = 50) -> List[Dict[str, Any]]:
        """사용자의 자동화 작업 목록 조회"""
        session = self.get_session()
        if not session:
            return []
        
        try:
            query = session.query(AutomationTask).filter(AutomationTask.user_id == user_id)
            
            if status:
                query = query.filter(AutomationTask.status == status)
            
            tasks = query.order_by(AutomationTask.created_at.desc()).limit(limit).all()
            
            result = []
            for task in tasks:
                result.append({
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "title": task.title,
                    "status": task.status,
                    "scheduled_at": task.scheduled_at,
                    "executed_at": task.executed_at,
                    "created_at": task.created_at
                })
            
            return result
            
        except Exception as e:
            logger.error(f"사용자 자동화 작업 조회 실패: {e}")
            return []
        finally:
            session.close()
    
    async def save_automation_log(self, task_id: int, log_type: str, 
                                message: str, success: bool, 
                                error_message: Optional[str] = None) -> bool:
        """자동화 작업 로그 저장"""
        session = self.get_session()
        if not session:
            return False
        
        try:
            from datetime import datetime
            from sqlalchemy import text
            
            # 로그 테이블이 있다면 저장 (없으면 스킵)
            log_query = text("""
                INSERT INTO automation_logs 
                (task_id, log_type, message, success, error_message, created_at)
                VALUES (:task_id, :log_type, :message, :success, :error_message, :created_at)
            """)
            
            session.execute(log_query, {
                "task_id": task_id,
                "log_type": log_type,
                "message": message,
                "success": success,
                "error_message": error_message,
                "created_at": datetime.now()
            })
            
            session.commit()
            return True
            
        except Exception as e:
            # 로그 테이블이 없는 경우 등은 조용히 처리
            logger.debug(f"자동화 로그 저장 실패 (선택사항): {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    async def get_conversation_context(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """대화 컨텍스트 조회"""
        session = self.get_session()
        if not session:
            return None
        
        try:
            conversation = session.query(Conversation)\
                                 .filter(Conversation.conversation_id == conversation_id)\
                                 .first()
            
            if conversation:
                return {
                    "conversation_id": conversation.conversation_id,
                    "user_id": conversation.user_id,
                    "started_at": conversation.started_at,
                    "ended_at": conversation.ended_at,
                    "is_visible": conversation.is_visible
                }
            return None
            
        except Exception as e:
            logger.error(f"대화 컨텍스트 조회 실패: {e}")
            return None
        finally:
            session.close()
    
    async def get_recent_messages(self, conversation_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 메시지 목록 조회"""
        session = self.get_session()
        if not session:
            return []
        
        try:
            messages = session.query(Message)\
                             .filter(Message.conversation_id == conversation_id)\
                             .order_by(Message.created_at.desc())\
                             .limit(limit)\
                             .all()
            
            result = []
            for msg in messages:
                result.append({
                    "message_id": msg.message_id,
                    "sender_type": msg.sender_type,
                    "agent_type": msg.agent_type,
                    "content": msg.content,
                    "created_at": msg.created_at
                })
            
            return result
            
        except Exception as e:
            logger.error(f"최근 메시지 조회 실패: {e}")
            return []
        finally:
            session.close()
    
    async def check_user_permissions(self, user_id: int, permission: str) -> bool:
        """사용자 권한 확인"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # 관리자는 모든 권한 허용
        if user.get("admin", False):
            return True
        
        # 기본적으로는 모든 사용자에게 자동화 권한 허용
        # 추후 세분화된 권한 체계 구현 가능
        allowed_permissions = [
            "automation_create",
            "automation_read",
            "automation_update",
            "automation_delete"
        ]
        
        return permission in allowed_permissions
    
    def health_check(self) -> bool:
        """데이터베이스 연결 상태 확인"""
        try:
            if not engine:
                return False
            
            with engine.connect() as connection:
                from sqlalchemy import text
                connection.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"데이터베이스 연결 확인 실패: {e}")
            return False
    
    async def get_task_statistics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """작업 통계 조회"""
        session = self.get_session()
        if not session:
            return {}
        
        try:
            from sqlalchemy import func
            
            query = session.query(
                AutomationTask.status,
                func.count(AutomationTask.task_id).label('count')
            )
            
            if user_id:
                query = query.filter(AutomationTask.user_id == user_id)
            
            stats = query.group_by(AutomationTask.status).all()
            
            result = {
                "total": 0,
                "pending": 0,
                "processing": 0,
                "success": 0,
                "failed": 0,
                "cancelled": 0
            }
            
            for status, count in stats:
                result[status] = count
                result["total"] += count
            
            return result
            
        except Exception as e:
            logger.error(f"작업 통계 조회 실패: {e}")
            return {}
        finally:
            session.close()


# 전역 인스턴스
_automation_db_helper = None

def get_automation_db_helper() -> AutomationDatabaseHelper:
    """AutomationDatabaseHelper 싱글톤 인스턴스 반환"""
    global _automation_db_helper
    if _automation_db_helper is None:
        _automation_db_helper = AutomationDatabaseHelper()
    return _automation_db_helper

# 편의 함수들
async def get_user_email(user_id: int) -> Optional[str]:
    """사용자 이메일 조회 (편의 함수)"""
    return await get_automation_db_helper().get_user_email(user_id)

async def get_automation_task(task_id: int) -> Optional[Dict[str, Any]]:
    """자동화 작업 조회 (편의 함수)"""
    return await get_automation_db_helper().get_automation_task_by_id(task_id)

async def update_task_status(task_id: int, status: str, **kwargs) -> bool:
    """작업 상태 업데이트 (편의 함수)"""
    return await get_automation_db_helper().update_automation_task_status(task_id, status, **kwargs)

# 기존 코드와의 호환성을 위한 별칭
DatabaseHelper = AutomationDatabaseHelper
get_db_helper = get_automation_db_helper
