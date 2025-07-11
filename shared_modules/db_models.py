"""
데이터베이스 모델 v4 - 실제 DDL과 완전 일치
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, JSON, DECIMAL, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared_modules.database import Base

class User(Base):
    """사용자 테이블 - DDL과 완전 일치"""
    __tablename__ = 'user'
    __table_args__ = {'extend_existing': True}
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), unique=True, nullable=False)
    nickname = Column(String(50), nullable=False)
    business_type = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    provider = Column(String(32), nullable=False)
    social_id = Column(String(128), nullable=False)
    admin = Column(Boolean, nullable=False)
    experience = Column(Boolean, nullable=False)
    access_token = Column(String(1024), nullable=False)
    refresh_token = Column(String(1024), nullable=True)
    
    # 관계
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    automation_tasks = relationship("AutomationTask", back_populates="user", cascade="all, delete-orphan")
    template_messages = relationship("TemplateMessage", back_populates="user", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")

class FAQ(Base):
    """FAQ 테이블"""
    __tablename__ = 'faq'
    __table_args__ = {'extend_existing': True}
    
    faq_id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False)
    question = Column(Text, nullable=False)
    view_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)

class Conversation(Base):
    """대화 세션 테이블"""
    __tablename__ = 'conversation'
    __table_args__ = {'extend_existing': True}
    
    conversation_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    started_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    ended_at = Column(TIMESTAMP, nullable=True)
    is_visible = Column(Boolean, nullable=False, default=True)
    
    # 관계
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="conversation", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="conversation", cascade="all, delete-orphan")
    automation_tasks = relationship("AutomationTask", back_populates="conversation", cascade="all, delete-orphan")

class Feedback(Base):
    """피드백 테이블"""
    __tablename__ = 'feedback'
    __table_args__ = (
        CheckConstraint('rating BETWEEN 1 AND 5', name='ck_rating'),
        {'extend_existing': True}
    )
    
    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    conversation_id = Column(Integer, ForeignKey('conversation.conversation_id'), nullable=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    
    # 관계
    user = relationship("User", back_populates="feedbacks")
    conversation = relationship("Conversation", back_populates="feedbacks")

class Message(Base):
    """메시지 테이블"""
    __tablename__ = 'message'
    __table_args__ = (
        CheckConstraint("sender_type IN ('USER', 'AGENT')", name='ck_sender_type'),
        {'extend_existing': True}
    )
    
    message_id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversation.conversation_id'), nullable=False)
    sender_type = Column(String(20), nullable=False)
    agent_type = Column(String(50), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    
    # 관계
    conversation = relationship("Conversation", back_populates="messages")

class PHQ9Result(Base):
    """PHQ-9 검사 결과 테이블"""
    __tablename__ = 'phq9_result'
    __table_args__ = {'extend_existing': True}
    
    user_id = Column(Integer, ForeignKey('user.user_id'), primary_key=True)
    score = Column(Integer, nullable=False)
    level = Column(Integer, nullable=True)
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)
    
    # 관계
    user = relationship("User", backref="phq9_result")

class Report(Base):
    """리포트 테이블"""
    __tablename__ = 'report'
    __table_args__ = {'extend_existing': True}
    
    report_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    conversation_id = Column(Integer, ForeignKey('conversation.conversation_id'), nullable=True)
    report_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    content_data = Column(JSON, nullable=True)
    file_url = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    
    # 관계
    user = relationship("User", back_populates="reports")
    conversation = relationship("Conversation", back_populates="reports")

class Subscription(Base):
    """구독 테이블"""
    __tablename__ = 'subscription'
    __table_args__ = (
        CheckConstraint("plan_type IN ('BASIC', 'PREMIUM', 'ENTERPRISE')", name='ck_plan_type'),
        CheckConstraint('monthly_fee >= 0', name='subscription_chk_1'),
        {'extend_existing': True}
    )
    
    subscription_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    plan_type = Column(String(50), nullable=False)
    monthly_fee = Column(DECIMAL(10, 2), nullable=False)
    start_date = Column(TIMESTAMP, nullable=False)
    end_date = Column(TIMESTAMP, nullable=True)
    
    # 관계
    user = relationship("User", back_populates="subscriptions")

class TemplateMessage(Base):
    """템플릿 메시지 테이블"""
    __tablename__ = 'template_message'
    __table_args__ = (
        CheckConstraint("channel_type IN ('EMAIL', 'SMS', 'PUSH', 'SLACK')", name='ck_channel_type'),
        {'extend_existing': True}
    )
    
    template_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    template_type = Column(String(50), nullable=False)
    channel_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    content_type = Column(String(20), nullable=True)
    
    # 관계
    user = relationship("User", back_populates="template_messages")
    automation_tasks = relationship("AutomationTask", back_populates="template", cascade="all, delete-orphan")

class AutomationTask(Base):
    """자동화 작업 테이블"""
    __tablename__ = 'automation_task'
    __table_args__ = (
        CheckConstraint("status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')", name='ck_status'),
        {'extend_existing': True}
    )
    
    task_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    conversation_id = Column(Integer, ForeignKey('conversation.conversation_id'), nullable=True)
    task_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    template_id = Column(Integer, ForeignKey('template_message.template_id'), nullable=True)
    task_data = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False)
    scheduled_at = Column(TIMESTAMP, nullable=True)
    executed_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    
    # 관계
    user = relationship("User", back_populates="automation_tasks")
    conversation = relationship("Conversation", back_populates="automation_tasks")
    template = relationship("TemplateMessage", back_populates="automation_tasks")

# Vector store collections table (벡터 스토어용)
class VectorCollection(Base):
    """벡터 스토어 컬렉션 테이블"""
    __tablename__ = 'collections'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    topic = Column(String(200))
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
