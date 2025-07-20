"""
통합 비즈니스 기획 에이전트 매니저 - 멀티턴 대화 시스템
마케팅 에이전트의 구조를 참고하여 리팩토링
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from enum import Enum
import json
from datetime import datetime

# 공통 모듈 임포트
from shared_modules import (
    get_config,
    get_llm_manager,
    get_vector_manager,
    get_or_create_conversation_session,
    create_message,
    get_recent_messages,
    insert_message_raw,
    get_session_context,
    create_success_response,
    create_error_response,
    create_business_response,
    get_current_timestamp,
    format_conversation_history,
    load_prompt_from_file,
    PromptTemplate,
    get_template_by_title
)

from buisness_planning_agent.config.persona_config import PERSONA_CONFIG, get_persona_by_topic
from buisness_planning_agent.config.prompts_config import PROMPT_META

logger = logging.getLogger(__name__)

class ConversationStage(Enum):
    """대화 단계 정의"""
    INITIAL = "initial"                    # 초기 접촉
    INFORMATION_GATHERING = "info_gathering"  # 정보 수집
    ANALYSIS = "analysis"                  # 분석
    PLANNING = "planning"                  # 기획/계획 수립
    PROPOSAL = "proposal"                  # 제안
    FEEDBACK = "feedback"                  # 피드백 수집
    REFINEMENT = "refinement"              # 수정
    FINAL_RESULT = "final_result"          # 최종 결과
    COMPLETED = "completed"                # 완료

class ConversationState:
    """대화 상태 관리 클래스"""
    
    def __init__(self, conversation_id: int, user_id: int):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.stage = ConversationStage.INITIAL
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # 수집된 정보
        self.collected_info = {
            "business_idea": None,           # 비즈니스 아이디어
            "industry": None,                # 업종/산업
            "target_customers": None,        # 타겟 고객
            "unique_value": None,            # 고유 가치/차별점
            "business_stage": None,          # 현재 단계 (아이디어/준비/운영 등)
            "budget": None,                  # 예산
            "timeline": None,                # 타임라인
            "location": None,                # 지역/위치
            "team_size": None,               # 팀 규모
            "experience": None,              # 관련 경험
            "goals": None,                   # 목표
            "concerns": None,                # 우려사항
            "additional_context": {}
        }
        
        # 분석 결과
        self.analysis_results = {
            "primary_topics": [],
            "intent_analysis": {},
            "market_analysis": {},
            "risk_analysis": {},
            "recommendations": []
        }
        
        # 계획 및 제안
        self.business_plans = []
        self.feedback_history = []
        self.refinements = []
        
        # 최종 결과
        self.final_plan = None
        self.action_plan = None
        
        # 단계별 프롬프트 기록
        self.stage_prompts = {}
        
    def update_stage(self, new_stage: ConversationStage):
        """단계 업데이트"""
        self.stage = new_stage
        self.updated_at = datetime.now()
        
    def add_collected_info(self, key: str, value: Any):
        """수집된 정보 추가"""
        self.collected_info[key] = value
        self.updated_at = datetime.now()
        
    def add_feedback(self, feedback: Dict[str, Any]):
        """피드백 추가"""
        feedback["timestamp"] = datetime.now()
        self.feedback_history.append(feedback)
        self.updated_at = datetime.now()
        
    def is_information_complete(self) -> bool:
        """정보 수집 완료 여부 확인"""
        required_fields = ["business_idea", "industry", "target_customers", "goals"]
        return all(self.collected_info.get(field) for field in required_fields)
        
    def get_completion_rate(self) -> float:
        """정보 수집 완료율"""
        total_fields = len(self.collected_info)
        completed_fields = len([v for v in self.collected_info.values() if v])
        return completed_fields / total_fields if total_fields > 0 else 0.0

class BusinessPlanningAgentManager:
    """통합 비즈니스 기획 에이전트 관리자 - 멀티턴 대화 시스템"""
    
    def __init__(self):
        """비즈니스 기획 매니저 초기화"""
        self.config = get_config()
        self.llm_manager = get_llm_manager()
        self.vector_manager = get_vector_manager()
        
        # 프롬프트 디렉토리 설정
        self.prompts_dir = Path(__file__).parent.parent / 'prompts'
        
        # 전문 지식 벡터 스토어 설정
        self.knowledge_collection = 'business-planning-knowledge'
        
        # 비즈니스 기획 토픽 정의
        self.business_topics = {
            "startup_preparation": "창업 준비 및 체크리스트",
            "idea_validation": "아이디어 검증 및 시장성 분석",
            "business_model": "비즈니스 모델 및 린캔버스",
            "market_research": "시장 조사 및 경쟁 분석",
            "mvp_development": "MVP 개발 및 초기 제품 설계",
            "funding_strategy": "자금 조달 및 투자 유치",
            "business_registration": "사업자 등록 및 법적 절차",
            "financial_planning": "재무 계획 및 예산 관리",
            "growth_strategy": "성장 전략 및 확장 계획",
            "risk_management": "리스크 관리 및 위기 대응"
        }
        
        # 대화 상태 관리 (메모리 기반)
        self.conversation_states: Dict[int, ConversationState] = {}
        
        # 단계별 정보 수집 질문 템플릿
        self.info_gathering_questions = {
            "business_idea": "어떤 비즈니스 아이디어를 가지고 계신가요?",
            "industry": "어떤 업종/산업 분야인가요?",
            "target_customers": "주요 타겟 고객은 누구인가요?",
            "unique_value": "기존과 다른 차별점이나 고유 가치는 무엇인가요?",
            "business_stage": "현재 어느 단계에 있나요? (아이디어/준비/운영 등)",
            "budget": "초기 투자 가능한 예산은 어느 정도인가요?",
            "timeline": "언제까지 사업을 시작하고 싶으신가요?",
            "location": "사업 지역이나 위치가 정해져 있나요?",
            "team_size": "혼자 시작하시나요? 팀이 있나요?",
            "experience": "관련 업계 경험이나 전문성이 있으신가요?",
            "goals": "1-2년 내 달성하고 싶은 목표는 무엇인가요?",
            "concerns": "가장 걱정되거나 어려운 부분은 무엇인가요?"
        }
        
        # 지식 기반 초기화
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """비즈니스 기획 전문 지식 벡터 스토어 초기화"""
        try:
            vectorstore = self.vector_manager.get_vectorstore(
                collection_name=self.knowledge_collection,
                create_if_not_exists=True
            )
            
            if not vectorstore:
                logger.warning("벡터 스토어 초기화 실패")
                return
            
            logger.info("✅ 비즈니스 기획 전문 지식 벡터 스토어 초기화 완료")
            
        except Exception as e:
            logger.error(f"전문 지식 벡터 스토어 초기화 실패: {e}")
    
    def get_or_create_conversation_state(self, conversation_id: int, user_id: int) -> ConversationState:
        """대화 상태 조회 또는 생성"""
        if conversation_id not in self.conversation_states:
            self.conversation_states[conversation_id] = ConversationState(conversation_id, user_id)
        return self.conversation_states[conversation_id]
    
    def load_topic_prompt(self, topic: str) -> str:
        """토픽별 프롬프트 파일 직접 로드"""
        try:
            prompt_file = self.prompts_dir / f"{topic}.txt"
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(f"프롬프트 파일 없음: {topic}")
                return ""
        except Exception as e:
            logger.error(f"프롬프트 로드 실패 ({topic}): {e}")
            return ""
    
    def classify_business_topic_with_llm(self, user_input: str, context: str = "") -> List[str]:
        """LLM을 활용한 비즈니스 토픽 분류"""
        try:
            topic_classification_prompt = f"""다음 사용자 질문을 분석하여 관련된 비즈니스 기획 토픽을 분류해주세요.

