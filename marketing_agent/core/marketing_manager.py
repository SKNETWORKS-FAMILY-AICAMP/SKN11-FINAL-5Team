"""
통합 마케팅 에이전트 매니저 - 멀티턴 대화 시스템
정보 수집 → 분석 → 제안 → 피드백 → 수정 → 최종 결과 플로우
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
    create_marketing_response,
    get_current_timestamp,
    format_conversation_history,
    load_prompt_from_file,
    PromptTemplate
)

from marketing_agent.config.persona_config import PERSONA_CONFIG
from marketing_agent.config.prompts_config import PROMPT_META
from marketing_agent.utils import get_marketing_analysis_tools

logger = logging.getLogger(__name__)

class ConversationStage(Enum):
    """대화 단계 정의"""
    INITIAL = "initial"                    # 초기 접촉
    INFORMATION_GATHERING = "info_gathering"  # 정보 수집
    ANALYSIS = "analysis"                  # 분석
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
            "business_type": None,
            "target_audience": None,
            "product_service": None,
            "current_challenges": None,
            "goals": None,
            "budget": None,
            "timeline": None,
            "platforms": [],
            "industry": None,
            "competitors": [],
            "additional_context": {}
        }
        
        # 분석 결과
        self.analysis_results = {
            "primary_topics": [],
            "intent_analysis": {},
            "mcp_results": {},
            "recommendations": []
        }
        
        # 제안 및 피드백
        self.proposals = []
        self.feedback_history = []
        self.refinements = []
        
        # 최종 결과
        self.final_strategy = None
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
        required_fields = ["business_type", "target_audience", "product_service", "goals"]
        return all(self.collected_info.get(field) for field in required_fields)
        
    def get_completion_rate(self) -> float:
        """정보 수집 완료율"""
        total_fields = len(self.collected_info)
        completed_fields = len([v for v in self.collected_info.values() if v])
        return completed_fields / total_fields if total_fields > 0 else 0.0

class MarketingAgentManager:
    """통합 마케팅 에이전트 관리자 - 멀티턴 대화 시스템"""
    
    def __init__(self):
        """마케팅 매니저 초기화"""
        self.config = get_config()
        self.llm_manager = get_llm_manager()
        self.vector_manager = get_vector_manager()
        self.analysis_tools = get_marketing_analysis_tools()
        
        # 프롬프트 디렉토리 설정
        self.prompts_dir = Path(__file__).parent.parent / 'prompts'
        
        # 전문 지식 벡터 스토어 설정
        self.knowledge_collection = 'marketing-knowledge'
        
        # 마케팅 토픽 정의
        self.marketing_topics = {
            "marketing_fundamentals": "마케팅 기초 이론",
            "social_media_marketing": "SNS 전반 전략",
            "email_marketing": "이메일, 뉴스레터",
            "content_marketing": "콘텐츠 전략, 포맷 기획",
            "personal_branding": "퍼스널 및 브랜드 포지셔닝",
            "digital_advertising": "페이드 미디어, 광고 채널",
            "conversion_optimization": "전환 퍼널, A/B 테스트",
            "influencer_marketing": "협업, 제휴 마케팅",
            "marketing_automation": "자동화, 캠페인 설정",
            "viral_marketing": "바이럴, 입소문 전략",
            "blog_marketing": "블로그 마케팅",
            "marketing_metrics": "ROAS, CAC 등 성과 지표",
            "local_marketing": "지역 기반 마케팅"
        }
        
        # 대화 상태 관리 (메모리 기반)
        self.conversation_states: Dict[int, ConversationState] = {}
        
        # 단계별 정보 수집 질문 템플릿
        self.info_gathering_questions = {
            "business_type": "어떤 비즈니스/업종에서 활동하고 계신가요?",
            "target_audience": "주요 타겟 고객층은 누구인가요? (연령, 성별, 관심사 등)",
            "product_service": "구체적으로 어떤 제품이나 서비스를 제공하시나요?",
            "current_challenges": "현재 마케팅에서 가장 큰 어려움은 무엇인가요?",
            "goals": "달성하고 싶은 마케팅 목표는 무엇인가요?",
            "budget": "월 마케팅 예산은 대략 어느 정도인가요?",
            "timeline": "언제까지 결과를 보고 싶으신가요?",
            "platforms": "현재 활용하고 있거나 관심있는 마케팅 채널은?",
            "industry": "업계 특성이나 경쟁 상황을 알려주세요",
            "competitors": "주요 경쟁사나 벤치마킹하는 브랜드가 있나요?"
        }
        
        # 실제 전문 지식 벡터 스토어 초기화 (프롬프트 파일 제외)
        self._initialize_real_knowledge_base()
    
    def _initialize_real_knowledge_base(self):
        """실제 마케팅 전문 지식 벡터 스토어 초기화 (프롬프트 파일 제외)"""
        try:
            # 벡터 스토어 확인
            vectorstore = self.vector_manager.get_vectorstore(
                collection_name=self.knowledge_collection,
                create_if_not_exists=True
            )
            
            if not vectorstore:
                logger.warning("벡터 스토어 초기화 실패")
                return
            
            # ✅ 실제 전문 지식 데이터만 로드 (프롬프트 파일은 제외)
            # 향후 실제 마케팅 전문 콘텐츠, 사례, 이론 등을 여기서 로드
            # knowledge_data_dir = Path(__file__).parent.parent / 'knowledge_data'
            # 또는 외부 API에서 마케팅 지식 가져오기
            
            logger.info("✅ 실제 전문 지식 벡터 스토어 초기화 완료 (프롬프트 파일 제외)")
            
        except Exception as e:
            logger.error(f"전문 지식 벡터 스토어 초기화 실패: {e}")
    
    def _get_knowledge_area(self, topic: str) -> str:
        """토픽에 따른 지식 영역 분류"""
        knowledge_areas = {
            "marketing_fundamentals": "기초 이론",
            "social_media_marketing": "디지털 마케팅",
            "email_marketing": "디지털 마케팅",
            "content_marketing": "콘텐츠 전략",
            "personal_branding": "브랜딩",
            "digital_advertising": "광고/미디어",
            "conversion_optimization": "데이터 분석",
            "influencer_marketing": "파트너십",
            "marketing_automation": "기술/도구",
            "viral_marketing": "소셜/바이럴",
            "blog_marketing": "콘텐츠 전략",
            "marketing_metrics": "데이터 분석",
            "local_marketing": "지역 마케팅"
        }
        return knowledge_areas.get(topic, "일반")
    
    def get_or_create_conversation_state(self, conversation_id: int, user_id: int) -> ConversationState:
        """대화 상태 조회 또는 생성"""
        if conversation_id not in self.conversation_states:
            self.conversation_states[conversation_id] = ConversationState(conversation_id, user_id)
        return self.conversation_states[conversation_id]
    
    def load_topic_prompt(self, topic: str) -> str:
        """토픽별 프롬프트 파일 직접 로드"""
        try:
            prompt_file = self.prompts_dir / f"{topic}.md"
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(f"프롬프트 파일 없음: {topic}")
                return ""
        except Exception as e:
            logger.error(f"프롬프트 로드 실패 ({topic}): {e}")
            return ""
    
    def _format_topic_prompts(self, topic_prompts: Dict[str, str]) -> str:
        """토픽별 프롬프트를 분석용으로 포맷팅"""
        if not topic_prompts:
            return "기본 마케팅 분석 수행"
        
        formatted = []
        for topic, prompt_content in topic_prompts.items():
            topic_name = self.marketing_topics.get(topic, topic)
            formatted.append(f"[{topic_name}]\n{prompt_content}\n")
        
        return "\n".join(formatted)
    
    def classify_marketing_topic_with_llm(self, user_input: str, context: str = "") -> List[str]:
        """LLM을 활용한 마케팅 토픽 분류"""
        try:
            # 토픽 분류 프롬프트
            topic_classification_prompt = f"""다음 사용자 질문을 분석하여 관련된 마케팅 토픽을 분류해주세요.

