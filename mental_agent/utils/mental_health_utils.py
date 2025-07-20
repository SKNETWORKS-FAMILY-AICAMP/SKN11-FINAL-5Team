"""
Mental Health Agent Utilities
정신건강 관련 유틸리티 함수들
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# PHQ-9 설문 문항
PHQ9_QUESTIONS = [
    "지난 2주 동안, 일을 하는데 흥미나 즐거움을 거의 느끼지 못했다",
    "지난 2주 동안, 기분이 가라앉거나, 우울하거나, 희망이 없다고 느꼈다", 
    "지난 2주 동안, 잠들기 어렵거나 자주 깨거나 혹은 너무 많이 잤다",
    "지난 2주 동안, 피곤하다고 느끼거나 기력이 거의 없었다",
    "지난 2주 동안, 식욕이 떨어지거나 과식을 했다",
    "지난 2주 동안, 자신을 부정적으로 생각하거나, 자신이 실패자라고 생각하거나, 자신 또는 가족을 실망시켰다고 생각했다",
    "지난 2주 동안, 신문을 읽거나 텔레비전 보는 것과 같은 일에 집중하는 것이 어려웠다",
    "지난 2주 동안, 다른 사람들이 눈치 챌 정도로 평소보다 말과 행동이 느려졌거나, 반대로 안절부절못하거나 들떠서 평소보다 많이 움직였다",
    "지난 2주 동안, 자신을 해치거나 죽어버리고 싶다는 생각을 했다"
]

def calculate_phq9_score(responses: List[int]) -> Dict[str, Any]:
    """PHQ-9 점수 계산 및 해석"""
    try:
        if len(responses) != 9:
            raise ValueError("PHQ-9는 9개 문항이 필요합니다")
        
        # 각 응답은 0-3 범위여야 함
        for i, response in enumerate(responses):
            if not (0 <= response <= 3):
                raise ValueError(f"문항 {i+1}의 응답은 0-3 범위여야 합니다")
        
        total_score = sum(responses)
        
        # 점수별 해석
        if total_score >= 20:
            severity = "심각한 우울"
            recommendation = "즉시 전문의의 도움을 받으시기 바랍니다."
            action_needed = "immediate"
        elif total_score >= 15:
            severity = "중등도 심각 우울"
            recommendation = "정신건강 전문가와 상담받으시기 바랍니다."
            action_needed = "urgent"
        elif total_score >= 10:
            severity = "중등도 우울"
            recommendation = "상담이나 치료를 고려해보시기 바랍니다."
            action_needed = "recommended"
        elif total_score >= 5:
            severity = "경미한 우울"
            recommendation = "생활습관 개선이나 스트레스 관리가 도움이 될 수 있습니다."
            action_needed = "lifestyle"
        else:
            severity = "정상"
            recommendation = "현재 우울 증상은 최소한입니다."
            action_needed = "none"
        
        # 9번 문항 (자해/자살 사고) 특별 체크
        suicide_risk = responses[8] > 0  # 9번 문항이 1 이상이면 위험
        
        return {
            "total_score": total_score,
            "severity": severity,
            "recommendation": recommendation,
            "action_needed": action_needed,
            "suicide_risk": suicide_risk,
            "responses": responses,
            "assessment_date": datetime.now(),
            "interpretation": get_detailed_interpretation(total_score, suicide_risk)
        }
        
    except Exception as e:
        logger.error(f"PHQ-9 점수 계산 실패: {e}")
        return {
            "error": str(e),
            "total_score": 0,
            "severity": "평가 불가",
            "recommendation": "다시 평가해주세요."
        }

def get_detailed_interpretation(score: int, suicide_risk: bool) -> str:
    """상세한 PHQ-9 해석 제공"""
    interpretation = f"""
PHQ-9 총점: {score}점

