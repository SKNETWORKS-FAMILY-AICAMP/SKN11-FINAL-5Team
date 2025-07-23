"""
LLM 기반 유연한 4단계 마케팅 에이전트 매니저
- 순서 무관 즉시 응답
- 중간 단계부터 시작
- 단계 건너뛰기
- 모든 의도 분석 LLM 기반
- 마케팅 툴 자동 활용
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from enum import Enum
import json
from datetime import datetime

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# 공통 모듈 임포트 (안전한 import)
try:
    from shared_modules import (
        get_config,
        get_llm_manager,
        get_vector_manager,
        get_or_create_conversation_session,
        create_message,
        get_recent_messages,
        insert_message_raw,
        get_session_context,
        create_success_response,
        create_error_response,
        create_marketing_response,
        get_current_timestamp,
        format_conversation_history,
        load_prompt_from_file,
        PromptTemplate
    )
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"shared_modules import 실패: {e}")

try:
    from marketing_agent.config.persona_config import PERSONA_CONFIG
except ImportError:
    PERSONA_CONFIG = {}

try:
    from marketing_agent.config.prompts_config import PROMPT_META
except ImportError:
    PROMPT_META = {}

try:
    from marketing_agent.utils import get_marketing_analysis_tools
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"analysis_tools import 실패: {e}")
    def get_marketing_analysis_tools():
        return None

logger = logging.getLogger(__name__)

class MarketingStage(Enum):
    """4단계 마케팅 프로세스"""
    ANY_QUESTION = "any_question"                   # 순서 무관 즉시 응답
    STAGE_1_GOAL = "stage_1_goal"                   # 1단계: 목표 정의
    STAGE_2_TARGET = "stage_2_target"               # 2단계: 타겟 분석
    STAGE_3_STRATEGY = "stage_3_strategy"           # 3단계: 전략 기획
    STAGE_4_EXECUTION = "stage_4_execution"         # 4단계: 실행 계획
    COMPLETED = "completed"                         # 완료

class ResponseType(Enum):
    """응답 타입"""
    IMMEDIATE_ANSWER = "immediate_answer"           # 즉시 응답
    STAGE_PROGRESS = "stage_progress"               # 단계 진행
    FLOW_CONTROL = "flow_control"                   # 진행 제어
    COMPREHENSIVE = "comprehensive"                 # 종합 전략
    CLARIFICATION = "clarification"                 # 명확화 필요
    TOOL_REQUIRED = "tool_required"                 # 마케팅 툴 필요


def clean_json_response(response: str) -> str:
    """
    LLM 응답에서 코드블록(````json ... ````)을 제거하고 JSON만 추출
    """
    cleaned = response.strip()
    if cleaned.startswith("```"):
        # 첫번째 ``` 제거
        cleaned = cleaned.strip("`")
        # "json" 태그 제거
        cleaned = cleaned.replace("json", "", 1).strip()
        # 마지막 ``` 제거
        if cleaned.endswith("```"):
            cleaned = cleaned[:cleaned.rfind("```")].strip()
    return cleaned

class Enhanced4StageMarketingManager:
    """LLM 기반 유연한 4단계 마케팅 에이전트 관리자"""
    
    def __init__(self):
        """마케팅 매니저 초기화"""
        self.config = get_config()
        self.llm_manager = get_llm_manager()
        self.vector_manager = get_vector_manager()
        self.analysis_tools = get_marketing_analysis_tools()
        
        # 프롬프트 디렉토리 설정
        self.prompts_dir = Path(__file__).parent.parent / 'prompts'
        
        # 대화 상태 관리 (메모리 기반)
        self.conversation_states: Dict[int, 'FlexibleConversationState'] = {}
        
        # LLM 프롬프트 템플릿들
        self.intent_analysis_system_prompt = self._create_intent_analysis_prompt()
        self.response_generation_system_prompt = self._create_response_generation_prompt()
        self.flow_control_system_prompt = self._create_flow_control_prompt()
    
    def _create_intent_analysis_prompt(self) -> str:
        """의도 분석 시스템 프롬프트"""
        return """당신은 마케팅 상담 전문가입니다. 사용자의 입력을 분석하여 최적의 응답 방식을 결정합니다.

분석 기준:
1. 응답 타입 결정:
   - immediate_answer: 바로 답변 가능한 일반적 질문
   - stage_progress: 특정 단계 진행 관련
   - flow_control: 대화 제어 (중단/재개/건너뛰기)
   - comprehensive: 종합적 전략 필요
   - clarification: 추가 정보 필요
   - tool_required: 마케팅 툴 사용 필요

2. 사용자 의도:
   - 주요 목적과 정보 필요도
   - 긴급도와 구체성 수준
   - 진행 방식 선호도

3. 컨텍스트 활용:
   - 기존 정보 활용 필요성
   - 개인화 수준
   - 업종별 맞춤화

4. 마케팅 툴 필요성 판단:
   - 트렌드 분석: 키워드 트렌드, 검색량 분석이 필요한 경우 (모든 단계에서 가능)
   - 해시태그 분석: 인스타그램, SNS 마케팅 관련 질문 (모든 단계에서 가능)
   - 콘텐츠 생성: 블로그, 인스타그램 콘텐츠 제작 요청 (**단, 4단계(실행 계획)에서만 가능**)
   - 키워드 연구: SEO, 검색 마케팅 관련 질문 (모든 단계에서 가능)

5. 단계별 제한 사항:
   - 콘텐츠 생성은 반드시 4단계(실행 계획)에서만 수행
   - 다른 단계에서 콘텐츠 생성 요청시 flow_control로 처리하거나 단계 이동 안내

응답은 반드시 JSON 형태로 제공하세요."""

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

    def analyze_user_intent_with_llm(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """LLM 기반 사용자 의도 분석"""
        logger.info(f"[단계 로그] 사용자 의도 분석 시작 - 입력: {user_input[:50]}...")
        
        # 먼저 비즈니스 유형
        detected_business = self.detect_business_type_with_llm(user_input, context)
        if detected_business != "일반":
            context["business_type"] = detected_business
            logger.info(f"[단계 로그] - 비즈니스 유형 감지: {detected_business}")
        
        analysis_prompt = f"""현재 마케팅 상담 상황을 분석해주세요.

사용자 입력: "{user_input}"

현재 컨텍스트:
- 대화 모드: {context.get('conversation_mode', 'flexible')}
- 현재 단계: {context.get('current_stage', 'none')}
- 수집된 정보: {json.dumps(context.get('collected_info', {}), ensure_ascii=False, indent=2)}
- 업종: {context.get('business_type', '미확인')}
- 대화 히스토리: {context.get('history_summary', '새 대화')}

