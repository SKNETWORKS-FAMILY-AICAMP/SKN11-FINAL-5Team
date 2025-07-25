"""
Business Planning Agent Utilities
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# OpenAI 챗봇 임포트
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

# 비즈니스 기획 토픽 정의
BUSINESS_TOPICS = {
    "startup_preparation": "창업 준비 및 체크리스트",
    "idea_validation": "아이디어 검증 및 시장성 분석",
    "business_model": "비즈니스 모델 및 린캔버스",
    "market_research": "시장 조사 및 경쟁 분석",
    "mvp_development": "MVP 개발 및 초기 제품 설계",
    "funding_strategy": "자금 조달 및 투자 유치",
    "business_registration": "사업자 등록 및 법적 절차",
    "financial_planning": "재무 계획 및 예산 관리",
    "growth_strategy": "성장 전략 및 확장 계획",
    "risk_management": "리스크 관리 및 위기 대응"
}

# 단계별 정보 수집 질문 템플릿
INFO_GATHERING_QUESTIONS = {
    "business_idea": "어떤 비즈니스 아이디어를 가지고 계신가요?",
    "industry": "어떤 업종/산업 분야인가요?",
    "target_customers": "주요 타겟 고객은 누구인가요?",
    "unique_value": "기존과 다른 차별점이나 고유 가치는 무엇인가요?",
    "business_stage": "현재 어느 단계에 있나요? (아이디어/준비/운영 등)",
    "budget": "초기 투자 가능한 예산은 어느 정도인가요?",
    "timeline": "언제까지 사업을 시작하고 싶으신가요?",
    "location": "사업 지역이나 위치가 정해져 있나요?",
    "team_size": "혼자 시작하시나요? 팀이 있나요?",
    "experience": "관련 업계 경험이나 전문성이 있으신가요?",
    "goals": "1-2년 내 달성하고 싶은 목표는 무엇인가요?",
    "concerns": "가장 걱정되거나 어려운 부분은 무엇인가요?"
}

def get_business_topics() -> Dict[str, str]:
    """비즈니스 토픽 반환"""
    return BUSINESS_TOPICS

def get_info_gathering_questions() -> Dict[str, str]:
    """정보 수집 질문 반환"""
    return INFO_GATHERING_QUESTIONS

def format_topic_prompts(topic_prompts: Dict[str, str], business_topics: Dict[str, str]) -> str:
    """토픽별 프롬프트를 분석용으로 포맷팅"""
    if not topic_prompts:
        return "기본 비즈니스 분석 수행"
    
    formatted = []
    for topic, prompt_content in topic_prompts.items():
        topic_name = business_topics.get(topic, topic)
        formatted.append(f"[{topic_name}]\n{prompt_content}\n")
    
    return "\n".join(formatted)

def format_business_summary(business_info: Dict[str, Any], questions: Dict[str, str]) -> str:
    """비즈니스 정보 요약 포맷팅"""
    try:
        summary_parts = []
        
        key_mappings = {
            "business_idea": "💡 아이디어",
            "industry": "🏢 업종",
            "target_customers": "👥 타겟",
            "unique_value": "⭐ 차별점",
            "business_stage": "📍 현재 단계",
            "budget": "💰 예산",
            "timeline": "⏰ 타임라인",
            "goals": "🎯 목표"
        }
        
        for field, value in business_info.items():
            if value and field in key_mappings:
                summary_parts.append(f"{key_mappings[field]}: {value}")
        
        return "\n".join(summary_parts) if summary_parts else "수집된 정보가 부족합니다."
        
    except Exception as e:
        logger.error(f"비즈니스 요약 포맷팅 실패: {e}")
        return "요약 생성 중 오류가 발생했습니다."

def extract_business_info_with_llm(
    llm_manager, 
    user_input: str, 
    current_info: Dict[str, Any], 
    questions: Dict[str, str]
) -> Dict[str, Any]:
    """LLM을 활용한 비즈니스 정보 추출"""
    try:
        extraction_prompt = f"""사용자의 답변에서 비즈니스 관련 정보를 추출해주세요.

