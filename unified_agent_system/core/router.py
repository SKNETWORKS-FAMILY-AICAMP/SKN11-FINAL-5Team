"""
라우팅 로직 - 사용자 질의를 분석하여 적절한 에이전트 결정
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .models import AgentType, RoutingDecision, Priority, UnifiedRequest
from .config import OPENAI_API_KEY, GEMINI_API_KEY, get_system_config

logger = logging.getLogger(__name__)


class ConversationContext:
    """대화 컨텍스트를 관리하는 클래스"""
    
    def __init__(self):
        self.current_agent: Optional[AgentType] = None
        self.agent_switch_count = 0
        self.conversation_topic: Optional[str] = None
        self.last_routing_time: Optional[datetime] = None
        self.message_count = 0
        self.recent_keywords: List[str] = []
        self.agent_confidence_history: List[float] = []
    
    def update(self, agent_type: AgentType, confidence: float, keywords: List[str]):
        """컨텍스트 업데이트"""
        if self.current_agent != agent_type:
            self.agent_switch_count += 1
            self.current_agent = agent_type
        
        self.last_routing_time = datetime.now()
        self.message_count += 1
        self.recent_keywords.extend(keywords)
        self.agent_confidence_history.append(confidence)
        
        # 최근 키워드만 유지 (최대 20개)
        self.recent_keywords = self.recent_keywords[-20:]
        self.agent_confidence_history = self.agent_confidence_history[-10:]
    
    def get_stats(self) -> Dict[str, Any]:
        """컨텍스트 통계 반환"""
        return {
            "current_agent": self.current_agent.value if self.current_agent else None,
            "message_count": self.message_count,
            "agent_switches": self.agent_switch_count,
            "switch_rate": (self.agent_switch_count / self.message_count 
                          if self.message_count > 0 else 0),
            "recent_keywords": self.recent_keywords[-10:],
            "avg_confidence": (sum(self.agent_confidence_history) / 
                             len(self.agent_confidence_history)
                             if self.agent_confidence_history else 0),
            "last_routing": self.last_routing_time.isoformat() if self.last_routing_time else None
        }


class QueryRouter:
    """사용자 질의를 분석하여 적절한 에이전트로 라우팅하는 클래스"""
    
    def __init__(self):
        self.config = get_system_config()
        self.llm = self._initialize_llm()
        self._create_routing_prompt()
        
        # 컨텍스트 관리 추가
        self.context = ConversationContext()
        
        # 라우팅 설정
        self.min_routing_interval = timedelta(minutes=2)  # 최소 라우팅 간격
        self.context_continuity_threshold = 0.7  # 컨텍스트 연속성 임계값
        self.agent_switch_penalty = 0.15  # 에이전트 변경 패널티
    
    def _initialize_llm(self):
        """LLM 초기화 (OpenAI 우선, Gemini 폴백)"""
        try:
            if OPENAI_API_KEY:
                return ChatOpenAI(
                    model="gpt-3.5-turbo",
                    temperature=0.3,
                    api_key=OPENAI_API_KEY
                )
        except Exception as e:
            logger.warning(f"OpenAI 초기화 실패: {e}")
        
        try:
            if GEMINI_API_KEY:
                return ChatGoogleGenerativeAI(
                    model="gemini-pro",
                    temperature=0.3,
                    google_api_key=GEMINI_API_KEY
                )
        except Exception as e:
            logger.error(f"Gemini 초기화도 실패: {e}")
            raise Exception("사용 가능한 LLM이 없습니다")
    
    def _create_routing_prompt(self):
        """라우팅용 프롬프트 생성"""
        agent_descriptions = []
        for agent_type, config in self.config.agents.items():
            keywords = ", ".join(config.keywords[:10])  # 처음 10개 키워드만
            agent_descriptions.append(
                f"- {agent_type.value}: {config.description} (키워드: {keywords})"
            )
        
        self.routing_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""
당신은 사용자의 질문을 분석하여 가장 적절한 전문 에이전트를 선택하는 라우터입니다.

사용 가능한 에이전트들:
{chr(10).join(agent_descriptions)}

사용자의 질문을 분석하고 다음 형식으로 정확히 답변하세요:

AGENT: [에이전트타입]
CONFIDENCE: [0.0-1.0 사이의 신뢰도]
PRIORITY: [low/medium/high/urgent]
KEYWORDS: [키워드1, 키워드2, 키워드3]
REASONING: [선택 이유]

규칙:
1. AGENT는 반드시 위의 5개 중 하나여야 합니다: business_planning, customer_service, marketing, mental_health, task_automation
2. CONFIDENCE는 0.0-1.0 사이의 숫자입니다
3. PRIORITY는 low, medium, high, urgent 중 하나입니다
4. KEYWORDS는 쉼표로 구분된 관련 키워드들입니다
5. REASONING은 한 줄로 간단히 설명합니다

예시:
AGENT: business_planning
CONFIDENCE: 0.85
PRIORITY: medium
KEYWORDS: 창업, 사업계획, 아이디어
REASONING: 창업 관련 질문으로 비즈니스 플래닝 에이전트가 적합합니다
"""),
            ("human", "사용자 질문: {query}")
        ])
        
        # 컨텍스트 고려 라우팅 프롬프트 추가
        self.context_routing_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""
