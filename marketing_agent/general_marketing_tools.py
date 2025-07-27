"""
마케팅 도구 모음 - 개선된 버전
✅ 맞춤화 강화, 실행력 중심, 밀도 최적화, 컨텍스트 활용 개선
"""

import json
import logging
import asyncio
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
import openai
from datetime import datetime
from config import config

# MCP 관련 임포트 (안전한 import)
try:
    from shared_modules import get_llm_manager
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"shared_modules import 실패: {e}")
    
    def get_llm_manager():
        return None

# mcp_marketing_tools import
try:
    from mcp_marketing_tools import get_marketing_mcp_marketing_tools
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"mcp_marketing_tools import 실패: {e}")
    
    def get_marketing_mcp_marketing_tools():
        return None

logger = logging.getLogger(__name__)

class MarketingTools:
    """🆕 개선된 마케팅 도구 - 맞춤화, 실행력, 컨텍스트 활용 강화"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.prompts_dir = config.PROMPTS_DIR
        self.mcp_marketing_tools = None
        self.llm_manager = get_llm_manager()
        self._load_enhanced_templates()
        self.logger = logging.getLogger(__name__)
        
        # 🆕 업종별 맞춤 설정
        self._init_industry_configs()
        
        # 🆕 컨텐츠 품질 향상을 위한 프롬프트 개선
        self._init_enhanced_prompts()
    
    def get_mcp_marketing_tools(self):
        """분석 도구를 lazy loading으로 반환"""
        if self.mcp_marketing_tools is None:
            try:
                from mcp_marketing_tools import get_marketing_mcp_marketing_tools
                self.mcp_marketing_tools = get_marketing_mcp_marketing_tools()
            except ImportError:
                self.mcp_marketing_tools = {}
        return self.mcp_marketing_tools
    
    def _load_enhanced_templates(self):
        """🆕 개선된 템플릿 로드 - 업종별 특화"""
        self.templates = {}
        
        # 핵심 템플릿들 로드
        key_templates = [
            "content_marketing.md",
            "social_media_marketing.md", 
            "blog_marketing.md",
            "digital_advertising.md"
        ]
        
        for template_file in key_templates:
            template_path = self.prompts_dir / template_file
            if template_path.exists():
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        self.templates[template_file] = f.read()
                except Exception as e:
                    self.logger.warning(f"템플릿 로드 실패: {template_file}, 오류: {e}")
            else:
                self.logger.warning(f"템플릿 파일 없음: {template_path}")
    
    def _init_industry_configs(self):
        """🆕 업종별 맞춤 설정 초기화"""
        self.industry_configs = {
            "뷰티": {
                "target_platforms": ["인스타그램", "틱톡", "유튜브"],
                "content_focus": ["제품 리뷰", "뷰티 팁", "트렌드"],
                "hashtag_style": "트렌디하고 감각적인",
                "tone": "친근하고 유행에 민감한",
                "keywords": ["뷰티", "화장품", "스킨케어", "메이크업", "트렌드"]
            },
            "음식점": {
                "target_platforms": ["인스타그램", "네이버 지도", "배달앱"],
                "content_focus": ["음식 사진", "매장 분위기", "이벤트"],
                "hashtag_style": "맛집과 지역 중심",
                "tone": "따뜻하고 친근한",
                "keywords": ["맛집", "음식", "레스토랑", "지역명", "분위기"]
            },
            "온라인쇼핑몰": {
                "target_platforms": ["인스타그램", "페이스북", "블로그"],
                "content_focus": ["제품 소개", "후기", "할인 정보"],
                "hashtag_style": "제품과 혜택 중심",
                "tone": "신뢰감 있고 전문적인",
                "keywords": ["쇼핑", "할인", "신제품", "후기", "품질"]
            },
            "서비스업": {
                "target_platforms": ["네이버 블로그", "인스타그램", "유튜브"],
                "content_focus": ["서비스 소개", "고객 사례", "전문성"],
                "hashtag_style": "전문성과 신뢰도 중심",
                "tone": "전문적이고 신뢰감 있는",
                "keywords": ["서비스", "전문", "고객만족", "품질", "신뢰"]
            }
        }
    
    def _init_enhanced_prompts(self):
        """🆕 향상된 프롬프트 초기화"""
        
        # 🆕 맞춤형 인스타그램 포스트 생성 프롬프트
        self.instagram_creation_prompt = """다음 정보를 바탕으로 업종 특성을 반영한 인스타그램 포스트를 생성해주세요.

### 비즈니스 정보
- 업종: {business_type}
- 제품/서비스: {product}
- 타겟 고객: {target_audience}
- 마케팅 목표: {main_goal}
- 키워드: {keywords}

