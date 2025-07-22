"""
Customer Service Agent Utilities
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def analyze_customer_sentiment(text: str) -> str:
    """고객 감정 분석"""
    try:
        text_lower = text.lower()
        
        # 부정적 키워드
        negative_keywords = ["불만", "화남", "짜증", "문제", "실망", "최악", "환불", "취소"]
        # 긍정적 키워드  
        positive_keywords = ["좋음", "만족", "감사", "훌륭", "추천", "최고", "완벽"]
        # 긴급 키워드
        urgent_keywords = ["급함", "긴급", "즉시", "당장", "빨리"]
        
        negative_count = sum(1 for keyword in negative_keywords if keyword in text_lower)
        positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
        urgent_count = sum(1 for keyword in urgent_keywords if keyword in text_lower)
        
        if urgent_count > 0:
            return "urgent"
        elif negative_count > positive_count:
            return "negative"
        elif positive_count > negative_count:
            return "positive"
        else:
            return "neutral"
            
    except Exception as e:
        logger.error(f"고객 감정 분석 실패: {e}")
        return "neutral"

def calculate_urgency_level(customer_info: Dict[str, Any]) -> str:
    """긴급도 계산"""
    try:
        urgency_factors = []
        
        # 감정 기반 긴급도
        sentiment = customer_info.get("customer_sentiment", "neutral")
        if sentiment == "urgent":
            urgency_factors.append("high")
        elif sentiment == "negative":
            urgency_factors.append("medium")
        
        # 이슈 타입 기반
        issue = customer_info.get("customer_issue", "").lower()
        if any(keyword in issue for keyword in ["환불", "취소", "불량", "오배송"]):
            urgency_factors.append("high")
        
        # 타임라인 기반
        timeline = customer_info.get("timeline", "").lower()
        if any(keyword in timeline for keyword in ["오늘", "즉시", "당장"]):
            urgency_factors.append("high")
        
        # 최고 긴급도 반환
        if "high" in urgency_factors:
            return "high"
        elif "medium" in urgency_factors:
            return "medium"
        else:
            return "low"
            
    except Exception as e:
        logger.error(f"긴급도 계산 실패: {e}")
        return "medium"

def suggest_response_tone(customer_sentiment: str, urgency_level: str) -> Dict[str, Any]:
    """응답 톤 제안"""
    try:
        tone_mapping = {
            ("positive", "low"): {
                "tone": "친근하고 감사하는 톤",
                "approach": "긍정적 관계 유지",
                "sample": "감사합니다! 더 나은 서비스로 보답하겠습니다."
            },
            ("neutral", "medium"): {
                "tone": "정중하고 전문적인 톤",
                "approach": "명확한 정보 제공",
                "sample": "말씀해주신 내용을 정확히 파악하여 도움을 드리겠습니다."
            },
            ("negative", "high"): {
                "tone": "공감하고 사과하는 톤",
                "approach": "즉시 문제 해결",
                "sample": "불편을 끼쳐드려 진심으로 죄송합니다. 즉시 해결해드리겠습니다."
            },
            ("urgent", "high"): {
                "tone": "신속하고 결단력 있는 톤",
                "approach": "즉시 대응",
                "sample": "긴급 상황으로 인지하고 최우선으로 처리하겠습니다."
            }
        }
        
        key = (customer_sentiment, urgency_level)
        return tone_mapping.get(key, tone_mapping[("neutral", "medium")])
        
    except Exception as e:
        logger.error(f"응답 톤 제안 실패: {e}")
        return {
            "tone": "정중하고 전문적인 톤",
            "approach": "문제 파악 및 해결",
            "sample": "고객님의 말씀을 정확히 파악하여 최선의 해결책을 제시하겠습니다."
        }

def categorize_customer_issue(issue_description: str) -> str:
    """고객 이슈 분류"""
    try:
        issue_lower = issue_description.lower()
        
        categories = {
            "product_issue": ["불량", "파손", "오작동", "품질", "결함"],
            "delivery_issue": ["배송", "늦음", "미도착", "오배송", "택배"],
            "service_issue": ["응대", "서비스", "직원", "태도", "불친절"],
            "billing_issue": ["결제", "요금", "청구", "환불", "취소"],
            "system_issue": ["사이트", "앱", "오류", "접속", "로그인"],
            "general_inquiry": ["문의", "질문", "정보", "안내"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in issue_lower for keyword in keywords):
                return category
        
        return "general_inquiry"
        
    except Exception as e:
        logger.error(f"고객 이슈 분류 실패: {e}")
        return "general_inquiry"

def generate_follow_up_questions(customer_info: Dict[str, Any]) -> List[str]:
    """후속 질문 생성"""
    try:
        questions = []
        
        issue_category = categorize_customer_issue(customer_info.get("customer_issue", ""))
        
        if issue_category == "product_issue":
            questions = [
                "구체적으로 어떤 문제가 발생했나요?",
                "언제부터 이 문제가 시작되었나요?",
                "사진이나 영상으로 문제 상황을 보여주실 수 있나요?"
            ]
        elif issue_category == "delivery_issue":
            questions = [
                "주문 번호를 알려주실 수 있나요?",
                "배송 주소가 정확한가요?",
                "배송 예정일은 언제였나요?"
            ]
        elif issue_category == "service_issue":
            questions = [
                "어떤 상황에서 발생한 일인가요?",
                "담당자나 매장 정보를 알려주세요",
                "구체적으로 어떤 부분이 불만족스러우셨나요?"
            ]
        else:
            questions = [
                "더 자세한 상황을 설명해주실 수 있나요?",
                "이전에 유사한 경험이 있으셨나요?",
                "어떤 도움을 원하시나요?"
            ]
        
        return questions[:3]  # 최대 3개
        
    except Exception as e:
        logger.error(f"후속 질문 생성 실패: {e}")
        return ["더 자세한 정보를 알려주실 수 있나요?"]

def estimate_resolution_time(issue_category: str, urgency_level: str) -> str:
    """해결 시간 예상"""
    try:
        time_matrix = {
            ("product_issue", "high"): "24시간 이내",
            ("product_issue", "medium"): "2-3일",
            ("product_issue", "low"): "3-5일",
            ("delivery_issue", "high"): "즉시 확인 후 당일 연락",
            ("delivery_issue", "medium"): "1-2일",
            ("delivery_issue", "low"): "2-3일",
            ("service_issue", "high"): "즉시 처리",
            ("service_issue", "medium"): "당일 처리",
            ("service_issue", "low"): "1-2일",
            ("billing_issue", "high"): "즉시 처리",
            ("billing_issue", "medium"): "당일 처리", 
            ("billing_issue", "low"): "1-2일",
            ("system_issue", "high"): "긴급 수정 (수시간 이내)",
            ("system_issue", "medium"): "1일 이내",
            ("system_issue", "low"): "2-3일",
            ("general_inquiry", "high"): "즉시 답변",
            ("general_inquiry", "medium"): "당일 답변",
            ("general_inquiry", "low"): "1-2일 내 답변"
        }
        
        key = (issue_category, urgency_level)
        return time_matrix.get(key, "2-3일 내 처리")
        
    except Exception as e:
        logger.error(f"해결 시간 예상 실패: {e}")
        return "신속히 처리하겠습니다"

def validate_customer_info(customer_info: Dict[str, Any]) -> Dict[str, Any]:
    """고객 정보 유효성 검증"""
    try:
        validation_result = {
            "is_valid": True,
            "missing_fields": [],
            "warnings": [],
            "score": 0.0
        }
        
        required_fields = ["business_type", "customer_issue", "desired_outcome"]
        
        for field in required_fields:
            if not customer_info.get(field):
                validation_result["missing_fields"].append(field)
        
        # 점수 계산
        total_fields = len(customer_info)
        filled_fields = len([v for v in customer_info.values() if v])
        validation_result["score"] = filled_fields / total_fields if total_fields > 0 else 0.0
        
        # 유효성 판단
        validation_result["is_valid"] = len(validation_result["missing_fields"]) == 0
        
        # 경고사항
        if not customer_info.get("urgency_level"):
            validation_result["warnings"].append("긴급도 정보가 없으면 우선순위 설정이 어려울 수 있습니다")
        
        if not customer_info.get("customer_data"):
            validation_result["warnings"].append("고객 데이터가 없으면 개인화된 서비스 제공이 제한될 수 있습니다")
        
        return validation_result
        
    except Exception as e:
        logger.error(f"고객 정보 검증 실패: {e}")
        return {
            "is_valid": False,
            "missing_fields": [],
            "warnings": ["검증 중 오류가 발생했습니다"],
            "score": 0.0
        }
