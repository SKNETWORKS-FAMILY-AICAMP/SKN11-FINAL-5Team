"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Mail } from "lucide-react"
import type { ContentTemplate, EmailContent, EmailTemplate } from "../types"

interface EmailTemplateListProps {
  templates: EmailTemplate[]         // 관리자 템플릿
  contents: EmailContent[]           // 사용자 콘텐츠
  selectedTemplate: EmailTemplate | EmailContent | null
  onTemplateSelect: (template: EmailTemplate | EmailContent) => void
}

export function EmailTemplateList({
  templates,
  contents,
  selectedTemplate,
  onTemplateSelect,
}: EmailTemplateListProps) {
  const [emailLeftTab, setEmailLeftTab] = useState("templates")

  return (
    <Card className="rounded-xl border-0 shadow-sm bg-white">
      <CardHeader className="pb-3">
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
          <Button
            variant={emailLeftTab === "templates" ? "default" : "ghost"}
            className={`rounded-md text-xs px-3 py-1 h-7 ${
              emailLeftTab === "templates" ? "bg-white shadow-sm text-gray-900" : "hover:bg-gray-200 text-gray-600"
            }`}
            onClick={() => setEmailLeftTab("templates")}
          >
            템플릿
          </Button>
          <Button
            variant={emailLeftTab === "sent" ? "default" : "ghost"}
            className={`rounded-md text-xs px-3 py-1 h-7 ${
              emailLeftTab === "sent" ? "bg-white shadow-sm text-gray-900" : "hover:bg-gray-200 text-gray-600"
            }`}
            onClick={() => setEmailLeftTab("sent")}
          >
            컨텐츠 목록
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[500px]">
          <div className="space-y-2">
            {emailLeftTab === "templates"
              ? templates.map((template) => (
                  <Card
                    key={template.id}
                    className={`cursor-pointer transition-colors rounded-lg ${
                      selectedTemplate?.id === template.id
                        ? "border-green-500 bg-green-50"
                        : "hover:bg-gray-50 border-gray-200"
                    }`}
                    onClick={() => onTemplateSelect(template)}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-center space-x-2 mb-2">
                        <Mail className="h-4 w-4 text-blue-600" />
                        <h4 className="font-medium text-sm">{template.title}</h4>
                      </div>
                      <p className="text-xs text-gray-600 line-clamp-2">{template.content}</p>
                    </CardContent>
                  </Card>
                ))
              : contents.map((content) => (
                  <Card
                    key={content.id}
                    className={`cursor-pointer transition-colors rounded-lg ${
                      selectedTemplate?.id === content.id
                        ? "border-green-500 bg-green-50"
                        : "hover:bg-gray-50 border-gray-200"
                    }`}
                    onClick={() => onTemplateSelect(content)}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <Mail className="h-4 w-4 text-blue-600" />
                          <h4 className="font-medium text-sm line-clamp-1">{content.title}</h4>
                        </div>
                        <span className="text-xs text-gray-400">{content.createdAt}</span>
                      </div>
                      <p className="text-xs text-gray-600 line-clamp-2">{content.content}</p>
                    </CardContent>
                  </Card>
                ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
