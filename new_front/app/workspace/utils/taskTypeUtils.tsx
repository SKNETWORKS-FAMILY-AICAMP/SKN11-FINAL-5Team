// src/utils/taskTypeUtils.ts
import { Instagram, Mail, FileText, Calendar, Bell } from "lucide-react"
import type { JSX } from "react"

// 라벨 반환
export function getTaskTypeLabel(taskType: string): string {
  const labels: Record<string, string> = {
    sns_publish_instagram: "인스타그램",
    sns_publish_blog: "블로그",
    email_marketing: "이메일",
    calendar_sync: "캘린더",
    reminder_notify: "리마인더",
  }
  return labels[taskType] || taskType
}

// 아이콘 반환
export function getTaskTypeIcon(taskType: string): JSX.Element {
  switch (taskType) {
    case "sns_publish_instagram":
      return <Instagram className="h-4 w-4 text-pink-600" />
    case "sns_publish_blog":
      return <FileText className="h-4 w-4 text-green-600" />
    case "email_marketing":
      return <Mail className="h-4 w-4 text-blue-600" />
    case "calendar_sync":
      return <Calendar className="h-4 w-4 text-indigo-600" />
    case "reminder_notify":
      return <Bell className="h-4 w-4 text-yellow-600" />
    default:
      return <FileText className="h-4 w-4 text-gray-400" />
  }
}