"""
마케팅 에이전트 정보 수집 모듈
"""

import json
import logging
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from .utils import clean_json_response
from .conversation_state import FlexibleConversationState

logger = logging.getLogger(__name__)


class InformationCollector:
    """정보 수집 관리 클래스"""
    
    def update_collected_information(self, user_input: str, intent_analysis: Dict[str, Any], 
                                   state: FlexibleConversationState):
        """수집된 정보 업데이트"""
        logger.info(f"[단계 로그] 정보 수집 시작 - 현재 수집된 정보: {len(state.collected_info)}개")
        
        # LLM을 사용해 사용자 입력에서 정보 추출
        extraction_prompt = f"""사용자 입력에서 마케팅 상담에 유용한 정보를 추출해주세요.

사용자 입력: "{user_input}"
기존 정보: {json.dumps(state.collected_info, ensure_ascii=False)}

다음 항목들을 JSON 형태로 추출해주세요:
{{
    "business_info": {{
        "business_type": "업종",
        "business_name": "사업명",
        "location": "위치",
        "scale": "규모"
    }},
    "goals": {{
        "main_goal": "주요 목적",
        "target_metrics": "목표 지표",
        "timeline": "목표 기한"
    }},
    "target_audience": {{
        "age_group": "연령대",
        "gender": "성별",
        "interests": "관심사",
        "behavior": "행동 패턴"
    }},
    "marketing_info": {{
        "budget": "예산",
        "channels": "선호 채널",
        "experience": "경험 수준",
        "tools": "사용 도구"
    }},
    "additional": {{
        "pain_points": "고민 사항",
        "preferences": "선호사항",
        "constraints": "제약사항"
    }}
}}

정보가 없는 항목은 null로 설정하세요."""

        try:
            messages = [
                SystemMessage(content="마케팅 정보 추출 전문가입니다. 사용자 입력에서 유용한 정보만 정확히 추출합니다."),
                HumanMessage(content=extraction_prompt)
            ]
            
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            raw_response = llm.invoke(messages)
            response = str(raw_response.content) if hasattr(raw_response, 'content') else str(raw_response)
            
            # JSON 파싱
            if isinstance(response, str):
                cleaned = clean_json_response(response)
                try:
                    extracted_info = json.loads(cleaned)
                    logger.info(f"[단계 로그] - 추출된 정보: {extracted_info}")
                    
                    # 추출된 정보를 상태에 업데이트
                    for category, info_dict in extracted_info.items():
                        if isinstance(info_dict, dict):
                            for key, value in info_dict.items():
                                if value and value != "null":
                                    state.add_information(f"{category}_{key}", value, "user_input")
                                    
                except json.JSONDecodeError:
                    logger.warning(f"JSON 파싱 실패: {cleaned[:100]}")
                    return
            
        except Exception as e:
            logger.error(f"정보 추출 실패: {e}")

    def prepare_conversation_context(self, user_id: int, conversation_id: int, 
                                   conversation_states: Dict[int, FlexibleConversationState]) -> Dict[str, Any]:
        """대화 컨텍스트 준비"""
        
        context = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "conversation_mode": "flexible",
            "current_stage": "any_question",
            "collected_info": {},
            "business_type": "일반",
            "history_summary": "새로운 대화"
        }
        
        if conversation_id and conversation_id in conversation_states:
            state = conversation_states[conversation_id]
            context.update({
                "current_stage": state.current_stage.value,
                "collected_info": state.collected_info,
                "business_type": state.detected_business_type,
                "history_summary": self.summarize_conversation_history(state)
            })
        
        return context

    def summarize_conversation_history(self, state: FlexibleConversationState) -> str:
        """대화 히스토리 요약"""
        
        if not hasattr(state, 'conversation_history') or not state.conversation_history:
            return "새로운 대화"
        
        # 최근 대화 요약 (간단하게)
        recent = state.conversation_history[-3:]
        collected_info = state.collected_info
        
        summary_parts = []
        if collected_info:
            summary_parts.append(f"수집된 정보: {len(collected_info)}개 항목")
        if state.detected_business_type != "일반":
            summary_parts.append(f"업종: {state.detected_business_type}")
        
        return " | ".join(summary_parts) if summary_parts else "마케팅 상담 진행 중"