### 업종별 맞춤 요구사항
{industry_specific_guide}

### 생성 조건
1. **캡션 작성**: 타겟 고객의 언어로 작성, 감정적 연결 유도
2. **해시태그**: 업종 특성 반영, 트렌드 + 니치 해시태그 조합 (20개)
3. **CTA**: 명확하고 실행하기 쉬운 행동 유도
4. **이미지 콘셉트**: 업종에 맞는 비주얼 3가지 제안
5. **포스팅 팁**: 최적 업로드 시간, 인게이지먼트 전략

### 출력 형식
**📸 캡션**
[매력적이고 자연스러운 캡션 - 2-3문단]

**🔖 해시태그**
#해시태그1 #해시태그2... (20개, 트렌드 + 니치 조합)

**👆 CTA**
[구체적인 행동 유도 문구]

**🎨 이미지 아이디어**
1. [이모지] [구체적인 이미지 콘셉트 1]
2. [이모지] [구체적인 이미지 콘셉트 2] 
3. [이모지] [구체적인 이미지 콘셉트 3]

**💡 포스팅 최적화 팁**
- 최적 업로드 시간: [업종별 권장 시간]
- 인게이지먼트 전략: [구체적인 방법 2-3개]

업종의 특성과 타겟 고객의 니즈를 정확히 반영하여 실제 마케팅 효과를 낼 수 있는 포스트를 만들어주세요."""

        # 🆕 맞춤형 블로그 포스트 생성 프롬프트
        self.blog_creation_prompt = """다음 정보를 바탕으로 SEO 최적화된 블로그 포스트를 생성해주세요.

### 비즈니스 정보
- 업종: {business_type}
- 제품/서비스: {product}
- 타겟 독자: {target_audience}
- 주요 키워드: {keywords}
- 마케팅 목표: {main_goal}

### 업종별 특화 전략
{industry_specific_guide}

### 블로그 포스트 요구사항
1. **SEO 최적화**: 제목, 메타 설명, 키워드 밀도 고려
2. **독자 중심**: 타겟 독자의 문제 해결과 가치 제공
3. **실용성**: 바로 적용 가능한 정보와 팁 포함
4. **신뢰성**: 전문성을 보여주는 내용과 데이터
5. **자연스러운 마케팅**: 부드러운 브랜드/제품 언급

### 출력 형식
**📝 SEO 최적화 제목** 
[클릭을 유도하는 매력적인 제목]

**📄 메타 설명 (150자 이내)**
[검색 결과에 노출될 요약 설명]

**📋 목차**
1. [도입부 소제목]
2. [본론 1 소제목]
3. [본론 2 소제목]
4. [본론 3 소제목]
5. [결론 소제목]

**📖 본문 (1800-2200자)**
[각 목차에 따른 상세 내용 - 실용적 정보, 팁, 사례 포함]

**🎯 SEO 키워드**
주요 키워드: [메인 키워드 3개]
관련 키워드: [롱테일 키워드 7개]

**📊 활용 가이드**
- 소셜미디어 공유 포인트: [핵심 메시지 2-3개]
- 후속 콘텐츠 아이디어: [관련 주제 3개]

전문성과 실용성을 겸비하여 독자에게 진짜 도움이 되는 콘텐츠를 작성해주세요."""

        # 🆕 전략 수립 프롬프트
        self.strategy_creation_prompt = """다음 비즈니스 정보를 바탕으로 실행 가능한 마케팅 전략을 수립해주세요.

### 현재 상황 분석
- 업종: {business_type}
- 제품/서비스: {product}
- 주요 목표: {main_goal}
- 타겟 고객: {target_audience}
- 예산 규모: {budget}
- 선호 채널: {channels}

### 업종별 시장 특성
{industry_insights}

### 전략 수립 원칙
1. **실행 가능성**: 현실적이고 달성 가능한 목표
2. **단계적 접근**: 즉시 시작 → 단기 성과 → 장기 성장
3. **ROI 중심**: 투자 대비 효과 명확히 제시
4. **차별화**: 경쟁사 대비 독특한 포지셔닝
5. **측정 가능**: 구체적인 성과 지표 설정

### 전략서 구조
**🎯 전략 개요**
[핵심 전략 한 줄 요약 + 기대 효과]

**📊 현황 분석**
- 시장 기회: [업종별 트렌드와 기회 요소]
- 경쟁 우위: [차별화 포인트]
- 핵심 과제: [해결해야 할 주요 이슈]