사용 가능한 비즈니스 토픽:
{chr(10).join([f"- {key}: {value}" for key, value in self.business_topics.items()])}

{f"대화 컨텍스트: {context}" if context else ""}

사용자 질문: "{user_input}"

위 질문과 가장 관련성이 높은 토픽을 최대 3개까지 선택하여 키워드만 쉼표로 구분하여 답변해주세요.
예시: startup_preparation, idea_validation, business_model

답변:"""

            messages = [
                {"role": "system", "content": "당신은 비즈니스 기획 전문가로서 사용자 질문을 정확한 비즈니스 토픽으로 분류합니다."},
                {"role": "user", "content": topic_classification_prompt}
            ]
            
            response = self.llm_manager.generate_response_sync(messages)
            
            if response:
                topics = [topic.strip() for topic in response.split(',')]
                valid_topics = [topic for topic in topics if topic in self.business_topics]
                return valid_topics[:3] if valid_topics else ["startup_preparation"]
            
            return ["startup_preparation"]
            
        except Exception as e:
            logger.error(f"LLM 토픽 분류 실패: {e}")
            return ["startup_preparation", "business_model"]
    
    def analyze_user_intent_and_stage(self, user_input: str, state: ConversationState) -> Dict[str, Any]:
        """사용자 의도 및 대화 단계 분석"""
        try:
            context_info = {
                "current_stage": state.stage.value,
                "collected_info": state.collected_info,
                "completion_rate": state.get_completion_rate()
            }
            
            intent_analysis_prompt = f"""사용자의 비즈니스 기획 상담 의도와 대화 진행 방향을 분석해주세요.

