export interface Message {
  sender: "user" | "agent"
  text: string
}

export interface ConversationMessage {
  message_id: number
  role: "user" | "assistant"
  content: string
  timestamp: string
  agent_type: string
}