사용자 답변: "{user_input}"

현재 수집된 정보:
{json.dumps(current_info, ensure_ascii=False, indent=2)}

추출 가능한 정보 항목들:
{chr(10).join([f"- {key}: {value}" for key, value in questions.items()])}

사용자 답변에서 추출할 수 있는 정보를 다음 JSON 형태로 제공해주세요:
{{
    "field_name": "추출된 정보 값"
}}

정보가 명확하지 않으면 빈 객체 {{}}를 반환해주세요.

추출 결과:"""

        messages = [
            {"role": "system", "content": "당신은 사용자 답변에서 비즈니스 관련 정보를 정확히 추출하는 전문가입니다."},
            {"role": "user", "content": extraction_prompt}
        ]
        
        response = llm_manager.generate_response_sync(convert_messages_to_dict(messages), output_format="json")
        
        if isinstance(response, dict):
            return response
        elif isinstance(response, str):
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass
        
        return {}
        
    except Exception as e:
        logger.error(f"LLM 정보 추출 실패: {e}")
        return {}

def validate_conversation_completeness(business_info: Dict[str, Any], questions: Dict[str, str]) -> Dict[str, Any]:
    """대화 완료도 검증"""
    try:
        result = {
            "is_complete": False,
            "completion_rate": 0.0,
            "missing_fields": [],
            "completed_fields": [],
            "critical_missing": []
        }
        
        # 필수 필드 정의
        critical_fields = ["business_idea", "industry", "target_customers", "goals"]
        
        for field, question in questions.items():
            if business_info.get(field):
                result["completed_fields"].append(field)
            else:
                result["missing_fields"].append(field)
                if field in critical_fields:
                    result["critical_missing"].append(field)
        
        # 완료율 계산
        total_fields = len(questions)
        completed_fields = len(result["completed_fields"])
        result["completion_rate"] = completed_fields / total_fields if total_fields > 0 else 0.0
        
        # 완료 여부 판단 (필수 필드 모두 완료 또는 전체 70% 이상 완료)
        result["is_complete"] = (
            len(result["critical_missing"]) == 0 or 
            result["completion_rate"] >= 0.7
        )
        
        return result
        
    except Exception as e:
        logger.error(f"대화 완료도 검증 실패: {e}")
        return {
            "is_complete": False,
            "completion_rate": 0.0,
            "missing_fields": list(questions.keys()),
            "completed_fields": [],
            "critical_missing": ["business_idea", "industry", "target_customers", "goals"]
        }

def generate_single_turn_response(
    llm_manager,
    user_input: str,
    business_topics: Dict[str, str],
    classify_func,
    load_prompt_func,
    get_knowledge_func
) -> str:
    """싱글톤 응답 생성"""
    try:
        # 토픽 분류
        topics = classify_func(user_input)
        
        # 토픽별 프롬프트 로드
        topic_prompts = {}
        for topic in topics:
            prompt_content = load_prompt_func(topic)
            if prompt_content:
                topic_prompts[topic] = prompt_content
        
        # 관련 지식 검색
        relevant_knowledge = get_knowledge_func(user_input, topics)
        
        # 응답 생성 프롬프트
        response_prompt = f"""사용자의 비즈니스 관련 질문에 전문가 수준의 답변을 제공해주세요.

사용자 질문: "{user_input}"

관련 비즈니스 토픽: {', '.join(topics)}

토픽별 전문 지침:
{format_topic_prompts(topic_prompts, business_topics)}

관련 전문 지식:
{chr(10).join(relevant_knowledge) if relevant_knowledge else "기본 비즈니스 지식 활용"}

위 정보를 바탕으로 다음 요소를 포함한 실용적인 답변을 제공해주세요:
1. 질문에 대한 직접적인 답변
2. 실행 가능한 구체적인 조언
3. 주의사항이나 고려사항
4. 필요시 추가 정보나 다음 단계 제안

