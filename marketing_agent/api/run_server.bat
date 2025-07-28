@echo off

echo 🚀 마케팅 분석 도구 API 서버 시작 중...

REM 환경 변수 설정
set PYTHONPATH=%PYTHONPATH%;%cd%\..

REM FastAPI 서버 실행
echo 📡 FastAPI 서버를 8000번 포트에서 실행합니다...
echo 📖 API 문서: http://localhost:8000/docs
echo 🔍 API 상태: http://localhost:8000/health

uvicorn marketing_api:app --host 0.0.0.0 --port 8000 --reload --log-level info

pause
