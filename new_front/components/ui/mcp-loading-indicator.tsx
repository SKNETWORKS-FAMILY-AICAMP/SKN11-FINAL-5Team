import Image from "next/image"
import { Loader2 } from "lucide-react"

// MCP 소스 타입별 설정
const MCP_SOURCE_CONFIG = {
  appstore: {
    icon: "/icons/app_store.png", // 로컬 이미지 경로로 변경
    label: "App Store 인기 앱 분석 중...",
    color: "text-blue-600",
    bgColor: "bg-blue-50",
    borderColor: "border-blue-200",
  },
  amazon: {
    icon: "/icons/amazon.png",
    label: "아마존 인기 상품 분석 중...",
    color: "text-orange-600",
    bgColor: "bg-orange-50",
    borderColor: "border-orange-200",
  },
  youtube: {
    icon: "/icons/youtube.png",
    label: "유튜브 트렌드 분석 중...",
    color: "text-red-600",
    bgColor: "bg-red-50",
    borderColor: "border-red-200",
  },
  google_search: {
    icon: "/icons/google.png",
    label: "구글 검색 트렌드 분석 중...",
    color: "text-blue-600",
    bgColor: "bg-blue-50",
    borderColor: "border-blue-200",
  },
  naver_trend: {
    icon: "/icons/naver.png",
    label: "네이버 트렌드 분석 중...",
    color: "text-green-600",
    bgColor: "bg-green-50",
    borderColor: "border-green-200",
  },
  instagram_hashtag: {
    icon: "/icons/instagram.png",
    label: "인스타그램 해시태그 분석 중...",
    color: "text-pink-600",
    bgColor: "bg-pink-50",
    borderColor: "border-pink-200",
  },
} as const

export type MCPSourceType = keyof typeof MCP_SOURCE_CONFIG

interface MCPLoadingIndicatorProps {
  sourceType: MCPSourceType
  className?: string
}

export function MCPLoadingIndicator({ sourceType, className = "" }: MCPLoadingIndicatorProps) {
  const config = MCP_SOURCE_CONFIG[sourceType]

  if (!config) {
    return (
      <div
        className={`inline-flex items-center gap-3 px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 w-fit ${className}`}
      >
        <Loader2 className="w-4 h-4 animate-spin text-gray-600" />
        <span className="text-sm font-medium text-gray-700">분석 중...</span>
      </div>
    )
  }

  return (
    <div
      className={`inline-flex items-center gap-3 px-4 py-3 rounded-lg ${config.bgColor} border ${config.borderColor} w-fit ${className}`}
    >
      <div className="w-6 h-6 rounded-full overflow-hidden bg-white shadow-sm flex-shrink-0">
        <Image
          src={config.icon || "/placeholder.svg"}
          alt={sourceType}
          width={24}
          height={24}
          className="w-full h-full object-cover"
        />
      </div>
      <span className={`text-sm font-medium ${config.color} flex-1 text-center`}>{config.label}</span>
      <Loader2 className={`w-4 h-4 animate-spin ${config.color}`} />
    </div>
  )
}

interface MCPMultiLoadingProps {
  sources: MCPSourceType[]
  className?: string
}

export function MCPMultiLoading({ sources, className = "" }: MCPMultiLoadingProps) {
  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {sources.map((source) => (
        <MCPLoadingIndicator key={source} sourceType={source} />
      ))}
    </div>
  )
}
