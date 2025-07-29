// ✅ Google Calendar 반영 포함된 전체 Calendar.tsx (점 색상 분기: 자동화=빨강, 수동+구글=초록)
"use client"

import { useState, useRef, useEffect } from "react"
import axios from "axios"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  CalendarIcon,
  Plus,
  Clock,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  Instagram,
  Mail,
  FileText,
  XCircle,
  AlertCircle,
} from "lucide-react"
import type { ScheduleEvent, AutomationTask } from "../types"
import type { NewEvent } from "@/app/workspace/types"

interface CalendarProps {
  selectedDate?: Date
  setSelectedDate: (date: Date) => void
  scheduleEvents: ScheduleEvent[]
  automationTasks: AutomationTask[]
  googleEvents: any[]
  newEvent: NewEvent
  setNewEvent: (event: NewEvent) => void
  onAddEvent: (event: NewEvent) => void
  userId: number
  getEventsForDate: (date: Date) => {
    manual: ScheduleEvent[]
    automation: AutomationTask[]
    google: any[]
  }
  upcomingEvents: any[]
  fetchUpcomingEvents: () => Promise<void>
}

export function Calendar({
  selectedDate,
  setSelectedDate,
  scheduleEvents = [],
  automationTasks = [],
  googleEvents = [],
  newEvent,
  setNewEvent,
  onAddEvent,
  userId,
  upcomingEvents = [],
  fetchUpcomingEvents,
  getEventsForDate,
}: CalendarProps) {
  const [isEventDialogOpen, setIsEventDialogOpen] = useState(false)
  const [currentDate, setCurrentDate] = useState(new Date())
  const [isTaxIntegrationOpen, setIsTaxIntegrationOpen] = useState(false)
  const [copySuccess, setCopySuccess] = useState(false)
  const [isEventDetailOpen, setIsEventDetailOpen] = useState(false)
  const [selectedDateForDetail, setSelectedDateForDetail] = useState<Date | null>(null)
  const dueDateRef = useRef<HTMLInputElement>(null)
  const [taskLists, setTaskLists] = useState<any[]>([])
  const [selectedTaskListId, setSelectedTaskListId] = useState<string>("")
  const [tasks, setTasks] = useState<any[]>([])

  useEffect(() => {
    fetchTaskLists()
  }, [])

  const fetchTaskLists = async () => {
    try {
      const res = await axios.get("http://localhost:8005/google/tasks", {
        params: { user_id: userId },
      })
      console.log("✅ userId 전달됨:", userId)
      setTaskLists(res.data.items || [])
    } catch (err) {
      console.error("Tasklist 목록 조회 실패:", err)
    }
  }

  const fetchTasksForList = async (tasklistId: string) => {
    try {
      const res = await axios.get(`http://localhost:8005/google/tasks/${tasklistId}`, {
        params: { user_id: userId },
      })
      setTasks(res.data.items || [])
    } catch (err) {
      console.error("작업 목록 불러오기 실패:", err)
    }
  }

  const handleAddTask = async (title: string, dueDate?: string) => {
    if (!selectedTaskListId) {
      alert("먼저 Tasklist를 선택하세요")
      return
    }
    try {
      const dueISO = dueDate ? new Date(dueDate).toISOString() : undefined
      await axios.post("http://localhost:8005/google/tasks", null, {
        params: {
          user_id: userId,
          tasklist_id: selectedTaskListId,
          title,
          due: dueISO,
        },
      })
      fetchTasksForList(selectedTaskListId)
    } catch (err) {
      console.error("할 일 추가 실패:", err)
    }
  }

  const handleCreateTaskList = async (title: string) => {
    try {
      await axios.post("http://localhost:8005/google/tasks/lists", null, {
        params: {
          user_id: userId,
          title,
        },
      })
      fetchTaskLists()
    } catch (err) {
      console.error("Tasklist 생성 실패:", err)
    }
  }

  const handleSelectTaskList = (tasklistId: string) => {
    setSelectedTaskListId(tasklistId)
    fetchTasksForList(tasklistId)
  }

  const handleTaskListCreateClick = () => {
    const listName = prompt("새 목록 이름을 입력하세요:")
    if (listName) {
      handleCreateTaskList(listName)
    }
  }

  const handleTaskListSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    handleSelectTaskList(e.target.value)
  }

  const handleAddEvent = () => {
    onAddEvent(newEvent)
    setIsEventDialogOpen(false)
  }

  const handleCopyLink = async () => {
    const link =
      "https://calendar.google.com/calendar/ical/vsh0ama0r43cn8qoigf94ave8g%40group.calendar.google.com/public/basic.ics"
    try {
      await navigator.clipboard.writeText(link)
      setCopySuccess(true)
      setTimeout(() => setCopySuccess(false), 2000)
    } catch (err) {
      console.error("Failed to copy: ", err)
    }
  }

  const handleDateClick = (date: Date) => {
    setSelectedDate(date)
    setSelectedDateForDetail(date)
    setIsEventDetailOpen(true)
  }

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

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear()
    const month = date.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const daysInMonth = lastDay.getDate()
    const startingDayOfWeek = firstDay.getDay()

    const days = []

    for (let i = startingDayOfWeek - 1; i >= 0; i--) {
      const prevDate = new Date(year, month, -i)
      days.push({
        date: prevDate,
        isCurrentMonth: false,
        isToday: false,
        hasManualOrGoogle: false,
        hasAutomation: false,
      })
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const dayDate = new Date(year, month, day)
      const isToday = dayDate.toDateString() === new Date().toDateString()
      const dayEvents = getEventsForDate(dayDate)
      const hasManualOrGoogle = dayEvents.manual.length > 0 || dayEvents.google.length > 0
      const hasAutomation = dayEvents.automation.length > 0

      days.push({
        date: dayDate,
        isCurrentMonth: true,
        isToday,
        hasManualOrGoogle,
        hasAutomation,
      })
    }

    const remainingDays = 42 - days.length
    for (let day = 1; day <= remainingDays; day++) {
      const nextDate = new Date(year, month + 1, day)
      days.push({
        date: nextDate,
        isCurrentMonth: false,
        isToday: false,
        hasManualOrGoogle: false,
        hasAutomation: false,
      })
    }

    return days
  }

  const navigateMonth = (direction: "prev" | "next") => {
    setCurrentDate((prev) => {
      const newDate = new Date(prev)
      if (direction === "prev") {
        newDate.setMonth(prev.getMonth() - 1)
      } else {
        newDate.setMonth(prev.getMonth() + 1)
      }
      return newDate
    })
  }

  const days = getDaysInMonth(currentDate)
  const weekDays = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]

  const selectedDateEvents = selectedDateForDetail
    ? getEventsForDate(selectedDateForDetail)
    : { manual: [], automation: [], google: [] }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
      <div className="lg:col-span-3">
        <Card className="rounded-xl border-0 shadow-sm bg-white h-[600px] flex flex-col">
          <CardHeader className="pb-3 flex-shrink-0">
            <div className="flex flex-row justify-between items-center">
              <div className="flex items-center space-x-2">
                <CalendarIcon className="h-4 w-4 text-green-600" />
                <span className="text-base font-semibold">일정 캘린더</span>
                <div className="flex items-center space-x-1 text-xs">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-green-600">사용자/구글 일정</span>
                  <div className="w-2 h-2 bg-red-500 rounded-full ml-2"></div>
                  <span className="text-red-600">자동화 업무</span>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Dialog open={isTaxIntegrationOpen} onOpenChange={setIsTaxIntegrationOpen}>
                  <DialogTrigger asChild>
                    <Button
                      variant="outline"
                      className="bg-green-50 hover:bg-green-100 border-green-200 text-green-700 rounded-lg text-sm px-3 py-2 h-8"
                    >
                      💸세무 일정 연동하기
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="rounded-xl max-w-md">
                    <DialogHeader className="relative">
                      <DialogTitle className="text-center text-lg font-semibold mb-4">
                        하단 링크를 구글 캘린더와 연동하세요
                      </DialogTitle>
                      <button
                        onClick={() => setIsTaxIntegrationOpen(false)}
                        className="absolute right-0 top-0 p-1 hover:bg-gray-100 rounded-full text-gray-500 hover:text-gray-700"
                      >
                        ✕
                      </button>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div className="bg-gray-50 p-4 rounded-lg border">
                        <p className="text-sm text-gray-600 mb-3 font-medium text-center">Google Calendar 연동 링크:</p>
                        <div className="bg-white p-3 rounded border text-xs text-gray-800 break-all font-mono mb-3">
                          https://calendar.google.com/calendar/ical/vsh0ama0r43cn8qoigf94ave8g%40group.calendar.google.com/public/basic.ics
                        </div>
                        <div className="flex justify-center">
                          <Button
                            onClick={handleCopyLink}
                            size="sm"
                            className={`${copySuccess ? "bg-green-500 hover:bg-green-600" : "bg-green-500 hover:bg-green-600"}`}
                          >
                            {copySuccess ? "복사됨!" : "복사"}
                          </Button>
                        </div>
                      </div>
                      <div className="text-sm text-gray-600 bg-green-50 p-3 rounded-lg border border-green-200">
                        <p className="font-medium text-green-800 mb-2">💡 연동 방법:</p>
                        <div className="space-y-1 text-green-700">
                          <p>1. 위 링크를 복사하세요</p>
                          <p>2. Google Calendar → "다른 캘린더 추가"</p>
                          <p>3. "URL로 추가"를 선택하고 링크를 붙여넣으세요</p>
                        </div>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>

                <Dialog open={isEventDialogOpen} onOpenChange={setIsEventDialogOpen}>
                  <DialogTrigger asChild>
                    <Button className="bg-green-500 hover:bg-green-600 rounded-lg text-sm px-3 py-2 h-8">
                      <Plus className="h-3 w-3 mr-1" /> 일정 등록
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="rounded-xl">
                    <DialogHeader>
                      <DialogTitle>새 일정 등록</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <Input
                        placeholder="제목"
                        value={newEvent.title}
                        onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                      />
                      <Input
                        type="date"
                        value={newEvent.date}
                        onChange={(e) => setNewEvent({ ...newEvent, date: e.target.value })}
                      />
                      <Input
                        type="time"
                        value={newEvent.time}
                        onChange={(e) => setNewEvent({ ...newEvent, time: e.target.value })}
                      />
                      <Textarea
                        placeholder="설명"
                        value={newEvent.description}
                        onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                      />
                      <Button
                        onClick={handleAddEvent}
                        disabled={!newEvent.title || !newEvent.date || !newEvent.time}
                        className="w-full bg-green-500 hover:bg-green-600"
                      >
                        일정 추가
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-0 flex-1 flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <Button variant="ghost" size="sm" onClick={() => navigateMonth("prev")} className="p-2">
                <ChevronLeft className="h-5 w-5" />
              </Button>
              <h3 className="text-lg font-semibold">
                {currentDate.toLocaleDateString("en-US", { month: "long", year: "numeric" })}
              </h3>
              <Button variant="ghost" size="sm" onClick={() => navigateMonth("next")} className="p-2">
                <ChevronRight className="h-5 w-5" />
              </Button>
            </div>
            <div className="grid grid-cols-7 gap-2 mb-3">
              {weekDays.map((day) => (
                <div key={day} className="text-center text-sm font-medium text-gray-500 py-2">
                  {day}
                </div>
              ))}
            </div>
            <div className="grid grid-cols-7 gap-2 flex-1">
              {days.map((day, index) => {
                const isSelected = selectedDate && day.date.toDateString() === selectedDate.toDateString()
                return (
                  <button
                    key={index}
                    onClick={() => handleDateClick(day.date)}
                    className={`
                      relative p-2 text-sm font-medium rounded-lg transition-colors h-12 flex items-center justify-center
                      ${day.isCurrentMonth ? "text-gray-900" : "text-gray-400"}
                      ${day.isToday ? "bg-green-100 text-green-800 font-bold" : ""}
                      ${isSelected ? "bg-green-500 text-white font-bold" : "hover:bg-gray-100"}
                      ${!day.isCurrentMonth ? "hover:bg-gray-50" : ""}
                    `}
                  >
                    {day.date.getDate()}
                    <div className="absolute bottom-1 left-1/2 transform -translate-x-1/2 flex space-x-1">
                      {day.hasManualOrGoogle && <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>}
                      {day.hasAutomation && <div className="w-1.5 h-1.5 bg-red-500 rounded-full"></div>}
                    </div>
                  </button>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Event Detail Dialog */}
        <Dialog open={isEventDetailOpen} onOpenChange={setIsEventDetailOpen}>
          <DialogContent className="rounded-xl max-w-lg max-h-[80vh] overflow-hidden">
            <DialogHeader>
              <DialogTitle className="flex items-center space-x-2">
                <CalendarIcon className="h-5 w-5 text-green-600" />
                <span>일정 상세보기</span>
                {selectedDateForDetail && (
                  <span className="text-sm text-gray-500 font-normal">
                    (
                    {selectedDateForDetail.toLocaleDateString("ko-KR", {
                      month: "short",
                      day: "numeric",
                      weekday: "short",
                    })}
                    )
                  </span>
                )}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-2">
              {/* 수동 등록 일정 */}
              {(selectedDateEvents.manual || []).map((event) => (
                <Card key={`manual-${event.id}`} className="border-l-4 border-green-500 bg-green-50 rounded-lg">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 mb-2 text-base">{event.title}</h4>
                        <div className="flex items-center text-sm text-gray-600 mb-2">
                          <Clock className="h-4 w-4 mr-2" />
                          <span>{event.time}</span>
                          <span className="ml-3 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                            사용자 일정
                          </span>
                        </div>
                        {event.description && (
                          <div className="mt-3">
                            <p className="text-sm text-gray-600 mb-1">상세 내용:</p>
                            <p className="text-sm text-gray-800 bg-white p-3 rounded border leading-relaxed">
                              {event.description}
                            </p>
                          </div>
                        )}
                      </div>
                      <div className="w-4 h-4 bg-green-500 rounded-full flex-shrink-0" title="사용자 일정"></div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {/* 자동화 업무 일정 */}
              {(selectedDateEvents.automation || []).map((task) => (
                <Card key={`auto-${task.task_id}`} className="border-l-4 border-red-500 bg-red-50 rounded-lg">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 mb-2 text-base">{task.title}</h4>
                        <div className="flex items-center space-x-3 text-sm text-gray-600 mb-2">
                          <div className="flex items-center space-x-1">
                            {getTaskTypeIcon(task.task_type)}
                            <span>{getTaskTypeLabel(task.task_type)}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            {getStatusIcon(task.status)}
                            <span>{task.status}</span>
                          </div>
                        </div>
                        {task.task_data && (
                          <div className="mt-3">
                            <p className="text-sm text-gray-600 mb-1">작업 내용:</p>
                            <div className="text-sm text-gray-800 bg-white p-3 rounded border">
                              {task.task_data.full_content || task.task_data.post_content || "내용 없음"}
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="w-4 h-4 bg-red-500 rounded-full flex-shrink-0" title="자동화 업무"></div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {/* 구글 캘린더 일정 */}
              {(selectedDateEvents.google || []).map((gEvent) => (
                <Card key={`google-${gEvent.id}`} className="border-l-4 border-blue-500 bg-blue-50 rounded-lg">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 mb-2 text-base">
                          {gEvent.summary || "(제목 없음)"}
                        </h4>
                        <div className="flex items-center text-sm text-gray-600 mb-2">
                          <Clock className="h-4 w-4 mr-2" />
                          <span>{gEvent.start?.dateTime?.slice(11, 16) || gEvent.start?.date || "시간 없음"}</span>
                          <span className="ml-3 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                            구글 캘린더
                          </span>
                        </div>
                        {gEvent.description && (
                          <div className="mt-3">
                            <p className="text-sm text-gray-600 mb-1">상세 내용:</p>
                            <p className="text-sm text-gray-800 bg-white p-3 rounded border leading-relaxed">
                              {gEvent.description}
                            </p>
                          </div>
                        )}
                      </div>
                      <div className="w-4 h-4 bg-blue-500 rounded-full flex-shrink-0" title="구글 캘린더"></div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {/* 일정이 없을 때 */}
              {selectedDateEvents.manual.length === 0 &&
                selectedDateEvents.automation.length === 0 &&
                selectedDateEvents.google.length === 0 && (
                  <div className="text-center text-gray-500 py-12">
                    <CalendarIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                    <p className="text-lg">선택된 날짜에 일정이 없습니다</p>
                    <p className="text-sm mt-2">새로운 일정을 추가해보세요!</p>
                  </div>
                )}
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="lg:col-span-2 flex flex-col space-y-4 h-[600px]">
        {/* Enhanced To do list Card with Google Tasks Integration */}
        <Card className="rounded-xl border-0 shadow-sm bg-white h-[400px] flex flex-col">
          <CardHeader className="pb-3 flex-shrink-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-4 w-4 text-blue-600" />
                <span className="text-base font-semibold">To do list</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="text-xs px-2 py-1 h-7 bg-blue-50 hover:bg-blue-100 border-blue-200 text-blue-700"
                onClick={() => {
                  const listName = prompt("새 목록 이름을 입력하세요:")
                  if (listName) {
                    // TODO: API call to POST /google/tasks/lists
                    console.log("Creating new tasklist:", listName)
                  }
                }}
              >
                <Plus className="h-3 w-3 mr-1" />새 목록
              </Button>
            </div>

            {/* Tasklist Selector */}
            <div className="mt-2">
              <select
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                onChange={(e) => {
                  // TODO: API call to GET /google/tasks for selected list
                  console.log("Selected tasklist:", e.target.value)
                }}
              >
                <option value="">목록을 선택하세요</option>
                <option value="default">기본 목록</option>
                <option value="work">업무</option>
                <option value="personal">개인</option>
              </select>
            </div>
          </CardHeader>

          <CardContent className="flex-1 overflow-hidden flex flex-col">
            {/* Task List */}
            <div className="flex-1 overflow-y-auto pr-2 space-y-2">
              {/* Sample tasks - replace with actual data */}
              <div className="flex items-center space-x-3 p-2 hover:bg-gray-50 rounded-lg group">
                <input
                  type="checkbox"
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  onChange={(e) => {
                    // TODO: Update task completion status
                    console.log("Task completed:", e.target.checked)
                  }}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">프로젝트 기획서 작성</p>
                  <p className="text-xs text-gray-500">마감: 2024-01-15</p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="opacity-0 group-hover:opacity-100 p-1 h-6 w-6 text-red-500 hover:text-red-700"
                  onClick={() => {
                    // TODO: Delete task
                    console.log("Delete task")
                  }}
                >
                  <XCircle className="h-4 w-4" />
                </Button>
              </div>

              {/* Completed task example */}
              <div className="flex items-center space-x-3 p-2 hover:bg-gray-50 rounded-lg group opacity-60">
                <input
                  type="checkbox"
                  checked
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  onChange={(e) => {
                    console.log("Task uncompleted:", !e.target.checked)
                  }}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate line-through">회의 자료 준비</p>
                  <p className="text-xs text-gray-500 line-through">마감: 2024-01-10</p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="opacity-0 group-hover:opacity-100 p-1 h-6 w-6 text-red-500 hover:text-red-700"
                  onClick={() => {
                    console.log("Delete completed task")
                  }}
                >
                  <XCircle className="h-4 w-4" />
                </Button>
              </div>

              {/* Empty state when no tasks */}
              <div className="text-sm text-gray-500 text-center py-4 hidden">할 일이 없습니다</div>
            </div>

            {/* Add Task Form */}
            <div className="border-t pt-3 mt-3 space-y-2 flex-shrink-0">
              <div className="flex space-x-2">
                <Input
                  placeholder="새 할 일 추가..."
                  className="flex-1 text-sm h-8"
                  onKeyPress={(e) => {
                    if (e.key === "Enter") {
                      const input = e.target as HTMLInputElement
                      const taskTitle = input.value.trim()
                      const dueDate = dueDateRef.current?.value || ""

                      if (taskTitle) {
                        // TODO: API call to POST /google/tasks
                        console.log(`할 일: '${taskTitle}', 마감일: '${dueDate}'`)

                        // 입력창 초기화
                        input.value = ""
                        if (dueDateRef.current) {
                          dueDateRef.current.value = ""
                        }
                      }
                    }
                  }}
                />
                <Input ref={dueDateRef} type="date" className="w-32 text-sm h-8" title="마감일 (선택사항)" />
              </div>
              <Button
                size="sm"
                className="w-full h-7 text-xs bg-blue-600 hover:bg-blue-700"
                onClick={() => {
                  const titleInput = document.querySelector('input[placeholder="새 할 일 추가..."]') as HTMLInputElement
                  const taskTitle = titleInput?.value.trim() || ""
                  const dueDate = dueDateRef.current?.value || ""

                  if (taskTitle) {
                    // TODO: API call to POST /google/tasks
                    console.log(`할 일: '${taskTitle}', 마감일: '${dueDate}'`)

                    // 입력창 초기화
                    if (titleInput) titleInput.value = ""
                    if (dueDateRef.current) dueDateRef.current.value = ""
                  }
                }}
              >
                추가
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Upcoming Events Card */}
        <Card className="rounded-xl border-0 shadow-sm bg-white h-[200px] flex flex-col">
          <CardHeader className="pb-3 flex-shrink-0">
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-orange-600" />
              <span className="text-base font-semibold">다가오는 일정</span>
            </div>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden">
            <div className="h-full overflow-y-auto pr-2">
              <div className="text-sm text-gray-500 text-center py-8">다가오는 이벤트가 없습니다</div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
