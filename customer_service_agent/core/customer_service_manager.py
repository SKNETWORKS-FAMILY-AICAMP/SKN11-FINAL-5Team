"""
통합 고객 서비스 에이전트 매니저 - 멀티턴 대화 시스템
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
    get_current_timestamp,
    format_conversation_history,
    load_prompt_from_file,
    PromptTemplate,
    get_templates_by_type
)

from customer_service_agent.config.persona_config import PERSONA_CONFIG, get_persona_by_topic
from customer_service_agent.config.prompts_config import PROMPT_META

logger = logging.getLogger(__name__)

class ConversationStage(Enum):
    """대화 단계 정의"""
    INITIAL = "initial"                    # 초기 접촉
    PROBLEM_IDENTIFICATION = "problem_identification"  # 문제 파악
    INFORMATION_GATHERING = "info_gathering"  # 정보 수집
    ANALYSIS = "analysis"                  # 분석
    SOLUTION_PROPOSAL = "solution_proposal"  # 해결책 제안
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
            "business_type": None,           # 사업 유형
            "customer_issue": None,          # 고객 문제/불만
            "customer_segment": None,        # 고객 세그먼트
            "current_situation": None,       # 현재 상황
            "desired_outcome": None,         # 원하는 결과
            "urgency_level": None,           # 긴급도
            "available_resources": None,     # 가용 자원
            "previous_attempts": None,       # 이전 시도
            "customer_data": None,          # 고객 데이터
            "communication_channel": None,   # 소통 채널
            "timeline": None,               # 해결 기한
            "budget": None,                 # 예산
            "additional_context": {}
        }
        
        # 분석 결과
        self.analysis_results = {
            "primary_topics": [],
            "intent_analysis": {},
            "customer_sentiment": "neutral",
            "problem_category": None,
            "recommendations": []
        }
        
        # 해결책 및 제안
        self.solutions = []
        self.feedback_history = []
        self.refinements = []
        
        # 최종 결과
        self.final_solution = None
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
        required_fields = ["business_type", "customer_issue", "desired_outcome"]
        return all(self.collected_info.get(field) for field in required_fields)
        
    def get_completion_rate(self) -> float:
        """정보 수집 완료율"""
        total_fields = len(self.collected_info)
        completed_fields = len([v for v in self.collected_info.values() if v])
        return completed_fields / total_fields if total_fields > 0 else 0.0

class CustomerServiceAgentManager:
    """통합 고객 서비스 에이전트 관리자 - 멀티턴 대화 시스템"""
    
    def __init__(self):
        """고객 서비스 매니저 초기화"""
        self.config = get_config()
        self.llm_manager = get_llm_manager()
        self.vector_manager = get_vector_manager()
        
        # 프롬프트 디렉토리 설정
        self.prompts_dir = Path(__file__).parent.parent / 'prompts'
        
        # 전문 지식 벡터 스토어 설정
        self.knowledge_collection = 'customer-service-knowledge'
        
        # 고객 서비스 토픽 정의
        self.customer_topics = {
            "customer_service": "고객 응대 및 클레임 처리",
            "customer_retention": "재방문 유도 및 고객 유지",
            "customer_satisfaction": "고객 만족도 개선",
            "customer_feedback": "고객 피드백 분석",
            "customer_segmentation": "고객 타겟팅 및 세분화",
            "community_building": "커뮤니티 구축",
            "customer_data": "고객 데이터 활용",
            "privacy_compliance": "개인정보 보호",
            "customer_message": "고객 메시지 템플릿",
            "customer_etc": "기타 고객 관리"
        }
        
        # 대화 상태 관리 (메모리 기반)
        self.conversation_states: Dict[int, ConversationState] = {}
        
        # 단계별 정보 수집 질문 템플릿
        self.info_gathering_questions = {
            "business_type": "어떤 업종/사업을 운영하고 계신가요?",
            "customer_issue": "현재 어떤 고객 관련 문제나 이슈가 있으신가요?",
            "customer_segment": "주요 고객층은 어떻게 되나요?",
            "current_situation": "현재 상황을 자세히 설명해주실 수 있나요?",
            "desired_outcome": "어떤 결과를 원하시나요?",
            "urgency_level": "이 문제의 긴급도는 어느 정도인가요?",
            "available_resources": "현재 활용 가능한 자원(인력, 시스템 등)은 어떻게 되나요?",
            "previous_attempts": "이전에 시도해본 해결 방법이 있나요?",
            "customer_data": "고객 데이터나 피드백이 있다면 알려주세요",
            "communication_channel": "주로 어떤 채널로 고객과 소통하시나요?",
            "timeline": "언제까지 해결하고 싶으신가요?",
            "budget": "예산 범위가 있다면 알려주세요"
        }
        
        # 지식 기반 초기화
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """고객 서비스 전문 지식 벡터 스토어 초기화"""
        try:
            vectorstore = self.vector_manager.get_vectorstore(
                collection_name=self.knowledge_collection,
                create_if_not_exists=True
            )
            
            if not vectorstore:
                logger.warning("벡터 스토어 초기화 실패")
                return
            
            logger.info("✅ 고객 서비스 전문 지식 벡터 스토어 초기화 완료")
            
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
    
    def classify_customer_topic_with_llm(self, user_input: str, context: str = "") -> List[str]:
        """LLM을 활용한 고객 서비스 토픽 분류"""
        try:
            topic_classification_prompt = f"""다음 사용자 질문을 분석하여 관련된 고객 서비스 토픽을 분류해주세요.

