"""
마케팅 에이전트 - 개선된 버전
✅ 개선 사항 반영: 중복 최소화, 진행형 대화, 맞춤화, 피로도 관리, 실행 가능성 강화
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import asyncio

from conversation_manager import ConversationManager, MarketingStage, ConversationMode
from general_marketing_tools import MarketingTools
from mcp_marketing_tools import MarketingAnalysisTools
from config import config, create_response

logger = logging.getLogger(__name__)

class MarketingAgent:
    """🆕 개선된 마케팅 에이전트 - 사용자 중심 대화, 실행력 강화"""
    
    def __init__(self):
        """에이전트 초기화"""
        self.conversation_manager = ConversationManager()
        self.general_marketing_tools = MarketingTools()
        self.mcp_marketing_tools = MarketingAnalysisTools()
        self.version = config.VERSION
        
        from config import config as cfg
        self.client = self.conversation_manager.client
        self.model = cfg.OPENAI_MODEL
        self.temperature = cfg.TEMPERATURE
        
        logger.info(f"🆕 개선된 마케팅 에이전트 초기화 완료 (v{self.version})")
    
    async def _generate_enhanced_response(self, prompt: str, context: str = "") -> str:
        """개선된 LLM 응답 생성 - 맞춤화 및 실행력 강화"""
        try:
            full_prompt = f"{prompt}\n\n컨텍스트: {context}" if context else prompt
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": """당신은 친근하고 전문적인 마케팅 컨설턴트입니다. 
                    
### 응답 원칙:
1. **맞춤화**: 사용자의 업종, 제품, 상황에 맞는 구체적 조언
2. **실행력**: 바로 적용 가능한 구체적 방법 제시
3. **진행형 대화**: 이전 내용을 반복하지 않고 다음 단계로 발전
4. **질문 배치**: 후속 질문은 마지막 문단에만, 자연스럽게 연결
5. **밀도 높은 정보**: 핵심만 간결하게, 불필요한 개행 최소화
6. **친근한 톤**: 전문성과 친근함의 균형

