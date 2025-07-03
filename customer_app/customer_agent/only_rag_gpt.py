from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from config.env_config import llm, vectorstore

def build_simple_prompt():
    system_template = "너는 1인 창업 전문 컨설턴트야. 제공된 문서를 참고해 질문에 답변해줘."
    human_template = """Context: {context}

    Question: {question}
    Answer:"""
    
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template)
    ])

def run_rag_only(user_input: str):
    prompt = build_simple_prompt()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )

    # Pass as dictionary with 'query' key
    result = qa_chain.invoke({"query": user_input})
    
    sources = "\n\n".join(
        [f"# 문서\n{doc.page_content}\n" 
         for doc in result.get('source_documents', [])]
    )
    return {
        "answer": result['result'],
        "sources": sources
    }

# 직접 실행
if __name__ == "__main__":
    input_question = "고객 생일을 받아서 쿠폰 보내고 싶은데, 이건 민감정보 처리에 해당돼? 별도로 동의를 받아야 해?"#"우리 쇼핑몰에 가입은 했지만 30일 동안 구매 이력이 없는 고객 데이터를 따로 관리하고 싶은데, CRM에서는 이걸 어떻게 분류해?"#"인스타그램에 자주 태그해주는 팬들이 있어. 이런 고객들과 장기적인 관계를 만들려면 어떻게해?"#"첫 구매만 하고 재구매가 없는 고객이랑, 자주 구매하는 고객을 다르게 타겟팅하고 싶은데, 어떻게 나눠서 전략 짜면 좋을까?"#"최근 고객 리뷰에 ‘포장이 부실하다’는 말이 자주 보여. 이걸 어떻게 분석하고 개선하면 좋을까?"#"쇼핑몰 운영중인데 첫 구매만 하고 떠난 고객이 많아. 어떻게 다시 유도할 수 있을까?"#"배송이 너무 늦어서 별점1개가 달렸어. 어떻게 답변 달아야 할까?"
    result = run_rag_only(input_question)
    
    print("답변:")
    print(result['answer'])
    print("\n참고 문서:")
    print(result['sources'])
