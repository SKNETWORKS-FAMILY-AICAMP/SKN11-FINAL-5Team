# Customer Service Agent v3.0

마케팅 에이전트의 구조를 참고하여 리팩토링된 고객 서비스 전문 컨설팅 에이전트입니다.

## 🚀 주요 개선사항

### 구조적 개선
- **디렉토리 구조화**: `agents/`, `config/`, `core/`, `utils/` 디렉토리로 체계적 구성
- **공통 모듈 활용**: `shared_modules`를 최대한 활용하여 코드 중복 제거
- **레거시 파일 정리**: `deprecated_files/`로 사용하지 않는 파일들 이동

### 기능적 개선
- **멀티턴 대화 시스템**: 단계별 문제 파악 및 해결책 제시
- **단계별 프로세스**: 문제파악 → 정보수집 → 분석 → 솔루션제안 → 피드백 → 수정 → 최종결과
- **페르소나 시스템**: 고객 관리 분야별 맞춤형 전문가 제공
- **템플릿 지원**: 고객 메시지 템플릿 검색 및 제공

## 📁 디렉토리 구조

```
customer_service_agent/
├── agents/                    # 전문화된 에이전트들
│   ├── base_agent.py         # 기본 에이전트 클래스
│   └── specialized_agents.py # 전문 에이전트들
├── config/                   # 설정 파일들
│   ├── persona_config.py     # 페르소나 설정
│   └── prompts_config.py     # 프롬프트 메타데이터
├── core/                     # 핵심 로직
│   └── customer_service_manager.py # 메인 매니저
├── utils/                    # 유틸리티 함수들
│   └── customer_utils.py     # 고객 관리 유틸리티
├── prompts/                  # 프롬프트 템플릿들
├── logs/                     # 로그 파일들
├── deprecated_files/         # 사용하지 않는 파일들
├── main.py                   # 메인 진입점 (FastAPI)
├── example_multiturn_usage.py # 멀티턴 대화 예제
└── README_v3.md             # 이 파일
```

## 🔄 멀티턴 대화 시스템

### 대화 단계 (ConversationStage)
1. **INITIAL**: 초기 접촉
2. **PROBLEM_IDENTIFICATION**: 문제 파악
3. **INFORMATION_GATHERING**: 정보 수집
4. **ANALYSIS**: 심층 분석
5. **SOLUTION_PROPOSAL**: 해결책 제안
6. **FEEDBACK**: 피드백 수집
7. **REFINEMENT**: 수정
8. **FINAL_RESULT**: 최종 결과
9. **COMPLETED**: 완료

### 수집하는 정보
- 사업 유형
- 고객 문제/불만
- 고객 세그먼트
- 현재 상황
- 원하는 결과
- 긴급도
- 가용 자원
- 이전 시도
- 고객 데이터
- 소통 채널
- 해결 기한
- 예산

## 🎭 페르소나 시스템

- **고객 응대 전문가**: 클레임 및 문의 처리
- **고객 유지 전문가**: 재방문 및 단골 고객 전환
- **고객 만족도 전문가**: 고객 여정 분석 및 만족도 향상
- **고객 세분화 전문가**: 고객 페르소나 및 세그먼트 생성
- **커뮤니티 구축 전문가**: 고객 커뮤니티 및 팬덤 형성
- **고객 데이터 활용 전문가**: CRM 기반 분석 및 자동화
- **개인정보 보호 전문가**: 개인정보 및 동의 관리
- **통합 고객 관리 컨설턴트**: 모든 영역을 아우르는 종합 컨설팅

## 🛠️ 사용 방법

### 1. 기본 서버 실행
```bash
cd customer_service_agent
python main.py
```

### 2. API 엔드포인트
- `POST /agent/query`: 멀티턴 대화 쿼리 처리
- `GET /agent/status`: 에이전트 상태 조회
- `GET /health`: 헬스체크

### 3. 멀티턴 대화 예제 실행
```bash
python example_multiturn_usage.py
```

