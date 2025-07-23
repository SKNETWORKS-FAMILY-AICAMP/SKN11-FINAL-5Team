"""
마케팅 에이전트 의도 분석 모듈 (체계적 상담 감지 강화)
"""

import json
import logging
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from .utils import clean_json_response, create_default_intent_analysis

logger = logging.getLogger(__name__)


class IntentAnalyzer:
    """LLM 기반 의도 분석 클래스 (체계적 4단계 상담 감지 강화)"""
    
    def __init__(self):
        self.intent_analysis_system_prompt = self._create_intent_analysis_prompt()
    
    def _create_intent_analysis_prompt(self) -> str:
        """개선된 의도 분석 시스템 프롬프트 - 체계적 상담 감지 강화"""
        return """당신은 마케팅 상담 전문가입니다. 사용자의 입력을 분석하여 최적의 응답 방식을 결정합니다.

**중요**: 마케팅 툴은 사용자가 **명시적으로 분석을 요청**할 때만 사용합니다.

**체계적 4단계 상담 감지 강화**:
다음 표현들이 있으면 **structured_consultation**로 분류:
- "체계적으로", "단계별로", "처음부터", "차근차근"
- "순서대로", "4단계", "전체적으로", "완전히", "컴플리트하게"
- "마케팅 상담 시작", "마케팅 배우고 싶어요", "전략 수립해주세요"
- "전반적인 마케팅", "마케팅 전체", "기초부터 마케팅"

분석 기준:
1. 응답 타입 결정:
- **immediate_answer**: 일반적 마케팅 조언, 방법론, 전략 논의
- **structured_consultation**: 체계적 4단계 상담 시작 요청
- stage_progress: 특정 단계 진행 관련
- flow_control: 대화 제어 (중단/재개/건너뛰기)
- comprehensive: 종합적 전략 수립
- clarification: 추가 정보 필요
- **tool_required**: 마케팅 툴 사용 필요 (매우 제한적)

2. **툴 사용 조건** (매우 엄격):
다음과 같은 **명시적 요청**이 있을 때만 tool_required:

✅ **콘텐츠 생성 요청**:
- "인스타그램 광고 만들어줘", "카피 작성해줘", "인스타 포스트 작성"
- "블로그 글 써줘", "콘텐츠 제작해줘", "제목 추천해줘"

✅ **분석 도구 요청**:
- "키워드 분석해줘", "트렌드 분석 부탁해", "검색량 조사해줘"
- "해시태그 추천해줘", "해시태그 분석 부탁", "인스타 해시태그 찾아줘"

❌ **일반적 질문은 immediate_answer**:
- "마케팅을 어떻게 시작할까요?", "마케팅 전략은?", "인스타그램 마케팅 방법은?"
- "브랜드 인지도를 높이려면?", "고객 유치 방법은?", "바이럴 마케팅이란?"

3. 사용자 의도:
- 주요 목적과 정보 필요도
- 긴급도와 구체성 수준
- 진행 방식 선호도

4. 컨텍스트 활용:
- 기존 정보 활용 필요성
- 개인화 수준
- 업종별 맞춤화

5. **콘텐츠 생성 요청 감지**:
사용자가 구체적으로 콘텐츠 제작을 요청하면:
- tool_required + content_generation으로 분류
- 현재 단계가 4단계가 아니면 auto_stage_jump: true
- stage_preference: "4" 설정

6. **기본 원칙**: 확실하지 않으면 immediate_answer로 처리
- 사용자가 분석을 명시적으로 요청하지 않았다면 일반 조언 제공
- 마케팅 전략, 방법론, 제안은 모두 immediate_answer

응답은 반드시 JSON 형태로 제공하세요."""

    async def analyze_user_intent_with_llm(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """개선된 LLM 기반 사용자 의도 분석"""
        logger.info(f"[단계 로그] 사용자 의도 분석 시작 - 입력: {user_input[:50]}...")
        
        analysis_prompt = f"""현재 마케팅 상담 상황을 분석해주세요.

사용자 입력: "{user_input}"

현재 컨텍스트:
- 대화 모드: {context.get('conversation_mode', 'flexible')}
- 현재 단계: {context.get('current_stage', 'none')}
- 수집된 정보: {json.dumps(context.get('collected_info', {}), ensure_ascii=False, indent=2)}
- 업종: {context.get('business_type', '미확인')}
- 대화 히스토리: {context.get('history_summary', '새 대화')}

**체계적 상담 감지 강화 기준**:
다음 표현이 있으면 **structured_consultation**로 분류:
✅ "체계적으로", "단계별로", "처음부터", "차근차근"
✅ "순서대로", "4단계", "전체적으로", "완전히", "컴플리트하게"
✅ "마케팅 상담 시작", "마케팅 배우고 싶어요", "전략 수립해주세요"
✅ "전반적인 마케팅", "마케팅 전체", "기초부터 마케팅"

**기본 원칙**: 사용자가 **명시적으로 분석이나 제작을 요청**하지 않았다면 **immediate_answer**로 처리하세요.

**예시 분류**:
✅ **immediate_answer** (대부분의 경우):
- "마케팅을 어떻게 시작할까요?", "마케팅 전략은?", "인스타 마케팅 방법은?"
- "마케팅 목표를 어떻게 설정하나요?", "타겟 고객을 어떻게 찾나요?"
- "브랜드 인지도 향상 방법", "고객 유치 전략은?"

✅ **structured_consultation** (체계적 상담 요청):
- "마케팅을 체계적으로 배우고 싶어요"
- "처음부터 마케팅 전략을 수립해주세요"
- "단계별로 마케팅을 배우고 싶습니다"

✅ **tool_required** (명시적 요청만):
- "키워드 분석해줘", "해시태그 추천해줘", "트렌드 분석 부탁해"
- "인스타 포스트 만들어줘", "블로그 글 써줘", "콘텐츠 제작해줘"
- "광고 문구 만들어줘", "카피 작성 부탁", "제목 추천해줘"

다음을 JSON 형태로 분석해주세요:
{{
    "response_type": "immediate_answer|structured_consultation|stage_progress|flow_control|comprehensive|clarification|tool_required",
    "user_intent": {{
        "primary_goal": "사용자의 주요 목적",
        "information_need": "필요한 정보",
        "urgency_level": "high|medium|low",
        "specificity": "general|specific|very_specific"
    }},
    "flow_control": {{
        "wants_immediate": true/false,
        "wants_structured": true/false,
        "stage_preference": "1|2|3|4|any|none",
        "control_command": "pause|resume|skip|restart|next|none",
        "auto_stage_jump": true/false
    }},
    "context_needs": {{
        "use_existing_info": true/false,
        "business_type_detection": "필요시 업종",
        "personalization_level": "high|medium|low"
    }},
    "tool_requirements": {{
        "needs_tool": true/false,
        "tool_type": "trend_analysis|hashtag_analysis|content_generation|keyword_research|none",
        "target_keyword": "분석할 주요 키워드",
        "content_type": "blog|instagram|general",
        "reasoning": "툴 사용 이유",
        "stage_requirement_met": true/false
    }},
    "suggested_action": "추천하는 다음 액션"
}}"""

        try:
            messages = [
                SystemMessage(content=self.intent_analysis_system_prompt),
                HumanMessage(content=analysis_prompt)
            ]
            
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            raw_response = llm.invoke(messages)
            response = str(raw_response.content) if hasattr(raw_response, 'content') else str(raw_response)
            
            # JSON 파싱
            if isinstance(response, str):
                cleaned = clean_json_response(response)
                try:
                    logger.info(f"[정보 추출 결과] 파싱 시작")
                    parsed_result = json.loads(cleaned)
                    
                    # 로그로 분석 결과 확인
                    logger.info(f"[의도 분석] 응답 타입: {parsed_result.get('response_type')}")
                    logger.info(f"[의도 분석] 체계적 진행 선호: {parsed_result.get('flow_control', {}).get('wants_structured')}")
                    logger.info(f"[의도 분석] 툴 필요: {parsed_result.get('tool_requirements', {}).get('needs_tool')}")
                    logger.info(f"[의도 분석] 툴 타입: {parsed_result.get('tool_requirements', {}).get('tool_type')}")
                    
                    return parsed_result
                except json.JSONDecodeError:
                    logger.warning(f"JSON 파싱 실패: {cleaned[:100]}")
                    return create_default_intent_analysis(user_input)
                
            return response
            
        except Exception as e:
            logger.error(f"의도 분석 실패: {e}")
            return create_default_intent_analysis(user_input)

    def detect_business_type_with_llm(self, user_input: str, context: Dict[str, Any]) -> str:
        """LLM 기반 업종 감지"""
        logger.info(f"[단계 로그] 업종 감지 시작 - 현재 컨텍스트: {context.get('business_type', '미확인')}")

        detection_prompt = f"""다음 사용자 입력에서 비즈니스 업종을 감지해주세요.

사용자 입력: "{user_input}"
기존 컨텍스트: {json.dumps(context.get('collected_info', {}), ensure_ascii=False)}

다음 중에서 가장 적합한 업종을 선택하거나 새로운 업종을 제안해주세요:
- 앱 (모바일앱, 게임앱, 생산성앱 등)
- 뷰티 (미용실, 네일샵, 피부관리, 뷰티 플랫폼 등)
- 크리에이터 (유튜브, 인플루언서, 1인 콘텐츠 제작자 등)
- 음식점 (카페, 레스토랑, 배달전문점, 푸드트럭 등)
- 온라인쇼핑몰 (이커머스, 온라인 셀러, 라이브커머스 등)
- 서비스업 (컨설팅, 교육, 헬스케어 등)
- 기타 (신규 업종 또는 융합 업종 등)

업종명만 간단히 답변해주세요. (예: "뷰티", "음식점", "온라인쇼핑몰")"""

        try:
            messages = [
                SystemMessage(content="업종 분류 전문가입니다. 간결하게 업종명만 답변합니다."),
                HumanMessage(content=detection_prompt)
            ]
            
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            raw_response = llm.invoke(messages)
            response = str(raw_response.content) if hasattr(raw_response, 'content') else str(raw_response)
            
            return response.strip() if response else "일반"
            
        except Exception as e:
            logger.error(f"업종 감지 실패: {e}")
            return "일반"
