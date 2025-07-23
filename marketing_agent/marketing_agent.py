"""
마케팅 에이전트 - 완전 LLM 기반 버전
단순하고 효율적인 멀티턴 대화 기반 마케팅 상담
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio

from conversation_manager import ConversationManager, MarketingStage
from marketing_tools import MarketingTools
from config import config, create_response

logger = logging.getLogger(__name__)

class MarketingAgent:
    """완전 LLM 기반 통합 마케팅 에이전트 - 멀티턴 대화 + 도구 활용"""
    
    def __init__(self):
        """에이전트 초기화"""
        self.conversation_manager = ConversationManager()
        self.marketing_tools = MarketingTools()
        self.version = config.VERSION
        
        logger.info(f"LLM 기반 마케팅 에이전트 초기화 완료 (v{self.version})")
    
    async def process_message(self, user_input: str, user_id: int, 
                         conversation_id: Optional[int] = None) -> Dict[str, Any]:
        """메인 메시지 처리 함수 - 완전 LLM 기반"""
        start_time = datetime.now()
        
        try:
            logger.info(f"LLM 기반 메시지 처리 시작 - user_id: {user_id}, input: {user_input[:50]}...")
            
            # 1. 대화 상태 관리
            conversation, is_new = self.conversation_manager.get_or_create_conversation(user_id, conversation_id)
            conversation_id = conversation.conversation_id
            
            # 2. LLM 기반 맥락적 응답 생성 및 intent 분석
            response_text = await self.conversation_manager.generate_response_with_context(user_input, conversation)
            
            # intent_analysis 결과에서 콘텐츠 생성 요청 감지
            latest_intent = None
            if conversation.conversation_history:
                last_msg = conversation.conversation_history[-1]
                if "intent_analysis" in last_msg.get("metadata", {}):
                    latest_intent = last_msg["metadata"]["intent_analysis"]

            trigger_from_intent = latest_intent.get("trigger_content_generation", False) if latest_intent else False

            # 3. 콘텐츠 생성 요청 검사 (LLM intent OR 키워드 기반)
            tool_results = None
            # if trigger_from_intent or await self._should_generate_content_with_llm(user_input, conversation):
            if trigger_from_intent:
                logger.info(f"콘텐츠 생성 조건 충족: trigger_from_intent={trigger_from_intent}")
                tool_results = await self._handle_content_generation_with_llm(user_input, conversation)
                if tool_results and tool_results.get("success"):
                    response_text += f"\n\n{self._format_tool_results(tool_results)}"
            
            # 4. 성능 정보
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 5. 응답 생성
            return create_response(
                success=True,
                data={
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "answer": response_text,
                    "current_stage": conversation.current_stage.value,
                    "completion_rate": conversation.get_completion_rate(),
                    "collected_info": dict(conversation.collected_info),
                    "tool_results": tool_results,
                    "processing_time": processing_time,
                    "is_new_conversation": is_new,
                    "llm_powered": True
                }
            )
            
        except Exception as e:
            logger.error(f"메시지 처리 실패: {e}")
            return create_response(
                success=False,
                error=f"메시지 처리 중 오류가 발생했습니다: {str(e)}"
            )

    
    def _is_greeting(self, user_input: str) -> bool:
        """인사말 확인"""
        greetings = ["안녕", "hello", "hi", "처음", "시작", "상담"]
        return any(greeting in user_input.lower() for greeting in greetings)
    
    async def _should_generate_content_with_llm(self, user_input: str, conversation) -> bool:
        """LLM 기반 콘텐츠 생성 필요성 판단"""
        
        # 명시적인 콘텐츠 생성 키워드
        content_keywords = [
            "만들어", "생성", "작성", "콘텐츠", "포스트", "글", "캠페인",
            "전략 세워", "계획 세워", "인스타그램", "블로그"
        ]
        
        has_content_request = any(keyword in user_input for keyword in content_keywords)
        has_enough_info = conversation.get_completion_rate() > 0.2
        is_execution_stage = conversation.current_stage in [MarketingStage.EXECUTION, MarketingStage.COMPLETED]
        
        # 실행 단계이거나 충분한 정보가 있으면서 콘텐츠 요청이 있는 경우
        return (is_execution_stage and has_content_request) or (has_content_request and has_enough_info)
    
    async def _handle_content_generation_with_llm(self, user_input: str, conversation) -> Optional[Dict[str, Any]]:
        """LLM 기반 콘텐츠 생성 처리"""
        try:
            # 컨텍스트 정보 준비
            context = self._prepare_context_for_tools(conversation)
            
            # LLM을 통한 콘텐츠 유형 분석
            content_type = await self._analyze_content_type_with_llm(user_input, context)
            
            if content_type == "instagram":
                keyword = await self._extract_keyword_with_llm(user_input, conversation)
                return await self.marketing_tools.create_instagram_post(keyword, context)
                
            elif content_type == "blog":
                keyword = await self._extract_keyword_with_llm(user_input, conversation)
                return await self.marketing_tools.create_blog_post(keyword, context)
                
            elif content_type == "strategy":
                return await self.marketing_tools.generate_marketing_strategy(context)
                
            elif content_type == "campaign":
                return await self.marketing_tools.create_campaign_plan(context)
                
            elif content_type == "multiple":
                keyword = await self._extract_keyword_with_llm(user_input, conversation)
                content_types = ["instagram", "blog", "strategy"]
                return await self.marketing_tools.generate_multiple_contents(content_types, keyword, context)
            
            else:
                # 기본적으로 전략 생성
                return await self.marketing_tools.generate_marketing_strategy(context)
                
        except Exception as e:
            logger.error(f"콘텐츠 생성 처리 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "content_generation"
            }
    
    async def _analyze_content_type_with_llm(self, user_input: str, context: Dict[str, Any]) -> str:
        """LLM 기반 콘텐츠 유형 분석"""
        try:
            analysis_prompt = f"""다음 사용자 요청을 분석하여 어떤 종류의 마케팅 콘텐츠를 원하는지 판단해주세요.

