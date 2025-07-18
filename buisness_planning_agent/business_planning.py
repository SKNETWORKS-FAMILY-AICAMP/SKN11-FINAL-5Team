"""
Business Planning Agent - 공통 모듈 최대 활용 버전
모든 shared_modules 기능을 최대한 활용하여 리팩토링
"""

import sys
import os
import time
from typing import Optional, List, Dict, Any
from datetime import datetime

# 텔레메트리 비활성화 (ChromaDB 오류 방지)
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY'] = 'False' 
os.environ['DO_NOT_TRACK'] = '1'

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared_modules.utils import get_or_create_conversation_session
# 공통 모듈에서 모든 필요한 것들 import (이제 __init__.py에서 export됨)
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
    load_prompt_from_file,
    create_success_response,
    create_error_response,
    format_conversation_history,
    sanitize_filename,
    get_current_timestamp,
    create_business_response  # 표준 응답 생성 함수 추가
)

sys.path.append(os.path.join(os.path.dirname(__file__), '../unified_agent_system'))
from core.models import UnifiedResponse, RoutingDecision, AgentType

from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.chains import RetrievalQA
from langchain_core.output_parsers import StrOutputParser
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

# 로깅 설정 - 공통 모듈 활용
logger = setup_logging("business_planning", log_file="logs/business_planning.log")

# 설정 로드 - 공통 모듈 활용
config = get_config()

# LLM, Vector, DB 매니저 - 공통 모듈 활용
llm_manager = get_llm_manager()
vector_manager = get_vector_manager()
db_manager = get_db_manager()

