"""
간소화된 설정 관리 v3
"""

import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="../unified_agent_system/.env")

class Config:
    """애플리케이션 설정"""
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Database
    MYSQL_URL = os.getenv("MYSQL_URL", "mysql+pymysql://root:skn11penta!!@penta-db.czocsimuw0dc.ap-northeast-2.rds.amazonaws.com:3306/pantaDB")
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./vector_db")
    
    # LLM Settings
    DEFAULT_MODEL = "gemini-1.5-flash"
    EMBEDDING_MODEL = "text-embedding-3-large"
    MAX_TOKENS = 1500
    TEMPERATURE = 0.7
    
    # RAG Settings
    CHUNK_SIZE = 500
    MAX_SEARCH_RESULTS = 5
    
    # Server Settings
    HOST = "0.0.0.0"
    PORT = 8003
    LOG_LEVEL = "INFO"
    
    # Cache Settings
    CACHE_TTL = 1800  # 30 minutes
    
    @classmethod
    def validate(cls) -> dict:
        """환경 설정 검증"""
        issues = []
        warnings = []
        
        if not cls.OPENAI_API_KEY and not cls.GOOGLE_API_KEY:
            issues.append("OpenAI 또는 Google API 키가 필요합니다")
        
        if not cls.MYSQL_URL:
            warnings.append("데이터베이스 URL이 설정되지 않았습니다")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }

config = Config()
