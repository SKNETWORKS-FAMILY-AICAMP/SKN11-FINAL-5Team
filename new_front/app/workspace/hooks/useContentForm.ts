"use client"

import { useState, useEffect } from "react"
import type {
  ContentForm,
  EmailContent,
  EmailTemplate,
  AiGeneratedContent,
} from "../types"
import {
  createEmailTemplate,
  updateEmailTemplate,
  fetchEmailTemplates,
} from "../lib/api"
import axios from "axios"
export function useContentForm(userId: number) {
  const [contentForm, setContentForm] = useState<ContentForm>({
    title: "",
    content: "",
  })
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | EmailContent | null>(null)
  const [emailContents, setEmailContents] = useState<EmailContent[]>([])
  const [templates, setTemplates] = useState<EmailTemplate[]>([])

  useEffect(() => {
    const fetchData = async () => {
      try {
        const { templates, contents } = await fetchEmailTemplates(userId)
        setTemplates(templates)
        setEmailContents(contents)
      } catch (error) {
        console.error("이메일 템플릿 불러오기 실패:", error)
      }
    }

    if (userId) fetchData()
  }, [userId])

const saveEmailContent = async () => {
  const payload = {
    user_id: Number(userId), // 타입 확실히
    title: contentForm.title.trim(),
    content: contentForm.content.trim(),
    channel_type: "EMAIL",
    content_type: "text", // 또는 "marketing"
  }

  console.log("📤 보낼 payload", payload)

  try {
    const res = await axios.post("http://localhost:8005/workspace/email", payload)
    console.log("✅ 이메일 콘텐츠 저장 성공", res.data)
    alert("콘텐츠가 저장되었습니다!")

    // ✅ 저장 후 목록 새로고침
    const { templates, contents } = await fetchEmailTemplates(userId)
    setTemplates(templates)
    setEmailContents(contents)

  } catch (err) {
    console.error("❌ 저장 실패:", err)
    alert("저장에 실패했습니다.")
  }
}

  return {
    contentForm,
    setContentForm,
    emailContents,
    setEmailContents,
    templates,
    setTemplates,
    selectedTemplate,
    setSelectedTemplate,
    saveEmailContent,
  }
}

export function useAiContents() {
  const [aiGeneratedContents, setAiGeneratedContents] = useState<AiGeneratedContent[]>([])

const generateContent = (keywords: string, platform: string) => {
  const contentText = `${keywords}에 대한 예시 콘텐츠입니다.`

  const generated: AiGeneratedContent = {
    task_id: Date.now(),
    user_id: 3,
    task_type: platform.toLowerCase(),
    title: `[${platform}] ${keywords} 관련 제목`,
    template_id: undefined,
    task_data: {
      content: contentText,
      platform
    },
    status: "draft",
    scheduled_at: null,
    executed_at: null,
    created_at: new Date().toISOString()
  }

    setAiGeneratedContents((prev) => [generated, ...prev])
    return generated
  }

  return { aiGeneratedContents, generateContent }}