"""
MCP 마케팅 도구 - 개선된 버전
✅ 컨텍스트 활용 강화, 실행력 중심, 맞춤화 개선, 결과 최적화
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import openai
from config import config

# MCP 관련 안전한 임포트
try:
    from shared_modules import get_llm_manager
    from shared_modules.mcp_client import MCPClientManager
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"MCP 모듈 import 실패: {e}")
    
    def get_llm_manager():
        return None
    
    class MCPClientManager:
        def __init__(self):
            pass
        
        async def call_tool(self, tool_name: str, **kwargs):
            return {"success": False, "error": "MCP 클라이언트 사용 불가"}

logger = logging.getLogger(__name__)

class MarketingAnalysisTools:
    """🆕 개선된 MCP 마케팅 분석 도구 - 컨텍스트 활용 및 결과 최적화"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.mcp_client = MCPClientManager()
        self.llm_manager = get_llm_manager()
        self.logger = logging.getLogger(__name__)
        
        # 🆕 분석 결과 향상을 위한 프롬프트 개선
        self._init_analysis_prompts()
        
        # 🆕 업종별 분석 특화 설정
        self._init_industry_analysis_configs()
    
    def _init_analysis_prompts(self):
        """🆕 분석 전용 프롬프트 초기화"""
        
        # 🆕 트렌드 분석 결과 해석 프롬프트
        self.trend_analysis_prompt = """다음 네이버 트렌드 데이터를 비즈니스 관점에서 분석하여 실행 가능한 마케팅 인사이트를 제공해주세요.

### 트렌드 데이터
{trend_data}

### 비즈니스 컨텍스트
- 업종: {business_type}
- 제품/서비스: {product}
- 타겟 고객: {target_audience}
- 마케팅 목표: {main_goal}

### 분석 요구사항
1. **트렌드 핵심 인사이트**: 데이터에서 발견되는 주요 패턴과 변화
2. **비즈니스 기회**: 해당 업종에서 활용할 수 있는 구체적 기회
3. **실행 가능한 전략**: 트렌드를 활용한 마케팅 방법
4. **타이밍 전략**: 언제, 어떻게 활용할지 구체적 계획
5. **경쟁 우위**: 트렌드를 통해 얻을 수 있는 차별화 포인트

### 출력 형식
**📊 트렌드 핵심 인사이트**
[주요 발견사항 3개, 각각 한 줄로 요약]

**💡 비즈니스 기회**
[업종 특성을 반영한 구체적 기회 3개]

**🎯 실행 전략**
1. **즉시 실행**: [바로 시작할 수 있는 방법]
2. **단기 전략** (1-2주): [트렌드 활용 방법]
3. **중기 전략** (1-2개월): [지속적 활용 계획]

**⏰ 최적 타이밍**
[언제, 어떤 방식으로 활용할지 구체적 가이드]

**🏆 경쟁 우위 확보**
[이 트렌드로 차별화할 수 있는 방법]

**📈 성과 예측**
[예상되는 마케팅 효과 및 지표]

업종 특성을 반영하여 바로 실행할 수 있는 구체적이고 실용적인 분석을 제공해주세요."""

        # 🆕 해시태그 분석 결과 해석 프롬프트
        self.hashtag_analysis_prompt = """다음 인스타그램 해시태그 분석 결과를 바탕으로 효과적인 SNS 마케팅 전략을 제시해주세요.

### 해시태그 분석 데이터
{hashtag_data}

### 비즈니스 컨텍스트
- 업종: {business_type}
- 제품/서비스: {product}
- 타겟 고객: {target_audience}
- 현재 사용 해시태그: {current_hashtags}

### 분석 목표
1. **해시태그 성과 분석**: 현재 해시태그의 효과성 평가
2. **최적 해시태그 조합**: 도달률과 참여도를 높이는 조합
3. **업종별 특화 전략**: 해당 분야에 특화된 해시태그 활용법
4. **트렌드 반영**: 최신 트렌드 해시태그 적용 방안
5. **성장 전략**: 팔로워와 인게이지먼트 증대 방법

### 출력 형식
**🔍 현재 해시태그 분석**
[사용 중인 해시태그의 효과성과 개선점]

**✨ 추천 해시태그 조합**
**상시 사용** (브랜드/업종): #태그1 #태그2 #태그3 #태그4 #태그5
**트렌드 활용** (시즌/이슈): #태그6 #태그7 #태그8 #태그9 #태그10
**타겟 특화** (고객층): #태그11 #태그12 #태그13 #태그14 #태그15
**지역/커뮤니티**: #태그16 #태그17 #태그18 #태그19 #태그20

**📋 해시태그 전략**
1. **도달률 극대화**: [넓은 노출을 위한 인기 해시태그]
2. **타겟 정확도**: [정확한 타겟팅을 위한 니치 해시태그]
3. **참여도 향상**: [인게이지먼트를 높이는 해시태그]

**📅 활용 일정**
- **월요일**: [해시태그 조합 A + 사용 이유]
- **수요일**: [해시태그 조합 B + 사용 이유]
- **금요일**: [해시태그 조합 C + 사용 이유]

**📊 성과 측정**
[추적해야 할 지표와 개선 방향]

**💡 추가 팁**
[해시태그 외 SNS 성장을 위한 실용적 조언]

업종 특성과 타겟 고객에 맞는 실제 사용 가능한 해시태그 전략을 제공해주세요."""

        # 🆕 키워드 리서치 종합 분석 프롬프트
        self.keyword_research_prompt = """다음 키워드 리서치 결과를 종합 분석하여 마케팅 활용 전략을 수립해주세요.

### 키워드 데이터
- 타겟 키워드: {target_keywords}
- 트렌드 데이터: {trend_data}
- 관련 키워드: {related_keywords}

### 비즈니스 정보
- 업종: {business_type}
- 제품/서비스: {product}
- 마케팅 목표: {main_goal}
- 타겟 고객: {target_audience}

### 키워드 전략 수립 요구사항
1. **우선순위 키워드**: 효과와 경쟁도를 고려한 핵심 키워드
2. **콘텐츠 전략**: 키워드 기반 콘텐츠 기획
3. **SEO 최적화**: 검색 노출 향상 방안
4. **광고 활용**: 유료 광고에서의 키워드 활용
5. **장기 전략**: 지속 가능한 키워드 마케팅

### 출력 형식
**🎯 핵심 키워드 전략**
**1순위** (즉시 집중): [키워드 3개 + 선정 이유]
**2순위** (단기 목표): [키워드 4개 + 활용 방법]  
**3순위** (장기 전략): [키워드 3개 + 성장 계획]

**📝 콘텐츠 기획**
- **블로그 포스트**: [키워드 기반 주제 5개]
- **SNS 콘텐츠**: [키워드 활용 포스트 아이디어 3개]
- **영상 콘텐츠**: [키워드 반영 영상 기획 2개]

**🔍 SEO 최적화 계획**
1. **온페이지 SEO**: [웹사이트 내 키워드 최적화 방법]
2. **콘텐츠 SEO**: [검색 친화적 콘텐츠 작성법]
3. **기술적 SEO**: [구조적 개선사항]

**💰 광고 키워드 전략**
- **검색 광고**: [Google/네이버 검색 광고용 키워드]
- **디스플레이**: [배너 광고 타겟팅 키워드]
- **소셜 광고**: [SNS 광고 관심사 키워드]

**📈 성과 측정 및 최적화**
[키워드별 성과 지표와 개선 방법]

**🗓️ 3개월 실행 로드맵**
**1개월차**: [초기 집중 키워드와 기반 구축]
**2개월차**: [확장 키워드와 콘텐츠 다양화]
**3개월차**: [최적화 및 새로운 기회 탐색]

업종 특성과 비즈니스 목표에 맞는 실행 가능한 키워드 마케팅 전략을 제공해주세요."""
    
    def _init_industry_analysis_configs(self):
        """🆕 업종별 분석 특화 설정"""
        self.industry_analysis_configs = {
            "뷰티": {
                "trend_focus": ["계절 트렌드", "성분 트렌드", "뷰티 기법", "셀럽 스타일"],
                "hashtag_categories": ["뷰티팁", "제품리뷰", "메이크업", "스킨케어", "트렌드"],
                "keyword_priorities": ["효과", "성분", "후기", "추천", "트렌드"],
                "analysis_angle": "뷰티 트렌드와 소비자 니즈 변화"
            },
            "음식점": {
                "trend_focus": ["계절 메뉴", "음식 트렌드", "건강식", "지역 특산물"],
                "hashtag_categories": ["맛집", "음식스타그램", "지역태그", "분위기", "메뉴"],
                "keyword_priorities": ["맛집", "지역명", "음식명", "분위기", "가격대"],
                "analysis_angle": "외식 트렌드와 지역 특성"
            },
            "온라인쇼핑몰": {
                "trend_focus": ["쇼핑 트렌드", "상품 카테고리", "가격 민감도", "배송 서비스"],
                "hashtag_categories": ["쇼핑", "할인", "신상", "후기", "추천"],
                "keyword_priorities": ["쇼핑", "할인", "후기", "배송", "품질"],
                "analysis_angle": "이커머스 트렌드와 소비 패턴"
            },
            "서비스업": {
                "trend_focus": ["서비스 혁신", "고객 만족", "전문성", "효율성"],
                "hashtag_categories": ["서비스", "전문가", "솔루션", "고객만족", "신뢰"],
                "keyword_priorities": ["서비스", "전문", "솔루션", "신뢰", "효과"],
                "analysis_angle": "서비스 품질과 고객 기대치"
            }
        }
    
    # ============================================
    # 🆕 개선된 분석 도구 메서드들
    # ============================================
    
    async def analyze_naver_trends(self, keywords: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """🆕 네이버 트렌드 분석 - 컨텍스트 활용 강화"""
        try:
            # MCP 클라이언트를 통한 트렌드 데이터 수집
            trend_result = await self.mcp_client.call_tool(
                "naver_trends",
                keywords=keywords,
                period="3month"  # 최근 3개월 데이터
            )
            
            if not trend_result.get("success"):
                return await self._generate_fallback_trend_analysis(keywords, context)
            
            # 🆕 비즈니스 컨텍스트 기반 분석 수행
            analysis_result = await self._analyze_trends_with_context(
                trend_result.get("data", {}), 
                keywords, 
                context or {}
            )
            
            return {
                "success": True,
                "type": "trend_analysis",
                "keywords": keywords,
                "raw_data": trend_result.get("data", {}),
                "business_analysis": analysis_result,
                "recommendations": await self._generate_trend_recommendations(analysis_result, context),
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"네이버 트렌드 분석 실패: {e}")
            return await self._generate_fallback_trend_analysis(keywords, context)
    
    async def analyze_instagram_hashtags(self, question: str, user_hashtags: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """🆕 인스타그램 해시태그 분석 - 업종별 최적화"""
        try:
            # MCP 클라이언트를 통한 해시태그 데이터 수집
            hashtag_result = await self.mcp_client.call_tool(
                "instagram_hashtag_analysis",
                hashtags=user_hashtags,
                analysis_type="comprehensive"
            )
            
            if not hashtag_result.get("success"):
                return await self._generate_fallback_hashtag_analysis(user_hashtags, context)
            
            # 🆕 업종별 특화 해시태그 분석
            analysis_result = await self._analyze_hashtags_with_context(
                hashtag_result.get("data", {}),
                user_hashtags,
                context or {}
            )
            
            return {
                "success": True,
                "type": "hashtag_analysis",
                "question": question,
                "analyzed_hashtags": user_hashtags,
                "raw_data": hashtag_result.get("data", {}),
                "business_analysis": analysis_result,
                "optimized_hashtags": await self._generate_optimized_hashtags(analysis_result, context),
                "strategy": await self._generate_hashtag_strategy(analysis_result, context),
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"인스타그램 해시태그 분석 실패: {e}")
            return await self._generate_fallback_hashtag_analysis(user_hashtags, context)
    
    async def create_blog_content_workflow(self, target_keyword: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """🆕 블로그 콘텐츠 워크플로우 - 키워드 최적화"""
        try:
            # 🆕 키워드 분석과 블로그 콘텐츠 통합 생성
            keyword_analysis = await self.analyze_keyword_comprehensive([target_keyword], context)
            
            if not keyword_analysis.get("success"):
                return await self._generate_basic_blog_workflow(target_keyword, context)
            
            # 🆕 SEO 최적화된 블로그 콘텐츠 워크플로우 생성
            workflow_result = await self._create_blog_workflow_with_seo(
                target_keyword, 
                keyword_analysis.get("analysis", {}),
                context or {}
            )
            
            return {
                "success": True,
                "type": "blog_workflow",
                "target_keyword": target_keyword,
                "keyword_analysis": keyword_analysis.get("analysis", {}),
                "content_workflow": workflow_result,
                "seo_optimization": await self._generate_seo_recommendations(target_keyword, context),
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"블로그 콘텐츠 워크플로우 생성 실패: {e}")
            return await self._generate_basic_blog_workflow(target_keyword, context)
    
    async def create_instagram_content_workflow(self, target_keyword: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """🆕 인스타그램 콘텐츠 워크플로우 - 비주얼 최적화"""
        try:
            # 🆕 키워드 기반 해시태그 분석
            hashtag_analysis = await self.analyze_instagram_hashtags(
                f"{target_keyword} 관련 인스타그램 콘텐츠",
                [target_keyword],
                context
            )
            
            # 🆕 비주얼 중심의 인스타그램 워크플로우 생성
            workflow_result = await self._create_instagram_workflow_with_visuals(
                target_keyword,
                hashtag_analysis.get("optimized_hashtags", []),
                context or {}
            )
            
            return {
                "success": True,
                "type": "instagram_workflow",
                "target_keyword": target_keyword,
                "hashtag_analysis": hashtag_analysis.get("business_analysis", {}),
                "content_workflow": workflow_result,
                "visual_strategy": await self._generate_visual_strategy(target_keyword, context),
                "engagement_tips": await self._generate_engagement_tips(context),
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"인스타그램 콘텐츠 워크플로우 생성 실패: {e}")
            return await self._generate_basic_instagram_workflow(target_keyword, context)
    
    async def generate_instagram_content(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """🆕 인스타그램 콘텐츠 생성 - 통합 최적화"""
        try:
            if not context:
                context = {}
            
            # 🆕 비즈니스 정보 기반 콘텐츠 생성
            business_type = context.get("business_type", "일반")
            product = context.get("product", "제품/서비스")
            
            # 업종별 특화 콘텐츠 생성
            content_result = await self._generate_instagram_content_optimized(business_type, product, context)
            
            return {
                "success": True,
                "type": "instagram_content",
                "business_type": business_type,
                "content": content_result,
                "optimization_applied": True,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"인스타그램 콘텐츠 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "instagram_content"
            }
    
    # ============================================
    # 🆕 새로운 분석 메서드들
    # ============================================
    
    async def analyze_keyword_comprehensive(self, keywords: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """🆕 종합적인 키워드 분석"""
        try:
            # 트렌드 분석과 키워드 분석을 통합
            trend_analysis = await self.analyze_naver_trends(keywords, context)
            
            # 🆕 키워드별 상세 분석 수행
            keyword_details = await self._analyze_keywords_detailed(keywords, context or {})
            
            # 🆕 비즈니스 활용 전략 생성
            utilization_strategy = await self._generate_keyword_utilization_strategy(
                keywords, keyword_details, context or {}
            )
            
            return {
                "success": True,
                "type": "keyword_comprehensive",
                "keywords": keywords,
                "trend_analysis": trend_analysis.get("business_analysis", {}),
                "keyword_details": keyword_details,
                "utilization_strategy": utilization_strategy,
                "recommendations": await self._generate_comprehensive_recommendations(keywords, context),
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"종합 키워드 분석 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "keyword_comprehensive"
            }
    
    # ============================================
    # 🆕 컨텍스트 기반 분석 헬퍼 메서드들
    # ============================================
    
    async def _analyze_trends_with_context(self, trend_data: Dict[str, Any], keywords: List[str], context: Dict[str, Any]) -> str:
        """🆕 컨텍스트 기반 트렌드 분석"""
        try:
            business_type = context.get("business_type", "일반")
            product = context.get("product", "제품/서비스")
            target_audience = context.get("target_audience", "일반 고객")
            main_goal = context.get("main_goal", "브랜드 인지도 향상")
            
            # 업종별 분석 설정 적용
            industry_config = self.industry_analysis_configs.get(business_type, {})
            analysis_angle = industry_config.get("analysis_angle", "일반적인 마케팅 관점")
            
            formatted_prompt = self.trend_analysis_prompt.format(
                trend_data=json.dumps(trend_data, ensure_ascii=False),
                business_type=business_type,
                product=product,
                target_audience=target_audience,
                main_goal=main_goal
            )
            
            response = await self._call_analysis_llm(formatted_prompt)
            return response
            
        except Exception as e:
            self.logger.error(f"컨텍스트 기반 트렌드 분석 실패: {e}")
            return "트렌드 데이터 분석 중 오류가 발생했습니다."
    
    async def _analyze_hashtags_with_context(self, hashtag_data: Dict[str, Any], hashtags: List[str], context: Dict[str, Any]) -> str:
        """🆕 컨텍스트 기반 해시태그 분석"""
        try:
            business_type = context.get("business_type", "일반")
            product = context.get("product", "제품/서비스")
            target_audience = context.get("target_audience", "일반 고객")
            
            formatted_prompt = self.hashtag_analysis_prompt.format(
                hashtag_data=json.dumps(hashtag_data, ensure_ascii=False),
                business_type=business_type,
                product=product,
                target_audience=target_audience,
                current_hashtags=', '.join(hashtags)
            )
            
            response = await self._call_analysis_llm(formatted_prompt)
            return response
            
        except Exception as e:
            self.logger.error(f"컨텍스트 기반 해시태그 분석 실패: {e}")
            return "해시태그 데이터 분석 중 오류가 발생했습니다."
    
    async def _analyze_keywords_detailed(self, keywords: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """🆕 키워드 상세 분석"""
        try:
            business_type = context.get("business_type", "일반")
            main_goal = context.get("main_goal", "브랜드 인지도 향상")
            target_audience = context.get("target_audience", "일반 고객")
            
            # 업종별 키워드 우선순위 적용
            industry_config = self.industry_analysis_configs.get(business_type, {})
            priority_keywords = industry_config.get("keyword_priorities", [])
            
            analysis_prompt = f"""다음 키워드들을 {business_type} 업종의 관점에서 상세 분석해주세요.

키워드: {', '.join(keywords)}
업종 특성: {business_type}
마케팅 목표: {main_goal}
타겟 고객: {target_audience}
우선 키워드 유형: {', '.join(priority_keywords)}

각 키워드별로 다음을 분석해주세요:
1. 검색 의도 분석
2. 경쟁도 예상 (상/중/하)
3. 비즈니스 연관성 (상/중/하)
4. 활용 우선순위 (1-5점)
5. 추천 활용 방법

JSON 형태로 결과를 제공해주세요."""
            
            response = await self._call_analysis_llm(analysis_prompt)
            
            # JSON 파싱 시도
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"analysis": response, "parsed": False}
                
        except Exception as e:
            self.logger.error(f"키워드 상세 분석 실패: {e}")
            return {"error": str(e)}
    
    async def _call_analysis_llm(self, prompt: str) -> str:
        """🆕 분석 전용 LLM 호출"""
        try:
            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": """당신은 마케팅 데이터 분석 전문가입니다. 다음 원칙에 따라 분석해주세요:

1. **실행 중심**: 바로 적용할 수 있는 구체적인 인사이트 제공
2. **업종 특화**: 해당 업종의 특성과 트렌드 반영
3. **맞춤화**: 비즈니스 컨텍스트에 맞는 분석
4. **우선순위**: 효과 높은 것부터 순서대로 제시
5. **측정 가능**: 성과를 추적할 수 있는 구체적 방법 제안

데이터를 단순히 설명하지 말고, 비즈니스 성장에 도움되는 실용적 인사이트를 제공해주세요."""},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 분석의 일관성을 위해 낮은 온도 설정
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"분석 LLM 호출 실패: {e}")
            return f"분석 중 오류가 발생했습니다: {str(e)}"
    
    # ============================================
    # 🆕 전략 생성 메서드들
    # ============================================
    
    async def _generate_trend_recommendations(self, analysis_result: str, context: Dict[str, Any]) -> List[str]:
        """🆕 트렌드 기반 추천 생성"""
        try:
            business_type = context.get("business_type", "일반") if context else "일반"
            
            prompt = f"""다음 트렌드 분석 결과를 바탕으로 {business_type} 업종에서 바로 실행할 수 있는 구체적인 마케팅 액션 5개를 추천해주세요.

분석 결과: {analysis_result}

각 추천사항은 다음 형식으로 작성해주세요:
- 구체적 액션: [무엇을 할지]
- 실행 방법: [어떻게 할지]
- 예상 효과: [어떤 결과를 기대할지]

JSON 배열 형태로 응답해주세요."""
            
            response = await self._call_analysis_llm(prompt)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # 파싱 실패 시 기본 추천사항 반환
                return [
                    "트렌드 키워드를 활용한 콘텐츠 제작",
                    "시즌별 마케팅 메시지 조정",
                    "타겟 고객 관심사 반영한 캠페인 기획",
                    "경쟁사 대비 차별화 포인트 강화",
                    "데이터 기반 마케팅 전략 최적화"
                ]
                
        except Exception as e:
            self.logger.error(f"트렌드 추천 생성 실패: {e}")
            return ["트렌드 분석 기반 마케팅 전략 수립이 필요합니다."]
    
    async def _generate_optimized_hashtags(self, analysis_result: str, context: Dict[str, Any]) -> Dict[str, List[str]]:
        """🆕 최적화된 해시태그 생성"""
        try:
            business_type = context.get("business_type", "일반") if context else "일반"
            
            # 업종별 해시태그 카테고리 적용
            industry_config = self.industry_analysis_configs.get(business_type, {})
            hashtag_categories = industry_config.get("hashtag_categories", ["일반", "마케팅", "비즈니스"])
            
            optimized_hashtags = {
                "brand_core": [f"#{business_type}", "#브랜드", "#품질", "#신뢰", "#전문"],
                "trending": [f"#{cat}트렌드" for cat in hashtag_categories[:3]],
                "target_specific": [f"#{business_type}추천", f"#{business_type}팁", f"#{business_type}정보"],
                "engagement": ["#일상", "#소통", "#공감", "#체험", "#후기"]
            }
            
            return optimized_hashtags
            
        except Exception as e:
            self.logger.error(f"최적화된 해시태그 생성 실패: {e}")
            return {
                "brand_core": ["#브랜드", "#품질", "#전문", "#신뢰", "#서비스"],
                "trending": ["#트렌드", "#인기", "#핫한", "#최신", "#화제"],
                "target_specific": ["#추천", "#팁", "#정보", "#가이드", "#노하우"],
                "engagement": ["#일상", "#소통", "#공감", "#체험", "#후기"]
            }
    
    async def _generate_hashtag_strategy(self, analysis_result: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """🆕 해시태그 전략 생성"""
        try:
            strategy = {
                "posting_schedule": {
                    "월요일": "브랜드 소개 + 전문성 어필 해시태그",
                    "수요일": "제품/서비스 관련 + 트렌드 해시태그", 
                    "금요일": "고객 소통 + 참여 유도 해시태그"
                },
                "engagement_tips": [
                    "포스트 내용과 연관성 높은 해시태그 우선 사용",
                    "인기 해시태그와 니치 해시태그 조합 (7:3 비율)",
                    "스토리에서는 위치 태그와 함께 활용",
                    "댓글에서 추가 해시태그로 노출 확대"
                ],
                "monitoring_metrics": [
                    "해시태그별 도달률",
                    "인게이지먼트 비율",
                    "팔로워 증가율",
                    "프로필 방문률"
                ]
            }
            
            return strategy
            
        except Exception as e:
            self.logger.error(f"해시태그 전략 생성 실패: {e}")
            return {"error": str(e)}
    
    # ============================================
    # 🆕 워크플로우 생성 메서드들 (스텁으로 구현)
    # ============================================
    
    async def _create_blog_workflow_with_seo(self, keyword: str, analysis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """🆕 SEO 최적화된 블로그 워크플로우"""
        try:
            business_type = context.get("business_type", "일반")
            
            workflow = {
                "planning_phase": {
                    "keyword_research": f"{keyword} 및 관련 키워드 심화 분석",
                    "competitor_analysis": "상위 랭킹 블로그 콘텐츠 분석",
                    "content_gap": "경쟁사가 다루지 않은 차별화 포인트 발굴"
                },
                "creation_phase": {
                    "title_optimization": f"SEO 친화적 제목 (타겟 키워드: {keyword})",
                    "structure_planning": "H1-H2-H3 구조화 및 키워드 배치",
                    "content_writing": "독자 중심의 유용한 정보 제공",
                    "internal_linking": "관련 포스트 및 서비스 페이지 연결"
                },
                "optimization_phase": {
                    "meta_tags": "메타 제목, 설명 최적화",
                    "image_seo": "이미지 alt 텍스트 및 파일명 최적화",
                    "readability": "가독성 향상 (문단, bullet point 활용)",
                    "cta_placement": "자연스러운 전환 유도"
                },
                "distribution_phase": {
                    "social_sharing": "SNS 채널별 맞춤 공유",
                    "email_marketing": "뉴스레터 구독자 대상 배포",
                    "community_sharing": "관련 커뮤니티 및 포럼 공유"
                }
            }
            
            return workflow
            
        except Exception as e:
            self.logger.error(f"블로그 워크플로우 생성 실패: {e}")
            return {"error": str(e)}
    
    async def _create_instagram_workflow_with_visuals(self, keyword: str, hashtags: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """🆕 비주얼 중심 인스타그램 워크플로우"""
        try:
            business_type = context.get("business_type", "일반")
            
            workflow = {
                "concept_development": {
                    "visual_theme": f"{business_type} 브랜드 아이덴티티 반영",
                    "content_pillars": "교육/영감/엔터테인먼트/홍보 4축 균형",
                    "storytelling": f"{keyword} 중심의 브랜드 스토리 전개"
                },
                "content_creation": {
                    "photo_shooting": "브랜드 톤앤매너 일관성 유지",
                    "graphic_design": "정보 전달용 카드뉴스 제작",
                    "video_content": "릴스/스토리용 짧은 영상 콘텐츠",
                    "caption_writing": "타겟 고객 언어로 친근한 텍스트"
                },
                "posting_strategy": {
                    "optimal_timing": "타겟 고객 활성 시간대 포스팅",
                    "hashtag_rotation": "해시태그 조합 3가지 순환 사용",
                    "story_utilization": "일상적 소통 및 비하인드 공유",
                    "reels_strategy": "트렌드 음악/효과 활용한 참여 유도"
                },
                "engagement_building": {
                    "community_interaction": "댓글 적극 응답 및 타 계정 소통",
                    "user_generated_content": "고객 포스트 리포스트 및 감사 표현",
                    "collaboration": "동종업계 인플루언서/브랜드 협업",
                    "live_streaming": "실시간 소통을 통한 친밀감 형성"
                }
            }
            
            return workflow
            
        except Exception as e:
            self.logger.error(f"인스타그램 워크플로우 생성 실패: {e}")
            return {"error": str(e)}
    
    # ============================================
    # 🆕 폴백 메서드들 (MCP 연결 실패 시)
    # ============================================
    
    async def _generate_fallback_trend_analysis(self, keywords: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """🆕 MCP 연결 실패 시 폴백 트렌드 분석"""
        try:
            business_type = context.get("business_type", "일반") if context else "일반"
            
            # 업종별 가상 트렌드 분석 생성
            analysis_prompt = f"""다음 키워드에 대한 {business_type} 업종 관점의 트렌드 분석을 수행해주세요.

키워드: {', '.join(keywords)}
업종: {business_type}

일반적인 시장 트렌드를 바탕으로 다음을 분석해주세요:
1. 키워드별 관심도 변화 예상
2. 계절적/시기적 특성
3. 타겟 고객의 검색 패턴
4. 마케팅 활용 기회
5. 실행 가능한 전략 제안

실무에서 바로 활용할 수 있는 구체적인 인사이트를 제공해주세요."""
            
            analysis_result = await self._call_analysis_llm(analysis_prompt)
            
            return {
                "success": True,
                "type": "trend_analysis_fallback",
                "keywords": keywords,
                "analysis": analysis_result,
                "note": "외부 데이터 연결 없이 일반적 트렌드 분석 수행",
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"폴백 트렌드 분석 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "trend_analysis_fallback"
            }
    
    async def _generate_fallback_hashtag_analysis(self, hashtags: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """🆕 MCP 연결 실패 시 폴백 해시태그 분석"""
        try:
            business_type = context.get("business_type", "일반") if context else "일반"
            
            # 업종별 해시태그 최적화 제안
            optimized_hashtags = await self._generate_optimized_hashtags("", context or {})
            strategy = await self._generate_hashtag_strategy("", context or {})
            
            return {
                "success": True,
                "type": "hashtag_analysis_fallback",
                "analyzed_hashtags": hashtags,
                "optimized_hashtags": optimized_hashtags,
                "strategy": strategy,
                "note": "업종별 모범사례 기반 해시태그 최적화",
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"폴백 해시태그 분석 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "hashtag_analysis_fallback"
            }
    
    async def _generate_basic_blog_workflow(self, keyword: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """🆕 기본 블로그 워크플로우"""
        workflow = await self._create_blog_workflow_with_seo(keyword, {}, context or {})
        
        return {
            "success": True,
            "type": "blog_workflow_basic",
            "target_keyword": keyword,
            "workflow": workflow,
            "note": "기본 SEO 워크플로우 적용",
            "created_at": datetime.now().isoformat()
        }
    
    async def _generate_basic_instagram_workflow(self, keyword: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """🆕 기본 인스타그램 워크플로우"""
        workflow = await self._create_instagram_workflow_with_visuals(keyword, [], context or {})
        
        return {
            "success": True,
            "type": "instagram_workflow_basic",
            "target_keyword": keyword,
            "workflow": workflow,
            "note": "기본 비주얼 워크플로우 적용",
            "created_at": datetime.now().isoformat()
        }

# ============================================
# 🆕 모듈 팩토리 함수
# ============================================

def get_marketing_mcp_marketing_tools() -> MarketingAnalysisTools:
    """🆕 마케팅 분석 도구 인스턴스 반환"""
    return MarketingAnalysisTools()
