"""
Mental Health Agent - 공통 모듈 최대 활용 버전
모든 shared_modules 기능을 최대한 활용하여 리팩토링
"""

import sys
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 공통 모듈에서 모든 필요한 것들 import
from shared_modules.llm_utils import get_llm
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
    get_user_by_social,
    create_user_social,
    insert_message_raw,
    create_success_response,
    create_error_response,
    format_conversation_history,
    get_current_timestamp,
    save_or_update_phq9_result,
    get_latest_phq9_by_user
)

from fastapi import FastAPI, Depends, HTTPException, APIRouter, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

# 기존 모듈들
try:
    from schemas import ChatRequest, ChatResponse, ConversationCreate, SocialLoginRequest
    from mental_agent_graph import build_mental_graph
except ImportError:
    logger = None  # 임시로 설정
    if logger: logger.warning("mental agent 모듈들을 찾을 수 없습니다.")
    
    # 기본 스키마 정의
    class ChatRequest(BaseModel):
        user_id: str
        conversation_id: str
        user_input: str
    
    class ChatResponse(BaseModel):
        response: str
        type: str = "normal"
    
    class ConversationCreate(BaseModel):
        user_id: str
        title: Optional[str] = None
    
    class SocialLoginRequest(BaseModel):
        provider: str
        social_id: str
        username: str
        email: str
    
    def build_mental_graph():
        return None

# 로깅 설정 - 공통 모듈 활용
logger = setup_logging("mental_health", log_file="logs/mental_health.log")

# 설정 로드 - 공통 모듈 활용
config = get_config()

# LLM, Vector, DB 매니저 - 공통 모듈 활용
llm_manager = get_llm_manager()
vector_manager = get_vector_manager()
db_manager = get_db_manager()