**🏆 목표 설정 (SMART)**
- 주 목표: [구체적, 측정 가능한 목표]
- 부 목표: [보조 목표 2-3개]
- 성공 지표: [KPI 및 측정 방법]

**👥 타겟 전략**
- 주요 타겟: [상세 페르소나]
- 고객 여정: [인식 → 관심 → 구매 → 충성]
- 메시지 전략: [타겟별 핵심 메시지]

**📺 채널 전략**
- 주력 채널: [예산과 효과성 기준 선정]
- 보조 채널: [시너지 효과 기대 채널]
- 채널별 역할: [각 채널의 구체적 활용법]

**📅 실행 로드맵 (3개월)**
**1개월차**: [기반 구축 활동]
**2개월차**: [본격 실행 활동]  
**3개월차**: [최적화 및 확장]

**💰 예산 배분**
- 채널별 예산: [구체적 금액/비율]
- 콘텐츠 제작: [제작비 가이드]
- 운영 비용: [월별 운영비]

**📈 성과 측정**
- 주간 체크: [주요 지표 3개]
- 월간 평가: [종합 성과 리뷰]
- 개선 방안: [지속적 최적화 방법]

실무진이 바로 실행할 수 있도록 구체적이고 실용적인 전략을 제시해주세요."""

        # 🆕 캠페인 기획 프롬프트
        self.campaign_creation_prompt = """다음 정보를 바탕으로 효과적인 마케팅 캠페인을 기획해주세요.

### 캠페인 기본 정보
- 업종: {business_type}
- 제품/서비스: {product}
- 캠페인 목표: {campaign_goal}
- 타겟 고객: {target_audience}
- 예산: {budget}
- 기간: {duration}
- 주요 채널: {channels}

### 업종별 캠페인 특성
{industry_campaign_guide}

### 캠페인 기획 요구사항
1. **임팩트**: 타겟에게 강한 인상 남기기
2. **차별화**: 경쟁사와 구별되는 독창적 아이디어
3. **실행성**: 예산과 기간 내 실현 가능
4. **확장성**: 성공 시 스케일업 가능
5. **측정성**: 성과 추적 가능한 구조

### 캠페인 기획서
**🚀 캠페인 개요**
- 캠페인명: [기억하기 쉬운 네이밍]
- 핵심 메시지: [한 줄 슬로건]
- 차별화 포인트: [독창적 아이디어]

**🎯 목표 및 성공 지표**
- 주요 목표: [구체적 수치 목표]
- 보조 목표: [부가적 기대 효과]
- 성공 지표: [측정 가능한 KPI]

**👥 타겟 분석**
- 주 타겟: [상세 페르소나 + 니즈]
- 부 타겟: [보조 타겟층]
- 타겟 인사이트: [행동 패턴과 선호도]

**💡 핵심 아이디어**
- 컨셉: [캠페인 핵심 아이디어]
- 스토리텔링: [감정적 연결 방법]
- 참여 요소: [고객 참여 유도 방법]

**📺 채널별 실행 계획**
{channels} 채널 활용:
- 콘텐츠 유형: [채널별 맞춤 콘텐츠]
- 메시지 조정: [채널 특성 반영]
- 예산 배분: [채널별 투자 비율]

**📅 실행 일정**
- 사전 준비: [2-3주 전 준비사항]
- 캠페인 런칭: [1주차 활동]
- 본격 실행: [2-3주차 활동]  
- 마무리: [4주차 정리 활동]

**🎨 크리에이티브 가이드**
- 비주얼 콘셉트: [이미지/영상 방향성]
- 톤앤매너: [브랜드 일관성 유지]
- 제작 우선순위: [핵심 크리에이티브]

**📊 성과 측정 계획**
- 실시간 모니터링: [일일 체크 지표]
- 주간 리포트: [주요 성과 정리]
- 캠페인 종료 후: [최종 성과 분석]

**🔄 최적화 방안**
- A/B 테스트: [테스트할 요소들]
- 피드백 반영: [고객 반응 활용법]
- 확장 계획: [성공 시 후속 방안]

