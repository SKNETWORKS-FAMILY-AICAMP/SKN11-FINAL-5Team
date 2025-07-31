// API 클라이언트 유틸리티
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// 타입 정의
export interface KeywordAnalysisRequest {
  user_id: number
  keyword: string
  platform: 'naver_blog' | 'instagram' | 'tistory' | 'medium'
  include_trends?: boolean
  include_related?: boolean
}

export interface KeywordAnalysisResponse {
  success: boolean
  data: {
    keyword: string
    search_volume: number
    competition: 'low' | 'medium' | 'high'
    difficulty: number
    trend_score: number
    related_keywords: string[]
    monthly_trends?: Array<{ month: string; volume: number }>
    suggestions?: string[]
  }
}

export interface ContentGenerationRequest {
  keyword?: string
  hashtags?: string[]
  template?: string
  platform: 'naver_blog' | 'instagram' | 'tistory' | 'medium'
  auto_upload?: boolean
  auto_post?: boolean
  image_style?: string
  blog_config?: Record<string, any>
  instagram_config?: Record<string, any>
}

export interface BlogContentResponse {
  success: boolean
  data: {
    title: string
    content: string
    tags: string[]
    seo_analysis?: Record<string, any>
    word_count: number
    reading_time: number
    generated_at: string
  }
}

export interface BlogPublishRequest {
  content_id: string
  blog_config: {
    blog_id?: string
    category?: string
    tags?: string[]
    publish_date?: string
  }
}

export interface BlogPublishResponse {
  success: boolean
  message: string
  data?: {
    publish_id: string
    status: 'pending' | 'published' | 'failed'
  }
}

