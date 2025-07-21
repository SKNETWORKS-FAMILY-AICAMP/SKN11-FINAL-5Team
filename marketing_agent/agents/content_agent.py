"""
콘텐츠 제작 전문 에이전트 - RAG 강화 버전
"""

from typing import Dict, Any, List
from base_agent import BaseMarketingAgent
from utils.llm_utils import call_llm
from config.prompts_config import PROMPT_META


class ContentAgent(BaseMarketingAgent):
    """콘텐츠 제작 전문 마케팅 에이전트 - RAG 기반"""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.specialization = "콘텐츠 제작"

    def get_persona_prompt(self) -> str:
        """콘텐츠 에이전트 페르소나 프롬프트"""
        return f"""
        당신은 {self.config.get('name', '콘텐츠 크리에이터')}입니다.
        
        역할: 솔로프리너를 위한 콘텐츠 제작 및 마케팅 전문가
        
        전문분야:
        - 소셜미디어 콘텐츠 제작
        - 바이럴 마케팅 전략
        - SEO 최적화 콘텐츠
        - 영상 콘텐츠 기획
        - 카피라이팅
        
        응답 방식:
        1. 제공된 참고 문서를 최우선으로 활용
        2. 플랫폼별 특성을 고려한 맞춤형 조언
        3. 트렌드와 최신 정보 반영
        4. 실행 가능한 구체적 아이디어 제공
        5. 창의적이고 친근한 톤 유지
        """

    def get_prompt_text(self, topic: str = "content_marketing") -> str:
        """프롬프트 파일 내용 로드"""
        file_path = PROMPT_META.get(topic, {}).get("file", "")
        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def generate_response(self, query: str, context: Dict[str, Any] = None) -> str:
        """RAG + LLM 기반 콘텐츠 응답 생성"""
        try:
            agent_name = self.config.get('name', '콘텐츠 크리에이터')
            persona_prompt = self.get_persona_prompt()
            processed_query = self.preprocess_query(query)

            # RAG 문서 정리
            relevant_docs = context.get('relevant_documents', []) if context else []
            rag_context = "\n\n".join(
                f"📄 문서 {i+1}: {doc.get('title', '')}\n{doc.get('content', '')[:500]}"
                for i, doc in enumerate(relevant_docs[:2])
            ) if relevant_docs else "❌ 참고할 문서 없음"

            topic_prompt = self.get_prompt_text("content_marketing")

            # 통합 프롬프트
            final_prompt = f"""{persona_prompt}

{topic_prompt}

사용자 질문:
{processed_query}

관련 문서:
{rag_context}

콘텐츠 마케팅 전문가로서 위 질문에 대해 현실적이고 창의적인 조언을 3~5문장으로 작성해주세요.
"""

            # LLM 호출
            llm_response = call_llm(final_prompt)

            final_response = f"✨ 안녕하세요! {agent_name}입니다!\n\n{llm_response}\n" + self._get_action_items()
            return self.postprocess_response(final_response)

        except Exception as e:
            return self.handle_error(e, query)

    def _get_action_items(self) -> str:
        """실행 가능한 액션 아이템"""
        return """

💡 **오늘 바로 할 수 있는 액션:**
• 1주일 콘텐츠 캘린더 계획하기
• 첫 번째 포스트 아이디어 스케치하기
• 타겟 해시태그 15개 리스트 만들기
"""
