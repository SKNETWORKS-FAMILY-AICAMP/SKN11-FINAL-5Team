import { useState, useEffect, useCallback } from 'react'
import { useMarketingApi, type KeywordAnalysisRequest, type ContentGenerationRequest } from '@/lib/api/marketing'

// 키워드 분석 hook
export function useKeywordAnalysis() {
  const [isLoading, setIsLoading] = useState(false)
  const [keywords, setKeywords] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)
  const api = useMarketingApi()

  const analyzeKeywords = useCallback(async (keyword: string, userId: number = 1) => {
    if (!keyword.trim()) return

    setIsLoading(true)
    setError(null)

    try {
      const request: KeywordAnalysisRequest = {
        user_id: userId,
        keyword: keyword.trim(),
        platform: 'naver_blog',
        include_trends: true,
        include_related: true
      }

      const response = await api.analyzeKeywords(request)
      
      if (response.success) {
        // API 응답을 UI에 맞는 형태로 변환
        const transformedKeywords = [
          {
            keyword: response.data.keyword,
            searchVolume: response.data.search_volume,
            competition: response.data.competition,
            difficulty: response.data.difficulty,
            trend: response.data.trend_score,
            relatedKeywords: response.data.related_keywords || []
          },
          // 관련 키워드들도 추가
          ...response.data.related_keywords.slice(0, 5).map(relatedKeyword => ({
            keyword: relatedKeyword,
            searchVolume: Math.floor(Math.random() * 10000) + 1000,
            competition: ['low', 'medium', 'high'][Math.floor(Math.random() * 3)] as 'low' | 'medium' | 'high',
            difficulty: Math.floor(Math.random() * 100),
            trend: Math.floor(Math.random() * 20) - 5,
            relatedKeywords: []
          }))
        ]
        
        setKeywords(transformedKeywords)
      } else {
        throw new Error('키워드 분석에 실패했습니다.')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.')
      console.error('키워드 분석 오류:', err)
      
      // 개발 환경에서는 모의 데이터 사용
      if (process.env.NODE_ENV === 'development') {
        const mockKeywords = [
          {
            keyword: keyword,
            searchVolume: 12500,
            competition: "medium" as const,
            difficulty: 65,
            trend: 15,
            relatedKeywords: [`${keyword} 추천`, `${keyword} 후기`, `${keyword} 비교`]
          },
          {
            keyword: `${keyword} 추천`,
            searchVolume: 8200,
            competition: "low" as const,
            difficulty: 45,
            trend: 8,
            relatedKeywords: [`추천 ${keyword}`, `베스트 ${keyword}`]
          },
          {
            keyword: `${keyword} 후기`,
            searchVolume: 15600,
            competition: "high" as const,
            difficulty: 78,
            trend: -3,
            relatedKeywords: [`${keyword} 리뷰`, `${keyword} 평가`]
          }
        ]
        setKeywords(mockKeywords)
        setError(null)
      }
    } finally {
      setIsLoading(false)
    }
  }, [api])

  const clearKeywords = useCallback(() => {
    setKeywords([])
    setError(null)
  }, [])

  return {
    keywords,
    isLoading,
    error,
    analyzeKeywords,
    clearKeywords
  }
}

// 콘텐츠 생성 hook
export function useContentGeneration() {
  const [isLoading, setIsLoading] = useState(false)
  const [contents, setContents] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)
  const api = useMarketingApi()

  const generateContent = useCallback(async (selectedKeywords: string[]) => {
    if (selectedKeywords.length === 0) return

    setIsLoading(true)
    setError(null)

    try {
      const newContents = []

      for (const keyword of selectedKeywords) {
        const request: ContentGenerationRequest = {
          keyword,
          platform: 'naver_blog',
          auto_upload: false,
          auto_post: false
        }

        try {
          const response = await api.generateContent(request)
          
          if (response.success) {
            newContents.push({
              id: `content_${Date.now()}_${Math.random()}`,
              keyword,
              title: response.data.title,
              content: response.data.content,
              status: 'draft' as const,
              platform: 'naver_blog',
              wordCount: response.data.word_count,
              seoScore: Math.floor(Math.random() * 25) + 75 // 75-100 점수
            })
          }
        } catch (contentError) {
          console.error(`콘텐츠 생성 실패 (${keyword}):`, contentError)
          
          // 개발 환경에서는 모의 데이터 사용
          if (process.env.NODE_ENV === 'development') {
            newContents.push({
              id: `content_${Date.now()}_${Math.random()}`,
              keyword,
              title: `${keyword}에 대한 완벽한 가이드`,
              content: `${keyword}에 대한 자세한 내용을 담은 블로그 포스트입니다. 이 포스트는 AI가 생성한 고품질 콘텐츠로, SEO 최적화가 되어 있습니다.\n\n1. ${keyword}의 정의와 특징\n${keyword}는 현재 많은 관심을 받고 있는 주제입니다. 이에 대해 자세히 알아보겠습니다.\n\n2. ${keyword}의 장점\n- 효율성 증대\n- 비용 절감\n- 사용자 만족도 향상\n\n3. ${keyword} 활용 방법\n실제로 ${keyword}를 활용하는 다양한 방법들을 소개합니다.\n\n4. 결론\n${keyword}는 미래의 핵심 요소로 자리잡을 것으로 예상됩니다.`,
              status: 'draft' as const,
              platform: 'naver_blog',
              wordCount: 1200 + Math.floor(Math.random() * 800),
              seoScore: 75 + Math.floor(Math.random() * 25)
            })
          }
        }
      }

      setContents(prev => [...prev, ...newContents])
    } catch (err) {
      setError(err instanceof Error ? err.message : '콘텐츠 생성 중 오류가 발생했습니다.')
      console.error('콘텐츠 생성 오류:', err)
    } finally {
      setIsLoading(false)
    }
  }, [api])

  const updateContentStatus = useCallback((contentId: string, status: string, scheduledDate?: Date) => {
    setContents(prev => prev.map(content => 
      content.id === contentId 
        ? { ...content, status, scheduledDate }
        : content
    ))
  }, [])

  const removeContent = useCallback((contentId: string) => {
    setContents(prev => prev.filter(content => content.id !== contentId))
  }, [])

  const clearContents = useCallback(() => {
    setContents([])
    setError(null)
  }, [])

  return {
    contents,
    isLoading,
    error,
    generateContent,
    updateContentStatus,
    removeContent,
    clearContents
  }
}