창의적이면서도 실현 가능한 캠페인을 기획해주세요."""
    
    # ============================================
    # MCP 연동 함수들 (기존 유지)
    # ============================================
    
    async def analyze_naver_trends(self, keywords: List[str]) -> Dict[str, Any]:
        """네이버 트렌드 분석 (MCP 연동)"""
        if not self.mcp_marketing_tools:
            return {"success": False, "error": "mcp_marketing_tools 초기화 실패"}
        
        return await self.mcp_marketing_tools.analyze_naver_trends(keywords)
    
    async def analyze_instagram_hashtags(self, question: str, user_hashtags: List[str]) -> Dict[str, Any]:
        """인스타그램 해시태그 분석 (MCP 연동)"""
        if not self.mcp_marketing_tools:
            return {"success": False, "error": "mcp_marketing_tools 초기화 실패"}
        
        return await self.mcp_marketing_tools.analyze_instagram_hashtags(question, user_hashtags)
    
    async def create_blog_content_workflow(self, target_keyword: str) -> Dict[str, Any]:
        """블로그 콘텐츠 워크플로우 (MCP 연동)"""
        if not self.mcp_marketing_tools:
            return {"success": False, "error": "mcp_marketing_tools 초기화 실패"}
        
        result = await self.mcp_marketing_tools.create_blog_content_workflow(target_keyword)
        
        if result.get("success"):
            result["tool_type"] = "content_generation"
            result["content_type"] = "blog"
        
        return result
    
    async def create_instagram_content_workflow(self, target_keyword: str) -> Dict[str, Any]:
        """인스타그램 콘텐츠 워크플로우 (MCP 연동)"""
        if not self.mcp_marketing_tools:
            return {"success": False, "error": "mcp_marketing_tools 초기화 실패"}
        
        result = await self.mcp_marketing_tools.create_instagram_content_workflow(target_keyword)
        
        if result.get("success"):
            result["tool_type"] = "content_generation"
            result["content_type"] = "instagram"
        
        return result
    
    async def generate_instagram_content(self) -> Dict[str, Any]:
        """인스타그램 마케팅 콘텐츠 생성 (MCP 연동)"""
        if not self.mcp_marketing_tools:
            return {"success": False, "error": "mcp_marketing_tools 초기화 실패"}
        
        return await self.mcp_marketing_tools.generate_instagram_content()
    
    # ============================================
    # 🆕 개선된 콘텐츠 생성 함수들
    # ============================================
    
    async def create_strategy_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """🆕 업종별 맞춤 전략 콘텐츠 생성"""
        try:
            business_type = context.get("business_type", "일반")
            
            # 업종별 인사이트 추가
            industry_insights = self._get_industry_insights(business_type)
            
            result = await self.generate_marketing_strategy_enhanced(context, industry_insights)
            
            if result.get("success"):
                result["tool_type"] = "content_generation"
                result["content_type"] = "strategy"
            
            return result
            
        except Exception as e:
            self.logger.error(f"전략 콘텐츠 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_type": "content_generation",
                "content_type": "strategy"
            }
    
    async def create_campaign_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """🆕 업종별 맞춤 캠페인 콘텐츠 생성"""
        try:
            business_type = context.get("business_type", "일반")
            
            # 업종별 캠페인 가이드 추가
            campaign_guide = self._get_industry_campaign_guide(business_type)
            
            result = await self.create_campaign_plan_enhanced(context, campaign_guide)
            
            if result.get("success"):
                result["tool_type"] = "content_generation"
                result["content_type"] = "campaign"
            
            return result
            
        except Exception as e:
            self.logger.error(f"캠페인 콘텐츠 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_type": "content_generation",
                "content_type": "campaign"
            }
    
    async def create_instagram_post(self, keywords: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """🆕 업종별 맞춤 인스타그램 포스트 생성"""
        try:
            if not context:
                context = {}
                
            business_type = context.get("business_type", "일반")
            target_audience = context.get("target_audience", "20-30대")
            product = context.get("product", "미정")
            main_goal = context.get("main_goal", "브랜드 인지도 향상")
            
            # 🆕 업종별 특화 가이드 생성
            industry_guide = self._get_industry_specific_guide(business_type, "instagram")
            
            # 향상된 프롬프트로 콘텐츠 생성
            formatted_prompt = self.instagram_creation_prompt.format(
                business_type=business_type,
                product=product,
                target_audience=target_audience,
                main_goal=main_goal,
                keywords=', '.join(keywords),
                industry_specific_guide=industry_guide
            )
            
            content = await self.generate_content_with_enhanced_llm(formatted_prompt, context)
            
            # 🆕 향상된 결과 파싱
            result = self._parse_instagram_content_enhanced(content)
            result.update({
                "success": True,
                "type": "instagram_post",
                "keywords": keywords,
                "business_type": business_type,
                "industry_optimized": True,
                "generated_at": datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"인스타그램 포스트 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "instagram_post"
            }
    
    async def create_blog_post(self, keywords: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """🆕 업종별 맞춤 블로그 포스트 생성"""
        try:
            if not context:
                context = {}
                
            business_type = context.get("business_type", "일반")
            target_audience = context.get("target_audience", "일반 고객")
            product = context.get("product", "미정")
            main_goal = context.get("main_goal", "전문성 어필")
            
            # 🆕 업종별 특화 가이드 생성
            industry_guide = self._get_industry_specific_guide(business_type, "blog")
            
            # 향상된 프롬프트로 콘텐츠 생성
            formatted_prompt = self.blog_creation_prompt.format(
                business_type=business_type,
                product=product,
                target_audience=target_audience,
                keywords=', '.join(keywords),
                main_goal=main_goal,
                industry_specific_guide=industry_guide
            )
            
            content = await self.generate_content_with_enhanced_llm(formatted_prompt, context)
            
            # 🆕 향상된 결과 파싱
            result = self._parse_blog_content_enhanced(content)
            result.update({
                "success": True,
                "type": "blog_post",
                "keywords": keywords,
                "business_type": business_type,
                "industry_optimized": True,
                "generated_at": datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"블로그 포스트 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "blog_post"
            }
    
    # ============================================
    # 🆕 업종별 특화 메서드들
    # ============================================
    
    def _get_industry_specific_guide(self, business_type: str, content_type: str) -> str:
        """🆕 업종별 특화 가이드 생성"""
        industry_config = self.industry_configs.get(business_type, {})
        
        if not industry_config:
            return "일반적인 마케팅 원칙을 적용합니다."
        
        if content_type == "instagram":
            return f"""
