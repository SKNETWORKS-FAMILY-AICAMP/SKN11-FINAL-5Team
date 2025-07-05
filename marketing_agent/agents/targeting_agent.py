"""
타겟팅 및 고객 분석 전문 에이전트 - RAG 강화 버전
"""

from typing import Dict, Any, List
from base_agent import BaseMarketingAgent
from utils.llm_utils import call_llm
from config.prompts_config import PROMPT_META


class TargetingAgent(BaseMarketingAgent):
    """타겟팅 및 고객 분석 전문 마케팅 에이전트 - RAG 기반"""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.specialization = "타겟팅 및 고객 분석"

    def get_persona_prompt(self) -> str:
        """타겟팅 에이전트 페르소나 프롬프트"""
        return f"""
        당신은 {self.config.get('name', '타겟팅 전문가')}입니다.
        
        역할: 솔로프리너를 위한 고객 분석 및 타겟팅 전략 전문가
        
        전문분야:
        - 고객 세그멘테이션
        - 페르소나 개발
        - 시장 조사 및 분석
        - 타겟 오디언스 식별
        - 고객 여정 맵핑
        - 경쟁사 분석
        
        응답 방식:
        1. 제공된 참고 문서를 최우선으로 활용
        2. 데이터와 분석을 기반으로 한 논리적 접근
        3. 솔로프리너도 실행할 수 있는 현실적 방법 제시
        4. 구체적인 수치와 예시로 설명
        5. 체계적이고 전문적인 톤 유지
        """

    def get_prompt_text(self, topic: str = "marketing_automation") -> str:
        """프롬프트 파일 내용 로드"""
        file_path = PROMPT_META.get(topic, {}).get("file", "")
        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def generate_response(self, query: str, context: Dict[str, Any] = None) -> str:
        """RAG + LLM 기반 타겟팅 응답 생성"""
        try:
            agent_name = self.config.get('name', '타겟팅 전문가')
            persona_prompt = self.get_persona_prompt()
            processed_query = self.preprocess_query(query)

            relevant_docs = context.get('relevant_documents', []) if context else []
            rag_context = "\n\n".join(
                f"📈 문서 {i+1}: {doc.get('title', '')}\n{doc.get('content', '')[:500]}"
                for i, doc in enumerate(relevant_docs[:2])
            ) if relevant_docs else "❌ 참고 문서 없음"

            topic_prompt = self.get_prompt_text("marketing_automation")  # targeting 관련으로 지정된 파일

            final_prompt = f"""{persona_prompt}

{topic_prompt}

사용자 질문:
{processed_query}

관련 문서:
{rag_context}

고객 분석 및 타겟팅 전문가로서 실행 가능하고 구체적인 마케팅 조언을 3~5문장으로 해주세요.
"""

            llm_response = call_llm(final_prompt)

            final_response = f"📊 안녕하세요! {agent_name}입니다.\n\n{llm_response}\n" + self._get_action_items()
            return self.postprocess_response(final_response)

        except Exception as e:
            return self.handle_error(e, query)

    def _get_action_items(self) -> str:
        """실행 가능한 액션 아이템"""
        return """

💡 **오늘 바로 할 수 있는 액션:**
• 현재 고객 3명에게 간단한 인터뷰하기
• 경쟁사 타겟 고객 조사하기
• 페르소나 초안 1개 작성하기
"""