사용자 요청: "{user_input}"
비즈니스 컨텍스트: {context.get('business_type', '일반')}

다음 중 하나로 분류해주세요:
- instagram: 인스타그램 포스트, SNS 콘텐츠
- blog: 블로그 포스트, 긴 글 콘텐츠
- strategy: 마케팅 전략, 전반적 계획
- campaign: 캠페인, 이벤트 기획
- multiple: 여러 콘텐츠 동시 생성

단답으로 답변해주세요."""
            
            content = await self.marketing_tools.generate_content_with_llm(analysis_prompt)
            
            # 응답에서 콘텐츠 타입 추출
            content_lower = content.lower()
            if "instagram" in content_lower:
                return "instagram"
            elif "blog" in content_lower:
                return "blog"
            elif "strategy" in content_lower:
                return "strategy"
            elif "campaign" in content_lower:
                return "campaign"
            elif "multiple" in content_lower:
                return "multiple"
            else:
                return "strategy"  # 기본값
                
        except Exception as e:
            logger.warning(f"콘텐츠 타입 분석 실패: {e}")
            return "strategy"
    
    async def _extract_keyword_with_llm(self, user_input: str, conversation) -> str:
        """LLM 기반 키워드 추출"""
        try:
            keyword_prompt = f"""다음 맥락에서 마케팅 콘텐츠 생성에 사용할 핵심 키워드를 추출해주세요.

사용자 요청: "{user_input}"
업종: {conversation.business_type}
수집된 정보: {conversation.collected_info}

