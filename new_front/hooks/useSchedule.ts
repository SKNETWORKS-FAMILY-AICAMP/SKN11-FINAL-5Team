// src/workspace/hooks/useSchedule.ts
"use client"
import { useEffect, useState } from "react"

export interface ScheduleEvent {
  id: number
  title: string
  date: string // YYYY-MM-DD
  time: string // HH:mm
  description: string
  type: "manual"
}

export function useSchedule() {
  const [events, setEvents] = useState<ScheduleEvent[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchEvents()
  }, [])

  const fetchEvents = () => {
    setLoading(true)

    // TODO: 실제 API 연동 시 대체
    const mock: ScheduleEvent[] = [
      {
        id: 1,
        title: "가을신상 촬영하기",
        date: "2025-07-20",
        time: "14:00",
        description: "가을 신상품 촬영 일정",
        type: "manual",
      },
      {
        id: 2,
        title: "재고 점검",
        date: "2025-07-22",
        time: "10:30",
        description: "월말 재고 점검",
        type: "manual",
      },
    ]

    setTimeout(() => {
      setEvents(mock)
      setLoading(false)
    }, 300)
  }

  const addEvent = (event: Omit<ScheduleEvent, "id">) => {
    const newEvent: ScheduleEvent = {
      id: Date.now(), // 임시 ID
      ...event,
    }
    setEvents((prev) => [...prev, newEvent])
    console.log("📆 일정 추가:", newEvent)
  }

  const deleteEvent = (id: number) => {
    setEvents((prev) => prev.filter((e) => e.id !== id))
    console.log("🗑️ 일정 삭제:", id)
  }

  return {
    events,
    loading,
    addEvent,
    deleteEvent,
    refetch: fetchEvents,
  }
}
