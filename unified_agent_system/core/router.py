"""
라우팅 로직 - 사용자 질의를 분석하여 적절한 에이전트 결정
"""

import re
import logging
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from .models import AgentType, RoutingDecision, Priority, UnifiedRequest
from .config import OPENAI_API_KEY, GEMINI_API_KEY, get_system_config
import sys
import os

# 공통 모듈 경로 추가
# sys.path.append(os.path.join(os.path.dirname(__file__), "../shared_modules"))
# 템플릿 관련 imports 추가
from shared_modules.database import DatabaseManager
import shared_modules.queries
from .models import (
    TemplateCreate, TemplateUpdate, TemplateResponse, 
    TemplateListResponse, TemplateOperationResponse
)

logger = logging.getLogger(__name__)


class QueryRouter:
    """사용자 질의를 분석하여 적절한 에이전트로 라우팅하는 클래스"""
    
    def __init__(self):
        self.config = get_system_config()
        self.llm = self._initialize_llm()
        self._create_routing_prompt()
    
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
    
    async def route_query(self, request: UnifiedRequest) -> RoutingDecision:
        """사용자 질의를 라우팅합니다"""
        try:
            # 1. 선호 에이전트가 지정된 경우
            if request.preferred_agent:
                return RoutingDecision(
                    agent_type=request.preferred_agent,
                    confidence=1.0,
                    reasoning="사용자가 직접 지정한 에이전트",
                    keywords=[],
                    priority=Priority.MEDIUM
                )
            
            # 2. 키워드 기반 빠른 매칭 시도
            quick_match = self._quick_keyword_match(request.message)
            if quick_match and quick_match.confidence >= 0.9:
                logger.info(f"키워드 기반 빠른 매칭 성공: {quick_match.agent_type}")
                return quick_match
            
            # 3. LLM 기반 라우팅
            llm_decision = await self._llm_based_routing(request.message)
            
            # 4. 신뢰도가 낮으면 기본 에이전트 사용
            if llm_decision.confidence < self.config.routing_confidence_threshold:
                logger.warning(f"라우팅 신뢰도 낮음: {llm_decision.confidence}")
                llm_decision.agent_type = self.config.default_agent
                llm_decision.reasoning += " (신뢰도 낮음으로 기본 에이전트 사용)"
            
            return llm_decision
            
        except Exception as e:
            logger.error(f"라우팅 실패: {e}")
            return RoutingDecision(
                agent_type=self.config.default_agent,
                confidence=0.5,
                reasoning=f"라우팅 오류로 기본 에이전트 사용: {str(e)}",
                keywords=[],
                priority=Priority.MEDIUM
            )
    
    def _quick_keyword_match(self, query: str) -> Optional[RoutingDecision]:
        """키워드 기반 빠른 매칭"""
        query_lower = query.lower()
        matches = {}
        
        for agent_type, config in self.config.agents.items():
            match_count = 0
            matched_keywords = []
            
            for keyword in config.keywords:
                if keyword in query_lower:
                    match_count += 1
                    matched_keywords.append(keyword)
            
            if match_count > 0:
                # 키워드 매칭 점수 계산 (매칭된 키워드 수 / 전체 키워드 수)
                score = match_count / len(config.keywords)
                matches[agent_type] = {
                    'score': score,
                    'count': match_count,
                    'keywords': matched_keywords
                }
        
        if not matches:
            return None
        
        # 가장 높은 점수의 에이전트 선택
        best_agent = max(matches.keys(), key=lambda x: matches[x]['score'])
        best_match = matches[best_agent]
        
        # 높은 신뢰도 조건: 여러 키워드 매칭 + 상위 점수
        confidence = min(0.9, best_match['score'] * 2 + (best_match['count'] * 0.1))
        
        if confidence >= 0.7:  # 임계값 이상일 때만 반환
            priority = Priority.HIGH if best_match['count'] >= 3 else Priority.MEDIUM
            
            return RoutingDecision(
                agent_type=best_agent,
                confidence=confidence,
                reasoning=f"키워드 매칭: {', '.join(best_match['keywords'][:3])}",
                keywords=best_match['keywords'][:5],
                priority=priority
            )
        
        return None
    
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
    
# FastAPI 라우터 생성
template_router = APIRouter(prefix="/templates", tags=["templates"])

# 데이터베이스 의존성
def get_db():
    """데이터베이스 세션 의존성"""
    db_manager = DatabaseManager()
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()

def get_current_user_id(db: Session = Depends(get_db)) -> int:
    """현재 사용자 ID 반환 (실제 구현에서는 JWT 토큰에서 추출)"""
    # TODO: JWT 토큰 파싱 로직으로 교체 필요
    # 임시로 테스트용 user_id 반환
    return 1

