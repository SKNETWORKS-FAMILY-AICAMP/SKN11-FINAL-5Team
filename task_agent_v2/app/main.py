"""
TinkerBell 프로젝트 - 메인 FastAPI 애플리케이션
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler

from .core.config import config
from .core.exceptions import TinkerBellException, to_http_exception
from .core.response import ResponseFormatter
from .core.dependencies import validate_environment

# API 라우터들 임포트
from .api import (
    agent, automation, users, 
    conversations, feedback, system
)

# 기존 모듈들 (추후 완전히 리팩토링)
from .core.utils import LoggingUtils
from .core.db.database import init_database

# 로깅 설정
LoggingUtils.setup_logging(config.server.log_level)
logger = logging.getLogger(__name__)

# 애플리케이션 생명주기 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 이벤트 관리"""
    # 시작 시 실행
    logger.info(f"애플리케이션 시작")
    
    try:
        # 환경 설정 검증
        validate_environment()
        logger.info("환경 설정 검증 완료")
        
        # 데이터베이스 초기화
        init_database()
        logger.info("데이터베이스 초기화 완료")
        
        # 서비스 초기화 (필요시)
        logger.info("서비스 초기화 완료")
        
    except Exception as e:
        logger.error(f"애플리케이션 초기화 실패: {e}")
        raise RuntimeError(f"초기화 실패: {e}")
    
    yield  # 애플리케이션 실행
    
    # 종료 시 실행
    logger.info(f"애플리케이션 종료")
    
    try:
        # 리소스 정리
        logger.info("리소스 정리 완료")
    except Exception as e:
        logger.error(f"리소스 정리 실패: {e}")

# FastAPI 애플리케이션 생성
def create_app() -> FastAPI:
    """FastAPI 애플리케이션 팩토리"""
    
    app = FastAPI(
        title=f"업무지원 에이전트",
        description="1인 창업자를 위한 AI 기반 업무지원 시스템",
        version="1.0.0",
        lifespan=lifespan,
        debug=config.server.debug,
        docs_url="/docs" if not config.is_production else None,
        redoc_url="/redoc" if not config.is_production else None
    )
    
    # CORS 미들웨어 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.server.cors_origins,
        allow_credentials=True,
        allow_methods=config.server.cors_methods,
        allow_headers=config.server.cors_headers,
    )
    
    # API 라우터 등록
    app.include_router(agent.router)
    app.include_router(automation.router)
    app.include_router(users.router)
    app.include_router(conversations.router)
    app.include_router(feedback.router)
    app.include_router(system.router)
    
    # 예외 핸들러 등록
    register_exception_handlers(app)
    
    # 기본 라우트 등록
    register_basic_routes(app)
    
    return app

def register_exception_handlers(app: FastAPI):
    """예외 핸들러 등록"""
    
    @app.exception_handler(TinkerBellException)
    async def tinkerbell_exception_handler(request, exc: TinkerBellException):
        """TinkerBell 커스텀 예외 처리"""
        logger.error(f"TinkerBell 예외: {exc.message}, 코드: {exc.error_code}")
        return JSONResponse(
            status_code=500,
            content=ResponseFormatter.error(
                message=exc.message,
                error_code=exc.error_code,
                details=exc.details
            )
        )
    
    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(request, exc: HTTPException):
        """HTTP 예외 처리"""
        logger.error(f"HTTP 예외: {exc.status_code} - {exc.detail}")
        
        # 표준화된 오류 응답 형식 사용
        if isinstance(exc.detail, dict):
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail
            )
        else:
            return JSONResponse(
                status_code=exc.status_code,
                content=ResponseFormatter.error(
                    message=str(exc.detail),
                    error_code=f"HTTP_{exc.status_code}"
                )
            )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        """일반 예외 처리"""
        logger.error(f"처리되지 않은 예외: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=ResponseFormatter.error(
                message="내부 서버 오류가 발생했습니다.",
                error_code="INTERNAL_SERVER_ERROR"
            )
        )

def register_basic_routes(app: FastAPI):
    """기본 라우트 등록"""
    
    @app.get("/")
    async def root():
        """루트 엔드포인트"""
        return ResponseFormatter.success(
            data={
                "service": "TinkerBell 업무지원 에이전트",
                "version": "1.0.0",
                "environment": config.environment.value,
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "documentation": "/docs" if not config.is_production else "disabled"
            },
            message=f"API 서버가 정상 작동 중입니다."
        )
    
    @app.get("/health")
    async def health_check():
        """간단한 헬스체크 (시스템 API와 별도)"""
        return ResponseFormatter.success(
            data={
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": config.version
            },
            message="서비스가 정상 작동 중입니다."
        )
    
    @app.get("/version")
    async def get_version():
        """버전 정보"""
        return ResponseFormatter.success(
            data={
                "version": config.version,
                "environment": config.environment.value,
                "build_date": datetime.now().isoformat()  # 실제로는 빌드 시간
            }
        )

# 애플리케이션 인스턴스 생성
app = create_app()

# 개발 환경에서만 사용할 추가 라우트
if config.is_development:
    
    @app.get("/debug/config")
    async def debug_config():
        """개발용 설정 정보 확인"""
        return {
            "config": {
                "environment": config.environment.value,
                "debug": config.server.debug,
                "log_level": config.server.log_level,
                "api_keys_configured": config.validate_api_keys()
            }
        }
    
    @app.post("/debug/test-error")
    async def debug_test_error():
        """개발용 에러 테스트"""
        raise TinkerBellException("테스트 에러입니다.", "TEST_ERROR")

# 애플리케이션 메타데이터
app.state.config = config
app.state.start_time = datetime.now()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.is_development,
        log_level=config.server.log_level.lower(),
        access_log=True
    )
