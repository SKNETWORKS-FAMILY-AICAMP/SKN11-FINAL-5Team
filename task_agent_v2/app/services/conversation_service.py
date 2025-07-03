"""
TinkerBell 프로젝트 - 대화 서비스
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from ..core.exceptions import DatabaseError, ValidationError, not_found_error
from ..schemas.base import ConversationCreate, ConversationResponse, MessageCreate, MessageResponse

logger = logging.getLogger(__name__)

class ConversationService:
    """대화 관리 서비스"""
    
    def __init__(self, db: Session):
        """서비스 초기화"""
        self.db = db
    
    async def create_conversation(
        self, 
        user_id: int
    ) -> ConversationResponse:
        """대화 세션 생성"""
        try:
            # 기존 모듈 사용 (추후 리팩토링)
            from ..core.db.db_services import conversation_service
            
            with conversation_service as service:
                conversation = service.create_conversation(user_id)
                
                return ConversationResponse(
                    conversation_id=conversation.conversation_id,
                    user_id=conversation.user_id,
                    started_at=conversation.started_at,
                    ended_at=conversation.ended_at,
                    is_visible=conversation.is_visible
                )
                
        except Exception as e:
            logger.error(f"대화 세션 생성 실패: {e}")
            raise DatabaseError(f"대화 세션 생성 중 오류 발생: {e}", "create_conversation")
    
    async def get_conversation(self, conversation_id: int) -> ConversationResponse:
        """대화 세션 조회"""
        try:
            from ..core.db.db_services import conversation_service
            
            with conversation_service as service:
                conversation = service.get_conversation_by_id(conversation_id)
                
                if not conversation:
                    raise not_found_error("대화 세션", str(conversation_id))
                
                return ConversationResponse(
                    conversation_id=conversation.conversation_id,
                    user_id=conversation.user_id,
                    started_at=conversation.started_at,
                    ended_at=conversation.ended_at,
                    is_visible=conversation.is_visible
                )
                
        except Exception as e:
            if "대화 세션" in str(e):
                raise
            logger.error(f"대화 세션 조회 실패: {e}")
            raise DatabaseError(f"대화 세션 조회 중 오류 발생: {e}", "get_conversation")
    
    async def get_user_conversations(
        self, 
        user_id: int, 
        visible_only: bool = True
    ) -> List[ConversationResponse]:
        """사용자의 대화 세션 목록 조회"""
        try:
            from ..core.db.db_services import conversation_service
            
            with conversation_service as service:
                conversations = service.get_user_conversations(user_id, visible_only)
                
                return [
                    ConversationResponse(
                        conversation_id=conv.conversation_id,
                        user_id=conv.user_id,
                        started_at=conv.started_at,
                        ended_at=conv.ended_at,
                        is_visible=conv.is_visible
                    )
                    for conv in conversations
                ]
                
        except Exception as e:
            logger.error(f"사용자 대화 세션 목록 조회 실패: {e}")
            raise DatabaseError(f"대화 세션 목록 조회 중 오류 발생: {e}", "get_user_conversations")
    
    async def end_conversation(self, conversation_id: int) -> bool:
        """대화 세션 종료"""
        try:
            from ..core.db.db_services import conversation_service
            
            with conversation_service as service:
                conversation = service.get_conversation_by_id(conversation_id)
                
                if not conversation:
                    raise not_found_error("대화 세션", str(conversation_id))
                
                # 종료 시간 업데이트 (실제 구현 필요)
                # conversation.ended_at = datetime.now()
                # service.update_conversation(conversation)
                
                return True
                
        except Exception as e:
            if "대화 세션" in str(e):
                raise
            logger.error(f"대화 세션 종료 실패: {e}")
            raise DatabaseError(f"대화 세션 종료 중 오류 발생: {e}", "end_conversation")
    
    async def create_message(
        self, 
        conversation_id: int,
        sender_type: str,
        content: str,
        agent_type: Optional[str] = None
    ) -> MessageResponse:
        """메시지 생성"""
        try:
            from ..core.db.db_services import message_service
            
            with message_service as service:
                message = service.create_message(
                    conversation_id=conversation_id,
                    sender_type=sender_type,
                    content=content,
                    agent_type=agent_type
                )
                
                return MessageResponse(
                    message_id=message.message_id,
                    conversation_id=message.conversation_id,
                    sender_type=message.sender_type,
                    agent_type=message.agent_type,
                    content=message.content,
                    created_at=message.created_at
                )
                
        except Exception as e:
            logger.error(f"메시지 생성 실패: {e}")
            raise DatabaseError(f"메시지 생성 중 오류 발생: {e}", "create_message")
    
    async def get_conversation_messages(
        self, 
        conversation_id: int, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[MessageResponse]:
        """대화 세션의 메시지 목록 조회"""
        try:
            from ..core.db.db_services import message_service
            
            with message_service as service:
                messages = service.get_conversation_messages(
                    conversation_id, limit, offset
                )
                
                return [
                    MessageResponse(
                        message_id=msg.message_id,
                        conversation_id=msg.conversation_id,
                        sender_type=msg.sender_type,
                        agent_type=msg.agent_type,
                        content=msg.content,
                        created_at=msg.created_at
                    )
                    for msg in messages
                ]
                
        except Exception as e:
            logger.error(f"대화 메시지 목록 조회 실패: {e}")
            raise DatabaseError(f"메시지 목록 조회 중 오류 발생: {e}", "get_conversation_messages")
    
    async def get_conversation_history(
        self, 
        conversation_id: int, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """대화 히스토리 조회 (에이전트용 포맷)"""
        try:
            messages = await self.get_conversation_messages(conversation_id, limit)
            
            history = []
            for msg in reversed(messages):  # 최신순 정렬
                history.append({
                    "role": "user" if msg.sender_type == "user" else "assistant",
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat(),
                    "agent_type": msg.agent_type
                })
            
            return history
            
        except Exception as e:
            logger.error(f"대화 히스토리 조회 실패: {e}")
            raise DatabaseError(f"대화 히스토리 조회 중 오류 발생: {e}", "get_conversation_history")
    
    async def get_or_create_conversation(
        self, 
        user_id: int, 
        conversation_id: Optional[str] = None
    ) -> ConversationResponse:
        """대화 세션 조회 또는 생성"""
        try:
            if conversation_id:
                try:
                    conv_id = int(conversation_id)
                    conversation = await self.get_conversation(conv_id)
                    
                    # 사용자 권한 확인
                    if conversation.user_id != user_id:
                        logger.warning(f"권한 없는 대화 세션 접근 시도: user_id={user_id}, conv_id={conv_id}")
                        raise ValidationError("접근 권한이 없는 대화 세션입니다.")
                    
                    return conversation
                    
                except (ValueError, Exception) as e:
                    logger.warning(f"유효하지 않은 conversation_id: {conversation_id}, 새 세션 생성")
            
            # 새로운 대화 세션 생성
            return await self.create_conversation(user_id)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"대화 세션 조회/생성 실패: {e}")
            raise DatabaseError(f"대화 세션 처리 중 오류 발생: {e}", "get_or_create_conversation")
    
    async def save_user_message(
        self, 
        conversation_id: int, 
        content: str
    ) -> MessageResponse:
        """사용자 메시지 저장"""
        return await self.create_message(
            conversation_id=conversation_id,
            sender_type="user",
            content=content
        )
    
    async def save_agent_message(
        self, 
        conversation_id: int, 
        content: str,
        agent_type: str = "task_agent"
    ) -> MessageResponse:
        """에이전트 메시지 저장"""
        return await self.create_message(
            conversation_id=conversation_id,
            sender_type="agent",
            content=content,
            agent_type=agent_type
        )
    
    async def hide_conversation(self, conversation_id: int) -> bool:
        """대화 세션 숨기기"""
        try:
            # 실제 구현 필요
            logger.info(f"대화 세션 숨기기: {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"대화 세션 숨기기 실패: {e}")
            raise DatabaseError(f"대화 세션 숨기기 중 오류 발생: {e}", "hide_conversation")
    
    async def get_conversation_stats(self, user_id: int) -> Dict[str, Any]:
        """사용자의 대화 통계"""
        try:
            conversations = await self.get_user_conversations(user_id)
            
            stats = {
                "total_conversations": len(conversations),
                "active_conversations": len([c for c in conversations if not c.ended_at]),
                "today_conversations": len([
                    c for c in conversations 
                    if c.started_at.date() == datetime.now().date()
                ])
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"대화 통계 조회 실패: {e}")
            return {"total_conversations": 0, "active_conversations": 0, "today_conversations": 0}
    
    def format_history_for_agent(self, history: List[MessageResponse]) -> List[Dict[str, Any]]:
        """에이전트용 히스토리 포맷 변환"""
        formatted_history = []
        
        for msg in history:
            formatted_history.append({
                "role": "user" if msg.sender_type == "user" else "assistant",
                "content": msg.content,
                "timestamp": msg.created_at.isoformat()
            })
        
        return formatted_history
