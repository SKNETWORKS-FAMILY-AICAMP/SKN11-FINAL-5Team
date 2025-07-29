"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { FileText, Instagram, Plus, Save, Send, FolderOpen, X } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import type { ContentForm, PublishSchedule, AutomationTask } from "../types"

interface ContentEditorProps {
  contentForm: ContentForm
  setContentForm: (form: ContentForm) => void
  selectedTemplate: AutomationTask | null
  publishSchedule: PublishSchedule
  setPublishSchedule: (schedule: PublishSchedule) => void
  saveGeneratedContent: (title: string, content: string, tags: string[]) => Promise<void>
  onPublish: () => void
  onSave: () => void
  onGenerateContent?: (
    keywords: string,
    platform: string,
  ) => Promise<{ title: string; content: string; tags: string[] }>
  onSetTags?: (tags: string[]) => void
  showContentGenerator?: boolean
  tags: string[]
}

export function ContentEditor({
  contentForm,
  setContentForm,
  selectedTemplate,
  publishSchedule,
  setPublishSchedule,
  saveGeneratedContent,
  onPublish,
  onSave,
  onGenerateContent,
  onSetTags,
  tags,
  showContentGenerator = false,
}: ContentEditorProps) {
  const [isContentGeneratorOpen, setIsContentGeneratorOpen] = useState(false)
  const [tagInput, setTagInput] = useState("")
  const [localTags, setLocalTags] = useState<string[]>([])
  const [isAccountModalOpen, setIsAccountModalOpen] = useState(false)
  const [isPublishModalOpen, setIsPublishModalOpen] = useState(false)
  const [accountInfo, setAccountInfo] = useState({ username: "", password: "" })
  const [isLoading, setIsLoading] = useState(false)
  const [loadingStep, setLoadingStep] = useState(0)
  const [contentGeneratorForm, setContentGeneratorForm] = useState({
    platform: "instagram",
    keywords: "",
  })
  const [attachedImages, setAttachedImages] = useState<Array<{ id: string; name: string; url: string }>>([])

  // Check if current platform is naver_blog
  const isNaverBlog = selectedTemplate?.task_data?.platform === "naver_blog"

  const instagramSteps = [
    "🔍 키워드 분석 중...",
    "🏷️ 해시태그 추천 중...",
    "🤖 LLM 기반 컨텐츠 생성 중...",
    "✍️ 인스타그램 컨텐츠 마무리 중...",
  ]

  const blogSteps = [
    "🔍 키워드 분석 중...",
    "📊 네이버 검색어 트렌드 분석 중...",
    "🤖 LLM 기반 컨텐츠 생성 중...",
    "✍️ 블로그 컨텐츠 마무리 중...",
  ]

  useEffect(() => {
    setLocalTags(tags)
  }, [tags])

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (files) {
      Array.from(files).forEach((file) => {
        const reader = new FileReader()
        reader.onload = (e) => {
          const imageUrl = e.target?.result as string
          const newImage = {
            id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
            name: file.name,
            url: imageUrl,
          }
          setAttachedImages((prev) => [...prev, newImage])
        }
        reader.readAsDataURL(file)
      })
    }
    // Reset input
    event.target.value = ""
  }

  const insertImageLink = (imageUrl: string, imageName: string) => {
    const linkText = `[이미지: ${imageName}](${imageUrl})`
    setContentForm({
      ...contentForm,
      content: contentForm.content + "\n" + linkText,
    })
  }

  const removeImage = (imageId: string) => {
    setAttachedImages((prev) => prev.filter((img) => img.id !== imageId))
  }

  const handleGenerateContent = async () => {
    if (!onGenerateContent) return

    const keyword = contentGeneratorForm.keywords.trim()
    if (!keyword) {
      alert("키워드를 입력해주세요!")
      return
    }

    setContentForm({ title: "", content: "" })
    setIsLoading(true)
    setLoadingStep(0)

    const steps = contentGeneratorForm.platform === "instagram" ? instagramSteps : blogSteps
    steps.forEach((_, idx) => {
      if (idx < steps.length - 1) {
        setTimeout(() => {
          setLoadingStep(idx)
        }, idx * 4000)
      } else {
        setTimeout(
          () => {
            setLoadingStep(idx)
          },
          (steps.length - 1) * 4000,
        )
      }
    })

    try {
      const { content, title, tags } = await onGenerateContent(keyword, contentGeneratorForm.platform)

      setContentForm({ title, content })
      setLocalTags(tags)
      onSetTags?.(tags)
      setIsContentGeneratorOpen(false)
      setContentGeneratorForm({ platform: "instagram", keywords: "" })
    } catch (err) {
      console.error("❌ 컨텐츠 생성 실패:", err)
      alert("컨텐츠 생성 중 오류가 발생했습니다.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleAccountConnect = () => {
    console.log("계정 연결:", accountInfo)
    setIsAccountModalOpen(false)
  }

  const handlePublishConfirm = () => {
    console.log("발행 설정:", publishSchedule)
    setIsPublishModalOpen(false)
    onPublish()
  }

  return (
    <Card className="rounded-xl border-0 shadow-sm bg-white h-[588px] flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FileText className="h-4 w-4 text-blue-600" />
            <span className="text-base">컨텐츠 에디터</span>
          </div>
          <div className="flex items-center space-x-2 flex-shrink-0">
            {showContentGenerator && (
              <Button
                onClick={() => setIsContentGeneratorOpen(!isContentGeneratorOpen)}
                className="bg-blue-500 hover:bg-blue-600 rounded-lg text-sm px-3 py-2 h-8"
              >
                <Plus className="h-3 w-3 mr-1" />
                컨텐츠 생성
              </Button>
            )}
            <Button onClick={onSave} variant="outline" className="rounded-lg text-sm px-3 py-2 h-8 bg-transparent">
              <Save className="h-3 w-3 mr-1" />
              저장
            </Button>

            {/* Publish Dialog */}
            <div className="relative group">
              <Dialog open={isPublishModalOpen} onOpenChange={setIsPublishModalOpen}>
                <DialogTrigger asChild>
                  <Button
                    className={`rounded-lg text-sm px-3 py-2 h-8 ${
                      isNaverBlog
                        ? "bg-gray-400 hover:bg-gray-400 cursor-not-allowed"
                        : "bg-green-500 hover:bg-green-600"
                    }`}
                    disabled={isNaverBlog}
                  >
                    <Send className="h-3 w-3 mr-1" />
                    발행
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader>
                    <DialogTitle>컨텐츠 발행</DialogTitle>
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
                    <div className="flex justify-end space-x-2 pt-4">
                      <Button variant="outline" onClick={() => setIsPublishModalOpen(false)} className="rounded-lg">
                        취소
                      </Button>
                      <Button onClick={handlePublishConfirm} className="bg-green-500 hover:bg-green-600 rounded-lg">
                        {publishSchedule.type === "immediate" ? "즉시 발행" : "예약 발행"}
                      </Button>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>

              {/* Tooltip for disabled publish button */}
              {isNaverBlog && (
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-10 pointer-events-none">
                  네이버는 현재 자동 발행이 지원되지 않습니다.
                  <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-800"></div>
                </div>
              )}
            </div>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 flex-1 overflow-hidden flex flex-col">
        {showContentGenerator && isContentGeneratorOpen && (
          <Card className="border-2 border-blue-200 bg-blue-50 rounded-lg flex-shrink-0">
            <CardContent className="p-4">
              <Label>플랫폼 선택</Label>
              <div className="flex space-x-4 mb-4">
                {[
                  { id: "instagram", icon: <Instagram className="h-4 w-4 text-pink-600" /> },
                  { id: "naver", icon: <FileText className="h-4 w-4 text-green-600" /> },
                ].map(({ id, icon }) => (
                  <label key={id} className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="radio"
                      value={id}
                      checked={contentGeneratorForm.platform === id}
                      onChange={(e) => setContentGeneratorForm({ ...contentGeneratorForm, platform: e.target.value })}
                    />
                    {icon}
                    <span className="text-sm">{id}</span>
                  </label>
                ))}
              </div>

              {contentGeneratorForm.platform === "instagram" && (
                <div className="mb-4">
                  <Dialog open={isAccountModalOpen} onOpenChange={setIsAccountModalOpen}>
                    <DialogTrigger asChild>
                      <Button
                        variant="outline"
                        className="rounded-lg text-sm px-3 py-2 h-8 bg-transparent border-gray-200 hover:bg-gray-50"
                      >
                        인스타그램 계정 연동
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>인스타그램 계정 연동</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-2">
                        <Label htmlFor="username">아이디</Label>
                        <Input
                          id="username"
                          value={accountInfo.username}
                          onChange={(e) => setAccountInfo({ ...accountInfo, username: e.target.value })}
                        />
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mt-4">
                          <p className="text-sm text-yellow-800">
                            ⚠️ 인스타그램 비즈니스 계정이어야 연동이 가능하며, 연동이 완료되면 24시간 이내에 초대장이
                            발송됩니다.
                          </p>
                        </div>
                      </div>
                      <div className="flex justify-end space-x-2 mt-4">
                        <Button variant="outline" onClick={() => setIsAccountModalOpen(false)}>
                          취소
                        </Button>
                        <Button
                          onClick={handleAccountConnect}
                          className="bg-pink-500 hover:bg-pink-600 text-white rounded-lg text-sm px-3 py-2 h-8"
                          disabled={!accountInfo.username}
                        >
                          연동하기
                        </Button>
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>
              )}

              <Label>키워드</Label>
              <Input
                value={contentGeneratorForm.keywords}
                onChange={(e) => setContentGeneratorForm({ ...contentGeneratorForm, keywords: e.target.value })}
              />
              <Button onClick={handleGenerateContent} className="mt-4 w-full bg-blue-600 text-white">
                {isLoading ? (
                  <div className="flex flex-col items-center justify-center w-full h-full">
                    <AnimatePresence mode="wait">
                      <motion.p
                        key={loadingStep}
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -5 }}
                        transition={{ duration: 0.3 }}
                        className="text-sm text-white text-center"
                      >
                        {contentGeneratorForm.platform === "instagram"
                          ? instagramSteps[loadingStep]
                          : blogSteps[loadingStep]}
                      </motion.p>
                    </AnimatePresence>
                  </div>
                ) : (
                  "컨텐츠 생성하기"
                )}
              </Button>
            </CardContent>
          </Card>
        )}

        <div className="flex-1 flex flex-col space-y-4 min-h-0">
          <div>
            <Label htmlFor="title">제목</Label>
            <Input
              id="title"
              value={contentForm.title}
              onChange={(e) => setContentForm({ ...contentForm, title: e.target.value })}
            />
          </div>
          <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
            <Label htmlFor="content" className="mb-2">
              본문
            </Label>
            <Textarea
              id="content"
              className={`flex-1 resize-none overflow-y-auto ${
                isContentGeneratorOpen ? "min-h-[120px] max-h-[200px]" : "min-h-[200px]"
              }`}
              value={contentForm.content}
              onChange={(e) => setContentForm({ ...contentForm, content: e.target.value })}
            />

            {/* 이미지 첨부 섹션 */}
            <div className="mt-3 space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm text-gray-600">이미지 첨부 (인스타그램용)</Label>
                <div className="flex items-center space-x-2">
                  <input
                    type="file"
                    id="imageUpload"
                    multiple
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="hidden"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => document.getElementById("imageUpload")?.click()}
                    className="text-xs px-2 py-1 h-7"
                  >
                    <FolderOpen className="h-3 w-3 mr-1" />
                    폴더 열기
                  </Button>
                </div>
              </div>

              {/* 첨부된 이미지 목록 */}
              {attachedImages.length > 0 && (
                <div className="border rounded-lg p-2 bg-gray-50 max-h-24 overflow-y-auto">
                  <div className="space-y-1">
                    {attachedImages.map((image) => (
                      <div
                        key={image.id}
                        className="flex items-center justify-between text-xs bg-white rounded px-2 py-1"
                      >
                        <div className="flex items-center space-x-2 flex-1 min-w-0">
                          <img
                            src={image.url || "/placeholder.svg"}
                            alt={image.name}
                            className="w-6 h-6 object-cover rounded"
                          />
                          <span className="truncate">{image.name}</span>
                        </div>
                        <div className="flex items-center space-x-1 flex-shrink-0">
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => insertImageLink(image.url, image.name)}
                            className="text-blue-600 hover:text-blue-800 p-0 h-auto text-xs"
                          >
                            삽입
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => removeImage(image.id)}
                            className="text-red-600 hover:text-red-800 p-0 h-auto"
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
