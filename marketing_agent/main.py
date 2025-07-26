"""
LangGraph 기반 마케팅 에이전트 메인 실행 파일
FastAPI 기반 API 서버 + LangGraph 워크플로우
"""

import os
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# 내부 모듈 import
from config import config, create_response, get_current_timestamp
from marketing_agent import marketing_agent

# 로깅 설정
logger = config.setup_logging()

# 설정 검증
try:
    config.validate_config()
except ValueError as e:
    logger.error(f"설정 오류: {e}")
    exit(1)

# FastAPI 앱 초기화
app = FastAPI(
    title="LangGraph 마케팅 에이전트 API",
    description="LangGraph 기반 마케팅 전문 AI 어시스턴트 - 상태 기반 워크플로우",
    version=config.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청 모델 정의
class MessageRequest(BaseModel):
    """메시지 요청 모델"""
    user_id: int = Field(..., description="사용자 ID")
    message: str = Field(..., description="사용자 메시지")
    conversation_id: Optional[int] = Field(None, description="대화 ID (기존 대화 계속 시)")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 12345,
                "message": "카페 마케팅을 시작하고 싶어요",
                "conversation_id": 67890
            }
        }

class BatchRequest(BaseModel):
    """배치 요청 모델"""
    messages: List[Dict[str, Any]] = Field(..., description="메시지 리스트")
    
    class Config:
        schema_extra = {
            "example": {
                "messages": [
                    {"user_id": 123, "message": "안녕하세요"},
                    {"user_id": 123, "message": "마케팅 도와주세요"}
                ]
            }
        }

# API 엔드포인트

@app.post("/agent/query")
async def chat(request: MessageRequest):
    """메인 채팅 엔드포인트 - LangGraph 워크플로우 사용"""
    try:
        logger.info(f"LangGraph 채팅 요청: user_id={request.user_id}, message='{request.message[:50]}...'")
        
        result = await marketing_agent.batch_process([request.dict()])
        
        logger.info(f"LangGraph 채팅 응답 완료: success={result.get('success')}")
        return result
        
    except Exception as e:
        logger.error(f"LangGraph 채팅 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/conversation/{conversation_id}/status")
async def get_conversation_status(conversation_id: int):
    """대화 상태 조회"""
    try:
        status = marketing_agent.get_conversation_status(conversation_id)
        return create_response(success=True, data=status)
        
    except Exception as e:
        logger.error(f"대화 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/conversation/{conversation_id}")
async def reset_conversation(conversation_id: int):
    """대화 초기화"""
    try:
        success = await marketing_agent.reset_conversation(conversation_id)
        
        if success:
            return create_response(
                success=True, 
                data={"message": f"대화 {conversation_id}가 초기화되었습니다"}
            )
        else:
            return create_response(
                success=False,
                error="대화를 찾을 수 없습니다"
            )
            
    except Exception as e:
        logger.error(f"대화 초기화 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/batch")