# FastAPI 앱 초기화
app = FastAPI(
    title="Mental Health Agent",
    description="정신건강 상담 AI 에이전트",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

# 정신건강 전용 프롬프트
MENTAL_HEALTH_SYSTEM_PROMPT = """
당신은 전문적인 정신건강 상담 AI입니다. 다음 지침을 따라 응답하세요:

1. 공감적이고 따뜻한 톤으로 대화
2. 사용자의 감정을 인정하고 검증
3. 전문적인 도움이 필요한 경우 권유
4. 자해나 타해 위험이 감지되면 즉시 긴급 연락처 제공
5. 진단이나 처방은 절대 하지 않음
6. 희망적이고 건설적인 방향으로 안내

위험 키워드: 죽고싶다, 자살, 자해, 소용없다, 끝내고싶다 등
"""

# 긴급상황 키워드들
EMERGENCY_KEYWORDS = [
    "죽고싶", "자살", "자해", "죽을까", "죽어버리", "소용없", "끝내고싶", 
    "사라지고싶", "뛰어내리", "목매", "약을먹고", "칼로", "번개", "차에받이", 
    "강에뛰어", "자살사이트", "자살방법"
]

class MentalHealthService:
    """정신건강 서비스 클래스 - 공통 모듈 최대 활용"""
    
    def __init__(self):
        """서비스 초기화"""
        self.llm_manager = llm_manager
        self.vector_manager = vector_manager
        self.db_manager = db_manager
        self.mental_graph = build_mental_graph()
        
        logger.info("MentalHealthService 초기화 완료")
    
    def check_emergency(self, user_input: str) -> bool:
        """긴급상황 키워드 체크"""
        user_input_lower = user_input.lower().replace(" ", "")
        return any(keyword in user_input_lower for keyword in EMERGENCY_KEYWORDS)
    
    async def analyze_mental_state(self, user_input: str, user_context: str = "") -> Dict[str, Any]:
        """정신상태 분석"""
        try:
            analysis_prompt = f"""
            다음 사용자의 메시지를 분석하여 정신건강 상태를 평가해주세요:
            
            사용자 컨텍스트: {user_context}
            사용자 메시지: {user_input}
            
            다음 항목들을 JSON 형태로 분석해주세요:
            {{
                "mood_level": "1-10 점수",
                "risk_level": "low/medium/high/emergency",
                "suggested_response_type": "supportive/educational/referral/emergency",
                "key_concerns": ["주요 우려사항들"],
                "phq9_relevant": true/false
            }}
            """
            
            # messages = [
            #     {"role": "system", "content": "당신은 정신건강 전문 분석가입니다."},
            #     {"role": "user", "content": analysis_prompt}
            # ]
            
            # result = await self.llm_manager.generate_response(
            #     messages=messages,
            #     provider="openai",
            #     output_format="json"
            # )
            inputs = {
                "user_context": user_context,
                "user_input": user_input
            }
            llm = get_llm("gemini", True)
            result = await llm.ainvoke(inputs)
            
            return result if isinstance(result, dict) else {"risk_level": "low"}
            
        except Exception as e:
            logger.error(f"정신상태 분석 실패: {e}")
            return {"risk_level": "low", "suggested_response_type": "supportive"}
    
    def format_history(self, messages: List[Any]) -> str:
        """대화 히스토리 포맷팅"""
        history_data = []
        for msg in reversed(messages):
            history_data.append({
                "role": "user" if msg.sender_type.lower() == "user" else "assistant",
                "content": msg.content
            })
        
        return format_conversation_history(history_data, max_messages=6)
    
    async def run_mental_health_chat(
        self,
        conversation_id: int,
        user_input: str,
        user_id: int
    ) -> Dict[str, Any]:
        """정신건강 채팅 실행"""
        try:
            # 1. 긴급상황 체크
            if self.check_emergency(user_input):
                return self._generate_emergency_response(user_input)
            
            # 2. 대화 히스토리 조회
            with get_session_context() as db:
                messages = get_recent_messages(db, conversation_id, 10)
                history = self.format_history(messages)
                
                # PHQ-9 기록 조회
                phq9_record = get_latest_phq9_by_user(db, user_id)
                user_context = f"PHQ-9 점수: {phq9_record.score if phq9_record else '없음'}"
            
            # 3. 정신상태 분석
            analysis = await self.analyze_mental_state(user_input, user_context)
            
            # 4. 정신건강 그래프 실행 (만약 사용 가능하다면)
            if self.mental_graph:
                return await self._run_mental_graph(
                    user_id, conversation_id, user_input, analysis, history
                )
            else:
                # 기본 정신건강 상담 실행
                return await self._run_basic_counseling(
                    user_input, history, analysis, user_context
                )
                
        except Exception as e:
            logger.error(f"정신건강 채팅 실행 실패: {e}")
            return await self._generate_error_fallback(user_input)
    
    async def _run_mental_graph(
        self, user_id: int, conversation_id: int, user_input: str, 
        analysis: Dict[str, Any], history: str
    ) -> Dict[str, Any]:
        """정신건강 그래프 실행"""
        try:
            state = {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "user_input": user_input,
                "analysis": analysis,
                "history": history,
                "phq9_suggested": analysis.get("phq9_relevant", False)
            }
            
            if self.mental_graph:
                runnable = self.mental_graph.compile()
                result = runnable.invoke(state)
                
                return {
                    "type": result.get("type", "normal"),
                    "answer": result.get("response", result.get("answer", "")),
                    "analysis": analysis,
                    "phq9_suggested": result.get("phq9_suggested", False),
                    "sources": "정신건강 전문 상담 시스템",
                    "retrieval_used": True
                }
            else:
                return await self._run_basic_counseling(user_input, history, analysis, "")
                
        except Exception as e:
            logger.error(f"정신건강 그래프 실행 실패: {e}")
            return await self._run_basic_counseling(user_input, history, analysis, "")
    
    async def _run_basic_counseling(
        self, user_input: str, history: str, analysis: Dict[str, Any], user_context: str
    ) -> Dict[str, Any]:
        """기본 정신건강 상담"""
        try:
            risk_level = analysis.get("risk_level", "low")
            response_type = analysis.get("suggested_response_type", "supportive")
            
            # 위험도에 따른 시스템 프롬프트 조정
            if risk_level == "high":
                system_prompt = MENTAL_HEALTH_SYSTEM_PROMPT + "\n\n특별 지시: 이 사용자는 고위험 상태입니다. 전문적 도움을 권유하고 희망적인 메시지를 전달하세요."
            elif risk_level == "medium":
                system_prompt = MENTAL_HEALTH_SYSTEM_PROMPT + "\n\n특별 지시: 이 사용자는 중간 위험 상태입니다. 더 자세한 상담과 지지를 제공하세요."
            else:
                system_prompt = MENTAL_HEALTH_SYSTEM_PROMPT
            
            template = f"""{system_prompt}

사용자 컨텍스트: {user_context}

최근 대화:
{history}

사용자 메시지: "{user_input}"

위험도: {risk_level}, 권장 응답 유형: {response_type}

공감적이고 전문적인 정신건강 상담을 제공하세요."""
            
            messages = [
                {"role": "system", "content": template}
            ]
            
            result = await self.llm_manager.generate_response(messages, provider="gemini")
            
            return {
                "type": "counseling",
                "answer": result,
                "analysis": analysis,
                "phq9_suggested": analysis.get("phq9_relevant", False),
                "sources": "기본 정신건강 상담 지식",
                "retrieval_used": False
            }
            
        except Exception as e:
            logger.error(f"기본 상담 실행 실패: {e}")
            return await self._generate_error_fallback(user_input)
    
    def _generate_emergency_response(self, user_input: str) -> Dict[str, Any]:
        """긴급상황 응답 생성"""
        emergency_response = """
😢 지금 많이 힘드신 것 같습니다. 당신의 고통이 느껴집니다.

하지만 당신은 혼자가 아닙니다. 즉시 전문가의 도움을 받으실 것을 강력히 권합니다.

🆘 **긴급 연락처**
• 생명의전화: 1588-9191 (24시간)
• 청소년전화: 1388 (24시간)  
• 정신건강위기상담전화: 1577-0199 (24시간)
• 응급실: 119

💝 **기억해주세요**
- 당신의 생명은 매우 소중합니다
- 지금의 고통은 영원하지 않습니다  
- 전문가가 반드시 도움을 줄 수 있습니다
- 많은 사람들이 당신을 아끼고 있습니다

지금 당장 위의 번호로 전화해주세요. 24시간 누군가 당신을 기다리고 있습니다.
"""
        
        logger.warning(f"긴급상황 감지: {user_input[:100]}")
        
        return {
            "type": "emergency",
            "answer": emergency_response,
            "emergency_contacts": [
                {"name": "생명의전화", "number": "1588-9191"},
                {"name": "청소년전화", "number": "1388"},
                {"name": "정신건강위기상담전화", "number": "1577-0199"},
                {"name": "응급실", "number": "119"}
            ],
            "analysis": {"risk_level": "emergency"},
            "phq9_suggested": False,
            "sources": "긴급상황 대응 매뉴얼",
            "retrieval_used": False
        }
    
    async def _generate_error_fallback(self, user_input: str) -> Dict[str, Any]:
        """에러 폴백 응답"""
        return {
            "type": "error",
            "answer": "죄송합니다. 현재 상담 시스템에 문제가 발생했습니다. 긴급한 상황이시라면 생명의전화(1588-9191)로 연락해주세요.",
            "analysis": {"risk_level": "unknown"},
            "phq9_suggested": False,
            "sources": "시스템 오류",
            "retrieval_used": False,
            "error": True
        }

# 전역 서비스 인스턴스
mental_health_service = MentalHealthService()

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
                "message": "요즘 우울하고 무기력해요",
                "persona": "common"
            }
        }

