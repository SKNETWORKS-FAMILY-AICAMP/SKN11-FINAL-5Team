"""
LangGraph 기반 마케팅 에이전트 워크플로우
StateGraph를 사용한 마케팅 상담 프로세스 정의
"""

import imp
import logging
from typing import Literal, Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from marketing_state import MarketingAgentState, MarketingStage, StateManager
from marketing_nodes import marketing_nodes
from config import config

import asyncio

logger = logging.getLogger(__name__)

class MarketingWorkflow:
    """LangGraph 기반 마케팅 에이전트 워크플로우"""
    
    def __init__(self):
        self.workflow = None
        self.compiled_graph = None
        self.memory = MemorySaver()
        self._build_workflow()
    
    def _build_workflow(self):
        """워크플로우 구성"""
        logger.info("마케팅 에이전트 워크플로우 구성 시작")
        
        # StateGraph 초기화
        self.workflow = StateGraph(MarketingAgentState)
        
        # Node 추가
        self.workflow.add_node("initial_consultation", marketing_nodes.initial_consultation)
        self.workflow.add_node("goal_setting", marketing_nodes.goal_setting)
        self.workflow.add_node("target_analysis", marketing_nodes.target_analysis)
        self.workflow.add_node("strategy_planning", marketing_nodes.strategy_planning)
        self.workflow.add_node("content_creation", marketing_nodes.content_creation)
        self.workflow.add_node("content_feedback", marketing_nodes.content_feedback)
        self.workflow.add_node("execution_guidance", marketing_nodes.execution_guidance)
        self.workflow.add_node("error_handler", marketing_nodes.error_handler)
        
        # 시작점 설정
        self.workflow.add_edge(START, "initial_consultation")
        
        # 조건부 라우팅 설정
        self.workflow.add_conditional_edges(
            "initial_consultation",
            self._route_from_initial,
            {
                "goal_setting": "goal_setting",
                "continue_initial": "initial_consultation",
                "error": "error_handler",
                "end": END
            }
        )
        
        self.workflow.add_conditional_edges(
            "goal_setting",
            self._route_from_goal_setting,
            {
                "target_analysis": "target_analysis",
                "continue_goal_setting": "goal_setting",
                "error": "error_handler",
                "end": END
            }
        )
        
        self.workflow.add_conditional_edges(
            "target_analysis",
            self._route_from_target_analysis,
            {
                "strategy_planning": "strategy_planning",
                "continue_target_analysis": "target_analysis",
                "error": "error_handler",
                "end": END
            }
        )
        
        self.workflow.add_conditional_edges(
            "strategy_planning",
            self._route_from_strategy_planning,
            {
                "content_creation": "content_creation",
                "continue_strategy_planning": "strategy_planning",
                "suggest_content_creation": "strategy_planning",
                "error": "error_handler",
                "end": END
            }
        )
        
        self.workflow.add_conditional_edges(
            "content_creation",
            self._route_from_content_creation,
            {
                "content_feedback": "content_feedback",
                "strategy_planning": "strategy_planning",
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
                "continue_feedback": "content_feedback",
                "error": "error_handler",
                "end": END
            }
        )
        
        self.workflow.add_conditional_edges(
            "execution_guidance",
            self._route_from_execution,
            {
                "end": END,
                "error": "error_handler"
            }
        )
        
        self.workflow.add_conditional_edges(
            "error_handler",
            self._route_from_error,
            {
                "initial_consultation": "initial_consultation",
                "end": END
            }
        )
        
        # 워크플로우 컴파일
        self.compiled_graph = self.workflow.compile(
            checkpointer=self.memory,
            interrupt_before=[]  # 필요시 인터럽트 포인트 추가
        )
        
        logger.info("마케팅 에이전트 워크플로우 구성 완료")
    
    # 라우팅 함수들
    
    def _route_from_initial(self, state: MarketingAgentState) -> Literal["goal_setting", "continue_initial", "error", "end"]:
        """초기 상담에서의 라우팅"""
        try:
            if state.get("error"):
                return "error"
            
            if state.get("should_end"):
                return "end"
            
            next_action = state.get("next_action", "continue_initial")
            
            if next_action == "goal_setting":
                return "goal_setting"
            else:
                return "continue_initial"
                
        except Exception as e:
            logger.error(f"초기 상담 라우팅 오류: {e}")
            return "error"
    
    def _route_from_goal_setting(self, state: MarketingAgentState) -> Literal["target_analysis", "continue_goal_setting", "error", "end"]:
        """목표 설정에서의 라우팅"""
        try:
            if state.get("error"):
                return "error"
            
            if state.get("should_end"):
                return "end"
            
            next_action = state.get("next_action", "continue_goal_setting")
            
            if next_action == "target_analysis":
                return "target_analysis"
            else:
                return "continue_goal_setting"
                
        except Exception as e:
            logger.error(f"목표 설정 라우팅 오류: {e}")
            return "error"
    
    def _route_from_target_analysis(self, state: MarketingAgentState) -> Literal["strategy_planning", "continue_target_analysis", "error", "end"]:
        """타겟 분석에서의 라우팅"""
        try:
            if state.get("error"):
                return "error"
            
            if state.get("should_end"):
                return "end"
            
            next_action = state.get("next_action", "continue_target_analysis")
            
            if next_action == "strategy_planning":
                return "strategy_planning"
            else:
                return "continue_target_analysis"
                
        except Exception as e:
            logger.error(f"타겟 분석 라우팅 오류: {e}")
            return "error"
    
    def _route_from_strategy_planning(self, state: MarketingAgentState) -> Literal["content_creation", "continue_strategy_planning", "suggest_content_creation", "error", "end"]:
        """전략 기획에서의 라우팅"""
        try:
            if state.get("error"):
                return "error"
            
            if state.get("should_end"):
                return "end"
            
            next_action = state.get("next_action", "continue_strategy_planning")
            
            if next_action == "content_creation":
                return "content_creation"
            elif next_action == "suggest_content_creation":
                return "suggest_content_creation"
            else:
                return "continue_strategy_planning"
                
        except Exception as e:
            logger.error(f"전략 기획 라우팅 오류: {e}")
            return "error"
    
    def _route_from_content_creation(self, state: MarketingAgentState) -> Literal["content_feedback", "strategy_planning", "error", "end"]:
        """컨텐츠 생성에서의 라우팅"""
        try:
            if state.get("error"):
                return "error"
            
            if state.get("should_end"):
                return "end"
            
            next_action = state.get("next_action", "content_feedback")
            
            if next_action == "content_feedback":
                return "content_feedback"
            elif next_action == "strategy_planning":
                return "strategy_planning"
            else:
                return "content_feedback"
                
        except Exception as e:
            logger.error(f"컨텐츠 생성 라우팅 오류: {e}")
            return "error"
    
    def _route_from_content_feedback(self, state: MarketingAgentState) -> Literal["content_creation", "execution", "continue_feedback", "error", "end"]:
        """컨텐츠 피드백에서의 라우팅"""
        try:
            if state.get("error"):
                return "error"
            
            if state.get("should_end"):
                return "end"
            
            next_action = state.get("next_action", "continue_feedback")
            
            if next_action == "content_creation":
                return "content_creation"
            elif next_action == "execution":
                return "execution"
            else:
                return "continue_feedback"
                
        except Exception as e:
            logger.error(f"컨텐츠 피드백 라우팅 오류: {e}")
            return "error"
    
    def _route_from_execution(self, state: MarketingAgentState) -> Literal["end", "error"]:
        """실행 가이드에서의 라우팅"""
        try:
            if state.get("error"):
                return "error"
            else:
                return "end"
                
        except Exception as e:
            logger.error(f"실행 가이드 라우팅 오류: {e}")
            return "error"
    
    def _route_from_error(self, state: MarketingAgentState) -> Literal["initial_consultation", "end"]:
        """에러 핸들러에서의 라우팅"""
        try:
            if state.get("should_end") or state.get("retry_count", 0) >= 3:
                return "end"
            else:
                return "initial_consultation"
                
        except Exception as e:
            logger.error(f"에러 핸들러 라우팅 오류: {e}")
            return "end"
    
    # 공개 메서드들
    
    async def process_message(self, user_id: int, conversation_id: int, user_input: str) -> Dict[str, Any]:
        """메시지 처리 - 메인 진입점"""
        try:
            logger.info(f"[{conversation_id}] 메시지 처리 시작: {user_input[:50]}...")
            
            # 초기 상태 생성
            initial_state = StateManager.initialize_state(user_id, conversation_id, user_input)
            
            # Thread config 설정 (세션 관리)
            config_dict = {
                "configurable": {
                    "thread_id": str(conversation_id)
                }
            }
            
            try:
                print(f"ainvoke 시작: {initial_state}")
                result = await asyncio.wait_for(
                    self.compiled_graph.ainvoke(initial_state, config=config_dict),
                    timeout=100
                )
            except asyncio.TimeoutError:
                logger.error("워크플로우 실행이 10초 안에 끝나지 않음 - 문제 노드 확인 필요")
            
            # 응답 생성
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
                "next_suggestions": self._get_next_suggestions(result),
                "workflow_type": "langraph",
                "version": config.VERSION
            }
            
            logger.info(f"[{conversation_id}] 메시지 처리 완료")
            return {"success": True, "data": response_data}
            
        except Exception as e:
            logger.error(f"[{conversation_id}] 메시지 처리 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "answer": "죄송합니다. 처리 중 오류가 발생했습니다. 다시 시도해주세요.",
                    "current_stage": "error",
                    "workflow_type": "langraph"
                }
            }
    
    def _get_next_suggestions(self, state: MarketingAgentState) -> List[str]:
        """다음 단계 제안"""
        current_stage = state["current_stage"]
        suggestions = []
        
        if current_stage == MarketingStage.INITIAL:
            suggestions = [
                "어떤 업종에서 사업을 하고 계신가요?",
                "주력 제품이나 서비스는 무엇인가요?",
                "마케팅에서 가장 고민되는 부분은 무엇인가요?"
            ]
        elif current_stage == MarketingStage.GOAL_SETTING:
            suggestions = [
                "매출 증대가 목표입니다",
                "브랜드 인지도를 높이고 싶어요",
                "신규 고객을 늘리고 싶습니다"
            ]
        elif current_stage == MarketingStage.TARGET_ANALYSIS:
            suggestions = [
                "20-30대 여성을 타겟으로 하고 있어요",
                "지역 주민들이 주요 고객입니다",
                "B2B 고객을 대상으로 합니다"
            ]
        elif current_stage == MarketingStage.STRATEGY_PLANNING:
            suggestions = [
                "인스타그램 포스트를 만들어주세요",
                "마케팅 전략서를 작성해주세요",
                "블로그 콘텐츠를 생성해주세요"
            ]
        elif current_stage == MarketingStage.CONTENT_CREATION:
            suggestions = [
                "이 콘텐츠가 마음에 들어요",
                "다른 스타일로 다시 만들어주세요",
                "좀 더 친근한 톤으로 수정해주세요"
            ]
        
        return suggestions
    
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
                    "workflow_type": "langraph"
                }
            else:
                return {
                    "conversation_id": conversation_id,
                    "status": "not_found",
                    "workflow_type": "langraph"
                }
                
        except Exception as e:
            logger.error(f"대화 상태 조회 실패: {e}")
            return {
                "conversation_id": conversation_id,
                "status": "error",
                "error": str(e),
                "workflow_type": "langraph"
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
            "workflow_type": "langraph",
            "version": config.VERSION,
            "nodes": [
                "initial_consultation",
                "goal_setting", 
                "target_analysis",
                "strategy_planning",
                "content_creation",
                "content_feedback",
                "execution_guidance",
                "error_handler"
            ],
            "stages": [stage.value for stage in MarketingStage],
            "features": [
                "langraph_state_management",
                "conditional_routing",
                "memory_persistence",
                "error_handling",
                "content_generation",
                "feedback_processing"
            ]
        }

# 전역 워크플로우 인스턴스
marketing_workflow = MarketingWorkflow()
