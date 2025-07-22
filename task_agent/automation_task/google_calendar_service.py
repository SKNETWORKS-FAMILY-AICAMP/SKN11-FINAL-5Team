"""Google Calendar API 연동 서비스 - 공용 모듈 사용 버전"""

import os
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from task_agent.automation_task.common import (
    get_auth_manager, get_oauth_http_client, get_config_manager,
    DateTimeUtils
)
import logging

logger = logging.getLogger(__name__)

# Google Calendar API 스코프
SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendarService:
    """Google Calendar API 서비스 클래스 (공용 모듈 사용)"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Google Calendar 서비스 초기화
        
        config 예시:
        {
            "google_calendar": {
                "client_id": "your_client_id",
                "client_secret": "your_client_secret", 
                "redirect_uri": "http://localhost:8080/auth/google/callback"
            }
        }
        """
        self.auth_manager = get_auth_manager()
        self.http_client = get_oauth_http_client()
        self.config_manager = get_config_manager()
        
        if config:
            self.config = config.get("google_calendar", {})
        else:
            # Use environment variables for OAuth configuration
            self.config = {
                "client_id": os.getenv("GOOGLE_CALENDAR_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET"),
                "redirect_uri": os.getenv("GOOGLE_CALENDAR_REDIRECT_URI")
            }
        
        self.services_cache = {}  # 사용자별 서비스 객체 캐시
        self.platform = "google_calendar"
    
    # ===== OAuth 인증 관련 메서드들 =====
    
    def generate_auth_url(self, user_id: int) -> Dict[str, Any]:
        """Google Calendar OAuth 인증 URL 생성"""
        try:
            state = self.auth_manager.generate_state(str(user_id), self.platform)
            
            params = {
                "client_id": self.config.get("client_id"),
                "redirect_uri": self.config.get("redirect_uri"),
                "scope": " ".join(SCOPES),
                "response_type": "code",
                "state": state,
                "access_type": "offline",  # refresh token을 위해 필수
                "prompt": "consent"  # 매번 consent 화면 표시하여 refresh token 확보
            }
            
            base_url = "https://accounts.google.com/o/oauth2/v2/auth"
            auth_url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            return {
                "success": True,
                "auth_url": auth_url,
                "state": state,
                "platform": self.platform
            }
            
        except Exception as e:
            logger.error(f"Google Calendar 인증 URL 생성 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def exchange_code_for_token(self, code: str, state: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Authorization Code를 Access Token으로 교환"""
        try:
            # state 검증
            state_data = self.auth_manager.validate_state(state, str(user_id) if user_id else None, self.platform)
            if not state_data:
                return {"success": False, "error": "유효하지 않은 state 파라미터"}
            
            # 토큰 교환 요청
            result = await self.http_client.exchange_oauth_code(
                token_url="https://oauth2.googleapis.com/token",
                client_id=self.config.get("client_id"),
                client_secret=self.config.get("client_secret"),
                code=code,
                redirect_uri=self.config.get("redirect_uri")
            )
            
            if result.get("success"):
                token_data = result.get("data", {})
                
                # 사용자 정보 가져오기
                user_info = await self._get_user_info(token_data.get("access_token"))
                
                response_data = {
                    "success": True,
                    "platform": self.platform,
                    "access_token": token_data.get("access_token"),
                    "refresh_token": token_data.get("refresh_token"),
                    "token_type": token_data.get("token_type", "Bearer"),
                    "expires_in": token_data.get("expires_in"),
                    "scope": token_data.get("scope"),
                    "user_info": user_info
                }
                
                # 토큰 저장
                target_user_id = user_id or state_data.get("user_id")
                if target_user_id:
                    self.store_token(int(target_user_id), response_data)
                
                return response_data
            else:
                return {"success": False, "error": f"토큰 교환 실패: {result.get('error')}"}
                        
        except Exception as e:
            logger.error(f"Google Calendar 토큰 교환 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Google 사용자 정보 가져오기"""
        try:
            result = await self.http_client.oauth_request(
                method="GET",
                url="https://www.googleapis.com/oauth2/v2/userinfo",
                access_token=access_token
            )
            
            if result.get("success"):
                return result.get("data", {})
            return {}
        except Exception as e:
            logger.error(f"Google 사용자 정보 가져오기 실패: {e}")
            return {}
    
    # ===== 토큰 관리 =====
    
    def store_token(self, user_id: str, token_data: Dict[str, Any]) -> bool:
        """토큰 저장"""
        success = self.auth_manager.store_token(user_id, self.platform, token_data)
        
        # 서비스 캐시 초기화 (새 토큰으로 업데이트)
        if success and user_id in self.services_cache:
            del self.services_cache[user_id]
        
        return success
    
    def get_token(self, user_id: int) -> Optional[Dict[str, Any]]:
        """저장된 토큰 가져오기"""
        return self.auth_manager.get_token(str(user_id), self.platform)
    
    async def refresh_token(self, user_id: int) -> Dict[str, Any]:
        """토큰 갱신"""
        try:
            stored_token = self.get_token(str(user_id))
            if not stored_token:
                return {"success": False, "error": "저장된 토큰이 없습니다"}
            
            refresh_token = stored_token.get("refresh_token")
            if not refresh_token:
                return {"success": False, "error": "Refresh token이 없습니다"}
            
            result = await self.http_client.refresh_oauth_token(
                token_url="https://oauth2.googleapis.com/token",
                client_id=self.config.get("client_id"),
                client_secret=self.config.get("client_secret"),
                refresh_token=refresh_token
            )
            
            if result.get("success"):
                token_data = result.get("data", {})
                
                # 기존 토큰 업데이트
                update_data = {
                    "access_token": token_data.get("access_token"),
                    "expires_in": token_data.get("expires_in"),
                    "token_type": token_data.get("token_type", "Bearer"),
                    "stored_at": datetime.now().isoformat()
                }
                
                # 새 refresh_token이 있으면 업데이트
                if token_data.get("refresh_token"):
                    update_data["refresh_token"] = token_data.get("refresh_token")
                
                # 토큰 업데이트
                self.auth_manager.update_token(str(user_id), self.platform, update_data)
                
                return {
                    "success": True,
                    "access_token": token_data.get("access_token"),
                    "token_type": token_data.get("token_type", "Bearer"),
                    "expires_in": token_data.get("expires_in")
                }
            else:
                return {"success": False, "error": f"토큰 갱신 실패: {result.get('error')}"}
                        
        except Exception as e:
            logger.error(f"Google Calendar 토큰 갱신 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def is_token_valid(self, user_id: int) -> bool:
        """토큰 유효성 검사"""
        return self.auth_manager.is_token_valid(user_id, self.platform)
    
    # ===== Google Calendar API 서비스 객체 관리 =====
    
    async def _get_calendar_service(self, user_id: int):
        """사용자별 Google Calendar API 서비스 객체 가져오기"""
        try:
            # # 캐시된 서비스가 있고 토큰이 유효하면 반환
            # if user_id in self.services_cache and self.is_token_valid(user_id):
            #     return self.services_cache[user_id]
            
            # # 토큰 가져오기
            # token_data = self.get_token(user_id)
            # if not token_data:
            #     raise ValueError("저장된 토큰이 없습니다. 먼저 계정을 연동해주세요.")
            
            # # 토큰 유효성 검사 및 갱신
            # if not self.is_token_valid(user_id):
            #     refresh_result = await self.refresh_token(user_id)
            #     if not refresh_result.get("success"):
            #         raise ValueError("토큰이 만료되었습니다. 다시 인증해주세요.")
            #     token_data = self.get_token(user_id)  # 갱신된 토큰 다시 가져오기
            
            # Credentials 객체 생성
            credentials = Credentials(
                token="ya29.a0AS3H6NzOX8VJMtKB0Xzrfpmjp0IgY12cuz8p791HjV6EbRW3nXqV5yGtqdRcrgd1GDlLCda5K6qJLBffNPcxxpf3__FA2nvhRw5Jtnqo_Og_lO5vCgC1kOjAlQZ3GLE84P2mkbOxbKwTuO7ikd-8g01uqfZmRaEykmNUcWIfaCgYKAWISARcSFQHGX2MiZ81-vRlPLVzYFlMWPTBuqQ0175",
                refresh_token="gAAAAABoZ3ZQVdVQh5UbvE8OYIyaX1eAcMzfnWJuqF1GssxGMbnk491YLUkUBfD9p1TkaqQyiOO7Yri7YkHhXXQ6w24h-FH-HQJoA6mXShb7yokcdz7Dr1z9_Ib_gL3VSnyCmMl8w_2xe_D4eB7e1yW_MM9fuM55-59flV3SotZM7KvqPq_UryzaYF7U2dpsztJK2ShJrhqqPapgIYvd0-I5LWnFQ3UNmg==",
                # token=token_data["access_token"],
                # refresh_token=token_data.get("refresh_token"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.config.get("client_id"),
                client_secret=self.config.get("client_secret"),
                scopes=SCOPES
            )
            print(SCOPES)
            
            # Calendar API 서비스 객체 생성
            service = build('calendar', 'v3', credentials=credentials)
            
            # 캐시에 저장
            self.services_cache[user_id] = service
            
            return service
            
        except Exception as e:
            logger.error(f"Google Calendar 서비스 객체 생성 실패: {e}")
            raise e
    
    # ===== Calendar API 메서드들 =====
    
    async def create_event(self, user_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Google Calendar에 이벤트 생성 (재시도 기능 포함)"""
        try:
            service = await self._get_calendar_service(str(user_id))
            
            # 이벤트 데이터 준비
            event = self._prepare_event_data(event_data)
            
            # 캘린더 ID
            calendar_id = event_data.get('calendar_id', 'primary')
            
            # 이벤트 생성
            created_event = service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
            
            logger.info(f"Google Calendar 이벤트 생성 완료: {created_event.get('id')}")
            
            return {
                "success": True,
                "event_id": created_event.get('id'),
                "event_link": created_event.get('htmlLink'),
                "event_data": created_event
            }
            
        except HttpError as e:
            logger.error(f"Google Calendar API 오류: {e}")
            return {
                "success": False,
                "error": f"Google Calendar API 오류: {e}",
                "error_code": e.resp.status
            }
        except Exception as e:
            logger.error(f"Google Calendar 이벤트 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _prepare_event_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Google Calendar API 형식에 맞게 이벤트 데이터 준비"""
        # 필수 필드
        title = event_data.get('title', '제목 없음')
        start_time = event_data.get('start_time')
        end_time = event_data.get('end_time')
        
        # 시간 처리 - DateTimeUtils 사용
        if isinstance(start_time, str):
            start_time = DateTimeUtils.parse_datetime(start_time)
        if isinstance(end_time, str) and end_time:
            end_time = DateTimeUtils.parse_datetime(end_time)
        
        # 종료 시간이 없으면 시작 시간 + 1시간으로 설정
        if not end_time:
            end_time = DateTimeUtils.add_time_delta(start_time, hours=1)
        
        # Google Calendar 이벤트 객체
        event = {
            'summary': title,
            'description': event_data.get('description', ''),
            'start': {
                'dateTime': DateTimeUtils.format_datetime_iso(start_time),
                'timeZone': event_data.get('timezone', 'Asia/Seoul'),
            },
            'end': {
                'dateTime': DateTimeUtils.format_datetime_iso(end_time),
                'timeZone': event_data.get('timezone', 'Asia/Seoul'),
            },
        }
        
        # 위치 추가
        if event_data.get('location'):
            event['location'] = event_data['location']
        
        # 리마인더 설정
        reminders = event_data.get('reminders')
        if reminders:
            event['reminders'] = {
                'useDefault': False,
                'overrides': reminders
            }
        else:
            # 기본 리마인더 (15분 전)
            event['reminders'] = {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 15},
                ]
            }
        
        # 반복 일정 설정
        if event_data.get('recurrence'):
            event['recurrence'] = event_data['recurrence']
        
        return event
    
    async def get_events(self, user_id: int, start_date: datetime, end_date: datetime, 
                        calendar_id: str = 'primary') -> Dict[str, Any]:
        """지정된 기간의 이벤트 조회"""
        try:
            service = await self._get_calendar_service(str(user_id))
            
            # RFC3339 형식으로 시간 변환
            time_min = DateTimeUtils.format_datetime_iso(start_date) + 'Z'
            time_max = DateTimeUtils.format_datetime_iso(end_date) + 'Z'
            
            # 이벤트 조회
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            return {
                "success": True,
                "events": events,
                "count": len(events)
            }
            
        except HttpError as e:
            logger.error(f"Google Calendar 이벤트 조회 실패: {e}")
            return {
                "success": False,
                "error": f"Google Calendar API 오류: {e}",
                "error_code": e.resp.status
            }
        except Exception as e:
            logger.error(f"이벤트 조회 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_event(self, user_id: int, event_id: str, event_data: Dict[str, Any], 
                          calendar_id: str = 'primary') -> Dict[str, Any]:
        """기존 이벤트 수정"""
        try:
            service = await self._get_calendar_service(str(user_id))
            
            # 기존 이벤트 가져오기
            existing_event = service.events().get(
                calendarId=calendar_id, 
                eventId=event_id
            ).execute()
            
            # 업데이트할 데이터 준비
            updated_event = self._prepare_event_data(event_data)
            
            # 기존 데이터와 병합
            for key, value in updated_event.items():
                existing_event[key] = value
            
            # 이벤트 업데이트
            updated = service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=existing_event
            ).execute()
            
            logger.info(f"Google Calendar 이벤트 수정 완료: {event_id}")
            
            return {
                "success": True,
                "event_id": updated.get('id'),
                "event_link": updated.get('htmlLink'),
                "event_data": updated
            }
            
        except HttpError as e:
            logger.error(f"Google Calendar 이벤트 수정 실패: {e}")
            return {
                "success": False,
                "error": f"Google Calendar API 오류: {e}",
                "error_code": e.resp.status
            }
        except Exception as e:
            logger.error(f"이벤트 수정 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_event(self, user_id: int, event_id: str, calendar_id: str = 'primary') -> Dict[str, Any]:
        """이벤트 삭제"""
        try:
            service = await self._get_calendar_service(str(user_id))
            
            # 이벤트 삭제
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"Google Calendar 이벤트 삭제 완료: {event_id}")
            
            return {
                "success": True,
                "message": "이벤트가 성공적으로 삭제되었습니다"
            }
            
        except HttpError as e:
            logger.error(f"Google Calendar 이벤트 삭제 실패: {e}")
            return {
                "success": False,
                "error": f"Google Calendar API 오류: {e}",
                "error_code": e.resp.status
            }
        except Exception as e:
            logger.error(f"이벤트 삭제 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ===== 계정 연동 관리 =====
    
    def is_connected(self, user_id: int) -> bool:
        """Google Calendar 연동 상태 확인"""
        token_data = self.get_token(str(user_id))
        return token_data is not None and self.is_token_valid(str(user_id))
    
    def disconnect_account(self, user_id: int) -> bool:
        """Google Calendar 연동 해제"""
        success = self.auth_manager.remove_token(str(user_id), self.platform)
        
        # 서비스 캐시에서 제거
        if user_id in self.services_cache:
            del self.services_cache[user_id]
        
        return success
    
    def get_connection_info(self, user_id: int) -> Dict[str, Any]:
        """연동 정보 조회"""
        return self.auth_manager.get_connection_info(str(user_id), self.platform)


# 전역 인스턴스를 위한 팩토리 함수
_global_calendar_service = None

def get_google_calendar_service(config: Dict[str, Any] = None) -> GoogleCalendarService:
    """Google Calendar 서비스 인스턴스 반환 (싱글톤)"""
    global _global_calendar_service
    if _global_calendar_service is None:
        _global_calendar_service = GoogleCalendarService(config)
    return _global_calendar_service


# ===== 사용 예시 =====

async def example_usage():
    """Google Calendar Service 사용 예시"""
    
    # 1. 서비스 초기화
    calendar_service = get_google_calendar_service()
    # 2. 인증 URL 생성
    auth_result = calendar_service.generate_auth_url(2)
    if auth_result["success"]:
        print(f"Google Calendar 인증 URL: {auth_result['auth_url']}")
    else:
        print("fail")
    
    # 3. 인증 완료 후 토큰 교환 (콜백에서 실행)
    # token_result = await calendar_service.exchange_code_for_token("auth_code", "state", 2)
    
    # 4. 이벤트 생성
    event_data = {
        "title": "팀 미팅",
        "start_time": "2024-01-15T14:00:00",
        "end_time": "2024-01-15T15:30:00",
        "description": "주간 팀 미팅",
        "location": "회의실 A",
        "reminders": [{"method": "popup", "minutes": 15}]
    }
    
    result = await calendar_service.create_event(2, event_data)
    if result["success"]:
        print(f"이벤트 생성 완료: {result['event_link']}")
    
    # 5. 연동 상태 확인
    connection_info = calendar_service.get_connection_info(2)
    print(f"연동 상태: {connection_info}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
