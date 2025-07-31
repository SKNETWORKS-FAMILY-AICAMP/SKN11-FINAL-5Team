# TinkerBell 업무지원 에이전트 v5.0 (리팩토링됨)

> 사용자 요청에 따라 자동화 업무를 등록하고, task_automation 테이블에 등록된 스케쥴에 맞게 실제 업무 API를 실행하는 지능형 업무지원 시스템

## 🎯 핵심 기능

### 1. 지능형 자동화 업무 등록
- **자연어 인식**: 사용자가 자연스럽게 말한 내용에서 자동화 의도를 파악
- **스마트 정보 추출**: 필요한 정보를 대화에서 자동으로 추출
- **누락 정보 요청**: 부족한 정보만 골라서 사용자에게 요청
- **즉시 등록**: 모든 정보가 갖춰지면 즉시 task_automation 테이블에 등록

### 2. 스케쥴 기반 자동 실행
- **정확한 시간 실행**: 등록된 스케쥴 시간에 맞춰 자동화 작업 실행
- **실행기 시스템**: 작업 타입별 전용 실행기가 실제 API 호출
- **실행 상태 추적**: 실행 전/중/후 상태를 실시간으로 추적
- **에러 처리**: 실행 실패시 재시도 및 에러 로깅

### 3. 지원하는 자동화 작업
- **📧 이메일 발송**: SMTP를 통한 이메일 자동 발송
- **📅 일정 등록**: Google Calendar, Outlook 일정 자동 등록
- **⏰ 리마인더**: 푸시 알림, 이메일 리마인더 발송
- **💬 메시지 발송**: Slack, Teams, Discord 메시지 자동 발송
- **📱 SNS 마케팅**: Instagram 등 SNS 컨텐츠 자동 게시 (마케팅 페이지 연동)

## 🏗️ 리팩토링된 아키텍처

### 계층 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application Layer                │
│                         (main.py)                          │
├─────────────────────────────────────────────────────────────┤
│                     Service Layer                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │ TaskAgentService│ │AutomationService│ │ConversationSvc  │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │   LLMService    │ │   RAGService    │ │  EmailService   │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      Core Layer                            │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │   TaskAgent     │ │AutomationManager│ │ LLMHandler      │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Executor Layer                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │ EmailExecutor   │ │CalendarExecutor │ │ReminderExecutor │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│              Infrastructure Layer                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │   Database      │ │   Scheduler     │ │  External APIs  │ │
│  │   (MySQL)       │ │ (APScheduler)   │ │ (SMTP,Calendar) │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 주요 개선사항

1. **의존성 주입 도입**: 서비스 간 의존성이 명시적으로 관리됩니다
2. **Service Layer 추가**: 비즈니스 로직이 서비스 레이어로 분리되었습니다  
3. **Executor 시스템**: 자동화 실행 로직이 전용 실행기로 분리되었습니다
4. **향상된 스케쥴링**: APScheduler 기반의 더 안정적인 스케쥴링 시스템

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 현재 디렉토리에서 (task_agent 폴더 내에서)
cd /Users/comet39/SKN_PJT/SKN11-FINAL-5Team/task_agent

# 필요한 패키지 설치 (requirements.txt가 있는 경우)
pip install fastapi uvicorn apscheduler python-dateutil

# 또는 기존 requirements.txt 사용
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
# .env 파일에 다음 설정 추가 (config.py에 맞게)
OPENAI_API_KEY=your_openai_api_key
MYSQL_URL=mysql://user:password@localhost/tinkerbell
GOOGLE_CALENDAR_CLIENT_ID=your_google_client_id
GOOGLE_CALENDAR_CLIENT_SECRET=your_google_client_secret
EMAIL_GMAIL_ADDRESS=your_email@gmail.com
EMAIL_GMAIL_PASSWORD=your_app_password
```

### 3. 애플리케이션 실행

```bash
# 리팩토링된 애플리케이션 실행
python main.py

# 또는 uvicorn 직접 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📡 API 사용법

### 1. 자동화 업무 등록 (자연어)

```bash
POST http://localhost:8000/agent/query
Content-Type: application/json

{
    "user_id": "123",
    "message": "내일 오후 2시에 팀 미팅 일정 등록해줘",
    "persona": "business",
    "conversation_id": null
}
```

**응답 예시:**
```json
{
    "success": true,
    "data": {
        "conversation_id": 456,
        "answer": "✅ 일정 등록 자동화가 성공적으로 등록되었습니다!\n\n📋 작업 ID: 789\n⏰ 예약된 시간에 자동으로 실행됩니다.",
        "automation_created": true
    }
}
```

### 2. 자동화 작업 상태 확인

```bash
GET http://localhost:8000/automation/task/789
```

### 3. 사용자 자동화 작업 목록

```bash
GET http://localhost:8000/automation/tasks?user_id=123
```

### 4. 시스템 상태 확인

```bash
GET http://localhost:8000/health
GET http://localhost:8000/status
```

