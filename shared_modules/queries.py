from sqlalchemy.orm import Session
from shared_modules.db_models import User
from datetime import datetime
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import bindparam, text
from shared_modules.database import DatabaseManager

engine = DatabaseManager().engine
logger = logging.getLogger(__name__)

# -------------------
# User 관련 함수
# -------------------
def create_user(db: Session, email: str, password: str, nickname: str = "", business_type: str = "") -> User:
    try:
        user = User(
            email=email,
            password=password,
            nickname=nickname or email.split('@')[0],
            business_type=business_type
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        logger.error(f"[create_user 오류] {e}", exc_info=True)
        db.rollback()
        return None

def get_user_by_email(db: Session, email: str) -> User:
    try:
        return db.query(User).filter(User.email == email).first()
    except Exception as e:
        logger.error(f"[get_user_by_email 오류] {e}", exc_info=True)
        return None

def get_user_by_id(db: Session, user_id: int) -> User:
    try:
        return db.query(User).filter(User.user_id == user_id).first()
    except Exception as e:
        logger.error(f"[get_user_by_id 오류] {e}", exc_info=True)
        return None

def get_user_by_social(db: Session, provider: str, social_id: str) -> User:
    try:
        return db.query(User).filter(User.provider == provider, User.social_id == social_id).first()
    except Exception as e:
        logger.error(f"[get_user_by_social 오류] {e}", exc_info=True)
        return None

def create_user_social(db: Session, provider: str, social_id: str, email: str, nickname: str = "", access_token=None) -> User:
    try:
        user = User(
            email=email,
            password=None,
            nickname=nickname or email.split('@')[0],
            provider=provider,
            social_id=social_id,
            access_token=access_token
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        logger.error(f"[create_user_social 오류] {e}", exc_info=True)
        db.rollback()
        return None

# -------------------
# Conversation 관련 함수
# -------------------
def create_conversation(db: Session, user_id: int, conversation_type: str = "general"):
    try:
        from db_models import Conversation
        conversation = Conversation(
            user_id=user_id,
            conversation_type=conversation_type,
            started_at=datetime.now(),
            is_visible=True
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    except Exception as e:
        logger.error(f"[create_conversation 오류] {e}", exc_info=True)
        db.rollback()
        return None

def get_conversation_by_id(db: Session, conversation_id: int):
    try:
        from db_models import Conversation
        return db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
    except Exception as e:
        logger.error(f"[get_conversation_by_id 오류] {e}", exc_info=True)
        return None

def get_user_conversations(db: Session, user_id: int, visible_only: bool = True):
    try:
        from db_models import Conversation
        query = db.query(Conversation).filter(Conversation.user_id == user_id)
        if visible_only:
            query = query.filter(Conversation.is_visible == True)
        return query.order_by(Conversation.started_at.desc()).all()
    except Exception as e:
        logger.error(f"[get_user_conversations 오류] {e}", exc_info=True)
        return []

def end_conversation(db: Session, conversation_id: int) -> bool:
    try:
        from db_models import Conversation
        conversation = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
        if conversation:
            conversation.ended_at = datetime.now()
            db.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"[end_conversation 오류] {e}", exc_info=True)
        db.rollback()
        return False

# -------------------
# Message 관련 함수
# -------------------
def create_message(db: Session, conversation_id: int, sender_type: str, agent_type: str, content: str):
    try:
        from db_models import Message
        msg = Message(
            conversation_id=conversation_id,
            sender_type=sender_type,
            agent_type=agent_type,
            content=content,
            created_at=datetime.now()
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg
    except Exception as e:
        logger.error(f"[create_message 오류] {e}", exc_info=True)
        db.rollback()
        return None

def get_conversation_messages(db: Session, conversation_id: int, limit: int = 100, offset: int = 0):
    try:
        from db_models import Message
        return db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).offset(offset).limit(limit).all()
    except Exception as e:
        logger.error(f"[get_conversation_messages 오류] {e}", exc_info=True)
        return []

def get_recent_messages(db: Session, conversation_id: int, limit: int = 10):
    try:
        from db_models import Message
        return db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(limit).all()
    except Exception as e:
        logger.error(f"[get_recent_messages 오류] {e}", exc_info=True)
        return []

def get_conversation_history(db: Session, conversation_id: int, limit=6):
    try:
        from db_models import Message
        messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.message_id).all()
        history = []
        for m in messages[-limit:]:
            prefix = "Human" if m.sender_type == "user" else "AI"
            history.append(f"{prefix}: {m.content}")
        return "\n".join(history)
    except Exception as e:
        logger.error(f"[get_conversation_history 오류] {e}", exc_info=True)
        return ""

# -------------------
# PHQ9 관련 함수
# -------------------
def save_or_update_phq9_result(db: Session, user_id: int, score: int, level: str):
    try:
        from db_models import PHQ9Result
        now = datetime.now()
        result = db.query(PHQ9Result).filter_by(user_id=user_id).first()
        if result:
            result.score = score
            result.level = level
            result.updated_at = now
        else:
            result = PHQ9Result(
                user_id=user_id,
                score=score,
                level=level,
                updated_at=now
            )
            db.add(result)
        db.commit()
        return result
    except Exception as e:
        logger.error(f"[save_or_update_phq9_result 오류] {e}", exc_info=True)
        db.rollback()
        return None

def get_latest_phq9_by_user(db: Session, user_id: int):
    try:
        from db_models import PHQ9Result
        return db.query(PHQ9Result).filter_by(user_id=user_id).first()
    except Exception as e:
        logger.error(f"[get_latest_phq9_by_user 오류] {e}", exc_info=True)
        return None
    
def get_user_context_from_db(db: Session, user_id: int):
    phq9 = get_latest_phq9_by_user(db, user_id)
    context_parts = []
    if phq9:
        context_parts.append(
            f"PHQ-9 점수: {phq9.score}점 ({phq9.level}, {phq9.updated_at.strftime('%Y-%m-%d %H:%M')})"
        )
    return "\n".join(context_parts) if context_parts else "이전 세션 정보 없음"

# -------------------
# AutomationTask 관련 함수
# -------------------
def get_user_tasks(db: Session, user_id: int, status: str = None, limit: int = 50):
    try:
        from db_models import AutomationTask
        query = db.query(AutomationTask).filter(AutomationTask.user_id == user_id)
        if status:
            query = query.filter(AutomationTask.status == status)
        return query.order_by(AutomationTask.created_at.desc()).limit(limit).all()
    except Exception as e:
        logger.error(f"[get_user_tasks 오류] {e}", exc_info=True)
        return []

def get_pending_tasks(db: Session, limit: int = 100):
    try:
        from db_models import AutomationTask
        return db.query(AutomationTask).filter(AutomationTask.status == "pending").order_by(AutomationTask.scheduled_at.asc()).limit(limit).all()
    except Exception as e:
        logger.error(f"[get_pending_tasks 오류] {e}", exc_info=True)
        return []

def handle_db_error(e: Exception, operation: str):
    logger.error(f"[{operation} 오류] {type(e).__name__}: {e}", exc_info=True)
    if isinstance(e, SQLAlchemyError):
        return {"error": "Database operation failed"}
    return {"error": "System error"}

# user 테이블 연산

def insert_user(email: str, password: str, nickname: str = None, business_type: str = None) -> int:
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                INSERT INTO user (email, password, nickname, business_type)
                VALUES (:email, :password, :nickname, :business_type)
                """),
                {
                    "email": email,
                    "password": password,
                    "nickname": nickname,
                    "business_type": business_type
                }
            )
            return result.lastrowid
    except SQLAlchemyError as e:
        logger.error(f"Error inserting user: {e}")
        return -1

def get_business_type(user_id: int) -> str:
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT business_type FROM user WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            return row.business_type if row else "common"
    except Exception as e:
        return handle_db_error(e, "get_business_type") or "common"

def get_user(user_id: int) -> dict:
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM user WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            return dict(row._mapping) if row else {}
    except Exception as e:
        return handle_db_error(e, "get_user") or {}

def get_user_by_email(email: str) -> dict:
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM user WHERE email = :email"),
                {"email": email}
            )
            row = result.fetchone()
            return dict(row._mapping) if row else {}
    except Exception as e:
        return handle_db_error(e, "get_user_by_email") or {}

def get_all_users() -> list:
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM user")
            )
            return [dict(row._mapping) for row in result]
    except Exception as e:
        return handle_db_error(e, "get_all_users") or []

# template_message 테이블 연산

def insert_template(
    user_id: int,
    template_type: str = None,
    channel_type: str = None,
    title: str = None,
    content: str = None
) -> int:
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                INSERT INTO template_message 
                (user_id, template_type, channel_type, title, content, created_at)
                VALUES (:user_id, :template_type, :channel_type, :title, :content, :created_at)
                """),
                {
                    "user_id": user_id,
                    "template_type": template_type,
                    "channel_type": channel_type,
                    "title": title,
                    "content": content,
                    "created_at": datetime.utcnow()
                }
            )
            return result.lastrowid
    except Exception as e:
        logger.error(f"Error inserting template: {e}")
        return -1

