"""
간소화된 데이터베이스 서비스 v3
"""

import hashlib
import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from database import get_db_session
from db_models import User, Conversation, Message, AutomationTask

logger = logging.getLogger(__name__)

class DatabaseService:
    """기본 데이터베이스 서비스 클래스"""
    
    def __init__(self):
        self.session = None
    
    def __enter__(self):
        self.session = get_db_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type is None:
                self.session.commit()
            else:
                self.session.rollback()
            self.session.close()

class UserService(DatabaseService):
    """사용자 관리 서비스"""
    
    def create_user(self, email: str, password: str, nickname: str = None, 
                   business_type: str = None) -> User:
        """사용자 생성"""
        hashed_password = self._hash_password(password)
        
        user = User(
            email=email,
            password=hashed_password,
            nickname=nickname or email.split('@')[0],
            business_type=business_type
        )
        
        self.session.add(user)
        self.session.flush()
        return user
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """ID로 사용자 조회"""
        return self.session.query(User).filter(User.user_id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        return self.session.query(User).filter(User.email == email).first()
    
    def verify_password(self, email: str, password: str) -> Optional[User]:
        """비밀번호 검증"""
        user = self.get_user_by_email(email)
        if user and self._verify_password(password, user.password):
            return user
        return None
    
    def _hash_password(self, password: str) -> str:
        """비밀번호 해시화"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """비밀번호 검증"""
        return self._hash_password(password) == hashed

class ConversationService(DatabaseService):
    """대화 관리 서비스"""
    
    def create_conversation(self, user_id: int, conversation_type: str = "general") -> Conversation:
        """대화 세션 생성"""
        conversation = Conversation(
            user_id=user_id,
            conversation_type=conversation_type,
            started_at=datetime.now(),
            is_visible=True
        )
        
        self.session.add(conversation)
        self.session.flush()
        return conversation
    
    def get_conversation_by_id(self, conversation_id: int) -> Optional[Conversation]:
        """ID로 대화 세션 조회"""
        return self.session.query(Conversation).filter(
            Conversation.conversation_id == conversation_id
        ).first()
    
    def get_user_conversations(self, user_id: int, visible_only: bool = True) -> List[Conversation]:
        """사용자의 대화 세션 목록 조회"""
        query = self.session.query(Conversation).filter(Conversation.user_id == user_id)
        
        if visible_only:
            query = query.filter(Conversation.is_visible == True)
        
        return query.order_by(Conversation.started_at.desc()).all()
    
    def end_conversation(self, conversation_id: int) -> bool:
        """대화 세션 종료"""
        conversation = self.get_conversation_by_id(conversation_id)
        if conversation:
            conversation.ended_at = datetime.now()
            return True
        return False

class MessageService(DatabaseService):
    """메시지 관리 서비스"""
    
    def create_message(self, conversation_id: int, sender_type: str, content: str, 
                      agent_type: str = None) -> Message:
        """메시지 생성"""
        message = Message(
            conversation_id=conversation_id,
            sender_type=sender_type,
            agent_type=agent_type,
            content=content
        )
        
        self.session.add(message)
        self.session.flush()
        return message
    
    def get_conversation_messages(self, conversation_id: int, limit: int = 100, 
                                offset: int = 0) -> List[Message]:
        """대화의 메시지 목록 조회"""
        return self.session.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.created_at.asc()
        ).offset(offset).limit(limit).all()
    
    def get_recent_messages(self, conversation_id: int, limit: int = 10) -> List[Message]:
        """최근 메시지 조회"""
        return self.session.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.created_at.desc()
        ).limit(limit).all()

class AutomationTaskService(DatabaseService):
    """자동화 작업 관리 서비스"""
    
    def get_user_tasks(self, user_id: int, status: str = None, limit: int = 50) -> List[AutomationTask]:
        """사용자의 자동화 작업 목록 조회"""
        query = self.session.query(AutomationTask).filter(AutomationTask.user_id == user_id)
        
        if status:
            query = query.filter(AutomationTask.status == status)
        
        return query.order_by(AutomationTask.created_at.desc()).limit(limit).all()
    
    def get_pending_tasks(self, limit: int = 100) -> List[AutomationTask]:
        """대기중인 자동화 작업 조회"""
        return self.session.query(AutomationTask).filter(
            AutomationTask.status == "pending"
        ).order_by(
            AutomationTask.scheduled_at.asc()
        ).limit(limit).all()

# 서비스 인스턴스들 (컨텍스트 매니저로 사용)
user_service = UserService
conversation_service = ConversationService
message_service = MessageService
automation_task_service = AutomationTaskService
