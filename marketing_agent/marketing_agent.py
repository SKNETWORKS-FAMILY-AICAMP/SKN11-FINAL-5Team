"""
LangGraph 기반 마케팅 에이전트 - 메인 클래스
기존 인터페이스와 호환성 유지하면서 LangGraph 워크플로우 활용
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from marketing_workflow import marketing_workflow
from config import config, create_response

logger = logging.getLogger(__name__)

class MarketingAgent:
    """LangGraph 기반 마케팅 에이전트 - 기존 인터페이스 호환"""
    
    def __init__(self):
        """에이전트 초기화"""
        self.workflow = marketing_workflow
        self.version = config.VERSION
        
        logger.info(f"🚀 LangGraph 기반 마케팅 에이전트 초기화 완료 (v{self.version})")
    
    async def process_message(self, user_input: str, user_id: int, 
                             conversation_id: Optional[int] = None) -> Dict[str, Any]:
        """메시지 처리 - 기존 인터페이스와 호환"""
        start_time = datetime.now()
        
        try:
            logger.info(f"메시지 처리 시작 - user_id: {user_id}, input: {user_input[:50]}...")
            
            # conversation_id가 없으면 생성
            if conversation_id is None:
                conversation_id = self._generate_conversation_id(user_id)
            
            # LangGraph 워크플로우 실행
            result = await self.workflow.process_message(user_id, conversation_id, user_input)
            
            # 처리 시간 계산
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 기존 형식에 맞게 응답 조정
            if result.get("success"):
                data = result["data"]
                data.update({
                    "processing_time": processing_time,
                    "is_new_conversation": conversation_id != conversation_id,  # 새 대화 여부는 별도 로직 필요
                    "workflow_engine": "langraph",
                    "features": [
                        "langraph_workflow",
                        "state_management", 
                        "conditional_routing",
                        "memory_persistence",
                        "error_recovery"
                    ]
                })
            else:
                # 에러 응답도 기존 형식 유지
                data = result.get("data", {})
                data.update({
                    "processing_time": processing_time,
                    "workflow_engine": "langraph"
                })
            
            return result
            
        except Exception as e:
            logger.error(f"메시지 처리 실패: {e}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return create_response(
                success=False,
                error=f"마케팅 상담 중 문제가 발생했습니다: {str(e)}",
                data={
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "answer": "죄송합니다. 시스템 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                    "processing_time": processing_time,
                    "workflow_engine": "langraph",
                    "error_type": "system_error"
                }
            )
    
    def get_conversation_status(self, conversation_id: int) -> Dict[str, Any]:
        """대화 상태 조회 - 기존 인터페이스와 호환"""
        try:
            status = self.workflow.get_conversation_status(conversation_id)
            return status
            
        except Exception as e:
            logger.error(f"대화 상태 조회 실패: {e}")
            return {
                "error": f"대화 상태 조회 중 오류 발생: {str(e)}",
                "conversation_id": conversation_id,
                "workflow_engine": "langraph"
            }
    
    async def reset_conversation(self, conversation_id: int) -> bool:
        """대화 초기화 - 기존 인터페이스와 호환"""
        try:
            success = await self.workflow.reset_conversation(conversation_id)
            if success:
                logger.info(f"대화 초기화 완료: {conversation_id}")
            return success
            
        except Exception as e:
            logger.error(f"대화 초기화 실패: {e}")
            return False
    
    def get_agent_status(self) -> Dict[str, Any]:
        """에이전트 상태 조회 - 기존 인터페이스와 호환"""
        try:
            workflow_info = self.workflow.get_workflow_info()
            
            return {
                "version": self.version,
                "service_name": config.SERVICE_NAME,
                "status": "healthy",
                "workflow_engine": "langraph",
                "workflow_info": workflow_info,
                "capabilities": [
                    "multi_stage_consultation",
                    "adaptive_conversation_flow",
                    "content_generation",
                    "business_analysis",
                    "strategy_planning",
                    "execution_guidance"
                ],
                "langraph_features": [
                    "stateful_workflow",
                    "conditional_routing", 
                    "memory_persistence",
                    "error_recovery",
                    "checkpoint_support",
                    "async_processing"
                ],
                "improvements_over_previous": [
                    "더 명확한 상태 관리",
                    "조건부 라우팅으로 유연한 대화 흐름",
                    "메모리 기반 세션 지속성",
                    "체계적인 에러 처리",
                    "모듈화된 아키텍처",
                    "확장 가능한 워크플로우"
                ]
            }
            
        except Exception as e:
            logger.error(f"에이전트 상태 조회 실패: {e}")
            return {
                "version": self.version,
                "service_name": config.SERVICE_NAME,
                "status": "error",
                "error": str(e),
                "workflow_engine": "langraph"
            }
    
    async def batch_process(self, messages: list) -> Dict[str, Any]:
        """배치 메시지 처리 - 기존 인터페이스와 호환"""
        try:
            results = []
            
            for message_data in messages:
                result = await self.process_message(
                    user_input=message_data.get("message", ""),
                    user_id=message_data.get("user_id", 0),
                    conversation_id=message_data.get("conversation_id")
                )
                results.append(result)
                
                # 배치 처리 간 딜레이
                await asyncio.sleep(0.1)
            
            success_count = len([r for r in results if r.get("success")])
            
            return create_response(
                success=True,
                data={
                    "batch_results": results,
                    "processed_count": len(results),
                    "success_count": success_count,
                    "workflow_engine": "langraph"
                }
            )
            
        except Exception as e:
            logger.error(f"배치 처리 실패: {e}")
            
            return create_response(
                success=False,
                error=f"배치 메시지 처리 중 오류가 발생했습니다: {str(e)}",
                data={
                    "workflow_engine": "langraph"
                }
            )
    
    # 유틸리티 메서드들
    
    def _generate_conversation_id(self, user_id: int) -> int:
        """대화 ID 생성"""
        import time
        return int(f"{user_id}{int(time.time())}")
    
    # 추가 LangGraph 특화 메서드들
    
    def get_workflow_diagram(self) -> Dict[str, Any]:
        """워크플로우 다이어그램 정보 (LangGraph 전용)"""
        try:
            # LangGraph의 워크플로우 구조를 시각적으로 표현
            workflow_structure = {
                "nodes": [
                    {
                        "id": "initial_consultation",
                        "label": "초기 상담",
                        "description": "기본 정보 수집 및 상담 시작"
                    },
                    {
                        "id": "goal_setting", 
                        "label": "목표 설정",
                        "description": "마케팅 목표 및 원하는 결과 설정"
                    },
                    {
                        "id": "target_analysis",
                        "label": "타겟 분석", 
                        "description": "고객층 및 시장 분석"
                    },
                    {
                        "id": "strategy_planning",
                        "label": "전략 기획",
                        "description": "구체적 마케팅 전략 수립"
                    },
                    {
                        "id": "content_creation",
                        "label": "콘텐츠 생성",
                        "description": "실제 마케팅 콘텐츠 제작"
                    },
                    {
                        "id": "content_feedback",
                        "label": "피드백 처리",
                        "description": "콘텐츠에 대한 피드백 수집 및 반영"
                    },
                    {
                        "id": "execution_guidance",
                        "label": "실행 가이드",
                        "description": "마케팅 실행 방법 안내"
                    },
                    {
                        "id": "error_handler",
                        "label": "에러 처리",
                        "description": "오류 상황 처리 및 복구"
                    }
                ],
                "edges": [
                    {"from": "START", "to": "initial_consultation"},
                    {"from": "initial_consultation", "to": "goal_setting", "condition": "정보 충족"},
                    {"from": "goal_setting", "to": "target_analysis", "condition": "목표 설정 완료"},
                    {"from": "target_analysis", "to": "strategy_planning", "condition": "타겟 분석 완료"},
                    {"from": "strategy_planning", "to": "content_creation", "condition": "콘텐츠 요청"},
                    {"from": "content_creation", "to": "content_feedback", "condition": "콘텐츠 생성 완료"},
                    {"from": "content_feedback", "to": "execution_guidance", "condition": "승인"},
                    {"from": "content_feedback", "to": "content_creation", "condition": "수정 요청"},
                    {"from": "execution_guidance", "to": "END"},
                    {"from": "*", "to": "error_handler", "condition": "오류 발생"}
                ],
                "workflow_type": "langraph_stateful"
            }
            
            return {
                "success": True,
                "workflow_structure": workflow_structure,
                "visualization_url": "/workflow/diagram",  # 실제 시각화 엔드포인트
                "mermaid_diagram": self._generate_mermaid_diagram()
            }
            
        except Exception as e:
            logger.error(f"워크플로우 다이어그램 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_mermaid_diagram(self) -> str:
        """Mermaid 다이어그램 코드 생성"""
        return """
