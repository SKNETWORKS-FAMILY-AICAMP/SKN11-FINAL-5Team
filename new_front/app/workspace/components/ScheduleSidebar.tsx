import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Clock, CheckCircle, XCircle, AlertCircle, Instagram, Mail, FileText, Calendar } from "lucide-react"
import type { AutomationTask, ScheduleEvent } from "../types"

interface ScheduleSidebarProps {
  selectedDate: Date | undefined
  getEventsForDate: (date: Date) => {
    manual: ScheduleEvent[]
    automation: AutomationTask[]
    google: any[]
  }
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

  const events = selectedDate ? getEventsForDate(selectedDate) : { manual: [], automation: [], google: [] }

  const CalendarIcon = Calendar

  return (
    <Card className="rounded-xl border-0 shadow-sm bg-white h-full flex flex-col">
      <CardHeader className="pb-3 flex-shrink-0">
        <div className="flex items-center space-x-2">
          <CalendarIcon className="h-4 w-4 text-green-600" />
          <span className="text-base font-semibold">일정 상세보기</span>
          {selectedDate && (
            <span className="text-sm text-gray-500">
              ({selectedDate.toLocaleDateString("ko-KR", { month: "short", day: "numeric", weekday: "short" })})
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden">
        <div className="space-y-3 h-full overflow-y-auto pr-2">
          {/* 수동 등록 일정 */}
          {(events.manual || []).map((event) => (
            <Card
              key={`manual-${event.id}`}
              className="border-l-4 border-green-500 bg-green-50 rounded-lg hover:shadow-md transition-shadow cursor-pointer"
            >
              <CardContent className="p-3">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900 mb-1 text-sm">{event.title}</h4>
                    <div className="flex items-center text-xs text-gray-600 mb-2">
                      <Clock className="h-3 w-3 mr-1" />
                      <span>{event.time}</span>
                      <span className="ml-2 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                        사용자 일정
                      </span>
                    </div>
                    {event.description && (
                      <p className="text-xs text-gray-700 bg-white p-2 rounded border">{event.description}</p>
                    )}
                  </div>
                  <div className="w-3 h-3 bg-green-500 rounded-full flex-shrink-0" title="사용자 일정"></div>
                </div>
              </CardContent>
            </Card>
          ))}

          {/* 자동화 업무 일정 */}
          {(events.automation || []).map((task) => (
            <Card key={`auto-${task.task_id}`} className="border-l-4 border-red-500 bg-red-50 rounded-lg">
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

          {/* 구글 캘린더 일정 */}
          {(events.google || []).map((gEvent) => (
            <Card key={`google-${gEvent.id}`} className="border-l-4 border-green-500 bg-green-50 rounded-lg">
              <CardContent className="p-3">
                <div className="flex items-start justify-between mb-1">
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900 mb-1 text-sm">{gEvent.summary || "(제목 없음)"}</h4>
                    <div className="flex items-center text-xs text-gray-600 mb-1">
                      <Clock className="h-3 w-3 mr-1" />
                      <span>{gEvent.start?.dateTime?.slice(11, 16) || gEvent.start?.date || "시간 없음"}</span>
                    </div>
                    {gEvent.description && <p className="text-xs text-gray-700">{gEvent.description}</p>}
                  </div>
                  <div className="w-3 h-3 bg-green-500 rounded-full flex-shrink-0" title="구글 캘린더"></div>
                </div>
              </CardContent>
            </Card>
          ))}

          {/* 일정이 없을 때 */}
          {events.manual.length === 0 && events.automation.length === 0 && events.google.length === 0 && (
            <div className="text-center text-gray-500 text-sm py-8">선택된 날짜에 일정이 없습니다</div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
