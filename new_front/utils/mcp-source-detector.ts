import type { MCPSourceType } from "@/components/ui/mcp-loading-indicator"

// 백엔드 응답에서 source_type 추출하는 유틸리티
export function detectMCPSource(response: any): MCPSourceType | null {
  // 직접적으로 source_type이 있는 경우
  if (response?.source_type) {
    return response.source_type as MCPSourceType
  }

  // metadata에서 찾기
  if (response?.metadata?.source_type) {
    return response.metadata.source_type as MCPSourceType
  }

  // data 객체에서 찾기
  if (response?.data?.source_type) {
    return response.data.source_type as MCPSourceType
  }

  // 응답 내용을 기반으로 추론
  const content = JSON.stringify(response).toLowerCase()

  if (content.includes("appstore") || content.includes("app store")) {
    return "appstore"
  }
  if (content.includes("amazon")) {
    return "amazon"
  }
  if (content.includes("youtube")) {
    return "youtube"
  }
  if (content.includes("google") || content.includes("구글")) {
    return "google_search"
  }
  if (content.includes("naver") || content.includes("네이버")) {
    return "naver_trend"
  }
  if (content.includes("instagram") || content.includes("인스타그램")) {
    return "instagram_hashtag"
  }

  return null
}

// 질문 내용을 기반으로 예상 소스 타입 추론
export function predictMCPSource(query: string): MCPSourceType | null {
  const lowerQuery = query.toLowerCase()

  if (lowerQuery.includes("앱스토어") || lowerQuery.includes("app store") || lowerQuery.includes("앱")) {
    return "appstore"
  }
  if (lowerQuery.includes("아마존") || lowerQuery.includes("amazon") || lowerQuery.includes("쇼핑")) {
    return "amazon"
  }
  if (lowerQuery.includes("유튜브") || lowerQuery.includes("youtube") || lowerQuery.includes("영상")) {
    return "youtube"
  }
  if (lowerQuery.includes("구글") || lowerQuery.includes("google") || lowerQuery.includes("검색")) {
    return "google_search"
  }
  if (lowerQuery.includes("네이버") || lowerQuery.includes("naver") || lowerQuery.includes("트렌드")) {
    return "naver_trend"
  }
  if (lowerQuery.includes("인스타그램") || lowerQuery.includes("instagram") || lowerQuery.includes("해시태그")) {
    return "instagram_hashtag"
  }

  return null
}
