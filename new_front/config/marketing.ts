// 마케팅 자동화 관련 설정

export const MARKETING_CONFIG = {
  // API 기본 설정
  API: {
    BASE_URL: process.env.NEXT_PUBLIC_MARKETING_API_URL || 'http://localhost:8000',
    TIMEOUT: 30000, // 30초
    RETRY_ATTEMPTS: 3,
  },

  // 키워드 분석 설정
  KEYWORD: {
    MAX_KEYWORDS_PER_REQUEST: 20,
    MIN_SEARCH_VOLUME: 100,
    MAX_SEARCH_VOLUME: 1000000,
    DEFAULT_FILTERS: {
      search_volume_range: { min: 1000, max: 100000 },
      category: 'IT'
    }
  },

  // 콘텐츠 생성 설정
  CONTENT: {
    MIN_WORD_COUNT: 500,
    MAX_WORD_COUNT: 3000,
    DEFAULT_WORD_COUNT: 1200,
    MIN_SEO_SCORE: 70,
    TEMPLATES: [
      'blog_post',
      'product_review',
      'how_to_guide',
      'list_article',
      'news_article'
    ]
  },

  // 발행 스케줄 설정
  SCHEDULE: {
    DEFAULT_TIME: '09:00',
    TIME_SLOTS: Array.from({ length: 24 }, (_, i) => 
      `${i.toString().padStart(2, '0')}:00`
    ),
    DAYS_OF_WEEK: [
      'sunday',
      'monday', 
      'tuesday',
      'wednesday',
      'thursday',
      'friday',
      'saturday'
    ],
    MAX_SCHEDULED_POSTS: 100
  },

  // 플랫폼 설정
  PLATFORMS: {
    NAVER_BLOG: {
      name: '네이버 블로그',
      icon: 'naver',
      color: '#03C75A',
      maxTitleLength: 100,
      maxContentLength: 10000,
      supportsTags: true,
      supportsImages: true
    },
    INSTAGRAM: {
      name: '인스타그램',
      icon: 'instagram', 
      color: '#E4405F',
      maxCaptionLength: 2200,
      maxHashtags: 30,
      supportsImages: true,
      supportsVideos: true
    },
    TISTORY: {
      name: '티스토리',
      icon: 'tistory',
      color: '#FF5722',
      maxTitleLength: 200,
      maxContentLength: 50000,
      supportsTags: true,
      supportsImages: true
    }
  },

  // UI 설정
  UI: {
    ITEMS_PER_PAGE: 10,
    MAX_ITEMS_PER_PAGE: 50,
    TOAST_DURATION: 5000,
    LOADING_DEBOUNCE: 300,
    COLORS: {
      primary: '#10B981',
      secondary: '#F59E0B', 
      success: '#059669',
      error: '#DC2626',
      warning: '#D97706',
      info: '#2563EB'
    }
  },

  // 검증 규칙
  VALIDATION: {
    KEYWORD: {
      minLength: 1,
      maxLength: 50,
      pattern: /^[가-힣a-zA-Z0-9\s]+$/
    },
    CONTENT_TITLE: {
      minLength: 5,
      maxLength: 100
    },
    CONTENT_BODY: {
      minLength: 100,
      maxLength: 10000
    }
  },

  // 기본값
  DEFAULTS: {
    PLATFORM: 'naver_blog' as const,
    LANGUAGE: 'ko',
    TIMEZONE: 'Asia/Seoul',
    AUTO_PUBLISH: false,
    AUTO_GENERATE: false
  }
}

// 환경별 설정 오버라이드
export const getEnvironmentConfig = () => {
  const env = process.env.NODE_ENV

  switch (env) {
    case 'development':
      return {
        ...MARKETING_CONFIG,
        API: {
          ...MARKETING_CONFIG.API,
          BASE_URL: 'http://localhost:8000'
        }
      }
    
    case 'production':
      return {
        ...MARKETING_CONFIG,
        API: {
          ...MARKETING_CONFIG.API,
          BASE_URL: process.env.NEXT_PUBLIC_MARKETING_API_URL || 'https://api.tinkerbell.ai'
        }
      }
    
    default:
      return MARKETING_CONFIG
  }
}

export default getEnvironmentConfig()