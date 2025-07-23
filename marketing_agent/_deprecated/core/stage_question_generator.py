"""
단계별 맞춤 질문 동적 생성 모듈
"""

import json
import logging
from typing import Dict, Any, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from .enums import MarketingStage
from .conversation_state import FlexibleConversationState
from .utils import clean_json_response

logger = logging.getLogger(__name__)


class StageQuestionGenerator:
    """단계별 맞춤 질문 동적 생성기"""
    
    def __init__(self):
        self.question_generation_system_prompt = self._create_question_generation_prompt()
        
    def _create_question_generation_prompt(self) -> str:
        """질문 생성 시스템 프롬프트"""
        return """당신은 마케팅 4단계 상담에서 최적의 질문을 생성하는 전문가입니다.

**4단계별 핵심 목표:**
1단계(목표 정의): 명확한 마케팅 목표, 성공 지표, 타임라인 파악
2단계(타겟 분석): 고객 페르소나, 행동 패턴, 니즈 분석
3단계(전략 기획): 채널 믹스, 예산 배분, 콘텐츠 방향
4단계(실행 계획): 구체적 콘텐츠 제작, 실행 일정

**업종별 맞춤화:**
- 뷰티: 트렌드, 인플루언서, 비포&애프터 콘텐츠
- 음식점: 지역성, 메뉴, 분위기, 리뷰
- 온라인쇼핑몰: 상품군, 경쟁사, 리뷰, 배송
- 서비스업: 전문성, 신뢰도, 차별점
- 앱: 사용성, 리텐션, 바이럴
- 크리에이터: 개성, 스토리텔링, 팬덤

**질문 원칙:**
1. 구체적이고 실행 가능한 답변을 유도
2. 업종 특성을 반영한 맞춤형 질문
3. 이전 답변을 활용한 연결성 있는 질문
4. 사용자 친화적이고 이해하기 쉬운 표현
5. 선택지를 제공해 답변 부담 줄이기

JSON 형태로 질문을 생성하세요."""

    async def generate_stage_question(self, stage: MarketingStage, context: Dict[str, Any], 
                                    state: FlexibleConversationState) -> str:
        """단계별 맞춤 질문 생성"""
        
        logger.info(f"[질문 생성] {stage.value} 단계 질문 생성 시작")
        
        # 기존 정보 요약
        collected_info_summary = self._summarize_collected_info(state, stage)
        
        question_prompt = f"""현재 마케팅 상담에서 {stage.value} 단계의 최적 질문을 생성해주세요.

**현재 상황:**
- 단계: {stage.value}
- 업종: {context.get('business_type', '일반')}
- 사업 규모: {context.get('business_scale', '미확인')}

**이미 수집된 정보:**
{collected_info_summary}

**단계별 요구사항:**
{self._get_stage_requirements(stage)}

**업종 특성 고려사항:**
{self._get_business_specific_context(context.get('business_type', '일반'))}

JSON 형태로 다음을 생성해주세요:
{{
    "main_question": "핵심 질문 (친근한 톤)",
    "sub_questions": ["세부 질문들"],
    "options_provided": ["선택지들 (있는 경우)"],
    "context_explanation": "왜 이 정보가 필요한지 간단 설명",
    "examples": ["구체적인 답변 예시들"],
    "follow_up_hints": ["추가로 물어볼 수 있는 것들"]
}}"""

        try:
            messages = [
                SystemMessage(content=self.question_generation_system_prompt),
                HumanMessage(content=question_prompt)
            ]
            
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            raw_response = llm.invoke(messages)
            response = str(raw_response.content) if hasattr(raw_response, 'content') else str(raw_response)
            
            # JSON 파싱
            if isinstance(response, str):
                cleaned = clean_json_response(response)
                try:
                    question_data = json.loads(cleaned)
                    return self._format_stage_question(question_data, stage)
                except json.JSONDecodeError:
                    logger.warning(f"JSON 파싱 실패: {cleaned[:100]}")
                    return self._get_fallback_stage_question(stage, context)
            
            return response
            
        except Exception as e:
            logger.error(f"단계 질문 생성 실패: {e}")
            return self._get_fallback_stage_question(stage, context)

    async def generate_follow_up_question(self, stage: MarketingStage, missing_info: List[str],
                                        context: Dict[str, Any], state: FlexibleConversationState) -> str:
        """부족한 정보에 대한 후속 질문 생성"""
        
        logger.info(f"[후속 질문] {stage.value} 단계 후속 질문 생성 - 부족 정보: {len(missing_info)}개")
        
        follow_up_prompt = f"""현재 {stage.value} 단계에서 부족한 정보에 대한 후속 질문을 생성해주세요.

**부족한 정보들:**
{json.dumps(missing_info, ensure_ascii=False)}

**현재 상황:**
- 업종: {context.get('business_type', '일반')}
- 기존 답변: {self._get_recent_answers_summary(state)}

**요구사항:**
1. 가장 중요한 부족 정보 1-2개에 집중
2. 이전 답변과 연결된 자연스러운 질문
3. 구체적이고 답변하기 쉬운 형태
4. 업종 특성 반영

JSON 형태로 생성해주세요:
{{
    "priority_question": "가장 중요한 후속 질문",
    "reasoning": "왜 이 질문이 중요한지",
    "connection_to_previous": "이전 답변과의 연결점",
    "answer_guidance": "어떻게 답변하면 좋을지 가이드"
}}"""

        try:
            messages = [
                SystemMessage(content=self.question_generation_system_prompt),
                HumanMessage(content=follow_up_prompt)
            ]
            
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            raw_response = llm.invoke(messages)
            response = str(raw_response.content) if hasattr(raw_response, 'content') else str(raw_response)
            
            # JSON 파싱
            if isinstance(response, str):
                cleaned = clean_json_response(response)
                try:
                    question_data = json.loads(cleaned)
                    return self._format_follow_up_question(question_data)
                except json.JSONDecodeError:
                    logger.warning(f"JSON 파싱 실패: {cleaned[:100]}")
                    return f"추가로 알려주실 수 있는 정보가 있으신가요? 특히 {missing_info[0] if missing_info else '관련 정보'}에 대해 더 구체적으로 설명해주시면 도움이 됩니다."
            
            return response
            
        except Exception as e:
            logger.error(f"후속 질문 생성 실패: {e}")
            return "추가로 알려주실 내용이 있으신가요? 더 구체적인 정보를 주시면 더 정확한 조언을 드릴 수 있습니다."

    async def generate_completion_summary_question(self, stage: MarketingStage, context: Dict[str, Any],
                                                 state: FlexibleConversationState) -> str:
        """단계 완료 요약 + 다음 단계 예고 질문"""
        
        summary_prompt = f"""현재 {stage.value} 단계가 완료되었습니다. 
요약과 함께 다음 단계로 넘어가는 자연스러운 질문을 생성해주세요.

**수집된 정보:**
{json.dumps(self._get_stage_collected_info(state, stage), ensure_ascii=False, indent=2)}

**다음 단계:** {self._get_next_stage_name(stage)}

JSON 형태로 생성:
{{
    "stage_summary": "현재 단계에서 확인된 내용 요약",
    "transition_message": "다음 단계로의 자연스러운 연결",
    "next_stage_preview": "다음 단계에서 할 일 간단 설명",
    "confirmation_question": "사용자 확인 질문"
}}"""

        try:
            messages = [
                SystemMessage(content=self.question_generation_system_prompt),
                HumanMessage(content=summary_prompt)
            ]
            
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            raw_response = llm.invoke(messages)
            response = str(raw_response.content) if hasattr(raw_response, 'content') else str(raw_response)
            
            # JSON 파싱
            if isinstance(response, str):
                cleaned = clean_json_response(response)
                try:
                    summary_data = json.loads(cleaned)
                    return self._format_completion_summary(summary_data)
                except json.JSONDecodeError:
                    logger.warning(f"JSON 파싱 실패: {cleaned[:100]}")
                    return "현재 단계가 완료되었습니다! 다음 단계로 진행할까요?"
            
            return response
            
        except Exception as e:
            logger.error(f"완료 요약 질문 생성 실패: {e}")
            return "현재 단계가 완료되었습니다! 다음 단계로 진행할까요?"

    def _summarize_collected_info(self, state: FlexibleConversationState, stage: MarketingStage) -> str:
        """수집된 정보 요약"""
        if not state.collected_info:
            return "아직 수집된 정보가 없습니다."
        
        # 단계별 관련 정보 필터링
        stage_keywords = {
            MarketingStage.STAGE_1_GOAL: ['goal', 'target', 'business'],
            MarketingStage.STAGE_2_TARGET: ['target', 'audience', 'customer'],
            MarketingStage.STAGE_3_STRATEGY: ['marketing', 'budget', 'channel'],
            MarketingStage.STAGE_4_EXECUTION: ['execution', 'content', 'timeline']
        }
        
        relevant_keywords = stage_keywords.get(stage, [])
        relevant_info = {}
        
        for key, value in state.collected_info.items():
            if any(keyword in key.lower() for keyword in relevant_keywords):
                relevant_info[key] = value['value']
        
        return json.dumps(relevant_info, ensure_ascii=False, indent=2) if relevant_info else "해당 단계 관련 정보 없음"

    def _get_stage_requirements(self, stage: MarketingStage) -> str:
        """단계별 요구사항"""
        requirements = {
            MarketingStage.STAGE_1_GOAL: """
- 구체적인 마케팅 목표 (매출 증대, 인지도 상승, 고객 확보 등)
- 성공을 어떻게 측정할 것인지 (KPI)
- 언제까지 달성하고 싶은지 (타임라인)
- 현재 비즈니스 상황과 배경
            """,
            MarketingStage.STAGE_2_TARGET: """
- 주요 타겟 고객의 인구통계학적 특성
- 고객의 관심사, 취미, 라이프스타일
- 고객의 구매 행동 패턴
- 고객이 주로 이용하는 매체/채널
            """,
            MarketingStage.STAGE_3_STRATEGY: """
- 우선적으로 활용할 마케팅 채널
- 마케팅 예산과 배분 계획
- 콘텐츠 톤앤매너와 브랜딩 방향
- 경쟁사 대비 차별점과 강점
            """,
            MarketingStage.STAGE_4_EXECUTION: """
- 구체적인 콘텐츠 유형과 주제
- 제작 일정과 발행 스케줄
- 필요한 리소스와 도구
- 성과 측정과 개선 계획
            """
        }
        return requirements.get(stage, "일반적인 마케팅 정보")

    def _get_business_specific_context(self, business_type: str) -> str:
        """업종별 특성"""
        contexts = {
            "뷰티": "트렌드 민감성, 비포&애프터, 인플루언서 활용, 계절성 고려",
            "음식점": "지역성, 메뉴 특화, 분위기/경험, 리뷰 관리",
            "온라인쇼핑몰": "상품 카테고리, 경쟁가격, 배송정책, 고객리뷰",
            "서비스업": "전문성 어필, 신뢰도 구축, 차별화 포인트",
            "앱": "사용자 경험, 리텐션, 바이럴 요소",
            "크리에이터": "개성과 스토리텔링, 팬덤 형성, 꾸준함"
        }
        return contexts.get(business_type, "일반적인 비즈니스 특성")

    def _format_stage_question(self, question_data: Dict[str, Any], stage: MarketingStage) -> str:
        """단계 질문 포맷팅"""
        stage_icons = {
            MarketingStage.STAGE_1_GOAL: "🎯",
            MarketingStage.STAGE_2_TARGET: "👥", 
            MarketingStage.STAGE_3_STRATEGY: "📊",
            MarketingStage.STAGE_4_EXECUTION: "🚀"
        }
        
        icon = stage_icons.get(stage, "💡")
        
        formatted = f"{icon} **{question_data.get('main_question', '질문을 생성할 수 없습니다.')}**\n\n"
        
        # 컨텍스트 설명
        if question_data.get('context_explanation'):
            formatted += f"💭 {question_data['context_explanation']}\n\n"
        
        # 세부 질문들
        sub_questions = question_data.get('sub_questions', [])
        if sub_questions:
            formatted += "**구체적으로 알려주세요:**\n"
            for i, sub_q in enumerate(sub_questions[:3], 1):  # 최대 3개
                formatted += f"{i}. {sub_q}\n"
            formatted += "\n"
        
        # 선택지 제공
        options = question_data.get('options_provided', [])
        if options:
            formatted += "**선택 옵션:**\n"
            for option in options[:5]:  # 최대 5개
                formatted += f"• {option}\n"
            formatted += "\n"
        
        # 예시 제공
        examples = question_data.get('examples', [])
        if examples:
            formatted += "**답변 예시:**\n"
            for example in examples[:2]:  # 최대 2개
                formatted += f"💡 {example}\n"
        
        return formatted

    def _format_follow_up_question(self, question_data: Dict[str, Any]) -> str:
        """후속 질문 포맷팅"""
        formatted = f"🔍 **{question_data.get('priority_question', '추가 질문')}**\n\n"
        
        if question_data.get('reasoning'):
            formatted += f"📝 {question_data['reasoning']}\n\n"
        
        if question_data.get('answer_guidance'):
            formatted += f"💡 **가이드**: {question_data['answer_guidance']}"
        
        return formatted

    def _format_completion_summary(self, summary_data: Dict[str, Any]) -> str:
        """완료 요약 포맷팅"""
        formatted = f"✅ **단계 완료!**\n\n"
        formatted += f"📋 **확인된 내용**: {summary_data.get('stage_summary', '정보 수집 완료')}\n\n"
        formatted += f"⏭️ {summary_data.get('transition_message', '다음 단계로 진행합니다.')}\n\n"
        
        if summary_data.get('next_stage_preview'):
            formatted += f"🔮 **다음에 할 일**: {summary_data['next_stage_preview']}\n\n"
        
        formatted += f"❓ {summary_data.get('confirmation_question', '계속 진행할까요?')}"
        
        return formatted

    def _get_fallback_stage_question(self, stage: MarketingStage, context: Dict[str, Any]) -> str:
        """기본 단계 질문 (백업용)"""
        fallback_questions = {
            MarketingStage.STAGE_1_GOAL: f"""🎯 **마케팅 목표를 구체적으로 알려주세요!**

{context.get('business_type', '비즈니스')} 마케팅을 통해 어떤 결과를 얻고 싶으신가요?

**예시:**
• 매출 20% 증대
• 브랜드 인지도 상승  
• 신규 고객 100명 확보
• SNS 팔로워 증가""",

            MarketingStage.STAGE_2_TARGET: f"""👥 **타겟 고객을 분석해보세요!**

주요 고객은 어떤 분들인가요?

**알려주세요:**
1. 연령대와 성별
2. 관심사나 취미
3. 주로 이용하는 SNS나 매체
4. 구매 패턴이나 라이프스타일""",

            MarketingStage.STAGE_3_STRATEGY: f"""📊 **마케팅 전략을 계획해보세요!**

어떤 방식으로 마케팅하고 싶으신가요?

**결정해주세요:**
• 주력 채널 (인스타그램, 블로그, 광고 등)
• 월 마케팅 예산 범위
• 원하는 브랜드 톤앤매너
• 경쟁사 대비 강점""",

            MarketingStage.STAGE_4_EXECUTION: f"""🚀 **실행 계획을 수립해보세요!**

구체적으로 어떤 콘텐츠를 만들고 싶으신가요?

**선택해주세요:**
• 인스타그램 포스트
• 블로그 콘텐츠  
• 광고 캐페인
• 이벤트 기획"""
        }
        
        return fallback_questions.get(stage, "마케팅에 대해 더 자세히 알려주세요!")

    def _get_recent_answers_summary(self, state: FlexibleConversationState) -> str:
        """최근 답변 요약"""
        # 간단한 최근 정보 요약
        recent_info = list(state.collected_info.items())[-3:] if state.collected_info else []
        return str({key: value['value'] for key, value in recent_info}) if recent_info else "없음"

    def _get_stage_collected_info(self, state: FlexibleConversationState, stage: MarketingStage) -> Dict[str, Any]:
        """특정 단계의 수집된 정보"""
        # 단계별 정보 필터링 (간단 버전)
        stage_info = {}
        for key, value in state.collected_info.items():
            stage_info[key] = value['value']
        return stage_info

    def _get_next_stage_name(self, current_stage: MarketingStage) -> str:
        """다음 단계 이름"""
        next_stages = {
            MarketingStage.STAGE_1_GOAL: "2단계: 타겟 분석",
            MarketingStage.STAGE_2_TARGET: "3단계: 전략 기획",
            MarketingStage.STAGE_3_STRATEGY: "4단계: 실행 계획",
            MarketingStage.STAGE_4_EXECUTION: "완료"
        }
        return next_stages.get(current_stage, "다음 단계")
