@echo off

REM 마케팅 에이전트 서버 시작 스크립트 (Windows)

echo 🚀 마케팅 에이전트 서버 시작 중...

REM 환경변수 확인
if "%OPENAI_API_KEY%"=="" (
    echo ❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다
    echo 다음 명령어로 설정해주세요:
    echo set OPENAI_API_KEY=your-api-key-here
    pause
    exit /b 1
)

REM 의존성 설치 확인
echo 📦 의존성 확인 중...
python -c "import fastapi, uvicorn, openai" 2>nul
if errorlevel 1 (
    echo ⚠️ 의존성이 설치되지 않았습니다. 설치 중...
    pip install -r requirements.txt
)

REM 서버 시작
echo 🌟 서버 시작 중...
python main.py

pause
