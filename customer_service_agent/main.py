"""
Customer Service Agent - 공통 모듈 최대 활용 버전
모든 shared_modules 기능을 최대한 활용하여 리팩토링
"""

import sys
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

# 텔레메트리 비활성화 (ChromaDB 오류 방지)
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY'] = 'False' 
os.environ['DO_NOT_TRACK'] = '1'

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 공통 모듈에서 모든 필요한 것들 import
from shared_modules import (
    get_config, 
    get_llm_manager,
    get_vector_manager, 
    get_db_manager,
    get_session_context,
    setup_logging,
    create_conversation, 
    create_message, 
    get_conversation_by_id, 
    get_recent_messages,
    get_template_by_title,
    insert_message_raw,
    get_business_type,
    get_template,
    create_success_response,
    create_error_response,
    format_conversation_history,
    sanitize_filename,
    get_current_timestamp
)

from shared_modules.utils import get_or_create_conversation_session


from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA
from langchain_core.output_parsers import StrOutputParser

# 기존 고객 서비스 모듈들 (선택적)
try:
    from customer_agent.graph import customer_workflow, CustomerAgentState
except ImportError:
    logger = None  # 임시로 설정, 아래에서 재설정됨
    if logger: logger.warning("customer_agent 모듈을 찾을 수 없습니다.")
    customer_workflow = None
    CustomerAgentState = dict

# 로깅 설정 - 공통 모듈 활용
logger = setup_logging("customer_service", log_file="logs/customer_service.log")

# 설정 로드 - 공통 모듈 활용
config = get_config()

# LLM, Vector, DB 매니저 - 공통 모듈 활용
llm_manager = get_llm_manager()
vector_manager = get_vector_manager()
db_manager = get_db_manager()