현재 대화 상태:
- 단계: {state.stage.value}
- 정보 수집 완료율: {state.get_completion_rate():.1%}
- 수집된 정보: {json.dumps(state.collected_info, ensure_ascii=False, indent=2)}

사용자 입력: "{user_input}"

다음 JSON 형태로 분석 결과를 제공해주세요:
{{
    "intent_type": "info_provide|question_ask|feedback_give|refinement_request|completion_request|general_inquiry|lean_canvas_request",
    "confidence": 0.9,
    "extracted_info": {{
        "field_name": "추출된 정보 (해당하는 경우)"
    }},
    "next_stage_recommendation": "info_gathering|analysis|planning|proposal|feedback|refinement|final_result",
    "user_sentiment": "positive|neutral|negative|frustrated",
    "urgency_level": "high|medium|low",
    "suggested_questions": ["추가로 물어볼 질문들"]
}}

분석 결과:"""

            messages = [
                {"role": "system", "content": "당신은 비즈니스 기획 상담 전문가로서 대화 흐름과 사용자 의도를 정확히 분석합니다."},
                {"role": "user", "content": intent_analysis_prompt}
            ]
            
            response = self.llm_manager.generate_response_sync(messages, output_format="json")
            
            if isinstance(response, dict):
                return response
            elif isinstance(response, str):
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    pass
            
            # 파싱 실패 시 기본값 반환
            return {
                "intent_type": "general_inquiry",
                "confidence": 0.7,
                "extracted_info": {},
                "next_stage_recommendation": "info_gathering",
                "user_sentiment": "neutral",
                "urgency_level": "medium",
                "suggested_questions": []
            }
            
        except Exception as e:
            logger.error(f"의도 및 단계 분석 실패: {e}")
            return {
                "intent_type": "general_inquiry",
                "confidence": 0.5,
                "extracted_info": {},
                "next_stage_recommendation": "info_gathering",
                "user_sentiment": "neutral",
                "urgency_level": "medium",
                "suggested_questions": []
            }
    
    def handle_information_gathering(self, user_input: str, state: ConversationState, intent_analysis: Dict[str, Any]) -> str:
        """정보 수집 단계 처리"""
        
        # 사용자 입력에서 정보 추출
        extracted_info = intent_analysis.get("extracted_info", {})
        
        # 수집된 정보 업데이트
        for field, value in extracted_info.items():
            if field in state.collected_info and value:
                state.add_collected_info(field, value)
        
        # 다음 질문 결정
        missing_info = []
        for field, question in self.info_gathering_questions.items():
            if not state.collected_info.get(field):
                missing_info.append((field, question))
        
        # 정보 수집 완료 확인
        if state.is_information_complete() or len(missing_info) <= 2:
            # 분석 단계로 전환
            state.update_stage(ConversationStage.ANALYSIS)
            return self._generate_transition_to_analysis_response(state)
        
        # 다음 정보 수집 질문
        next_field, next_question = missing_info[0]
        
        collected_summary = []
        for field, value in state.collected_info.items():
            if value:
                collected_summary.append(f"- {self.info_gathering_questions.get(field, field)}: {value}")
        
        response = f"""감사합니다! 지금까지 수집된 정보를 정리해보겠습니다:

{chr(10).join(collected_summary) if collected_summary else "아직 수집된 정보가 없습니다."}

💡 **다음 질문**: {next_question}

더 정확한 맞춤 비즈니스 계획을 위해 위 정보를 알려주세요!"""
        
        return response
    
    def _generate_transition_to_analysis_response(self, state: ConversationState) -> str:
        """분석 단계로 전환 시 응답 생성"""
        collected_info_summary = []
        for field, value in state.collected_info.items():
            if value:
                field_name = self.info_gathering_questions.get(field, field)
                collected_info_summary.append(f"- {field_name}: {value}")
        
        return f"""🎯 **정보 수집 완료!** 

수집된 정보:
{chr(10).join(collected_info_summary)}