async def batch_chat(request: BatchRequest, background_tasks: BackgroundTasks):
    """배치 채팅 처리"""
    try:
        if len(request.messages) > 10:  # 과부하 방지
            raise HTTPException(
                status_code=400, 
                detail="배치 요청은 최대 10개까지만 가능합니다"
            )
        
        # 작은 배치는 즉시 처리
        if len(request.messages) <= 3:
            result = await marketing_agent.batch_process(request.messages)
            return result
        
        # 큰 배치는 백그라운드 처리
        task_id = f"batch_{get_current_timestamp().replace(':', '')}"
        background_tasks.add_task(
            process_batch_background, 
            task_id, 
            request.messages
        )
        
        return create_response(
            success=True,
            data={
                "task_id": task_id,
                "message": "배치 처리가 시작되었습니다",
                "message_count": len(request.messages)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"배치 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_batch_background(task_id: str, messages: List[Dict[str, Any]]):
    """백그라운드 배치 처리"""
    try:
        logger.info(f"백그라운드 배치 처리 시작: {task_id}")
        result = await marketing_agent.batch_process(messages)
        logger.info(f"백그라운드 배치 처리 완료: {task_id}")
        # 실제로는 결과를 데이터베이스나 캐시에 저장
        
    except Exception as e:
        logger.error(f"백그라운드 배치 처리 실패: {task_id}, 오류: {e}")

@app.get("/api/v1/agent/status")
async def get_agent_status():
    """에이전트 상태 조회"""
    try:
        status = marketing_agent.get_agent_status()
        return create_response(success=True, data=status)
        
    except Exception as e:
        logger.error(f"에이전트 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# LangGraph 전용 엔드포인트들

@app.get("/api/v1/workflow/diagram")
async def get_workflow_diagram():
    """워크플로우 다이어그램 조회 (LangGraph 전용)"""
    try:
        diagram = marketing_agent.get_workflow_diagram()
        return create_response(success=True, data=diagram)
        
    except Exception as e:
        logger.error(f"워크플로우 다이어그램 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/conversation/{conversation_id}/flow-analysis")
async def get_conversation_flow_analysis(conversation_id: int):
    """대화 흐름 분석 (LangGraph 전용)"""
    try:
        analysis = marketing_agent.get_conversation_flow_analysis(conversation_id)
        return create_response(success=True, data=analysis)
        
    except Exception as e:
        logger.error(f"대화 흐름 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    try:
        agent_status = marketing_agent.get_agent_status()
        
        health_data = {
            "service": config.SERVICE_NAME,
            "version": config.VERSION,
            "status": "healthy",
            "timestamp": get_current_timestamp(),
            "workflow_engine": "langraph",
            "config": {
                "model": config.OPENAI_MODEL,
                "temperature": config.TEMPERATURE,
                "host": config.HOST,
                "port": config.PORT,
                "max_iterations": config.MAX_ITERATIONS
            },
            "langraph_features": [
                "상태 기반 워크플로우",
                "조건부 라우팅",
                "메모리 지속성",
                "에러 복구",
                "체크포인트 지원",
                "비동기 처리"
            ],
            "workflow_capabilities": [
                "다단계 마케팅 상담",
                "적응형 대화 흐름",
                "콘텐츠 자동 생성",
                "비즈니스 분석",
                "전략 기획",
                "실행 가이드"
            ]
        }
        
        return create_response(success=True, data=health_data)
        
    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": f"LangGraph 마케팅 에이전트 API v{config.VERSION}",
        "workflow_engine": "langraph",
        "docs": "/docs",
        "health": "/health",
        "workflow_diagram": "/api/v1/workflow/diagram",
        "status": "running"
    }

# 시작 이벤트
@app.on_event("startup")
async def startup_event():
    """서버 시작시 실행"""
    logger.info("=" * 70)
    logger.info(f"🚀 LangGraph 마케팅 에이전트 API v{config.VERSION} 시작")
    logger.info("=" * 70)
    logger.info("✨ LangGraph 기반 주요 개선사항:")
    logger.info("  - 🎯 상태 기반 워크플로우 관리")
    logger.info("  - 🔀 조건부 라우팅으로 유연한 대화 흐름")
    logger.info("  - 💾 메모리 기반 세션 지속성")
    logger.info("  - 🛡️ 체계적인 에러 처리 및 복구")
    logger.info("  - 📊 대화 흐름 분석 및 최적화")
    logger.info("  - ⚡ 비동기 처리로 성능 향상")
    logger.info("=" * 70)
    logger.info("📋 지원하는 마케팅 단계:")
    logger.info("  1. 초기 상담 (기본 정보 수집)")
    logger.info("  2. 목표 설정 (마케팅 목표 정의)")
    logger.info("  3. 타겟 분석 (고객층 분석)")
    logger.info("  4. 전략 기획 (마케팅 전략 수립)")
    logger.info("  5. 콘텐츠 생성 (실제 콘텐츠 제작)")
    logger.info("  6. 피드백 처리 (콘텐츠 개선)")
    logger.info("  7. 실행 가이드 (실행 방법 안내)")
    logger.info("=" * 70)
    logger.info(f"📍 서버 주소: http://{config.HOST}:{config.PORT}")
    logger.info(f"📖 API 문서: http://{config.HOST}:{config.PORT}/docs")
    logger.info(f"🔧 워크플로우 다이어그램: http://{config.HOST}:{config.PORT}/api/v1/workflow/diagram")
    logger.info("=" * 70)

# 종료 이벤트
@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료시 실행"""
    logger.info("LangGraph 마케팅 에이전트 서버 종료 중...")
    # LangGraph 워크플로우 정리 작업
    logger.info("워크플로우 세션 정리 완료")
    logger.info("서버 종료 완료")

# 개발 모드용 테스트 엔드포인트
if config.LOG_LEVEL == "DEBUG":
    @app.post("/api/v1/test/workflow")
    async def test_workflow():
        """테스트용 워크플로우 시뮬레이션"""
        test_messages = [
            "안녕하세요",
            "카페 마케팅을 시작하고 싶어요",
            "매출 증대가 목표입니다",
            "20-30대 여성 고객이 주요 타겟이에요",
            "인스타그램 포스트를 만들어주세요"
        ]
        
        results = []
        conversation_id = None
        
        for i, message in enumerate(test_messages):
            result = await marketing_agent.process_message(
                user_input=message,
                user_id=99999,
                conversation_id=conversation_id
            )
            
            if not conversation_id and result.get("success"):
                conversation_id = result["data"]["conversation_id"]
            
            results.append({
                "step": i + 1,
                "message": message,
                "response": result["data"]["answer"] if result.get("success") else result.get("error"),
                "stage": result["data"]["current_stage"] if result.get("success") else None,
                "workflow_engine": "langraph"
            })
            
            # 시뮬레이션 딜레이
            await asyncio.sleep(0.3)
        
        # 워크플로우 분석 추가
        flow_analysis = marketing_agent.get_conversation_flow_analysis(conversation_id)
        
        return create_response(
            success=True,
            data={
                "test_results": results,
                "conversation_id": conversation_id,
                "flow_analysis": flow_analysis,
                "workflow_engine": "langraph"
            }
        )
    
    @app.get("/api/v1/debug/workflow-info")
    async def debug_workflow_info():
        """워크플로우 디버그 정보"""
        try:
            agent_status = marketing_agent.get_agent_status()
            workflow_diagram = marketing_agent.get_workflow_diagram()
            
            debug_info = {
                "agent_status": agent_status,
                "workflow_diagram": workflow_diagram,
                "config": config.get_config_dict(),
                "langraph_version": "latest",
                "debug_timestamp": get_current_timestamp()
            }
            
            return create_response(success=True, data=debug_info)
            
        except Exception as e:
            logger.error(f"디버그 정보 조회 실패: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# 메인 실행부
def main():
    """메인 실행 함수"""
    logger.info("LangGraph 마케팅 에이전트 서버 시작 준비...")
    
    # 환경변수 확인
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY 환경변수가 설정되지 않았습니다")
        logger.error("export OPENAI_API_KEY='your-api-key-here'")
        exit(1)
    
    # LangGraph 워크플로우 초기화 확인
    try:
        agent_status = marketing_agent.get_agent_status()
        logger.info(f"LangGraph 워크플로우 초기화 완료: {agent_status.get('status')}")
    except Exception as e:
        logger.error(f"LangGraph 워크플로우 초기화 실패: {e}")
        exit(1)
    
    # 서버 시작
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=8003,
        reload=config.LOG_LEVEL == "DEBUG",
        log_level=config.LOG_LEVEL.lower(),
        access_log=True
    )

if __name__ == "__main__":
    main()
