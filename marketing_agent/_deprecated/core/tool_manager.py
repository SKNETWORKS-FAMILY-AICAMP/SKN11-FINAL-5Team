"""
마케팅 에이전트 툴 관리 모듈
"""

import logging
from typing import Dict, Any, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# 공통 모듈 임포트 (안전한 import)
try:
    from shared_modules import get_llm_manager
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"shared_modules import 실패: {e}")
    
    def get_llm_manager():
        return None

try:
    from marketing_agent.utils import get_marketing_analysis_tools
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"analysis_tools import 실패: {e}")
    
    def get_marketing_analysis_tools():
        return None

logger = logging.getLogger(__name__)


class ToolManager:
    """마케팅 툴 관리 클래스"""
    
    def __init__(self):
        self.analysis_tools = get_marketing_analysis_tools()
        self.llm_manager = get_llm_manager()
    
    async def execute_marketing_tool(self, user_input: str, intent_analysis: Dict[str, Any], 
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """마케팅 툴 실행"""
        try:
            tool_requirements = intent_analysis.get("tool_requirements", {})
            tool_type = tool_requirements.get("tool_type", "none")
            target_keyword = tool_requirements.get("target_keyword", "")
            content_type = tool_requirements.get("content_type", "general")
            current_stage = context.get("current_stage", "any_question")
            
            if not self.analysis_tools:
                return {
                    "success": False,
                    "error": "마케팅 분석 도구가 초기화되지 않았습니다.",
                    "tool_type": tool_type
                }
            
            logger.info(f"[툴 실행] 툴 타입: {tool_type}, 키워드: {target_keyword}, 현재 단계: {current_stage}")
            
            # 콘텐츠 생성은 4단계(실행 계획)에서만 가능
            if tool_type == "content_generation":
                if current_stage != "stage_4_execution":
                    return {
                        "success": False,
                        "error": "콘텐츠 생성은 4단계(실행 계획) 단계에서만 가능합니다.",
                        "tool_type": tool_type,
                        "stage_requirement": "stage_4_execution",
                        "current_stage": current_stage,
                        "suggestion": "먼저 1단계(목표 정의) → 2단계(타겟 분석) → 3단계(전략 기획)를 완료한 후 콘텐츠를 생성해보세요."
                    }
            
            # 키워드가 없으면 사용자 입력에서 추출
            if not target_keyword:
                target_keyword = await self._extract_keyword_from_input(user_input)
            
            # 툴 타입별 실행
            if tool_type == "trend_analysis":
                keywords = [target_keyword] + await self._generate_related_keywords(target_keyword, 4)
                result = await self.analysis_tools.analyze_naver_trends(keywords)
                
            elif tool_type == "hashtag_analysis":
                result = await self.analysis_tools.analyze_instagram_hashtags(
                    question=user_input,
                    user_hashtags=[target_keyword]
                )
                
            elif tool_type == "content_generation":
                # 이미 위에서 단계 체크를 했으므로 여기서는 바로 실행
                if content_type == "blog":
                    result = await self.analysis_tools.create_blog_content_workflow(target_keyword)
                elif content_type == "instagram":
                    result = await self.analysis_tools.create_instagram_content_workflow(target_keyword)
                else:
                    # 일반적인 콘텐츠 생성
                    result = await self.analysis_tools.generate_instagram_content()
                    
            elif tool_type == "keyword_research":
                keywords = await self.analysis_tools.generate_related_keywords(target_keyword, 15)
                trend_result = await self.analysis_tools.analyze_naver_trends(keywords[:5])
                result = {
                    "success": True,
                    "keywords": keywords,
                    "trend_data": trend_result
                }
                
            else:
                return {
                    "success": False,
                    "error": f"지원하지 않는 툴 타입: {tool_type}",
                    "tool_type": tool_type
                }
            
            # 결과에 툴 정보 추가
            if isinstance(result, dict):
                result["tool_type"] = tool_type
                result["target_keyword"] = target_keyword
                result["content_type"] = content_type
            
            logger.info(f"[툴 실행] 완료: {result.get('success', False)}")
            return result
            
        except Exception as e:
            logger.error(f"마케팅 툴 실행 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_type": tool_requirements.get("tool_type", "unknown")
            }
    
    async def generate_response_with_tool_result(self, user_input: str, intent_analysis: Dict[str, Any], 
                                               context: Dict[str, Any], tool_result: Dict[str, Any]) -> str:
        """툴 결과를 포함한 응답 생성"""
        try:
            tool_type = tool_result.get("tool_type", "unknown")
            success = tool_result.get("success", False)
            
            if not success:
                error_msg = tool_result.get("error", "알 수 없는 오류")
                
                # 단계 제한 오류 특별 처리 (콘텐츠 생성)
                if "stage_requirement" in tool_result:
                    current_stage = tool_result.get("current_stage", "unknown")
                    required_stage = tool_result.get("stage_requirement", "unknown")
                    suggestion = tool_result.get("suggestion", "")
                    
                    response = f"🚧 **콘텐츠 생성 단계 안내**\n\n"
                    response += f"현재 단계: **{current_stage}**\n"
                    response += f"요구 단계: **{required_stage}**\n\n"
                    response += f"📄 **안내사항**:\n{suggestion}\n\n"
                    response += "🚀 **단계별 진행 방법**:\n"
                    response += "• '단계 이동' 또는 '4단계로 이동'이라고 말씩하세요\n"
                    response += "• '체계적 상담 시작'으로 1단계부터 진행하세요\n"
                    response += "• 현재 단계에서 다른 마케팅 질문을 해주세요"
                    
                    return response
                
                # 일반적인 오류 처리
                return f"죄송합니다. {tool_type} 분석 중 오류가 발생했습니다: {error_msg}\n\n일반적인 마케팅 조언을 드리겠습니다."
            
            # 툴 타입별 결과 포맷팅
            if tool_type == "trend_analysis":
                return await self._format_trend_analysis_response(user_input, tool_result, context)
            elif tool_type == "hashtag_analysis":
                return await self._format_hashtag_analysis_response(user_input, tool_result, context)
            elif tool_type == "content_generation":
                return await self._format_content_generation_response(user_input, tool_result, context)
            elif tool_type == "keyword_research":
                return await self._format_keyword_research_response(user_input, tool_result, context)
            else:
                return await self._format_general_tool_response(user_input, tool_result, context)
                
        except Exception as e:
            logger.error(f"툴 결과 응답 생성 실패: {e}")
            return "마케팅 분석을 진행했지만 결과 처리 중 오류가 발생했습니다. 다시 시도해주세요."
    
    async def _extract_keyword_from_input(self, user_input: str) -> str:
        """사용자 입력에서 키워드 추출"""
        try:
            if self.llm_manager:
                messages = [
                    {"role": "system", "content": "사용자 입력에서 마케팅 분석에 가장 적합한 주요 키워드 1개를 추출하세요. 키워드만 출력하세요."},
                    {"role": "user", "content": f"다음 질문에서 주요 키워드를 추출해주세요: {user_input}"}
                ]
                
                result = self.llm_manager.generate_response_sync(messages)
                return result.strip() if result else "마케팅"
            
            # LLM이 없을 경우 대체 방법
            return "마케팅"
            
        except Exception as e:
            logger.error(f"키워드 추출 실패: {e}")
            return "마케팅"
    
    async def _generate_related_keywords(self, base_keyword: str, count: int = 5) -> List[str]:
        """관련 키워드 생성 (간단 버전)"""
        try:
            if self.analysis_tools:
                keywords = await self.analysis_tools.generate_related_keywords(base_keyword, count)
                return keywords[1:]  # 기본 키워드 제외
            return []
        except Exception as e:
            logger.error(f"관련 키워드 생성 실패: {e}")
            return []
    
    async def _format_trend_analysis_response(self, user_input: str, tool_result: Dict[str, Any], context: Dict[str, Any]) -> str:
        """트렌드 분석 결과 포맷팅"""
        try:
            data = tool_result.get("data", [])
            keywords = tool_result.get("keywords", [])
            period = tool_result.get("period", "")
            
            response = f"📈 **키워드 트렌드 분석 결과**\n\n"
            response += f"🔍 **분석 기간**: {period}\n"
            response += f"🎯 **분석 키워드**: {', '.join(keywords)}\n\n"
            
            if data:
                response += "📊 **트렌드 순위**:\n"
                # 트렌드 데이터 정렬 및 표시
                trend_scores = []
                for result in data[:5]:  # 상위 5개만
                    if "data" in result:
                        scores = [item["ratio"] for item in result["data"] if "ratio" in item]
                        avg_score = sum(scores) / len(scores) if scores else 0
                        trend_scores.append((result["title"], avg_score))
                
                trend_scores.sort(key=lambda x: x[1], reverse=True)
                
                for i, (keyword, score) in enumerate(trend_scores, 1):
                    response += f"{i}. **{keyword}** (평균 검색량: {score:.1f})\n"
                
                response += "\n💡 **마케팅 인사이트**:\n"
                if trend_scores:
                    top_keyword = trend_scores[0][0]
                    response += f"• '{top_keyword}'가 가장 높은 검색 트렌드를 보이고 있습니다.\n"
                    response += f"• 이 키워드를 중심으로 콘텐츠를 제작하면 높은 관심도를 얻을 수 있습니다.\n"
                
            else:
                response += "트렌드 데이터를 가져오는데 문제가 있었습니다. 일반적인 키워드 활용 방안을 제시드리겠습니다.\n"
            
            # 후속 제안
            response += "\n🎬 **다음 단계 제안**:\n"
            response += "• 블로그 콘텐츠 제작\n• 인스타그램 해시태그 분석\n• SEO 최적화 전략 수립\n"
            
            return response
            
        except Exception as e:
            logger.error(f"트렌드 분석 응답 포맷팅 실패: {e}")
            return "트렌드 분석을 완료했지만 결과 정리 중 오류가 발생했습니다."
    
    async def _format_hashtag_analysis_response(self, user_input: str, tool_result: Dict[str, Any], context: Dict[str, Any]) -> str:
        """해시태그 분석 결과 포맷팅"""
        try:
            searched_hashtags = tool_result.get("searched_hashtags", [])
            popular_hashtags = tool_result.get("popular_hashtags", [])
            total_posts = tool_result.get("total_posts", 0)
            
            response = f"#️⃣ **인스타그램 해시태그 분석 결과**\n\n"
            response += f"🔍 **분석 해시태그**: #{', #'.join(searched_hashtags)}\n"
            response += f"📊 **분석된 포스트 수**: {total_posts:,}개\n\n"
            
            if popular_hashtags:
                response += "🔥 **추천 인기 해시태그**:\n"
                for i, hashtag in enumerate(popular_hashtags[:15], 1):
                    if not hashtag.startswith('#'):
                        hashtag = f"#{hashtag}"
                    response += f"{i}. {hashtag}\n"
                
                response += "\n💡 **해시태그 활용 팁**:\n"
                response += "• 인기 해시태그와 틈새 해시태그를 적절히 조합하세요\n"
                response += "• 포스트당 20-30개의 해시태그 사용을 권장합니다\n"
                response += "• 브랜드만의 고유 해시태그도 함께 활용하세요\n"
            else:
                response += "해시태그 데이터 수집에 문제가 있었습니다. 일반적인 해시태그 전략을 제안드리겠습니다.\n"
            
            # 후속 제안
            response += "\n📝 **다음 단계 제안**:\n"
            response += "• 인스타그램 콘텐츠 제작\n• 해시태그 성과 분석\n• 경쟁사 해시태그 연구\n"
            
            return response
            
        except Exception as e:
            logger.error(f"해시태그 분석 응답 포맷팅 실패: {e}")
            return "해시태그 분석을 완료했지만 결과 정리 중 오류가 발생했습니다."
    
    async def _format_content_generation_response(self, user_input: str, tool_result: Dict[str, Any], context: Dict[str, Any]) -> str:
        """콘텐츠 생성 결과 포맷팅"""
        try:
            content_type = tool_result.get("content_type", "general")
            base_keyword = tool_result.get("base_keyword", "")
            
            response = f"✍️ **{content_type.upper()} 콘텐츠 생성 완료**\n\n"
            response += f"🎯 **주요 키워드**: {base_keyword}\n\n"
            
            if content_type == "blog":
                blog_content = tool_result.get("blog_content", {})
                if blog_content and "full_content" in blog_content:
                    response += "📝 **생성된 블로그 콘텐츠**:\n"
                    response += f"{blog_content['full_content'][:1000]}...\n\n"
                    response += f"📊 **콘텐츠 정보**: 약 {blog_content.get('word_count', 0)}단어\n"
                
            elif content_type == "instagram":
                instagram_content = tool_result.get("instagram_content", {})
                if instagram_content and "post_content" in instagram_content:
                    response += "📱 **생성된 인스타그램 포스트**:\n"
                    response += f"{instagram_content['post_content']}\n\n"
                    
                    hashtags = instagram_content.get("selected_hashtags", [])
                    if hashtags:
                        response += f"#️⃣ **추천 해시태그** ({len(hashtags)}개):\n"
                        response += " ".join(hashtags[:20]) + "\n\n"
            
            # 관련 키워드 정보
            related_keywords = tool_result.get("related_keywords", [])
            if related_keywords:
                response += f"🔑 **관련 키워드**: {', '.join(related_keywords[:10])}\n\n"
            
            response += "💡 **활용 가이드**:\n"
            response += "• 생성된 콘텐츠를 브랜드 톤앤매너에 맞게 수정하세요\n"
            response += "• 타겟 고객의 관심사를 반영해 개인화하세요\n"
            response += "• 정기적인 콘텐츠 업데이트로 지속적인 관심을 유도하세요\n"
            
            return response
            
        except Exception as e:
            logger.error(f"콘텐츠 생성 응답 포맷팅 실패: {e}")
            return "콘텐츠 생성을 완료했지만 결과 정리 중 오류가 발생했습니다."
    
    async def _format_keyword_research_response(self, user_input: str, tool_result: Dict[str, Any], context: Dict[str, Any]) -> str:
        """키워드 연구 결과 포맷팅"""
        try:
            keywords = tool_result.get("keywords", [])
            trend_data = tool_result.get("trend_data", {})
            
            response = f"🔍 **키워드 연구 결과**\n\n"
            
            if keywords:
                response += f"📝 **추천 키워드** ({len(keywords)}개):\n"
                for i, keyword in enumerate(keywords[:15], 1):
                    response += f"{i}. {keyword}\n"
                response += "\n"
            
            if trend_data.get("success") and trend_data.get("data"):
                response += "📈 **트렌드 분석**:\n"
                for result in trend_data["data"][:5]:
                    if "data" in result:
                        scores = [item["ratio"] for item in result["data"] if "ratio" in item]
                        avg_score = sum(scores) / len(scores) if scores else 0
                        response += f"• {result['title']}: 평균 검색량 {avg_score:.1f}\n"
                response += "\n"
            
            response += "🎯 **SEO 활용 전략**:\n"
            response += "• 장꼬리 키워드(Long-tail)를 활용해 경쟁도를 낮추세요\n"
            response += "• 계절성과 트렌드를 고려한 키워드 선택을 하세요\n"
            response += "• 지역 기반 키워드로 로컬 SEO를 강화하세요\n"
            
            return response
            
        except Exception as e:
            logger.error(f"키워드 연구 응답 포맷팅 실패: {e}")
            return "키워드 연구를 완료했지만 결과 정리 중 오류가 발생했습니다."
    
    async def _format_general_tool_response(self, user_input: str, tool_result: Dict[str, Any], context: Dict[str, Any]) -> str:
        """일반 툴 결과 포맷팅"""
        return f"마케팅 분석을 완료했습니다. 결과를 바탕으로 맞춤형 전략을 제안드리겠습니다."
