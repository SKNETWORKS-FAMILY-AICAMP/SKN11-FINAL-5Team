#!/bin/bash

# 마케팅 에이전트 데모 실행 스크립트

echo "🎬 마케팅 에이전트 데모 시작!"

# 환경변수 확인
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다"
    echo "다음 명령어로 설정해주세요:"
    echo "export OPENAI_API_KEY='your-api-key-here'"
    exit 1
fi

# 의존성 확인
python3 -c "import openai" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️ 의존성이 설치되지 않았습니다. 설치 중..."
    pip install -r requirements.txt
fi

# 데모 실행
echo "🚀 데모 시작 중..."
python3 demo.py