사용 가능한 고객 서비스 토픽:
{chr(10).join([f"- {key}: {value}" for key, value in self.customer_topics.items()])}

{f"대화 컨텍스트: {context}" if context else ""}

사용자 질문: "{user_input}"

위 질문과 가장 관련성이 높은 토픽을 최대 2개까지 선택하여 키워드만 쉼표로 구분하여 답변해주세요.
예시: customer_service, customer_retention

답변:"""

            messages = [
                {"role": "system", "content": "당신은 고객 서비스 전문가로서 사용자 질문을 정확한 고객 관리 토픽으로 분류합니다."},
                {"role": "user", "content": topic_classification_prompt}
            ]
            
            response = self.llm_manager.generate_response_sync(messages)
            
            if response:
                topics = [topic.strip() for topic in response.split(',')]
                valid_topics = [topic for topic in topics if topic in self.customer_topics]
                return valid_topics[:2] if valid_topics else ["customer_service"]
            
            return ["customer_service"]
            
        except Exception as e:
            logger.error(f"LLM 토픽 분류 실패: {e}")
            return ["customer_service", "customer_etc"]
    
    def analyze_user_intent_and_stage(self, user_input: str, state: ConversationState) -> Dict[str, Any]:
        """사용자 의도 및 대화 단계 분석"""
        try:
            context_info = {
                "current_stage": state.stage.value,
                "collected_info": state.collected_info,
                "completion_rate": state.get_completion_rate()
            }
            
            intent_analysis_prompt = f"""사용자의 고객 서비스 상담 의도와 대화 진행 방향을 분석해주세요.

현재 대화 상태:
- 단계: {state.stage.value}
- 정보 수집 완료율: {state.get_completion_rate():.1%}
- 수집된 정보: {json.dumps(state.collected_info, ensure_ascii=False, indent=2)}

사용자 입력: "{user_input}"

다음 JSON 형태로 분석 결과를 제공해주세요:
{{
    "intent_type": "problem_report|info_provide|solution_request|feedback_give|template_request|general_inquiry",
    "confidence": 0.9,
    "extracted_info": {{
        "field_name": "추출된 정보 (해당하는 경우)"
    }},
    "next_stage_recommendation": "problem_identification|info_gathering|analysis|solution_proposal|feedback|refinement|final_result",
    "customer_sentiment": "positive|neutral|negative|frustrated|urgent",
    "urgency_level": "high|medium|low",
    "suggested_questions": ["추가로 물어볼 질문들"]
}}

