"""
SNS Service - OAuth 인증 및 게시물 발행을 위한 통합 서비스
"""

import json
import secrets
import urllib.parse
import base64
from typing import Dict, List, Any, Optional, Tuple
import aiohttp
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SNSService:
    """SNS 플랫폼 통합 서비스"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        SNS 서비스 초기화
        
        config 예시:
        {
            "facebook": {
                "app_id": "your_app_id",
                "app_secret": "your_app_secret",
                "redirect_uri": "http://localhost:8000/auth/facebook/callback"
            },
            "twitter": {
                "client_id": "your_client_id",
                "client_secret": "your_client_secret",
                "redirect_uri": "http://localhost:8000/auth/twitter/callback"
            },
            "linkedin": {
                "client_id": "your_client_id",
                "client_secret": "your_client_secret",
                "redirect_uri": "http://localhost:8000/auth/linkedin/callback"
            }
        }
        """
        self.config = config
        self.tokens_storage = {}  # 실제로는 데이터베이스 사용
        
    # ===== OAuth 인증 관련 메서드들 =====
    
    def generate_auth_url(self, platform: str, user_id: str, scopes: List[str] = None) -> Dict[str, Any]:
        """OAuth 인증 URL 생성"""
        try:
            state = secrets.token_urlsafe(32)
            
            # state를 저장 (실제로는 Redis나 DB 사용)
            self.tokens_storage[f"state_{user_id}_{platform}"] = {
                "state": state,
                "platform": platform,
                "user_id": user_id,
                "created_at": datetime.now()
            }
            
            if platform.lower() == "facebook":
                return self._generate_facebook_auth_url(state, scopes)
            elif platform.lower() == "twitter":
                return self._generate_twitter_auth_url(state, scopes)
            elif platform.lower() == "linkedin":
                return self._generate_linkedin_auth_url(state, scopes)
            else:
                return {"success": False, "error": f"지원하지 않는 플랫폼: {platform}"}
                
        except Exception as e:
            logger.error(f"인증 URL 생성 실패 ({platform}): {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_facebook_auth_url(self, state: str, scopes: List[str] = None) -> Dict[str, Any]:
        """Facebook OAuth 인증 URL 생성"""
        if not scopes:
            scopes = [
                "pages_manage_posts",
                "pages_read_engagement", 
                "instagram_basic",
                "instagram_content_publish",
                "business_management"
            ]
        
        config = self.config.get("facebook", {})
        
        params = {
            "client_id": config.get("app_id"),
            "redirect_uri": config.get("redirect_uri"),
            "scope": ",".join(scopes),
            "response_type": "code",
            "state": state
        }
        
        base_url = "https://www.facebook.com/v18.0/dialog/oauth"
        auth_url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        return {
            "success": True,
            "auth_url": auth_url,
            "state": state,
            "platform": "facebook"
        }
    
    def _generate_twitter_auth_url(self, state: str, scopes: List[str] = None) -> Dict[str, Any]:
        """Twitter OAuth 2.0 인증 URL 생성"""
        if not scopes:
            scopes = ["tweet.read", "tweet.write", "users.read"]
        
        config = self.config.get("twitter", {})
        
        params = {
            "response_type": "code",
            "client_id": config.get("client_id"),
            "redirect_uri": config.get("redirect_uri"),
            "scope": " ".join(scopes),
            "state": state,
            "code_challenge": "challenge",  # PKCE 사용
            "code_challenge_method": "plain"
        }
        
        base_url = "https://twitter.com/i/oauth2/authorize"
        auth_url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        return {
            "success": True,
            "auth_url": auth_url,
            "state": state,
            "platform": "twitter"
        }
    
    def _generate_linkedin_auth_url(self, state: str, scopes: List[str] = None) -> Dict[str, Any]:
        """LinkedIn OAuth 2.0 인증 URL 생성"""
        if not scopes:
            scopes = ["r_liteprofile", "r_emailaddress", "w_member_social"]
        
        config = self.config.get("linkedin", {})
        
        params = {
            "response_type": "code",
            "client_id": config.get("client_id"),
            "redirect_uri": config.get("redirect_uri"),
            "scope": " ".join(scopes),
            "state": state
        }
        
        base_url = "https://www.linkedin.com/oauth/v2/authorization"
        auth_url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        return {
            "success": True,
            "auth_url": auth_url,
            "state": state,
            "platform": "linkedin"
        }
    
    async def exchange_code_for_token(self, platform: str, code: str, state: str) -> Dict[str, Any]:
        """Authorization Code를 Access Token으로 교환"""
        try:
            # state 검증
            state_data = None
            for key, data in self.tokens_storage.items():
                if key.startswith("state_") and data.get("state") == state:
                    state_data = data
                    break
            
            if not state_data:
                return {"success": False, "error": "유효하지 않은 state 파라미터"}
            
            if platform.lower() == "facebook":
                return await self._exchange_facebook_token(code)
            elif platform.lower() == "twitter":
                return await self._exchange_twitter_token(code)
            elif platform.lower() == "linkedin":
                return await self._exchange_linkedin_token(code)
            else:
                return {"success": False, "error": f"지원하지 않는 플랫폼: {platform}"}
                
        except Exception as e:
            logger.error(f"토큰 교환 실패 ({platform}): {e}")
            return {"success": False, "error": str(e)}
    
    async def _exchange_facebook_token(self, code: str) -> Dict[str, Any]:
        """Facebook Access Token 교환"""
        config = self.config.get("facebook", {})
        
        params = {
            "client_id": config.get("app_id"),
            "client_secret": config.get("app_secret"),
            "redirect_uri": config.get("redirect_uri"),
            "code": code
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://graph.facebook.com/v18.0/oauth/access_token",
                params=params
            ) as resp:
                if resp.status == 200:
                    token_data = await resp.json()
                    
                    # 사용자 정보 및 페이지 정보 가져오기
                    user_info = await self._get_facebook_user_info(token_data["access_token"], session)
                    pages_info = await self._get_facebook_pages(token_data["access_token"], session)
                    
                    return {
                        "success": True,
                        "platform": "facebook",
                        "access_token": token_data["access_token"],
                        "token_type": token_data.get("token_type", "bearer"),
                        "expires_in": token_data.get("expires_in"),
                        "user_info": user_info,
                        "pages": pages_info
                    }
                else:
                    error_msg = await resp.text()
                    return {"success": False, "error": f"Facebook 토큰 교환 실패: {error_msg}"}
    
    async def _exchange_twitter_token(self, code: str) -> Dict[str, Any]:
        """Twitter Access Token 교환"""
        config = self.config.get("twitter", {})
        
        data = {
            "code": code,
            "grant_type": "authorization_code",
            "client_id": config.get("client_id"),
            "redirect_uri": config.get("redirect_uri"),
            "code_verifier": "challenge"  # PKCE
        }
        
        # Basic Auth 헤더
        credentials = f"{config.get('client_id')}:{config.get('client_secret')}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.twitter.com/2/oauth2/token",
                headers=headers,
                data=data
            ) as resp:
                if resp.status == 200:
                    token_data = await resp.json()
                    
                    # 사용자 정보 가져오기
                    user_info = await self._get_twitter_user_info(token_data["access_token"], session)
                    
                    return {
                        "success": True,
                        "platform": "twitter",
                        "access_token": token_data["access_token"],
                        "token_type": token_data.get("token_type", "bearer"),
                        "expires_in": token_data.get("expires_in"),
                        "refresh_token": token_data.get("refresh_token"),
                        "user_info": user_info
                    }
                else:
                    error_msg = await resp.text()
                    return {"success": False, "error": f"Twitter 토큰 교환 실패: {error_msg}"}
    
    async def _exchange_linkedin_token(self, code: str) -> Dict[str, Any]:
        """LinkedIn Access Token 교환"""
        config = self.config.get("linkedin", {})
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": config.get("redirect_uri"),
            "client_id": config.get("client_id"),
            "client_secret": config.get("client_secret")
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://www.linkedin.com/oauth/v2/accessToken",
                headers=headers,
                data=data
            ) as resp:
                if resp.status == 200:
                    token_data = await resp.json()
                    
                    # 사용자 정보 가져오기
                    user_info = await self._get_linkedin_user_info(token_data["access_token"], session)
                    
                    return {
                        "success": True,
                        "platform": "linkedin",
                        "access_token": token_data["access_token"],
                        "token_type": token_data.get("token_type", "bearer"),
                        "expires_in": token_data.get("expires_in"),
                        "user_info": user_info
                    }
                else:
                    error_msg = await resp.text()
                    return {"success": False, "error": f"LinkedIn 토큰 교환 실패: {error_msg}"}
    
    # ===== 사용자 정보 가져오기 =====
    
    async def _get_facebook_user_info(self, access_token: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Facebook 사용자 정보 가져오기"""
        try:
            async with session.get(
                f"https://graph.facebook.com/v18.0/me?fields=id,name,email&access_token={access_token}"
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {}
        except Exception as e:
            logger.error(f"Facebook 사용자 정보 가져오기 실패: {e}")
            return {}
    
    async def _get_facebook_pages(self, access_token: str, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """Facebook 페이지 목록 가져오기"""
        try:
            async with session.get(
                f"https://graph.facebook.com/v18.0/me/accounts?access_token={access_token}"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data", [])
                return []
        except Exception as e:
            logger.error(f"Facebook 페이지 정보 가져오기 실패: {e}")
            return []
    
    async def _get_twitter_user_info(self, access_token: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Twitter 사용자 정보 가져오기"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            async with session.get(
                "https://api.twitter.com/2/users/me",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data", {})
                return {}
        except Exception as e:
            logger.error(f"Twitter 사용자 정보 가져오기 실패: {e}")
            return {}
    
    async def _get_linkedin_user_info(self, access_token: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """LinkedIn 사용자 정보 가져오기"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            async with session.get(
                "https://api.linkedin.com/v2/me",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {}
        except Exception as e:
            logger.error(f"LinkedIn 사용자 정보 가져오기 실패: {e}")
            return {}
    
    # ===== 토큰 관리 =====
    
    def store_token(self, user_id: str, platform: str, token_data: Dict[str, Any]) -> bool:
        """토큰 저장"""
        try:
            key = f"token_{user_id}_{platform}"
            token_data["stored_at"] = datetime.now().isoformat()
            self.tokens_storage[key] = token_data
            
            logger.info(f"토큰 저장 완료: {platform} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"토큰 저장 실패: {e}")
            return False
    
    def get_token(self, user_id: str, platform: str) -> Optional[Dict[str, Any]]:
        """저장된 토큰 가져오기"""
        try:
            key = f"token_{user_id}_{platform}"
            return self.tokens_storage.get(key)
        except Exception as e:
            logger.error(f"토큰 가져오기 실패: {e}")
            return None
    
    async def refresh_token(self, user_id: str, platform: str) -> Dict[str, Any]:
        """토큰 갱신"""
        try:
            stored_token = self.get_token(user_id, platform)
            if not stored_token:
                return {"success": False, "error": "저장된 토큰이 없습니다"}
            
            refresh_token = stored_token.get("refresh_token")
            if not refresh_token:
                return {"success": False, "error": "Refresh token이 없습니다"}
            
            if platform.lower() == "twitter":
                return await self._refresh_twitter_token(refresh_token)
            else:
                return {"success": False, "error": f"{platform}는 토큰 갱신을 지원하지 않습니다"}
                
        except Exception as e:
            logger.error(f"토큰 갱신 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _refresh_twitter_token(self, refresh_token: str) -> Dict[str, Any]:
        """Twitter 토큰 갱신"""
        config = self.config.get("twitter", {})
        
        data = {
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "client_id": config.get("client_id")
        }
        
        # Basic Auth 헤더
        credentials = f"{config.get('client_id')}:{config.get('client_secret')}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.twitter.com/2/oauth2/token",
                headers=headers,
                data=data
            ) as resp:
                if resp.status == 200:
                    token_data = await resp.json()
                    return {
                        "success": True,
                        "access_token": token_data["access_token"],
                        "token_type": token_data.get("token_type", "bearer"),
                        "expires_in": token_data.get("expires_in"),
                        "refresh_token": token_data.get("refresh_token", refresh_token)
                    }
                else:
                    error_msg = await resp.text()
                    return {"success": False, "error": f"토큰 갱신 실패: {error_msg}"}
    
    def is_token_valid(self, user_id: str, platform: str) -> bool:
        """토큰 유효성 검사"""
        try:
            token_data = self.get_token(user_id, platform)
            if not token_data:
                return False
            
            # 만료 시간 확인
            expires_in = token_data.get("expires_in")
            stored_at = token_data.get("stored_at")
            
            if expires_in and stored_at:
                stored_time = datetime.fromisoformat(stored_at)
                expiry_time = stored_time + timedelta(seconds=expires_in)
                return datetime.now() < expiry_time
            
            return True  # 만료 정보가 없으면 유효한 것으로 간주
            
        except Exception as e:
            logger.error(f"토큰 유효성 검사 실패: {e}")
            return False
    
    # ===== 게시물 발행 (통합 인터페이스) =====
    
    async def publish_post(self, user_id: str, platform: str, content: str, 
                          hashtags: List[str] = None, image_urls: List[str] = None, 
                          additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """통합 게시물 발행"""
        try:
            # 토큰 가져오기
            token_data = self.get_token(user_id, platform)
            if not token_data:
                return {"success": False, "error": "인증 토큰이 없습니다. 먼저 계정을 연동해주세요."}
            
            access_token = token_data["access_token"]
            
            # 토큰 유효성 검사
            if not self.is_token_valid(user_id, platform):
                # 토큰 갱신 시도
                refresh_result = await self.refresh_token(user_id, platform)
                if refresh_result.get("success"):
                    # 새 토큰으로 업데이트
                    token_data.update(refresh_result)
                    self.store_token(user_id, platform, token_data)
                    access_token = refresh_result["access_token"]
                else:
                    return {"success": False, "error": "토큰이 만료되었습니다. 다시 인증해주세요."}
            
            # 플랫폼별 게시
            if platform.lower() == "facebook":
                return await self.publish_to_facebook(
                    content, image_urls or [], access_token, additional_data or {}
                )
            elif platform.lower() == "instagram":
                return await self.publish_to_instagram(
                    content, hashtags or [], image_urls or [], access_token, additional_data or {}
                )
            elif platform.lower() == "twitter":
                return await self.publish_to_twitter(
                    content, hashtags or [], image_urls or [], access_token, additional_data or {}
                )
            elif platform.lower() == "linkedin":
                return await self.publish_to_linkedin(
                    content, image_urls or [], access_token, additional_data or {}
                )
            else:
                return {"success": False, "error": f"지원하지 않는 플랫폼: {platform}"}
                
        except Exception as e:
            logger.error(f"게시물 발행 실패 ({platform}): {e}")
            return {"success": False, "error": str(e)}
    
    # ===== 플랫폼별 게시물 발행 함수들 =====
    
    async def publish_to_facebook(self, content: str, image_urls: List[str], 
                                 access_token: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Facebook 게시물 발행 (Facebook Graph API)"""
        try:
            page_id = task_data.get("page_id")
            if not page_id:
                return {"success": False, "error": "Facebook Page ID가 필요합니다"}
            
            async with aiohttp.ClientSession() as session:
                if image_urls:
                    # 이미지가 있는 경우
                    if len(image_urls) == 1:
                        # 단일 이미지
                        post_data = {
                            "message": content,
                            "url": image_urls[0],
                            "access_token": access_token
                        }
                        url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
                    else:
                        # 다중 이미지 - 각각 업로드 후 한 번에 게시
                        photo_ids = []
                        for image_url in image_urls:
                            photo_data = {
                                "url": image_url,
                                "published": "false",
                                "access_token": access_token
                            }
                            
                            async with session.post(f"https://graph.facebook.com/v18.0/{page_id}/photos", data=photo_data) as resp:
                                if resp.status == 200:
                                    photo_result = await resp.json()
                                    photo_ids.append({"media_fbid": photo_result["id"]})
                                else:
                                    error_msg = await resp.text()
                                    return {"success": False, "error": f"이미지 업로드 실패: {error_msg}"}
                        
                        # 다중 이미지 게시물 생성
                        post_data = {
                            "message": content,
                            "attached_media": json.dumps(photo_ids),
                            "access_token": access_token
                        }
                        url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
                else:
                    # 텍스트 전용
                    post_data = {
                        "message": content,
                        "access_token": access_token
                    }
                    url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
                
                async with session.post(url, data=post_data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        post_id = result["id"]
                        
                        logger.info(f"Facebook 게시물 발행 성공: {post_id}")
                        return {
                            "success": True,
                            "post_id": post_id,
                            "post_url": f"https://www.facebook.com/{post_id}"
                        }
                    else:
                        error_msg = await resp.text()
                        logger.error(f"Facebook 게시물 발행 실패: {error_msg}")
                        return {"success": False, "error": error_msg}
                        
        except Exception as e:
            logger.error(f"Facebook 게시물 발행 중 오류: {e}")
            return {"success": False, "error": str(e)}
    
    async def publish_to_instagram(self, content: str, hashtags: List[str], image_urls: List[str], 
                                  access_token: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Instagram 게시물 발행 (Instagram Graph API)"""
        try:
            # Instagram은 Business 계정과 Facebook 페이지가 필요
            instagram_business_account_id = task_data.get("instagram_business_account_id")
            if not instagram_business_account_id:
                return {"success": False, "error": "Instagram Business Account ID가 필요합니다"}
            
            # 해시태그 추가
            if hashtags:
                content += " " + " ".join([f"#{tag}" for tag in hashtags])
            
            async with aiohttp.ClientSession() as session:
                # 이미지가 있는 경우
                if image_urls:
                    # 이미지 컨테이너 생성
                    containers = []
                    for image_url in image_urls:
                        container_data = {
                            "image_url": image_url,
                            "caption": content if len(image_urls) == 1 else "",
                            "access_token": access_token
                        }
                        
                        container_url = f"https://graph.facebook.com/v18.0/{instagram_business_account_id}/media"
                        async with session.post(container_url, data=container_data) as resp:
                            if resp.status == 200:
                                container_result = await resp.json()
                                containers.append(container_result["id"])
                            else:
                                error_msg = await resp.text()
                                logger.error(f"Instagram 이미지 컨테이너 생성 실패: {error_msg}")
                                return {"success": False, "error": f"이미지 업로드 실패: {error_msg}"}
                    
                    # 게시물 발행
                    if len(containers) == 1:
                        # 단일 이미지
                        publish_data = {
                            "creation_id": containers[0],
                            "access_token": access_token
                        }
                    else:
                        # 다중 이미지 (캐러셀)
                        publish_data = {
                            "media_type": "CAROUSEL",
                            "children": ",".join(containers),
                            "caption": content,
                            "access_token": access_token
                        }
                        
                        # 캐러셀 컨테이너 생성
                        container_url = f"https://graph.facebook.com/v18.0/{instagram_business_account_id}/media"
                        async with session.post(container_url, data=publish_data) as resp:
                            if resp.status == 200:
                                container_result = await resp.json()
                                publish_data = {
                                    "creation_id": container_result["id"],
                                    "access_token": access_token
                                }
                            else:
                                error_msg = await resp.text()
                                return {"success": False, "error": f"캐러셀 생성 실패: {error_msg}"}
                else:
                    # 텍스트 전용 게시물은 Instagram에서 지원하지 않음
                    return {"success": False, "error": "Instagram은 이미지가 포함된 게시물만 지원합니다"}
                
                # 최종 발행
                publish_url = f"https://graph.facebook.com/v18.0/{instagram_business_account_id}/media_publish"
                async with session.post(publish_url, data=publish_data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        post_id = result["id"]
                        
                        logger.info(f"Instagram 게시물 발행 성공: {post_id}")
                        return {
                            "success": True,
                            "post_id": post_id,
                            "post_url": f"https://www.instagram.com/p/{post_id}"
                        }
                    else:
                        error_msg = await resp.text()
                        logger.error(f"Instagram 게시물 발행 실패: {error_msg}")
                        return {"success": False, "error": error_msg}
                        
        except Exception as e:
            logger.error(f"Instagram 게시물 발행 중 오류: {e}")
            return {"success": False, "error": str(e)}
    
    async def publish_to_twitter(self, content: str, hashtags: List[str], image_urls: List[str], 
                                access_token: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Twitter/X 게시물 발행 (Twitter API v2)"""
        try:
            # Twitter API v2는 Bearer Token 또는 OAuth 2.0 사용
            bearer_token = access_token
            
            # 해시태그 추가
            if hashtags:
                content += " " + " ".join([f"#{tag}" for tag in hashtags])
            
            # 문자 수 제한 확인 (280자)
            if len(content) > 280:
                content = content[:277] + "..."
            
            headers = {
                "Authorization": f"Bearer {bearer_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                if image_urls:
                    # 이미지 업로드 (Twitter API v1.1 사용)
                    media_ids = []
                    for image_url in image_urls:
                        # 이미지 다운로드 및 업로드
                        async with session.get(image_url) as img_resp:
                            if img_resp.status == 200:
                                image_data = await img_resp.read()
                                
                                # Twitter 미디어 업로드
                                upload_headers = {
                                    "Authorization": f"Bearer {bearer_token}"
                                }
                                
                                upload_data = aiohttp.FormData()
                                upload_data.add_field('media', image_data, filename='image.jpg')
                                
                                async with session.post(
                                    "https://upload.twitter.com/1.1/media/upload.json",
                                    headers=upload_headers,
                                    data=upload_data
                                ) as upload_resp:
                                    if upload_resp.status == 200:
                                        upload_result = await upload_resp.json()
                                        media_ids.append(upload_result["media_id_string"])
                                    else:
                                        error_msg = await upload_resp.text()
                                        return {"success": False, "error": f"이미지 업로드 실패: {error_msg}"}
                    
                    # 트윗 생성 (이미지 포함)
                    tweet_data = {
                        "text": content,
                        "media": {
                            "media_ids": media_ids
                        }
                    }
                else:
                    # 텍스트 전용 트윗
                    tweet_data = {
                        "text": content
                    }
                
                async with session.post(
                    "https://api.twitter.com/2/tweets",
                    headers=headers,
                    json=tweet_data
                ) as resp:
                    if resp.status == 201:
                        result = await resp.json()
                        tweet_id = result["data"]["id"]
                        
                        logger.info(f"Twitter 게시물 발행 성공: {tweet_id}")
                        return {
                            "success": True,
                            "post_id": tweet_id,
                            "post_url": f"https://twitter.com/i/status/{tweet_id}"
                        }
                    else:
                        error_msg = await resp.text()
                        logger.error(f"Twitter 게시물 발행 실패: {error_msg}")
                        return {"success": False, "error": error_msg}
                        
        except Exception as e:
            logger.error(f"Twitter 게시물 발행 중 오류: {e}")
            return {"success": False, "error": str(e)}
    
    async def publish_to_linkedin(self, content: str, image_urls: List[str], 
                                 access_token: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """LinkedIn 게시물 발행 (LinkedIn API)"""
        try:
            person_urn = task_data.get("person_urn")  # urn:li:person:PERSON_ID
            organization_urn = task_data.get("organization_urn")  # 회사 페이지용
            
            if not person_urn and not organization_urn:
                return {"success": False, "error": "LinkedIn Person URN 또는 Organization URN이 필요합니다"}
            
            author_urn = organization_urn if organization_urn else person_urn
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            async with aiohttp.ClientSession() as session:
                if image_urls:
                    # 이미지 업로드
                    media_assets = []
                    for image_url in image_urls:
                        # 미디어 자산 등록
                        register_data = {
                            "registerUploadRequest": {
                                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                                "owner": author_urn,
                                "serviceRelationships": [
                                    {
                                        "relationshipType": "OWNER",
                                        "identifier": "urn:li:userGeneratedContent"
                                    }
                                ]
                            }
                        }
                        
                        async with session.post(
                            "https://api.linkedin.com/v2/assets?action=registerUpload",
                            headers=headers,
                            json=register_data
                        ) as register_resp:
                            if register_resp.status == 200:
                                register_result = await register_resp.json()
                                upload_url = register_result["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
                                asset_id = register_result["value"]["asset"]
                                
                                # 이미지 업로드
                                async with session.get(image_url) as img_resp:
                                    if img_resp.status == 200:
                                        image_data = await img_resp.read()
                                        
                                        upload_headers = {
                                            "Authorization": f"Bearer {access_token}"
                                        }
                                        
                                        async with session.put(
                                            upload_url,
                                            headers=upload_headers,
                                            data=image_data
                                        ) as upload_resp:
                                            if upload_resp.status == 201:
                                                media_assets.append(asset_id)
                                            else:
                                                error_msg = await upload_resp.text()
                                                return {"success": False, "error": f"이미지 업로드 실패: {error_msg}"}
                                    else:
                                        return {"success": False, "error": "이미지 다운로드 실패"}
                            else:
                                error_msg = await register_resp.text()
                                return {"success": False, "error": f"미디어 등록 실패: {error_msg}"}
                    
                    # 이미지가 포함된 게시물
                    post_data = {
                        "author": author_urn,
                        "lifecycleState": "PUBLISHED",
                        "specificContent": {
                            "com.linkedin.ugc.ShareContent": {
                                "shareCommentary": {
                                    "text": content
                                },
                                "shareMediaCategory": "IMAGE",
                                "media": [
                                    {
                                        "status": "READY",
                                        "description": {
                                            "text": "Image"
                                        },
                                        "media": asset_id,
                                        "title": {
                                            "text": "Image"
                                        }
                                    } for asset_id in media_assets
                                ]
                            }
                        },
                        "visibility": {
                            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                        }
                    }
                else:
                    # 텍스트 전용 게시물
                    post_data = {
                        "author": author_urn,
                        "lifecycleState": "PUBLISHED",
                        "specificContent": {
                            "com.linkedin.ugc.ShareContent": {
                                "shareCommentary": {
                                    "text": content
                                },
                                "shareMediaCategory": "NONE"
                            }
                        },
                        "visibility": {
                            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                        }
                    }
                
                async with session.post(
                    "https://api.linkedin.com/v2/ugcPosts",
                    headers=headers,
                    json=post_data
                ) as resp:
                    if resp.status == 201:
                        result = await resp.json()
                        post_id = result["id"]
                        
                        logger.info(f"LinkedIn 게시물 발행 성공: {post_id}")
                        return {
                            "success": True,
                            "post_id": post_id,
                            "post_url": f"https://www.linkedin.com/feed/update/{post_id}"
                        }
                    else:
                        error_msg = await resp.text()
                        logger.error(f"LinkedIn 게시물 발행 실패: {error_msg}")
                        return {"success": False, "error": error_msg}
                        
        except Exception as e:
            logger.error(f"LinkedIn 게시물 발행 중 오류: {e}")
            return {"success": False, "error": str(e)}
    
    # ===== 계정 연동 상태 확인 =====
    
    def get_connected_accounts(self, user_id: str) -> Dict[str, Any]:
        """연동된 계정 목록 조회"""
        connected = {}
        platforms = ["facebook", "twitter", "linkedin", "instagram"]
        
        for platform in platforms:
            token_data = self.get_token(user_id, platform)
            if token_data:
                connected[platform] = {
                    "connected": True,
                    "user_info": token_data.get("user_info", {}),
                    "connected_at": token_data.get("stored_at"),
                    "is_valid": self.is_token_valid(user_id, platform)
                }
            else:
                connected[platform] = {"connected": False}
        
        return connected
    
    def disconnect_account(self, user_id: str, platform: str) -> bool:
        """계정 연동 해제"""
        try:
            key = f"token_{user_id}_{platform}"
            if key in self.tokens_storage:
                del self.tokens_storage[key]
                logger.info(f"계정 연동 해제 완료: {platform} for user {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"계정 연동 해제 실패: {e}")
            return False


# ===== 사용 예시 =====

async def example_usage():
    """SNS Service 사용 예시"""
    
    # 1. 서비스 초기화
    config = {
        "facebook": {
            "app_id": "your_facebook_app_id",
            "app_secret": "your_facebook_app_secret",
            "redirect_uri": "http://localhost:8000/auth/facebook/callback"
        },
        "twitter": {
            "client_id": "your_twitter_client_id", 
            "client_secret": "your_twitter_client_secret",
            "redirect_uri": "http://localhost:8000/auth/twitter/callback"
        },
        "linkedin": {
            "client_id": "your_linkedin_client_id",
            "client_secret": "your_linkedin_client_secret", 
            "redirect_uri": "http://localhost:8000/auth/linkedin/callback"
        }
    }
    
    sns_service = SNSService(config)
    
    # 2. 인증 URL 생성
    auth_result = sns_service.generate_auth_url("facebook", "user123")
    if auth_result["success"]:
        print(f"Facebook 인증 URL: {auth_result['auth_url']}")
    
    # 3. 인증 완료 후 토큰 교환
    # token_result = await sns_service.exchange_code_for_token("facebook", "auth_code", "state")
    
    # 4. 토큰 저장
    # sns_service.store_token("user123", "facebook", token_result)
    
    # 5. 게시물 발행
    # publish_result = await sns_service.publish_post(
    #     user_id="user123",
    #     platform="facebook", 
    #     content="안녕하세요! 자동 게시물입니다.",
    #     hashtags=["자동화", "SNS"],
    #     additional_data={"page_id": "your_page_id"}
    # )
    
    # 6. 연동 계정 확인
    # connected_accounts = sns_service.get_connected_accounts("user123")
    # print(f"연동된 계정: {connected_accounts}")
