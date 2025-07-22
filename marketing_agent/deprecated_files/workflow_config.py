"""
워크플로우 설정 관리 클래스
YAML 기반 워크플로우 설정을 로드하고 관리하는 유틸리티
"""

import yaml
import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class WorkflowConfigManager:
    """워크플로우 설정 관리자"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        
    def _get_default_config_path(self) -> str:
        """기본 설정 파일 경로 반환"""
        current_dir = Path(__file__).parent
        return str(current_dir / "workflow_config.yaml")
    
    def _load_config(self) -> Dict[str, Any]:
        """YAML 설정 파일 로드"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    return yaml.safe_load(file)
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """기본 설정 반환"""
        return {
            "workflow": {
                "name": "marketing_automation_workflow",
                "description": "기본 마케팅 워크플로우",
                "version": "1.0.0"
            },
            "mcp_servers": {
                "hashtag_generator": {
                    "url": "https://smithery.ai/server/@smithery-ai/hashtag-generator",
                    "tools": ["generate_hashtags"]
                },
                "naver_search": {
                    "url": "https://smithery.ai/server/@smithery-ai/naver-search-mcp", 
                    "tools": ["get_related_keywords"]
                },
                "vibe_marketing": {
                    "url": "https://smithery.ai/server/@synthetic-ci/vibe-marketing",
                    "tools": ["find-hooks"]
                },
                "meta_scheduler": {
                    "url": "https://smithery.ai/server/@midwest/meta-post-scheduler-mcp",
                    "tools": ["schedule_post", "post_now"]
                }
            },
            "platform_configs": {
                "instagram": {
                    "hashtag_limit": 30,
                    "character_limit": 2200,
                    "optimal_posting_times": {
                        "weekdays": ["08:00-09:00", "12:00-13:00", "19:00-21:00"],
                        "weekends": ["10:00-11:00", "14:00-15:00", "20:00-22:00"]
                    }
                },
                "naver_blog": {
                    "keyword_density": "2-3%",
                    "min_content_length": 1000,
                    "seo_requirements": [
                        "제목에 키워드 포함",
                        "소제목 활용", 
                        "이미지 ALT 텍스트",
                        "내부 링크 연결"
                    ]
                }
            }
        }
    
    def get_workflow_steps(self) -> List[Dict[str, Any]]:
        """워크플로우 단계 목록 반환"""
        return self.config.get("workflow", {}).get("steps", [])
    
    def get_mcp_server_url(self, server_name: str) -> Optional[str]:
        """MCP 서버 URL 반환"""
        servers = self.config.get("mcp_servers", {})
        server_config = servers.get(server_name, {})
        return server_config.get("url")
    
    def get_mcp_server_tools(self, server_name: str) -> List[str]:
        """MCP 서버의 사용 가능한 도구 목록 반환"""
        servers = self.config.get("mcp_servers", {})
        server_config = servers.get(server_name, {})
        return server_config.get("tools", [])
    
    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """플랫폼별 설정 반환"""
        platform_configs = self.config.get("platform_configs", {})
        return platform_configs.get(platform, {})
    
    def get_optimal_posting_times(self, platform: str) -> Dict[str, List[str]]:
        """플랫폼별 최적 포스팅 시간 반환"""
        platform_config = self.get_platform_config(platform)
        return platform_config.get("optimal_posting_times", {})
    
    def get_content_guidelines(self, platform: str) -> List[str]:
        """플랫폼별 콘텐츠 가이드라인 반환"""
        platform_config = self.get_platform_config(platform)
        return platform_config.get("content_guidelines", [])
    
    def get_analytics_config(self, platform: str) -> Dict[str, Any]:
        """플랫폼별 분석 설정 반환"""
        analytics = self.config.get("analytics", {})
        return analytics.get(platform, {})
    
    def get_automation_rules(self) -> Dict[str, Any]:
        """자동화 규칙 반환"""
        return self.config.get("automation_rules", {})
    
    def validate_workflow_step(self, step: Dict[str, Any]) -> bool:
        """워크플로우 단계 유효성 검증"""
        required_fields = ["step", "type"]
        return all(field in step for field in required_fields)
    
    def get_branch_condition(self, branch: Dict[str, Any]) -> str:
        """분기 조건 반환"""
        return branch.get("when", "")
    
    def get_step_by_name(self, step_name: str) -> Optional[Dict[str, Any]]:
        """이름으로 워크플로우 단계 검색"""
        steps = self.get_workflow_steps()
        for step in steps:
            if step.get("step") == step_name:
                return step
        return None
    
    def get_error_handling_config(self) -> Dict[str, Any]:
        """에러 처리 설정 반환"""
        return self.config.get("error_handling", {
            "retry_attempts": 3,
            "fallback_strategies": ["use_cached_content", "manual_intervention"],
            "notifications": {"channels": ["email"], "escalation_levels": ["error"]}
        })
    
    def save_config(self, config_path: Optional[str] = None) -> bool:
        """설정을 파일에 저장"""
        try:
            save_path = config_path or self.config_path
            with open(save_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.config, file, default_flow_style=False, allow_unicode=True)
            logger.info(f"Config saved to: {save_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """설정 업데이트"""
        def deep_update(base_dict: Dict, update_dict: Dict) -> Dict:
            """중첩된 딕셔너리 깊이 업데이트"""
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
            return base_dict
        
        deep_update(self.config, updates)
        logger.info("Config updated successfully")
    
    def get_security_config(self) -> Dict[str, Any]:
        """보안 설정 반환"""
        return self.config.get("security", {
            "api_keys": {"storage": "environment_variables"},
            "access_control": {"role_based": True, "audit_logging": True},
            "data_privacy": {"user_data_retention": "30_days", "anonymization": True}
        })
    
    def is_platform_supported(self, platform: str) -> bool:
        """플랫폼 지원 여부 확인"""
        supported_platforms = list(self.config.get("platform_configs", {}).keys())
        return platform.lower() in supported_platforms
    
    def get_supported_platforms(self) -> List[str]:
        """지원되는 플랫폼 목록 반환"""
        return list(self.config.get("platform_configs", {}).keys())
    
    def __str__(self) -> str:
        """설정 요약 정보 반환"""
        workflow_name = self.config.get("workflow", {}).get("name", "Unknown")
        version = self.config.get("workflow", {}).get("version", "Unknown")
        platforms = len(self.get_supported_platforms())
        servers = len(self.config.get("mcp_servers", {}))
        
        return f"WorkflowConfig(name='{workflow_name}', version='{version}', platforms={platforms}, servers={servers})"
    
    def to_json(self) -> str:
        """설정을 JSON 문자열로 변환"""
        return json.dumps(self.config, ensure_ascii=False, indent=2)
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """워크플로우 요약 정보 반환"""
        workflow_info = self.config.get("workflow", {})
        return {
            "name": workflow_info.get("name"),
            "description": workflow_info.get("description"),
            "version": workflow_info.get("version"),
            "supported_platforms": self.get_supported_platforms(),
            "mcp_servers": list(self.config.get("mcp_servers", {}).keys()),
            "steps_count": len(self.get_workflow_steps()),
            "automation_enabled": bool(self.get_automation_rules())
        }


# 글로벌 설정 인스턴스
_config_manager = None

def get_workflow_config() -> WorkflowConfigManager:
    """글로벌 워크플로우 설정 매니저 반환"""
    global _config_manager
    if _config_manager is None:
        _config_manager = WorkflowConfigManager()
    return _config_manager

def reload_workflow_config(config_path: Optional[str] = None) -> WorkflowConfigManager:
    """워크플로우 설정 재로드"""
    global _config_manager
    _config_manager = WorkflowConfigManager(config_path)
    return _config_manager
