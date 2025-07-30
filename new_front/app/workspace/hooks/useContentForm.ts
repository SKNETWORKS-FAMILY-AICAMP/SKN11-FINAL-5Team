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
} from "../lib/api"
import axios from "axios"

async function fetchEmailTemplates(userId: number) {
  const res = await axios.get("http://localhost:8005/api/email/templates", {
    params: { user_id: userId },
  })
  return {
    templates: res.data.templates,
    contents: [], // ← 필요 시 수정
  }
}
export function useContentForm(userId: number | null) {
  const [contentForm, setContentForm] = useState<ContentForm>({
    title: "",
    content: "",
  })
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | EmailContent | null>(null)
  const [emailContents, setEmailContents] = useState<EmailContent[]>([])
  const [templates, setTemplates] = useState<EmailTemplate[]>([])
  
  
  

  useEffect(() => {
    if (!userId) return

    const fetchData = async () => {
      try {
        const { templates, contents } = await fetchEmailTemplates(userId)
        setTemplates(templates)
        
        // setEmailContents(contents)
      } catch (error) {
        console.error("이메일 템플릿 불러오기 실패:", error)
      }
    }

    fetchData()
  }, [userId])

  const saveEmailContent = async () => {
  if (!userId) {
    alert("로그인 정보가 없습니다. 다시 로그인해주세요.")
    return
  }

  const payload = {
    user_id: Number(userId),
    title: contentForm.title.trim(),
    content: contentForm.content.trim(),
    channel_type: "EMAIL",
    content_type: "text",
  }

  const payloadWithType = {
    ...payload,
    template_type: "user_made",  
  }

  console.log("📤 보낼 payload", payloadWithType)

  try {
    const res = await axios.post("http://localhost:8005/api/email/templates", payloadWithType)
    alert("콘텐츠가 저장되었습니다!")

    const { templates, contents } = await fetchEmailTemplates(userId)
    setTemplates(templates)
    // setEmailContents(contents)
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

export function useAiContents(userId: number | null) {
  const [aiGeneratedContents, setAiGeneratedContents] = useState<AiGeneratedContent[]>([])
  const [latestGeneratedContent, setLatestGeneratedContent] = useState<any | null>(null) 

  const generateContent = async (keyword: string, platform: string) => {
    if (!userId) {
      throw new Error("userId가 없습니다. 로그인 상태를 확인해주세요.")
    }

    let url = ""
    let taskType = ""

    if (platform === "instagram") {
      url = "http://localhost:8003/marketing/api/v1/content/instagram"
      taskType = "sns_publish_instagram"
    } else if (platform === "naver") {
      url = "http://localhost:8003/marketing/api/v1/content/blog"
      taskType = "sns_publish_blog"
    } else {
      throw new Error("지원되지 않는 플랫폼입니다.")
    }

    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ keyword }),
    })

    if (!res.ok) {
      throw new Error("콘텐츠 생성 실패")
    }

    const data = await res.json()

    const content =
      data.post_content ??
      data.instagram_content?.post_content ??
      data.full_content ??
      data.blog_content?.full_content ?? ""

    const hashtags =
      data.selected_hashtags ??
      data.instagram_content?.selected_hashtags ??
      data.hashtag_analysis?.searched_hashtags ?? []

    const topKeywords =
      data.blog_content?.top_keywords ??
      data.top_keywords ?? []

    const generated = {
      title: `${keyword} 자동 생성 콘텐츠`,
      task_type: taskType,
      task_data:
        platform === "instagram"
          ? {
              platform,
              post_content: content,
              searched_hashtags: hashtags,
            }
          : {
              platform,
              full_content: content,
              top_keywords: topKeywords,
            },
      content,
      keywords: [...hashtags, ...topKeywords],
    }

    setLatestGeneratedContent(generated) // 
    return generated
  }

  // 저장 함수 추가
  const saveGeneratedContent = async () => {
    if (!userId || !latestGeneratedContent) return

    const payload = {
      user_id: userId,
      title: latestGeneratedContent.title,
      task_type: latestGeneratedContent.task_type,
      task_data: latestGeneratedContent.task_data,
      status: "created",
    }

    try {
      const res = await axios.post("http://localhost:8005/workspace/automation/ai", payload)
      alert("✅ 자동 생성 콘텐츠가 저장되었습니다!")
      return res.data
    } catch (err) {
      console.error("❌ 자동 생성 콘텐츠 저장 실패:", err)
      alert("저장 중 오류가 발생했습니다.")
    }
  }

  const fetchGeneratedContents = async () => {
  const res = await axios.get("http://localhost:8005/workspace/automation/contents", {
    params: { user_id: userId },
  });
  setAiGeneratedContents(res.data.data); // 기존 state에 넣기
};

  // ✅ 저장 함수와 latest 추가 리턴
  return {
    aiGeneratedContents,
    setAiGeneratedContents,
    generateContent,
    saveGeneratedContent,     
    latestGeneratedContent,   
    fetchGeneratedContents,
    
  }
}