# FastAPI 초기화
app = FastAPI(
    title="Customer Service Agent",
    description="고객 서비스 전문 AI 에이전트",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 고객 서비스 토픽 분류 프롬프트
CUSTOMER_TOPIC_CLASSIFY_PROMPT = """
너는 고객 서비스 문의를 분석해서 관련된 토픽을 골라주는 역할이야.

아래의 토픽 중에서 질문과 관련된 키워드를 **최대 2개까지** 골라줘.
콤마(,)로 구분된 키만 출력하고, 설명은 하지마.

가능한 토픽:
1. order_inquiry(주문 조회, 주문 상태)
2. payment_support(결제 문제, 환불)
3. product_support(제품 문의, 사용법)
4. delivery_tracking(배송 조회, 배송 문제)
5. return_exchange(반품, 교환)
6. account_management(계정 관리, 회원 정보)
7. technical_support(기술 지원, 오류 해결)
8. complaint_handling(불만 처리, 개선 요청)
9. general_inquiry(일반 문의, 기타)

**출력 예시**: order_inquiry, payment_support
"""

class CustomerServiceService:
    """고객 서비스 클래스 - 공통 모듈 최대 활용"""
    
    def __init__(self):
        """서비스 초기화"""
        self.llm_manager = llm_manager
        self.vector_manager = vector_manager
        self.db_manager = db_manager
        
        logger.info("CustomerServiceService 초기화 완료")
    
    async def classify_inquiry_type(self, user_input: str) -> List[str]:
        """문의 유형 분류"""
        try:
            messages = [
                {"role": "system", "content": CUSTOMER_TOPIC_CLASSIFY_PROMPT},
                {"role": "user", "content": f"고객 문의: {user_input}"}
            ]
            
            result = await self.llm_manager.generate_response(
                messages=messages,
                provider="openai"
            )
            
            topics = [t.strip() for t in result.split(",") if t.strip()]
            logger.info(f"문의 유형 분류 결과: {topics}")
            return topics
            
        except Exception as e:
            logger.error(f"문의 유형 분류 실패: {e}")
            return ["general_inquiry"]
    
    def format_message_history(self, messages: List[Any]) -> str:
        """메시지 히스토리 포맷팅"""
        history_data = []
        for msg in reversed(messages):
            history_data.append({
                "role": "user" if msg.sender_type.lower() == "user" else "assistant",
                "content": msg.content
            })
        
        return format_conversation_history(history_data, max_messages=10)
    
    async def run_customer_service_query(
        self,
        conversation_id: int,
        user_input: str,
        user_id: int,
        use_retriever: bool = True
    ) -> Dict[str, Any]:
        """고객 서비스 쿼리 실행"""
        try:
            # 1. 문의 유형 분류
            topics = await self.classify_inquiry_type(user_input)
            
            # 2. 비즈니스 타입 확인
            business_type = get_business_type(user_id) or "common"
            logger.info(f"Business type for user {user_id}: {business_type}")
            
            # 3. 대화 히스토리 조회
            with get_session_context() as db:
                messages = get_recent_messages(db, conversation_id, 10)
                history = self.format_message_history(messages)
            
            # 4. 고객 서비스 워크플로우 실행 (만약 사용 가능하다면)
            if customer_workflow:
                return await self._run_workflow(
                    user_id, conversation_id, user_input, business_type, topics, history
                )
            else:
                # 기본 RAG 실행
                return await self._run_basic_rag(
                    user_input, business_type, topics, history, use_retriever
                )
                
        except Exception as e:
            logger.error(f"고객 서비스 쿼리 실행 실패: {e}")
            return await self._generate_error_fallback(user_input)
    
    async def _run_workflow(
        self, user_id: int, conversation_id: int, user_input: str, 
        business_type: str, topics: List[str], history: str
    ) -> Dict[str, Any]:
        """워크플로우 실행"""
        try:
            # 히스토리를 LangChain 메시지로 변환
            history_messages = []
            for line in history.split('\n'):
                if line.startswith('사용자:'):
                    history_messages.append(HumanMessage(content=line[4:]))
                elif line.startswith('에이전트:'):
                    history_messages.append(AIMessage(content=line[5:]))
            
            initial_state: CustomerAgentState = {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "user_input": user_input,
                "business_type": business_type,
                "mode": "owner",
                "inquiry_type": topics[0] if topics else "general_inquiry",
                "topics": topics,
                "answer": "",
                "sources": "",
                "a2a_data": {},
                "history": history_messages
            }
            
            final_state = customer_workflow.invoke(initial_state)
            
            return {
                "topics": final_state.get("topics", topics),
                "answer": final_state["answer"],
                "sources": final_state.get("sources", ""),
                "inquiry_type": final_state.get("inquiry_type", topics[0] if topics else "general"),
                "business_type": business_type,
                "retrieval_used": True
            }
            
        except Exception as e:
            logger.error(f"워크플로우 실행 실패: {e}")
            return await self._run_basic_rag(user_input, business_type, topics, history, True)
    
    async def _run_basic_rag(
        self, user_input: str, business_type: str, topics: List[str], 
        history: str, use_retriever: bool
    ) -> Dict[str, Any]:
        """기본 RAG 실행"""
        try:
            # 프롬프트 구성
            system_context = f"""당신은 {business_type} 분야의 전문 고객 서비스 담당자입니다.
문의 유형: {', '.join(topics)}

다음 지침을 따라 답변하세요:
- 친절하고 정중한 톤으로 응답
- 구체적이고 실용적인 해결책 제시
- 필요시 추가 정보 요청
- 고객의 불편함에 공감 표현

최근 대화:
{history}

참고 문서:
{{context}}

고객 문의: "{user_input}"

위 지침에 따라 고객의 문의에 대해 도움이 되는 답변을 제공하세요."""

            # 벡터 검색 (고객 서비스 관련 문서)
            if use_retriever and topics:
                topic_filter = {
                    "$and": [
                        {"category": "customer_service"},
                        {"topic": {"$in": topics}}
                    ]
                }
                
                retriever = self.vector_manager.get_retriever(
                    collection_name="global-documents",
                    k=5,
                    search_kwargs={"filter": topic_filter}
                )
                
                if retriever:
                    from langchain.prompts import PromptTemplate
                    prompt = PromptTemplate(
                        input_variables=["context"],
                        template=system_context
                    )
                    
                    llm = self.llm_manager.get_llm(load_balance=True)
                    
                    qa_chain = RetrievalQA.from_chain_type(
                        llm=llm,
                        chain_type="stuff",
                        retriever=retriever,
                        chain_type_kwargs={"prompt": prompt},
                        return_source_documents=True
                    )
                    
                    result = qa_chain.invoke(user_input)
                    
                    sources = self._format_source_documents(result.get('source_documents', []))
                    
                    return {
                        "topics": topics,
                        "answer": result['result'],
                        "sources": sources,
                        "inquiry_type": topics[0] if topics else "general",
                        "business_type": business_type,
                        "retrieval_used": True
                    }
            
            # 검색기 없이 기본 응답
            return await self._generate_fallback_response(user_input, business_type, topics)
            
        except Exception as e:
            logger.error(f"기본 RAG 실행 실패: {e}")
            return await self._generate_fallback_response(user_input, business_type, topics)
            # return await self._generate_error_fallback(user_input)
    
    def _format_source_documents(self, documents: List[Any]) -> str:
        """소스 문서 포맷팅"""
        if not documents:
            return "관련 문서를 찾지 못했습니다."
        
        sources = []
        for doc in documents:
            sources.append(f"# 참고 자료\n{doc.page_content[:300]}\n")
        
        return "\n\n".join(sources)
    
    async def _generate_fallback_response(
        self, user_input: str, business_type: str, topics: List[str]
    ) -> Dict[str, Any]:
        """폴백 응답 생성"""
        try:
            messages = [
                {
                    "role": "system", 
                    "content": f"당신은 {business_type} 분야의 전문 고객 서비스 담당자입니다. 친절하고 도움이 되는 답변을 제공해주세요."
                },
                {
                    "role": "user", 
                    "content": user_input
                }
            ]
            
            result = await self.llm_manager.generate_response(messages, provider="gemini")
            
            return {
                "topics": topics,
                "answer": result,
                "sources": "기본 고객 서비스 지식으로 답변합니다.",
                "inquiry_type": topics[0] if topics else "general",
                "business_type": business_type,
                "retrieval_used": False
            }
            
        except Exception as e:
            logger.error(f"폴백 응답 생성 실패: {e}")
            return await self._generate_error_fallback(user_input)
    
    async def _generate_error_fallback(self, user_input: str) -> Dict[str, Any]:
        """에러 폴백 응답"""
        return {
            "topics": [],
            "answer": "죄송합니다. 현재 시스템에 문제가 발생했습니다. 고객센터로 직접 연락해주시기 바랍니다.",
            "sources": "시스템 오류로 인해 응답을 생성할 수 없습니다.",
            "inquiry_type": "error",
            "business_type": "unknown",
            "retrieval_used": False,
            "error": True
        }

# 전역 서비스 인스턴스
customer_service = CustomerServiceService()

# 요청 모델 정의 (통일된 구조)
class UserQuery(BaseModel):
    """사용자 쿼리 요청"""
    user_id: Optional[int] = Field(..., description="사용자 ID")
    conversation_id: Optional[int] = Field(None, description="대화 ID")
    message: str = Field(..., description="사용자 메시지")
    persona: Optional[str] = Field(default="common", description="페르소나")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "conversation_id": 456,
                "message": "주문 취소 방법을 알려주세요",
                "persona": "common"
            }
        }

