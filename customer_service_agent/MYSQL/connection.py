from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from config.env_config import DB_URL
# SQLAlchemy 엔진 생성
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)