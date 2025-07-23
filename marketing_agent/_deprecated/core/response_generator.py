"""
마케팅 에이전트 응답 생성 모듈
"""

import json
import logging
from typing import Dict, Any
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from .utils import format_prompts_for_response, clean_json_response, create_default_action_result
from .enums import BUSINESS_PROMPT_MAPPING, ALL_PROMPT_FILES

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """응답 생성 클래스"""
    
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self.response_generation_system_prompt = self._create_response_generation_prompt()
        self.flow_control_system_prompt = self._create_flow_control_prompt()
    
    def _create_response_generation_prompt(self) -> str:
        """응답 생성 시스템 프롬프트"""
        return """당신은 친근하고 전문적인 마케팅 컨설턴트입니다. 
사용자의 상황을 고려한 맞춤형 조언을 제공합니다.

응답 원칙:
1. 개인화된 구체적 조언
2. 즉시 실행 가능한 팁
3. 친근하고 이해하기 쉬운 톤
4. 적절한 이모지 사용
5. 300-500자 내외로 간결하게

업종별 전문성과 사용자 컨텍스트를 최대한 활용하세요."""

    def _create_flow_control_prompt(self) -> str:
        """진행 제어 시스템 프롬프트"""
        return """대화 진행을 최적화하는 전문가입니다.
사용자의 상황과 의도에 따라 최적의 다음 액션을 결정합니다.

가능한 액션:
- continue_immediate: 즉시 응답으로 완료
- start_structured: 체계적 4단계 상담 시작
- jump_to_stage: 특정 단계로 이동
- collect_more_info: 추가 정보 수집
- provide_strategy: 전략 제안
- pause_conversation: 대화 일시 중단

사용자에게 최대한 도움이 되는 방향으로 결정하세요."""

    def generate_contextual_response(self, user_input: str, intent: Dict[str, Any], 
                                   context: Dict[str, Any]) -> str:
        """컨텍스트 기반 응답 생성"""
        logger.info(f"[단계 로그] 컨텍스트 기반 응답 생성 시작 - 현재 단계: {context.get('current_stage', '없음')}")

        # 업종별 프롬프트 로드
        stage_prompts = {}
        if context.get('business_type') and context['business_type'] != '일반':
            stage_prompts = self.load_stage_prompts_for_business(context['business_type'])
        else:
            stage_prompts = self.load_all_stage_prompts()
        
        response_prompt = f"""사용자의 마케팅 질문에 맞춤형 답변을 제공해주세요.

사용자 질문: "{user_input}"

의도 분석:
{json.dumps(intent, ensure_ascii=False, indent=2)}

현재 상황:
- 업종: {context.get('business_type', '일반')}
- 수집된 정보: {json.dumps(context.get('collected_info', {}), ensure_ascii=False)}
- 현재 단계: {context.get('current_stage', '없음')}
- 이전 대화: {context.get('history_summary', '새로운 대화')}

중요 지침:
1. 이미 알고 있는 사용자 정보를 적극 활용하세요
2. 업종이 확인된 경우, 해당 업종을 직접 언급하며 맞춤형 조언 제공
3. 예: "카페 창업"을 언급했다면, "어떤 비즈니스를 하시나요?" 대신 "카페 창업에 대한..."로 시작
4. 사용자가 제공한 컨텍스트를 무시하지 말고 연결성 있게 응답

활용 가능한 마케팅 가이드라인:
{format_prompts_for_response(stage_prompts)}

응답 요구사항:
1. 사용자 상황에 맞는 개인화된 조언
2. 즉시 실행 가능한 구체적 팁
3. 친근하고 전문적인 톤
4. 적절한 이모지와 구조화
5. 필요시 후속 진행 제안

응답 길이: 300-500자 내외"""

        try:
            messages = [
                SystemMessage(content=self.response_generation_system_prompt),
                HumanMessage(content=response_prompt)
            ]
            
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            raw_response = llm.invoke(messages)
            response = str(raw_response.content) if hasattr(raw_response, 'content') else str(raw_response)
            
            return response
            
        except Exception as e:
            logger.error(f"응답 생성 실패: {e}")
            return f"마케팅 질문에 대한 조언을 준비 중입니다. 조금 더 구체적으로 알려주신게 필요합니다."

    def determine_next_action(self, user_input: str, intent: Dict[str, Any], 
                            context: Dict[str, Any]) -> Dict[str, Any]:
        """다음 액션 결정"""
        logger.info(f"[단계 로그] 다음 액션 결정 시작 - 의도 타입: {intent.get('response_type', '알 수 없음')}")

        action_prompt = f"""현재 마케팅 상담 상황에서 다음 액션을 결정해주세요.

사용자 입력: "{user_input}"
의도 분석: {json.dumps(intent, ensure_ascii=False)}
현재 컨텍스트: {json.dumps(context, ensure_ascii=False)}

JSON 형태로 제공해주세요:
{{
    "recommended_action": "continue_immediate|start_structured|jump_to_stage|collect_info|provide_strategy|pause",
    "reasoning": "추천 이유",
    "parameters": {{
        "target_stage": "이동할 단계 (해당시)",
        "info_needed": ["수집할 정보들"],
        "immediate_response": true/false
    }},
    "user_options": ["사용자 선택지들"],
    "follow_up": "후속 진행 방향"
}}"""

        try:
            messages = [
                SystemMessage(content=self.flow_control_system_prompt),
                HumanMessage(content=action_prompt)
            ]
            
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            raw_response = llm.invoke(messages)
            response = str(raw_response.content) if hasattr(raw_response, 'content') else str(raw_response)
            
            # JSON 파싱
            if isinstance(response, str):
                cleaned = clean_json_response(response)
                try:
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    logger.warning(f"JSON 파싱 실패: {cleaned[:100]}")
                    return create_default_action_result()
            return response
            
        except Exception as e:
            logger.error(f"다음 액션 결정 실패: {e}")
            return create_default_action_result()

    def load_stage_prompts_for_business(self, business_type: str) -> Dict[str, str]:
        """업종별 단계 프롬프트 로드"""
        prompts = {}
        
        prompt_files = BUSINESS_PROMPT_MAPPING.get(business_type, [])
        
        for prompt_file in prompt_files:
            try:
                prompt_path = self.prompts_dir / prompt_file
                if prompt_path.exists():
                    with open(prompt_path, 'r', encoding='utf-8') as f:
                        prompts[prompt_file.replace('.md', '')] = f.read()
            except Exception as e:
                logger.error(f"프롬프트 로드 실패 ({prompt_file}): {e}")
        
        return prompts

    def load_all_stage_prompts(self) -> Dict[str, str]:
        """모든 단계 프롬프트 로드"""
        prompts = {}
        
        for prompt_file in ALL_PROMPT_FILES:
            try:
                prompt_path = self.prompts_dir / prompt_file
                if prompt_path.exists():
                    with open(prompt_path, 'r', encoding='utf-8') as f:
                        prompts[prompt_file.replace('.md', '')] = f.read()
            except Exception as e:
                logger.error(f"프롬프트 로드 실패 ({prompt_file}): {e}")
        
        return prompts
