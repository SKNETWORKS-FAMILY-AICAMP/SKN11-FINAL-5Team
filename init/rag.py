import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import chromadb
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from langchain_chroma import Chroma
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_openai import OpenAIEmbeddings
from deep_translator import GoogleTranslator
from config import settings
import os
import uuid
import unicodedata
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class RAG:

    def __init__(self):
        # 벡터 DB 경로
        self.persist_directory = os.path.abspath(settings.VECTOR_DB_PATH)
        os.makedirs(self.persist_directory, exist_ok=True)
        logger.info(f"Vector DB path: {self.persist_directory}")
        
        # OpenAI 임베딩 설정
        self.embedding_function = OpenAIEmbeddings(
            model=SentenceTransformer("nlpai-lab/KURE-v1"),
            openai_api_key=settings.OPENAI_API_KEY,
            dimensions=384  # dimensions는 직접 파라미터로 전달
        )
        
        # 텍스트 분할기
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # Chroma 벡터스토어 초기화 (langchain-chroma 사용)
        self.vectorstore = Chroma(
            collection_name="global-documents",
            embedding_function=self.embedding_function,
            persist_directory=self.persist_directory
        )
        logger.info("Chroma vectorstore initialized")
        
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # 번역기 초기화
        self.ko_to_en = GoogleTranslator(source='ko', target='en')
        self.en_to_ko = GoogleTranslator(source='en', target='ko')
        
        # 문서 타입별 페르소나와 카테고리 매핑
        self.doc_type_mapping = {
            "이커머스비즈니스모델": {"persona": "e_commerce", "category": "business_planning", "source": ["blog"]},
            "뷰티샵비즈니스모델": {"persona": "beautyshop", "category": "business_planning", "source": ["blog"]}, 
            "크리에이터비즈니스모델": {"persona": "creator", "category": "business_planning", "source": ["blog"]},
            "린캔버스": {"persona": "common", "category": "business_planning", "source": ["blog", "youtube"]},
            "뷰티샵창업가이드": {"persona": "beautyshop", "category": "business_planning", "source": ["blog", "youtube"]},
            "사업자등록": {"persona": "common", "category": "business_planning", "source": ["blog", "goverment"]},
            "이커머스창업가이드": {"persona": "e_commerce", "category": "business_planning", "source": ["blog", "youtube"]},
            "유튜브크리에이터가이드": {"persona": "creator", "category": "business_planning", "source": ["blog", "youtube"]},
            "정부지원사업": {"persona": "common", "category": "business_planning", "source": ["goverment"]}
        }
        
        # 문서 패턴 (확장된 패턴)
        self.doc_pattern = r"(.+)\.pdf"
    
    def search_with_translation(
        self,
        query: str,
        persona: Optional[str] = None,
        category: Optional[str] = None,
        topic: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """한국어 질문을 영어로 번역하여 검색 - 새로운 메타데이터 구조 사용"""
        
        # 한국어 질문을 영어로 번역
        translated_query = self.ko_to_en.translate(query)
        logger.info(f"Translated query: {translated_query}")
        
        # 검색 필터 구성
        search_kwargs = {"k": 5}
        filter_dict = {}
        
        if persona:
            filter_dict["persona"] = persona
        if category:
            filter_dict["category"] = category
        if topic:
            filter_dict["topic"] = topic
            
        if filter_dict:
            search_kwargs["filter"] = filter_dict
            
        retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs=search_kwargs
        )
        
        # 문서 검색
        docs = retriever.get_relevant_documents(translated_query)
        
        if not docs:
            return "관련 문서를 찾지 못했습니다.", []
        
        # 컨텍스트와 참조 구성
        context_parts = []
        references = []
        
        for i, doc in enumerate(docs[:3]):  # 최대 3개 문서
            context_parts.append(doc.page_content)
            metadata = doc.metadata
            references.append({
                "doc_id": metadata.get("doc_id", "Unknown"),
                "chunk_id": metadata.get("chunk_id", "Unknown"),
                "persona": metadata.get("persona", "Unknown"),
                "category": metadata.get("category", "Unknown"),
                "topic": metadata.get("topic", "Unknown"),
                "source": metadata.get("source", "Unknown"),
                "last_updated": metadata.get("last_updated", "Unknown")
            })
        
        context = "\n\n---\n\n".join(context_parts)
        return context, references
    
    def search_by_persona(self, query: str, persona: str) -> Tuple[str, List[Dict[str, Any]]]:
        """페르소나별 검색"""
        return self.search_with_translation(query, persona=persona)
    
    def search_by_category(self, query: str, category: str) -> Tuple[str, List[Dict[str, Any]]]:
        """카테고리별 검색"""
        return self.search_with_translation(query, category=category)
    
    def search_by_topic(self, query: str, topic: str) -> Tuple[str, List[Dict[str, Any]]]:
        """토픽별 검색"""
        return self.search_with_translation(query, topic=topic)
    
    def get_available_personas(self) -> List[str]:
        """사용 가능한 페르소나 목록 반환"""
        return list(set([mapping["persona"] for mapping in self.doc_type_mapping.values()]))
    
    def get_available_categories(self) -> List[str]:
        """사용 가능한 카테고리 목록 반환"""
        return list(set([mapping["category"] for mapping in self.doc_type_mapping.values()]))
    
    def get_available_topics(self) -> List[str]:
        """사용 가능한 토픽 목록 반환"""
        return list(self.doc_type_mapping.keys())
        
if __name__ == "__main__":
    rag = RAG()
    
    # 테스트 검색
    query = "사업자 등록은 어떻게 해야 하나요?"
    context, references = rag.search_with_translation(query, persona="beautyshop")
    print("Context:", context)
    print("References:", references)
    
    # 사용 가능한 페르소나, 카테고리, 토픽 출력
    print("Available personas:", rag.get_available_personas())
    print("Available categories:", rag.get_available_categories())
    print("Available topics:", rag.get_available_topics())
