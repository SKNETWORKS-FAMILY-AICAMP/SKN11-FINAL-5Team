"""
타겟팅 전문 에이전트
공통 모듈을 활용한 고객 분석 및 타겟팅 전략
"""

from typing import Dict, Any, List
from .base_agent import BaseMarketingAgent
from shared_modules import load_prompt_from_file

class TargetingAgent(BaseMarketingAgent):
    """타겟팅 및 고객 분석 전문 마케팅 에이전트"""

    def __init__(self, name: str = "타겟팅 애널리스트", config: Dict[str, Any] = None):
        """타겟팅 에이전트 초기화"""
        if config is None:
            config = {
                "specialization": "타겟팅 분석",
                "name": name,
                "role": "고객 분석 및 타겟팅 전략 전문가",
                "personality": "분석적이고 논리적인 데이터 기반 전문가"
            }
        
        super().__init__(name, config)
        
        # 타겟팅 관련 키워드
        self.targeting_keywords = [
            "타겟", "고객", "페르소나", "세분화", "분석", "데이터",
            "오디언스", "타겟팅", "마케팅", "세그먼트", "인사이트"
        ]
        
        # 고객 세그먼트 템플릿
        self.customer_segments = {
            "연령대": ["10대", "20대", "30대", "40대", "50대 이상"],
            "성별": ["남성", "여성", "무관"],
            "관심사": ["뷰티", "패션", "음식", "여행", "운동", "문화", "기술"],
            "구매력": ["프리미엄", "중간", "가성비", "할인 선호"],
            "라이프스타일": ["액티브", "가정 중심", "커리어 중심", "취미 중심"]
        }

    def get_persona_prompt(self) -> str:
        """타겟팅 에이전트 페르소나 프롬프트"""
        return f"""당신은 {self.config.get('name', '타겟팅 애널리스트')}입니다.

역할: {self.config.get('role', '고객 분석 및 타겟팅 전략 전문가')}

전문분야:
- 고객 세그멘테이션
- 페르소나 개발
- 시장 조사 및 분석
- 경쟁사 분석
- 고객 여정 맵핑
- 데이터 분석
- 타겟 오디언스 최적화

응답 방식:
1. 데이터와 분석을 기반으로 한 체계적인 접근
2. 구체적인 수치와 사례를 통한 논리적 설명
3. 실행 가능한 타겟팅 전략 제시
4. 차분하고 전문적인 톤 유지"""

    def is_targeting_query(self, query: str) -> bool:
        """타겟팅 관련 쿼리인지 판별"""
        relevance_score = self.get_relevance_score(query, self.targeting_keywords)
        return relevance_score > 0.1

    async def generate_response(self, query: str, context: Dict[str, Any] = None) -> str:
        """타겟팅 관련 응답 생성"""
        try:
            # 쿼리 검증
            if not self.validate_query(query):
                return "타겟팅이나 고객 분석에 관해 구체적으로 질문해 주세요."

            processed_query = self.preprocess_query(query)
            
            # 타겟팅 관련 여부 확인
            is_relevant = self.is_targeting_query(processed_query)
            
            # 페르소나 프롬프트
            persona_prompt = self.get_persona_prompt()
            
            # 최종 프롬프트 구성
            if is_relevant:
                system_message = f"""{persona_prompt}

사용자의 타겟팅 및 고객 분석 관련 질문에 대해 데이터 기반의 전문적인 조언을 3-5문장으로 제공해주세요.
구체적인 타겟팅 전략과 실행 방안을 포함해주세요."""
            else:
                system_message = f"""{persona_prompt}

사용자의 질문이 타겟팅 분석과 직접적으로 관련이 없어 보입니다.
타겟팅 관점에서 어떻게 도움을 드릴 수 있는지 안내하고,
고객 분석 관련 질문을 유도해주세요."""

            # LLM 응답 생성
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": processed_query}
            ]

            response = await self.generate_llm_response(messages)
            
            # 상호작용 로깅
            self.log_interaction(processed_query, response)
            
            return response

        except Exception as e:
            return self.handle_error(e, query)

    def create_customer_persona(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """비즈니스 정보 기반 고객 페르소나 생성"""
        business_type = business_info.get("type", "일반")
        product_price = business_info.get("price_range", "중간")
        
        # 비즈니스 타입별 기본 페르소나
        persona_templates = {
            "뷰티": {
                "연령대": "20-30대",
                "성별": "여성 중심",
                "관심사": ["뷰티", "패션", "셀프케어"],
                "구매패턴": "브랜드 선호, 리뷰 중시",
                "채널": "인스타그램, 유튜브"
            },
            "F&B": {
                "연령대": "20-40대",
                "성별": "무관",
                "관심사": ["음식", "맛집", "건강"],
                "구매패턴": "맛과 가격 중시",
                "채널": "인스타그램, 블로그"
            },
            "패션": {
                "연령대": "20-30대",
                "성별": "무관",
                "관심사": ["패션", "트렌드", "스타일"],
                "구매패턴": "트렌드 민감, 스타일 중시",
                "채널": "인스타그램, 틱톡"
            }
        }
        
        base_persona = persona_templates.get(business_type, {
            "연령대": "20-40대",
            "성별": "무관",
            "관심사": ["일반"],
            "구매패턴": "가성비 중시",
            "채널": "다양한 플랫폼"
        })
        
        # 가격대에 따른 조정
        if product_price == "프리미엄":
            base_persona["구매력"] = "높음"
            base_persona["특징"] = "품질과 브랜드 가치 중시"
        elif product_price == "가성비":
            base_persona["구매력"] = "중간"
            base_persona["특징"] = "합리적 소비, 할인 선호"
        
        return base_persona

    def analyze_target_audience(self, audience_data: Dict[str, Any]) -> Dict[str, Any]:
        """타겟 오디언스 분석"""
        analysis = {
            "size_estimation": "중간 규모",
            "engagement_potential": "보통",
            "competition_level": "중간",
            "recommended_strategy": "차별화된 콘텐츠로 접근"
        }
        
        # 연령대별 분석
        age_group = audience_data.get("age_group", "20-30대")
        if "20" in age_group:
            analysis["platform_preference"] = "인스타그램, 틱톡"
            analysis["content_style"] = "트렌디, 시각적"
        elif "30" in age_group:
            analysis["platform_preference"] = "인스타그램, 네이버"
            analysis["content_style"] = "실용적, 정보성"
        elif "40" in age_group:
            analysis["platform_preference"] = "페이스북, 네이버"
            analysis["content_style"] = "신뢰성, 전문성"
        
        return analysis

    def suggest_targeting_strategy(self, persona: Dict[str, Any]) -> List[str]:
        """페르소나 기반 타겟팅 전략 제안"""
        strategies = []
        
        # 채널 전략
        preferred_channels = persona.get("채널", "인스타그램")
        strategies.append(f"주요 채널: {preferred_channels}에서 집중 마케팅")
        
        # 콘텐츠 전략
        interests = persona.get("관심사", ["일반"])
        strategies.append(f"콘텐츠 주제: {', '.join(interests)} 관련 콘텐츠 제작")
        
        # 타이밍 전략
        age_group = persona.get("연령대", "20-30대")
        if "20" in age_group:
            strategies.append("포스팅 시간: 저녁 7-9시, 주말 오후")
        else:
            strategies.append("포스팅 시간: 점심시간, 퇴근 후")
        
        # 메시징 전략
        purchase_pattern = persona.get("구매패턴", "가성비 중시")
        if "브랜드" in purchase_pattern:
            strategies.append("메시지: 브랜드 가치와 품질 강조")
        elif "가성비" in purchase_pattern:
            strategies.append("메시지: 합리적 가격과 실용성 강조")
        
        return strategies

    def calculate_market_potential(self, target_data: Dict[str, Any]) -> Dict[str, Any]:
        """시장 잠재력 계산"""
        # 간단한 점수 기반 계산
        market_size = target_data.get("market_size", 100000)
        competition = target_data.get("competition_level", "중간")
        growth_rate = target_data.get("growth_rate", 5)
        
        # 경쟁 수준에 따른 가중치
        competition_weights = {"낮음": 1.2, "중간": 1.0, "높음": 0.8}
        weight = competition_weights.get(competition, 1.0)
        
        potential_score = (market_size / 10000) * weight * (growth_rate / 5)
        
        if potential_score > 15:
            potential = "높음"
            recommendation = "적극적인 마케팅 투자 권장"
        elif potential_score > 8:
            potential = "보통"
            recommendation = "단계적 시장 진입 권장"
        else:
            potential = "낮음"
            recommendation = "신중한 접근 필요"
        
        return {
            "potential_score": round(potential_score, 1),
            "potential_level": potential,
            "recommendation": recommendation,
            "estimated_reach": int(market_size * 0.1)  # 10% 도달 가능성
        }
