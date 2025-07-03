# /app/services/google_calendar_service.py
"""
개선된 Google Calendar API 연동 서비스
"""

import os
import json
import secrets
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import aiohttp
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .common.base_service import BaseService
from .common.user_service import UserService
from .common.config_service import ConfigService

# DB 서비스 import
try:
    from ..core.db.db_services import user_service
except ImportError:
    user_service = None

# Google Calendar API 스코프
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarService(BaseService):
    """Google Calendar API 서비스 클래스"""
    
    def __init__(self, db_session, config: Optional[Dict[str, Any]] = None):
        super().__init__(db_session, config)
        self.user_service = UserService(db_session, config)
        self.config_service = ConfigService(db_session, config)
        self.calendar_config = self.config_service.get_google_calendar_config()
        
        self.state_storage = {}  # state 임시 저장용 (메모리)
        self.services_cache = {}  # 사용자별 서비스 객체 캐시
        
    # ===== OAuth 인증 관련 메서드들 =====
    
    def generate_auth_url(self, user_id: str) -> Dict[str, Any]:
        """Google Calendar OAuth 인증 URL 생성"""
        try:
            if not self.config_service.is_service_enabled("google_calendar"):
                return {"success": False, "error": "Google Calendar 서비스가 설정되지 않았습니다"}
                
            state = secrets.token_urlsafe(32)
            
            # state 저장 (메모리에 임시 저장)
            self.state_storage[f"state_{user_id}_google_calendar"] = {
                "state": state,
                "user_id": user_id,
                "created_at": datetime.now()
            }
            
            params = {
                "client_id": self.calendar_config.get("client_id"),
                "redirect_uri": self.calendar_config.get("redirect_uri"),
                "scope": " ".join(SCOPES),
                "response_type": "code",
                "state": state,
                "access_type": "offline",
                "prompt": "consent"
            }
            
            base_url = "https://accounts.google.com/o/oauth2/v2/auth"
            auth_url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            return {
                "success": True,
                "auth_url": auth_url,
                "state": state,
                "platform": "google_calendar"
            }
            
        except Exception as e:
            self.logger.error(f"Google Calendar 인증 URL 생성 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        """Authorization Code를 Access Token으로 교환"""
        try:
            # state 검증
            state_data = None
            for key, data in self.state_storage.items():
                if key.startswith("state_") and data.get("state") == state:
                    state_data = data
                    break
            
            if not state_data:
                return {"success": False, "error": "유효하지 않은 state 파라미터"}
            
            # 토큰 교환 요청
            token_data = {
                "client_id": self.calendar_config.get("client_id"),
                "client_secret": self.calendar_config.get("client_secret"),
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.calendar_config.get("redirect_uri")
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://oauth2.googleapis.com/token",
                    data=token_data
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        
                        # 사용자 정보 가져오기
                        user_info = await self._get_user_info(result["access_token"], session)
                        
                        return {
                            "success": True,
                            "platform": "google_calendar",
                            "access_token": result["access_token"],
                            "refresh_token": result.get("refresh_token"),
                            "token_type": result.get("token_type", "Bearer"),
                            "expires_in": result.get("expires_in"),
                            "scope": result.get("scope"),
                            "user_info": user_info
                        }
                    else:
                        error_msg = await resp.text()
                        return {"success": False, "error": f"토큰 교환 실패: {error_msg}"}
                        
        except Exception as e:
            self.logger.error(f"Google Calendar 토큰 교환 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_user_info(self, access_token: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Google 사용자 정보 가져오기"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            async with session.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {}
        except Exception as e:
            self.logger.error(f"Google 사용자 정보 가져오기 실패: {e}")
            return {}
    
    # ===== 토큰 관리 =====
    
    def store_token(self, user_id: int, token_data: Dict[str, Any]) -> bool:
        """토큰 DB에 저장"""
        try:
            if not user_service:
                self.logger.warning("DB 서비스를 사용할 수 없습니다")
                return False
                
            with user_service:
                result = user_service.store_google_token(
                    user_id=user_id,
                    access_token=token_data["access_token"],
                    refresh_token=token_data.get("refresh_token"),
                    expires_in=token_data.get("expires_in"),
                    user_info=token_data.get("user_info")
                )
                
                if result:
                    # 서비스 캐시 초기화
                    if user_id in self.services_cache:
                        del self.services_cache[user_id]
                    
                    self.logger.info(f"Google Calendar 토큰 DB 저장 완료: user {user_id}")
                    return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"토큰 DB 저장 실패: {e}")
            return False
    
    def get_token(self, user_id: int) -> Optional[Dict[str, Any]]:
        """DB에서 저장된 토큰 가져오기"""
        try:
            if not user_service:
                return None
                
            with user_service:
                token_data = user_service.get_google_token(user_id)
                return token_data
                
        except Exception as e:
            self.logger.error(f"토큰 DB 조회 실패: {e}")
            return None
    
    async def refresh_token(self, user_id: int) -> Dict[str, Any]:
        """토큰 갱신"""
        try:
            stored_token = self.get_token(user_id)
            if not stored_token:
                return {"success": False, "error": "저장된 토큰이 없습니다"}
            
            refresh_token = stored_token.get("refresh_token")
            if not refresh_token:
                return {"success": False, "error": "Refresh token이 없습니다"}
            
            token_data = {
                "client_id": self.calendar_config.get("client_id"),
                "client_secret": self.calendar_config.get("client_secret"),
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://oauth2.googleapis.com/token",
                    data=token_data
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        
                        # DB에 새 액세스 토큰 저장
                        if user_service:
                            with user_service:
                                user_service.update_access_token(
                                    user_id=user_id,
                                    access_token=result["access_token"],
                                    expires_in=result.get("expires_in")
                                )
                        
                        # 서비스 캐시 초기화
                        if user_id in self.services_cache:
                            del self.services_cache[user_id]
                        
                        return {
                            "success": True,
                            "access_token": result["access_token"],
                            "token_type": result.get("token_type", "Bearer"),
                            "expires_in": result.get("expires_in")
                        }
                    else:
                        error_msg = await resp.text()
                        return {"success": False, "error": f"토큰 갱신 실패: {error_msg}"}
                        
        except Exception as e:
            self.logger.error(f"Google Calendar 토큰 갱신 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def is_token_valid(self, user_id: int) -> bool:
        """토큰 유효성 검사"""
        try:
            if not user_service:
                return False
            with user_service:
                return user_service.is_google_token_valid(user_id)
        except Exception as e:
            self.logger.error(f"토큰 유효성 검사 실패: {e}")
            return False
    
    # ===== Calendar API 메서드들 =====
    
    async def create_event(self, user_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Google Calendar에 이벤트 생성"""
        try:
            service = await self._get_calendar_service(user_id)
            
            # 이벤트 데이터 준비
            event = self._prepare_event_data(event_data)
            
            # 캘린더 ID
            calendar_id = event_data.get('calendar_id', 'primary')
            
            # 이벤트 생성
            created_event = service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
            
            self.logger.info(f"Google Calendar 이벤트 생성 완료: {created_event.get('id')}")
            
            return {
                "success": True,
                "event_id": created_event.get('id'),
                "event_link": created_event.get('htmlLink'),
                "event_data": created_event
            }
            
        except HttpError as e:
            self.logger.error(f"Google Calendar API 오류: {e}")
            return {
                "success": False,
                "error": f"Google Calendar API 오류: {e}",
                "error_code": e.resp.status
            }
        except Exception as e:
            self.logger.error(f"Google Calendar 이벤트 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_event_with_reminder(
        self, 
        user_id: int, 
        event_data: Dict[str, Any],
        reminder_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """리마인더가 포함된 이벤트 생성"""
        try:
            # 기본 리마인더 설정
            if reminder_settings:
                reminder_types = reminder_settings.get("types", ["popup"])
                reminder_minutes = reminder_settings.get("minutes", [15])
                
                # 구글 캘린더 리마인더 형식으로 변환
                reminders = []
                for reminder_type in reminder_types:
                    if reminder_type == "popup":
                        for minutes in reminder_minutes:
                            reminders.append({"method": "popup", "minutes": minutes})
                    elif reminder_type == "email":
                        for minutes in reminder_minutes:
                            reminders.append({"method": "email", "minutes": minutes})
                
                event_data["reminders"] = reminders
            
            # 이벤트 생성
            result = await self.create_event(user_id, event_data)
            
            # 추가 리마인더 서비스 호출 (앱 알림, SMS 등)
            if result.get("success") and reminder_settings:
                await self._setup_additional_reminders(user_id, event_data, reminder_settings)
            
            return result
            
        except Exception as e:
            self.logger.error(f"리마인더 이벤트 생성 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _setup_additional_reminders(
        self, 
        user_id: int, 
        event_data: Dict[str, Any], 
        reminder_settings: Dict[str, Any]
    ):
        """추가 리마인더 설정 (앱 알림, SMS 등)"""
        try:
            from .common.notification_service import NotificationService
            
            notification_service = NotificationService(self.db, self.config)
            
            # 이벤트 시작 시간 가져오기
            start_time_str = event_data.get("start_time")
            if not start_time_str:
                return
            
            start_time = datetime.fromisoformat(start_time_str.replace('T', ' '))
            
            # 추가 리마인더 타입
            additional_reminders = reminder_settings.get("additional_types", [])
            reminder_minutes = reminder_settings.get("minutes", [15])
            
            for reminder_type in additional_reminders:
                if reminder_type in ["app", "email", "sms"]:
                    for minutes in reminder_minutes:
                        reminder_time = start_time - timedelta(minutes=minutes)
                        
                        # 스케줄러에 리마인더 등록 (추후 구현)
                        self.logger.info(
                            f"추가 리마인더 스케줄링: {reminder_type}, "
                            f"User {user_id}, Time {reminder_time}"
                        )
            
        except Exception as e:
            self.logger.error(f"추가 리마인더 설정 실패: {e}")
    
    def _prepare_event_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Google Calendar API 형식에 맞게 이벤트 데이터 준비"""
        # 필수 필드
        title = event_data.get('title', '제목 없음')
        start_time = event_data.get('start_time')
        end_time = event_data.get('end_time')
        
        # 시간 처리
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('T', ' '))
        if isinstance(end_time, str) and end_time:
            end_time = datetime.fromisoformat(end_time.replace('T', ' '))
        
        # 종료 시간이 없으면 시작 시간 + 1시간으로 설정
        if not end_time:
            end_time = start_time + timedelta(hours=1)
        
        # Google Calendar 이벤트 객체
        event = {
            'summary': title,
            'description': event_data.get('description', ''),
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': event_data.get('timezone', 'Asia/Seoul'),
            },
            'end': {
                'dateTime': end_time.isoformat(),
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
    
    async def _get_calendar_service(self, user_id: int):
        """사용자별 Google Calendar API 서비스 객체 가져오기"""
        try:
            # 캐시된 서비스가 있고 토큰이 유효하면 반환
            if user_id in self.services_cache and self.is_token_valid(user_id):
                return self.services_cache[user_id]
            
            # 토큰 가져오기
            token_data = self.get_token(user_id)
            if not token_data:
                raise ValueError("저장된 토큰이 없습니다. 먼저 계정을 연동해주세요.")
            
            # 토큰 유효성 검사 및 갱신
            if not self.is_token_valid(user_id):
                refresh_result = await self.refresh_token(user_id)
                if not refresh_result.get("success"):
                    raise ValueError("토큰이 만료되었습니다. 다시 인증해주세요.")
                token_data = self.get_token(user_id)  # 갱신된 토큰 다시 가져오기
            
            # Credentials 객체 생성
            credentials = Credentials(
                token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.calendar_config.get("client_id"),
                client_secret=self.calendar_config.get("client_secret"),
                scopes=SCOPES
            )
            
            # Calendar API 서비스 객체 생성
            service = build('calendar', 'v3', credentials=credentials)
            
            # 캐시에 저장
            self.services_cache[user_id] = service
            
            return service
            
        except Exception as e:
            self.logger.error(f"Google Calendar 서비스 객체 생성 실패: {e}")
            raise e
    
    # ===== 계정 연동 관리 =====
    
    def is_connected(self, user_id: int) -> bool:
        """Google Calendar 연동 상태 확인"""
        token_data = self.get_token(user_id)
        return token_data is not None and self.is_token_valid(user_id)
    
    def disconnect_account(self, user_id: int) -> bool:
        """Google Calendar 연동 해제"""
        try:
            if not user_service:
                return False
                
            with user_service:
                result = user_service.delete_google_token(user_id)
                
                # 서비스 캐시에서 제거
                if user_id in self.services_cache:
                    del self.services_cache[user_id]
                
                if result:
                    self.logger.info(f"Google Calendar 연동 해제 완료: user {user_id}")
                    return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Google Calendar 연동 해제 실패: {e}")
            return False
    
    def get_connection_info(self, user_id: int) -> Dict[str, Any]:
        """연동 정보 조회"""
        token_data = self.get_token(user_id)
        if token_data:
            return {
                "connected": True,
                "user_info": token_data.get("user_info", {}),
                "connected_at": token_data.get("created_at"),
                "is_valid": self.is_token_valid(user_id)
            }
        else:
            return {"connected": False}
    
    async def get_service_status(self) -> Dict[str, Any]:
        """서비스 상태 조회"""
        return {
            "service": "google_calendar_service",
            "status": "healthy",
            "configured": self.config_service.is_service_enabled("google_calendar"),
            "cached_services": len(self.services_cache)
        }
    
    async def cleanup(self):
        """서비스 정리"""
        self.services_cache.clear()
        self.state_storage.clear()
        await self.user_service.cleanup()
        await self.config_service.cleanup()
        self.logger.info("Google Calendar 서비스 정리 완료")