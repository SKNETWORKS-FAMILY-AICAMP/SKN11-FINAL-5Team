"""
Task Agent v3 공용 모듈
"""

from auth_manager import AuthManager, get_auth_manager
from http_client import HttpClient, OAuthHttpClient, get_http_client, get_oauth_http_client
from email_manager import EmailManager, get_email_manager
from config_manager import ConfigManager, get_config_manager, get_config
from db_helper import DatabaseHelper, RedisHelper, get_db_helper, get_redis_helper, get_db_session
from notification_manager import NotificationManager, get_notification_manager
from utils import (
    ValidationUtils, DateTimeUtils, SecurityUtils, DataUtils, URLUtils, RetryUtils, LogUtils,
    generate_uuid, get_current_timestamp, format_file_size, truncate_string
)

__version__ = "1.0.0"
__all__ = [
    # Auth Manager
    "AuthManager", "get_auth_manager",
    
    # HTTP Client
    "HttpClient", "OAuthHttpClient", "get_http_client", "get_oauth_http_client",
    
    # Email Manager
    "EmailManager", "get_email_manager",
    
    # Config Manager
    "ConfigManager", "get_config_manager", "get_config",
    
    # Database Helper
    "DatabaseHelper", "RedisHelper", "get_db_helper", "get_redis_helper", "get_db_session",
    
    # Notification Manager
    "NotificationManager", "get_notification_manager",
    
    # Utilities
    "ValidationUtils", "DateTimeUtils", "SecurityUtils", "DataUtils", "URLUtils", "RetryUtils", "LogUtils",
    "generate_uuid", "get_current_timestamp", "format_file_size", "truncate_string"
]
