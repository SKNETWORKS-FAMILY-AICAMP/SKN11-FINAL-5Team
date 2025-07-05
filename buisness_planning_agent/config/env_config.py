import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT"))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ✅ OpenAI
llm_openai = ChatOpenAI(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY)

# ✅ Gemini (Google Generative AI)
llm_gemini = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=GOOGLE_API_KEY)



CHROMA_DIR = os.getenv("CHROMA_DIR", "./vector_db")

# ✅ 임베딩 모델 초기화
embedding = OpenAIEmbeddings(
    model="text-embedding-3-small",
    dimensions=1536,
    openai_api_key=OPENAI_API_KEY
)

# ✅ 벡터스토어 불러오기
vectorstore = Chroma(
    collection_name="global-documents",
    persist_directory=CHROMA_DIR,
    embedding_function=embedding
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

