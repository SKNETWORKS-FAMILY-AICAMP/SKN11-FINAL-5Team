# SKN11 Final Project - MCP 연동 에이전트 시스템

## 📋 프로젝트 개요

이 프로젝트는 **사업기획**, **마케팅**, **업무지원** 세 가지 전문 에이전트가 MCP(Model Context Protocol) 서버를 통해 외부 도구들과 연동하여 완전한 비즈니스 워크플로우를 자동화하는 시스템입니다.

### 🎯 핵심 기능

- **🏢 사업기획 에이전트**: 트렌드 분석 → 시장 조사 → 린캔버스 생성 → 문서화
- **📱 마케팅 에이전트**: 콘텐츠 생성 → 캠페인 기획 → 자동 포스팅 → 성과 분석  
- **📋 업무지원 에이전트**: 프로젝트 분해 → 태스크 관리 → 일정 관리 → 자동화

## 🏗 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  사업기획 에이전트  │    │   마케팅 에이전트   │    │  업무지원 에이전트  │
│      MCP 서버     │    │      MCP 서버     │    │      MCP 서버     │
│    Port: 3001    │    │    Port: 3002    │    │    Port: 3003    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    외부 MCP 서버 연동                          │
├─────────────────────────────────────────────────────────────┤
│ • Search MCP        • Vibe Marketing    • Task Manager      │
│ • Lean Canvas MCP   • Meta Scheduler    • Calendar MCP      │  
│ • Notion MCP        • Buffer MCP        • GSuite MCP        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone [repository-url]
cd SKN11-FINAL-5Team

# 환경 설정 실행
chmod +x setup.sh
./setup.sh
```

### 2. 모든 서버 시작

```bash
# 모든 MCP 서버 시작
./start_all_servers.sh
```

### 3. 워크플로우 테스트

```bash
# 통합 워크플로우 테스트
./test_workflow.sh
```

### 4. 서버 종료

```bash
# 모든 서버 안전하게 종료
./stop_all_servers.sh
```

## 📊 에이전트별 상세 기능

### 🏢 사업기획 에이전트 (Port: 3001)

#### 🔧 주요 도구
- `trend_search_with_mcp`: 외부 검색 MCP를 활용한 트렌드 분석
- `market_analysis`: 시장 규모 및 경쟁사 분석
- `generate_lean_canvas_with_mcp`: 외부 MCP를 활용한 린캔버스 생성
- `save_to_notion`: Notion에 사업계획서 자동 저장
- `comprehensive_business_workflow`: 전체 워크플로우 자동 실행

#### 🔗 연동 외부 MCP
- **Search MCP**: 트렌드 및 시장 데이터 검색
- **Lean Canvas MCP**: 비즈니스 모델 구조화
- **Notion MCP**: 문서 자동 저장 및 관리

#### 📋 워크플로우 예시
```
사용자 입력: "AI 콘텐츠 자동화 서비스 창업하고 싶어"
    ↓
1. 트렌드 검색 → 2025년 AI 서비스 트렌드 분석
    ↓
2. 시장 분석 → 시장 규모, 경쟁사, 고객 분석
    ↓
3. 린캔버스 생성 → 비즈니스 모델 구조화
    ↓
4. Notion 저장 → 완성된 사업계획서 자동 저장
```

### 📱 마케팅 에이전트 (Port: 3002)

#### 🔧 주요 도구
- `marketing_workflow`: 전체 마케팅 워크플로우 자동 실행
- `generate_vibe_content`: Vibe Marketing MCP로 매력적인 콘텐츠 생성
- `schedule_social_post`: 소셜 미디어 자동 포스팅 스케줄링
- `analyze_content_performance`: 콘텐츠 성과 분석 및 최적화
- `create_campaign_strategy`: 마케팅 캠페인 전략 수립
- `optimize_posting_schedule`: 최적 포스팅 시간 분석

#### 🔗 연동 외부 MCP
- **Vibe Marketing MCP**: 플랫폼별 매력적인 콘텐츠 생성
- **Meta Post Scheduler MCP**: 자동 포스팅 및 스케줄링

#### 📋 워크플로우 예시
```
사용자 입력: "신제품 출시 마케팅 콘텐츠 만들어줘"
    ↓
