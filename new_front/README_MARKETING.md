# TinkerBell Business - 마케팅 업무 자동화

1인 창업자를 위한 AI 마케팅 자동화 플랫폼입니다. 키워드 분석부터 콘텐츠 생성, 발행 스케줄 관리까지 마케팅 업무를 통합적으로 자동화할 수 있습니다.

## 🚀 주요 기능

### 1. 키워드 추천 및 분석
- 타겟 키워드 입력 시 관련 키워드 자동 추천
- 월간 검색량, 경쟁도, 난이도, 트렌드 분석
- 관련 키워드 및 제안 키워드 제공

### 2. AI 콘텐츠 생성
- 선택한 키워드 기반 고품질 블로그 콘텐츠 자동 생성
- SEO 최적화된 콘텐츠 작성
- 콘텐츠 미리보기 및 편집 기능

### 3. 발행 일정 예약
- 생성된 콘텐츠의 발행 날짜/시간 예약
- 자동 발행 스케줄 관리
- 발행 상태 실시간 모니터링

## 🛠️ 기술 스택

### Frontend
- **Next.js 15** - React 프레임워크
- **TypeScript** - 타입 안전성
- **Tailwind CSS** - 스타일링
- **shadcn/ui** - UI 컴포넌트 라이브러리
- **Radix UI** - 접근성 우선 컴포넌트
- **date-fns** - 날짜 처리
- **Sonner** - 토스트 알림

### Backend API
- **FastAPI** - Python 웹 프레임워크
- **Pydantic** - 데이터 검증
- **SQLAlchemy** - ORM
- **네이버 검색 API** - 키워드 분석
- **OpenAI/Claude API** - 콘텐츠 생성

## 📁 프로젝트 구조

```
new_front/
├── app/
│   ├── marketing/
│   │   └── page.tsx          # 마케팅 자동화 메인 페이지
│   ├── layout.tsx            # 루트 레이아웃
│   └── globals.css           # 전역 스타일
├── components/
│   ├── ui/                   # shadcn/ui 컴포넌트
│   └── layout/
│       └── navigation.tsx    # 네비게이션 컴포넌트
├── hooks/
│   └── useMarketing.ts       # 마케팅 관련 React Hooks
├── lib/
│   ├── api/
│   │   └── marketing.ts      # API 클라이언트
│   ├── utils.ts              # 유틸리티 함수
│   └── toast.ts              # 토스트 알림 유틸리티
└── README.md
```

## 🚀 설치 및 실행

### 1. 의존성 설치
```bash
cd new_front
npm install
```

### 2. 환경 변수 설정
`.env.local` 파일을 생성하고 다음 내용을 추가:

```env
# 마케팅 API 서버 URL
NEXT_PUBLIC_MARKETING_API_URL=http://localhost:8000

# 네이버 API 설정 (선택사항)
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

# OpenAI API 설정 (선택사항)
OPENAI_API_KEY=your_openai_api_key

# Claude API 설정 (선택사항)
CLAUDE_API_KEY=your_claude_api_key
```

### 3. 개발 서버 실행
```bash
npm run dev
```

애플리케이션이 `http://localhost:3000`에서 실행됩니다.

### 4. 백엔드 서버 실행 (별도)
```bash
cd task_agent/automation_task/marketing
python main.py
```

백엔드 API 서버가 `http://localhost:8000`에서 실행됩니다.

## 📱 사용법

### 1. 키워드 분석
1. "키워드 분석" 탭에서 분석할 키워드 입력
2. "분석하기" 버튼 클릭
3. 결과에서 원하는 키워드 선택
4. "선택한 키워드로 콘텐츠 생성" 버튼 클릭

### 2. 콘텐츠 관리
1. "콘텐츠 생성" 탭에서 생성된 콘텐츠 확인
2. "미리보기" 버튼으로 콘텐츠 내용 확인
3. "편집" 버튼으로 콘텐츠 수정
4. "발행 예약" 버튼으로 발행 일정 설정

### 3. 스케줄 관리
1. "발행 스케줄" 탭에서 예약된 콘텐츠 확인
2. 발행 상태 모니터링
3. 필요시 스케줄 수정 또는 취소

## 🎨 UI/UX 특징

- **반응형 디자인**: 모바일, 태블릿, 데스크톱 지원
- **다크/라이트 모드**: 사용자 선호도에 따른 테마 지원
- **직관적인 탭 구조**: 키워드 분석 → 콘텐츠 생성 → 발행 스케줄 순서
- **실시간 피드백**: 로딩 상태, 성공/실패 알림
- **모바일 네비게이션**: 하단 고정 네비게이션 바

## 🔗 API 엔드포인트

### 키워드 관련
- `POST /keywords/recommend` - 키워드 분석 및 추천
- `GET /keywords/expand` - 키워드 확장
- `GET /keywords/metrics` - 키워드 메트릭스 조회
- `GET /keywords/demographics` - 키워드 인구통계 정보
- `GET /keywords/history` - 키워드 분석 히스토리

### 콘텐츠 관련
- `POST /blog/content/generate` - 블로그 콘텐츠 생성
- `GET /blog/content/history` - 콘텐츠 히스토리 조회
- `GET /blog/content/{content_id}` - 특정 콘텐츠 상세 조회

### 발행 관련
- `POST /blog/publish/` - 블로그 발행
- `GET /blog/publish/status/{content_id}` - 발행 상태 조회
- `GET /blog/publish/posts` - 발행된 포스트 목록
- `DELETE /blog/publish/{content_id}` - 발행 취소

## 🔧 개발자 가이드

### 새로운 기능 추가
1. `hooks/useMarketing.ts`에 관련 hook 추가
2. `lib/api/marketing.ts`에 API 클라이언트 메서드 추가
3. UI 컴포넌트 구현
4. 타입 정의 업데이트

### 커스텀 훅 사용
```typescript
import { useMarketingData } from '@/hooks/useMarketing'

const MyComponent = () => {
  const marketing = useMarketingData()
  
  // 키워드 분석
  await marketing.analyzeKeywords('키워드')
  
  // 콘텐츠 생성
  await marketing.generateContent(['키워드1', '키워드2'])
  
  // 통계 데이터 접근
  console.log(marketing.stats)
}
```

## 📋 TODO

- [ ] 인스타그램 자동 포스팅 기능
- [ ] 콘텐츠 템플릿 관리
- [ ] 성과 분석 대시보드
- [ ] 다중 플랫폼 동시 발행
- [ ] 사용자 권한 관리
- [ ] 콘텐츠 A/B 테스트

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 지원

문의사항이 있으시면 다음으로 연락해주세요:
- 이메일: contact@tinkerbell.ai
- 전화: 1588-0000