사용 가능한 마케팅 토픽:
{chr(10).join([f"- {key}: {value}" for key, value in self.marketing_topics.items()])}

{f"대화 컨텍스트: {context}" if context else ""}

사용자 질문: "{user_input}"

위 질문과 가장 관련성이 높은 토픽을 최대 3개까지 선택하여 키워드만 쉼표로 구분하여 답변해주세요.
예시: marketing_fundamentals, content_marketing, social_media_marketing

답변:"""

            messages = [
                {"role": "system", "content": "당신은 마케팅 전문가로서 사용자 질문을 정확한 마케팅 토픽으로 분류합니다."},
                {"role": "user", "content": topic_classification_prompt}
            ]
            
            response = self.llm_manager.generate_response_sync(messages)
            
            # 응답에서 토픽 추출
            if response:
                topics = [topic.strip() for topic in response.split(',')]
                # 유효한 토픽만 필터링
                valid_topics = [topic for topic in topics if topic in self.marketing_topics]
                return valid_topics[:3] if valid_topics else ["marketing_fundamentals"]
            
            return ["marketing_fundamentals"]
            
        except Exception as e:
            logger.error(f"LLM 토픽 분류 실패: {e}")
            return ["marketing_fundamentals", "content_marketing"]
    
    def analyze_user_intent_and_stage(self, user_input: str, state: ConversationState) -> Dict[str, Any]:
        """사용자 의도 및 대화 단계 분석"""
        try:
            # 현재 단계와 수집된 정보를 바탕으로 의도 분석
            context_info = {
                "current_stage": state.stage.value,
                "collected_info": state.collected_info,
                "completion_rate": state.get_completion_rate()
            }
            
            intent_analysis_prompt = f"""사용자의 마케팅 상담 의도와 대화 진행 방향을 분석해주세요.

