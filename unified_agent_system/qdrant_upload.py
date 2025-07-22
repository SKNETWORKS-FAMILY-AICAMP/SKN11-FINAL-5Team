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

# === FastAPI 앱 및 라우터 ===
app = FastAPI()
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

app.include_router(router)