점수별 해석:
- 0-4점: 정상 (우울증상 거의 없음)
- 5-9점: 경미한 우울 (생활습관 개선 권장)
- 10-14점: 중등도 우울 (상담 치료 권장)
- 15-19점: 중등도 심각 우울 (전문가 치료 필요)
- 20-27점: 심각한 우울 (즉시 전문의 진료 필요)
"""
    
    if suicide_risk:
        interpretation += "\n⚠️ 자해나 자살에 대한 생각이 있으신 것으로 나타났습니다. 즉시 전문가의 도움을 받으시기 바랍니다."
    
    return interpretation

def analyze_emotional_state(text: str) -> Dict[str, Any]:
    """텍스트에서 감정 상태 분석"""
    try:
        text_lower = text.lower()
        
        # 감정 키워드 정의
        emotion_keywords = {
            "sad": ["슬프", "우울", "울적", "기운없", "침울", "쓸쓸", "외로", "허전"],
            "anxious": ["불안", "걱정", "초조", "긴장", "두려", "무서", "겁", "떨림"],
            "angry": ["화", "짜증", "분노", "빡침", "열받", "성질", "약오름"],
            "hopeless": ["희망없", "절망", "포기", "의미없", "무력", "막막", "답답"],
            "suicidal": ["죽고싶", "자살", "사라지고싶", "끝내고싶", "괴로", "못살겠"],
            "positive": ["좋", "행복", "기쁘", "즐거", "만족", "감사", "평화"],
            "neutral": ["그냥", "보통", "평범", "괜찮", "무난"]
        }
        
        detected_emotions = {}
        for emotion, keywords in emotion_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            if count > 0:
                detected_emotions[emotion] = count
        
        # 주요 감정 결정
        primary_emotion = "neutral"
        if detected_emotions:
            primary_emotion = max(detected_emotions, key=detected_emotions.get)
        
        # 위험도 평가
        risk_level = "low"
        if "suicidal" in detected_emotions or "hopeless" in detected_emotions:
            risk_level = "high"
        elif "sad" in detected_emotions or "anxious" in detected_emotions:
            risk_level = "medium"
        
        return {
            "primary_emotion": primary_emotion,
            "detected_emotions": detected_emotions,
            "risk_level": risk_level,
            "requires_immediate_attention": "suicidal" in detected_emotions,
            "emotional_intensity": sum(detected_emotions.values())
        }
        
    except Exception as e:
        logger.error(f"감정 상태 분석 실패: {e}")
        return {
            "primary_emotion": "neutral",
            "detected_emotions": {},
            "risk_level": "low",
            "requires_immediate_attention": False
        }

def detect_crisis_indicators(text: str) -> Dict[str, Any]:
    """위기 상황 지표 감지"""
    try:
        text_lower = text.lower()
        
        # 위기 지표 키워드
        crisis_keywords = {
            "suicide_direct": ["자살", "죽고싶", "목숨", "죽어버리"],
            "suicide_indirect": ["사라지고싶", "끝내고싶", "지쳐", "못살겠"],
            "self_harm": ["자해", "상처", "칼", "베어", "때리"],
            "substance": ["술", "약", "마약", "음주", "약물"],
            "isolation": ["혼자", "외로", "아무도", "버림받"],
            "hopelessness": ["희망없", "절망", "포기", "의미없", "소용없"]
        }
        
        detected_indicators = {}
        for category, keywords in crisis_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            if count > 0:
                detected_indicators[category] = count
        
        # 위기 수준 결정
        crisis_level = "none"
        immediate_intervention = False
        
        if "suicide_direct" in detected_indicators:
            crisis_level = "severe"
            immediate_intervention = True
        elif "suicide_indirect" in detected_indicators or "self_harm" in detected_indicators:
            crisis_level = "moderate"
        elif any(detected_indicators.values()):
            crisis_level = "mild"
        
        return {
            "crisis_level": crisis_level,
            "detected_indicators": detected_indicators,
            "immediate_intervention": immediate_intervention,
            "total_indicators": sum(detected_indicators.values()),
            "emergency_resources_needed": immediate_intervention
        }
        
    except Exception as e:
        logger.error(f"위기 지표 감지 실패: {e}")
        return {
            "crisis_level": "none",
            "detected_indicators": {},
            "immediate_intervention": False
        }

def generate_safety_plan(crisis_info: Dict[str, Any]) -> Dict[str, Any]:
    """안전 계획 생성"""
    try:
        safety_plan = {
            "immediate_actions": [],
            "coping_strategies": [],
            "support_contacts": [],
            "emergency_contacts": [],
            "professional_resources": []
        }
        
        crisis_level = crisis_info.get("crisis_level", "none")
        
        if crisis_level == "severe":
            safety_plan["immediate_actions"] = [
                "즉시 안전한 장소로 이동하세요",
                "주변의 위험한 물건들을 치워주세요",
                "신뢰할 수 있는 사람에게 연락하세요",
                "아래 응급 연락처로 즉시 도움을 요청하세요"
            ]
            safety_plan["emergency_contacts"] = [
                "생명의전화: 1393",
                "청소년전화: 1388",
                "응급실: 119"
            ]
        elif crisis_level == "moderate":
            safety_plan["immediate_actions"] = [
                "깊게 숨을 쉬고 잠시 진정하세요",
                "신뢰할 수 있는 사람과 이야기하세요",
                "전문가의 도움을 받는 것을 고려해보세요"
            ]
        
        # 공통 대처 전략
        safety_plan["coping_strategies"] = [
            "깊은 호흡이나 명상하기",
            "좋아하는 음악 듣기",
            "산책이나 가벼운 운동하기",
            "일기 쓰기",
            "따뜻한 차 마시기"
        ]
        
        safety_plan["professional_resources"] = [
            "정신건강상담센터",
            "병원 정신건강의학과",
            "온라인 상담 서비스",
            "지역 보건소"
        ]
        
        return safety_plan
        
    except Exception as e:
        logger.error(f"안전 계획 생성 실패: {e}")
        return {"error": "안전 계획 생성에 실패했습니다"}

def get_follow_up_questions(emotional_state: Dict[str, Any]) -> List[str]:
    """감정 상태에 따른 후속 질문 생성"""
    try:
        primary_emotion = emotional_state.get("primary_emotion", "neutral")
        
        question_sets = {
            "sad": [
                "언제부터 이런 기분이 드셨나요?",
                "특별히 힘든 일이 있으셨나요?",
                "평소에 기분이 좋아지는 활동이 있나요?"
            ],
            "anxious": [
                "어떤 상황에서 불안감을 느끼시나요?",
                "불안할 때 몸에 어떤 변화가 있나요?",
                "이전에 도움이 되었던 방법이 있나요?"
            ],
            "angry": [
                "화가 나는 구체적인 이유가 있나요?",
                "평소 화를 다스리는 방법이 있나요?",
                "누군가와 이야기를 나누셨나요?"
            ],
            "hopeless": [
                "어떤 부분에서 희망이 없다고 느끼시나요?",
                "이전에 비슷한 기분을 느낀 적이 있나요?",
                "작은 것이라도 기대되는 것이 있나요?"
            ],
            "suicidal": [
                "지금 안전한 곳에 계신가요?",
                "신뢰할 수 있는 누군가와 함께 계신가요?",
                "전문가의 도움을 받은 적이 있나요?"
            ]
        }
        
        return question_sets.get(primary_emotion, [
            "현재 어떤 기분이신가요?",
            "요즘 어떻게 지내세요?",
            "어떤 도움이 필요하신가요?"
        ])
        
    except Exception as e:
        logger.error(f"후속 질문 생성 실패: {e}")
        return ["더 자세히 말씀해 주실 수 있나요?"]

def recommend_resources(assessment: Dict[str, Any]) -> Dict[str, List[str]]:
    """평가 결과에 따른 자원 추천"""
    try:
        phq9_score = assessment.get("total_score", 0)
        suicide_risk = assessment.get("suicide_risk", False)
        
        recommendations = {
            "immediate": [],
            "professional": [],
            "self_help": [],
            "lifestyle": []
        }
        
        if suicide_risk or phq9_score >= 20:
            recommendations["immediate"] = [
                "생명의전화 1393",
                "정신건강위기상담전화 1577-0199",
                "가까운 응급실 방문"
            ]
        
        if phq9_score >= 15:
            recommendations["professional"] = [
                "정신건강의학과 전문의 상담",
                "임상심리사 상담",
                "정신건강상담센터 이용"
            ]
        elif phq9_score >= 10:
            recommendations["professional"] = [
                "심리상담센터 이용",
                "온라인 상담 서비스",
                "지역 보건소 정신건강팀"
            ]
        
        if phq9_score >= 5:
            recommendations["self_help"] = [
                "우울증 자가관리 앱 사용",
                "명상 및 마음챙김 실천",
                "인지행동치료 자조서적 읽기"
            ]
        
        recommendations["lifestyle"] = [
            "규칙적인 운동 (주 3회 이상)",
            "충분한 수면 (7-8시간)",
            "균형잡힌 식사",
            "사회적 관계 유지",
            "스트레스 관리 기법 학습"
        ]
        
        return recommendations
        
    except Exception as e:
        logger.error(f"자원 추천 실패: {e}")
        return {"error": ["추천 생성에 실패했습니다"]}
