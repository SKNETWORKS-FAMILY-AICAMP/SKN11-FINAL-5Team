"""
균형잡힌 LangGraph 기반 마케팅 에이전트 Node 함수들
자연스러운 대화 흐름 + 스마트한 무한 루프 방지
"""

import logging
import json
from typing import Dict, Any, List, Optional
import openai
from datetime import datetime
import asyncio
import re

from marketing_state import MarketingAgentState, MarketingStage, ContentType, StateManager
from config import config

logger = logging.getLogger(__name__)

class BalancedMarketingNodes:
    """균형잡힌 마케팅 에이전트 Node 클래스"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL
        self.temperature = config.TEMPERATURE
        self.max_tokens = 1000  # 좀 더 여유롭게
        
        # 개선된 LLM 프롬프트 (더 단순하고 신뢰성 있게)
        self.system_prompts = {
            "initial": """당신은 친근한 마케팅 컨설턴트입니다. 
사용자와 자연스럽게 대화하며 업종과 제품 정보를 수집하세요.

중요: 충분한 정보가 수집되면 자연스럽게 다음 단계로 유도하세요.
- 업종과 제품 정보가 모두 파악되면 목표 설정으로 이동
- 불충분하면 자연스럽게 더 질문하세요

응답 끝에 반드시 다음 중 하나를 포함하세요:
- [READY_TO_PROCEED] - 다음 단계 준비됨
- [NEED_MORE_INFO] - 더 많은 정보 필요""",

            "goal_setting": """마케팅 목표 설정을 도와주는 전문가입니다.
사용자의 마케팅 목표를 명확히 파악하세요.

응답 끝에 반드시 다음 중 하나를 포함하세요:
- [GOAL_CLEAR] - 목표가 명확히 설정됨
- [NEED_CLARIFICATION] - 목표에 대한 더 자세한 정보 필요""",

            "target_analysis": """타겟 고객 분석 전문가입니다.
구체적인 타겟 고객층을 파악하세요.

응답 끝에 반드시 다음 중 하나를 포함하세요:
- [TARGET_IDENTIFIED] - 타겟이 명확히 식별됨
- [NEED_TARGET_INFO] - 타겟에 대한 더 자세한 정보 필요""",

            "strategy_planning": """마케팅 전략 수립 전문가입니다.
수집된 정보를 바탕으로 전략을 제안하고 사용자의 요청을 파악하세요.

응답 끝에 반드시 다음 중 하나를 포함하세요:
- [CONTENT_REQUESTED] - 콘텐츠 생성 요청됨
- [STRATEGY_COMPLETE] - 전략 완료, 실행 단계로
- [CONTINUE_PLANNING] - 전략 논의 계속""",

            "content_creation": """마케팅 콘텐츠 제작 전문가입니다.
