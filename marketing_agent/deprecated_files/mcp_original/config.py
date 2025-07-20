# MCP 설정 파일
import os
from dataclasses import dataclass

@dataclass
class MCPConfig:
    """MCP 클라이언트 설정"""
    apify_token: str = "apify_api_LAUmyixlrAn8cvwanbU9moalojDpaF2e0deQ"
    smithery_api_key: str = "056f88d0-aa2e-4ea9-8f2d-382ba74dcb07"
    profile: str = "realistic-possum-fgq4Y7"
    server_url: str = "https://server.smithery.ai/@HeurisTech/product-trends-mcp/mcp"

    def get_full_url(self) -> str:
        """완전한 서버 URL 생성"""
        import json
        import base64
        
        config = {"APIFY_API_TOKEN": self.apify_token}
        config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
        
        return f"{self.server_url}?config={config_b64}&api_key={self.smithery_api_key}&profile={self.profile}"