### 응답 구조:
- **인사/공감** (간단히)
- **핵심 조언** (실행 가능한 방법)
- **구체적 예시** (사용자 상황 반영)
- **다음 단계 제안** (자연스럽게)
- **후속 질문** (마지막에 1-2개만)"""},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=self.temperature,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"LLM 응답 생성 실패: {e}")
            return "죄송합니다. 응답 생성 중 문제가 발생했습니다. 다시 시도해주세요."

    async def process_message(self, user_input: str, user_id: int, 
                    conversation_id: Optional[int] = None) -> Dict[str, Any]:
        """🆕 개선된 메시지 처리 - 단계별 맞춤 대화, 피로도 관리"""
        start_time = datetime.now()
        
        try:
            logger.info(f"메시지 처리 시작 - user_id: {user_id}, input: {user_input[:50]}...")
            
            # 1. 대화 상태 관리
            conversation, is_new = self.conversation_manager.get_or_create_conversation(user_id, conversation_id)
            conversation_id = conversation.conversation_id
            
            # 2. 컨텐츠 제작 세션 중인지 확인
            tool_results = None
            if conversation.is_in_content_creation():
                response_text = await self._handle_content_session(user_input, conversation)
                
                # 컨텐츠 생성 시그널 처리
                if response_text.startswith("TRIGGER_"):
                    trigger_parts = response_text.split(":", 1)
                    if len(trigger_parts) == 2:
                        trigger_type, display_text = trigger_parts
                        response_text = display_text
                        
                        # 자동화 작업 생성 처리
                        if trigger_type == "TRIGGER_AUTOMATION_TASK":
                            automation_result = await self._handle_automation_task_creation(display_text, conversation)
                            if automation_result.get("success"):
                                response_text = automation_result["message"]
                            else:
                                error_context = f"자동화 예약 실패: {automation_result.get('error', '알 수 없는 오류')}"
                                response_text = await self._generate_enhanced_response(
                                    "자동화 예약이 실패했을 때 사용자에게 친근하게 사과하고 다시 시도를 안내하는 메시지를 생성해주세요.",
                                    error_context
                                )
                        
                        # 실제 컨텐츠 생성 수행
                        elif trigger_type in ["TRIGGER_CONTENT_GENERATION", "TRIGGER_CONTENT_MODIFICATION", "TRIGGER_CONTENT_REGENERATION"]:
                            content_result = await self._handle_content_generation_with_context(user_input, conversation)
                            if content_result and content_result.get("success"):
                                tool_results = content_result
                                formatted_content = await self._format_tool_results(content_result)
                                response_text += f"\n\n{formatted_content}"
                                
                                conversation.update_content_session(formatted_content, user_input)
                                conversation.current_content_for_posting = content_result
                            else:
                                error_message = await self._generate_enhanced_response(
                                    "컨텐츠 생성 중 오류가 발생했을 때 친근하게 사과하고 다시 시도를 안내하는 메시지를 생성해주세요."
                                )
                                response_text += f"\n\n{error_message}"
            else:
                # 3. 일반 대화 처리 (개선된 응답 분석)
                response_text = await self.conversation_manager.generate_progressive_response(user_input, conversation)
                
                # 컨텐츠 생성 시그널 확인
                if response_text.startswith("TRIGGER_CONTENT_GENERATION"):
                    response_text = ""
                    content_result = await self._handle_content_generation_with_context(user_input, conversation)
                    if content_result and content_result.get("success"):
                        tool_results = content_result
                        formatted_content = await self._format_tool_results(content_result)
                        response_text += f"\n\n{formatted_content}"
                        
                        conversation.update_content_session(formatted_content, user_input)
                        conversation.current_content_for_posting = content_result
                    else:
                        error_message = await self._generate_enhanced_response(
                            "컨텐츠 생성 중 오류가 발생했을 때 친근하게 사과하고 다시 시도를 안내하는 메시지를 생성해주세요."
                        )
                        response_text += f"\n\n{error_message}"
            
            # 4. 성능 정보
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 5. 응답 생성
            response_data = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "answer": response_text,
                "current_stage": conversation.current_stage.value,
                "current_mode": conversation.current_mode.value,
                "completion_rate": conversation.get_completion_rate(),
                "collected_info": dict(conversation.collected_info),
                "tool_results": tool_results,
                "processing_time": processing_time,
                "is_new_conversation": is_new,
                "in_content_creation": conversation.is_in_content_creation(),
                "content_session": conversation.current_content_session,
                "user_engagement_level": conversation.user_engagement_level,
                "conversation_progress": conversation.get_conversation_progress(),
                "features": [
                    "progressive_conversation", 
                    "fatigue_management", 
                    "contextual_customization", 
                    "execution_focused",
                    "density_optimized"
                ]
            }
            
            return create_response(success=True, data=response_data)
            
        except Exception as e:
            logger.error(f"메시지 처리 실패: {e}")
            
            error_message = await self._generate_enhanced_response(
                f"마케팅 상담 중 기술적 문제가 발생했을 때 사용자에게 친근하게 사과하고 도움을 계속 제공하겠다는 메시지를 생성해주세요.",
                f"발생한 오류: {str(e)}"
            )
            
            return create_response(
                success=False,
                error=error_message,
                data={
                    "suggested_actions": [
                        "마케팅 상담 다시 시작하기",
                        "기본 마케팅 전략 상담받기"
                    ],
                    "has_follow_up_questions": True
                }
            )
   
    async def _handle_content_session(self, user_input: str, conversation, is_initial: bool = False) -> str:
        """컨텐츠 제작 세션 처리 - 멀티턴 대화 지원"""
        try:
            response_text = await self.conversation_manager._handle_content_creation_session(
                user_input, conversation, is_initial
            )
            
            if response_text.startswith("TRIGGER_"):
                return response_text
            
            return response_text
            
        except Exception as e:
            logger.error(f"컨텐츠 세션 처리 실패: {e}")
            return await self._generate_enhanced_response(
                "컨텐츠 제작 중 오류가 발생했을 때 친근하게 사과하고 다시 시도를 안내하는 메시지를 생성해주세요.",
                f"오류 내용: {str(e)}"
            )
    
    async def _handle_automation_task_creation(self, display_text: str, conversation) -> Dict[str, Any]:
        """자동화 작업 생성 처리"""
        try:
            if "|" in display_text:
                scheduled_at_str, message = display_text.split("|", 1)
            else:
                return {"success": False, "error": "스케줄 시간 정보가 없습니다."}
            
            try:
                from datetime import datetime
                scheduled_at = datetime.fromisoformat(scheduled_at_str)
            except ValueError:
                return {"success": False, "error": f"잘못된 날짜 형식: {scheduled_at_str}"}
            
            try:
                from shared_modules.database import SessionLocal
                from shared_modules.queries import create_automation_task
                
                with SessionLocal() as db:
                    content_data = conversation.current_content_for_posting or {}
                    task_data = {
                        "content_type": content_data.get("type", "general"),
                        "content": content_data.get("full_content", ""),
                        "platform": "social_media",
                        "user_id": conversation.user_id,
                        "conversation_id": conversation.conversation_id
                    }
                    
                    automation_task = create_automation_task(
                        db=db,
                        user_id=conversation.user_id,
                        task_type="social_posting",
                        title=f"마케팅 컨텐츠 자동 포스팅",
                        template_id=None,
                        task_data=task_data,
                        conversation_id=conversation.conversation_id,
                        scheduled_at=scheduled_at
                    )
                    
                    if automation_task:
                        conversation.complete_posting_process()
                        conversation.end_content_session()
                        conversation.current_stage = MarketingStage.COMPLETED
                        
                        success_message = await self._generate_enhanced_response(
                            f"자동화 예약이 성공적으로 완료되었을 때 사용자에게 기쁘게 알리는 메시지를 생성해주세요.",
                            f"예약 시간: {scheduled_at.strftime('%Y년 %m월 %d일 %H:%M')}, 작업 ID: {automation_task.task_id}"
                        )
                        
                        return {
                            "success": True,
                            "message": success_message,
                            "task_id": automation_task.task_id,
                            "scheduled_at": scheduled_at.isoformat()
                        }
                    else:
                        return {"success": False, "error": "데이터베이스에 작업 저장 실패"}
                        
            except Exception as db_error:
                logger.error(f"데이터베이스 오류: {db_error}")
                return {"success": False, "error": f"데이터베이스 오류: {str(db_error)}"}
                
        except Exception as e:
            logger.error(f"자동화 작업 생성 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_content_generation_with_context(self, user_input: str, conversation) -> Optional[Dict[str, Any]]:
        """🆕 컨텍스트 기반 개선된 콘텐츠 생성 처리"""
        try:
            # 컨텍스트 정보 준비 (더 풍부한 정보 활용)
            context = self._prepare_enhanced_context(conversation)
            
            # 필수 정보 체크 (완화된 조건)
            missing_info = await self._check_essential_info(context)
            if missing_info:
                return {
                    "success": False,
                    "error": missing_info,
                    "type": "missing_essential_info"
                }
            
            # 사용자 선택 및 의도 분석 (개선된 분석)
            content_analysis = await self._analyze_content_request_with_context(user_input, context)
            tool_type = content_analysis.get("tool_type", "content_generation")
            content_type = content_analysis.get("content_type", "instagram")
            
            # 타겟 키워드 추출 (컨텍스트 기반)
            target_keywords = await self._extract_contextual_keywords(user_input, conversation)
            
            # 툴 타입별 실행 (개선된 버전)
            if tool_type == "trend_analysis":
                result = await self.general_marketing_tools.analyze_naver_trends(target_keywords)
                
            elif tool_type == "hashtag_analysis":
                result = await self.general_marketing_tools.analyze_instagram_hashtags(
                    question=user_input,
                    user_hashtags=target_keywords
                )
                
            elif tool_type == "content_generation":
                if content_type == "blog":
                    result = await self.general_marketing_tools.create_blog_post(target_keywords, context)
                elif content_type == "instagram":
                    result = await self.general_marketing_tools.create_instagram_post(target_keywords, context)
                elif content_type == "strategy":
                    result = await self.general_marketing_tools.create_strategy_content(context)
                elif content_type == "campaign":
                    result = await self.general_marketing_tools.create_campaign_content(context)
                else:
                    result = await self.general_marketing_tools.create_instagram_post(target_keywords, context)
                    
            elif tool_type == "keyword_research":
                trend_result = await self.mcp_marketing_tools.analyze_naver_trends(target_keywords)
                result = {
                    "success": True,
                    "keywords": target_keywords,
                    "trend_data": trend_result
                }
                
            else:
                return {
                    "success": False,
                    "error": f"지원하지 않는 툴 타입: {tool_type}",
                    "tool_type": tool_type
                }
            
            return result
                
        except Exception as e:
            logger.error(f"콘텐츠 생성 처리 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "content_generation"
            }
    
    async def _analyze_content_request_with_context(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """🆕 컨텍스트 기반 콘텐츠 요청 분석"""
        try:
            user_job = context.get('business_type') or context.get('job')
            product_info = context.get('product') or context.get('service')
            
            analysis_prompt = f"""사용자의 콘텐츠 요청을 분석하여 최적의 마케팅 도구와 콘텐츠 유형을 추천해주세요.

