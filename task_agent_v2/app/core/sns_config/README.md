# SNS 자동화 연동 가이드

이 가이드는 실제 SNS API와 연동하여 게시물을 자동으로 발행하는 방법을 설명합니다.

## 지원 플랫폼

- **Instagram** (Instagram Graph API)
- **Facebook** (Facebook Graph API)
- **Twitter/X** (Twitter API v2)
- **LinkedIn** (LinkedIn API)

## 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env` 파일을 생성하고 다음과 같이 설정하세요:

```bash
# .env 파일 예제를 복사
cp sns_config/.env.example .env

# .env 파일을 편집하여 실제 API 키 입력
nano .env
```

### 3. API 설정

각 플랫폼별로 API 설정이 필요합니다:

#### Instagram
1. [Facebook Developer Console](https://developers.facebook.com/) 에서 앱 생성
2. Instagram Graph API 활성화
3. Instagram Business Account 필요
4. Facebook 페이지와 Instagram 계정 연결
5. 장기 액세스 토큰 생성 (60일)

#### Facebook
1. Facebook Developer Console에서 앱 생성
2. `pages_manage_posts`, `pages_read_engagement` 권한 요청
3. 페이지 액세스 토큰 생성

#### Twitter/X
1. [Twitter Developer Portal](https://developer.twitter.com/) 에서 앱 생성
2. API v2 액세스 신청
3. `tweet.write`, `media.upload` 권한 확보
4. Bearer Token 생성

#### LinkedIn
1. [LinkedIn Developer Portal](https://developer.linkedin.com/) 에서 앱 생성
2. Marketing Developer Platform 신청
3. `w_member_social`, `w_organization_social` 권한 요청
4. OAuth 2.0 토큰 생성

## 사용법

### 기본 사용 예제

```python
from automation import AutomationManager
from models import AutomationRequest

# 자동화 매니저 초기화
automation_manager = AutomationManager()

# Instagram 게시물 발행
request = AutomationRequest(
    user_id=1,
    task_type="publish_sns",
    title="Instagram 자동 게시",
    task_data={
        "platform": "instagram",
        "content": "자동화로 업로드된 게시물입니다! 🚀",
        "hashtags": ["자동화", "Instagram", "AI"],
        "image_urls": ["https://example.com/image.jpg"],
        "access_token": "your_access_token",
        "instagram_business_account_id": "your_account_id"
    }
)

result = await automation_manager.create_automation_task(request)
print(result)
```

### 예약 게시

```python
from datetime import datetime, timedelta

# 1시간 후 게시 예약
scheduled_time = datetime.now() + timedelta(hours=1)

request = AutomationRequest(
    user_id=1,
    task_type="publish_sns",
    title="예약된 게시물",
    task_data={
        "platform": "facebook",
        "content": "예약된 시간에 자동으로 게시됩니다!",
        "access_token": "your_token",
        "page_id": "your_page_id"
    },
    scheduled_at=scheduled_time
)
```

### 다중 플랫폼 동시 게시

```python
platforms = ["instagram", "facebook", "twitter"]

for platform in platforms:
    request = AutomationRequest(
        user_id=1,
        task_type="publish_sns",
        title=f"{platform} 게시",
        task_data={
            "platform": platform,
            "content": "모든 SNS에 동시 게시!",
            "access_token": f"your_{platform}_token",
            # 플랫폼별 추가 설정...
        }
    )
    await automation_manager.create_automation_task(request)
```

## 플랫폼별 필수 설정값

### Instagram
- `access_token`: Instagram Graph API 액세스 토큰
- `instagram_business_account_id`: Instagram Business Account ID
- `page_id`: 연결된 Facebook 페이지 ID

### Facebook
- `access_token`: Facebook 페이지 액세스 토큰
- `page_id`: Facebook 페이지 ID

### Twitter
- `access_token`: Twitter Bearer Token 또는 Access Token

### LinkedIn
- `access_token`: LinkedIn 액세스 토큰
- `person_urn`: 개인 계정용 URN (선택)
- `organization_urn`: 회사 페이지용 URN (선택)

## 이미지 업로드

모든 플랫폼에서 이미지 URL을 통한 업로드를 지원합니다:

```python
task_data = {
    "platform": "instagram",
    "content": "이미지와 함께 게시",
    "image_urls": [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg"
    ],
    # 기타 설정...
}
```

## 에러 처리

API 연동 중 발생할 수 있는 오류들:

- **인증 오류**: 액세스 토큰 만료 또는 권한 부족
- **업로드 오류**: 이미지 URL 접근 불가 또는 파일 형식 오류
- **플랫폼 제한**: 텍스트 길이 제한, 이미지 개수 제한 등

## 제한사항

### Instagram
- Business Account 필수
- 이미지 또는 비디오 필수 (텍스트만 게시 불가)
- Facebook 페이지 연결 필요

### Facebook
- 페이지 관리자 권한 필요
- 커뮤니티 가이드라인 준수

### Twitter
- 280자 제한
- 이미지 최대 4개
- API 요청 제한

### LinkedIn
- 전문적인 콘텐츠 권장
- 스팸 정책 엄격

## 보안 주의사항

1. **API 키 보안**: 환경변수나 보안 저장소 사용
2. **액세스 토큰 관리**: 정기적인 토큰 갱신
3. **권한 최소화**: 필요한 권한만 요청
4. **로그 관리**: 민감한 정보 로그 제외

## 문제 해결

### 자주 발생하는 문제

1. **401 Unauthorized**: 액세스 토큰 확인
2. **403 Forbidden**: 권한 설정 확인
3. **400 Bad Request**: 요청 데이터 형식 확인
4. **500 Internal Server Error**: API 서버 상태 확인

### 디버깅

로그를 확인하여 구체적인 오류 메시지를 파악하세요:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 예제 실행

완전한 예제를 실행해보세요:

```bash
cd sns_config
python sns_example.py
```

## 지원 및 문의

API 관련 문제는 각 플랫폼의 개발자 문서를 참조하세요:

- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api/)
- [Facebook Graph API](https://developers.facebook.com/docs/graph-api/)
- [Twitter API v2](https://developer.twitter.com/en/docs/twitter-api)
- [LinkedIn API](https://docs.microsoft.com/en-us/linkedin/)
