"""
Business Planning Agent Utilities
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def analyze_business_stage(business_info: Dict[str, Any]) -> str:
    """비즈니스 단계 분석"""
    try:
        stage = business_info.get("business_stage", "").lower()
        idea = business_info.get("business_idea", "")
        
        if "아이디어" in stage or not stage:
            return "idea_stage"
        elif "준비" in stage or "계획" in stage:
            return "preparation_stage"
        elif "운영" in stage or "시작" in stage:
            return "operation_stage"
        else:
            return "unknown_stage"
            
    except Exception as e:
        logger.error(f"비즈니스 단계 분석 실패: {e}")
        return "unknown_stage"

def calculate_risk_score(business_info: Dict[str, Any]) -> float:
    """리스크 점수 계산 (0.0 ~ 1.0)"""
    try:
        risk_factors = []
        
        # 예산 리스크
        budget = business_info.get("budget", "")
        if not budget or "적음" in budget or "부족" in budget:
            risk_factors.append(0.3)
        
        # 경험 리스크
        experience = business_info.get("experience", "")
        if not experience or "없음" in experience:
            risk_factors.append(0.2)
        
        # 팀 리스크
        team_size = business_info.get("team_size", "")
        if "혼자" in team_size or not team_size:
            risk_factors.append(0.1)
        
        return min(sum(risk_factors), 1.0)
        
    except Exception as e:
        logger.error(f"리스크 점수 계산 실패: {e}")
        return 0.5

def suggest_next_steps(business_info: Dict[str, Any]) -> List[str]:
    """다음 단계 제안"""
    try:
        stage = analyze_business_stage(business_info)
        
        if stage == "idea_stage":
            return [
                "아이디어 구체화 및 검증",
                "시장 조사 및 경쟁 분석",
                "MVP 설계 및 프로토타입 제작"
            ]
        elif stage == "preparation_stage":
            return [
                "사업자 등록 및 법적 절차",
                "초기 자금 조달 계획",
                "팀 구성 및 역할 분담"
            ]
        elif stage == "operation_stage":
            return [
                "마케팅 및 고객 확보",
                "운영 프로세스 최적화",
                "성장 전략 수립"
            ]
        else:
            return [
                "현재 상황 점검 및 분석",
                "목표 재설정",
                "우선순위 정리"
            ]
            
    except Exception as e:
        logger.error(f"다음 단계 제안 실패: {e}")
        return ["현재 상황 점검이 필요합니다"]

def format_business_summary(business_info: Dict[str, Any]) -> str:
    """비즈니스 정보 요약 포맷팅"""
    try:
        summary_parts = []
        
        if business_info.get("business_idea"):
            summary_parts.append(f"💡 아이디어: {business_info['business_idea']}")
        
        if business_info.get("industry"):
            summary_parts.append(f"🏢 업종: {business_info['industry']}")
        
        if business_info.get("target_customers"):
            summary_parts.append(f"👥 타겟: {business_info['target_customers']}")
        
        if business_info.get("unique_value"):
            summary_parts.append(f"⭐ 차별점: {business_info['unique_value']}")
        
        return "\n".join(summary_parts) if summary_parts else "수집된 정보가 부족합니다."
        
    except Exception as e:
        logger.error(f"비즈니스 요약 포맷팅 실패: {e}")
        return "요약 생성 중 오류가 발생했습니다."

def validate_business_info(business_info: Dict[str, Any]) -> Dict[str, Any]:
    """비즈니스 정보 유효성 검증"""
    try:
        validation_result = {
            "is_valid": True,
            "missing_fields": [],
            "warnings": [],
            "score": 0.0
        }
        
        required_fields = ["business_idea", "industry", "target_customers", "goals"]
        
        for field in required_fields:
            if not business_info.get(field):
                validation_result["missing_fields"].append(field)
        
        # 점수 계산
        total_fields = len(business_info)
        filled_fields = len([v for v in business_info.values() if v])
        validation_result["score"] = filled_fields / total_fields if total_fields > 0 else 0.0
        
        # 유효성 판단
        validation_result["is_valid"] = len(validation_result["missing_fields"]) == 0
        
        # 경고사항
        if not business_info.get("budget"):
            validation_result["warnings"].append("예산 정보가 없으면 정확한 계획 수립이 어려울 수 있습니다")
        
        if not business_info.get("experience"):
            validation_result["warnings"].append("관련 경험이 없으면 추가 학습이 필요할 수 있습니다")
        
        return validation_result
        
    except Exception as e:
        logger.error(f"비즈니스 정보 검증 실패: {e}")
        return {
            "is_valid": False,
            "missing_fields": [],
            "warnings": ["검증 중 오류가 발생했습니다"],
            "score": 0.0
        }