사용자 요청: "{user_input}"
업종: {user_job}
제품/서비스: {product_info}
마케팅 목표: {context.get('main_goal', '매출 증대')}
타겟 고객: {context.get('target_audience', '일반 고객')}

다음 JSON 형식으로 답변해주세요:
{{
    "tool_type": "가장 적합한 하나의 도구만 선택 (trend_analysis, hashtag_analysis, content_generation, keyword_research 중 1개)",
    "content_type": "가장 적합한 하나의 콘텐츠 유형만 선택 (instagram, blog, strategy, campaign 중 1개)",
    "confidence": 0.8,
    "reasoning": "선택 이유"
}}

**중요**: tool_type과 content_type은 각각 하나의 값만 선택해야 합니다. 여러 개를 선택하지 마세요.

선택 기준:
- 업종과 제품에 최적화된 마케팅 방법
- 사용자 요청의 명확성과 의도
- 현재 수집된 정보의 충분성
- 실행 가능성과 효과성

예시 응답:
{{
    "tool_type": "content_generation",
    "content_type": "instagram",
    "confidence": 0.9,
    "reasoning": "사용자가 인스타그램 콘텐츠 제작을 요청했고, 제품 특성상 시각적 콘텐츠가 효과적이기 때문"
}}"""
            
            content = await self.general_marketing_tools.generate_content_with_llm(analysis_prompt)
            
            # JSON 파싱 시도
            try:
                import json
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                elif "{" in content and "}" in content:
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    json_content = content[json_start:json_end]
                else:
                    raise ValueError("JSON 형식을 찾을 수 없음")
                
                parsed_result = json.loads(json_content)
                return parsed_result
                
            except (json.JSONDecodeError, ValueError):
                # 파싱 실패 시 기본값 반환
                content_lower = content.lower()
                
                if any(word in content_lower for word in ["트렌드", "검색량", "분석"]):
                    return {"tool_type": "trend_analysis", "content_type": "instagram"}
                elif any(word in content_lower for word in ["해시태그", "sns"]):
                    return {"tool_type": "hashtag_analysis", "content_type": "instagram"}
                elif any(word in content_lower for word in ["블로그", "blog"]):
                    return {"tool_type": "content_generation", "content_type": "blog"}
                elif any(word in content_lower for word in ["전략", "strategy"]):
                    return {"tool_type": "content_generation", "content_type": "strategy"}
                else:
                    return {"tool_type": "content_generation", "content_type": "instagram"}
                
        except Exception as e:
            logger.warning(f"콘텐츠 타입 분석 실패: {e}")
            return {"tool_type": "content_generation", "content_type": "instagram"}
    
    async def _extract_contextual_keywords(self, user_input: str, conversation) -> List[str]:
        """🆕 컨텍스트 기반 키워드 추출 (더 정교한 분석)"""
        try:
            context = self._prepare_enhanced_context(conversation)
            product_info = context.get('product') or context.get('service')
            business_type = context.get('business_type')
            target_audience = context.get('target_audience')
            
            keyword_prompt = f"""다음 정보를 종합하여 마케팅에 효과적인 핵심 키워드 10개를 추출해주세요.

