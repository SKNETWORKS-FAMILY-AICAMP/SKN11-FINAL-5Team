from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import RetrievalQA
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Body
from pydantic import BaseModel
from langchain_core.output_parsers import StrOutputParser

from config.prompts_config import PROMPT_META
from fastapi.responses import FileResponse

# 공통 모듈 사용
from shared_modules.env_config import get_config
from shared_modules.llm_utils import get_llm_manager, get_llm
from shared_modules.vector_utils import get_vector_manager, get_vectorstore, get_retriever
from shared_modules.utils import load_prompt_from_file
from shared_modules.queries import get_templates_by_type

# 기존 모듈 (공통 모듈에 없는 함수들)
try:
    from MYSQL import queries as db
except ImportError:
    # MYSQL 모듈이 없으면 대체 함수 사용
    class MockDB:
        @staticmethod
        def get_last_messages(conversation_id, limit=5):
            return []
        
        @staticmethod  
        def insert_conversation(user_id):
            return 1  # 목 conversation_id
            
        @staticmethod
        def insert_message(conversation_id, sender_type, content, agent_type=None):
            return True
    
    db = MockDB()

from typing import Optional
from pydantic import BaseModel

from config.persona_config import get_persona_by_type, get_specialized_config

from datetime import datetime as dt



# ✅ 환경설정 로드 (공통 모듈 사용)
config = get_config()

# ✅ 벡터 스토어 매니저 초기화 (공통 모듈 사용)
vector_manager = get_vector_manager(config)
vectorstore = get_vectorstore("global-documents")

# ✅ LLM 매니저 초기화 (공통 모듈 사용)
llm_manager = get_llm_manager(config)

# ✅ LLM 자동 선택 함수 (공통 모듈 사용)
def get_llm_auto():
    """로드 밸런싱된 LLM 반환"""
    llm = llm_manager.get_llm(load_balance=True)
    status = llm_manager.get_status()
    print(f"🔄 현재 LLM: {status.get('current_provider', 'unknown')} (호출 수: {status.get('call_count', 0)})")
    return llm

# ✅ 기본 retriever 초기화 (공통 모듈 사용)
base_retriever = get_retriever("global-documents", k=5) if vectorstore else None

# ✅ 기본 LLM 초기화 (공통 모듈 사용)
llm = get_llm()

# ✅ FastAPI 초기화
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 기본 퍼소나
persona = "e-commerce"

# ✅ 프롬프트 파일 로드 함수 (공통 모듈 사용)
def load_prompt_text(file_path: str) -> str:
    abs_path = os.path.join(os.path.dirname(__file__), file_path)
    return load_prompt_from_file(abs_path)

# ✅ 마케팅 토픽 분류 프롬프트
TOPIC_CLASSIFY_SYSTEM_PROMPT = """
너는 고객 질문을 분석해서 관련된 마케팅 토픽을 모두 골라주는 역할이야.

아래의 토픽 중에서 질문과 관련된 키워드를 복수 개까지 골라줘.
콤마(,)로 구분된 키만 출력하고, 설명은 하지마.

가능한 토픽:
1. marketing_fundamentals – 마케팅 기초 이론
2. social_media_marketing – SNS 전반 전략
3. email_marketing – 이메일, 뉴스레터
4. content_marketing – 콘텐츠 전략, 포맷 기획
5. personal_branding – 퍼스널 및 브랜드 포지셔닝
6. digital_advertising – 페이드 미디어, 광고 채널
7. seo_optimization – 검색 노출 최적화
8. conversion_optimization – 전환 퍼널, A/B 테스트
9. influencer_marketing – 협업, 제휴 마케팅
10. local_marketing – 지역 기반 마케팅
11. marketing_automation – 자동화, 캠페인 설정
12. viral_marketing – 바이럴, 입소문 전략
13. blog_marketing – 블로그 기반 콘텐츠 운영
14. marketing_metrics – ROAS, CAC 등 성과 지표

출력 예시: marketing_fundamentals, social_media_marketing
"""

