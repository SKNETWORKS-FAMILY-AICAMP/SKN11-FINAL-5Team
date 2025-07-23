"""
4단계 체계적 멀티턴 진행 관리 모듈
"""

import json
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from .enums import MarketingStage
from .conversation_state import FlexibleConversationState
from .utils import clean_json_response

logger = logging.getLogger(__name__)


class MultiTurnFlowManager:
    """4단계 체계적 멀티턴 진행 관리자"""
    
    def __init__(self):
        self.flow_analysis_system_prompt = self._create_flow_analysis_prompt()
        
    def _create_flow_analysis_prompt(self) -> str:
        """멀티턴 플로우 분석 시스템 프롬프트"""
        return """당신은 마케팅 상담의 4단계 체계적 진행을 관리하는 전문가입니다.

**4단계 마케팅 프로세스:**
1단계(목표 정의): 마케팅 목표, 원하는 결과, 성공 지표
2단계(타겟 분석): 고객 분석, 페르소나, 고객 여정
3단계(전략 기획): 채널 선택, 예산 배분, 콘텐츠 전략
4단계(실행 계획): 구체적 콘텐츠 제작, 캠페인 실행

**진행 방식 결정:**
- **structured_start**: 사용자가 체계적 진행을 원할 때
- **continue_current**: 현재 단계 계속 진행
- **auto_next**: 현재 단계 완료 후 자동 다음 단계
- **jump_stage**: 특정 단계로 점프
- **immediate_only**: 즉시 응답만 (단계 진행 없음)

**단계 완료 기준:**
1단계: 명확한 마케팅 목표 + 성공 지표 확인
2단계: 타겟 고객 특성 + 페르소나 정의
3단계: 마케팅 채널 + 예산/일정 결정  
4단계: 구체적 콘텐츠 또는 실행 계획 수립

JSON으로 분석 결과를 제공하세요."""

    async def analyze_multiturn_flow(self, user_input: str, intent_analysis: Dict[str, Any], 
                                   context: Dict[str, Any], state: FlexibleConversationState) -> Dict[str, Any]:
        """멀티턴 플로우 분석 및 진행 방향 결정"""
        
        logger.info(f"[멀티턴] 플로우 분석 시작 - 현재 단계: {state.current_stage.value}")
        
        # 현재 상황 요약
        completion_rates = self._calculate_stage_completion_rates(state)
        
        flow_prompt = f"""현재 마케팅 상담 상황을 분석하고 최적의 진행 방향을 결정해주세요.

**현재 상황:**
- 사용자 입력: "{user_input}"
- 현재 단계: {state.current_stage.value}
- 업종: {context.get('business_type', '일반')}
- 수집된 정보: {len(state.collected_info)}개

**단계별 완료율:**
- 1단계(목표): {completion_rates.get('stage_1', 0):.0%}
- 2단계(타겟): {completion_rates.get('stage_2', 0):.0%}  
- 3단계(전략): {completion_rates.get('stage_3', 0):.0%}
- 4단계(실행): {completion_rates.get('stage_4', 0):.0%}

**수집된 핵심 정보:**
{json.dumps(self._extract_key_info(state), ensure_ascii=False, indent=2)}

**의도 분석:**
{json.dumps(intent_analysis, ensure_ascii=False, indent=2)}

**분석 요청:**
JSON 형태로 다음을 분석해주세요:
{{
    "flow_decision": "structured_start|continue_current|auto_next|jump_stage|immediate_only",
    "reasoning": "결정 이유",
    "current_stage_analysis": {{
        "completion_level": 0.0-1.0,
        "missing_info": ["부족한 정보들"],
        "is_ready_for_next": true/false
    }},
    "next_action": {{
        "action_type": "ask_question|provide_summary|generate_content|move_to_next",
        "target_stage": "1|2|3|4|none",
        "requires_structured_flow": true/false
    }},
    "user_engagement": {{
        "wants_structured": true/false,
        "prefers_immediate": true/false,
        "engagement_level": "high|medium|low"
    }},
    "recommendations": ["진행 방향 제안들"]
}}"""

        try:
            messages = [
                SystemMessage(content=self.flow_analysis_system_prompt),
                HumanMessage(content=flow_prompt)
            ]
            
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            raw_response = llm.invoke(messages)
            response = str(raw_response.content) if hasattr(raw_response, 'content') else str(raw_response)
            
            # JSON 파싱
            if isinstance(response, str):
                cleaned = clean_json_response(response)
                try:
                    result = json.loads(cleaned)
                    logger.info(f"[멀티턴] 플로우 결정: {result.get('flow_decision')}")
                    return result
                except json.JSONDecodeError:
                    logger.warning(f"JSON 파싱 실패: {cleaned[:100]}")
                    return self._create_default_flow_analysis()
            
            return response
            
        except Exception as e:
            logger.error(f"멀티턴 플로우 분석 실패: {e}")
            return self._create_default_flow_analysis()

    def _calculate_stage_completion_rates(self, state: FlexibleConversationState) -> Dict[str, float]:
        """단계별 완료율 계산"""
        
        # 1단계: 목표 정의 관련 정보
        stage_1_keys = ['goals_main_goal', 'goals_target_metrics', 'goals_timeline', 'business_info_business_type']
        stage_1_score = sum(1 for key in stage_1_keys if key in state.collected_info) / len(stage_1_keys)
        
        # 2단계: 타겟 분석 관련 정보  
        stage_2_keys = ['target_audience_age_group', 'target_audience_gender', 'target_audience_interests', 'target_audience_behavior']
        stage_2_score = sum(1 for key in stage_2_keys if key in state.collected_info) / len(stage_2_keys)
        
        # 3단계: 전략 기획 관련 정보
        stage_3_keys = ['marketing_info_channels', 'marketing_info_budget', 'marketing_info_tools', 'additional_preferences']
        stage_3_score = sum(1 for key in stage_3_keys if key in state.collected_info) / len(stage_3_keys)
        
        # 4단계: 실행 관련 정보
        stage_4_keys = ['execution_content_type', 'execution_timeline', 'execution_resources']
        stage_4_score = sum(1 for key in stage_4_keys if key in state.collected_info) / len(stage_4_keys)
        
        return {
            'stage_1': stage_1_score,
            'stage_2': stage_2_score,  
            'stage_3': stage_3_score,
            'stage_4': stage_4_score
        }

    def _extract_key_info(self, state: FlexibleConversationState) -> Dict[str, Any]:
        """핵심 정보 추출"""
        key_info = {}
        
        # 중요한 정보들만 추출
        important_keys = [
            'business_info_business_type', 'goals_main_goal', 'target_audience_age_group',
            'marketing_info_budget', 'marketing_info_channels', 'additional_pain_points'
        ]
        
        for key in important_keys:
            if key in state.collected_info:
                key_info[key] = state.collected_info[key]['value']
        
        return key_info

    def _create_default_flow_analysis(self) -> Dict[str, Any]:
        """기본 플로우 분석 결과"""
        return {
            "flow_decision": "continue_current",
            "reasoning": "분석 실패로 인한 기본 진행",
            "current_stage_analysis": {
                "completion_level": 0.3,
                "missing_info": ["기본 정보"],
                "is_ready_for_next": False
            },
            "next_action": {
                "action_type": "ask_question",
                "target_stage": "none",
                "requires_structured_flow": False
            },
            "user_engagement": {
                "wants_structured": False,
                "prefers_immediate": True,
                "engagement_level": "medium"
            },
            "recommendations": ["일반적인 마케팅 조언 제공"]
        }

    async def execute_flow_decision(self, flow_analysis: Dict[str, Any], user_input: str,
                                  context: Dict[str, Any], state: FlexibleConversationState) -> Tuple[str, Dict[str, Any]]:
        """플로우 결정 실행"""
        
        flow_decision = flow_analysis.get("flow_decision", "continue_current")
        next_action = flow_analysis.get("next_action", {})
        
        logger.info(f"[멀티턴] 플로우 실행: {flow_decision}")
        
        if flow_decision == "structured_start":
            return await self._start_structured_flow(state, context)
            
        elif flow_decision == "auto_next":
            return await self._auto_progress_to_next_stage(state, context)
            
        elif flow_decision == "jump_stage":
            target_stage = next_action.get("target_stage", "1")
            return await self._jump_to_target_stage(target_stage, state, context)
            
        elif flow_decision == "continue_current":
            return await self._continue_current_stage(state, context, flow_analysis)
            
        else:  # immediate_only
            return "", {"requires_general_response": True}

    async def _start_structured_flow(self, state: FlexibleConversationState, 
                                   context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """체계적 4단계 플로우 시작"""
        
        state.current_stage = MarketingStage.STAGE_1_GOAL
        state.user_preferences["prefers_structured"] = True
        
        response = f"""🚀 **마케팅 4단계 체계적 상담을 시작합니다!**

**진행 과정:**
1️⃣ **목표 정의** ← 현재 단계
2️⃣ **타겟 분석** 
3️⃣ **전략 기획**
4️⃣ **실행 계획**

---

### 📋 **1단계: 마케팅 목표 정의**

성공적인 마케팅을 위해서는 명확한 목표가 필요합니다."""
        
        # 업종별 맞춤 질문 요청
        from .stage_question_generator import StageQuestionGenerator
        question_generator = StageQuestionGenerator()
        stage_question = await question_generator.generate_stage_question(
            MarketingStage.STAGE_1_GOAL, context, state
        )
        
        response += f"\n\n{stage_question}"
        
        return response, {"stage_changed": True, "new_stage": "stage_1_goal"}

    async def _auto_progress_to_next_stage(self, state: FlexibleConversationState, 
                                         context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """자동으로 다음 단계 진행"""
        
        next_stage = state.get_next_stage()
        if not next_stage:
            return "모든 단계가 완료되었습니다! 🎉", {"flow_completed": True}
        
        state.current_stage = next_stage
        
        # 단계 완료 축하 메시지
        stage_names = {
            MarketingStage.STAGE_2_TARGET: "2단계: 타겟 분석",
            MarketingStage.STAGE_3_STRATEGY: "3단계: 전략 기획", 
            MarketingStage.STAGE_4_EXECUTION: "4단계: 실행 계획"
        }
        
        response = f"""✅ **이전 단계 완료!** 

🎯 **{stage_names.get(next_stage, '다음 단계')}**로 이동합니다.

---
"""
        
        # 새 단계 질문 생성
        from .stage_question_generator import StageQuestionGenerator
        question_generator = StageQuestionGenerator()
        stage_question = await question_generator.generate_stage_question(
            next_stage, context, state
        )
        
        response += stage_question
        
        return response, {"stage_changed": True, "new_stage": next_stage.value}

    async def _jump_to_target_stage(self, target_stage: str, state: FlexibleConversationState,
                                  context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """특정 단계로 점프"""
        
        stage_mapping = {
            "1": MarketingStage.STAGE_1_GOAL,
            "2": MarketingStage.STAGE_2_TARGET,
            "3": MarketingStage.STAGE_3_STRATEGY,
            "4": MarketingStage.STAGE_4_EXECUTION
        }
        
        if target_stage not in stage_mapping:
            return f"'{target_stage}' 단계를 찾을 수 없습니다.", {"error": True}
        
        target_stage_enum = stage_mapping[target_stage]
        state.current_stage = target_stage_enum
        
        response = f"🚀 **{target_stage}단계로 이동했습니다!**\n\n"
        
        # 해당 단계 질문 생성
        from .stage_question_generator import StageQuestionGenerator
        question_generator = StageQuestionGenerator()
        stage_question = await question_generator.generate_stage_question(
            target_stage_enum, context, state
        )
        
        response += stage_question
        
        return response, {"stage_changed": True, "new_stage": target_stage_enum.value}

    async def _continue_current_stage(self, state: FlexibleConversationState, context: Dict[str, Any],
                                    flow_analysis: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """현재 단계 계속 진행"""
        
        current_analysis = flow_analysis.get("current_stage_analysis", {})
        missing_info = current_analysis.get("missing_info", [])
        
        if missing_info:
            # 부족한 정보에 대한 추가 질문 생성
            from .stage_question_generator import StageQuestionGenerator  
            question_generator = StageQuestionGenerator()
            
            follow_up_question = await question_generator.generate_follow_up_question(
                state.current_stage, missing_info, context, state
            )
            
            return follow_up_question, {"continue_stage": True}
        else:
            # 현재 단계 완료, 다음 단계로 자동 진행
            return await self._auto_progress_to_next_stage(state, context)

    async def should_use_structured_flow(self, user_input: str, intent_analysis: Dict[str, Any],
                                      state: FlexibleConversationState) -> bool:
        """LLM 기반 체계적 플로우 사용 여부 결정 (하드코딩 없는 개선 버전)"""
        try:
            messages = [
                SystemMessage(content="""당신은 마케팅 상담에서 체계적 단계별 진행 여부를 판단하는 전문가입니다.

                **다음 조건 중 하나라도 해당되면 무조건 requires_structured = true로 하세요:**
                1. 사용자가 마케팅을 처음 시작하거나 "아무것도 모른다", "어떻게 시작해야 하나", "처음이라 몰라" 등 불확실함을 표현.
                2. 사용자가 "홍보하고 싶다", "마케팅 하고 싶다", "프로모션 하고 싶다" 등 막연한 의지만 표현 (세부 계획 없음).
                3. 새로운 제품/서비스를 어떻게 마케팅할지 질문하는 경우.
                4. 마케팅 전략, 브랜딩, 실행계획, 타겟 설정 등 단계적 가이드가 필요한 경우.
                5. 현재 state.current_stage가 ANY_QUESTION이 아니거나 intent_analysis에서 복잡한 마케팅 주제가 감지되는 경우.

                **즉시 응답이 적합한 경우 (requires_structured = false):**
                - 단순 질의(예: "페이스북 광고 예산은 얼마?").
                - 특정 채널 사용법, 특정 기능에 대한 질문 (단계적 상담이 불필요).
                
                JSON 형식으로만 답변하세요:
                {"requires_structured": true/false, "confidence": 0.0-1.0, "reasoning": "판단 근거"}
                """),
                HumanMessage(content=f"""다음 정보를 바탕으로 체계적 진행 여부를 판단하세요.

                **사용자 입력:**
                "{user_input}"

                **현재 상태:**
                - 현재 단계: {state.current_stage.value}
                - 선호도: {json.dumps(state.user_preferences, ensure_ascii=False)}

                **의도 분석:**
                {json.dumps(intent_analysis, ensure_ascii=False, indent=2)}""")
            ]

            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            response = await llm.ainvoke(messages)
            response_content = str(response.content) if hasattr(response, 'content') else str(response)

            logger.debug(f"[멀티턴] LLM 응답 원문: {response_content}")

            # JSON 포맷 보정
            cleaned = response_content.replace("```json", "").replace("```", "").strip()
            try:
                result = json.loads(cleaned)
                logger.info(f"[멀티턴] 체계적 진행 결정: {result}")
                return result.get('requires_structured', False)
            except json.JSONDecodeError:
                logger.warning(f"JSON 파싱 실패: {cleaned[:100]}")
                return self._default_structured_flow_decision(user_input, intent_analysis, state)

        except Exception as e:
            logger.error(f"체계적 진행 분석 실패: {e}")
            return self._default_structured_flow_decision(user_input, intent_analysis, state)
    
    def _default_structured_flow_decision(self, user_input: str, intent_analysis: Dict[str, Any],
                                        state: FlexibleConversationState) -> bool:
        """기본 체계적 플로우 결정 로직"""
        
        # 체계적 진행 키워드
        structured_keywords = [
            "체계적", "단계별", "처음부터", "차근차근", "순서대로", 
            "4단계", "전체적으로", "완전히", "상담 시작"
        ]
        
        # 사용자가 체계적 진행을 원하는 경우
        if any(keyword in user_input for keyword in structured_keywords):
            return True
        
        # 현재 상태가 체계적 진행 중인 경우
        if (state.user_preferences.get("prefers_structured", False) and 
            state.current_stage != MarketingStage.ANY_QUESTION):
            return True
        
        # 의도 분석에서 체계적 진행을 권장하는 경우
        if intent_analysis.get("flow_control", {}).get("wants_structured", False):
            return True
            
        return False
