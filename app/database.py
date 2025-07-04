from sqlalchemy import create_engine
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
    f"mysql+pymysql://"
    f"{MYSQL_USER}:{MYSQL_PASSWORD}@"
    f"{MYSQL_HOST}:{MYSQL_PORT}/"
    f"{MYSQL_DB}?charset=utf8mb4"
)

engine = create_engine(DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:1234@192.168.0.20:3305/mydb?charset=utf8mb4"
# SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:skn11penta!!@penta-db.czocsimuw0dc.ap-northeast-2.rds.amazonaws.com/pantaDB?charset=utf8mb4"
# engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