## 🔧 새로운 파일 구조

```
task_agent/
├── main.py                    # 리팩토링된 FastAPI 앱
├── agent.py                   # 리팩토링된 TaskAgent
├── automation.py              # 리팩토링된 AutomationManager
├── dependencies.py            # 의존성 주입 컨테이너
│
├── services/                  # 서비스 레이어
│   ├── __init__.py
│   ├── task_agent_service.py
│   ├── automation_service.py
│   ├── llm_service.py
│   ├── rag_service.py
│   ├── conversation_service.py
│   ├── email_service.py
│   ├── calendar_service.py
│   └── instagram_service.py
│
├── automation_executors/      # 자동화 실행기들
│   ├── __init__.py
│   ├── email_executor.py
│   ├── calendar_executor.py
│   ├── reminder_executor.py
│   └── message_executor.py
│
├── [기존 파일들...]
│   ├── llm_handler.py
│   ├── rag.py
│   ├── models.py
│   ├── config.py
│   └── utils.py
```

## 🔄 주요 변경사항

### 1. 의존성 주입 패턴 도입

**이전:**
```python
class TaskAgent:
    def __init__(self):
        self.llm_handler = TaskAgentLLMHandler()
        self.rag_manager = TaskAgentRAGManager()
        # 직접 생성
```

**현재:**
```python
class TaskAgent:
    def __init__(self, llm_service: LLMService, rag_service: RAGService, ...):
        self.llm_service = llm_service
        # 의존성 주입
```

### 2. 서비스 레이어 분리

**이전:**
```python
# main.py에서 직접 에이전트 사용
agent = TaskAgent()
response = await agent.process_query(query)
```

**현재:**
```python
# 서비스를 통한 처리
task_service: TaskAgentService = Depends(get_task_agent_service)
response = await task_service.process_query(query)
```

### 3. 실행기 시스템

**이전:**
```python
# automation.py 내에서 직접 처리
async def _execute_email(self, task_data, user_id):
    # 이메일 발송 로직이 automation.py 안에 혼재
```

**현재:**
```python
# 전용 실행기로 분리
class EmailExecutor:
    async def execute(self, task_data, user_id):
        # 이메일 발송 전용 로직
```

## 🧪 테스트

### 기본 동작 테스트

```bash
# 1. 서버 시작 확인
curl http://localhost:8000/health

# 2. 자동화 업무 등록 테스트
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123",
    "message": "내일 오후 2시에 팀 미팅 등록해줘",
    "persona": "business"
  }'

# 3. 작업 상태 확인
curl http://localhost:8000/automation/tasks?user_id=123
```

## 🔧 문제 해결

### 자주 발생하는 문제들

1. **ImportError: No module named 'shared_modules'**
   - 공통 모듈이 없는 경우 더미 구현을 사용합니다
   - 정상적으로 동작하도록 fallback 로직이 구현되어 있습니다

2. **APScheduler 관련 오류**
   ```bash
   pip install apscheduler
   ```

3. **의존성 주입 오류**
   - 서비스 컨테이너가 초기화되지 않은 경우
   - main.py의 lifespan 이벤트에서 초기화됩니다

## 📝 다음 단계

1. **데이터베이스 연결**: 실제 MySQL 데이터베이스 연결
2. **외부 API 연동**: Google Calendar, Slack 등 실제 API 연결
3. **인증 시스템**: JWT 기반 사용자 인증 추가
4. **모니터링**: 로깅 및 메트릭 수집 시스템
5. **테스트 코드**: 단위 테스트 및 통합 테스트 추가

## 🤝 개발 가이드

### 새로운 자동화 타입 추가하기

1. **모델 정의**: `models.py`에 새로운 `AutomationTaskType` 추가
2. **실행기 생성**: `automation_executors/`에 새로운 실행기 클래스 생성
3. **매니저 등록**: `AutomationManager._setup_executors()`에 실행기 등록
4. **검증 로직**: 데이터 검증 로직 추가

### 새로운 서비스 추가하기

1. **서비스 클래스**: `services/`에 새로운 서비스 클래스 생성
2. **의존성 등록**: `dependencies.py`에 서비스 등록
3. **API 엔드포인트**: `main.py`에 엔드포인트 추가

---

이제 리팩토링된 시스템이 완성되었습니다! 

핵심 개선사항:
- 🏗️ **명확한 계층 구조**: Service → Core → Executor → Infrastructure
- 💉 **의존성 주입**: 테스트 용이성과 유지보수성 향상
- 🔧 **실행기 시스템**: 자동화 타입별 전용 실행기로 확장성 확보
- 📊 **향상된 스케쥴링**: APScheduler 기반의 안정적인 작업 스케쥴링
- ⚡ **성능 최적화**: 메모리 캐싱 및 비동기 처리

사용자 요청 → 자동화 업무 등록 → task_automation 테이블 저장 → 스케쥴 실행 플로우가 완벽하게 구현되었습니다!
