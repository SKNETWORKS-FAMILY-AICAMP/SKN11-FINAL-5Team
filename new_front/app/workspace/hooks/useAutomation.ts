// src/workspace/hooks/useAutomation.ts
"use client"
import { useEffect, useState } from "react"

export interface AutomationTask {
  id: number
  task_type: "instagram" | "email"
  title: string
  status: "발행 완료" | "발행 전" | "오류"
  created_at: string
  scheduled_at: string
  task_data: string
}

export function useAutomation() {
  const [tasks, setTasks] = useState<AutomationTask[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchTasks()
  }, [])

  const fetchTasks = () => {
    setLoading(true)

    // TODO: 실제 API 요청으로 대체
    const mock: AutomationTask[] = [
      {
        id: 1,
        task_type: "instagram",
        title: "인스타 포스트",
        status: "발행 완료",
        created_at: "2025-07-18",
        scheduled_at: "2025-07-20",
        task_data: JSON.stringify({
          content: "✨ 여름 신상 출시 ✨",
          image_url: "/placeholder.svg",
        }),
      },
      {
        id: 2,
        task_type: "email",
        title: "신규회원 이메일",
        status: "발행 전",
        created_at: "2025-07-19",
        scheduled_at: "2025-07-22",
        task_data: JSON.stringify({
          subject: "환영합니다!",
          content: "10% 할인 쿠폰을 드려요!",
        }),
      },
    ]

    setTimeout(() => {
      setTasks(mock)
      setLoading(false)
    }, 300)
  }

  const deleteTask = (taskId: number) => {
    setTasks((prev) => prev.filter((task) => task.id !== taskId))
    console.log("🗑️ 삭제됨:", taskId)
  }

  const updateTaskData = (taskId: number, newData: string) => {
    setTasks((prev) =>
      prev.map((task) => (task.id === taskId ? { ...task, task_data: newData } : task))
    )
    console.log("💾 데이터 저장:", taskId)
  }

  return {
    tasks,
    loading,
    deleteTask,
    updateTaskData,
    refetch: fetchTasks,
  }
}
