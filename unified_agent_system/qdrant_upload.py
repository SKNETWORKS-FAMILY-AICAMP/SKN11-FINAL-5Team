import os
import uuid
import fitz
import boto3
from fastapi import FastAPI, UploadFile, Form, APIRouter
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from qdrant_init import chunk_text, insert_texts
import tempfile
import urllib
from fastapi.responses import FileResponse

# === 환경 변수 로드 ===
load_dotenv()

# === AWS S3 설정 ===
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_S3_REGION")
BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# === Qdrant 설정 ===
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "docs")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=OPENAI_API_KEY)
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def get_safe_filename(original_filename: str) -> str:
    # 파일 확장자 추출
    ext = os.path.splitext(original_filename)[1]
    safe_name = f"{uuid.uuid4()}{ext}"
    return safe_name

def get_safe_s3_key(user_id: int, original_filename: str) -> str:
    safe_name = get_safe_filename(original_filename)
    # URL 인코딩
    return urllib.parse.quote(f"uploads/user_{user_id}/{safe_name}")

# === S3 업로드 ===
def upload_to_s3(file_path, s3_key):
    s3.upload_file(file_path, BUCKET_NAME, s3_key)
    return f"s3://{BUCKET_NAME}/{s3_key}"

# === PDF 텍스트 추출 ===
def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text.strip()

# === S3 파일 삭제 ===
def delete_from_s3(s3_key):
    s3.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
    return f"s3://{BUCKET_NAME}/{s3_key} deleted"

# === Qdrant 문서 삭제 ===
def delete_from_qdrant(user_id: int, s3_key: str):
    filter_condition = models.Filter(
        must=[
            models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
            models.FieldCondition(key="source_file", match=models.MatchValue(value=s3_key))
        ]
    )
    qdrant.delete(collection_name=COLLECTION_NAME, points_selector=models.PointIdsList([]), filter=filter_condition)
    return f"Qdrant entries for {s3_key} deleted"

# === FastAPI 앱 및 라우터 ===
app = FastAPI()
router = APIRouter()

@router.post("/upload")
async def upload_file(user_id: int = Form(...), file: UploadFile = None):
    # tmp_path = f"/tmp/{uuid.uuid4()}_{safe_filename}"  # For EC2
    
    safe_filename = get_safe_filename(file.filename)
    
    tmp_dir = tempfile.gettempdir()
    os.makedirs(tmp_dir, exist_ok=True)

    tmp_path = os.path.join(tmp_dir, f"{uuid.uuid4()}_{safe_filename}")
    
    # 파일 저장
    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    # S3 경로
    s3_key = f"uploads/user_{user_id}/{safe_filename}"
    upload_to_s3(tmp_path, s3_key)

    text = extract_text_from_pdf(tmp_path)
    chunks = chunk_text(text)
    insert_texts(chunks, {"data_scope": "user", "user_id": user_id, "source_file": s3_key})

    # 임시 파일 삭제
    os.remove(tmp_path)

    return {"message": "File uploaded & indexed", "s3_key": s3_key}

@router.get("/download")
async def download_file(user_id: int, s3_key: str):
    """
    지정된 user_id의 s3_key 파일을 다운로드합니다.
    """
    # S3에서 임시 파일로 다운로드
    tmp_dir = tempfile.gettempdir()
    os.makedirs(tmp_dir, exist_ok=True)
    local_path = os.path.join(tmp_dir, os.path.basename(s3_key))

    try:
        s3.download_file(BUCKET_NAME, s3_key, local_path)
    except Exception as e:
        return {"error": f"파일 다운로드 실패: {e}"}

    # FileResponse로 반환 (브라우저 다운로드)
    return FileResponse(local_path, filename=os.path.basename(s3_key))

@router.get("/search")
async def search(query: str, user_id: int = None):
    vector = embeddings.embed_query(query)
    filters = [models.FieldCondition(key="data_scope", match=models.MatchValue(value="global"))]
    if user_id:
        filters.append(models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)))

    results = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        limit=5,
        query_filter=models.Filter(should=filters)
    )
    return [
        {"score": r.score, "text": r.payload.get("text"), "source": r.payload.get("source_file")}
        for r in results
    ]

def delete_from_qdrant(user_id: int, s3_key: str):
    # 1. 해당 데이터 검색해서 ID 수집
    points = qdrant.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
                models.FieldCondition(key="source_file", match=models.MatchValue(value=s3_key))
            ]
        ),
        limit=10000
    )[0]
    
    point_ids = [p.id for p in points]
    if not point_ids:
        return f"No points found for {s3_key}"
    
    # 2. 포인트 삭제
    qdrant.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.PointIdsList(points=point_ids)
    )
    return f"Deleted {len(point_ids)} points for {s3_key}"

app.include_router(router)
