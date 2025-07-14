import { API_BASE_URL } from '@/config/constants'

export interface ConversationResponse {
  status: string
  data: {
    conversation_id: number
    user_id: number
    title: string
    created_at: string
    is_new: boolean
  }
}

export interface MessageResponse {
  status: string
  data: {
    messages: Array<{
      message_id: number
      role: 'user' | 'assistant'
      content: string
      timestamp: string
      agent_type: string
    }>
  }
}

export interface FeedbackResponse {
  status: string
  data: {
    feedback_id: number
    created_at: string
  }
}

export const agentApi = {
  // 대화 세션 생성
  createConversation: async (userId: number, title?: string) => {
    const response = await fetch(`${API_BASE_URL}/conversations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ user_id: userId, title }),
    })
    return response.json() as Promise<ConversationResponse>
  },

  // 대화 메시지 목록 조회
  getConversationMessages: async (conversationId: number, limit: number = 50) => {
    const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages?limit=${limit}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    return response.json() as Promise<MessageResponse>
  },

  // 에이전트 쿼리 전송
  sendQuery: async (userId: number, conversationId: number, message: string, agentType: string = 'unified_agent') => {
    const port = {
      unified_agent: 8000,
      planner: 8001,
      marketing: 8002,
      crm: 8003,
      task: 8004,
      mentalcare: 8005,
    }[agentType] || 8000

    const endpoint = agentType === 'unified_agent' 
      ? `http://localhost:${port}/query`
      : `http://localhost:${port}/agent/query`

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        conversation_id: conversationId,
        message,
        persona: 'common',
      }),
    })
    return response.json()
  },

  // 피드백 전송
  sendFeedback: async (userId: number, conversationId: number, rating: number, comment: string, category: string) => {
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
        category,
      }),
    })
    return response.json() as Promise<FeedbackResponse>
  },
}