// export interface Message {
//   sender: "user" | "agent"
//   text: string
// }

// export interface ConversationMessage {
//   message_id: number
//   role: "user" | "assistant"
//   content: string
//   timestamp: string
//   agent_type: string
// }

// 기존 Message 타입에 추가
import type { MCPSourceType } from "@/components/ui/mcp-loading-indicator"

export interface Message {
  sender: "user" | "agent"
  text: string
  isComplete?: boolean
  isTyping?: boolean
  mcpSourceType?: MCPSourceType | null // 🎯 새로운 필드 추가
}

export interface ExtendedMessage extends Message {
  isTyping?: boolean
  isComplete?: boolean
  mcpSourceType?: MCPSourceType | null // 🎯 새로운 필드 추가
}