# FastAPI 초기화
app = FastAPI(
    title="Business Planning Agent",
    description="1인 창업 전문 컨설팅 에이전트",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 프롬프트 설정 - 공통 모듈의 유틸리티 활용
try:
    from config.prompts_config import PROMPT_META
except ImportError:
    logger.warning("prompts_config.py를 찾을 수 없습니다. 기본 설정을 사용합니다.")
    PROMPT_META = {}

from idea_market import get_persona_trend, get_market_analysis

class BusinessPlanningService:
    """비즈니스 기획 서비스 클래스 - 공통 모듈 최대 활용"""
    
    def __init__(self):
        """서비스 초기화"""
        self.llm_manager = llm_manager
        self.vector_manager = vector_manager
        self.db_manager = db_manager
        
        # 토픽 분류 시스템 프롬프트
        self.topic_classify_prompt = self._load_classification_prompt()
        
        logger.info("BusinessPlanningService 초기화 완료")
    
    # 4. market_research(시장/경쟁 분석, 시장규모)
    def _load_classification_prompt(self) -> str:
        """분류 프롬프트 로드"""
        return """
        너는 고객 질문을 분석해서 관련된 사업기획 topic을 모두 골라주는 역할이야.
        소괄호 안은 topic에 대한 부가 설명이야. 부가 설명을 참고해서

        아래의 토픽 중에서 질문과 관련된 키워드를 **복수 개까지** 골라줘.

        콤마(,)로 구분된 키만 출력하고, 설명은 하지마.

        가능한 토픽:
        0. startup_preparation(창업 준비, 체크리스트)
        1. idea_recommendation(창업 아이템, 트렌드, 아이디어 추천)
        2. idea_validation(아이디어 검증, 시장성 분석, 시장규모, 타겟 분석)
        3. business_model(린캔버스, 수익 구조)
        5. mvp_development(MVP 기획, 초기 제품 설계)
        6. funding_strategy(투자유치, 정부지원, 자금 조달)
        7. business_registration(사업자등록, 면허, 신고 절차)
        8. financial_planning(예산, 매출, 세무)
        9. growth_strategy(사업 확장, 스케일업)
        10. risk_management(리스크 관리, 위기 대응)

        **출력 예시**: startup_preparation, idea_validation
        """
    
    async def classify_topics(self, user_input: str) -> List[str]:
        """토픽 분류 - 공통 모듈의 LLM 매니저 활용"""
        try:
            messages = [
                {"role": "system", "content": self.topic_classify_prompt},
                {"role": "user", "content": f"사용자 질문: {user_input}"}
            ]
            
            # 공통 모듈의 LLM 매니저로 응답 생성
            result = await self.llm_manager.generate_response(
                messages=messages,
                provider="openai"  # 분류에는 OpenAI 사용
            )
            
            # 결과 파싱
            topics = [t.strip() for t in result.split(",") if t.strip() in PROMPT_META]
            logger.info(f"토픽 분류 결과: {topics}")
            return topics
            
        except Exception as e:
            logger.error(f"토픽 분류 실패: {e}")
            return []
    
    def load_prompt_texts(self, topics: List[str]) -> List[str]:
        """프롬프트 텍스트 로드 - 공통 모듈의 유틸리티 활용"""
        merged_prompts = []
        
        for topic in topics:
            if topic in PROMPT_META:
                file_path = PROMPT_META[topic]["file"]
                # 공통 모듈의 load_prompt_from_file 활용
                prompt_text = load_prompt_from_file(file_path)
                if prompt_text:
                    merged_prompts.append(prompt_text)
                    logger.info(f"프롬프트 로드 성공: {topic}")
                else:
                    logger.warning(f"프롬프트 로드 실패: {file_path}")
        
        return merged_prompts
    

    def build_agent_prompt(self, topics: List[str], user_input: str, persona: str, history: str) -> PromptTemplate:
        """에이전트 프롬프트 구성"""
        merged_prompts = self.load_prompt_texts(topics)
        role_descriptions = [PROMPT_META[topic]["role"] for topic in topics if topic in PROMPT_META]
        
        # 페르소나별 시스템 컨텍스트
        if persona == "common":
            system_context = f"당신은 1인 창업 전문 컨설턴트입니다. {', '.join(role_descriptions)}"
        else:
            system_context = f"당신은 {persona} 전문 1인 창업 컨설턴트입니다. {', '.join(role_descriptions)}"

        template = f"""{system_context}

다음 지침을 따라 답변하세요:
{chr(10).join(merged_prompts)}

최근 대화:
{history}

참고 문서:
{{context}}

사용자 질문: "{user_input}"

위 지침에 따라 사용자의 질문에 대해 구체적이고 실용적인 답변을 제공하세요. 지침 내용을 그대로 반복하지 말고, 실제 답변만 작성하세요."""

        return PromptTemplate(
            input_variables=["context"],
            template=template
        )
    
    def format_history(self, messages: List[Any]) -> str:
        """대화 히스토리 포맷팅 - 공통 모듈 활용"""
        history_data = []
        for msg in reversed(messages):  # 시간순 정렬
            history_data.append({
                "role": "user" if msg.sender_type.lower() == "user" else "assistant",
                "content": msg.content,
                "timestamp": msg.created_at.isoformat() if msg.created_at else None,
                "agent_type": msg.agent_type
            })
        
        # 공통 모듈의 format_conversation_history 활용
        return format_conversation_history(history_data, max_messages=10)
    
    async def _handle_special_topic(self, topic: str, persona: str, user_input: str, prompt: str):
        """idea_recommendation, idea_validation 공통 처리 함수"""
      
        topic_data_funcs = {
            "idea_recommendation": get_persona_trend,
            "idea_validation": get_market_analysis,
        }
       
        get_data_func = topic_data_funcs.get(topic)
      
        if not get_data_func:
            raise ValueError(f"Unsupported topic for special handling: {topic}")

        if topic == "idea_recommendation":
            trend_data, mcp_source = await get_data_func(persona, user_input)
        else:
            trend_data = await get_data_func(user_input)
            mcp_source = "smithery_ai/brightdata-search"

        prompt_str = prompt.format(context=trend_data)
        messages = [{"role": "user", "content": prompt_str}]

        answer = await self.llm_manager.generate_response(
            messages=messages,
            provider="openai",
        )

        return {
            "topics": [topic],
            "answer": answer,
            "sources": mcp_source,
            "retrieval_used": False,
        }
    
    async def run_rag_query(
        self, 
        conversation_id: int, 
        user_input: str, 
        use_retriever: bool = True, 
        persona: str = "common"
    ) -> Dict[str, Any]:
        """RAG 쿼리 실행 - 공통 모듈들 최대 활용"""
        try:
            # 1. 토픽 분류
            topics = await self.classify_topics(user_input)
            
            # 2. 대화 히스토리 조회 - 공통 모듈의 DB 함수 활용
            with get_session_context() as db:
                messages = get_recent_messages(db, conversation_id, 10)
                history = self.format_history(messages)
            
            # 3. 프롬프트 생성
            prompt = self.build_agent_prompt(topics, user_input, persona, history)
            
            if "idea_recommendation" in topics:
                return await self._handle_special_topic("idea_recommendation", persona, user_input, prompt)
            elif "idea_validation" in topics:
                return await self._handle_special_topic("idea_validation", persona, user_input, prompt)

            # if "idea_recommendation" in topics:
            #     trend_data, mcp_source = await get_persona_trend(persona, user_input)
                
            #     prompt_str=prompt.format(context=trend_data)
            #     messages=[
            #         {"role":"user","content":prompt_str}
            #     ]
                
            #     logger.info(f"[idea_recommendation_prompt] : {prompt_str}")              
                
            #     # chain 없이 context만 바꿔 LLM 단독 호출
            #     answer = await self.llm_manager.generate_response(
            #         messages=messages,
            #         provider="openai"
            #     )
                
            #     logger.info(f"[idea_recommendation] : {answer}")

            #     return {
            #                 "topics": topics,
            #                 "answer": answer,
            #                 "sources":  mcp_source,
            #                 "retrieval_used": False
            #             }
            
            else:
                # 4. 벡터 검색 설정 - 공통 모듈의 vector_manager 활용
                if use_retriever and topics:
                    topic_filter = {
                        "$and": [
                            {"category": "business_planning"},
                            {"topic": {"$in": topics}}
                        ]
                    }
                    
                    # 공통 모듈의 벡터 매니저로 검색기 생성
                    retriever = self.vector_manager.get_retriever(
                        collection_name="global-documents",
                        k=5,
                        search_kwargs={"filter": topic_filter}
                    )
                    
                    if retriever:
                        # LLM으로 로드 밸런싱
                        llm = self.llm_manager.get_llm(load_balance=True)
                        
                        # RetrievalQA 체인 생성
                        qa_chain = RetrievalQA.from_chain_type(
                            llm=llm,
                            chain_type="stuff",
                            retriever=retriever,
                            chain_type_kwargs={"prompt": prompt},
                            return_source_documents=True
                        )
                        
                        result = qa_chain.invoke(user_input)
                        
                        # 소스 문서 정보 포맷팅
                        sources = self._format_source_documents(result.get('source_documents', []))
                        
                        return {
                            "topics": topics,
                            "answer": result['result'],
                            "sources": sources,
                            "retrieval_used": True
                        }
                
                # 5. 검색기 없이 기본 응답 생성
                return await self._generate_fallback_response(topics, user_input, prompt)
            
        except Exception as e:
            logger.error(f"RAG 쿼리 실행 실패: {e}")
            return await self._generate_fallback_response(topics, user_input, prompt)
            # return await self._generate_error_fallback(user_input)
    
    def _format_source_documents(self, documents: List[Any]) -> str:
        """소스 문서 포맷팅"""
        if not documents:
            return "관련 문서를 찾지 못했습니다."
        
        sources = []
        for doc in documents:
            source_info = {
                "source": doc.metadata.get("source", "❌ 없음"),
                "metadata": doc.metadata,
                "length": len(doc.page_content),
                "snippet": doc.page_content[:300]
            }
            sources.append(f"# 문서\n{source_info['snippet']}\n")
        
        return "\n\n".join(sources)
    
    async def _generate_fallback_response(self, topics: List[str], user_input: str, prompt: PromptTemplate) -> Dict[str, Any]:
        """폴백 응답 생성"""
        try:
            # Gemini로 폴백 응답 생성
            llm = self.llm_manager.get_llm("gemini", load_balance=True)
            
            formatted_prompt = prompt.template.format(context="관련 문서를 찾지 못했습니다. 기본 컨설턴트 지식만으로 답변해주세요.")
            
            messages = [{"role": "user", "content": formatted_prompt}]
            result = await self.llm_manager.generate_response(messages, provider="gemini")
            
            return {
                "topics": topics,
                "answer": result,
                "sources": "문서를 찾지 못했습니다. 기본 지식으로 답변합니다.",
                "retrieval_used": False
            }
            
        except Exception as e:
            logger.error(f"폴백 응답 생성 실패: {e}")
            return await self._generate_error_fallback(user_input)
    
    async def _generate_error_fallback(self, user_input: str) -> Dict[str, Any]:
        """에러 폴백 응답"""
        return {
            "topics": [],
            "answer": "죄송합니다. 현재 시스템에 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
            "sources": "시스템 오류로 인해 문서 검색이 불가능합니다.",
            "retrieval_used": False,
            "error": True
        }
    
    def handle_lean_canvas_request(self, user_question: str) -> Dict[str, Any]:
        """린캔버스 요청 처리 - 공통 모듈의 DB 함수 활용"""
        try:
            # 기본값: Common
            template_title = "린 캔버스_common"

            # 세부 키워드에 따라 타이틀 지정
            if "네일" in user_question:
                template_title = "린 캔버스_nail"
            elif "속눈썹" in user_question:
                template_title = "린 캔버스_eyelash"
            elif "쇼핑몰" in user_question:
                template_title = "린 캔버스_ecommers"
            elif "유튜버" in user_question or "크리에이터" in user_question:
                template_title = "린 캔버스_creator"

            # 공통 모듈의 DB 함수로 템플릿 조회
            template = get_template_by_title(template_title)

            return {
                "type": "lean_canvas",
                "title": template_title,
                "content": template["content"] if template else "<p>템플릿 없음</p>"
            }
            
        except Exception as e:
            logger.error(f"린캔버스 요청 처리 실패: {e}")
            return create_error_response("린캔버스 템플릿을 로드할 수 없습니다.", "TEMPLATE_LOAD_ERROR")

# 전역 서비스 인스턴스
business_service = BusinessPlanningService()

# 요청 모델 정의
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
                "message": "창업 아이디어를 검증하고 싶습니다",
                "persona": "common"
            }
        }

