import { MCPChatLoading } from "./mcp-chat-loading"
import type { MCPSourceType } from "./mcp-loading-indicator"

interface EnhancedTypingAnimationProps {
  sourceType?: MCPSourceType
  message?: string
  className?: string
}

export function EnhancedTypingAnimation({ sourceType, message, className = "" }: EnhancedTypingAnimationProps) {
  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      {sourceType ? (
        <MCPChatLoading sourceType={sourceType} message={message} />
      ) : (
        <div className="flex items-center space-x-2">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
          </div>
          <span className="text-sm text-gray-500">{message || "답변 중입니다..."}</span>
        </div>
      )}
    </div>
  )
}
