"""
데이터베이스 CRUD 서비스
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import hashlib
import logging

from .database import get_db, SessionLocal
from  ...schemas.db_models import User, Conversation, Message, AutomationTask, Feedback

logger = logging.getLogger(__name__)

class BaseService:
    """기본 서비스 클래스"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

class UserService(BaseService):
    """사용자 관련 서비스"""
    
    def create_user(self, email: str, password: str, nickname: str = None, business_type: str = None, admin: bool = False) -> User:
        """사용자 생성"""
        try:
            # 비밀번호 해시화
            hashed_password = self._hash_password(password)
            
            user = User(
                email=email,
                password=hashed_password,
                nickname=nickname,
                business_type=business_type,
                admin=admin
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"사용자 생성 완료: {email}")
            return user
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"사용자 생성 실패: {e}")
            raise
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """사용자 ID로 조회"""
        try:
            return self.db.query(User).filter(User.user_id == user_id).first()
        except SQLAlchemyError as e:
            logger.error(f"사용자 조회 실패: {e}")
            raise
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        try:
            return self.db.query(User).filter(User.email == email).first()
        except SQLAlchemyError as e:
            logger.error(f"사용자 조회 실패: {e}")
            raise
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """사용자 정보 업데이트"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            for key, value in kwargs.items():
                if hasattr(user, key):
                    if key == 'password':
                        value = self._hash_password(value)
                    setattr(user, key, value)
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"사용자 정보 업데이트 완료: {user_id}")
            return user
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"사용자 정보 업데이트 실패: {e}")
            raise
    
    def verify_password(self, email: str, password: str) -> Optional[User]:
        """로그인 인증"""
        try:
            user = self.get_user_by_email(email)
            if user and self._verify_password(password, user.password):
                return user
            return None
        except SQLAlchemyError as e:
            logger.error(f"비밀번호 검증 실패: {e}")
            raise
    
    def _hash_password(self, password: str) -> str:
        """비밀번호 해시화"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """비밀번호 검증"""
        return self._hash_password(password) == hashed
    
    # Google Calendar 토큰 관련 메서드들
    def store_google_token(self, user_id: int, access_token: str, refresh_token: str = None, 
                          expires_in: int = None, user_info: Dict[str, Any] = None) -> Optional[User]:
        """Google Calendar 토큰 저장"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            user.access_token = access_token
            if refresh_token:
                user.google_refresh_token = refresh_token
            user.google_token_expires_in = expires_in
            user.google_token_created_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Google 토큰 저장 완료: user_id={user_id}")
            return user
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Google 토큰 저장 실패: {e}")
            raise
    
    def get_google_token(self, user_id: int) -> Optional[Dict[str, Any]]:
        """사용자의 Google 토큰 정보 조회"""
        try:
            user = self.get_user_by_id(user_id)
            if not user or not user.access_token:
                return None
            
            return {
                "access_token": user.access_token,
                "refresh_token": user.google_refresh_token,
                "expires_in": user.google_token_expires_in,
                "created_at": user.google_token_created_at
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Google 토큰 조회 실패: {e}")
            raise
    
    def update_access_token(self, user_id: int, access_token: str, expires_in: int = None) -> Optional[User]:
        """Google 액세스 토큰만 업데이트 (리프레시 시)"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            user.access_token = access_token
            if expires_in:
                user.google_token_expires_in = expires_in
            user.google_token_created_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Google 액세스 토큰 업데이트 완료: user_id={user_id}")
            return user
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Google 액세스 토큰 업데이트 실패: {e}")
            raise
    
    def is_google_token_valid(self, user_id: int) -> bool:
        """Google 토큰 유효성 검사"""
        try:
            user = self.get_user_by_id(user_id)
            if not user or not user.access_token:
                return False
            
            # 만료 시간 확인
            if user.google_token_expires_in and user.google_token_created_at:
                from datetime import timedelta
                expiry_time = user.google_token_created_at + timedelta(seconds=user.google_token_expires_in)
                return datetime.now() < expiry_time
            
            return True  # 만료 정보가 없으면 유효한 것으로 간주
            
        except SQLAlchemyError as e:
            logger.error(f"Google 토큰 유효성 검사 실패: {e}")
            return False
    
    def delete_google_token(self, user_id: int) -> Optional[User]:
        """Google 토큰 삭제 (연동 해제)"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            user.access_token = None
            user.google_refresh_token = None
            user.google_token_expires_in = None
            user.google_token_created_at = None
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Google 토큰 삭제 완료: user_id={user_id}")
            return user
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Google 토큰 삭제 실패: {e}")
            raise

class ConversationService(BaseService):
    """대화 세션 관련 서비스"""
    
    def create_conversation(self, user_id: int) -> Conversation:
        """대화 세션 생성"""
        try:
            conversation = Conversation(
                user_id=user_id,
                started_at=datetime.now(),
                is_visible=True
            )
            
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)
            
            logger.info(f"대화 세션 생성 완료: {conversation.conversation_id}")
            return conversation
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"대화 세션 생성 실패: {e}")
            raise
    
    def get_conversation_by_id(self, conversation_id: int) -> Optional[Conversation]:
        """대화 세션 ID로 조회"""
        try:
            return self.db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
        except SQLAlchemyError as e:
            logger.error(f"대화 세션 조회 실패: {e}")
            raise
    
    def get_user_conversations(self, user_id: int, visible_only: bool = True) -> List[Conversation]:
        """사용자의 대화 세션 목록 조회"""
        try:
            query = self.db.query(Conversation).filter(Conversation.user_id == user_id)
            if visible_only:
                query = query.filter(Conversation.is_visible == True)
            return query.order_by(Conversation.started_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"대화 세션 목록 조회 실패: {e}")
            raise
    
    def end_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """대화 세션 종료"""
        try:
            conversation = self.get_conversation_by_id(conversation_id)
            if not conversation:
                return None
            
            conversation.ended_at = datetime.now()
            self.db.commit()
            self.db.refresh(conversation)
            
            logger.info(f"대화 세션 종료: {conversation_id}")
            return conversation
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"대화 세션 종료 실패: {e}")
            raise
    
    def hide_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """대화 세션 숨기기"""
        try:
            conversation = self.get_conversation_by_id(conversation_id)
            if not conversation:
                return None
            
            conversation.is_visible = False
            self.db.commit()
            self.db.refresh(conversation)
            
            logger.info(f"대화 세션 숨김: {conversation_id}")
            return conversation
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"대화 세션 숨김 실패: {e}")
            raise