다음을 JSON 형태로 분석해주세요:
{{
    "response_type": "immediate_answer|stage_progress|flow_control|comprehensive|clarification|tool_required",
    "user_intent": {{
        "primary_goal": "사용자의 주요 목적",
        "information_need": "필요한 정보",
        "urgency_level": "high|medium|low",
        "specificity": "general|specific|very_specific"
    }},
    "flow_control": {{
        "wants_immediate": true/false,
        "wants_structured": true/false,
        "stage_preference": "1|2|3|4|any|none",
        "control_command": "pause|resume|skip|restart|next|none"
    }},
    "context_needs": {{
        "use_existing_info": true/false,
        "business_type_detection": "필요시 업종",
        "personalization_level": "high|medium|low"
    }},
    "tool_requirements": {{
        "needs_tool": true/false,
        "tool_type": "trend_analysis|hashtag_analysis|content_generation|keyword_research|none",
        "target_keyword": "분석할 주요 키워드",
        "content_type": "blog|instagram|general",
        "reasoning": "툴 사용 이유"
    }},
    "suggested_action": "추천하는 다음 액션"
}}"""

        try:
            messages = [
                SystemMessage(content=self.intent_analysis_system_prompt),
                HumanMessage(content=analysis_prompt)
            ]
            
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            raw_response = llm.invoke(messages)
            response = str(raw_response.content) if hasattr(raw_response, 'content') else str(raw_response)
            
            # JSON 파싱
            if isinstance(response, str):
                cleaned = clean_json_response(response)
                try:
                    logger.info("[단계 로그] 정보 추출 결과 파싱 시작")
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    logger.warning(f"JSON 파싱 실패: {cleaned[:100]}")
                    return self._create_default_intent_analysis(user_input)
                
            return response
            
        except Exception as e:
            logger.error(f"의도 분석 실패: {e}")
            return self._create_default_intent_analysis(user_input)

    def _create_default_intent_analysis(self, user_input: str) -> Dict[str, Any]:
        """기본 의도 분석 결과"""
        return {
            "response_type": "immediate_answer",
            "user_intent": {
                "primary_goal": "마케팅 정보 획득",
                "information_need": user_input,
                "urgency_level": "medium",
                "specificity": "general"
            },
            "flow_control": {
                "wants_immediate": True,
                "wants_structured": False,
                "stage_preference": "any",
                "control_command": "none"
            },
            "context_needs": {
                "use_existing_info": False,
                "business_type_detection": "일반",
                "personalization_level": "medium"
            },
            "tool_requirements": {
                "needs_tool": False,
                "tool_type": "none",
                "target_keyword": "",
                "content_type": "general",
                "reasoning": ""
            },
            "suggested_action": "provide_immediate_answer"
        }

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
{self._format_prompts_for_response(stage_prompts)}

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

    def _format_prompts_for_response(self, prompts: Dict[str, str]) -> str:
        """응답 생성용 프롬프트 포맷팅"""
        if not prompts:
            return "일반적인 마케팅 가이드라인을 활용합니다."
        
        formatted = []
        for name, content in prompts.items():
            # 프롬프트 내용을 요약해서 포함 (너무 길면 잘라냄)
            summary = content[:200] + "..." if len(content) > 200 else content
            formatted.append(f"[{name}] {summary}")
        
        return "\n".join(formatted)

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
                    return self._create_default_action_result()
            return response
            
        except Exception as e:
            logger.error(f"다음 액션 결정 실패: {e}")
            return self._create_default_action_result()
    
    def _create_default_action_result(self) -> Dict[str, Any]:
        """기본 액션 결과"""
        return {
            "recommended_action": "continue_immediate",
            "reasoning": "즉시 응답 제공",
            "parameters": {"immediate_response": True},
            "user_options": ["체계적 상담 시작", "추가 질문"],
            "follow_up": "상황에 따라 진행"
        }

    def detect_business_type_with_llm(self, user_input: str, context: Dict[str, Any]) -> str:
        """LLM 기반 업종 감지"""
        logger.info(f"[단계 로그] 업종 감지 시작 - 현재 컨텍스트: {context.get('business_type', '미확인')}")

        
        detection_prompt = f"""다음 사용자 입력에서 비즈니스 업종을 감지해주세요.

사용자 입력: "{user_input}"
기존 컨텍스트: {json.dumps(context.get('collected_info', {}), ensure_ascii=False)}

다음 중에서 가장 적합한 업종을 선택하거나 새로운 업종을 제안해주세요:
- 앱 (모바일앱, 게임앱, 생산성앱 등)
- 뷰티 (미용실, 네일샵, 피부관리, 뷰티 플랫폼 등)
- 크리에이터 (유튜브, 인플루언서, 1인 콘텐츠 제작자 등)
- 음식점 (카페, 레스토랑, 배달전문점, 푸드트럭 등)
- 온라인쇼핑몰 (이커머스, 온라인 셀러, 라이브커머스 등)
- 서비스업 (컨설팅, 교육, 헬스케어 등)
- 기타 (신규 업종 또는 융합 업종 등)

