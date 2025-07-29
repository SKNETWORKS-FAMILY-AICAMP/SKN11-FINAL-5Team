"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import Image from "next/image"
import { Eye, Save, Send, Mail } from "lucide-react"
import type { ContentForm, PublishSchedule } from "../types"
import { useState } from "react"

interface EmailEditorProps {
  contentForm: ContentForm
  setContentForm: (form: ContentForm) => void
  isPreviewMode: boolean
  setIsPreviewMode: (mode: boolean) => void
  publishSchedule: PublishSchedule
  setPublishSchedule: (schedule: PublishSchedule) => void
  onSave: () => void
  onPublish: () => void
  toEmail: string
  setToEmail: (value: string) => void
}

export function EmailEditor({
  contentForm,
  setContentForm,
  isPreviewMode,
  setIsPreviewMode,
  publishSchedule,
  setPublishSchedule,
  onSave,
  onPublish,
  toEmail,      
  setToEmail  
}: EmailEditorProps) {
  const [isPublishDialogOpen, setIsPublishDialogOpen] = useState(false)
  const [recipientEmail, setRecipientEmail] = useState("")

  const handlePublish = () => {
    onPublish()
    setIsPublishDialogOpen(false)
  }

  const renderEmailPreview = () => {
    return (
      <div className="bg-white border rounded-xl overflow-hidden shadow-sm">
        {/* 이메일 헤더 */}
        <div className="bg-gray-50 p-4 border-b">
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-600">보내는 사람:</span>
              <span className="text-sm">TinkerBell Shop &lt;noreply@tinkerbell.com&gt;</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-600">받는 사람:</span>
              <span className="text-sm">{recipientEmail || "customer@example.com"}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-600">제목:</span>
              <span className="text-sm font-semibold">{contentForm.title || "제목을 입력하세요"}</span>
            </div>
          </div>
        </div>
        {/* 이메일 본문 */}
        <div className="p-4">
          <div className="mb-4">
            <Image
              src="/placeholder.svg?height=40&width=120"
              alt="TinkerBell Logo"
              width={120}
              height={40}
              className="mb-4"
            />
          </div>
          <div className="prose max-w-none">
            <div className="whitespace-pre-wrap text-gray-700 leading-relaxed text-sm">
              {contentForm.content || "내용을 입력하세요..."}
            </div>
          </div>
          {/* 이메일 푸터 */}
          <div className="mt-6 pt-4 border-t border-gray-200">
            <div className="text-xs text-gray-500 space-y-1">
              <p>TinkerBell Shop</p>
              <p>서울시 금천구 가산디지털로 12345</p>
              <p>고객센터: 1588-0000</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <Card className="rounded-xl border-0 shadow-sm bg-white">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Mail className="h-4 w-4 text-blue-600" />
            <span className="text-base">이메일 에디터</span>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              onClick={() => setIsPreviewMode(!isPreviewMode)}
              className="rounded-lg text-sm px-3 py-2 h-8"
            >
              <Eye className="h-3 w-3 mr-1" />
              {isPreviewMode ? "편집" : "미리보기"}
            </Button>
            <Button onClick={onSave} variant="outline" className="rounded-lg text-sm px-3 py-2 h-8 bg-transparent">
              <Save className="h-3 w-3 mr-1" />
              저장
            </Button>
            <Dialog open={isPublishDialogOpen} onOpenChange={setIsPublishDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-green-500 hover:bg-green-600 rounded-lg text-sm px-3 py-2 h-8">
                  <Send className="h-3 w-3 mr-1" />
                  발송
                </Button>
              </DialogTrigger>
              <DialogContent className="rounded-xl">
                <DialogHeader>
                  <DialogTitle>이메일 발송</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-3">
                    <Label>발송 방식</Label>
                    <div className="flex space-x-4">
                      <label className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="radio"
                          name="publishType"
                          value="immediate"
                          checked={publishSchedule.type === "immediate"}
                          onChange={(e) =>
                            setPublishSchedule({
                              ...publishSchedule,
                              type: e.target.value as "immediate" | "scheduled",
                            })
                          }
                          className="text-green-500"
                        />
                        <span className="text-sm">즉시 발송</span>
                      </label>
                      <label className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="radio"
                          name="publishType"
                          value="scheduled"
                          checked={publishSchedule.type === "scheduled"}
                          onChange={(e) =>
                            setPublishSchedule({
                              ...publishSchedule,
                              type: e.target.value as "immediate" | "scheduled",
                            })
                          }
                          className="text-green-500"
                        />
                        <span className="text-sm">예약 발송</span>
                      </label>
                    </div>
                  </div>
                  {publishSchedule.type === "scheduled" && (
                    <>
                      <div className="space-y-2">
                        <Label htmlFor="publishDate">발송 날짜</Label>
                        <Input
                          id="publishDate"
                          type="date"
                          value={publishSchedule.date}
                          onChange={(e) => setPublishSchedule({ ...publishSchedule, date: e.target.value })}
                          className="rounded-lg"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="publishTime">발송 시간</Label>
                        <Input
                          id="publishTime"
                          type="time"
                          value={publishSchedule.time}
                          onChange={(e) => setPublishSchedule({ ...publishSchedule, time: e.target.value })}
                          className="rounded-lg"
                        />
                      </div>
                    </>
                  )}
                  <Button
                    onClick={handlePublish}
                    className="w-full bg-green-500 hover:bg-green-600 rounded-lg"
                    disabled={publishSchedule.type === "scheduled" && (!publishSchedule.date || !publishSchedule.time)}
                  >
                    {publishSchedule.type === "immediate" ? "즉시 발송" : "예약 발송"}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {!isPreviewMode ? (
          <>
            {/* 제목 입력 */}
            <div className="space-y-2">
              <Label htmlFor="emailSubject" className="text-sm font-medium text-gray-700">
                제목 
              </Label>
              <Input
                id="emailSubject"
                // placeholder="이메일 제목을 입력하세요"
                value={contentForm.title}
                onChange={(e) => setContentForm({ ...contentForm, title: e.target.value })}
                className="rounded-lg"
              />
            </div>

            {/* 본문 입력 */}
            <div className="space-y-2">
              <Label htmlFor="emailContent" className="text-sm font-medium text-gray-700">
                본문
              </Label>
              <Textarea
                id="emailContent"
                // placeholder="이메일 본문을 입력하세요..."
                className="min-h-[300px] rounded-lg"
                value={contentForm.content}
                onChange={(e) => setContentForm({ ...contentForm, content: e.target.value })}
              />
            </div>

            {/* 받는 사람 이메일 입력 - 본문 바로 아래로 이동 */}
            <div className="space-y-2">
              <Label htmlFor="recipientEmail" className="text-sm font-medium text-gray-700">
                받는 사람
              </Label>
              <Input
                id="recipientEmail"
                type="email"
                value={toEmail} // ✅ props 사용
                onChange={(e) => setToEmail(e.target.value)} // ✅ props setter 사용
                className="rounded-lg"
              />
            </div>
          </>
        ) : (
          <div className="min-h-[400px]">{renderEmailPreview()}</div>
        )}
      </CardContent>
    </Card>
  )
}