전문적이면서도 이해하기 쉬운 답변을 제공해주세요."""

        messages = [
            {"role": "system", "content": "당신은 비즈니스 기획 전문가로서 실용적이고 실행 가능한 조언을 제공합니다."},
            {"role": "user", "content": response_prompt}
        ]
        # ChatOpenAI 인스턴스를 직접 사용
        llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
        raw_response = llm.invoke(messages)
        response = str(raw_response.content) if hasattr(raw_response, 'content') else str(raw_response)
        
        if isinstance(response, dict):
            return response
        elif isinstance(response, str):
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass
        
        return response if response else "죄송합니다. 답변 생성 중 오류가 발생했습니다."
        
    except Exception as e:
        logger.error(f"싱글톤 응답 생성 실패: {e}")
        return "요청 처리 중 오류가 발생했습니다. 다시 시도해주세요."

def create_conversation_state_summary(state) -> Dict[str, Any]:
    """대화 상태 요약 생성"""
    try:
        return {
            "conversation_id": state.conversation_id,
            "current_stage": state.stage.value,
            "completion_rate": state.get_completion_rate(),
            "collected_info_count": len([v for v in state.collected_info.values() if v]),
            "total_info_fields": len(state.collected_info),
            "analysis_completed": bool(state.analysis_results.get("analysis_content")),
            "last_updated": state.updated_at.isoformat() if state.updated_at else None,
            "feedback_count": len(state.feedback_history),
            "primary_topics": state.analysis_results.get("primary_topics", [])
        }
        
    except Exception as e:
        logger.error(f"대화 상태 요약 생성 실패: {e}")
        return {
            "conversation_id": getattr(state, 'conversation_id', None),
            "current_stage": "unknown",
            "completion_rate": 0.0,
            "error": "요약 생성 실패"
        }

def get_next_action_recommendations(business_info: Dict[str, Any], stage: str) -> List[str]:
    """현재 단계에 따른 다음 액션 추천"""
    try:
        recommendations = []
        
        if stage == "initial" or stage == "info_gathering":
            if not business_info.get("business_idea"):
                recommendations.append("비즈니스 아이디어를 구체화해보세요")
            if not business_info.get("target_customers"):
                recommendations.append("타겟 고객을 명확히 정의해보세요")
            if not business_info.get("unique_value"):
                recommendations.append("경쟁 우위나 차별점을 찾아보세요")
                
        elif stage == "analysis":
            recommendations.extend([
                "시장 조사를 통해 경쟁 현황을 파악해보세요",
                "MVP(최소 실행 가능 제품) 개념을 설계해보세요",
                "초기 비용과 수익 모델을 계획해보세요"
            ])
            
        elif stage == "planning":
            recommendations.extend([
                "구체적인 실행 계획과 타임라인을 수립해보세요",
                "필요한 자원과 팀 구성을 계획해보세요",
                "마케팅 전략을 구체화해보세요"
            ])
        
        return recommendations[:3]  # 최대 3개까지
        
    except Exception as e:
        logger.error(f"다음 액션 추천 실패: {e}")
        return ["현재 상황을 점검하고 우선순위를 정리해보세요"]

def calculate_business_readiness_score(business_info: Dict[str, Any]) -> float:
    """비즈니스 준비도 점수 계산 (0.0 ~ 1.0)"""
    try:
        score = 0.0
        total_weight = 0.0
        
        # 가중치 설정
        field_weights = {
            "business_idea": 0.2,      # 20%
            "industry": 0.1,           # 10%
            "target_customers": 0.15,  # 15%
            "unique_value": 0.15,      # 15%
            "business_stage": 0.1,     # 10%
            "budget": 0.1,             # 10%
            "timeline": 0.05,          # 5%
            "experience": 0.1,         # 10%
            "goals": 0.05              # 5%
        }
        
        for field, weight in field_weights.items():
            total_weight += weight
            if business_info.get(field):
                score += weight
        
        return min(score / total_weight, 1.0) if total_weight > 0 else 0.0
        
    except Exception as e:
        logger.error(f"준비도 점수 계산 실패: {e}")
        return 0.0

def analyze_business_complexity_with_llm(llm_manager, user_input: str) -> Dict[str, Any]:
    """LLM 기반 비즈니스 복잡도 분석"""
    try:
        complexity_prompt = f"""다음 사용자 질문의 비즈니스 복잡도를 분석해주세요.