업종명만 간단히 답변해주세요. (예: "뷰티", "음식점", "온라인쇼핑몰")"""

        try:
            messages = [
                SystemMessage(content="업종 분류 전문가입니다. 간결하게 업종명만 답변합니다."),
                HumanMessage(content=detection_prompt)
            ]
            
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            raw_response = llm.invoke(messages)
            response = str(raw_response.content) if hasattr(raw_response, 'content') else str(raw_response)
            
            return response.strip() if response else "일반"
            
        except Exception as e:
            logger.error(f"업종 감지 실패: {e}")
            return "일반"

    async def execute_marketing_tool(self, user_input: str, intent_analysis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """마케팅 툴 실행"""
        try:
            tool_requirements = intent_analysis.get("tool_requirements", {})
            tool_type = tool_requirements.get("tool_type", "none")
            target_keyword = tool_requirements.get("target_keyword", "")
            content_type = tool_requirements.get("content_type", "general")
            current_stage = context.get("current_stage", "any_question")
            
            if not self.analysis_tools:
                return {
                    "success": False,
                    "error": "마케팅 분석 도구가 초기화되지 않았습니다.",
                    "tool_type": tool_type
                }
            
            logger.info(f"[툴 실행] 툴 타입: {tool_type}, 키워드: {target_keyword}, 현재 단계: {current_stage}")
            
            # 콘텐츠 생성은 4단계(실행 계획)에서만 가능
            if tool_type == "content_generation":
                if current_stage != "stage_4_execution":
                    return {
                        "success": False,
                        "error": "콘텐츠 생성은 4단계(실행 계획) 단계에서만 가능합니다.",
                        "tool_type": tool_type,
                        "stage_requirement": "stage_4_execution",
                        "current_stage": current_stage,
                        "suggestion": "먼저 1단계(목표 정의) → 2단계(타겟 분석) → 3단계(전략 기획)를 완료한 후 콘텐츠를 생성해보세요."
                    }
            
            # 키워드가 없으면 사용자 입력에서 추출
            if not target_keyword:
                target_keyword = await self._extract_keyword_from_input(user_input)
            
            # 툴 타입별 실행
            if tool_type == "trend_analysis":
                keywords = [target_keyword] + await self._generate_related_keywords(target_keyword, 4)
                result = await self.analysis_tools.analyze_naver_trends(keywords)
                
            elif tool_type == "hashtag_analysis":
                result = await self.analysis_tools.analyze_instagram_hashtags(
                    question=user_input,
                    user_hashtags=[target_keyword]
                )
                
            elif tool_type == "content_generation":
                # 이미 위에서 단계 체크를 했으므로 여기서는 바로 실행
                if content_type == "blog":
                    result = await self.analysis_tools.create_blog_content_workflow(target_keyword)
                elif content_type == "instagram":
                    result = await self.analysis_tools.create_instagram_content_workflow(target_keyword)
                else:
                    # 일반적인 콘텐츠 생성
                    result = await self.analysis_tools.generate_instagram_content()
                    
            elif tool_type == "keyword_research":
                keywords = await self.analysis_tools.generate_related_keywords(target_keyword, 15)
                trend_result = await self.analysis_tools.analyze_naver_trends(keywords[:5])
                result = {
                    "success": True,
                    "keywords": keywords,
                    "trend_data": trend_result
                }
                
            else:
                return {
                    "success": False,
                    "error": f"지원하지 않는 툴 타입: {tool_type}",
                    "tool_type": tool_type
                }
            
            # 결과에 툴 정보 추가
            if isinstance(result, dict):
                result["tool_type"] = tool_type
                result["target_keyword"] = target_keyword
                result["content_type"] = content_type
            
            logger.info(f"[툴 실행] 완료: {result.get('success', False)}")
            return result
            
        except Exception as e:
            logger.error(f"마케팅 툴 실행 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_type": tool_requirements.get("tool_type", "unknown")
            }
    
    async def generate_response_with_tool_result(self, user_input: str, intent_analysis: Dict[str, Any], 
                                               context: Dict[str, Any], tool_result: Dict[str, Any]) -> str:
        """툴 결과를 포함한 응답 생성"""
        try:
            tool_type = tool_result.get("tool_type", "unknown")
            success = tool_result.get("success", False)
            
            if not success:
                error_msg = tool_result.get("error", "알 수 없는 오류")
                
                # 단계 제한 오류 특별 처리 (콘텐츠 생성)
                if "stage_requirement" in tool_result:
                    current_stage = tool_result.get("current_stage", "unknown")
                    required_stage = tool_result.get("stage_requirement", "unknown")
                    suggestion = tool_result.get("suggestion", "")
                    
                    response = f"🚧 **콘텐츠 생성 단계 안내**\n\n"
                    response += f"현재 단계: **{current_stage}**\n"
                    response += f"요구 단계: **{required_stage}**\n\n"
                    response += f"📄 **안내사항**:\n{suggestion}\n\n"
                    response += "🚀 **단계별 진행 방법**:\n"
                    response += "• '단계 이동' 또는 '4단계로 이동'이라고 말씩하세요\n"
                    response += "• '체계적 상담 시작'으로 1단계부터 진행하세요\n"
                    response += "• 현재 단계에서 다른 마케팅 질문을 해주세요"
                    
                    return response
                
                # 일반적인 오류 처리
                return f"죄송합니다. {tool_type} 분석 중 오류가 발생했습니다: {error_msg}\n\n일반적인 마케팅 조언을 드리겠습니다."
            
            # 툴 타입별 결과 포맷팅
            if tool_type == "trend_analysis":
                return await self._format_trend_analysis_response(user_input, tool_result, context)
            elif tool_type == "hashtag_analysis":
                return await self._format_hashtag_analysis_response(user_input, tool_result, context)
            elif tool_type == "content_generation":
                return await self._format_content_generation_response(user_input, tool_result, context)
            elif tool_type == "keyword_research":
                return await self._format_keyword_research_response(user_input, tool_result, context)
            else:
                return await self._format_general_tool_response(user_input, tool_result, context)
                
        except Exception as e:
            logger.error(f"툴 결과 응답 생성 실패: {e}")
            return "마케팅 분석을 진행했지만 결과 처리 중 오류가 발생했습니다. 다시 시도해주세요."
    
    async def _extract_keyword_from_input(self, user_input: str) -> str:
        """사용자 입력에서 키워드 추출"""
        try:
            from shared_modules import get_llm_manager
            llm_manager = get_llm_manager()
            
            messages = [
                {"role": "system", "content": "사용자 입력에서 마케팅 분석에 가장 적합한 주요 키워드 1개를 추출하세요. 키워드만 출력하세요."},
                {"role": "user", "content": f"다음 질문에서 주요 키워드를 추출해주세요: {user_input}"}
            ]
            
            result = llm_manager.generate_response_sync(messages)
            return result.strip() if result else "마케팅"
            
        except Exception as e:
            logger.error(f"키워드 추출 실패: {e}")
            return "마케팅"
    
    async def _generate_related_keywords(self, base_keyword: str, count: int = 5) -> List[str]:
        """관련 키워드 생성 (간단 버전)"""
        try:
            if self.analysis_tools:
                keywords = await self.analysis_tools.generate_related_keywords(base_keyword, count)
                return keywords[1:]  # 기본 키워드 제외
            return []
        except Exception as e:
            logger.error(f"관련 키워드 생성 실패: {e}")
            return []
    
    async def _format_trend_analysis_response(self, user_input: str, tool_result: Dict[str, Any], context: Dict[str, Any]) -> str:
        """트렌드 분석 결과 포맷팅"""
        try:
            data = tool_result.get("data", [])
            keywords = tool_result.get("keywords", [])
            period = tool_result.get("period", "")
            
            response = f"📈 **키워드 트렌드 분석 결과**\n\n"
            response += f"🔍 **분석 기간**: {period}\n"
            response += f"🎯 **분석 키워드**: {', '.join(keywords)}\n\n"
            
            if data:
                response += "📊 **트렌드 순위**:\n"
                # 트렌드 데이터 정렬 및 표시
                trend_scores = []
                for result in data[:5]:  # 상위 5개만
                    if "data" in result:
                        scores = [item["ratio"] for item in result["data"] if "ratio" in item]
                        avg_score = sum(scores) / len(scores) if scores else 0
                        trend_scores.append((result["title"], avg_score))
                
                trend_scores.sort(key=lambda x: x[1], reverse=True)
                
                for i, (keyword, score) in enumerate(trend_scores, 1):
                    response += f"{i}. **{keyword}** (평균 검색량: {score:.1f})\n"
                
                response += "\n💡 **마케팅 인사이트**:\n"
                if trend_scores:
                    top_keyword = trend_scores[0][0]
                    response += f"• '{top_keyword}'가 가장 높은 검색 트렌드를 보이고 있습니다.\n"
                    response += f"• 이 키워드를 중심으로 콘텐츠를 제작하면 높은 관심도를 얻을 수 있습니다.\n"
                
            else:
                response += "트렌드 데이터를 가져오는데 문제가 있었습니다. 일반적인 키워드 활용 방안을 제시드리겠습니다.\n"
            
            # 후속 제안
            response += "\n🎬 **다음 단계 제안**:\n"
            response += "• 블로그 콘텐츠 제작\n• 인스타그램 해시태그 분석\n• SEO 최적화 전략 수립\n"
            
            return response
            
        except Exception as e:
            logger.error(f"트렌드 분석 응답 포맷팅 실패: {e}")
            return "트렌드 분석을 완료했지만 결과 정리 중 오류가 발생했습니다."
    
    async def _format_hashtag_analysis_response(self, user_input: str, tool_result: Dict[str, Any], context: Dict[str, Any]) -> str:
        """해시태그 분석 결과 포맷팅"""
        try:
            searched_hashtags = tool_result.get("searched_hashtags", [])
            popular_hashtags = tool_result.get("popular_hashtags", [])
            total_posts = tool_result.get("total_posts", 0)
            
            response = f"#️⃣ **인스타그램 해시태그 분석 결과**\n\n"
            response += f"🔍 **분석 해시태그**: #{', #'.join(searched_hashtags)}\n"
            response += f"📊 **분석된 포스트 수**: {total_posts:,}개\n\n"
            
            if popular_hashtags:
                response += "🔥 **추천 인기 해시태그**:\n"
                for i, hashtag in enumerate(popular_hashtags[:15], 1):
                    if not hashtag.startswith('#'):
                        hashtag = f"#{hashtag}"
                    response += f"{i}. {hashtag}\n"
                
                response += "\n💡 **해시태그 활용 팁**:\n"
                response += "• 인기 해시태그와 틈새 해시태그를 적절히 조합하세요\n"
                response += "• 포스트당 20-30개의 해시태그 사용을 권장합니다\n"
                response += "• 브랜드만의 고유 해시태그도 함께 활용하세요\n"
            else:
                response += "해시태그 데이터 수집에 문제가 있었습니다. 일반적인 해시태그 전략을 제안드리겠습니다.\n"
            
            # 후속 제안
            response += "\n📝 **다음 단계 제안**:\n"
            response += "• 인스타그램 콘텐츠 제작\n• 해시태그 성과 분석\n• 경쟁사 해시태그 연구\n"
            
            return response
            
        except Exception as e:
            logger.error(f"해시태그 분석 응답 포맷팅 실패: {e}")
            return "해시태그 분석을 완료했지만 결과 정리 중 오류가 발생했습니다."
    
    async def _format_content_generation_response(self, user_input: str, tool_result: Dict[str, Any], context: Dict[str, Any]) -> str:
        """콘텐츠 생성 결과 포맷팅"""
        try:
            content_type = tool_result.get("content_type", "general")
            base_keyword = tool_result.get("base_keyword", "")
            
            response = f"✍️ **{content_type.upper()} 콘텐츠 생성 완료**\n\n"
            response += f"🎯 **주요 키워드**: {base_keyword}\n\n"
            
            if content_type == "blog":
                blog_content = tool_result.get("blog_content", {})
                if blog_content and "full_content" in blog_content:
                    response += "📝 **생성된 블로그 콘텐츠**:\n"
                    response += f"{blog_content['full_content'][:1000]}...\n\n"
                    response += f"📊 **콘텐츠 정보**: 약 {blog_content.get('word_count', 0)}단어\n"
                
            elif content_type == "instagram":
                instagram_content = tool_result.get("instagram_content", {})
                if instagram_content and "post_content" in instagram_content:
                    response += "📱 **생성된 인스타그램 포스트**:\n"
                    response += f"{instagram_content['post_content']}\n\n"
                    
                    hashtags = instagram_content.get("selected_hashtags", [])
                    if hashtags:
                        response += f"#️⃣ **추천 해시태그** ({len(hashtags)}개):\n"
                        response += " ".join(hashtags[:20]) + "\n\n"
            
            # 관련 키워드 정보
            related_keywords = tool_result.get("related_keywords", [])
            if related_keywords:
                response += f"🔑 **관련 키워드**: {', '.join(related_keywords[:10])}\n\n"
            
            response += "💡 **활용 가이드**:\n"
            response += "• 생성된 콘텐츠를 브랜드 톤앤매너에 맞게 수정하세요\n"
            response += "• 타겟 고객의 관심사를 반영해 개인화하세요\n"
            response += "• 정기적인 콘텐츠 업데이트로 지속적인 관심을 유도하세요\n"
            
            return response
            
        except Exception as e:
            logger.error(f"콘텐츠 생성 응답 포맷팅 실패: {e}")
            return "콘텐츠 생성을 완료했지만 결과 정리 중 오류가 발생했습니다."
    
    async def _format_keyword_research_response(self, user_input: str, tool_result: Dict[str, Any], context: Dict[str, Any]) -> str:
        """키워드 연구 결과 포맷팅"""
        try:
            keywords = tool_result.get("keywords", [])
            trend_data = tool_result.get("trend_data", {})
            
            response = f"🔍 **키워드 연구 결과**\n\n"
            
            if keywords:
                response += f"📝 **추천 키워드** ({len(keywords)}개):\n"
                for i, keyword in enumerate(keywords[:15], 1):
                    response += f"{i}. {keyword}\n"
                response += "\n"
            
            if trend_data.get("success") and trend_data.get("data"):
                response += "📈 **트렌드 분석**:\n"
                for result in trend_data["data"][:5]:
                    if "data" in result:
                        scores = [item["ratio"] for item in result["data"] if "ratio" in item]
                        avg_score = sum(scores) / len(scores) if scores else 0
                        response += f"• {result['title']}: 평균 검색량 {avg_score:.1f}\n"
                response += "\n"
            
            response += "🎯 **SEO 활용 전략**:\n"
            response += "• 장꼬리 키워드(Long-tail)를 활용해 경쟁도를 낮추세요\n"
            response += "• 계절성과 트렌드를 고려한 키워드 선택을 하세요\n"
            response += "• 지역 기반 키워드로 로컬 SEO를 강화하세요\n"
            
            return response
            
        except Exception as e:
            logger.error(f"키워드 연구 응답 포맷팅 실패: {e}")
            return "키워드 연구를 완료했지만 결과 정리 중 오류가 발생했습니다."
    
    async def _format_general_tool_response(self, user_input: str, tool_result: Dict[str, Any], context: Dict[str, Any]) -> str:
        """일반 툴 결과 포맷팅"""
        return f"마케팅 분석을 완료했습니다. 결과를 바탕으로 맞춤형 전략을 제안드리겠습니다."

    def load_stage_prompts_for_business(self, business_type: str) -> Dict[str, str]:
        """업종별 단계 프롬프트 로드"""
        prompts = {}
        
        # 업종별 프롬프트 파일 매핑
        business_prompt_mapping = {
            "뷰티": [
                "personal_branding.md", "social_media_marketing.md", "local_marketing.md",
                "content_marketing.md", "influencer_marketing.md", "blog_marketing.md"
            ],
            "음식점": [
                "local_marketing.md", "social_media_marketing.md", "content_marketing.md",
                "email_marketing.md", "blog_marketing.md", "marketing_fundamentals.md"
            ],
            "온라인쇼핑몰": [
                "digital_advertising.md", "content_marketing.md", "conversion_optimization.md",
                "marketing_automation.md", "email_marketing.md", "marketing_metrics.md"
            ],
            "서비스업": [
                "personal_branding.md", "content_marketing.md", "blog_marketing.md",
                "marketing_fundamentals.md", "marketing_metrics.md"
            ],
            "앱": [
                "viral_marketing.md", "email_marketing.md", "marketing_metrics.md",
                "content_marketing.md"
            ],
            "크리에이터": [
                "personal_branding.md",
                "content_marketing.md", "blog_marketing.md", "social_media_marketing.md",
                "influencer_marketing.md"
            ]
        }

        
        prompt_files = business_prompt_mapping.get(business_type, [])
        
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
        
        all_prompt_files = [
            "marketing_fundamentals.md",
            "marketing_metrics.md", 
            "personal_branding.md",
            "social_media_marketing.md",
            "influencer_marketing.md",
            "local_marketing.md",
            "digital_advertising.md",
            "content_marketing.md",
            "blog_marketing.md",
            "viral_marketing.md",
            "conversion_optimization.md",
            "email_marketing.md",
            "marketing_automation.md"
        ]
        
        for prompt_file in all_prompt_files:
            try:
                prompt_path = self.prompts_dir / prompt_file
                if prompt_path.exists():
                    with open(prompt_path, 'r', encoding='utf-8') as f:
                        prompts[prompt_file.replace('.md', '')] = f.read()
            except Exception as e:
                logger.error(f"프롬프트 로드 실패 ({prompt_file}): {e}")
        
        return prompts

    def get_or_create_conversation_state(self, conversation_id: int, user_id: int) -> 'FlexibleConversationState':
        """대화 상태 조회 또는 생성"""
        if conversation_id not in self.conversation_states:
            self.conversation_states[conversation_id] = FlexibleConversationState(conversation_id, user_id)
        return self.conversation_states[conversation_id]

    def handle_flow_control(self, command: str, state: 'FlexibleConversationState', 
                                user_input: str) -> Dict[str, Any]:
        """진행 제어 처리"""
        logger.info(f"[단계 로그] 진행 제어 처리 - 명령: {command}, 현재 단계: {state.current_stage.value}")

        
        if command == "pause":
            state.is_paused = True
            return {
                "action": "paused",
                "message": f"🛑 대화를 일시 중단했습니다.\n\n현재 진행 상황을 저장했습니다. '재개'라고 말씀하시면 이어서 진행하겠습니다.",
                "pause_info": {
                    "stage": state.current_stage.value,
                    "completion": state.get_overall_completion_rate(),
                    "paused_at": datetime.now().isoformat()
                }
            }
        
        elif command == "resume":
            state.is_paused = False
            return {
                "action": "resumed", 
                "message": f"▶️ 대화를 재개합니다!\n\n현재 {state.current_stage.value} 단계에서 계속 진행하겠습니다.",
                "current_stage": state.current_stage.value
            }
        
        elif command == "skip":
            available_stages = [s for s in MarketingStage if s != state.current_stage and s not in [MarketingStage.ANY_QUESTION, MarketingStage.COMPLETED]]
            return {
                "action": "stage_selection",
                "message": "어떤 단계로 이동하시겠습니까?",
                "options": [s.value for s in available_stages]
            }
        
        elif command == "restart":
            state.reset_conversation()
            return {
                "action": "restarted",
                "message": "🔄 처음부터 다시 시작합니다!\n\n어떤 방식으로 진행하시겠습니까?",
                "options": ["체계적 4단계 진행", "즉시 질문 응답", "특정 단계로 이동"]
            }
        
        elif command == "next":
            next_stage = state.get_next_stage()
            if next_stage:
                state.current_stage = next_stage
                
                # 단계 이동 후 해당 단계의 질문 자동 생성
                stage_questions = {
                    MarketingStage.STAGE_1_GOAL: "🎯 비즈니스의 마케팅 목표를 명확히 해보세요! 구체적으로 어떤 결과를 얻고 싶으신가요? (예: 매출 증대, 브랜드 인지도 향상, 고객 유치 등)",
                    MarketingStage.STAGE_2_TARGET: "🎯 타겟 고객 분석을 시작합니다! 주요 타겟 고객은 누구인가요? 연령대, 성별, 관심사, 라이프스타일 등을 알려주세요.",
                    MarketingStage.STAGE_3_STRATEGY: "📊 마케팅 전략 기획 단계입니다! 어떤 마케팅 채널에 집중하고 싶으신가요? (예: SNS, 블로그, 광고, 이벤트 등) 예산과 목표도 함께 알려주세요.",
                    MarketingStage.STAGE_4_EXECUTION: "🚀 마케팅 실행 단계입니다! 이제 구체적인 콘텐츠나 캠페인을 만들어보세요. 블로그 글, 인스타그램 포스트, 광고 콘텐츠 중 무엇을 만들고 싶으신가요?"
                }
                
                stage_message = f"⏭️ {next_stage.value} 단계로 이동했습니다.\n\n"
                stage_question = stage_questions.get(next_stage, "새로운 단계에서 어떤 도움이 필요하신가요?")
                
                return {
                    "action": "next_stage",
                    "message": stage_message + stage_question,
                    "new_stage": next_stage.value,
                    "include_question": True
                }
            else:
                return {
                    "action": "no_next_stage",
                    "message": "더 이상 진행할 단계가 없습니다. 현재 단계를 완료해주세요."
                }
        
        return {"action": "unknown_command", "message": f"'{command}' 명령을 인식할 수 없습니다."}

    def jump_to_stage(self, target_stage: str, state: 'FlexibleConversationState') -> Dict[str, Any]:
        """특정 단계로 이동"""
        
        stage_mapping = {
            "1": MarketingStage.STAGE_1_GOAL,
            "2": MarketingStage.STAGE_2_TARGET,
            "3": MarketingStage.STAGE_3_STRATEGY,
            "4": MarketingStage.STAGE_4_EXECUTION,
            "목표": MarketingStage.STAGE_1_GOAL,
            "타겟": MarketingStage.STAGE_2_TARGET,
            "전략": MarketingStage.STAGE_3_STRATEGY,
            "실행": MarketingStage.STAGE_4_EXECUTION,
            "any": MarketingStage.ANY_QUESTION
        }
        
        if target_stage not in stage_mapping:
            return {
                "success": False,
                "message": f"'{target_stage}' 단계를 찾을 수 없습니다.",
                "available_stages": list(stage_mapping.keys())
            }
        
        target_stage_enum = stage_mapping[target_stage]
        state.current_stage = target_stage_enum
        state.updated_at = datetime.now()
        
        # 자연스러운 단계 전환 메시지 (수집된 정보 활용)
        business_info = state.get_information("business_info_business_type") or "비즈니스"
        
        stage_messages = {
            MarketingStage.STAGE_1_GOAL: "🎯비즈니스의 마케팅 목표를 명확히 해보세요! 구체적으로 어떤 결과를 얻고 싶으신가요? (예: 매출 증대, 브랜드 인지도 향상, 고객 유치 등)",
            MarketingStage.STAGE_2_TARGET: "🎯타겟 고객 분석을 시작합니다! 주요 타겟 고객은 누구인가요? 연령대, 성별, 관심사, 라이프스타일 등을 알려주세요.",
            MarketingStage.STAGE_3_STRATEGY: "📊 마케팅 전략 기획 단계입니다! 어떤 마케팅 채널에 집중하고 싶으신가요?(예: SNS, 블로그, 광고, 이벤트 등) 예산과 목표도 함께 알려주세요.",
            MarketingStage.STAGE_4_EXECUTION: "🚀 마케팅 실행 단계입니다! 이제 구체적인 콘텐츠나 캐페인을 만들어보세요. 블로그 글, 인스타그램 포스트, 광고 콘텐츠 중 무엇을 만들고 싶으신가요?",
            MarketingStage.ANY_QUESTION: "자유롭게 마케팅 질문을 해주세요. 바로 답변드리겠습니다!"
        }
        
        return {
            "success": True,
            "message": stage_messages[target_stage_enum],
            "new_stage": target_stage_enum.value
        }
    
    def prepare_conversation_context(self, user_id: int, conversation_id: Optional[int]) -> Dict[str, Any]:
        """대화 컨텍스트 준비"""
        
        context = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "conversation_mode": "flexible",
            "current_stage": MarketingStage.ANY_QUESTION.value,
            "collected_info": {},
            "business_type": "일반",
            "history_summary": "새로운 대화"
        }
        
        if conversation_id and conversation_id in self.conversation_states:
            state = self.conversation_states[conversation_id]
            context.update({
                "current_stage": state.current_stage.value,
                "collected_info": state.collected_info,
                "business_type": state.detected_business_type,
                "history_summary": self.summarize_conversation_history(state)
            })
        
        return context

    def summarize_conversation_history(self, state: 'FlexibleConversationState') -> str:
        """대화 히스토리 요약"""
        
        if not hasattr(state, 'conversation_history') or not state.conversation_history:
            return "새로운 대화"
        
        # 최근 대화 요약 (간단하게)
        recent = state.conversation_history[-3:]
        collected_info = state.collected_info
        
        summary_parts = []
        if collected_info:
            summary_parts.append(f"수집된 정보: {len(collected_info)}개 항목")
        if state.detected_business_type != "일반":
            summary_parts.append(f"업종: {state.detected_business_type}")
        
        return " | ".join(summary_parts) if summary_parts else "마케팅 상담 진행 중"

    async def process_user_query(self, user_input: str, user_id: int, 
                          conversation_id: Optional[int] = None) -> Dict[str, Any]:
        """메인 쿼리 처리 함수"""
        return await self._process_user_query_async(user_input, user_id, conversation_id)

    async def _process_user_query_async(self, user_input: str, user_id: int, 
                                      conversation_id: Optional[int] = None) -> Dict[str, Any]:
        """비동기 사용자 쿼리 처리"""
        
        try:
            logger.info(f"[단계 로그] === 마케팅 쿼리 처리 시작 ===\n사용자 입력: {user_input[:50]}...\n사용자 ID: {user_id}\n대화 ID: {conversation_id}")
            
            # 대화 세션 처리
            logger.info("[단계 로그] 1. 대화 세션 처리 시작")
            session_info = get_or_create_conversation_session(user_id, conversation_id)
            conversation_id = session_info["conversation_id"]
            logger.info(f"[단계 로그] - 세션 처리 완료: {conversation_id}")
            
            # 대화 상태 조회/생성
            logger.info("[단계 로그] 2. 대화 상태 조회/생성")
            state = self.get_or_create_conversation_state(conversation_id, user_id)
            logger.info(f"[단계 로그] - 현재 단계: {state.current_stage.value}")
            
            # 사용자 메시지 저장
            with get_session_context() as db:
                create_message(db, conversation_id, "user", "marketing", user_input)
            
            # 대화 컨텍스트 준비
            logger.info("[단계 로그] 3. 대화 컨텍스트 준비")
            context = self.prepare_conversation_context(user_id, conversation_id)
            logger.info(f"[단계 로그] - 컨텍스트 준비 완료: {context.get('business_type')}, {context.get('current_stage')}")
            
            # 1. LLM 기반 의도 분석
            logger.info("[단계 로그] 4. LLM 의도 분석 시작")
            intent_analysis = self.analyze_user_intent_with_llm(user_input, context)
            logger.info(f"[단계 로그] - 의도 분석 완료: {intent_analysis.get('response_type', '알 수 없음')}")
            
            # 2. 업종 감지 (필요시) 및 정보 업데이트
            logger.info("[단계 로그] 5. 업종 감지 및 정보 업데이트")
            
            # 첫 번째 대화에서 업종 감지 및 저장
            if context.get("business_type") and context["business_type"] != "일반":
                state.detected_business_type = context["business_type"]
                state.add_information("business_info_business_type", context["business_type"], "auto_detected")
                logger.info(f"[단계 로그] - 업종 정보 저장: {context['business_type']}")
            
            # 추가 추출 또는 LLM 기반 감지
            if intent_analysis.get("context_needs", {}).get("business_type_detection"):
                detected_type = self.detect_business_type_with_llm(user_input, context)
                if detected_type != "일반" and detected_type != state.detected_business_type:
                    state.detected_business_type = detected_type
                    state.add_information("business_info_business_type", detected_type, "llm_detected")
                    context["business_type"] = detected_type
            
            # 3. 진행 제어 명령 처리
            logger.info("[단계 로그] 6. 진행 제어 명령 처리")
            flow_control = intent_analysis.get("flow_control", {})
            control_command = flow_control.get("control_command", "none")
            stage_preference = flow_control.get("stage_preference")
            logger.info(f"[단계 로그] - 제어 명령: {control_command}")
            
            if control_command != "none":
                control_result = self.handle_flow_control(control_command, state, user_input)
                response_content = control_result["message"]
                
                # 특별한 경우 처리
                if control_command == "skip" and "options" in control_result:
                    response_content += "\n\n선택 가능한 단계:\n" + "\n".join([f"• {opt}" for opt in control_result["options"]])
            
            elif stage_preference and stage_preference != "any" and stage_preference != "none":
                # 4. 단계 이동 처리 - 자연스러운 응답 생성
                logger.info("[단계 로그] 7. 단계 이동 처리")
                jump_result = self.jump_to_stage(stage_preference, state)
                
                if jump_result["success"]:
                    # 단계 이동 성공 - 자연스러운 메시지로 응답
                    response_content = jump_result["message"]
                else:
                    # 단계 이동 실패 - 오류 메시지
                    response_content = jump_result["message"]
            
            # 5. 마케팅 툴 사용 필요성 검사
            elif intent_analysis.get("response_type") == "tool_required" or intent_analysis.get("tool_requirements", {}).get("needs_tool"):
                logger.info("[단계 로그] 8. 마케팅 툴 사용 시작")
                tool_result = await self.execute_marketing_tool(user_input, intent_analysis, context)
                logger.info(f"[단계 로그] - 툴 실행 완료: {tool_result.get('success', False)}")
                
                # 툴 결과를 포함한 응답 생성
                response_content = await self.generate_response_with_tool_result(
                    user_input, intent_analysis, context, tool_result
                )
                
            # 6. 일반 응답 생성
            else:
                try:
                    logger.info("[단계 로그] 9. 일반 응답 생성 시작")
                    # 컨텍스트 기반 응답 생성
                    response_content = self.generate_contextual_response(user_input, intent_analysis, context)
                    logger.info("[단계 로그] - 응답 생성 완료")
                    
                    # 다음 액션 결정
                    next_action = self.determine_next_action(user_input, intent_analysis, context)
                    
                    # 사용자 옵션 추가
                    if next_action and next_action.get("user_options"):
                        options_text = "\n\n💡 **다음 옵션:**\n" + "\n".join([f"• {opt}" for opt in next_action["user_options"]])
                        response_content += options_text
                except Exception as e:
                    logger.error(f"응답 생성 중 오류 발생: {e}")
                    response_content = "죄송합니다. 응답 생성 중 오류가 발생했습니다."
            
            # 정보 수집 및 업데이트
            logger.info("[단계 로그] 10. 정보 수집 및 업데이트")
            self.update_collected_information(user_input, intent_analysis, state)
            logger.info(f"[단계 로그] - 수집된 정보 수: {len(state.collected_info)}")
            
            # 응답 메시지 저장
            insert_message_raw(
                conversation_id=conversation_id,
                sender_type="agent",
                agent_type="marketing",
                content=response_content
            )
            
            # 표준 응답 형식으로 반환
            logger.info("[단계 로그] === 마케팅 쿼리 처리 완료 ===")
            return create_marketing_response(
                conversation_id=conversation_id,
                answer=response_content,
                topics=[],
                sources="LLM 기반 유연한 마케팅 시스템",
                intent=intent_analysis.get("response_type", "flexible"),
                confidence=0.9,
                conversation_stage=state.current_stage.value,
                completion_rate=state.get_overall_completion_rate(),
                collected_info=state.collected_info,
                mcp_results={},
                multiturn_flow=True,
                flexible_mode=True,
                intent_analysis=intent_analysis
            )
            
        except Exception as e:
            logger.error(f"LLM 기반 마케팅 쿼리 처리 실패: {e}")
            return create_error_response(
                error_message=f"마케팅 상담 처리 중 오류가 발생했습니다: {str(e)}",
                error_code="LLM_MARKETING_ERROR"
            )

    def update_collected_information(self, user_input: str, intent_analysis: Dict[str, Any], 
                                         state: 'FlexibleConversationState'):
        """수집된 정보 업데이트"""
        logger.info(f"[단계 로그] 정보 수집 시작 - 현재 수집된 정보: {len(state.collected_info)}개")
        
        # LLM을 사용해 사용자 입력에서 정보 추출
        extraction_prompt = f"""사용자 입력에서 마케팅 상담에 유용한 정보를 추출해주세요.