업종과 타겟에 맞는 실용적인 콘텐츠를 생성하세요."""
        }
    
    async def _call_llm_simple(self, system_prompt: str, user_message: str, context: str = "") -> str:
        """단순하고 신뢰성 있는 LLM 호출"""
        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.append({"role": "user", "content": f"현재 상황: {context}"})
        messages.append({"role": "user", "content": user_message})

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                ),
                timeout=25  # 좀 더 여유롭게
            )
            return response.choices[0].message.content.strip()
        except asyncio.TimeoutError:
            logger.error("LLM 호출 타임아웃")
            return "죄송합니다. 잠시 처리가 지연되고 있습니다. 다시 말씀해주세요."
        except Exception as e:
            logger.error(f"LLM 호출 실패: {e}")
            return "죄송합니다. 응답 생성 중 문제가 발생했습니다."
    
    def _extract_action_signal(self, response: str) -> str:
        """응답에서 액션 신호 추출"""
        if "[READY_TO_PROCEED]" in response:
            return "next_stage"
        elif "[GOAL_CLEAR]" in response:
            return "next_stage"
        elif "[TARGET_IDENTIFIED]" in response:
            return "next_stage"
        elif "[CONTENT_REQUESTED]" in response:
            return "content_creation"
        elif "[STRATEGY_COMPLETE]" in response:
            return "execution"
        else:
            return "continue"
    
    def _extract_basic_info(self, response: str, user_input: str) -> Dict[str, Any]:
        """기본적인 정보 추출 (키워드 기반)"""
        info = {}
        text = f"{response} {user_input}".lower()
        
        # 업종 추출
        if any(word in text for word in ['카페', '커피', '음료']):
            info['business_type'] = '카페/음료'
        elif any(word in text for word in ['쇼핑몰', '이커머스', '온라인']):
            info['business_type'] = '온라인 쇼핑몰'
        elif any(word in text for word in ['뷰티', '화장품', '미용']):
            info['business_type'] = '뷰티/화장품'
        elif any(word in text for word in ['식당', '레스토랑', '음식']):
            info['business_type'] = '음식점'
        elif any(word in text for word in ['헬스', '운동', '피트니스']):
            info['business_type'] = '헬스/피트니스'
        
        # 목표 추출
        if any(word in text for word in ['매출', '수익', '판매']):
            info['main_goal'] = '매출 증대'
        elif any(word in text for word in ['인지도', '브랜드', '알려']):
            info['main_goal'] = '브랜드 인지도 향상'
        elif any(word in text for word in ['고객', '손님', '방문']):
            info['main_goal'] = '신규 고객 확보'
        
        # 타겟 추출
        if any(word in text for word in ['20대', '청년']):
            info['target_audience'] = '20대'
        elif any(word in text for word in ['30대', '직장인']):
            info['target_audience'] = '30대 직장인'
        elif any(word in text for word in ['여성', '여자']):
            current = info.get('target_audience', '')
            info['target_audience'] = f"{current} 여성".strip()
        
        return info
    
    def _check_information_completeness(self, state: MarketingAgentState, stage: MarketingStage) -> float:
        """정보 완성도 체크 (0.0 ~ 1.0)"""
        if stage == MarketingStage.INITIAL:
            # 업종과 제품 정보가 있는지 확인
            business = bool(state.get("business_type"))
            product_mentioned = bool(state.get("product")) or len(state.get("messages", [])) >= 2
            return 0.8 if (business and product_mentioned) else 0.3
            
        elif stage == MarketingStage.GOAL_SETTING:
            # 목표가 설정되었는지 확인
            return 0.9 if state.get("main_goal") else 0.4
            
        elif stage == MarketingStage.TARGET_ANALYSIS:
            # 타겟이 설정되었는지 확인
            return 0.9 if state.get("target_audience") else 0.4
            
        return 0.5
    
    # Node 함수들 (더 균형잡힌 로직)
    
    async def initial(self, state: MarketingAgentState) -> MarketingAgentState:
        """균형잡힌 초기 상담 Node"""
        logger.info(f"[{state['conversation_id']}] Initial consultation node - balanced")
        
        try:
            user_input = state["user_input"]
            context = StateManager.get_stage_context(state)
            iteration_count = state.get("iteration_count", 0) + 1
            
            # 스마트한 강제 진행 조건 (정보 완성도 + 반복 횟수)
            completeness = self._check_information_completeness(state, MarketingStage.INITIAL)
            
            if iteration_count >= 6 or (iteration_count >= 3 and completeness >= 0.7):
                logger.info(f"초기 상담 자연스럽게 진행: 완성도={completeness:.2f}, 반복={iteration_count}")
                state = StateManager.add_message(state, "user", user_input)
                state = StateManager.add_message(state, "assistant", 
                    "좋습니다! 기본 정보를 바탕으로 마케팅 목표를 설정해봅시다.")
                state["response"] = "좋습니다! 기본 정보를 바탕으로 마케팅 목표를 설정해봅시다."
                state["current_stage"] = MarketingStage.GOAL_SETTING
                state["next_action"] = "goal_setting"
                state["iteration_count"] = 0
                return state
            
            # LLM 호출
            response = await self._call_llm_simple(
                self.system_prompts["initial"],
                f"사용자: {user_input}",
                context
            )
            
            # 액션 신호 추출
            action_signal = self._extract_action_signal(response)
            
            # 정보 추출
            extracted_info = self._extract_basic_info(response, user_input)
            
            # 응답에서 신호 제거
            clean_response = re.sub(r'\[.*?\]', '', response).strip()
            
            # 상태 업데이트
            state = StateManager.add_message(state, "user", user_input)
            state = StateManager.add_message(state, "assistant", clean_response)
            state = StateManager.update_business_info(state, **extracted_info)
            state["response"] = clean_response
            state["iteration_count"] = iteration_count
            
            # 다음 액션 결정 (더 스마트하게)
            completeness_after = self._check_information_completeness(state, MarketingStage.INITIAL)
            
            if action_signal == "next_stage" or completeness_after >= 0.8:
                state["next_action"] = "goal_setting"
                state["current_stage"] = MarketingStage.GOAL_SETTING
                state["iteration_count"] = 0
            else:
                state["next_action"] = "continue_initial"
            
            return state
            
        except Exception as e:
            logger.error(f"초기 상담 Node 오류: {e}")
            return StateManager.set_error(state, str(e))
    
    async def goal_setting(self, state: MarketingAgentState) -> MarketingAgentState:
        """균형잡힌 목표 설정 Node"""
        logger.info(f"[{state['conversation_id']}] Goal setting node - balanced")
        
        try:
            user_input = state["user_input"]
            context = StateManager.get_stage_context(state)
            iteration_count = state.get("iteration_count", 0) + 1
            
            # 스마트한 진행 조건
            completeness = self._check_information_completeness(state, MarketingStage.GOAL_SETTING)
            
            if iteration_count >= 5 or (iteration_count >= 3 and completeness >= 0.7):
                logger.info(f"목표 설정 자연스럽게 진행: 완성도={completeness:.2f}, 반복={iteration_count}")
                state = StateManager.add_message(state, "user", user_input)
                state = StateManager.add_message(state, "assistant", 
                    "목표를 바탕으로 타겟 고객을 분석해보겠습니다!")
                state["response"] = "목표를 바탕으로 타겟 고객을 분석해보겠습니다!"
                state["current_stage"] = MarketingStage.TARGET_ANALYSIS
                state["next_action"] = "target_analysis"
                state["iteration_count"] = 0
                return state
            
            # LLM 호출
            response = await self._call_llm_simple(
                self.system_prompts["goal_setting"],
                f"사용자: {user_input}",
                context
            )
            
            # 액션 신호 추출
            action_signal = self._extract_action_signal(response)
            
            # 정보 추출
            extracted_info = self._extract_basic_info(response, user_input)
            
            # 응답 정리
            clean_response = re.sub(r'\[.*?\]', '', response).strip()
            
            # 상태 업데이트
            state = StateManager.add_message(state, "user", user_input)
            state = StateManager.add_message(state, "assistant", clean_response)
            state = StateManager.update_business_info(state, **extracted_info)
            state["response"] = clean_response
            state["iteration_count"] = iteration_count
            
            # 다음 액션 결정
            completeness_after = self._check_information_completeness(state, MarketingStage.GOAL_SETTING)
            
            if action_signal == "next_stage" or completeness_after >= 0.8:
                state["next_action"] = "target_analysis"
                state["current_stage"] = MarketingStage.TARGET_ANALYSIS
                state["iteration_count"] = 0
            else:
                state["next_action"] = "continue_goal_setting"
            
            return state
            
        except Exception as e:
            logger.error(f"목표 설정 Node 오류: {e}")
            return StateManager.set_error(state, str(e))
    
    async def target_analysis(self, state: MarketingAgentState) -> MarketingAgentState:
        """균형잡힌 타겟 분석 Node"""
        logger.info(f"[{state['conversation_id']}] Target analysis node - balanced")
        
        try:
            user_input = state["user_input"]
            context = StateManager.get_stage_context(state)
            iteration_count = state.get("iteration_count", 0) + 1
            
            # 스마트한 진행 조건
            completeness = self._check_information_completeness(state, MarketingStage.TARGET_ANALYSIS)
            
            if iteration_count >= 5 or (iteration_count >= 3 and completeness >= 0.7):
                logger.info(f"타겟 분석 자연스럽게 진행: 완성도={completeness:.2f}, 반복={iteration_count}")
                state = StateManager.add_message(state, "user", user_input)
                state = StateManager.add_message(state, "assistant", 
                    "타겟 정보를 바탕으로 마케팅 전략을 수립해보겠습니다!")
                state["response"] = "타겟 정보를 바탕으로 마케팅 전략을 수립해보겠습니다!"
                state["current_stage"] = MarketingStage.STRATEGY_PLANNING
                state["next_action"] = "strategy_planning"
                state["iteration_count"] = 0
                return state
            
            # LLM 호출
            response = await self._call_llm_simple(
                self.system_prompts["target_analysis"],
                f"사용자: {user_input}",
                context
            )
            
            # 액션 신호 추출
            action_signal = self._extract_action_signal(response)
            
            # 정보 추출
            extracted_info = self._extract_basic_info(response, user_input)
            
            # 응답 정리
            clean_response = re.sub(r'\[.*?\]', '', response).strip()
            
            # 상태 업데이트
            state = StateManager.add_message(state, "user", user_input)
            state = StateManager.add_message(state, "assistant", clean_response)
            state = StateManager.update_business_info(state, **extracted_info)
            state["response"] = clean_response
            state["iteration_count"] = iteration_count
            
            # 다음 액션 결정
            completeness_after = self._check_information_completeness(state, MarketingStage.TARGET_ANALYSIS)
            
            if action_signal == "next_stage" or completeness_after >= 0.8:
                state["next_action"] = "strategy_planning"
                state["current_stage"] = MarketingStage.STRATEGY_PLANNING
                state["iteration_count"] = 0
            else:
                state["next_action"] = "continue_target_analysis"
            
            return state
            
        except Exception as e:
            logger.error(f"타겟 분석 Node 오류: {e}")
            return StateManager.set_error(state, str(e))
    
    async def strategy_planning(self, state: MarketingAgentState) -> MarketingAgentState:
        """균형잡힌 전략 기획 Node"""
        logger.info(f"[{state['conversation_id']}] Strategy planning node - balanced")
        
        try:
            user_input = state["user_input"]
            context = StateManager.get_stage_context(state)
            iteration_count = state.get("iteration_count", 0) + 1
            
            # LLM 호출
            response = await self._call_llm_simple(
                self.system_prompts["strategy_planning"],
                f"사용자: {user_input}",
                context
            )
            
            # 액션 신호 추출
            action_signal = self._extract_action_signal(response)
            
            # 응답 정리
            clean_response = re.sub(r'\[.*?\]', '', response).strip()
            
            # 상태 업데이트
            state = StateManager.add_message(state, "user", user_input)
            state = StateManager.add_message(state, "assistant", clean_response)
            state["response"] = clean_response
            state["iteration_count"] = iteration_count
            
            # 콘텐츠 생성 요청 감지
            content_keywords = ["만들어", "포스트", "글", "콘텐츠", "작성", "생성", "블로그", "인스타"]
            
            if (action_signal == "content_creation" or 
                any(keyword in user_input for keyword in content_keywords)):
                # 콘텐츠 생성 요청
                content_type = self._determine_content_type(user_input)
                state = StateManager.set_content_creation(state, content_type)
                state["next_action"] = "content_creation"
            elif (action_signal == "execution" or 
                  iteration_count >= 6):  # 더 관대한 제한
                # 실행 가이드로 이동
                state["next_action"] = "execution"
                state["current_stage"] = MarketingStage.EXECUTION
                state["iteration_count"] = 0
            else:
                # 전략 논의 계속
                state["next_action"] = "continue_strategy_planning"
            
            return state
            
        except Exception as e:
            logger.error(f"전략 기획 Node 오류: {e}")
            return StateManager.set_error(state, str(e))
    
    # 나머지 노드들은 기존과 동일하되 더 관대한 조건 적용
    
    async def content_creation(self, state: MarketingAgentState) -> MarketingAgentState:
        """콘텐츠 생성 Node"""
        logger.info(f"[{state['conversation_id']}] Content creation node")
        
        try:
            content_type = state.get("content_type", ContentType.INSTAGRAM_POST)
            
            # 빠른 콘텐츠 생성
            generated_content = await self._generate_content_fast(state, content_type)
            
            if generated_content.get("success"):
                state = StateManager.save_generated_content(state, generated_content)
                
                response = f"✨ {content_type.value} 콘텐츠를 생성했습니다!\n\n"
                response += self._format_content_display(generated_content)
                response += "\n\n만족하시나요? 수정이 필요하면 말씀해주세요!"
                
                state["next_action"] = "content_feedback"
                state["current_stage"] = MarketingStage.CONTENT_CREATION
            else:
                response = "콘텐츠 생성에 실패했습니다. 전략을 다시 논의해봅시다."
                state["next_action"] = "strategy_planning"
            
            state = StateManager.add_message(state, "assistant", response)
            state["response"] = response
            
            return state
            
        except Exception as e:
            logger.error(f"콘텐츠 생성 Node 오류: {e}")
            return StateManager.set_error(state, str(e))
    
    async def content_feedback(self, state: MarketingAgentState) -> MarketingAgentState:
        """콘텐츠 피드백 Node - 더 관대한 조건"""
        logger.info(f"[{state['conversation_id']}] Content feedback node")
        
        try:
            user_input = state["user_input"]
            feedback_count = state.get("feedback_count", 0) + 1
            
            # 더 관대한 피드백 제한 (5회)
            if feedback_count >= 5:
                state["next_action"] = "execution"
                state["current_stage"] = MarketingStage.EXECUTION
                response = "충분한 피드백을 받았습니다. 이제 실행 방법을 안내해드리겠습니다!"
            elif "좋아" in user_input or "완성" in user_input or "ok" in user_input.lower():
                state["next_action"] = "execution"
                state["current_stage"] = MarketingStage.EXECUTION
                response = "훌륭합니다! 이제 실제 마케팅 실행 방법을 안내해드리겠습니다."
            else:
                state["next_action"] = "content_creation"
                state["feedback_count"] = feedback_count
                response = "피드백을 반영해서 새로운 콘텐츠를 생성하겠습니다!"
            
            state = StateManager.add_message(state, "user", user_input)
            state = StateManager.add_message(state, "assistant", response)
            state["response"] = response
            
            return state
            
        except Exception as e:
            logger.error(f"콘텐츠 피드백 Node 오류: {e}")
            return StateManager.set_error(state, str(e))
    
    async def execution_guidance(self, state: MarketingAgentState) -> MarketingAgentState:
        """실행 가이드 Node"""
        logger.info(f"[{state['conversation_id']}] Execution guidance node")
        
        try:
            guide = self._generate_quick_execution_guide(state)
            
            response = f"🚀 마케팅 실행 가이드\n\n{guide}\n\n추가 질문이 있으시면 언제든 말씀해주세요!"
            
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
        
        if retry_count < 3:  # 더 관대한 재시도
            response = "죄송합니다. 일시적인 문제가 발생했습니다. 간단하게 다시 말씀해주시겠어요?"
            state["next_action"] = "initial"
            state["current_stage"] = MarketingStage.INITIAL
        else:
            response = "죄송합니다. 계속 문제가 발생하고 있습니다. 나중에 다시 시도해주세요."
            state["should_end"] = True
        
        state = StateManager.add_message(state, "assistant", response)
        state["response"] = response
        state = StateManager.clear_error(state)
        
        return state
    
    # 헬퍼 메서드들
    
    def _determine_content_type(self, user_input: str) -> ContentType:
        """컨텐츠 타입 결정"""
        if "인스타" in user_input:
            return ContentType.INSTAGRAM_POST
        elif "블로그" in user_input:
            return ContentType.BLOG_POST
        elif "전략" in user_input:
            return ContentType.MARKETING_STRATEGY
        else:
            return ContentType.INSTAGRAM_POST
    
    async def _generate_content_fast(self, state: MarketingAgentState, content_type: ContentType) -> Dict[str, Any]:
        """빠른 콘텐츠 생성"""
        try:
            context = {
                "business_type": state.get("business_type", "일반"),
                "product": state.get("product", "제품"),
                "target_audience": state.get("target_audience", "고객"),
                "main_goal": state.get("main_goal", "홍보")
            }
            
            prompt = f"""다음 정보로 {content_type.value}을 만들어주세요:
