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
    """벡터 데이터베이스 초기화"""
    
    # PDF 디렉토리 경로 설정
    pdf_dir = "/Users/comet39/SKN_PJT/SKN11-3rd-6Team/backend_v1/data/pdfs"  # PDF 파일들이 있는 디렉토리 경로
    
    # 디렉토리 확인
    if not os.path.exists(pdf_dir):
        logger.error(f"PDF directory not found: {pdf_dir}")
        logger.info("Creating directory and adding sample message...")
        os.makedirs(pdf_dir, exist_ok=True)
        
        # 샘플 파일 경로 출력
        logger.info(f"Please add PDF files to: {os.path.abspath(pdf_dir)}")
        logger.info("Expected file format: country_doctype.pdf")
        logger.info("Example: china_visa_info.pdf")
        return
    
    # PDF 파일 목록 확인
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {pdf_dir}")
        logger.info("Please add PDF files with format: country_doctype.pdf")
        logger.info("Supported doctypes: visa_info, insurance_info, immigration_regulations_info, immigration_safety_info")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    logger.info(f"Files: {pdf_files}")
    
    # RAG 인스턴스 생성
    rag = RAG()
    
    # 벡터 DB 경로 생성
    os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
    
    # PDF 파일들 처리
    logger.info("Starting PDF processing...")
    rag.process_pdf_directory(pdf_dir)
    
    logger.info("Vector database initialization completed")

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
        except:
            logger.info("Collection not found. Initializing...")
            initialize_vector_database()
            
    except Exception as e:
        logger.error(f"Error checking vector DB: {e}")

# FastAPI 앱에서 사용할 수 있는 startup 이벤트 핸들러
async def startup_event():
    """애플리케이션 시작 시 실행"""
    check_and_init_vector_db()

if __name__ == "__main__":
    initialize_vector_database()