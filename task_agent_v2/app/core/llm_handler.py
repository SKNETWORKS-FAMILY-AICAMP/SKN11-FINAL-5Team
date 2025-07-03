import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

from ..schemas.enums import PersonaType, TaskTopic
from .config import GOOGLE_API_KEY, LLM_MODELS, OPENAI_API_KEY, config
from .prompts import Prompts

logger = logging.getLogger(__name__)

class LLMHandler:
    """간소화된 LLM 핸들러"""

    def __init__(self):
        """LLM 핸들러 초기화"""
        self.models = {}
        
        # OpenAI 모델 설정
        if OPENAI_API_KEY:
            self.models["gpt"] = ChatOpenAI(
                model=LLM_MODELS.get("gpt", "gpt-4o-mini"),
                api_key=OPENAI_API_KEY,
                temperature=0.7,
                max_tokens=1500
            )
            
        # Google Gemini 모델 설정
        if GOOGLE_API_KEY:
            self.models["gemini"] = ChatGoogleGenerativeAI(
                model=LLM_MODELS.get("gemini", "gemini-1.5-flash"),
                google_api_key=GOOGLE_API_KEY,
                temperature=0.1,
                max_output_tokens=1500
            )

        # 기본 모델 설정
        self.default_model = "gemini" if "gemini" in self.models else "gpt"
        
        # Output Parsers
        self.str_parser = StrOutputParser()
        self.json_parser = JsonOutputParser()
        
        # Prompts 인스턴스 초기화
        self.prompts = Prompts()
        
        logger.info(f"LLM 핸들러 초기화 완료 - 기본 모델: {self.default_model}")

    async def analyze_intent(self, message: str, persona: PersonaType) -> Dict[str, Any]:
        """사용자 의도 분석"""
        try:
            model = self.models.get('gpt')
            if not model:
                return self._fallback_analysis(message, persona)

            # PersonaType enum을 문자열로 변환
            persona_value = persona.value if hasattr(persona, 'value') else str(persona)

            prompt = ChatPromptTemplate.from_messages([
                ("system", "당신은 사용자 메시지 의도 분석 전문가입니다."),
                ("human", """
                    사용자 메시지를 분석하여 의도, 긴급도, 확신도를 JSON 형태로 반환해주세요.

                    메시지: "{message}"
                    페르소나: {persona}

                    분석 기준:
                    1. intent: tool_stack, schedule_management, task_prioritization, task_automation, general_inquiry 중 선택
                    2. urgency: high(즉시), medium(며칠내), low(장기) 중 선택  
                    3. confidence: 0.0-1.0 범위의 분석 확신도

                    JSON 형태로 응답: {{"intent": "...", "urgency": "...", "confidence": 0.0}}
                """)
            ])

            chain = prompt | model | self.json_parser
            result = await chain.ainvoke({
                "message": message,
                "persona": persona_value
            })

            return {
                "intent": result.get("intent", "general_inquiry"),
                "urgency": result.get("urgency", "medium"),
                "confidence": result.get("confidence", 0.5)
            }

        except Exception as e:
            logger.error(f"의도 분석 실패: {e}")
            return self._fallback_analysis(message, persona)

    async def classify_automation_intent(self, message: str) -> Optional[str]:
        """자동화 의도 분류"""
        try:
            model = self.models.get('gpt')
            if not model:
                return None

            prompt = ChatPromptTemplate.from_messages([
                ("system", "당신은 자동화 작업 분류 전문가입니다."),
                ("human", """
                    메시지를 분석하여 자동화 작업 유형을 분류해주세요.

                    메시지: "{message}"

                    자동화 유형:
                    - schedule_calendar: 일정 등록, 캘린더 추가
                    - publish_sns: SNS 게시물 발행
                    - send_email: 이메일 발송
                    - send_reminder: 리마인더 알림
                    - send_message: 메시지 전송

                    자동화와 관련이 없으면 "none"을 반환하세요.
                    유형만 반환해주세요 (예: "schedule_calendar" 또는 "none")
                """)
            ])

            chain = prompt | model | self.str_parser
            result = await chain.ainvoke({"message": message})
            
            result = result.strip().strip('"')
            return result if result != "none" else None

        except Exception as e:
            logger.error(f"자동화 의도 분류 실패: {e}")
            return None

    async def generate_personalized_response(
        self, 
        message: str, 
        persona: PersonaType, 
        topic: TaskTopic, 
        context: str = "",
        user_data: dict = None
    ) -> str:
        """개인화된 응답 생성 - prompts.py 참조"""
        try:
            model = self.models.get(self.default_model)
            if not model:
                return self._get_fallback_response(persona, topic)

            # enum을 문자열로 변환
            persona_value = persona.value if hasattr(persona, 'value') else str(persona)
            topic_value = topic.value if hasattr(topic, 'value') else str(topic)

            # prompts.py에서 페르소나별 상세 프롬프트 가져오기
            prompt_config = self.prompts.get_prompt(persona, topic)
            
            # 완성된 컨텍스트 메시지 생성
            context_message = self.prompts.get_context_message(
                persona=persona,
                topic=topic,
                user_message=message,
                user_data=user_data
            )
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", prompt_config["system_prompt"]),
                ("human", context_message + f"\n\n관련 추가 정보: {context}" if context else context_message)
            ])

            chain = prompt | model | self.str_parser
            result = await chain.ainvoke({
                "message": message,
                "topic": topic_value,
                "context": context,
                "persona": persona_value
            })

            return result

        except Exception as e:
            logger.error(f"개인화된 응답 생성 실패: {e}")
            return self._get_fallback_response(persona, topic)

    async def generate_daily_recommendations(
        self, 
        user_id: str,
        completed_tasks: list,
        upcoming_tasks: list
    ) -> List[str]:
        """일일 추천사항 생성"""
        try:
            model = self.models.get(self.default_model)
            if not model:
                return self._get_default_recommendations()

            prompt = ChatPromptTemplate.from_messages([
                ("system", "당신은 생산성 개선 전문가입니다."),
                ("human", """
                    사용자의 일일 업무 현황을 분석하여 3-5개의 구체적인 추천사항을 제시하세요.

                    완료된 업무 ({completed_count}개):
                    {completed_tasks}

                    내일 예정 업무 ({upcoming_count}개):
                    {upcoming_tasks}

                    다음 관점에서 추천사항을 제시하세요:
                    1. 업무 효율성 개선
                    2. 시간 관리 최적화  
                    3. 우선순위 조정
                    4. 자동화 기회
                    5. 휴식 및 밸런스

                    추천사항들을 JSON 배열로 반환: ["추천1", "추천2", "추천3"]
                """)
            ])

            chain = prompt | model | self.json_parser
            result = await chain.ainvoke({
                "completed_count": len(completed_tasks),
                "completed_tasks": json.dumps(completed_tasks, ensure_ascii=False, indent=2),
                "upcoming_count": len(upcoming_tasks),
                "upcoming_tasks": json.dumps(upcoming_tasks, ensure_ascii=False, indent=2)
            })

            return result if isinstance(result, list) else self._get_default_recommendations()

        except Exception as e:
            logger.error(f"추천사항 생성 실패: {e}")
            return self._get_default_recommendations()

    # ===== 히스토리 처리 메소드들 =====
    
    async def generate_response(
        self, 
        message: str, 
        persona: PersonaType, 
        topic: TaskTopic, 
        context: str = "",
        conversation_history: List[Dict[str, Any]] = None
    ) -> str:
        """대화 히스토리를 고려한 개인화된 응답 생성"""
        try:
            model = self.models.get(self.default_model)
            if not model:
                return self._get_fallback_response(persona, topic)

            # enum을 문자열로 변환
            persona_value = persona.value if hasattr(persona, 'value') else str(persona)
            topic_value = topic.value if hasattr(topic, 'value') else str(topic)

            # 히스토리 컨텍스트 구성
            history_context = self._format_history_for_llm(conversation_history) if conversation_history else ""

            # prompts.py에서 페르소나별 상세 프롬프트 가져오기
            prompt_config = self.prompts.get_prompt(persona, topic)
            
            # 완성된 컨텍스트 메시지 생성
            context_message = self.prompts.get_context_message(
                persona=persona,
                topic=topic,
                user_message=message
            )
            
            # 히스토리를 포함한 프롬프트 구성
            enhanced_context = context_message
            
            if history_context:
                enhanced_context += f"\n\n=== 대화 히스토리 ===\n{history_context}\n=== 히스토리 끝 ===\n"
            
            if context:
                enhanced_context += f"\n\n=== 추가 정보 ===\n{context}"

            prompt = ChatPromptTemplate.from_messages([
                ("system", prompt_config["system_prompt"] + "\n\n대화 히스토리를 참고하여 일관성 있고 콘텍스트에 맞는 응답을 제공하세요."),
                ("human", enhanced_context)
            ])

            chain = prompt | model | self.str_parser
            result = await chain.ainvoke({
                "message": message,
                "topic": topic_value,
                "context": context,
                "persona": persona_value
            })

            return result

        except Exception as e:
            logger.error(f"히스토리 포함 응답 생성 실패: {e}")
            return self._get_fallback_response(persona, topic)

    def _format_history_for_llm(self, conversation_history: List[Dict[str, Any]]) -> str:
        """대화 히스토리를 LLM에 전달할 형식으로 변환"""
        if not conversation_history:
            return "처음 대화입니다."
        
        formatted_messages = []
        for msg in conversation_history[-10:]:  # 최근 10개 메시지만 포함
            role = "사용자" if msg["role"] == "user" else "에이전트"
            timestamp = msg.get("timestamp", "")
            content = msg["content"]
            
            if timestamp:
                formatted_messages.append(f"[{timestamp}] {role}: {content}")
            else:
                formatted_messages.append(f"{role}: {content}")
        
        return "\n".join(formatted_messages)

    # ===== 백업 메서드들 =====
    def _fallback_analysis(self, message: str, persona: PersonaType) -> Dict[str, Any]:
        """백업 분석 로직"""
        message_lower = message.lower()

        # 긴급도 분석
        urgency = "medium"
        if any(keyword in message_lower for keyword in ["긴급", "즉시", "오늘", "지금"]):
            urgency = "high"
        elif any(keyword in message_lower for keyword in ["언젠가", "나중에", "여유"]):
            urgency = "low"

        # 의도 분석
        intent = "general_inquiry"
        if any(keyword in message_lower for keyword in ["일정", "스케줄", "미팅"]):
            intent = "schedule_management"
        elif any(keyword in message_lower for keyword in ["자동화", "자동", "반복"]):
            intent = "task_automation"
        elif any(keyword in message_lower for keyword in ["우선순위", "중요도"]):
            intent = "task_prioritization"
        elif any(keyword in message_lower for keyword in ["도구", "프로그램", "AI"]):
            intent = "tool_stack"

        return {
            "intent": intent,
            "urgency": urgency,
            "confidence": 0.3
        }

    def _get_fallback_response(self, persona: PersonaType, topic: TaskTopic) -> str:
        """백업 응답"""
        # enum을 안전하게 문자열로 변환
        persona_value = persona.value if hasattr(persona, 'value') else str(persona)
        topic_value = topic.value if hasattr(topic, 'value') else str(topic)
        
        return f"{persona_value}를 위한 {topic_value} 조언을 준비 중입니다."

    def _get_default_recommendations(self) -> List[str]:
        """기본 추천사항"""
        return [
            "내일의 가장 중요한 업무 3개를 선정하여 우선순위를 설정하세요.",
            "반복적인 업무가 있다면 자동화 도구 활용을 검토해보세요.",
            "업무 완료 후에는 적절한 휴식을 취하여 번아웃을 예방하세요."
        ]

    # ===== 자동화 업무 정보 추출 =====

    async def extract_schedule_info(
        self, 
        message: str, 
        conversation_history: List[Dict[str, Any]] = None, 
        context_from_history: str = ""
    ) -> Optional[Dict[str, Any]]:
        """대화 히스토리를 고려한 일정 정보 추출 - Google Calendar API 호환 형태로 반환"""
        try:
            model = self.models.get(self.default_model)
            if not model:
                return None

            # 히스토리 컨텍스트 구성
            history_context = ""
            if conversation_history:
                history_context = self._format_history_for_llm(conversation_history)

            prompt = ChatPromptTemplate.from_messages([
                ("system", "당신은 대화 히스토리를 고려하여 자연어에서 일정 정보를 추출하는 전문가입니다. Google Calendar API 호환 형태로 정보를 추출해야 합니다."),
                ("human", """
                    대화 히스토리와 현재 메시지를 종합하여 일정 정보를 추출하여 JSON 형태로 반환해주세요.

                    대화 히스토리:
                    {history_context}

                    이전 대화에서 확인된 정보:
                    {context_from_history}

                    현재 메시지: "{message}"
                    현재 날짜: {current_date}

                    추출할 정보:
                    - title: 일정 제목 (필수)
                    - start_time: 시작시간 (YYYY-MM-DDTHH:MM:SS 형식, 필수)
                    - end_time: 종료시간 (YYYY-MM-DDTHH:MM:SS 형식, 선택사항)
                    - description: 일정 설명 (선택사항)
                    - location: 장소 (선택사항)
                    - calendar_id: 캘린더 ID (기본값: "primary")
                    - timezone: 시간대 (기본값: "Asia/Seoul")
                    - reminders: 리마인더 설정 ([{{"method": "popup", "minutes": 15}}] 형태)
                    - recurrence: 반복 설정 (["RRULE:FREQ=WEEKLY"] 형태, 반복 일정인 경우만)

                    반복 설정 예시:
                    - 매일: ["RRULE:FREQ=DAILY"]
                    - 매주: ["RRULE:FREQ=WEEKLY"]
                    - 매월: ["RRULE:FREQ=MONTHLY"]
                    - 평일만: ["RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR"]

                    일정 정보가 충분하지 않으면 null을 반환하세요.
                    시간이 지정되지 않으면 기본값으로 시작시간 09:00, 종료시간 10:00을 사용하세요.

                    JSON 형태:
                    {{
                        "title": "회의 제목",
                        "start_time": "2024-01-15T14:00:00",
                        "end_time": "2024-01-15T15:30:00",
                        "description": "회의 설명",
                        "location": "회의실 A",
                        "calendar_id": "primary",
                        "timezone": "Asia/Seoul",
                        "reminders": [{{"method": "popup", "minutes": 15}}],
                        "recurrence": null
                    }}
                """)
            ])

            chain = prompt | model | self.json_parser
            result = await chain.ainvoke({
                "message": message,
                "current_date": datetime.now().strftime("%Y-%m-%d"),
                "history_context": history_context,
                "context_from_history": context_from_history
            })

            # 필수 필드 검증 및 기본값 설정
            if result and result.get("title") and result.get("start_time"):
                # 기본값 설정
                if not result.get("end_time"):
                    # 시작시간에서 1시간 후로 설정
                    try:
                        start_dt = datetime.fromisoformat(result["start_time"].replace('T', ' '))
                        end_dt = start_dt.replace(hour=start_dt.hour + 1)
                        result["end_time"] = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
                    except:
                        # 파싱 실패시 기본값
                        result["end_time"] = result["start_time"].replace("T09:00:00", "T10:00:00")
                
                # 기본값들 설정
                result.setdefault("description", "")
                result.setdefault("location", "")
                result.setdefault("calendar_id", "primary")
                result.setdefault("timezone", "Asia/Seoul")
                result.setdefault("reminders", [{"method": "popup", "minutes": 15}])
                result.setdefault("recurrence", None)
                
                return result
            
            return None

        except Exception as e:
            logger.error(f"히스토리 포함 일정 정보 추출 실패: {e}")
            return None

    async def extract_sns_info(
        self, 
        message: str, 
        conversation_history: List[Dict[str, Any]], 
        context_from_history: str = ""
    ) -> Optional[Dict[str, Any]]:
        """대화 히스토리를 고려한 SNS 발행 정보 추출"""
        try:
            model = self.models.get(self.default_model)
            if not model:
                return None

            # 히스토리 컨텍스트 구성
            history_context = self._format_history_for_llm(conversation_history)

            prompt = ChatPromptTemplate.from_messages([
                ("system", "당신은 대화 히스토리를 고려하여 자연어에서 SNS 발행 정보를 추출하는 전문가입니다."),
                ("human", """
                    대화 히스토리와 현재 메시지를 종합하여 SNS 발행 정보를 추출하여 JSON 형태로 반환해주세요.

                    대화 히스토리:
                    {history_context}

                    이전 대화에서 확인된 정보:
                    {context_from_history}

                    현재 메시지: "{message}"
                    현재 날짜: {current_date}

                    추출할 정보:
                    - platform: SNS 플랫폼 (Twitter, Facebook, Instagram, LinkedIn 등)
                    - content: 발행할 내용
                    - scheduled_time: 예약시간 (YYYY-MM-DD HH:MM 형식, 선택사항)
                    - hashtags: 해시태그 (선택사항)
                    - image_url: 이미지 URL (선택사항)

                    SNS 발행 정보가 충분하지 않으면 null을 반환하세요.

                    JSON 형태: {{"platform": "...", "content": "...", "scheduled_time": "...", "hashtags": "...", "image_url": "..."}}
                """)
            ])

            chain = prompt | model | self.json_parser
            result = await chain.ainvoke({
                "message": message,
                "current_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "history_context": history_context,
                "context_from_history": context_from_history
            })

            # 필수 필드 검증
            if result and result.get("platform") and result.get("content"):
                return result
            
            return None

        except Exception as e:
            logger.error(f"히스토리 포함 SNS 정보 추출 실패: {e}")
            return None

    async def extract_email_info(
        self, 
        message: str, 
        conversation_history: List[Dict[str, Any]], 
        context_from_history: str = ""
    ) -> Optional[Dict[str, Any]]:
        """대화 히스토리를 고려한 이메일 정보 추출"""
        try:
            model = self.models.get(self.default_model)
            if not model:
                return None

            # 히스토리 컨텍스트 구성
            history_context = self._format_history_for_llm(conversation_history)

            prompt = ChatPromptTemplate.from_messages([
                ("system", "당신은 대화 히스토리를 고려하여 자연어에서 이메일 정보를 추출하는 전문가입니다."),
                ("human", """
                    대화 히스토리와 현재 메시지를 종합하여 이메일 정보를 추출하여 JSON 형태로 반환해주세요.

                    대화 히스토리:
                    {history_context}

                    이전 대화에서 확인된 정보:
                    {context_from_history}

                    현재 메시지: "{message}"
                    현재 날짜: {current_date}

                    추출할 정보:
                    - to: 받는사람 이메일 주소
                    - subject: 이메일 제목
                    - body: 이메일 본문
                    - scheduled_time: 예약시간 (YYYY-MM-DD HH:MM 형식, 선택사항)
                    - cc: 참조 이메일 주소들 (선택사항)
                    - attachments: 첨부파일 경로들 (선택사항)

                    이메일 정보가 충분하지 않으면 null을 반환하세요.

                    JSON 형태: {{"to": "...", "subject": "...", "body": "...", "scheduled_time": "...", "cc": [...], "attachments": [...]}}
                """)
            ])

            chain = prompt | model | self.json_parser
            result = await chain.ainvoke({
                "message": message,
                "current_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "history_context": history_context,
                "context_from_history": context_from_history
            })

            # 필수 필드 검증
            if result and result.get("to") and result.get("subject") and result.get("body"):
                return result
            
            return None

        except Exception as e:
            logger.error(f"히스토리 포함 이메일 정보 추출 실패: {e}")
            return None

    async def extract_reminder_info(
        self, 
        message: str, 
        conversation_history: List[Dict[str, Any]], 
        context_from_history: str = ""
    ) -> Optional[Dict[str, Any]]:
        """대화 히스토리를 고려한 리마인더 정보 추출"""
        try:
            model = self.models.get(self.default_model)
            if not model:
                return None

            # 히스토리 컨텍스트 구성
            history_context = self._format_history_for_llm(conversation_history)

            prompt = ChatPromptTemplate.from_messages([
                ("system", "당신은 대화 히스토리를 고려하여 자연어에서 리마인더 정보를 추출하는 전문가입니다."),
                ("human", """
                    대화 히스토리와 현재 메시지를 종합하여 리마인더 정보를 추출하여 JSON 형태로 반환해주세요.

                    대화 히스토리:
                    {history_context}

                    이전 대화에서 확인된 정보:
                    {context_from_history}

                    현재 메시지: "{message}"
                    현재 날짜: {current_date}

                    추출할 정보:
                    - title: 리마인더 제목
                    - reminder_time: 알림시간 (YYYY-MM-DD HH:MM 형식)
                    - description: 리마인더 내용 (선택사항)
                    - repeat: 반복 설정 (once, daily, weekly, monthly 중 하나, 선택사항)
                    - advance_notice: 사전알림 (분 단위, 선택사항)

                    리마인더 정보가 충분하지 않으면 null을 반환하세요.

                    JSON 형태: {{"title": "...", "reminder_time": "...", "description": "...", "repeat": "...", "advance_notice": 0}}
                """)
            ])

            chain = prompt | model | self.json_parser
            result = await chain.ainvoke({
                "message": message,
                "current_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "history_context": history_context,
                "context_from_history": context_from_history
            })

            # 필수 필드 검증
            if result and result.get("title") and result.get("reminder_time"):
                return result
            
            return None

        except Exception as e:
            logger.error(f"히스토리 포함 리마인더 정보 추출 실패: {e}")
            return None

    async def extract_message_info(
        self, 
        message: str, 
        conversation_history: List[Dict[str, Any]], 
        context_from_history: str = ""
    ) -> Optional[Dict[str, Any]]:
        """대화 히스토리를 고려한 메시지 정보 추출"""
        try:
            model = self.models.get(self.default_model)
            if not model:
                return None

            # 히스토리 컨텍스트 구성
            history_context = self._format_history_for_llm(conversation_history)

            prompt = ChatPromptTemplate.from_messages([
                ("system", "당신은 대화 히스토리를 고려하여 자연어에서 메시지 정보를 추출하는 전문가입니다."),
                ("human", """
                    대화 히스토리와 현재 메시지를 종합하여 메시지 전송 정보를 추출하여 JSON 형태로 반환해주세요.

                    대화 히스토리:
                    {history_context}

                    이전 대화에서 확인된 정보:
                    {context_from_history}

                    현재 메시지: "{message}"
                    현재 날짜: {current_date}

                    추출할 정보:
                    - platform: 메시지 플랫폼 (SMS, Slack, Teams, KakaoTalk 등)
                    - recipient: 받는사람 (전화번호 또는 사용자명)
                    - content: 메시지 내용
                    - scheduled_time: 예약시간 (YYYY-MM-DD HH:MM 형식, 선택사항)
                    - priority: 우선순위 (high, medium, low 중 하나, 선택사항)

                    메시지 정보가 충분하지 않으면 null을 반환하세요.

                    JSON 형태: {{"platform": "...", "recipient": "...", "content": "...", "scheduled_time": "...", "priority": "..."}}
                """)
            ])

            chain = prompt | model | self.json_parser
            result = await chain.ainvoke({
                "message": message,
                "current_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "history_context": history_context,
                "context_from_history": context_from_history
            })

            # 필수 필드 검증
            if result and result.get("platform") and result.get("recipient") and result.get("content"):
                return result
            
            return None

        except Exception as e:
            logger.error(f"히스토리 포함 메시지 정보 추출 실패: {e}")
            return None
