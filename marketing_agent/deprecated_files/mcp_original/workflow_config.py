"""
MCP 서버 설정 - 각 단계별 MCP 서버 정보
"""

import os
import json
import base64
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class MCPServerConfig:
    """개별 MCP 서버 설정"""
    name: str
    url: str
    api_key: Optional[str] = None
    config: Optional[Dict] = None

@dataclass 
class WorkflowConfig:
    """워크플로우용 MCP 설정"""
    
    # 기본 설정
    config = {
    "APIFY_API_TOKEN": "apify_api_LAUmyixlrAn8cvwanbU9moalojDpaF2e0deQ"
    }
    apify_token: str = "apify_api_LAUmyixlrAn8cvwanbU9moalojDpaF2e0deQ"
    smithery_api_key: str = "056f88d0-aa2e-4ea9-8f2d-382ba74dcb07"
    config_b64 = base64.b64encode(json.dumps(config).encode()).decode()

    def __post_init__(self):
        """MCP 서버들 초기화"""
        self.servers = {
            # 해시태그 생성기 (Instagram용)
            "hashtag": MCPServerConfig(
                name="hashtag-generator",
                url = f"https://server.smithery.ai/@HeurisTech/product-trends-mcp/mcp?config={self.config_b64}&api_key={self.smithery_api_key}&profile=realistic-possum-fgq4Y7"
            ),
            
            # Vibe Marketing (콘텐츠 생성)
            "vibe_marketing": MCPServerConfig(
                name="vibe-marketing", 
                url=f"https://server.smithery.ai/@HeurisTech/vibe-marketing/mcp?api_key={self.smithery_api_key}&profile=realistic-possum-fgq4Y7"
            ),
            
            # 네이버 검색 (키워드 추천)
            "naver_search": MCPServerConfig(
                name="naver-search",
                url=f"https://server.smithery.ai/@HeurisTech/naver-search-mcp/mcp?api_key={self.smithery_api_key}&profile=realistic-possum-fgq4Y7"
            ),
            
            # Meta 포스트 스케줄러 (Instagram 포스팅)
            "meta_scheduler": MCPServerConfig(
                name="meta-post-scheduler",
                url=f"https://server.smithery.ai/@HeurisTech/meta-post-scheduler-mcp/mcp?api_key={self.smithery_api_key}&profile=realistic-possum-fgq4Y7"
            ),
            
            # Product Trends (기존)
            "product_trends": MCPServerConfig(
                name="product-trends",
                url=self._build_product_trends_url()
            )
        }
    
    def _build_product_trends_url(self) -> str:
        """Product Trends MCP URL 생성"""
        config = {"APIFY_API_TOKEN": self.apify_token}
        config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
        return f"https://server.smithery.ai/@HeurisTech/product-trends-mcp/mcp?config={config_b64}&api_key={self.smithery_api_key}&profile=realistic-possum-fgq4Y7"
    
    def get_server_url(self, server_name: str) -> str:
        """특정 서버 URL 조회"""
        if server_name in self.servers:
            return self.servers[server_name].url
        raise ValueError(f"알 수 없는 서버: {server_name}")
    
    def get_server_config(self, server_name: str) -> MCPServerConfig:
        """특정 서버 설정 조회"""
        if server_name in self.servers:
            return self.servers[server_name]
        raise ValueError(f"알 수 없는 서버: {server_name}")