class MessageService(BaseService):
    """메시지 관련 서비스"""
    
    def create_message(self, conversation_id: int, sender_type: str, content: str, agent_type: str = None) -> Message:
        """메시지 생성"""
        try:
            message = Message(
                conversation_id=conversation_id,
                sender_type=sender_type,
                agent_type=agent_type,
                content=content
            )
            
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)
            
            logger.debug(f"메시지 생성 완료: {message.message_id}")
            return message
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"메시지 생성 실패: {e}")
            raise
    
    def get_conversation_messages(self, conversation_id: int, limit: int = 100, offset: int = 0) -> List[Message]:
        """대화 세션의 메시지 목록 조회"""
        try:
            return (self.db.query(Message)
                   .filter(Message.conversation_id == conversation_id)
                   .order_by(Message.created_at.asc())
                   .offset(offset)
                   .limit(limit)
                   .all())
        except SQLAlchemyError as e:
            logger.error(f"메시지 목록 조회 실패: {e}")
            raise
    
    def get_message_by_id(self, message_id: int) -> Optional[Message]:
        """메시지 ID로 조회"""
        try:
            return self.db.query(Message).filter(Message.message_id == message_id).first()
        except SQLAlchemyError as e:
            logger.error(f"메시지 조회 실패: {e}")
            raise

