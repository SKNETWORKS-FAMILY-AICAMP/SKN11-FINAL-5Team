"""간단한 MCP 클라이언트"""

import mcp
from .streamable_http import streamablehttp_client
import asyncio
import logging
from typing import List, Dict, Any, Optional
from ..config import MCPConfig

logger = logging.getLogger(__name__)

class SimpleMCPClient:
    """간단한 MCP 클라이언트"""
    
    def __init__(self, config: MCPConfig = None):
        self.config = config or MCPConfig()
        self.url = self.config.get_full_url()
    
    async def connect_and_list_tools(self) -> List[str]:
        """서버에 연결하고 사용 가능한 도구 목록 조회"""
        try:
            async with streamablehttp_client(self.url) as (read_stream, write_stream, _):
                async with mcp.ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()
                    tool_names = [t.name for t in tools_result.tools]
                    logger.info(f"사용 가능한 도구: {', '.join(tool_names)}")
                    return tool_names
        except Exception as e:
            logger.error(f"MCP 연결 오류: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """특정 도구 호출"""
        try:
            async with streamablehttp_client(self.url) as (read_stream, write_stream, _):
                async with mcp.ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments or {})
                    logger.info(f"도구 '{tool_name}' 호출 성공")
                    return result
        except Exception as e:
            logger.error(f"도구 '{tool_name}' 호출 오류: {e}")
            return None

# 편의 함수들
async def get_tools() -> List[str]:
    """사용 가능한 도구 목록 조회"""
    client = SimpleMCPClient()
    return await client.connect_and_list_tools()

async def call_mcp_tool(tool_name: str, arguments: Dict[str, Any] = None) -> Any:
    """MCP 도구 호출"""
    client = SimpleMCPClient()
    return await client.call_tool(tool_name, arguments)