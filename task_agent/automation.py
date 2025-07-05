"""
간소화된 자동화 시스템 v3
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from models import AutomationRequest, AutomationResponse, AutomationStatus
from db_models import AutomationTask
from database import get_db_session

logger = logging.getLogger(__name__)

class AutomationManager:
    """간소화된 자동화 매니저"""
    
    def __init__(self):
        """자동화 매니저 초기화"""
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        logger.info("자동화 매니저 초기화 완료")

    async def create_automation_task(self, request: AutomationRequest) -> AutomationResponse:
        """자동화 작업 생성"""
        try:
            # DB에 작업 저장
            db_session = get_db_session()
            try:
                automation_task = AutomationTask(
                    user_id=request.user_id,
                    task_type=request.task_type,
                    title=request.title,
                    task_data=request.task_data,
                    status=AutomationStatus.PENDING,
                    scheduled_at=request.scheduled_at
                )
                
                db_session.add(automation_task)
                db_session.commit()
                db_session.refresh(automation_task)
                task_id = automation_task.task_id
                
            finally:
                db_session.close()
            
            # 스케줄 설정
            if request.scheduled_at:
                self.scheduler.add_job(
                    self._execute_task,
                    'date',
                    run_date=request.scheduled_at,
                    args=[task_id],
                    id=f"auto_{task_id}"
                )
                
                return AutomationResponse(
                    task_id=task_id,
                    status="scheduled",
                    message=f"작업이 {request.scheduled_at.strftime('%Y-%m-%d %H:%M')}에 예약되었습니다.",
                    scheduled_time=request.scheduled_at
                )
            else:
                # 즉시 실행
                result = await self._execute_task(task_id)
                return AutomationResponse(
                    task_id=task_id,
                    status=result.get("status", "success"),
                    message=result.get("message", "작업이 실행되었습니다.")
                )
                
        except Exception as e:
            logger.error(f"자동화 작업 생성 실패: {e}")
            return AutomationResponse(
                task_id=-1,
                status="failed",
                message=f"작업 생성 실패: {str(e)}"
            )

    async def _execute_task(self, task_id: int) -> Dict[str, Any]:
        """자동화 작업 실행"""
        db_session = get_db_session()
        try:
            # 작업 조회
            task = db_session.query(AutomationTask).filter(
                AutomationTask.task_id == task_id
            ).first()
            
            if not task:
                return {"status": "failed", "message": "작업을 찾을 수 없습니다"}
            
            # 상태 업데이트 - PROCESSING
            task.status = AutomationStatus.PROCESSING
            task.executed_at = datetime.now()
            db_session.commit()
            
            # 작업 실행
            result = await self._execute_by_type(task.task_type, task.task_data)
            
            # 결과에 따른 상태 업데이트
            task.status = AutomationStatus.SUCCESS if result["status"] == "success" else AutomationStatus.FAILED
            db_session.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"작업 실행 실패 (ID: {task_id}): {e}")
            # 실패 상태로 업데이트
            if 'task' in locals():
                task.status = AutomationStatus.FAILED
                db_session.commit()
            return {"status": "failed", "message": str(e)}
        finally:
            db_session.close()
    
    async def _execute_by_type(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """타입별 작업 실행"""
        try:
            if task_type == "schedule_calendar":
                return await self._execute_calendar(task_data)
            elif task_type == "send_email":
                return await self._execute_email(task_data)
            elif task_type == "publish_sns":
                return await self._execute_sns(task_data)
            elif task_type == "send_reminder":
                return await self._execute_reminder(task_data)
            else:
                return {"status": "failed", "message": f"지원하지 않는 작업 타입: {task_type}"}
        except Exception as e:
            return {"status": "failed", "message": str(e)}
    
    async def _execute_calendar(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """캘린더 일정 추가"""
        try:
            # Google Calendar API 연동 (실제 구현 필요)
            title = task_data.get("title", "")
            start_time = task_data.get("start_time", "")
            
            # 여기서 실제 Google Calendar API 호출
            # 현재는 시뮬레이션
            logger.info(f"캘린더 일정 추가: {title} ({start_time})")
            
            return {
                "status": "success",
                "message": f"'{title}' 일정이 추가되었습니다",
                "details": {
                    "title": title,
                    "start_time": start_time
                }
            }
            
        except Exception as e:
            logger.error(f"캘린더 작업 실패: {e}")
            return {"status": "failed", "message": str(e)}
    
    async def _execute_email(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """이메일 발송"""
        try:
            # 이메일 발송 로직 (실제 구현 필요)
            to_emails = task_data.get("to_emails", [])
            subject = task_data.get("subject", "")
            
            # 여기서 실제 이메일 API 호출
            # 현재는 시뮬레이션
            logger.info(f"이메일 발송: {subject} -> {', '.join(to_emails)}")
            
            return {
                "status": "success",
                "message": f"{len(to_emails)}명에게 이메일이 발송되었습니다",
                "details": {
                    "subject": subject,
                    "recipients": len(to_emails)
                }
            }
            
        except Exception as e:
            logger.error(f"이메일 작업 실패: {e}")
            return {"status": "failed", "message": str(e)}
    
    async def _execute_sns(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """SNS 게시물 발행"""
        try:
            # SNS 발행 로직 (실제 구현 필요)
            platform = task_data.get("platform", "")
            content = task_data.get("content", "")
            
            # 여기서 실제 SNS API 호출
            # 현재는 시뮬레이션
            logger.info(f"SNS 발행: {platform} - {content[:50]}...")
            
            return {
                "status": "success",
                "message": f"{platform}에 게시물이 발행되었습니다",
                "details": {
                    "platform": platform,
                    "content_length": len(content)
                }
            }
            
        except Exception as e:
            logger.error(f"SNS 작업 실패: {e}")
            return {"status": "failed", "message": str(e)}
    
    async def _execute_reminder(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """리마인더 발송"""
        try:
            # 리마인더 발송 로직 (실제 구현 필요)
            message = task_data.get("message", "")
            user_id = task_data.get("user_id", "")
            
            # 여기서 실제 알림 발송
            # 현재는 시뮬레이션
            logger.info(f"리마인더 발송: {message} (User: {user_id})")
            
            return {
                "status": "success",
                "message": "리마인더가 발송되었습니다",
                "details": {
                    "message": message,
                    "user_id": user_id
                }
            }
            
        except Exception as e:
            logger.error(f"리마인더 작업 실패: {e}")
            return {"status": "failed", "message": str(e)}

    async def get_task_status(self, task_id: int) -> Dict[str, Any]:
        """작업 상태 조회"""
        db_session = get_db_session()
        try:
            task = db_session.query(AutomationTask).filter(
                AutomationTask.task_id == task_id
            ).first()
            
            if not task:
                return {"error": "작업을 찾을 수 없습니다"}
            
            return {
                "task_id": task_id,
                "status": task.status,
                "title": task.title,
                "task_type": task.task_type,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "executed_at": task.executed_at.isoformat() if task.executed_at else None,
                "scheduled_at": task.scheduled_at.isoformat() if task.scheduled_at else None
            }
            
        except Exception as e:
            logger.error(f"작업 상태 조회 실패: {e}")
            return {"error": str(e)}
        finally:
            db_session.close()

    async def cancel_task(self, task_id: int) -> bool:
        """작업 취소"""
        try:
            # 스케줄러에서 제거
            try:
                self.scheduler.remove_job(f"auto_{task_id}")
            except:
                pass  # 이미 실행되었거나 존재하지 않는 경우
            
            # DB 상태 업데이트
            db_session = get_db_session()
            try:
                task = db_session.query(AutomationTask).filter(
                    AutomationTask.task_id == task_id
                ).first()
                
                if task:
                    task.status = AutomationStatus.CANCELLED
                    db_session.commit()
                    return True
                    
            finally:
                db_session.close()
                
            return False
            
        except Exception as e:
            logger.error(f"작업 취소 실패: {e}")
            return False

    async def shutdown(self):
        """자동화 매니저 종료"""
        try:
            self.scheduler.shutdown()
            logger.info("자동화 매니저 종료 완료")
        except Exception as e:
            logger.error(f"자동화 매니저 종료 실패: {e}")
