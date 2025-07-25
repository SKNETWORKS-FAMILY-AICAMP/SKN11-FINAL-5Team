import logging
from typing import Dict, Any, Optional, List, Union, AsyncGenerator
import openai
from openai import AsyncOpenAI
import google.generativeai as genai
import json
from langchain_openai import ChatOpenAI
import asyncio
import time
import os
from config import settings

logger = logging.getLogger(__name__)

class LLM:
    """한국어 비즈니스 컨설팅을 위한 LLM 모듈"""
    
    def __init__(self, model_name: Optional[str] = None):
        
        if model_name:
            self.model_name = model_name
        else:
            # 기본 모델 설정 (settings에 없을 경우 대비)
            self.model_name = getattr(settings, 'DEFAULT_LLM_MODEL', 'gpt-3.5-turbo')
        
        # OpenAI 초기화
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=60.0,  # 60초 타임아웃
                max_retries=3  # 최대 3회 재시도
            )
        
        # Gemini 초기화 (API 키가 있는 경우)
        if hasattr(settings, 'GOOGLE_API_KEY') and settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        # 번역기 초기화 (OpenAI 기반)
        self.translator = ChatOpenAI(
            model="gpt-3.5-turbo", 
            temperature=0, 
            openai_api_key=settings.OPENAI_API_KEY
        )
    
    async def generate_with_translation(
        self,
        query: str,
        context: str,
        references: List[Dict[str, Any]],
        translate_to_korean: bool = True,
        history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        persona: Optional[str] = None
    ) -> str:
        """비즈니스 컨설팅 응답 생성 후 한국어로 번역"""
        
        # 비즈니스 컨설팅에 맞는 시스템 프롬프트
        if not system_prompt:
            # 페르소나에 따른 시스템 프롬프트 설정
            if persona == "e_commerce":
                system_prompt = """당신은 이커머스 창업 전문 컨설턴트입니다.
온라인 쇼핑몰 창업, 마케팅, 비즈니스 모델, 운영 전략 등에 대한 전문적인 조언을 제공합니다.
실용적이고 구체적인 답변을 제공하며, 업계 베스트 프랙티스를 바탕으로 도움을 줍니다."""
            elif persona == "beautyshop":
                system_prompt = """당신은 뷰티샵 창업 전문 컨설턴트입니다.
뷰티샵 사업 계획, 인테리어 디자인, 고객 관리, 마케팅 전략 등에 대한 전문적인 조언을 제공합니다.
실용적이고 구체적인 답변을 제공하며, 뷰티 업계의 베스트 프랙티스를 바탕으로 도움을 줍니다."""
            elif persona == "creator":
                system_prompt = """당신은 콘텐츠 크리에이터 비즈니스 전문 컨설턴트입니다.
YouTube, 인스타그램, 오디오 플랫폼 등에서의 콘텐츠 제작, 수익 창출, 팬덤 관리 등에 대한 전문적인 조언을 제공합니다.
실용적이고 구체적인 답변을 제공하며, 콘텐츠 제작자에게 도움이 되는 실질적인 조언을 드립니다."""
            else:  # common or default
                system_prompt = """당신은 비즈니스 컨설턴트입니다.
창업, 사업 계획, 마케팅, 경영 전략, 사업자 등록 등 다양한 비즈니스 영역에 대한 전문적인 조언을 제공합니다.
실용적이고 구체적인 답변을 제공하며, 한국의 비즈니스 환경에 맞는 조언을 드립니다."""
            
            system_prompt += """

중요한 가이드라인:
1. "콘텍스트에 따르면" 또는 "제공된 정보에 따라" 같은 표현을 절대 사용하지 마세요
2. 자연스럽고 자신있게 답변하세요
3. 대화체로 친근하게 소통하세요
4. 구체적인 정보가 있으면 자신있게 공유하세요
5. 구체적인 정보가 없으면 일반적이지만 도움이 되는 조언을 제공하세요

기억하세요: 당신은 비즈니스 도움이 필요한 창업자와 자연스러운 대화를 나누고 있습니다."""
        
        # 이전 대화 기록이 있는 경우 컨텍스트에 포함
        messages = [{"role": "system", "content": system_prompt}]
        
        # history 추가 (이미 번역된 상태로 전달됨)
        if history and isinstance(history, list) and len(history) > 0:
            messages.extend(history)
        
        # 참조 정보 처리 - 새로운 메타데이터 구조 사용
        reference_info = ""
        if references and len(references) > 0:
            reference_info += "\\n\\n참조 문서 정보:\\n"
            for i, ref in enumerate(references[:3]):  # 최대 3개 참조
                topic = ref.get('topic', 'Unknown')
                persona_ref = ref.get('persona', 'Unknown')
                source = ref.get('source', 'Unknown')
                reference_info += f"- 문서 {i+1}: {topic} (페르소나: {persona_ref}, 출처: {source})\\n"
        
        # 새로운 사용자 질문 추가
        if context and context.strip():
            user_prompt = f"""질문: {query}

관련 정보:
{context}{reference_info}

위 질문에 대해 자연스럽고 도움이 되는 답변을 제공해주세요."""
        else:
            user_prompt = f"""질문: {query}{reference_info}

이 질문에 대해 도움이 되는 답변을 제공해주세요."""
            
        messages.append({"role": "user", "content": user_prompt})

        # LLM 응답 생성
        if self.model_name.startswith("gpt-"):
            try:
                response = await self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.7,  # 약간의 창의성 허용
                    max_tokens=1000
                )
                answer = response.choices[0].message.content
                
            except openai.RateLimitError as e:
                logger.warning(f"Rate limit reached: {e}")
                await asyncio.sleep(5)  # 5초 대기 후 재시도
                response = await self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                answer = response.choices[0].message.content
                
            except openai.APIStatusError as e:
                logger.error(f"OpenAI API error: {e}")
                if e.status_code == 500:
                    # 500 오류의 경우 대체 모델 사용
                    logger.warning("Falling back to gpt-3.5-turbo due to 500 error")
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=1000
                    )
                    answer = response.choices[0].message.content
                else:
                    raise
                    
        elif self.model_name.startswith("gemini-"):
            # Gemini 모델 처리
            history_text = ""
            if history and isinstance(history, list) and len(history) > 0:
                for h in history:
                    if h['role'] == 'user':
                        history_text += f"User: {h['content']}\\n"
                    elif h['role'] == 'assistant':
                        history_text += f"Assistant: {h['content']}\\n"
                history_text += "\\n"
                
            full_prompt = f"{system_prompt}\\n\\n{history_text}User: {user_prompt}\\nAssistant:"
            
            try:
                model = genai.GenerativeModel(self.model_name)
                response = model.generate_content(full_prompt)
                answer = response.text
            except Exception as e:
                logger.error(f"Gemini API error: {e}")
                # Gemini 오류 시 OpenAI로 폴백
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                answer = response.choices[0].message.content
        else:
            # 기본적으로 OpenAI 사용
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            answer = response.choices[0].message.content

        # 한국어로 번역 (이미 한국어 대화이므로 translate_to_korean=False로 설정 가능)
        if translate_to_korean:
            try:
                # 응답이 이미 한국어인지 체크
                if any(ord(char) >= 0xAC00 and ord(char) <= 0xD7A3 for char in answer[:50]):
                    # 이미 한국어 포함되어 있으면 번역 스킵
                    return answer
                    
                # 영어 응답을 한국어로 번역
                translate_prompt = f"다음 텍스트를 한국어로 번역해주세요. 자연스럽고 대화체로 작성하며, 번역투가 아닌 자연스러운 한국어로 만들어주세요. 의미는 그대로 유지해주세요:\\n\\n{answer}"
                
                translated_answer = self.translator.invoke(translate_prompt)
                return translated_answer.content
            except Exception as e:
                logger.error(f"Translation error: {e}")
                return answer
        
        return answer
    
    async def generate(
        self,
        query: str,
        context: str = "",
        references: List[Dict[str, Any]] = None,
        stream: bool = False,
        persona: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Union[str, AsyncGenerator[Dict[str, Any], None]]:
        """비즈니스 컨설팅 응답 생성"""
        # 한국어 번역 기능 통합
        return await self.generate_with_translation(
            query=query,
            context=context,
            references=references or [],
            translate_to_korean=True,
            persona=persona,
            history=history
        )

async def test_llm():
    """LLM 모듈 테스트 함수"""
    try:
        from rag import RAG
        
        # RAG와 LLM 인스턴스 생성
        rag = RAG()
        llm = LLM()
        
        # 테스트 질문
        query = "사업자 등록은 어떻게 해야 하나요?"
        
        print(f"테스트 질문: {query}")
        print("=" * 50)
        
        try:
            # RAG에서 검색
            context, references = rag.search_with_translation(query, persona="beautyshop")
            print(f"Context: {context[:200] if context else 'None'}...")  # 처음 200자만 출력
            print(f"References: {len(references)}개 문서 참조")
            print("=" * 50)
            
        except Exception as rag_error:
            print(f"RAG 검색 오류: {rag_error}")
            # RAG 오류 시 빈 컨텍스트로 진행
            context = ""
            references = []
        
        # LLM으로 응답 생성
        response = await llm.generate(
            query=query,
            context=context,
            references=references,
            persona="common"
        )
        
        print("생성된 응답:")
        print(response)
        
    except ImportError:
        print("RAG 모듈을 불러올 수 없습니다. LLM 단독 테스트를 진행합니다.")
        
        # LLM 단독 테스트
        llm = LLM()
        query = "사업자 등록은 어떻게 해야 하나요?"
        
        response = await llm.generate(
            query=query,
            context="",
            references=[],
            persona="common"
        )
        
        print("LLM 단독 테스트 응답:")
        print(response)
        
    except Exception as e:
        print(f"테스트 오류: {e}")
        print(f"오류 타입: {type(e)}")
        import traceback
        print("상세 오류:")
        traceback.print_exc()

def main():
    """메인 함수"""
    print("=== 비즈니스 컨설팅 LLM 모듈 테스트 ===")
    asyncio.run(test_llm())

if __name__ == "__main__":
    main()
