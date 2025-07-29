import { CheckCircle, Clock, XCircle } from "lucide-react"
import type { JSX } from "react"

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: "발행 전",
    completed: "발행 완료",
    failed: "실패",
    cancelled: "취소됨",
  }
  return labels[status] || status
}

export function getStatusIcon(status: string): JSX.Element {
  switch (status) {
    case "pending":
      return <Clock className="h-4 w-4 text-yellow-600" />
    case "completed":
      return <CheckCircle className="h-4 w-4 text-green-600" />
    case "failed":
      return <XCircle className="h-4 w-4 text-red-600" />
    case "cancelled":
      return <XCircle className="h-4 w-4 text-gray-400" />
    default:
      return <Clock className="h-4 w-4 text-gray-400" />
  }
}
