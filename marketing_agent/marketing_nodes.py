"""
LangGraph 기반 마케팅 에이전트 Node 함수들
각 마케팅 단계를 처리하는 개별 Node들
"""

import logging
import json
from typing import Dict, Any, List, Optional
import openai
from datetime import datetime
import asyncio

from marketing_state import MarketingAgentState, MarketingStage, ContentType, StateManager
from config import config

logger = logging.getLogger(__name__)

class MarketingNodes:
    """마케팅 에이전트의 모든 Node 함수를 담은 클래스"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL
        self.temperature = config.TEMPERATURE
        
        # LLM 호출용 시스템 프롬프트들
        self.system_prompts = {
            "initial": """당신은 친근하고 전문적인 마케팅 컨설턴트입니다. 
사용자의 마케팅 상담을 도와주며, 자연스럽게 기본 정보를 수집합니다.
- 업종, 제품/서비스에 대해 자연스럽게 질문
- 친근하고 격려하는 톤 유지
- 구체적이고 실행 가능한 조언 제공""",

            "goal_setting": """마케팅 목표 설정 전문가로서 도움을 제공합니다.
- 명확하고 측정 가능한 목표 설정 유도
- 현실적이고 달성 가능한 범위 제안
- 단기/중기/장기 관점에서 조언""",

            "target_analysis": """타겟 고객 분석 전문가입니다.
- 구체적인 고객 페르소나 개발 도움
- 고객의 니즈와 행동 패턴 분석
- 시장 세분화 관점에서 조언""",

            "strategy_planning": """마케팅 전략 기획 전문가입니다.
- 수집된 정보를 바탕으로 전략 방향 제시
- 예산과 채널에 맞는 최적 전략 추천
- 실행 가능한 구체적 방법론 제안""",

            "content_creation": """마케팅 콘텐츠 제작 전문가입니다.
