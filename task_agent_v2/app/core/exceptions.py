"""
TinkerBell 프로젝트 - 표준화된 예외 처리
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class TinkerBellException(Exception):
    """기본 TinkerBell 예외"""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "GENERAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(TinkerBellException):
    """입력 검증 오류"""
    
    def __init__(self, message: str, field: str = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field": field, **(details or {})}
        )

class LLMError(TinkerBellException):
    """LLM 처리 오류"""
    
    def __init__(self, message: str, model_name: str = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="LLM_ERROR",
            details={"model": model_name, **(details or {})}
        )

class AutomationError(TinkerBellException):
    """자동화 작업 오류"""
    
    def __init__(self, message: str, task_type: str = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTOMATION_ERROR",
            details={"task_type": task_type, **(details or {})}
        )

class DatabaseError(TinkerBellException):
    """데이터베이스 오류"""
    
    def __init__(self, message: str, operation: str = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details={"operation": operation, **(details or {})}
        )

class RAGError(TinkerBellException):
    """RAG 시스템 오류"""
    
    def __init__(self, message: str, operation: str = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RAG_ERROR",
            details={"operation": operation, **(details or {})}
        )

class ConfigurationError(TinkerBellException):
    """설정 오류"""
    
    def __init__(self, message: str, config_key: str = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details={"config_key": config_key, **(details or {})}
        )

class ExternalAPIError(TinkerBellException):
    """외부 API 호출 오류"""
    
    def __init__(self, message: str, api_name: str = None, status_code: int = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="EXTERNAL_API_ERROR",
            details={"api_name": api_name, "status_code": status_code, **(details or {})}
        )

# HTTP 예외 변환 함수들
def to_http_exception(error: TinkerBellException) -> HTTPException:
    """TinkerBell 예외를 HTTP 예외로 변환"""
    
    status_map = {
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "LLM_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "AUTOMATION_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "RAG_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "CONFIGURATION_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "EXTERNAL_API_ERROR": status.HTTP_502_BAD_GATEWAY,
        "GENERAL_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR
    }
    
    status_code = status_map.get(error.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return HTTPException(
        status_code=status_code,
        detail={
            "error_code": error.error_code,
            "message": error.message,
            "details": error.details
        }
    )

def validation_error(message: str, field: str = None) -> HTTPException:
    """검증 오류 생성"""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error_code": "VALIDATION_ERROR",
            "message": message,
            "field": field
        }
    )

def not_found_error(resource: str, resource_id: str = None) -> HTTPException:
    """리소스 없음 오류 생성"""
    message = f"{resource}을(를) 찾을 수 없습니다."
    if resource_id:
        message += f" (ID: {resource_id})"
    
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error_code": "NOT_FOUND",
            "message": message,
            "resource": resource,
            "resource_id": resource_id
        }
    )

def permission_error(message: str = "권한이 없습니다.") -> HTTPException:
    """권한 오류 생성"""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "error_code": "PERMISSION_DENIED",
            "message": message
        }
    )

def internal_server_error(message: str = "내부 서버 오류가 발생했습니다.") -> HTTPException:
    """내부 서버 오류 생성"""
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": message
        }
    )
