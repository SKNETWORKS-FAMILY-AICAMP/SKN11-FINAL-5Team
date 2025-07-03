"""
TinkerBell 프로젝트 - 시스템 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime

from ..core.dependencies import check_system_health, validate_environment
from ..core.response import ResponseFormatter
from ..core.config import config
from ..schemas.base import HealthResponse

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/system", tags=["system"])

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """시스템 헬스체크"""
    try:
        health_status = await check_system_health()
        
        # 전체 상태 결정
        overall_status = "healthy"
        if not all(health_status.get("api_keys", {}).values()):
            overall_status = "warning"
        
        # API 키 상태 세부 정보
        api_status = health_status.get("api_keys", {})
        missing_keys = [key for key, status in api_status.items() if not status]
        
        components = {
            "database": health_status.get("database", "unknown"),
            "llm": health_status.get("llm", "unknown"),
            "vector_db": health_status.get("vector_db", "unknown"),
            "api_keys": {
                "configured": api_status,
                "missing": missing_keys
            }
        }
        
        return ResponseFormatter.health_response(
            status=overall_status,
            components=components
        )
        
    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        return ResponseFormatter.health_response(
            status="unhealthy",
            components={"error": str(e)}
        )

@router.get("/status", response_model=Dict[str, Any])
async def get_system_status():
    """상세 시스템 상태 조회"""
    try:
        # 환경 설정 검증
        validate_environment()
        
        # 시스템 정보
        system_info = {
            "service": "TinkerBell",
            "version": "1.0.0",
            "environment": config.environment.value,
            "timestamp": datetime.now().isoformat(),
            "uptime": "정보 없음",  # 실제로는 프로세스 시작 시간 계산
        }
        
        # 설정 정보
        configuration = {
            "database": {
                "mysql_configured": bool(config.database.mysql_url),
                "redis_configured": bool(config.database.redis_url),
                "chroma_configured": bool(config.database.chroma_persist_dir)
            },
            "llm": {
                "openai_configured": bool(config.llm.openai_api_key),
                "google_configured": bool(config.llm.google_api_key),
                "default_model": "gemini" if config.llm.google_api_key else "gpt"
            }
            # },
            # "external_apis": {
            #     "slack_configured": bool(config.external_api.slack_bot_token),
            #     "google_calendar_configured": bool(
            #         config.external_api.google_calendar_client_id and 
            #         config.external_api.google_calendar_client_secret
            #     )
            # }
        }
        
        # 리소스 정보 (실제로는 더 상세한 모니터링 필요)
        resources = {
            "memory": "정보 없음",
            "cpu": "정보 없음",
            "disk": "정보 없음"
        }
        
        return ResponseFormatter.success(
            data={
                "system": system_info,
                "configuration": configuration,
                "resources": resources
            },
            message="시스템 상태 조회 완료"
        )
        
    except Exception as e:
        logger.error(f"시스템 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="시스템 상태 조회 중 오류가 발생했습니다.")

@router.get("/config", response_model=Dict[str, Any])
async def get_system_config():
    """시스템 설정 정보 조회 (민감한 정보 제외)"""
    try:
        # 민감하지 않은 설정 정보만 반환
        safe_config = {
            "project": {
                "name": "TinkerBell",
                "version": "1.0.0",
                "environment": "development"
            },
            "server": {
                "host": config.server.host,
                "port": config.server.port,
                "debug": config.server.debug,
                "log_level": config.server.log_level
            },
            "llm": {
                "gpt_model": config.llm.gpt_model,
                "gemini_model": config.llm.gemini_model,
                "embedding_model": config.llm.embedding_model,
                "temperature": config.llm.temperature,
                "max_tokens": config.llm.max_tokens
            },
            "rag": {
                "chunk_size": config.rag.chunk_size,
                "overlap_size": config.rag.overlap_size,
                "max_search_results": config.rag.max_search_results,
                "similarity_threshold": config.rag.similarity_threshold
            },
            "automation": {
                "max_concurrent_tasks": config.automation.max_concurrent_tasks,
                "task_timeout_minutes": config.automation.task_timeout_minutes,
                "retry_attempts": config.automation.retry_attempts,
                "cleanup_interval_hours": config.automation.cleanup_interval_hours
            }
        }
        
        return ResponseFormatter.success(
            data=safe_config,
            message="시스템 설정 조회 완료"
        )
        
    except Exception as e:
        logger.error(f"시스템 설정 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="시스템 설정 조회 중 오류가 발생했습니다.")

@router.get("/version", response_model=Dict[str, Any])
async def get_version():
    """버전 정보 조회"""
    try:
        version_info = {
            "version": "1.0.0",
            "project": "TinkerBell",
            "environment": "development",
            "build_date": "정보 없음",  # 실제 빌드 시 설정
            "commit_hash": "정보 없음",  # Git 커밋 해시
            "python_version": "3.11+",
            "dependencies": {
                "fastapi": "0.104.1",
                "langchain": "0.1.0",
                "pydantic": "2.5.0"
            }
        }
        
        return ResponseFormatter.success(
            data=version_info,
            message="버전 정보 조회 완료"
        )
        
    except Exception as e:
        logger.error(f"버전 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="버전 정보 조회 중 오류가 발생했습니다.")

@router.post("/maintenance", response_model=Dict[str, Any])
async def toggle_maintenance_mode(enabled: bool):
    """유지보수 모드 토글 (관리자 전용)"""
    try:
        # 실제로는 Redis나 데이터베이스에 상태 저장
        logger.info(f"유지보수 모드 {'활성화' if enabled else '비활성화'}")
        
        return ResponseFormatter.success(
            data={"maintenance_mode": enabled},
            message=f"유지보수 모드가 {'활성화' if enabled else '비활성화'}되었습니다."
        )
        
    except Exception as e:
        logger.error(f"유지보수 모드 토글 실패: {e}")
        raise HTTPException(status_code=500, detail="유지보수 모드 변경 중 오류가 발생했습니다.")

@router.get("/metrics", response_model=Dict[str, Any])
async def get_system_metrics():
    """시스템 메트릭 조회"""
    try:
        # 실제로는 Prometheus, Grafana 등과 연동
        metrics = {
            "requests": {
                "total": 0,
                "success": 0,
                "error": 0,
                "rate_per_minute": 0
            },
            "response_times": {
                "avg": 0,
                "p95": 0,
                "p99": 0
            },
            "users": {
                "active": 0,
                "total": 0
            },
            "tasks": {
                "created_today": 0,
                "completed_today": 0,
                "pending": 0
            },
            "automation": {
                "successful_tasks": 0,
                "failed_tasks": 0,
                "queued_tasks": 0
            }
        }
        
        return ResponseFormatter.success(
            data=metrics,
            message="시스템 메트릭 조회 완료"
        )
        
    except Exception as e:
        logger.error(f"시스템 메트릭 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="시스템 메트릭 조회 중 오류가 발생했습니다.")

@router.post("/cache/clear", response_model=Dict[str, Any])
async def clear_system_cache():
    """전체 시스템 캐시 클리어 (관리자 전용)"""
    try:
        # 각 서비스의 캐시 클리어
        cleared_caches = []
        
        # 에이전트 캐시 클리어
        try:
            from ..services.agent_service import AgentService
            agent_service = AgentService()
            if hasattr(agent_service, 'cache_manager'):
                agent_service.cache_manager.clear()
                cleared_caches.append("agent_cache")
        except Exception as e:
            logger.warning(f"에이전트 캐시 클리어 실패: {e}")
        
        # Redis 캐시 클리어 (구현 필요)
        # cleared_caches.append("redis_cache")
        
        return ResponseFormatter.success(
            data={"cleared_caches": cleared_caches},
            message="시스템 캐시가 클리어되었습니다."
        )
        
    except Exception as e:
        logger.error(f"시스템 캐시 클리어 실패: {e}")
        raise HTTPException(status_code=500, detail="시스템 캐시 클리어 중 오류가 발생했습니다.")

@router.get("/logs", response_model=Dict[str, Any])
async def get_system_logs(
    level: str = "INFO",
    limit: int = 100,
    offset: int = 0
):
    """시스템 로그 조회 (관리자 전용)"""
    try:
        # 실제로는 로그 파일이나 중앙 로깅 시스템에서 조회
        logs = []
        
        # 임시 로그 데이터
        sample_logs = [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "logger": "app.api.agent",
                "message": "쿼리 처리 완료: conversation_id=123",
                "user_id": "1"
            }
        ]
        
        return ResponseFormatter.paginated(
            items=sample_logs,
            page=(offset // limit) + 1,
            per_page=limit,
            total=len(sample_logs)
        )
        
    except Exception as e:
        logger.error(f"시스템 로그 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="시스템 로그 조회 중 오류가 발생했습니다.")