# FastAPI 엔드포인트들 (통일된 응답 구조)
@app.post("/agent/query")
async def process_user_query(request: UserQuery):
    """사용자 쿼리 처리 - 통일된 응답 구조"""
    try:
        logger.info(f"고객 서비스 쿼리 처리 시작 - user_id: {request.user_id}")
        
        user_question = request.message
        user_id = request.user_id
        conversation_id = request.conversation_id
        
        # 1. 대화 세션 처리 - 통일된 로직 사용
        try:
            session_info = get_or_create_conversation_session(user_id, conversation_id)
            conversation_id = session_info["conversation_id"]
        except Exception as e:
            logger.error(f"대화 세션 처리 실패: {e}")
            return create_error_response("대화 세션 생성에 실패했습니다", "SESSION_CREATE_ERROR")

        # 2. 사용자 메시지 저장
        try:
            with get_session_context() as db:
                user_message = create_message(db, conversation_id, "user", "customer_service", user_question)
                if not user_message:
                    logger.warning("사용자 메시지 저장 실패")
        except Exception as e:
            logger.warning(f"사용자 메시지 저장 실패: {e}")

        # 3. 고객 서비스 쿼리 실행
        result = await customer_service.run_customer_service_query(
            conversation_id,
            user_question,
            user_id,
            use_retriever=True
        )

        # 4. 에이전트 응답 저장
        try:
            insert_message_raw(
                conversation_id=conversation_id,
                sender_type="agent",
                agent_type="customer_service",
                content=result["answer"]
            )
        except Exception as e:
            logger.warning(f"에이전트 메시지 저장 실패: {e}")

        # 5. 통일된 응답 생성
        response_data = {
            "conversation_id": conversation_id,
            "topics": result.get("topics", []),
            "answer": result["answer"],
            "sources": result.get("sources", ""),
            "retrieval_used": result.get("retrieval_used", False),
            "inquiry_type": result.get("inquiry_type", ""),
            "business_type": result.get("business_type", ""),
            "timestamp": get_current_timestamp()
        }

        return create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"고객 서비스 쿼리 처리 중 오류 발생: {e}")
        return create_error_response(f"쿼리 처리 중 오류가 발생했습니다: {str(e)}", "QUERY_PROCESSING_ERROR")

