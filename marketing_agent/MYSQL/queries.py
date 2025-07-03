from sqlalchemy import text, bindparam
from sqlalchemy.exc import SQLAlchemyError
from MYSQL.connection import engine
from datetime import datetime
import logging
import pymysql
from typing import List, Dict
import os
from dotenv import load_dotenv

# 로거 설정
logger = logging.getLogger(__name__)

def handle_db_error(e: Exception, operation: str):
    logger.error(f"[{operation} 오류] {type(e).__name__}: {e}", exc_info=True)
    if isinstance(e, SQLAlchemyError):
        return {"error": "Database operation failed"}
    return {"error": "System error"}

# Conversation 관련 함수
def insert_conversation(user_id: int) -> int:
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                INSERT INTO conversation (user_id)
                VALUES (:user_id)
                """),
                {"user_id": user_id}
            )
            return result.lastrowid
    except Exception as e:
        return handle_db_error(e, "insert_conversation") or -1

def get_conversations_by_user(user_id: int) -> list:
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM conversation WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            return [dict(row._mapping) for row in result]
    except Exception as e:
        return handle_db_error(e, "get_conversations_by_user") or []


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
    
def print_template(template_id: int) -> str:
    """
    template_id를 기반으로 템플릿 제목과 본문을 포맷팅하여 문자열로 반환
    """
    try:
        template = get_template(template_id)
        if template:
            return f"[{template['title']}]\n{template['content']}"
        else:
            return "⚠️ 템플릿을 찾을 수 없습니다."
    except Exception as e:
        logger.error(f"print_template 오류: {e}")
        return "❌ 템플릿 출력 중 오류 발생"


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
    
# history 최근 5 개 기억

def get_last_messages(conversation_id: int, limit: int = 7) -> List[Dict]:
    try:
        conn = pymysql.connect(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT")),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DB"),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )  
        # DB 설정
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = """
                SELECT sender_type, content
                FROM message
                WHERE conversation_id = %s
                ORDER BY message_id DESC
                LIMIT %s
            """
            cursor.execute(sql, (conversation_id, limit))
            messages = cursor.fetchall()
        conn.close()
        return list(reversed(messages))  # 시간 순으로 정렬 (과거 → 현재)
    except Exception as e:
        print(f"❌ get_last_messages 에러: {e}")
        return []
    

# 추가: 템플릿 타입 목록 조회 함수
def get_available_template_types() -> list:
    """사용 가능한 템플릿 타입 목록 반환"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT DISTINCT template_type FROM template_message WHERE template_type IS NOT NULL")
            )
            types = [row[0] for row in result if row[0]]
            print(f"📋 사용 가능한 템플릿 타입: {types}")
            return types
    except Exception as e:
        print(f"❌ get_available_template_types 오류: {e}")
        return []

# 디버깅용 함수 추가
def debug_template_data():
    """템플릿 데이터 디버깅"""
    try:
        with engine.connect() as conn:
            # 전체 템플릿 수
            total_result = conn.execute(text("SELECT COUNT(*) FROM template_message"))
            total_count = total_result.scalar()
            
            # 타입별 개수
            type_result = conn.execute(text("""
                SELECT template_type, COUNT(*) as count 
                FROM template_message 
                GROUP BY template_type
            """))
            type_counts = dict(type_result.fetchall())
            
            # 샘플 데이터
            sample_result = conn.execute(text("SELECT * FROM template_message LIMIT 3"))
            samples = [dict(row._mapping) for row in sample_result]
            
            print(f"🔍 템플릿 디버깅 정보:")
            print(f"  - 전체 템플릿 수: {total_count}")
            print(f"  - 타입별 개수: {type_counts}")
            print(f"  - 샘플 데이터: {len(samples)}개")
            
            return {
                "total_count": total_count,
                "type_counts": type_counts,
                "samples": samples
            }
            
    except Exception as e:
        print(f"❌ debug_template_data 오류: {e}")
        return None