1. 제품 분석 → 마케팅 포인트 추출
    ↓
2. Vibe 콘텐츠 생성 → 플랫폼 최적화된 매력적인 콘텐츠
    ↓
3. 자동 포스팅 → 최적 시간에 예약 포스팅
    ↓
4. 성과 추적 → 인게이지먼트 모니터링
```

### 📋 업무지원 에이전트 (Port: 3003)

#### 🔧 주요 도구
- `project_workflow`: 전체 프로젝트 관리 워크플로우 자동 실행
- `break_down_project_with_mcp`: 외부 MCP를 활용한 프로젝트 태스크 분해
- `register_tasks_to_manager`: 태스크 매니저에 업무 등록
- `schedule_to_calendar_mcp`: Google Calendar 일정 자동 등록
- `sync_calendar_with_tasks`: 태스크와 캘린더 양방향 동기화
- `generate_project_report`: 프로젝트 진행 상황 보고서 생성
- `set_automated_reminders`: 스마트 리마인더 자동 설정

#### 🔗 연동 외부 MCP
- **Task Manager MCP**: 프로젝트 태스크 관리
- **Task Queue MCP**: 백업 태스크 큐 시스템
- **Calendar MCP**: Google Calendar 연동
- **GSuite MCP**: Google Workspace 통합 관리

#### 📋 워크플로우 예시
```
사용자 입력: "신제품 개발 프로젝트 관리해줘"
    ↓
1. 프로젝트 분해 → 실행 가능한 태스크로 분해
    ↓
2. 태스크 등록 → 매니저에 우선순위별 등록
    ↓
3. 캘린더 연동 → Google Calendar 일정 자동 생성
    ↓
4. 리마인더 설정 → 자동 알림 및 진행 체크
```

## 🎯 통합 시나리오 예시

### 카페 창업 프로젝트 전체 워크플로우

```
1️⃣ 사업기획 에이전트
   사용자: "카페 창업 준비 전체적으로 도와줘"
   → 시장 조사 및 트렌드 분석
   → Notion MCP: 사업계획서 생성
   → Google Drive MCP: 계획서 저장
   → Airtable MCP: 프로젝트 추적 테이블 생성

2️⃣ 업무지원 에이전트
   → Asana MCP: 창업 준비 프로젝트 생성
   → Google Calendar MCP: 단계별 일정 등록
   → 자동 리마인더: 마일스톤 알림 설정

3️⃣ 마케팅 에이전트
   → Buffer MCP: 런칭 전 SNS 콘텐츠 예약
   → Mailchimp MCP: 오픈 전 이메일 캠페인 준비
   → Meta Scheduler: 오픈 당일 자동 포스팅

결과: 사업 계획서 → 실행 일정 → 마케팅 준비까지 원스톱 자동화
```

## 📁 프로젝트 구조

```
SKN11-FINAL-5Team/
├── buisness_planning_agent/
│   └── mcp_server/
│       ├── server.py                 # 사업기획 MCP 서버
│       ├── requirements.txt          # 의존성 패키지
│       └── run_server.sh            # 실행 스크립트
├── marketing_agent/
│   └── mcp_server/
│       ├── server.py                 # 마케팅 MCP 서버
│       ├── requirements.txt          # 의존성 패키지  
│       └── run_server.sh            # 실행 스크립트
├── task_agent/
│   └── mcp_server/
│       ├── server.py                 # 업무지원 MCP 서버
│       ├── requirements.txt          # 의존성 패키지
│       └── run_server.sh            # 실행 스크립트
├── config/
│   ├── mcp_config.yaml              # MCP 서버 설정
│   └── .env.template                # 환경 변수 템플릿
├── logs/                            # 서버 로그 디렉토리
├── test_results/                    # 테스트 결과 디렉토리
├── setup.sh                        # 환경 설정 스크립트
├── start_all_servers.sh            # 모든 서버 시작
├── stop_all_servers.sh             # 모든 서버 종료
├── test_workflow.sh                # 워크플로우 테스트
└── README.md                       # 프로젝트 문서
```

## 🛠 개발 환경 설정

### 요구사항
- Python 3.8+
- pip (Python 패키지 관리자)
- Git

### 선택사항
- Google Cloud Platform 계정 (Calendar, Drive 연동)
- Slack 워크스페이스 (알림 연동)
- Notion 계정 (문서 저장)
- 소셜 미디어 API 키 (자동 포스팅)

## 🔧 설정 가이드

### 1. API 키 설정

```bash
# .env 파일 생성
cp config/.env.template config/.env

