import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Clock, CheckCircle, XCircle, AlertCircle, Instagram, Mail, FileText } from "lucide-react"
import type { AutomationTask, ScheduleEvent } from "../types"

interface ScheduleSidebarProps {
  selectedDate: Date | undefined
  getEventsForDate: (date: Date) => { manual: ScheduleEvent[]; automation: AutomationTask[] }
}

export function ScheduleSidebar({ selectedDate, getEventsForDate }: ScheduleSidebarProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "발행 완료":
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "발행 전":
        return <Clock className="h-4 w-4 text-yellow-600" />
      case "오류":
        return <XCircle className="h-4 w-4 text-red-600" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-600" />
    }
  }

  const getTaskTypeIcon = (taskType: string) => {
    switch (taskType) {
      case "instagram":
      case "sns":
        return <Instagram className="h-4 w-4 text-pink-600" />
      case "email":
        return <Mail className="h-4 w-4 text-blue-600" />
      default:
        return <FileText className="h-4 w-4 text-gray-600" />
    }
  }

  const getTaskTypeLabel = (taskType: string) => {
    const labels = {
      instagram: "인스타그램",
      sns: "SNS",
      email: "이메일",
    }
    return labels[taskType as keyof typeof labels] || taskType
  }

  return (
    <Card className="rounded-xl border-0 shadow-sm bg-white h-[500px]">
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold">
          {selectedDate?.toLocaleDateString("ko-KR", {
            year: "numeric",
            month: "long",
            day: "numeric",
          })}{" "}
          일정
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[380px]">
          <div className="space-y-3">
            {selectedDate &&
              (() => {
                const events = getEventsForDate(selectedDate)
                const hasEvents = (events.manual?.length || 0) > 0 || (events.automation?.length || 0) > 0
                if (!hasEvents) {
                  return (
                    <div className="flex items-center justify-center h-[300px]">
                      <p className="text-gray-500 text-center text-sm">선택된 날짜에 일정이 없습니다</p>
                    </div>
                  )
                }
                return (
                  <>
                    {/* 수동 등록 일정 */}
                    {events.manual.map((event) => (
                      <Card key={`manual-${event.id}`} className="border-l-4 border-purple-500 bg-purple-50 rounded-lg">
                        <CardContent className="p-3">
                          <div className="flex items-start justify-between mb-1">
                            <div className="flex-1">
                              <h4 className="font-semibold text-gray-900 mb-1 text-sm">{event.title}</h4>
                              <div className="flex items-center text-xs text-gray-600 mb-1">
                                <Clock className="h-3 w-3 mr-1" />
                                <span>{event.time}</span>
                              </div>
                              {event.description && <p className="text-xs text-gray-700">{event.description}</p>}
                            </div>
                            <div className="w-3 h-3 bg-purple-500 rounded-full flex-shrink-0" title="사용자 일정"></div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                    {/* 자동화 업무 일정 */}
                    {events.automation.map((task) => (
                      <Card key={`auto-${task.id}`} className="border-l-4 border-red-500 bg-red-50 rounded-lg">
                        <CardContent className="p-3">
                          <div className="flex items-start justify-between mb-1">
                            <div className="flex-1">
                              <h4 className="font-semibold text-gray-900 mb-1 text-sm">{task.title}</h4>
                              <div className="flex items-center space-x-2 text-xs text-gray-600 mb-1">
                                <div className="flex items-center space-x-1">
                                  {getTaskTypeIcon(task.task_type)}
                                  <span>{getTaskTypeLabel(task.task_type)}</span>
                                </div>
                                <div className="flex items-center space-x-1">
                                  {getStatusIcon(task.status)}
                                  <span>{task.status}</span>
                                </div>
                              </div>
                            </div>
                            <div className="w-3 h-3 bg-red-500 rounded-full flex-shrink-0" title="자동화 업무"></div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </>
                )
              })()}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
