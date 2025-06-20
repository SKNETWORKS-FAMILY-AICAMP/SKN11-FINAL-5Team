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
from backend_v1.config import settings
import os

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
        
        # 문서 타입 패턴
        self.doc_type_pattern = r"(.*?)_(visa_info|insurance_info|immigration_regulations_info|immigration_safety_info)\.pdf"
    
    def process_pdf_directory(self, pdf_dir: str):
        """PDF 디렉토리 처리"""
        pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
        processed_count = 0
        
        for filename in pdf_files:
            match = re.match(self.doc_type_pattern, filename)
            if not match:
                logger.warning(f"Skipping file with invalid pattern: {filename}")
                continue
                
            country, doc_type = match.groups()
            pdf_path = os.path.join(pdf_dir, filename)
            
            logger.info(f"Processing {country.upper()} - {doc_type}")
            
            try:
                # PDF 로드 및 처리
                docs = PyMuPDFLoader(pdf_path).load()
                splits = self.text_splitter.split_documents(docs)
                texts = [doc.page_content for doc in splits]
                
                # 메타데이터
                metadatas = [
                    {
                        "country": country,
                        "document_type": doc_type,
                        "tag": f"{country}_{doc_type}",
                        "updated_at": datetime.now().isoformat(),
                        "source": filename
                    }
                    for _ in splits
                ]
                
                # 배치 크기 제한
                MAX_BATCH_SIZE = 500  # 더 작은 배치 크기 사용
                
                # 배치 처리
                total_texts = len(texts)
                logger.info(f"Total chunks to process: {total_texts}")
                
                for i in range(0, total_texts, MAX_BATCH_SIZE):
                    end_idx = min(i + MAX_BATCH_SIZE, total_texts)
                    batch_texts = texts[i:end_idx]
                    batch_metadatas = metadatas[i:end_idx]
                    
                    logger.info(f"Processing batch {i//MAX_BATCH_SIZE + 1}: chunks {i} to {end_idx-1}")
                    
                    # 벡터 스토어에 배치 추가
                    self.vectorstore.add_texts(texts=batch_texts, metadatas=batch_metadatas)
                    
                logger.info(f"Successfully indexed {country}_{doc_type}")
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                continue
        
        # 모든 문서 처리 완료
        logger.info(f"Processed {processed_count} PDF files")
        
        # 최신 버전의 Chroma는 자동으로 persist됨
        logger.info("Vector database automatically persisted to disk")
    
    def search_with_translation(
        self,
        query: str,
        country: Optional[str] = None,
        doc_type: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """한국어 질문을 영어로 번역하여 검색"""
        
        # 태그 구성
        tag = f"{country}_{doc_type}" if country and doc_type else country
        
        # 한국어 질문을 영어로 번역
        translated_query = self.ko_to_en.translate(query)
        logger.info(f"Translated query: {translated_query}")
        
        # 검색 실행 (MMR 사용)
        search_kwargs = {"k": 5}
        if tag:
            search_kwargs["filter"] = {"tag": tag}
            
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
                "title": metadata.get("document_type", "Unknown"),
                "country": metadata.get("country", "Unknown"),
                "tag": metadata.get("tag", ""),
                "updated_at": metadata.get("updated_at", "")
            })
        
        context = "\n\n---\n\n".join(context_parts)
        return context, references
    
    def add_document(self, text: str, metadata: Dict[str, Any]) -> bool:
        """단일 문서 추가"""
        try:
            # 텍스트 분할
            splits = self.text_splitter.split_text(text)
            texts = splits
            
            # 각 청크에 메타데이터 추가
            metadatas = []
            for i in range(len(splits)):
                chunk_metadata = {
                    **metadata,
                    "chunk_index": i,
                    "total_chunks": len(splits)
                }
                metadatas.append(chunk_metadata)
            
            # 배치 크기 제한 적용
            MAX_BATCH_SIZE = 1000
            total_texts = len(texts)
            
            for i in range(0, total_texts, MAX_BATCH_SIZE):
                end_idx = min(i + MAX_BATCH_SIZE, total_texts)
                batch_texts = texts[i:end_idx]
                batch_metadatas = metadatas[i:end_idx]
                
                # 벡터 스토어에 배치 추가
                self.vectorstore.add_texts(texts=batch_texts, metadatas=batch_metadatas)
                
            return True
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False
        
if __name__ == "__main__":
    rag = RAG()
    query = "프랑스에서 비자 연장하려면?"
    context, references = rag.search_with_translation(query, country="france", doc_type="visa_info")
    print("Context:", context)
    print("References:", references)