import json
import logging
from typing import List, Dict, Any

class MultiTurnManager:
    """
    멀티턴 대화 흐름 및 단계별 정보 수집을 관리하는 매니저
    """

    # 단계와 토픽 매핑
    STAGE_TOPIC_MAP = {
        "아이디어 탐색": ["idea_recommendation"],
        "시장 검증": ["idea_validation"],
        "비즈니스 모델링": ["business_model", "mvp_development"],
        "실행 계획 수립": ["funding_strategy", "financial_planning", "startup_preparation"],
        "성장 전략 & 리스크 관리": ["growth_strategy", "risk_management"],
    }

    STAGES = list(STAGE_TOPIC_MAP.keys())

    # 각 단계별 요구 정보 
    STAGE_REQUIREMENTS = {
        "아이디어 탐색": ["창업 아이디어", "시장 트렌드"],
        "시장 검증": ["경쟁사 분석", "타겟 고객", "시장 규모"],
        "비즈니스 모델링": ["BMC", "MVP 개발 계획"],
        "실행 계획 수립": ["자금 조달 계획", "MVP 개발 계획","창업 준비 체크리스트"],
        "성장 전략 & 리스크 관리": ["사업 확장 전략", "리스크 관리 방안"],
    }

    def __init__(self, llm_manager):
        self.llm_manager = llm_manager

    def determine_stage(self, topics: List[str]) -> str:
        """토픽 기반으로 현재 상담 단계 추론"""
        for stage, mapped_topics in self.STAGE_TOPIC_MAP.items():
            if any(t in mapped_topics for t in topics):
                return stage
        return "아이디어 탐색"  # 기본값

    def get_next_stage(self, current_stage: str) -> str:
        """다음 단계 반환 (없으면 None)"""
        try:
            idx = self.STAGES.index(current_stage)
            return self.STAGES[idx + 1] if idx + 1 < len(self.STAGES) else None
        except ValueError:
            return None

    async def check_stage_progress(self, current_stage: str, history: str) -> Dict[str, Any]:
        """
        LLM을 통해 현재 단계의 요구 정보가 얼마나 수집되었는지 평가.
        - progress: 0~1 (수집 비율)
        - missing: 누락된 항목 목록
        """
        required_info = self.STAGE_REQUIREMENTS.get(current_stage, [])
        if not required_info:
            return {"progress": 0.0, "missing": []}  # 정보 없음 = 진행률 계산 불가

        prompt = f"""
        다음 대화 기록에서 현재 단계 "{current_stage}"에 필요한 정보 항목이 얼마나 수집되었는지 평가해주세요.
        필요한 정보 항목: {', '.join(required_info)}
        대화 기록:
        {history}

        각 항목에 대해 '있음' 또는 '없음'으로 평가하고,
        누락된 항목 목록과 진행률(0~1)을 JSON으로 출력하세요.
        예시:
        {{
            "progress": 0.6,
            "missing": ["경쟁사 분석", "타겟 시장"]
        }}
        """.replace("{", "{{").replace("}", "}}")

        try:
            messages = [
                {"role": "system", "content": "너는 단계별 정보 수집 현황을 JSON으로 평가하는 전문가야."},
                {"role": "user", "content": prompt}
            ]
            result = await self.llm_manager.generate_response(messages=messages, provider="openai")
            return self._parse_progress_json(result)
        except Exception as e:
            return {"progress": 0.0, "missing": required_info}

    def _parse_progress_json(self, result: str) -> Dict[str, Any]:
        """LLM의 JSON 응답 파싱"""
        print("LLM의 progress 판단 답변",result)
        try:
            print("json 리턴함")
            return json.loads(result)
        except Exception as e:
            return {"progress": 0.0, "missing": []}
