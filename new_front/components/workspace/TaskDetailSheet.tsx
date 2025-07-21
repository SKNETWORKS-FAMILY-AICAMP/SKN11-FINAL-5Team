// src/workspace/components/TaskDetailSheet.tsx
"use client"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Save } from "lucide-react"
import { Instagram, Mail, FileText, CheckCircle, Clock, XCircle, AlertCircle } from "lucide-react"

interface Task {
  id: number
  task_type: string
  title: string
  status: string
  created_at: string
  scheduled_at: string
  task_data: string
}

interface Props {
  task: Task
  onClose: () => void
}

export default function TaskDetailSheet({ task, onClose }: Props) {
  const getTypeIcon = () => {
    switch (task.task_type) {
      case "instagram":
        return <Instagram className="h-4 w-4 text-pink-500" />
      case "email":
        return <Mail className="h-4 w-4 text-blue-500" />
      default:
        return <FileText className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusIcon = () => {
    switch (task.status) {
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
    <Sheet open={true} onOpenChange={onClose}>
      <SheetContent className="w-[500px] sm:w-[500px] rounded-l-xl">
        <SheetHeader>
          <SheetTitle className="flex items-center space-x-2">
            {getTypeIcon()}
            <span>{task.title}</span>
          </SheetTitle>
        </SheetHeader>

        <div className="mt-6 space-y-4 text-sm">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-gray-500">유형</Label>
              <p className="font-medium">{task.task_type}</p>
            </div>
            <div>
              <Label className="text-gray-500">상태</Label>
              <div className="flex items-center space-x-1">
                {getStatusIcon()}
                <span className="font-medium">{task.status}</span>
              </div>
            </div>
            <div>
              <Label className="text-gray-500">생성일</Label>
              <p className="font-medium">
                {new Date(task.created_at).toLocaleDateString("ko-KR")}
              </p>
            </div>
            <div>
              <Label className="text-gray-500">발행일</Label>
              <p className="font-medium">
                {new Date(task.scheduled_at).toLocaleDateString("ko-KR")}
              </p>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="taskData">업무 데이터</Label>
            <Textarea
              id="taskData"
              className="min-h-[250px] font-mono text-sm rounded-lg"
              defaultValue={task.task_data}
            />
          </div>

          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={onClose} className="rounded-lg">
              취소
            </Button>
            <Button className="bg-green-500 hover:bg-green-600 rounded-lg">
              <Save className="h-4 w-4 mr-2" />
              저장
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}
