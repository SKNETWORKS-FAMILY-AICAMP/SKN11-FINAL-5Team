# Business Planning Agent v3.0

마케팅 에이전트의 구조를 참고하여 리팩토링된 1인 창업 전문 비즈니스 기획 에이전트입니다.

## 🚀 주요 개선사항

### 구조적 개선
- **디렉토리 구조화**: `agents/`, `config/`, `core/`, `utils/` 디렉토리로 체계적 구성
- **공통 모듈 활용**: `shared_modules`를 최대한 활용하여 코드 중복 제거
- **레거시 파일 정리**: `deprecated_files/`로 사용하지 않는 파일들 이동

### 기능적 개선
- **멀티턴 대화 시스템**: 단계별 정보 수집 및 대화 상태 관리
- **단계별 프로세스**: 정보수집 → 분석 → 기획 → 제안 → 피드백 → 수정 → 최종결과
- **페르소나 시스템**: 전문 분야별 맞춤형 컨설팅 제공

## 📁 디렉토리 구조

```
buisness_planning_agent/
├── agents/                    # 전문화된 에이전트들
│   ├── base_agent.py         # 기본 에이전트 클래스
│   └── specialized_agents.py # 전문 에이전트들
├── config/                   # 설정 파일들
│   ├── persona_config.py     # 페르소나 설정
│   └── prompts_config.py     # 프롬프트 메타데이터
├── core/                     # 핵심 로직
│   └── business_planning_manager.py # 메인 매니저
├── utils/                    # 유틸리티 함수들
│   └── business_utils.py     # 비즈니스 관련 유틸리티
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
2. **INFORMATION_GATHERING**: 정보 수집
3. **ANALYSIS**: 심층 분석
4. **PLANNING**: 계획 수립
5. **PROPOSAL**: 제안
6. **FEEDBACK**: 피드백 수집
7. **REFINEMENT**: 수정
8. **FINAL_RESULT**: 최종 결과
9. **COMPLETED**: 완료

### 수집하는 정보
- 비즈니스 아이디어
- 업종/산업
- 타겟 고객
- 고유 가치/차별점
- 현재 단계
- 예산
- 타임라인
- 지역/위치
- 팀 규모
- 관련 경험
- 목표
- 우려사항

## 🎭 페르소나 시스템

- **창업 준비 전문가**: 체계적인 창업 준비 프로세스
- **아이디어 검증 전문가**: 객관적인 시장성 분석
- **비즈니스 모델 설계 전문가**: 린캔버스와 수익 구조
- **자금 조달 전문가**: 투자 유치와 자금 조달
- **성장 전략 전문가**: 사업 확장과 스케일업
- **통합 비즈니스 컨설턴트**: 모든 영역을 아우르는 종합 컨설팅

## 🛠️ 사용 방법

### 1. 기본 서버 실행
```bash
cd buisness_planning_agent
python main.py
```

### 2. API 엔드포인트
- `POST /agent/query`: 멀티턴 대화 쿼리 처리
- `GET /agent/status`: 에이전트 상태 조회
- `GET /conversation/{id}/status`: 특정 대화 상태 조회
- `DELETE /conversation/{id}`: 대화 초기화
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
  "message": "온라인 강의 플랫폼 창업을 준비하고 있습니다"
}
```

### 기존 대화 이어가기
```json
{
  "user_id": 123,
  "conversation_id": 456,
  "message": "IT 업계이고 초보 개발자들을 타겟으로 합니다"
}
```

## 🔧 공통 모듈 활용

- **LLM 관리**: `get_llm_manager()` - 로드 밸런싱과 다중 LLM 지원
- **벡터 검색**: `get_vector_manager()` - 전문 지식 검색
- **데이터베이스**: `get_db_manager()` - 대화 이력 관리
- **로깅**: `setup_logging()` - 통일된 로깅 시스템
- **응답 형식**: `create_business_response()` - 표준 응답 형식

## ⚡ 성능 최적화

- **비동기 처리**: asyncio 기반 비동기 쿼리 처리
- **메모리 관리**: 대화 상태의 효율적인 메모리 관리
- **캐싱**: 벡터 검색 결과 캐싱
- **로드 밸런싱**: 다중 LLM 간 로드 밸런싱

## 🔍 주요 특징

### 1. 지능적 정보 수집
- 사용자 입력에서 자동으로 비즈니스 정보 추출
- 누락된 정보에 대한 체계적인 질문 생성
- 완료율 기반 진행 상황 관리

### 2. 전문화된 분석
- 토픽별 전문 프롬프트 활용
- 비즈니스 단계별 맞춤 분석
- 리스크 평가 및 실현 가능성 검토

### 3. 실용적 제안
- 단계별 실행 계획 수립
- 우선순위 기반 액션 아이템
- 피드백 기반 계획 수정

## 🚨 마이그레이션 가이드

### 기존 v2.0에서 v3.0으로
1. 기존 `business_planning.py` → `deprecated_files/`로 이동됨
2. 새로운 `main.py` 사용
3. API 엔드포인트: `/query` → `/agent/query`
4. 응답 형식 변경: 멀티턴 대화 정보 추가
5. 대화 상태 관리 기능 추가

### 호환성
- 기존 API는 `/query` 엔드포인트로 여전히 지원 (Deprecated)
- 기본 쿼리 처리 로직은 유지
- 점진적 마이그레이션 가능

## 📊 모니터링

### 로그 파일
- `logs/business_planning.log`: 메인 로그
- 대화 단계별 상세 로깅
- 오류 및 성능 메트릭

### 상태 조회
```bash
curl http://localhost:8000/agent/status
curl http://localhost:8000/conversation/123/status
```

## 🤝 확장성

### 새 에이전트 추가
1. `agents/specialized_agents.py`에 새 클래스 추가
2. `BaseBusinessAgent` 상속
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