### {business_type} 업종 인스타그램 특화 전략
- **주요 플랫폼**: {', '.join(industry_config.get('target_platforms', []))}
- **콘텐츠 포커스**: {', '.join(industry_config.get('content_focus', []))}
- **해시태그 스타일**: {industry_config.get('hashtag_style', '')}
- **권장 톤**: {industry_config.get('tone', '')}
- **핵심 키워드**: {', '.join(industry_config.get('keywords', []))}

### 업종별 성공 포인트
{self._get_industry_success_tips(business_type, 'instagram')}
"""
        elif content_type == "blog":
            return f"""
### {business_type} 업종 블로그 특화 전략  
- **전문성 어필 포인트**: {self._get_expertise_points(business_type)}
- **타겟 독자 관심사**: {self._get_reader_interests(business_type)}
- **SEO 최적화 키워드**: {', '.join(industry_config.get('keywords', []))}
- **신뢰도 구축 방법**: {self._get_trust_building_methods(business_type)}

### 콘텐츠 차별화 전략
{self._get_content_differentiation(business_type)}
"""
        
        return "업종별 맞춤 전략을 적용합니다."
    
    def _get_industry_insights(self, business_type: str) -> str:
        """🆕 업종별 시장 인사이트"""
        insights = {
            "뷰티": """
**뷰티 시장 특성**
- 트렌드 변화가 빠름 (주기: 3-6개월)
- 비주얼 중심의 마케팅 효과적
- 인플루언서 마케팅 필수
- 개인화/맞춤화 트렌드 증가
- MZ세대가 주요 소비층
""",
            "음식점": """
**외식업 시장 특성**
- 지역 기반 마케팅 중요
- 배달 서비스 확산으로 온라인 존재감 필수
- 리뷰와 입소문이 결정적 영향
- 시각적 어필 (음식 사진) 중요
- 단골 고객 유지가 핵심
""",
            "온라인쇼핑몰": """
**이커머스 시장 특성**
- 치열한 가격 경쟁
- 고객 리뷰와 평점의 중요성 증대
- 빠른 배송, 간편한 교환/환불 기대
- 개인화 추천 시스템 필요
- 모바일 퍼스트 전략 필수
""",
            "서비스업": """
**서비스업 시장 특성**
- 신뢰도와 전문성이 핵심
- 무형의 가치를 유형으로 시각화 필요
- 고객 사례와 후기가 중요
- 관계 마케팅 중심
- 지속적인 커뮤니케이션 필요
"""
        }
        
        return insights.get(business_type, "일반적인 시장 분석을 적용합니다.")
    
    def _get_industry_campaign_guide(self, business_type: str) -> str:
        """🆕 업종별 캠페인 가이드"""
        guides = {
            "뷰티": """
**뷰티 캠페인 특화 요소**
- 시즌/트렌드 연계 기획 (봄 컬러, 여름 선케어 등)
- 뷰티 인플루언서/뷰티크리에이터 협업
- 체험단/제품 리뷰 캠페인 효과적
- 비포&애프터 콘텐츠 활용
- 한정판/신제품 출시와 연계
""",
            "음식점": """
**외식업 캠페인 특화 요소**
- 시즌 메뉴/이벤트와 연계 (여름 냉면, 겨울 국물요리)
- 지역 커뮤니티 참여형 이벤트
- 음식 사진/영상 콘테스트
- 단골 고객 대상 로열티 프로그램
- 배달앱과 연계한 할인 이벤트
""",
            "온라인쇼핑몰": """
