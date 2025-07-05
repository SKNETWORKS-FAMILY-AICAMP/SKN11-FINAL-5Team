import os
import logging
import uuid
import unicodedata
from datetime import datetime
import tiktoken

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from chromadb import PersistentClient
from config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class VectorDBManager:
    def __init__(self):
        self.persist_directory = os.path.abspath(settings.VECTOR_DB_PATH)
        os.makedirs(self.persist_directory, exist_ok=True)
        
        self.embedding_function = HuggingFaceEmbeddings(
            model_name="nlpai-lab/KURE-v1"
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.vectorstore = Chroma(
            collection_name="global-documents",
            embedding_function=self.embedding_function,
            persist_directory=self.persist_directory
        )
        
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # 문서 타입 매핑
        self.doc_type_mapping = {
            "이커머스비즈니스모델": {"persona": "e_commerce", "category": "business_planning", "topic": "business_model,market_research,idea_validation,mvp_development,growth_strategy", "source": "blog"},
            "뷰티샵비즈니스모델": {"persona": "beautyshop", "category": "business_planning", "topic": "business_model,financial_planning,growth_strategy,market_research", "source": "blog"}, 
            "크리에이터비즈니스모델": {"persona": "creator", "category": "business_planning", "topic": "business_model,growth_strategy,financial_planning,risk_management", "source": "blog"},
            "린캔버스": {"persona": "common", "category": "business_planning", "topic": "business_model,idea_validation", "source": "blog,youtube"},
            "뷰티샵창업가이드": {"persona": "beautyshop", "category": "business_planning", "topic": "startup_preparation,business_registration,financial_planning", "source": "blog,youtube"},
            "사업자등록": {"persona": "common", "category": "business_planning", "topic": "business_registration", "source": "blog,gov"},
            "이커머스창업가이드": {"persona": "e_commerce", "category": "business_planning", "topic": "startup_preparation,idea_validation,business_model,market_research,business_registration,financial_planning,growth_strategy,risk_management", "source": "blog,youtube"},
            "유튜브크리에이터가이드": {"persona": "creator", "category": "business_planning", "topic": "startup_preparation,business_registration,financial_planning,risk_management", "source": "blog,youtube"},
            "정부지원사업": {"persona": "common", "category": "business_planning", "topic": "funding_strategy", "source": "goverment"}
        }

    def get_existing_documents(self):
        """기존 벡터 DB의 문서 목록 조회"""
        try:
            client = PersistentClient(path=settings.VECTOR_DB_PATH)
            collection = client.get_collection("global-documents")
            
            # 모든 메타데이터에서 topic 추출
            results = collection.get()
            existing_topics = set()
            
            if results and results['metadatas']:
                for metadata in results['metadatas']:
                    if 'topic' in metadata:
                        existing_topics.add(metadata['topic'])
            
            return existing_topics
            
        except Exception as e:
            logger.info(f"기존 문서 조회 중 오류 (새 DB인 경우 정상): {e}")
            return set()

    def get_new_pdf_files(self, pdf_dir: str):
        """새로 추가할 PDF 파일 목록 조회"""
        if not os.path.exists(pdf_dir):
            logger.error(f"PDF 디렉토리를 찾을 수 없습니다: {pdf_dir}")
            return []
        
        # 디렉토리의 모든 PDF 파일
        all_pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
        
        # 기존 문서 목록 조회
        existing_topics = self.get_existing_documents()
        
        # 새로운 문서만 필터링
        new_files = []
        for pdf_file in all_pdf_files:
            doc_name = unicodedata.normalize('NFC', pdf_file.replace('.pdf', ''))
            if doc_name not in existing_topics:
                new_files.append(pdf_file)
            else:
                logger.info(f"이미 존재하는 문서를 건너뜁니다: {doc_name}")
        
        return new_files

    def check_vector_db_status(self):
        """벡터 DB 상태 확인"""
        try:
            if not os.path.exists(settings.VECTOR_DB_PATH):
                logger.info("벡터 DB가 존재하지 않습니다. 새로 생성합니다.")
                return "new"
            
            client = PersistentClient(path=settings.VECTOR_DB_PATH)
            try:
                collection = client.get_collection("global-documents")
                count = collection.count()
                logger.info(f"기존 벡터 DB에 {count}개의 문서가 있습니다")
                
                if count == 0:
                    return "empty"
                
                # 메타데이터 구조 확인
                sample_results = collection.peek(limit=1)
                if sample_results['metadatas']:
                    sample_metadata = sample_results['metadatas'][0]
                    required_fields = ['doc_id', 'chunk_id', 'persona', 'category', 'topic', 'source', 'last_updated']
                    missing_fields = [field for field in required_fields if field not in sample_metadata]
                    
                    if missing_fields:
                        logger.warning(f"메타데이터 구조가 오래되었습니다. 재초기화가 필요합니다.")
                        return "outdated"
                    else:
                        return "ready"
                        
            except Exception:
                logger.info("컬렉션을 찾을 수 없습니다.")
                return "new"
                
        except Exception as e:
            logger.error(f"벡터 DB 상태 확인 오류: {e}")
            return "error"

    def add_new_documents(self):
        """새로운 문서들을 벡터 DB에 추가"""
        pdf_dir = os.path.join(os.path.dirname(__file__), "data", "BP")
        
        # 벡터 DB 상태 확인
        db_status = self.check_vector_db_status()
        
        if db_status == "outdated":
            logger.warning("메타데이터 구조가 오래되어 전체 재초기화를 수행합니다.")
            try:
                client = PersistentClient(path=settings.VECTOR_DB_PATH)
                client.delete_collection("global-documents")
                logger.info("기존 컬렉션을 삭제했습니다.")
            except Exception as e:
                logger.error(f"컬렉션 삭제 오류: {e}")
            
            # 전체 초기화
            return self.initialize_all_documents(pdf_dir)
        
        elif db_status in ["new", "empty", "error"]:
            logger.info("벡터 DB를 새로 초기화합니다.")
            return self.initialize_all_documents(pdf_dir)
        
        elif db_status == "ready":
            # 새로운 문서만 추가
            new_files = self.get_new_pdf_files(pdf_dir)
            
            if not new_files:
                logger.info("추가할 새로운 문서가 없습니다.")
                return
            
            logger.info(f"{len(new_files)}개의 새로운 문서를 추가합니다: {new_files}")
            self.process_pdf_files(pdf_dir, new_files)
            logger.info("새로운 문서 추가 완료")

    def initialize_all_documents(self, pdf_dir: str):
        """모든 문서를 처리하여 벡터 DB 초기화"""
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir, exist_ok=True)
            logger.info(f"디렉토리를 생성했습니다: {os.path.abspath(pdf_dir)}")
            return
        
        all_pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
        if not all_pdf_files:
            logger.warning(f"PDF 파일이 없습니다: {pdf_dir}")
            return
        
        logger.info(f"전체 {len(all_pdf_files)}개의 PDF 파일을 처리합니다")
        self.process_pdf_files(pdf_dir, all_pdf_files)
        logger.info("벡터 데이터베이스 초기화 완료")

    def process_pdf_files(self, pdf_dir: str, pdf_files: list):
        """지정된 PDF 파일들 처리"""
        processed_count = 0
        
        for filename in pdf_files:
            doc_name = unicodedata.normalize('NFC', filename.replace('.pdf', ''))
            mapping = self.doc_type_mapping.get(doc_name)
            
            if not mapping:
                logger.error(f"문서 매핑을 찾을 수 없습니다: {doc_name}")
                logger.error(f"사용 가능한 매핑: {list(self.doc_type_mapping.keys())}")
                continue
            
            pdf_path = os.path.join(pdf_dir, filename)
            logger.info(f"처리 중: {doc_name}")
            
            try:
                doc_id = str(uuid.uuid4())
                docs = PyMuPDFLoader(pdf_path).load()
                splits = self.text_splitter.split_documents(docs)
                texts = [doc.page_content for doc in splits]
                
                # 메타데이터 생성
                metadatas = []
                for i, split in enumerate(splits):
                    metadata = {
                        "doc_id": doc_id,
                        "chunk_id": str(uuid.uuid4()),
                        "persona": mapping["persona"],
                        "category": mapping["category"],
                        "topic": mapping["topic"],
                        "source": ", ".join(mapping["source"]) if isinstance(mapping["source"], list) else mapping["source"],
                        "last_updated": datetime.now().isoformat()
                    }
                    metadatas.append(metadata)
                
                # 배치 처리
                self.add_texts_in_batches(texts, metadatas)
                
                logger.info(f"{doc_name} 인덱싱 완료 ({len(texts)} 청크)")
                processed_count += 1
                
            except Exception as e:
                logger.error(f"{filename} 처리 오류: {e}")
        
        logger.info(f"{processed_count}개의 PDF 파일 처리 완료")

    def add_texts_in_batches(self, texts: list, metadatas: list):
        """텍스트를 배치로 나누어 벡터스토어에 추가"""
        MAX_BATCH_SIZE = 200
        total_texts = len(texts)
        
        for i in range(0, total_texts, MAX_BATCH_SIZE):
            end_idx = min(i + MAX_BATCH_SIZE, total_texts)
            batch_texts = texts[i:end_idx]
            batch_metadatas = metadatas[i:end_idx]
            
            # 토큰 수 확인
            estimated_tokens = sum(len(self.tokenizer.encode(text)) for text in batch_texts)
            
            if estimated_tokens > 250000:
                # 배치를 더 작게 나누기
                mid_point = len(batch_texts) // 2
                sub_batches = [
                    (batch_texts[:mid_point], batch_metadatas[:mid_point]),
                    (batch_texts[mid_point:], batch_metadatas[mid_point:])
                ]
                
                for sub_texts, sub_metas in sub_batches:
                    if sub_texts:
                        try:
                            self.vectorstore.add_texts(texts=sub_texts, metadatas=sub_metas)
                        except Exception as e:
                            logger.error(f"서브 배치 처리 오류: {e}")
            else:
                try:
                    self.vectorstore.add_texts(texts=batch_texts, metadatas=batch_metadatas)
                except Exception as e:
                    logger.error(f"배치 처리 오류: {e}")

    def get_db_stats(self):
        """벡터 DB 통계 정보 조회"""
        try:
            client = PersistentClient(path=settings.VECTOR_DB_PATH)
            collection = client.get_collection("global-documents")
            
            total_count = collection.count()
            
            # 문서별 통계
            results = collection.get()
            if results and results['metadatas']:
                topics = {}
                for metadata in results['metadatas']:
                    if 'topic' in metadata:
                        topic = metadata['topic']
                        topics[topic] = topics.get(topic, 0) + 1
                
                logger.info(f"총 {total_count}개의 청크가 있습니다")
                logger.info("문서별 청크 수:")
                for topic, count in topics.items():
                    logger.info(f"  - {topic}: {count}개")
            
            return total_count
            
        except Exception as e:
            logger.error(f"통계 조회 오류: {e}")
            return 0


def main():
    """메인 실행 함수"""
    logger.info("=== 벡터 데이터베이스 관리 ===")
    
    manager = VectorDBManager()
    
    # 새로운 문서 추가 (기존 문서는 유지)
    manager.add_new_documents()
    
    # 최종 통계
    manager.get_db_stats()
    
    logger.info("완료")


if __name__ == "__main__":
    main()
