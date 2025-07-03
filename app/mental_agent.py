import os
import threading
from datetime import datetime
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
import openai

from sqlalchemy.orm import Session
from app.crud import (
    create_message, get_conversation_history,
    save_or_update_phq9_result, get_latest_phq9_by_user
)

from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

embedding = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma(
    collection_name="global-documents",
    embedding_function=embedding,
    persist_directory="D:/penta/data/vector_db"
)

answer_prompt = PromptTemplate(
    input_variables=["context", "question", "chat_history"],
    template="""
당신은 친절하고 공감하는 멘탈 건강 상담사입니다.
아래 이전 대화 내용, 상담 기록, 참고 내용을 종합적으로 고려하여 사용자 질문에 대해 친절하고 이해하기 쉽게 답변해 주세요.
특히 이전 대화에서 언급된 PHQ-9 점수, 감정 상태, 개인적 상황 등을 기억하고 연속성 있는 상담을 제공하세요.
상담자가 우울함을 표시하고 있다면 공감을 표하고 PHQ-9 설문을 제안하세요. 단 PHQ-9 설문 제안은 1회에 한해서만 하세요.
PHQ-9 점수에 따라 적절한 조치를 안내하세요.
상담 기록 및 참고 내용에 실명이 들어가 있다면 무시해줘.

이전 대화 내용:
{chat_history}

상담 기록 및 참고 내용:
{context}

사용자 질문:
{question}

답변:
"""
)

LLM_POOL = {
    "openai": ChatOpenAI(
        model="gpt-4o-mini", 
        temperature=0.7, 
        api_key=OPENAI_API_KEY
        ),
    "gemini": ChatGoogleGenerativeAI(
        google_api_key=GEMINI_API_KEY,
        model="gemini-1.5-flash-latest",
        temperature=0.7,
    )
}
llm_call_count = 0
llm_lock = threading.Lock()

def get_llm_choice():
    global llm_call_count
    with llm_lock:
        use_gemini = (llm_call_count % 5 == 4)
        llm_call_count += 1
    return "gemini" if use_gemini else "openai"

def get_fallback_llm_name(current_llm_name):
    return "gemini" if current_llm_name == "openai" else "openai"

def analyze_emotion(text: str) -> str:
    prompt = (
        f"다음 사용자의 감정을 하나의 단어로 요약해 주세요. "
        f"가능한 값: 긍정, 중립, 슬픔, 우울, 불안, 분노, 행복, 기타.\n"
        f"텍스트: \"{text}\"\n"
        f"감정:"
    )
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 감정분석가입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"감정 분석 오류: {e}")
        return "중립"

def is_depressed_emotion(emotion: str) -> bool:
    return any(keyword in emotion for keyword in ["우울"])

def get_user_context_from_db(db: Session, user_id: int):
    phq9 = get_latest_phq9_by_user(db, user_id)
    context_parts = []
    if phq9:
        context_parts.append(
            f"PHQ-9 점수: {phq9.score}점 ({phq9.level}, {phq9.updated_at.strftime('%Y-%m-%d %H:%M')})"
        )
    return "\n".join(context_parts) if context_parts else "이전 세션 정보 없음"

def extract_and_save_phq9(db: Session, user_id: int, conversation_id: int, text: str):
    import re
    phq9_patterns = [
        r'PHQ.*?(\d+)점',
        r'점수.*?(\d+)',
        r'(\d+)점',
        r'총.*?(\d+)',
    ]
    for pattern in phq9_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            score = int(match)
            if 0 <= score <= 27:
                if score <= 4:
                    level = "정상"
                elif score <= 9:
                    level = "경미한 우울"
                elif score <= 14:
                    level = "중등도 우울"
                elif score <= 19:
                    level = "중증 우울"
                else:
                    level = "매우 심한 우울"
                save_or_update_phq9_result(db, user_id, score, level)
                return (score, level)
    return (None, None)

def load_phq9_markdown():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    phq9_path = os.path.join(base_dir, "data", "PHQ-9.txt")
    try:
        with open(phq9_path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "PHQ-9 설문지 파일을 찾을 수 없습니다."
