// src/workspace/hooks/useTemplates.ts
"use client"
import { useEffect, useState } from "react"

export interface Template {
  id: number
  type: "email" | "sns" | "message"
  title: string
  content: string
  tags: string[]
}

export function useTemplates(type: Template["type"]) {
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)

    // TODO: 실제 API 연동 시 fetch(`/api/templates?type=${type}`) 등으로 교체
    const mockData: Template[] = [
      {
        id: 1,
        type: "email",
        title: "고객 감사 메일",
        content: "안녕하세요, 고객님 감사합니다!",
        tags: ["감사", "고객"],
      },
      {
        id: 2,
        type: "sns",
        title: "인스타 신상품 소개",
        content: "🌟 신상품 출시! 🌟",
        tags: ["신상품", "SNS"],
      },
    ]

    const filtered = mockData.filter((t) => t.type === type)
    setTimeout(() => {
      setTemplates(filtered)
      setLoading(false)
    }, 300) // simulate delay
  }, [type])

  return { templates, loading }
}
