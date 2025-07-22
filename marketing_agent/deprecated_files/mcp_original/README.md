# 🚀 마케팅 워크플로우 자동화 시스템

사용자 정의 5단계 플로우에 따른 마케팅 콘텐츠 자동 생성 및 포스팅 시스템입니다.

## 📋 워크플로우 구조

### 공통 단계
1️⃣ **사용자 입력 해석** (LLM)  
2️⃣ **플랫폼 선택** (memory)

### Instagram 경로
3️⃣ **해시태그 추천** (hashtag-mcp)  
4️⃣ **콘텐츠 생성** (vibe-marketing + 해시태그 포함)  
5️⃣ **자동 포스팅** (meta-post-scheduler-mcp)

### Naver Blog 경로  
3️⃣ **키워드 추천** (naver-search-mcp)  
4️⃣ **콘텐츠 생성** (vibe-marketing + 키워드 포함)  
5️⃣ **자동 포스팅** (puppeteer)

## 🔧 설치 및 설정

### 1. 의존성 설치
```bash
cd /Users/comet39/SKN_PJT/SKN11-FINAL-5Team/marketing_agent/mcp
pip install -r requirements.txt
```

### 2. 설정 확인
`workflow_config.py`에서 MCP 서버 설정을 확인하세요:
- Smithery API Key
- Apify Token  
- 각 MCP 서버 URL

## 🚀 사용 방법

### 방법 1: 메인 스크립트 실행
```bash
cd /Users/comet39/SKN_PJT/SKN11-FINAL-5Team/marketing_agent/mcp
python server.py
```

실행 모드 선택:
- **1**: Instagram 워크플로우 데모
- **2**: 네이버 블로그 워크플로우 데모  
- **3**: 전체 워크플로우 통합 데모
- **4**: 인터랙티브 모드 (사용자 입력)
- **5**: 모든 데모 실행

### 방법 2: 직접 코드 사용
```python
from mcp import run_marketing_workflow

# Instagram 마케팅
result = await run_marketing_workflow(
    "새로운 스킨케어 제품을 출시합니다.", 
    "instagram"
)

# 네이버 블로그 마케팅
result = await run_marketing_workflow(
    "홈카페 원두 구독 서비스를 시작합니다.", 
    "blog"
)

if result['success']:
    print("✅ 성공!")
    print(result['final_result']['content'])
else:
    print(f"❌ 실패: {result['error']}")
```

### 방법 3: 단계별 실행
```python
from mcp import MarketingWorkflowManager

manager = MarketingWorkflowManager()

# 1단계: 입력 해석
interpreted = await manager.step1_interpret_user_input("제품 설명")

# 2단계: 플랫폼 선택
platform_info = await manager.step2_select_platform("instagram")

# 3단계: 추천 요소 가져오기
recommendations = await manager.step3_get_recommendations()

# 4단계: 콘텐츠 생성
content = await manager.step4_generate_content()

# 5단계: 자동 포스팅
posting_result = await manager.step5_auto_posting()
```

## 🧪 테스트

### 전체 테스트 실행
```bash
cd /Users/comet39/SKN_PJT/SKN11-FINAL-5Team/marketing_agent
python test_workflow.py
```

테스트 항목:
- ⚙️ 워크플로우 설정 테스트
- 🔗 MCP 서버 연결 테스트
- 🔍 개별 단계 테스트
- 📱 Instagram 전체 워크플로우
- 📝 네이버 블로그 전체 워크플로우
- ⚡ 성능 테스트

### 개별 MCP 테스트
```bash
cd /Users/comet39/SKN_PJT/SKN11-FINAL-5Team/marketing_agent
python test_mcp.py
```

## 📁 파일 구조

