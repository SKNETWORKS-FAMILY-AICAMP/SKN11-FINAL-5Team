"""
통합 에이전트 시스템 메인 FastAPI 애플리케이션
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from core.models import (
    UnifiedRequest, UnifiedResponse, HealthCheck, 
    AgentType, RoutingDecision
)
from core.workflow import get_workflow
from core.config import (
    SERVER_HOST, SERVER_PORT, DEBUG_MODE, 
    LOG_LEVEL, LOG_FORMAT
)

# 로깅 설정
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 라이프사이클 함수"""
    # 시작 시
    logger.info("통합 에이전트 시스템 시작")
    workflow = get_workflow()
    
    # 에이전트 상태 확인
    status = await workflow.get_workflow_status()
    logger.info(f"활성 에이전트: {status['active_agents']}/{status['total_agents']}")
    
    yield
    
    # 종료 시
    logger.info("통합 에이전트 시스템 종료")
    await workflow.cleanup()


# FastAPI 앱 생성
app = FastAPI(
    title="통합 에이전트 시스템",
    description="5개의 전문 에이전트를 통합한 AI 상담 시스템",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/test-ui")
async def test_ui():
    """테스트 웹 인터페이스 제공"""
    return FileResponse("web_interface.html")

@app.get("/", response_class=HTMLResponse)
async def root():
    """루트 페이지"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>통합 에이전트 시스템</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .agent { 
                border: 1px solid #ddd; 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 8px;
                background: #f9f9f9;
            }
            .status { color: green; font-weight: bold; }
            .endpoint { font-family: monospace; background: #f0f0f0; padding: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 통합 에이전트 시스템</h1>
            <p>5개의 전문 에이전트를 통합한 AI 상담 시스템입니다.</p>
            
            <h2>📋 지원하는 에이전트</h2>
            <div class="agent">
                <h3>💼 비즈니스 플래닝 에이전트</h3>
                <p>창업 준비, 사업 계획, 시장 조사, 투자 유치 등</p>
            </div>
            
            <div class="agent">
                <h3>🤝 고객 서비스 에이전트</h3>
                <p>고객 관리, 서비스 개선, 고객 만족도 향상 등</p>
            </div>
            
            <div class="agent">
                <h3>📢 마케팅 에이전트</h3>
                <p>마케팅 전략, SNS 마케팅, 브랜딩, 광고 등</p>
            </div>
            
            <div class="agent">
                <h3>🧠 멘탈 헬스 에이전트</h3>
                <p>스트레스 관리, 심리 상담, 멘탈 케어 등</p>
            </div>
            
            <div class="agent">
                <h3>⚡ 업무 자동화 에이전트</h3>
                <p>일정 관리, 이메일 자동화, 생산성 도구 등</p>
            </div>
            
            <h2>🔗 주요 API 엔드포인트</h2>
            <p><span class="endpoint">POST /query</span> - 통합 질의 처리</p>
            <p><span class="endpoint">GET /health</span> - 시스템 상태 확인</p>
            <p><span class="endpoint">GET /docs</span> - API 문서</p>
            <p><span class="endpoint">GET /test-ui</span> - 웹 테스트 인터페이스</p>
            
            <h2>📊 시스템 상태</h2>
            <p class="status">✅ 서비스 정상 운영 중</p>
        </div>
    </body>
    </html>
    """


@app.post("/query", response_model=UnifiedResponse)
async def process_query(request: UnifiedRequest):
    """통합 질의 처리"""
    try:
        logger.info(f"사용자 {request.user_id}: {request.message[:50]}...")
        
        workflow = get_workflow()
        response = await workflow.process_request(request)
        
        logger.info(f"응답 완료: {response.agent_type} (신뢰도: {response.confidence:.2f})")
        
        return response
        
    except Exception as e:
        logger.error(f"질의 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"처리 중 오류가 발생했습니다: {str(e)}")


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """시스템 상태 확인"""
    try:
        workflow = get_workflow()
        status = await workflow.get_workflow_status()
        
        return HealthCheck(
            status="healthy",
            agents=status["agent_health"],
            system_info={
                "active_agents": status["active_agents"],
                "total_agents": status["total_agents"],
                "workflow_version": status["workflow_version"],
                "multi_agent_enabled": status["config"]["enable_multi_agent"]
            }
        )
        
    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        raise HTTPException(status_code=503, detail=f"시스템 상태 확인 실패: {str(e)}")


@app.get("/agents", response_model=Dict[str, Any])
async def get_agents_info():
    """에이전트 정보 조회"""
    try:
        workflow = get_workflow()
        status = await workflow.get_workflow_status()
        
        return {
            "total_agents": status["total_agents"],
            "active_agents": status["active_agents"],
            "agent_status": status["agent_health"],
            "agent_types": [agent.value for agent in AgentType if agent != AgentType.UNKNOWN]
        }
        
    except Exception as e:
        logger.error(f"에이전트 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/route", response_model=RoutingDecision)
async def route_query(message: str, user_id: int = 1):
    """질의 라우팅 테스트 (디버깅용)"""
    try:
        request = UnifiedRequest(user_id=user_id, message=message)
        workflow = get_workflow()
        routing_decision = await workflow.router.route_query(request)
        
        return routing_decision
        
    except Exception as e:
        logger.error(f"라우팅 테스트 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/{agent_type}/health")
async def check_agent_health(agent_type: AgentType):
    """특정 에이전트 상태 확인"""
    try:
        workflow = get_workflow()
        agent_health = await workflow.agent_manager.health_check_all()
        
        if agent_type not in agent_health:
            raise HTTPException(status_code=404, detail="에이전트를 찾을 수 없습니다")
        
        return {
            "agent_type": agent_type.value,
            "status": "healthy" if agent_health[agent_type] else "unhealthy",
            "available": agent_health[agent_type]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"에이전트 상태 확인 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test")
async def test_system():
    """시스템 통합 테스트"""
    test_queries = [
        ("사업계획서 작성 방법을 알려주세요", AgentType.BUSINESS_PLANNING),
        ("고객 불만 처리 방법은?", AgentType.CUSTOMER_SERVICE),
        ("SNS 마케팅 전략을 추천해주세요", AgentType.MARKETING),
        ("요즘 스트레스가 심해요", AgentType.MENTAL_HEALTH),
        ("회의 일정을 자동으로 잡아주세요", AgentType.TASK_AUTOMATION)
    ]
    
    results = []
    
    for query, expected_agent in test_queries:
        try:
            request = UnifiedRequest(user_id=999, message=query)
            workflow = get_workflow()
            routing_decision = await workflow.router.route_query(request)
            
            results.append({
                "query": query,
                "expected_agent": expected_agent.value,
                "routed_agent": routing_decision.agent_type.value,
                "confidence": routing_decision.confidence,
                "correct": routing_decision.agent_type == expected_agent
            })
            
        except Exception as e:
            results.append({
                "query": query,
                "expected_agent": expected_agent.value,
                "error": str(e),
                "correct": False
            })
    
    accuracy = sum(1 for r in results if r.get("correct", False)) / len(results)
    
    return {
        "test_results": results,
        "accuracy": accuracy,
        "total_tests": len(results)
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=DEBUG_MODE,
        log_level=LOG_LEVEL.lower()
    )
