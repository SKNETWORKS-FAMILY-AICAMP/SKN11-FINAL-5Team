# 마케팅 분석 도구 API

네이버 트렌드 분석과 인스타그램 해시태그 분석을 통한 마케팅 콘텐츠 자동 생성 API

## 🚀 주요 기능

### 1. 블로그 콘텐츠 생성 워크플로우
- 키워드 입력 → LLM 기반 관련 키워드 10개 추천 → 네이버 검색어 트렌드 분석 → 상위 5개 키워드 + 마케팅 템플릿 활용 블로그 콘텐츠 작성

### 2. 인스타그램 콘텐츠 생성 워크플로우
- 키워드 입력 → LLM 기반 관련 키워드 10개 추천 → 관련 인스타 해시태그 추천 → 해시태그 + 마케팅 템플릿 활용 인스타 콘텐츠 작성

## 📦 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 서버 실행
```bash
# Linux/Mac
chmod +x run_server.sh
./run_server.sh

# Windows
run_server.bat

# 직접 실행
uvicorn marketing_api:app --host 0.0.0.0 --port 8000 --reload
```

### 3. API 문서 확인
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## 🔗 API 엔드포인트

### 메인 워크플로우

#### 1. 블로그 콘텐츠 생성
```http
POST /api/v1/content/blog
Content-Type: application/json

{
  "keyword": "스킨케어",
  "description": "여성 타겟 스킨케어 제품 마케팅"
}
```

**응답 예시:**
```json
{
  "success": true,
  "base_keyword": "스킨케어",
  "related_keywords": ["스킨케어", "화장품", "뷰티", "피부관리", "..."],
  "top_keywords": ["스킨케어", "화장품", "뷰티", "안티에이징", "보습"],
  "trend_analysis": {
    "success": true,
    "data": [...],
    "period": "2024-01-01 ~ 2024-12-31"
  },
  "blog_content": {
    "full_content": "# 2024년 스킨케어 트렌드...",
    "keywords_used": ["스킨케어", "화장품", "뷰티"],
    "word_count": 1247,
    "seo_optimized": true
  },
  "processing_time": 12.34
}
```

#### 2. 인스타그램 콘텐츠 생성
```http
POST /api/v1/content/instagram
Content-Type: application/json

{
  "keyword": "홈트레이닝",
  "description": "집에서 할 수 있는 운동 프로그램"
}
```

**응답 예시:**
```json
{
  "success": true,
  "base_keyword": "홈트레이닝",
  "related_keywords": ["홈트레이닝", "홈워크아웃", "운동", "피트니스", "..."],
  "hashtag_analysis": {
    "success": true,
    "searched_hashtags": ["#홈트레이닝", "#홈워크아웃", "..."],
    "popular_hashtags": ["#fitness", "#workout", "#홈트", "..."],
    "total_posts": 1542
  },
  "instagram_content": {
    "post_content": "🏠 집에서도 완벽한 운동이 가능해요! 💪\n\n바쁜 일상 속에서도...",
    "selected_hashtags": ["#홈트레이닝", "#홈워크아웃", "#fitness", "..."],
    "hashtag_count": 25,
    "engagement_optimized": true
  },
  "processing_time": 15.67
}
```

### 개별 기능

#### 3. 네이버 트렌드 분석
```http
POST /api/v1/analysis/naver-trends
Content-Type: application/json

{
  "keywords": ["스킨케어", "화장품", "뷰티"],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

#### 4. 인스타그램 해시태그 분석
```http
POST /api/v1/analysis/instagram-hashtags
Content-Type: application/json

{
  "question": "스킨케어 마케팅",
  "hashtags": ["#skincare", "#beauty", "#cosmetics"]
}
```

#### 5. 관련 키워드 생성
```http
POST /api/v1/keywords/generate
Content-Type: application/json

