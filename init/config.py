import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Settings:
    # OpenAI API 키
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    
    # 벡터 DB 경로
    VECTOR_DB_PATH: str = os.path.join(os.path.dirname(__file__), "vector_db")
    
    # 기본 페르소나와 카테고리
    DEFAULT_PERSONA: str = "business_consultant"
    DEFAULT_CATEGORY: str = "general"
    
    # 로깅 레벨
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# settings 인스턴스 생성
settings = Settings()
