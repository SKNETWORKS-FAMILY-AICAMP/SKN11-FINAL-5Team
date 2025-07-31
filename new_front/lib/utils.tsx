// lib/utils.tsx
import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: any[]) {
  return twMerge(clsx(inputs))
}

import { CheckCircle, AlertTriangle, XCircle, Clock } from "lucide-react"
import Image from "next/image"
import { Badge } from "@/components/ui/badge"

export const getStatusIcon = (status: string) => {
  switch (status) {
    case "healthy":
      return <CheckCircle className="h-4 w-4 text-emerald-600" />
    case "warning":
      return <AlertTriangle className="h-4 w-4 text-amber-600" />
    case "critical":
      return <XCircle className="h-4 w-4 text-red-600" />
    default:
      return <Clock className="h-4 w-4 text-gray-600" />
  }
}

export const getStatusBadge = (status: string) => {
  switch (status) {
    case "healthy":
      return <Badge className="bg-emerald-100 text-emerald-700 border-emerald-300">정상</Badge>
    case "warning":
      return <Badge className="bg-amber-100 text-amber-700 border-amber-300">주의</Badge>
    case "critical":
      return <Badge className="bg-red-100 text-red-700 border-red-300">위험</Badge>
    default:
      return <Badge variant="secondary">{status}</Badge>
  }
}

export const getPlanBadge = (planType: string) => {
  switch (planType.toLowerCase()) {
    case "basic":
      return <Badge className="bg-gray-100 text-gray-700 border-gray-300">베이직</Badge>
    case "premium":
      return <Badge className="bg-purple-100 text-purple-700 border-purple-300">프리미엄</Badge>
    case "enterprise":
      return <Badge className="bg-blue-100 text-blue-700 border-blue-300">엔터프라이즈</Badge>
    default:
      return <Badge variant="secondary">{planType}</Badge>
  }
}

const agentIconMap: Record<string, string> = {
  business_planning: "3D_사업기획",
  marketing: "3D_마케팅",
  customer_service: "3D_고객관리",
  mental_health: "3D_멘탈케어",
  task_automation: "3D_업무관리",
}

export const getAgentIcon = (agentType: string) => {
  const iconName = agentIconMap[agentType] || "default"
  return (
    <Image
      src={`/icons/${iconName}.png`}
      alt={`${agentType} 아이콘`}
      width={20}
      height={20}
      className="rounded-sm"
    />
  )
}