# ✅ 벡터스토어 상태 확인 함수 (공통 모듈 사용)
def check_vectorstore_status():
    """벡터스토어의 상태를 확인하는 함수"""
    try:
        if not vectorstore:
            print("❌ 벡터스토어를 사용할 수 없습니다")
            return False
            
        # 전체 문서 수 확인
        total_docs = vectorstore._collection.count()
        print(f"📊 벡터스토어 총 문서 수: {total_docs}")
        
        # 샘플 문서 확인
        sample_docs = vector_manager.search_documents("마케팅", k=3)
        print(f"📋 샘플 검색 결과: {len(sample_docs)}개")
        
        for i, doc in enumerate(sample_docs):
            print(f"  {i+1}. 메타데이터: {doc.metadata}")
            print(f"     내용 미리보기: {doc.page_content[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ 벡터스토어 확인 실패: {e}")
        return False

# ✅ 관련 토픽 추론 함수
def classify_topics(user_input: str) -> list:
    classify_prompt = ChatPromptTemplate.from_messages([
        ("system", TOPIC_CLASSIFY_SYSTEM_PROMPT),
        ("human", f"사용자 질문: {user_input}")
    ])
    chain = classify_prompt | llm | StrOutputParser()
    result = chain.invoke({"input": user_input}).strip()
    topics = [t.strip() for t in result.split(",") if t.strip()]
    
    print(f"🏷️ 분류된 토픽: {topics}")
    return topics

# ✅ 스마트 retriever 생성 함수 (공통 모듈 사용)
def create_smart_retriever(user_input: str, topics: list = None):
    """토픽 기반으로 스마트하게 문서를 검색하는 retriever 생성"""
    
    if not vectorstore:
        print("❌ 벡터스토어를 사용할 수 없습니다")
        return base_retriever
    
    # 1. 토픽 기반 필터 시도
    if topics:
        try:
            # 실제 메타데이터 구조에 맞게 수정 필요
            topic_filter = {"topic": {"$in": topics}}
            
            topic_retriever = get_retriever(
                "global-documents", 
                k=5, 
                search_kwargs={"filter": topic_filter}
            )
            
            # 필터링된 검색 테스트
            test_docs = vector_manager.search_documents(
                user_input, 
                "global-documents", 
                k=5, 
                filter_dict=topic_filter
            )
            if test_docs:
                print(f"✅ 토픽 필터링 검색 성공: {len(test_docs)}개 문서")
                return topic_retriever
            else:
                print("⚠️ 토픽 필터링 결과 없음, 일반 검색으로 전환")
        except Exception as e:
            print(f"⚠️ 토픽 필터링 실패: {e}, 일반 검색으로 전환")
    
    # 2. 일반 검색으로 폴백
    try:
        general_retriever = get_retriever(
            "global-documents",
            k=8,
            search_kwargs={"fetch_k": 20}
        )
        
        test_docs = vector_manager.search_documents(user_input, "global-documents", k=8)
        print(f"✅ 일반 검색 성공: {len(test_docs)}개 문서")
        return general_retriever
        
    except Exception as e:
        print(f"❌ 검색 완전 실패: {e}")
        return base_retriever
    
# ✅ 이전 메시지 불러오기 함수 (공통 모듈 사용)
def get_history_messages(conversation_id: int) -> list[str]:
    """이전 대화 기록을 불러온다 (최신 순 정렬, 최근 N개만)"""
    try:
        history = db.get_last_messages(conversation_id, limit=5)
        # (sender_type, content) 튜플 리스트 형태라고 가정
        formatted = []

        for msg in history:
            if isinstance(msg, dict):
                sender = msg.get("sender_type", "unknown")
                content = msg.get("content", "")
            else:
                # 목 데이터 처리
                continue
            prefix = "사용자:" if sender == "user" else "에이전트:"
            formatted.append(f"{prefix} {content}")
        return formatted
    except Exception as e:
        print(f"⚠️ 히스토리 로드 실패: {e}")
        return []