# FastAPI 엔드포인트들
@app.post("/agent/query")
async def process_user_query(request: UserQuery):
    """사용자 쿼리 처리 - 공통 모듈들 최대 활용"""
    try:
        start_time = time.time()
        logger.info(f"[START] 쿼리 처리 시작 - user_id: {request.user_id}")

        user_question = request.message
        user_id = request.user_id
        conversation_id = request.conversation_id

        # 1. 대화 세션 처리
        logger.info("[STEP 1] 대화 세션 처리 시작")
        try:
            session_info = get_or_create_conversation_session(user_id, conversation_id)
            conversation_id = session_info["conversation_id"]
            logger.info("[STEP 1] 대화 세션 처리 완료")
        except Exception as e:
            logger.error(f"[STEP 1] 대화 세션 처리 실패: {e}")
            return create_error_response("대화 세션 생성에 실패했습니다", "SESSION_CREATE_ERROR")

        # 2. 사용자 메시지 저장
        logger.info("[STEP 2] 사용자 메시지 저장 시작")
        try:
            with get_session_context() as db:
                user_message = create_message(db, conversation_id, "user", "business_planning", user_question)
                if not user_message:
                    logger.warning("[STEP 2] 사용자 메시지 저장 실패")
            logger.info("[STEP 2] 사용자 메시지 저장 완료")
        except Exception as e:
            logger.warning(f"[STEP 2] 사용자 메시지 저장 실패: {e}")

        # 3. 린캔버스 요청 분기
        logger.info("[STEP 3] 린캔버스 여부 확인")
        if "린캔버스" in user_question:
            logger.info("[STEP 3] 린캔버스 요청 분기 진입")
            lean_canvas_start = time.time()
            lean_canvas_result = business_service.handle_lean_canvas_request(user_question)
            logger.info(f"[STEP 3] 린캔버스 처리 완료 - 소요시간: {time.time() - lean_canvas_start:.2f}s")

            response_data = UnifiedResponse(
                conversation_id=conversation_id,
                agent_type=AgentType.BUSINESS_PLANNING,
                response=lean_canvas_result["content"],
                confidence=0.9,
                routing_decision=RoutingDecision(
                    agent_type=AgentType.BUSINESS_PLANNING,
                    confidence=0.9,
                    reasoning="린캔버스 템플릿 요청",
                    keywords=["린캔버스", lean_canvas_result["title"]]
                ),
                sources=None,
                metadata={
                    "type": "lean_canvas",
                    "template_title": lean_canvas_result["title"]
                },
                processing_time=time.time() - start_time
            )
            return create_success_response(response_data)

        # 4. 일반 RAG 쿼리 처리
        logger.info("[STEP 4] RAG 쿼리 요청 시작")
        rag_start = time.time()
        result = await business_service.run_rag_query(
            conversation_id,
            user_question,
            use_retriever=True,
            persona=request.persona or "common"
        )
        logger.info(f"[STEP 4] RAG 쿼리 처리 완료 - 소요시간: {time.time() - rag_start:.2f}s")

        # 5. 에이전트 응답 저장
        logger.info("[STEP 5] 에이전트 응답 저장 시작")
        try:
            insert_message_raw(
                conversation_id=conversation_id,
                sender_type="agent",
                agent_type="business_planning",
                content=result["answer"]
            )
            logger.info("[STEP 5] 에이전트 응답 저장 완료")
        except Exception as e:
            logger.warning(f"[STEP 5] 에이전트 메시지 저장 실패: {e}")

        # 6. 응답 생성
        logger.info("[STEP 6] 응답 생성 및 반환")
        response_data = create_business_response(
            conversation_id=conversation_id,
            answer=result["answer"],
            topics=result.get("topics", []),
            sources=result.get("sources", "")
        )

        logger.info(f"[END] 전체 처리 완료 - 총 소요시간: {time.time() - start_time:.2f}s")
        return create_success_response(response_data)

    except Exception as e:
        logger.error(f"[ERROR] 쿼리 처리 중 예외 발생: {e}")
        return create_error_response(f"쿼리 처리 중 오류가 발생했습니다: {str(e)}", "QUERY_PROCESSING_ERROR")