# 기존 호환성을 위한 DB 세션 함수
def get_db():
    """데이터베이스 세션 의존성 (기존 호환성 유지)"""
    return db_manager.get_session()

# FastAPI 엔드포인트들 (통일된 응답 구조)
@app.post("/agent/query")
async def process_user_query(request: UserQuery):
    """사용자 쿼리 처리 - 통일된 응답 구조"""
    try:
        logger.info(f"정신건강 쿼리 처리 시작 - user_id: {request.user_id}")
        
        user_question = request.message
        user_id = request.user_id
        conversation_id = request.conversation_id
        
        # 1. 대화 세션 처리
        with get_session_context() as db:
            if conversation_id:
                conversation = get_conversation_by_id(db, conversation_id)
                if conversation and conversation.user_id == user_id:
                    logger.info(f"기존 대화 세션 사용: {conversation_id}")
                else:
                    conversation = create_conversation(db, user_id)
                    if not conversation:
                        logger.error(f"대화 세션 생성 실패 - user_id: {user_id}")
                        return create_error_response("대화 세션 생성에 실패했습니다", "SESSION_CREATE_ERROR")
                    conversation_id = conversation.conversation_id
                    logger.info(f"새 대화 세션 생성: {conversation_id}")
            else:
                conversation = create_conversation(db, user_id)
                if not conversation:
                    logger.error(f"대화 세션 생성 실패 - user_id: {user_id}")
                    return create_error_response("대화 세션 생성에 실패했습니다", "SESSION_CREATE_ERROR")
                conversation_id = conversation.conversation_id
                logger.info(f"새 대화 세션 생성: {conversation_id}")

            # 2. 사용자 메시지 저장
            user_message = create_message(db, conversation_id, "user", "mental_health", user_question)
            if not user_message:
                logger.warning("사용자 메시지 저장 실패")

        # 3. 정신건강 상담 실행
        result = await mental_health_service.run_mental_health_chat(
            conversation_id,
            user_question,
            user_id
        )

        # 4. 에이전트 응답 저장
        try:
            insert_message_raw(
                conversation_id=conversation_id,
                sender_type="agent",
                agent_type="mental_health",
                content=result["answer"]
            )
        except Exception as e:
            logger.warning(f"에이전트 메시지 저장 실패: {e}")

        # 5. 통일된 응답 생성
        response_data = {
            "conversation_id": conversation_id,
            "topics": ["mental_health"],
            "answer": result["answer"],
            "sources": result.get("sources", ""),
            "retrieval_used": result.get("retrieval_used", False),
            "response_type": result.get("type", "normal"),
            "analysis": result.get("analysis", {}),
            "phq9_suggested": result.get("phq9_suggested", False),
            "emergency_contacts": result.get("emergency_contacts", []),
            "timestamp": get_current_timestamp()
        }

        return create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"정신건강 쿼리 처리 중 오류 발생: {e}")
        return create_error_response(f"쿼리 처리 중 오류가 발생했습니다: {str(e)}", "QUERY_PROCESSING_ERROR")