분석 결과:"""

            messages = [
                {"role": "system", "content": "당신은 고객 서비스 상담 전문가로서 대화 흐름과 사용자 의도를 정확히 분석합니다."},
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
                "next_stage_recommendation": "problem_identification",
                "customer_sentiment": "neutral",
                "urgency_level": "medium",
                "suggested_questions": []
            }
            
        except Exception as e:
            logger.error(f"의도 및 단계 분석 실패: {e}")
            return {
                "intent_type": "general_inquiry",
                "confidence": 0.5,
                "extracted_info": {},
                "next_stage_recommendation": "problem_identification",
                "customer_sentiment": "neutral",
                "urgency_level": "medium",
                "suggested_questions": []
            }
    
    def handle_template_request(self, user_input: str, state: ConversationState) -> str:
        """고객 메시지 템플릿 요청 처리"""
        try:
            # 템플릿 타입 추출
            template_type = self.extract_template_type(user_input)
            logger.info(f"추출된 템플릿 타입: {template_type}")
            
            # 템플릿 조회
            templates = get_templates_by_type(template_type)
            
            if template_type == "고객 맞춤 메시지" and templates:
                # 맞춤형 메시지의 경우 추가 필터링
                filtered_templates = self.filter_templates_by_query(templates, user_input)
            else:
                filtered_templates = templates
            
            if filtered_templates:
                answer_blocks = []
                for t in filtered_templates:
                    if t.get("content_type") == "html":
                        preview_url = f"http://localhost:8001/preview/{t['template_id']}"
                        answer_blocks.append(f"📋 **{t['title']}**\n\n[HTML 미리보기]({preview_url})")
                    else:
                        answer_blocks.append(f"📋 **{t['title']}**\n\n{t['content']}")
                
                answer = "\n\n---\n\n".join(answer_blocks)
                answer += f"\n\n✅ 위 템플릿들을 참고하여 고객에게 보낼 메시지를 작성해보세요!"
                return answer
            else:
                return f"'{template_type}' 관련 템플릿을 찾지 못했습니다. 다른 키워드로 다시 검색해보세요."
            
        except Exception as e:
            logger.error(f"템플릿 요청 처리 실패: {e}")
            return "템플릿 검색 중 오류가 발생했습니다."
    
    def extract_template_type(self, user_input: str) -> str:
        """템플릿 타입 추출"""
        template_extract_prompt = f"""다음은 고객 메시지 템플릿 유형 목록입니다.
- 생일/기념일
- 구매 후 안내 (출고 완료, 배송 시작, 배송 안내 등 포함)
- 재구매 유도
- 고객 맞춤 메시지 (VIP, 가입 고객 등 포함)
- 리뷰 요청
- 설문 요청
- 이벤트 안내
- 예약
- 재방문
- 해당사항 없음

아래 질문에서 가장 잘 맞는 템플릿 유형을 한글로 정확히 1개만 골라주세요.
설명 없이 키워드만 출력하세요.

질문: {user_input}
"""

        try:
            messages = [
                {"role": "system", "content": template_extract_prompt},
                {"role": "user", "content": user_input}
            ]
            
            result = self.llm_manager.generate_response_sync(messages)
            return result.strip() if result else "해당사항 없음"
            
        except Exception as e:
            logger.error(f"템플릿 타입 추출 실패: {e}")
            return "해당사항 없음"
    
    def filter_templates_by_query(self, templates: List[Dict], query: str) -> List[Dict]:
        """쿼리에 따른 템플릿 필터링"""
        query_lower = query.lower()
        filtered = []
        
        for t in templates:
            title = t.get('title', '')
            title_lower = title.lower()
            
            # VIP/단골 그룹
            if ('vip' in query_lower or '단골' in query_lower) and ('vip' in title_lower or '단골' in title_lower):
                filtered.append(t)
            # 휴면/장기미구매 그룹
            elif ('휴면' in query_lower or '장기미구매' in query_lower) and '휴면' in title:
                filtered.append(t)
            # 가입, 회원가입 그룹
            elif ('가입' in query_lower or '회원가입' in query_lower) and ('가입' in title_lower or '회원가입' in title_lower):
                filtered.append(t)
            # 최근 구매, 최근구매 그룹
            elif ('최근 구매' in query_lower or '최근구매' in query_lower) and ('최근 구매' in title_lower or '최근구매' in title_lower):
                filtered.append(t)
        
        return filtered if filtered else templates
    
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
    
    def process_user_query(
        self, 
        user_input: str, 
        user_id: int, 
        conversation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """사용자 쿼리 처리 - 멀티턴 대화 플로우"""
        
        try:
            logger.info(f"멀티턴 고객 서비스 쿼리 처리 시작: {user_input[:50]}...")
            
            # 대화 세션 처리
            session_info = get_or_create_conversation_session(user_id, conversation_id)
            conversation_id = session_info["conversation_id"]
            
            # 대화 상태 조회/생성
            state = self.get_or_create_conversation_state(conversation_id, user_id)
            
            # 사용자 메시지 저장
            with get_session_context() as db:
                create_message(db, conversation_id, "user", "customer_service", user_input)
            
            # 템플릿 요청 체크
            if any(keyword in user_input for keyword in ["템플릿", "메시지", "문구", "알림"]):
                response_content = self.handle_template_request(user_input, state)
            else:
                # 의도 및 단계 분석
                intent_analysis = self.analyze_user_intent_and_stage(user_input, state)
                
                # 현재 단계에 따른 처리
                if state.stage == ConversationStage.INITIAL:
                    # 초기 접촉 시 문제 파악 단계로 전환
                    state.update_stage(ConversationStage.PROBLEM_IDENTIFICATION)
                    response_content = f"""안녕하세요! 고객 서비스 전문 컨설턴트입니다. 🎯

