"use client"

import type React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  Zap,
  CheckCircle,
  Clock,
  XCircle,
  AlertCircle,
  Instagram,
  Mail,
  FileText,
  X
} from "lucide-react"
import type { AutomationTask } from "../types"

interface AutomationTableProps {
  automationTasks: AutomationTask[]
  onTaskClick: (task: AutomationTask) => void
  onDeleteTask: (taskId: number, e: React.MouseEvent) => void
}

export function AutomationTable({
  automationTasks,
  onTaskClick,
  onDeleteTask
}: AutomationTableProps) {
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
      email: "이메일"
    }
    return labels[taskType as keyof typeof labels] || taskType
  }

  return (
    <Card className="rounded-xl border-0 shadow-sm bg-white">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center space-x-2">
          <Zap className="h-4 w-4 text-yellow-600" />
          <span className="text-base">자동화 업무 목록</span>
        </CardTitle>
      </CardHeader>

      <CardContent>
        <div className="rounded-lg border overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50">
                <TableHead className="text-xs">유형</TableHead>
                <TableHead className="text-xs">작업명</TableHead>
                <TableHead className="text-xs">상태</TableHead>
                <TableHead className="text-xs">생성일</TableHead>
                <TableHead className="text-xs">발행일</TableHead>
                <TableHead className="w-8" />
              </TableRow>
            </TableHeader>

            <TableBody>
              {(automationTasks ?? []).map((task) => (
                <TableRow
                  key={task.task_id}
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => onTaskClick(task)}
                >
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      {getTaskTypeIcon(task.task_type)}
                      <span className="text-xs">{getTaskTypeLabel(task.task_type)}</span>
                    </div>
                  </TableCell>

                  <TableCell className="font-medium text-sm">{task.title}</TableCell>

                  <TableCell>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(task.status)}
                      <Badge
                        variant={task.status === "발행 완료" ? "default" : "secondary"}
                        className="text-xs rounded-md"
                      >
                        {task.status}
                      </Badge>
                    </div>
                  </TableCell>

                  <TableCell className="text-xs text-gray-500">
                    {new Date(task.created_at).toLocaleDateString("ko-KR")}
                  </TableCell>

                  <TableCell className="text-xs text-gray-500">
                  {task.scheduled_at
                    ? new Date(task.scheduled_at).toLocaleDateString("ko-KR")
                    : "-"}
                </TableCell>

                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => onDeleteTask(task.task_id, e)}
                      className="h-6 w-6 p-0 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-md"
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
