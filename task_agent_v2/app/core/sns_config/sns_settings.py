"""
SNS 플랫폼별 설정 관리
각 플랫폼의 API 키, 액세스 토큰, 설정값들을 관리합니다.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class InstagramConfig:
    """Instagram Graph API 설정"""
    app_id: str
    app_secret: str
    access_token: str
    instagram_business_account_id: str
    page_id: str  # Facebook 페이지 ID (Instagram과 연결된)
    
    @classmethod
    def from_env(cls) -> 'InstagramConfig':
        return cls(
            app_id=os.getenv('INSTAGRAM_APP_ID', ''),
            app_secret=os.getenv('INSTAGRAM_APP_SECRET', ''),
            access_token=os.getenv('INSTAGRAM_ACCESS_TOKEN', ''),
            instagram_business_account_id=os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID', ''),
            page_id=os.getenv('FACEBOOK_PAGE_ID', '')
        )


@dataclass
class FacebookConfig:
    """Facebook Graph API 설정"""
    app_id: str
    app_secret: str
    access_token: str
    page_id: str
    
    @classmethod
    def from_env(cls) -> 'FacebookConfig':
        return cls(
            app_id=os.getenv('FACEBOOK_APP_ID', ''),
            app_secret=os.getenv('FACEBOOK_APP_SECRET', ''),
            access_token=os.getenv('FACEBOOK_ACCESS_TOKEN', ''),
            page_id=os.getenv('FACEBOOK_PAGE_ID', '')
        )


@dataclass
class TwitterConfig:
    """Twitter API v2 설정"""
    api_key: str
    api_secret: str
    bearer_token: str
    access_token: str
    access_token_secret: str
    
    @classmethod
    def from_env(cls) -> 'TwitterConfig':
        return cls(
            api_key=os.getenv('TWITTER_API_KEY', ''),
            api_secret=os.getenv('TWITTER_API_SECRET', ''),
            bearer_token=os.getenv('TWITTER_BEARER_TOKEN', ''),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN', ''),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET', '')
        )


@dataclass
class LinkedInConfig:
    """LinkedIn API 설정"""
    client_id: str
    client_secret: str
    access_token: str
    person_urn: Optional[str] = None  # 개인 계정용
    organization_urn: Optional[str] = None  # 회사 페이지용
    
    @classmethod
    def from_env(cls) -> 'LinkedInConfig':
        return cls(
            client_id=os.getenv('LINKEDIN_CLIENT_ID', ''),
            client_secret=os.getenv('LINKEDIN_CLIENT_SECRET', ''),
            access_token=os.getenv('LINKEDIN_ACCESS_TOKEN', ''),
            person_urn=os.getenv('LINKEDIN_PERSON_URN'),
            organization_urn=os.getenv('LINKEDIN_ORGANIZATION_URN')
        )


class SNSConfigManager:
    """SNS 설정 관리자"""
    
    def __init__(self):
        self.instagram = InstagramConfig.from_env()
        self.facebook = FacebookConfig.from_env()
        self.twitter = TwitterConfig.from_env()
        self.linkedin = LinkedInConfig.from_env()
    
    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """플랫폼별 설정 반환"""
        platform = platform.lower()
        
        if platform == "instagram":
            return {
                "access_token": self.instagram.access_token,
                "instagram_business_account_id": self.instagram.instagram_business_account_id,
                "page_id": self.instagram.page_id
            }
        elif platform == "facebook":
            return {
                "access_token": self.facebook.access_token,
                "page_id": self.facebook.page_id
            }
        elif platform in ["twitter", "x"]:
            return {
                "access_token": self.twitter.bearer_token,
                "api_key": self.twitter.api_key,
                "api_secret": self.twitter.api_secret
            }
        elif platform == "linkedin":
            return {
                "access_token": self.linkedin.access_token,
                "person_urn": self.linkedin.person_urn,
                "organization_urn": self.linkedin.organization_urn
            }
        else:
            raise ValueError(f"지원하지 않는 플랫폼: {platform}")
    
    def validate_platform_config(self, platform: str) -> bool:
        """플랫폼 설정 유효성 검사"""
        try:
            config = self.get_platform_config(platform)
            return bool(config.get("access_token"))
        except ValueError:
            return False


# 전역 설정 인스턴스
sns_config = SNSConfigManager()
