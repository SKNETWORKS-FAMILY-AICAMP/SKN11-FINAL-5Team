"""
마케팅 에이전트 유틸리티 함수들
"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def clean_json_response(response: str) -> str:
    """
    LLM 응답에서 코드블록(````json ... ````)을 제거하고 JSON만 추출
    """
    cleaned = response.strip()
    if cleaned.startswith("```"):
        # 첫번째 ``` 제거
        cleaned = cleaned.strip("`")
        # "json" 태그 제거
        cleaned = cleaned.replace("json", "", 1).strip()
        # 마지막 ``` 제거
        if cleaned.endswith("```"):
            cleaned = cleaned[:cleaned.rfind("```")].strip()
    return cleaned


def create_default_intent_analysis(user_input: str) -> Dict[str, Any]:
    """기본 의도 분석 결과 - 일반 질문은 immediate_answer로 처리"""
    return {
        "response_type": "immediate_answer",
        "user_intent": {
            "primary_goal": "마케팅 조언 및 정보 획득",
            "information_need": user_input,
            "urgency_level": "medium",
            "specificity": "general"
        },
        "flow_control": {
            "wants_immediate": True,
            "wants_structured": False,
            "stage_preference": "any",
            "control_command": "none",
            "auto_stage_jump": False
        },
        "context_needs": {
            "use_existing_info": True,
            "business_type_detection": "일반",
            "personalization_level": "medium"
        },
        "tool_requirements": {
            "needs_tool": False,
            "tool_type": "none",
            "target_keyword": "",
            "content_type": "general",
            "reasoning": "마케팅 조언은 바로 제공 가능",
            "stage_requirement_met": True
        },
        "suggested_action": "provide_immediate_marketing_advice"
    }


def create_default_progress_analysis(stage: str) -> Dict[str, Any]:
    """기본 진행 분석 결과 (진행 추적기용)"""
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


def create_default_action_result() -> Dict[str, Any]:
    """기본 액션 결과"""
    return {
        "recommended_action": "continue_immediate",
        "reasoning": "즉시 응답 제공",
        "parameters": {"immediate_response": True},
        "user_options": ["체계적 상담 시작", "추가 질문"],
        "follow_up": "상황에 따라 진행"
    }


def format_prompts_for_response(prompts: Dict[str, str]) -> str:
    """응답 생성용 프롬프트 포맷팅"""
    if not prompts:
        return "일반적인 마케팅 가이드라인을 활용합니다."
    
    formatted = []
    for name, content in prompts.items():
        # 프롬프트 내용을 요약해서 포함 (너무 길면 잘라냄)
        summary = content[:200] + "..." if len(content) > 200 else content
        formatted.append(f"[{name}] {summary}")
    
    return "\n".join(formatted)


def create_default_flow_analysis() -> Dict[str, Any]:
    """기본 플로우 분석 결과 (멀티턴 매니저용)"""
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


def extract_key_information(collected_info: Dict[str, Any], category: str) -> Dict[str, Any]:
    """수집된 정보에서 특정 카테고리 정보 추출"""
    category_info = {}
    for key, value_data in collected_info.items():
        if key.startswith(category + "_"):
            category_info[key] = value_data.get("value", "")
    return category_info


def calculate_information_completeness(collected_info: Dict[str, Any], required_keys: list) -> float:
    """필수 정보 대비 수집 완성도 계산"""
    if not required_keys:
        return 0.0
    
    collected_keys = [key for key in required_keys if key in collected_info]
    return len(collected_keys) / len(required_keys)


def format_stage_transition_message(from_stage: str, to_stage: str, completion_rate: float) -> str:
    """단계 전환 메시지 포맷팅"""
    stage_names = {
        "stage_1_goal": "1단계: 목표 정의",
        "stage_2_target": "2단계: 타겟 분석", 
        "stage_3_strategy": "3단계: 전략 기획",
        "stage_4_execution": "4단계: 실행 계획"
    }
    
    from_name = stage_names.get(from_stage, from_stage)
    to_name = stage_names.get(to_stage, to_stage)
    
    return f"✅ **{from_name} 완료!** ({completion_rate:.0%})\n\n🔄 **{to_name}**로 이동합니다."


def validate_stage_readiness(stage: str, collected_info: Dict[str, Any]) -> Dict[str, Any]:
    """단계별 진행 준비 상태 검증"""
    stage_requirements = {
        "stage_1_goal": ["goals_main_goal", "business_info_business_type"],
        "stage_2_target": ["target_audience_age_group", "target_audience_interests"],
        "stage_3_strategy": ["marketing_info_channels", "marketing_info_budget"],
        "stage_4_execution": ["execution_content_type", "execution_timeline"]
    }
    
    required = stage_requirements.get(stage, [])
    collected = [key for key in required if key in collected_info]
    missing = [key for key in required if key not in collected_info]
    
    completion = len(collected) / len(required) if required else 0.0
    is_ready = completion >= 0.7  # 70% 이상 완료 시 준비됨
    
    return {
        "is_ready": is_ready,
        "completion_rate": completion,
        "collected_keys": collected,
        "missing_keys": missing,
        "required_count": len(required),
        "collected_count": len(collected)
    }