@app.get("/lean_canvas/{title}")
def preview_template(title: str):
    """린캔버스 템플릿 미리보기 - 통합 시스템 사용 권장"""
    return create_error_response("이 API는 통합 시스템으로 이동되었습니다. 통합 시스템의 /lean_canvas/{title}을 사용해주세요.", "API_MOVED")

@app.get("/health")
def health_check():
    """상태 확인 엔드포인트 - 공통 모듈들의 상태 체크"""
    try:
        # 각 매니저의 상태 확인
        config_status = config.validate_config()
        llm_status = llm_manager.get_status()
        vector_status = vector_manager.get_status()
        db_status = db_manager.test_connection()
        
        health_data = {
            "service": "business_planning_agent",
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
            }
        }
        
        return create_success_response(health_data)
        
    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        return create_error_response(f"헬스체크 실패: {str(e)}", "HEALTH_CHECK_ERROR")

@app.get("/status/detailed")
def detailed_status():
    """상세 상태 확인 - 각 공통 모듈의 상세 정보"""
    try:
        # LLM 연결 테스트
        llm_test = llm_manager.test_connection()
        
        # 벡터 스토어 정보
        vector_info = vector_manager.get_collection_info()
        
        detailed_data = {
            "service_info": {
                "name": "Business Planning Agent",
                "version": "2.0.0",
                "uptime": get_current_timestamp()
            },
            "llm_test_results": llm_test,
            "vector_collection_info": vector_info,
            "config_summary": config.to_dict(),
            "prompt_meta_available": len(PROMPT_META) > 0,
            "prompt_topics": list(PROMPT_META.keys()) if PROMPT_META else []
        }
        
        return create_success_response(detailed_data)
        
    except Exception as e:
        logger.error(f"상세 상태 확인 실패: {e}")
        return create_error_response(f"상세 상태 확인 실패: {str(e)}", "DETAILED_STATUS_ERROR")

# 메인 실행
if __name__ == "__main__":
    import uvicorn
    
    logger.info("=== Business Planning Agent v2.0 시작 ===\n✅ 이제 통합 시스템과 연동됩니다.")
    logger.info("✅ 핵심 기능만 유지: /agent/query, /health, /status")
    logger.info("✅ 린캔버스 템플릿은 통합 시스템 사용")
    
    uvicorn.run(
        app, 
        host=config.HOST, 
        port=config.PORT,
        log_level=config.LOG_LEVEL.lower()
    )

# 실행 명령어:
# uvicorn business_planning:app --reload --host 0.0.0.0 --port 8080
# http://127.0.0.1:8080/docs
