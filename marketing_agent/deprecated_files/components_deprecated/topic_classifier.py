"""
토픽 분류 서비스
사용자 입력을 마케팅 토픽으로 분류하는 LLM 기반 분류기
"""

from typing import List
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class TopicClassifier:
    """토픽 분류 서비스"""
    
    TOPIC_CLASSIFY_PROMPT = """
너는 고객 질문을 분석해서 관련된 마케팅 토픽을 모두 골라주는 역할이야.

아래의 토픽 중에서 질문과 관련된 키워드를 복수 개까지 골라줘.
콤마(,)로 구분된 키만 출력하고, 설명은 하지마.

가능한 토픽:
1. marketing_fundamentals – 마케팅 기초 이론
2. social_media_marketing – SNS 전반 전략
3. email_marketing – 이메일, 뉴스레터
4. content_marketing – 콘텐츠 전략, 포맷 기획
5. personal_branding – 퍼스널 및 브랜드 포지셔닝
6. digital_advertising – 페이드 미디어, 광고 채널
7. seo_optimization – 검색 노출 최적화
8. conversion_optimization – 전환 퍼널, A/B 테스트
9. influencer_marketing – 협업, 제휴 마케팅
10. local_marketing – 지역 기반 마케팅
11. marketing_automation – 자동화, 캠페인 설정
12. viral_marketing – 바이럴, 입소문 전략
13. blog_marketing – 블로그 기반 콘텐츠 운영
14. marketing_metrics – ROAS, CAC 등 성과 지표

출력 예시: marketing_fundamentals, social_media_marketing
"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def classify(self, user_input: str) -> List[str]:
        """사용자 입력을 토픽으로 분류"""
        try:
            classify_prompt = ChatPromptTemplate.from_messages([
                ("system", self.TOPIC_CLASSIFY_PROMPT),
                ("human", f"사용자 질문: {user_input}")
            ])
            
            chain = classify_prompt | self.llm | StrOutputParser()
            result = chain.invoke({"input": user_input}).strip()
            topics = [t.strip() for t in result.split(",") if t.strip()]
            
            print(f"🏷️ 분류된 토픽: {topics}")
            return topics
            
        except Exception as e:
            print(f"⚠️ 토픽 분류 실패: {e}")
            return []
