"""
마케팅 에이전트 - 완전 LLM 기반 버전
단순하고 효율적인 멀티턴 대화 기반 마케팅 상담
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import asyncio

from conversation_manager import ConversationManager, MarketingStage
from general_marketing_tools import MarketingTools
from mcp_marketing_tools import MarketingAnalysisTools
from config import config, create_response

logger = logging.getLogger(__name__)

# 커스텀 예외 클래스
class ContentSelectionRequiredException(Exception):
    """콘텐츠 선택이 필요할 때 발생하는 예외"""
    def __init__(self, message: str, tool_type_options: List[str], content_type_options: List[str]):
        self.message = message
        self.tool_type_options = tool_type_options
        self.content_type_options = content_type_options
        super().__init__(self.message)

class MarketingAgent:
    """완전 LLM 기반 통합 마케팅 에이전트 - 멀티턴 대화 + 도구 활용"""
    
    def __init__(self):
        """에이전트 초기화"""
        self.conversation_manager = ConversationManager()
        self.general_marketing_tools = MarketingTools()
        self.mcp_marketing_tools = MarketingAnalysisTools()
        self.version = config.VERSION
        
        logger.info(f"LLM 기반 마케팅 에이전트 초기화 완료 (v{self.version})")
    
    async def process_message(self, user_input: str, user_id: int, 
                    conversation_id: Optional[int] = None) -> Dict[str, Any]:
        """개선된 메시지 처리 - 응답 분석 + 컨텐츠 멀티턴 지원"""
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
            
                # ✅ 컨텐츠 생성 시그널 확인 및 처리
                if response_text.startswith("TRIGGER_"):
                    trigger_parts = response_text.split(":", 1)
                    if len(trigger_parts) == 2:
                        trigger_type, display_text = trigger_parts
                        response_text = display_text
                        
                        # ✅ 자동화 작업 생성 처리
                        if trigger_type == "TRIGGER_AUTOMATION_TASK":
                            automation_result = await self._handle_automation_task_creation(display_text, conversation)
                            if automation_result.get("success"):
                                response_text = automation_result["message"]
                            else:
                                response_text = f"❌ 자동화 예약 실패: {automation_result.get('error', '알 수 없는 오류')}"
                        
                        # 실제 컨텐츠 생성 수행
                        elif trigger_type in ["TRIGGER_CONTENT_GENERATION", "TRIGGER_CONTENT_MODIFICATION", "TRIGGER_CONTENT_REGENERATION", "TRIGGER_NEW_CONTENT"]:
                            content_result = await self._handle_content_generation_with_llm(user_input, conversation)
                            if content_result and content_result.get("success"):
                                tool_results = content_result
                                formatted_content = self._format_tool_results(content_result)
                                response_text += f"\n\n{formatted_content}"
                                
                                # 🆕 컨텐츠 세션 업데이트 및 포스팅 데이터 설정
                                conversation.update_content_session(formatted_content, user_input)
                                conversation.current_content_for_posting = content_result
                            else:
                                response_text += "\n\n❌ 컨텐츠 생성 중 오류가 발생했습니다. 다시 시도해주세요."
            else:
                # 3. 일반 대화 처리 (응답 분석 포함)
                response_text = await self.conversation_manager.generate_response_with_context(user_input, conversation)
                
                # ✅ 컨텐츠 생성 시그널 확인 및 처리
                if response_text.startswith("TRIGGER_CONTENT_GENERATION:"):
                    display_text = response_text.split(":", 1)[1]
                    response_text = display_text
                    
                    # 실제 컨텐츠 생성 수행
                    content_result = await self._handle_content_generation_with_llm(user_input, conversation)
                    if content_result and content_result.get("success"):
                        tool_results = content_result
                        formatted_content = self._format_tool_results(content_result)
                        response_text += f"\n\n{formatted_content}"
                        
                        # 🆕 컨텐츠 세션 업데이트 및 포스팅 데이터 설정
                        conversation.update_content_session(formatted_content, user_input)
                        conversation.current_content_for_posting = content_result
                    else:
                        response_text += "\n\n❌ 컨텐츠 생성 중 오류가 발생했습니다. 다시 시도해주세요."
            
            # 5. 성능 정보
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 6. 응답 생성
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
                    "in_content_creation": conversation.is_in_content_creation(),
                    "content_session": conversation.current_content_session,
                    "features": ["response_analysis", "content_multiturn", "fixed_content_generation"]
                }
            )
            
        except Exception as e:
            logger.error(f"메시지 처리 실패: {e}")
            return create_response(
                success=False,
                error=f"메시지 처리 중 오류가 발생했습니다: {str(e)}"
            )
   
    async def _handle_content_session(self, user_input: str, conversation, is_initial: bool = False) -> str:
        """컨텐츠 제작 세션 처리 - 멀티턴 대화 지원"""
        try:
            # conversation_manager의 컨텐츠 세션 처리 호출
            response_text = await self.conversation_manager._handle_content_creation_session(
                user_input, conversation, is_initial
            )
            
            # 시그널 확인 - conversation_manager에서 시그널을 반환하면 여기서 처리
            if response_text.startswith("TRIGGER_"):
                # 시그널은 process_message에서 처리하므로 그대로 반환
                return response_text
            
            # 일반 응답인 경우 그대로 반환
            return response_text
            
        except Exception as e:
            logger.error(f"컨텐츠 세션 처리 실패: {e}")
            return f"컨텐츠 처리 중 오류가 발생했습니다: {str(e)}"
    
    def _is_greeting(self, user_input: str) -> bool:
        """인사말 확인"""
        greetings = ["안녕", "hello", "hi", "처음", "시작", "상담"]
        return any(greeting in user_input.lower() for greeting in greetings)
    
    async def _generate_initial_content(self, user_input: str, conversation) -> Tuple[str, Optional[Dict]]:
        """초기 컨텐츠 생성"""
        try:
            # LLM 기반 컨텐츠 생성 시도
            tool_result = await self._handle_content_generation_with_llm(user_input, conversation)
            
            if tool_result:
                # 컨텐츠 세션 시작
                content_type = tool_result.get("content_type", "general")
                conversation.start_content_session(content_type, user_input)
                
                # 결과 포맷팅
                formatted_result = self._format_tool_results(tool_result)
                return formatted_result, tool_result
            else:
                return "컨텐츠 생성에 실패했습니다. 다시 시도해주세요.", None
                
        except Exception as e:
            logger.error(f"초기 컨텐츠 생성 실패: {e}")
            return f"컨텐츠 생성 중 오류가 발생했습니다: {str(e)}", None
    
    async def _should_generate_content_with_llm(self, user_input: str, conversation) -> bool:
        """LLM 기반 콘텐츠 생성 필요성 판단"""
        has_enough_info = conversation.get_completion_rate() > 0.2
        is_execution_stage = conversation.current_stage in [MarketingStage.EXECUTION, MarketingStage.COMPLETED]
        
        # 실행 단계이거나 충분한 정보가 있으면서 콘텐츠 요청이 있는 경우
        return is_execution_stage or has_enough_info
    
    async def _handle_automation_task_creation(self, display_text: str, conversation) -> Dict[str, Any]:
        """자동화 작업 생성 처리"""
        try:
            # display_text에서 scheduled_at 추출 ("scheduled_at|message" 형식)
            if "|" in display_text:
                scheduled_at_str, message = display_text.split("|", 1)
            else:
                return {
                    "success": False,
                    "error": "스케줄 시간 정보가 없습니다."
                }
            
            # 날짜 파싱
            try:
                from datetime import datetime
                scheduled_at = datetime.fromisoformat(scheduled_at_str)
            except ValueError:
                return {
                    "success": False,
                    "error": f"잘못된 날짜 형식: {scheduled_at_str}"
                }
            
            # create_automation_task 호출
            try:
                from shared_modules.database import SessionLocal
                from shared_modules.queries import create_automation_task
                
                with SessionLocal() as db:
                    # 컨텐츠 데이터 준비
                    content_data = conversation.current_content_for_posting or {}
                    task_data = {
                        "content_type": content_data.get("type", "general"),
                        "content": content_data.get("full_content", ""),
                        "platform": "social_media",  # 기본값
                        "user_id": conversation.user_id,
                        "conversation_id": conversation.conversation_id
                    }
                    
                    # 자동화 작업 생성
                    automation_task = create_automation_task(
                        db=db,
                        user_id=conversation.user_id,
                        task_type="social_posting",
                        title=f"마케팅 컨텐츠 자동 포스팅",
                        template_id=None,  # 필요시 템플릿 ID 추가
                        task_data=task_data,
                        conversation_id=conversation.conversation_id,
                        scheduled_at=scheduled_at
                    )
                    
                    if automation_task:
                        # 포스팅 프로세스 완료
                        conversation.complete_posting_process()
                        conversation.end_content_session()
                        conversation.current_stage = MarketingStage.COMPLETED
                        
                        return {
                            "success": True,
                            "message": f"🎉 **자동화 예약 완료!**\n\n📅 **예약 시간**: {scheduled_at.strftime('%Y년 %m월 %d일 %H:%M')}\n🚀 **상태**: 예약 대기 중\n\n컨텐츠가 지정된 시간에 자동으로 포스팅됩니다!",
                            "task_id": automation_task.task_id,
                            "scheduled_at": scheduled_at.isoformat()
                        }
                    else:
                        return {
                            "success": False,
                            "error": "데이터베이스에 작업 저장 실패"
                        }
                        
            except Exception as db_error:
                logger.error(f"데이터베이스 오류: {db_error}")
                return {
                    "success": False,
                    "error": f"데이터베이스 오류: {str(db_error)}"
                }
                
        except Exception as e:
            logger.error(f"자동화 작업 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_content_generation_with_llm(self, user_input: str, conversation) -> Optional[Dict[str, Any]]:
        """LLM 기반 콘텐츠 생성 처리"""
        try:
            # 컨텍스트 정보 준비
            context = self._prepare_context_for_tools(conversation)
            
            # 필수 정보 체크: 직종과 판매 제품 정보
            missing_info = self._check_required_info(context)
            if missing_info:
                return {
                    "success": False,
                    "error": missing_info,
                    "type": "missing_required_info"
                }
            
            # 사용자가 선택 옵션을 제공했는지 확인
            parsed_selection = self._parse_user_selection(user_input, conversation)
            if parsed_selection:
                tool_type, content_type = parsed_selection
            else:
                # LLM을 통한 tool_type과 content_type 분석
                try:
                    tool_type, content_type = await self._analyze_content_type_with_llm(user_input, context)
                except ContentSelectionRequiredException as e:
                    # 선택이 필요한 경우 메시지 반환
                    return {
                        "success": False,
                        "error": e.message,
                        "type": "selection_required",
                        "tool_options": e.tool_type_options,
                        "content_options": e.content_type_options
                    }
            
            # 키워드 추출
            target_keyword = await self._extract_keyword_with_llm(user_input, conversation)
            
            # 툴 타입별 실행
            if tool_type == "trend_analysis":
                keywords = [target_keyword] + await self.general_marketing_tools.generate_related_keywords(target_keyword, 4)
                result = await self.general_marketing_tools.analyze_naver_trends(keywords)
                
            elif tool_type == "hashtag_analysis":
                result = await self.general_marketing_tools.analyze_instagram_hashtags(
                    question=user_input,
                    user_hashtags=[target_keyword]
                )
                
            elif tool_type == "content_generation":
                # 이미 위에서 단계 체크를 했으므로 여기서는 바로 실행
                if content_type == "blog":
                    result = await self.general_marketing_tools.create_blog_post(target_keyword, context)
                elif content_type == "instagram":
                    result = await self.general_marketing_tools.create_instagram_post(target_keyword, context)
                elif content_type == "strategy":
                    result = await self.general_marketing_tools.create_strategy_content(target_keyword, context)
                elif content_type == "campaign":
                    result = await self.general_marketing_tools.create_campaign_content(target_keyword, context)
                else:
                    # 일반적인 콘텐츠 생성
                    result = await self.general_marketing_tools.generate_instagram_content()
                    
            elif tool_type == "keyword_research":
                keywords = await self.mcp_marketing_tools.generate_related_keywords(target_keyword, 15)
                trend_result = await self.mcp_marketing_tools.analyze_naver_trends(keywords[:5])
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
            
            return result
                
        except Exception as e:
            logger.error(f"콘텐츠 생성 처리 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "content_generation"
            }
    
    async def _analyze_content_type_with_llm(self, user_input: str, context: Dict[str, Any]) -> Tuple[str, str]:
        """LLM 기반 tool_type과 content_type 분석"""
        try:
            # 사용자 직종과 제품 정보 추출
            user_job = context.get('business_type') or context.get('job') or context.get('occupation')
            product_info = (context.get('product') or context.get('service') or 
                           context.get('target_product') or context.get('selling_product'))
            
            analysis_prompt = f"""다음 사용자 요청을 분석하여 마케팅 도구 타입과 콘텐츠 타입을 판단해주세요.