사용자 요청: "{user_input}"
업종: {business_type}
제품/서비스: {product_info}
타겟 고객: {target_audience}
마케팅 목표: {context.get('main_goal')}

키워드 추출 조건:
1. 검색량이 높을 것으로 예상되는 키워드
2. 타겟 고객이 사용할 법한 용어
3. 제품/서비스와 직접 연관된 키워드
4. 트렌드성이 있는 키워드
5. 롱테일 키워드도 포함

각 줄에 하나씩 키워드만 출력하세요. 설명이나 번호는 제외하고 키워드만 작성하세요."""

            content = await self.general_marketing_tools.generate_content_with_llm(keyword_prompt)
            
            keywords = [kw.strip() for kw in content.splitlines() if kw.strip() and not kw.strip().isdigit()]
            return keywords[:10] if keywords else [product_info or business_type or "마케팅"]

        except Exception as e:
            logger.warning(f"키워드 추출 실패: {e}")
            context = self._prepare_enhanced_context(conversation)
            fallback_keyword = (context.get('product') or 
                               context.get('business_type') or 
                               "마케팅")
            return [fallback_keyword]
    
    async def _check_essential_info(self, context: Dict[str, Any]) -> Optional[str]:
        """🆕 필수 정보 체크 (완화된 조건)"""
        missing_items = []
        
        # 업종 정보 (완화: 기본값도 허용)
        user_job = context.get("business_type") or context.get("job")
        if not user_job:
            missing_items.append("업종")
        
        # 제품 정보 (완화: 서비스나 목표로도 대체 가능)
        product_info = (context.get("product") or context.get("service") or 
                       context.get("main_goal") or context.get("target_audience"))
        if not product_info:
            missing_items.append("제품/서비스 또는 마케팅 목표")
        
        # 둘 다 없으면 최소 정보 요청
        if len(missing_items) >= 2:
            missing_info_message = await self._generate_enhanced_response(
                f"효과적인 컨텐츠 생성을 위해 다음 정보가 필요하다는 것을 친근하게 안내하는 메시지를 생성해주세요: {', '.join(missing_items)}"
            )
            return missing_info_message
        
        return None
    
    def _prepare_enhanced_context(self, conversation) -> Dict[str, Any]:
        """🆕 향상된 컨텍스트 준비 (더 풍부한 정보)"""
        context = {}
        
        # 수집된 정보에서 값 추출
        for key, info in conversation.collected_info.items():
            context[key] = info["value"]
        
        # 기본 값 및 추론 정보 설정
        context.setdefault("business_type", conversation.business_type)
        context.setdefault("current_stage", conversation.current_stage.value)
        context.setdefault("user_engagement", conversation.user_engagement_level)
        context.setdefault("completion_rate", conversation.get_completion_rate())
        
        # 컨텍스트 기반 추론 정보 추가
        if context.get("business_type") == "뷰티":
            context.setdefault("target_audience", "20-30대 여성")
            context.setdefault("preferred_channel", "인스타그램, 틱톡")
        elif context.get("business_type") == "음식점":
            context.setdefault("target_audience", "지역 주민")
            context.setdefault("preferred_channel", "네이버 지도, 인스타그램")
        
        return context
    
    async def _format_tool_results(self, tool_results: Dict[str, Any]) -> str:
        """🆕 개선된 도구 결과 포맷팅 - 실행 중심, 밀도 높은 정보"""
        if not tool_results.get("success"):
            error_type = tool_results.get("type", "general_error")
            
            if error_type == "missing_essential_info":
                return tool_results.get("error", "필수 정보가 부족합니다.")
            else:
                error_message = await self._generate_enhanced_response(
                    "컨텐츠 생성 중 오류가 발생했을 때 친근하게 사과하고 다시 시도를 안내하는 메시지를 생성해주세요.",
                    f"오류 내용: {tool_results.get('error', '알 수 없는 오류')}"
                )
                return error_message
        
        # 키워드 리서치 결과 포맷팅
        if 'keywords' in tool_results and 'trend_data' in tool_results:
            return await self._format_keyword_research_result(tool_results)
        
        content_type = tool_results.get("type", "content")
        
        if content_type == "instagram_post":
            return await self._format_instagram_result(tool_results)
        elif content_type == "blog_post":
            return await self._format_blog_result(tool_results)
        elif content_type == "marketing_strategy":
            strategy_message = await self._generate_enhanced_response(
                "마케팅 전략이 완성되었다는 것을 밝은톤으로 알리고 핵심 포인트를 강조하는 메시지를 생성해주세요.",
                f"전략 내용: {tool_results.get('strategy', '')}"
            )
            return strategy_message
        else:
            content_message = await self._generate_enhanced_response(
                f"{content_type} 생성이 완료되었다는 것을 밝은톤으로 알리고 바로 활용할 수 있는 방법을 제안하는 메시지를 생성해주세요.",
                f"생성된 내용: {tool_results.get('full_content', str(tool_results))}"
            )
            return content_message
    
    async def _format_instagram_result(self, result: Dict[str, Any]) -> str:
        """인스타그램 결과 포맷팅 - 실행 중심"""
        instagram_context = f"""
        캡션: {result.get('caption', '')}
        해시태그: {result.get('hashtags', '')}
        CTA: {result.get('cta', '')}
        """
        
        formatted_message = await self._generate_enhanced_response(
            "인스타그램 포스트가 완성되었다는 것을 밝은톤으로 알리고, 바로 사용할 수 있도록 캡션, 해시태그, CTA를 깔끔하게 정리해서 보여주는 메시지를 생성해주세요. 포스팅 팁도 간단히 포함해주세요.",
            instagram_context
        )
        return formatted_message
    
    async def _format_blog_result(self, result: Dict[str, Any]) -> str:
        """블로그 결과 포맷팅 - 실행 중심"""
        blog_context = f"""
        제목: {result.get('title', '')}
        목차: {result.get('outline', '')}
        본문 미리보기: {result.get('body', '')[:300]}{'...' if len(result.get('body', '')) > 300 else ''}
        SEO 키워드: {result.get('keywords', '')}
        """
        
        formatted_message = await self._generate_enhanced_response(
            "블로그 포스트가 완성되었다는 것을 밝은톤으로 알리고, 제목, 목차, SEO 키워드를 중심으로 정리해서 보여주는 메시지를 생성해주세요. 블로그 활용 팁도 간단히 포함해주세요.",
            blog_context
        )
        return formatted_message
    
    async def _format_keyword_research_result(self, result: Dict[str, Any]) -> str:
        """키워드 리서치 결과 포맷팅 - 실행 중심"""
        keyword_context = f"""
        추천 키워드: {result.get('keywords', [])}
        트렌드 데이터: {result.get('trend_data', {})}
        """
        
        formatted_message = await self._generate_enhanced_response(
            "키워드 분석이 완료되었다는 것을 밝은톤으로 알리고, 추천 키워드를 활용 우선순위 순으로 정리해서 보여주는 메시지를 생성해주세요. 키워드 활용 방법도 간단히 포함해주세요.",
            keyword_context
        )
        return formatted_message
    
    def get_conversation_status(self, conversation_id: int) -> Dict[str, Any]:
        """대화 상태 조회"""
        return self.conversation_manager.get_conversation_summary(conversation_id)
    
    def get_agent_status(self) -> Dict[str, Any]:
        """에이전트 상태 조회"""
        cleaned_count = self.conversation_manager.cleanup_expired_conversations()
        
        return {
            "version": self.version,
            "service_name": config.SERVICE_NAME,
            "status": "healthy",
            "intelligence_type": "enhanced_contextual",
            "active_conversations": len(self.conversation_manager.conversations),
            "cleaned_conversations": cleaned_count,
            "available_tools": len(self.general_marketing_tools.get_available_tools()),
            "enhanced_capabilities": [
                "진행형 대화 구조",
                "사용자 피로도 관리",
                "맞춤형 컨텍스트 분석",
                "실행 중심 조언",
                "밀도 높은 정보 제공",
                "자연스러운 후속 질문",
                "단계별 맞춤 대화"
            ],
            "features": [
                "progressive_conversation_flow",
                "fatigue_aware_interaction", 
                "contextual_personalization",
                "execution_focused_advice",
                "density_optimized_content",
                "natural_follow_up_questions",
                "stage_aware_customization"
            ],
            "conversation_improvements": {
                "duplicate_minimization": "이전 조언 반복 방지, 다음 단계로 발전",
                "question_placement": "후속 질문을 마지막 문단에 자연스럽게 배치",
                "user_customization": "업종, 제품, 상황별 맞춤 조언",
                "stage_management": "단계별 진행 상황 추적 및 맞춤 대화",
                "content_density": "핵심 정보 위주, 불필요한 개행 최소화",
                "execution_focus": "바로 적용 가능한 구체적 방법 제시",
                "tone_consistency": "친근하면서 전문적인 일관된 톤",
                "context_maintenance": "이전 대화 맥락 유지 및 활용"
            }
        }
    
    async def reset_conversation(self, conversation_id: int) -> bool:
        """대화 초기화"""
        if conversation_id in self.conversation_manager.conversations:
            del self.conversation_manager.conversations[conversation_id]
            logger.info(f"대화 초기화 완료: {conversation_id}")
            return True
        return False
    
    async def batch_process(self, messages: list) -> Dict[str, Any]:
        """배치 메시지 처리"""
        try:
            results = []
            
            for message_data in messages:
                result = await self.process_message(
                    user_input=message_data.get("message", ""),
                    user_id=message_data.get("user_id", 0),
                    conversation_id=message_data.get("conversation_id")
                )
                results.append(result)
                
                await asyncio.sleep(0.1)
            
            return create_response(
                success=True,
                data={
                    "batch_results": results,
                    "processed_count": len(results),
                    "success_count": len([r for r in results if r.get("success")])
                }
            )
            
        except Exception as e:
            logger.error(f"배치 처리 실패: {e}")
            
            error_message = await self._generate_enhanced_response(
                "배치 메시지 처리 중 오류가 발생했을 때 사용자에게 친근하게 사과하고 개별 메시지로 다시 시도를 안내하는 메시지를 생성해주세요.",
                f"오류 내용: {str(e)}"
            )
            
            return create_response(
                success=False,
                error=error_message
            )