@template_router.get("/", response_model=TemplateListResponse)
async def get_user_templates(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """사용자 템플릿 목록 조회 (기본 + 커스텀)"""
    try:
        logger.info(f"사용자 {user_id} 템플릿 목록 조회 시작")
        
        templates_data = queries.get_user_templates_with_defaults(db, user_id)
        
        templates = []
        for template_data in templates_data:
            template = TemplateResponse(
                template_id=template_data["template_id"],
                user_id=template_data["user_id"],
                title=template_data["title"],
                content=template_data["content"],
                template_type=template_data["template_type"],
                channel_type=template_data["channel_type"],
                content_type=template_data.get("content_type"),
                created_at=template_data["created_at"],
                is_custom=template_data["is_custom"]
            )
            templates.append(template)
        
        logger.info(f"사용자 {user_id} 템플릿 {len(templates)}개 조회 완료")
        
        return TemplateListResponse(
            templates=templates,
            total_count=len(templates)
        )
        
    except Exception as e:
        logger.error(f"템플릿 목록 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="템플릿 목록을 불러오는데 실패했습니다."
        )

@template_router.put("/{template_id}", response_model=TemplateOperationResponse)
async def update_template(
    template_id: int,
    template_update: TemplateUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """템플릿 수정"""
    try:
        logger.info(f"사용자 {user_id} 템플릿 {template_id} 수정 시작")
        
        # 1. 기존 템플릿 조회
        existing_template = queries.get_template_with_ownership_check(db, template_id, user_id)
        if not existing_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="템플릿을 찾을 수 없습니다."
            )
        
        # 2. 기본 템플릿 수정 시 커스텀 템플릿 생성
        if not existing_template["is_custom"]:  # 기본 템플릿인 경우
            logger.info(f"기본 템플릿 {template_id} 를 커스텀 템플릿으로 복사")
            copied_template = queries.copy_default_template_to_user(db, user_id, template_id)
            
            if not copied_template:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="커스텀 템플릿 생성에 실패했습니다."
                )
            
            template_id = copied_template["template_id"]
        
        # 3. 템플릿 업데이트
        update_data = {k: v for k, v in template_update.dict().items() if v is not None}
        if update_data:
            success = queries.update_user_template(db, template_id, user_id, **update_data)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="템플릿 수정에 실패했습니다."
                )
        
        # 4. 수정된 템플릿 조회
        updated_template_data = queries.get_template_with_ownership_check(db, template_id, user_id)
        updated_template = TemplateResponse(**updated_template_data)
        
        return TemplateOperationResponse(
            success=True,
            message="템플릿이 성공적으로 수정되었습니다.",
            template=updated_template
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"템플릿 수정 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="템플릿 수정에 실패했습니다."
        )

@template_router.post("/", response_model=TemplateOperationResponse)
async def create_template(
    template: TemplateCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """새 커스텀 템플릿 생성"""
    try:
        logger.info(f"사용자 {user_id} 새 템플릿 생성: {template.title}")
        
        template_obj = queries.create_template_message(
            db=db,
            user_id=user_id,
            template_type=template.template_type,
            channel_type=template.channel_type,
            title=template.title,
            content=template.content,
            content_type=template.content_type
        )
        
        if not template_obj:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="템플릿 생성에 실패했습니다."
            )
        
        created_template = TemplateResponse(
            template_id=template_obj.template_id,
            user_id=template_obj.user_id,
            title=template_obj.title,
            content=template_obj.content,
            template_type=template_obj.template_type,
            channel_type=template_obj.channel_type,
            content_type=template_obj.content_type,
            created_at=template_obj.created_at,
            is_custom=True
        )
        
        return TemplateOperationResponse(
            success=True,
            message="템플릿이 성공적으로 생성되었습니다.",
            template=created_template
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"템플릿 생성 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="템플릿 생성에 실패했습니다."
        )

@template_router.delete("/{template_id}", response_model=TemplateOperationResponse)
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """커스텀 템플릿 삭제"""
    try:
        logger.info(f"사용자 {user_id} 템플릿 {template_id} 삭제 시작")
        
        template_data = queries.get_template_with_ownership_check(db, template_id, user_id)
        if not template_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="템플릿을 찾을 수 없습니다."
            )
        
        if not template_data["is_custom"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="기본 템플릿은 삭제할 수 없습니다."
            )
        
        success = queries.delete_user_template(db, template_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="템플릿 삭제에 실패했습니다."
            )
        
        return TemplateOperationResponse(
            success=True,
            message="템플릿이 성공적으로 삭제되었습니다."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"템플릿 삭제 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="템플릿 삭제에 실패했습니다."
        )

# ==================== 메인 라우터 생성 ====================

def create_api_router():
    """모든 라우터를 포함하는 메인 API 라우터 생성"""
    main_router = APIRouter()
    
    # 템플릿 라우터 등록
    main_router.include_router(template_router)
    
    # 다른 라우터들도 여기에 추가
    # main_router.include_router(user_router)
    # main_router.include_router(chat_router)
    
    return main_router

# main.py에서 사용할 라우터
api_router = create_api_router()