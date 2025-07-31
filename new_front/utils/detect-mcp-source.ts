import type { MCPSourceType } from "@/components/ui/mcp-loading-indicator"

// 백엔드 응답에서 source_type 추출
export function detectMCPSource(response: any): MCPSourceType | null {
  if (response?.source_type) return response.source_type
  if (response?.metadata?.source_type) return response.metadata.source_type
  if (response?.data?.source_type) return response.data.source_type
  return null
}

// 사용자 질문에서 예상 소스 추론
export function predictMCPSource(query: string): MCPSourceType | null {
  const lower = query.toLowerCase()
  
  // 직접적인 플랫폼 언급
  if (lower.includes("앱스토어") || lower.includes("app store")) return "appstore"
  if (lower.includes("아마존") || lower.includes("amazon")) return "amazon"
  if (lower.includes("유튜브") || lower.includes("youtube")) return "youtube"
  if (lower.includes("구글") || lower.includes("google")) return "google_search"
  if (lower.includes("네이버") || lower.includes("naver")) return "naver_trend"
  if (lower.includes("인스타그램") || lower.includes("instagram")) return "instagram_hashtag"
  
  // 앱 관련 키워드 - 앱스토어 우선
  if (lower.includes("앱 개발") || lower.includes("앱개발") || 
      lower.includes("어떤앱") || lower.includes("어떤 앱") ||
      lower.includes("앱 만들기") || lower.includes("앱만들기") ||
      lower.includes("모바일 앱") || lower.includes("모바일앱") ||
      lower.includes("app development") || lower.includes("mobile app")) {
    return "appstore"
  }
  
  // 트렌드 관련 키워드 - 네이버 트렌드 우선
  if (lower.includes("트렌드") || lower.includes("trend") ||
      lower.includes("인기") || lower.includes("popular") ||
      lower.includes("요즘") || lower.includes("최근") ||
      lower.includes("핫한") || lower.includes("hot")) {
    return "naver_trend"
  }
  
  // 쇼핑/상품 관련 키워드 - 아마존 우선
  if (lower.includes("쇼핑") || lower.includes("shopping") ||
      lower.includes("상품") || lower.includes("product") ||
      lower.includes("구매") || lower.includes("buy") ||
      lower.includes("판매") || lower.includes("sell")) {
    return "amazon"
  }
  
  // 동영상/콘텐츠 관련 키워드 - 유튜브 우선
  if (lower.includes("동영상") || lower.includes("video") ||
      lower.includes("콘텐츠") || lower.includes("content") ||
      lower.includes("영상") || lower.includes("채널") ||
      lower.includes("channel")) {
    return "youtube"
  }
  
  // 해시태그/소셜미디어 관련 키워드 - 인스타그램 우선
  if (lower.includes("해시태그") || lower.includes("hashtag") ||
      lower.includes("#") || lower.includes("태그") ||
      lower.includes("소셜") || lower.includes("social")) {
    return "instagram_hashtag"
  }
  
  // 검색 관련 키워드 - 구글 검색 우선
  if (lower.includes("검색") || lower.includes("search") ||
      lower.includes("찾기") || lower.includes("find") ||
      lower.includes("정보") || lower.includes("info")) {
    return "google_search"
  }

  return null
}