```
mcp/
├── 📄 __init__.py              # 패키지 초기화
├── 📄 config.py               # 기본 MCP 설정
├── 📄 workflow_config.py      # 워크플로우 MCP 서버 설정
├── 📄 client.py               # 기본 MCP 클라이언트
├── 📄 simple_server.py        # 간단한 마케팅 클라이언트
├── 📄 workflow_manager.py     # 워크플로우 매니저 (⭐ 핵심)
├── 📄 server.py              # 메인 실행 스크립트
├── 📄 server_backup.py       # 기존 서버 백업
├── 📄 requirements.txt       # 의존성
└── 📄 README.md             # 이 파일

test_workflow.py               # 워크플로우 테스트
test_mcp.py                   # 기본 MCP 테스트
```

## 🎯 사용 예시

### Instagram 마케팅 예시
```
🎯 입력: "AI 기반 피트니스 앱을 출시했습니다."

📱 Instagram 워크플로우:
1️⃣ 해석: "개인 맞춤형 운동 및 건강 관리 솔루션"
2️⃣ 플랫폼: Instagram 선택
3️⃣ 해시태그: #피트니스 #AI #헬스케어 #운동 #다이어트
4️⃣ 콘텐츠: 시각적 매력적인 Instagram 포스트 생성
5️⃣ 포스팅: Meta API를 통한 자동 업로드
```

### 네이버 블로그 예시  
```
🎯 입력: "친환경 세제 브랜드를 출시합니다."

📝 네이버 블로그 워크플로우:
1️⃣ 해석: "환경 친화적 생활용품으로 건강한 라이프스타일 제안"
2️⃣ 플랫폼: 네이버 블로그 선택  
3️⃣ 키워드: 친환경세제, 무독성세제, 아기세제, 천연세제
4️⃣ 콘텐츠: SEO 최적화된 블로그 포스트 생성
5️⃣ 포스팅: Puppeteer를 통한 자동 업로드
```

## 🔧 주요 MCP 서버

| 서버명 | 용도 | 단계 |
|--------|------|------|
| `hashtag-mcp` | Instagram 해시태그 생성 | 3️⃣ (Instagram) |
| `vibe-marketing` | 매력적인 콘텐츠 생성 | 4️⃣ (공통) |
| `naver-search-mcp` | 네이버 키워드 추천 | 3️⃣ (Blog) |
| `meta-post-scheduler-mcp` | Instagram 자동 포스팅 | 5️⃣ (Instagram) |
| `product-trends-mcp` | 제품 트렌드 분석 | 추가 기능 |

## ⚠️ 주의사항

1. **API 키 설정**: `workflow_config.py`에서 올바른 API 키 설정 필요
2. **MCP 서버 상태**: 일부 MCP 서버가 오프라인일 수 있음
3. **네트워크 연결**: 안정적인 인터넷 연결 필요
4. **로그 확인**: 오류 발생 시 로그를 통해 문제 파악

## 📈 성능 최적화

- **비동기 처리**: 모든 MCP 호출은 비동기로 처리
- **오류 처리**: 각 단계별 fallback 로직 포함
- **캐싱**: 반복적인 요청에 대한 결과 캐싱 (향후 추가 예정)
- **병렬 처리**: 독립적인 작업들의 병렬 실행 (향후 추가 예정)

## 🆕 업데이트 내역

### v2.0.0 (현재)
- ✅ 사용자 정의 5단계 워크플로우 구현
- ✅ 플랫폼별 분기 처리 (Instagram/네이버 블로그)
- ✅ 여러 MCP 서버 통합 연동
- ✅ 단계별 테스트 시스템 구축
- ✅ 인터랙티브 모드 추가

### v1.0.0 (이전)
- 기본 MCP 클라이언트 기능
- 간단한 마케팅 콘텐츠 생성

## 🤝 기여 방법

1. 새로운 MCP 서버 추가: `workflow_config.py` 수정
2. 워크플로우 단계 추가: `workflow_manager.py` 확장
3. 테스트 케이스 추가: `test_workflow.py` 업데이트

## 📞 지원

문제 발생 시:
1. 로그 확인 (`logging.basicConfig(level=logging.DEBUG)`)
2. MCP 서버 연결 상태 확인
3. API 키 및 설정 검증
4. 테스트 스크립트 실행으로 문제 격리

---

**🎯 목표**: 마케팅 콘텐츠 생성부터 자동 포스팅까지 원클릭으로!
