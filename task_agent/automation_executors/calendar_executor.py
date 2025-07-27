"""
캘린더 자동화 실행기
일정 관리 자동화 작업을 실제로 수행
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CalendarExecutor:
    """캘린더 자동화 실행기"""
    
    def __init__(self):
        """캘린더 실행기 초기화"""
        self.supported_providers = ["google", "outlook", "apple"]
        self.default_timezone = "Asia/Seoul"
        
        logger.info("CalendarExecutor 초기화 완료")

    async def execute(self, task_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """일정 등록 실행"""
        try:
            logger.info(f"일정 등록 실행 시작 - 사용자: {user_id}")
            
            # 필수 데이터 검증
            validation_result = self._validate_task_data(task_data)
            if not validation_result["is_valid"]:
                return {
                    "success": False,
                    "message": f"데이터 검증 실패: {', '.join(validation_result['errors'])}",
                    "details": validation_result
                }
            
            # 일정 데이터 추출 및 정규화
            event_data = await self._normalize_event_data(task_data)
            
            # 캘린더 연동 시뮬레이션 (실제로는 Google/Outlook API 사용)
            result = await self._create_calendar_event(event_data, user_id)
            
            if result["success"]:
                logger.info(f"일정 등록 성공 - 이벤트 ID: {result.get('event_id')}")
                return {
                    "success": True,
                    "message": f"'{event_data['title']}' 일정이 성공적으로 등록되었습니다",
                    "details": {
                        "event_id": result.get("event_id"),
                        "title": event_data["title"],
                        "start_time": event_data["start_time"],
                        "end_time": event_data.get("end_time"),
                        "calendar_link": result.get("calendar_link"),
                        "provider": "google"
                    }
                }
            else:
                logger.error(f"일정 등록 실패: {result.get('error')}")
                return {
                    "success": False,
                    "message": f"일정 등록 실패: {result.get('error')}",
                    "details": result
                }
                
        except Exception as e:
            logger.error(f"캘린더 실행기 오류: {e}")
            return {
                "success": False,
                "message": f"일정 등록 중 오류 발생: {str(e)}",
                "details": {"error": str(e)}
            }

    def _validate_task_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """일정 작업 데이터 검증"""
        errors = []
        warnings = []
        
        # 필수 필드 검증
        if not task_data.get("title"):
            errors.append("일정 제목이 필요합니다")
        
        if not task_data.get("start_time"):
            errors.append("시작 시간이 필요합니다")
        else:
            # 시간 형식 검증
            start_time = self._parse_datetime(task_data["start_time"])
            if not start_time:
                errors.append("잘못된 시작 시간 형식입니다")
            elif start_time < datetime.now():
                warnings.append("과거 시간으로 일정이 설정됩니다")
        
        # 종료 시간 검증 (선택적)
        if task_data.get("end_time"):
            end_time = self._parse_datetime(task_data["end_time"])
            start_time = self._parse_datetime(task_data["start_time"])
            
            if not end_time:
                warnings.append("잘못된 종료 시간 형식 - 기본값 사용")
            elif start_time and end_time <= start_time:
                errors.append("종료 시간은 시작 시간보다 늦어야 합니다")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """문자열을 datetime 객체로 변환"""
        try:
            # ISO 형식 시도
            if 'T' in datetime_str:
                return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            
            # 다양한 형식 시도
            try:
                from dateutil.parser import parse
                return parse(datetime_str)
            except ImportError:
                # dateutil이 없는 경우 기본 파싱
                return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
            
        except Exception as e:
            logger.warning(f"날짜 파싱 실패: {datetime_str}, 오류: {e}")
            return None

    async def _normalize_event_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """이벤트 데이터 정규화"""
        try:
            normalized = {
                "title": task_data.get("title", "").strip(),
                "description": task_data.get("description", "").strip(),
                "location": task_data.get("location", "").strip(),
                "attendees": task_data.get("attendees", []),
                "reminder_minutes": task_data.get("reminder_minutes", 15),
                "all_day": task_data.get("all_day", False)
            }
            
            # 시간 정규화
            start_time = self._parse_datetime(task_data["start_time"])
            if start_time:
                normalized["start_time"] = start_time
            
            # 종료 시간 설정
            if task_data.get("end_time"):
                end_time = self._parse_datetime(task_data["end_time"])
                if end_time:
                    normalized["end_time"] = end_time
            
            # 종료 시간이 없으면 1시간 후로 설정
            if "end_time" not in normalized and "start_time" in normalized:
                if normalized.get("all_day"):
                    # 종일 이벤트는 같은 날짜
                    normalized["end_time"] = normalized["start_time"]
                else:
                    # 1시간 후로 설정
                    normalized["end_time"] = normalized["start_time"] + timedelta(hours=1)
            
            return normalized
            
        except Exception as e:
            logger.error(f"이벤트 데이터 정규화 실패: {e}")
            raise

    async def _create_calendar_event(self, event_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """캘린더 이벤트 생성 (시뮬레이션)"""
        try:
            # 실제로는 Google Calendar API 또는 Outlook API 호출
            event_id = f"event_{user_id}_{datetime.now().timestamp()}"
            
            logger.info(f"캘린더 이벤트 생성: {event_data['title']} - {event_data['start_time']}")
            
            return {
                "success": True,
                "event_id": event_id,
                "calendar_link": f"https://calendar.google.com/calendar/event?eid={event_id}",
                "provider": "google",
                "message": "일정이 성공적으로 생성되었습니다"
            }
            
        except Exception as e:
            logger.error(f"캘린더 이벤트 생성 실패: {e}")
            return {"success": False, "error": str(e)}

    def is_available(self) -> bool:
        """실행기 사용 가능 여부"""
        return True

    async def test_connection(self) -> Dict[str, Any]:
        """캘린더 연결 테스트"""
        try:
            return {
                "success": True,
                "message": "캘린더 연결이 정상입니다 (시뮬레이션)",
                "provider": "google"
            }
        except Exception as e:
            return {"success": False, "error": f"연결 테스트 실패: {str(e)}"}

    async def cleanup(self):
        """실행기 정리"""
        try:
            logger.info("CalendarExecutor 정리 완료")
        except Exception as e:
            logger.error(f"CalendarExecutor 정리 실패: {e}")