이제 이 정보를 바탕으로 **심층 분석**을 진행하겠습니다. 
잠시만 기다려주세요... 📊"""
    
    def handle_analysis_stage(self, user_input: str, state: ConversationState) -> str:
        """분석 단계 처리"""
        
        try:
            # 수집된 정보를 바탕으로 토픽 분류
            analysis_context = " ".join([str(v) for v in state.collected_info.values() if v])
            topics = self.classify_business_topic_with_llm(analysis_context)
            
            # 토픽별 프롬프트 직접 로드
            topic_prompts = {}
            for topic in topics:
                prompt_content = self.load_topic_prompt(topic)
                if prompt_content:
                    topic_prompts[topic] = prompt_content
            
            # 관련 지식 검색
            relevant_knowledge = self.get_relevant_knowledge(analysis_context, topics)
            
            # 분석 프롬프트 생성
            analysis_prompt = f"""다음 정보를 바탕으로 비즈니스 전문가 관점에서 심층 분석을 수행해주세요.

수집된 비즈니스 정보:
{json.dumps(state.collected_info, ensure_ascii=False, indent=2)}

관련 비즈니스 토픽: {', '.join(topics)}

토픽별 분석 지침:
{self._format_topic_prompts(topic_prompts)}

전문 지식 참고:
{chr(10).join(relevant_knowledge) if relevant_knowledge else "기본 비즈니스 지식 활용"}

위 토픽별 지침에 따라 다음 분석을 수행해주세요:

1. **비즈니스 아이디어 분석**: 아이디어의 강점과 개선점
2. **시장 기회 분석**: 시장 상황과 기회 요소
3. **경쟁력 분석**: 차별화 포인트와 경쟁 우위
4. **리스크 분석**: 예상 위험 요소와 대응 방안
5. **실현 가능성**: 현실적인 실행 가능성 평가
6. **우선순위**: 가장 먼저 해야 할 3가지

전문적이면서도 실행 가능한 분석을 제공해주세요."""

            messages = [
                {"role": "system", "content": "당신은 비즈니스 전략 전문가로서 주어진 토픽별 지침에 따라 데이터 기반의 실용적인 분석을 제공합니다."},
                {"role": "user", "content": analysis_prompt}
            ]
            
            analysis_result = self.llm_manager.generate_response_sync(messages)
            
            # 분석 결과 저장
            state.analysis_results = {
                "primary_topics": topics,
                "topic_prompts_used": list(topic_prompts.keys()),
                "analysis_content": analysis_result,
                "timestamp": datetime.now()
            }
            
            # 기획 단계로 전환
            state.update_stage(ConversationStage.PLANNING)
            
            return f"""🔍 **심층 분석 완료**

{analysis_result}

---
이제 이 분석을 바탕으로 **구체적인 비즈니스 계획과 실행 전략**을 수립해드리겠습니다. 잠시만 기다려주세요! 🚀"""
            
        except Exception as e:
            logger.error(f"분석 단계 처리 실패: {e}")
            return "분석 중 오류가 발생했습니다. 다시 시도해주세요."
    
    def _format_topic_prompts(self, topic_prompts: Dict[str, str]) -> str:
        """토픽별 프롬프트를 분석용으로 포맷팅"""
        if not topic_prompts:
            return "기본 비즈니스 분석 수행"
        
        formatted = []
        for topic, prompt_content in topic_prompts.items():
            topic_name = self.business_topics.get(topic, topic)
            formatted.append(f"[{topic_name}]\n{prompt_content}\n")
        
        return "\n".join(formatted)
    
    def get_relevant_knowledge(self, query: str, topics: List[str] = None) -> List[str]:
        """관련 전문 지식 검색"""
        try:
            search_results = self.vector_manager.search_documents(
                query=query,
                collection_name=self.knowledge_collection,
                k=5
            )
            
            knowledge_texts = []
            for doc in search_results[:3]:
                knowledge_area = doc.metadata.get('knowledge_area', '일반')
                content = doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content
                knowledge_texts.append(f"[{knowledge_area}]\n{content}")
            
            return knowledge_texts
            
        except Exception as e:
            logger.error(f"전문 지식 검색 실패: {e}")
            return []
    
    def handle_lean_canvas_request(self, user_input: str, state: ConversationState) -> str:
        """린캔버스 요청 처리"""
        try:
            # 기본값: Common
            template_title = "린 캔버스_common"

            # 수집된 정보를 바탕으로 맞춤형 템플릿 선택
            business_idea = state.collected_info.get("business_idea", "")
            industry = state.collected_info.get("industry", "")
            
            if "네일" in business_idea or "네일" in industry:
                template_title = "린 캔버스_nail"
            elif "속눈썹" in business_idea or "속눈썹" in industry:
                template_title = "린 캔버스_eyelash"
            elif "쇼핑몰" in business_idea or "이커머스" in industry:
                template_title = "린 캔버스_ecommers"
            elif "유튜버" in business_idea or "크리에이터" in business_idea:
                template_title = "린 캔버스_creator"

            # 템플릿 조회
            template = get_template_by_title(template_title)
            
            if template:
                return f"""📋 **맞춤형 린캔버스 템플릿**

