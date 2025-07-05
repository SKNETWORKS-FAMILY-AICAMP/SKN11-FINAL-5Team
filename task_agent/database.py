"""
간소화된 데이터베이스 설정 v3
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import config

# 엔진 및 세션 설정
engine = create_engine(config.MYSQL_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """데이터베이스 세션 (FastAPI 의존성)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    """데이터베이스 세션 (직접 사용)"""
    return SessionLocal()

def init_database():
    """데이터베이스 테이블 생성"""
    Base.metadata.create_all(bind=engine)