당신은 대화 컨텍스트를 고려하여 에이전트 라우팅을 결정하는 전문가입니다.

사용 가능한 에이전트들:
{chr(10).join(agent_descriptions)}

현재 대화 상황:
- 현재 에이전트: {{current_agent}}
- 대화 메시지 수: {{message_count}}
- 최근 키워드: {{recent_keywords}}
- 평균 신뢰도: {{avg_confidence}}

다음을 분석하여 답변하세요:
1. 현재 질문이 기존 대화와 연관성이 있는가?
2. 에이전트를 변경해야 하는가?
3. 컨텍스트 연속성을 유지해야 하는가?

답변 형식:
CONTINUITY: [high/medium/low] - 기존 대화와의 연관성
SWITCH_NEEDED: [yes/no] - 에이전트 변경 필요성
AGENT: [에이전트타입]
CONFIDENCE: [0.0-1.0]
PRIORITY: [low/medium/high/urgent]
KEYWORDS: [키워드1, 키워드2, 키워드3]
REASONING: [상세한 이유]
"""),
            ("human", "새로운 질문: {query}")
        ])
    
    async def route_query(self, request: UnifiedRequest, 
                         conversation_history: Optional[List[Dict[str, Any]]] = None,
                         enable_context_routing: bool = True) -> RoutingDecision:
        """사용자 질의를 라우팅합니다 (컨텍스트 고려 가능)"""
        try:
            # 1. 선호 에이전트가 지정된 경우
            if request.preferred_agent:
                decision = RoutingDecision(
                    agent_type=request.preferred_agent,
                    confidence=1.0,
                    reasoning="사용자가 직접 지정한 에이전트",
                    keywords=[],
                    priority=Priority.MEDIUM
                )
                if enable_context_routing:
                    self.context.update(decision.agent_type, decision.confidence, decision.keywords)
                return decision
            
            # 2. 컨텍스트 라우팅 활성화된 경우
            if enable_context_routing:
                return await self._smart_routing(request.message, conversation_history)
            
            # 3. 기존 LLM 기반 라우팅 (기본값)
            llm_decision = await self._llm_based_routing(request.message)
            
            # 4. 신뢰도가 낮으면 기본 에이전트 사용
            if llm_decision.confidence < self.config.routing_confidence_threshold:
                logger.warning(f"라우팅 신뢰도 낮음: {llm_decision.confidence}")
                llm_decision.agent_type = self.config.default_agent
                llm_decision.reasoning += " (신뢰도 낮음으로 기본 에이전트 사용)"
            
            return llm_decision
            
        except Exception as e:
            logger.error(f"라우팅 실패: {e}")
            fallback_agent = (self.context.current_agent if enable_context_routing and self.context.current_agent 
                            else self.config.default_agent)
            return RoutingDecision(
                agent_type=fallback_agent,
                confidence=0.5,
                reasoning=f"라우팅 오류로 기본/기존 에이전트 사용: {str(e)}",
                keywords=[],
                priority=Priority.MEDIUM
            )
    
    async def _smart_routing(self, query: str, 
                           conversation_history: Optional[List[Dict[str, Any]]] = None) -> RoutingDecision:
        """컨텍스트를 고려한 스마트 라우팅"""
        try:
            # 1. 첫 번째 메시지이거나 컨텍스트가 없는 경우
            if self.context.message_count == 0 or not conversation_history:
                decision = await self._llm_based_routing(query)
                self.context.update(decision.agent_type, decision.confidence, decision.keywords)
                return decision
            
            # 2. 라우팅 필요성 판단
            routing_needed = self._should_perform_routing(conversation_history)
            
            if not routing_needed:
                # 기존 에이전트 유지
                decision = RoutingDecision(
                    agent_type=self.context.current_agent,
                    confidence=0.8,
                    reasoning="대화 연속성 유지를 위해 기존 에이전트 사용",
                    keywords=self.context.recent_keywords[-3:],
                    priority=Priority.MEDIUM
                )
                self.context.message_count += 1
                return decision
            
            # 3. 컨텍스트를 고려한 새로운 라우팅
            decision = await self._contextual_routing(query, conversation_history)
            self.context.update(decision.agent_type, decision.confidence, decision.keywords)
            return decision
            
        except Exception as e:
            logger.error(f"스마트 라우팅 실패: {e}")
            # 기존 에이전트 유지 또는 기본 라우팅
            if self.context.current_agent:
                return RoutingDecision(
                    agent_type=self.context.current_agent,
                    confidence=0.6,
                    reasoning=f"스마트 라우팅 오류로 기존 에이전트 유지: {str(e)}",
                    keywords=[],
                    priority=Priority.MEDIUM
                )
            else:
                return await self._llm_based_routing(query)
    
    def _should_perform_routing(self, conversation_history: List[Dict[str, Any]]) -> bool:
        """라우팅이 필요한지 판단"""
        
        # 1. 최소 시간 간격 체크
        if (self.context.last_routing_time and 
            datetime.now() - self.context.last_routing_time < self.min_routing_interval):
            return False
        
        # 2. 너무 자주 에이전트가 바뀌는 경우 방지
        if (self.context.message_count > 0 and 
            self.context.agent_switch_count / self.context.message_count > 0.5):
            return False
        
        # 3. 최근 평균 신뢰도가 높으면 유지
        if (self.context.agent_confidence_history and 
            sum(self.context.agent_confidence_history) / len(self.context.agent_confidence_history) > 0.8):
            return False
        
        # 4. 연속된 짧은 질문들은 같은 에이전트 유지
        recent_messages = conversation_history[-3:] if conversation_history else []
        if all(len(msg.get('content', '')) < 50 for msg in recent_messages):
            return False
        
        return True
    
    async def _contextual_routing(self, query: str, 
                                conversation_history: List[Dict[str, Any]]) -> RoutingDecision:
        """컨텍스트를 고려한 라우팅"""
        try:
            # 컨텍스트 정보 준비
            avg_confidence = (
                sum(self.context.agent_confidence_history) / len(self.context.agent_confidence_history)
                if self.context.agent_confidence_history else 0.5
            )
            
            context_vars = {
                "query": query,
                "current_agent": self.context.current_agent.value if self.context.current_agent else "none",
                "message_count": self.context.message_count,
                "recent_keywords": ", ".join(self.context.recent_keywords[-5:]),
                "avg_confidence": f"{avg_confidence:.2f}"
            }
            
            chain = self.context_routing_prompt | self.llm | StrOutputParser()
            result = await chain.ainvoke(context_vars)
            
            return self._parse_contextual_result(result)
            
        except Exception as e:
            logger.error(f"컨텍스트 라우팅 실패: {e}")
            # 기존 에이전트 유지
            return RoutingDecision(
                agent_type=self.context.current_agent or self.config.default_agent,
                confidence=0.6,
                reasoning=f"컨텍스트 라우팅 오류로 기존 에이전트 유지: {str(e)}",
                keywords=[],
                priority=Priority.MEDIUM
            )
    
    def _parse_contextual_result(self, result: str) -> RoutingDecision:
        """컨텍스트 고려 라우팅 결과 파싱"""
        try:
            lines = result.strip().split('\n')
            parsed = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    parsed[key.strip().upper()] = value.strip()
            
            # 연속성 체크
            continuity = parsed.get('CONTINUITY', 'medium').lower()
            switch_needed = parsed.get('SWITCH_NEEDED', 'no').lower() == 'yes'
            
            # 기본 파싱
            base_decision = self._parse_routing_result(result)
            
            # 컨텍스트 고려한 조정
            if continuity == 'high' and not switch_needed:
                # 높은 연속성이고 변경이 불필요하면 기존 에이전트 유지
                base_decision.agent_type = self.context.current_agent or base_decision.agent_type
                base_decision.confidence = min(1.0, base_decision.confidence + 0.1)
                base_decision.reasoning += " (높은 컨텍스트 연속성)"
            
            elif switch_needed and base_decision.agent_type != self.context.current_agent:
                # 에이전트 변경 시 패널티 적용하여 신중하게 결정
                base_decision.confidence = max(0.0, base_decision.confidence - self.agent_switch_penalty)
                if base_decision.confidence < self.config.routing_confidence_threshold:
                    # 신뢰도가 너무 낮으면 기존 유지
                    base_decision.agent_type = self.context.current_agent or base_decision.agent_type
                    base_decision.reasoning += " (에이전트 변경 신뢰도 부족)"
            
            return base_decision
            
        except Exception as e:
            logger.error(f"컨텍스트 라우팅 결과 파싱 실패: {e}")
            return RoutingDecision(
                agent_type=self.context.current_agent or AgentType.BUSINESS_PLANNING,
                confidence=0.5,
                reasoning=f"파싱 오류로 기존 에이전트 유지: {str(e)}",
                keywords=[],
                priority=Priority.MEDIUM
            )
    
    async def _llm_based_routing(self, query: str) -> RoutingDecision:
        """LLM 기반 라우팅"""
        try:
            chain = self.routing_prompt | self.llm | StrOutputParser()
            result = await chain.ainvoke({"query": query})
            
            return self._parse_routing_result(result)
            
        except Exception as e:
            logger.error(f"LLM 라우팅 실패: {e}")
            raise
    
    def _parse_routing_result(self, result: str) -> RoutingDecision:
        """LLM 결과 파싱"""
        try:
            lines = result.strip().split('\n')
            parsed = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    parsed[key.strip().upper()] = value.strip()
            
            # 필수 필드 추출
            agent_str = parsed.get('AGENT', '').lower()
            confidence = float(parsed.get('CONFIDENCE', '0.5'))
            priority_str = parsed.get('PRIORITY', 'medium').lower()
            keywords_str = parsed.get('KEYWORDS', '')
            reasoning = parsed.get('REASONING', 'LLM 기반 라우팅')
            
            # AgentType 매핑
            agent_mapping = {
                'business_planning': AgentType.BUSINESS_PLANNING,
                'customer_service': AgentType.CUSTOMER_SERVICE,
                'marketing': AgentType.MARKETING,
                'mental_health': AgentType.MENTAL_HEALTH,
                'task_automation': AgentType.TASK_AUTOMATION
            }
            
            agent_type = agent_mapping.get(agent_str, AgentType.BUSINESS_PLANNING)
            
            # Priority 매핑
            priority_mapping = {
                'low': Priority.LOW,
                'medium': Priority.MEDIUM,
                'high': Priority.HIGH,
                'urgent': Priority.URGENT
            }
            priority = priority_mapping.get(priority_str, Priority.MEDIUM)
            
            # 키워드 파싱
            keywords = []
            if keywords_str:
                keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
            
            return RoutingDecision(
                agent_type=agent_type,
                confidence=max(0.0, min(1.0, confidence)),  # 0-1 범위 제한
                reasoning=reasoning,
                keywords=keywords,
                priority=priority
            )
            
        except Exception as e:
            logger.error(f"라우팅 결과 파싱 실패: {e}")
            return RoutingDecision(
                agent_type=AgentType.BUSINESS_PLANNING,
                confidence=0.5,
                reasoning=f"파싱 오류: {str(e)}",
                keywords=[],
                priority=Priority.MEDIUM
            )
    
    def get_agent_recommendations(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """상위 K개 에이전트 추천"""
        query_lower = query.lower()
        recommendations = []
        
        for agent_type, config in self.config.agents.items():
            match_score = 0
            matched_keywords = []
            
            for keyword in config.keywords:
                if keyword in query_lower:
                    match_score += 1
                    matched_keywords.append(keyword)
            
            if match_score > 0:
                confidence = min(1.0, match_score / len(config.keywords) * 2)
                recommendations.append({
                    'agent_type': agent_type,
                    'confidence': confidence,
                    'matched_keywords': matched_keywords,
                    'description': config.description
                })
        
        # 신뢰도순 정렬
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        return recommendations[:top_k]
    
    # 컨텍스트 관리 메서드들 추가
    def get_conversation_insights(self) -> Dict[str, Any]:
        """현재 대화 상태 정보 반환"""
        return self.context.get_stats()
    
    def reset_context(self):
        """대화 컨텍스트 초기화"""
        self.context = ConversationContext()
        logger.info("대화 컨텍스트가 초기화되었습니다")
    
    def set_routing_config(self, 
                          min_interval_minutes: int = 2,
                          continuity_threshold: float = 0.7,
                          switch_penalty: float = 0.15):
        """라우팅 설정 변경"""
        self.min_routing_interval = timedelta(minutes=min_interval_minutes)
        self.context_continuity_threshold = continuity_threshold
        self.agent_switch_penalty = switch_penalty
        logger.info(f"라우팅 설정 변경: interval={min_interval_minutes}분, threshold={continuity_threshold}, penalty={switch_penalty}")