사용자 질문: "{user_input}"

다음 JSON 형태로 분석 결과를 제공해주세요:
{{
    "complexity_level": "simple|moderate|complex",
    "requires_consultation": true/false,
    "estimated_time": "quick|medium|extensive",
    "key_topics": ["관련 주요 토픽들"],
    "immediate_answerable": true/false,
    "reasoning": "판단 근거"
}}

분석 기준:
- simple: 일반적인 정보 문의, 즉시 답변 가능
- moderate: 약간의 분석이 필요하지만 단일 응답으로 해결 가능
- complex: 체계적인 상담과 정보 수집이 필요

분석 결과:"""

        messages = [
            {"role": "system", "content": "당신은 비즈니스 질문의 복잡도를 정확히 분석하는 전문가입니다."},
            {"role": "user", "content": complexity_prompt}
        ]
        
        response = llm_manager.generate_response_sync(convert_messages_to_dict(messages), output_format="json")
        
        if isinstance(response, dict):
            return response
        elif isinstance(response, str):
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass
        
        return {
            "complexity_level": "moderate",
            "requires_consultation": True,
            "estimated_time": "medium",
            "key_topics": [],
            "immediate_answerable": False,
            "reasoning": "분석 실패로 인한 기본값"
        }
        
    except Exception as e:
        logger.error(f"LLM 복잡도 분석 실패: {e}")
        return {
            "complexity_level": "moderate",
            "requires_consultation": True,
            "estimated_time": "medium",
            "key_topics": [],
            "immediate_answerable": False,
            "reasoning": f"분석 중 오류 발생: {str(e)}"
        }

def generate_adaptive_response_with_llm(
    llm_manager,
    user_input: str,
    business_info: Dict[str, Any],
    conversation_history: List[str] = None
) -> str:
    """LLM 기반 적응형 응답 생성"""
    try:
        context = ""
        if conversation_history:
            context = f"\n대화 기록:\n{chr(10).join(conversation_history[-3:])}"  # 최근 3개만
        
        if business_info and any(business_info.values()):
            context += f"\n\n수집된 비즈니스 정보:\n{format_business_summary(business_info, INFO_GATHERING_QUESTIONS)}"
        
        adaptive_prompt = f"""사용자와의 비즈니스 상담에서 가장 적절한 응답을 생성해주세요.

사용자 입력: "{user_input}"
{context}

응답 가이드라인:
1. 사용자의 현재 상황과 니즈에 맞춰 개인화된 답변 제공
2. 구체적이고 실행 가능한 조언 포함
3. 필요시 다음 단계나 추가 정보 요청
4. 전문적이면서도 친근한 톤 유지
5. 비즈니스 실무에 도움이 되는 실용적 내용 중심

위 가이드라인에 따라 맞춤형 응답을 제공해주세요."""

        messages = [
            {"role": "system", "content": "당신은 경험 많은 비즈니스 컨설턴트로서 개인의 상황에 맞는 맞춤형 조언을 제공합니다."},
            {"role": "user", "content": adaptive_prompt}
        ]
        
        response = llm_manager.generate_response_sync(convert_messages_to_dict(messages))
        return response if response else "적절한 응답을 생성할 수 없습니다."
        
    except Exception as e:
        logger.error(f"적응형 응답 생성 실패: {e}")
        return "응답 생성 중 오류가 발생했습니다."