graph TD
    START([시작]) --> IC[초기 상담]
    IC --> GS[목표 설정]
    IC --> IC
    GS --> TA[타겟 분석]
    GS --> GS
    TA --> SP[전략 기획]
    TA --> TA
    SP --> CC[콘텐츠 생성]
    SP --> SP
    CC --> CF[피드백 처리]
    CF --> CC
    CF --> EG[실행 가이드]
    EG --> END([완료])
    IC --> EH[에러 처리]
    GS --> EH
    TA --> EH
    SP --> EH
    CC --> EH
    CF --> EH
    EG --> EH
    EH --> IC
    EH --> END
    
    classDef startEnd fill:#e1f5fe
    classDef process fill:#f3e5f5
    classDef decision fill:#fff3e0
    classDef error fill:#ffebee
    
    class START,END startEnd
    class IC,GS,TA,SP,CC,CF,EG process
    class EH error
"""
    
    def get_conversation_flow_analysis(self, conversation_id: int) -> Dict[str, Any]:
        """대화 흐름 분석 (LangGraph 전용)"""
        try:
            status = self.get_conversation_status(conversation_id)
            
            if status.get("status") == "not_found":
                return {
                    "success": False,
                    "error": "대화를 찾을 수 없습니다"
                }
            
            # 대화 흐름 분석
            analysis = {
                "conversation_id": conversation_id,
                "current_stage": status.get("current_stage"),
                "progression": self._analyze_stage_progression(status),
                "efficiency_score": self._calculate_efficiency_score(status),
                "recommendations": self._get_flow_recommendations(status),
                "workflow_performance": {
                    "stages_completed": self._count_completed_stages(status),
                    "completion_rate": status.get("completion_rate", 0),
                    "estimated_remaining_time": self._estimate_remaining_time(status)
                }
            }
            
            return {
                "success": True,
                "flow_analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"대화 흐름 분석 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _analyze_stage_progression(self, status: Dict[str, Any]) -> List[Dict[str, Any]]:
        """단계 진행 분석"""
        # 구현 예정
        return []
    
    def _calculate_efficiency_score(self, status: Dict[str, Any]) -> float:
        """효율성 점수 계산"""
        completion_rate = status.get("completion_rate", 0)
        message_count = status.get("message_count", 1)
        
        # 간단한 효율성 계산 (메시지 수 대비 완료율)
        efficiency = completion_rate * 100 / max(message_count, 1)
        return min(efficiency, 100.0)
    
    def _get_flow_recommendations(self, status: Dict[str, Any]) -> List[str]:
        """흐름 개선 권장사항"""
        recommendations = []
        
        completion_rate = status.get("completion_rate", 0)
        current_stage = status.get("current_stage", "")
        
        if completion_rate < 0.3:
            recommendations.append("기본 정보 수집을 완료하면 더 정확한 조언을 제공할 수 있습니다")
        
        if current_stage == "strategy_planning" and completion_rate > 0.6:
            recommendations.append("충분한 정보가 수집되었으니 콘텐츠 생성을 시작해보세요")
        
        return recommendations
    
    def _count_completed_stages(self, status: Dict[str, Any]) -> int:
        """완료된 단계 수 계산"""
        # 구현 예정
        return 0
    
    def _estimate_remaining_time(self, status: Dict[str, Any]) -> str:
        """남은 예상 시간"""
        completion_rate = status.get("completion_rate", 0)
        
        if completion_rate < 0.3:
            return "5-10분"
        elif completion_rate < 0.7:
            return "3-5분"
        else:
            return "1-3분"

# 기존 인터페이스와의 호환성을 위한 전역 인스턴스
marketing_agent = MarketingAgent()