{
  "keyword": "다이어트",
  "description": "건강한 체중 감량"
}
```

#### 6. 인스타그램 마케팅 템플릿
```http
GET /api/v1/templates/instagram
```

### 배치 처리

#### 7. 다중 키워드 콘텐츠 생성
```http
POST /api/v1/batch/content-generation
Content-Type: application/json

["키워드1", "키워드2", "키워드3"]
```
*최대 5개 키워드까지 배치 처리 가능*

## 🔧 환경 설정

### 필수 환경 변수
```bash
# 네이버 API
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

# Smithery API (기본값 제공)
SMITHERY_API_KEY=your_smithery_api_key
```

### .env 파일 예시
```env
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
SMITHERY_API_KEY=056f88d0-aa2e-4ea9-8f2d-382ba74dcb07
```

## 📊 API 사용 예시 (Python)

```python
import requests
import json

# API 베이스 URL
BASE_URL = "http://localhost:8000"

# 블로그 콘텐츠 생성
def create_blog_content(keyword, description=""):
    url = f"{BASE_URL}/api/v1/content/blog"
    data = {
        "keyword": keyword,
        "description": description
    }
    
    response = requests.post(url, json=data)
    return response.json()

# 인스타그램 콘텐츠 생성
def create_instagram_content(keyword, description=""):
    url = f"{BASE_URL}/api/v1/content/instagram"
    data = {
        "keyword": keyword,
        "description": description
    }
    
    response = requests.post(url, json=data)
    return response.json()

# 사용 예시
if __name__ == "__main__":
    # 블로그 콘텐츠 생성
    blog_result = create_blog_content("비건 화장품", "친환경 뷰티 제품")
    print("블로그 콘텐츠:", blog_result["blog_content"]["full_content"][:200])
    
    # 인스타그램 콘텐츠 생성
    instagram_result = create_instagram_content("요가", "집에서 하는 요가")
    print("인스타 콘텐츠:", instagram_result["instagram_content"]["post_content"])
```

## 📊 API 사용 예시 (JavaScript)

```javascript
// 블로그 콘텐츠 생성
async function createBlogContent(keyword, description = "") {
    const response = await fetch('http://localhost:8000/api/v1/content/blog', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            keyword: keyword,
            description: description
        })
    });
    
    return await response.json();
}

// 인스타그램 콘텐츠 생성
async function createInstagramContent(keyword, description = "") {
    const response = await fetch('http://localhost:8000/api/v1/content/instagram', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            keyword: keyword,
            description: description
        })
    });
    
    return await response.json();
}

// 사용 예시
createBlogContent("반려동물 용품", "강아지와 고양이를 위한 제품")
    .then(result => {
        console.log("블로그 콘텐츠:", result.blog_content.full_content);
    });

createInstagramContent("플랜테리어", "식물 인테리어 데코")
    .then(result => {
        console.log("인스타 콘텐츠:", result.instagram_content.post_content);
    });
```

## ⚠️ 주의사항

1. **API 호출 제한**: 네이버 트렌드 분석은 동시에 최대 5개 키워드까지만 처리 가능
2. **처리 시간**: 전체 워크플로우 완료까지 10-30초 소요 예상
3. **환경 설정**: 네이버 API 키가 필요하며, 없을 경우 트렌드 분석 기능 제한
4. **배치 처리**: 과부하 방지를 위해 최대 5개 키워드까지만 배치 처리 지원

## 🐛 트러블슈팅

### 공통 문제
1. **ModuleNotFoundError**: `pip install -r requirements.txt`로 의존성 재설치
2. **API 키 오류**: 환경 변수 설정 확인
3. **포트 충돌**: `--port 8080` 등으로 다른 포트 사용
4. **타임아웃 오류**: 네트워크 연결 및 외부 API 상태 확인

### 로그 확인
```bash
# 상세 로그 출력
uvicorn marketing_api:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

## 📞 지원

문제가 발생하거나 기능 추가 요청이 있으시면 이슈를 등록해주세요.

---

**개발자**: SKN11-FINAL-5Team  
**버전**: 1.0.0  
**최종 업데이트**: 2025년 7월