- 업종과 타겟에 맞는 콘텐츠 제작
- 트렌드를 반영한 창의적 아이디어 제공
- 즉시 활용 가능한 실용적 콘텐츠 생성"""
        }
    
    async def _call_llm(self, system_prompt: str, user_message: str, context: str = "") -> str:
        """OpenAI LLM 호출 (타임아웃 적용)"""
        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.append({"role": "user", "content": f"컨텍스트: {context}"})
        messages.append({"role": "user", "content": user_message})

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=1000
                ),
                timeout=100
            )
            return response.choices[0].message.content.strip()
        except asyncio.TimeoutError:
            logger.error("LLM 호출 타임아웃")
            return "죄송합니다. 응답이 지연되고 있습니다."
        except Exception as e:
            logger.error(f"LLM 호출 실패: {e}")
            return f"죄송합니다. 응답 생성 중 문제가 발생했습니다: {e}"
    
    # Node 함수들
    
    async def initial_consultation(self, state: MarketingAgentState) -> MarketingAgentState:
        logger.info(f"[{state['conversation_id']}] Initial consultation node")
        try:
            user_input = state["user_input"]
            context = StateManager.get_stage_context(state)

            response = await self._call_llm(
                self.system_prompts["initial"],
                f"사용자 입력: {user_input}",
                context
            )

            # 상태 업데이트
            state = StateManager.add_message(state, "user", user_input)
            state = StateManager.add_message(state, "assistant", response)
            state["response"] = response

            if state.get("business_type") and state.get("product"):
                state["next_action"] = "goal_setting"
            else:
                state["next_action"] = "continue_initial"

            return state
        except Exception as e:
            logger.error(f"초기 상담 Node 오류: {e}")
            return StateManager.set_error(state, str(e))
    
    async def goal_setting(self, state: MarketingAgentState) -> MarketingAgentState:
        logger.info(f"[{state['conversation_id']}] Goal setting node")
        try:
            user_input = state["user_input"]
            context = StateManager.get_stage_context(state)

            response = await self._call_llm(
                self.system_prompts["goal_setting"],
                f"사용자 입력: {user_input}",
                context
            )

            state = StateManager.add_message(state, "user", user_input)
            state = StateManager.add_message(state, "assistant", response)
            state["response"] = response

            if state.get("main_goal"):
                state["next_action"] = "target_analysis"
            else:
                state["next_action"] = "continue_goal_setting"

            return state
        except Exception as e:
            logger.error(f"목표 설정 Node 오류: {e}")
            return StateManager.set_error(state, str(e))
    
    async def target_analysis(self, state: MarketingAgentState) -> MarketingAgentState:
        """타겟 분석 Node"""
        logger.info(f"[{state['conversation_id']}] Target analysis node")
        
        try:
            user_input = state["user_input"]
            context = StateManager.get_stage_context(state)
            
            # 타겟 관련 정보 추출
            target_info = self._extract_target_info(user_input)
            if target_info:
                state = StateManager.update_business_info(state, **target_info)
            
            # 응답 생성
            response = self._call_llm(
                self.system_prompts["target_analysis"],
                f"사용자 입력: {user_input}",
                context
            )
            
            # 상태 업데이트
            state = StateManager.add_message(state, "user", user_input)
            state = StateManager.add_message(state, "assistant", response)
            state["response"] = response
            
            # 타겟이 설정되면 다음 단계로
            if state.get("target_audience"):
                state["next_action"] = "strategy_planning"
            else:
                state["next_action"] = "continue_target_analysis"
            
            return state
            
        except Exception as e:
            logger.error(f"타겟 분석 Node 오류: {e}")
            return StateManager.set_error(state, str(e))
    
    async def strategy_planning(self, state: MarketingAgentState) -> MarketingAgentState:
        """전략 기획 Node"""
        logger.info(f"[{state['conversation_id']}] Strategy planning node")
        
        try:
            user_input = state["user_input"]
            context = StateManager.get_stage_context(state)
            
            # 전략 관련 정보 추출
            strategy_info = self._extract_strategy_info(user_input)
            if strategy_info:
                state = StateManager.update_business_info(state, **strategy_info)
            
            # 응답 생성
            response = await self._call_llm(
                self.system_prompts["strategy_planning"],
                f"사용자 입력: {user_input}",
                context
            )
            
            # 상태 업데이트
            state = StateManager.add_message(state, "user", user_input)
            state = StateManager.add_message(state, "assistant", response)
            state["response"] = response
            
            # 컨텐츠 제작 요청 감지
            if self._is_content_creation_request(user_input):
                content_type = self._determine_content_type(user_input)
                state = StateManager.set_content_creation(state, content_type)
                state["next_action"] = "content_creation"
            elif state.get("completion_rate", 0) > 0.6:
                state["next_action"] = "suggest_content_creation"
            else:
                state["next_action"] = "continue_strategy_planning"
            
            return state
            
        except Exception as e:
            logger.error(f"전략 기획 Node 오류: {e}")
            return StateManager.set_error(state, str(e))
    
    async def content_creation(self, state: MarketingAgentState) -> MarketingAgentState:
        """컨텐츠 생성 Node"""
        logger.info(f"[{state['conversation_id']}] Content creation node")
        
        try:
            content_type = state.get("content_type", ContentType.INSTAGRAM_POST)
            context = StateManager.get_stage_context(state)
            
            # 컨텐츠 생성
            generated_content = await self._generate_content(state, content_type)
            
            if generated_content.get("success"):
                # 성공적으로 생성된 경우
                state = StateManager.save_generated_content(state, generated_content)
                
                response = f"✨ {content_type.value} 콘텐츠가 생성되었습니다!\n\n"
                response += self._format_content_display(generated_content)
                response += "\n\n이 콘텐츠가 마음에 드시나요? 수정이 필요하시거나 다른 콘텐츠를 원하시면 말씀해주세요!"
                
                state["next_action"] = "content_feedback"
            else:
                # 생성 실패한 경우
                response = "죄송합니다. 콘텐츠 생성 중 문제가 발생했습니다. 다시 시도해주세요."
                state["next_action"] = "strategy_planning"
            
            # 상태 업데이트
            state = StateManager.add_message(state, "assistant", response)
            state["response"] = response
            
            return state
            
        except Exception as e:
            logger.error(f"컨텐츠 생성 Node 오류: {e}")
            return StateManager.set_error(state, str(e))
    
    async def content_feedback(self, state: MarketingAgentState) -> MarketingAgentState:
        """컨텐츠 피드백 처리 Node"""
        logger.info(f"[{state['conversation_id']}] Content feedback node")
        
        try:
            user_input = state["user_input"]
            
            # 피드백 분석
            feedback_analysis = await self._analyze_content_feedback(user_input)
            
            if feedback_analysis["action"] == "regenerate":
                # 다시 생성
                state["next_action"] = "content_creation"
                response = "새로운 콘텐츠를 생성하겠습니다!"
                
            elif feedback_analysis["action"] == "modify":
                # 수정 요청
                state["next_action"] = "content_creation"
                response = "피드백을 반영해서 수정하겠습니다!"
                
            elif feedback_analysis["action"] == "approve":
                # 승인
                state["next_action"] = "execution"
                response = "훌륭합니다! 이제 실제 마케팅 실행 방법을 안내해드리겠습니다."
                
            else:
                # 추가 피드백 요청
                response = "더 구체적인 피드백을 주시면 더 나은 콘텐츠로 수정해드릴 수 있습니다!"
                state["next_action"] = "content_feedback"
            
            # 상태 업데이트
            state = StateManager.add_message(state, "user", user_input)
            state = StateManager.add_message(state, "assistant", response)
            state["response"] = response
            
            return state
            
        except Exception as e:
            logger.error(f"컨텐츠 피드백 Node 오류: {e}")
            return StateManager.set_error(state, str(e))
    
    async def execution_guidance(self, state: MarketingAgentState) -> MarketingAgentState:
        """실행 가이드 Node"""
        logger.info(f"[{state['conversation_id']}] Execution guidance node")
        
        try:
            context = StateManager.get_stage_context(state)
            
            # 실행 가이드 생성
            execution_guide = self._generate_execution_guide(state)
            
            response = f"🚀 마케팅 실행 가이드\n\n{execution_guide}\n\n"
            response += "추가 질문이나 도움이 필요하시면 언제든 말씀해주세요!"
            
            # 상태 업데이트
            state = StateManager.add_message(state, "assistant", response)
            state["response"] = response
            state["current_stage"] = MarketingStage.COMPLETED
            state["should_end"] = True
            
            return state
            
        except Exception as e:
            logger.error(f"실행 가이드 Node 오류: {e}")
            return StateManager.set_error(state, str(e))
    
    async def error_handler(self, state: MarketingAgentState) -> MarketingAgentState:
        """에러 처리 Node"""
        logger.info(f"[{state['conversation_id']}] Error handler node")
        
        error_message = state.get("error", "알 수 없는 오류")
        retry_count = state.get("retry_count", 0)
        
        if retry_count < 3:
            response = "죄송합니다. 잠시 문제가 발생했네요. 다시 한 번 말씀해주시면 도움을 드리겠습니다!"
            state["next_action"] = "initial_consultation"
        else:
            response = "죄송합니다. 계속 문제가 발생하고 있습니다. 나중에 다시 시도해주시거나 관리자에게 문의해주세요."
            state["should_end"] = True
        
        # 상태 업데이트
        state = StateManager.add_message(state, "assistant", response)
        state["response"] = response
        state = StateManager.clear_error(state)
        
        return state
    
    # 헬퍼 메서드들
    
    def _extract_business_info(self, user_input: str) -> Dict[str, Any]:
        """사용자 입력에서 비즈니스 정보 추출"""
        try:
            prompt = f"""다음 사용자 입력에서 비즈니스 정보를 추출해주세요:
            
