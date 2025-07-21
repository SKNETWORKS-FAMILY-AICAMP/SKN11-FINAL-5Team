"""
브랜딩 전문 에이전트
"""

from typing import Dict, Any
from base_agent import BaseMarketingAgent
from utils.llm_utils import call_llm
from config.prompts_config import PROMPT_META


class BrandingAgent(BaseMarketingAgent):
    """브랜딩 전문 마케팅 에이전트"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.specialization = "브랜딩"
    
    def get_persona_prompt(self) -> str:
        """브랜딩 에이전트 페르소나 프롬프트"""
        return f"""
        당신은 {self.config.get('name', '브랜딩 전문가')}입니다.
        
        역할: {self.config.get('role', '브랜딩 전문 컨설턴트')}
        
        성격: {self.config.get('personality', '창의적이고 전략적인 사고를 가진 브랜딩 전문가')}
        
        전문분야:
        - 브랜드 아이덴티티 개발
        - 브랜드 포지셔닝 전략
        - 브랜드 스토리텔링
        - 시각적 아이덴티티 디자인
        - 브랜드 일관성 관리
        
        응답 스타일: {self.config.get('tone', '전문적이면서도 친근한 톤')}
        """

    def get_prompt_text(self, topic: str = "personal_branding") -> str:
        """토픽에 맞는 프롬프트 파일 내용 로드"""
        file_path = PROMPT_META.get(topic, {}).get("file", "")
        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def generate_response(self, query: str, context: Dict[str, Any] = None) -> str:
        """브랜딩 관련 응답 생성 - LLM 연동 포함"""
        try:
            processed_query = self.preprocess_query(query)

            # 브랜딩 관련 여부 판별
            branding_keywords = [
                "브랜드", "로고", "아이덴티티", "포지셔닝", "스토리",
                "미션", "비전", "가치", "컨셉", "이미지"
            ]
            is_branding_query = any(kw in processed_query.lower() for kw in branding_keywords)

            # 프롬프트 생성
            persona_prompt = self.get_persona_prompt()
            topic_prompt = self.get_prompt_text("personal_branding")

            final_prompt = f"""{persona_prompt}

{topic_prompt}

사용자 질문:
{processed_query}

브랜딩 전문가로서 위 질문에 구체적이고 실용적인 조언을 해주세요.
"""

            # LLM 호출
            if is_branding_query:
                response = call_llm(final_prompt)
            else:
                response = f"""
브랜딩과 직접적 관련은 적지만, '{processed_query}'에 대해 가능한 범위에서 조언드릴게요.

{call_llm(final_prompt)}
"""

            final_response = self.postprocess_response(response)
            self.log_interaction(query, final_response)
            return final_response

        except Exception as e:
            return self.handle_error(e, query)

    def analyze_brand_keywords(self, text: str) -> Dict[str, Any]:
        """브랜드 관련 키워드 분석"""
        branding_elements = {
            "identity": ["브랜드", "아이덴티티", "정체성"],
            "positioning": ["포지셔닝", "차별화", "경쟁력"],
            "values": ["가치", "미션", "비전", "철학"],
            "visual": ["로고", "색상", "디자인", "시각적"],
            "story": ["스토리", "이야기", "브랜딩 스토리"]
        }

        found_elements = {}
        for category, keywords in branding_elements.items():
            found = [kw for kw in keywords if kw in text.lower()]
            if found:
                found_elements[category] = found

        return found_elements
