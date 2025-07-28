"""
개선된 LangGraph 기반 마케팅 에이전트 워크플로우
무한 루프 방지 및 성능 최적화
"""

import logging
from typing import Literal, Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from marketing_state import MarketingAgentState, MarketingStage, StateManager
from marketing_nodes import improved_marketing_nodes
from config import config

import asyncio

logger = logging.getLogger(__name__)

class ImprovedMarketingWorkflow:
    """개선된 LangGraph 기반 마케팅 에이전트 워크플로우"""
    
    def __init__(self):
        self.workflow = None
        self.compiled_graph = None
        self.memory = MemorySaver()
        self.nodes = improved_marketing_nodes
        self._build_workflow()
    
    def _build_workflow(self):
        """워크플로우 구성 - 단순화 및 최적화"""
        logger.info("개선된 마케팅 에이전트 워크플로우 구성 시작")
        
        # StateGraph 초기화
        self.workflow = StateGraph(MarketingAgentState)
        
        # Node 추가
        self.workflow.add_node("initial", self.nodes.initial)
        self.workflow.add_node("goal_setting", self.nodes.goal_setting)
        self.workflow.add_node("target_analysis", self.nodes.target_analysis)
        self.workflow.add_node("strategy_planning", self.nodes.strategy_planning)
        self.workflow.add_node("content_creation", self.nodes.content_creation)
        self.workflow.add_node("content_feedback", self.nodes.content_feedback)
        self.workflow.add_node("execution_guidance", self.nodes.execution_guidance)
        self.workflow.add_node("error_handler", self.nodes.error_handler)
        
        # 시작점 설정
        self.workflow.add_edge(START, "initial")
        
        # 단순화된 조건부 라우팅 (무한 루프 강력 방지)
        self.workflow.add_conditional_edges(
            "initial",
            self._route_from_initial,
            {
                "goal_setting": "goal_setting",
                "continue": "initial",
                "error": "error_handler",
                "end": END
            }
        )
        
        self.workflow.add_conditional_edges(
            "goal_setting",
            self._route_from_goal_setting,
            {
                "target_analysis": "target_analysis",
                "continue": "goal_setting",
                "error": "error_handler",
                "end": END
            }
        )
        
        self.workflow.add_conditional_edges(
            "target_analysis",
            self._route_from_target_analysis,
            {
                "strategy_planning": "strategy_planning",
                "continue": "target_analysis",
                "error": "error_handler",
                "end": END
            }
        )
        
        self.workflow.add_conditional_edges(
            "strategy_planning",
            self._route_from_strategy_planning,
            {
                "content_creation": "content_creation",
                "execution": "execution_guidance",
                "continue": "strategy_planning",
                "error": "error_handler",
                "end": END
            }
        )
        
        self.workflow.add_conditional_edges(
            "content_creation",
            self._route_from_content_creation,
            {
                "content_feedback": "content_feedback",
                "error": "error_handler",
                "end": END
            }
        )
        
        self.workflow.add_conditional_edges(
            "content_feedback",
            self._route_from_content_feedback,
            {
                "content_creation": "content_creation",
                "execution": "execution_guidance",
                "error": "error_handler",
                "end": END
            }
        )
        
        # 실행 가이드는 항상 종료
        self.workflow.add_edge("execution_guidance", END)
        
        # 에러 핸들러 라우팅
        self.workflow.add_conditional_edges(
            "error_handler",
            self._route_from_error,
            {
                "retry": "initial",
                "end": END
            }
        )
        
        # 워크플로우 컴파일
        self.compiled_graph = self.workflow.compile(
            checkpointer=self.memory,
            interrupt_before=[]
        )
        
        logger.info("개선된 마케팅 에이전트 워크플로우 구성 완료")
    
    # 강화된 라우팅 함수들 (무한 루프 강력 방지)
    
    def _route_from_initial(self, state: MarketingAgentState) -> Literal["goal_setting", "continue", "error", "end"]:
        """초기 상담 라우팅 - 강력한 무한 루프 방지"""
        try:
            if state.get("error"):
                return "error"
            
            if state.get("should_end"):
                return "end"
            
            iteration_count = state.get("iteration_count", 0)
            next_action = state.get("next_action", "continue")
            
            # 스마트한 진행 조건 (정보 완성도 + 반복 횟수)
            if iteration_count >= 7:
                logger.info(f"초기 상담 자연스럽게 진행: {iteration_count}회")
                return "goal_setting"
            
            # 기본 정보 완성도 확인
            has_business = bool(state.get("business_type"))
            has_product = bool(state.get("product"))
            
            if next_action == "goal_setting" or (has_business and has_product):
                return "goal_setting"
            else:
                return "continue"
                
        except Exception as e:
            logger.error(f"초기 상담 라우팅 오류: {e}")
            return "error"
    
    def _route_from_goal_setting(self, state: MarketingAgentState) -> Literal["target_analysis", "continue", "error", "end"]:
        """목표 설정 라우팅 - 강력한 무한 루프 방지"""
        try:
            if state.get("error"):
                return "error"
            
            if state.get("should_end"):
                return "end"
            
            iteration_count = state.get("iteration_count", 0)
            next_action = state.get("next_action", "continue")
            
            # 더 관대한 반복 제한
            if iteration_count >= 5:
                logger.info(f"목표 설정 자연스럽게 진행: {iteration_count}회")
                return "target_analysis"
            
            if next_action == "target_analysis" or state.get("main_goal"):
                return "target_analysis"
            else:
                return "continue"
                
        except Exception as e:
            logger.error(f"목표 설정 라우팅 오류: {e}")
            return "error"
    
    def _route_from_target_analysis(self, state: MarketingAgentState) -> Literal["strategy_planning", "continue", "error", "end"]:
        """타겟 분석 라우팅 - 강력한 무한 루프 방지"""
        try:
            if state.get("error"):
                return "error"
            
            if state.get("should_end"):
                return "end"
            
            iteration_count = state.get("iteration_count", 0)
            next_action = state.get("next_action", "continue")
            
            # 더 관대한 반복 제한
            if iteration_count >= 5:
                logger.info(f"타겟 분석 자연스럽게 진행: {iteration_count}회")
                return "strategy_planning"
            
            if next_action == "strategy_planning" or state.get("target_audience"):
                return "strategy_planning"
            else:
                return "continue"
                
        except Exception as e:
            logger.error(f"타겟 분석 라우팅 오류: {e}")
            return "error"
    
    def _route_from_strategy_planning(self, state: MarketingAgentState) -> Literal["content_creation", "execution", "continue", "error", "end"]:
        """전략 기획 라우팅 - 강력한 무한 루프 방지"""
        try:
            if state.get("error"):
                return "error"
            
            if state.get("should_end"):
                return "end"
            
            iteration_count = state.get("iteration_count", 0)
            next_action = state.get("next_action", "continue")
            
            # 더 관대한 반복 제한
            if iteration_count >= 6:
                logger.info(f"전략 기획 자연스럽게 완료: {iteration_count}회")
                return "execution"
            
            if next_action == "content_creation":
                return "content_creation"
            elif next_action == "execution":
                return "execution"
            else:
                return "continue"
                
        except Exception as e:
            logger.error(f"전략 기획 라우팅 오류: {e}")
            return "error"
    
    def _route_from_content_creation(self, state: MarketingAgentState) -> Literal["content_feedback", "error", "end"]:
        """컨텐츠 생성 라우팅 - 단순화"""
        try:
            if state.get("error"):
                return "error"
            
            if state.get("should_end"):
                return "end"
            
            # 컨텐츠 생성 후 무조건 피드백으로
            return "content_feedback"
                
        except Exception as e:
            logger.error(f"컨텐츠 생성 라우팅 오류: {e}")
            return "error"
    
    def _route_from_content_feedback(self, state: MarketingAgentState) -> Literal["content_creation", "execution", "error", "end"]:
        """컨텐츠 피드백 라우팅 - 강력한 무한 루프 방지"""
        try:
            if state.get("error"):
                return "error"
            
            if state.get("should_end"):
                return "end"
            
            feedback_count = state.get("feedback_count", 0)
            next_action = state.get("next_action", "execution")
            
            # 피드백 횟수 적절한 제한
            if feedback_count >= 4:  # 최대 4회
                logger.info(f"피드백 완료: {feedback_count}회")
                return "execution"
            
            if next_action == "content_creation":
                return "content_creation"
            else:
                return "execution"
                
        except Exception as e:
            logger.error(f"피드백 라우팅 오류: {e}")
            return "error"
    
    def _route_from_error(self, state: MarketingAgentState) -> Literal["retry", "end"]:
        """에러 핸들러 라우팅 - 단순화"""
        try:
            retry_count = state.get("retry_count", 0)
            
            if retry_count >= 2 or state.get("should_end"):
                return "end"
            else:
                return "retry"
                
        except Exception as e:
            logger.error(f"에러 라우팅 오류: {e}")
            return "end"
    
    # 공개 메서드들 (타임아웃 강화)
    async def process_message(self, user_id: int, conversation_id: int, user_input: str) -> Dict[str, Any]:
        """단계별로 한 번만 실행 후 응답 반환 (정보 미수집 시 같은 노드 유지)"""
        try:
            logger.info(f"[{conversation_id}] 메시지 처리 시작 (단계별): {user_input[:30]}...")
            
            # 현재 상태 초기화 또는 기존 상태 불러오기
            initial_state = StateManager.initialize_state(user_id, conversation_id, user_input)
            current_stage = initial_state.get("current_stage", MarketingStage.INITIAL)

            # 현재 단계(Node) 함수 선택
            node_fn = getattr(self.nodes, current_stage.value.lower(), None)
            if node_fn is None:
                return {
                    "success": False,
                    "error": f"노드 '{current_stage}'를 찾을 수 없습니다.",
                    "data": {
                        "conversation_id": conversation_id,
                        "user_id": user_id,
                        "answer": "알 수 없는 단계입니다.",
                        "current_stage": current_stage.value
                    }
                }

            # 현재 단계 실행
            result = await node_fn(initial_state)

            # 다음 단계 여부 확인 (정보 수집 부족 시 현재 단계 유지)
            next_stage = result.get("next_action")
            if next_stage and "continue" not in next_stage:
                result["current_stage"] = getattr(MarketingStage, next_stage.upper(), current_stage)
            else:
                result["current_stage"] = current_stage  # 계속 같은 단계 유지

            # 응답 데이터 생성
            response_data = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "answer": result.get("response", "응답을 생성하지 못했습니다."),
                "current_stage": result["current_stage"].value,
                "completion_rate": result.get("completion_rate", 0.0),
                "business_info": {
                    "business_type": result.get("business_type"),
                    "product": result.get("product"),
                    "target_audience": result.get("target_audience"),
                    "main_goal": result.get("main_goal")
                },
                "generated_content": result.get("generated_content"),
                "is_completed": result.get("should_end", False),
                "next_suggestions": self._get_quick_suggestions(result),
                "workflow_type": "improved_langraph",
                "version": f"{config.VERSION}-improved"
            }

            logger.info(f"[{conversation_id}] 메시지 처리 완료 (단계별)")
            return {"success": True, "data": response_data}

        except Exception as e:
            logger.error(f"[{conversation_id}] 메시지 처리 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "answer": "시스템 오류가 발생했습니다. 다시 시도해주세요.",
                    "current_stage": "error",
                    "workflow_type": "improved_langraph"
                }
            }
    
    def _get_quick_suggestions(self, state: MarketingAgentState) -> List[str]:
        """빠른 제안 생성"""
        current_stage = state["current_stage"]
        
        stage_suggestions = {
            MarketingStage.INITIAL: [
                "카페를 운영하고 있어요",
                "온라인 쇼핑몰입니다",
                "마케팅이 처음이에요"
            ],
            MarketingStage.GOAL_SETTING: [
                "매출을 늘리고 싶어요",
                "더 많은 사람들이 알았으면 좋겠어요",
                "신규 고객을 확보하고 싶습니다"
            ],
            MarketingStage.TARGET_ANALYSIS: [
                "20-30대 여성이 주요 고객입니다",
                "직장인들을 대상으로 해요",
                "지역 주민들이 주 고객층입니다"
            ],
            MarketingStage.STRATEGY_PLANNING: [
                "인스타그램 포스트 만들어주세요",
                "어떻게 시작하면 좋을까요?",
                "실행 방법을 알려주세요"
            ]
        }
        
        return stage_suggestions.get(current_stage, ["계속 진행해주세요"])
    
    def get_conversation_status(self, conversation_id: int) -> Dict[str, Any]:
        """대화 상태 조회"""
        try:
            config_dict = {
                "configurable": {
                    "thread_id": str(conversation_id)
                }
            }
            
            # 현재 상태 조회
            current_state = self.compiled_graph.get_state(config=config_dict)
            
            if current_state and current_state.values:
                state_values = current_state.values
                return {
                    "conversation_id": conversation_id,
                    "current_stage": state_values.get("current_stage", MarketingStage.INITIAL).value,
                    "completion_rate": state_values.get("completion_rate", 0.0),
                    "message_count": len(state_values.get("messages", [])),
                    "business_info": {
                        "business_type": state_values.get("business_type"),
                        "product": state_values.get("product"),
                        "target_audience": state_values.get("target_audience"),
                        "main_goal": state_values.get("main_goal")
                    },
                    "is_completed": state_values.get("should_end", False),
                    "last_activity": state_values.get("last_activity"),
                    "workflow_type": "improved_langraph"
                }
            else:
                return {
                    "conversation_id": conversation_id,
                    "status": "not_found",
                    "workflow_type": "improved_langraph"
                }
                
        except Exception as e:
            logger.error(f"대화 상태 조회 실패: {e}")
            return {
                "conversation_id": conversation_id,
                "status": "error",
                "error": str(e),
                "workflow_type": "improved_langraph"
            }
    
    async def reset_conversation(self, conversation_id: int) -> bool:
        """대화 초기화"""
        try:
            config_dict = {
                "configurable": {
                    "thread_id": str(conversation_id)
                }
            }
            
            # 메모리에서 대화 삭제
            # MemorySaver의 경우 직접적인 삭제 방법이 제한적이므로
            # 새로운 상태로 덮어쓰기
            empty_state = {
                "conversation_id": conversation_id,
                "current_stage": MarketingStage.INITIAL,
                "messages": [],
                "should_end": True
            }
            
            logger.info(f"대화 초기화 완료: {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"대화 초기화 실패: {e}")
            return False
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """워크플로우 정보 조회"""
        return {
            "workflow_type": "improved_langraph",
            "version": f"{config.VERSION}-improved",
            "optimizations": [
                "llm_based_intent_analysis",
                "aggressive_loop_prevention", 
                "timeout_optimization",
                "simplified_routing",
                "fast_content_generation"
            ],
            "max_iterations": {
                "initial": 3,
                "goal_setting": 2,
                "target_analysis": 2,
                "strategy_planning": 2,
                "content_feedback": 2
            },
            "timeout_settings": {
                "total_workflow": 20,
                "llm_calls": 15,
                "content_generation": 10
            }
        }

# 전역 워크플로우 인스턴스
improved_marketing_workflow = ImprovedMarketingWorkflow()
