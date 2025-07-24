"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import Image from "next/image"
import {
  Plus,
  Eye,
  Save,
  Send,
  Zap,
  FileText,
  Instagram,
  Heart,
  MessageCircle,
  Bookmark,
  MoreHorizontal,
} from "lucide-react"
import type { ContentForm, PublishSchedule } from "../types"

interface ContentEditorProps {
  contentForm: ContentForm
  setContentForm: (form: ContentForm) => void
  isPreviewMode: boolean
  setIsPreviewMode: (mode: boolean) => void
  selectedTemplate: any
  publishSchedule: PublishSchedule
  setPublishSchedule: (schedule: PublishSchedule) => void
  onSave: () => void
  onPublish: () => void
  onGenerateContent?: (keywords: string, platform: string) => void
  showContentGenerator?: boolean
}

export function ContentEditor({
  contentForm,
  setContentForm,
  isPreviewMode,
  setIsPreviewMode,
  selectedTemplate,
  publishSchedule,
  setPublishSchedule,
  onSave,
  onPublish,
  onGenerateContent,
  showContentGenerator = false,
}: ContentEditorProps) {
  const [isPublishDialogOpen, setIsPublishDialogOpen] = useState(false)
  const [isContentGeneratorOpen, setIsContentGeneratorOpen] = useState(false)
  const [contentGeneratorForm, setContentGeneratorForm] = useState({
    platform: "instagram",
    keywords: "",
  })

  const handlePublish = () => {
    onPublish()
    setIsPublishDialogOpen(false)
  }

  const handleGenerateContent = () => {
    if (onGenerateContent) {
      onGenerateContent(contentGeneratorForm.keywords, contentGeneratorForm.platform)
    }
    setIsContentGeneratorOpen(false)
    setContentGeneratorForm({ platform: "instagram", keywords: "" })
  }

  const renderTemplateUI = () => {
    if (!selectedTemplate) {
      return <div className="flex items-center justify-center h-[300px] text-gray-500">템플릿을 선택해주세요</div>
    }
    switch (selectedTemplate.type) {
      case "sns":
        return (
          <div className="max-w-sm mx-auto bg-white border rounded-xl overflow-hidden shadow-sm">
            {/* Instagram Header */}
            <div className="flex items-center justify-between p-3 border-b">
              <div className="flex items-center space-x-3">
                <Avatar className="w-8 h-8">
                  <AvatarImage src="/placeholder.svg" />
                  <AvatarFallback>TB</AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-semibold text-sm">tinkerbell_shop</p>
                  <p className="text-xs text-gray-500">Seoul, South Korea</p>
                </div>
              </div>
              <MoreHorizontal className="w-5 h-5" />
            </div>
            {/* Instagram Image */}
            <div className="aspect-square bg-gray-100 flex items-center justify-center">
              <Image
                src="/placeholder.svg?height=300&width=300"
                alt="Post"
                width={300}
                height={300}
                className="w-full h-full object-cover"
              />
            </div>
            {/* Instagram Actions */}
            <div className="p-3">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-4">
                  <Heart className="w-5 h-5" />
                  <MessageCircle className="w-5 h-5" />
                  <Send className="w-5 h-5" />
                </div>
                <Bookmark className="w-5 h-5" />
              </div>
              <p className="font-semibold text-sm mb-1">1,234개의 좋아요</p>
              {/* Instagram Caption */}
              <div className="text-sm">
                <span className="font-semibold">tinkerbell_shop</span>{" "}
                <span className="whitespace-pre-wrap">{contentForm.content}</span>
              </div>
              <p className="text-xs text-gray-500 mt-2">1시간 전</p>
            </div>
          </div>
        )
      case "email":
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
                  <span className="text-sm">고객님 &lt;customer@example.com&gt;</span>
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
                  <p>서울시 강남구 테헤란로 123</p>
                  <p>고객센터: 1588-1234</p>
                </div>
              </div>
            </div>
          </div>
        )
      default:
        return (
          <div className="flex items-center justify-center h-[300px] text-gray-500">
            지원하지 않는 템플릿 유형입니다
          </div>
        )
    }
  }

  return (
    <Card className="rounded-xl border-0 shadow-sm bg-white">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FileText className="h-4 w-4 text-blue-600" />
            <span className="text-base">콘텐츠 에디터</span>
          </div>
          <div className="flex items-center space-x-2">
            {showContentGenerator && (
              <Button
                onClick={() => setIsContentGeneratorOpen(!isContentGeneratorOpen)}
                className="bg-blue-500 hover:bg-blue-600 rounded-lg text-sm px-3 py-2 h-8"
              >
                <Plus className="h-3 w-3 mr-1" />
                콘텐츠 생성
              </Button>
            )}
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
                  발행
                </Button>
              </DialogTrigger>
              <DialogContent className="rounded-xl">
                <DialogHeader>
                  <DialogTitle>콘텐츠 발행</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-3">
                    <Label>발행 방식</Label>
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
                        <span className="text-sm">즉시 발행</span>
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
                        <span className="text-sm">예약 발행</span>
                      </label>
                    </div>
                  </div>
                  {publishSchedule.type === "scheduled" && (
                    <>
                      <div className="space-y-2">
                        <Label htmlFor="publishDate">발행 날짜</Label>
                        <Input
                          id="publishDate"
                          type="date"
                          value={publishSchedule.date}
                          onChange={(e) => setPublishSchedule({ ...publishSchedule, date: e.target.value })}
                          className="rounded-lg"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="publishTime">발행 시간</Label>
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
                    {publishSchedule.type === "immediate" ? "즉시 발행" : "예약 발행"}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* 콘텐츠 생성기 */}
        {showContentGenerator && isContentGeneratorOpen && (
          <Card className="border-2 border-blue-200 bg-blue-50 rounded-lg">
            <CardContent className="p-4">
              <div className="space-y-4">
                <div className="space-y-3">
                  <Label>플랫폼 선택</Label>
                  <div className="flex space-x-4">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="radio"
                        name="platform"
                        value="instagram"
                        checked={contentGeneratorForm.platform === "instagram"}
                        onChange={(e) => setContentGeneratorForm({ ...contentGeneratorForm, platform: e.target.value })}
                        className="text-blue-500"
                      />
                      <Instagram className="h-4 w-4 text-pink-600" />
                      <span className="text-sm">인스타그램</span>
                    </label>
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="radio"
                        name="platform"
                        value="naver"
                        checked={contentGeneratorForm.platform === "naver"}
                        onChange={(e) => setContentGeneratorForm({ ...contentGeneratorForm, platform: e.target.value })}
                        className="text-blue-500"
                      />
                      <FileText className="h-4 w-4 text-green-600" />
                      <span className="text-sm">네이버</span>
                    </label>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="keywords">키워드</Label>
                  <Input
                    id="keywords"
                    placeholder="콘텐츠 생성을 위한 키워드를 입력하세요"
                    value={contentGeneratorForm.keywords}
                    onChange={(e) => setContentGeneratorForm({ ...contentGeneratorForm, keywords: e.target.value })}
                    className="rounded-lg"
                  />
                </div>
                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setIsContentGeneratorOpen(false)} className="rounded-lg">
                    취소
                  </Button>
                  <Button
                    onClick={handleGenerateContent}
                    className="bg-blue-500 hover:bg-blue-600 rounded-lg"
                    disabled={!contentGeneratorForm.keywords.trim()}
                  >
                    <Zap className="h-4 w-4 mr-2" />
                    자동 생성
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {!isPreviewMode ? (
          <>
            <div className="space-y-2">
              <Label htmlFor="contentTitle" className="text-sm">
                제목
              </Label>
              <Input
                id="contentTitle"
                placeholder="콘텐츠 제목을 입력하세요"
                value={contentForm.title}
                onChange={(e) => setContentForm({ ...contentForm, title: e.target.value })}
                className="rounded-lg"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="contentBody" className="text-sm">
                본문
              </Label>
              <Textarea
                id="contentBody"
                placeholder="콘텐츠 본문을 입력하세요..."
                className="min-h-[300px] rounded-lg"
                value={contentForm.content}
                onChange={(e) => setContentForm({ ...contentForm, content: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="contentTags" className="text-sm">
                키워드/태그
              </Label>
            </div>
          </>
        ) : (
          <div className="min-h-[400px]">{renderTemplateUI()}</div>
        )}
      </CardContent>
    </Card>
  )
}
