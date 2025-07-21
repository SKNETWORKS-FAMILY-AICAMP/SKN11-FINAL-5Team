// src/workspace/components/StatusBadge.tsx
"use client"
import { Badge } from "@/components/ui/badge"
import {
  CheckCircle,
  Clock,
  XCircle,
  AlertCircle,
} from "lucide-react"

interface Props {
  status: string
}

export default function StatusBadge({ status }: Props) {
  const iconMap: Record<string, JSX.Element> = {
    "발행 완료": <CheckCircle className="h-3 w-3 text-green-600" />,
    "발행 전": <Clock className="h-3 w-3 text-yellow-600" />,
    "오류": <XCircle className="h-3 w-3 text-red-600" />,
    "기타": <AlertCircle className="h-3 w-3 text-gray-600" />,
  }

  const variant = status === "발행 완료" ? "default" : "secondary"
  const icon = iconMap[status] || iconMap["기타"]

  return (
    <Badge variant={variant} className="text-xs rounded-md flex items-center space-x-1">
      {icon}
      <span>{status}</span>
    </Badge>
  )
}