현재 대화 상태:
- 단계: {state.stage.value}
- 정보 수집 완료율: {state.get_completion_rate():.1%}
- 수집된 정보: {json.dumps(state.collected_info, ensure_ascii=False, indent=2)}

사용자 입력: "{user_input}"

다음 JSON 형태로 분석 결과를 제공해주세요:
{{
    "intent_type": "info_provide|question_ask|feedback_give|refinement_request|completion_request|general_inquiry",
    "confidence": 0.9,
    "extracted_info": {{
        "field_name": "추출된 정보 (해당하는 경우)"
    }},
    "next_stage_recommendation": "info_gathering|analysis|proposal|feedback|refinement|final_result",
    "requires_mcp_tools": true/false,
    "mcp_tools_needed": ["hashtag_analysis", "trend_analysis", "content_generation"],
    "user_sentiment": "positive|neutral|negative|frustrated",
    "urgency_level": "high|medium|low",
    "suggested_questions": ["추가로 물어볼 질문들"]
}}

분석 결과:"""

            messages = [
                {"role": "system", "content": "당신은 마케팅 상담 전문가로서 대화 흐름과 사용자 의도를 정확히 분석합니다."},
                {"role": "user", "content": intent_analysis_prompt}
            ]
            
            response = self.llm_manager.generate_response_sync(messages, output_format="json")
            
            # JSON 응답 파싱
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
                "requires_mcp_tools": False,
                "mcp_tools_needed": [],
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
                "requires_mcp_tools": False,
                "mcp_tools_needed": [],
                "user_sentiment": "neutral",
                "urgency_level": "medium",
                "suggested_questions": []
            }
    
    async def execute_mcp_analysis(self, intent_analysis: Dict[str, Any], user_input: str, state: ConversationState) -> Dict[str, Any]:
        """MCP 도구 실행"""
        results = {}
        
        try:
            if not intent_analysis.get("requires_mcp_tools", False):
                return results
            
            mcp_tools = intent_analysis.get("mcp_tools_needed", [])
            
            # 해시태그 분석
            if "hashtag_analysis" in mcp_tools:
                logger.info("인스타그램 해시태그 분석 실행 중...")
                keywords = []
                if state.collected_info.get("product_service"):
                    keywords.append(state.collected_info["product_service"])
                if state.collected_info.get("industry"):
                    keywords.append(state.collected_info["industry"])
                
                hashtag_result = await self.analysis_tools.analyze_instagram_hashtags(
                    question=user_input,
                    user_hashtags=keywords
                )
                results["hashtag_analysis"] = hashtag_result
            
            # 트렌드 분석
            if "trend_analysis" in mcp_tools:
                logger.info("네이버 트렌드 분석 실행 중...")
                keywords = []
                if state.collected_info.get("product_service"):
                    keywords.append(state.collected_info["product_service"])
                if state.collected_info.get("industry"):
                    keywords.append(state.collected_info["industry"])
                
                if keywords:
                    trend_result = await self.analysis_tools.analyze_naver_trends(keywords)
                    results["trend_analysis"] = trend_result
            
            # 콘텐츠 생성
            if "content_generation" in mcp_tools:
                logger.info("인스타그램 콘텐츠 생성 실행 중...")
                content_result = await self.analysis_tools.generate_instagram_content()
                results["content_generation"] = content_result
            
            return results
            
        except Exception as e:
            logger.error(f"MCP 도구 실행 실패: {e}")
            return {"error": str(e)}
    
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

더 정확한 맞춤 전략을 위해 위 정보를 알려주세요!"""
        
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
    
    def handle_analysis_stage(self, user_input: str, state: ConversationState, mcp_results: Dict[str, Any]) -> str:
        """분석 단계 처리"""
        
        try:
            # 수집된 정보를 바탕으로 토픽 분류
            analysis_context = " ".join([str(v) for v in state.collected_info.values() if v])
            topics = self.classify_marketing_topic_with_llm(analysis_context)
            
            # ✅ 토픽별 프롬프트 직접 로드
            topic_prompts = {}
            for topic in topics:
                prompt_content = self.load_topic_prompt(topic)
                if prompt_content:
                    topic_prompts[topic] = prompt_content
            
            # ✅ 실제 전문 지식 검색 (벡터DB에서 - 별도 데이터)
            relevant_knowledge = self.get_relevant_knowledge(analysis_context, topics)
            
            # 분석 프롬프트 생성
            analysis_prompt = f"""다음 정보를 바탕으로 마케팅 전문가 관점에서 심층 분석을 수행해주세요.

수집된 고객 정보:
{json.dumps(state.collected_info, ensure_ascii=False, indent=2)}

관련 마케팅 토픽: {', '.join(topics)}

토픽별 분석 지침:
{self._format_topic_prompts(topic_prompts)}

실제 전문 지식 참고:
{chr(10).join(relevant_knowledge) if relevant_knowledge else "기본 마케팅 지식 활용"}

실시간 분석 데이터:
{json.dumps(mcp_results, ensure_ascii=False, indent=2) if mcp_results else "실시간 데이터 없음"}

위 토픽별 지침에 따라 다음 분석을 수행해주세요:

1. **현황 분석**: 현재 상황과 문제점 파악
2. **기회 요소**: 활용 가능한 강점과 기회
3. **위험 요소**: 주의해야 할 위협과 약점  
4. **전략 방향**: 추천하는 마케팅 접근법
5. **우선순위**: 가장 먼저 해야 할 3가지

전문적이면서도 실행 가능한 분석을 제공해주세요."""

            messages = [
                {"role": "system", "content": "당신은 마케팅 전략 전문가로서 주어진 토픽별 지침에 따라 데이터 기반의 실용적인 분석을 제공합니다."},
                {"role": "user", "content": analysis_prompt}
            ]
            
            analysis_result = self.llm_manager.generate_response_sync(messages)
            
            # 분석 결과 저장
            state.analysis_results = {
                "primary_topics": topics,
                "topic_prompts_used": list(topic_prompts.keys()),
                "analysis_content": analysis_result,
                "mcp_results": mcp_results,
                "timestamp": datetime.now()
            }
            
            # 제안 단계로 전환
            state.update_stage(ConversationStage.PROPOSAL)
            
            return f"""🔍 **심층 분석 완료**

{analysis_result}

---
이제 이 분석을 바탕으로 **구체적인 마케팅 전략과 실행 계획**을 제안해드리겠습니다. 잠시만 기다려주세요! 🚀"""
            
        except Exception as e:
            logger.error(f"분석 단계 처리 실패: {e}")
            return "분석 중 오류가 발생했습니다. 다시 시도해주세요."
    
    def handle_proposal_stage(self, user_input: str, state: ConversationState) -> str:
        """제안 단계 처리 - 토픽별 프롬프트 활용"""
        
        try:
            # 분석에서 사용된 토픽들의 프롬프트 다시 로드
            topics = state.analysis_results.get("primary_topics", [])
            topic_prompts = {}
            for topic in topics:
                prompt_content = self.load_topic_prompt(topic)
                if prompt_content:
                    topic_prompts[topic] = prompt_content
            
            # ✅ 토픽별 지침이 포함된 제안 프롬프트
            proposal_prompt = f"""분석 결과를 바탕으로 구체적이고 실행 가능한 마케팅 전략을 제안해주세요.

고객 정보:
{json.dumps(state.collected_info, ensure_ascii=False, indent=2)}

분석 결과:
{state.analysis_results.get('analysis_content', '')}

토픽별 제안 지침:
{self._format_topic_prompts(topic_prompts)}

다음 형태로 제안을 구성해주세요:

## 🎯 맞춤 마케팅 전략

### 1️⃣ 핵심 전략
- 전략명: 
- 목표: 
- 예상 효과:

### 2️⃣ 실행 계획 (4주 로드맵)
**1주차:**
- [ ] 액션 1
- [ ] 액션 2

**2주차:**
- [ ] 액션 1  
- [ ] 액션 2

**3-4주차:**
- [ ] 액션 1
- [ ] 액션 2

### 3️⃣ 예산 배분 권장안
- 콘텐츠 제작: X%
- 광고비: X%  
- 도구/자동화: X%

### 4️⃣ 성과 측정 지표
- 주요 KPI: 
- 측정 방법:
- 목표치:

### 5️⃣ 리스크 관리
- 예상 리스크:
- 대응 방안:

이 제안에 대해 어떻게 생각하시나요? 수정하고 싶은 부분이 있으시면 말씀해주세요!"""

            messages = [
                {"role": "system", "content": "당신은 실전 마케팅 전략가로서 주어진 토픽별 지침에 따라 즉시 실행 가능한 구체적인 계획을 제시합니다."},
                {"role": "user", "content": proposal_prompt}
            ]
            
            proposal = self.llm_manager.generate_response_sync(messages)
            
            # 제안 저장
            proposal_data = {
                "content": proposal,
                "topics_used": topics,
                "timestamp": datetime.now(),
                "version": len(state.proposals) + 1
            }
            state.proposals.append(proposal_data)
            
            # 피드백 단계로 전환
            state.update_stage(ConversationStage.FEEDBACK)
            
            return proposal
            
        except Exception as e:
            logger.error(f"제안 단계 처리 실패: {e}")
            return "제안 생성 중 오류가 발생했습니다. 다시 시도해주세요."
    
    def handle_feedback_stage(self, user_input: str, state: ConversationState) -> str:
        """피드백 단계 처리"""
        
        # 피드백 분석
        feedback_analysis_prompt = f"""사용자의 피드백을 분석해주세요.

제안된 전략:
{state.proposals[-1]['content'] if state.proposals else '제안 없음'}

사용자 피드백: "{user_input}"

다음 JSON 형태로 분석해주세요:
{{
    "feedback_type": "positive|negative|neutral|modification_request",
    "satisfaction_level": 0.8,
    "specific_concerns": ["구체적인 우려사항들"],
    "modification_requests": ["수정 요청사항들"],
    "approved_elements": ["승인된 요소들"],
    "needs_refinement": true/false,
    "next_action": "refine|finalize|gather_more_info"
}}"""

        try:
            messages = [
                {"role": "system", "content": "당신은 고객 피드백 분석 전문가입니다."},
                {"role": "user", "content": feedback_analysis_prompt}
            ]
            
            feedback_response = self.llm_manager.generate_response_sync(messages, output_format="json")
            
            if isinstance(feedback_response, str):
                feedback_analysis = json.loads(feedback_response)
            else:
                feedback_analysis = feedback_response
                
        except Exception as e:
            logger.error(f"피드백 분석 실패: {e}")
            feedback_analysis = {
                "feedback_type": "neutral",
                "satisfaction_level": 0.7,
                "needs_refinement": True,
                "next_action": "refine"
            }
        
        # 피드백 저장
        state.add_feedback({
            "user_input": user_input,
            "analysis": feedback_analysis
        })
        
        # 다음 액션 결정
        if feedback_analysis.get("next_action") == "finalize":
            state.update_stage(ConversationStage.FINAL_RESULT)
            return "완벽합니다! 최종 전략 문서를 작성하겠습니다..."
        elif feedback_analysis.get("next_action") == "refine":
            state.update_stage(ConversationStage.REFINEMENT)
            return self.handle_refinement_stage(user_input, state, feedback_analysis)
        else:
            return f"""피드백 감사합니다! 

분석 결과:
- 만족도: {feedback_analysis.get('satisfaction_level', 0.7):.1%}
- 피드백 유형: {feedback_analysis.get('feedback_type', 'neutral')}

더 구체적으로 어떤 부분을 수정하면 좋을지 알려주세요!"""
    
    def handle_refinement_stage(self, user_input: str, state: ConversationState, feedback_analysis: Dict[str, Any]) -> str:
        """수정 단계 처리"""
        
        try:
            # 수정 프롬프트
            refinement_prompt = f"""사용자 피드백을 반영하여 마케팅 전략을 수정해주세요.

기존 제안:
{state.proposals[-1]['content'] if state.proposals else ''}

사용자 피드백 분석:
{json.dumps(feedback_analysis, ensure_ascii=False, indent=2)}

사용자 의견: "{user_input}"

피드백을 적극 반영하여 수정된 전략을 제시해주세요. 
기존 구조를 유지하되, 사용자가 우려한 부분을 개선하고 요청사항을 반영해주세요."""

            messages = [
                {"role": "system", "content": "당신은 고객 맞춤형 전략 수정 전문가입니다."},
                {"role": "user", "content": refinement_prompt}
            ]
            
            refined_proposal = self.llm_manager.generate_response_sync(messages)
            
            # 수정된 제안 저장
            refinement_data = {
                "content": refined_proposal,
                "original_feedback": user_input,
                "feedback_analysis": feedback_analysis,
                "timestamp": datetime.now(),
                "version": len(state.refinements) + 1
            }
            state.refinements.append(refinement_data)
            
            # 다시 피드백 단계로
            state.update_stage(ConversationStage.FEEDBACK)
            
            return f"""✨ **수정된 전략 제안**

{refined_proposal}

---
이번 수정안은 어떠신가요? 추가로 조정할 부분이 있으시면 언제든 말씀해주세요!"""
            
        except Exception as e:
            logger.error(f"수정 단계 처리 실패: {e}")
            return "전략 수정 중 오류가 발생했습니다. 다시 시도해주세요."
    
    def handle_final_result_stage(self, user_input: str, state: ConversationState) -> str:
        """최종 결과 단계 처리"""
        
        try:
            # 최종 전략 문서 생성
            final_prompt = f"""모든 피드백을 반영한 최종 마케팅 전략 문서를 작성해주세요.

고객 정보:
{json.dumps(state.collected_info, ensure_ascii=False, indent=2)}

최종 제안:
{(state.refinements[-1]['content'] if state.refinements else state.proposals[-1]['content']) if (state.refinements or state.proposals) else ''}

피드백 히스토리:
{json.dumps([f['analysis'] for f in state.feedback_history], ensure_ascii=False, indent=2)}

다음 형태로 완성된 최종 문서를 작성해주세요:

# 🎯 [고객명] 맞춤 마케팅 전략 문서

## 📋 프로젝트 개요
- 고객: [비즈니스 정보]
- 목표: [주요 목표]
- 기간: [타임라인]
- 예산: [예산 정보]

## 🔍 현황 분석
[분석 요약]

## 🚀 실행 전략
[확정된 전략]

## 📅 4주 실행 로드맵
[상세 실행 계획]

## 💰 예산 가이드
[예산 배분]

## 📊 성과 측정
[KPI 및 측정 방법]

## ⚠️ 주의사항 & 팁
[실행 시 주의점]

## 🔄 다음 단계
[전략 실행 후 해야할 일들]

---
**마케팅 전략 수립이 완료되었습니다!** 🎉
추가 질문이나 실행 과정에서 도움이 필요하시면 언제든 연락해주세요."""

            messages = [
                {"role": "system", "content": "당신은 최종 마케팅 전략 문서 작성 전문가입니다."},
                {"role": "user", "content": final_prompt}
            ]
            
            final_document = self.llm_manager.generate_response_sync(messages)
            
            # 최종 결과 저장
            state.final_strategy = {
                "content": final_document,
                "timestamp": datetime.now(),
                "total_iterations": len(state.refinements) + 1
            }
            
            # 완료 단계로 전환
            state.update_stage(ConversationStage.COMPLETED)
            
            return final_document
            
        except Exception as e:
            logger.error(f"최종 결과 생성 실패: {e}")
            return "최종 문서 생성 중 오류가 발생했습니다. 다시 시도해주세요."
    
    def get_relevant_knowledge(self, query: str, topics: List[str] = None) -> List[str]:
        """실제 전문 지식 검색 (벡터DB - 프롬프트 파일 제외)"""
        try:
            # ✅ 실제 전문 지식만 검색 (프롬프트 파일은 제외)
            search_results = self.vector_manager.search_documents(
                query=query,
                collection_name=self.knowledge_collection,
                k=5
            )
            
            # 프롬프트 파일은 필터링 제외
            filtered_results = []
            for doc in search_results:
                # 프롬프트 파일이 아닌 실제 지식 콘텐츠만
                if doc.metadata.get('type') != 'prompt_template':
                    filtered_results.append(doc)
            
            # 전문 지식 내용 추출
            knowledge_texts = []
            for doc in filtered_results[:3]:
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
        """사용자 쿼리 처리 - 멀티턴 대화 플로우 메인 엔트리포인트"""
        
        try:
            logger.info(f"멀티턴 마케팅 쿼리 처리 시작: {user_input[:50]}...")
            
            # 대화 세션 처리
            session_info = get_or_create_conversation_session(user_id, conversation_id)
            conversation_id = session_info["conversation_id"]
            
            # 대화 상태 조회/생성
            state = self.get_or_create_conversation_state(conversation_id, user_id)
            
            # 사용자 메시지 저장
            with get_session_context() as db:
                create_message(db, conversation_id, "user", "marketing", user_input)
            
            # 의도 및 단계 분석
            intent_analysis = self.analyze_user_intent_and_stage(user_input, state)
            
            # MCP 도구 실행 (필요한 경우)
            mcp_results = {}
            if intent_analysis.get("requires_mcp_tools", False):
                logger.info("MCP 분석 도구 실행 중...")
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(
                                lambda: asyncio.run(self.execute_mcp_analysis(intent_analysis, user_input, state))
                            )
                            mcp_results = future.result(timeout=30)
                    else:
                        mcp_results = loop.run_until_complete(self.execute_mcp_analysis(intent_analysis, user_input, state))
                except Exception as e:
                    logger.warning(f"MCP 도구 실행 실패: {e}")
                    mcp_results = {}
            
            # 현재 단계에 따른 처리
            if state.stage == ConversationStage.INITIAL:
                # 초기 접촉 시 정보 수집 단계로 전환
                state.update_stage(ConversationStage.INFORMATION_GATHERING)
                response_content = f"""안녕하세요! 솔로프리너을 위한 마케팅 전문 컨설턴트입니다. 🚀

맞춤형 마케팅 전략을 제공하기 위해 몇 가지 질문을 드리겠습니다.

**첫 번째 질문**: {list(self.info_gathering_questions.values())[0]}

정확한 전략 수립을 위해 차근차근 진행해보겠습니다!"""
                
            elif state.stage == ConversationStage.INFORMATION_GATHERING:
                response_content = self.handle_information_gathering(user_input, state, intent_analysis)
                
            elif state.stage == ConversationStage.ANALYSIS:
                response_content = self.handle_analysis_stage(user_input, state, mcp_results)
                
            elif state.stage == ConversationStage.PROPOSAL:
                response_content = self.handle_proposal_stage(user_input, state)
                
            elif state.stage == ConversationStage.FEEDBACK:
                response_content = self.handle_feedback_stage(user_input, state)
                
            elif state.stage == ConversationStage.REFINEMENT:
                # 이미 handle_feedback_stage에서 처리됨
                response_content = "수정 중입니다..."
                
            elif state.stage == ConversationStage.FINAL_RESULT:
                response_content = self.handle_final_result_stage(user_input, state)
                
            elif state.stage == ConversationStage.COMPLETED:
                response_content = f"""전략 수립이 완료되었습니다! 🎉

새로운 마케팅 상담을 원하시면 언제든 말씀해주세요.
혹은 기존 전략에 대한 추가 질문도 환영합니다!

현재 완료된 전략:
- 총 {len(state.proposals) + len(state.refinements)}번의 제안/수정
- {len(state.feedback_history)}번의 피드백 반영
- 최종 완료일: {state.final_strategy['timestamp'].strftime('%Y-%m-%d %H:%M')}"""
            
            else:
                response_content = "대화 흐름에 오류가 발생했습니다. 다시 시작해주세요."
            
            # 응답 메시지 저장
            insert_message_raw(
                conversation_id=conversation_id,
                sender_type="agent",
                agent_type="marketing",
                content=response_content
            )
            
            # 표준 응답 형식으로 반환
            return create_marketing_response(
                conversation_id=conversation_id,
                answer=response_content,
                topics=getattr(state.analysis_results, 'primary_topics', []),
                sources=f"멀티턴 대화 시스템 (단계: {state.stage.value})",
                intent=intent_analysis.get("intent_type"),
                confidence=intent_analysis.get("confidence"),
                conversation_stage=state.stage.value,
                completion_rate=state.get_completion_rate(),
                collected_info=state.collected_info,
                mcp_results=mcp_results,
                multiturn_flow=True
            )
            
        except Exception as e:
            logger.error(f"멀티턴 마케팅 쿼리 처리 실패: {e}")
            return create_error_response(
                error_message=f"마케팅 상담 처리 중 오류가 발생했습니다: {str(e)}",
                error_code="MULTITURN_MARKETING_ERROR"
            )
    
    def get_conversation_status(self, conversation_id: int) -> Dict[str, Any]:
        """대화 상태 조회"""
        if conversation_id in self.conversation_states:
            state = self.conversation_states[conversation_id]
            return {
                "conversation_id": conversation_id,
                "stage": state.stage.value,
                "completion_rate": state.get_completion_rate(),
                "collected_info": state.collected_info,
                "total_proposals": len(state.proposals),
                "total_refinements": len(state.refinements),
                "total_feedback": len(state.feedback_history),
                "is_completed": state.stage == ConversationStage.COMPLETED,
                "last_updated": state.updated_at.isoformat()
            }
        else:
            return {"error": "대화를 찾을 수 없습니다"}
    
    def reset_conversation(self, conversation_id: int) -> bool:
        """대화 초기화"""
        if conversation_id in self.conversation_states:
            del self.conversation_states[conversation_id]
            return True
        return False
    
    def get_agent_status(self) -> Dict[str, Any]:
        """마케팅 에이전트 상태 반환"""
        return {
            "agent_type": "marketing",
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
            "mcp_tools_available": ["hashtag_analysis", "trend_analysis", "content_generation"]
        }
