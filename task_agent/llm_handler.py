"""
Task Agent LLM 핸들러 v4
공통 모듈의 llm_utils를 활용하여 LLM 처리
"""

import sys
import os
import json
import logging
from typing import Dict, Any, Optional, List

# 공통 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "../shared_modules"))

from llm_utils import get_llm_manager, LLMManager
from env_config import get_config

from models import PersonaType
from config import config
from prompts import prompt_manager

logger = logging.getLogger(__name__)

class TaskAgentLLMHandler:
    """Task Agent 전용 LLM 핸들러"""

    def __init__(self):
        """LLM 핸들러 초기화"""
        # 공통 LLM 매니저 사용
        self.llm_manager = get_llm_manager()
        
        # Task Agent 전용 설정
        self.default_provider = "openai"
        
        logger.info(f"Task Agent LLM 핸들러 초기화 완료 (기본 프로바이더: {self.default_provider})")

    from typing import Union

    async def analyze_intent(self, message: str, persona: Union[str, PersonaType], 
                       conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """사용자 의도 분석"""
        try:
            # 히스토리 컨텍스트 구성
            history_context = self._format_history(conversation_history) if conversation_history else ""
            
            # persona를 문자열로 변환
            persona_str = persona.value if hasattr(persona, 'value') else str(persona)
            
            # 직접 LangChain으로 LLM 호출
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage, HumanMessage
            from langchain_core.output_parsers import JsonOutputParser
            from shared_modules.env_config import get_config
            
            config = get_config()
            
            # ChatOpenAI 인스턴스 생성
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1,
                api_key=config.OPENAI_API_KEY
            )
            
            # JSON 파서 설정
            json_parser = JsonOutputParser()
            
            # 메시지 구성
            messages = [
                SystemMessage(content=prompt_manager.get_intent_analysis_prompt()),
                HumanMessage(content=f"""
                페르소나: {persona_str}
                대화 히스토리: {history_context}
                현재 메시지: {message}
                """)
            ]
            
            # 체인 구성 및 실행
            chain = llm | json_parser
            result = await chain.ainvoke(messages)
            
            # 결과 검증 및 기본값 설정
            if isinstance(result, dict):
                return {
                    "intent": result.get("intent", "general_inquiry"),
                    "urgency": result.get("urgency", "medium"),
                    "confidence": result.get("confidence", 0.5)
                }
            
            # JSON 파싱 시도 (결과가 문자열인 경우)
            try:
                parsed_result = json.loads(str(result))
                return {
                    "intent": parsed_result.get("intent", "general_inquiry"),
                    "urgency": parsed_result.get("urgency", "medium"),
                    "confidence": parsed_result.get("confidence", 0.5)
                }
            except json.JSONDecodeError:
                pass

        except Exception as e:
            logger.error(f"의도 분석 실패: {e}")

        return self._fallback_intent_analysis(message)

    async def classify_automation_intent(self, message: str) -> Optional[str]:
        """자동화 의도 분류"""
        try:
            messages = [
                {"role": "system", "content": prompt_manager.get_automation_classification_prompt()},
                {"role": "user", "content": f"메시지: {message}"}
            ]

            result = await self.llm_manager.generate_response(
                messages=messages,
                provider=self.default_provider,
                output_format="string"
            )
            
            if isinstance(result, str):
                result = result.strip().strip('"')
                return result if result != "none" else None
            
            return None

        except Exception as e:
            logger.error(f"자동화 의도 분류 실패: {e}")
            return None
    async def generate_response(self, message: str, persona: PersonaType, intent: str,
                                context: str = "", conversation_history: List[Dict] = None) -> str:
        """개인화된 응답 생성"""
        try:
            # 1. 히스토리 컨텍스트 구성
            history_context = self._format_history(conversation_history) if conversation_history else ""

            # 2. 사용자 입력 + 히스토리 기반 컨텍스트 메시지 구성
            context_message = f"{history_context}\n\n사용자 메시지: {message}".strip()

            # 3. system 프롬프트: 페르소나+의도 역할 지시 프롬프트만 사용
            def is_brief_request(message: str) -> bool:
                return any(kw in message for kw in ["간단히", "요약", "짧게", "한눈에", "핵심만"])

            def is_detailed_request(message: str) -> bool:
                return any(kw in message for kw in ["자세히", "상세히", "예시 포함", "설명 좀", "길게"])
            
            system_prompt = prompt_manager.get_intent_specific_prompt(persona, intent)

            if is_brief_request(message):
                system_prompt += "\n\n(주의: 응답은 300자 이내로 핵심 요약. 이 문장은 출력하지 말 것.)"
            elif is_detailed_request(message):
                system_prompt += "\n\n(주의: 가능한 한 구체적 예시와 함께 상세하게 설명. 이 문장은 출력하지 말 것.)"
            else:
                system_prompt += "\n\n(주의: 기본은 간결하게, 질문자가 요청 시에만 자세히 설명. 이 문장은 출력하지 말 것.)"

            # 4. 추가 컨텍스트가 있다면 user 메시지에 포함
            if context:
                context_message += f"\n\n=== 추가 정보 ===\n{context}"

            # 5. 구성된 메시지
            messages = [
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": context_message.strip()}
            ]

            result = await self.llm_manager.generate_response(
                messages=messages,
                provider=self.default_provider,
                output_format="string"
            )

            return str(result) if result else self._fallback_response(persona)

        except Exception as e:
            logger.error(f"응답 생성 실패: {e}")
            return self._fallback_response(persona)


    async def extract_information(self, message: str, extraction_type: str, 
                        conversation_history: List[Dict] = None) -> Optional[Dict[str, Any]]:
        """정보 추출 (일정, 이메일, SNS 등) - 단일/다중 지원"""
        try:
            # 히스토리 컨텍스트 구성
            history_context = self._format_history(conversation_history) if conversation_history else ""
            
            # 시스템 프롬프트 가져오기
            system_prompt = prompt_manager.get_information_extraction_prompt(extraction_type)
            
            # 명확한 JSON 응답 지시 추가
            enhanced_system_prompt = f"""{system_prompt}

    중요: 반드시 유효한 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.
    정보가 부족하거나 추출할 수 없는 경우 null을 반환하세요."""
            
            # 사용자 메시지 구성 (system_prompt 중복 제거)
            user_content = f"""
            대화 히스토리: {history_context}
            현재 메시지: {message}
            현재 시간: {self._get_current_time()}

            위 정보를 바탕으로 {extraction_type} 정보를 추출해주세요.
            """
            
            # OpenAI API 직접 호출
            import openai
            from shared_modules.env_config import get_config
            
            config = get_config()
            
            # API 키 확인
            if not config.OPENAI_API_KEY:
                logger.error("OpenAI API 키가 설정되지 않았습니다.")
                return None
                
            client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": enhanced_system_prompt},
                    {"role": "user", "content": user_content.strip()}
                ],
                temperature=0.1,
                max_tokens=1000,
                response_format={"type": "json_object"}  # JSON 응답 강제
            )
            
            # 응답 검증
            if not response or not response.choices:
                logger.error("OpenAI API 응답이 비어있습니다.")
                return None
                
            if not response.choices[0] or not response.choices[0].message:
                logger.error("OpenAI API 응답 구조가 올바르지 않습니다.")
                return None
                
            result_content = response.choices[0].message.content
            
            # content가 None인 경우 처리
            if result_content is None:
                logger.error("OpenAI API에서 content가 None을 반환했습니다.")
                return None
                
            # 빈 문자열 처리
            if not result_content.strip():
                logger.error("OpenAI API에서 빈 응답을 반환했습니다.")
                return None
            
            # JSON 파싱
            try:
                import json
                parsed_result = json.loads(result_content)
                return parsed_result
                # 검증
                # if self._validate_multiple_extraction(parsed_result, extraction_type):
                #     return parsed_result
                # else:
                #     logger.warning(f"추출된 정보가 검증을 통과하지 못했습니다: {parsed_result}")
                #     return None
                    
            except json.JSONDecodeError as json_error:
                logger.error(f"JSON 파싱 실패: {json_error}, 응답: {result_content}")
                return None
            
        except openai.APIError as api_error:
            logger.error(f"OpenAI API 오류: {api_error}")
            return None
        except openai.RateLimitError as rate_error:
            logger.error(f"OpenAI API 요청 한도 초과: {rate_error}")
            return None
        except Exception as e:
            logger.error(f"정보 추출 실패 ({extraction_type}): {e}")
            return None

    def _validate_multiple_extraction(self, data: Dict[str, Any], extraction_type: str) -> bool:
        """다중 추출된 정보 검증"""
        if extraction_type == "schedule":
            schedules = data.get("schedules", [])
            if not isinstance(schedules, list) or not schedules:
                return False
            # 각 일정이 필수 필드를 가지고 있는지 확인
            return all(schedule.get("title") and schedule.get("start_time") for schedule in schedules)
        elif extraction_type == "email":
            emails = data.get("emails", [])
            if not isinstance(emails, list) or not emails:
                return False
            return all(email.get("to_emails") and email.get("subject") and email.get("body") for email in emails)
        elif extraction_type == "sns":
            posts = data.get("posts", [])
            if not isinstance(posts, list) or not posts:
                return False
            return all(post.get("platform") and post.get("content") for post in posts)
        return True

    def _format_history(self, conversation_history: List[Dict]) -> str:
        """대화 히스토리 포맷팅"""
        if not conversation_history:
            return ""
        
        formatted = []
        for msg in conversation_history[-5:]:  # 최근 5개만
            role = "사용자" if msg["role"] == "user" else "에이전트"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted)

    def _validate_extraction(self, data: Dict[str, Any], extraction_type: str) -> bool:
        """추출된 정보 검증"""
        if extraction_type == "schedule":
            return bool(data.get("title") and data.get("start_time"))
        elif extraction_type == "email":
            return bool(data.get("to_emails") and data.get("subject") and data.get("body"))
        elif extraction_type == "sns":
            return bool(data.get("platform") and data.get("content"))
        return True

    def _get_current_time(self) -> str:
        """현재 시간 반환"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _fallback_intent_analysis(self, message: str) -> Dict[str, Any]:
        """백업 의도 분석"""
        message_lower = message.lower()
        
        # 간단한 키워드 기반 분석
        if any(word in message_lower for word in ["자동화", "자동", "예약", "스케줄"]):
            intent = "task_automation"
        elif any(word in message_lower for word in ["일정", "미팅", "회의"]):
            intent = "schedule_management"
        elif any(word in message_lower for word in ["도구", "프로그램", "추천"]):
            intent = "tool_recommendation"
        else:
            intent = "general_inquiry"

        urgency = "high" if any(word in message_lower for word in ["긴급", "즉시", "지금"]) else "medium"

        return {
            "intent": intent,
            "urgency": urgency,
            "confidence": 0.3
        }

    def _fallback_response(self, persona) -> str:
        """백업 응답"""
        # persona를 안전하게 문자열로 변환
        persona_str = persona.value if hasattr(persona, 'value') else str(persona)
        return f"{persona_str}를 위한 맞춤 조언을 준비하고 있습니다. 좀 더 구체적으로 말씀해주시면 더 정확한 도움을 드릴 수 있습니다."

    def get_status(self) -> Dict[str, Any]:
        """LLM 핸들러 상태 반환"""
        llm_status = self.llm_manager.get_status()
        
        return {
            "task_agent_handler": {
                "default_provider": self.default_provider,
                "initialized": True
            },
            "llm_manager_status": llm_status
        }

    def test_connection(self) -> Dict[str, bool]:
        """LLM 연결 테스트"""
        return self.llm_manager.test_connection()

