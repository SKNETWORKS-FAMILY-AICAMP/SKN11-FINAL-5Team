from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="../../unified_agent_system/.env")

# DB URL 구성
DB_URL = os.getenv("MYSQL_URL","mysql+pymysql://root:skn11penta!!@penta-db.czocsimuw0dc.ap-northeast-2.rds.amazonaws.com:3306/pantaDB")

# SQLAlchemy 엔진 생성
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)