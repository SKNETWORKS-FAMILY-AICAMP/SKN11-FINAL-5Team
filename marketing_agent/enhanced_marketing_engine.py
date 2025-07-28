"""
Enhanced Marketing Conversation Engine
완전히 개선된 마케팅 대화 엔진

✅ 핵심 개선사항:
- 맥락 인식 대화 (이미 수집된 정보 기억)
- 명확한 진행 조건 (체크리스트 기반)
- 사용자 의도 우선 (정보 수집보다 요구사항 우선)
- 효율적인 LLM 호출
- 스마트한 정보 추출
"""

import logging
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import openai
import re
import httpx  # Instagram API 호출을 위한 HTTP 클라이언트 추가

from enhanced_marketing_state import (
    EnhancedStateManager, ConversationContext, MarketingStage, 
    InfoCategory, enhanced_state_manager
)
from config import config

logger = logging.getLogger(__name__)

class EnhancedMarketingEngine:
    """완전히 개선된 마케팅 대화 엔진"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL
        self.temperature = 0.7
        self.state_manager = enhanced_state_manager
        self.task_agent_url = "http://localhost:8005"  # task_agent API URL
        
        # 🔥 핵심 개선: 컨텍스트 인식 프롬프트
        self._init_context_aware_prompts()
        
        logger.info("✅ 완전히 개선된 마케팅 대화 엔진 초기화 완료")
    
    def _init_context_aware_prompts(self):
        """맥락 인식 프롬프트 초기화"""
        
        # 🔥 핵심 개선: 수집된 정보를 명시적으로 활용하는 프롬프트
        self.context_aware_prompt = """당신은 전문 마케팅 컨설턴트입니다. 
수집된 정보를 먼저 분석한 후, 그에 기반하여 맞춤형 조언과 후속 질문을 제공하세요.

⚠️ 중요한 규칙:
1. **1단계: 정보 분석** - 수집된 정보를 먼저 요약하고 분석하세요
2. **2단계: 맞춤형 조언** - 분석 결과를 바탕으로 구체적인 조언을 제공하세요
3. **3단계: 후속 질문** - 더 나은 조언을 위해 필요한 핵심 질문을 1-2개만 하세요
4. 이미 수집된 정보는 다시 묻지 마세요
5. 사용자가 구체적인 요청(콘텐츠 생성 등)을 하면 정보 수집보다 요청 처리를 우선하세요

현재 상황:
{context}

사용자 입력: {user_input}

응답은 자연스러운 대화체로 작성해주세요. 
- 먼저 수집된 정보와 상황을 바탕으로 마케팅 관점에서 간단한 통찰을 제시해주세요.
- 이어서 실천 가능한 팁이나 전략을 2~3개 정도 제안해주세요.
- 필요하다면, 사용자가 답변하기 쉽게 자연스럽게 질문을 덧붙여주세요. 예: “혹시 이와 관련해 어떤 디자인을 주로 활용하고 계신가요?”
- 전체 분량은 약 300자 내외, 말 걸 듯한 친근한 톤을 유지해주세요. """

        # 🔥 핵심 개선: 사용자 의도 파악 프롬프트
        self.intent_analysis_prompt = """사용자의 메시지에서 의도와 정보를 정확히 추출하세요.

사용자 입력: "{user_input}"

### 추출 가이드라인:
1. **마케팅 채널 감지**: 인스타그램, 인스타, instagram → "인스타그램"
2. **업종 감지**: 카페, 커피 → "카페", 쇼핑몰, 이커머스 → "온라인쇼핑몰"
3. **목표 감지**: 매출, 수익 → "매출증대", 인지도, 브랜드 → "브랜드인지도"
4. **타겟 감지**: 20대, 청년 → "20대", 30대, 직장인 → "30대 직장인"

