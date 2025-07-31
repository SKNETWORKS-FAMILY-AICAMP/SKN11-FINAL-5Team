// 마케팅 자동화 관련 타입 정의

export interface KeywordData {
  keyword: string
  searchVolume: number
  competition: 'low' | 'medium' | 'high'
  difficulty: number
  trend: number
  relatedKeywords: string[]
}

export interface ContentData {
  id: string
  keyword: string
  title: string
  content: string
  status: 'draft' | 'scheduled' | 'published' | 'failed'
  scheduledDate?: Date
  platform: string
  wordCount: number
  seoScore: number
  createdAt?: Date
  updatedAt?: Date
  publishedAt?: Date
  url?: string
  views?: number
  engagement?: number
}

export interface ScheduleData {
  id: string
  contentId: string
  platform: string
  publishDate: Date
  status: 'pending' | 'published' | 'failed'
  error?: string
  publishedUrl?: string
}

export interface MarketingStats {
  totalKeywords: number
  totalContents: number
  scheduledContents: number
  publishedContents: number
  averageSeoScore: number
  topKeywords?: Array<{ keyword: string; count: number }>
  contentPerformance?: Array<{
    date: string
    contentsCreated: number
    contentsPublished: number
  }>
}

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
  timestamp?: string
}

export interface PaginatedResponse<T = any> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// 플랫폼 타입
export type PlatformType = 'naver_blog' | 'instagram' | 'tistory' | 'medium'

// 발행 상태 타입
export type PublishStatus = 'draft' | 'scheduled' | 'publishing' | 'published' | 'failed'

// 스케줄 빈도 타입
export type ScheduleFrequency = 'daily' | 'weekly' | 'monthly' | 'custom'

// 자동화 상태 타입
export type AutomationStatus = 'active' | 'paused' | 'error' | 'stopped'

// 사용자 정보 타입
export interface User {
  id: number
  email: string
  name: string
  avatar?: string
  role: 'user' | 'admin'
  createdAt: Date
  updatedAt: Date
}

// 설정 타입
export interface MarketingConfig {
  autoGenerate: boolean
  autoPublish: boolean
  defaultPlatform: PlatformType
  defaultSchedule: {
    frequency: ScheduleFrequency
    time: string
    days?: string[]
  }
  templates: string[]
  keywords: string[]
}

// 에러 타입
export interface ApiError {
  message: string
  status: number
  code?: string
  details?: any
}

// 알림 타입
export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  timestamp: Date
  read: boolean
  actionUrl?: string
}

// 분석 데이터 타입
export interface AnalyticsData {
  platform: PlatformType
  dateRange: {
    start: Date
    end: Date
  }
  totalPosts: number
  totalViews: number
  totalEngagement: number
  avgEngagementRate: number
  topKeywords: Array<{
    keyword: string
    posts: number
    views: number
    engagement: number
  }>
  dailyStats: Array<{
    date: string
    posts: number
    views: number
    engagement: number
  }>
}