고객 관리와 서비스 개선을 위해 도움을 드리겠습니다.

**첫 번째 질문**: {list(self.info_gathering_questions.values())[0]}

정확한 분석과 해결책 제시를 위해 차근차근 진행해보겠습니다!"""
                    
                elif state.stage == ConversationStage.PROBLEM_IDENTIFICATION:
                    # 문제 파악 후 정보 수집으로 전환
                    state.update_stage(ConversationStage.INFORMATION_GATHERING)
                    response_content = self.handle_information_gathering(user_input, state, intent_analysis)
                    
                elif state.stage == ConversationStage.INFORMATION_GATHERING:
                    response_content = self.handle_information_gathering(user_input, state, intent_analysis)
                    
                # 추가 단계들은 필요시 구현
                else:
                    response_content = "죄송합니다. 아직 구현되지 않은 단계입니다."
            
            # 응답 메시지 저장
            insert_message_raw(
                conversation_id=conversation_id,
                sender_type="agent",
                agent_type="customer_service",
                content=response_content
            )
            
            # 표준 응답 형식으로 반환 (shared_modules에 create_customer_service_response 함수가 있다고 가정)
            try:
                from shared_modules.standard_responses import create_customer_service_response
                return create_customer_service_response(
                    conversation_id=conversation_id,
                    answer=response_content,
                    topics=getattr(state.analysis_results, 'primary_topics', []),
                    sources=f"멀티턴 대화 시스템 (단계: {state.stage.value})"
                )
            except ImportError:
                # 백업용 표준 응답
                return create_success_response({
                    "conversation_id": conversation_id,
                    "answer": response_content,
                    "agent_type": "customer_service",
                    "stage": state.stage.value,
                    "completion_rate": state.get_completion_rate(),
                    "timestamp": get_current_timestamp()
                })
            
        except Exception as e:
            logger.error(f"멀티턴 고객 서비스 쿼리 처리 실패: {e}")
            return create_error_response(
                error_message=f"고객 서비스 상담 처리 중 오류가 발생했습니다: {str(e)}",
                error_code="MULTITURN_CUSTOMER_SERVICE_ERROR"
            )
    
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

더 정확한 맞춤 해결책을 위해 위 정보를 알려주세요!"""
        
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
    
    def get_agent_status(self) -> Dict[str, Any]:
        """고객 서비스 에이전트 상태 반환"""
        return {
            "agent_type": "customer_service",
            "version": "3.0.0",
            "conversation_system": "multiturn",
            "stages": [stage.value for stage in ConversationStage],
            "active_conversations": len(self.conversation_states),
            "conversation_stages": {
                conv_id: state.stage.value 
                for conv_id, state in self.conversation_states.items()
            },
            "llm_status": self.llm_manager.get_status(),
            "vector_store_status": self.vector_manager.get_status(),
            "supported_features": [
                "고객 메시지 템플릿",
                "멀티턴 대화",
                "문제 파악 및 해결",
                "고객 세분화",
                "만족도 분석"
            ]
        }