다음 JSON 형식으로 정확히 답변하세요:
{{
    "intent":"blog_marketing|content_marketing|conversion_optimization|digital_advertising|email_marketing|influencer_marketing|local_marketing|marketing_fundamentals|marketing_metrics|personal_branding|social_media_marketing|viral_marketing",
    "extracted_info": {{
        "business_type": "업종명 또는 null",
        "product": "제품/서비스명 또는 null",
        "main_goal": "마케팅 목표 또는 null",
        "target_audience": "타겟 고객 또는 null",
        "budget": "예산 정보 또는 null",
        "channels": "마케팅 채널명 또는 null"
    }},
    "user_sentiment": "positive|neutral|negative",
    "next_action": "continue_conversation|create_content|provide_advice|ask_question"
}}

예시:
- "인스타그램 마케팅을 효과적으로 하는 법은?" → channels: "인스타그램"
- "카페 운영하는데 20대 고객 늘리고 싶어" → business_type: "카페", target_audience: "20대", main_goal: "신규고객"
"""

        # 🔥 핵심 개선: 콘텐츠 생성 프롬프트
        self.content_type_prompt = """
당신은 전문 마케팅 분석가입니다.
다음 정보를 바탕으로 **{channel}**에 최적화된 마케팅 콘텐츠 전략을 분석하고 추천하세요.

비즈니스 정보:
{business_context}

요구사항:
{user_request}

### 분석 기준
1. 사용자가 원하는 콘텐츠 유형 파악
2. 가장 적합한 마케팅 채널 결정 (채널이 명시되지 않은 경우 추천)
3. 마케팅에 필요한 키워드 정확히 5개 추출
4. 추천할 마케팅 도구/전략 결정 및 이유 설명

### 응답 형식 (JSON)
{{
    "content_type": "instagram_post | blog_post | strategy | campaign | trend_analysis | hashtag_analysis",
    "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"],
    "confidence": 0.95,
    "reasoning": "이 콘텐츠 유형과 키워드를 선택한 이유"
}}

