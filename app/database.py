from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# MySQL 설정에 맞게 수정하세요
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:1234@192.168.0.20:3305/mydb?charset=utf8mb4"
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