## 📋 API 사용 예제

### 새 대화 시작
```json
{
  "user_id": 123,
  "conversation_id": null,
  "message": "고객 불만 처리에 대해 상담받고 싶습니다"
}
```

### 기존 대화 이어가기
```json
{
  "user_id": 123,
  "conversation_id": 456,
  "message": "온라인 쇼핑몰을 운영하고 있어요"
}
```

### 템플릿 요청
```json
{
  "user_id": 123,
  "conversation_id": null,
  "message": "생일 축하 메시지 템플릿을 보여주세요"
}
```

## 🔧 공통 모듈 활용

- **LLM 관리**: `get_llm_manager()` - 로드 밸런싱과 다중 LLM 지원
- **벡터 검색**: `get_vector_manager()` - 전문 지식 검색
- **데이터베이스**: `get_db_manager()` - 대화 이력 관리
- **로깅**: `setup_logging()` - 통일된 로깅 시스템
- **템플릿**: `get_templates_by_type()` - 고객 메시지 템플릿 조회

## 📊 특별 기능

### 1. 고객 메시지 템플릿
- 생일/기념일 메시지
- 구매 후 안내
- 재구매 유도
- 고객 맞춤 메시지
- 리뷰 요청
- 설문 요청
- 이벤트 안내

### 2. 감정 분석
- 고객 감정 자동 분석 (positive/neutral/negative/urgent)
- 감정에 따른 응답 톤 제안
- 긴급도 자동 계산

### 3. 문제 분류
- product_issue: 제품 문제
- delivery_issue: 배송 문제
- service_issue: 서비스 문제
- billing_issue: 결제 문제
- system_issue: 시스템 문제
- general_inquiry: 일반 문의

## ⚡ 성능 최적화

- **비동기 처리**: asyncio 기반 비동기 쿼리 처리
- **메모리 관리**: 대화 상태의 효율적인 메모리 관리
- **캐싱**: 벡터 검색 결과 캐싱
- **로드 밸런싱**: 다중 LLM 간 로드 밸런싱

## 🔍 주요 특징

### 1. 지능적 문제 파악
- 사용자 입력에서 자동으로 고객 문제 추출
- 감정 상태 및 긴급도 자동 분석
- 문제 카테고리 자동 분류

### 2. 맞춤형 솔루션 제안
- 문제 유형별 전문화된 해결책
- 고객 세그먼트 기반 개인화
- 실행 가능한 액션 플랜

### 3. 템플릿 기반 효율성
- 상황별 고객 메시지 템플릿
- 즉시 사용 가능한 문구 제공
- HTML 미리보기 지원

## 🚨 마이그레이션 가이드

### 기존 버전에서 v3.0으로
1. 기존 파일들은 `deprecated_files/`로 이동
2. 새로운 `main.py` 사용
3. API 엔드포인트: 새로운 멀티턴 시스템 적용
4. 대화 상태 관리 기능 추가
5. 템플릿 지원 기능 추가

### 호환성
- 기존 템플릿 시스템과 호환
- 기본 쿼리 처리 로직 유지
- 점진적 마이그레이션 가능

## 📊 모니터링

### 로그 파일
- `logs/customer_service.log`: 메인 로그
- 대화 단계별 상세 로깅
- 오류 및 성능 메트릭

### 상태 조회
```bash
curl http://localhost:8002/agent/status
curl http://localhost:8002/health
```

## 🤝 확장성

### 새 에이전트 추가
1. `agents/specialized_agents.py`에 새 클래스 추가
2. `BaseCustomerServiceAgent` 상속
3. `process_query()` 및 `get_specialized_prompt()` 구현

### 새 페르소나 추가
1. `config/persona_config.py`에 설정 추가
2. 관련 프롬프트 템플릿 작성
3. 토픽 매핑 업데이트

---

**개발팀**: SKN Team  
**버전**: 3.0.0  
**최종 업데이트**: 2025-07-20  
**기반**: Marketing Agent v3.0 구조
