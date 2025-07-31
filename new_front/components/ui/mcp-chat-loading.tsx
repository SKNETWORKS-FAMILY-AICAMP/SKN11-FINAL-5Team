import { MCPLoadingIndicator, type MCPSourceType } from "./mcp-loading-indicator"

interface MCPChatLoadingProps {
  sourceType?: MCPSourceType
  message?: string
  className?: string
}

export function MCPChatLoading({ sourceType, message, className = "" }: MCPChatLoadingProps) {
  if (sourceType) {
    return (
      <div className={`flex flex-col space-y-2 ${className}`}>
        {message && <div className="text-sm text-gray-600 mb-2">{message}</div>}
        <MCPLoadingIndicator sourceType={sourceType} />
      </div>
    )
  }

  // 기본 로딩 (소스 타입 없음)
  return (
    <div className={`flex items-center gap-2 text-sm text-gray-600 ${className}`}>
      <div className="w-4 h-4 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin"></div>
      {message || "분석 중..."}
    </div>
  )
}
