from chromadb import PersistentClient
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from dotenv import load_dotenv
import os
from langchain_openai import OpenAIEmbeddings

# ✅ 환경 설정
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ 기존 Chroma 컬렉션이 1024차원인 경우, 일치하는 임베딩 모델 사용
# embedding = HuggingFaceEmbeddings(
#     #model_name="nlpai-lab/KURE-v1",  # 또는 당시 사용한 모델명
#     #model_name="nlpai-lab/KURE-v1",
#     model_kwargs={"device": "cpu"}
# )
embedding = OpenAIEmbeddings(
    model="text-embedding-3-small",
    dimensions=384,  # 또는 1536 (기본값)
    openai_api_key=OPENAI_API_KEY
)
print("✅ 임베딩 모델 로딩 완료")

# ✅ 기존 Chroma 컬렉션 불러오기
vectorstore = Chroma(
    collection_name="global-documents",
    persist_directory="../vector_db_text-embedding-3-small",  # 윈도우 경로 주의
    embedding_function=embedding
)
print("✅ Vectorstore 초기화 완료")

# ✅ LLM 준비
llm = ChatOpenAI(model="gpt-4.1", api_key=OPENAI_API_KEY)
print("✅ LLM 초기화 완료")

# ✅ QA 체인 구성
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    return_source_documents=True
)
print("✅ RetrievalQA 체인 생성 완료")

# ✅ 질의 실행
query = "hellolksdjaf;l jsl fㅇ니ㅏㅣㅇㄴㅁ라ㅣㅓ ;ㅓ나ㅣㅇㄻ"
print(f"📨 질의: {query}")
result = qa_chain.invoke(query)
print("✅ QA 체인 실행 완료")

# ✅ 결과 출력
print("\n:bulb: 최종 답변:\n", result['result'])

print("\n:link: 참고한 소스:")
source_docs = result.get('source_documents', [])

if not source_docs:
    print("❗ source_documents가 비어있습니다.")
else:
    for i, doc in enumerate(source_docs, 1):
        print(f"\n📄 [문서 {i}]")
        print(f" - 📌 source: {doc.metadata.get('source', '❌ 없음')}")
        print(f" - 📄 전체 메타데이터: {doc.metadata}")
        print(f" - 📚 문서 내용 길이: {len(doc.page_content)}")
        print(f" - 📑 내용 일부:\n{doc.page_content[:300]}...")