### 중요 규칙
- content_type은 다음 중 정확히 하나만 선택: "instagram_post", "blog_post", "strategy", "campaign", "trend_analysis", "hashtag_analysis"
- 채널이 명시되지 않은 경우 recommended_channel 필드에 가장 적합한 채널을 추천
- keywords는 반드시 5개여야 함
- confidence는 0.0~1.0 사이의 값
"""

    async def process_user_message(self, user_id: int, conversation_id: int, 
                                  user_input: str) -> Dict[str, Any]:
        """🔥 핵심 개선: 사용자 메시지 처리"""
        try:
            logger.info(f"[{conversation_id}] 메시지 처리 시작: {user_input[:50]}...")
            
            # 1. 대화 컨텍스트 조회/생성
            context = self.state_manager.get_or_create_conversation(user_id, conversation_id)
            context.add_message("user", user_input)
            
            # 2. 🔥 핵심 개선: 사용자 의도 및 정보 추출
            intent_result = await self._analyze_user_intent(user_input, context)
            
            # 3. 추출된 정보 저장
            self._save_extracted_info(context, intent_result.get("extracted_info", {}))
            
            # 4. 🔥 핵심 개선: 의도에 따른 처리 분기
            user_intent = intent_result.get("intent")
            next_action = intent_result.get("next_action", "continue_conversation")
            
            print(f"user_intent: {intent_result}")
            print(f"next_action: {next_action}")
            
            if next_action == "create_content":
                business_type = context.get_info_value("business_type")
                product = context.get_info_value("product")

                if not business_type or not product:
                    logger.info("[create_content] fil수 정보 부족 → 질문")
                    context.flags["create_content_pending"] = True
                    context.flags["show_posting_modal"] = False
                    response = await self._collect_essential_info(context, user_input)
                else:
                    response = await self._handle_content_creation(context, user_input, intent_result)
                
                if context.flags["show_posting_modal"]:
                    context.flags["show_posting_modal"] = False
                    return {
                        "success": True,
                        "data": {
                            "answer": response,
                            "metadata": {
                            "show_posting_modal": True,
                            "generated_content": {
                                "content": "생성된 콘텐츠",
                                "hashtags": ["해시태그들"],
                                "platform": "instagram"
                            }
                            }
                        }
                    }
                    
            elif context.flags.get("create_content_pending") and context.get_info_value("business_type") and context.get_info_value("product"):
                logger.info("[create_content] 보류된 콘텐츠 제작 실행")
                context.flags["create_content_pending"] = False
                response = await self._handle_content_creation(context, user_input, intent_result)

            elif context.can_proceed_to_next_stage():
                print("continue_conversation")
                # 충분한 정보가 있거나 사용자가 구체적 요청을 한 경우 → 조언 제공
                response = await self._provide_contextual_advice(context, user_input, user_intent)
            else:
                print("collect_essential_info")
                # 정보 부족 → 핵심 정보만 추가 수집
                response = await self._collect_essential_info(context, user_input)
            
            # 5. 응답 저장 및 반환
            context.add_message("assistant", response)
            
            return {
                "success": True,
                "data": {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "answer": response,
                    "current_stage": context.current_stage.value,
                    "completion_rate": context.get_completion_rate(),
                    "collected_info": {k: v.value for k, v in context.collected_info.items()},
                    "can_proceed": context.can_proceed_to_next_stage(),
                    "user_engagement": context.user_engagement,
                    "processing_engine": "enhanced_v2"
                }
            }
            
        except Exception as e:
            logger.error(f"[{conversation_id}] 메시지 처리 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "answer": "죄송합니다. 시스템에 문제가 발생했습니다. 다시 시도해주세요.",
                    "processing_engine": "enhanced_v2"
                }
            }
    
    async def _analyze_user_intent(self, user_input: str, context: ConversationContext) -> Dict[str, Any]:
        """🔥 핵심 개선: 사용자 의도 분석"""
        try:
            # LLM 기반 의도 분석
            response = await self._call_llm_with_timeout(
                self.intent_analysis_prompt.format(user_input=user_input),
                timeout=10
            )
            
            # JSON 파싱 시도
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                result = self._safe_json_parse(response)
                logger.warning(f"JSON 파싱 실패, 폴백 사용: {response}")
                return result
                
        except Exception as e:
            logger.warning(f"의도 분석 실패, 폴백 사용: {e}")
    
    def _save_extracted_info(self, context: ConversationContext, extracted_info: Dict[str, Any]):
        """추출된 정보 저장"""
        # 🔥 개선: 유효하지 않은 값들 정의
        invalid_values = {"없음", "null", "None", "", "undefined", "N/A"}
        
        for key, value in extracted_info.items():
            # 값이 존재하고 유효한지 확인
            if (value is not None and 
                str(value).strip() and 
                str(value).lower() not in invalid_values):
                
                # 카테고리 결정
                if key in ["business_type", "product"]:
                    category = InfoCategory.BASIC
                elif key in ["main_goal", "budget"]:
                    category = InfoCategory.GOAL
                elif key in ["target_audience"]:
                    category = InfoCategory.TARGET
                elif key in ["channels"]:
                    category = InfoCategory.CHANNEL
                else:
                    category = InfoCategory.BASIC
                
                context.add_info(key, value, category, source="extracted", confidence=0.8)

    def _load_prompt_by_intent(self, user_intent: str) -> str:
        import os
        """user_intent에 맞는 프롬프트 파일을 로드"""
        try:
            # prompts 폴더 경로
            prompts_dir = os.path.join(os.path.dirname(__file__), 'prompts')
            
            # intent에 맞는 파일명 매핑
            intent_to_file = {
                'blog_marketing': 'blog_marketing.md',
                'content_marketing': 'content_marketing.md', 
                'conversion_optimization': 'conversion_optimization.md',
                'digital_advertising': 'digital_advertising.md',
                'email_marketing': 'email_marketing.md',
                'influencer_marketing': 'influencer_marketing.md',
                'local_marketing': 'local_marketing.md',
                'marketing_fundamentals': 'marketing_fundamentals.md',
                'marketing_metrics': 'marketing_metrics.md',
                'personal_branding': 'personal_branding.md',
                'social_media_marketing': 'social_media_marketing.md',
                'viral_marketing': 'viral_marketing.md'
            }
            
            # 해당하는 프롬프트 파일이 있으면 로드
            if user_intent in intent_to_file:
                file_path = os.path.join(prompts_dir, intent_to_file[user_intent])
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        prompt_content = f.read()
                    
                    # 프롬프트 내용을 컨텍스트와 사용자 입력을 받을 수 있는 형태로 포맷팅
                    formatted_prompt = f"""
{prompt_content}