# 기존 호환성을 위한 엔드포인트들
@app.post("/chat", response_model=ChatResponse)
def chat_legacy(req: ChatRequest, db: Session = Depends(get_db)):
    """기존 호환성을 위한 채팅 엔드포인트"""
    try:
        logger.info(f"레거시 정신건강 채팅 요청: {req.user_input[:100]}...")
        
        # 새로운 구조로 변환
        user_query = UserQuery(
            user_id=int(req.user_id),
            conversation_id=int(req.conversation_id),
            message=req.user_input
        )
        
        # 새로운 엔드포인트 호출
        import asyncio
        result = asyncio.run(process_user_query(user_query))
        
        if result.get("success"):
            data = result["data"]
            return ChatResponse(
                response=data["answer"],
                type=data.get("response_type", "normal")
            )
        else:
            return ChatResponse(
                response="죄송합니다. 상담 처리 중 오류가 발생했습니다.",
                type="error"
            )
        
    except Exception as e:
        logger.error(f"레거시 채팅 오류: {e}")
        raise HTTPException(status_code=500, detail="정신건강 상담 처리 중 오류가 발생했습니다.")

@app.post("/create_conversation")
def create_conversation_endpoint(req: ConversationCreate, db: Session = Depends(get_db)):
    """대화 세션 생성"""
    try:
        with get_session_context() as db:
            conversation = create_conversation(db, int(req.user_id))
            if not conversation:
                raise HTTPException(status_code=500, detail="대화 세션 생성에 실패했습니다.")
            
            logger.info(f"새 대화 세션 생성: conversation_id={conversation.conversation_id}, user_id={req.user_id}")
            
            response_data = {
                "conversation_id": conversation.conversation_id,
                "user_id": conversation.user_id,
                "title": req.title or "정신건강 상담",
                "created_at": conversation.started_at.isoformat() if conversation.started_at else None
            }
            
            return create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"대화 세션 생성 오류: {e}")
        raise HTTPException(status_code=500, detail="대화 세션 생성에 실패했습니다.")

@app.post("/social_login")
def social_login(req: SocialLoginRequest, db: Session = Depends(get_db)):
    """소셜 로그인"""
    try:
        with get_session_context() as db:
            # 기존 사용자 확인
            user = get_user_by_social(db, req.provider, req.social_id)
            
            if user:
                logger.info(f"기존 사용자 로그인: user_id={user.user_id}, provider={req.provider}")
                response_data = {
                    "user_id": user.user_id,
                    "username": req.username,
                    "email": req.email,
                    "is_new_user": False
                }
            else:
                # 새 사용자 생성
                user = create_user_social(
                    db,
                    provider=req.provider,
                    social_id=req.social_id,
                    email=req.email,
                    nickname=req.username
                )
                
                logger.info(f"새 소셜 사용자 생성: user_id={user.user_id}, provider={req.provider}")
                
                response_data = {
                    "user_id": user.user_id,
                    "username": req.username,
                    "email": req.email,
                    "is_new_user": True
                }
            
            return create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"소셜 로그인 오류: {e}")
        raise HTTPException(status_code=500, detail="소셜 로그인에 실패했습니다.")

