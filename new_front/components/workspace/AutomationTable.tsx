// src/workspace/components/AutomationTable.tsx
"use client"
import { useState } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { X } from "lucide-react"
import { Instagram, Mail, FileText, CheckCircle, Clock, XCircle, AlertCircle } from "lucide-react"
import TaskDetailSheet from "./TaskDetailSheet"

interface Task {
  id: number
  task_type: string
  title: string
  status: string
  created_at: string
  scheduled_at: string
  task_data: string
}

const mockTasks: Task[] = [
  {
    id: 1,
    task_type: "instagram",
    title: "인스타 포스트",
    status: "발행 완료",
    created_at: "2025-07-18",
    scheduled_at: "2025-07-20",
    task_data: "{}",
  },
  {
    id: 2,
    task_type: "email",
    title: "환영 이메일",
    status: "발행 전",
    created_at: "2025-07-19",
    scheduled_at: "2025-07-25",
    task_data: "{}",
  },
]

export default function AutomationTable() {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)

  const handleClick = (task: Task) => {
    setSelectedTask(task)
  }

  const handleDelete = (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    console.log("🗑️ 삭제:", id)
  }

  const getIcon = (type: string) => {
    switch (type) {
      case "instagram":
        return <Instagram className="h-4 w-4 text-pink-500" />
      case "email":
        return <Mail className="h-4 w-4 text-blue-500" />
      default:
        return <FileText className="h-4 w-4 text-gray-500" />
    }
  }

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

  return (
    <>
      <div className="rounded-lg border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-gray-50">
              <TableHead className="text-xs">유형</TableHead>
              <TableHead className="text-xs">작업명</TableHead>
              <TableHead className="text-xs">상태</TableHead>
              <TableHead className="text-xs">생성일</TableHead>
              <TableHead className="text-xs">발행일</TableHead>
              <TableHead className="w-8"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {mockTasks.map((task) => (
              <TableRow
                key={task.id}
                onClick={() => handleClick(task)}
                className="cursor-pointer hover:bg-gray-50"
              >
                <TableCell className="text-xs flex items-center space-x-2">
                  {getIcon(task.task_type)}
                  <span>{task.task_type}</span>
                </TableCell>
                <TableCell className="font-medium text-sm">{task.title}</TableCell>
                <TableCell className="text-xs">
                  <div className="flex items-center space-x-1">
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
                  {new Date(task.scheduled_at).toLocaleDateString("ko-KR")}
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => handleDelete(task.id, e)}
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

      {selectedTask && (
        <TaskDetailSheet task={selectedTask} onClose={() => setSelectedTask(null)} />
      )}
    </>
  )
}
