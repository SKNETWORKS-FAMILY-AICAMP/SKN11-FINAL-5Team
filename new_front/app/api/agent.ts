import { API_BASE_URL } from '@/config/constants'

export const agentApi = {
  createConversation: async (userId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: userId })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      if (!data.success) {
        return {
          success: false,
          error: data.error || '대화 세션 생성에 실패했습니다'
        }
      }
      return {
        success: true,
        data: {
          conversationId: data.data.conversation_id,
          userId: data.data.user_id,
          title: data.data.title,
          createdAt: data.data.created_at,
          isNew: data.data.is_new
        }
      }
    } catch (error) {
      console.error('Create conversation error:', error)
      return {
        success: false,
        error: 'Failed to create conversation'
      }
    }
  },

  getConversationMessages: async (conversationId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      if (!data.success) {
        return {
          success: false,
          error: data.error || '메시지 목록 조회에 실패했습니다'
        }
      }
      return {
        success: true,
        data: {
          messages: data.data.map((msg: any) => ({
            messageId: msg.message_id,
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp,
            agentType: msg.agent_type
          }))
        }
      }
    } catch (error) {
      console.error('Get messages error:', error)
      return {
        success: false,
        error: '메시지 목록 조회에 실패했습니다'
      }
    }
  },

  sendQuery: async (userId: number, conversationId: number, message: string, agentType: string = 'unified_agent') => {
    try {
      const response = await fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          conversation_id: conversationId,
          message: message,
          agent_type: agentType
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      if (!data.success) {
        return {
          success: false,
          error: data.error || '메시지 전송에 실패했습니다'
        }
      }
      return {
        success: true,
        data: {
          answer: data.data.response,
          agentType: data.data.agent_type,
          confidence: data.data.confidence,
          sources: data.data.sources
        }
      }
    } catch (error) {
      console.error('Send query error:', error)
      return {
        success: false,
        error: '메시지 전송에 실패했습니다'
      }
    }


  },

  sendFeedback: async (userId: number, conversationId: number, rating: number, comment: string, category: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          conversation_id: conversationId,
          rating,
          comment,
          category
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      if (!data.success) {
        return {
          success: false,
          error: data.error || '피드백 전송에 실패했습니다'
        }
      }
      return {
        success: true,
        data: data.data
      }
    } catch (error) {
      console.error('Send feedback error:', error)
      return {
        success: false,
        error: '피드백 전송에 실패했습니다'
      }
    }
  },

  getUserProfile: async (accessToken: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/profile`, {
        headers: {
          Authorization: `Bearer ${accessToken}`
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()

      if (!data.success) {
        return {
          success: false,
          error: data.error || "프로필 불러오기에 실패했습니다"
        }
      }

      return {
        success: true,
        data: data.data
      }
    } catch (error) {
      console.error("getUserProfile error:", error)
      return {
        success: false,
        error: "프로필 불러오기에 실패했습니다"
      }
    }
  },
  getTemplates: async (accessToken: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/templates`, {
        headers: {
          Authorization: `Bearer ${accessToken}`
        }
      })
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }
      return await res.json()
    } catch (err) {
      console.error("템플릿 조회 실패:", err)
      throw err
    }
  }
}