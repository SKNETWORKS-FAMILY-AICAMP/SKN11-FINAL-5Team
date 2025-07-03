from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.env_config import llm, vectorstore
from prompts_config import PROMPT_META

# ✅ 관련 토픽 추론
TOPIC_CLASSIFY_SYSTEM_PROMPT = """
너는 고객 질문을 분석해서 관련된 고객관리 토픽을 모두 골라주는 역할이야.

아래의 토픽 중에서 질문과 관련된 키워드를 **가장 밀접한 키워드 1개만** 골라줘.
키만 출력하고, 설명은 하지마. (예: customer_service)

가능한 토픽:
- customer_service – 응대, 클레임
- customer_retention – 재방문, 단골 전략
- customer_satisfaction – 만족도, 여정
- customer_feedback – 의견 수집 및 개선
- customer_segmentation – 타겟 분류, 페르소나
- community_building – 팬, 팬덤, 커뮤니티
- customer_data – 고객DB, CRM
- privacy_compliance – 개인정보, 동의 관리
"""
def classify_topics(user_input: str) -> list:
    classify_prompt = ChatPromptTemplate.from_messages([
        ("system", TOPIC_CLASSIFY_SYSTEM_PROMPT),
        ("human", f"사용자 질문: {user_input}")
    ])
    chain = classify_prompt | llm | StrOutputParser()
    result = chain.invoke({"input": user_input}).strip()
    return [t.strip() for t in result.split(",") if t.strip() in PROMPT_META]

# ✅ 간단한 프롬프트 구성
def build_simple_prompt():
    system_template = "너는 1인 창업 전문 컨설턴트야. 제공된 문서를 참고해 질문에 답변해줘."
    human_template = """Context: {context}

Question: {question}
Answer:"""
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template)
    ])

# ✅ 실행 함수: topic 기반 filter 포함
def run_topic_filtered_rag(user_input: str):
    topics = classify_topics(user_input)
    prompt = build_simple_prompt()

    if topics:
        topic_filter = {
            "$and": [
                {"category": "customer_management"},
                {"topic": {"$in": topics}}
            ]
        }
    else:
        topic_filter = {}

    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 5, "filter": topic_filter}
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )

    result = qa_chain.invoke({"query": user_input})

    sources = "\n\n".join(
        [f"# 문서\n{doc.page_content}\n" for doc in result.get('source_documents', [])]
    )

    return {
        "topics": topics,
        "answer": result['result'],
        "sources": sources
    }

# ✅ 직접 실행
if __name__ == "__main__":
    question =  "CRM 시스템에서 30일 이내 구매 이력이 없는 고객 데이터를 필터링하고 관리하려면 어떤 방식으로 데이터를 처리해야 할까?"
#"인스타그램에 자주 태그해주는 팬들이 있어. 이런 고객들과 장기적인 관계를 만들려면 어떻게해?"#"첫 구매만 하고 재구매가 없는 고객이랑, 자주 구매하는 고객을 다르게 타겟팅하고 싶은데, 어떻게 나눠서 전략 짜면 좋을까?"#"최근 고객 리뷰에 ‘포장이 부실하다’는 말이 자주 보여. 이걸 어떻게 분석하고 개선하면 좋을까?"#"쇼핑몰 운영중인데 첫 구매만 하고 떠난 고객이 많아. 어떻게 다시 유도할 수 있을까?"#"배송이 너무 늦어서 별점1개가 달렸어. 어떻게 답변 달아야 할까?"
    result = run_topic_filtered_rag(question)

    print("▶ 관련 토픽:", result['topics'])
    print("\n▶ 답변:\n", result['answer'])
    print("\n▶ 참고 문서:\n", result['sources'])
