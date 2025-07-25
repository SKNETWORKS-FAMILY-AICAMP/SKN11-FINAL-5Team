"""
멀티턴 대화 관리자 - 개선된 버전
✅ 질문 반복 방지, 맥락 이해 개선, 친밀감 강화, 사용자 피로도 감소
✅ 모든 응답 LLM 생성, 하드코딩 완전 제거
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from langchain_core.runnables.config import P
import openai
from general_marketing_tools import MarketingTools
from mcp_marketing_tools import MarketingAnalysisTools

general_marketing_tools = MarketingTools()
mcp_marketing_tools = MarketingAnalysisTools()

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

class ConversationMode(Enum):
    """대화 모드"""
    QUESTIONING = "QUESTIONING"   # 질문 모드 (정보 수집)
    SUGGESTING = "SUGGESTING"     # 제안 모드 (직접 추천/조언)
    CONTENT_CREATION = "CONTENT_CREATION"  # 컨텐츠 제작 모드

@dataclass
class ConversationState:
    """대화 상태 관리"""
    user_id: int
    conversation_id: int
    current_stage: MarketingStage = MarketingStage.INITIAL
    current_mode: ConversationMode = ConversationMode.QUESTIONING
    business_type: str = "일반"
    collected_info: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    stage_progress: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    # 🆕 사용자 응답 패턴 추적
    negative_response_count: int = 0
    last_negative_response: Optional[str] = None
    suggestion_attempts: int = 0
    user_engagement_level: str = "high"  # high, medium, low
    
    # 🆕 컨텐츠 제작 관련 상태
    current_content_session: Optional[Dict[str, Any]] = None
    content_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # 🆕 포스팅 관련 상태
    awaiting_posting_confirmation: bool = False
    awaiting_scheduling_time: bool = False
    current_content_for_posting: Optional[Dict[str, Any]] = None
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """메시지 추가"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "stage": self.current_stage.value,
            "mode": self.current_mode.value
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
    
    # 🆕 부정적 응답 추적
    def record_negative_response(self, response: str):
        """부정적 응답 기록"""
        self.negative_response_count += 1
        self.last_negative_response = response
        
        # 참여도 조정
        if self.negative_response_count >= 2:
            self.user_engagement_level = "low"
        elif self.negative_response_count >= 1:
            self.user_engagement_level = "medium"
    
    def reset_negative_responses(self):
        """부정적 응답 카운터 리셋"""
        self.negative_response_count = 0
        self.last_negative_response = None
        self.user_engagement_level = "high"
    
    def should_switch_to_suggestion_mode(self) -> bool:
        """제안 모드로 전환해야 하는지 판단"""
        return (self.negative_response_count >= 2 or 
                self.user_engagement_level == "low" or
                self.suggestion_attempts < 3)
    
    def switch_to_suggestion_mode(self):
        """제안 모드로 전환"""
        self.current_mode = ConversationMode.SUGGESTING
        self.suggestion_attempts += 1
    
    def has_sufficient_info_for_suggestions(self) -> bool:
        """제안을 위한 충분한 정보가 있는지 확인"""
        # 최소한의 정보만 있어도 제안 가능
        return (self.business_type != "일반" or 
                self.get_info('product') or 
                self.get_info('business_type') or
                self.get_info('main_goal') or
                len(self.collected_info) > 0)
    
    # 기존 메서드들...
    def start_content_session(self, content_type: str, initial_request: str):
        """컨텐츠 제작 세션 시작"""
        session_data = {
            "content_type": content_type,
            "initial_request": initial_request,
            "created_at": datetime.now().isoformat(),
            "iteration_count": 1,
            "last_content": None,
            "context_info": {
                "business_type": self.business_type,
                "keywords": self.get_info('keywords'),
                "trend_data": self.get_info('trend_data'),
                "product": self.get_info('product'),
                "target_audience": self.get_info('target_audience'),
                "main_goal": self.get_info('main_goal')
            }
        }
        self.current_content_session = session_data
        self.current_mode = ConversationMode.CONTENT_CREATION
        logger.info(f"컨텐츠 세션 시작: {content_type}, 컨텍스트 정보 포함")
    
    def update_content_session(self, new_content: str, user_feedback: str = None):
        """컨텐츠 제작 세션 업데이트"""
        if self.current_content_session:
            self.current_content_session["last_content"] = new_content
            self.current_content_session["iteration_count"] += 1
            if user_feedback:
                self.current_content_session["last_feedback"] = user_feedback
            logger.info(f"컨텐츠 세션 업데이트: 반복 {self.current_content_session['iteration_count']}회")
    
    def end_content_session(self):
        """컨텐츠 제작 세션 종료"""
        if self.current_content_session:
            self.content_history.append(self.current_content_session.copy())
            self.current_content_session = None
            self.current_mode = ConversationMode.SUGGESTING
            logger.info("컨텐츠 세션 종료")
    
    def is_in_content_creation(self) -> bool:
        """컨텐츠 제작 단계 여부"""
        return self.current_stage == MarketingStage.CONTENT_CREATION and self.current_content_session is not None
    
    # 포스팅 관련 메서드들 (기존 유지)
    def start_posting_confirmation(self, content_data: Dict[str, Any]):
        """포스팅 확인 단계 시작"""
        self.awaiting_posting_confirmation = True
        self.current_content_for_posting = content_data
        logger.info(f"포스팅 확인 단계 시작: {content_data.get('type', 'unknown')}")
    
    def confirm_posting_and_request_schedule(self):
        """포스팅 확인 후 스케줄 입력 요청"""
        self.awaiting_posting_confirmation = False
        self.awaiting_scheduling_time = True
        logger.info("포스팅 확인됨, 스케줄 입력 대기 중")
    
    def complete_posting_process(self):
        """포스팅 프로세스 완료"""
        self.awaiting_posting_confirmation = False
        self.awaiting_scheduling_time = False
        self.current_content_for_posting = None
        logger.info("포스팅 프로세스 완료")
    
    def cancel_posting_process(self):
        """포스팅 프로세스 취소"""
        self.awaiting_posting_confirmation = False
        self.awaiting_scheduling_time = False
        self.current_content_for_posting = None
        logger.info("포스팅 프로세스 취소됨")
    
    def is_awaiting_posting_response(self) -> bool:
        """포스팅 관련 응답 대기 중인지 확인"""
        return self.awaiting_posting_confirmation or self.awaiting_scheduling_time
    
    def get_completion_rate(self) -> float:
        """전체 완료율 계산"""
        required_fields = ["business_type", "product", "main_goal", "target_audience", "budget", "channels"]
        completed_fields = sum(1 for field in required_fields if self.get_info(field))
        return completed_fields / len(required_fields)
    
    def get_missing_info(self, for_content_creation: bool = False) -> List[str]:
        if for_content_creation:
            # 컨텐츠 제작 시에는 키워드나 트렌드 데이터가 있으면 최소 정보만 요구
            has_keywords_or_trends = self.get_info('keywords') or self.get_info('trend_data')
            if has_keywords_or_trends:
                essential_fields = ["business_type", "product"]
                missing = [field for field in essential_fields if not self.get_info(field) and (field != "business_type" or self.business_type == "일반")]
                return missing if len(missing) == len(essential_fields) else []
        
        required_fields = ["business_type", "product", "main_goal", "target_audience", "budget", "channels", "pain_points"]
        return [field for field in required_fields if not self.get_info(field)]
    
    def get_context_based_missing_info(self) -> Dict[str, Any]:
        """🆕 컨텍스트 기반 부족한 정보 분석"""
        missing_info = self.get_missing_info()
        
        # 단계별 우선순위 정보 정의
        stage_priorities = {
            MarketingStage.GOAL: ["main_goal", "business_type", "product"],
            MarketingStage.TARGET: ["target_audience", "main_goal", "product"],
            MarketingStage.STRATEGY: ["budget", "channels", "target_audience"],
            MarketingStage.EXECUTION: ["channels", "budget", "pain_points"],
            MarketingStage.CONTENT_CREATION: ["product", "target_audience", "main_goal"]
        }
        
        current_priorities = stage_priorities.get(self.current_stage, [])
        
        # 우선순위가 높은 부족한 정보 필터링
        priority_missing = [field for field in current_priorities if field in missing_info]
        
        return {
            "total_missing": missing_info,
            "priority_missing": priority_missing,
            "completion_rate": self.get_completion_rate(),
            "current_stage": self.current_stage.value,
            "can_proceed": len(priority_missing) <= 1,  # 우선순위 정보 1개 이하면 진행 가능
            "suggested_focus": priority_missing[0] if priority_missing else None
        }

    def get_conversation_context(self) -> str:
        """대화 컨텍스트 요약"""
        context_parts = []
        
        # 기본 정보
        if self.business_type != "일반":
            context_parts.append(f"업종: {self.business_type}")
        
        # 사용자 참여도 정보
        context_parts.append(f"참여도: {self.user_engagement_level}")
        context_parts.append(f"대화 모드: {self.current_mode.value}")
        
        if self.negative_response_count > 0:
            context_parts.append(f"부정적 응답 횟수: {self.negative_response_count}")
        
        # 수집된 정보 요약
        key_info = {}
        special_info = {}
        
        for key, info in self.collected_info.items():
            if key in ['keywords', 'trend_data']:
                special_info[key] = info["value"]
            else:
                key_info[key] = info["value"]
        
        if special_info:
            context_parts.append(f"키워드/트렌드 데이터: {json.dumps(special_info, ensure_ascii=False)}")
        
        if key_info:
            context_parts.append(f"기타 수집된 정보: {json.dumps(key_info, ensure_ascii=False)}")
        
        # 최근 대화 6개
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
    """🆕 개선된 대화 관리자 - 질문 반복 방지, 맥락 이해, 친밀감 강화"""
    
    def __init__(self):
        from config import config
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL
        self.temperature = config.TEMPERATURE
        self.conversations: Dict[int, ConversationState] = {}
        
        # LLM 프롬프트 초기화
        self._init_llm_prompts()
        logger.info("🆕 개선된 ConversationManager 초기화 완료")
    
    def _init_llm_prompts(self):
        """🆕 개선된 LLM 프롬프트 초기화"""
        
        # 🆕 부정적 응답 감지 프롬프트
        self.negative_response_detection_prompt = """사용자의 응답이 부정적이거나 정보 제공을 거부하는 내용인지 분석해주세요.

분석 대상:
- "몰라", "모르겠어", "잘 모르겠어"
- "니가 알려줘", "당신이 말해줘", "추천해줘"
- "잘 모르겠는데", "확실하지 않아"
- "그냥", "아무거나", "상관없어"
- "별로", "싫어", "안 좋아"

다음 형식으로 답변해주세요:
{
    "is_negative": true/false,
    "type": "no_knowledge|request_suggestion|indifferent|rejection|neutral",
    "confidence": 0.0-1.0,
    "suggested_action": "switch_to_suggestion|continue_questioning|provide_options"
}"""

        # 🆕 제안 모드 응답 생성 프롬프트
        self.suggestion_mode_prompt = """당신은 친근하고 전문적인 마케팅 컨설턴트입니다. 
사용자가 정보를 제공하기 어려워하거나 모른다고 할 때, 직접적인 제안과 추천을 제공해주세요.

## 응답 가이드라인:
1. **공감과 이해**: 사용자가 모르는 것을 자연스럽게 받아들이기
2. **즉시 제안**: 질문 대신 구체적인 아이디어나 전략 제시
3. **개인화**: 수집된 정보를 최대한 활용
4. **실용성**: 바로 적용 가능한 실질적 조언
5. **친근한 톤**: 상담사처럼 따뜻하고 이해심 있는 말투

## 응답 스타일:
- "그럴 수 있어요! 이런 상황에서는 보통..."
- "괜찮습니다. 제가 경험상 추천드리는 건..."
- "이해해요. 그럼 이런 아이디어는 어떠세요?"
- "많은 분들이 비슷하게 고민하시는데, 보통 이렇게 시작하시더라고요..."

## 제안 유형:
- **맞춤형 전략**: 업종별 특화 전략
- **구체적 아이디어**: 실행 가능한 마케팅 방법
- **성공 사례**: 비슷한 업종의 성공 사례
- **단계적 가이드**: 차근차근 따라할 수 있는 방법

응답은 자연스러운 문단으로 작성하되, 2-4개 문단으로 구성해주세요."""

        # 🆕 싱글턴 완료 판단 프롬프트
        self.singleton_completion_prompt = """사용자의 요청이 한 번의 응답으로 완전히 해결될 수 있는지 판단해주세요.

싱글턴으로 완료 가능한 경우:
- 간단한 마케팅 질문 (예: "SNS 마케팅이 뭐야?")
- 일반적인 조언 요청 (예: "브랜딩 팁 알려줘")
- 특정 개념 설명 (예: "타겟 마케팅 설명해줘")
- 즉시 답변 가능한 정보성 질문

멀티턴이 필요한 경우:
- 맞춤형 전략 수립
- 개인 상황 분석이 필요한 상담
- 컨텐츠 제작 및 피드백
- 단계별 진행이 필요한 복잡한 문제

다음 형식으로 답변해주세요:
{
    "can_complete_as_singleton": true/false,
    "reasoning": "판단 이유",
    "suggested_response_type": "informational|advisory|strategic|conversational"
}"""

        # 🆕 구조화된 응답 생성 프롬프트 (후속 질문 포함)
        self.structured_response_prompt = """
당신은 친근하고 전문적인 마케팅 컨설턴트입니다. 사용자의 상황을 깊이 이해하고 공감하며, 아래 지침에 따라 유용한 조언과 함께 자연스럽게 대화를 이어갈 수 있는 후속 질문 및 실행 아이디어를 제시하세요.

---

### **◆ 답변 작성 원칙:**

1. **공감 및 이해**: 사용자의 고민에 대해 먼저 공감과 이해를 표현하고, 따뜻하면서도 전문적인 어조로 조언을 시작합니다.
2. **핵심 조언 제시**: 사용자의 질문에 대한 핵심적인 조언을 명확하게 전달합니다. 관련성 높은 정보는 한 문단에 응축하여 제공하며, 불필요한 개행은 피합니다.
3. **실행 가능한 아이디어 제안**: "이런 걸 시도해보시면 어떨까요?", "이런 방향도 고려해볼 수 있겠어요."와 같이 자연스럽게 시도할 수 있는 1~2가지 실행 아이디어를 제시합니다.
4. **후속 질문 배치**: **후속 질문은 반드시 답변의 마지막 문단에 배치**하며, 본문 내용과 자연스럽게 연결되도록 작성합니다. "혹시 ~~ 하신 적이 있나요?", "혹시 ~~ 에 대해 더 자세히 알려주실 수 있나요?" 등 개방형 질문을 1~2개 포함합니다.
5. **가독성 및 구조**: 마크다운 헤딩(##), 볼드체(**), 구분선(---), 목록(-) 등을 전략적으로 활용해 답변의 주요 내용을 시각적으로 강조하고 구조화합니다. 정보의 밀도를 높여 한눈에 파악할 수 있게 작성합니다.

---

### **◆ 질문 생성 세부 원칙:**

- **타이밍**: 정보가 부족한 경우 보편적 질문(예: "어떤 제품/서비스를 홍보하시나요?")을 마지막 문단에서 자연스럽게 던집니다.
- **맥락 적합성**: 질문은 앞선 조언과 유기적으로 연결되어야 하며, 독립된 질문 목록처럼 보이지 않게 합니다.
- **실용성 및 유도성**: 답변하기 쉬우면서 다음 컨설팅 단계로 이어질 수 있도록 설계합니다.
- **다양성**: 개방형과 선택형 질문을 적절히 혼합합니다.

---

### **◆ 예시 답변 스타일 (참고):**

**사용자:** "저희 제품 마케팅을 어떻게 해야 할지 모르겠어요."

**AI 답변 스타일:**  
"마케팅 방향을 잡는 게 처음엔 막막하게 느껴질 수 있죠. 충분히 공감합니다! 하지만 걱정 마세요. 함께 차근차근 방향을 찾아나가면 분명 좋은 결과를 만들 수 있을 거예요.  
우선, 우리 제품이 고객에게 주는 **핵심 가치**를 명확히 정의하고 그 가치를 고객의 언어로 표현해보는 연습부터 해보시면 좋겠어요.  
혹시 **현재 어떤 제품이나 서비스를 홍보하고 계신지**, 그리고 **어떤 고객층을 주요 타겟으로 설정하고 있는지** 알려주실 수 있을까요?"
"""

        # 🆕 개선된 응답 생성 프롬프트 (친밀감 강화) - 백업용
        self.enhanced_response_prompt = """당신은 친근하고 따뜻한 마케팅 전문가입니다. 사용자와 자연스럽고 개인적인 대화를 나누며 도움을 주세요.

## 친밀감 강화 가이드라인:
1. **개인적 경험 공유**: "저도 비슷한 경험이 있어서 이해해요"
2. **공감적 표현**: "정말 어려우시겠어요", "그런 고민 많이 하시죠"
3. **격려와 지지**: "충분히 가능하세요", "잘 하고 계시는 것 같아요"
4. **자연스러운 말투**: 딱딱한 표현보다는 일상적이고 편안한 말투
5. **맞춤형 호칭**: 상황에 따라 "사장님", "대표님", "크리에이터님" 등

## 톤 다양성:
- **격려형**: "정말 좋은 아이디어네요! 이런 점이 특히 인상적이에요..."
- **공감형**: "아, 그런 어려움이 있으셨군요. 많은 분들이 비슷하게 겪으시는 부분이에요..."
- **전문가형**: "업계 경험상 이런 경우에는..."
- **친구형**: "개인적으로 추천드리고 싶은 건..."

## 응답 구조:
1. **공감/인사**: 사용자 상황에 대한 이해와 공감
2. **개인화된 조언**: 수집된 정보를 활용한 맞춤형 제안
3. **구체적 방법**: 실행 가능한 단계별 가이드
4. **격려와 동행**: 함께 해결해나간다는 느낌

매번 다른 표현과 접근으로 응답하되, 항상 따뜻하고 전문적인 톤을 유지해주세요."""

        # 기존 프롬프트들 (개선)
        self.intent_analysis_prompt = """당신은 마케팅 상담에서 사용자의 의도와 정보를 분석하는 전문가입니다.

사용자의 메시지를 분석하여 다음 정보를 JSON 형태로 추출해주세요:

{
    "intent": {
        "primary": "정보_요청|목표_설정|타겟_분석|전략_기획|콘텐츠_생성|콘텐츠_수정|일반_질문",
        "confidence": 0.0-1.0,
        "description": "의도 설명",
        "topic":"blog_marketing|content_marketing|conversion_optimization|digital_advertising|email_marketing|influencer_marketing|local_marketing|marketing_automation|marketing_fundamentals|marketing_metrics|personal_branding|social_media_marketing|viral_marketing"
    },
    "extracted_info": {
        "business_type": "추출된 업종 (없으면 null)",
        "product": "판매 제품/서비스 정보 (없으면 null)",
        "main_goal": "주요 목표 (없으면 null)",
        "target_audience": "타겟 고객 정보 (없으면 null)",
        "budget": "예산 정보 (없으면 null)",
        "channels": "선호 채널 (없으면 null)",
        "pain_points": "고민거리 (없으면 null)"
    },
    "stage_assessment": {
        "current_stage_complete": true/false,
        "ready_for_next": true/false,
        "suggested_next_stage": "initial|goal|target|strategy|execution|content_creation|completed"
    },
    "content_intent": {
        "is_content_request": true/false,
        "content_type": "instagram|blog|strategy|campaign"
    },
    "user_sentiment": {
        "engagement_level": "high|medium|low",
        "frustration_level": "none|low|medium|high",
        "needs_encouragement": true/false
    }
}"""

        # 🆕 컨텐츠 피드백 분석 프롬프트  
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
    
    async def _call_llm(self, prompt: str, user_input: str, context: str = "") -> Dict[str, Any]:
        """LLM 호출 및 응답 파싱"""
        try:
            full_prompt = f"""
{prompt}

현재 상황:
{context}

사용자 입력:
"{user_input}"
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": full_prompt}
                ],
                temperature=self.temperature,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            
            try:
                # JSON 블록 추출 시도
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                elif "{" in content and "}" in content:
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    json_content = content[json_start:json_end]
                else:
                    return {"raw_response": content}
                
                return json.loads(json_content)
                
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 원문 반환
                return {"raw_response": content}
                
        except Exception as e:
            logger.error(f"LLM 호출 실패: {e}")
            return {"error": str(e)}
    
    # 🆕 부정적 응답 감지
    async def detect_negative_response(self, user_input: str, conversation: ConversationState) -> Dict[str, Any]:
        """부정적 응답 감지"""
        context = f"""
        현재 대화 모드: {conversation.current_mode.value}
        부정적 응답 횟수: {conversation.negative_response_count}
        사용자 참여도: {conversation.user_engagement_level}
        """
        
        result = await self._call_llm(self.negative_response_detection_prompt, user_input, context)
        
        if "error" in result:
            return {"is_negative": False, "type": "neutral", "confidence": 0.0}
        
        return result
    
    # 🆕 싱글턴 완료 가능 여부 판단
    async def can_complete_as_singleton(self, user_input: str, conversation: ConversationState) -> bool:
        """싱글턴으로 완료 가능한지 판단"""
        context = f"""
        현재 단계: {conversation.current_stage.value}
        수집된 정보 수: {len(conversation.collected_info)}
        완료율: {conversation.get_completion_rate():.1%}
        """
        
        result = await self._call_llm(self.singleton_completion_prompt, user_input, context)
        
        if "error" in result:
            return False
        
        return result.get("can_complete_as_singleton", False)
    
    # 🆕 제안 모드 응답 생성
    async def generate_suggestion_response(self, user_input: str, conversation: ConversationState) -> str:
        """제안 모드 응답 생성 - 질문 대신 직접 제안"""
        context = f"""
        업종: {conversation.business_type}
        수집된 정보: {json.dumps(conversation.collected_info, ensure_ascii=False)}
        부정적 응답: {conversation.last_negative_response}
        사용자 참여도: {conversation.user_engagement_level}
        
        대화 히스토리:
        {conversation.get_conversation_context()}
        """
        
        result = await self._call_llm(self.suggestion_mode_prompt, user_input, context)
        
        if "error" in result:
            # 기본 제안 메시지 (LLM 생성)
            fallback_prompt = f"""사용자가 "{user_input}"라고 했을 때, 마케팅 전문가로서 친근하게 도움을 주는 응답을 생성해주세요. 
            질문하지 말고 직접적인 조언과 제안을 해주세요."""
            
            fallback_result = await self._call_llm(fallback_prompt, "", "")
            return fallback_result.get("raw_response", "그렇다면 제가 몇 가지 아이디어를 제안해드릴게요!")
        
        return result.get("raw_response", result.get("response", ""))
    
    # 🆕 즉시 추천 생성
    async def generate_instant_recommendations(self, conversation: ConversationState) -> str:
        """수집된 정보 기반으로 즉시 추천 생성"""
        context_info = "\n".join(
            [f"- {key}: {info['value']}" for key, info in conversation.collected_info.items()]
        )

        prompt = f"""
        당신은 친근하고 경험이 풍부한 마케팅 전문가입니다.
        다음 정보를 반드시 참고하여 맞춤형 마케팅 전략을 제시하세요.

        [비즈니스 맥락]
        업종: {conversation.business_type}
        완료율: {conversation.get_completion_rate():.1%}

        [수집된 정보]
        {context_info}

        위 정보를 최대한 반영하여, **지금 바로 실행할 수 있는 실용적인 마케팅 전략과 팁**을 작성하세요.
        - 글은 인삿말 없이 본문으로 시작
        - 각 항목은 간결하게, 불필요한 설명은 생략
        - 아래 구조를 따르되 너무 딱딱하지 않게 자연스럽게 작성:
        1. 즉시 시작할 수 있는 마케팅 방법 3가지
        2. 예상 효과와 시작 방법
        3. 성공을 위한 핵심 팁
        4. 마지막 문단에서 자연스럽게 이어질 후속 질문 1~2개 포함
        - 따뜻하고 격려하는 톤 유지
        """
        
        result = await self._call_llm(prompt, "", "")
        return result.get("raw_response", "지금까지의 정보를 바탕으로 맞춤형 전략을 추천해드리겠습니다!")
    
    # 🆕 구조화된 응답 생성 메서드
    async def generate_structured_response(self, user_input: str, conversation: ConversationState) -> Dict[str, Any]:
        """
        구조화된 응답 생성 - 메인 응답 + 후속 질문 + 행동 제안
        """
        try:
            # 컨텍스트 정보 준비
            missing_info_analysis = conversation.get_context_based_missing_info()
            context = f"""
            현재 마케팅 단계: {conversation.current_stage.value}
            대화 모드: {conversation.current_mode.value}
            완료율: {conversation.get_completion_rate():.1%}
            부족한 정보 분석: {json.dumps(missing_info_analysis, ensure_ascii=False)}
            사용자 참여도: {conversation.user_engagement_level}
            업종: {conversation.business_type}
            
            수집된 정보:
            {json.dumps(conversation.collected_info, ensure_ascii=False)}
            
            최근 대화 흐름:
            {conversation.get_conversation_context()}
            """

            result = await self._call_llm(self.structured_response_prompt, user_input, context)
            return result.get("raw_response", "응답 없음")

        except Exception as e:
            self.logger.error(f"[{conversation.conversation_id}] 구조화된 응답 생성 실패: {e}", exc_info=True)
            return {
                "main_response": "죄송합니다, 응답 생성 중 문제가 발생했습니다.",
                "follow_up_questions": [],
                "suggested_actions": [],
                "conversation_direction": "continue_info_gathering"
            }

    
    async def _generate_fallback_follow_up_questions(self, conversation: ConversationState) -> List[str]:
        """백업 후속 질문 생성"""
        missing_info_analysis = conversation.get_context_based_missing_info()
        priority_missing = missing_info_analysis["priority_missing"]
        
        # 단계별 기본 후속 질문
        stage_questions = {
            MarketingStage.GOAL: [
                "어떤 결과를 가장 빠르게 보고 싶으신가요?",
                "현재 가장 큰 마케팅 고민은 무엇인가요?",
                "성공의 기준을 어떻게 정의하시나요?"
            ],
            MarketingStage.TARGET: [
                "주요 고객층의 연령대는 어떻게 되시나요?",
                "고객들이 주로 어떤 채널을 이용하나요?",
                "고객들이 가장 중요하게 생각하는 가치는 무엇일까요?"
            ],
            MarketingStage.STRATEGY: [
                "월 마케팅 예산은 어느 정도 계획하고 계신가요?",
                "어떤 마케팅 채널에 가장 관심이 있으신가요?",
                "경쟁사들은 어떤 전략을 사용하고 있나요?"
            ],
            MarketingStage.EXECUTION: [
                "언제부터 마케팅을 시작하고 싶으신가요?",
                "현재 운영하고 있는 온라인 채널이 있나요?",
                "마케팅 담당자가 따로 있으신가요?"
            ]
        }
        
        default_questions = stage_questions.get(conversation.current_stage, [
            "더 자세히 알고 싶은 부분이 있으신가요?",
            "어떤 도움이 가장 필요하신가요?",
            "다른 궁금한 점은 없으신가요?"
        ])
        
        return default_questions[:3]  # 최대 3개
    
    async def _generate_fallback_actions(self, conversation: ConversationState) -> List[str]:
        """백업 추천 액션 생성"""
        if conversation.current_stage == MarketingStage.GOAL:
            return [
                "마케팅 목표를 구체적으로 정의해보기",
                "타겟 고객 페르소나 만들어보기"
            ]
        elif conversation.current_stage == MarketingStage.TARGET:
            return [
                "고객 설문조사 진행해보기",
                "경쟁사 분석 시작하기"
            ]
        elif conversation.current_stage == MarketingStage.STRATEGY:
            return [
                "마케팅 예산 계획 세우기",
                "채널별 우선순위 정하기"
            ]
        else:
            return [
                "첫 번째 마케팅 캠페인 기획하기",
                "성과 측정 방법 정하기"
            ]

    # 🆕 개선된 메인 응답 생성 메서드
    async def generate_response_with_context(self, user_input: str, conversation: ConversationState) -> str:
        """🆕 개선된 맥락적 응답 생성 - 질문 반복 방지, 친밀감 강화"""
        conversation.add_message("user", user_input)
        logger.info(f"[{conversation.conversation_id}] 사용자 입력: {user_input}")

        try:
            # 🆕 포스팅 관련 응답 처리 우선
            if conversation.is_awaiting_posting_response():
                return await self._handle_posting_response(user_input, conversation)
            
            # 🆕 컨텐츠 제작 세션 중인지 확인
            if conversation.is_in_content_creation():
                return await self._handle_content_creation_session(user_input, conversation)
            
            # # 🆕 1. 싱글턴 완료 가능 여부 확인
            # if await self.can_complete_as_singleton(user_input, conversation):
            #     # 즉시 완료 가능한 경우 바로 응답 생성
            #     response = await self.generate_enhanced_response(user_input, conversation, is_singleton=True)
            #     conversation.add_message("assistant", response)
            #     return response
            
            # 🆕 2. 부정적 응답 감지
            negative_analysis = await self.detect_negative_response(user_input, conversation)
            if negative_analysis.get("is_negative", False):
                print("부정적 응답 감지")
                conversation.record_negative_response(user_input)
                
                # 제안 모드로 전환
                if conversation.should_switch_to_suggestion_mode():
                    conversation.switch_to_suggestion_mode()
                    
                    # 제안 모드 응답 생성
                    if conversation.has_sufficient_info_for_suggestions():
                        response = await self.generate_instant_recommendations(conversation)
                    else:
                        response = await self.generate_suggestion_response(user_input, conversation)
                    
                    conversation.add_message("assistant", response)
                    return response
            else:
                # 긍정적 응답이면 카운터 리셋
                conversation.reset_negative_responses()
            
            # 3. 사용자 의도 분석
            intent_analysis = await self.analyze_user_intent_with_llm(user_input, conversation)
            logger.info(f"[{conversation.conversation_id}] 의도 분석: {intent_analysis.get('intent', {}).get('primary', 'unknown')}")

            # 추출된 정보 저장
            extracted_info = intent_analysis.get("extracted_info", {})
            for key, value in extracted_info.items():
                if value:
                    conversation.add_info(key, value, "llm_extracted")
                    if key == "business_type" and value != "일반":
                        conversation.business_type = value
      
            primary_intent = intent_analysis.get('intent', {}).get('primary', '')
            topic = intent_analysis.get('intent', {}).get('topic', '')
            print ("primary_intent:"+primary_intent)
            print ("topic:"+topic)
            print(f"extracted_info:{extracted_info}")     
            
            # 🆕 4. 컨텐츠 생성 요청 감지
            content_intent = intent_analysis.get("content_intent", {})
            has_basic_info = (conversation.business_type and conversation.business_type != "일반") or conversation.get_info('product') or conversation.get_info('business_type')
            has_keywords_or_trends = conversation.get_info('keywords') or conversation.get_info('trend_data')
            
            if content_intent.get("is_content_request") and (has_basic_info or has_keywords_or_trends):
                print("컨텐츠생성요청")
                conversation.current_stage = MarketingStage.CONTENT_CREATION
                conversation.start_content_session(
                    content_intent.get("content_type", "general"),
                    user_input
                )
                return "TRIGGER_CONTENT_GENERATION"

            # # 🆕 5. 제안 모드인 경우 질문 대신 제안 생성
            # if conversation.current_mode == ConversationMode.SUGGESTING:
            #     response = await self.generate_instant_recommendations(conversation)
            #     conversation.add_message("assistant", response)
            #     return response
            
            # 6. 일반적인 개선된 응답 생성
            # 🆕 구조화된 응답 생성
            if conversation.get_completion_rate() > 0.3:
                print("즉시제안")
                conversation.switch_to_suggestion_mode()
                response = await self.generate_instant_recommendations(conversation)
                conversation.add_message("assistant", response)
                return response
            else:
                print("일반")
                # 구조화된 응답 생성 (메인 응답 + 후속 질문)
                structured_response = await self.generate_structured_response(user_input, conversation)
                conversation.add_message("assistant", structured_response)
                return f"STRUCTURED_RESPONSE:{structured_response}"

        except Exception as e:
            logger.error(f"[{conversation.conversation_id}] 응답 생성 중 오류: {e}", exc_info=True)
            # 오류 시에도 LLM으로 응답 생성
            error_prompt = "사용자와의 대화 중 기술적 문제가 발생했을 때 친근하게 사과하고 다시 시도를 요청하는 메시지를 생성해주세요."
            error_result = await self._call_llm(error_prompt, "", "")
            return error_result.get("raw_response", "죄송합니다. 잠시 문제가 발생했네요. 다시 한 번 말씀해주시면 도움을 드리겠습니다!")
    
    # 🆕 개선된 응답 생성 (친밀감 강화)
    async def generate_enhanced_response(self, user_input: str, conversation: ConversationState, 
                                       topic: str = "", is_singleton: bool = False) -> str:
        """친밀감과 개인화가 강화된 응답 생성"""
        context = f"""
        업종: {conversation.business_type}
        완료율: {conversation.get_completion_rate():.1%}
        참여도: {conversation.user_engagement_level}
        수집된 정보: {json.dumps(conversation.collected_info, ensure_ascii=False)}
        싱글턴 완료: {is_singleton}
        토픽: {topic}
        
        대화 컨텍스트:
        {conversation.get_conversation_context()}
        """
        
        result = await self._call_llm(self.enhanced_response_prompt, user_input, context)
        return result.get("raw_response", result.get("response", ""))
    
    
    # 포스팅 및 컨텐츠 세션 관련 메서드들 (기존 유지하되 LLM 기반으로 개선)
    async def _handle_posting_response(self, user_input: str, conversation: ConversationState) -> str:
        """포스팅 관련 응답 처리 - LLM 기반"""
        user_input_lower = user_input.lower().strip()
        
        if conversation.awaiting_posting_confirmation:
            if any(word in user_input_lower for word in ["네", "예", "포스팅", "posting", "업로드", "게시"]):
                conversation.confirm_posting_and_request_schedule()
                
                # LLM으로 스케줄 요청 메시지 생성
                prompt = "사용자가 포스팅을 확인했을 때, 친근하게 언제 포스팅할지 시간을 물어보는 메시지를 생성해주세요. 다양한 시간 입력 예시도 포함해주세요."
                result = await self._call_llm(prompt, "", "")
                return result.get("raw_response", "포스팅 일정을 알려주세요!")
            else:
                conversation.cancel_posting_process()
                conversation.end_content_session()
                conversation.current_stage = MarketingStage.COMPLETED
                
                # LLM으로 완료 메시지 생성
                prompt = "포스팅을 취소했을 때 자연스럽게 컨텐츠 제작 완료를 알리고 추가 도움을 제안하는 메시지를 생성해주세요."
                result = await self._call_llm(prompt, "", "")
                return result.get("raw_response", "컨텐츠 제작이 완료되었습니다!")
        
        elif conversation.awaiting_scheduling_time:
            try:
                scheduled_at = await self._parse_schedule_time(user_input)
                
                if scheduled_at:
                    return f"TRIGGER_AUTOMATION_TASK:{scheduled_at.isoformat()}|자동화 예약이 완료되었습니다!"
                else:
                    # LLM으로 시간 재입력 요청 메시지 생성
                    prompt = "시간 형식을 인식할 수 없을 때 친근하게 다시 입력을 요청하는 메시지를 생성해주세요."
                    result = await self._call_llm(prompt, "", "")
                    return result.get("raw_response", "시간 형식을 다시 확인해주세요.")
            except Exception as e:
                logger.error(f"스케줄 파싱 오류: {e}")
                prompt = "시간 처리 중 오류가 발생했을 때 사과하고 다시 시도를 요청하는 메시지를 생성해주세요."
                result = await self._call_llm(prompt, "", "")
                return result.get("raw_response", "시간 처리 중 문제가 발생했습니다. 다시 시도해주세요.")
        
        return "예상치 못한 포스팅 상태입니다."
    
    async def _handle_content_creation_session(self, user_input: str, conversation: ConversationState, is_initial: bool = False) -> str:
        """컨텐츠 제작 세션 처리 - LLM 기반"""
        if is_initial:
            # LLM으로 컨텐츠 제작 시작 메시지 생성
            prompt = "컨텐츠 제작을 시작한다는 것을 친근하고 전문적으로 알리는 메시지를 생성해주세요."
            result = await self._call_llm(prompt, "", "")
            return result.get("raw_response", "컨텐츠 제작을 시작합니다!")
        else:
            # 피드백 처리
            feedback_analysis = await self.handle_content_feedback_with_llm(user_input, conversation)
            
            request_type = feedback_analysis.get("request_type", "feedback")
            
            if request_type == "modify":
                # LLM으로 수정 메시지 생성
                prompt = "사용자가 컨텐츠 수정을 요청했을 때 친근하게 수정하겠다고 알리는 메시지를 생성해주세요."
                result = await self._call_llm(prompt, "", "")
                conversation.update_content_session("수정 중...", user_input)
                return "TRIGGER_CONTENT_MODIFICATION:" + result.get("raw_response", "컨텐츠를 수정하겠습니다!")
                
            elif request_type == "regenerate":
                prompt = "새로운 컨텐츠를 생성하겠다고 친근하게 알리는 메시지를 생성해주세요."
                result = await self._call_llm(prompt, "", "")
                conversation.update_content_session("재생성 중...", user_input)
                return "TRIGGER_CONTENT_REGENERATION:" + result.get("raw_response", "새로운 컨텐츠를 생성하겠습니다!")
                
            elif request_type == "approval":
                if conversation.current_content_for_posting:
                    # LLM으로 포스팅 확인 메시지 생성
                    prompt = "사용자가 컨텐츠를 마음에 들어할 때 포스팅 여부를 친근하게 묻는 메시지를 생성해주세요."
                    result = await self._call_llm(prompt, "", "")
                    conversation.start_posting_confirmation(conversation.current_content_for_posting)
                    return result.get("raw_response", "포스팅하시겠습니까?")
                else:
                    # LLM으로 완료 메시지 생성
                    prompt = "컨텐츠 제작이 완료되었을 때 추가 도움을 제안하는 메시지를 생성해주세요."
                    result = await self._call_llm(prompt, "", "")
                    conversation.end_content_session()
                    conversation.current_stage = MarketingStage.COMPLETED
                    return result.get("raw_response", "컨텐츠 제작이 완료되었습니다!")
            else:
                # LLM으로 피드백 요청 메시지 생성
                prompt = "사용자의 피드백에 감사를 표하고 더 구체적인 수정 방향을 묻는 메시지를 생성해주세요."
                result = await self._call_llm(prompt, "", "")
                return result.get("raw_response", "피드백 감사합니다!")
    
    # 기존 메서드들 유지...
    async def analyze_user_intent_with_llm(self, user_input: str, conversation: ConversationState) -> Dict[str, Any]:
        """LLM 기반 사용자 의도 분석"""
        context = f"""
        현재 단계: {conversation.current_stage.value}
        현재 모드: {conversation.current_mode.value}
        업종: {conversation.business_type}
        완료율: {conversation.get_completion_rate():.1%}
        사용자 참여도: {conversation.user_engagement_level}
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
                "content_intent": {"is_content_request": False, "content_type": ""},
                "user_sentiment": {"engagement_level": "medium", "frustration_level": "none", "needs_encouragement": False}
            }
        
        return result

    async def handle_content_feedback_with_llm(self, user_input: str, conversation: ConversationState) -> Dict[str, Any]:
        """컨텐츠 피드백 처리"""
        context = f"""
        현재 컨텐츠 세션: {conversation.current_content_session}
        이전 컨텐츠: {conversation.current_content_session.get('last_content', '') if conversation.current_content_session else ''}
        반복 횟수: {conversation.current_content_session.get('iteration_count', 0) if conversation.current_content_session else 0}
        """
        
        result = await self._call_llm(self.content_feedback_prompt, user_input, context)
        
        if "error" in result:
            return {
                "request_type": "feedback",
                "specific_changes": [],
                "content_direction": {},
                "action_needed": {"type": "provide_feedback", "priority": "medium"}
            }
        
        return result

    async def _parse_schedule_time(self, user_input: str) -> Optional[datetime]:
        """사용자 입력에서 시간 파싱 - LLM 기반"""
        user_input_lower = user_input.lower().strip()
        
        # 지금 바로
        if any(word in user_input_lower for word in ["지금", "바로", "now", "immediately"]):
            return datetime.now()
        
        # LLM을 사용한 시간 파싱
        try:
            time_parsing_prompt = f"""다음 사용자 입력에서 날짜와 시간을 추출하여 ISO 8601 형식으로 반환해주세요.
            
사용자 입력: "{user_input}"
현재 시간: {datetime.now().isoformat()}

다음 형식으로만 응답해주세요:
- 성공: "2024-01-15T14:30:00" (정확한 ISO 8601 형식)
- 실패: "INVALID"

추가 설명 없이 오직 날짜/시간 또는 "INVALID"만 반환하세요."""
            
            result = await self._call_llm("당신은 시간 파싱 전문가입니다.", time_parsing_prompt)
            
            if isinstance(result, dict) and "raw_response" in result:
                time_str = result["raw_response"].strip()
            else:
                time_str = str(result).strip()
            
            if time_str != "INVALID" and "T" in time_str:
                return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                
        except Exception as e:
            logger.warning(f"시간 파싱 실패: {e}")
        
        return None
    
    # 대화 관리 관련 메서드들 (기존 유지)
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
    
    def get_conversation_summary(self, conversation_id: int) -> Dict[str, Any]:
        """대화 요약 정보"""
        if conversation_id not in self.conversations:
            return {"error": "대화를 찾을 수 없습니다"}
        
        conversation = self.conversations[conversation_id]
        
        return {
            "conversation_id": conversation_id,
            "user_id": conversation.user_id,
            "current_stage": conversation.current_stage.value,
            "current_mode": conversation.current_mode.value,
            "business_type": conversation.business_type,
            "completion_rate": conversation.get_completion_rate(),
            "collected_info_count": len(conversation.collected_info),
            "message_count": len(conversation.conversation_history),
            "created_at": conversation.created_at.isoformat(),
            "last_activity": conversation.last_activity.isoformat(),
            "user_engagement_level": conversation.user_engagement_level,
            "negative_response_count": conversation.negative_response_count,
            "in_content_creation": conversation.is_in_content_creation(),
            # "features": ["improved_context_understanding", "negative_response_handling", "suggestion_mode", "singleton_completion", "no_hardcoding"]
            "features": ["improved_context_understanding", "negative_response_handling", "suggestion_mode", "no_hardcoding"]
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
    
    def should_use_structured_response(self, conversation: ConversationState) -> bool:
        """🆕 구조화된 응답 사용 여부 판단"""
        # 컨텐츠 제작 단계이거나 제안 모드에서는 구조화된 응답 사용하지 않음
        if (conversation.current_stage == MarketingStage.CONTENT_CREATION or 
            conversation.current_mode == ConversationMode.SUGGESTING or
            conversation.is_awaiting_posting_response()):
            return False
        
        # 완료율이 높으면 구조화된 응답 사용하지 않음
        if conversation.get_completion_rate() > 0.7:
            return False
        
        # 정보 수집이 필요한 경우에만 구조화된 응답 사용
        return conversation.current_mode == ConversationMode.QUESTIONING
    
    async def get_welcome_message_with_llm(self, conversation: ConversationState) -> Dict[str, Any]:
        """🆕 LLM 기반 구조화된 환영 메시지 생성"""
        welcome_prompt = """사용자가 마케팅 상담을 시작할 때 사용할 환영 메시지를 다음 JSON 형태로 생성해주세요.

{
  "main_response": "친근하고 전문적인 환영 메시지 (이모지와 마크다운 활용)",
  "follow_up_questions": [
    "자연스러운 시작 질문 1 (업종 관련)",
    "자연스러운 시작 질문 2 (목표 관련)",
    "자연스러운 시작 질문 3 (현재 상황 관련)"
  ],
  "suggested_actions": [
    "바로 시작할 수 있는 첫 번째 액션",
    "바로 시작할 수 있는 두 번째 액션"
  ],
  "conversation_direction": "continue_info_gathering"
}

요구사항:
1. 친근하고 전문적인 톤
2. 마케팅 전문가로서의 신뢰성 전달
3. 개선된 기능들 소개 (질문 반복 방지, 맞춤형 제안, 친밀한 대화)
4. 사용자의 참여를 자연스럽게 유도
5. 이모지와 마크다운 활용

새로운 특징:
- 사용자가 모를 때 직접 제안 및 추천
- 질문 반복 방지
- 친밀하고 자연스러운 대화
- 즉시 답변 가능한 것은 바로 완료
- 후속 질문으로 대화 흐름 자연스럽게 이어가기

반드시 유효한 JSON 형태로 응답해주세요."""
        
        result = await self._call_llm(welcome_prompt, "환영 메시지 생성 요청", "")
        
        # JSON 파싱 실패 시 기본 구조 반환
        if "error" in result or "main_response" not in result:
            return {
                "main_response": "🎯 **안녕하세요! 마케팅 전문 컨설턴트입니다** 🎯\n\n비즈니스 성장을 위한 맞춤형 마케팅 전략을 함께 만들어보아요! 어떤 도움이 필요하신가요?",
                "follow_up_questions": [
                    "어떤 업종에서 사업을 하고 계신가요?",
                    "현재 가장 큰 마케팅 고민은 무엇인가요?",
                    "어떤 결과를 가장 빠르게 보고 싶으신가요?"
                ],
                "suggested_actions": [
                    "비즈니스 현황 진단받기",
                    "맞춤형 마케팅 전략 상담받기"
                ],
                "conversation_direction": "continue_info_gathering"
            }
        
        return result