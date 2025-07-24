"use client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Instagram, FileText } from "lucide-react"
import type { AutomationTask } from "../types"

interface AiContentListProps {
  contents: AutomationTask[]
  onContentSelect: (content: AutomationTask) => void
}

export function AiContentList({ contents, onContentSelect }: AiContentListProps) {
  return (
    <Card className="rounded-xl border-0 shadow-sm bg-white">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">AI 생성 콘텐츠</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[500px]">
          <div className="space-y-3">
            {contents.length > 0 ? (
              contents.map((content) => (
              <Card
                key={content.task_id}
                onClick={() => onContentSelect(content)}
                className="cursor-pointer transition-colors rounded-lg border hover:bg-gray-50 border-gray-200"
              >
                  <CardContent className="p-3">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {content.task_data?.platform === "instagram" ? (
                          <Instagram className="h-4 w-4 text-pink-600" />
                        ) : (
                          <FileText className="h-4 w-4 text-green-600" />
                        )}
                        <span className="text-xs text-gray-500 capitalize">
                          {content.task_data?.platform === "instagram" ? "인스타그램" : "네이버"}
                        </span>
                      </div>
                      <span className="text-xs text-gray-400">
                        {new Date(content.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <h4 className="font-medium text-sm mb-2 line-clamp-2">{content.title}</h4>
                    <p className="text-xs text-gray-600 line-clamp-2 mb-2">
                      {content.task_data?.content}
                    </p>
                  </CardContent>
                </Card>
              ))
            ) : (
              <div className="flex items-center justify-center h-[200px] text-gray-500 text-sm">
                생성된 콘텐츠가 없습니다
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