하나의 핵심 키워드만 추출해서 단답으로 답변해주세요."""
            
            content = await self.marketing_tools.generate_content_with_llm(keyword_prompt)
            
            # 첫 번째 단어 추출
            extracted = content.strip().split()[0] if content.strip() else "마케팅"
            
            return extracted
            
        except Exception as e:
            logger.warning(f"키워드 추출 실패: {e}")
            # 폴백: 업종 또는 기본값 사용
            return conversation.business_type if conversation.business_type != "일반" else "마케팅"
    
    def _prepare_context_for_tools(self, conversation) -> Dict[str, Any]:
        """도구용 컨텍스트 준비"""
        context = {}
        
        # 수집된 정보에서 값 추출
        for key, info in conversation.collected_info.items():
            context[key] = info["value"]
        
        # 기본 값 설정
        context.setdefault("business_type", conversation.business_type)
        context.setdefault("current_stage", conversation.current_stage.value)
        
        return context
    
    def _format_tool_results(self, tool_results: Dict[str, Any]) -> str:
        """도구 결과 포맷팅"""
        if not tool_results.get("success"):
            return f"❌ 콘텐츠 생성 중 오류가 발생했습니다: {tool_results.get('error', '알 수 없는 오류')}"
        
        content_type = tool_results.get("type", "content")
        
        if content_type == "instagram_post":
            return self._format_instagram_result(tool_results)
        elif content_type == "blog_post":
            return self._format_blog_result(tool_results)
        elif content_type == "marketing_strategy":
            return f"📊 **마케팅 전략이 완성되었습니다!**\n\n{tool_results.get('strategy', '')}"
        elif content_type == "multiple_contents":
            return self._format_multiple_results(tool_results)
        else:
            return f"✅ **{content_type} 생성 완료!**\n\n{tool_results.get('full_content', str(tool_results))}"
    
    def _format_instagram_result(self, result: Dict[str, Any]) -> str:
        """인스타그램 결과 포맷팅"""
        formatted = "📱 **인스타그램 포스트가 완성되었습니다!**\n\n"
        
        if result.get("caption"):
            formatted += f"**📝 캡션:**\n{result['caption']}\n\n"
        
        if result.get("hashtags"):
            formatted += f"**🏷️ 해시태그:**\n{result['hashtags']}\n\n"
        
        if result.get("cta"):
            formatted += f"**💬 CTA (Call-to-Action):**\n{result['cta']}"
        
        return formatted
    
    def _format_blog_result(self, result: Dict[str, Any]) -> str:
        """블로그 결과 포맷팅"""
        formatted = "📝 **블로그 포스트가 완성되었습니다!**\n\n"
        
        if result.get("title"):
            formatted += f"**제목:** {result['title']}\n\n"
        
        if result.get("outline"):
            formatted += f"**목차:**\n{result['outline']}\n\n"
        
        if result.get("body"):
            # 본문이 너무 길면 일부만 표시
            body = result['body']
            if len(body) > 500:
                body = body[:500] + "...\n\n[전체 내용은 생성된 블로그 포스트를 참조해주세요]"
            formatted += f"**본문:**\n{body}\n\n"
        
        if result.get("keywords"):
            formatted += f"**SEO 키워드:** {result['keywords']}"
        
        return formatted
    
    def _format_multiple_results(self, result: Dict[str, Any]) -> str:
        """다중 콘텐츠 결과 포맷팅"""
        formatted = "🎉 **여러 콘텐츠가 동시에 생성되었습니다!**\n\n"
        
        results = result.get("results", {})
        for content_type, content_result in results.items():
            if content_result.get("success"):
                formatted += f"✅ {content_type.upper()} 생성 완료\n"
            else:
                formatted += f"❌ {content_type.upper()} 생성 실패\n"
        
        formatted += f"\n총 {len([r for r in results.values() if r.get('success')])}개 콘텐츠가 생성되었습니다."
        
        return formatted
    
    def get_conversation_status(self, conversation_id: int) -> Dict[str, Any]:
        """대화 상태 조회"""
        return self.conversation_manager.get_conversation_summary(conversation_id)
    
    def get_agent_status(self) -> Dict[str, Any]:
        """에이전트 상태 조회"""
        # 만료된 대화 정리
        cleaned_count = self.conversation_manager.cleanup_expired_conversations()
        
        return {
            "version": self.version,
            "service_name": config.SERVICE_NAME,
            "status": "healthy",
            "intelligence_type": "complete_llm_based",
            "active_conversations": len(self.conversation_manager.conversations),
            "cleaned_conversations": cleaned_count,
            "available_tools": len(self.marketing_tools.get_available_tools()),
            "llm_capabilities": [
                "자연어 의도 분석",
                "맥락적 응답 생성",
                "단계별 진행 제어",
                "개인화된 질문 생성",
                "업종별 맞춤 상담"
            ],
            "features": [
                "완전 LLM 기반 대화",
                "단계별 마케팅 상담",
                "인스타그램 콘텐츠 생성",
                "블로그 포스트 작성",
                "마케팅 전략 수립",
                "캠페인 계획 수립",
                "키워드 분석"
            ],
            "supported_business_types": [
                "뷰티/미용", "음식점/카페", "온라인쇼핑몰", 
                "서비스업", "교육", "헬스케어", "제조업", "크리에이터"
            ],
            "conversation_intelligence": {
                "intent_analysis": "GPT-4 기반",
                "stage_progression": "LLM 자동 결정",
                "question_generation": "맞춤형 LLM 생성",
                "response_quality": "전문가 수준"
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
                
                # 과부하 방지
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
            return create_response(
                success=False,
                error=f"배치 처리 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def analyze_conversation_quality(self, conversation_id: int) -> Dict[str, Any]:
        """LLM 기반 대화 품질 분석"""
        try:
            if conversation_id not in self.conversation_manager.conversations:
                return {"error": "대화를 찾을 수 없습니다"}
            
            conversation = self.conversation_manager.conversations[conversation_id]
            
            quality_analysis_prompt = f"""다음 마케팅 상담 대화를 분석하여 품질을 평가해주세요.

대화 정보:
- 단계: {conversation.current_stage.value}
- 업종: {conversation.business_type}
- 완료율: {conversation.get_completion_rate():.1%}
- 메시지 수: {len(conversation.conversation_history)}
- 수집된 정보: {conversation.collected_info}

대화 히스토리:
{conversation.get_conversation_context()}

다음 기준으로 평가해주세요 (1-10점):
1. 정보 수집 완성도
2. 단계별 진행 적절성
3. 사용자 만족도 추정
4. 전문성 수준
5. 실용성

JSON 형태로 분석 결과를 제공해주세요."""
            
            analysis_result = await self.conversation_manager._call_llm(
                "대화 품질을 분석하는 전문가입니다.",
                quality_analysis_prompt
            )
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "quality_analysis": analysis_result,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"대화 품질 분석 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
