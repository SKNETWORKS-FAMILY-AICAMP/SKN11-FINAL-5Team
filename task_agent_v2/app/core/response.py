"""
TinkerBell 프로젝트 - 표준화된 응답 형식
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

class BaseResponse(BaseModel):
    """기본 응답 모델"""
    success: bool = Field(description="요청 성공 여부")
    message: str = Field(description="응답 메시지")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")
    
class SuccessResponse(BaseResponse):
    """성공 응답 모델"""
    success: bool = Field(default=True)
    data: Optional[Any] = Field(default=None, description="응답 데이터")

class ErrorResponse(BaseResponse):
    """오류 응답 모델"""
    success: bool = Field(default=False)
    error_code: str = Field(description="오류 코드")
    details: Optional[Dict[str, Any]] = Field(default=None, description="오류 상세 정보")

class PaginatedResponse(SuccessResponse):
    """페이지네이션 응답 모델"""
    pagination: Dict[str, Any] = Field(description="페이지네이션 정보")

class QueryResponse(BaseModel):
    """쿼리 응답 모델"""
    status: str = Field(description="응답 상태")
    response: str = Field(description="응답 내용")
    conversation_id: str = Field(description="대화 ID")
    intent: str = Field(description="사용자 의도")
    urgency: str = Field(description="긴급도")
    confidence: float = Field(description="신뢰도")
    actions: Optional[List[Dict[str, Any]]] = Field(default=None, description="후속 액션")
    knowledge_sources: Optional[List[str]] = Field(default=None, description="지식 소스")

class ResponseFormatter:
    """응답 포맷터 클래스"""
    
    @staticmethod
    def success(
        data: Any = None, 
        message: str = "요청이 성공적으로 처리되었습니다."
    ) -> Dict[str, Any]:
        """성공 응답 생성"""
        return SuccessResponse(
            message=message,
            data=data
        ).dict()
    
    @staticmethod
    def error(
        message: str,
        error_code: str = "GENERAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """오류 응답 생성"""
        return ErrorResponse(
            message=message,
            error_code=error_code,
            details=details
        ).dict()
    
    @staticmethod
    def paginated(
        items: List[Any],
        page: int,
        per_page: int,
        total: int,
        message: str = "데이터를 성공적으로 조회했습니다."
    ) -> Dict[str, Any]:
        """페이지네이션 응답 생성"""
        total_pages = (total + per_page - 1) // per_page
        
        return PaginatedResponse(
            message=message,
            data=items,
            pagination={
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        ).dict()
    
    @staticmethod
    def query_response(
        response_text: str,
        conversation_id: str,
        intent: str = "general_inquiry",
        urgency: str = "medium", 
        confidence: float = 0.8,
        status: str = "success",
        actions: Optional[List[Dict[str, Any]]] = None,
        knowledge_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """쿼리 응답 생성"""
        return QueryResponse(
            status=status,
            response=response_text,
            conversation_id=conversation_id,
            intent=intent,
            urgency=urgency,
            confidence=confidence,
            actions=actions or [],
            knowledge_sources=knowledge_sources or []
        ).dict()
    
    @staticmethod
    def automation_response(
        task_id: int,
        task_type: str,
        status: str = "created",
        message: str = "자동화 작업이 생성되었습니다."
    ) -> Dict[str, Any]:
        """자동화 작업 응답 생성"""
        return ResponseFormatter.success(
            data={
                "task_id": task_id,
                "task_type": task_type,
                "status": status
            },
            message=message
        )
    
    @staticmethod
    def health_response(
        status: str = "healthy",
        components: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """헬스체크 응답 생성"""
        return ResponseFormatter.success(
            data={
                "status": status,
                "components": components or {},
                "timestamp": datetime.now().isoformat()
            },
            message="시스템 상태가 정상입니다." if status == "healthy" else "시스템에 문제가 있습니다."
        )

# 하위 호환성을 위한 별칭들
def success_response(data: Any = None, message: str = "성공") -> Dict[str, Any]:
    """성공 응답 (하위 호환성)"""
    return ResponseFormatter.success(data, message)

def error_response(message: str, code: str = "ERROR") -> Dict[str, Any]:
    """오류 응답 (하위 호환성)"""
    return ResponseFormatter.error(message, code)

def paginated_response(items: List, page: int, per_page: int, total: int) -> Dict[str, Any]:
    """페이지네이션 응답 (하위 호환성)"""
    return ResponseFormatter.paginated(items, page, per_page, total)