수집된 정보를 바탕으로 **{template_title}** 템플릿을 추천합니다.

{template["content"]}

---
이 템플릿을 참고하여 구체적인 비즈니스 모델을 설계해보세요!
추가 질문이나 수정이 필요하면 언제든 말씀해주세요."""
            else:
                return "죄송합니다. 해당 린캔버스 템플릿을 찾을 수 없습니다."
            
        except Exception as e:
            logger.error(f"린캔버스 요청 처리 실패: {e}")
            return "린캔버스 템플릿 로드 중 오류가 발생했습니다."
    
    def process_user_query(
        self, 
        user_input: str, 
        user_id: int, 
        conversation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """사용자 쿼리 처리 - 멀티턴 대화 플로우"""
        
        try:
            logger.info(f"멀티턴 비즈니스 기획 쿼리 처리 시작: {user_input[:50]}...")
            
            # 대화 세션 처리
            session_info = get_or_create_conversation_session(user_id, conversation_id)
            conversation_id = session_info["conversation_id"]
            
            # 대화 상태 조회/생성
            state = self.get_or_create_conversation_state(conversation_id, user_id)
            
            # 사용자 메시지 저장
            with get_session_context() as db:
                create_message(db, conversation_id, "user", "business_planning", user_input)
            
            # 린캔버스 요청 체크
            if "린캔버스" in user_input:
                response_content = self.handle_lean_canvas_request(user_input, state)
            else:
                # 의도 및 단계 분석
                intent_analysis = self.analyze_user_intent_and_stage(user_input, state)
                
                # 현재 단계에 따른 처리
                if state.stage == ConversationStage.INITIAL:
                    # 초기 접촉 시 정보 수집 단계로 전환
                    state.update_stage(ConversationStage.INFORMATION_GATHERING)
                    response_content = f"""안녕하세요! 1인 창업 전문 비즈니스 컨설턴트입니다. 🚀

맞춤형 비즈니스 계획을 수립하기 위해 몇 가지 질문을 드리겠습니다.

**첫 번째 질문**: {list(self.info_gathering_questions.values())[0]}

체계적인 비즈니스 계획 수립을 위해 차근차근 진행해보겠습니다!"""
                    
                elif state.stage == ConversationStage.INFORMATION_GATHERING:
                    response_content = self.handle_information_gathering(user_input, state, intent_analysis)
                    
                elif state.stage == ConversationStage.ANALYSIS:
                    response_content = self.handle_analysis_stage(user_input, state)
                    
                # 추가 단계들은 필요시 구현
                else:
                    response_content = "죄송합니다. 아직 구현되지 않은 단계입니다."
            
            # 응답 메시지 저장
            insert_message_raw(
                conversation_id=conversation_id,
                sender_type="agent",
                agent_type="business_planning",
                content=response_content
            )
            
            # 표준 응답 형식으로 반환
            return create_business_response(
                conversation_id=conversation_id,
                answer=response_content,
                topics=getattr(state.analysis_results, 'primary_topics', []),
                sources=f"멀티턴 대화 시스템 (단계: {state.stage.value})"
            )
            
        except Exception as e:
            logger.error(f"멀티턴 비즈니스 기획 쿼리 처리 실패: {e}")
            return create_error_response(
                error_message=f"비즈니스 기획 상담 처리 중 오류가 발생했습니다: {str(e)}",
                error_code="MULTITURN_BUSINESS_ERROR"
            )
    
    def get_agent_status(self) -> Dict[str, Any]:
        """비즈니스 기획 에이전트 상태 반환"""
        return {
            "agent_type": "business_planning",
            "version": "3.0.0",
            "conversation_system": "multiturn",
            "stages": [stage.value for stage in ConversationStage],
            "active_conversations": len(self.conversation_states),
            "conversation_stages": {
                conv_id: state.stage.value 
                for conv_id, state in self.conversation_states.items()
            },
            "llm_status": self.llm_manager.get_status(),
            "vector_store_status": self.vector_manager.get_status()
        }
