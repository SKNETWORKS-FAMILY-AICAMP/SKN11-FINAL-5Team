"""
간소화된 데이터베이스 모델 v3
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    """사용자 테이블"""
    __tablename__ = 'user'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    nickname = Column(String(100))
    business_type = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    admin = Column(Boolean, default=False)
    
    # 관계
    conversations = relationship("Conversation", back_populates="user")
    automation_tasks = relationship("AutomationTask", back_populates="user")

class Conversation(Base):
    """대화 세션 테이블"""
    __tablename__ = 'conversation'
    
    conversation_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    conversation_type = Column(String(50), default="general")
    started_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    ended_at = Column(TIMESTAMP)
    is_visible = Column(Boolean, default=True)
    
    # 관계
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    """메시지 테이블"""
    __tablename__ = 'message'
    
    message_id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversation.conversation_id'), nullable=False)
    sender_type = Column(String(50), nullable=False)  # user, agent
    agent_type = Column(String(50))  # task_agent, automation_agent
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    # 관계
    conversation = relationship("Conversation", back_populates="messages")

class AutomationTask(Base):
    """자동화 작업 테이블"""
    __tablename__ = 'automation_task'
    
    task_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    conversation_id = Column(Integer, ForeignKey('conversation.conversation_id'))
    task_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    task_data = Column(JSON)
    status = Column(String(20), default="pending")
    scheduled_at = Column(TIMESTAMP)
    executed_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    # 관계
    user = relationship("User", back_populates="automation_tasks")
