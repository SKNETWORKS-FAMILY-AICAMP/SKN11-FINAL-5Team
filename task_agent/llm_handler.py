"""
간소화된 LLM 핸들러 v3
"""

import json
import logging
from typing import Dict, Any, Optional, List

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

from models import PersonaType
from config import config
from prompts import prompt_manager

logger = logging.getLogger(__name__)

class LLMHandler:
    """간소화된 LLM 핸들러"""

    def __init__(self):
        """LLM 초기화"""
        self.models = {}
        self.setup_models()
        self.str_parser = StrOutputParser()
        self.json_parser = JsonOutputParser()
        
        logger.info(f"LLM 핸들러 초기화 완료")

    def setup_models(self):
        """LLM 모델 설정"""
        # OpenAI 모델
        if config.OPENAI_API_KEY:
            self.models["openai"] = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=config.OPENAI_API_KEY,
                temperature=config.TEMPERATURE,
                max_tokens=config.MAX_TOKENS
            )
            
        # Google Gemini 모델
        if config.GOOGLE_API_KEY:
            self.models["gemini"] = ChatGoogleGenerativeAI(
                model=config.DEFAULT_MODEL,
                google_api_key=config.GOOGLE_API_KEY,
                temperature=config.TEMPERATURE,
                max_output_tokens=config.MAX_TOKENS
            )

        # 기본 모델 설정
        self.default_model = "gemini" if "gemini" in self.models else "openai"

    async def analyze_intent(self, message: str, persona: PersonaType, 
                           conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """사용자 의도 분석"""
        try:
            model = self.models.get(self.default_model)
            if not model:
                return self._fallback_intent_analysis(message)

            # 히스토리 컨텍스트 구성
            history_context = self._format_history(conversation_history) if conversation_history else ""
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", prompt_manager.get_intent_analysis_prompt()),
                ("human", f"""
                페르소나: {persona.value}
                대화 히스토리: {history_context}
                현재 메시지: {message}
                """)
            ])

            chain = prompt | model | self.json_parser
            result = await chain.ainvoke({})

            return {
                "intent": result.get("intent", "general_inquiry"),
                "urgency": result.get("urgency", "medium"),
                "confidence": result.get("confidence", 0.5)
            }

        except Exception as e:
            logger.error(f"의도 분석 실패: {e}")
            return self._fallback_intent_analysis(message)

    async def classify_automation_intent(self, message: str) -> Optional[str]:
        """자동화 의도 분류"""
        try:
            model = self.models.get(self.default_model)
            if not model:
                return None

            prompt = ChatPromptTemplate.from_messages([
                ("system", prompt_manager.get_automation_classification_prompt()),
                ("human", f"메시지: {message}")
            ])

            chain = prompt | model | self.str_parser
            result = await chain.ainvoke({})
            
            result = result.strip().strip('"')
            return result if result != "none" else None

        except Exception as e:
            logger.error(f"자동화 의도 분류 실패: {e}")
            return None

    async def generate_response(self, message: str, persona: PersonaType, 
                              context: str = "", conversation_history: List[Dict] = None) -> str:
        """개인화된 응답 생성"""
        try:
            model = self.models.get(self.default_model)
            if not model:
                return self._fallback_response(persona)

            # 히스토리 컨텍스트 구성
            history_context = self._format_history(conversation_history) if conversation_history else ""
            
            # 컨텍스트 메시지 생성
            context_message = prompt_manager.get_context_message(persona, message, history_context)
            
            if context:
                context_message += f"\n\n=== 추가 정보 ===\n{context}"

            prompt = ChatPromptTemplate.from_messages([
                ("system", prompt_manager.get_system_prompt(persona)),
                ("human", context_message)
            ])

            chain = prompt | model | self.str_parser
            result = await chain.ainvoke({})

            return result

        except Exception as e:
            logger.error(f"응답 생성 실패: {e}")
            return self._fallback_response(persona)

    async def extract_information(self, message: str, extraction_type: str, 
                                conversation_history: List[Dict] = None) -> Optional[Dict[str, Any]]:
        """정보 추출 (일정, 이메일, SNS 등)"""
        try:
            model = self.models.get(self.default_model)
            if not model:
                return None

            # 히스토리 컨텍스트 구성
            history_context = self._format_history(conversation_history) if conversation_history else ""
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", prompt_manager.get_information_extraction_prompt(extraction_type)),
                ("human", f"""
                대화 히스토리: {history_context}
                현재 메시지: {message}
                현재 시간: {self._get_current_time()}
                """)
            ])

            chain = prompt | model | self.json_parser
            result = await chain.ainvoke({})

            # 기본 검증
            if result and self._validate_extraction(result, extraction_type):
                return result
            
            return None

        except Exception as e:
            logger.error(f"정보 추출 실패 ({extraction_type}): {e}")
            return None

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