사용자 요청: "{user_input}"
사용자 직종: {user_job}
판매 제품/서비스: {product_info}
비즈니스 컨텍스트: {context}

다음 형식으로 답변해주세요:
tool_type: [trend_analysis/hashtag_analysis/content_generation/keyword_research 중 하나만]
content_type: [instagram/blog/strategy/campaign 중 하나만]

분류 기준:
- trend_analysis: 트렌드 분석, 검색량 조사
- hashtag_analysis: 해시태그 분석, SNS 분석
- content_generation: 콘텐츠 생성, 글 작성
- keyword_research: 키워드 연구, 관련 키워드 찾기

- instagram: 인스타그램 포스트, SNS 콘텐츠
- blog: 블로그 포스트, 긴 글 콘텐츠
- strategy: 마케팅 전략, 전반적 계획
- campaign: 캠페인, 이벤트 기획

사용자의 직종과 판매 제품을 고려하여 가장 적합한 마케팅 도구와 콘텐츠 유형을 선택해주세요.
반드시 각 항목에서 하나씩만 선택하여 답변해주세요."""
            
            content = await self.general_marketing_tools.generate_content_with_llm(analysis_prompt)
            
            # 응답에서 tool_type과 content_type 추출
            content_lower = content.lower()
            
            # 여러 옵션이 선택되었는지 확인
            tool_type_options = self._extract_multiple_options(content, "tool_type")
            content_type_options = self._extract_multiple_options(content, "content_type")
            
            # 여러 옵션이 있으면 사용자에게 선택 요청
            if len(tool_type_options) > 1 or len(content_type_options) > 1:
                return self._request_user_selection(tool_type_options, content_type_options)
            
            # 단일 옵션 추출 (기존 로직)
            tool_type = "content_generation"  # 기본값
            if "trend_analysis" in content_lower:
                tool_type = "trend_analysis"
            elif "hashtag_analysis" in content_lower:
                tool_type = "hashtag_analysis"
            elif "keyword_research" in content_lower:
                tool_type = "keyword_research"
            elif "content_generation" in content_lower:
                tool_type = "content_generation"
            
            # content_type 추출
            content_type = "instagram"  # 기본값
            if "blog" in content_lower:
                content_type = "blog"
            elif "strategy" in content_lower:
                content_type = "strategy"
            elif "campaign" in content_lower:
                content_type = "campaign"
            elif "instagram" in content_lower:
                content_type = "instagram"
            
            return tool_type, content_type
                
        except Exception as e:
            logger.warning(f"콘텐츠 타입 분석 실패: {e}")
            return "content_generation", "instagram"
    
    def _extract_multiple_options(self, content: str, option_type: str) -> List[str]:
        """응답에서 여러 옵션이 선택되었는지 확인"""
        try:
            lines = content.split('\n')
            for line in lines:
                if option_type in line.lower():
                    # [option1/option2/option3] 형태 찾기
                    if '[' in line and ']' in line:
                        options_text = line[line.find('[')+1:line.find(']')]
                        if '/' in options_text:
                            options = [opt.strip() for opt in options_text.split('/')]
                            # 유효한 옵션들만 필터링
                            valid_options = []
                            if option_type == "tool_type":
                                valid_types = ["trend_analysis", "hashtag_analysis", "content_generation", "keyword_research"]
                                valid_options = [opt for opt in options if opt in valid_types]
                            elif option_type == "content_type":
                                valid_types = ["instagram", "blog", "strategy", "campaign"]
                                valid_options = [opt for opt in options if opt in valid_types]
                            
                            return valid_options if len(valid_options) > 1 else []
            return []
        except Exception as e:
            logger.warning(f"옵션 추출 실패: {e}")
            return []
    
    def _request_user_selection(self, tool_type_options: List[str], content_type_options: List[str]) -> Tuple[str, str]:
        """사용자에게 선택을 요청하는 메시지 생성"""
        selection_message = "🤔 **더 정확한 컨텐츠 제작을 위해 선택해주세요!**\n\n"
        
        if len(tool_type_options) > 1:
            selection_message += "📊 **마케팅 도구 유형:**\n"
            for i, option in enumerate(tool_type_options, 1):
                option_name = {
                    "trend_analysis": "트렌드 분석",
                    "hashtag_analysis": "해시태그 분석", 
                    "content_generation": "콘텐츠 생성",
                    "keyword_research": "키워드 연구"
                }.get(option, option)
                selection_message += f"{i}. {option_name}\n"
            selection_message += "\n"
        
        if len(content_type_options) > 1:
            selection_message += "🎨 **콘텐츠 유형:**\n"
            for i, option in enumerate(content_type_options, 1):
                option_name = {
                    "instagram": "인스타그램 포스트",
                    "blog": "블로그 포스트",
                    "strategy": "마케팅 전략",
                    "campaign": "캠페인 기획"
                }.get(option, option)
                selection_message += f"{i}. {option_name}\n"
        
        selection_message += "\n원하시는 번호를 말씀해주시거나, 구체적으로 어떤 것을 원하시는지 알려주세요!"
        
        # 선택 요청 예외 발생 (이를 통해 상위에서 처리)
        raise ContentSelectionRequiredException(selection_message, tool_type_options, content_type_options)
    
    async def _extract_keyword_with_llm(self, user_input: str, conversation) -> str:
        """LLM 기반 키워드 추출"""
        try:
            # 컨텍스트에서 제품 정보 추출
            context = self._prepare_context_for_tools(conversation)
            product_info = (context.get('product') or context.get('service') or 
                           context.get('target_product') or context.get('selling_product'))
            
            keyword_prompt = f"""다음 맥락에서 마케팅 콘텐츠 생성에 사용할 핵심 키워드를 추출해주세요.

