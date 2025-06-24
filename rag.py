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

logger = logging.getLogger(__name__)

class RAG:

    def __init__(self):
        # 벡터 DB 경로
        self.persist_directory = os.path.abspath(settings.VECTOR_DB_PATH)
        os.makedirs(self.persist_directory, exist_ok=True)
        logger.info(f"Vector DB path: {self.persist_directory}")
        
        # OpenAI 임베딩 설정
        self.embedding_function = OpenAIEmbeddings(
            model="text-embedding-3-small",
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
    
    def _extract_doc_info(self, filename: str) -> Tuple[str, str, str]:
        """파일명에서 문서 정보 추출"""
        # 확장자 제거
        doc_name = filename.replace('.pdf', '')
        
        # Unicode 정규화 (한글 파일명 문제 해결)
        doc_name = unicodedata.normalize('NFC', doc_name)
        
        # 페르소나와 카테고리 결정
        mapping = self.doc_type_mapping.get(doc_name)
        
        if mapping is None:
            logger.error(f"No mapping found for document: {doc_name}")
            logger.error(f"Document name length: {len(doc_name)}")
            logger.error(f"Document name bytes: {doc_name.encode('utf-8')}")
            logger.error(f"Available mappings: {list(self.doc_type_mapping.keys())}")
            # Try to find similar keys
            similar_keys = [key for key in self.doc_type_mapping.keys() if key in doc_name or doc_name in key]
            if similar_keys:
                logger.error(f"Similar keys found: {similar_keys}")
            raise ValueError(f"No mapping configuration found for document: {doc_name}")
        
        return doc_name, mapping["persona"], mapping["category"], mapping["source"]
    
    def process_pdf_directory(self, pdf_dir: str):
        """PDF 디렉토리 처리 - 새로운 메타데이터 구조 적용"""
        pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
        processed_count = 0
        
        for filename in pdf_files:
            # 문서 정보 추출
            doc_name, persona, category, source = self._extract_doc_info(filename)
            pdf_path = os.path.join(pdf_dir, filename)
            
            logger.info(f"Processing {doc_name} (persona: {persona}, category: {category})")
            
            try:
                # 문서 고유 ID 생성
                doc_id = str(uuid.uuid4())
                
                # PDF 로드 및 처리
                docs = PyMuPDFLoader(pdf_path).load()
                splits = self.text_splitter.split_documents(docs)
                texts = [doc.page_content for doc in splits]
                
                # 새로운 메타데이터 구조로 변경
                metadatas = []
                for i, split in enumerate(splits):
                    chunk_id = str(uuid.uuid4())
                    metadata = {
                        "doc_id": doc_id,
                        "chunk_id": chunk_id,
                        "persona": persona,
                        "category": category,
                        "topic": doc_name,  # 주제로 문서명 사용
                        "source": ", ".join(source) if isinstance(source, list) else source,  # 리스트를 문자열로 변환
                        "last_updated": datetime.now().isoformat()
                    }
                    metadatas.append(metadata)
                
                # 배치 처리를 위한 기본 변수 설정
                total_texts = len(texts)
                logger.info(f"Total chunks to process: {total_texts}")
                
                # 배치 크기 제한 - 토큰 수를 고려하여 동적 조정
                MAX_BATCH_SIZE = 200  # 기본 배치 크기 감소
                
                # 대용량 문서의 경우 배치 크기를 더 작게 설정
                if total_texts > 500:
                    MAX_BATCH_SIZE = 100
                elif total_texts > 200:
                    MAX_BATCH_SIZE = 150
                
                for i in range(0, total_texts, MAX_BATCH_SIZE):
                    end_idx = min(i + MAX_BATCH_SIZE, total_texts)
                    batch_texts = texts[i:end_idx]
                    batch_metadatas = metadatas[i:end_idx]
                    
                    logger.info(f"Processing batch {i//MAX_BATCH_SIZE + 1}: chunks {i} to {end_idx-1}")
                    
                    # 토큰 수 추정 및 조정
                    estimated_tokens = sum(len(self.tokenizer.encode(text)) for text in batch_texts)
                    logger.info(f"Estimated tokens for batch: {estimated_tokens}")
                    
                    # 토큰 수가 너무 많은 경우 배치를 더 작게 나누기
                    if estimated_tokens > 250000:  # 25만 토큰 제한
                        # 배치를 절반으로 나누기
                        mid_point = len(batch_texts) // 2
                        sub_batches = [
                            (batch_texts[:mid_point], batch_metadatas[:mid_point]),
                            (batch_texts[mid_point:], batch_metadatas[mid_point:])
                        ]
                        
                        for sub_batch_idx, (sub_texts, sub_metas) in enumerate(sub_batches):
                            if sub_texts:  # 빈 배치 방지
                                logger.info(f"Processing sub-batch {sub_batch_idx + 1} (size: {len(sub_texts)})")
                                try:
                                    self.vectorstore.add_texts(texts=sub_texts, metadatas=sub_metas)
                                except Exception as batch_error:
                                    logger.error(f"Error in sub-batch {sub_batch_idx + 1}: {batch_error}")
                                    continue
                    else:
                        # 정상적인 배치 처리
                        try:
                            self.vectorstore.add_texts(texts=batch_texts, metadatas=batch_metadatas)
                        except Exception as batch_error:
                            logger.error(f"Error in batch {i//MAX_BATCH_SIZE + 1}: {batch_error}")
                            continue
                    
                logger.info(f"Successfully indexed {doc_name} with {len(texts)} chunks")
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                continue
        
        # 모든 문서 처리 완료
        logger.info(f"Processed {processed_count} PDF files")
        logger.info("Vector database automatically persisted to disk")
    
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
    
    def add_document(
        self, 
        text: str, 
        topic: str,
        persona: str = None,
        category: str = None,
        source: str = "manual_input"
    ) -> bool:
        """단일 문서 추가 - 새로운 메타데이터 구조 사용"""
        try:
            # 문서 ID 생성
            doc_id = str(uuid.uuid4())
            
            # 페르소나와 카테고리 기본값 설정
            if not persona:
                persona = "business_consultant"
            if not category:
                category = "general"
            
            # 텍스트 분할
            splits = self.text_splitter.split_text(text)
            texts = splits
            
            # 각 청크에 새로운 메타데이터 구조 적용
            metadatas = []
            for i in range(len(splits)):
                chunk_id = str(uuid.uuid4())
                chunk_metadata = {
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                    "persona": persona,
                    "category": category,
                    "topic": topic,
                    "source": ", ".join(source) if isinstance(source, list) else source,  # 리스트를 문자열로 변환
                    "last_updated": datetime.now().isoformat()
                }
                metadatas.append(chunk_metadata)
            
            # 배치 크기 제한 적용 - 동적 조정
            MAX_BATCH_SIZE = 200
            total_texts = len(texts)
            
            if total_texts > 500:
                MAX_BATCH_SIZE = 100
            elif total_texts > 200:
                MAX_BATCH_SIZE = 150
            
            for i in range(0, total_texts, MAX_BATCH_SIZE):
                end_idx = min(i + MAX_BATCH_SIZE, total_texts)
                batch_texts = texts[i:end_idx]
                batch_metadatas = metadatas[i:end_idx]
                
                # 에러 핸들링과 함께 벡터 스토어에 배치 추가
                try:
                    self.vectorstore.add_texts(texts=batch_texts, metadatas=batch_metadatas)
                except Exception as batch_error:
                    logger.error(f"Error adding batch {i//MAX_BATCH_SIZE + 1}: {batch_error}")
                    continue
                
            logger.info(f"Successfully added document: {topic} with {len(texts)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False

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
