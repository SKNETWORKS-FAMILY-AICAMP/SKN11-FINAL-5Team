"""
SQLAlchemy ORM 모델 정의
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.db.database import Base

class User(Base):
    """사용자 테이블"""
    __tablename__ = 'user'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True, comment='사용자 고유 ID')
    email = Column(String(255), unique=True, nullable=False, comment='로그인용 이메일')
    password = Column(String(255), nullable=False, comment='비밀번호 (해시 처리된 값)')
    nickname = Column(String(100), comment='사용자 닉네임')
    business_type = Column(String(100), comment='사용자의 업종')
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment='가입일')
    admin = Column(Boolean, default=False, comment='관리자')
    
    # Google Calendar OAuth 토큰 관련 필드
    access_token = Column(Text, comment='Google 액세스 토큰')
    google_refresh_token = Column(Text, comment='Google 리프레시 토큰')
    google_token_expires_in = Column(Integer, comment='Google 토큰 만료 시간(초)')
    google_token_created_at = Column(TIMESTAMP, comment='Google 토큰 생성 시각')
    
    # 관계 설정
    conversations = relationship("Conversation", back_populates="user")
    automation_tasks = relationship("AutomationTask", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")

class Conversation(Base):
    """상담 세션 테이블"""
    __tablename__ = 'conversation'
    
    conversation_id = Column(Integer, primary_key=True, autoincrement=True, comment='상담 세션 ID')
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False, comment='사용자 ID')
    started_at = Column(TIMESTAMP, comment='대화 시작 시각')
    ended_at = Column(TIMESTAMP, comment='대화 종료 시각')
    is_visible = Column(Boolean, nullable=False, default=False, comment='세션 삭제 여부')
    
    # 관계 설정
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
    automation_tasks = relationship("AutomationTask", back_populates="conversation")
    feedbacks = relationship("Feedback", back_populates="conversation")

class Message(Base):
    """메시지 테이블"""
    __tablename__ = 'message'
    
    message_id = Column(Integer, primary_key=True, autoincrement=True, comment='메시지 ID')
    conversation_id = Column(Integer, ForeignKey('conversation.conversation_id'), nullable=False, comment='소속 상담 ID')
    sender_type = Column(String(50), comment='보낸 사람 유형 (user 또는 agent)')
    agent_type = Column(String(50), comment='에이전트 유형 (예: marketing)')
    content = Column(Text, comment='메시지 본문')
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment='생성 시각')
    
    # 관계 설정
    conversation = relationship("Conversation", back_populates="messages")

class AutomationTask(Base):
    """자동화 작업 테이블"""
    __tablename__ = 'automation_task'
    
    task_id = Column(Integer, primary_key=True, autoincrement=True, comment='자동화 작업 ID')
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False, comment='요청한 사용자 ID')
    conversation_id = Column(Integer, ForeignKey('conversation.conversation_id'), comment='관련 대화 ID')
    task_type = Column(String(50), comment='작업 유형 (예: SEND_MESSAGE)')
    title = Column(String(100), comment='작업 이름 또는 요약')
    # template_id = Column(Integer, ForeignKey('template_message.template_id'), comment='연결된 템플릿 (nullable)')  # template_message 테이블이 정의되지 않아 주석 처리
    template_id = Column(Integer, comment='연결된 템플릿 (nullable)')  # 임시로 Integer로 설정
    task_data = Column(JSON, comment='자동화 작업을 위한 데이터 (파라미터)')
    status = Column(String(20), comment='진행 상태 (예: pending, success, failed)')
    scheduled_at = Column(TIMESTAMP, comment='예약 실행 시간')
    executed_at = Column(TIMESTAMP, comment='실행된 시간')
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment='작업 등록 시각')
    
    # 관계 설정
    user = relationship("User", back_populates="automation_tasks")
    conversation = relationship("Conversation", back_populates="automation_tasks")

class Feedback(Base):
    """피드백 테이블"""
    __tablename__ = 'feedback'
    
    feedback_id = Column(Integer, primary_key=True, autoincrement=True, comment='피드백 ID')
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False, comment='피드백 제공자')
    conversation_id = Column(Integer, ForeignKey('conversation.conversation_id'), comment='대상 세션 ID')
    rating = Column(Integer, comment='만족도 점수')
    comment = Column(Text, comment='피드백 코멘트')
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment='작성 시각')
    
    # 관계 설정
    user = relationship("User", back_populates="feedbacks")
    conversation = relationship("Conversation", back_populates="feedbacks")
