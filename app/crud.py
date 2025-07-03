from sqlalchemy.orm import Session
from app.models import User, Conversation, Message, PHQ9Result
from datetime import datetime

def create_message(db: Session, conversation_id: int, sender_type: str, agent_type: str, content: str):
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

def get_conversation_history(db: Session, conversation_id: int, limit=6):
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.message_id)
        .all()
    )
    history = []
    for m in messages[-limit:]:
        prefix = "Human" if m.sender_type == "user" else "AI"
        history.append(f"{prefix}: {m.content}")
    return "\n".join(history)

def save_or_update_phq9_result(db: Session, user_id: int, score: int, level: str):
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

def get_latest_phq9_by_user(db: Session, user_id: int):
    return db.query(PHQ9Result).filter_by(user_id=user_id).first()

def create_user(db: Session, email: str, password: str, nickname: str = "", business_type: str = ""):
    user = User(
        email=email,
        password=password,
        nickname=nickname,
        business_type=business_type,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_social(db: Session, provider: str, social_id: str):
    return db.query(User).filter(User.provider == provider, User.social_id == social_id).first()

def create_user_social(db: Session, provider: str, social_id: str, email: str, nickname: str = "", access_token=None):
    user = User(
        email=email,
        password=None,  # 소셜 로그인은 비밀번호 없음
        nickname=nickname,
        provider=provider,
        social_id=social_id,
        access_token=access_token
    )
    db.add(user)
    db.commit()
    db.refresh(user) 
    return user