"""
Marketing Agent MCP 패키지
워크플로우 기반 마케팅 자동화
"""

from .config import MCPConfig
from .workflow_config import WorkflowConfig, MCPServerConfig
from .client import SimpleMCPClient, get_tools, call_mcp_tool
# Marketing functionality moved to other modules
from .workflow_manager import MarketingWorkflowManager, run_marketing_workflow

__all__ = [
    # 기본 설정
    'MCPConfig',
    'WorkflowConfig', 
    'MCPServerConfig',
    
    # 기본 클라이언트
    'SimpleMCPClient',
    
    # 워크플로우 매니저
    'MarketingWorkflowManager',
    
    # 편의 함수들
    'get_tools',
    'call_mcp_tool',

    'run_marketing_workflow'
]

__version__ = "2.0.0"
