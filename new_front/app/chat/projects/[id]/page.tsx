"use client"

import React, { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { ArrowLeft, Upload, FileText, Trash2, Edit2, Check, MessageCircle, Send, Bot } from "lucide-react"
import { API_BASE_URL } from "@/config/constants"

interface Project {
  id: number
  title: string
  description: string
  category: string
  createdAt: string
  updatedAt: string
}

interface ProjectDocument {
  document_id: number
  project_id: number
  file_name: string
  file_path: string
  uploaded_at: string
}

interface ProjectChat {
  conversation_id: number
  title: string
  lastMessage: string
  lastMessageTime: string
  messageCount: number
  createdAt: string
}

export default function ProjectDetailPage() {
  const router = useRouter()
  const params = useParams()
  const projectId = params?.id ? Number(Array.isArray(params.id) ? params.id[0] : params.id) : null

  const [userId, setUserId] = useState<number | null>(null)
  const [project, setProject] = useState<Project | null>(null)
  const [documents, setDocuments] = useState<ProjectDocument[]>([])
  const [chats, setChats] = useState<ProjectChat[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [isCreatingChat, setIsCreatingChat] = useState(false)

  const [chatInput, setChatInput] = useState("")
  const [creatingChat, setCreatingChat] = useState(false)

  const [editingChatId, setEditingChatId] = useState<number | null>(null)
  const [editedTitle, setEditedTitle] = useState("")
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null)

  const chatTitlesKey = `chat_titles_${projectId}`

  // 사용자 인증 체크
  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedUser = localStorage.getItem("user")
      if (storedUser) {
        try {
          const user = JSON.parse(storedUser)
          setUserId(user.user_id)
        } catch (e) {
          console.error("유저 파싱 오류:", e)
          router.push("/login")
        }
      } else {
        router.push("/login")
      }
    }
  }, [router])

  // 프로젝트, 문서, 채팅 데이터 로딩
  const fetchProject = async () => {
    if (!userId || !projectId) return
    try {
      const response = await fetch(`${API_BASE_URL}/projects?user_id=${userId}`)
      const result = await response.json()
      if (result.success) {
        const foundProject = result.data.find((p: Project) => p.id === projectId)
        if (foundProject) setProject(foundProject)
        else router.push("/chat/room")
      }
    } catch (e) {
      console.error("프로젝트 불러오기 실패:", e)
    }
  }

  const fetchDocuments = async () => {
    if (!projectId) return
    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/documents`)
      const result = await response.json()
      if (result.success) setDocuments(result.data || [])
    } catch (e) {
      console.error("문서 불러오기 실패:", e)
    }
  }

  const mergeLocalChatTitles = (fetchedChats: ProjectChat[]) => {
    const saved = JSON.parse(localStorage.getItem(chatTitlesKey) || "{}")
    return fetchedChats.map((chat) => ({
      ...chat,
      title: saved[chat.conversation_id] || chat.title,
    }))
  }

  const fetchChats = async () => {
    if (!projectId) return
    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/chats`)
      const result = await response.json()
      if (result.success) setChats(mergeLocalChatTitles(result.data || []))
    } catch (e) {
      console.error("채팅 불러오기 실패:", e)
    }
  }

  useEffect(() => {
    if (userId && projectId) {
      setIsLoading(true)
      Promise.all([fetchProject(), fetchDocuments(), fetchChats()]).finally(() =>
        setIsLoading(false)
      )
    }
  }, [userId, projectId])

  // 파일 업로드
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length || !userId || !projectId) return
    const file = e.target.files[0]
    if (file.size > 10 * 1024 * 1024) {
      alert("파일 크기는 10MB 이하여야 합니다.")
      return
    }

    setUploading(true)
    const formData = new FormData()
    formData.append("file", file)
    formData.append("user_id", String(userId))

    // conversation_id가 null이 아닐 때만 추가
    if (activeConversationId !== null && activeConversationId !== undefined) {
      formData.append("conversation_id", String(activeConversationId))
    }

    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/documents`, {
        method: "POST",
        body: formData,
      })
      const result = await response.json()
      if (result.success) {
        setDocuments((prev) => [...prev, result.data])
        alert("파일이 성공적으로 업로드되었습니다.")
      } else {
        alert("파일 업로드에 실패했습니다: " + result.error)
      }
    } catch (e) {
      console.error("문서 업로드 실패:", e)
      alert("파일 업로드 중 오류가 발생했습니다.")
    } finally {
      setUploading(false)
      // 파일 입력 초기화
      if (e.target) {
        e.target.value = ""
      }
    }
  }

  // 파일 삭제
  const handleDeleteDocument = async (docId: number) => {
    if (!window.confirm("이 문서를 삭제하시겠습니까?")) return
    try {
      const response = await fetch(
        `${API_BASE_URL}/projects/${projectId}/documents/${docId}`,
        { method: "DELETE" }
      )
      const result = await response.json()
      if (result.success) {
        setDocuments((prev) => prev.filter((doc) => doc.document_id !== docId))
      }
    } catch (e) {
      console.error("문서 삭제 실패:", e)
    }
  }

  // 채팅 생성 + AI 응답 (질문도 함께 처리)
  const handleSendChat = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!chatInput.trim() || !userId || !projectId || isCreatingChat) return
    
    setIsCreatingChat(true)
    const currentInput = chatInput
    setChatInput("")

    try {
      // 1. 채팅방 생성 (메시지도 함께)
      const createChatResponse = await fetch(`${API_BASE_URL}/projects/${projectId}/chats`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          title: currentInput.slice(0, 20),
          message: currentInput
        }),
      })
      const chatResult = await createChatResponse.json()
      if (!chatResult.success) throw new Error("채팅 생성 실패")

      const conversationId = chatResult.data.conversation_id

      // 2. AI 응답 생성
      const aiResponse = await fetch(`${API_BASE_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          conversation_id: conversationId,
          message: currentInput,
          preferred_agent: "unified_agent"
        }),
      })

      if (!aiResponse.ok) {
        console.warn("AI 응답 생성 실패, 채팅방으로 이동합니다.")
      }

      // 3. 채팅방으로 이동
      router.push(`/chat/room?conversation_id=${conversationId}&project_id=${projectId}`)
    } catch (error) {
      console.error("채팅 생성 실패:", error)
      setChatInput(currentInput)
      alert("채팅 생성에 실패했습니다.")
    } finally {
      setIsCreatingChat(false)
    }
  }

  // 채팅 제목 저장 (로컬)
  const saveChatTitle = (chatId: number, title: string) => {
    const saved = JSON.parse(localStorage.getItem(chatTitlesKey) || "{}")
    saved[chatId] = title
    localStorage.setItem(chatTitlesKey, JSON.stringify(saved))
    setChats((prev) =>
      prev.map((chat) => (chat.conversation_id === chatId ? { ...chat, title } : chat))
    )
    setEditingChatId(null)
  }

  // 채팅 삭제
  const handleDeleteChat = async (chatId: number) => {
    if (!window.confirm("채팅을 삭제하시겠습니까?")) return
    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/chats/${chatId}`, {
        method: "DELETE",
      })
      const result = await response.json()
      if (result.success) {
        setChats((prev) => prev.filter((c) => c.conversation_id !== chatId))
      }
    } catch (e) {
      console.error("채팅 삭제 실패:", e)
    }
  }

  if (isLoading) return <div className="p-6 text-center">로딩 중...</div>
  if (!project) return <div className="p-6 text-center">프로젝트를 찾을 수 없습니다.</div>

  return (
    <div className="flex min-h-screen bg-white p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* 프로젝트 헤더 */}
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.push("/chat/room")} className="hover:bg-white/70">
            <ArrowLeft className="w-4 h-4 mr-2" /> 뒤로
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{project.title}</h1>
            <p className="text-gray-600">{project.description || "프로젝트 설명이 없습니다."}</p>
          </div>
        </div>

        {/* AI와 대화하기 */}
        <Card className="bg-white rounded-3xl shadow-sm border border-gray-200">
          <CardContent className="p-6">
            <form onSubmit={handleSendChat}>
              <div className="relative">
                <div className="flex items-center gap-3 p-4 border border-green-200 rounded-3xl bg-green-50 focus-within:bg-white focus-within:border-green-200 transition-colors">
                  <Input
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="자유롭게 대화해 보세요."
                    className="flex-1 border-0 bg-transparent focus:ring-0 focus:outline-none text-gray-700"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        handleSendChat()
                      }
                    }}
                  />
                  <Button
                    type="submit"
                    disabled={isCreatingChat || !chatInput.trim()}
                    size="sm"
                    className="w-8 h-8 rounded-full bg-green-500 hover:bg-green-600 text-white flex-shrink-0 p-0"
                  >
                    {isCreatingChat ? (
                      <div className="animate-spin rounded-full h-3 w-3 border border-white border-t-transparent"></div>
                    ) : (
                      <Send className="w-3 h-3" />
                    )}
                  </Button>
                </div>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* 파일 업로드 */}
        <Card className="bg-white rounded-2xl shadow-sm border border-green-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                  <FileText className="w-4 h-4 text-green-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-800">파일 추가</h3>
              </div>
              <Button
                onClick={() => document.getElementById("fileUpload")?.click()}
                disabled={uploading}
                size="sm"
                className="bg-green-500 hover:bg-green-600 text-white rounded-lg"
              >
                {uploading ? "업로드 중..." : "파일 업로드"}
                <Upload className="w-4 h-4 ml-2" />
              </Button>
            </div>
            
            <input 
              type="file" 
              id="fileUpload" 
              className="hidden" 
              onChange={handleFileUpload}
              accept=".pdf,.doc,.docx,.txt,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.gif"
            />
            
            {documents.length === 0 ? (
              <div className="text-center py-8">
                <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-3">
                  <FileText className="w-6 h-6 text-green-400" />
                </div>
                <p className="text-gray-500">업로드된 파일이 없습니다</p>
              </div>
            ) : (
              <div className="space-y-2">
                {documents.map((doc) => (
                  <div key={doc.document_id} className="flex justify-between items-center p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex items-center gap-3">
                      <FileText className="w-4 h-4 text-green-600" />
                      <div>
                        <span className="font-medium text-gray-900 text-sm">{doc.file_name}</span>
                        <p className="text-xs text-gray-500">
                          {new Date(doc.uploaded_at).toLocaleDateString('ko-KR')}
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg"
                      onClick={() => handleDeleteDocument(doc.document_id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 채팅 목록 */}
        <Card className="bg-white rounded-2xl shadow-sm border border-green-200">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                <MessageCircle className="w-4 h-4 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-800">채팅 목록</h3>
              <span className="text-sm text-gray-500">({chats.length})</span>
            </div>
            
            {chats.length === 0 ? (
              <div className="text-center py-8">
                <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-3">
                  <MessageCircle className="w-6 h-6 text-gray-400" />
                </div>
                <p className="text-gray-500">채팅이 없습니다</p>
              </div>
            ) : (
              <div className="space-y-2">
                {chats.map((chat) => (
                  <div
                    key={chat.conversation_id}
                    className="flex justify-between items-center p-4 bg-green-50 rounded-xl hover:bg-green-100 transition-colors cursor-pointer group"
                    onClick={() =>
                      router.push(
                        `/chat/room?conversation_id=${chat.conversation_id}&project_id=${projectId}`
                      )
                    }
                  >
                    {editingChatId === chat.conversation_id ? (
                      <div className="flex gap-2 flex-1">
                        <Input
                          value={editedTitle}
                          onChange={(e) => setEditedTitle(e.target.value)} 
                          className="flex-1 rounded-lg"
                          onClick={(e) => e.stopPropagation()}
                        />
                        <Button
                          size="sm"
                          className="bg-purple-500 hover:bg-purple-600 text-white rounded-lg"
                          onClick={(e) => {
                            e.stopPropagation()
                            saveChatTitle(chat.conversation_id, editedTitle)
                          }}
                        >
                          <Check className="w-4 h-4" />
                        </Button>
                      </div>
                    ) : (
                      <>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-gray-900 mb-1 truncate">{chat.title}</div>
                          <div className="text-sm text-gray-600 mb-1 line-clamp-2 break-words">{chat.lastMessage}</div>
                          <div className="text-xs text-gray-500">
                            {new Date(chat.lastMessageTime).toLocaleDateString('ko-KR')} • {chat.messageCount}개 메시지
                          </div>
                        </div>
                        <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-purple-600 hover:bg-purple-50 rounded-lg"
                            onClick={(e) => {
                              e.stopPropagation()
                              setEditingChatId(chat.conversation_id)
                              setEditedTitle(chat.title)
                            }}
                          >
                            <Edit2 className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-red-500 hover:bg-red-50 rounded-lg"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteChat(chat.conversation_id)
                            }}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}