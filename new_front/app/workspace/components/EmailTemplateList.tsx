"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Mail } from "lucide-react"
import type { EmailContent, EmailTemplate } from "../types"

interface EmailTemplateListProps {
  templates: EmailTemplate[] // 관리자 템플릿
  contents: EmailContent[] // 사용자 콘텐츠
  selectedTemplate: EmailTemplate | EmailContent | null
  onTemplateSelect: (template: EmailTemplate | EmailContent) => void
}

// HTML 및 코드 정리 함수
const cleanContent = (content: string): string => {
  if (!content) return "내용 없음"

  return (
    content
      // HTML 태그 완전 제거
      .replace(/<[^>]*>/g, " ")
      // JavaScript/CSS 코드 패턴 제거
      .replace(/const\s+\w+\s*=\s*[^;]+;?/g, " ")
      .replace(/function\s+\w+\s*$$[^)]*$$\s*\{[^}]*\}/g, " ")
      .replace(/\{[^}]*\}/g, " ")
      .replace(/\[[^\]]*\]/g, " ")
      // CSS 스타일 속성 제거
      .replace(/[a-zA-Z-]+\s*:\s*[^;]+;?/g, " ")
      // 특수 문자와 기호 정리
      .replace(/[{}[\]();,]/g, " ")
      .replace(/["'`]/g, " ")
      // 연속된 공백을 하나로 통합
      .replace(/\s+/g, " ")
      // 앞뒤 공백 제거
      .trim() ||
    // 너무 짧으면 기본 메시지
    "템플릿 내용을 확인하세요"
  )
}

export function EmailTemplateList({ templates, contents, selectedTemplate, onTemplateSelect }: EmailTemplateListProps) {
  const [emailLeftTab, setEmailLeftTab] = useState("templates")

  return (
    <Card className="rounded-xl border-0 shadow-sm bg-white">
      <CardHeader className="pb-3">
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
          <Button
            variant={emailLeftTab === "templates" ? "default" : "ghost"}
            className={`rounded-md text-sm font-medium px-3 py-1 h-7 transition-all ${
              emailLeftTab === "templates" ? "bg-white shadow-sm text-gray-900" : "hover:bg-gray-200 text-gray-600"
            }`}
            onClick={() => setEmailLeftTab("templates")}
          >
            템플릿
          </Button>
          <Button
            variant={emailLeftTab === "sent" ? "default" : "ghost"}
            className={`rounded-md text-sm font-medium px-3 py-1 h-7 transition-all ${
              emailLeftTab === "sent" ? "bg-white shadow-sm text-gray-900" : "hover:bg-gray-200 text-gray-600"
            }`}
            onClick={() => setEmailLeftTab("sent")}
          >
            컨텐츠 목록
          </Button>
        </div>
      </CardHeader>
      <CardContent className="px-4">
        <ScrollArea className="h-[500px]">
          <div className="space-y-3">
            {emailLeftTab === "templates"
              ? templates.map((template, index) => (
                  <Card
                    key={template.id || `${template.title}-${index}`}
                    className="cursor-pointer transition-all duration-200 rounded-lg hover:shadow-md hover:border-gray-300 border border-gray-200 min-h-[120px] bg-white"
                    onClick={() => onTemplateSelect(template)}
                  >
                    <CardContent className="py-4 px-4 h-full flex flex-col justify-between">
                      {/* Header Section */}
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <Mail className="h-4 w-4 text-blue-600 flex-shrink-0" />
                          <span className="text-xs font-medium text-gray-600">템플릿</span>
                        </div>
                      </div>

                      {/* Content Section */}
                      <div className="flex-1 space-y-1">
                        <h4 className="text-sm font-semibold text-gray-900 line-clamp-1 break-words">
                          {template.title}
                        </h4>
                        <p className="text-xs text-gray-600 line-clamp-2 leading-relaxed overflow-hidden break-words hyphens-auto">
                          {cleanContent(template.content)}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                ))
              : contents.map((content, index) => (
                  <Card
                    key={content.id || `${content.title}-${index}`}
                    className="cursor-pointer transition-all duration-200 rounded-lg hover:shadow-md hover:border-gray-300 border border-gray-200 min-h-[120px] bg-white"
                    onClick={() => onTemplateSelect(content)}
                  >
                    <CardContent className="py-4 px-4 h-full flex flex-col justify-between">
                      {/* Header Section */}
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <Mail className="h-4 w-4 text-blue-600 flex-shrink-0" />
                          <span className="text-xs font-medium text-gray-600">콘텐츠</span>
                        </div>
                        <span className="text-xs text-gray-400 flex-shrink-0">{content.createdAt}</span>
                      </div>

                      {/* Content Section */}
                      <div className="flex-1 space-y-1">
                        <h4 className="text-sm font-semibold text-gray-900 line-clamp-1 break-words">
                          {content.title}
                        </h4>
                        <p className="text-xs text-gray-600 line-clamp-2 leading-relaxed overflow-hidden break-words hyphens-auto">
                          {cleanContent(content.content)}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