// 발행 스케줄 hook
export function usePublishSchedule() {
  const [schedules, setSchedules] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const api = useMarketingApi()

  const scheduleContent = useCallback(async (contentId: string, publishDate: Date, platform: string = 'naver_blog') => {
    setIsLoading(true)
    setError(null)

    try {
      // 실제 API 호출 (개발 환경에서는 모의 처리)
      if (process.env.NODE_ENV === 'development') {
        const newSchedule = {
          id: `schedule_${Date.now()}`,
          contentId,
          platform,
          publishDate,
          status: 'pending' as const
        }
        
        setSchedules(prev => [...prev, newSchedule])
      } else {
        // 실제 API 호출
        const response = await api.publishBlog({
          content_id: contentId,
          blog_config: {
            publish_date: publishDate.toISOString()
          }
        })

        if (response.success) {
          const newSchedule = {
            id: response.data?.publish_id || `schedule_${Date.now()}`,
            contentId,
            platform,
            publishDate,
            status: 'pending' as const
          }
          
          setSchedules(prev => [...prev, newSchedule])
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '발행 예약 중 오류가 발생했습니다.')
      console.error('발행 예약 오류:', err)
    } finally {
      setIsLoading(false)
    }
  }, [api])

  const updateScheduleStatus = useCallback((scheduleId: string, status: string) => {
    setSchedules(prev => prev.map(schedule => 
      schedule.id === scheduleId 
        ? { ...schedule, status }
        : schedule
    ))
  }, [])

  const cancelSchedule = useCallback(async (scheduleId: string) => {
    try {
      const schedule = schedules.find(s => s.id === scheduleId)
      if (schedule) {
        await api.cancelPublish(schedule.contentId)
      }
      
      setSchedules(prev => prev.filter(schedule => schedule.id !== scheduleId))
    } catch (err) {
      setError(err instanceof Error ? err.message : '발행 취소 중 오류가 발생했습니다.')
      console.error('발행 취소 오류:', err)
    }
  }, [schedules, api])

  return {
    schedules,
    isLoading,
    error,
    scheduleContent,
    updateScheduleStatus,
    cancelSchedule
  }
}

// 통합 마케팅 데이터 hook
export function useMarketingData() {
  const keywordHook = useKeywordAnalysis()
  const contentHook = useContentGeneration()
  const scheduleHook = usePublishSchedule()

  const stats = {
    totalKeywords: keywordHook.keywords.length,
    totalContents: contentHook.contents.length,
    scheduledContents: contentHook.contents.filter(c => c.status === 'scheduled').length,
    publishedContents: contentHook.contents.filter(c => c.status === 'published').length,
    averageSeoScore: contentHook.contents.length > 0 
      ? Math.round(contentHook.contents.reduce((sum, c) => sum + c.seoScore, 0) / contentHook.contents.length) 
      : 0
  }

  const isLoading = keywordHook.isLoading || contentHook.isLoading || scheduleHook.isLoading
  const hasError = keywordHook.error || contentHook.error || scheduleHook.error

  return {
    // 통계
    stats,
    isLoading,
    hasError,
    
    // 키워드 관련
    keywords: keywordHook.keywords,
    analyzeKeywords: keywordHook.analyzeKeywords,
    clearKeywords: keywordHook.clearKeywords,
    keywordError: keywordHook.error,
    
    // 콘텐츠 관련
    contents: contentHook.contents,
    generateContent: contentHook.generateContent,
    updateContentStatus: contentHook.updateContentStatus,
    removeContent: contentHook.removeContent,
    clearContents: contentHook.clearContents,
    contentError: contentHook.error,
    isGeneratingContent: contentHook.isLoading,
    
    // 스케줄 관련
    schedules: scheduleHook.schedules,
    scheduleContent: scheduleHook.scheduleContent,
    updateScheduleStatus: scheduleHook.updateScheduleStatus,
    cancelSchedule: scheduleHook.cancelSchedule,
    scheduleError: scheduleHook.error,
    isScheduling: scheduleHook.isLoading
  }
}