업종: {context['business_type']}
제품: {context['product']}
타겟: {context['target_audience']}
목표: {context['main_goal']}

실용적이고 즉시 사용 가능한 콘텐츠로 작성해주세요."""
            
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=800
                ),
                timeout=20
            )
            
            return {
                "success": True,
                "type": content_type.value,
                "content": response.choices[0].message.content.strip(),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _format_content_display(self, content: Dict[str, Any]) -> str:
        """컨텐츠 표시 포맷"""
        return f"📱 {content.get('type', 'content')}\n\n{content.get('content', '')}"
    
    def _generate_quick_execution_guide(self, state: MarketingAgentState) -> str:
        """실행 가이드 생성"""
        business_type = state.get("business_type", "일반")
        
        return f"""
📍 {business_type} 마케팅 실행 체크리스트

1. 📅 포스팅 계획
   - 최적 시간: 평일 19-21시, 주말 14-16시
   - 주기: 주 2-3회

2. 📊 성과 측정
   - 좋아요, 댓글, 조회수 모니터링
   - 월 1회 분석

3. 💡 핵심 팁
   - 고객과 적극 소통
   - 트렌드 반영
   - 꾸준한 업데이트

더 자세한 전략이 필요하시면 말씀해주세요!
"""

# 균형잡힌 전역 인스턴스
improved_marketing_nodes = BalancedMarketingNodes()
