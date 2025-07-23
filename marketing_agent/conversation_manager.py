"""
멀티턴 대화 관리자 - 개선된 버전
사용자 응답 분석 + 컨텐츠 제작 멀티턴 대화 지원
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import openai

logger = logging.getLogger(__name__)

class MarketingStage(Enum):
    """마케팅 단계 정의"""
    INITIAL = "INITIAL"           # 초기 상태
    GOAL = "GOAL"                # 1단계: 목표 설정  
    TARGET = "TARGET"            # 2단계: 타겟 분석
    STRATEGY = "STRATEGY"        # 3단계: 전략 기획
    EXECUTION = "EXECUTION"      # 4단계: 실행 계획
    CONTENT_CREATION = "CONTENT_CREATION"  # 5단계: 컨텐츠 제작 (멀티턴)
    COMPLETED = "COMPLETED"      # 완료

@dataclass
class ConversationState:
    """대화 상태 관리"""
    user_id: int
    conversation_id: int
    current_stage: MarketingStage = MarketingStage.INITIAL
    business_type: str = "일반"
    collected_info: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    stage_progress: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    # 컨텐츠 제작 관련 상태
    current_content_session: Optional[Dict[str, Any]] = None
    content_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """메시지 추가"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "stage": self.current_stage.value
        }
        if metadata:
            message.update(metadata)
        
        self.conversation_history.append(message)
        self.last_activity = datetime.now()
        
        # 히스토리 크기 제한 (최근 20개만 유지)
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def add_info(self, key: str, value: Any, source: str = "user"):
        """정보 수집"""
        self.collected_info[key] = {
            "value": value,
            "source": source,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_info(self, key: str) -> Any:
        """정보 조회"""
        info = self.collected_info.get(key)
        return info["value"] if info else None
    
    def start_content_session(self, content_type: str, initial_request: str):
        """컨텐츠 제작 세션 시작"""
        self.current_content_session = {
            "content_type": content_type,
            "initial_request": initial_request,
            "created_at": datetime.now().isoformat(),
            "iteration_count": 1,
            "last_content": None
        }
    
    def update_content_session(self, new_content: str, user_feedback: str = None):
        """컨텐츠 제작 세션 업데이트"""
        if self.current_content_session:
            self.current_content_session["last_content"] = new_content
            self.current_content_session["iteration_count"] += 1
            if user_feedback:
                self.current_content_session["last_feedback"] = user_feedback
    
    def end_content_session(self):
        """컨텐츠 제작 세션 종료"""
        if self.current_content_session:
            self.content_history.append(self.current_content_session.copy())
            self.current_content_session = None
    
    def is_in_content_creation(self) -> bool:
        """컨텐츠 제작 단계 여부"""
        return self.current_stage == MarketingStage.CONTENT_CREATION and self.current_content_session is not None
    
    def get_completion_rate(self) -> float:
        """전체 완료율 계산"""
        required_fields = ["business_type", "main_goal", "target_audience", "budget", "channels"]
        completed_fields = sum(1 for field in required_fields if self.get_info(field))
        return completed_fields / len(required_fields)
    
    def get_missing_info(self) -> List[str]:
        required_fields = ["business_type", "main_goal", "target_audience", "budget", "channels", "timeline", "pain_points"]
        return [field for field in required_fields if not self.get_info(field)]

    def get_conversation_context(self) -> str:
        """대화 컨텍스트 요약"""
        context_parts = []
        
        # 기본 정보
        if self.business_type != "일반":
            context_parts.append(f"업종: {self.business_type}")
        
        # 수집된 정보 요약
        key_info = {}
        for key, info in self.collected_info.items():
            key_info[key] = info["value"]
        
        if key_info:
            context_parts.append(f"수집된 정보: {json.dumps(key_info, ensure_ascii=False)}")
        
        # 최근 대화 3개
        recent_messages = self.conversation_history[-6:] if self.conversation_history else []
        if recent_messages:
            context_parts.append("최근 대화:")
            for msg in recent_messages:
                role = "사용자" if msg["role"] == "user" else "AI"
                context_parts.append(f"- {role}: {msg['content'][:100]}...")
        
        return "\n".join(context_parts)
    
    def is_expired(self, timeout_minutes: int = 60) -> bool:
        """세션 만료 확인"""
        expiry_time = self.last_activity + timedelta(minutes=timeout_minutes)
        return datetime.now() > expiry_time

class ConversationManager:
    """개선된 대화 관리자 - 응답 분석 + 컨텐츠 멀티턴 지원"""
    
    def __init__(self):
        from config import config
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL
        self.temperature = config.TEMPERATURE
        self.conversations: Dict[int, ConversationState] = {}
        
        # LLM 프롬프트 초기화
        self._init_llm_prompts()
    
    def _init_llm_prompts(self):
        """LLM 프롬프트 초기화"""
        self.response_analysis_prompt = """당신은 마케팅 상담에서 사용자의 응답을 분석하는 전문가입니다.

사용자가 제공한 정보를 분석하여 다음을 제공해주세요:

{
    "analysis": {
        "provided_info": "사용자가 제공한 정보 요약",
        "insights": "이 정보에서 얻을 수 있는 마케팅 인사이트",
        "strengths": "강점이나 기회 요소",
        "recommendations": "즉시 제안할 수 있는 조언"
    },
    "target_analysis": {
        "customer_profile": "타겟 고객 프로필 분석 (제공된 경우)",
        "market_opportunity": "시장 기회 분석",
        "competitive_advantage": "경쟁 우위 요소"
    },
    "next_questions": {
        "priority": "high|medium|low",
        "missing_critical_info": ["중요한 부족 정보들"],
        "suggested_questions": ["구체적인 질문들"]
    }
}

사용자가 타겟에 대해 말했다면 깊이 있는 타겟 분석을 제공하고,
업종을 언급했다면 해당 업종의 마케팅 특성을 분석해주세요."""

        self.content_feedback_prompt = """당신은 마케팅 콘텐츠 피드백 전문가입니다.

사용자의 콘텐츠 관련 요청을 분석하여 다음을 제공해주세요:

{
    "request_type": "modify|regenerate|new_content|feedback|approval",
    "specific_changes": ["구체적인 수정 요청들"],
    "content_direction": {
        "tone": "변경하고자 하는 톤앤매너",
        "style": "변경하고자 하는 스타일",
        "length": "길이 조정 요청",
        "focus": "집중하고자 하는 포인트"
    },
    "action_needed": {
        "type": "revise_content|create_new|provide_feedback|end_session",
        "priority": "high|medium|low"
    }
}

사용자가 만족하면 세션을 종료하고, 수정 요청이 있으면 구체적인 개선 방향을 제시해주세요."""

        # 기존 프롬프트들도 유지...
        self.intent_analysis_prompt = """당신은 마케팅 상담에서 사용자의 의도와 정보를 분석하는 전문가입니다.

사용자의 메시지를 분석하여 다음 정보를 JSON 형태로 추출해주세요:

{
    "intent": {
        "primary": "정보_요청|목표_설정|타겟_분석|전략_기획|콘텐츠_생성|콘텐츠_수정|일반_질문",
        "confidence": 0.0-1.0,
        "description": "의도 설명"
    },
    "extracted_info": {
        "business_type": "추출된 업종 (없으면 null)",
        "main_goal": "주요 목표 (없으면 null)",
        "target_audience": "타겟 고객 정보 (없으면 null)",
        "budget": "예산 정보 (없으면 null)",
        "channels": "선호 채널 (없으면 null)",
        "timeline": "일정 정보 (없으면 null)",
        "pain_points": "고민거리 (없으면 null)"
    },
    "stage_assessment": {
        "current_stage_complete": true/false,
        "ready_for_next": true/false,
        "suggested_next_stage": "initial|goal|target|strategy|execution|content_creation|completed"
    },
    "content_intent": {
        "is_content_request": true/false,
        "content_type": "instagram|blog|strategy|campaign|multiple",
        "modification_request": true/false
    }
}"""

        self.stage_decision_prompt = """당신은 마케팅 상담의 단계 진행을 결정하는 전문가입니다.

현재 상황을 분석하여 최적의 다음 액션을 JSON 형태로 제안해주세요:

{
    "action": {
        "type": "continue_current|advance_stage|jump_to_stage|generate_content|provide_summary",
        "reasoning": "결정 이유",
        "confidence": 0.0-1.0
    },
    "stage_progress": {
        "current_completion": 0.0-1.0,
        "missing_info": ["부족한 정보들"],
        "next_stage": "목표 단계"
    },
    "response_strategy": {
        "tone": "friendly|professional|encouraging|consultative",
        "format": "question|advice|summary|content",
        "personalization_level": "high|medium|low"
    },
    "follow_up": {
        "ask_question": true/false,
        "question_type": "clarification|deep_dive|expansion|validation",
        "suggested_topics": ["추천 질문 주제들"]
    }
}

단계별 완료 조건:
- GOAL: 명확한 마케팅 목표 + 성공 지표
- TARGET: 타겟 고객 특성 + 페르소나  
- STRATEGY: 마케팅 채널 + 예산/일정
- EXECUTION: 구체적 실행 계획 수립"""

        self.question_generation_prompt = """당신은 마케팅 상담에서 효과적인 질문을 생성하는 전문가입니다.

주어진 상황에 맞는 맞춤형 질문을 생성해주세요:

{
    "question": {
        "main_question": "핵심 질문",
        "context": "질문 배경 설명",
        "examples": ["구체적인 답변 예시들"],
        "follow_up_options": ["후속 질문 옵션들"]
    },
    "guidance": {
        "why_important": "왜 이 질문이 중요한지",
        "how_to_answer": "어떻게 답변하면 좋은지",
        "common_mistakes": "흔한 실수들"
    },
    "personalization": {
        "business_specific": "업종별 맞춤 내용",
        "stage_appropriate": "단계별 적절성",
        "user_friendly": "사용자 친화적 요소"
    }
}

질문 생성 원칙:
1. 구체적이고 실행 가능한 답변을 유도
2. 업종 특성을 반영한 맞춤형 질문
3. 단계별 목적에 부합하는 내용
4. 사용자가 쉽게 이해할 수 있는 언어"""

        self.response_generation_prompt = """당신은 마케팅 전문가로서 사용자에게 도움이 되는 응답을 생성합니다.

다음 원칙에 따라 응답을 생성해주세요:

1. 전문성: 마케팅 전문 지식 기반
2. 실용성: 즉시 적용 가능한 조언
3. 개인화: 사용자 상황에 맞춤
4. 친근함: 편안하고 이해하기 쉬운 톤
5. 구체성: 추상적이지 않은 구체적 가이드

응답 구조:
- 상황 이해 및 공감
- 전문적 조언 및 가이드
- 구체적 다음 액션
- 격려 및 동기부여

이모지와 마크다운을 적절히 사용하여 가독성을 높여주세요."""
    
    async def _call_llm(self, prompt: str, user_input: str, context: str = "") -> Dict[str, Any]:
        """LLM 호출 및 응답 파싱"""
        try:
            full_prompt = f"""{prompt}

현재 상황:
{context}

사용자 입력:
"{user_input}"

위 정보를 바탕으로 분석해주세요."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=self.temperature,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            
            # JSON 파싱 시도
            try:
                # JSON 블록 추출
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                elif "{" in content and "}" in content:
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    json_content = content[json_start:json_end]
                else:
                    json_content = content
                
                return json.loads(json_content)
                
            except json.JSONDecodeError:
                logger.warning(f"JSON 파싱 실패, 원문 반환: {content[:100]}")
                return {"raw_response": content, "error": "json_parse_failed"}
                
        except Exception as e:
            logger.error(f"LLM 호출 실패: {e}")
            return {"error": str(e)}
    
    async def analyze_user_response_with_llm(self, user_input: str, conversation: ConversationState) -> Dict[str, Any]:
        """사용자 응답 분석 - 새로운 기능"""
        context = f"""
        현재 단계: {conversation.current_stage.value}
        업종: {conversation.business_type}
        완료율: {conversation.get_completion_rate():.1%}
        대화 컨텍스트:
        {conversation.get_conversation_context()}
        """
        
        result = await self._call_llm(self.response_analysis_prompt, user_input, context)
        
        # 기본값 설정
        if "error" in result:
            return {
                "analysis": {
                    "provided_info": "정보 수집 중",
                    "insights": "추가 분석이 필요합니다",
                    "strengths": "",
                    "recommendations": ""
                },
                "target_analysis": {},
                "next_questions": {"priority": "medium", "missing_critical_info": [], "suggested_questions": []}
            }
        
        return result
    
    async def handle_content_feedback_with_llm(self, user_input: str, conversation: ConversationState) -> Dict[str, Any]:
        """컨텐츠 피드백 처리 - 새로운 기능"""
        context = f"""
        현재 컨텐츠 세션: {conversation.current_content_session}
        이전 컨텐츠: {conversation.current_content_session.get('last_content', '') if conversation.current_content_session else ''}
        반복 횟수: {conversation.current_content_session.get('iteration_count', 0) if conversation.current_content_session else 0}
        """
        
        result = await self._call_llm(self.content_feedback_prompt, user_input, context)
        
        # 기본값 설정
        if "error" in result:
            return {
                "request_type": "feedback",
                "specific_changes": [],
                "content_direction": {},
                "action_needed": {"type": "provide_feedback", "priority": "medium"}
            }
        
        return result

    async def generate_response_with_context(self, user_input: str, conversation: ConversationState) -> str:
        """개선된 맥락적 응답 생성 - 응답 분석 + 컨텐츠 멀티턴 지원"""
        conversation.add_message("user", user_input)
        logger.info(f"[{conversation.conversation_id}] 사용자 입력: {user_input}")

        try:
            response_parts = []
            
            # 컨텐츠 제작 세션 중인지 확인
            if conversation.is_in_content_creation():
                return await self._handle_content_creation_session(user_input, conversation)
            
            # 1. 사용자 의도 분석
            intent_analysis = await self.analyze_user_intent_with_llm(user_input, conversation)
            logger.info(f"[{conversation.conversation_id}] 의도 분석: {intent_analysis.get('intent', {}).get('primary', 'unknown')}")

            # 2. **새로운 기능: 사용자 응답 분석 먼저 제공**
            if conversation.current_stage != MarketingStage.INITIAL:
                response_analysis = await self.analyze_user_response_with_llm(user_input, conversation)
                
                # 분석 결과를 응답에 포함
                analysis = response_analysis.get("analysis", {})
                if analysis.get("provided_info"):
                    response_parts.append(f"📊 **{analysis['provided_info']}**")
                
                if analysis.get("insights"):
                    response_parts.append(f"💡 **마케팅 인사이트**: {analysis['insights']}")
                
                if analysis.get("strengths"):
                    response_parts.append(f"✨ **강점/기회**: {analysis['strengths']}")
                
                # 타겟 분석이 있는 경우
                target_analysis = response_analysis.get("target_analysis", {})
                if target_analysis.get("customer_profile"):
                    response_parts.append(f"👥 **타겟 분석**: {target_analysis['customer_profile']}")

            # 3. 추출된 정보 저장
            extracted_info = intent_analysis.get("extracted_info", {})
            confirmed_info = []
            for key, value in extracted_info.items():
                if value:
                    conversation.add_info(key, value, "llm_extracted")
                    if key == "business_type" and value != "일반":
                        conversation.business_type = value
                    confirmed_info.append(f"{key}: {value}")

            # 4. 컨텐츠 생성 요청 감지
            content_intent = intent_analysis.get("content_intent", {})
            if content_intent.get("is_content_request"):
                # 컨텐츠 제작 단계로 전환
                conversation.current_stage = MarketingStage.CONTENT_CREATION
                conversation.start_content_session(
                    content_intent.get("content_type", "general"),
                    user_input
                )
                response_parts.append("🎨 **컨텐츠 제작 단계로 진입합니다!**")
                return await self._handle_content_creation_session(user_input, conversation, is_initial=True)

            # 5. 다음 액션 결정
            action_plan = await self.determine_next_action_with_llm(user_input, conversation, intent_analysis)
            await self._handle_stage_progression(conversation, action_plan)

            # 6. 단계 변경 알림
            if action_plan.get("action", {}).get("type") == "advance_stage":
                stage_name = self._get_stage_display_name(conversation.current_stage)
                response_parts.append(f"✅ **{stage_name}로 진행합니다!**")

            # 7. 확인된 정보 표시
            if confirmed_info:
                response_parts.append(f"📝 **확인된 정보**: {', '.join(confirmed_info)}")

            # 8. 부족한 정보 질문 생성
            missing_info = conversation.get_missing_info()
            if missing_info:
                response_parts.append("❗ **추가로 필요한 정보가 있어요.**")
                for info_key in missing_info[:2]:
                    question = await self._generate_specific_question(info_key, conversation)
                    response_parts.append(f"• {question}")

            # 9. 추가 응답 생성
            if not missing_info:
                if not action_plan.get("follow_up", {}).get("ask_question"):
                    response = await self.generate_personalized_response_with_llm(
                        user_input, conversation, action_plan
                    )
                    response_parts.append(response)
                else:
                    question = await self.generate_stage_question_with_llm(
                        conversation.current_stage, conversation
                    )
                    response_parts.append(question)

            # 10. 진행률 표시
            completion = conversation.get_completion_rate()
            if completion > 0:
                response_parts.append(f"\n📊 **전체 진행률**: {completion:.1%}")

            # 최종 응답 조립
            final_response = "\n\n".join(response_parts)
            conversation.add_message("assistant", final_response, metadata={"intent_analysis": intent_analysis})
            
            return final_response

        except Exception as e:
            logger.error(f"[{conversation.conversation_id}] 응답 생성 중 오류: {e}", exc_info=True)
            return "죄송합니다. 응답 생성 중 문제가 발생했습니다. 다시 말씀해주시면 도움을 드리겠습니다."
    
    async def _handle_content_creation_session(self, user_input: str, conversation: ConversationState, is_initial: bool = False) -> str:
        """컨텐츠 제작 세션 처리 - 멀티턴 대화 지원"""
        response_parts = []
        
        if is_initial:
            # 최초 컨텐츠 생성 요청
            response_parts.append("🎨 **컨텐츠 제작을 시작합니다!**")
            response_parts.append("원하시는 컨텐츠를 생성하고 있습니다. 생성 후 수정이나 개선이 필요하시면 언제든지 말씀해주세요.")
            
        else:
            # 피드백 처리
            feedback_analysis = await self.handle_content_feedback_with_llm(user_input, conversation)
            
            request_type = feedback_analysis.get("request_type", "feedback")
            action_needed = feedback_analysis.get("action_needed", {})
            
            if request_type == "modify":
                response_parts.append("🔄 **컨텐츠를 수정하겠습니다!**")
                changes = feedback_analysis.get("specific_changes", [])
                if changes:
                    response_parts.append(f"**수정 사항**: {', '.join(changes)}")
                
                # 실제 컨텐츠 수정은 marketing_agent에서 처리
                conversation.update_content_session("수정 중...", user_input)
                
            elif request_type == "regenerate":
                response_parts.append("🆕 **새로운 컨텐츠를 생성하겠습니다!**")
                conversation.update_content_session("재생성 중...", user_input)
                
            elif request_type == "new_content":
                response_parts.append("✨ **다른 종류의 컨텐츠를 만들어보겠습니다!**")
                # 새로운 컨텐츠 타입으로 세션 업데이트
                
            elif request_type == "approval":
                response_parts.append("✅ **컨텐츠를 마음에 들어하시는군요!**")
                response_parts.append("다른 컨텐츠도 필요하시거나 추가 마케팅 상담이 필요하시면 언제든지 말씀해주세요.")
                conversation.end_content_session()
                conversation.current_stage = MarketingStage.COMPLETED
                
            else:
                # 일반 피드백
                response_parts.append("💬 **피드백 감사합니다!**")
                response_parts.append("구체적으로 어떤 부분을 수정하고 싶으신지 말씀해주시면 더 정확하게 도와드릴 수 있습니다.")
        
        return "\n\n".join(response_parts)
    
    async def _generate_specific_question(self, info_key: str, conversation: ConversationState) -> str:
        """특정 정보에 대한 질문 생성"""
        question_prompts = {
            "business_type": f"어떤 업종에서 일하고 계신가요?",
            "main_goal": f"마케팅을 통해 달성하고 싶은 주요 목표는 무엇인가요?",
            "target_audience": f"주요 고객층은 어떤 분들인가요? (연령대, 성별, 관심사 등)",
            "budget": f"마케팅 예산은 어느 정도로 생각하고 계신가요?",
            "channels": f"어떤 마케팅 채널을 활용하고 싶으신가요? (SNS, 블로그, 광고 등)",
            "timeline": f"언제까지 결과를 보고 싶으신가요?",
            "pain_points": f"현재 마케팅에서 가장 어려운 점은 무엇인가요?"
        }
        
        base_question = question_prompts.get(info_key, f"{info_key}에 대해 알려주실 수 있을까요?")
        
        # 업종별 맞춤 질문 생성
        if conversation.business_type != "일반":
            context_prompt = f"""
            {conversation.business_type} 업종에서 '{info_key}'에 대한 질문을 만들어주세요.
            기본 질문: {base_question}
            
            업종 특성을 반영한 더 구체적인 질문으로 만들어주세요.
            질문 한 문장만 출력하세요.
            """
            
            try:
                result = await self._call_llm(
                    "업종별 맞춤 질문을 생성하는 전문가입니다.",
                    context_prompt
                )
                if isinstance(result, dict) and "raw_response" in result:
                    custom_question = result["raw_response"].strip()
                    if custom_question and len(custom_question) < 200:
                        return custom_question
            except:
                pass
        
        return base_question
    
    # 기존 메서드들 유지...
    async def analyze_user_intent_with_llm(self, user_input: str, conversation: ConversationState) -> Dict[str, Any]:
        """LLM 기반 사용자 의도 분석 (기존 메서드 유지)"""
        context = f"""
        현재 단계: {conversation.current_stage.value}
        업종: {conversation.business_type}
        완료율: {conversation.get_completion_rate():.1%}
        컨텐츠 세션 활성: {conversation.is_in_content_creation()}
        대화 컨텍스트:
        {conversation.get_conversation_context()}
        """
        
        result = await self._call_llm(self.intent_analysis_prompt, user_input, context)
        
        # 기본값 설정
        if "error" in result:
            return {
                "intent": {"primary": "일반_질문", "confidence": 0.5},
                "extracted_info": {},
                "stage_assessment": {"current_stage_complete": False, "ready_for_next": False},
                "content_intent": {"is_content_request": False, "content_type": "", "modification_request": False}
            }
        
        return result
    
    async def determine_next_action_with_llm(self, user_input: str, conversation: ConversationState, 
                                           intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """LLM 기반 다음 액션 결정"""
        context = f"""
        의도 분석 결과: {json.dumps(intent_analysis, ensure_ascii=False)}
        현재 단계: {conversation.current_stage.value}  
        업종: {conversation.business_type}
        완료율: {conversation.get_completion_rate():.1%}
        수집된 정보: {len(conversation.collected_info)}개
        대화 컨텍스트:
        {conversation.get_conversation_context()}
        """
        
        result = await self._call_llm(self.stage_decision_prompt, user_input, context)
        
        # 기본값 설정
        if "error" in result:
            return {
                "action": {"type": "continue_current", "reasoning": "기본 진행"},
                "stage_progress": {"current_completion": 0.3, "missing_info": []},
                "response_strategy": {"tone": "friendly", "format": "question"},
                "follow_up": {"ask_question": True, "suggested_topics": ["마케팅 목표"]}
            }
        
        return result
    
    async def generate_stage_question_with_llm(self, stage: MarketingStage, conversation: ConversationState,
                                             missing_info: List[str] = None) -> str:
        """LLM 기반 단계별 맞춤 질문 생성"""
        context = f"""
목표 단계: {stage.value}
현재 업종: {conversation.business_type}
부족한 정보: {missing_info or []}
수집된 정보: {json.dumps(conversation.collected_info, ensure_ascii=False)}
대화 맥락:
{conversation.get_conversation_context()}
"""
        
        stage_descriptions = {
            MarketingStage.INITIAL: "마케팅 상담 시작 단계",
            MarketingStage.GOAL: "마케팅 목표 설정 단계", 
            MarketingStage.TARGET: "타겟 고객 분석 단계",
            MarketingStage.STRATEGY: "마케팅 전략 기획 단계",
            MarketingStage.EXECUTION: "실행 계획 수립 단계"
        }
        
        stage_prompt = f"""
{self.question_generation_prompt}

단계별 목적: {stage_descriptions.get(stage, "일반 상담")}
"""
        
        result = await self._call_llm(stage_prompt, f"{stage.value} 단계를 위한 질문 생성", context)
        
        if "error" in result:
            # 폴백 질문
            fallback_questions = {
                MarketingStage.GOAL: "🎯 마케팅을 통해 달성하고 싶은 구체적인 목표는 무엇인가요?",
                MarketingStage.TARGET: "👥 주요 타겟 고객은 누구인가요? 연령대, 관심사 등을 알려주세요.",
                MarketingStage.STRATEGY: "📊 어떤 마케팅 채널을 활용하고 싶으신가요? 예산은 얼마나 가능한가요?",
                MarketingStage.EXECUTION: "🚀 구체적으로 어떤 콘텐츠나 캠페인을 만들어보고 싶으신가요?"
            }
            return fallback_questions.get(stage, "어떻게 도와드릴까요?")
        
        # 질문 추출
        if isinstance(result, dict) and "question" in result:
            question_data = result["question"]
            main_question = question_data.get("main_question", "")
            context_info = question_data.get("context", "")
            examples = question_data.get("examples", [])
            
            response = ""
            if context_info:
                response += f"{context_info}\n\n"
            
            response += f"**{main_question}**"
            
            if examples:
                response += f"\n\n💡 **예시:**\n"
                for example in examples[:3]:  # 최대 3개
                    response += f"• {example}\n"
            
            return response
        
        return result.get("raw_response", "어떻게 도와드릴까요?")
    
    async def generate_personalized_response_with_llm(self, user_input: str, conversation: ConversationState,
                                                    action_plan: Dict[str, Any]) -> str:
        """LLM 기반 개인화된 응답 생성"""
        context = f"""
사용자 입력: {user_input}
액션 플랜: {json.dumps(action_plan, ensure_ascii=False)}
현재 단계: {conversation.current_stage.value}
업종: {conversation.business_type}
대화 맥락:
{conversation.get_conversation_context()}
"""
        
        response_prompt = f"""
{self.response_generation_prompt}

응답 전략: {action_plan.get('response_strategy', {})}
톤: {action_plan.get('response_strategy', {}).get('tone', 'friendly')}
형식: {action_plan.get('response_strategy', {}).get('format', 'advice')}
"""
        
        result = await self._call_llm(response_prompt, "위 상황에 맞는 마케팅 전문가 응답 생성", context)
        
        if "error" in result:
            return "마케팅 전문가로서 도움을 드리고 싶지만, 현재 처리 중 문제가 발생했습니다. 조금 더 구체적으로 질문해주시면 더 나은 조언을 드릴 수 있습니다."
        
        return result.get("raw_response", result.get("response", "도움이 되는 조언을 준비 중입니다."))
    
    def get_or_create_conversation(self, user_id: int, conversation_id: Optional[int] = None) -> Tuple[ConversationState, bool]:
        """대화 상태 조회 또는 생성"""
        if conversation_id is None:
            conversation_id = self._generate_conversation_id(user_id)
        
        # 기존 대화 확인
        if conversation_id in self.conversations:
            conversation = self.conversations[conversation_id]
            # 만료된 대화는 새로 시작
            if conversation.is_expired():
                logger.info(f"만료된 대화 재시작: {conversation_id}")
                conversation = ConversationState(user_id, conversation_id)
                self.conversations[conversation_id] = conversation
                return conversation, True
            return conversation, False
        
        # 새 대화 생성
        conversation = ConversationState(user_id, conversation_id)
        self.conversations[conversation_id] = conversation
        logger.info(f"새 대화 시작: user_id={user_id}, conversation_id={conversation_id}")
        return conversation, True
    
    def _generate_conversation_id(self, user_id: int) -> int:
        """대화 ID 생성"""
        import time
        return int(f"{user_id}{int(time.time())}")

    async def _handle_stage_progression(self, conversation: ConversationState, action_plan: Dict[str, Any]):
        """단계 진행 처리"""
        action_type = action_plan.get("action", {}).get("type")
        
        if action_type == "advance_stage":
            next_stage_name = action_plan.get("stage_progress", {}).get("next_stage")
            if next_stage_name:
                try:
                    next_stage = MarketingStage(next_stage_name.upper())
                    conversation.current_stage = next_stage
                    logger.info(f"단계 진행: {conversation.conversation_id} -> {next_stage.value}")
                except ValueError:
                    logger.warning(f"잘못된 단계명: {next_stage_name}")
        
        elif action_type == "jump_to_stage":
            target_stage = action_plan.get("stage_progress", {}).get("next_stage")
            if target_stage:
                try:
                    conversation.current_stage = MarketingStage(target_stage.upper())
                    logger.info(f"단계 점프: {conversation.conversation_id} -> {target_stage}")
                except ValueError:
                    logger.warning(f"잘못된 단계명: {target_stage}")
    
    def _get_stage_display_name(self, stage: MarketingStage) -> str:
        """단계 표시명 반환"""
        display_names = {
            MarketingStage.INITIAL: "상담 시작",
            MarketingStage.GOAL: "1단계: 목표 설정",
            MarketingStage.TARGET: "2단계: 타겟 분석",
            MarketingStage.STRATEGY: "3단계: 전략 기획", 
            MarketingStage.EXECUTION: "4단계: 실행 계획",
            MarketingStage.CONTENT_CREATION: "5단계: 컨텐츠 제작",
            MarketingStage.COMPLETED: "상담 완료"
        }
        return display_names.get(stage, stage.value)
    
    def get_conversation_summary(self, conversation_id: int) -> Dict[str, Any]:
        """대화 요약 정보"""
        if conversation_id not in self.conversations:
            return {"error": "대화를 찾을 수 없습니다"}
        
        conversation = self.conversations[conversation_id]
        
        return {
            "conversation_id": conversation_id,
            "user_id": conversation.user_id,
            "current_stage": conversation.current_stage.value,
            "business_type": conversation.business_type,
            "completion_rate": conversation.get_completion_rate(),
            "collected_info_count": len(conversation.collected_info),
            "message_count": len(conversation.conversation_history),
            "created_at": conversation.created_at.isoformat(),
            "last_activity": conversation.last_activity.isoformat(),
            "stage_progress": conversation.stage_progress,
            "llm_powered": True,
            "intelligence_level": "enhanced",
            "in_content_creation": conversation.is_in_content_creation(),
            "content_session": conversation.current_content_session,
            "content_history_count": len(conversation.content_history)
        }
    
    def cleanup_expired_conversations(self):
        """만료된 대화 정리"""
        expired_ids = []
        for conv_id, conv in self.conversations.items():
            if conv.is_expired():
                expired_ids.append(conv_id)
        
        for conv_id in expired_ids:
            del self.conversations[conv_id]
            logger.info(f"만료된 대화 정리: {conv_id}")
        
        return len(expired_ids)
    
    async def get_welcome_message_with_llm(self, conversation: ConversationState) -> str:
        """LLM 기반 환영 메시지 생성"""
        welcome_prompt = """사용자가 마케팅 상담을 시작할 때 사용할 환영 메시지를 생성해주세요.

요구사항:
1. 친근하고 전문적인 톤
2. 마케팅 전문가로서의 신뢰성 전달
3. 구체적인 도움 영역 제시
4. 사용자의 참여를 유도하는 질문
5. 이모지와 마크다운 활용

마케팅 상담 영역:
- 전략 수립
- 타겟 분석
- 콘텐츠 제작
- 채널 최적화
- 성과 측정

환영 메시지를 생성해주세요."""
        
        result = await self._call_llm(welcome_prompt, "환영 메시지 생성 요청", "")
        
        if "error" in result:
            return """🎉 **마케팅 전문가에게 오신 것을 환영합니다!**

저는 당신의 비즈니스 성장을 도와드리는 AI 마케팅 컨설턴트입니다.

💡 **제가 도와드릴 수 있는 것들:**
• 마케팅 전략 수립
• SNS 콘텐츠 제작 (인스타그램, 블로그)
• 타겟 고객 분석
• 마케팅 캠페인 기획
• 키워드 분석 및 SEO

🚀 **시작해볼까요?**
어떤 업종의 마케팅을 도와드릴까요? (예: 카페, 뷰티샵, 온라인쇼핑몰 등)

💬 자연스럽게 대화하듯 말씀해주세요!"""
        
        return result.get("raw_response", result.get("message", "안녕하세요! 마케팅 상담을 도와드리겠습니다."))
