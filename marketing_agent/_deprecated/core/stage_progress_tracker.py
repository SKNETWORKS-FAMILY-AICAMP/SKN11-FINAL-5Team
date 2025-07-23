"""
단계 완료 조건 체크 및 자동 진행 관리 모듈
"""

import json
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from .enums import MarketingStage
from .conversation_state import FlexibleConversationState
from .utils import clean_json_response

logger = logging.getLogger(__name__)


class StageProgressTracker:
    """단계 진행 추적 및 완료 조건 체크"""
    
    def __init__(self):
        self.progress_analysis_system_prompt = self._create_progress_analysis_prompt()
        
    def _create_progress_analysis_prompt(self) -> str:
        """단계 진행 분석 시스템 프롬프트"""
        return """당신은 마케팅 4단계 상담의 진행 상황을 분석하는 전문가입니다.

**4단계 완료 기준:**

**1단계(목표 정의) 완료 조건:**
- 구체적인 마케팅 목표 (매출, 인지도, 고객확보 등)
- 성공 측정 지표 (KPI)
- 목표 달성 기한
- 비즈니스 배경 정보

**2단계(타겟 분석) 완료 조건:**
- 타겟 고객 인구통계 (연령, 성별, 지역 등)
- 고객 관심사 및 라이프스타일
- 구매 행동 패턴
- 주 이용 매체/채널

**3단계(전략 기획) 완료 조건:**
- 주력 마케팅 채널 결정
- 예산 범위 및 배분
- 브랜드 톤앤매너
- 차별화 전략

**4단계(실행 계획) 완료 조건:**
- 구체적 콘텐츠 유형 결정
- 제작/발행 일정
- 필요 리소스 파악
- 성과 측정 계획

**분석 기준:**
- 필수 정보 완성도 (0.0-1.0)
- 정보 품질과 구체성
- 다음 단계 진행 가능 여부
- 부족한 정보 우선순위

JSON으로 분석 결과를 제공하세요."""

    async def analyze_stage_progress(self, stage: MarketingStage, user_input: str, 
                                   state: FlexibleConversationState, context: Dict[str, Any]) -> Dict[str, Any]:
        """단계 진행 상황 분석"""
        
        logger.info(f"[진행 추적] {stage.value} 단계 진행 분석 시작")
        
        # 사용자 입력에서 새로운 정보 추출
        await self._extract_and_update_information(user_input, stage, state)
        
        # 현재 단계의 수집된 정보 분석
        stage_info = self._get_stage_relevant_info(stage, state)
        
        progress_prompt = f"""현재 {stage.value} 단계의 진행 상황을 분석해주세요.

**사용자 최신 입력:** "{user_input}"

**현재 단계:** {stage.value}

**수집된 관련 정보:**
{json.dumps(stage_info, ensure_ascii=False, indent=2)}

**전체 수집 정보 개수:** {len(state.collected_info)}개

**컨텍스트:**
- 업종: {context.get('business_type', '일반')}
- 진행 방식: {context.get('conversation_mode', 'flexible')}

다음을 JSON 형태로 분석해주세요:
{{
    "completion_analysis": {{
        "completion_rate": 0.0-1.0,
        "essential_info_collected": ["수집된 핵심 정보들"],
        "missing_essential_info": ["부족한 핵심 정보들"],
        "quality_score": 0.0-1.0,
        "specificity_level": "low|medium|high"
    }},
    "readiness_for_next": {{
        "is_ready": true/false,
        "confidence": 0.0-1.0,
        "blocking_issues": ["다음 단계 진행을 막는 요소들"],
        "recommendations": ["개선을 위한 제안들"]
    }},
    "information_gaps": {{
        "critical_missing": ["즉시 필요한 정보"],
        "nice_to_have": ["있으면 좋은 추가 정보"],
        "follow_up_questions": ["후속 질문 제안"]
    }},
    "progress_decision": {{
        "should_continue_current": true/false,
        "should_ask_follow_up": true/false,
        "should_move_next": true/false,
        "reasoning": "결정 이유"
    }}
}}"""

        try:
            messages = [
                SystemMessage(content=self.progress_analysis_system_prompt),
                HumanMessage(content=progress_prompt)
            ]
            
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            raw_response = llm.invoke(messages)
            response = str(raw_response.content) if hasattr(raw_response, 'content') else str(raw_response)
            
            # JSON 파싱
            if isinstance(response, str):
                cleaned = clean_json_response(response)
                try:
                    analysis_result = json.loads(cleaned)
                    logger.info(f"[진행 추적] 완료율: {analysis_result.get('completion_analysis', {}).get('completion_rate', 0):.1%}")
                    return analysis_result
                except json.JSONDecodeError:
                    logger.warning(f"JSON 파싱 실패: {cleaned[:100]}")
                    return self._create_default_progress_analysis(stage)
            
            return response
            
        except Exception as e:
            logger.error(f"단계 진행 분석 실패: {e}")
            return self._create_default_progress_analysis(stage)

    async def _extract_and_update_information(self, user_input: str, stage: MarketingStage, 
                                            state: FlexibleConversationState):
        """사용자 입력에서 정보 추출 및 업데이트"""
        
        extraction_prompt = f"""사용자의 {stage.value} 단계 답변에서 마케팅 정보를 추출해주세요.

사용자 입력: "{user_input}"
현재 단계: {stage.value}

단계별 추출 대상:
{self._get_extraction_targets(stage)}

JSON 형태로 추출된 정보를 제공해주세요:
{{
    "extracted_info": {{
        "key1": "value1",
        "key2": "value2"
    }},
    "confidence_scores": {{
        "key1": 0.0-1.0,
        "key2": 0.0-1.0
    }},
    "additional_insights": ["추가로 파악된 인사이트들"]
}}"""

        try:
            messages = [
                SystemMessage(content="마케팅 정보 추출 전문가입니다. 사용자 입력에서 정확한 정보만 추출합니다."),
                HumanMessage(content=extraction_prompt)
            ]
            
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            raw_response = llm.invoke(messages)
            response = str(raw_response.content) if hasattr(raw_response, 'content') else str(raw_response)
            
            # JSON 파싱
            if isinstance(response, str):
                cleaned = clean_json_response(response)
                try:
                    extraction_result = json.loads(cleaned)
                    
                    # 추출된 정보를 상태에 업데이트
                    extracted_info = extraction_result.get("extracted_info", {})
                    confidence_scores = extraction_result.get("confidence_scores", {})
                    
                    for key, value in extracted_info.items():
                        if value and value.strip():
                            confidence = confidence_scores.get(key, 0.8)
                            state.add_information(
                                key, 
                                value, 
                                f"{stage.value}_extraction"
                            )
                            # 신뢰도 점수도 저장
                            if key in state.collected_info:
                                state.collected_info[key]["confidence"] = confidence
                    
                    logger.info(f"[정보 추출] {len(extracted_info)}개 정보 업데이트 완료")
                    
                except json.JSONDecodeError:
                    logger.warning(f"정보 추출 JSON 파싱 실패: {cleaned[:100]}")
                    
        except Exception as e:
            logger.error(f"정보 추출 실패: {e}")

    def _get_extraction_targets(self, stage: MarketingStage) -> str:
        """단계별 정보 추출 대상"""
        targets = {
            MarketingStage.STAGE_1_GOAL: """
- goals_main_goal: 주요 마케팅 목표
- goals_target_metrics: 성공 지표 (KPI)
- goals_timeline: 목표 달성 기한
- business_info_business_type: 업종/비즈니스 유형
- business_info_scale: 사업 규모
- goals_background: 현재 상황/배경
            """,
            MarketingStage.STAGE_2_TARGET: """
- target_audience_age_group: 타겟 연령대
- target_audience_gender: 성별
- target_audience_location: 지역
- target_audience_interests: 관심사/취미
- target_audience_behavior: 구매/행동 패턴
- target_audience_channels: 주 이용 매체
- target_audience_lifestyle: 라이프스타일
            """,
            MarketingStage.STAGE_3_STRATEGY: """
- marketing_info_channels: 주력 마케팅 채널
- marketing_info_budget: 예산 범위
- marketing_info_tone: 브랜드 톤앤매너
- marketing_info_differentiation: 차별화 포인트
- marketing_info_timeline: 마케팅 일정
- marketing_info_competitors: 주요 경쟁사
            """,
            MarketingStage.STAGE_4_EXECUTION: """
- execution_content_type: 콘텐츠 유형
- execution_timeline: 제작/발행 일정
- execution_resources: 필요 리소스
- execution_tools: 사용 도구
- execution_measurement: 성과 측정 방법
- execution_frequency: 콘텐츠 발행 주기
            """
        }
        return targets.get(stage, "일반적인 마케팅 정보")

    def _get_stage_relevant_info(self, stage: MarketingStage, state: FlexibleConversationState) -> Dict[str, Any]:
        """단계별 관련 정보 추출"""
        
        stage_keywords = {
            MarketingStage.STAGE_1_GOAL: ['goals_', 'business_info_'],
            MarketingStage.STAGE_2_TARGET: ['target_audience_'],
            MarketingStage.STAGE_3_STRATEGY: ['marketing_info_'],
            MarketingStage.STAGE_4_EXECUTION: ['execution_']
        }
        
        keywords = stage_keywords.get(stage, [])
        relevant_info = {}
        
        for key, value_data in state.collected_info.items():
            if any(keyword in key for keyword in keywords):
                relevant_info[key] = {
                    "value": value_data["value"],
                    "confidence": value_data.get("confidence", 0.8),
                    "source": value_data.get("source", "unknown")
                }
        
        return relevant_info

    def check_stage_completion(self, stage: MarketingStage, state: FlexibleConversationState) -> Tuple[bool, float, List[str]]:
        """단계 완료 여부 체크"""
        
        # 단계별 필수 정보 리스트
        essential_keys = {
            MarketingStage.STAGE_1_GOAL: [
                'goals_main_goal', 'goals_target_metrics', 'business_info_business_type'
            ],
            MarketingStage.STAGE_2_TARGET: [
                'target_audience_age_group', 'target_audience_interests', 'target_audience_behavior'
            ],
            MarketingStage.STAGE_3_STRATEGY: [
                'marketing_info_channels', 'marketing_info_budget', 'marketing_info_tone'
            ],
            MarketingStage.STAGE_4_EXECUTION: [
                'execution_content_type', 'execution_timeline', 'execution_resources'
            ]
        }
        
        required_keys = essential_keys.get(stage, [])
        if not required_keys:
            return False, 0.0, []
        
        # 보유한 필수 정보 계산
        collected_keys = [key for key in required_keys if key in state.collected_info]
        completion_rate = len(collected_keys) / len(required_keys)
        
        # 부족한 정보 리스트
        missing_keys = [key for key in required_keys if key not in state.collected_info]
        
        # 완료 기준: 70% 이상의 필수 정보 수집
        is_completed = completion_rate >= 0.7
        
        logger.info(f"[완료 체크] {stage.value} - 완료율: {completion_rate:.1%}, 완료: {is_completed}")
        
        return is_completed, completion_rate, missing_keys

    def get_stage_progress_summary(self, state: FlexibleConversationState) -> Dict[str, Any]:
        """전체 단계 진행 현황 요약"""
        
        all_stages = [
            MarketingStage.STAGE_1_GOAL,
            MarketingStage.STAGE_2_TARGET,
            MarketingStage.STAGE_3_STRATEGY,
            MarketingStage.STAGE_4_EXECUTION
        ]
        
        stage_summaries = {}
        overall_progress = 0.0
        
        for stage in all_stages:
            is_completed, completion_rate, missing_keys = self.check_stage_completion(stage, state)
            stage_summaries[stage.value] = {
                "completed": is_completed,
                "completion_rate": completion_rate,
                "missing_count": len(missing_keys),
                "missing_keys": missing_keys
            }
            overall_progress += completion_rate
        
        overall_progress /= len(all_stages)
        
        return {
            "overall_progress": overall_progress,
            "current_stage": state.current_stage.value,
            "stage_details": stage_summaries,
            "total_info_collected": len(state.collected_info),
            "is_conversation_complete": overall_progress >= 0.8
        }

    def recommend_next_action(self, progress_analysis: Dict[str, Any], 
                           state: FlexibleConversationState) -> Dict[str, Any]:
        """다음 액션 추천"""
        
        completion_analysis = progress_analysis.get("completion_analysis", {})
        readiness = progress_analysis.get("readiness_for_next", {})
        decision = progress_analysis.get("progress_decision", {})
        
        completion_rate = completion_analysis.get("completion_rate", 0.0)
        is_ready = readiness.get("is_ready", False)
        
        # 액션 결정 로직
        if completion_rate >= 0.8 and is_ready:
            action = "move_to_next_stage"
            message = "현재 단계가 완료되었습니다. 다음 단계로 진행하겠습니다!"
            
        elif completion_rate >= 0.5 and decision.get("should_ask_follow_up", True):
            action = "ask_follow_up"
            message = "좀 더 구체적인 정보가 필요합니다. 추가 질문을 드리겠습니다."
            
        elif completion_rate < 0.3:
            action = "continue_current_stage"
            message = "현재 단계를 계속 진행하겠습니다."
            
        else:
            action = "provide_interim_summary"
            message = "현재까지의 정보를 정리해보겠습니다."
        
        return {
            "recommended_action": action,
            "message": message,
            "completion_rate": completion_rate,
            "confidence": readiness.get("confidence", 0.5),
            "reasoning": decision.get("reasoning", "진행 상황 분석 결과")
        }

    def _create_default_progress_analysis(self, stage: MarketingStage) -> Dict[str, Any]:
        """기본 진행 분석 결과"""
        return {
            "completion_analysis": {
                "completion_rate": 0.3,
                "essential_info_collected": [],
                "missing_essential_info": ["기본 정보"],
                "quality_score": 0.5,
                "specificity_level": "medium"
            },
            "readiness_for_next": {
                "is_ready": False,
                "confidence": 0.3,
                "blocking_issues": ["추가 정보 필요"],
                "recommendations": ["더 구체적인 정보 제공 필요"]
            },
            "information_gaps": {
                "critical_missing": ["핵심 정보"],
                "nice_to_have": ["추가 정보"],
                "follow_up_questions": ["구체적인 내용을 알려주세요"]
            },
            "progress_decision": {
                "should_continue_current": True,
                "should_ask_follow_up": True,
                "should_move_next": False,
                "reasoning": "더 많은 정보가 필요합니다"
            }
        }

    async def generate_progress_feedback(self, progress_analysis: Dict[str, Any],
                                       stage: MarketingStage, state: FlexibleConversationState) -> str:
        """진행 상황 피드백 생성"""
        
        completion_rate = progress_analysis.get("completion_analysis", {}).get("completion_rate", 0.0)
        collected_info = progress_analysis.get("completion_analysis", {}).get("essential_info_collected", [])
        missing_info = progress_analysis.get("completion_analysis", {}).get("missing_essential_info", [])
        
        feedback_prompt = f"""현재 {stage.value} 단계의 진행 상황에 대한 사용자 피드백을 생성해주세요.

**진행 상황:**
- 완료율: {completion_rate:.1%}
- 수집된 정보: {collected_info}
- 부족한 정보: {missing_info}

**요구사항:**
1. 긍정적이고 격려하는 톤
2. 현재 진행 상황 간단 요약
3. 다음에 필요한 것 명확히 제시
4. 사용자의 참여 동기 부여

JSON 형태로 생성:
{{
    "progress_message": "진행 상황 메시지",
    "encouragement": "격려 멘트",
    "next_steps": "다음 단계 안내"
}}"""

        try:
            messages = [
                SystemMessage(content="마케팅 상담에서 사용자에게 도움이 되는 피드백을 제공하는 전문가입니다."),
                HumanMessage(content=feedback_prompt)
            ]
            
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            raw_response = llm.invoke(messages)
            response = str(raw_response.content) if hasattr(raw_response, 'content') else str(raw_response)
            
            # JSON 파싱
            if isinstance(response, str):
                cleaned = clean_json_response(response)
                try:
                    feedback_data = json.loads(cleaned)
                    
                    feedback = f"📊 **진행 현황 ({completion_rate:.0%})**\n\n"
                    feedback += f"{feedback_data.get('progress_message', '정보 수집 중입니다.')}\n\n"
                    feedback += f"💪 {feedback_data.get('encouragement', '잘 진행하고 있습니다!')}\n\n"
                    feedback += f"⏭️ **다음 단계**: {feedback_data.get('next_steps', '계속 진행하겠습니다.')}"
                    
                    return feedback
                    
                except json.JSONDecodeError:
                    logger.warning(f"피드백 JSON 파싱 실패: {cleaned[:100]}")
            
            return f"현재 {completion_rate:.0%} 완료되었습니다. 계속 진행하겠습니다!"
            
        except Exception as e:
            logger.error(f"진행 피드백 생성 실패: {e}")
            return f"현재 {completion_rate:.0%} 완료되었습니다. 계속 진행하겠습니다!"

    def _create_default_progress_analysis(self, stage: MarketingStage) -> Dict[str, Any]:
        """기본 진행 분석 결과"""
        return {
            "completion_analysis": {
                "completion_rate": 0.3,
                "essential_info_collected": [],
                "missing_essential_info": ["기본 정보"],
                "quality_score": 0.5,
                "specificity_level": "medium"
            },
            "readiness_for_next": {
                "is_ready": False,
                "confidence": 0.3,
                "blocking_issues": ["추가 정보 필요"],
                "recommendations": ["더 구체적인 정보 제공 필요"]
            },
            "information_gaps": {
                "critical_missing": ["핵심 정보"],
                "nice_to_have": ["추가 정보"],
                "follow_up_questions": ["구체적인 내용을 알려주세요"]
            },
            "progress_decision": {
                "should_continue_current": True,
                "should_ask_follow_up": True,
                "should_move_next": False,
                "reasoning": "더 많은 정보가 필요합니다"
            }
        }