// API 클라이언트 클래스
class MarketingApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`API 요청 실패: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }

  // 키워드 분석 API
  async analyzeKeywords(request: KeywordAnalysisRequest): Promise<KeywordAnalysisResponse> {
    return this.request<KeywordAnalysisResponse>('/keywords/recommend', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  // 키워드 확장 API
  async expandKeywords(keyword: string, maxResults: number = 100): Promise<{
    success: boolean
    data: string[]
  }> {
    return this.request(`/keywords/expand?keyword=${encodeURIComponent(keyword)}&max_results=${maxResults}`)
  }

  // 키워드 메트릭스 조회 API
  async getKeywordMetrics(keyword: string): Promise<{
    success: boolean
    data: {
      keyword: string
      search_volume: number
      competition: string
      cpc: number
      difficulty: number
    }
  }> {
    return this.request(`/keywords/metrics?keyword=${encodeURIComponent(keyword)}`)
  }

  // 키워드 인구통계 정보 조회 API
  async getKeywordDemographics(keyword: string): Promise<{
    success: boolean
    data: {
      age_groups: Array<{ age: string; percentage: number }>
      gender: { male: number; female: number }
      device: { mobile: number; desktop: number }
    }
  }> {
    return this.request(`/keywords/demographics?keyword=${encodeURIComponent(keyword)}`)
  }

  // 키워드 분석 히스토리 조회 API
  async getKeywordHistory(page: number = 1, limit: number = 10, keyword?: string): Promise<{
    success: boolean
    data: {
      items: Array<{
        id: string
        keyword: string
        analyzed_at: string
        platform: string
        result: Record<string, any>
      }>
      total: number
      page: number
      pages: number
    }
  }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    })
    
    if (keyword) {
      params.append('keyword', keyword)
    }

    return this.request(`/keywords/history?${params.toString()}`)
  }

  // 블로그 콘텐츠 생성 API
  async generateContent(request: ContentGenerationRequest): Promise<BlogContentResponse> {
    return this.request<BlogContentResponse>('/blog/content/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  // 콘텐츠 히스토리 조회 API
  async getContentHistory(
    page: number = 1, 
    limit: number = 10, 
    keyword?: string, 
    status?: string
  ): Promise<{
    success: boolean
    data: {
      items: Array<{
        id: string
        keyword: string
        title: string
        content: string
        status: 'draft' | 'scheduled' | 'published'
        platform: string
        word_count: number
        seo_score: number
        created_at: string
        updated_at: string
      }>
      total: number
      page: number
      pages: number
    }
  }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    })
    
    if (keyword) params.append('keyword', keyword)
    if (status) params.append('status', status)

    return this.request(`/blog/content/history?${params.toString()}`)
  }

  // 특정 콘텐츠 상세 조회 API
  async getContentDetail(contentId: string): Promise<{
    success: boolean
    data: {
      id: string
      keyword: string
      title: string
      content: string
      status: string
      platform: string
      word_count: number
      seo_score: number
      created_at: string
      updated_at: string
    }
  }> {
    return this.request(`/blog/content/${contentId}`)
  }

  // 블로그 발행 API
  async publishBlog(request: BlogPublishRequest): Promise<BlogPublishResponse> {
    return this.request<BlogPublishResponse>('/blog/publish/', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  // 블로그 발행 상태 조회 API
  async getPublishStatus(contentId: string): Promise<{
    success: boolean
    data: {
      content_id: string
      status: 'pending' | 'publishing' | 'published' | 'failed'
      progress: number
      message?: string
      published_url?: string
      error?: string
    }
  }> {
    return this.request(`/blog/publish/status/${contentId}`)
  }

  // 발행된 블로그 포스트 목록 조회 API
  async getPublishedPosts(
    page: number = 1,
    limit: number = 10,
    keyword?: string
  ): Promise<{
    success: boolean
    data: Array<{
      id: string
      keyword: string
      title: string
      url: string
      published_at: string
      platform: string
      views?: number
      engagement?: number
    }>
  }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    })
    
    if (keyword) params.append('keyword', keyword)

    return this.request(`/blog/publish/posts?${params.toString()}`)
  }

  // 블로그 발행 취소 API
  async cancelPublish(contentId: string): Promise<{
    success: boolean
    message: string
  }> {
    return this.request(`/blog/publish/${contentId}`, {
      method: 'DELETE',
    })
  }

  // 통계 데이터 조회 API (커스텀)
  async getAnalytics(dateRange: { start: string; end: string }): Promise<{
    success: boolean
    data: {
      total_keywords: number
      total_contents: number
      scheduled_contents: number
      published_contents: number
      average_seo_score: number
      top_keywords: Array<{ keyword: string; count: number }>
      content_performance: Array<{
        date: string
        contents_created: number
        contents_published: number
      }>
    }
  }> {
    const params = new URLSearchParams({
      start_date: dateRange.start,
      end_date: dateRange.end,
    })

    return this.request(`/analytics?${params.toString()}`)
  }

  // Instagram 계정 연동 상태 확인 API
//   async checkInstagramConnection(userId: number): Promise<{
//     success: boolean
//     data: {
//       is_connected: boolean
//       username?: string
//       graph_id?: string
//       created_at?: string
//     }
//   }> {
//     return this.request(`/instagram/connection/status?user_id=${userId}`)
//   }
}

// 싱글톤 인스턴스
export const marketingApi = new MarketingApiClient()

// React Hook으로 API 사용
export function useMarketingApi() {
  return {
    // 키워드 관련
    analyzeKeywords: marketingApi.analyzeKeywords.bind(marketingApi),
    expandKeywords: marketingApi.expandKeywords.bind(marketingApi),
    getKeywordMetrics: marketingApi.getKeywordMetrics.bind(marketingApi),
    getKeywordDemographics: marketingApi.getKeywordDemographics.bind(marketingApi),
    getKeywordHistory: marketingApi.getKeywordHistory.bind(marketingApi),
    
    // 콘텐츠 관련
    generateContent: marketingApi.generateContent.bind(marketingApi),
    getContentHistory: marketingApi.getContentHistory.bind(marketingApi),
    getContentDetail: marketingApi.getContentDetail.bind(marketingApi),
    
    // 발행 관련
    publishBlog: marketingApi.publishBlog.bind(marketingApi),
    getPublishStatus: marketingApi.getPublishStatus.bind(marketingApi),
    getPublishedPosts: marketingApi.getPublishedPosts.bind(marketingApi),
    cancelPublish: marketingApi.cancelPublish.bind(marketingApi),
    
    // 통계
    getAnalytics: marketingApi.getAnalytics.bind(marketingApi),
    
    // Instagram 관련
    // checkInstagramConnection: marketingApi.checkInstagramConnection.bind(marketingApi),
  }
}

// 에러 처리 유틸리티
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: any
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

// 요청 인터셉터 (필요시 추가)
export function setupApiInterceptors(token?: string) {
  // JWT 토큰이나 기타 인증 헤더 설정
  if (token) {
    // API 클라이언트에 토큰 설정 로직 추가
  }
}