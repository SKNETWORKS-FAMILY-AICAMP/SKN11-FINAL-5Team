"""
마케팅 워크플로우 매니저
사용자 정의 플로우에 따른 단계별 처리
"""

from ast import main
import mcp
from mcp.client.streamable_http import streamablehttp_client
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json

from .workflow_config import WorkflowConfig
from .client import SimpleMCPClient

logger = logging.getLogger(__name__)

class MarketingWorkflowManager:
    """마케팅 워크플로우 매니저"""
    
    def __init__(self):
        self.config = WorkflowConfig()
        self.selected_platform = None
        self.workflow_data = {}
    
    async def call_mcp_server(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """특정 MCP 서버의 도구 호출"""
        try:
            server_url = self.config.get_server_url(server_name)
            
            async with streamablehttp_client(server_url) as (read_stream, write_stream, _):
                async with mcp.ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    
                    # 결과 처리
                    if hasattr(result, 'content') and result.content:
                        return result.content[0].text if result.content[0].text else str(result)
                    return str(result)
                    
        except Exception as e:
            logger.error(f"MCP 서버 '{server_name}' 도구 '{tool_name}' 호출 오류: {e}")
            return f"오류 발생: {str(e)}"
    
    async def step1_interpret_user_input(self, user_request: str) -> str:
        """1️⃣ 사용자 입력 해석 (LLM)"""
        logger.info("1️⃣ 사용자 입력 해석 중...")
        
        # 간단한 LLM 해석 (실제로는 OpenAI API 등을 사용)
        interpreted = f"""
마케팅 분석 결과:
- 원본 요청: {user_request}
- 제품/서비스 타입: 감지된 키워드 기반 분류
- 타겟 고객층: 제품 특성에 따른 추정
- 마케팅 포인트: 차별화 요소 및 강점
- 추천 마케팅 방향: 감정적 연결 + 실용성 강조
        """
        
        self.workflow_data['original_request'] = user_request
        self.workflow_data['interpreted_request'] = interpreted
        
        logger.info("✅ 사용자 입력 해석 완료")
        return interpreted
    
    async def step2_select_platform(self, platform: Optional[str] = None) -> str:
        """2️⃣ 플랫폼 선택 (memory)"""
        logger.info("2️⃣ 플랫폼 선택 중...")
        
        if platform and platform.lower() in ['instagram', 'naver', 'blog']:
            if platform.lower() in ['naver', 'blog']:
                self.selected_platform = 'naver_blog'
            else:
                self.selected_platform = 'instagram'
        else:
            # 사용자에게 선택 요청
            self.selected_platform = 'instagram'  # 기본값
        
        self.workflow_data['selected_platform'] = self.selected_platform
        
        logger.info(f"✅ 플랫폼 선택 완료: {self.selected_platform}")
        return f"선택된 플랫폼: {self.selected_platform.upper()}"
    
    async def step3_get_recommendations(self) -> str:
        """3️⃣ 플랫폼별 추천 (해시태그 or 키워드)"""
        if self.selected_platform == 'instagram':
            return await self._get_hashtags()
        else:  # naver_blog
            return await self._get_keywords()
    
    async def _get_hashtags(self) -> str:
        """Instagram용 해시태그 추천"""
        logger.info("3️⃣ 해시태그 추천 중...")
        
        try:
            query = self.workflow_data.get('original_request', '')
            hashtags = await self.call_mcp_server(
                'hashtag',
                'insta_hashtag_scraper',
                {'query': query}
            )
            
            self.workflow_data['hashtags'] = hashtags
            logger.info("✅ 해시태그 추천 완료")
            return hashtags
            
        except Exception as e:
            logger.error(f"해시태그 추천 오류: {e}")
            # 기본 해시태그 제공
            default_hashtags = "#마케팅 #신제품 #추천 #좋아요 #팔로우"
            self.workflow_data['hashtags'] = default_hashtags
            return default_hashtags
    
    async def _get_keywords(self) -> str:
        """네이버 블로그용 키워드 추천"""
        logger.info("3️⃣ 키워드 추천 중...")
        
        try:
            query = self.workflow_data.get('original_request', '')
            keywords = await self.call_mcp_server(
                'naver_search',
                'get_related_keywords', 
                {'query': query}
            )
            
            self.workflow_data['keywords'] = keywords
            logger.info("✅ 키워드 추천 완료")
            return keywords
            
        except Exception as e:
            logger.error(f"키워드 추천 오류: {e}")
            # 기본 키워드 제공
            default_keywords = "마케팅, 신제품, 추천, 리뷰, 후기"
            self.workflow_data['keywords'] = default_keywords
            return default_keywords
    
    async def step4_generate_content(self) -> str:
        """4️⃣ 콘텐츠 생성 (vibe-marketing + 해시태그/키워드 포함)"""
        logger.info("4️⃣ 콘텐츠 생성 중...")
        
        try:
            # Vibe Marketing으로 기본 콘텐츠 생성
            platform_type = "instagram" if self.selected_platform == 'instagram' else "blog"
            context = self.workflow_data.get('interpreted_request', '')
            
            base_content = await self.call_mcp_server(
                'vibe_marketing',
                'find-hooks',
                {
                    'platform': platform_type,
                    'category': 'promotional',
                    'context': context,
                    'limit': 1
                }
            )
            
            # 플랫폼별 추천 요소 추가
            if self.selected_platform == 'instagram':
                hashtags = self.workflow_data.get('hashtags', '')
                final_content = f"{base_content}\n\n{hashtags}"
            else:  # naver_blog
                keywords = self.workflow_data.get('keywords', '')
                final_content = f"{base_content}\n\n🔍 관련 키워드: {keywords}"
            
            self.workflow_data['final_content'] = final_content
            logger.info("✅ 콘텐츠 생성 완료")
            return final_content
            
        except Exception as e:
            logger.error(f"콘텐츠 생성 오류: {e}")
            # 기본 콘텐츠 제공
            request = self.workflow_data.get('original_request', '')
            recommendations = self.workflow_data.get('hashtags' if self.selected_platform == 'instagram' else 'keywords', '')
            
            default_content = f"""
🎯 {request}

✨ 추천 포인트:
- 고품질의 우수한 제품
- 합리적인 가격대
- 차별화된 기능

{recommendations}
            """
            self.workflow_data['final_content'] = default_content
            return default_content
    
    async def step5_auto_posting(self) -> str:
        """5️⃣ 자동 포스팅"""
        if self.selected_platform == 'instagram':
            return await self._post_to_instagram()
        else:  # naver_blog
            return await self._post_to_naver_blog()
    
    async def _post_to_instagram(self) -> str:
        """Instagram 자동 포스팅 (meta-post-scheduler-mcp)"""
        logger.info("5️⃣ Instagram 자동 포스팅 중...")
        
        try:
            content = self.workflow_data.get('final_content', '')
            
            result = await self.call_mcp_server(
                'meta_scheduler',
                'schedule_post',
                {
                    'url': 'https://your-instagram-endpoint.com',
                    'method': 'POST',
                    'body': content,
                    'schedule_time': datetime.now().isoformat()
                }
            )
            
            logger.info("✅ Instagram 포스팅 완료")
            return f"Instagram 포스팅 성공: {result}"
            
        except Exception as e:
            logger.error(f"Instagram 포스팅 오류: {e}")
            return f"Instagram 포스팅 준비 완료 (수동 포스팅 필요): {str(e)}"
    
    async def _post_to_naver_blog(self) -> str:
        """네이버 블로그 자동 포스팅 (puppeteer)"""
        logger.info("5️⃣ 네이버 블로그 자동 포스팅 중...")
        
        try:
            content = self.workflow_data.get('final_content', '')
            
            # Puppeteer를 사용한 네이버 블로그 포스팅
            # 실제로는 Puppeteer 스크립트나 브라우저 자동화 도구 사용
            posting_result = f"""
네이버 블로그 포스팅 준비 완료:
- 제목: {self.workflow_data.get('original_request', '')[:50]}
- 내용: {len(content)} 글자
- 포스팅 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

수동으로 네이버 블로그에 로그인 후 다음 내용을 붙여넣어주세요:
{content}
            """
            
            logger.info("✅ 네이버 블로그 포스팅 준비 완료")
            return posting_result
            
        except Exception as e:
            logger.error(f"네이버 블로그 포스팅 오류: {e}")
            return f"네이버 블로그 포스팅 오류: {str(e)}"
    
    async def execute_full_workflow(self, user_request: str, platform: Optional[str] = None) -> Dict[str, Any]:
        """전체 워크플로우 실행"""
        workflow_log = []
        
        try:
            # 1단계: 사용자 입력 해석
            workflow_log.append("1️⃣ 사용자 입력 해석 시작")
            interpreted = await self.step1_interpret_user_input(user_request)
            workflow_log.append("✅ 사용자 입력 해석 완료")
            
            # 2단계: 플랫폼 선택
            workflow_log.append("2️⃣ 플랫폼 선택 시작")
            platform_info = await self.step2_select_platform(platform)
            workflow_log.append(f"✅ 플랫폼 선택 완료: {self.selected_platform}")
            
            # 3단계: 추천 요소 가져오기
            workflow_log.append(f"3️⃣ {'해시태그' if self.selected_platform == 'instagram' else '키워드'} 추천 시작")
            recommendations = await self.step3_get_recommendations()
            workflow_log.append(f"✅ {'해시태그' if self.selected_platform == 'instagram' else '키워드'} 추천 완료")
            
            # 4단계: 콘텐츠 생성
            workflow_log.append("4️⃣ 콘텐츠 생성 시작")
            content = await self.step4_generate_content()
            workflow_log.append("✅ 콘텐츠 생성 완료")
            
            # 5단계: 자동 포스팅
            workflow_log.append("5️⃣ 자동 포스팅 시작")
            posting_result = await self.step5_auto_posting()
            workflow_log.append("✅ 자동 포스팅 완료")
            
            return {
                'success': True,
                'workflow_log': workflow_log,
                'data': self.workflow_data,
                'final_result': {
                    'platform': self.selected_platform,
                    'content': content,
                    'posting_result': posting_result
                }
            }
            
        except Exception as e:
            logger.error(f"워크플로우 실행 오류: {e}")
            workflow_log.append(f"❌ 오류 발생: {str(e)}")
            
            return {
                'success': False,
                'workflow_log': workflow_log,
                'error': str(e),
                'data': self.workflow_data
            }

# 편의 함수
async def run_marketing_workflow(user_request: str, platform: Optional[str] = None) -> Dict[str, Any]:
    """마케팅 워크플로우 실행"""
    manager = MarketingWorkflowManager()
    return await manager.execute_full_workflow(user_request, platform)

if __name__ == "__main__":
    asyncio.run(run_marketing_workflow("AI 기반 언어 학습 앱을 출시합니다. 개인 맞춤형 학습 플랜을 제공합니다."))
