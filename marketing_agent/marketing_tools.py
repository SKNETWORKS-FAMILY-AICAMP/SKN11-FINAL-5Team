"""
마케팅 도구 모음 - 개선된 버전
컨텐츠 수정 및 멀티턴 대화 지원 기능 추가
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import openai
from config import config

logger = logging.getLogger(__name__)

class MarketingTools:
    """개선된 마케팅 도구 모음 - 컨텐츠 수정 및 멀티턴 지원"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.prompts_dir = config.PROMPTS_DIR
        self._load_templates()
    
    def _load_templates(self):
        """마케팅 템플릿 로드"""
        self.templates = {}
        
        # 주요 템플릿들만 로드
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
                    logger.warning(f"템플릿 로드 실패: {template_file}, 오류: {e}")
            else:
                logger.warning(f"템플릿 파일 없음: {template_path}")
    
    async def generate_content_with_llm(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """LLM을 사용한 콘텐츠 생성"""
        try:
            # 컨텍스트 정보 추가
            full_prompt = prompt
            if context:
                context_str = f"\n\n**참고 정보:**\n"
                for key, value in context.items():
                    if value and key not in ['modification_request', 'detected_modifications', 'previous_content']:
                        context_str += f"- {key}: {value}\n"
                
                # 수정 요청 관련 정보 별도 처리
                if context.get('modification_request'):
                    context_str += f"\n**수정 요청:** {context['modification_request']}\n"
                if context.get('previous_content'):
                    context_str += f"\n**이전 버전:** {context['previous_content'][:200]}...\n"
                
                full_prompt = context_str + "\n" + prompt
            
            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "당신은 마케팅 전문가입니다. 실용적이고 구체적인 마케팅 콘텐츠를 작성해주세요."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=config.TEMPERATURE,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM 콘텐츠 생성 실패: {e}")
            return f"죄송합니다. 콘텐츠 생성 중 오류가 발생했습니다: {str(e)}"
    
    async def create_instagram_post(self, keyword: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """인스타그램 포스트 생성"""
        try:
            business_type = context.get("business_type", "일반") if context else "일반"
            target_audience = context.get("target_audience", "20-30대") if context else "20-30대"
            
            prompt = f"""
{keyword}에 대한 인스타그램 포스트를 작성해주세요.

**요구사항:**
- 업종: {business_type}
- 타겟: {target_audience}
- 매력적인 캡션 (이모지 포함)
- 관련 해시태그 20개
- 참여를 유도하는 CTA (Call-to-Action)

**출력 형식:**
```
캡션:
[매력적인 캡션 내용]

해시태그:
#해시태그1 #해시태그2 ... (20개)

CTA:
[참여 유도 문구]
```
"""
            
            content = await self.generate_content_with_llm(prompt, context)
            
            # 결과 파싱
            result = self._parse_instagram_content(content)
            result.update({
                "success": True,
                "type": "instagram_post",
                "keyword": keyword,
                "business_type": business_type
            })
            
            return result
            
        except Exception as e:
            logger.error(f"인스타그램 포스트 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "instagram_post"
            }
    
    async def create_instagram_post_with_modifications(self, keyword: str, context: Dict[str, Any], 
                                                    modification_request: str) -> Dict[str, Any]:
        """인스타그램 포스트 수정 버전 생성 - 새로운 기능"""
        try:
            business_type = context.get("business_type", "일반")
            target_audience = context.get("target_audience", "20-30대")
            previous_content = context.get("previous_content", "")
            detected_modifications = context.get("detected_modifications", [])
            
            # 수정 지시사항 분석
            modification_instructions = self._analyze_modification_request(modification_request, detected_modifications)
            
            prompt = f"""
{keyword}에 대한 인스타그램 포스트를 사용자의 피드백에 따라 수정해주세요.

**기본 정보:**
- 업종: {business_type}
- 타겟: {target_audience}

**사용자 피드백:** {modification_request}

**수정 지시사항:**
{modification_instructions}

**이전 버전 참고:**
{previous_content[:300] if previous_content else "이전 버전 없음"}

**수정된 포스트 출력 형식:**
```
캡션:
[수정된 캡션 내용]

해시태그:
#해시태그1 #해시태그2 ... 

CTA:
[수정된 참여 유도 문구]
```

사용자의 요청을 정확히 반영하여 개선해주세요.
"""
            
            content = await self.generate_content_with_llm(prompt, context)
            
            # 결과 파싱
            result = self._parse_instagram_content(content)
            result.update({
                "success": True,
                "type": "instagram_post",
                "keyword": keyword,
                "business_type": business_type,
                "modification_applied": modification_request,
                "iteration": context.get("iteration_count", 1)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"인스타그램 포스트 수정 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "instagram_post"
            }
    
    def _analyze_modification_request(self, request: str, detected_modifications: List[str]) -> str:
        """수정 요청 분석 및 지시사항 생성"""
        instructions = []
        
        request_lower = request.lower()
        
        # 톤앤매너 수정
        if "친근" in request or "casual" in detected_modifications:
            instructions.append("- 톤을 더 친근하고 편안하게 수정")
        elif "전문적" in request or "professional" in detected_modifications:
            instructions.append("- 톤을 더 전문적이고 신뢰성 있게 수정")
        elif "재밌게" in request or "fun" in detected_modifications:
            instructions.append("- 톤을 더 재미있고 유머러스하게 수정")
        
        # 길이 조정
        if "짧게" in request or "shorter" in detected_modifications:
            instructions.append("- 전체 길이를 짧고 간결하게 수정")
        elif "길게" in request or "longer" in detected_modifications:
            instructions.append("- 더 자세하고 길게 내용을 확장")
        
        # 해시태그 수정
        if "해시태그" in request or "hashtags" in detected_modifications:
            if "추가" in request:
                instructions.append("- 해시태그를 더 많이 추가 (25-30개)")
            elif "줄여" in request:
                instructions.append("- 해시태그 수를 줄이기 (10-15개)")
            else:
                instructions.append("- 해시태그를 다른 키워드로 교체")
        
        # 스타일 변경
        if "스타일" in request:
            instructions.append("- 전체적인 글쓰기 스타일을 다르게 변경")
        
        # 기본 지시사항
        if not instructions:
            instructions.append("- 사용자 피드백을 반영하여 전반적으로 개선")
        
        return "\n".join(instructions)
    
    def _parse_instagram_content(self, content: str) -> Dict[str, str]:
        """인스타그램 콘텐츠 파싱"""
        try:
            lines = content.split('\n')
            result = {
                "caption": "",
                "hashtags": "",
                "cta": "",
                "full_content": content
            }
            
            current_section = None
            for line in lines:
                line = line.strip()
                if line.startswith('캡션:'):
                    current_section = "caption"
                elif line.startswith('해시태그:'):
                    current_section = "hashtags"
                elif line.startswith('CTA:'):
                    current_section = "cta"
                elif line and current_section:
                    if result[current_section]:
                        result[current_section] += "\n" + line
                    else:
                        result[current_section] = line
            
            return result
            
        except Exception as e:
            logger.warning(f"인스타그램 콘텐츠 파싱 실패: {e}")
            return {
                "caption": content,
                "hashtags": "",
                "cta": "",
                "full_content": content
            }
    
    async def create_blog_post(self, keyword: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """블로그 포스트 생성"""
        try:
            business_type = context.get("business_type", "일반") if context else "일반"
            target_audience = context.get("target_audience", "일반 고객") if context else "일반 고객"
            
            # 블로그 템플릿 사용
            blog_template = self.templates.get("blog_marketing.md", "")
            
            prompt = f"""
{keyword}에 대한 블로그 포스트를 작성해주세요.

**요구사항:**
- 업종: {business_type}
- 타겟 독자: {target_audience}
- 1500-2000자 분량
- SEO 최적화된 제목
- 목차와 소제목
- 실용적인 정보 제공
- 자연스러운 마케팅 메시지 포함

**블로그 마케팅 가이드:**
{blog_template[:1000]}

**출력 형식:**
```
제목: [SEO 최적화된 제목]

목차:
1. [소제목1]
2. [소제목2]
3. [소제목3]

본문:
[블로그 포스트 내용]

SEO 키워드: [관련 키워드 5개]
```
"""
            
            content = await self.generate_content_with_llm(prompt, context)
            
            # 결과 파싱
            result = self._parse_blog_content(content)
            result.update({
                "success": True,
                "type": "blog_post",
                "keyword": keyword,
                "business_type": business_type
            })
            
            return result
            
        except Exception as e:
            logger.error(f"블로그 포스트 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "blog_post"
            }
    
    async def create_blog_post_with_modifications(self, keyword: str, context: Dict[str, Any], 
                                                modification_request: str) -> Dict[str, Any]:
        """블로그 포스트 수정 버전 생성 - 새로운 기능"""
        try:
            business_type = context.get("business_type", "일반")
            target_audience = context.get("target_audience", "일반 고객")
            previous_content = context.get("previous_content", "")
            
            prompt = f"""
{keyword}에 대한 블로그 포스트를 사용자의 피드백에 따라 수정해주세요.

**기본 정보:**
- 업종: {business_type}
- 타겟 독자: {target_audience}

**사용자 피드백:** {modification_request}

**이전 버전 참고:**
{previous_content[:500] if previous_content else "이전 버전 없음"}

**수정 지침:**
- 사용자 피드백을 정확히 반영
- 전체적인 구조와 품질 유지
- SEO 최적화 고려

**수정된 블로그 포스트 출력 형식:**
```
제목: [수정된 제목]

목차:
1. [수정된 소제목들]

본문:
[수정된 본문 내용]

SEO 키워드: [관련 키워드]
```
"""
            
            content = await self.generate_content_with_llm(prompt, context)
            
            # 결과 파싱
            result = self._parse_blog_content(content)
            result.update({
                "success": True,
                "type": "blog_post",
                "keyword": keyword,
                "business_type": business_type,
                "modification_applied": modification_request,
                "iteration": context.get("iteration_count", 1)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"블로그 포스트 수정 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "blog_post"
            }
    
    def _parse_blog_content(self, content: str) -> Dict[str, str]:
        """블로그 콘텐츠 파싱"""
        try:
            lines = content.split('\n')
            result = {
                "title": "",
                "outline": "",
                "body": "",
                "keywords": "",
                "full_content": content
            }
            
            current_section = None
            for line in lines:
                line = line.strip()
                if line.startswith('제목:'):
                    result["title"] = line.replace('제목:', '').strip()
                elif line.startswith('목차:'):
                    current_section = "outline"
                elif line.startswith('본문:'):
                    current_section = "body"
                elif line.startswith('SEO 키워드:'):
                    result["keywords"] = line.replace('SEO 키워드:', '').strip()
                elif line and current_section:
                    if result[current_section]:
                        result[current_section] += "\n" + line
                    else:
                        result[current_section] = line
            
            return result
            
        except Exception as e:
            logger.warning(f"블로그 콘텐츠 파싱 실패: {e}")
            return {
                "title": "블로그 포스트",
                "outline": "",
                "body": content,
                "keywords": "",
                "full_content": content
            }
    
    async def generate_content_variations(self, original_content: Dict[str, Any], 
                                        variation_types: List[str]) -> Dict[str, Any]:
        """컨텐츠 변형 생성 - 새로운 기능"""
        try:
            variations = {}
            
            content_type = original_content.get("type", "")
            keyword = original_content.get("keyword", "")
            
            for variation_type in variation_types:
                if variation_type == "tone_friendly":
                    context = {"modification_request": "톤을 더 친근하게 만들어주세요"}
                elif variation_type == "tone_professional":
                    context = {"modification_request": "톤을 더 전문적으로 만들어주세요"}
                elif variation_type == "length_short":
                    context = {"modification_request": "길이를 짧게 만들어주세요"}
                elif variation_type == "length_long":
                    context = {"modification_request": "길이를 길게 만들어주세요"}
                else:
                    continue
                
                context["previous_content"] = original_content.get("full_content", "")
                
                if content_type == "instagram_post":
                    variation = await self.create_instagram_post_with_modifications(
                        keyword, context, context["modification_request"]
                    )
                elif content_type == "blog_post":
                    variation = await self.create_blog_post_with_modifications(
                        keyword, context, context["modification_request"]
                    )
                else:
                    continue
                
                variations[variation_type] = variation
            
            return {
                "success": True,
                "type": "content_variations",
                "original": original_content,
                "variations": variations,
                "generated_count": len(variations)
            }
            
        except Exception as e:
            logger.error(f"컨텐츠 변형 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "content_variations"
            }
    
    async def analyze_content_performance(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """컨텐츠 성과 예측 분석 - 새로운 기능"""
        try:
            content_text = content.get("full_content", "")
            content_type = content.get("type", "")
            
            prompt = f"""
다음 {content_type} 컨텐츠의 성과를 분석하고 개선점을 제안해주세요:

**컨텐츠:**
{content_text[:1000]}

**분석 항목:**
1. 타겟 어필도 (1-10점)
2. 가독성 (1-10점)
3. 참여 유도 효과 (1-10점)
4. SEO 최적화 (1-10점)
5. 브랜딩 효과 (1-10점)

**출력 형식:**
```
종합 점수: [점수]/10

강점:
- [강점1]
- [강점2]

개선점:
- [개선점1]
- [개선점2]

예상 성과:
- 도달률: [예측]
- 참여율: [예측]
- 전환율: [예측]

추천 개선 방향:
[구체적인 개선 제안]
```
"""
            
            analysis = await self.generate_content_with_llm(prompt)
            
            return {
                "success": True,
                "type": "performance_analysis",
                "content_analyzed": content_type,
                "analysis": analysis,
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"컨텐츠 성과 분석 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "performance_analysis"
            }
    
    # 기존 메서드들 유지...
    async def generate_marketing_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """마케팅 전략 생성"""
        try:
            business_type = context.get("business_type", "일반")
            main_goal = context.get("main_goal", "매출 증대")
            target_audience = context.get("target_audience", "일반 고객")
            budget = context.get("budget", "미정")
            channels = context.get("preferred_channel", "SNS")
            
            prompt = f"""
다음 정보를 바탕으로 종합적인 마케팅 전략을 수립해주세요.

**비즈니스 정보:**
- 업종: {business_type}
- 주요 목표: {main_goal}
- 타겟 고객: {target_audience}
- 예산: {budget}
- 선호 채널: {channels}

**출력 형식:**
```
마케팅 전략 요약:
[핵심 전략 요약]

1. 목표 설정:
[SMART 목표]

2. 타겟 분석:
[페르소나 및 고객 여정]

3. 채널 전략:
[채널별 활용 방안]

4. 콘텐츠 계획:
[콘텐츠 유형 및 일정]

5. 예산 배분:
[채널별 예산 분배]

6. 성과 측정:
[KPI 및 측정 방법]
```
"""
            
            content = await self.generate_content_with_llm(prompt, context)
            
            return {
                "success": True,
                "type": "marketing_strategy",
                "strategy": content,
                "business_type": business_type,
                "main_goal": main_goal
            }
            
        except Exception as e:
            logger.error(f"마케팅 전략 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "marketing_strategy"
            }
    
    async def create_campaign_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """캠페인 계획 생성"""
        try:
            business_type = context.get("business_type", "일반")
            main_goal = context.get("main_goal", "매출 증대")
            budget = context.get("budget", "미정")
            duration = context.get("duration", "1개월")
            
            prompt = f"""
다음 조건으로 마케팅 캠페인 계획을 수립해주세요.

**캠페인 정보:**
- 업종: {business_type}
- 목표: {main_goal}
- 예산: {budget}
- 기간: {duration}

**출력 형식:**
```
캠페인명: [캠페인 제목]

캠페인 목표:
[구체적인 목표]

타겟 오디언스:
[타겟 정의]

캠페인 전략:
[핵심 전략]

실행 계획:
주차별 실행 내용

예산 배분:
[항목별 예산]

성과 측정:
[KPI 및 목표 수치]
```
"""
            
            content = await self.generate_content_with_llm(prompt, context)
            
            return {
                "success": True,
                "type": "campaign_plan",
                "plan": content,
                "business_type": business_type
            }
            
        except Exception as e:
            logger.error(f"캠페인 계획 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "campaign_plan"
            }
    
    async def analyze_keywords(self, keyword: str) -> Dict[str, Any]:
        """키워드 분석 및 관련 키워드 추천"""
        try:
            prompt = f"""
'{keyword}'에 대한 마케팅 키워드 분석을 해주세요.

**분석 항목:**
1. 관련 키워드 10개 추천
2. 트렌드 예상 (상승/하락/유지)
3. 경쟁도 예상 (높음/중간/낮음)
4. 마케팅 활용 방안

**출력 형식:**
```
주요 키워드: {keyword}

관련 키워드:
1. [키워드1]
2. [키워드2]
...

트렌드 분석:
[트렌드 예상 및 근거]

경쟁도 분석:
[경쟁도 예상 및 근거]

마케팅 활용 방안:
[구체적인 활용 방법]
```
"""
            
            content = await self.generate_content_with_llm(prompt)
            
            return {
                "success": True,
                "type": "keyword_analysis", 
                "analysis": content,
                "keyword": keyword
            }
            
        except Exception as e:
            logger.error(f"키워드 분석 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "keyword_analysis"
            }
    
    async def generate_multiple_contents(self, content_types: List[str], keyword: str, 
                                       context: Dict[str, Any] = None) -> Dict[str, Any]:
        """여러 콘텐츠 동시 생성"""
        try:
            results = {}
            
            # 병렬 처리로 성능 향상
            tasks = []
            
            if "instagram" in content_types:
                tasks.append(("instagram", self.create_instagram_post(keyword, context)))
            
            if "blog" in content_types:
                tasks.append(("blog", self.create_blog_post(keyword, context)))
            
            if "strategy" in content_types:
                tasks.append(("strategy", self.generate_marketing_strategy(context or {})))
            
            if "keywords" in content_types:
                tasks.append(("keywords", self.analyze_keywords(keyword)))
            
            # 모든 작업 동시 실행
            completed_tasks = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
            
            # 결과 정리
            for i, (content_type, result) in enumerate(zip([task[0] for task in tasks], completed_tasks)):
                if isinstance(result, Exception):
                    results[content_type] = {
                        "success": False,
                        "error": str(result),
                        "type": content_type
                    }
                else:
                    results[content_type] = result
            
            return {
                "success": True,
                "results": results,
                "generated_types": list(results.keys()),
                "keyword": keyword
            }
            
        except Exception as e:
            logger.error(f"다중 콘텐츠 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "multiple_contents"
            }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록 (개선된 버전)"""
        return [
            {
                "name": "instagram_post",
                "description": "인스타그램 포스트 생성",
                "input": "키워드, 컨텍스트",
                "output": "캡션, 해시태그, CTA",
                "features": ["기본 생성", "수정 지원", "멀티턴 대화"]
            },
            {
                "name": "instagram_post_with_modifications",
                "description": "인스타그램 포스트 수정",
                "input": "키워드, 컨텍스트, 수정 요청",
                "output": "수정된 캡션, 해시태그, CTA",
                "features": ["NEW - 실시간 수정", "톤앤매너 조정", "길이 조절"]
            },
            {
                "name": "blog_post", 
                "description": "블로그 포스트 작성",
                "input": "키워드, 컨텍스트",
                "output": "제목, 본문, SEO 키워드",
                "features": ["기본 생성", "수정 지원"]
            },
            {
                "name": "blog_post_with_modifications",
                "description": "블로그 포스트 수정",
                "input": "키워드, 컨텍스트, 수정 요청",
                "output": "수정된 블로그 포스트",
                "features": ["NEW - 실시간 수정", "구조 조정", "내용 개선"]
            },
            {
                "name": "content_variations",
                "description": "컨텐츠 변형 생성",
                "input": "원본 컨텐츠, 변형 유형",
                "output": "다양한 스타일의 변형 컨텐츠",
                "features": ["NEW - 다중 변형", "A/B 테스트 지원"]
            },
            {
                "name": "performance_analysis",
                "description": "컨텐츠 성과 예측 분석",
                "input": "컨텐츠",
                "output": "성과 분석, 개선점",
                "features": ["NEW - 성과 예측", "개선 제안"]
            },
            {
                "name": "marketing_strategy",
                "description": "종합 마케팅 전략 수립",
                "input": "비즈니스 정보",
                "output": "전략, 채널별 계획",
                "features": ["전략 수립", "실행 계획"]
            },
            {
                "name": "keyword_analysis",
                "description": "키워드 분석 및 추천",
                "input": "키워드",
                "output": "관련 키워드, 트렌드 분석",
                "features": ["키워드 확장", "트렌드 분석"]
            },
            {
                "name": "campaign_plan",
                "description": "캠페인 계획 수립",
                "input": "캠페인 정보",
                "output": "실행 계획, 예산 배분",
                "features": ["캠페인 기획", "예산 계획"]
            },
            {
                "name": "multiple_contents",
                "description": "여러 콘텐츠 동시 생성",
                "input": "콘텐츠 유형 목록",
                "output": "각 콘텐츠 결과",
                "features": ["병렬 생성", "효율성"]
            }
        ]
