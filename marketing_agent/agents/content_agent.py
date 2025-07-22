"""
콘텐츠 제작 전문 에이전트
공통 모듈을 활용한 개선된 구조
"""

from typing import Dict, Any, List
from .base_agent import BaseMarketingAgent
from marketing_agent.config.prompts_config import PROMPT_META
from shared_modules import load_prompt_from_file

class ContentAgent(BaseMarketingAgent):
    """콘텐츠 제작 전문 마케팅 에이전트"""

    def __init__(self, name: str = "콘텐츠 크리에이터", config: Dict[str, Any] = None):
        """콘텐츠 에이전트 초기화"""
        if config is None:
            config = {
                "specialization": "콘텐츠 제작",
                "name": name,
                "role": "솔로프리너를 위한 콘텐츠 제작 및 마케팅 전문가",
                "personality": "트렌디하고 창의적인 콘텐츠 전문가"
            }
        
        super().__init__(name, config)
        
        # 콘텐츠 관련 키워드
        self.content_keywords = [
            "콘텐츠", "포스팅", "글", "카피", "카드뉴스", "영상",
            "인스타그램", "블로그", "SNS", "소셜미디어", "해시태그"
        ]
        
        # 플랫폼별 특성
        self.platform_characteristics = {
            "instagram": {
                "max_length": 2200,
                "style": "시각적, 감성적",
                "hashtag_limit": 30
            },
            "naver_blog": {
                "min_length": 1000,
                "style": "정보성, SEO 최적화",
                "structure": "제목, 소제목, 본문"
            },
            "facebook": {
                "optimal_length": 120,
                "style": "친근함, 공감대",
                "engagement": "댓글, 공유 유도"
            }
        }

    def get_persona_prompt(self) -> str:
        """콘텐츠 에이전트 페르소나 프롬프트"""
        return f"""당신은 {self.config.get('name', '콘텐츠 크리에이터')}입니다.

역할: {self.config.get('role', '솔로프리너를 위한 콘텐츠 제작 및 마케팅 전문가')}

전문분야:
- 소셜미디어 콘텐츠 제작
- 바이럴 마케팅 전략
- SEO 최적화 콘텐츠
- 영상 콘텐츠 기획
- 카피라이팅
- 해시태그 전략

응답 방식:
1. 플랫폼별 특성을 고려한 맞춤형 조언
2. 트렌드와 최신 정보 반영
3. 실행 가능한 구체적 아이디어 제공
4. 창의적이고 친근한 톤 유지"""

    def get_content_prompt_content(self, topic: str = "content_marketing") -> str:
        """콘텐츠 관련 프롬프트 파일 내용 로드"""
        file_path = PROMPT_META.get(topic, {}).get("file", "")
        if file_path:
            return load_prompt_from_file(file_path)
        return ""

    def is_content_query(self, query: str) -> bool:
        """콘텐츠 관련 쿼리인지 판별"""
        relevance_score = self.get_relevance_score(query, self.content_keywords)
        return relevance_score > 0.1

    def detect_platform(self, query: str) -> str:
        """쿼리에서 플랫폼 감지"""
        platform_keywords = {
            "instagram": ["인스타", "인스타그램", "릴스", "스토리"],
            "naver_blog": ["블로그", "네이버블로그", "포스팅"],
            "facebook": ["페이스북", "페북"],
            "youtube": ["유튜브", "영상", "동영상"],
            "tiktok": ["틱톡", "쇼츠"]
        }
        
        query_lower = query.lower()
        for platform, keywords in platform_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return platform
        
        return "general"

    async def generate_response(self, query: str, context: Dict[str, Any] = None) -> str:
        """콘텐츠 관련 응답 생성"""
        try:
            # 쿼리 검증
            if not self.validate_query(query):
                return "콘텐츠 제작에 관해 구체적으로 질문해 주세요."

            processed_query = self.preprocess_query(query)
            
            # 콘텐츠 관련 여부 확인
            is_relevant = self.is_content_query(processed_query)
            
            # 플랫폼 감지
            detected_platform = self.detect_platform(processed_query)
            
            # 페르소나 프롬프트
            persona_prompt = self.get_persona_prompt()
            
            # 관련 프롬프트 컨텍스트 로드
            content_context = self.get_content_prompt_content("content_marketing")
            
            # 플랫폼별 가이드라인
            platform_guide = ""
            if detected_platform in self.platform_characteristics:
                platform_info = self.platform_characteristics[detected_platform]
                platform_guide = f"""

플랫폼별 가이드라인 ({detected_platform}):
- 스타일: {platform_info.get('style', '일반적')}
- 길이 제한: {platform_info.get('max_length', platform_info.get('min_length', '제한 없음'))}
- 특별 고려사항: {platform_info.get('structure', platform_info.get('engagement', '없음'))}"""

            # 최종 프롬프트 구성
            if is_relevant:
                system_message = f"""{persona_prompt}

전문 지식:
{content_context}
{platform_guide}

사용자의 콘텐츠 제작 관련 질문에 대해 창의적이고 실용적인 조언을 3-5문장으로 제공해주세요.
트렌드를 반영하고 구체적인 실행 방안을 포함해주세요."""
            else:
                system_message = f"""{persona_prompt}

사용자의 질문이 콘텐츠 제작과 직접적으로 관련이 없어 보입니다.
콘텐츠 마케팅 관점에서 어떻게 도움을 드릴 수 있는지 안내하고,
콘텐츠 제작 관련 질문을 유도해주세요."""

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

    def generate_hashtags(self, content: str, platform: str = "instagram") -> List[str]:
        """콘텐츠 기반 해시태그 생성"""
        # 키워드 추출
        keywords = self.analyze_keywords(content, [
            "뷰티", "패션", "음식", "여행", "일상", "운동", "건강",
            "카페", "맛집", "셀카", "OOTD", "데일리", "추천"
        ])
        
        # 기본 해시태그 생성
        hashtags = [f"#{keyword}" for keyword in keywords[:5]]
        
        # 플랫폼별 인기 해시태그 추가
        if platform == "instagram":
            popular_tags = ["#일상", "#데일리", "#좋아요반사", "#팔로우미", "#인스타그램"]
        else:
            popular_tags = ["#추천", "#정보", "#공유", "#소통"]
        
        hashtags.extend(popular_tags[:3])
        
        return hashtags[:10]  # 최대 10개

    def analyze_content_performance(self, metrics: Dict[str, Any]) -> str:
        """콘텐츠 성과 분석"""
        engagement_rate = metrics.get("engagement_rate", 0)
        reach = metrics.get("reach", 0)
        
        if engagement_rate > 5:
            performance = "우수"
            advice = "현재 콘텐츠 스타일을 유지하세요."
        elif engagement_rate > 2:
            performance = "보통"
            advice = "해시태그와 포스팅 시간을 최적화해보세요."
        else:
            performance = "개선 필요"
            advice = "콘텐츠 형식과 주제를 다양화해보세요."
        
        return f"성과: {performance} (참여율: {engagement_rate}%) - {advice}"

    def suggest_content_calendar(self, business_type: str, frequency: str = "daily") -> List[Dict[str, str]]:
        """콘텐츠 캘린더 제안"""
        content_types = {
            "뷰티": ["제품 리뷰", "메이크업 튜토리얼", "스킨케어 팁", "룩북"],
            "F&B": ["메뉴 소개", "조리 과정", "재료 이야기", "고객 후기"],
            "패션": ["코디 제안", "신상품 소개", "스타일링 팁", "트렌드 분석"],
            "일반": ["일상 공유", "팁 & 노하우", "비하인드 스토리", "고객과의 소통"]
        }
        
        content_list = content_types.get(business_type, content_types["일반"])
        
        calendar = []
        for i, content_type in enumerate(content_list):
            calendar.append({
                "day": f"주 {i+1}회",
                "type": content_type,
                "goal": "팔로워 참여 유도"
            })
        
        return calendar