@app.get("/conversations/{user_id}")
def get_user_conversations(user_id: str, db: Session = Depends(get_db)):
    """사용자의 대화 세션 목록 조회"""
    try:
        # 공통 모듈의 쿼리 함수 사용
        from shared_modules.queries import get_user_conversations
        
        with get_session_context() as db:
            conversations = get_user_conversations(db, int(user_id))
            
            conversation_list = [
                {
                    "conversation_id": conv.conversation_id,
                    "title": "정신건강 상담",
                    "created_at": conv.started_at.isoformat() if conv.started_at else None,
                    "updated_at": conv.ended_at.isoformat() if conv.ended_at else None
                }
                for conv in conversations
            ]
            
            return create_success_response(conversation_list)
        
    except Exception as e:
        logger.error(f"대화 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="대화 목록 조회에 실패했습니다.")

# PHQ-9 관련 엔드포인트
@app.post("/phq9/start")
def start_phq9_assessment(user_id: str = Body(..., embed=True), conversation_id: str = Body(..., embed=True)):
    """PHQ-9 평가 시작"""
    try:
        logger.info(f"PHQ-9 평가 시작: user_id={user_id}, conversation_id={conversation_id}")
        
        response_data = {
            "message": "PHQ-9 우울증 선별검사를 시작합니다. 다음 질문들에 솔직하게 답변해주세요.",
            "assessment_type": "phq9",
            "status": "started",
            "questions": [
                "지난 2주 동안, 일 또는 여가활동을 하는데 흥미나 즐거움을 느끼지 못함",
                "지난 2주 동안, 기분이 가라앉거나, 우울하거나, 희망이 없다고 느낌",
                "지난 2주 동안, 잠이 들거나 계속 잠을 자는 것이 어려움, 또는 잠을 너무 많이 잠",
                "지난 2주 동안, 피곤하다고 느끼거나 기운이 거의 없음",
                "지난 2주 동안, 입맛이 없거나 과식을 함",
                "지난 2주 동안, 자신을 부정적으로 봄 — 혹은 자신이 실패자라고 느끼거나 자신 또는 가족을 실망시켰다고 느낌",
                "지난 2주 동안, 신문을 읽거나 텔레비전 보는 것과 같은 일에 집중하는 것이 어려움",
                "지난 2주 동안, 다른 사람들이 주목할 정도로 너무 느리게 움직이거나 말을 함. 또는 그 반대로 평상시보다 많이 움직여서 가만히 앉아 있을 수 없었음",
                "지난 2주 동안, 자신이 죽는 것이 더 낫다고 생각하거나 어떤 식으로든 자신을 해칠 것이라고 생각함"
            ]
        }
        
        return create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"PHQ-9 시작 오류: {e}")
        raise HTTPException(status_code=500, detail="PHQ-9 평가 시작에 실패했습니다.")

@app.post("/phq9/submit")
def submit_phq9_assessment(
    user_id: str = Body(...),
    conversation_id: str = Body(...),
    scores: List[int] = Body(...)
):
    """PHQ-9 평가 결과 제출"""
    try:
        if len(scores) != 9:
            raise HTTPException(status_code=400, detail="9개의 응답이 필요합니다.")
        
        total_score = sum(scores)
        
        # 우울증 수준 판정
        if total_score <= 4:
            level = 1  # 최소
            level_text = "최소 우울"
        elif total_score <= 9:
            level = 2  # 경미
            level_text = "경미한 우울"
        elif total_score <= 14:
            level = 3  # 중등도
            level_text = "중등도 우울"
        elif total_score <= 19:
            level = 4  # 중증
            level_text = "중증 우울"
        else:
            level = 5  # 최중증
            level_text = "최중증 우울"
        
        # DB에 결과 저장
        with get_session_context() as db:
            result = save_or_update_phq9_result(db, int(user_id), total_score, level)
            
            # 상담 메시지 저장
            phq9_message = f"PHQ-9 평가 완료: 총점 {total_score}점 ({level_text})"
            create_message(db, int(conversation_id), "system", "mental_health", phq9_message)
        
        # 권장사항 생성
        if total_score >= 15:
            recommendation = "전문의 상담을 강력히 권합니다. 정신건강의학과 방문을 고려해보세요."
        elif total_score >= 10:
            recommendation = "전문가 상담을 권합니다. 상담센터나 정신건강의학과 방문을 고려해보세요."
        elif total_score >= 5:
            recommendation = "경미한 우울 증상이 있습니다. 생활 습관 개선과 함께 지속적인 관찰이 필요합니다."
        else:
            recommendation = "현재 우울 증상은 최소 수준입니다. 현재 상태를 잘 유지하세요."
        
        logger.info(f"PHQ-9 평가 완료: user_id={user_id}, score={total_score}, level={level}")
        
        response_data = {
            "total_score": total_score,
            "level": level,
            "level_text": level_text,
            "recommendation": recommendation,
            "assessment_date": get_current_timestamp()
        }
        
        return create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"PHQ-9 제출 오류: {e}")
        raise HTTPException(status_code=500, detail="PHQ-9 평가 제출에 실패했습니다.")

