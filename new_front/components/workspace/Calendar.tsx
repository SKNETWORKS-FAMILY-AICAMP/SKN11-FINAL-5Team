// src/workspace/components/Calendar.tsx
"use client"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"

interface Props {
  selectedDate?: Date
  onSelect: (date: Date) => void
}

export default function Calendar({ selectedDate, onSelect }: Props) {
  const today = new Date()
  const currentDate = selectedDate || today
  const year = currentDate.getFullYear()
  const month = currentDate.getMonth()

  const firstDay = new Date(year, month, 1)
  const startDate = new Date(firstDay)
  startDate.setDate(firstDay.getDate() - firstDay.getDay())

  const days: JSX.Element[] = []
  const loopDate = new Date(startDate)

  for (let i = 0; i < 42; i++) {
    const dateStr = loopDate.toISOString().split("T")[0]
    const isCurrentMonth = loopDate.getMonth() === month
    const isSelected = selectedDate && loopDate.toDateString() === selectedDate.toDateString()

    days.push(
      <div key={i} className="relative">
        <button
          className={`w-full h-9 text-xs rounded-lg flex items-center justify-center hover:bg-gray-100 ${
            isSelected
              ? "bg-green-100 text-green-900 font-semibold"
              : isCurrentMonth
              ? "text-gray-900"
              : "text-gray-400"
          }`}
          onClick={() => onSelect(new Date(loopDate))}
        >
          {loopDate.getDate()}
        </button>
      </div>
    )

    loopDate.setDate(loopDate.getDate() + 1)
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          className="h-7 w-7 p-0 rounded-lg"
          onClick={() => {
            const newDate = new Date(currentDate)
            newDate.setMonth(currentDate.getMonth() - 1)
            onSelect(newDate)
          }}
        >
          <ChevronLeft className="h-3 w-3" />
        </Button>
        <h3 className="text-sm font-semibold">
          {currentDate.toLocaleDateString("ko-KR", { year: "numeric", month: "long" })}
        </h3>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 w-7 p-0 rounded-lg"
          onClick={() => {
            const newDate = new Date(currentDate)
            newDate.setMonth(currentDate.getMonth() + 1)
            onSelect(newDate)
          }}
        >
          <ChevronRight className="h-3 w-3" />
        </Button>
      </div>

      <div className="grid grid-cols-7 gap-1 text-center text-xs font-medium text-gray-500">
        <div className="p-1">일</div>
        <div className="p-1">월</div>
        <div className="p-1">화</div>
        <div className="p-1">수</div>
        <div className="p-1">목</div>
        <div className="p-1">금</div>
        <div className="p-1">토</div>
      </div>

      <div className="grid grid-cols-7 gap-1">{days}</div>
    </div>
  )
}
