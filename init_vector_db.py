import os
import logging
from rag import RAG
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def initialize_vector_database():
    """벡터 데이터베이스 초기화 - 새로운 메타데이터 구조 적용"""
    
    # PDF 디렉토리 경로 설정 (현재 프로젝트의 data/BP 디렉토리 사용)
    pdf_dir = os.path.join(os.path.dirname(__file__), "data", "BP")
    
    # 디렉토리 확인
    if not os.path.exists(pdf_dir):
        logger.error(f"PDF directory not found: {pdf_dir}")
        logger.info("Creating directory and adding sample message...")
        os.makedirs(pdf_dir, exist_ok=True)
        
        # 샘플 파일 경로 출력
        logger.info(f"Please add PDF files to: {os.path.abspath(pdf_dir)}")
        return
    
    # PDF 파일 목록 확인
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {pdf_dir}")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    logger.info(f"Files: {pdf_files}")
    
    # RAG 인스턴스 생성
    rag = RAG()
    
    # 벡터 DB 경로 생성
    os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
    
    # PDF 파일들 처리
    logger.info("Starting PDF processing with new metadata structure...")
    logger.info("New metadata fields: doc_id, chunk_id, persona, category, topic, source, last_updated")
    
    rag.process_pdf_directory(pdf_dir)
    
    logger.info("Vector database initialization completed")
    logger.info(f"Available personas: {rag.get_available_personas()}")
    logger.info(f"Available categories: {rag.get_available_categories()}")
    logger.info(f"Available topics: {rag.get_available_topics()}")

def check_and_init_vector_db():
    """벡터 DB 상태 확인 및 필요시 초기화"""
    try:
        # 벡터 DB 경로 확인
        if not os.path.exists(settings.VECTOR_DB_PATH):
            logger.info("Vector DB not found. Initializing...")
            initialize_vector_database()
            return
        
        # ChromaDB collection 확인
        from chromadb import PersistentClient
        client = PersistentClient(path=settings.VECTOR_DB_PATH)
        
        try:
            collection = client.get_collection("global-documents")
            count = collection.count()
            logger.info(f"Vector DB exists with {count} documents")
            
            if count == 0:
                logger.warning("Vector DB is empty. Initializing...")
                initialize_vector_database()
            else:
                # 메타데이터 구조 확인
                try:
                    # 샘플 문서로 메타데이터 구조 체크
                    sample_results = collection.peek(limit=1)
                    if sample_results['metadatas']:
                        sample_metadata = sample_results['metadatas'][0]
                        required_fields = ['doc_id', 'chunk_id', 'persona', 'category', 'topic', 'source', 'last_updated']
                        missing_fields = [field for field in required_fields if field not in sample_metadata]
                        
                        if missing_fields:
                            logger.warning(f"Vector DB metadata structure is outdated. Missing fields: {missing_fields}")
                            logger.info("Reinitializing with new metadata structure...")
                            # 기존 컬렉션 삭제
                            client.delete_collection("global-documents")
                            initialize_vector_database()
                        else:
                            logger.info("Vector DB metadata structure is up to date")
                except Exception as e:
                    logger.warning(f"Could not check metadata structure: {e}")
                    
        except Exception as e:
            logger.info(f"Collection not found or error: {e}. Initializing...")
            initialize_vector_database()
            
    except Exception as e:
        logger.error(f"Error checking vector DB: {e}")

def verify_metadata_structure():
    """메타데이터 구조 검증"""
    try:
        from chromadb import PersistentClient
        client = PersistentClient(path=settings.VECTOR_DB_PATH)
        
        collection = client.get_collection("global-documents")
        sample_results = collection.peek(limit=3)
        
        logger.info("=== Vector DB Metadata Structure Verification ===")
        logger.info(f"Total documents in collection: {collection.count()}")
        
        if sample_results['metadatas']:
            for i, metadata in enumerate(sample_results['metadatas'][:3]):
                logger.info(f"Sample document {i+1} metadata: {metadata}")
        else:
            logger.warning("No metadata found in collection")
            
    except Exception as e:
        logger.error(f"Error verifying metadata structure: {e}")

# FastAPI 앱에서 사용할 수 있는 startup 이벤트 핸들러
async def startup_event():
    """애플리케이션 시작 시 실행"""
    check_and_init_vector_db()

if __name__ == "__main__":
    logger.info("=== Vector Database Initialization ===")
    logger.info("New metadata structure:")
    logger.info("- doc_id: Document unique identifier")
    logger.info("- chunk_id: Chunk unique identifier") 
    logger.info("- persona: Persona type for the document")
    logger.info("- category: Document category")
    logger.info("- topic: Document topic/subject")
    logger.info("- source: Source filename")
    logger.info("- last_updated: Last update timestamp")
    logger.info("==========================================")
    
    initialize_vector_database()
    
    # 메타데이터 구조 검증
    verify_metadata_structure()