# 긴급상황 처리 엔드포인트
@app.post("/emergency")
def handle_emergency(
    user_id: str = Body(...),
    conversation_id: str = Body(...),
    message: str = Body(...)
):
    """긴급상황 처리"""
    try:
        logger.warning(f"긴급상황 감지: user_id={user_id}, message={message[:100]}")
        
        response = mental_health_service._generate_emergency_response(message)
        
        # 긴급 메시지 저장
        with get_session_context() as db:
            create_message(
                db,
                int(conversation_id),
                "system",
                "mental_health",
                f"긴급상황 감지: {message}"
            )
            
            create_message(
                db,
                int(conversation_id),
                "agent",
                "mental_health",
                response["answer"]
            )
        
        return create_success_response(response)
        
    except Exception as e:
        logger.error(f"긴급상황 처리 오류: {e}")
        raise HTTPException(status_code=500, detail="긴급상황 처리에 실패했습니다.")

@app.get("/health")
def health_check():
    """상태 확인 엔드포인트"""
    try:
        config_status = config.validate_config()
        llm_status = llm_manager.get_status()
        vector_status = vector_manager.get_status()
        db_status = db_manager.test_connection()
        
        health_data = {
            "service": "mental_health_agent",
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
            "mental_graph_available": mental_health_service.mental_graph is not None
        }
        
        return create_success_response(health_data)
        
    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        return create_error_response(f"헬스체크 실패: {str(e)}", "HEALTH_CHECK_ERROR")

@app.get("/status")
def get_detailed_status():
    """상세 상태 정보"""
    try:
        llm_test = llm_manager.test_connection()
        vector_info = vector_manager.get_collection_info()
        
        detailed_data = {
            "service_info": {
                "name": "Mental Health Agent",
                "version": "2.0.0",
                "uptime": get_current_timestamp()
            },
            "llm_test_results": llm_test,
            "vector_collection_info": vector_info,
            "config_summary": config.to_dict(),
            "mental_graph_available": mental_health_service.mental_graph is not None,
            "emergency_keywords_count": len(EMERGENCY_KEYWORDS)
        }
        
        return create_success_response(detailed_data)
        
    except Exception as e:
        logger.error(f"상세 상태 조회 오류: {e}")
        return create_error_response(f"상세 상태 조회 실패: {str(e)}", "DETAILED_STATUS_ERROR")

# 앱에 라우터 포함
app.include_router(router)

# 메인 실행
if __name__ == "__main__":
    import uvicorn
    
    logger.info("=== Mental Health Agent v2.0 시작 ===")
    logger.info(f"공통 모듈 활용 현황:")
    logger.info(f"  - 설정 관리: {config.__class__.__name__}")
    logger.info(f"  - LLM 관리: {llm_manager.__class__.__name__}")
    logger.info(f"  - 벡터 관리: {vector_manager.__class__.__name__}")
    logger.info(f"  - DB 관리: {db_manager.__class__.__name__}")
    logger.info(f"  - 정신건강 그래프: {'사용 가능' if mental_health_service.mental_graph else '사용 불가'}")
    
    # 설정 검증
    validation = config.validate_config()
    if validation["warnings"]:
        for warning in validation["warnings"]:
            logger.warning(warning)
    
    uvicorn.run(
        app,
        host=config.HOST,
        port=8004,
        log_level=config.LOG_LEVEL.lower()
    )

# 실행 명령어:
# uvicorn main:app --reload --host 0.0.0.0 --port 8004
# http://127.0.0.1:8004/docs