사용자 요청: "{user_input}"
직종/업종: {conversation.business_type}
판매 제품/서비스: {product_info}
수집된 정보: {conversation.collected_info}

사용자의 직종과 판매 제품을 고려하여 가장 효과적인 마케팅 키워드 하나를 추출해서 단답으로 답변해주세요."""
            
            content = await self.general_marketing_tools.generate_content_with_llm(keyword_prompt)
            
            # 첫 번째 단어 추출
            extracted = content.strip().split()[0] if content.strip() else "마케팅"
            
            return extracted
            
        except Exception as e:
            logger.warning(f"키워드 추출 실패: {e}")
            # 폴백: 업종 또는 기본값 사용
            return conversation.business_type if conversation.business_type != "일반" else "마케팅"
    
    def _parse_user_selection(self, user_input: str, conversation) -> Optional[Tuple[str, str]]:
        """사용자의 선택 입력을 파싱"""
        user_input_lower = user_input.lower()
        
        # 숫자 선택 또는 직접 명시한 선택 처리
        tool_type = None
        content_type = None
        
        # Tool type 파싱
        if any(word in user_input_lower for word in ["트렌드", "trend", "검색량", "분석"]):
            tool_type = "trend_analysis"
        elif any(word in user_input_lower for word in ["해시태그", "hashtag", "sns"]):
            tool_type = "hashtag_analysis"
        elif any(word in user_input_lower for word in ["콘텐츠", "content", "생성", "작성"]):
            tool_type = "content_generation"
        elif any(word in user_input_lower for word in ["키워드", "keyword", "연구"]):
            tool_type = "keyword_research"
        
        # Content type 파싱
        if any(word in user_input_lower for word in ["인스타", "instagram", "인스타그램"]):
            content_type = "instagram"
        elif any(word in user_input_lower for word in ["블로그", "blog"]):
            content_type = "blog"
        elif any(word in user_input_lower for word in ["전략", "strategy"]):
            content_type = "strategy"
        elif any(word in user_input_lower for word in ["캠페인", "campaign"]):
            content_type = "campaign"
        
        # 숫자 선택 처리 (1, 2, 3, 4)
        if tool_type is None:
            if "1" in user_input or "첫" in user_input:
                # 이전 선택 옵션에서 추정 (기본적으로 trend_analysis)
                tool_type = "trend_analysis"
            elif "2" in user_input or "두" in user_input:
                tool_type = "hashtag_analysis"
            elif "3" in user_input or "세" in user_input:
                tool_type = "content_generation"
            elif "4" in user_input or "네" in user_input:
                tool_type = "keyword_research"
        
        if content_type is None:
            if "1" in user_input or "첫" in user_input:
                content_type = "instagram"
            elif "2" in user_input or "두" in user_input:
                content_type = "blog"
            elif "3" in user_input or "세" in user_input:
                content_type = "strategy"
            elif "4" in user_input or "네" in user_input:
                content_type = "campaign"
        
        # 둘 다 선택되었으면 반환
        if tool_type and content_type:
            return tool_type, content_type
        
        return None
    
    def _check_required_info(self, context: Dict[str, Any]) -> Optional[str]:
        """컨텐츠 생성에 필요한 필수 정보 체크"""
        missing_items = []
        
        # 1. 직종 정보 체크
        user_job = context.get("business_type") or context.get("job") or context.get("occupation")
        if not user_job or user_job == "일반":
            missing_items.append("직종/업종")
        
        # 2. 판매 제품 정보 체크
        product_info = (context.get("product") or context.get("service") or 
                       context.get("target_product") or context.get("selling_product"))
        if not product_info:
            missing_items.append("판매 제품/서비스")
        
        if missing_items:
            missing_str = ", ".join(missing_items)
            return f"컨텐츠 생성을 위해 다음 정보가 필요합니다:\n\n📝 **필수 정보:**\n- {missing_str}\n\n위 정보를 알려주시면 맞춤형 마케팅 컨텐츠를 생성해드리겠습니다!"
        
        return None
    
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
            error_type = tool_results.get("type", "general_error")
            
            if error_type == "selection_required":
                # 사용자 선택 요청 메시지
                return tool_results.get("error", "선택이 필요합니다.")
            elif error_type == "missing_required_info":
                # 필수 정보 부족 메시지
                return tool_results.get("error", "필수 정보가 부족합니다.")
            else:
                # 일반 오류
                return f"❌ 콘텐츠 생성 중 오류가 발생했습니다: {tool_results.get('error', '알 수 없는 오류')}"
        
        # 키워드 리서치 결과인지 확인 (keywords와 trend_data가 모두 있는 경우)
        if 'keywords' in tool_results and 'trend_data' in tool_results:
            return self._format_keyword_research_result(tool_results)
        
        content_type = tool_results.get("type", "content")
        
        if content_type == "instagram_post":
            return self._format_instagram_result(tool_results)
        elif content_type == "blog_post":
            return self._format_blog_result(tool_results)
        elif content_type == "marketing_strategy":
            return f"📊 **마케팅 전략이 완성되었습니다!**\n\n{tool_results.get('strategy', '')}"
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
    
    def _format_keyword_research_result(self, result: Dict[str, Any]) -> str:
        """키워드 리서치 결과 포맷팅"""
        formatted = "🔍 **키워드 리서치 결과가 완성되었습니다!**\n\n"
        
        # 키워드 목록 표시
        keywords = result.get('keywords', [])
        if keywords:
            formatted += "🏷️ **추천 키워드:**\n"
            for i, keyword in enumerate(keywords[:10], 1):  # 상위 10개만 표시
                formatted += f"{i}. {keyword}\n"
            
            if len(keywords) > 10:
                formatted += f"\n... 총 {len(keywords)}개 키워드 (상위 10개 표시)\n"
            formatted += "\n"
        
        # 트렌드 데이터 표시
        trend_data = result.get('trend_data', {})
        if trend_data.get('success') and trend_data.get('data'):
            formatted += "📈 **키워드 트렌드 분석:**\n"
            
            trend_items = trend_data['data']
            for item in trend_items:
                keyword_name = item.get('title', '')
                trend_values = item.get('data', [])
                
                if trend_values:
                    # 최신 트렌드 비율 추출
                    latest_ratio = trend_values[0].get('ratio', 0)
                    if latest_ratio > 0:
                        # 비율에 따른 시각적 표시
                        if latest_ratio >= 80:
                            trend_icon = "🔥"  # 고온
                        elif latest_ratio >= 50:
                            trend_icon = "🔴"  # 중간
                        elif latest_ratio >= 20:
                            trend_icon = "🟡"  # 낮음
                        else:
                            trend_icon = "⚪"  # 매우 낮음
                        
                        formatted += f"{trend_icon} **{keyword_name}**: {latest_ratio:.1f}%\n"
                    else:
                        formatted += f"⚫ **{keyword_name}**: 데이터 없음\n"
                else:
                    formatted += f"⚫ **{keyword_name}**: 데이터 없음\n"
            
            # 분석 기간 정보
            period = trend_data.get('period', '')
            if period:
                formatted += f"\n📅 **분석 기간:** {period}\n"
        
        # 마케팅 활용 팁
        formatted += "\n💡 **마케팅 활용 팁:**\n"
        formatted += "• 고온 트렌드 (🔥) 키워드를 우선 활용하세요\n"
        formatted += "• 여러 키워드를 조합하여 콘텐츠를 제작하세요\n"
        formatted += "• 땅기 트렌드를 고려하여 전략을 수립하세요"
        
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
            "available_tools": len(self.general_marketing_tools.get_available_tools()),
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