def get_template(template_id: int) -> dict:
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM template_message WHERE template_id = :template_id"),
                {"template_id": template_id}
            )
            row = result.fetchone()
            return dict(row._mapping) if row else {}
    except Exception as e:
        return handle_db_error(e, "get_template") or {}

def get_templates_by_user(user_id: int) -> list:
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM template_message WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            return [dict(row._mapping) for row in result]
    except Exception as e:
        return handle_db_error(e, "get_templates_by_user") or []

def update_template(template_id: int, **kwargs) -> bool:
    try:
        valid_keys = {"template_type", "channel_type", "title", "content"}
        update_data = {k: kwargs.get(k, None) for k in valid_keys if k in kwargs}
        
        if not update_data:
            return False
            
        set_clause = ", ".join([f"{k} = {bindparam(k)}" for k in update_data.keys()])
        
        with engine.begin() as conn:
            stmt = text(f"UPDATE template_message SET {set_clause} WHERE template_id = :template_id")
            params = {**update_data, "template_id": template_id}
            result = conn.execute(stmt, params)
            return result.rowcount > 0
    except Exception as e:
        return handle_db_error(e, "update_template") or False

def delete_template(template_id: int) -> bool:
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM template_message WHERE template_id = :template_id"),
                {"template_id": template_id}
            )
            return result.rowcount > 0
    except Exception as e:
        return handle_db_error(e, "delete_template") or False

