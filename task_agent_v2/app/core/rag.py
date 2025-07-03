import logging
from typing import Dict, List, Any, Optional

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from ..schemas.base import (
    DocumentMetadata,
    SearchResult, KnowledgeChunk, PersonaType
)
from .config import CHROMA_PERSIST_DIR, CHUNK_SIZE, MAX_SEARCH_RESULTS, OPENAI_API_KEY, config

logger = logging.getLogger(__name__)

class RAGManager:
    """간소화된 RAG 매니저"""
    
    def __init__(self, persist_directory: str = None):
        """RAG 매니저 초기화"""
        persist_dir = persist_directory or CHROMA_PERSIST_DIR
        
        try:
            # Chroma DB 클라이언트 초기화
            self.chroma_client = chromadb.PersistentClient(path=persist_dir)
            
            # 임베딩 함수 설정
            self.embedding_function = OpenAIEmbeddingFunction(
                model_name=config.llm.embedding_model,
                api_key=OPENAI_API_KEY
            )
            
            # 컬렉션 생성
            self.collection = self.chroma_client.get_or_create_collection(
                name="task_knowledge",
                embedding_function=self.embedding_function
            )
            
            logger.info("RAG 매니저 초기화 완료")
            
        except Exception as e:
            logger.error(f"RAG 매니저 초기화 실패: {e}")
            # 백업으로 빈 컬렉션 생성
            self.collection = None

    async def search_knowledge(self, query: str, persona: PersonaType, 
                             topic: Optional[str] = None, 
                             n_results: int = None) -> SearchResult:
        """지식 베이스 검색"""
        try:
            if not self.collection:
                # 컬렉션이 없는 경우 빈 결과 반환
                return SearchResult(chunks=[], sources=[], total_results=0)
            
            n_results = n_results or MAX_SEARCH_RESULTS
            
            # 검색 조건 구성
            where_conditions = {
                "persona": {"$in": [persona.value, "common"]}
            }
            
            if topic and topic != "general":
                where_conditions["topic"] = topic
            
            # 벡터 검색 실행
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_conditions,
                include=['documents', 'metadatas', 'distances']
            )
            
            # 결과 처리
            knowledge_chunks = []
            sources = set()
            
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0] if results['metadatas'] else [],
                    results['distances'][0] if results['distances'] else []
                )):
                    chunk = KnowledgeChunk(
                        content=doc,
                        metadata=metadata or {},
                        relevance_score=1 - distance if distance else 0,
                        rank=i + 1
                    )
                    knowledge_chunks.append(chunk)
                    
                    if metadata and 'source' in metadata:
                        sources.add(metadata['source'])
            
            return SearchResult(
                chunks=knowledge_chunks,
                sources=list(sources),
                total_results=len(knowledge_chunks)
            )
            
        except Exception as e:
            logger.error(f"지식 검색 실패: {e}")
            return SearchResult(chunks=[], sources=[], total_results=0)

    async def add_document(self, content: str, metadata: DocumentMetadata, 
                         chunk_size: int = None) -> int:
        """문서를 청크로 나누어 벡터 DB에 추가"""
        try:
            if not self.collection:
                logger.warning("컬렉션이 초기화되지 않았습니다")
                return 0
            
            chunk_size = chunk_size or CHUNK_SIZE
            
            # 문서를 청크로 분할
            chunks = self._split_document(content, chunk_size)
            
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    documents.append(chunk.strip())
                    
                    chunk_metadata = metadata.dict()
                    chunk_metadata["chunk_id"] = i
                    
                    metadatas.append(chunk_metadata)
                    ids.append(f"{metadata.doc_id}_chunk_{i}")
            
            # Chroma DB에 추가
            if documents:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            
            logger.info(f"문서 추가 완료: {metadata.doc_id} ({len(documents)} chunks)")
            return len(documents)
            
        except Exception as e:
            logger.error(f"문서 추가 실패: {e}")
            return 0

    def _split_document(self, content: str, chunk_size: int) -> List[str]:
        """문서를 의미 단위로 청크 분할"""
        # 간단한 문단 단위 분할
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            if len(current_chunk + paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
