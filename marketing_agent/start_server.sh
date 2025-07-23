#!/bin/bash

# 마케팅 에이전트 서버 시작 스크립트

echo "🚀 마케팅 에이전트 서버 시작 중..."

# 환경변수 확인
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다"
    echo "다음 명령어로 설정해주세요:"
    echo "export OPENAI_API_KEY='your-api-key-here'"
    exit 1
fi

# 의존성 설치 확인
echo "📦 의존성 확인 중..."
python3 -c "import fastapi, uvicorn, openai" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️ 의존성이 설치되지 않았습니다. 설치 중..."
    pip install -r requirements.txt
fi

# 서버 시작
echo "🌟 서버 시작 중..."
python3 main.py