# message 테이블 연산

def insert_message(
    conversation_id: int,
    sender_type: str,
    content: str,
    agent_type: str = None
) -> bool:
    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                INSERT INTO message 
                (conversation_id, sender_type, agent_type, content)
                VALUES (:conversation_id, :sender_type, :agent_type, :content)
                """),
                {
                    "conversation_id": conversation_id,
                    "sender_type": sender_type,
                    "agent_type": agent_type,
                    "content": content
                }
            )
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error inserting message: {e}")
        return False

def get_recent_messages(conversation_id: int, limit: int = 5) -> list:
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT sender_type, content, agent_type, created_at
                    FROM message
                    WHERE conversation_id = :conversation_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"conversation_id": conversation_id, "limit": limit}
            )
            return [dict(row._mapping) for row in result]
    except Exception as e:
        return handle_db_error(e, "get_recent_messages") or []

def get_template_by_title(title: str) -> dict:
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM template_message WHERE title = :title"),
            {"title": title}
        )
        row = result.fetchone()
        return dict(row._mapping) if row else {}

def get_templates_by_type(template_type: str) -> list:
    """템플릿 타입별 조회 함수 개선"""
    try:
        with engine.connect() as conn:
            # 전체 조회인 경우
            if template_type == "전체":
                result = conn.execute(
                    text("SELECT * FROM template_message ORDER BY created_at DESC")
                )
            else:
                result = conn.execute(
                    text("""
                        SELECT * FROM template_message 
                        WHERE template_type = :template_type 
                        ORDER BY created_at DESC
                    """),
                    {"template_type": template_type}
                )
            
            templates = [dict(row._mapping) for row in result]
            print(f"📋 DB 조회 결과: {len(templates)}개 템플릿 (타입: {template_type})")
            
            # 디버깅: 첫 번째 템플릿 정보 출력
            if templates:
                first_template = templates[0]
                print(f"샘플 템플릿: {first_template.get('title', 'No Title')}")
                print(f"내용 미리보기: {first_template.get('content', 'No Content')[:50]}...")
            
            return templates
            
    except Exception as e:
        print(f"❌ get_templates_by_type 오류: {e}")
        return handle_db_error(e, "get_templates_by_type") or []
    