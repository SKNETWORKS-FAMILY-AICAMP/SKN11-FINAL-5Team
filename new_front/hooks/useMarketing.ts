import { useState, useEffect, useCallback } from 'react'
import { useMarketingApi, type KeywordAnalysisRequest, type ContentGenerationRequest } from '@/lib/api/marketing'
import { useRouter } from 'next/navigation'

// Instagram 포스팅 관련 hook 추가
export function useInstagramPosting() {
  const router = useRouter()
  // const { checkInstagramConnection } = useMarketingApi()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [generatedContent, setGeneratedContent] = useState<{
    content: string
    hashtags: string[]
    platform: string
  } | null>(null)
  const [isPosting, setIsPosting] = useState(false)
  const [isScheduling, setIsScheduling] = useState(false)
  const [hasGeneratedContent, setHasGeneratedContent] = useState(false)
  const [isConnected, setIsConnected] = useState<boolean | null>(null)
  const [instagramUsername, setInstagramUsername] = useState<string | null>(null)

  // 생성된 콘텐츠 저장 (모달은 열지 않음)
  const saveGeneratedContent = useCallback((contentData: {
    content: string
    hashtags: string[]
    platform: string
  }) => {
    console.log('[DEBUG] saveGeneratedContent 호출됨:', contentData)
    setGeneratedContent(contentData)
    setHasGeneratedContent(true)
    console.log('[DEBUG] 콘텐츠 저장 완료, 버튼 표시 준비')
  }, [])

  // Instagram 연동 상태 확인 함수
  // const checkConnection = useCallback(async (userId: number) => {
  //   try {
  //     const result = await checkInstagramConnection(userId)
  //     if (result.success) {
  //       setIsConnected(result.data.is_connected)
  //       setInstagramUsername(result.data.username || null)
  //       return result.data.is_connected
  //     }
  //     return false
  //   } catch (error) {
  //     console.error('Instagram 연동 상태 확인 실패:', error)
  //     setIsConnected(false)
  //     return false
  //   }
  // }, [checkInstagramConnection])

  // 실제로 모달을 여는 함수 (연동 상태 체크 포함)
  const openPostingModal = useCallback(async () => {
    console.log('[DEBUG] 모달 열기 버튼 클릭됨')
    
    // 사용자 ID 가져오기
    const storedUser = localStorage.getItem('user')
    if (!storedUser) {
      alert('로그인이 필요합니다.')
      return
    }
    
    let userId: number
    try {
      const user = JSON.parse(storedUser)
      userId = user.user_id
    } catch (error) {
      console.error('사용자 정보 파싱 오류:', error)
      alert('사용자 정보를 불러올 수 없습니다.')
      return
    }
    
    // Instagram 연동 상태 확인
    // const connected = await checkConnection(userId)
    
    // if (!connected) {
    //   // 연동되지 않았을 때 안내 메시지
    //   const confirmGoToMyPage = confirm(
    //     'Instagram 계정이 연동되지 않았습니다.\n\n'
    //     + '마이페이지에서 Instagram 계정을 연동하시겠습니까?'
    //   )
      
    //   if (confirmGoToMyPage) {
    //     router.push('/mypage')
    //   }
    //   return
    // }
    
    // 연동되어 있으면 모달 열기
    setIsModalOpen(true)
  }, [router])
  // }, [checkConnection, router])

  const closePostingModal = useCallback(() => {
    setIsModalOpen(false)
    setGeneratedContent(null)
    setHasGeneratedContent(false)
    setIsConnected(null)
    setInstagramUsername(null)
  }, [])

  const postToInstagram = useCallback(async (content: string, images: File[]) => {
    setIsPosting(true)
    try {
      // 실제 Instagram API 호출
      const formData = new FormData()
      formData.append('content', content)
      images.forEach((image, index) => {
        formData.append(`image_${index}`, image)
      })

      const response = await fetch('/api/instagram/post', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error('Instagram 포스팅 실패')
      }

      const result = await response.json()
      return result
    } catch (error) {
      console.error('Instagram 포스팅 오류:', error)
      throw error
    } finally {
      setIsPosting(false)
    }
  }, [])

  const scheduleInstagramPost = useCallback(async (content: string, images: File[], scheduledTime: Date) => {
    setIsScheduling(true)
    try {
      // 사용자 ID 가져오기
      const storedUser = localStorage.getItem('user')
      if (!storedUser) {
        throw new Error('로그인이 필요합니다.')
      }
      
      let user_id: number
      try {
        const user = JSON.parse(storedUser)
        user_id = user.user_id
      } catch (error) {
        throw new Error('사용자 정보를 불러올 수 없습니다.')
      }
  
      // 이미지를 S3에 업로드하고 URL 받기
      let image_url = ''
      if (images.length > 0) {
        const formData = new FormData()
        formData.append('image', images[0]) // 첫 번째 이미지만 사용
        
        const uploadResponse = await fetch('/api/upload/s3', {
          method: 'POST',
          body: formData
        })
        
        if (!uploadResponse.ok) {
          throw new Error('이미지 업로드 실패')
        }
        
        const uploadResult = await uploadResponse.json()
        image_url = uploadResult.url // S3 업로드된 이미지 URL
      }
  
      // 요청된 구조로 task_data 구성
      const api_post_data = {
        caption: content,
        image_url: image_url
      }
  
      const requestData = {
        user_id: user_id,
        task_type: "sns_publish_instagram",
        title: "Instagram 포스트 예약",
        task_data: {
          user_id: user_id,
          caption: api_post_data["caption"],
          image_url: api_post_data["image_url"]
        },
        scheduled_at: scheduledTime.toISOString()
      }
  
      // task_agent의 /automation/task 엔드포인트 호출
      const response = await fetch('https://localhost:8005/automation/task', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      })
  
      if (!response.ok) {
        throw new Error('Instagram 예약 실패')
      }
  
      const result = await response.json()
      return result
    } catch (error) {
      console.error('Instagram 예약 오류:', error)
      throw error
    } finally {
      setIsScheduling(false)
    }
  }, [])

  return {
    isModalOpen,
    generatedContent,
    isPosting,
    isScheduling,
    hasGeneratedContent,
    isConnected,
    instagramUsername,
    saveGeneratedContent,
    openPostingModal,
    closePostingModal,
    postToInstagram,
    scheduleInstagramPost
    // checkConnection
  }
}