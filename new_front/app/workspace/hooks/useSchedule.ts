"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import { format } from "date-fns"
import type {
  ScheduleEvent,
  NewEvent,
  PublishSchedule,
  AutomationTask,
  GoogleCalendarEvent,
  EventCreate 
} from "../types"

export function useSchedule(userId: number | null) {
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [automationTasks, setAutomationTasks] = useState<AutomationTask[]>([])
  const [scheduleEvents, setScheduleEvents] = useState<ScheduleEvent[]>([])
  const [googleEvents, setGoogleEvents] = useState<GoogleCalendarEvent[]>([])
  const [newEvent, setNewEvent] = useState<NewEvent>({
    title: "",
    date: "",
    time: "",
    description: "",
  })
  const [publishSchedule, setPublishSchedule] = useState<PublishSchedule>({
    date: "",
    time: "",
    type: "immediate",
  })
  

  useEffect(() => {
    if (!userId) return

    const fetchAutomationTasks = async () => {
      try {
        const res = await axios.get("https://localhost:8005/workspace/automation", {
          params: { user_id: userId },
        })
        console.log("📦 자동화 작업 응답:", res.data)
        setAutomationTasks(res.data?.data?.tasks || [])
      } catch (err) {
        console.error("자동화 작업 불러오기 실패:", err)
      }
    }

    const fetchGoogleCalendarEvents = async () => {
      const start = new Date()
      const end = new Date()
      end.setDate(end.getDate() + 30)

      const startDate = start.toISOString().split("T")[0]
      const endDate = end.toISOString().split("T")[0]

      console.log("📅 구글 캘린더 요청 날짜 범위:", startDate, endDate)

      const events = await getGoogleCalendarEvents(userId, startDate, endDate)
      console.log("📅 구글 캘린더에서 받은 이벤트:", events)
      setGoogleEvents(events)
    }

    fetchAutomationTasks()
    fetchGoogleCalendarEvents()
  }, [userId])

  useEffect(() => {
    const events: ScheduleEvent[] = automationTasks.map((task) => ({
      id: task.task_id,
      title: task.title,
      date: task.scheduled_at ? format(new Date(task.scheduled_at), "yyyy-MM-dd") : "",
      time: task.scheduled_at ? format(new Date(task.scheduled_at), "HH:mm") : "",
      description: task.task_data?.content || "",
      type: "automation",
    }))
    setScheduleEvents(events)
  }, [automationTasks])


  const [upcomingEvents, setUpcomingEvents] = useState<any[]>([])

const fetchUpcomingEvents = async () => {
  try {
    const res = await axios.get("https://localhost:8005/events/upcoming", {
      params: { user_id: userId, days: 7 }
    })

    console.log("🔥 서버 응답 원본:", res.data) // 전체 응답 구조 확인

    const events = res.data?.events || []
    console.log("📆 가공한 이벤트 목록:", events) // 실제로 뽑은 배열 확인

    setUpcomingEvents(events)

  } catch (err) {
    console.error("❌ 다가오는 이벤트 조회 실패:", err)
  }
}

  const getEventsForDate = (date: Date) => {
    const dateStr = date.toISOString().split("T")[0]

    const manualEvents = scheduleEvents.filter(event => event.date === dateStr)
    const automationEvents = automationTasks.filter(task => task.scheduled_at?.startsWith(dateStr))
    const googleDayEvents = googleEvents.filter((ev: GoogleCalendarEvent) => {
  const raw = ev.start?.dateTime || ev.start?.date
  if (!raw) return false
  const eventDate = new Date(raw).toISOString().split("T")[0]
  const selectedDateStr = date.toISOString().split("T")[0]
  return eventDate === selectedDateStr
})
    const result = {
      manual: manualEvents,
      automation: automationEvents,
      google: googleDayEvents,
    }

    // console.log("🧩 getEventsForDate 결과:", dateStr, result)
    return result
  }
  const deleteTask = async (taskId: number) => {
    try {
      await axios.delete(`https://localhost:8005/workspace/automation/${taskId}`)
      setAutomationTasks((prev) => prev.filter((task) => task.task_id !== taskId))
    } catch (err) {
      console.error("업무 삭제 실패:", err)
    }
  }

  const updateTask = async (task: AutomationTask) => {
    try {
      const res = await axios.put(`https://localhost:8005/workspace/automation/${task.task_id}`, task)
      console.log("업무 업데이트 완료:", res.data)
    } catch (err) {
      console.error("업무 업데이트 실패:", err)
    }
  }

  const publishContent = async (
    title: string,
    task_data: any,
    type: string,
    toEmail?: string,
    tags: string[] = []
  ) => {
    if (!userId) {
      console.warn("❌ userId가 없습니다. 콘텐츠 발행 불가")
      return false
    }

    try {
      let task_type = ""
      let endpoint = ""
      const status = "PENDING"

      if (type === "email") {
        task_type = "send_email"
        endpoint = "https://localhost:8005/workspace/automation/ai"
        task_data = {
          to_emails: [toEmail],
          subject: title,
          body: task_data.content,
          html_body: task_data.content,
          platform: "email",
        }
      } else if (type === "instagram") {
        task_type = "sns_publish_instagram"
        endpoint = "https://localhost:8005/workspace/automation/ai"
        task_data = {
          ...task_data,
          platform: "instagram",
          searched_hashtags: tags,
        }
      } else if (type === "naver") {
        task_type = "sns_publish_blog"
        endpoint = "https://localhost:8005/workspace/automation/ai"
        task_data = {
          ...task_data,
          platform: "naver_blog",
          top_keywords: tags,
        }
      } else {
        console.warn("❌ 알 수 없는 type 값:", type)
        return false
      }

      const automationRes = await axios.post(endpoint, {
        user_id: userId,
        task_type,
        title,
        task_data,
        platform: task_data.platform,
        content: task_data.full_content || task_data.post_content || "",
        scheduled_at: null,
        status,
      })

      console.log("📌 자동화 등록 완료:", automationRes.data)
      return true
    } catch (err: any) {
      console.error("❌ 콘텐츠 발행 실패:", err?.response?.data || err.message || err)
      return false
    }
  }

  async function getGoogleCalendarEvents(userId: number, start: string, end: string) {
    if (!userId || !start || !end) {
      console.warn("❗ 필수 파라미터 누락:", { userId, start, end })
      return []
    }

    try {
      console.log("🟢 구글 캘린더 API 호출", {
        user_id: userId,
        start_date: start,
        end_date: end,
        calendar_id: "all",
      })

      const res = await axios.get("https://localhost:8005/events", {
        params: {
          user_id: userId,
          start_date: start,
          end_date: end,
          calendar_id: "all",
        },
      })

      console.log("📨 구글 API 응답 전체:", res.data)
      const events = res.data.data?.items || []

      if (events.length > 0) {
        console.log("🔍 첫 번째 구글 이벤트:", events[0])
      } else {
        console.log("❗ 구글 이벤트 없음")
      }

      return events
    } catch (err: any) {
      console.error("❌ 구글 캘린더 일정 조회 실패:", err?.response?.data || err.message || err)
      return []
    }
  }
  const addEvent = async (event: NewEvent) => {
  const newSchedule: ScheduleEvent = {
    id: Date.now(),
    title: event.title,
    date: event.date,
    time: event.time,
    description: event.description,
    type: "manual",
  }

  setScheduleEvents((prev) => [...prev, newSchedule])
  setNewEvent({ title: "", date: "", time: "", description: "" })

  // ⏱️ 구글 캘린더에도 등록 요청
  try {
    const startTime = `${event.date}T${event.time}:00`
    const endTime = new Date(new Date(startTime).getTime() + 60 * 60 * 1000).toISOString() // +1시간

    const payload = {
      title: event.title,
      description: event.description,
      start_time: startTime,
      end_time: endTime,
      calendar_id: "primary",
      timezone: "Asia/Seoul",
    }

    const res = await axios.post("https://localhost:8005/events", payload, {
      params: { user_id: userId },
    })

    console.log("✅ 구글 캘린더 등록 완료:", res.data)
  } catch (err: any) {
    console.error("❌ 구글 캘린더 등록 실패:", err?.response?.data || err.message)
  }
}

  
  return {
    selectedDate,
    setSelectedDate,
    automationTasks,
    scheduleEvents,
    newEvent,
    setNewEvent,
    publishSchedule,
    setPublishSchedule,
    getEventsForDate,
    addEvent,
    deleteTask,
    updateTask,
    googleEvents,
    publishContent,
    upcomingEvents,
    fetchUpcomingEvents,
  }
}