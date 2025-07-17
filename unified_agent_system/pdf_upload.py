from fastapi import FastAPI, APIRouter, UploadFile, File, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
import boto3
import shutil
import tarfile
from datetime import datetime
from tempfile import TemporaryDirectory
import logging
from uuid import uuid4

from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from chromadb.config import Settings
from langchain.chains import RetrievalQA
from langchain.retrievers import EnsembleRetriever
from langchain.llms import OpenAI

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="PDF ChromaDB API",
    description="PDF 업로드 및 임베딩 검색 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 생성
router = APIRouter(prefix="/api/v1", tags=["PDF Processing"])

# 설정
S3_BUCKET = os.getenv("S3_BUCKET", "your-s3-bucket")
PDF_PREFIX = "pdfs"
VECTOR_PREFIX = "vectors"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

# AWS S3 클라이언트
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

# OpenAI 임베딩
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY
)

# OpenAI LLM
llm = OpenAI(
    api_key=OPENAI_API_KEY,
    temperature=0.7
)

# Pydantic 모델
class UploadResponse(BaseModel):
    success: bool
    message: str
    pdf_s3_key: Optional[str] = None
    vector_s3_key: Optional[str] = None
    processing_time: Optional[float] = None

class QueryRequest(BaseModel):
    user_id: int
    query: str
    max_results: Optional[int] = 5

class QueryResponse(BaseModel):
    success: bool
    result: Optional[str] = None
    sources: Optional[list] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

# 유틸리티 함수들
def save_pdf_to_s3(user_id: int, file: UploadFile) -> str:
    """PDF 파일을 S3에 저장"""
    try:
        s3_key = f"{PDF_PREFIX}/{user_id}/{file.filename}"
        file.file.seek(0)  # 파일 포인터를 처음으로 되돌림
        s3.upload_fileobj(file.file, S3_BUCKET, s3_key)
        logger.info(f"PDF 업로드 성공: {s3_key}")
        return s3_key
    except Exception as e:
        logger.error(f"PDF S3 업로드 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF 업로드 실패: {str(e)}")