입력: "{user_input}"

다음 JSON 형식으로만 응답해주세요:
{{
    "business_type": "추출된 업종 (없으면 null)",
    "product": "제품/서비스 (없으면 null)"
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            
            # JSON 파싱 시도
            import json
            if "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_content = content[json_start:json_end]
                result = json.loads(json_content)
                
                # null 값 제거
                return {k: v for k, v in result.items() if v and v != "null"}
            
            return {}
            
        except Exception as e:
            logger.warning(f"비즈니스 정보 추출 실패: {e}")
            return {}
    
    def _extract_goal_info(self, user_input: str) -> Dict[str, Any]:
        """목표 정보 추출"""
        try:
            prompt = f"""다음 사용자 입력에서 마케팅 목표 정보를 추출해주세요:
            
입력: "{user_input}"

다음 JSON 형식으로만 응답해주세요:
{{
    "main_goal": "주요 목표 (브랜드 인지도, 매출 증대, 고객 확보 등)",
    "target_metrics": "목표 지표 (조회수, 전환율, 매출액 등)",
    "timeline": "목표 기간 (1개월, 3개월, 6개월 등)"
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            
            # JSON 파싱 시도
            import json
            if "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_content = content[json_start:json_end]
                result = json.loads(json_content)
                
                # null 값 제거
                return {k: v for k, v in result.items() if v and v != "null"}
            
            return {}
            
        except Exception as e:
            logger.warning(f"목표 정보 추출 실패: {e}")
            return {}
    
    def _extract_target_info(self, user_input: str) -> Dict[str, Any]:
        """타겟 정보 추출"""
        try:
            prompt = f"""다음 사용자 입력에서 타겟 고객 정보를 추출해주세요:
            
입력: "{user_input}"

다음 JSON 형식으로만 응답해주세요:
{{
    "target_audience": "타겟 고객층 (20-30대 여성, 직장인, 학생 등)",
    "demographics": "인구통계학적 특성",
    "interests": "관심사 및 취향",
    "pain_points": "고객의 문제점이나 니즈"
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            
            # JSON 파싱 시도
            import json
            if "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_content = content[json_start:json_end]
                result = json.loads(json_content)
                
                # null 값 제거
                return {k: v for k, v in result.items() if v and v != "null"}
            
            return {}
            
        except Exception as e:
            logger.warning(f"타겟 정보 추출 실패: {e}")
            return {}
    
    def _extract_strategy_info(self, user_input: str) -> Dict[str, Any]:
        """전략 정보 추출"""
        try:
            prompt = f"""다음 사용자 입력에서 마케팅 전략 정보를 추출해주세요:
            
입력: "{user_input}"

다음 JSON 형식으로만 응답해주세요:
{{
    "channels": "마케팅 채널 (SNS, 블로그, 이메일 등)",
    "budget": "예산 정보",
    "approach": "접근 방식 (바이럴, 인플루언서, 콘텐츠 마케팅 등)",
    "content_type": "콘텐츠 유형 (영상, 이미지, 텍스트 등)"
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            
            # JSON 파싱 시도
            import json
            if "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_content = content[json_start:json_end]
                result = json.loads(json_content)
                
                # null 값 제거
                return {k: v for k, v in result.items() if v and v != "null"}
            
            return {}
            
        except Exception as e:
            logger.warning(f"전략 정보 추출 실패: {e}")
            return {}

    def _is_content_creation_request(self, user_input: str) -> bool:
        """컨텐츠 생성 요청인지 확인"""
        content_keywords = ["포스트", "콘텐츠", "글", "캠페인", "전략서", "만들어", "생성", "작성"]
        return any(keyword in user_input for keyword in content_keywords)
    
    def _determine_content_type(self, user_input: str) -> ContentType:
        """요청된 컨텐츠 타입 결정"""
        if "인스타" in user_input or "instagram" in user_input.lower():
            return ContentType.INSTAGRAM_POST
        elif "블로그" in user_input or "blog" in user_input.lower():
            return ContentType.BLOG_POST
        elif "전략" in user_input or "strategy" in user_input.lower():
            return ContentType.MARKETING_STRATEGY
        elif "캠페인" in user_input or "campaign" in user_input.lower():
            return ContentType.CAMPAIGN_PLAN
        else:
            return ContentType.INSTAGRAM_POST
    
    def _generate_content(self, state: MarketingAgentState, content_type: ContentType) -> Dict[str, Any]:
        """실제 컨텐츠 생성"""
        try:
            context = {
                "business_type": state.get("business_type"),
                "product": state.get("product"),
                "target_audience": state.get("target_audience"),
                "main_goal": state.get("main_goal")
            }
            
            if content_type == ContentType.INSTAGRAM_POST:
                return self._generate_instagram_post(context)
            elif content_type == ContentType.BLOG_POST:
                return self._generate_blog_post(context)
            elif content_type == ContentType.MARKETING_STRATEGY:
                return self._generate_marketing_strategy(context)
            elif content_type == ContentType.CAMPAIGN_PLAN:
                return self._generate_campaign_plan(context)
            
            return {"success": False, "error": "지원하지 않는 컨텐츠 타입"}
            
        except Exception as e:
            logger.error(f"컨텐츠 생성 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_instagram_post(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """인스타그램 포스트 생성"""
        prompt = f"""다음 정보를 바탕으로 인스타그램 포스트를 생성해주세요:

업종: {context.get('business_type', '미정')}
제품/서비스: {context.get('product', '미정')}
타겟 고객: {context.get('target_audience', '일반 고객')}
마케팅 목표: {context.get('main_goal', '브랜드 인지도 향상')}

다음 형식으로 생성해주세요:
캡션: [매력적인 캡션]
해시태그: [관련 해시태그 20개]
CTA: [행동 유도 문구]"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            
            return {
                "success": True,
                "type": "instagram_post",
                "content": content,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_blog_post(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """블로그 포스트 생성"""
        prompt = f"""다음 정보를 바탕으로 블로그 포스트를 생성해주세요:

업종: {context.get('business_type', '미정')}
제품/서비스: {context.get('product', '미정')}
타겟 고객: {context.get('target_audience', '일반 고객')}
마케팅 목표: {context.get('main_goal', '브랜드 인지도 향상')}

다음 형식으로 생성해주세요:
제목: [SEO 최적화된 제목]
서론: [독자의 관심을 끄는 도입부]
본론: [핵심 내용 3-4개 섹션]
결론: [요약 및 행동 유도]
SEO 키워드: [관련 키워드 10개]"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            
            return {
                "success": True,
                "type": "blog_post",
                "content": content,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_marketing_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """마케팅 전략 생성"""
        prompt = f"""다음 정보를 바탕으로 종합적인 마케팅 전략을 생성해주세요:

업종: {context.get('business_type', '미정')}
제품/서비스: {context.get('product', '미정')}
타겟 고객: {context.get('target_audience', '일반 고객')}
마케팅 목표: {context.get('main_goal', '브랜드 인지도 향상')}

다음 형식으로 생성해주세요:
1. 현황 분석
   - 시장 분석
   - 경쟁사 분석
   - SWOT 분석

2. 타겟 고객 분석
   - 페르소나 정의
   - 고객 여정 맵

3. 마케팅 전략
   - 포지셔닝 전략
   - 채널 전략
   - 콘텐츠 전략

4. 실행 계획
   - 단계별 실행 방안
   - 예산 배분
   - 성과 지표

5. 위험 요소 및 대응 방안"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            return {
                "success": True,
                "type": "marketing_strategy",
                "content": content,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_campaign_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """캠페인 계획 생성"""
        prompt = f"""다음 정보를 바탕으로 마케팅 캠페인 계획을 생성해주세요:

업종: {context.get('business_type', '미정')}
제품/서비스: {context.get('product', '미정')}
타겟 고객: {context.get('target_audience', '일반 고객')}
마케팅 목표: {context.get('main_goal', '브랜드 인지도 향상')}

다음 형식으로 생성해주세요:
캠페인명: [창의적인 캠페인 이름]

1. 캠페인 개요
   - 목표
   - 기간
   - 예산

2. 타겟 설정
   - 주요 타겟
   - 세부 타겟

3. 핵심 메시지
   - 메인 메시지
   - 서브 메시지

4. 채널별 전략
   - SNS (인스타그램, 페이스북 등)
   - 온라인 광고
   - 오프라인 활동

5. 콘텐츠 계획
   - 콘텐츠 유형
   - 제작 일정
   - 배포 계획

6. 성과 측정
   - KPI 설정
   - 측정 방법
   - 보고 주기"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=1800
            )
            
            content = response.choices[0].message.content
            
            return {
                "success": True,
                "type": "campaign_plan",
                "content": content,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _format_content_display(self, content: Dict[str, Any]) -> str:
        """생성된 컨텐츠를 보기 좋게 포맷팅"""
        if content.get("type") == "instagram_post":
            return f"📱 Instagram Post\n\n{content.get('content', '')}"
        else:
            return content.get('content', '')
    
    def _analyze_content_feedback(self, feedback: str) -> Dict[str, str]:
        """컨텐츠 피드백 분석"""
        feedback_lower = feedback.lower()
        
        if any(word in feedback_lower for word in ["좋아", "마음에", "훌륭", "완벽", "좋네요"]):
            return {"action": "approve"}
        elif any(word in feedback_lower for word in ["다시", "새로", "다른", "바꿔"]):
            return {"action": "regenerate"}
        elif any(word in feedback_lower for word in ["수정", "고쳐", "바꿔"]):
            return {"action": "modify"}
        else:
            return {"action": "clarify"}
    
    def _generate_execution_guide(self, state: MarketingAgentState) -> str:
        """실행 가이드 생성"""
        business_type = state.get("business_type", "일반")
        generated_content = state.get("generated_content", {})
        
        guide = f"""
🎯 {business_type} 마케팅 실행 가이드

1. 📅 포스팅 계획
   - 최적 시간: 평일 오후 7-9시, 주말 오후 2-4시
   - 주기: 주 2-3회 정기 포스팅

2. 📊 성과 측정
   - 조회수, 좋아요, 댓글 수 모니터링
   - 월 1회 성과 분석 및 전략 조정

3. 💡 추가 팁
   - 고객과의 적극적인 소통
   - 트렌드에 맞는 콘텐츠 업데이트
   - 정기적인 콘텐츠 기획 회의
"""
        
        return guide.strip()

# 전역 인스턴스
marketing_nodes = MarketingNodes()
