// src/workspace/components/ScheduleDialog.tsx
"use client"
import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"

export default function ScheduleDialog() {
  const [isOpen, setIsOpen] = useState(false)
  const [form, setForm] = useState({
    title: "",
    date: "",
    time: "",
    description: "",
  })

  const handleAdd = () => {
    if (form.title && form.date && form.time) {
      console.log("📆 새 일정 추가됨:", form)
      setForm({ title: "", date: "", time: "", description: "" })
      setIsOpen(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button className="bg-green-500 hover:bg-green-600 rounded-lg text-sm px-3 py-2 h-8">
          <Plus className="h-3 w-3 mr-1" />
          일정 등록
        </Button>
      </DialogTrigger>
      <DialogContent className="rounded-xl">
        <DialogHeader>
          <DialogTitle>새 일정 등록</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">일정 제목</Label>
            <Input
              id="title"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="예: 마케팅 회의"
              className="rounded-lg"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="date">날짜</Label>
            <Input
              id="date"
              type="date"
              value={form.date}
              onChange={(e) => setForm({ ...form, date: e.target.value })}
              className="rounded-lg"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="time">시간</Label>
            <Input
              id="time"
              type="time"
              value={form.time}
              onChange={(e) => setForm({ ...form, time: e.target.value })}
              className="rounded-lg"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="desc">설명</Label>
            <Textarea
              id="desc"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="세부 설명 입력"
              className="rounded-lg"
            />
          </div>
          <Button
            onClick={handleAdd}
            className="w-full bg-green-500 hover:bg-green-600 rounded-lg"
            disabled={!form.title || !form.date || !form.time}
          >
            일정 추가
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