**이커머스 캠페인 특화 요소**
- 시즌 세일/특가 이벤트 (블랙프라이데이, 연말정산)
- 신규 가입 혜택/첫 구매 할인
- 리뷰 작성 리워드 프로그램
- 소셜미디어 공유 이벤트
- 재구매 유도 리타겟팅 캠페인
""",
            "서비스업": """
**서비스업 캠페인 특화 요소**
- 전문성 어필 웨비나/세미나
- 고객 사례 공유 이벤트
- 무료 상담/진단 서비스 제공
- 고객 추천 리워드 프로그램
- 브랜드 스토리/가치 전달 캠페인
"""
        }
        
        return guides.get(business_type, "일반적인 캠페인 전략을 적용합니다.")
    
    def _get_industry_success_tips(self, business_type: str, content_type: str) -> str:
        """업종별 성공 팁"""
        tips = {
            "뷰티": {
                "instagram": "트렌드 해시태그 활용, 뷰티 팁 공유, 고객 변신 스토리 활용"
            },
            "음식점": {
                "instagram": "음식 사진 퀄리티, 매장 분위기 어필, 지역 태그 활용"
            }
        }
        
        return tips.get(business_type, {}).get(content_type, "업종 특성을 반영한 콘텐츠 제작")
    
    def _get_expertise_points(self, business_type: str) -> str:
        """전문성 어필 포인트"""
        points = {
            "뷰티": "성분 분석, 피부 타입별 추천, 뷰티 트렌드 분석",
            "음식점": "요리 레시피, 식재료 정보, 영양 정보",
            "온라인쇼핑몰": "상품 비교 분석, 구매 가이드, 품질 정보",
            "서비스업": "업계 노하우, 사례 분석, 문제 해결 방법"
        }
        return points.get(business_type, "전문 지식과 경험")
    
    def _get_reader_interests(self, business_type: str) -> str:
        """독자 관심사"""
        interests = {
            "뷰티": "뷰티 팁, 제품 리뷰, 트렌드 정보, 피부 관리법",
            "음식점": "맛집 정보, 요리법, 건강한 식단, 분위기 좋은 곳",
            "온라인쇼핑몰": "가성비 상품, 신제품 정보, 할인 혜택, 구매 팁",
            "서비스업": "문제 해결, 비용 절감, 효율성 향상, 전문 조언"
        }
        return interests.get(business_type, "관련 정보와 팁")
    
    def _get_trust_building_methods(self, business_type: str) -> str:
        """신뢰도 구축 방법"""
        methods = {
            "뷰티": "성분 근거 제시, 피부과 전문의 의견, 실제 사용 후기",
            "음식점": "신선한 재료 소개, 조리 과정 공개, 고객 후기",
            "온라인쇼핑몰": "상품 인증서, 고객 리뷰, 교환/환불 정책 안내",
            "서비스업": "자격증/경력 소개, 고객 사례, 투명한 프로세스"
        }
        return methods.get(business_type, "전문성과 투명성 강조")
    
    def _get_content_differentiation(self, business_type: str) -> str:
        """콘텐츠 차별화 전략"""
        strategies = {
            "뷰티": "개인별 맞춤 솔루션 제공, 트렌드 선도적 정보, 실용적 팁 중심",
            "음식점": "스토리텔링 강화, 지역 특색 반영, 감성적 경험 공유",
            "온라인쇼핑몰": "상품 큐레이션, 라이프스타일 제안, 실용 정보 제공",
            "서비스업": "데이터 기반 인사이트, 단계별 가이드, 실제 사례 중심"
        }
        return strategies.get(business_type, "독창적이고 유용한 콘텐츠 제작")
    
    # ============================================
    # 🆕 향상된 콘텐츠 생성 및 파싱 메서드들
    # ============================================
    
    async def generate_content_with_enhanced_llm(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """🆕 향상된 LLM 콘텐츠 생성 - 컨텍스트 활용 강화"""
        try:
            # 🆕 더 풍부한 컨텍스트 정보 추가
            enhanced_context = self._build_enhanced_context(context) if context else ""
            
            full_prompt = f"{enhanced_context}\n\n{prompt}" if enhanced_context else prompt
            
            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": """당신은 업종별 마케팅 전문가입니다. 다음 원칙에 따라 콘텐츠를 작성해주세요:

