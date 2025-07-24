"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import { format } from "date-fns"
import type {
  ScheduleEvent,
  NewEvent,
  PublishSchedule,
  AutomationTask,
} from "../types"

export function useSchedule() {
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [automationTasks, setAutomationTasks] = useState<AutomationTask[]>([])
  const [scheduleEvents, setScheduleEvents] = useState<ScheduleEvent[]>([])
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

  const userId = JSON.parse(localStorage.getItem("user") || "{}")?.user_id || 1

  useEffect(() => {
    const fetchAutomationTasks = async () => {
      try {
        const res = await axios.get("http://localhost:8005/workspace/automation", {
          params: { user_id: userId },
        })
        setAutomationTasks(res.data.data.tasks)
      } catch (err) {
        console.error("자동화 업무 불러오기 실패:", err)
      }
    }

    fetchAutomationTasks()
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

const getEventsForDate = (date: Date) => {
  const dateStr = date.toISOString().slice(0, 10)

  const manualEvents = scheduleEvents.filter(event => event.date === dateStr)
  const automationEvents = automationTasks.filter(task => task.scheduled_at?.startsWith(dateStr))

  return {
    manual: manualEvents,
    automation: automationEvents,
  }
}
  const addEvent = (event: NewEvent) => {
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
  }

  const deleteTask = async (taskId: number) => {
    try {
      await axios.delete(`http://localhost:8005/workspace/automation/${taskId}`)
      setAutomationTasks((prev) => prev.filter((task) => task.task_id !== taskId))
    } catch (err) {
      console.error("업무 삭제 실패:", err)
    }
  }

  const updateTask = async (task: AutomationTask) => {
    try {
      const res = await axios.put(`http://localhost:8005/workspace/automation/${task.task_id}`, task)
      console.log("업무 업데이트 완료:", res.data)
    } catch (err) {
      console.error("업무 업데이트 실패:", err)
    }
  }

  const publishContent = async (
    title: string,
    content: string,
    type: string,  // "email" | "instagram" | "blog"
    toEmail?: string
  ) => {
    try {
      // 1. 자동화 등록
      const automationRes = await axios.post("http://localhost:8005/workspace/automation", {
        user_id: userId,
        task_type: "send_email",
        title,
        task_data: {
          to_emails: [toEmail],
          subject: title,
          body: content,
          html_body: content
        },
        scheduled_at: null,
      })
      console.log("📌 자동화 등록 완료:", automationRes.data)


      return true
    } catch (err) {
      console.error("❌ 콘텐츠 발행 실패:", err)
      return false
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
    publishContent,
  }
}