# 필요한 API 키 설정
vim config/.env
```

### 2. Google Services 설정

```bash
# Google Cloud Console에서 서비스 계정 생성
# credentials.json 다운로드 후 config/ 디렉토리에 저장
```

### 3. 소셜 미디어 연동

```bash
# Twitter, Facebook, Instagram API 키 발급
# config/.env 파일에 추가
```

## 🧪 테스트

### 단위 테스트
```bash
# 각 에이전트별 개별 테스트
cd buisness_planning_agent/mcp_server && python -m pytest
cd marketing_agent/mcp_server && python -m pytest  
cd task_agent/mcp_server && python -m pytest
```

### 통합 테스트
```bash
# 전체 워크플로우 테스트
./test_workflow.sh
```

### 성능 테스트
```bash
# 동시 요청 처리 테스트
cd test_scripts && python load_test.py
```

## 📊 모니터링

### 실시간 로그 확인
```bash
# 모든 서버 로그
tail -f logs/*.log

# 특정 서버 로그
tail -f logs/business_planning.log
tail -f logs/marketing.log
tail -f logs/task.log
```

### 서버 상태 확인
```bash
# 프로세스 상태
ps aux | grep "python.*server.py"

# 포트 사용 확인
netstat -tulpn | grep :300[1-3]
```

## 🚨 문제 해결

### 일반적인 문제

#### 1. 서버 시작 실패
```bash
# 포트 충돌 확인
netstat -tulpn | grep :3001

# 기존 프로세스 종료
pkill -f "python.*server.py"
```

#### 2. 외부 MCP 연결 실패
```bash
# 네트워크 연결 확인
curl -I https://smithery.ai/server/@smithery-ai/search-mcp

# 타임아웃 설정 조정 (config/mcp_config.yaml)
```

#### 3. 의존성 패키지 오류
```bash
# 가상환경 재생성
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r */mcp_server/requirements.txt
```

### 로그 분석

주요 에러 패턴:
- `ConnectionError`: 외부 MCP 서버 연결 실패
- `TimeoutError`: 응답 시간 초과
- `AuthenticationError`: API 키 인증 실패
- `ValidationError`: 입력 데이터 검증 실패

## 🤝 기여 가이드

### 새로운 MCP 연동 추가

1. `EXTERNAL_MCP_URLS`에 새 서버 URL 추가
2. 새로운 도구 함수 작성
3. `setup_tools()`에 도구 등록
4. 테스트 케이스 추가

### 코드 스타일

```bash
# 코드 포맷팅
black *.py

# Import 정렬
isort *.py

# 타입 체크
mypy *.py
```

## 📈 성능 최적화

### 권장 설정
- **동시 연결**: 서버당 최대 100개
- **타임아웃**: 외부 MCP 호출 30초
- **재시도**: 실패 시 3회 재시도
- **캐싱**: 자주 사용되는 응답 캐시

### 확장성
- 로드 밸런서를 통한 수평 확장
- Redis 클러스터를 통한 세션 관리
- 데이터베이스 샤딩을 통한 성능 향상

## 📞 지원

### 문제 보고
- GitHub Issues: [repository-url]/issues
- 이메일: support@example.com

### 문서
- API 문서: `/docs/api`
- 개발자 가이드: `/docs/developer`
- FAQ: `/docs/faq`

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

---

## 🎉 마무리

이 시스템은 MCP 프로토콜을 활용하여 여러 전문 에이전트가 외부 도구들과 seamless하게 연동하는 차세대 비즈니스 자동화 플랫폼입니다. 

**주요 특장점:**
- ✅ **연속적 워크플로우**: 에이전트 간 자연스러운 연결
- ✅ **실시간 의사결정**: 멀티턴 대화를 통한 맞춤형 결과
- ✅ **확장 가능성**: 새로운 MCP 서버 추가 용이
- ✅ **실용적 통합**: 즉시 업무 적용 가능

더 자세한 정보나 문의사항이 있으시면 언제든 연락주세요! 🚀
