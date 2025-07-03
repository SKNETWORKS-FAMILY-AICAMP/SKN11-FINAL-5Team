"""
환경 설정 및 LLM 클라이언트 관리 (OpenAI → Gemini fallback)
"""
import os
import logging
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv

# config/env_config.py

from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

# OpenAI LLM 설정
llm = ChatOpenAI(
    model_name="gpt-4", 
    temperature=0.3
)

# 벡터스토어 (예: ChromaDB) 설정
embedding = OpenAIEmbeddings()

# 예: Chroma vector store 로드
vectorstore = Chroma(
    collection_name="global-documents", 
    embedding_function=embedding,
    persist_directory="./vector_db_text-3-small_pdf"
)


# 환경 변수 로드
load_dotenv()

logger = logging.getLogger(__name__)

class LLMConfig:
    """LLM 설정 클래스"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.current_provider = None
        self.openai_client = None
        self.gemini_client = None
        
    def get_available_providers(self) -> list:
        """사용 가능한 LLM 프로바이더 목록 반환"""
        providers = []
        if self.openai_api_key:
            providers.append('openai')
        if self.gemini_api_key:
            providers.append('gemini')
        return providers
    
    def initialize_openai(self):
        """OpenAI 클라이언트 초기화"""
        try:
            import openai
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI 클라이언트 초기화 성공")
            return True
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 초기화 실패: {e}")
            return False
    
    def initialize_gemini(self):
        """Gemini 클라이언트 초기화"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_client = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini 클라이언트 초기화 성공")
            return True
        except Exception as e:
            logger.error(f"Gemini 클라이언트 초기화 실패: {e}")
            return False

# 전역 LLM 설정 인스턴스
_llm_config = LLMConfig()

class LLMClient:
    """LLM 클라이언트 (자동 fallback 지원)"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.current_provider = None
        self.initialize_clients()
    
    def initialize_clients(self):
        """클라이언트 초기화 (우선순위: OpenAI → Gemini)"""
        # OpenAI 먼저 시도
        if self.config.openai_api_key and self.config.initialize_openai():
            self.current_provider = 'openai'
            logger.info("Primary LLM: OpenAI")
            return
        
        # OpenAI 실패 시 Gemini 시도
        if self.config.gemini_api_key and self.config.initialize_gemini():
            self.current_provider = 'gemini'
            logger.info("Primary LLM: Gemini (fallback)")
            return
        
        logger.warning("사용 가능한 LLM이 없습니다. API 키를 확인해주세요.")
    
    def generate_response(self, messages: list, **kwargs) -> str:
        """응답 생성 (자동 fallback)"""
        # 1차 시도: 현재 프로바이더
        try:
            if self.current_provider == 'openai':
                return self._generate_openai(messages, **kwargs)
            elif self.current_provider == 'gemini':
                return self._generate_gemini(messages, **kwargs)
        except Exception as e:
            logger.warning(f"{self.current_provider} 응답 생성 실패: {e}")
            
        # 2차 시도: fallback
        try:
            if self.current_provider == 'openai' and self.config.gemini_client:
                logger.info("Gemini로 fallback 시도")
                return self._generate_gemini(messages, **kwargs)
            elif self.current_provider == 'gemini' and self.config.openai_client:
                logger.info("OpenAI로 fallback 시도")
                return self._generate_openai(messages, **kwargs)
        except Exception as e:
            logger.error(f"Fallback도 실패: {e}")
        
        return "죄송합니다. 현재 AI 서비스에 접속할 수 없습니다."
    
    def _generate_openai(self, messages: list, **kwargs) -> str:
        """OpenAI로 응답 생성"""
        if not self.config.openai_client:
            raise Exception("OpenAI 클라이언트가 초기화되지 않았습니다")
        
        response = self.config.openai_client.chat.completions.create(
            model=kwargs.get('model', 'gpt-3.5-turbo'),
            messages=messages,
            max_tokens=kwargs.get('max_tokens', 1000),
            temperature=kwargs.get('temperature', 0.7)
        )
        return response.choices[0].message.content
    
    def _generate_gemini(self, messages: list, **kwargs) -> str:
        """Gemini로 응답 생성"""
        if not self.config.gemini_client:
            raise Exception("Gemini 클라이언트가 초기화되지 않았습니다")
        
        # messages를 Gemini 형식으로 변환
        prompt = self._convert_messages_to_prompt(messages)
        
        response = self.config.gemini_client.generate_content(
            prompt,
            generation_config={
                'max_output_tokens': kwargs.get('max_tokens', 1000),
                'temperature': kwargs.get('temperature', 0.7)
            }
        )
        return response.text
    
    def _convert_messages_to_prompt(self, messages: list) -> str:
        """OpenAI 메시지 형식을 Gemini 프롬프트로 변환"""
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"[시스템 지시사항]\n{content}\n")
            elif role == 'user':
                prompt_parts.append(f"[사용자]\n{content}\n")
            elif role == 'assistant':
                prompt_parts.append(f"[어시스턴트]\n{content}\n")
        
        return "\n".join(prompt_parts)
    
    def get_status(self) -> Dict[str, Any]:
        """현재 LLM 상태 반환"""
        return {
            'current_provider': self.current_provider,
            'available_providers': self.config.get_available_providers(),
            'openai_available': bool(self.config.openai_client),
            'gemini_available': bool(self.config.gemini_client)
        }

# 전역 LLM 클라이언트 인스턴스
_llm_client = None

def get_llm_client() -> LLMClient:
    """LLM 클라이언트 싱글톤 반환"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient(_llm_config)
    return _llm_client

def get_config() -> Dict[str, Any]:
    """전체 환경 설정 반환"""
    return {
        'app_name': os.getenv('APP_NAME', 'Solo Preneur Helper'),
        'debug': os.getenv('DEBUG', 'False').lower() == 'true',
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'max_tokens': int(os.getenv('MAX_TOKENS', '1000')),
        'temperature': float(os.getenv('TEMPERATURE', '0.7')),
        'llm_config': {
            'available_providers': _llm_config.get_available_providers(),
            'primary_provider': 'openai' if _llm_config.openai_api_key else 'gemini'
        }
    }

def test_llm_connection():
    """LLM 연결 테스트"""
    client = get_llm_client()
    
    print("🔍 LLM 연결 테스트 시작")
    print(f"현재 상태: {client.get_status()}")
    
    # 간단한 테스트 메시지
    test_messages = [
        {"role": "system", "content": "당신은 도움이 되는 AI 어시스턴트입니다."},
        {"role": "user", "content": "안녕하세요! 간단한 인사말을 해주세요."}
    ]
    
    try:
        response = client.generate_response(test_messages)
        print(f"✅ LLM 응답 테스트 성공: {response[:100]}...")
        return True
    except Exception as e:
        print(f"❌ LLM 응답 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    test_llm_connection()