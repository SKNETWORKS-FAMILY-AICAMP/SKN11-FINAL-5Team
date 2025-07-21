import os
import sys
import uuid
import json
import fitz
import boto3
from fastapi import FastAPI, UploadFile, Form, APIRouter
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

# === 환경 변수 로드 ===
load_dotenv()

# 공통 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

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

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY
)
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# === Qdrant 컬렉션 초기화 ===
def init_qdrant():
    try:
        qdrant.get_collection(collection_name=COLLECTION_NAME)
        print(f"Collection '{COLLECTION_NAME}' already exists.")
    except:
        qdrant.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
        )
        print(f"Collection '{COLLECTION_NAME}' created.")

# === 텍스트 분할 ===
def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
        if start >= len(text):
            break
    return chunks

# === Qdrant 저장 ===
def insert_texts(texts, metadata):
    points = []
    for i, text in enumerate(texts):
        vector = embeddings.embed_query(text)
        points.append(
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={**metadata, "chunk_index": i, "text": text}
            )
        )
    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)

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

# === JSON 텍스트 추출 ===
def extract_text_from_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return json.dumps(data, ensure_ascii=False)

# === 공통 데이터 초기화 ===
def process_initial_data(pdf_folder="/app/data/pdf", json_folder="/app/data/json"):
    init_qdrant()
    # PDF 처리
    for pdf_file in os.listdir(pdf_folder):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder, pdf_file)
            text = extract_text_from_pdf(pdf_path)
            chunks = chunk_text(text)
            insert_texts(chunks, {"data_scope": "global", "user_id": None, "source_file": pdf_file})
    # JSON 처리
    for json_file in os.listdir(json_folder):
        if json_file.endswith(".json"):
            json_path = os.path.join(json_folder, json_file)
            text = extract_text_from_json(json_path)
            chunks = chunk_text(text)
            insert_texts(chunks, {"data_scope": "global", "user_id": None, "source_file": json_file})

# === FastAPI 서버 ===
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_qdrant()  # Qdrant 초기화
    yield

app = FastAPI(lifespan=lifespan)
router = APIRouter()

@router.post("/upload")
async def upload_file(user_id: int = Form(...), file: UploadFile = None):
    tmp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    s3_key = f"uploads/user_{user_id}/{file.filename}"
    upload_to_s3(tmp_path, s3_key)

    text = extract_text_from_pdf(tmp_path)
    chunks = chunk_text(text)
    insert_texts(chunks, {"data_scope": "user", "user_id": user_id, "source_file": s3_key})
    return {"message": "File uploaded & indexed", "s3_key": s3_key}

@router.get("/search")
def search(query: str, user_id: int = None):
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
    return [{"score": r.score, "text": r.payload.get("text"), "source": r.payload.get("source_file")} for r in results]

@router.get("/status")
def qdrant_status():
    try:
        # Qdrant 서버 상태 확인을 get_collections()로 대신함
        collections = qdrant.get_collections()
        return {
            "qdrant_status": "ok",
            "collections": collections.model_dump().get("collections", [])
        }
    except Exception as e:
        return {"qdrant_status": "error", "message": str(e)}

if __name__ == "__main__":
    # 최초 실행 시 공통 데이터 삽입
    process_initial_data()
    import uvicorn
    uvicorn.run("qdrant:app", host="127.0.0.1", port=8080, reload=True)
