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
  ListTodo,
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
  const [upcomingEventsData, setUpcomingEventsData] = useState<any[]>([])
  const [isLoadingUpcoming, setIsLoadingUpcoming] = useState(false)
  const [isTaskListDialogOpen, setIsTaskListDialogOpen] = useState(false)
  const [newTaskListTitle, setNewTaskListTitle] = useState("")
  const [isTaskDialogOpen, setIsTaskDialogOpen] = useState(false)
  const [newTaskTitle, setNewTaskTitle] = useState("")
  const [newTaskDue, setNewTaskDue] = useState("")
  const [isLoadingTasks, setIsLoadingTasks] = useState(false)

  useEffect(() => {
    if (userId) {
      fetchTaskLists()
      fetchUpcomingEventsFromAPI()
    }
  }, [userId])

  

  const fetchTaskLists = async () => {
    if (!userId) {
      console.warn("userId가 없어서 Google Tasks 조회를 건너뜁니다.")
      return
    }
    
    try {
    const res = await axios.get("https://localhost:8005/google/tasks", {
      params: { user_id: userId },
    })
      console.log("✅ userId 전달됨:", userId)
      setTaskLists(res.data.items || [])
    } catch (err: any) {
      console.error("Tasklist 목록 조회 실패:", err)
    }
  }

  const fetchUpcomingEventsFromAPI = async () => {
    if (!userId) {
      console.warn("userId가 없어서 다가오는 일정 조회를 건너뜁니다.")
      return
    }
    
    setIsLoadingUpcoming(true)
    try {
      const res = await axios.get("https://localhost:8005/events/upcoming", {
        params: { 
          user_id: userId,
          days: 7,
          calendar_id: "primary"
        },
      })
      
      if (res.data.success) {
        setUpcomingEventsData(res.data.events || [])
      } else {
        console.error("다가오는 일정 조회 실패:", res.data)
        setUpcomingEventsData([])
      }
    } catch (err) {
      console.error("다가오는 일정 조회 실패:", err)
      setUpcomingEventsData([])
    } finally {
      setIsLoadingUpcoming(false)
    }
  }

  const fetchTasksForList = async (tasklistId: string) => {
    setIsLoadingTasks(true)
    try {
      const res = await axios.get(`https://localhost:8005/google/tasks/${tasklistId}`, {
        params: { user_id: userId },
      })
      setTasks(res.data.items || [])
    } catch (err) {
      console.error("작업 목록 불러오기 실패:", err)
    } finally {
      setIsLoadingTasks(false)
    }
  }

  const handleAddTask = async (title: string, dueDate?: string) => {
    if (!selectedTaskListId) {
      alert("먼저 Tasklist를 선택하세요")
      return
    }
    try {
      const dueISO = dueDate ? new Date(dueDate).toISOString() : undefined
      await axios.post("https://localhost:8005/google/tasks", null, {
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
      await axios.post("https://localhost:8005/google/tasks/lists", null, {
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

  // 다이얼로그용 함수들
  const handleCreateTaskListDialog = async () => {
    if (!newTaskListTitle.trim()) return
    
    try {
      await axios.post("https://localhost:8005/google/tasks/lists", null, {
        params: {
          user_id: userId,
          title: newTaskListTitle,
        },
      })
      fetchTaskLists()
      setIsTaskListDialogOpen(false)
      setNewTaskListTitle("")
    } catch (err) {
      console.error("Tasklist 생성 실패:", err)
    }
  }

  const handleAddTaskDialog = async () => {
    if (!newTaskTitle.trim() || !selectedTaskListId) return
    
    try {
      const dueISO = newTaskDue ? new Date(newTaskDue).toISOString() : undefined
      await axios.post("https://localhost:8005/google/tasks", null, {
        params: {
          user_id: userId,
          tasklist_id: selectedTaskListId,
          title: newTaskTitle,
          due: dueISO,
        },
      })
      fetchTasksForList(selectedTaskListId)
      setIsTaskDialogOpen(false)
      setNewTaskTitle("")
      setNewTaskDue("")
    } catch (err) {
      console.error("할 일 추가 실패:", err)
    }
  }

  const handleToggleTaskStatus = async (taskId: string, currentStatus: string) => {
    if (!selectedTaskListId) return
    
    try {
      // // 현재 상태에 따라 새로운 상태 결정
      // const newStatus = currentStatus === "completed" ? "needsAction" : "completed"
      
      // await axios.patch(`https://localhost:8005/google/tasks/${selectedTaskListId}/${taskId}`, null, {
      //   params: {
      //     user_id: userId,
      //     status: newStatus,
      //   },
      // })
      
      // 작업 목록 새로고침
      fetchTasksForList(selectedTaskListId)
    } catch (err) {
      console.error("작업 상태 변경 실패:", err)
    }
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

  // HTML을 안전하게 처리하는 함수
  const sanitizeAndRenderHTML = (htmlString: string) => {
    if (!htmlString) return null
    
    const cleanHTML = htmlString
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<u>(.*?)<\/u>/gi, '$1')
      .replace(/<\/?[^>]+(>|$)/g, '')
      .trim()
    
    return cleanHTML
  }

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
                        <div className="flex items-center text-sm text-gray-600 mb-2">
                          <Clock className="h-4 w-4 mr-2" />
                          <span>
                            {task.scheduled_at
                              ? new Date(task.scheduled_at).toLocaleTimeString("ko-KR", {
                                  hour: "2-digit",
                                  minute: "2-digit",
                                  hour12: false,
                                })
                              : "시간 미정"}
                          </span>
                          <span className="ml-3 px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs">
                            자동화 업무
                          </span>
                        </div>
                        <div className="flex items-center space-x-2 mb-2">
                          {getTaskTypeIcon(task.task_type)}
                          <span className="text-sm text-gray-600">{getTaskTypeLabel(task.task_type)}</span>
                          {getStatusIcon(task.status)}
                          <span className="text-sm text-gray-600">{task.status}</span>
                        </div>
                        {task.task_data && (
                          <div className="mt-3">
                            <p className="text-sm text-gray-600 mb-1">작업 내용:</p>
                            <div className="text-sm text-gray-800 bg-white p-3 rounded border">
                              {typeof task.task_data === "string"
                                ? task.task_data
                                : JSON.stringify(task.task_data, null, 2)}
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="w-4 h-4 bg-red-500 rounded-full flex-shrink-0" title="자동화 업무"></div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {/* Google Calendar 일정 */}
              {(selectedDateEvents.google || []).map((event, index) => {
                const eventTime = event.start?.dateTime
                  ? new Date(event.start.dateTime).toLocaleTimeString("ko-KR", {
                      hour: "2-digit",
                      minute: "2-digit",
                      hour12: false,
                    })
                  : "종일"
                
                const cleanDescription = sanitizeAndRenderHTML(event.description || event.summary || "")
                
                return (
                  <Card key={`google-${index}`} className="border-l-4 border-blue-500 bg-blue-50 rounded-lg">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-900 mb-2 text-base">
                            {event.summary || "제목 없음"}
                          </h4>
                          <div className="flex items-center text-sm text-gray-600 mb-2">
                            <Clock className="h-4 w-4 mr-2" />
                            <span>{eventTime}</span>
                            <span className="ml-3 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                              Google 캘린더
                            </span>
                          </div>
                          {cleanDescription && (
                            <div className="mt-3">
                              <p className="text-sm text-gray-600 mb-1">상세 내용:</p>
                              <div className="text-sm text-gray-800 bg-white p-3 rounded border leading-relaxed whitespace-pre-line">
                                {cleanDescription}
                              </div>
                            </div>
                          )}
                        </div>
                        <div className="w-4 h-4 bg-blue-500 rounded-full flex-shrink-0" title="Google 캘린더"></div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}

              {/* 일정이 없는 경우 */}
              {selectedDateEvents.manual.length === 0 &&
                selectedDateEvents.automation.length === 0 &&
                selectedDateEvents.google.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <CalendarIcon className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                    <p>이 날짜에는 등록된 일정이 없습니다.</p>
                  </div>
                )}
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* 오른쪽 사이드바 - To-do List 추가 */}
      <div className="lg:col-span-2 space-y-4">
        {/* Google Tasks To-do List */}
        <Card className="rounded-xl border-0 shadow-sm bg-white">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <ListTodo className="h-4 w-4 text-blue-600" />
                <span className="text-base font-semibold">Google Tasks</span>
              </div>
              <div className="flex items-center space-x-2">
                <Dialog open={isTaskListDialogOpen} onOpenChange={setIsTaskListDialogOpen}>
                  <DialogTrigger asChild>
                    <Button variant="outline" size="sm" className="text-xs px-2 py-1 h-7">
                      <Plus className="h-3 w-3 mr-1" /> 목록
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="rounded-xl max-w-md">
                    <DialogHeader>
                      <DialogTitle>새 작업 목록 만들기</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <Input
                        placeholder="작업 목록 이름"
                        value={newTaskListTitle}
                        onChange={(e) => setNewTaskListTitle(e.target.value)}
                        onKeyPress={(e) => e.key === "Enter" && handleCreateTaskListDialog()}
                      />
                      <div className="flex space-x-2">
                        <Button
                          onClick={handleCreateTaskListDialog}
                          disabled={!newTaskListTitle.trim()}
                          className="flex-1 bg-blue-500 hover:bg-blue-600"
                        >
                          생성
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => {
                            setIsTaskListDialogOpen(false)
                            setNewTaskListTitle("")
                          }}
                          className="flex-1"
                        >
                          취소
                        </Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
                
                <Dialog open={isTaskDialogOpen} onOpenChange={setIsTaskDialogOpen}>
                  <DialogTrigger asChild>
                    <Button size="sm" className="bg-blue-500 hover:bg-blue-600 text-xs px-2 py-1 h-7">
                      <Plus className="h-3 w-3 mr-1" /> 할 일
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="rounded-xl max-w-md">
                    <DialogHeader>
                      <DialogTitle>새 할 일 추가</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <Input
                        placeholder="할 일 제목"
                        value={newTaskTitle}
                        onChange={(e) => setNewTaskTitle(e.target.value)}
                        onKeyPress={(e) => e.key === "Enter" && handleAddTaskDialog()}
                      />
                      <Input
                        type="date"
                        value={newTaskDue}
                        onChange={(e) => setNewTaskDue(e.target.value)}
                        placeholder="마감일 (선택사항)"
                      />
                      <div className="flex space-x-2">
                        <Button
                          onClick={handleAddTaskDialog}
                          disabled={!newTaskTitle.trim() || !selectedTaskListId}
                          className="flex-1 bg-blue-500 hover:bg-blue-600"
                        >
                          추가
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => {
                            setIsTaskDialogOpen(false)
                            setNewTaskTitle("")
                            setNewTaskDue("")
                          }}
                          className="flex-1"
                        >
                          취소
                        </Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            {/* 작업 목록 선택 */}
            {taskLists.length > 0 && (
              <div className="mb-4">
                <select
                  value={selectedTaskListId}
                  onChange={(e) => handleSelectTaskList(e.target.value)}
                  className="w-full p-2 border rounded-lg text-sm bg-white"
                >
                  <option value="">작업 목록 선택</option>
                  {taskLists.map((list) => (
                    <option key={list.id} value={list.id}>
                      {list.title}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* 로딩 상태 */}
            {isLoadingTasks && (
              <div className="text-center py-4 text-gray-500">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto mb-2"></div>
                <p className="text-sm">로딩 중...</p>
              </div>
            )}

            {/* 작업 목록이 없는 경우 */}
            {!isLoadingTasks && taskLists.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <ListTodo className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                <p className="text-sm mb-2">Google Tasks 목록이 없습니다.</p>
                <p className="text-xs text-gray-400">새 목록을 만들어 시작하세요!</p>
              </div>
            )}

            {/* 선택된 목록의 작업들 */}
            {!isLoadingTasks && selectedTaskListId && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700 mb-2">작업 목록</h4>
                {tasks.length === 0 ? (
                  <p className="text-xs text-gray-500 text-center py-4">작업이 없습니다.</p>
                ) : (
                  tasks.map((task) => (
                    <div
                      key={task.id}
                      className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex-1">
                        <h4 className={`text-sm font-medium mb-1 ${
                          task.status === "completed" 
                            ? "text-gray-500 line-through" 
                            : "text-gray-900"
                        }`}>
                          {task.title}
                        </h4>
                        {task.due && (
                          <div className="flex items-center text-xs text-gray-500">
                            <Clock className="h-3 w-3 mr-1" />
                            <span>
                              마감: {new Date(task.due).toLocaleDateString("ko-KR")}
                            </span>
                          </div>
                        )}
                        {task.status === "completed" && (
                          <div className="flex items-center text-xs text-green-600 mt-1">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            <span>완료됨</span>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center space-x-1">
                        <button
                          onClick={() => handleToggleTaskStatus(task.id, task.status)}
                          className="p-1 hover:bg-gray-200 rounded transition-colors"
                          title={task.status === "completed" ? "미완료로 변경" : "완료로 변경"}
                        >
                          {task.status === "completed" ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : (
                            <div className="w-4 h-4 border-2 border-gray-300 rounded-full hover:border-green-400 transition-colors"></div>
                          )}
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 다가오는 일정 카드 */}
        <Card className="rounded-xl border-0 shadow-sm bg-white">
          <CardHeader className="pb-3">
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-orange-600" />
              <span className="text-base font-semibold">다가오는 일정</span>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            {isLoadingUpcoming ? (
              <div className="text-center py-4 text-gray-500">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-orange-500 mx-auto mb-2"></div>
                <p className="text-sm">로딩 중...</p>
              </div>
            ) : upcomingEventsData.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Clock className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                <p className="text-sm">다가오는 일정이 없습니다.</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[300px] overflow-y-auto">
                {upcomingEventsData.slice(0, 5).map((event, index) => {
                  const eventDate = event.start?.dateTime
                    ? new Date(event.start.dateTime)
                    : event.start?.date
                    ? new Date(event.start.date)
                    : null
                  
                  const eventTime = event.start?.dateTime
                    ? new Date(event.start.dateTime).toLocaleTimeString("ko-KR", {
                        hour: "2-digit",
                        minute: "2-digit",
                        hour12: false,
                      })
                    : "종일"
                  
                  return (
                    <div key={index} className="flex items-start space-x-3 p-3 bg-orange-50 rounded-lg">
                      <div className="w-2 h-2 bg-orange-500 rounded-full mt-2 flex-shrink-0"></div>
                      <div className="flex-1">
                        <h4 className="text-sm font-medium text-gray-900 mb-1">
                          {event.summary || "제목 없음"}
                        </h4>
                        <div className="flex items-center text-xs text-gray-500">
                          <Clock className="h-3 w-3 mr-1" />
                          <span>
                            {eventDate
                              ? `${eventDate.toLocaleDateString("ko-KR", {
                                  month: "short",
                                  day: "numeric",
                                })} ${eventTime}`
                              : "날짜 미정"}
                          </span>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
