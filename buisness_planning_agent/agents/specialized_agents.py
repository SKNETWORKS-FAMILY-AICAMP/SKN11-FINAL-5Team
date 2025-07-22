"""
Startup Preparation Agent - 창업 준비 전문 에이전트
"""

import logging
from typing import Dict, Any, List
from .base_agent import BaseBusinessAgent

logger = logging.getLogger(__name__)

class StartupPreparationAgent(BaseBusinessAgent):
    """창업 준비 전문 에이전트"""
    
    def __init__(self):
        super().__init__("창업 준비 전문가")
        
    def process_query(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """창업 준비 관련 쿼리 처리"""
        try:
            # 전문화된 프롬프트 생성
            specialized_prompt = self.get_specialized_prompt(user_input, context)
            
            # 관련 지식 검색
            knowledge = self.search_knowledge(user_input)
            
            # 프롬프트에 지식 추가
            if knowledge:
                specialized_prompt += f"\n\n참고 자료:\n{chr(10).join(knowledge)}"
            
            # 응답 생성
            response = self.generate_response(specialized_prompt, context)
            
            return {
                "agent_type": self.agent_type,
                "response": response,
                "knowledge_used": len(knowledge) > 0,
                "specialization": "startup_preparation"
            }
            
        except Exception as e:
            logger.error(f"창업 준비 쿼리 처리 실패: {e}")
            return {
                "agent_type": self.agent_type,
                "response": "창업 준비 관련 처리 중 오류가 발생했습니다.",
                "error": str(e)
            }
    
    def get_specialized_prompt(self, user_input: str, context: Dict[str, Any]) -> str:
        """창업 준비 전문 프롬프트 생성"""
        return f"""당신은 창업 준비 전문 컨설턴트입니다.
        
다음 영역에 대한 전문적인 조언을 제공해주세요:
- 창업 준비 체크리스트
- 사업자 등록 절차
- 필요한 허가 및 신고
- 초기 준비 사항
- 법적 요구사항

사용자 질문: {user_input}

수집된 정보:
{context.get('collected_info', '정보 없음')}

체계적이고 실무적인 창업 준비 가이드를 제공해주세요."""

class IdeaValidationAgent(BaseBusinessAgent):
    """아이디어 검증 전문 에이전트"""
    
    def __init__(self):
        super().__init__("아이디어 검증 전문가")
        
    def process_query(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """아이디어 검증 관련 쿼리 처리"""
        try:
            specialized_prompt = self.get_specialized_prompt(user_input, context)
            knowledge = self.search_knowledge(user_input)
            
            if knowledge:
                specialized_prompt += f"\n\n참고 자료:\n{chr(10).join(knowledge)}"
            
            response = self.generate_response(specialized_prompt, context)
            
            return {
                "agent_type": self.agent_type,
                "response": response,
                "knowledge_used": len(knowledge) > 0,
                "specialization": "idea_validation"
            }
            
        except Exception as e:
            logger.error(f"아이디어 검증 쿼리 처리 실패: {e}")
            return {
                "agent_type": self.agent_type,
                "response": "아이디어 검증 관련 처리 중 오류가 발생했습니다.",
                "error": str(e)
            }
    
    def get_specialized_prompt(self, user_input: str, context: Dict[str, Any]) -> str:
        """아이디어 검증 전문 프롬프트 생성"""
        return f"""당신은 아이디어 검증 전문가입니다.
        
다음 관점에서 객관적이고 전문적인 분석을 제공해주세요:
- 시장성 분석 (TAM, SAM, SOM)
- 타겟 고객 검증
- 경쟁사 분석
- 차별화 포인트 평가
- 수익성 검토
- MVP 설계 방향

사용자 질문: {user_input}

비즈니스 아이디어: {context.get('collected_info', {}).get('business_idea', '명시되지 않음')}
타겟 고객: {context.get('collected_info', {}).get('target_customers', '명시되지 않음')}

데이터 기반의 객관적인 아이디어 검증을 도와주세요."""

class BusinessModelAgent(BaseBusinessAgent):
    """비즈니스 모델 설계 전문 에이전트"""
    
    def __init__(self):
        super().__init__("비즈니스 모델 설계 전문가")
        
    def process_query(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """비즈니스 모델 관련 쿼리 처리"""
        try:
            specialized_prompt = self.get_specialized_prompt(user_input, context)
            knowledge = self.search_knowledge(user_input)
            
            if knowledge:
                specialized_prompt += f"\n\n참고 자료:\n{chr(10).join(knowledge)}"
            
            response = self.generate_response(specialized_prompt, context)
            
            return {
                "agent_type": self.agent_type,
                "response": response,
                "knowledge_used": len(knowledge) > 0,
                "specialization": "business_model"
            }
            
        except Exception as e:
            logger.error(f"비즈니스 모델 쿼리 처리 실패: {e}")
            return {
                "agent_type": self.agent_type,
                "response": "비즈니스 모델 관련 처리 중 오류가 발생했습니다.",
                "error": str(e)
            }
    
    def get_specialized_prompt(self, user_input: str, context: Dict[str, Any]) -> str:
        """비즈니스 모델 전문 프롬프트 생성"""
        return f"""당신은 비즈니스 모델 설계 전문가입니다.
        
다음 요소들을 포함한 체계적인 비즈니스 모델을 설계해주세요:
- 가치 제안 (Value Proposition)
- 핵심 파트너십
- 핵심 활동 및 자원
- 비용 구조
- 수익 흐름
- 고객 관계
- 채널 전략
- 고객 세그먼트

사용자 질문: {user_input}

수집된 비즈니스 정보:
{context.get('collected_info', '정보 없음')}

실행 가능하고 지속가능한 비즈니스 모델을 제안해주세요."""
