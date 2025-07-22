# 🚀 빠른 시작 가이드

마케팅 자동화 API를 5분 안에 실행해보세요!

## ⚡ 즉시 시작하기

### 1. 저장소 클론
```bash
cd /Users/comet39/SKN_PJT/SKN11-FINAL-5Team/task_agent/automation_task/marketing
```

### 2. 초기 설정
```bash
# 파이썬 가상환경 생성
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# 의존성 설치 및 초기 설정
python run.py install
python run.py setup
```

### 3. 환경변수 설정 (최소한)
`.env` 파일을 열고 다음 값들을 설정하세요:

```bash
# 기본 설정만으로도 테스트 가능
DEBUG=true
USE_MOCK_APIS=true

# 실제 API 사용시 (선택사항)
# NAVER_CLIENT_ID=your_naver_client_id
# NAVER_CLIENT_SECRET=your_naver_client_secret
# OPENAI_API_KEY=your_openai_api_key
```

### 4. 서버 실행
```bash
python run.py dev
```

🎉 **완료!** 브라우저에서 http://localhost:8000/docs 에서 API 문서를 확인하세요.

## 📋 기본 테스트

### API 상태 확인
```bash
curl http://localhost:8000/
```

### 키워드 분석 테스트
```bash
curl -X POST "http://localhost:8000/keywords/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "마케팅 자동화",
    "platform": "naver"
  }'
```

### 블로그 콘텐츠 생성 테스트
```bash
curl -X POST "http://localhost:8000/blog/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "AI 마케팅",
    "auto_upload": false
  }'
```

## 🔧 간단 설정

### 블로그 자동화 활성화
```python
import requests

config = {
    "enabled": True,
    "keywords": ["마케팅", "AI", "자동화"],
    "schedule": {
        "frequency": "daily",
        "time": "09:00"
    },
    "auto_publish": False
}

response = requests.post("http://localhost:8000/blog/setup", json=config)
print(response.json())
```

### 인스타그램 자동화 활성화
```python
config = {
    "enabled": True,
    "hashtags": ["#마케팅", "#AI", "#비즈니스"],
    "schedule": {
        "frequency": "daily", 
        "time": "12:00"
    },
    "auto_post": False
}

response = requests.post("http://localhost:8000/instagram/setup", json=config)
print(response.json())
```

## 🐳 Docker로 실행하기

### 1. Docker Compose 사용
```bash
# 전체 스택 실행 (PostgreSQL, Redis 포함)
docker-compose up -d

# 로그 확인
docker-compose logs -f marketing-api
```

### 2. 단독 실행
```bash
# Docker 이미지 빌드
docker build -t marketing-automation .

# 컨테이너 실행
docker run -p 8000:8000 \
  -e DEBUG=true \
  -e USE_MOCK_APIS=true \
  marketing-automation
```

## 📊 대시보드 확인

### 자동화 상태
- http://localhost:8000/dashboard/overview

### 스케줄된 작업
- http://localhost:8000/scheduler/jobs

### API 문서
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## 🔥 실제 API 키 설정하기

실제 서비스를 사용하려면 다음 API 키들을 발급받으세요:

### 네이버 검색 API
1. https://developers.naver.com/ 접속
2. 애플리케이션 등록
3. 검색 API 권한 활성화
4. `.env`에 추가:
   ```bash
   NAVER_CLIENT_ID=your_client_id
   NAVER_CLIENT_SECRET=your_client_secret
   ```

### OpenAI API (콘텐츠 생성)
1. https://platform.openai.com/ 접속
2. API 키 생성
3. `.env`에 추가:
   ```bash
   OPENAI_API_KEY=your_openai_key
   ```

### Instagram API (포스팅)
1. https://developers.facebook.com/ 접속
2. 앱 생성 및 Instagram Basic Display 설정
3. `.env`에 추가:
   ```bash
   INSTAGRAM_ACCESS_TOKEN=your_access_token
   ```

## ⚡ 주요 명령어

```bash
# 상태 확인
python run.py status

# 개발 서버 (자동 재시작)
python run.py dev

# 프로덕션 서버
python run.py prod --workers 4

# 데이터베이스 초기화
python run.py migrate

# 테스트 실행
python run.py test
```

## 🆘 문제 해결

### 포트 충돌
```bash
python run.py dev --port 8001
```

### 패키지 설치 오류
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### 데이터베이스 연결 오류
```bash
# SQLite 사용 (기본값)
# DATABASE_URL 설정을 제거하면 자동으로 SQLite 사용

# PostgreSQL 사용
docker run -d --name postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=marketing_automation \
  -p 5432:5432 postgres:14
```

### 로그 확인
```bash
# 실시간 로그
tail -f logs/marketing_automation_$(date +%Y-%m-%d).log

# 에러 로그만
tail -f logs/marketing_automation_errors.log
```

## 🎯 다음 단계

1. **커스텀 템플릿 작성**: 블로그 글 템플릿을 수정하여 브랜드에 맞는 콘텐츠 생성
2. **스케줄 최적화**: 타겟 오디언스의 활동 시간에 맞춰 포스팅 시간 조정
3. **성과 분석**: 생성된 콘텐츠의 성과를 분석하여 키워드와 해시태그 최적화
4. **자동화 확장**: 추가 플랫폼(유튜브, 페이스북 등) 연동

## 💡 유용한 팁

- **개발 모드**에서는 `USE_MOCK_APIS=true`로 설정하여 실제 API 호출 없이 테스트
- **스케줄러**는 서버가 실행 중일 때만 작동
- **데이터베이스**는 SQLite(개발용)와 PostgreSQL(프로덕션용) 모두 지원
- **로그 레벨**을 `DEBUG`로 설정하면 더 자세한 정보 확인 가능

더 자세한 내용은 [README.md](README.md)를 참조하세요! 🚀
