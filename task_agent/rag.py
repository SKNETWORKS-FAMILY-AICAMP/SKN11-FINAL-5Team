"""
간소화된 RAG 시스템 v3
"""

import logging
from typing import List, Optional

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from models import SearchResult, KnowledgeChunk, PersonaType
from config import config

logger = logging.getLogger(__name__)

class RAGManager:
    """간소화된 RAG 매니저"""
    
    def __init__(self):
        """RAG 매니저 초기화"""
        self.client = None
        self.collection = None
        self.setup_chroma()
        
    def setup_chroma(self):
        """ChromaDB 설정"""
        try:
            # ChromaDB 클라이언트 초기화
            self.client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
            
            # 임베딩 함수 설정
            embedding_function = None
            if config.OPENAI_API_KEY:
                embedding_function = OpenAIEmbeddingFunction(
                    model_name=config.EMBEDDING_MODEL,
                    api_key=config.OPENAI_API_KEY
                )
            
            # 컬렉션 생성/조회
            self.collection = self.client.get_or_create_collection(
                name="knowledge_base",
                embedding_function=embedding_function
            )
            
            logger.info("RAG 매니저 초기화 완료")
            
        except Exception as e:
            logger.error(f"RAG 매니저 초기화 실패: {e}")
            
    async def search_knowledge(self, query: str, persona: PersonaType, 
                             topic: Optional[str] = None) -> SearchResult:
        """지식 베이스 검색"""
        try:
            if not self.collection:
                return SearchResult(chunks=[], sources=[], total_results=0)
            
            # 검색 조건 구성
            where_conditions = {
                "persona": {"$in": [persona.value, "common"]}
            }
            
            if topic:
                where_conditions["topic"] = topic
            
            # 벡터 검색
            results = self.collection.query(
                query_texts=[query],
                n_results=config.MAX_SEARCH_RESULTS,
                where=where_conditions,
                include=['documents', 'metadatas', 'distances']
            )
            
            # 결과 처리
            chunks = []
            sources = set()
            
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0] or [],
                    results['distances'][0] or []
                )):
                    chunk = KnowledgeChunk(
                        content=doc,
                        metadata=metadata or {},
                        relevance_score=max(0, 1 - distance) if distance else 0
                    )
                    chunks.append(chunk)
                    
                    if metadata and 'source' in metadata:
                        sources.add(metadata['source'])
            
            return SearchResult(
                chunks=chunks,
                sources=list(sources),
                total_results=len(chunks)
            )
            
        except Exception as e:
            logger.error(f"지식 검색 실패: {e}")
            return SearchResult(chunks=[], sources=[], total_results=0)
    
    async def add_knowledge(self, content: str, persona: PersonaType, 
                          topic: str, source: str = "manual") -> bool:
        """지식 추가"""
        try:
            if not self.collection:
                return False
            
            # 문서를 청크로 분할
            chunks = self._split_content(content)
            
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "persona": persona.value,
                    "topic": topic,
                    "source": source,
                    "chunk_id": i
                })
                ids.append(f"{persona.value}_{topic}_{source}_{i}")
            
            # ChromaDB에 추가
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"지식 추가 완료: {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"지식 추가 실패: {e}")
            return False
    
    def _split_content(self, content: str) -> List[str]:
        """컨텐츠를 청크로 분할"""
        # 간단한 문단 기반 분할
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk + paragraph) > config.CHUNK_SIZE and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
