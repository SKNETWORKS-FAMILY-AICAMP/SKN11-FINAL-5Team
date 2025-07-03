"""
TinkerBell 프로젝트 - 개선된 설정 관리 (Pydantic v2 대응)
"""

import os
from enum import Enum
from typing import Dict, Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class DatabaseConfig(BaseSettings):
    mysql_url: str = Field(..., env="MYSQL_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    chroma_persist_dir: str = Field(..., env="CHROMA_PERSIST_DIR")

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

class LLMConfig(BaseSettings):
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    google_api_key: Optional[str] = Field(None, env="GOOGLE_API_KEY")
    gpt_model: str = Field(default="gpt-4o-mini")
    gemini_model: str = Field(default="gemini-1.5-flash")
    embedding_model: str = Field(default="text-embedding-3-large")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1500, gt=0)
    timeout: int = Field(default=30, gt=0)

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

class RAGConfig(BaseSettings):
    chunk_size: int = Field(default=500, gt=0)
    overlap_size: int = Field(default=50, ge=0)
    max_search_results: int = Field(default=5, gt=0)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

class AutomationConfig(BaseSettings):
    max_concurrent_tasks: int = Field(default=10, gt=0)
    task_timeout_minutes: int = Field(default=30, gt=0)
    retry_attempts: int = Field(default=3, ge=0)
    cleanup_interval_hours: int = Field(default=24, gt=0)

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

class ServerConfig(BaseSettings):
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8003, gt=0, le=65535)
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)
    cors_origins: List[str] = Field(default=["*"])
    cors_methods: List[str] = Field(default=["*"])
    cors_headers: List[str] = Field(default=["*"])

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

class ExternalAPIConfig(BaseSettings):
    instagram_client_id: Optional[str] = Field(None, env="INSTAGRAM_CLIENT_ID")
    instagram_client_secret: Optional[str] = Field(None, env="INSTAGRAM_CLIENT_SECRET")
    facebook_app_id: Optional[str] = Field(None, env="FACEBOOK_APP_ID")
    facebook_app_secret: Optional[str] = Field(None, env="FACEBOOK_APP_SECRET")
    mailchimp_api_key: Optional[str] = Field(None, env="MAILCHIMP_API_KEY")
    stibee_api_key: Optional[str] = Field(None, env="STIBEE_API_KEY")
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

class AppMetaConfig(BaseSettings):
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    project_name: str = Field(default="TinkerBell")
    version: str = Field(default="2.0.0")
    secret_key: str = Field(default="your-secret-key-here")
    access_token_expire_minutes: int = Field(default=30)

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

# 구성 요소별 설정 로딩
db_config = DatabaseConfig()
llm_config = LLMConfig()
rag_config = RAGConfig()
automation_config = AutomationConfig()
server_config = ServerConfig()
api_config = ExternalAPIConfig()
meta_config = AppMetaConfig()

# 전역 구성 객체
class Config:
    db = db_config
    llm = llm_config
    rag = rag_config
    automation = automation_config
    server = server_config
    api = api_config
    meta = meta_config

    def is_development(self) -> bool:
        return self.meta.environment == Environment.DEVELOPMENT

    def is_production(self) -> bool:
        return self.meta.environment == Environment.PRODUCTION

    def get_llm_models(self) -> Dict[str, str]:
        return {
            "gpt": self.llm.gpt_model,
            "gemini": self.llm.gemini_model
        }

    def validate_api_keys(self) -> Dict[str, bool]:
        return {
            "openai": bool(self.llm.openai_api_key),
            "google": bool(self.llm.google_api_key)
            # "slack": bool(self.api.slack_bot_token),
            # "google_calendar": bool(
            #     self.api.google_calendar_client_id and self.api.google_calendar_client_secret
            # )
        }

# 인스턴스 생성
config = Config()

# 별칭들 (하위 호환 또는 전역 접근용)
HOST = config.server.host
PORT = config.server.port
LOG_LEVEL = config.server.log_level
OPENAI_API_KEY = config.llm.openai_api_key
GOOGLE_API_KEY = config.llm.google_api_key
MYSQL_URL = config.db.mysql_url
CHROMA_PERSIST_DIR = config.db.chroma_persist_dir
LLM_MODELS = config.get_llm_models()
CHUNK_SIZE = config.rag.chunk_size
OVERLAP_SIZE = config.rag.overlap_size
MAX_SEARCH_RESULTS = config.rag.max_search_results
AUTOMATION_CONFIG = {
    "max_concurrent_tasks": config.automation.max_concurrent_tasks,
    "task_timeout_minutes": config.automation.task_timeout_minutes,
    "retry_attempts": config.automation.retry_attempts,
    "cleanup_interval_hours": config.automation.cleanup_interval_hours
}