1. **맞춤화**: 업종과 타겟 고객에 특화된 콘텐츠
2. **실행력**: 바로 사용할 수 있는 구체적인 내용
3. **전문성**: 해당 분야의 트렌드와 베스트 프랙티스 반영
4. **차별화**: 경쟁사와 구별되는 독창적 접근
5. **효과성**: 실제 마케팅 성과를 낼 수 있는 실용적 콘텐츠

업종별 특성을 정확히 파악하여 타겟 고객에게 어필할 수 있는 고품질 콘텐츠를 작성해주세요."""},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=config.TEMPERATURE,
                max_tokens=2500  # 토큰 수 증가
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"향상된 LLM 콘텐츠 생성 실패: {e}")
            return f"죄송합니다. 콘텐츠 생성 중 오류가 발생했습니다: {str(e)}"
    
    def _build_enhanced_context(self, context: Dict[str, Any]) -> str:
        """🆕 향상된 컨텍스트 구성"""
        context_parts = []
        
        # 핵심 비즈니스 정보
        business_type = context.get("business_type", "일반")
        if business_type != "일반":
            context_parts.append(f"### 비즈니스 컨텍스트\n업종: {business_type}")
            
            # 업종별 추가 인사이트
            industry_config = self.industry_configs.get(business_type, {})
            if industry_config:
                context_parts.append(f"핵심 키워드: {', '.join(industry_config.get('keywords', []))}")
                context_parts.append(f"권장 톤: {industry_config.get('tone', '')}")
        
        # 타겟 및 목표 정보
        target_info = []
        if context.get("target_audience"):
            target_info.append(f"타겟: {context['target_audience']}")
        if context.get("main_goal"):
            target_info.append(f"목표: {context['main_goal']}")
        if target_info:
            context_parts.append(f"### 마케팅 목표\n{', '.join(target_info)}")
        
        # 제품/서비스 정보
        if context.get("product"):
            context_parts.append(f"### 제품/서비스\n{context['product']}")
        
        # 기타 중요 정보
        other_info = []
        for key in ["budget", "channels", "pain_points"]:
            if context.get(key):
                other_info.append(f"{key}: {context[key]}")
        if other_info:
            context_parts.append(f"### 추가 정보\n{', '.join(other_info)}")
        
        return "\n\n".join(context_parts) if context_parts else ""
    
    def _parse_instagram_content_enhanced(self, content: str) -> Dict[str, str]:
        """🆕 향상된 인스타그램 콘텐츠 파싱"""
        try:
            result = {
                "caption": "",
                "hashtags": "",
                "cta": "",
                "image_concepts": [],
                "posting_tips": "",
                "full_content": content
            }
            
            # 섹션별 파싱 (이모지 기반)
            sections = {
                "📸": "caption",
                "🔖": "hashtags", 
                "👆": "cta",
                "🎨": "image_concepts",
                "💡": "posting_tips"
            }
            
            lines = content.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                # 섹션 헤더 감지
                for emoji, section_name in sections.items():
                    if line.startswith(emoji):
                        current_section = section_name
                        continue
                
                # 내용 추가
                if line and current_section:
                    if current_section == "image_concepts":
                        if line.startswith(('1.', '2.', '3.', '-')):
                            result[current_section].append(line)
                    else:
                        if result[current_section]:
                            result[current_section] += "\n" + line
                        else:
                            result[current_section] = line
            
            return result
            
        except Exception as e:
            self.logger.error(f"인스타그램 콘텐츠 파싱 실패: {e}")
            return {
                "caption": content[:500] + "..." if len(content) > 500 else content,
                "hashtags": "",
                "cta": "",
                "image_concepts": [],
                "posting_tips": "",
                "full_content": content
            }
    
    def _parse_blog_content_enhanced(self, content: str) -> Dict[str, str]:
        """🆕 향상된 블로그 콘텐츠 파싱"""
        try:
            result = {
                "title": "",
                "meta_description": "",
                "outline": "",
                "body": "",
                "seo_keywords": "",
                "usage_guide": "",
                "full_content": content
            }
            
            # 섹션별 파싱 (이모지 기반)
            sections = {
                "📝": "title",
                "📄": "meta_description",
                "📋": "outline",
                "📖": "body",
                "🎯": "seo_keywords",
                "📊": "usage_guide"
            }
            
            lines = content.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                # 섹션 헤더 감지
                for emoji, section_name in sections.items():
                    if line.startswith(emoji):
                        current_section = section_name
                        continue
                
                # 내용 추가
                if line and current_section:
                    if result[current_section]:
                        result[current_section] += "\n" + line
                    else:
                        result[current_section] = line
            
            return result
            
        except Exception as e:
            self.logger.error(f"블로그 콘텐츠 파싱 실패: {e}")
            return {
                "title": "블로그 포스트 제목",
                "meta_description": "",
                "outline": "",
                "body": content,
                "seo_keywords": "",
                "usage_guide": "",
                "full_content": content
            }
    
    # ============================================
    # 🆕 향상된 전략 및 캠페인 생성 메서드들
    # ============================================
    
    async def generate_marketing_strategy_enhanced(self, context: Dict[str, Any], industry_insights: str) -> Dict[str, Any]:
        """🆕 향상된 마케팅 전략 생성"""
        try:
            business_type = context.get("business_type", "일반")
            main_goal = context.get("main_goal", "매출 증대")
            target_audience = context.get("target_audience", "일반 고객")
            budget = context.get("budget", "미정")
            channels = context.get("preferred_channel", "SNS")
            
            formatted_prompt = self.strategy_creation_prompt.format(
                business_type=business_type,
                product=context.get("product", "미정"),
                main_goal=main_goal,
                target_audience=target_audience,
                budget=budget,
                channels=channels,
                industry_insights=industry_insights
            )
            
            content = await self.generate_content_with_enhanced_llm(formatted_prompt, context)
            
            return {
                "success": True,
                "type": "marketing_strategy",
                "strategy": content,
                "business_type": business_type,
                "main_goal": main_goal,
                "industry_optimized": True,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"향상된 마케팅 전략 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "marketing_strategy"
            }
    
    async def create_campaign_plan_enhanced(self, context: Dict[str, Any], campaign_guide: str) -> Dict[str, Any]:
        """🆕 향상된 캠페인 계획 생성"""
        try:
            business_type = context.get("business_type", "일반")
            campaign_goal = context.get("campaign_goal", "브랜드 인지도 향상")
            target_audience = context.get("target_audience", "일반 고객")
            budget = context.get("budget", "미정")
            duration = context.get("duration", "1개월")
            channels = context.get("preferred_channel", "SNS")
            
            formatted_prompt = self.campaign_creation_prompt.format(
                business_type=business_type,
                product=context.get("product", "미정"),
                campaign_goal=campaign_goal,
                target_audience=target_audience,
                budget=budget,
                duration=duration,
                channels=channels,
                industry_campaign_guide=campaign_guide
            )
            
            content = await self.generate_content_with_enhanced_llm(formatted_prompt, context)
            
            return {
                "success": True,
                "type": "campaign_plan",
                "plan": content,
                "business_type": business_type,
                "campaign_goal": campaign_goal,
                "duration": duration,
                "industry_optimized": True,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"향상된 캠페인 계획 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "campaign_plan"
            }
    
    # ============================================
    # 기존 메서드들 유지
    # ============================================
    
    async def analyze_keywords(self, keywords: List[str]) -> Dict[str, Any]:
        """키워드 분석 및 관련 키워드 추천"""
        try:
            main_keyword = keywords[0] if keywords else "마케팅"
            
            prompt = f"""
