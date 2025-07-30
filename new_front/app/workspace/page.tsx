// ✅ 전체 구조 안정화를 위한 WorkspacePage 리팩터링

"use client"

import { useState, useEffect } from "react"
import type React from "react"
import Image from "next/image"
import Link from "next/link"
import { User } from "lucide-react"
import { useRouter } from "next/navigation"
import axios from "axios"

import { TabMenu } from "./components/TabMenu"
import { Calendar } from "./components/Calendar"
import { ScheduleSidebar } from "./components/ScheduleSidebar"
import { AiContentList } from "./components/AiContentList"
import { TaskDetailSheet } from "./components/TaskDetailSheet"
import { ContentEditor } from "./components/ContentEditor"
import { EmailEditor } from "./components/EmailEditor"
import { EmailTemplateList } from "./components/EmailTemplateList"
import { AutomationTable } from "./components/AutomationTable"

import { useSchedule } from "./hooks/useSchedule"
import { useContentForm, useAiContents } from "./hooks/useContentForm"
import type { AutomationTask, EmailTemplate, EmailContent } from "./types"

export default function WorkspacePage() {
  const router = useRouter()
  const [userId, setUserId] = useState<number | null>(null)
  const schedule = useSchedule(userId)
  const [toEmail, setToEmail] = useState("")
  const [emailTemplates, setEmailTemplates] = useState<EmailTemplate[]>([])
  const [emailContents, setEmailContents] = useState<EmailTemplate[]>([])
  const [tags, setTags] = useState<string[]>([])
  const [generatedCount, setGeneratedCount] = useState(0)
  const { generateContent, saveGeneratedContent } = useAiContents(userId)
  const [aiGeneratedContents, setAiGeneratedContents] = useState<AutomationTask[]>([])
  const [activeTab, setActiveTab] = useState<string>("automation")
  const [isPreviewMode, setIsPreviewMode] = useState(false)
  const [selectedTask, setSelectedTask] = useState<AutomationTask | null>(null)
  const [isTaskSheetOpen, setIsTaskSheetOpen] = useState(false)
  const email = useContentForm(userId)
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | EmailContent | null>(null)
  const [selectedContent, setSelectedContent] = useState<AutomationTask | null>(null)
  const [workspaceLoading, setWorkspaceLoading] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem("user")
    if (!stored) {
      alert("로그인이 필요합니다.")
      router.replace("/login")
      return
    }
    try {
      const parsed = JSON.parse(stored)
      if (!parsed.user_id) throw new Error("user_id 없음")
      setUserId(parsed.user_id)
    } catch (e) {
      console.error("user 정보 파싱 실패", e)
      localStorage.removeItem("user")
      router.replace("/login")
    }
  }, [router])

  useEffect(() => {
    if (!userId) return

    const fetchTemplates = async () => {
      setWorkspaceLoading(true)
      try {
        const res = await axios.get("https://localhost:8005/api/email/templates", {
          params: { user_id: userId }
        })
        const templates: EmailTemplate[] = res.data.templates || []

        setEmailTemplates(
          templates.filter(
            (t) =>
              Number(t.user_id) === 3 &&
              t.template_type?.toLowerCase() !== "user_made" &&
              !t.template_type?.toLowerCase().includes("린캔버스")
          )
        )

        setEmailContents(
          templates.filter(
            (t) =>
              Number(t.user_id) === Number(userId) &&
              t.template_type?.toLowerCase() === "user_made"
          )
        )
      } catch (e) {
        console.error("이메일 템플릿 불러오기 실패:", e)
      } finally {
        setWorkspaceLoading(false)
      }
    }

    fetchTemplates()
  }, [userId])

  const handleTabChange = () => {
    setSelectedTemplate(null)
    email.setContentForm({ title: "", content: "" })
  }

  const handleTaskClick = (task: AutomationTask) => {
    setSelectedTask(task)
    setIsTaskSheetOpen(true)
  }

  const handleDeleteTask = (taskId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    schedule.deleteTask(taskId)
  }

  const handleSaveTaskData = () => {
    if (selectedTask) {
      schedule.updateTask(selectedTask)
      setIsTaskSheetOpen(false)
    }
  }

  const handleTemplateSelect = (template: EmailTemplate | EmailContent) => {
    setSelectedTemplate(template)
    email.setContentForm({ title: template.title, content: template.content })
  }

  const handleSaveContent = async () => {
    if (activeTab === "email") {
      await email.saveEmailContent()
      alert("컨텐츠가 저장되었습니다!")
      return
    }

    if (!selectedContent) {
      alert("저장할 콘텐츠를 선택해주세요.")
      return
    }

    const platform =
      selectedContent.task_data?.platform === "naver"
        ? "naver_blog"
        : selectedContent.task_data?.platform

    const taskType =
      platform === "naver_blog"
        ? "sns_publish_blog"
        : "sns_publish_instagram"

    const fullContent =
      selectedContent.task_data?.full_content ||
      selectedContent.task_data?.post_content ||
      selectedContent.task_data?.content || ""

    const topKeywords =
      selectedContent.task_data?.top_keywords ||
      selectedContent.task_data?.searched_hashtags || []

    const taskData =
      platform === "naver_blog"
        ? { platform, full_content: fullContent, top_keywords: topKeywords }
        : { platform, post_content: fullContent, searched_hashtags: topKeywords }

    const payload = {
      user_id: userId,
      title: selectedContent.title || "제목 없음",
      task_type: taskType,
      platform,
      content: fullContent,
      task_data: taskData,
      status: "created",
      scheduled_at: null,
    }

    try {
      console.log("📤 SNS 콘텐츠 저장 요청 payload:", payload)
      await axios.post("https://localhost:8005/workspace/automation/manual", payload)
      alert("SNS 콘텐츠가 저장되었습니다!")
    } catch (err) {
      console.error("SNS 콘텐츠 저장 실패:", err)
      alert("저장 중 오류가 발생했습니다.")
    }
  }

  const handlePublishContent = async () => {
    if (!selectedContent) {
      alert("발행할 콘텐츠를 선택해주세요.")
      return
    }

    const content = selectedContent.task_data?.post_content || selectedContent.task_data?.full_content || ""
    const imageUrl = selectedContent.task_data?.image_url

    if (!imageUrl) {
      alert("이미지 URL이 없습니다. 콘텐츠 생성 시 이미지가 필요합니다.")
      return
    }

    const taskType = "sns_publish_instagram"
    const taskData = {
      post_content: content,
      image_url: imageUrl,
    }

    const { date, time, type } = schedule.publishSchedule
    let scheduledAt = null
    if (type === "scheduled" && date && time) {
      scheduledAt = `${date} ${time}:00`
    }

    const payload = {
      user_id: userId,
      title: selectedContent.title || "제목 없음",
      task_type: taskType,
      content,
      task_data: taskData,
      status: "scheduled",
      scheduled_at: scheduledAt,
    }

    try {
      console.log("📤 SNS 콘텐츠 발행 요청 payload:", payload)
      await axios.post("https://localhost:8005/workspace/automation/manual", payload)
      alert("발행 요청이 완료되었습니다!")
    } catch (err) {
      console.error("SNS 콘텐츠 발행 실패:", err)
      alert("발행 중 오류가 발생했습니다.")
    }
  }



  const handlePublishEmail = async () => {
  if (!selectedTemplate) {
    alert("발송할 템플릿을 선택해주세요.")
    return
  }

  if (!toEmail) {
    alert("받는 사람 이메일을 입력해주세요.")
    return
  }

  const { title, content, id: templateId } = selectedTemplate
  const { type, date, time } = schedule.publishSchedule

  // 예약 발송 시간 구성
  const scheduledAt =
    type === "scheduled" && date && time ? `${date} ${time}:00` : null

  const payload = {
    user_id: userId,
    title: title || "제목 없음",
    task_type: "send_email",
    platform: "email",
    content: content || "",
    task_data: {
      to_email: toEmail,
      subject: title,
      body: content,
      template_id: templateId,
    },
    status: "scheduled",
    scheduled_at: scheduledAt,
  }

  try {
    console.log("📧 이메일 발송 요청 payload:", payload)

    // 1. 이메일 자동화 task 저장
    await axios.post("https://localhost:8005/workspace/automation/manual", payload)

    // 2. 즉시 발송이면 바로 메일 API 호출
    if (type === "immediate") {
      await axios.post("https://localhost:8005/email/send", {
        to_emails: [toEmail],
        subject: title,
        body: content,
      })
    }

    alert("이메일 발송 요청이 완료되었습니다!")
  } catch (err) {
    console.error("이메일 발송 실패:", err)
    alert("발송 중 오류가 발생했습니다.")
  }
}

  const handleGenerateContent = async (keyword: string, platform: string) => {
    try {
      const generated = await generateContent(keyword, platform)
      const autoTitle = `${keyword} 자동 생성 콘텐츠`
      const content = generated.task_data.full_content || generated.task_data.post_content || ""
      const keywords = generated.task_data.top_keywords || generated.task_data.searched_hashtags || []

      const newContent: AutomationTask = {
        task_id: Date.now(),
        title: autoTitle,
        task_type: platform === "naver_blog" ? "sns_publish_blog" : "sns_publish_instagram",
        task_data: {
          ...generated.task_data,
          platform: platform,
        },
        status: "created",
        created_at: new Date().toISOString(),
      }

      setSelectedContent(newContent)
      email.setContentForm({ title: autoTitle, content })
      setTags(keywords)

      return { title: autoTitle, content, tags: keywords }
    } catch (err) {
      console.error("❌ 콘텐츠 생성 실패:", err)
      alert("콘텐츠 생성에 실패했습니다.")
      return { title: "", content: "", tags: [] }
    }
  }

  const handleContentSelect = (content: AutomationTask) => {
    setSelectedContent(content)
    email.setContentForm({
      title: content.title,
      content:
        content.task_data?.full_content ||
        content.task_data?.post_content ||
        content.task_data?.content || "",
    })
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case "automation":
        return (
          <div className="space-y-4">
            <Calendar
              selectedDate={schedule.selectedDate}
              googleEvents={schedule.googleEvents}
              setSelectedDate={schedule.setSelectedDate}
              automationTasks={schedule.automationTasks}
              scheduleEvents={schedule.scheduleEvents}
              newEvent={schedule.newEvent}
              setNewEvent={schedule.setNewEvent}
              onAddEvent={schedule.addEvent}
              userId={userId!}
              getEventsForDate={schedule.getEventsForDate}
              upcomingEvents={schedule.upcomingEvents}
              fetchUpcomingEvents={schedule.fetchUpcomingEvents}
            />
            <AutomationTable
              automationTasks={schedule.automationTasks}
              onTaskClick={handleTaskClick}
              onDeleteTask={handleDeleteTask}
            />
          </div>
        )
      case "sns":
        return (
          <div className="grid lg:grid-cols-3 gap-4">
            <AiContentList contents={schedule.automationTasks} onContentSelect={handleContentSelect} />
            <div className="lg:col-span-2">
              <ContentEditor
                contentForm={email.contentForm}
                setContentForm={email.setContentForm}
                selectedTemplate={selectedContent}
                publishSchedule={schedule.publishSchedule}
                setPublishSchedule={schedule.setPublishSchedule}
                onSave={handleSaveContent}
                onPublish={handlePublishContent}
                onGenerateContent={handleGenerateContent}
                saveGeneratedContent={saveGeneratedContent}
                onSetTags={setTags}
                showContentGenerator={true}
                tags={tags}
              />
            </div>
          </div>
        )
      case "email":
        return workspaceLoading ? (
          <div className="p-10 text-center text-gray-500">데이터 불러오는 중...</div>
        ) : (
          <div className="grid lg:grid-cols-3 gap-4">
            <EmailTemplateList
              templates={emailTemplates}
              contents={emailContents}
              selectedTemplate={selectedTemplate}
              onTemplateSelect={handleTemplateSelect}
            />
            <div className="lg:col-span-2 space-y-2">
              <EmailEditor
                contentForm={email.contentForm}
                setContentForm={email.setContentForm}
                isPreviewMode={isPreviewMode}
                setIsPreviewMode={setIsPreviewMode}
                publishSchedule={schedule.publishSchedule}
                setPublishSchedule={schedule.setPublishSchedule}
                onSave={handleSaveContent}
                onPublish={handlePublishEmail}
                toEmail={toEmail}
                setToEmail={setToEmail}
              />
            </div>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-yellow-50 to-emerald-50">
      <nav className="px-4 py-3 bg-white/90 backdrop-blur-sm border-b border-gray-200">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <Link href="/" className="flex items-center space-x-2">
            <Image src="/placeholder.svg?height=24&width=24" alt="TinkerBell Logo" width={24} height={24} className="rounded-full" />
            <span className="text-lg font-bold text-gray-900">TinkerBell</span>
          </Link>
          <div className="flex items-center space-x-3">
            <span className="text-sm text-gray-600">솔로프리너 워크스페이스</span>
            <div className="w-7 h-7 bg-green-100 rounded-full flex items-center justify-center">
              <User className="w-3 h-3 text-green-600" />
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto p-4">
        <TabMenu activeTab={activeTab} setActiveTab={setActiveTab} onTabChange={handleTabChange} />
        {renderTabContent()}
        <TaskDetailSheet
          isOpen={isTaskSheetOpen}
          onOpenChange={setIsTaskSheetOpen}
          selectedTask={selectedTask}
          setSelectedTask={setSelectedTask}
          onSave={handleSaveTaskData}
        />
      </div>
    </div>
  )
}