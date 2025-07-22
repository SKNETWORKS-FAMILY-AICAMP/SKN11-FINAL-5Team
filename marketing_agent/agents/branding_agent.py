"""
브랜딩 전문 에이전트
공통 모듈을 활용한 개선된 구조
"""

from typing import Dict, Any, List
from .base_agent import BaseMarketingAgent
from marketing_agent.config.prompts_config import PROMPT_META
from shared_modules import load_prompt_from_file

class BrandingAgent(BaseMarketingAgent):
    """브랜딩 전문 마케팅 에이전트"""
    
    def __init__(self, name: str = "브랜딩 전문가", config: Dict[str, Any] = None):
        """브랜딩 에이전트 초기화"""
        if config is None:
            config = {
                "specialization": "브랜딩",
                "name": name,
                "role": "브랜드 아이덴티티 전문 컨설턴트",
                "personality": "창의적이고 전략적인 사고를 가진 브랜딩 전문가"
            }
        
        super().__init__(name, config)
        
        # 브랜딩 관련 키워드
        self.branding_keywords = [
            "브랜드", "로고", "아이덴티티", "포지셔닝", "스토리",
            "미션", "비전", "가치", "컨셉", "이미지", "브랜딩"
        ]
    
    def get_persona_prompt(self) -> str:
        """브랜딩 에이전트 페르소나 프롬프트"""
        return f"""당신은 {self.config.get('name', '브랜딩 전문가')}입니다.

역할: {self.config.get('role', '브랜드 아이덴티티 전문 컨설턴트')}

성격: {self.config.get('personality', '창의적이고 전략적인 사고를 가진 브랜딩 전문가')}

전문분야:
- 브랜드 아이덴티티 개발
- 브랜드 포지셔닝 전략
- 브랜드 스토리텔링
- 시각적 아이덴티티 디자인
- 브랜드 일관성 관리

응답 스타일: 전문적이면서도 친근한 톤으로 브랜드의 본질을 중시하는 조언 제공"""
    
    def get_branding_prompt_content(self, topic: str = "personal_branding") -> str:
        """브랜딩 관련 프롬프트 파일 내용 로드"""
        file_path = PROMPT_META.get(topic, {}).get("file", "")
        if file_path:
            return load_prompt_from_file(file_path)
        return ""
    
    def is_branding_query(self, query: str) -> bool:
        """브랜딩 관련 쿼리인지 판별"""
        relevance_score = self.get_relevance_score(query, self.branding_keywords)
        return relevance_score > 0.1  # 10% 이상 관련도
    
    async def generate_response(self, query: str, context: Dict[str, Any] = None) -> str:
        """브랜딩 관련 응답 생성"""
        try:
            # 쿼리 검증
            if not self.validate_query(query):
                return "브랜딩에 관해 구체적으로 질문해 주세요."
            
            processed_query = self.preprocess_query(query)
            
            # 브랜딩 관련 여부 확인
            is_relevant = self.is_branding_query(processed_query)
            
            # 페르소나 프롬프트
            persona_prompt = self.get_persona_prompt()
            
            # 관련 프롬프트 컨텍스트 로드
            branding_context = self.get_branding_prompt_content("personal_branding")
            
            # 최종 프롬프트 구성
            if is_relevant:
                system_message = f"""{persona_prompt}

전문 지식:
{branding_context}

사용자의 브랜딩 관련 질문에 대해 전문적이고 실용적인 조언을 3-5문장으로 제공해주세요.
브랜드의 본질과 일관성을 강조하며, 구체적인 실행 방안을 포함해주세요."""
            else:
                system_message = f"""{persona_prompt}

사용자의 질문이 브랜딩과 직접적으로 관련이 없어 보입니다. 
브랜딩 관점에서 어떻게 도움을 드릴 수 있는지 안내하고, 
브랜딩 관련 질문을 유도해주세요."""
            
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
    
    def analyze_brand_elements(self, text: str) -> Dict[str, List[str]]:
        """브랜드 요소 분석"""
        branding_elements = {
            "identity": ["브랜드", "아이덴티티", "정체성"],
            "positioning": ["포지셔닝", "차별화", "경쟁력"],
            "values": ["가치", "미션", "비전", "철학"],
            "visual": ["로고", "색상", "디자인", "시각적"],
            "story": ["스토리", "이야기", "브랜딩 스토리"]
        }
        
        found_elements = {}
        for category, keywords in branding_elements.items():
            found = self.analyze_keywords(text, keywords)
            if found:
                found_elements[category] = found
        
        return found_elements
    
    def suggest_branding_strategy(self, business_info: Dict[str, Any]) -> str:
        """비즈니스 정보 기반 브랜딩 전략 제안"""
        business_type = business_info.get("type", "일반")
        target_audience = business_info.get("target", "일반 고객")
        
        strategy_templates = {
            "뷰티": "뷰티 업계의 트렌드를 반영한 세련되고 전문적인 브랜드 이미지",
            "F&B": "신선함과 맛을 강조하는 친근하고 신뢰할 수 있는 브랜드",
            "패션": "개성과 스타일을 표현하는 차별화된 브랜드 아이덴티티",
            "IT/테크": "혁신적이고 신뢰할 수 있는 기술 중심의 브랜드",
            "교육": "전문성과 신뢰성을 바탕으로 한 교육적 가치 브랜드"
        }
        
        base_strategy = strategy_templates.get(business_type, "고유한 가치와 차별화된 경험을 제공하는 브랜드")
        
        return f"{target_audience}을 위한 {base_strategy} 전략을 추천합니다."
