"""
마케팅 에이전트 핵심 컴포넌트들
각 컴포넌트를 개별 파일로 분리할 수 있는 구조
"""

from .topic_classifier import TopicClassifier
from .context_analyzer import ConversationContextAnalyzer  
from .insight_collector import MarketingInsightCollector
from .smart_retriever import SmartRetriever
from .response_generator import ResponseGenerator
from .template_recommender import TemplateRecommender

__all__ = [
    'TopicClassifier',
    'ConversationContextAnalyzer', 
    'MarketingInsightCollector',
    'SmartRetriever',
    'ResponseGenerator',
    'TemplateRecommender'
]