현재 수집된 정보:
{{context}}

사용자 요청:
{{user_input}}

추가로 수집해야 할 정보:
{{missing_info}}

[요구사항]
1. 먼저 사용자 요청에 대한 주요 조언(2~3문장)을 친근하고 전문적인 톤으로 제공.
2. "💡 지금 바로 해볼 수 있는 행동:" 섹션을 마크다운 리스트(-)로 작성 (2~4개).
3. 추가 정보가 필요한 경우: 해당 정보를 자연스럽게 묻는 후속 질문을 1~2문장으로 작성.
4. 추가 정보가 없는 경우: 수집된 정보를 바탕으로 구체적인 실행 방안이나 다음 단계를 제안.
5. 후속 질문은 "혹시 ~에 대해 알려주실 수 있을까요?" 또는 "이 부분은 어떇게 생각하시나요?"처럼 대화 흐름에 맞게.
"""
                    
                    return formatted_prompt
            
            # 기본 프롬프트 반환 (해당하는 파일이 없는 경우)
            return self.context_aware_prompt
            
        except Exception as e:
            logger.error(f"프롬프트 파일 로드 실패: {e}")
            return self.context_aware_prompt
            
    async def _provide_contextual_advice(self, context: ConversationContext, user_input: str, user_intent: str) -> str:
        """🔥 핵심 개선: 수집된 컨텍스트 기반 조언 제공"""
        try:
            context_summary = context.get_context_summary()
            print("context_summary:", context_summary)
            
            self._advance_stage_if_needed(context)
            
            # 🔥 새로운 단계로 진행했다면 새 단계에 맞는 질문 생성
            missing_info = context.get_missing_required_info()
            selected_prompt = self._load_prompt_by_intent(user_intent)
            prompt = selected_prompt.format(
                context=context_summary,
                user_input=user_input,
                missing_info=missing_info
            )
            
            response = await self._call_llm_with_timeout(prompt, timeout=15)
            return response
            
        except Exception as e:
            logger.error(f"컨텍스트 기반 조언 제공 실패: {e}")
            return "수집된 정보를 바탕으로 맞춤형 조언을 준비하고 있습니다. 조금 더 구체적으로 말씀해주시면 더 정확한 도움을 드릴 수 있어요!"
    
    async def _collect_essential_info(self, context: ConversationContext, user_input: str) -> str:
        """🔥 핵심 개선: LLM 기반 동적 후속 질문 생성"""
        missing_info = context.get_missing_required_info()
        
        if not missing_info or context.should_skip_questions():
            # 부족한 정보가 없거나 사용자가 질문을 싫어하면 바로 조언 제공
            return await self._provide_contextual_advice(context, user_input)
        
        # 가장 중요한 정보 1-2개만 요청
        priority_missing = missing_info[:2]
        print("priority_missing:", priority_missing)
        # LLM을 활용한 동적 질문 생성
        return await self._generate_contextual_questions(context, priority_missing, user_input)
    
    async def _generate_contextual_questions(self, context: ConversationContext, missing_info: List[str], user_input: str) -> str:
        """LLM을 활용한 컨텍스트 기반 정보 분석 + 질문 생성"""
        
        # 현재 수집된 정보 요약
        collected_summary = ""
        if context.collected_info:
            collected_items = []
            for key, info in context.collected_info.items():
                collected_items.append(f"- {key}: {info.value}")
            collected_summary = "\n".join(collected_items)
        
        print("collected_summary:", collected_summary)
        # 정보 분석 + 질문 생성을 위한 프롬프트
        analysis_and_question_prompt = f"""
    당신은 마케팅 전문가입니다. 사용자와 자연스러운 대화를 통해 필요한 정보를 수집하고 있습니다.
    
    현재 상황:
    - 사용자 입력: "{user_input}"
    - 현재 단계: {context.current_stage.value}
    - 이미 수집된 정보:
    {collected_summary if collected_summary else "아직 수집된 정보 없음"}
    
    부족한 필수 정보: {', '.join(missing_info)}
    
    요구사항:
    1. **먼저 수집된 정보에 대한 간단한 분석/코멘트 제공**
       - 현재까지 파악된 상황 요약
       - 마케팅 관점에서의 인사이트나 방향성 제시
       - 긍정적이고 전문적인 톤으로 작성
    
    2. **그 다음 자연스럽게 후속 질문 연결**
       - 최대 2개의 질문만 하기 (사용자 피로도 고려)
       - 분석 내용과 자연스럽게 연결되는 질문
       - 구체적인 예시 포함하여 이해하기 쉽게 질문
       - 사용자가 이미 언급한 내용은 다시 묻지 않기
    
    다음 중 하나의 정보가 필요합니다:
    - business_type: 업종/비즈니스 유형
    - product: 주요 제품이나 서비스
    - main_goal: 마케팅의 주요 목표
    - target_audience: 주요 고객층
    - budget: 마케팅 예산 범위
    - channels: 선호하는 마케팅 채널
    
    응답은 자연스럽고 흐름 있는 대화체로 작성해주세요. 
    - 명확한 제목 없이 단락 형태로 이어지도록 하되, 전체 길이는 300자 내외로 유지해주세요.
    - 너무 포멀하지 않고, 말 걸듯 친근한 톤으로 작성해주세요.
    - 질문이 필요한 경우, 분석 내용과 연결해 1~2개의 질문을 자연스럽게 삽입해주세요.
    - 예: "지금 운영 중인 네일샵이라면 감각적인 이미지가 중요한데요, 혹시 고객들이 특히 좋아하는 디자인이 있으신가요?"

    
    전문적이면서도 친근한 톤으로 작성해주세요:
    """
        
        # _generate_contextual_questions 메서드 내부
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=[
                    {"role": "system", "content": "당신은 친근하고 전문적인 마케팅 컨설턴트입니다. 수집된 정보를 분석하고 인사이트를 제공한 후, 자연스럽게 필요한 추가 정보를 요청합니다."},
                    {"role": "user", "content": analysis_and_question_prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=1000
                ),
                timeout=30
            )
            generated_response = response.choices[0].message.content.strip()
            
            # 질문 피로도 증가
            context.question_fatigue += 1
            
            logger.info(f"LLM 기반 분석+질문 생성 완료: {len(generated_response)}자")
            return generated_response
        
        except asyncio.TimeoutError:
            logger.warning("분석+질문 생성 타임아웃, 폴백 응답 사용")
            return await self._fallback_analysis_and_questions(context, missing_info)
        except Exception as e:
            logger.error(f"분석+질문 생성 중 오류: {e}")
            return await self._fallback_analysis_and_questions(context, missing_info)
    
    async def _fallback_analysis_and_questions(self, context: ConversationContext, missing_info: List[str]) -> str:
        """LLM 실패 시 사용할 폴백 분석+질문"""
        
        # 간단한 분석 제공
        analysis = ""
        if context.collected_info:
            info_count = len(context.collected_info)
            analysis = f"지금까지 {info_count}가지 정보를 파악했네요! 좋은 시작입니다. 🎯"
        else:
            analysis = "마케팅 전략을 세우기 위한 정보 수집을 시작해보겠습니다! 💪"
        
        # 폴백 질문 템플릿
        question_templates = {
            "business_type": "어떤 업종에서 일하고 계신가요? (예: 카페, 온라인쇼핑몰, 뷰티 등)",
            "product": "주요 제품이나 서비스는 무엇인가요?",
            "main_goal": "마케팅의 주요 목표는 무엇인가요? (매출 증대, 브랜드 인지도, 신규 고객 등)",
            "target_audience": "주요 고객층은 어떻게 되나요? (연령대, 성별, 특성 등)",
            "budget": "마케팅 예산은 어느 정도 생각하고 계신가요?",
            "channels": "어떤 마케팅 채널을 선호하시나요? (인스타그램, 블로그, 유튜브 등)"
        }
        
        questions = []
        for info_key in missing_info[:2]:  # 최대 2개만
            if info_key in question_templates:
                questions.append(question_templates[info_key])
        
        if questions:
            question_part = ""
            if len(questions) == 1:
                question_part = f"\n\n더 구체적인 조언을 위해 {questions[0]}"
            else:
                question_part = f"\n\n더 효과적인 마케팅 전략을 위해 알려주세요:\n• {questions[0]}\n• {questions[1]}"
            
            return analysis + question_part
        else:
            return analysis + "\n\n마케팅에 대해 더 자세히 알려주세요!"

    async def _handle_content_creation(self, context: ConversationContext, 
                                     user_input: str, intent_result: Dict[str, Any]) -> str:
        """🔥 핵심 개선: 콘텐츠 생성 처리"""
        try:
            # 채널 결정
            channel = intent_result.get("extracted_info", {}).get("channels", "인스타그램")
            if not channel or channel == "없음":
                channel = self._infer_channel(user_input)
            
            # 비즈니스 컨텍스트 생성
            business_context = self._create_business_context(context)
            
            # 콘텐츠 생성
            content_prompt = self.content_type_prompt.format(
                channel=channel,
                business_context=business_context,
                user_request=user_input
            )
            
            response = await self._call_llm_with_timeout(content_prompt, timeout=20)
            intent_analysis = self._safe_json_parse(response)
            
            from general_marketing_tools import get_marketing_tools
            marketing_tools = get_marketing_tools()
            
            tool_type = intent_analysis.get("content_type", "instagram_post")
            keywords = intent_analysis.get("keywords", ["마케팅"])
            
            logger.info(f"마케팅 툴 실행: {tool_type}, 키워드: {keywords}")
            # context를 재할당하지 말고 별도 변수 사용
            collected_info_dict = {k: v.value for k, v in context.collected_info.items()}
            
            if tool_type == "instagram_post":
                generated_content = await marketing_tools.create_instagram_post(keywords, collected_info_dict)
                generated_content = generated_content.get('full_content')
                
                # 원본 context 객체의 flags에 접근
                context.flags["generated_content"] = generated_content
                context.flags["content_type"] = tool_type
                context.flags["awaiting_instagram_post_decision"] = True
                context.flags["show_posting_modal"] = True
                return generated_content
            
            elif tool_type == "blog_post":
                generated_content = await marketing_tools.create_blog_post(keywords, collected_info_dict)
                generated_content = generated_content.get('full_content')
                return f"✨ 블로그 콘텐츠를 생성했습니다!\n\n{generated_content}\n\n이 콘텐츠가 마음에 드시나요? 수정이 필요하면 말씀해주세요!"
            elif tool_type == "strategy":
                generated_content = await marketing_tools.create_strategy_content(collected_info_dict)
                return f"✨ 마케팅 전략을 생성했습니다!\n\n{generated_content}\n\n이 콘텐츠가 마음에 드시나요? 수정이 필요하면 말씀해주세요!"
            elif tool_type == "campaign":
                generated_content = await marketing_tools.create_campaign_content(collected_info_dict)
                return f"✨ 캠페인 콘텐츠를 생성했습니다!\n\n{generated_content}\n\n이 콘텐츠가 마음에 드시나요? 수정이 필요하면 말씀해주세요!"
            elif tool_type == "trend_analysis":
                if keywords:
                    generated_content = await marketing_tools.analyze_naver_trends(keywords)
                    return f"✨ 트렌드 분석 결과:\n\n{generated_content}\n\n"
                else:
                    return {"success": False, "error": "트렌드 분석을 위한 키워드가 필요합니다."}
            elif tool_type == "hashtag_analysis":
                if keywords:
                    generated_content = await marketing_tools.analyze_instagram_hashtags(user_input, keywords)
                    return f"✨ 해시태그 분석 결과:\n\n{generated_content}\n\n"
                else:
                    return {"success": False, "error": "해시태그 분석을 위한 키워드가 필요합니다."}
            else:
                # 기본값: 인스타그램 포스트
                generated_content = await marketing_tools.create_instagram_post(keywords, collected_info_dict)
                return f"✨ 콘텐츠를 생성했습니다!\n\n{generated_content}\n\n이 콘텐츠가 마음에 드시나요? 수정이 필요하면 말씀해주세요!"
            # # 단계를 콘텐츠 생성으로 진행
            # context.advance_stage(MarketingStage.CONTENT_CREATION)
            
        except Exception as e:
            logger.error(f"마케팅 툴 실행 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _call_instagram_api(self, content: str) -> Dict[str, Any]:
        """task_agent의 Instagram API 호출"""
        try:
            # Instagram API 요청 데이터 구성
            # 실제 구현에서는 사용자의 Instagram 계정 정보가 필요합니다
            post_data = {
                "instagram_id": "user_instagram_id",  # 실제 사용자 Instagram ID 필요
                "access_token": "user_access_token",  # 실제 사용자 액세스 토큰 필요
                "image_url": "https://example.com/default-image.jpg",  # 기본 이미지 또는 생성된 이미지 URL
                "caption": content
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.task_agent_url}/instagram/post",
                    json=post_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {
                        "success": False, 
                        "error": f"API 호출 실패 (상태코드: {response.status_code}): {response.text}"
                    }
                    
        except httpx.TimeoutException:
            return {"success": False, "error": "API 호출 시간 초과"}
        except Exception as e:
            return {"success": False, "error": f"API 호출 중 오류: {str(e)}"}

    def _safe_json_parse(self, response: str) -> Dict[str, Any]:
        """안전한 JSON 파싱 with fallback"""
        try:
            # 먼저 전체 응답을 JSON으로 파싱 시도
            return json.loads(response)
        except json.JSONDecodeError:
            try:
                # JSON 블록 추출 시도 (```json...``` 형태)
                import re
                json_match = re.search(r'```json\s*({.*?})\s*```', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                
                # 중괄호로 둘러싸인 JSON 추출 시도
                json_match = re.search(r'{.*}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                    
            except json.JSONDecodeError:
                pass
            
            # 모든 파싱 실패 시 기본값 반환
            logger.warning(f"JSON 파싱 실패, 기본값 사용. 응답: {response[:100]}...")
            return {
                "content_type": "instagram_post",
                "keywords": ["마케팅", "비즈니스", "브랜드", "고객", "성장"],
                "confidence": 0.5,
                "reasoning": "JSON 파싱 실패로 기본값 사용"
            }
            
    def _infer_channel(self, user_input: str) -> str:
        """사용자 입력에서 마케팅 채널 추론"""
        user_input_lower = user_input.lower()
        
        if "인스타" in user_input_lower:
            return "인스타그램"
        elif "블로그" in user_input_lower:
            return "블로그"
        elif "유튜브" in user_input_lower:
            return "유튜브"
        elif "페이스북" in user_input_lower:
            return "페이스북"
        elif "광고" in user_input_lower:
            return "온라인 광고"
        else:
            return "인스타그램"  # 기본값
    
    def _create_business_context(self, context: ConversationContext) -> str:
        """비즈니스 컨텍스트 생성"""
        context_parts = []
        
        # 수집된 정보 활용
        business_type = context.get_info_value("business_type")
        if business_type:
            context_parts.append(f"업종: {business_type}")
        
        product = context.get_info_value("product")
        if product:
            context_parts.append(f"제품/서비스: {product}")
        
        target = context.get_info_value("target_audience")
        if target:
            context_parts.append(f"타겟 고객: {target}")
        
        goal = context.get_info_value("main_goal")
        if goal:
            context_parts.append(f"마케팅 목표: {goal}")
        
        if not context_parts:
            context_parts.append("일반 비즈니스")
        
        return ", ".join(context_parts)
    
    def _advance_stage_if_needed(self, context: ConversationContext):
        """필요시 단계 진행"""
        current_stage = context.current_stage
        
        if current_stage == MarketingStage.INITIAL and context.can_proceed_to_next_stage():
            context.advance_stage(MarketingStage.GOAL_SETTING)
        elif current_stage == MarketingStage.GOAL_SETTING and context.can_proceed_to_next_stage():
            context.advance_stage(MarketingStage.TARGET_ANALYSIS)
        elif current_stage == MarketingStage.TARGET_ANALYSIS and context.can_proceed_to_next_stage():
            context.advance_stage(MarketingStage.STRATEGY)
        elif current_stage == MarketingStage.STRATEGY and context.can_proceed_to_next_stage():
            # 전략 단계에서는 사용자 요청에 따라 분기
            pass
    
    async def _call_llm_with_timeout(self, prompt: str, timeout: int = 15) -> str:
        """타임아웃이 있는 LLM 호출"""
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=1000
                ),
                timeout=timeout
            )
            return response.choices[0].message.content.strip()
        except asyncio.TimeoutError:
            logger.warning(f"LLM 호출 타임아웃 ({timeout}초)")
            return "응답 생성에 시간이 걸리고 있습니다. 더 간단한 질문으로 다시 시도해주세요."
        except Exception as e:
            logger.error(f"LLM 호출 실패: {e}")
            return "응답 생성 중 문제가 발생했습니다. 다시 시도해주세요."
    
    def get_conversation_status(self, conversation_id: int) -> Dict[str, Any]:
        """대화 상태 조회"""
        if conversation_id not in self.state_manager.conversations:
            return {"status": "not_found"}
        
        context = self.state_manager.conversations[conversation_id]
        
        return {
            "conversation_id": conversation_id,
            "current_stage": context.current_stage.value,
            "completion_rate": context.get_completion_rate(),
            "collected_info": {k: v.value for k, v in context.collected_info.items()},
            "can_proceed": context.can_proceed_to_next_stage(),
            "missing_info": context.get_missing_required_info(),
            "user_engagement": context.user_engagement,
            "message_count": len(context.conversation_history),
            "last_activity": context.last_activity.isoformat(),
            "processing_engine": "enhanced_v2",
            "improvements": [
                "context_aware_conversation",
                "efficient_info_collection", 
                "user_intent_priority",
                "smart_stage_progression"
            ]
        }
    
    def reset_conversation(self, conversation_id: int) -> bool:
        """대화 초기화"""
        try:
            if conversation_id in self.state_manager.conversations:
                del self.state_manager.conversations[conversation_id]
                logger.info(f"대화 초기화 완료: {conversation_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"대화 초기화 실패: {e}")
            return False

# 전역 엔진 인스턴스
enhanced_marketing_engine = EnhancedMarketingEngine()