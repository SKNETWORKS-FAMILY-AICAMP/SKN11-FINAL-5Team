"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { CalendarIcon, Plus, ChevronLeft, ChevronRight } from "lucide-react"
import type { AutomationTask, ScheduleEvent } from "../types"
import type { NewEvent } from "@/app/workspace/types"

interface CalendarProps {
  selectedDate: Date | undefined
  setSelectedDate: (date: Date) => void
  scheduleEvents: ScheduleEvent[]
  automationTasks: AutomationTask[]
  newEvent: NewEvent
  setNewEvent: (event: NewEvent) => void
  onAddEvent: (event: NewEvent) => void
}

export function Calendar({
  selectedDate,
  setSelectedDate,
  scheduleEvents,
  automationTasks,
  newEvent,
  setNewEvent,
  onAddEvent,
}: CalendarProps) {
  const [isEventDialogOpen, setIsEventDialogOpen] = useState(false)

const handleAddEvent = () => {
  onAddEvent(newEvent)
  setIsEventDialogOpen(false)
}

  return (
    <Card className="rounded-xl border-0 shadow-sm bg-white h-[500px]">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CalendarIcon className="h-4 w-4 text-green-600" />
            <span className="text-base font-semibold">일정 캘린더</span>
          </div>
          <Dialog open={isEventDialogOpen} onOpenChange={setIsEventDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-green-500 hover:bg-green-600 rounded-lg text-sm px-3 py-2 h-8">
                <Plus className="h-3 w-3 mr-1" />
                일정 등록
              </Button>
            </DialogTrigger>
            <DialogContent className="rounded-xl">
              <DialogHeader>
                <DialogTitle>새 일정 등록</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="eventTitle">일정 제목</Label>
                  <Input
                    id="eventTitle"
                    placeholder="일정 제목을 입력하세요"
                    value={newEvent.title}
                    onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                    className="rounded-lg"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="eventDate">날짜</Label>
                  <Input
                    id="eventDate"
                    type="date"
                    value={newEvent.date}
                    onChange={(e) => setNewEvent({ ...newEvent, date: e.target.value })}
                    className="rounded-lg"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="eventTime">시간</Label>
                  <Input
                    id="eventTime"
                    type="time"
                    value={newEvent.time}
                    onChange={(e) => setNewEvent({ ...newEvent, time: e.target.value })}
                    className="rounded-lg"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="eventDescription">설명</Label>
                  <Textarea
                    id="eventDescription"
                    placeholder="일정 설명을 입력하세요"
                    value={newEvent.description}
                    onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                    className="rounded-lg"
                  />
                </div>
                <Button
                  onClick={handleAddEvent}
                  className="w-full bg-green-500 hover:bg-green-600 rounded-lg"
                  disabled={!newEvent.title || !newEvent.date || !newEvent.time}
                >
                  일정 추가
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
        {/* 범례 */}
        <div className="mt-3">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <span className="text-xs text-gray-600">사용자 일정</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-red-500 rounded-full"></div>
              <span className="text-xs text-gray-600">자동화 업무</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {/* 커스텀 캘린더 */}
        <div className="space-y-3">
          {/* 월 네비게이션 */}
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 rounded-lg"
              onClick={() => {
                const newDate = new Date(selectedDate || new Date())
                newDate.setMonth(newDate.getMonth() - 1)
                setSelectedDate(newDate)
              }}
            >
              <ChevronLeft className="h-3 w-3" />
            </Button>
            <h3 className="text-sm font-semibold">
              {selectedDate?.toLocaleDateString("en-US", { month: "long", year: "numeric" }) || "July 2025"}
            </h3>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 rounded-lg"
              onClick={() => {
                const newDate = new Date(selectedDate || new Date())
                newDate.setMonth(newDate.getMonth() + 1)
                setSelectedDate(newDate)
              }}
            >
              <ChevronRight className="h-3 w-3" />
            </Button>
          </div>
          {/* 요일 헤더 */}
          <div className="grid grid-cols-7 gap-1 text-center text-xs font-medium text-gray-500">
            <div className="p-1">Su</div>
            <div className="p-1">Mo</div>
            <div className="p-1">Tu</div>
            <div className="p-1">We</div>
            <div className="p-1">Th</div>
            <div className="p-1">Fr</div>
            <div className="p-1">Sa</div>
          </div>
          {/* 날짜 그리드 */}
          <div className="grid grid-cols-7 gap-1">
            {(() => {
              const currentDate = selectedDate || new Date(2025, 6, 25)
              const year = currentDate.getFullYear()
              const month = currentDate.getMonth()
              const firstDay = new Date(year, month, 1)
              const startDate = new Date(firstDay)
              startDate.setDate(startDate.getDate() - firstDay.getDay())
              const days = []
              const currentDateForLoop = new Date(startDate)

              for (let i = 0; i < 42; i++) {
                const dateString = currentDateForLoop.toISOString().split("T")[0]
                const isCurrentMonth = currentDateForLoop.getMonth() === month
                const isSelected = selectedDate && currentDateForLoop.toDateString() === selectedDate.toDateString()
                const hasManualEvents = scheduleEvents.some((event) => event.date === dateString)
                const hasAutomationTasks = automationTasks?.some((task) => task.scheduled_at === dateString)

                days.push(
                  <div key={i} className="relative">
                    <button
                      className={`w-full h-9 text-xs rounded-lg hover:bg-gray-100 transition-colors flex items-center justify-center ${
                        isSelected
                          ? "bg-green-100 text-green-900 font-semibold"
                          : isCurrentMonth
                            ? "text-gray-900"
                            : "text-gray-400"
                      }`}
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        setSelectedDate(new Date(currentDateForLoop))
                      }}
                    >
                      {currentDateForLoop.getDate()}
                    </button>
                    <div className="absolute bottom-0.5 left-1/2 transform -translate-x-1/2 flex space-x-0.5">
                      {hasManualEvents && <div className="w-1 h-1 bg-purple-500 rounded-full"></div>}
                      {hasAutomationTasks && <div className="w-1 h-1 bg-red-500 rounded-full"></div>}
                    </div>
                  </div>,
                )
                currentDateForLoop.setDate(currentDateForLoop.getDate() + 1)
              }
              return days
            })()}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