# ✅ 에이전트용 프롬프트 생성
def build_agent_prompt(topics: list, user_input: str, persona: str,history: list[str] = []):
    merged_prompts = []
    
    if topics:
        for topic in topics:
            if topic in PROMPT_META:
                try:
                    file_path = PROMPT_META[topic]["file"]
                    prompt_text = load_prompt_text(file_path)
                    merged_prompts.append(f"# {topic}\n{prompt_text}")
                except Exception as e:
                    print(f"⚠️ 프롬프트 파일 로드 실패 ({topic}): {e}")

    role_descriptions = [
        PROMPT_META[topic]["role"] 
        for topic in topics 
        if topic in PROMPT_META
    ]

    system_template = f"""# 역할
너는 {persona if persona != 'common' else ''} 1인 창업 전문 컨설턴트로서 {', '.join(role_descriptions) if role_descriptions else '마케팅 전반을 도와주는 전문가'}야. 
목표와 출력포맷에 맞게 응답해줘.

창업 초기 1인 셀러/크리에이터에게 현실적이고 실천 가능한 마케팅 전략을 제안하는 게 중요해.
복잡한 이론보다 사용자의 상황과 고민에 맞춘 맞춤형 조언을 주는 게 중요해.
말투는 전문가지만 친절하고, 핵심을 콕 집어서 설명해줘.

# 출력 방식
- 꼭 존댓말을 써야돼.
- 번호나 제목으로 나누지 말고, 자연스러운 문단으로 이어지는 대화처럼 설명해줘.
- "1. 슬로건 예시", "**대표 키워드**" 같은 딱딱한 제목은 쓰지 마.
- '인삿말 (상황 공감)', '마무리 응원 문장' 같은 제목이나 소제목을 절대 쓰지 마.
- 글머리 기호(-, •) 없이 부드럽게 이어서 말해줘.
- 불필요한 설명은 줄이고, 실천 가능한 전략 2~3가지만 먼저 제안해줘
- 단순 나열보다는 "왜 필요한지 + 어떻게 할지"까지 포함해서 설명해줘
- 테이블보다는 자연스러운 문단 중심, 말하듯 써줘
- 말투는 친절하고 전문가스럽되, 마치 블로그나 에세이처럼 자연스럽게 써줘.
- 응원은 문장 말미에 자연스럽게 포함시켜줘. 따로 제목 붙이지 마.
"""
    history_block = "\n".join(history) if history else "없음"



    human_template = f"""
{chr(10).join(merged_prompts) if merged_prompts else "# 일반 마케팅 컨설팅"}

# 이전 대화 기록
{history_block}

# 참고 문서
{{context}}

# 사용자 입력
{user_input}
"""

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_template),
        SystemMessagePromptTemplate.from_template(f"# 이전 대화 기록\n{history_block}"),
        HumanMessagePromptTemplate.from_template(human_template)
    ])
    return prompt

# ✅ 메인 실행 함수 (개선된 RAG)
from fastapi import HTTPException

def is_template_query(text: str) -> bool:
    keywords = ["템플릿", "문자", "메시지", "문구", "추천"]
    return any(k in text.lower() for k in keywords)

