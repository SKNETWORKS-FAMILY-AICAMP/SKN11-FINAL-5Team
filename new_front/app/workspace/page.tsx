"use client"

import { useState, useEffect } from "react"
import type React from "react"
import Image from "next/image"
import Link from "next/link"
import { User } from "lucide-react"
import { useRouter } from "next/navigation"

// Components
import { TabMenu } from "./components/TabMenu"
import { Calendar } from "./components/Calendar"
import { ScheduleSidebar } from "./components/ScheduleSidebar"
import { AiContentList } from "./components/AiContentList"
import { TaskDetailSheet } from "./components/TaskDetailSheet"
import { ContentEditor } from "./components/ContentEditor"
import { EmailEditor } from "./components/EmailEditor"
import { EmailTemplateList } from "./components/EmailTemplateList"
import { AutomationTable } from "./components/AutomationTable"

// Hooks
import { useSchedule } from "./hooks/useSchedule"
import { useContentForm, useAiContents } from "./hooks/useContentForm"

// Types
import type { AutomationTask, EmailTemplate, EmailContent } from "./types"

export default function WorkspacePage() {
  const router = useRouter()
  const [userId, setUserId] = useState<number | null>(null)
  const [toEmail, setToEmail] = useState("")

  // 모든 Hook을 조건 없이 최상단에서 호출
  const { aiGeneratedContents, generateContent } = useAiContents()
  const [activeTab, setActiveTab] = useState<string>("automation")
  const [isPreviewMode, setIsPreviewMode] = useState(false)
  const [selectedTask, setSelectedTask] = useState<AutomationTask | null>(null)
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | EmailContent | null>(null)
  const [isTaskSheetOpen, setIsTaskSheetOpen] = useState(false)

  const {
    selectedDate,
    setSelectedDate,
    automationTasks,
    scheduleEvents,
    newEvent,
    setNewEvent,
    publishSchedule,
    setPublishSchedule,
    getEventsForDate,
    addEvent,
    deleteTask,
    updateTask,
    publishContent,
  } = useSchedule()

  const {
    contentForm,
    setContentForm,
    emailContents,
    setEmailContents,
    templates,
    saveEmailContent,
  } = useContentForm(userId ?? 3)

  useEffect(() => {

    console.log("🧭 [Workspace] user 체크 시작")

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

  if (userId === null) {
    console.log("⏳ [Workspace] userId가 null - 로딩 중 화면 렌더링")
    return (
      <div className="flex justify-center items-center min-h-[60vh] text-gray-500">
        로그인 정보를 확인 중입니다...
      </div>
    )
  }
  else {
  console.log("✅ [Workspace] userId 감지됨 - 페이지 렌더링 진행")}

  const handleTabChange = () => {
    setSelectedTemplate(null)
    setContentForm({ title: "", content: "" })
  }

  const handleTaskClick = (task: AutomationTask) => {
    setSelectedTask(task)
    setIsTaskSheetOpen(true)
  }

  const handleDeleteTask = (taskId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    deleteTask(taskId)
  }

  const handleSaveTaskData = () => {
    if (selectedTask) {
      updateTask(selectedTask)
      setIsTaskSheetOpen(false)
    }
  }

  const handleTemplateSelect = (template: EmailTemplate | EmailContent) => {
    setSelectedTemplate(template)
    setContentForm({
      title: template.title,
      content: template.content,
    })
  }

  const handleSaveContent = () => {
    saveEmailContent()
    alert("콘텐츠가 저장되었습니다!")
  }

  const handlePublishContent = async () => {
    if (!contentForm.title || !contentForm.content) {
      alert("제목과 내용을 입력해주세요!")
      return
    }
    if (!toEmail) {
      alert("수신자 이메일을 입력해주세요!")
      return
    }
    const success = await publishContent(contentForm.title, contentForm.content, "email", toEmail)
    if (success) {
      if (publishSchedule.type === "immediate") {
        alert("콘텐츠가 즉시 발행되었습니다!")
      } else {
        alert(`콘텐츠가 ${publishSchedule.date} ${publishSchedule.time}에 발행 예약되었습니다!`)
      }
    }
  }

  const handleGenerateContent = (keywords: string, platform: string) => {
    const generated = generateContent(keywords, platform)
    setContentForm({
      title: generated.title,
      content: generated.task_data.content,
    })
  }

  const handleContentSelect = (content: any) => {
    setSelectedTemplate(content)
    setContentForm({
      title: content.title,
      content: content.content,
    })
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case "automation":
        return (
          <div className="space-y-4">
            <div className="grid lg:grid-cols-2 gap-4">
              <Calendar
                selectedDate={selectedDate}
                setSelectedDate={setSelectedDate}
                scheduleEvents={scheduleEvents}
                automationTasks={automationTasks}
                newEvent={newEvent}
                setNewEvent={setNewEvent}
                onAddEvent={addEvent}
              />
              <ScheduleSidebar selectedDate={selectedDate} getEventsForDate={getEventsForDate} />
            </div>
            <AutomationTable
              automationTasks={automationTasks}
              onTaskClick={handleTaskClick}
              onDeleteTask={handleDeleteTask}
            />
          </div>
        )
      case "sns":
        return (
          <div className="grid lg:grid-cols-3 gap-4">
            <AiContentList contents={aiGeneratedContents} onContentSelect={handleContentSelect} />
            <div className="lg:col-span-2">
              <ContentEditor
                contentForm={contentForm}
                setContentForm={setContentForm}
                isPreviewMode={isPreviewMode}
                setIsPreviewMode={setIsPreviewMode}
                selectedTemplate={selectedTemplate}
                publishSchedule={publishSchedule}
                setPublishSchedule={setPublishSchedule}
                onSave={handleSaveContent}
                onPublish={handlePublishContent}
                onGenerateContent={handleGenerateContent}
                showContentGenerator={true}
              />
            </div>
          </div>
        )
      case "email":
        return (
          <div className="grid lg:grid-cols-3 gap-4">
            <EmailTemplateList
              templates={templates || []}
              contents={emailContents || []}
              selectedTemplate={selectedTemplate}
              onTemplateSelect={handleTemplateSelect}
            />
            <div className="lg:col-span-2 space-y-2">
              <EmailEditor
                contentForm={contentForm}
                setContentForm={setContentForm}
                isPreviewMode={isPreviewMode}
                setIsPreviewMode={setIsPreviewMode}
                publishSchedule={publishSchedule}
                setPublishSchedule={setPublishSchedule}
                onSave={handleSaveContent}
                onPublish={handlePublishContent}
              />
              <input
                type="email"
                placeholder="받는 사람 이메일 주소 입력"
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                value={toEmail}
                onChange={(e) => setToEmail(e.target.value)}
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
            <Image
              src="/placeholder.svg?height=24&width=24"
              alt="TinkerBell Logo"
              width={24}
              height={24}
              className="rounded-full"
            />
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
