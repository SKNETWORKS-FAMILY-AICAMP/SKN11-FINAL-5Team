import os
import fitz
import json
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

# === 환경 변수 로드 ===
load_dotenv()

# === Qdrant 설정 ===
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "docs")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=OPENAI_API_KEY)
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# === Qdrant 컬렉션 초기화 ===
def init_qdrant():
    print("[QDRANT] init_qdrant started")
    try:
        qdrant.get_collection(collection_name=COLLECTION_NAME)
        print(f"[QDRANT] Collection '{COLLECTION_NAME}' already exists.")
    except Exception:
        print(f"[QDRANT] Collection '{COLLECTION_NAME}' not found. Creating...")
        qdrant.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
        )
        print(f"[QDRANT] Collection '{COLLECTION_NAME}' created.")

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
def insert_texts(texts, metadata, batch_size=500):
    print(f"[QDRANT] Inserting {len(texts)} chunks with metadata: {metadata}")
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
        if len(points) >= batch_size:
            qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
            points = []
    if points:
        qdrant.upsert(collection_name=COLLECTION_NAME, points=points)

# === PDF & JSON 텍스트 추출 ===
def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text.strip()

def extract_text_from_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return json.dumps(data, ensure_ascii=False)

# === 초기 데이터 처리 ===
def process_initial_data(pdf_folder="../data/pdf", json_folder="../data/json"):
    print("[INIT] process_initial_data started")
    init_qdrant()

    for pdf_file in os.listdir(pdf_folder):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder, pdf_file)
            text = extract_text_from_pdf(pdf_path)
            chunks = chunk_text(text)
            insert_texts(chunks, {"data_scope": "global", "user_id": None, "source_file": pdf_file})

    for json_file in os.listdir(json_folder):
        if json_file.endswith(".json"):
            json_path = os.path.join(json_folder, json_file)
            text = extract_text_from_json(json_path)
            chunks = chunk_text(text)
            insert_texts(chunks, {"data_scope": "global", "user_id": None, "source_file": json_file})

if __name__ == "__main__":
    process_initial_data()
