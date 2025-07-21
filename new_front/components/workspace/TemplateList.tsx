"use client"
import { useEffect, useState } from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"

interface Template {
  id: number
  title: string
  tags: string[]
  type: string
  content: string
}

interface Props {
  type: string
  selected: Template | null
  onSelect: (template: Template) => void
}

export default function TemplateList({ type, selected, onSelect }: Props) {
  const [templates, setTemplates] = useState<Template[]>([])

  useEffect(() => {
    // 목 데이터 예시. 실제로는 API 호출로 대체
    const sample = [
      { id: 1, title: "신제품 홍보", tags: ["신제품", "마케팅"], type: "email", content: "<h1>신제품 출시!</h1>" },
      { id: 2, title: "할인 이벤트", tags: ["이벤트", "할인"], type: "email", content: "<h1>특가 세일 중!</h1>" },
    ]
    setTemplates(sample.filter((t) => t.type === type))
  }, [type])

  return (
    <Card className="rounded-xl border-0 shadow-sm bg-white h-[500px]">
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold">템플릿 목록</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[420px]">
          <ul className="space-y-1">
            {templates.map((template) => (
              <li
                key={template.id}
                className={cn(
                  "cursor-pointer px-4 py-2 hover:bg-gray-100",
                  selected?.id === template.id && "bg-gray-100 font-semibold"
                )}
                onClick={() => onSelect(template)}
              >
                <div className="text-sm">{template.title}</div>
                <div className="mt-1 space-x-1">
                  {template.tags.map((tag, idx) => (
                    <Badge key={idx} variant="secondary" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
