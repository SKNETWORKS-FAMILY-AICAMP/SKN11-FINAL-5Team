"""
데이터베이스 설정 및 연결 관리
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..config import MYSQL_URL, config

# 데이터베이스 URL
DATABASE_URL = MYSQL_URL

# SQLAlchemy 엔진 생성
engine = create_engine(DATABASE_URL)

# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()

def get_db():
    """데이터베이스 세션을 반환하는 의존성 (FastAPI용)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    """데이터베이스 세션을 직접 반환 (일반 코드용)"""
    return SessionLocal()

def init_database():
    """데이터베이스 테이블 생성"""
    Base.metadata.create_all(bind=engine)