def extract_and_save_vectors(pdf_path: str, user_id: int) -> str:
    """PDF에서 텍스트 추출 후 벡터 저장"""
    try:
        loader = PyPDFLoader(pdf_path)
        pages = loader.load_and_split()
        
        if not pages:
            raise ValueError("PDF에서 텍스트를 추출할 수 없습니다.")
        
        persist_dir = f"/tmp/chroma_{user_id}_{uuid4().hex[:8]}"
        vectorstore = Chroma.from_documents(
            documents=pages,
            embedding=embeddings,
            persist_directory=persist_dir,
            client_settings=Settings(anonymized_telemetry=False)
        )
        vectorstore.persist()
        logger.info(f"벡터 저장 완료: {persist_dir}")
        return persist_dir
    except Exception as e:
        logger.error(f"벡터 추출 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"벡터 추출 실패: {str(e)}")

def upload_chroma_to_s3(local_dir: str, user_id: int) -> str:
    """Chroma 디렉토리를 압축하여 S3에 업로드"""
    try:
        archive_path = f"/tmp/chroma_{user_id}_{uuid4().hex[:8]}.tar.gz"
        s3_key = f"{VECTOR_PREFIX}/{user_id}/chroma.tar.gz"
        
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(local_dir, arcname=os.path.basename(local_dir))
        
        s3.upload_file(archive_path, S3_BUCKET, s3_key)
        
        # 임시 파일 정리
        os.remove(archive_path)
        shutil.rmtree(local_dir)
        
        logger.info(f"벡터 DB S3 업로드 완료: {s3_key}")
        return s3_key
    except Exception as e:
        logger.error(f"벡터 DB S3 업로드 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"벡터 DB 업로드 실패: {str(e)}")

def download_and_restore_chroma(user_id: int) -> Chroma:
    """S3에서 Chroma DB 다운로드 및 복원"""
    local_archive = f"/tmp/chroma_{user_id}_{uuid4().hex[:8]}.tar.gz"
    local_dir = f"/tmp/chroma_{user_id}_{uuid4().hex[:8]}"
    s3_key = f"{VECTOR_PREFIX}/{user_id}/chroma.tar.gz"
    
    try:
        s3.download_file(S3_BUCKET, s3_key, local_archive)
        
        with tarfile.open(local_archive, "r:gz") as tar:
            tar.extractall(path=os.path.dirname(local_dir))
        
        os.remove(local_archive)
        
        vectorstore = Chroma(
            embedding_function=embeddings,
            persist_directory=local_dir,
            client_settings=Settings(anonymized_telemetry=False)
        )
        
        logger.info(f"벡터 DB 복원 완료: {local_dir}")
        return vectorstore
    except Exception as e:
        logger.error(f"벡터 DB 다운로드 실패: {str(e)}")
        raise HTTPException(status_code=404, detail=f"벡터 DB를 찾을 수 없습니다: {str(e)}")

def download_base_chroma() -> Chroma:
    """Base Chroma DB 다운로드"""
    base_user_id = 0
    return download_and_restore_chroma(base_user_id)

def cleanup_temp_files(user_id: int):
    """임시 파일 정리"""
    import glob
    temp_files = glob.glob(f"/tmp/chroma_{user_id}_*")
    for temp_file in temp_files:
        try:
            if os.path.isfile(temp_file):
                os.remove(temp_file)
            elif os.path.isdir(temp_file):
                shutil.rmtree(temp_file)
        except Exception as e:
            logger.warning(f"임시 파일 정리 실패: {temp_file}, {str(e)}")

# API 엔드포인트들
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """서버 상태 확인"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    user_id: int = Query(..., description="사용자 ID"),
    file: UploadFile = File(..., description="업로드할 PDF 파일")
):
    """PDF 업로드 및 임베딩 처리"""
    start_time = datetime.now()
    
    # 파일 검증
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")
    
    if file.size > 50 * 1024 * 1024:  # 50MB 제한
        raise HTTPException(status_code=400, detail="파일 크기는 50MB 이하여야 합니다.")
    
    try:
        with TemporaryDirectory() as tmpdir:
            # 1. 임시 파일로 저장
            local_pdf_path = os.path.join(tmpdir, file.filename)
            with open(local_pdf_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # 2. S3에 PDF 저장
            pdf_s3_key = save_pdf_to_s3(user_id, file)
            
            # 3. 벡터 추출 및 저장
            vector_dir = extract_and_save_vectors(local_pdf_path, user_id)
            
            # 4. Chroma 디렉토리 압축 후 S3에 저장
            vector_s3_key = upload_chroma_to_s3(vector_dir, user_id)
        
        # 5. 백그라운드에서 임시 파일 정리
        background_tasks.add_task(cleanup_temp_files, user_id)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return UploadResponse(
            success=True,
            message="PDF 업로드 및 임베딩 처리 완료",
            pdf_s3_key=pdf_s3_key,
            vector_s3_key=vector_s3_key,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"PDF 업로드 처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")

@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """문서 검색 쿼리 (RAG 챗봇용)"""
    start_time = datetime.now()
    
    try:
        # Base ChromaDB와 사용자 ChromaDB 로드
        base_store = download_base_chroma()
        
        # 사용자 ChromaDB가 있는지 확인
        try:
            user_store = download_and_restore_chroma(request.user_id)
            has_user_data = True
        except HTTPException:
            user_store = None
            has_user_data = False
            logger.info(f"사용자 {request.user_id}의 ChromaDB가 없습니다. Base만 사용합니다.")
        
        # Retriever 설정
        if has_user_data:
            # 사용자 데이터가 있으면 EnsembleRetriever 사용
            retriever = EnsembleRetriever(
                retrievers=[
                    user_store.as_retriever(search_kwargs={"k": request.max_results}),
                    base_store.as_retriever(search_kwargs={"k": request.max_results})
                ],
                weights=[0.8, 0.2]  # 사용자 데이터에 더 높은 가중치
            )
        else:
            # 사용자 데이터가 없으면 Base만 사용
            retriever = base_store.as_retriever(search_kwargs={"k": request.max_results})
        
        # RetrievalQA 체인 생성
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        
        # 쿼리 실행
        result = qa_chain({"query": request.query})
        
        # 소스 문서 정보 추출 (출처 구분)
        sources = []
        if "source_documents" in result:
            for doc in result["source_documents"]:
                source_type = "user" if has_user_data and "user" in doc.metadata.get("source", "").lower() else "base"
                sources.append({
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "source": doc.metadata.get("source", "Unknown"),
                    "page": doc.metadata.get("page", 0),
                    "type": source_type,  # 출처 구분
                    "relevance_score": getattr(doc, 'relevance_score', None)
                })
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResponse(
            success=True,
            result=result["result"],
            sources=sources,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"쿼리 처리 실패: {str(e)}")
        return QueryResponse(
            success=False,
            error=f"쿼리 처리 중 오류 발생: {str(e)}"
        )

@router.get("/query", response_model=QueryResponse)
async def query_documents_get(
    user_id: int = Query(..., description="사용자 ID"),
    query: str = Query(..., description="검색 쿼리"),
    max_results: int = Query(5, description="최대 결과 수")
):
    """GET 방식 문서 검색 쿼리"""
    request = QueryRequest(
        user_id=user_id,
        query=query,
        max_results=max_results
    )
    return await query_documents(request)

# RAG 챗봇용 추가 엔드포인트
@router.post("/chat", response_model=QueryResponse)
async def chat_with_context(request: QueryRequest):
    """RAG 기반 챗봇 대화 (컨텍스트 기반 답변)"""
    start_time = datetime.now()
    
    try:
        # Base ChromaDB와 사용자 ChromaDB 로드
        base_store = download_base_chroma()
        
        # 사용자 ChromaDB가 있는지 확인
        try:
            user_store = download_and_restore_chroma(request.user_id)
            has_user_data = True
        except HTTPException:
            user_store = None
            has_user_data = False
        
        # 관련 문서 검색
        if has_user_data:
            # 사용자 문서에서 먼저 검색
            user_docs = user_store.similarity_search(request.query, k=3)
            base_docs = base_store.similarity_search(request.query, k=2)
            all_docs = user_docs + base_docs
        else:
            # Base 문서만 검색
            all_docs = base_store.similarity_search(request.query, k=request.max_results)
        
        # 컨텍스트 구성
        context = "\n\n".join([
            f"문서 {i+1}: {doc.page_content}" 
            for i, doc in enumerate(all_docs)
        ])
        
        # 챗봇용 프롬프트 구성
        chat_prompt = f"""당신은 도움이 되는 AI 어시스턴트입니다. 
다음 문서들을 참고하여 사용자의 질문에 답변해주세요.

참고 문서:
{context}

사용자 질문: {request.query}

답변 시 주의사항:
- 참고 문서의 정보를 바탕으로 정확하고 도움이 되는 답변을 제공하세요
- 문서에 없는 정보는 추측하지 마세요
- 사용자에게 친근하고 이해하기 쉽게 설명하세요
"""
        
        # LLM으로 답변 생성
        response = llm(chat_prompt)
        
        # 소스 문서 정보
        sources = []
        for i, doc in enumerate(all_docs):
            source_type = "user" if has_user_data and i < 3 else "base"
            sources.append({
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "source": doc.metadata.get("source", "Unknown"),
                "page": doc.metadata.get("page", 0),
                "type": source_type
            })
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResponse(
            success=True,
            result=response,
            sources=sources,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"챗봇 대화 실패: {str(e)}")
        return QueryResponse(
            success=False,
            error=f"챗봇 처리 중 오류 발생: {str(e)}"
        )

@router.get("/user/{user_id}/status")
async def get_user_status(user_id: int):
    """사용자 데이터 상태 확인"""
    try:
        # 사용자 PDF 파일 확인
        pdf_objects = []
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=f"{PDF_PREFIX}/{user_id}/"):
            if 'Contents' in page:
                for obj in page['Contents']:
                    pdf_objects.append({
                        "filename": obj['Key'].split('/')[-1],
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat()
                    })
        
        # 벡터 DB 확인
        vector_key = f"{VECTOR_PREFIX}/{user_id}/chroma.tar.gz"
        has_vector_db = False
        vector_info = None
        
        try:
            response = s3.head_object(Bucket=S3_BUCKET, Key=vector_key)
            has_vector_db = True
            vector_info = {
                "size": response['ContentLength'],
                "last_modified": response['LastModified'].isoformat()
            }
        except:
            pass
        
        return {
            "user_id": user_id,
            "has_vector_db": has_vector_db,
            "vector_info": vector_info,
            "pdf_count": len(pdf_objects),
            "pdf_files": pdf_objects
        }
        
    except Exception as e:
        logger.error(f"사용자 상태 확인 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"상태 확인 중 오류 발생: {str(e)}")

@router.delete("/user/{user_id}")
async def delete_user_data(user_id: int):
    """사용자 데이터 삭제"""
    try:
        # S3에서 사용자 데이터 삭제
        pdf_prefix = f"{PDF_PREFIX}/{user_id}/"
        vector_key = f"{VECTOR_PREFIX}/{user_id}/chroma.tar.gz"
        
        # PDF 파일들 삭제
        objects_to_delete = []
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=pdf_prefix):
            if 'Contents' in page:
                for obj in page['Contents']:
                    objects_to_delete.append({'Key': obj['Key']})
        
        # 벡터 DB 삭제
        try:
            s3.head_object(Bucket=S3_BUCKET, Key=vector_key)
            objects_to_delete.append({'Key': vector_key})
        except:
            pass
        
        # 일괄 삭제
        if objects_to_delete:
            s3.delete_objects(
                Bucket=S3_BUCKET,
                Delete={'Objects': objects_to_delete}
            )
        
        return {"success": True, "message": f"사용자 {user_id}의 데이터가 삭제되었습니다."}
        
    except Exception as e:
        logger.error(f"사용자 데이터 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"삭제 중 오류 발생: {str(e)}")


# 메인 앱에 라우터 추가
app.include_router(router)

# 기본 엔드포인트
@app.get("/")
async def root():
    return {
        "message": "PDF ChromaDB API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

# 에러 핸들러
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"예상치 못한 오류: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("pdf_upload:app", host="127.0.0.1", port=8080, reload=True)
