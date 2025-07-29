"use client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Instagram, FileText } from "lucide-react"
import { format } from "date-fns"
import type { AutomationTask } from "../types"

interface AiContentListProps {
  contents: AutomationTask[]
  onContentSelect: (content: AutomationTask) => void
}

export function AiContentList({ contents, onContentSelect }: AiContentListProps) {
  return (
    <Card className="rounded-xl border-0 shadow-sm bg-white">
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-medium text-gray-900">AI 생성 컨텐츠</CardTitle>
      </CardHeader>
      <CardContent className="px-4">
        <ScrollArea className="h-[500px]">
          <div className="space-y-3">
            {contents && contents.length > 0 ? (
              contents.map((content) => (
                <Card
                  key={content.task_id}
                  onClick={() => onContentSelect(content)}
                  className="cursor-pointer transition-all duration-200 hover:shadow-md hover:border-gray-300 border border-gray-200 min-h-[120px] bg-white"
                >
                  <CardContent className="py-4 px-4 h-full flex flex-col justify-between">
                    {/* Header Section */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {content.task_data?.platform === "instagram" ? (
                          <>
                            <Instagram className="w-4 h-4 text-pink-500 flex-shrink-0" />
                            <span className="text-xs font-medium text-gray-600">인스타그램</span>
                          </>
                        ) : (
                          <>
                            <FileText className="w-4 h-4 text-green-600 flex-shrink-0" />
                            <span className="text-xs font-medium text-gray-600">네이버</span>
                          </>
                        )}
                      </div>
                      <span className="text-xs text-gray-400 flex-shrink-0">
                        {format(new Date(content.created_at), "yyyy. M. d.")}
                      </span>
                    </div>

                    {/* Content Section */}
                    <div className="flex-1 space-y-1">
                      <h4 className="text-sm font-semibold text-gray-900 line-clamp-1">{content.title}</h4>
                      <p className="text-xs text-gray-600 line-clamp-2 leading-relaxed overflow-hidden">
                        {typeof content.task_data?.full_content === "string"
                          ? content.task_data?.full_content
                          : typeof content.task_data?.post_content === "string"
                            ? content.task_data?.post_content
                            : typeof content.task_data?.content === "string"
                              ? content.task_data?.content
                              : Array.isArray(content.task_data?.searched_hashtags)
                                ? content.task_data?.searched_hashtags.join(" ")
                                : "내용 없음"}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <div className="flex items-center justify-center h-[200px] text-gray-500 text-sm">
                생성된 컨텐츠가 없습니다
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