def run_customer_agent_with_rag(user_input: str, user_id: int, conversation_id: int = None, use_retriever: bool = True, persona: str = "common"):
    print(f"\n🚀 사용자 질문: {user_input}")

    # ✅ 대화 ID 처리 (공통 모듈 사용)
    if conversation_id is None:
        conversation_id = db.insert_conversation(user_id)
        if isinstance(conversation_id, dict) or conversation_id == -1:
            print(f"❌ 대화 생성 실패: {conversation_id}")
            raise HTTPException(status_code=500, detail="MySQL 연결에 실패했습니다. 대화를 생성할 수 없습니다.")
        print(f"🆕 새 대화 생성: conversation_id={conversation_id}")
    else:
        print(f"🔄 기존 대화 사용: conversation_id={conversation_id}")

    # ✅ 사용자 메시지 저장 (공통 모듈 사용)
    message_result = db.insert_message(conversation_id, sender_type="user", content=user_input)
    if not message_result:
        print("⚠️ 사용자 메시지 저장 실패 (계속 진행)")

    # ✅ 토픽 분류
    topics = classify_topics(user_input)

    # ✅ 스마트 retriever 생성
    smart_retriever = create_smart_retriever(user_input, topics)

    #히스토리 불러오기
    history = get_history_messages(conversation_id)
    print("📜 불러온 히스토리:", history)

    #prompt 생성
    prompt = build_agent_prompt(topics, user_input, persona, history)


    try:
        documents = smart_retriever.invoke(user_input)
        context = "\n\n".join([
            f"[문서 {i+1}]\n{doc.page_content}"
            for i, doc in enumerate(documents)
        ])
        print(f"📚 검색된 문서 수: {len(documents)}")

        # LLM 응답 생성
        llm_selected = get_llm_auto()
        print(f"🔁 현재 LLM: {llm_state['current']} (요청 수: {llm_state['use_count']})")

        formatted_prompt = prompt.format_messages(context=context)
        response = llm_selected.invoke(formatted_prompt)

        # ✅ 응답 메시지 저장 (공통 모듈 사용)
        save_result = db.insert_message(conversation_id, sender_type="agent", agent_type="marketing", content=response.content)
        if not save_result:
            print("⚠️ 에이전트 응답 저장 실패")

        # 출처 요약
        sources = [
            {
                "source": doc.metadata.get("source", "❌ 없음"),
                "metadata": doc.metadata,
                "length": len(doc.page_content),
                "snippet": doc.page_content[:300]
            }
            for doc in documents
        ]
        formatted_sources = "\n\n".join([
            f"# 문서 {i+1}\n출처: {src['source']}\n내용: {src['snippet']}\n"
            for i, src in enumerate(sources)
        ])

        return {
            "conversation_id": conversation_id,
            "topics": topics,
            "answer": response.content,
            "sources": formatted_sources,
            "debug_info": {
                "documents_count": len(documents),
                "context_length": len(context),
                "retriever_type": "smart_filtered" if topics else "general"
            }
        }

    except Exception as e:
        print(f"❌ RAG 실행 실패: {e}")
        formatted_prompt = prompt.format_messages(context="참고 문서를 찾을 수 없습니다.")
        response = llm.invoke(formatted_prompt)

        return {
            "topics": topics,
            "answer": f"[참고 문서 없음] {response.content}",
            "sources": "참고 문서를 찾을 수 없었습니다.",
            "debug_info": {
                "error": str(e),
                "fallback": True
            }
        }
def extract_template_keyword(text: str) -> str:
    text_lower = text.lower()
    mapping = {
        "생일": "생일/기념일", 
        "기념일": "생일/기념일",
        "축하": "생일/기념일",
        "리뷰": "리뷰 요청", 
        "후기": "리뷰 요청",
        "평가": "리뷰 요청",
        "예약": "예약",
        "설문": "설문 요청",
        "감사": "구매 후 안내", 
        "출고": "구매 후 안내", 
        "배송": "구매 후 안내",
        "발송": "구매 후 안내",
        "재구매": "재구매 유도", 
        "재방문": "재방문",
        "다시": "재구매 유도",
        "VIP": "고객 맞춤 메시지", 
        "맞춤": "고객 맞춤 메시지",
        "특별": "고객 맞춤 메시지",
        "이벤트": "이벤트 안내", 
        "할인": "이벤트 안내", 
        "프로모션": "이벤트 안내",
        "세일": "이벤트 안내"
    }
    for keyword, template_type in mapping.items():
        if keyword in text_lower:
            print(f"🎯 키워드 '{keyword}' → 템플릿 타입 '{template_type}'")
            return template_type
    
    print("🔍 특정 키워드 없음 → '전체' 템플릿")
    return "전체"

# 템플릿 감지 함수
def is_template_query(text: str) -> bool:
    template_keywords = [
        "템플릿", "문자", "메시지", "문구", "추천", "예시", 
        "샘플", "양식", "포맷", "멘트", "말", "텍스트"
    ]
    text_lower = text.lower()
    is_template = any(keyword in text_lower for keyword in template_keywords)
    
    print(f"📝 템플릿 쿼리 감지: {is_template} (입력: '{text}')")
    return is_template