사용자 입력: "{user_input}"
기존 정보: {json.dumps(state.collected_info, ensure_ascii=False)}

다음 항목들을 JSON 형태로 추출해주세요:
{{
    "business_info": {{
        "business_type": "업종",
        "business_name": "사업명",
        "location": "위치",
        "scale": "규모"
    }},
    "goals": {{
        "main_goal": "주요 목적",
        "target_metrics": "목표 지표",
        "timeline": "목표 기한"
    }},
    "target_audience": {{
        "age_group": "연령대",
        "gender": "성별",
        "interests": "관심사",
        "behavior": "행동 패턴"
    }},
    "marketing_info": {{
        "budget": "예산",
        "channels": "선호 채널",
        "experience": "경험 수준",
        "tools": "사용 도구"
    }},
    "additional": {{
        "pain_points": "고민 사항",
        "preferences": "선호사항",
        "constraints": "제약사항"
    }}
}}

정보가 없는 항목은 null로 설정하세요."""

        try:
            messages = [
                SystemMessage(content="마케팅 정보 추출 전문가입니다. 사용자 입력에서 유용한 정보만 정확히 추출합니다."),
                HumanMessage(content=extraction_prompt)
            ]
            
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            raw_response = llm.invoke(messages)
            response = str(raw_response.content) if hasattr(raw_response, 'content') else str(raw_response)
            
            # JSON 파싱
            if isinstance(response, str):
                cleaned = clean_json_response(response)
                try:
                    extracted_info = json.loads(cleaned)
                    logger.info(f"[단계 로그] - 추출된 정보: {extracted_info}")
                    
                    # 추출된 정보를 상태에 업데이트
                    for category, info_dict in extracted_info.items():
                        if isinstance(info_dict, dict):
                            for key, value in info_dict.items():
                                if value and value != "null":
                                    state.add_information(f"{category}_{key}", value, "user_input")
                                    
                except json.JSONDecodeError:
                    logger.warning(f"JSON 파싱 실패: {cleaned[:100]}")
                    return
            
        except Exception as e:
            logger.error(f"정보 추출 실패: {e}")

    def get_conversation_status(self, conversation_id: int) -> Dict[str, Any]:
        """대화 상태 조회"""
        if conversation_id in self.conversation_states:
            state = self.conversation_states[conversation_id]
            return {
                "conversation_id": conversation_id,
                "current_stage": state.current_stage.value,
                "overall_completion": state.get_overall_completion_rate(),
                "collected_info_count": len(state.collected_info),
                "detected_business_type": state.detected_business_type,
                "is_paused": getattr(state, 'is_paused', False),
                "is_completed": state.current_stage == MarketingStage.COMPLETED,
                "last_updated": state.updated_at.isoformat(),
                "flexible_mode": True
            }
        else:
            return {"error": "대화를 찾을 수 없습니다"}

    def reset_conversation(self, conversation_id: int) -> bool:
        """대화 초기화"""
        if conversation_id in self.conversation_states:
            del self.conversation_states[conversation_id]
            return True
        return False

    def get_agent_status(self) -> Dict[str, Any]:
        """마케팅 에이전트 상태 반환"""
        return {
            "agent_type": "llm_based_flexible_marketing",
            "version": "5.0.0",
            "conversation_system": "llm_powered_flexible",
            "features": [
                "순서 무관 즉시 응답",
                "중간 단계부터 시작", 
                "단계 건너뛰기",
                "LLM 기반 의도 분석",
                "컨텍스트 기반 개인화",
                "마케팅 툴 자동 활용"
            ],
            "active_conversations": len(self.conversation_states),
            "conversation_stages": {
                conv_id: state.current_stage.value 
                for conv_id, state in self.conversation_states.items()
            },
            "llm_status": self.llm_manager.get_status() if hasattr(self.llm_manager, 'get_status') else "active",
            "vector_store_status": self.vector_manager.get_status() if hasattr(self.vector_manager, 'get_status') else "active",
            "flexible_features": {
                "immediate_response": True,
                "stage_jumping": True,
                "flow_control": True,
                "context_awareness": True,
                "marketing_tools": bool(self.analysis_tools)
            },
            "available_tools": {
                "trend_analysis": {
                    "description": "네이버 검색 트렌드 분석",
                    "stage_requirement": "모든 단계"
                },
                "hashtag_analysis": {
                    "description": "인스타그램 해시태그 분석",
                    "stage_requirement": "모든 단계"
                },
                "content_generation": {
                    "description": "블로그/SNS 콘텐츠 생성",
                    "stage_requirement": "4단계(실행 계획)만"
                },
                "keyword_research": {
                    "description": "SEO 키워드 연구",
                    "stage_requirement": "모든 단계"
                }
            },
            "tool_stage_restrictions": {
                "content_generation": "stage_4_execution",
                "reason": "콘텐츠 생성은 마케팅 전략이 및 타겟이 명확해진 후 실행 단계에서 수행되어야 함"
            }
        }


class FlexibleConversationState:
    """유연한 대화 상태 관리 클래스"""
    
    def __init__(self, conversation_id: int, user_id: int):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.current_stage = MarketingStage.ANY_QUESTION
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # 유연한 정보 수집 (단계 구분 없이)
        self.collected_info: Dict[str, Any] = {}
        
        # 대화 히스토리
        self.conversation_history: List[Dict[str, Any]] = []
        
        # 상태 플래그
        self.is_paused = False
        self.detected_business_type = "일반"
        
        # 사용자 선호도
        self.user_preferences = {
            "prefers_structured": False,
            "wants_immediate_answers": True,
            "communication_style": "friendly"
        }
    
    def add_information(self, key: str, value: Any, source: str = "user_input"):
        """정보 추가"""
        self.collected_info[key] = {
            "value": value,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "confidence": 1.0
        }
        self.updated_at = datetime.now()
    
    def get_information(self, key: str) -> Any:
        """정보 조회"""
        info = self.collected_info.get(key)
        return info["value"] if info else None
    
    def get_overall_completion_rate(self) -> float:
        """전체 완료율 계산"""
        # 수집된 정보 기반으로 완료율 계산
        essential_info_count = len([
            info for key, info in self.collected_info.items()
            if any(keyword in key.lower() for keyword in [
                "business_type", "main_goal", "target", "budget", "timeline"
            ])
        ])
        
        return min(essential_info_count / 10.0, 1.0)  # 10개 필수 정보 기준
    
    def get_next_stage(self) -> Optional[MarketingStage]:
        """다음 단계 반환"""
        stage_order = [
            MarketingStage.STAGE_1_GOAL,
            MarketingStage.STAGE_2_TARGET,
            MarketingStage.STAGE_3_STRATEGY,
            MarketingStage.STAGE_4_EXECUTION
        ]
        
        if self.current_stage in stage_order:
            current_index = stage_order.index(self.current_stage)
            if current_index < len(stage_order) - 1:
                return stage_order[current_index + 1]
        
        return None
    
    def reset_conversation(self):
        """대화 초기화"""
        self.current_stage = MarketingStage.ANY_QUESTION
        self.collected_info = {}
        self.conversation_history = []
        self.is_paused = False
        self.updated_at = datetime.now()


# 전역 인스턴스
_enhanced_marketing_manager = None

def get_enhanced_4stage_marketing_manager() -> Enhanced4StageMarketingManager:
    """개선된 4단계 마케팅 매니저 인스턴스 반환"""
    global _enhanced_marketing_manager
    if _enhanced_marketing_manager is None:
        _enhanced_marketing_manager = Enhanced4StageMarketingManager()
    return _enhanced_marketing_manager
