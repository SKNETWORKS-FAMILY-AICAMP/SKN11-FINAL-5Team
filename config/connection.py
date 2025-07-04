from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()
MYSQL_HOST = os.getenv("MYSQL_HOST")      
MYSQL_PORT = os.getenv("MYSQL_PORT")      
MYSQL_USER = os.getenv("MYSQL_USER")      
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD") 
MYSQL_DB = os.getenv("MYSQL_DB")

# DB URL 구성
DB_URL = (
    f"mysql+mysqlconnector://"
    f"{MYSQL_USER}:{MYSQL_PASSWORD}@"
    f"{MYSQL_HOST}:{MYSQL_PORT}/"
    f"{MYSQL_DB}"
)

# SQLAlchemy 엔진 생성
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)