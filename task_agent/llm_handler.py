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
        self.default_provider = "gemini" if self.llm_manager.models.get("gemini") else "openai"
        
        logger.info(f"Task Agent LLM 핸들러 초기화 완료 (기본 프로바이더: {self.default_provider})")

    async def analyze_intent(self, message: str, persona: PersonaType, 
                           conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """사용자 의도 분석"""
        try:
            # 히스토리 컨텍스트 구성
            history_context = self._format_history(conversation_history) if conversation_history else ""
            
            # 메시지 구성
            messages = [
                {"role": "system", "content": prompt_manager.get_intent_analysis_prompt()},
                {"role": "user", "content": f"""
                페르소나: {persona.value}
                대화 히스토리: {history_context}
                현재 메시지: {message}
                """}
            ]

            # 공통 LLM 매니저를 통한 응답 생성
            result = await self.llm_manager.generate_response(
                messages=messages,
                provider=self.default_provider,
                output_format="json"
            )

            # 결과 검증 및 기본값 설정
            if isinstance(result, dict):
                return {
                    "intent": result.get("intent", "general_inquiry"),
                    "urgency": result.get("urgency", "medium"),
                    "confidence": result.get("confidence", 0.5)
                }
            
            # JSON 파싱 시도
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
            
            # 사용자 메시지 구성
            user_content = f"""
            대화 히스토리: {history_context}
            현재 메시지: {message}
            현재 시간: {self._get_current_time()}
            
            주의: 메시지에 여러 일정이 포함된 경우, 모든 일정을 배열 형태로 반환하세요.
            단일 일정인 경우: {{"schedules": [{{"title": "...", "start_time": "..."}}]}}
            다중 일정인 경우: {{"schedules": [{{"title": "일정1", "start_time": "..."}}, {{"title": "일정2", "start_time": "..."}}]}}
            """
            
            # OpenAI API 직접 호출
            import openai
            from shared_modules.env_config import get_config
            
            config = get_config()
            client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            result_content = response.choices[0].message.content
            
            # JSON 파싱 시도
            try:
                import json
                parsed_result = json.loads(result_content)
                if self._validate_multiple_extraction(parsed_result, extraction_type):
                    return parsed_result
            except json.JSONDecodeError:
                # JSON이 아닌 경우 문자열에서 JSON 추출 시도
                import re
                json_match = re.search(r'\{.*\}', result_content, re.DOTALL)
                if json_match:
                    try:
                        parsed_result = json.loads(json_match.group())
                        if self._validate_multiple_extraction(parsed_result, extraction_type):
                            return parsed_result
                    except json.JSONDecodeError:
                        pass
            
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

    def _fallback_response(self, persona: PersonaType) -> str:
        """백업 응답"""
        return f"{persona.value}를 위한 맞춤 조언을 준비하고 있습니다. 좀 더 구체적으로 말씀해주시면 더 정확한 도움을 드릴 수 있습니다."

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