@app.get("/preview/{template_id}", response_class=HTMLResponse)
def preview_template(template_id: int):
    """템플릿 미리보기 - 통합 시스템 사용 권장"""
    return create_error_response("이 API는 통합 시스템으로 이동되었습니다. 통합 시스템의 /preview/{template_id}를 사용해주세요.", "API_MOVED")

@app.get("/health")
def health_check():
    """상태 확인 엔드포인트"""
    try:
        config_status = config.validate_config()
        llm_status = llm_manager.get_status()
        vector_status = vector_manager.get_status()
        db_status = db_manager.test_connection()
        
        health_data = {
            "service": "customer_service_agent",
            "status": "healthy",
            "timestamp": get_current_timestamp(),
            "config": config_status,
            "llm": {
                "available_models": llm_status["available_models"],
                "current_provider": llm_status["current_provider"],
                "call_count": llm_status["call_count"]
            },
            "vector": {
                "embedding_available": vector_status["embedding_available"],
                "default_collection": vector_status["default_collection"],
                "cached_vectorstores": vector_status["cached_vectorstores"]
            },
            "database": {
                "connected": db_status,
                "engine_info": db_manager.get_engine_info()
            },
            "workflow_available": customer_workflow is not None
        }
        
        return create_success_response(health_data)
        
    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        return create_error_response(f"헬스체크 실패: {str(e)}", "HEALTH_CHECK_ERROR")

@app.get("/status/detailed")
def detailed_status():
    """상세 상태 확인"""
    try:
        llm_test = llm_manager.test_connection()
        vector_info = vector_manager.get_collection_info()
        
        detailed_data = {
            "service_info": {
                "name": "Customer Service Agent",
                "version": "2.0.0",
                "uptime": get_current_timestamp()
            },
            "llm_test_results": llm_test,
            "vector_collection_info": vector_info,
            "config_summary": config.to_dict(),
            "workflow_available": customer_workflow is not None
        }
        
        return create_success_response(detailed_data)
        
    except Exception as e:
        logger.error(f"상세 상태 확인 실패: {e}")
        return create_error_response(f"상세 상태 확인 실패: {str(e)}", "DETAILED_STATUS_ERROR")

# 메인 실행
if __name__ == "__main__":
    import uvicorn
    
    logger.info("=== Customer Service Agent v2.0 시작 ===")
    logger.info(f"공통 모듈 활용 현황:")
    logger.info(f"  - 설정 관리: {config.__class__.__name__}")
    logger.info(f"  - LLM 관리: {llm_manager.__class__.__name__}")
    logger.info(f"  - 벡터 관리: {vector_manager.__class__.__name__}")
    logger.info(f"  - DB 관리: {db_manager.__class__.__name__}")
    logger.info(f"  - 워크플로우: {'사용 가능' if customer_workflow else '사용 불가'}")
    
    uvicorn.run(
        app, 
        host=config.HOST, 
        port=8001,
        log_level=config.LOG_LEVEL.lower()
    )

# 실행 명령어:
# uvicorn main:app --reload --host 0.0.0.0 --port 8001
# http://127.0.0.1:8001/docs