# 템플릿 추천 로직
def recommend_templates_core(query: str, limit: int = 5) -> list:
    """템플릿 추천 로직 (공통 모듈 사용)"""
    try:
        keyword = extract_template_keyword(query)
        print(f"📌 추출된 템플릿 키워드: {keyword}")
        
        # DB에서 템플릿 조회 (공통 모듈 사용)
        templates = get_templates_by_type(keyword)
        print(f"📋 조회된 템플릿 수: {len(templates)}")
        
        # 템플릿이 없으면 전체 템플릿에서 검색
        if not templates and keyword != "전체":
            print("⚠️ 특정 타입 템플릿 없음, 전체에서 검색...")
            templates = get_templates_by_type("전체")
        
        # 디버깅을 위한 템플릿 정보 출력
        for i, template in enumerate(templates[:3]):  # 처음 3개만
            print(f"템플릿 {i+1}: {template.get('title', 'No Title')}")
        
        return templates[:limit]
        
    except Exception as e:
        print(f"❌ 템플릿 추천 오류: {e}")
        return []

# ✅ FastAPI 요청 모델
class AgentQueryRequest(BaseModel):
    user_id: int
    question: str
    conversation_id: Optional[int] = None  # 새 대화 시작 시 None 전달

# ✅ 디버깅용 엔드포인트 추가
@app.get("/debug/vectorstore")
def debug_vectorstore():
    """벡터스토어 상태를 확인하는 디버깅 엔드포인트"""
    try:
        status = check_vectorstore_status()
        
        # 샘플 검색 테스트
        test_query = "마케팅 전략"
        sample_docs = vectorstore.similarity_search(test_query, k=3)
        
        return {
            "status": "success" if status else "failed",
            "total_documents": vectorstore._collection.count(),
            "sample_search": {
                "query": test_query,
                "results": len(sample_docs),
                "documents": [
                    {
                        "metadata": doc.metadata,
                        "content_preview": doc.page_content[:200]
                    } for doc in sample_docs
                ]
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/debug/templates")
def debug_templates():
    """템플릿 데이터 확인용 디버깅 엔드포인트 (공통 모듈 사용)"""
    try:
        # 전체 템플릿 조회 (공통 모듈 사용)
        all_templates = get_templates_by_type("전체")
        birthday_templates = get_templates_by_type("생일/기념일")
        
        return {
            "status": "success",
            "all_templates_count": len(all_templates),
            "birthday_templates_count": len(birthday_templates),
            "sample_templates": all_templates[:3] if all_templates else [],
            "available_types": list(set([t.get('template_type', 'Unknown') for t in all_templates]))
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/debug/templates/{template_type}")
def debug_templates_by_type(template_type: str):
    """특정 타입의 템플릿 확인 (공통 모듈 사용)"""
    try:
        templates = get_templates_by_type(template_type)
        return {
            "template_type": template_type,
            "count": len(templates),
            "templates": templates
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

    

# ✅ FastAPI 라우터
@app.post("/agent/query")
def query_agent(request: AgentQueryRequest = Body(...)):
    user_input = request.question
    print(f"🚀 사용자 입력: {user_input}")

    # 템플릿 쿼리 확인
    if is_template_query(user_input):
        print("📝 템플릿 요청으로 감지됨")
        
        templates = recommend_templates_core(user_input)
        
        if templates:
            return {
                "conversation_id": request.conversation_id,
                "answer": f"'{user_input}' 관련 템플릿을 {len(templates)}개 찾았습니다! 아래에서 참고해보세요.",
                "templates": templates,
                "topics": ["template_request"],
                "sources": "",
                "debug_info": {
                    "template_match": True,
                    "template_count": len(templates),
                    "query_type": "template"
                }
            }
        else:
            return {
                "conversation_id": request.conversation_id,
                "answer": "죄송합니다. 관련 템플릿을 찾을 수 없습니다. 다른 키워드로 검색해보시거나 구체적인 상황을 말씀해주세요.",
                "templates": [],
                "topics": ["template_request"],
                "sources": "",
                "debug_info": {
                    "template_match": True,
                    "template_count": 0,
                    "query_type": "template_no_result"
                }
            }
    
    # 일반 RAG 처리
    result = run_customer_agent_with_rag(
        user_input=request.question,
        user_id=request.user_id,
        conversation_id=request.conversation_id,
        use_retriever=True,
        persona="common"  # 또는 적절한 persona
    )
    return result



@app.get("/")
def serve_front():
    return FileResponse("test.html")
