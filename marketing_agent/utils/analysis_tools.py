"""
마케팅 분석 도구 모듈
네이버 트렌드 분석, 인스타그램 해시태그 분석 등 MCP 기반 마케팅 도구
"""

import os
import json
import base64
import asyncio
import mcp
from mcp.client.streamable_http import streamablehttp_client
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MarketingAnalysisTools:
    """마케팅 분석 도구 클래스"""
    
    def __init__(self):
        """분석 도구 초기화"""
        self.config = self._get_config()
        self.smithery_api_key = "056f88d0-aa2e-4ea9-8f2d-382ba74dcb07"
        self.profile = "realistic-possum-fgq4Y7"
    
    def _get_config(self) -> Dict[str, str]:
        """환경 설정 로드"""
        try:
            from shared_modules import get_config
            env_config = get_config()
            return {
                'naver_client_id': env_config.NAVER_CLIENT_ID,
                'naver_client_secret': env_config.NAVER_CLIENT_SECRET,
                'smithery_api_key': getattr(env_config, 'SMITHERY_API_KEY', self.smithery_api_key)
            }
        except Exception as e:
            logger.warning(f"환경 설정 로드 실패: {e}")
            return {
                'naver_client_id': os.getenv('NAVER_CLIENT_ID'),
                'naver_client_secret': os.getenv('NAVER_CLIENT_SECRET'),
                'smithery_api_key': os.getenv('SMITHERY_API_KEY', self.smithery_api_key)
            }
    
    async def analyze_naver_trends(
        self, 
        keywords: List[str], 
        start_date: str = None, 
        end_date: str = None
    ) -> Dict[str, Any]:
        """네이버 검색어 트렌드 분석"""
        try:
            # 기본 날짜 설정
            if not start_date or not end_date:
                today = datetime.now()
                start_date = today.replace(day=1).strftime('%Y-%m-%d')
                end_date = today.strftime('%Y-%m-%d')
            
            # MCP 설정
            config_b64 = base64.b64encode(json.dumps({
                "NAVER_CLIENT_ID": self.config['naver_client_id'],
                "NAVER_CLIENT_SECRET": self.config['naver_client_secret']
            }).encode()).decode()
            
            url = f"https://server.smithery.ai/@isnow890/naver-search-mcp/mcp?config={config_b64}&api_key={self.config['smithery_api_key']}&profile={self.profile}"
            
            # 키워드 그룹 생성
            keyword_groups = []
            for i, keyword in enumerate(keywords[:5]):  # 최대 5개
                keyword_groups.append({
                    "groupName": keyword,
                    "keywords": [keyword]
                })
            
            async with streamablehttp_client(url) as (read_stream, write_stream, _):
                async with mcp.ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    result = await session.call_tool("datalab_search", {
                        "startDate": start_date,
                        "endDate": end_date,
                        "timeUnit": "month",
                        "keywordGroups": keyword_groups
                    })
                    
                    if result and not result.isError:
                        data = json.loads(result.content[0].text)
                        return {
                            "success": True,
                            "data": data.get("results", []),
                            "period": f"{start_date} ~ {end_date}",
                            "keywords": keywords
                        }
            
            return {"success": False, "error": "트렌드 분석 실패"}
            
        except Exception as e:
            logger.error(f"네이버 트렌드 분석 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_instagram_hashtags(
        self, 
        question: str, 
        user_hashtags: List[str] = None
    ) -> Dict[str, Any]:
        """인스타그램 해시태그 트렌드 분석"""
        try:
            # 해시태그 추출 및 처리
            hashtags_to_analyze = []
            
            if user_hashtags:
                base_hashtags = [tag.lstrip('#') for tag in user_hashtags]
                hashtags_to_analyze.extend(base_hashtags)
                
                # 유사 해시태그 추출 (LLM 활용)
                for tag in base_hashtags:
                    similar_tags = await self._extract_similar_hashtags(tag)
                    hashtags_to_analyze.extend(similar_tags)
            else:
                # 질문에서 키워드 추출
                extracted_tags = await self._extract_hashtags_from_question(question)
                hashtags_to_analyze.extend(extracted_tags)
            
            if not hashtags_to_analyze:
                return {"success": False, "error": "분석할 해시태그가 없습니다"}
            
            # 중복 제거
            hashtags_to_analyze = list(dict.fromkeys(hashtags_to_analyze))
            
            # MCP 설정
            config = {
                "APIFY_API_TOKEN": "apify_api_LAUmyixlrAn8cvwanbU9moalojDpaF2e0deQ"
            }
            config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
            url = f"https://server.smithery.ai/@HeurisTech/product-trends-mcp/mcp?config={config_b64}&api_key={self.smithery_api_key}&profile={self.profile}"
            
            async with streamablehttp_client(url) as (read_stream, write_stream, _):
                async with mcp.ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    result = await session.call_tool("insta_hashtag_scraper", {
                        "hashtags": hashtags_to_analyze,
                        "results_limit": 3000
                    })
                    
                    # 데이터 처리
                    data = json.loads(result.content[0].text)
                    posts = data.get('results', [])
                    
                    # 인기 해시태그 추출
                    popular_hashtags = []
                    for post in posts:
                        likes = post.get("likesCount", 0)
                        hashtags = post.get("hashtags", [])
                        if likes >= 10 and hashtags:
                            popular_hashtags.extend(hashtags)
                    
                    # 중복 제거 및 정제
                    unique_hashtags = list({tag for tag in popular_hashtags if tag and len(tag) > 1})
                    
                    return {
                        "success": True,
                        "searched_hashtags": hashtags_to_analyze,
                        "popular_hashtags": unique_hashtags[:30],  # 상위 30개
                        "total_posts": len(posts)
                    }
            
        except Exception as e:
            logger.error(f"인스타그램 해시태그 분석 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_instagram_content(self) -> Dict[str, Any]:
        """인스타그램 마케팅 콘텐츠 생성"""
        try:
            config = {
                "debug": False,
                "hyperFeedApiKey": "bee-7dc552d8-7dee-46f4-9869-4123dd34f7dd"
            }
            config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
            url = f"https://server.smithery.ai/@synthetic-ci/vibe-marketing/mcp?config={config_b64}&api_key={self.smithery_api_key}&profile={self.profile}"
            
            async with streamablehttp_client(url) as (read_stream, write_stream, _):
                async with mcp.ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    # 인스타그램 훅 생성
                    hooks_result = await session.call_tool("find-hooks", {
                        "network": "instagram",
                        "category": "promotional",
                        "limit": 5
                    })
                    
                    # AIDA 템플릿 생성
                    aida_result = await session.call_tool("get-copywriting-framework", {
                        "network": "instagram",
                        "framework": "aida"
                    })
                    
                    return {
                        "success": True,
                        "hooks": hooks_result.content[0].text if hooks_result.content else "",
                        "aida_template": aida_result.content[0].text if aida_result.content else "",
                        "frameworks_available": True
                    }
            
        except Exception as e:
            logger.error(f"인스타그램 콘텐츠 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_content": {
                    "hooks": "1. 제품의 핵심 가치 강조\n2. 고객 문제 해결 방법 제시\n3. 실제 사용 사례 공유",
                    "aida_template": "1. Attention: 주목을 끄는 제목\n2. Interest: 흥미 유발\n3. Desire: 구매 욕구 자극\n4. Action: 행동 유도"
                }
            }
    
    async def _extract_hashtags_from_question(self, question: str) -> List[str]:
        """질문에서 해시태그 추출 (LLM 활용)"""
        try:
            from shared_modules import get_llm_manager
            llm_manager = get_llm_manager()
            
            messages = [
                {"role": "system", "content": "사용자 질문에서 마케팅에 유용한 키워드를 5개 추출하세요. 쉼표로 구분하여 키워드만 출력하세요."},
                {"role": "user", "content": f"다음 질문에서 해시태그용 키워드를 추출해주세요: {question}"}
            ]
            
            result = llm_manager.generate_response_sync(messages)
            keywords = [kw.strip() for kw in result.split(',')]
            return [tag for tag in keywords if len(tag) > 1][:5]
            
        except Exception as e:
            logger.error(f"키워드 추출 실패: {e}")
            return []
    
    async def _extract_similar_hashtags(self, hashtag: str) -> List[str]:
        """유사 해시태그 추출 (LLM 활용)"""
        try:
            from shared_modules import get_llm_manager
            llm_manager = get_llm_manager()
            
            messages = [
                {"role": "system", "content": "주어진 해시태그와 유사한 키워드 5개를 추출하세요. 쉼표로 구분하여 키워드만 출력하세요."},
                {"role": "user", "content": f"다음 해시태그와 유사한 키워드를 추출해주세요: {hashtag}"}
            ]
            
            result = llm_manager.generate_response_sync(messages)
            keywords = [kw.strip() for kw in result.split(',')]
            return [tag for tag in keywords if len(tag) > 1][:5]
            
        except Exception as e:
            logger.error(f"유사 키워드 추출 실패: {e}")
            return []

# 전역 인스턴스
_analysis_tools = None

def get_marketing_analysis_tools() -> MarketingAnalysisTools:
    """마케팅 분석 도구 인스턴스 반환"""
    global _analysis_tools
    if _analysis_tools is None:
        _analysis_tools = MarketingAnalysisTools()
    return _analysis_tools
