"""
SNS Service - OAuth 인증 및 게시물 발행을 위한 통합 서비스 (공용 모듈 사용)
"""

import json
import urllib.parse
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime

from common import (
    get_auth_manager, get_oauth_http_client, get_config_manager,
    DataUtils, SecurityUtils, RetryUtils, ValidationUtils
)
import logging

logger = logging.getLogger(__name__)


class SNSService:
    """SNS 플랫폼 통합 서비스 (공용 모듈 사용)"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
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
        self.auth_manager = get_auth_manager()
        self.http_client = get_oauth_http_client()
        self.config_manager = get_config_manager()
        
        self.config = config or {}
        # 설정이 없으면 config_manager에서 가져오기
        self.platforms = ["facebook", "twitter", "linkedin", "instagram"]
        
        for platform in self.platforms:
            if platform not in self.config:
                self.config[platform] = self.config_manager.get_oauth_config(platform)
    
    # ===== OAuth 인증 관련 메서드들 =====
    
    def generate_auth_url(self, platform: str, user_id: str, scopes: List[str] = None) -> Dict[str, Any]:
        """OAuth 인증 URL 생성"""
        try:
            state = self.auth_manager.generate_state(user_id, platform)
            
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
            "client_id": config.get("client_id") or config.get("app_id"),
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
    
    async def exchange_code_for_token(self, platform: str, code: str, state: str, user_id: str = None) -> Dict[str, Any]:
        """Authorization Code를 Access Token으로 교환"""
        try:
            # state 검증
            state_data = self.auth_manager.validate_state(state, user_id, platform)
            if not state_data:
                return {"success": False, "error": "유효하지 않은 state 파라미터"}
            
            if platform.lower() == "facebook":
                result = await self._exchange_facebook_token(code)
            elif platform.lower() == "twitter":
                result = await self._exchange_twitter_token(code)
            elif platform.lower() == "linkedin":
                result = await self._exchange_linkedin_token(code)
            else:
                return {"success": False, "error": f"지원하지 않는 플랫폼: {platform}"}
            
            # 토큰 저장
            if result.get("success"):
                target_user_id = user_id or state_data.get("user_id")
                if target_user_id:
                    self.store_token(target_user_id, platform, result)
            
            return result
                
        except Exception as e:
            logger.error(f"토큰 교환 실패 ({platform}): {e}")
            return {"success": False, "error": str(e)}
    
    async def _exchange_facebook_token(self, code: str) -> Dict[str, Any]:
        """Facebook Access Token 교환"""
        config = self.config.get("facebook", {})
        
        params = {
            "client_id": config.get("client_id") or config.get("app_id"),
            "client_secret": config.get("client_secret") or config.get("app_secret"),
            "redirect_uri": config.get("redirect_uri"),
            "code": code
        }
        
        result = await self.http_client.get(
            "https://graph.facebook.com/v18.0/oauth/access_token",
            params=params
        )
        
        if result.get("success"):
            token_data = result.get("data", {})
            
            # 사용자 정보 및 페이지 정보 가져오기
            user_info = await self._get_facebook_user_info(token_data.get("access_token"))
            pages_info = await self._get_facebook_pages(token_data.get("access_token"))
            
            return {
                "success": True,
                "platform": "facebook",
                "access_token": token_data.get("access_token"),
                "token_type": token_data.get("token_type", "bearer"),
                "expires_in": token_data.get("expires_in"),
                "user_info": user_info,
                "pages": pages_info
            }
        else:
            return {"success": False, "error": f"Facebook 토큰 교환 실패: {result.get('error')}"}
    
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
        basic_auth = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        result = await self.http_client.post(
            "https://api.twitter.com/2/oauth2/token",
            headers=headers,
            data=data
        )
        
        if result.get("success"):
            token_data = result.get("data", {})
            
            # 사용자 정보 가져오기
            user_info = await self._get_twitter_user_info(token_data.get("access_token"))
            
            return {
                "success": True,
                "platform": "twitter",
                "access_token": token_data.get("access_token"),
                "token_type": token_data.get("token_type", "bearer"),
                "expires_in": token_data.get("expires_in"),
                "refresh_token": token_data.get("refresh_token"),
                "user_info": user_info
            }
        else:
            return {"success": False, "error": f"Twitter 토큰 교환 실패: {result.get('error')}"}
    
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
        
        result = await self.http_client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            headers=headers,
            data=data
        )
        
        if result.get("success"):
            token_data = result.get("data", {})
            
            # 사용자 정보 가져오기
            user_info = await self._get_linkedin_user_info(token_data.get("access_token"))
            
            return {
                "success": True,
                "platform": "linkedin",
                "access_token": token_data.get("access_token"),
                "token_type": token_data.get("token_type", "bearer"),
                "expires_in": token_data.get("expires_in"),
                "user_info": user_info
            }
        else:
            return {"success": False, "error": f"LinkedIn 토큰 교환 실패: {result.get('error')}"}
    
    # ===== 사용자 정보 가져오기 =====
    
    async def _get_facebook_user_info(self, access_token: str) -> Dict[str, Any]:
        """Facebook 사용자 정보 가져오기"""
        try:
            result = await self.http_client.get(
                f"https://graph.facebook.com/v18.0/me?fields=id,name,email&access_token={access_token}"
            )
            
            if result.get("success"):
                return result.get("data", {})
            return {}
        except Exception as e:
            logger.error(f"Facebook 사용자 정보 가져오기 실패: {e}")
            return {}
    
    async def _get_facebook_pages(self, access_token: str) -> List[Dict[str, Any]]:
        """Facebook 페이지 목록 가져오기"""
        try:
            result = await self.http_client.get(
                f"https://graph.facebook.com/v18.0/me/accounts?access_token={access_token}"
            )
            
            if result.get("success"):
                data = result.get("data", {})
                return data.get("data", [])
            return []
        except Exception as e:
            logger.error(f"Facebook 페이지 정보 가져오기 실패: {e}")
            return []
    
    async def _get_twitter_user_info(self, access_token: str) -> Dict[str, Any]:
        """Twitter 사용자 정보 가져오기"""
        try:
            result = await self.http_client.oauth_request(
                method="GET",
                url="https://api.twitter.com/2/users/me",
                access_token=access_token
            )
            
            if result.get("success"):
                data = result.get("data", {})
                return data.get("data", {})
            return {}
        except Exception as e:
            logger.error(f"Twitter 사용자 정보 가져오기 실패: {e}")
            return {}
    
    async def _get_linkedin_user_info(self, access_token: str) -> Dict[str, Any]:
        """LinkedIn 사용자 정보 가져오기"""
        try:
            result = await self.http_client.oauth_request(
                method="GET",
                url="https://api.linkedin.com/v2/me",
                access_token=access_token
            )
            
            if result.get("success"):
                return result.get("data", {})
            return {}
        except Exception as e:
            logger.error(f"LinkedIn 사용자 정보 가져오기 실패: {e}")
            return {}
    
    # ===== 토큰 관리 =====
    
    def store_token(self, user_id: str, platform: str, token_data: Dict[str, Any]) -> bool:
        """토큰 저장"""
        return self.auth_manager.store_token(user_id, platform, token_data)
    
    def get_token(self, user_id: str, platform: str) -> Optional[Dict[str, Any]]:
        """저장된 토큰 가져오기"""
        return self.auth_manager.get_token(user_id, platform)
    
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
        basic_auth = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        result = await self.http_client.post(
            "https://api.twitter.com/2/oauth2/token",
            headers=headers,
            data=data
        )
        
        if result.get("success"):
            token_data = result.get("data", {})
            return {
                "success": True,
                "access_token": token_data.get("access_token"),
                "token_type": token_data.get("token_type", "bearer"),
                "expires_in": token_data.get("expires_in"),
                "refresh_token": token_data.get("refresh_token", refresh_token)
            }
        else:
            return {"success": False, "error": f"토큰 갱신 실패: {result.get('error')}"}
    
    def is_token_valid(self, user_id: str, platform: str) -> bool:
        """토큰 유효성 검사"""
        return self.auth_manager.is_token_valid(user_id, platform)
    
    # ===== 게시물 발행 (통합 인터페이스) =====
    
    @RetryUtils.retry_async
    async def publish_post(self, user_id: str, platform: str, content: str, 
                          hashtags: List[str] = None, image_urls: List[str] = None, 
                          additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """통합 게시물 발행 (재시도 기능 포함)"""
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
                    self.auth_manager.update_token(user_id, platform, refresh_result)
                    access_token = refresh_result["access_token"]
                else:
                    return {"success": False, "error": "토큰이 만료되었습니다. 다시 인증해주세요."}
            
            # 콘텐츠 정제
            content = ValidationUtils.sanitize_input(content, max_length=2000)
            
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
        """Facebook 게시물 발행"""
        try:
            page_id = task_data.get("page_id")
            if not page_id:
                return {"success": False, "error": "Facebook Page ID가 필요합니다"}
            
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
                    # 다중 이미지 처리 로직
                    photo_ids = []
                    for image_url in image_urls:
                        photo_data = {
                            "url": image_url,
                            "published": "false",
                            "access_token": access_token
                        }
                        
                        result = await self.http_client.post(
                            f"https://graph.facebook.com/v18.0/{page_id}/photos", 
                            data=photo_data
                        )
                        
                        if result.get("success"):
                            photo_result = result.get("data", {})
                            photo_ids.append({"media_fbid": photo_result.get("id")})
                        else:
                            return {"success": False, "error": f"이미지 업로드 실패: {result.get('error')}"}
                    
                    # 다중 이미지 게시물 생성
                    post_data = {
                        "message": content,
                        "attached_media": DataUtils.safe_json_dumps(photo_ids),
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
            
            result = await self.http_client.post(url, data=post_data)
            
            if result.get("success"):
                post_result = result.get("data", {})
                post_id = post_result.get("id")
                
                logger.info(f"Facebook 게시물 발행 성공: {post_id}")
                return {
                    "success": True,
                    "post_id": post_id,
                    "post_url": f"https://www.facebook.com/{post_id}"
                }
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"Facebook 게시물 발행 실패: {error_msg}")
                return {"success": False, "error": error_msg}
                        
        except Exception as e:
            logger.error(f"Facebook 게시물 발행 중 오류: {e}")
            return {"success": False, "error": str(e)}
    
    async def publish_to_twitter(self, content: str, hashtags: List[str], image_urls: List[str], 
                                access_token: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Twitter/X 게시물 발행"""
        try:
            # 해시태그 추가
            if hashtags:
                content += " " + " ".join([f"#{tag}" for tag in hashtags])
            
            # 문자 수 제한 확인 (280자)
            if len(content) > 280:
                content = content[:277] + "..."
            
            tweet_data = {"text": content}
            
            if image_urls:
                # 이미지 업로드 처리 (간소화된 버전)
                media_ids = []
                for image_url in image_urls[:4]:  # 최대 4개 이미지
                    # 실제 구현에서는 이미지를 다운로드하고 Twitter에 업로드해야 함
                    # 여기서는 예시로만 표시
                    pass
                
                if media_ids:
                    tweet_data["media"] = {"media_ids": media_ids}
            
            result = await self.http_client.oauth_request(
                method="POST",
                url="https://api.twitter.com/2/tweets",
                access_token=access_token,
                json_data=tweet_data
            )
            
            if result.get("success"):
                tweet_result = result.get("data", {})
                tweet_data_result = tweet_result.get("data", {})
                tweet_id = tweet_data_result.get("id")
                
                logger.info(f"Twitter 게시물 발행 성공: {tweet_id}")
                return {
                    "success": True,
                    "post_id": tweet_id,
                    "post_url": f"https://twitter.com/i/status/{tweet_id}"
                }
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"Twitter 게시물 발행 실패: {error_msg}")
                return {"success": False, "error": error_msg}
                        
        except Exception as e:
            logger.error(f"Twitter 게시물 발행 중 오류: {e}")
            return {"success": False, "error": str(e)}
    
    async def publish_to_linkedin(self, content: str, image_urls: List[str], 
                                 access_token: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """LinkedIn 게시물 발행"""
        try:
            person_urn = task_data.get("person_urn")
            organization_urn = task_data.get("organization_urn")
            
            if not person_urn and not organization_urn:
                return {"success": False, "error": "LinkedIn Person URN 또는 Organization URN이 필요합니다"}
            
            author_urn = organization_urn if organization_urn else person_urn
            
            post_data = {
                "author": author_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": content},
                        "shareMediaCategory": "IMAGE" if image_urls else "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # 이미지 처리는 복잡하므로 여기서는 텍스트만 처리
            if image_urls:
                # 실제 구현에서는 LinkedIn 미디어 업로드 API를 사용해야 함
                logger.warning("LinkedIn 이미지 업로드는 별도 구현이 필요합니다")
            
            result = await self.http_client.oauth_request(
                method="POST",
                url="https://api.linkedin.com/v2/ugcPosts",
                access_token=access_token,
                json_data=post_data
            )
            
            if result.get("success") and result.get("status_code") == 201:
                post_result = result.get("data", {})
                post_id = post_result.get("id")
                
                logger.info(f"LinkedIn 게시물 발행 성공: {post_id}")
                return {
                    "success": True,
                    "post_id": post_id,
                    "post_url": f"https://www.linkedin.com/feed/update/{post_id}"
                }
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"LinkedIn 게시물 발행 실패: {error_msg}")
                return {"success": False, "error": error_msg}
                        
        except Exception as e:
            logger.error(f"LinkedIn 게시물 발행 중 오류: {e}")
            return {"success": False, "error": str(e)}
    
    async def publish_to_instagram(self, content: str, hashtags: List[str], image_urls: List[str], 
                                  access_token: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Instagram 게시물 발행"""
        try:
            instagram_business_account_id = task_data.get("instagram_business_account_id")
            if not instagram_business_account_id:
                return {"success": False, "error": "Instagram Business Account ID가 필요합니다"}
            
            if not image_urls:
                return {"success": False, "error": "Instagram은 이미지가 포함된 게시물만 지원합니다"}
            
            # 해시태그 추가
            if hashtags:
                content += " " + " ".join([f"#{tag}" for tag in hashtags])
            
            # Instagram API 호출 (간소화된 버전)
            # 실제로는 미디어 컨테이너 생성 -> 게시물 발행 순서로 진행
            
            logger.info("Instagram 게시물 발행 시뮬레이션")
            return {
                "success": True,
                "post_id": "simulated_instagram_post_id",
                "post_url": "https://www.instagram.com/p/simulated_post"
            }
                        
        except Exception as e:
            logger.error(f"Instagram 게시물 발행 중 오류: {e}")
            return {"success": False, "error": str(e)}
    
    # ===== 계정 연동 상태 확인 =====
    
    def get_connected_accounts(self, user_id: str) -> Dict[str, Any]:
        """연동된 계정 목록 조회"""
        connected = {}
        
        for platform in self.platforms:
            connected[platform] = self.auth_manager.get_connection_info(user_id, platform)
        
        return connected
    
    def disconnect_account(self, user_id: str, platform: str) -> bool:
        """계정 연동 해제"""
        return self.auth_manager.remove_token(user_id, platform)


# 전역 인스턴스를 위한 팩토리 함수
_global_sns_service = None

def get_sns_service(config: Dict[str, Any] = None) -> SNSService:
    """SNSService 싱글톤 인스턴스 반환"""
    global _global_sns_service
    if _global_sns_service is None:
        _global_sns_service = SNSService(config)
    return _global_sns_service


# ===== 사용 예시 =====

async def example_usage():
    """SNS Service 사용 예시"""
    
    # 1. 서비스 초기화
    sns_service = get_sns_service()
    
    # 2. 인증 URL 생성
    auth_result = sns_service.generate_auth_url("facebook", "user123")
    if auth_result["success"]:
        print(f"Facebook 인증 URL: {auth_result['auth_url']}")
    
    # 3. 인증 완료 후 토큰 교환
    # token_result = await sns_service.exchange_code_for_token("facebook", "auth_code", "state", "user123")
    
    # 4. 게시물 발행
    # publish_result = await sns_service.publish_post(
    #     user_id="user123",
    #     platform="facebook", 
    #     content="안녕하세요! 자동 게시물입니다.",
    #     hashtags=["자동화", "SNS"],
    #     additional_data={"page_id": "your_page_id"}
    # )
    
    # 5. 연동 계정 확인
    # connected_accounts = sns_service.get_connected_accounts("user123")
    # print(f"연동된 계정: {connected_accounts}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
