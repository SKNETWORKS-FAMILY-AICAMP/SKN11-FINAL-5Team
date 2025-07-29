"use client"

import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { Save, CheckCircle, Clock, XCircle, AlertCircle, Instagram, Mail, FileText } from "lucide-react"
import type { AutomationTask } from "../types"

interface TaskDetailSheetProps {
  isOpen: boolean
  onOpenChange: (open: boolean) => void
  selectedTask: AutomationTask | null
  setSelectedTask: (task: AutomationTask) => void
  onSave: () => void
}

export function TaskDetailSheet({ isOpen, onOpenChange, selectedTask, setSelectedTask, onSave }: TaskDetailSheetProps) {
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
      email: "이메일",
    }
    return labels[taskType as keyof typeof labels] || taskType
  }

  return (
    <Sheet open={isOpen} onOpenChange={onOpenChange}>
      <SheetContent className="w-[500px] sm:w-[500px] rounded-l-xl">
        <SheetHeader>
          <SheetTitle className="flex items-center space-x-2">
            {selectedTask && getTaskTypeIcon(selectedTask.task_type)}
            <span>{selectedTask?.title}</span>
          </SheetTitle>
        </SheetHeader>
        {selectedTask && (
          <div className="mt-6 space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <Label className="text-gray-500">유형</Label>
                <p className="font-medium">{getTaskTypeLabel(selectedTask.task_type)}</p>
              </div>
              <div>
                <Label className="text-gray-500">상태</Label>
                <div className="flex items-center space-x-2">
                  {getStatusIcon(selectedTask.status)}
                  <span className="font-medium">{selectedTask.status}</span>
                </div>
              </div>
              <div>
                <Label className="text-gray-500">생성일</Label>
                <p className="font-medium">{new Date(selectedTask.created_at).toLocaleDateString("ko-KR")}</p>
              </div>
              <div>
                <Label className="text-gray-500">발행일</Label>
                <p className="font-medium">{new Date(selectedTask.scheduled_at).toLocaleDateString("ko-KR")}</p>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="taskData">업무 데이터</Label>
            <Textarea
              id="taskData"
              className="min-h-[250px] font-mono text-sm rounded-lg"
              value={JSON.stringify(selectedTask.task_data, null, 2)} 
              onChange={(e) =>
                setSelectedTask({
                  ...selectedTask,
                  task_data: JSON.parse(e.target.value),
                })
              }
            />
            </div>
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => onOpenChange(false)} className="rounded-lg">
                취소
              </Button>
              <Button onClick={onSave} className="bg-green-500 hover:bg-green-600 rounded-lg">
                <Save className="h-4 w-4 mr-2" />
                저장
              </Button>
            </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
  )
}
