"use client"

import React, { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  ArrowLeft,
  Upload,
  FileText,
  Trash2,
  MessageSquare,
  Plus,
  Calendar,
  Clock
} from "lucide-react"
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

  // params.id 안전하게 숫자로 변환
  const projectId = params?.id
    ? Number(Array.isArray(params.id) ? params.id[0] : params.id)
    : null

  const [userId, setUserId] = useState<number | null>(null)
  const [project, setProject] = useState<Project | null>(null)
  const [documents, setDocuments] = useState<ProjectDocument[]>([])
  const [chats, setChats] = useState<ProjectChat[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [creatingChat, setCreatingChat] = useState(false)

  // 사용자 초기화
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
          return
        }
      } else {
        router.push("/login")
        return
      }
    }
  }, [router])

  // 프로젝트 정보 가져오기
  const fetchProject = async () => {
    if (!userId || !projectId) return

    try {
      const response = await fetch(`${API_BASE_URL}/projects?user_id=${userId}`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      if (result.success) {
        const foundProject = result.data.find((p: Project) => p.id === projectId)
        if (foundProject) {
          setProject(foundProject)
        } else {
          alert("프로젝트를 찾을 수 없습니다.")
          router.push("/chat/room")
        }
      } else {
        console.error("프로젝트 조회 실패:", result.error)
        alert(`프로젝트 조회 실패: ${result.error}`)
      }
    } catch (error) {
      console.error("프로젝트 정보 불러오기 실패:", error)
      alert("프로젝트 정보를 불러오는 중 오류가 발생했습니다.")
    }
  }

  // 문서 목록 가져오기
  const fetchDocuments = async () => {
    if (!projectId) return
    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/documents`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const result = await response.json()
      if (result.success) {
        setDocuments(result.data || [])
      }
    } catch (error) {
      console.error("문서 목록 불러오기 실패:", error)
    }
  }

  // 채팅 목록 가져오기
  const fetchChats = async () => {
    if (!projectId) return
    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/chats`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const result = await response.json()
      if (result.success) {
        setChats(result.data || [])
      }
    } catch (error) {
      console.error("채팅 목록 불러오기 실패:", error)
    }
  }

  useEffect(() => {
    if (userId && projectId) {
      setIsLoading(true)
      Promise.all([fetchProject(), fetchDocuments(), fetchChats()])
        .finally(() => setIsLoading(false))
    }
  }, [userId, projectId])

  // 파일 업로드
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0 || !userId || !projectId) return

    const file = e.target.files[0]
    if (file.size > 10 * 1024 * 1024) {
      alert("파일 크기는 10MB 이하여야 합니다.")
      return
    }

    setUploading(true)
    const formData = new FormData()
    formData.append("file", file)
    formData.append("user_id", userId.toString())
   

    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/documents`, {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      if (result.success) {
        alert("문서가 성공적으로 업로드되었습니다.")
        await fetchDocuments()
        e.target.value = ""
      } else {
        alert("문서 업로드 실패: " + (result.error || "알 수 없는 오류"))
      }
    } catch (error) {
      console.error("문서 업로드 실패:", error)
      alert("문서 업로드 중 오류가 발생했습니다: " + (error as Error).message)
    } finally {
      setUploading(false)
    }
  }

  // 문서 삭제
  const handleDeleteDocument = async (docId: number) => {
    if (!projectId) return
    const confirmDelete = window.confirm("이 문서를 삭제하시겠습니까?")
    if (!confirmDelete) return

    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/documents/${docId}`, {
        method: "DELETE",
      })
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const result = await response.json()
      if (result.success) {
        setDocuments((prev) => prev.filter((doc) => doc.document_id !== docId))
        alert("문서가 성공적으로 삭제되었습니다.")
      } else {
        alert("문서 삭제 실패: " + (result.error || "알 수 없는 오류"))
      }
    } catch (error) {
      console.error("문서 삭제 실패:", error)
      alert("문서 삭제 중 오류가 발생했습니다: " + (error as Error).message)
    }
  }

  // 새 채팅 시작
  const handleNewChat = async () => {
    if (!userId || !projectId) {
      alert("사용자 정보가 없습니다. 다시 로그인해주세요.")
      return
    }

    setCreatingChat(true)
    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/chats`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
          title: `새 채팅 ${new Date().toLocaleString()}`,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      if (result.success) {
        router.push(`/chat/room?conversation_id=${result.data.conversation_id}&project_id=${projectId}`)
      } else {
        alert("채팅 생성 실패: " + (result.error || "알 수 없는 오류"))
      }
    } catch (error) {
      console.error("채팅 생성 실패:", error)
      alert("채팅 생성 중 오류가 발생했습니다: " + (error as Error).message)
    } finally {
      setCreatingChat(false)
    }
  }

  const handleOpenChat = (chatId: number) => {
    router.push(`/chat/room?conversation_id=${chatId}&project_id=${projectId}`)
  }

  // 로딩 화면
  if (isLoading) {
    return (
      <div className="min-h-screen bg-green-50 flex items-center justify-center">
        <div className="text-center text-2xl">로딩 중...</div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-green-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-gray-600">프로젝트를 찾을 수 없습니다.</div>
          <Button onClick={() => router.push("/chat/room")} className="mt-4">
            채팅으로 돌아가기
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-green-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* 헤더 */}
        <div className="flex items-center gap-4 mb-6">
          <Button variant="ghost" onClick={() => router.push("/chat/room")} className="hover:bg-green-100">
            <ArrowLeft className="w-4 h-4 mr-2" />
            채팅으로 돌아가기
          </Button>
        </div>

        {/* 프로젝트 정보 */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="text-2xl text-gray-800">{project.title}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">{project.description || "설명이 없습니다."}</p>
            <div className="flex items-center gap-6 text-sm text-gray-500">
              <span className="bg-gray-100 px-3 py-1 rounded-full">{project.category}</span>
              <div className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                생성일: {new Date(project.createdAt).toLocaleDateString()}
              </div>
              <div className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                수정일: {new Date(project.updatedAt).toLocaleDateString()}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 문서 관리 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  프로젝트 문서 ({documents.length})
                </CardTitle>
                <Button
                  size="sm"
                  className="bg-green-600 hover:bg-green-700"
                  onClick={() => document.getElementById("fileUpload")?.click()}
                  disabled={uploading}
                >
                  <Upload className="w-4 h-4 mr-2" />
                  {uploading ? "업로드 중..." : "업로드"}
                </Button>
                <input
                  key={uploading ? "uploading" : "ready"}
                  id="fileUpload"
                  type="file"
                  accept=".pdf,.doc,.docx,.txt,.jpg,.png,.jpeg"
                  className="hidden"
                  onChange={handleFileUpload}
                  disabled={uploading}
                />
              </div>
            </CardHeader>
            <CardContent>
              {/* 문서 목록 */}
              {documents.length > 0 ? (
                <div className="space-y-3">
                  {documents.map((doc) => (
                    <div
                      key={doc.document_id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center gap-3">
                        <FileText className="w-4 h-4 text-gray-500" />
                        <div>
                          <div className="font-medium text-sm">{doc.file_name}</div>
                          <div className="text-xs text-gray-500">
                            {new Date(doc.uploaded_at).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-red-500 hover:bg-red-100"
                        onClick={() => handleDeleteDocument(doc.document_id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>업로드된 문서가 없습니다.</p>
                  <p className="text-sm mt-1">문서를 업로드하여 AI와 함께 분석해보세요.</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 채팅 관리 */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="w-5 h-5" />
                  프로젝트 채팅 ({chats.length})
                </CardTitle>
                <Button
                  size="sm"
                  className="bg-blue-600 hover:bg-blue-700"
                  onClick={handleNewChat}
                  disabled={creatingChat}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  {creatingChat ? "생성 중..." : "새 채팅"}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {chats.length > 0 ? (
                <div className="space-y-3">
                  {chats.map((chat) => (
                    <div
                      key={chat.conversation_id}
                      className="p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
                      onClick={() => handleOpenChat(chat.conversation_id)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-medium text-sm">{chat.title}</div>
                        <div className="text-xs text-gray-500">
                          {new Date(chat.lastMessageTime).toLocaleDateString()}
                        </div>
                      </div>
                      <div className="text-xs text-gray-600 truncate mb-2">
                        마지막 메시지: {chat.lastMessage}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded">
                          {chat.messageCount}개 메시지
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>진행 중인 채팅이 없습니다.</p>
                  <p className="text-sm mt-1">새 채팅을 시작하여 AI와 대화해보세요.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