class AutomationTaskService(BaseService):
    """자동화 작업 관련 서비스"""
    
    def create_automation_task(
        self, 
        user_id: int, 
        task_type: str, 
        title: str, 
        task_data: Dict[str, Any],
        conversation_id: int = None,
        template_id: int = None,
        scheduled_at: datetime = None
    ) -> AutomationTask:
        """자동화 작업 생성"""
        try:
            task = AutomationTask(
                user_id=user_id,
                conversation_id=conversation_id,
                task_type=task_type,
                title=title,
                template_id=template_id,
                task_data=task_data,
                status='pending',
                scheduled_at=scheduled_at
            )
            
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            
            logger.info(f"자동화 작업 생성 완료: {task.task_id}")
            return task
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"자동화 작업 생성 실패: {e}")
            raise
    
    def get_task_by_id(self, task_id: int) -> Optional[AutomationTask]:
        """자동화 작업 ID로 조회"""
        try:
            return self.db.query(AutomationTask).filter(AutomationTask.task_id == task_id).first()
        except SQLAlchemyError as e:
            logger.error(f"자동화 작업 조회 실패: {e}")
            raise
    
    def get_user_tasks(self, user_id: int, status: str = None) -> List[AutomationTask]:
        """사용자의 자동화 작업 목록 조회"""
        try:
            query = self.db.query(AutomationTask).filter(AutomationTask.user_id == user_id)
            if status:
                query = query.filter(AutomationTask.status == status)
            return query.order_by(AutomationTask.created_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"자동화 작업 목록 조회 실패: {e}")
            raise
    
    def update_task_status(self, task_id: int, status: str, executed_at: datetime = None) -> Optional[AutomationTask]:
        """자동화 작업 상태 업데이트"""
        try:
            task = self.get_task_by_id(task_id)
            if not task:
                return None
            
            task.status = status
            if executed_at:
                task.executed_at = executed_at
            elif status in ['success', 'failed']:
                task.executed_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(task)
            
            logger.info(f"자동화 작업 상태 업데이트: {task_id} -> {status}")
            return task
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"자동화 작업 상태 업데이트 실패: {e}")
            raise

class FeedbackService(BaseService):
    """피드백 관련 서비스"""
    
    def create_feedback(self, user_id: int, conversation_id: int = None, rating: int = None, comment: str = None) -> Feedback:
        """피드백 생성"""
        try:
            feedback = Feedback(
                user_id=user_id,
                conversation_id=conversation_id,
                rating=rating,
                comment=comment
            )
            
            self.db.add(feedback)
            self.db.commit()
            self.db.refresh(feedback)
            
            logger.info(f"피드백 생성 완료: {feedback.feedback_id}")
            return feedback
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"피드백 생성 실패: {e}")
            raise
    
    def get_feedback_by_id(self, feedback_id: int) -> Optional[Feedback]:
        """피드백 ID로 조회"""
        try:
            return self.db.query(Feedback).filter(Feedback.feedback_id == feedback_id).first()
        except SQLAlchemyError as e:
            logger.error(f"피드백 조회 실패: {e}")
            raise
    
    def get_conversation_feedbacks(self, conversation_id: int) -> List[Feedback]:
        """대화 세션의 피드백 목록 조회"""
        try:
            return (self.db.query(Feedback)
                   .filter(Feedback.conversation_id == conversation_id)
                   .order_by(Feedback.created_at.desc())
                   .all())
        except SQLAlchemyError as e:
            logger.error(f"피드백 목록 조회 실패: {e}")
            raise
    
    def get_user_feedbacks(self, user_id: int) -> List[Feedback]:
        """사용자의 피드백 목록 조회"""
        try:
            return (self.db.query(Feedback)
                   .filter(Feedback.user_id == user_id)
                   .order_by(Feedback.created_at.desc())
                   .all())
        except SQLAlchemyError as e:
            logger.error(f"사용자 피드백 목록 조회 실패: {e}")
            raise

# 서비스 인스턴스들
user_service = UserService()
conversation_service = ConversationService()
message_service = MessageService()
automation_task_service = AutomationTaskService()
feedback_service = FeedbackService()