'{main_keyword}'에 대한 마케팅 키워드 분석을 해주세요.

**관련 키워드**: {', '.join(keywords)}

**분석 항목:**
1. 주요 키워드 특성 분석
2. 트렌드 예상 (상승/하락/유지)
3. 경쟁도 예상 (높음/중간/낮음)
4. 타겟 오디언스 예상
5. 마케팅 활용 방안

**출력 형식:**
```
주요 키워드: {main_keyword}

키워드 특성:
[키워드의 마케팅적 특성]

관련 키워드 TOP 10:
1. [키워드1] - [활용도]
2. [키워드2] - [활용도]
...

트렌드 분석:
[트렌드 예상 및 근거]

경쟁도 분석:
[경쟁도 예상 및 근거]

타겟 오디언스:
[예상 타겟층]

마케팅 활용 방안:
[구체적인 활용 방법]
```
"""
            
            content = await self.generate_content_with_enhanced_llm(prompt)
            
            return {
                "success": True,
                "type": "keyword_analysis", 
                "analysis": content,
                "keywords": keywords,
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"키워드 분석 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "keyword_analysis"
            }
    
    # 기존 generate_content_with_llm 메서드도 유지
    async def generate_content_with_llm(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """기존 LLM 콘텐츠 생성 (하위 호환성)"""
        return await self.generate_content_with_enhanced_llm(prompt, context)
    
    def get_available_tools(self) -> List[str]:
        """사용 가능한 도구 목록 반환"""
        return [
            "analyze_naver_trends",
            "analyze_instagram_hashtags", 
            "create_instagram_post",
            "create_blog_post",
            "create_strategy_content",
            "create_campaign_content",
            "analyze_keywords"
        ]
