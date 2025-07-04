from sqlalchemy import text, bindparam
from sqlalchemy.exc import SQLAlchemyError
from config.connection import engine
from datetime import datetime
from queries import *
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
    - 반환값: 성공 시 True, 실패 시 False
    """
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
    """
    message 테이블에서 특정 conversation_id에 속한 메시지를
    최신순으로 limit개만 가져옴.
    반환: [{sender_type, content, agent_type, created_at}, ...]
    """
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
