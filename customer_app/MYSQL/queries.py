from sqlalchemy import text, bindparam
from sqlalchemy.exc import SQLAlchemyError
from MYSQL.connection import engine
from datetime import datetime
import logging

# 로거 설정
logger = logging.getLogger(__name__)

def handle_db_error(e: Exception, operation: str):
    logger.error(f"[{operation} 오류] {type(e).__name__}: {e}", exc_info=True)
    if isinstance(e, SQLAlchemyError):
        return {"error": "Database operation failed"}
    return {"error": "System error"}

# user 테이블 연산 -------------------------------------------------

def insert_user(email: str, password: str, nickname: str = None, business_type: str = None) -> int:
    """
    user 테이블에 사용자 추가 (user_id auto_increment)
    - email, password: 필수
    - 반환값: 성공 시 user_id, 실패 시 -1
    """
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

# template_message 테이블 연산 --------------------------------------

def insert_template(
    user_id: int,
    template_type: str = None,
    channel_type: str = None,
    title: str = None,
    content: str = None
) -> int:
    """
    template_message에 템플릿 추가 (template_id auto_increment)
    - user_id: 필수
    - 반환값: 성공 시 template_id, 실패 시 -1
    """
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
    
def get_templates_by_type(template_type: str) -> list:
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT * FROM template_message 
                    WHERE template_type = :template_type
                """),
                {"template_type": template_type}
            )
            return [dict(row._mapping) for row in result]
    except Exception as e:
        return handle_db_error(e, "get_templates_by_type") or []

def get_template_by_id(template_id: int) -> dict | None:
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT template_id, template_type, content_type, title, content
                    FROM template_message
                    WHERE template_id = :template_id
                """),
                {"template_id": template_id}
            )
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None
    except Exception as e:
        return handle_db_error(e, "get_template_by_id")
    
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

# message 테이블 연산 ----------------------------------------------
def insert_message(
    conversation_id: int,
    sender_type: str,
    content: str,
    agent_type: str = None
) -> bool:
    """
    message 테이블에 메시지 추가
    - conversation_id, sender_type, content: 필수
    - agent_type: 선택 (기본값 NULL)
    - created_at: Python에서 현재 시간으로 직접 입력
    - 반환값: 성공 시 True, 실패 시 False
    """
    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                INSERT INTO message 
                (conversation_id, sender_type, agent_type, content, created_at)
                VALUES (:conversation_id, :sender_type, :agent_type, :content, :created_at)
                """),
                {
                    "conversation_id": conversation_id,
                    "sender_type": sender_type,
                    "agent_type": agent_type,
                    "content": content,
                    "created_at": datetime.now()  # 현재 시간 입력
                }
            )
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error inserting message: {e}")
        return False

def get_messages_by_conversation(conversation_id: int, recent_turns: int = 5) -> list:
    """
    message 테이블에서 conversation_id와 agent_type='customer_agent'인 메시지 중
    최신 N턴(2*recent_turns개)만 message_id 기준으로 내림차순 정렬 후 시간순(오래된→최신)으로 반환
    """
    limit_count = recent_turns * 2
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT *
                    FROM message
                    WHERE conversation_id = :conversation_id
                    ORDER BY message_id DESC
                    LIMIT :limit_count
                """),
                {
                    "conversation_id": conversation_id,
                    "limit_count": limit_count
                }
            )
            messages = [dict(row._mapping) for row in result]
            return list(reversed(messages))  # 오래된→최신 순서로 반환
    except Exception as e:
        logger.error(f"메시지 조회 오류: {str(e)}")
        return []
