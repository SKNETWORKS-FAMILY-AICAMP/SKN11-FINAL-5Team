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

  sendQuery: async (userId: number, conversationId: number, message: string, agentType: string = 'unified_agent',projectId: number | null) => {
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
          preferred_agent: agentType
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      // 백엔드가 UnifiedResponse 모델을 직접 반환하는 경우
      if (data.conversation_id !== undefined) {
        return {
          success: true,
          data: {
            conversationId: data.conversation_id,
            agentType: data.agent_type,
            answer: data.response, // 백엔드의 'response' 필드를 'answer'로 매핑
            confidence: data.confidence,
            routingDecision: data.routing_decision,
            sources: data.sources,
            metadata: data.metadata,
            processingTime: data.processing_time,
            timestamp: data.timestamp,
            alternatives: data.alternatives?.map((alt: any) => ({
              agentType: alt.agent_type,
              response: alt.response,
              confidence: alt.confidence,
              sources: alt.sources,
              metadata: alt.metadata,
              processingTime: alt.processing_time
            })) || []
          }
        }
      }
      
      // 표준 응답 구조인 경우
      if (!data.success) {
        return {
          success: false,
          error: data.error || '메시지 전송에 실패했습니다'
        }
      }
      
      return {
        success: true,
        data: {
          conversationId: data.data.conversation_id,
          agentType: data.data.agent_type,
          answer: data.data.response, // 백엔드의 'response' 필드를 'answer'로 매핑
          confidence: data.data.confidence,
          routingDecision: data.data.routing_decision,
          sources: data.data.sources,
          metadata: data.data.metadata,
          processingTime: data.data.processing_time,
          timestamp: data.data.timestamp,
          alternatives: data.data.alternatives?.map((alt: any) => ({
            agentType: alt.agent_type,
            response: alt.response,
            confidence: alt.confidence,
            sources: alt.sources,
            metadata: alt.metadata,
            processingTime: alt.processing_time
          })) || []
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
  }
}