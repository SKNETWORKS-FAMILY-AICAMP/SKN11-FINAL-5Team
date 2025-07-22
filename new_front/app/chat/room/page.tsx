"use client"

import type React from "react"
import { useState, useEffect, useRef } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import ReactMarkdown from "react-markdown"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import Image from "next/image"
import { Send, ArrowLeft, Plus, MoreVertical, X, Edit2, Trash2 } from "lucide-react"
import { agentApi } from "@/app/api/agent"
import { AGENT_CONFIG, type AgentType, API_BASE_URL } from "@/config/constants"
import type { Message, ConversationMessage } from "@/types/messages"
import { FeedbackModal } from "@/components/ui/FeedbackModal"

// ===== 인터페이스 정의 =====
interface Project {
  id: number
  title: string
  description: string
  category: string
  createdAt: string
  updatedAt: string
}

interface ChatHistoryItem {
  id: number
  title: string
  lastMessage: string
  timestamp: string
  displayNumber: number
}

// ===== 예시 질문 데이터 =====
const exampleQuestions = [
  {
    category: "사업기획",
    question: "온라인 쇼핑몰을 운영하려는데 초기 사업계획을 어떻게 세우면 좋을까요?",
    agent: "planner",
  },
  {
    category: "마케팅",
    question: "인스타그램에서 제품을 효과적으로 홍보하려면 어떤 팁이 있을까요?",
    agent: "marketing",
  },
  {
    category: "고객관리",
    question: "리뷰에 불만 글이 달렸을 때 어떻게 대응해야 좋을까요?",
    agent: "crm",
  },
  {
    category: "업무지원",
    question: "매번 반복되는 예약 문자 전송을 자동화할 수 있을까요?",
    agent: "task",
  },
]

// ===== 프로젝트 생성/수정 모달 컴포넌트 =====
function ProjectModal({ 
  isOpen, 
  onClose, 
  onSubmit, 
  editingProject 
}: {
  isOpen: boolean
  onClose: () => void
  onSubmit: (project: { title: string; description: string; category: string }) => void
  editingProject?: Project | null
}) {
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [category, setCategory] = useState("general")

  useEffect(() => {
    if (editingProject) {
      setTitle(editingProject.title)
      setDescription(editingProject.description)
      setCategory(editingProject.category)
    } else {
      setTitle("")
      setDescription("")
      setCategory("general")
    }
  }, [editingProject, isOpen])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return

    onSubmit({
      title: title.trim(),
      description: description.trim(),
      category,
    })
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">
            {editingProject ? "프로젝트 수정" : "새 프로젝트 만들기"}
          </h3>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              프로젝트 제목 *
            </label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="예: 온라인 쇼핑몰 창업 프로젝트"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">설명</label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="프로젝트에 대한 간단한 설명을 입력하세요..."
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">카테고리</label>
            <select
              className="w-full border border-gray-300 rounded-md p-2 text-sm"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="general">일반</option>
              <option value="planning">사업기획</option>
              <option value="marketing">마케팅</option>
              <option value="customer">고객관리</option>
              <option value="task">업무지원</option>
              <option value="mental">멘탈코칭</option>
            </select>
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button type="button" variant="ghost" onClick={onClose}>
              취소
            </Button>
            <Button type="submit" className="bg-green-600 hover:bg-green-700">
              {editingProject ? "수정하기" : "만들기"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ===== 프로젝트 메뉴 컴포넌트 =====
function ProjectMenu({ 
  project, 
  onEdit, 
  onDelete 
}: { 
  project: Project, 
  onEdit: (project: Project) => void, 
  onDelete: (projectId: number) => void 
}) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="icon"
        className="w-4 h-4 p-0 text-gray-400 hover:text-gray-800 ml-1 opacity-0 group-hover:opacity-100"
        onClick={() => setIsOpen(!isOpen)}
      >
        <MoreVertical className="w-3 h-3" />
      </Button>
      
      
      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-20 min-w-[120px]">
            <button
              className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 rounded-t-md"
              onClick={() => {
                onEdit(project)
                setIsOpen(false)
              }}
            >
              이름 변경
            </button>
            <button
              className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 text-red-600 rounded-b-md"
              onClick={() => {
                onDelete(project.id)
                setIsOpen(false)
              }}
            >
              삭제
            </button>
          </div>
        </>
      )}
    </div>
  )
}

// ===== 채팅 히스토리 메뉴 컴포넌트 =====
function ChatHistoryMenu({ 
  chat, 
  onEditTitle, 
  onDelete 
}: { 
  chat: ChatHistoryItem, 
  onEditTitle: (chatId: number, newTitle: string) => void, 
  onDelete: (chatId: number) => void 
}) {
  const [isOpen, setIsOpen] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(chat.title)

  const handleSaveTitle = () => {
    if (editTitle.trim()) {
      onEditTitle(chat.id, editTitle.trim())
      setIsEditing(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSaveTitle()
    } else if (e.key === "Escape") {
      setEditTitle(chat.title)
      setIsEditing(false)
    }
  }

  return (
    <div className="relative">
      {/* 수정 모드: 인풋 + 저장 */}
      {isEditing ? (
        <div className="flex items-center gap-1">
          <input
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            onKeyDown={handleKeyDown}
            autoFocus
            className="text-xs px-2 py-1 rounded-md border border-gray-300 focus:outline-none focus:ring-1 focus:ring-green-500 bg-white"
            style={{ maxWidth: "140px" }}
          />
          <Button
            size="sm"
            onClick={handleSaveTitle}
            className="text-xs px-2 py-1 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            저장
          </Button>
        </div>
      ) : (
        <>
          <Button
            variant="ghost"
            size="icon"
            className="w-4 h-4 p-0 text-gray-400 hover:text-gray-800 ml-1 opacity-0 group-hover:opacity-100"
            onClick={(e) => {
              e.stopPropagation()
              setIsOpen(!isOpen)
            }}
          >
            <MoreVertical className="w-3 h-3" />
          </Button>

          {isOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
              <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-20 min-w-[140px]">
                <button
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100"
                  onClick={() => {
                    setIsEditing(true)
                    setIsOpen(false)
                  }}
                >
                  제목 수정
                </button>
                <button
                  className="w-full text-left px-3 py-2 text-sm hover:bg-red-100 text-red-600"
                  onClick={() => {
                    if (confirm("이 대화를 삭제하시겠습니까?")) {
                      onDelete(chat.id)
                    }
                    setIsOpen(false)
                  }}
                >
                  삭제
                </button>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}




// ===== 사이드바 컴포넌트 =====
function ChatSidebar({
  onSelectAgent,
  chatHistory,
  currentChatId,
  onLoadPreviousChat,
  onNewChat,
  onEditChatTitle,
  onDeleteChat,
  projects,
  onCreateProject,
  onEditProject,
  onDeleteProject,
  onSelectProject,
  isExpanded,
  setIsExpanded,
}: {
  onSelectAgent: (type: string) => void
  chatHistory: ChatHistoryItem[]
  currentChatId: number | null
  onLoadPreviousChat: (chatId: number) => void
  onNewChat: () => void
  onEditChatTitle: (chatId: number, newTitle: string) => void
  onDeleteChat: (chatId: number) => void
  projects: Project[]
  onCreateProject: () => void
  onEditProject: (project: Project) => void
  onDeleteProject: (projectId: number) => void
  onSelectProject: (projectId: number) => void
  isExpanded: boolean
  setIsExpanded: (expanded: boolean) => void
}) {
  const router = useRouter()

  const menuItems = [
    {
      icon: "/icons/3D_새채팅.png",
      label: "새 채팅 시작하기",
      type: "unified_agent",
      action: () => onNewChat(),
    },
    {
      icon: "/icons/3D_홈.png",
      label: "상담 메인화면",
      type: "home",
      action: () => router.push("/chat"),
    },
    ...Object.entries(AGENT_CONFIG)
      .filter(([key]) => key !== "unified_agent")
      .map(([key, value]) => ({
        icon: value.icon,
        label: `${value.name} 에이전트`,
        type: key,
        action: () => onSelectAgent(key),
      })),
  ]

  return (
    <div
      className={`${
        isExpanded ? "w-52" : "w-14"
      } bg-green-200 flex flex-col py-3 px-1 transition-all duration-300 shrink-0 fixed left-0 top-0 h-screen z-30`}
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      <div className="flex flex-col space-y-2 mb-4">
        {menuItems.map((item, idx) => (
          <div
            key={idx}
            onClick={item.action}
            className={`flex items-center gap-1 text-xs transition-all duration-150 ${
              idx === 0 ? "text-green-700 font-semibold hover:bg-green-50" : "text-gray-800 hover:bg-green-100"
            } cursor-pointer ${isExpanded ? "px-1 py-1 rounded-md" : "justify-center"}`}
          >
            <div
              className="rounded-full bg-white flex items-center justify-center shadow shrink-0"
              style={{ width: "36px", height: "36px" }}
            >
              <Image
                src={item.icon || "/placeholder.svg"}
                alt={item.label}
                width={24}
                height={24}
                className="w-6 h-6"
              />
            </div>
            {isExpanded && <span className="whitespace-nowrap">{item.label}</span>}
          </div>
        ))}
      </div>

      {isExpanded && (
        <div className="px-1 flex-1 overflow-y-auto">
          {/* 프로젝트 섹션 */}
          <div className="text-[10px] text-gray-500 font-bold px-1 mb-1 mt-3">프로젝트</div>
          <div
            className={`text-xs px-1 py-[2px] rounded cursor-pointer hover:bg-green-100 text-gray-700 flex items-center gap-1`}
            onClick={onCreateProject}
          >
            <Plus className="h-3 w-3" />
            <span className="whitespace-nowrap">새 프로젝트 만들기</span>
          </div>
          <div className="space-y-[2px] mt-1">
            {projects.map((project) => (
              <div
                key={project.id}
                className="group relative text-xs px-1 py-[2px] rounded hover:bg-green-100 text-gray-700"
              >
                <div className="flex items-start justify-between">
                  <div
                    className="flex-1 cursor-pointer min-w-0 pr-1"
                    onClick={() => onSelectProject(project.id)}
                    title={`${project.title}\n${project.description || "설명 없음"}`}
                  >
                    <div className="truncate max-w-[140px]">{project.title}</div>
                    <div className="text-[10px] text-gray-500 truncate max-w-[140px]">
                      {project.description || "설명 없음"}
                    </div>
                  </div>
                  <ProjectMenu
                    project={project}
                    onEdit={onEditProject}
                    onDelete={onDeleteProject}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* 채팅 기록 섹션 */}
          <div className="text-[10px] text-gray-500 font-bold px-1 mb-1 mt-3">채팅 기록</div>
          <div
            className={`text-xs px-1 py-[2px] rounded cursor-pointer hover:bg-green-100 ${
              currentChatId === null ? "text-green-800 bg-green-50" : "text-gray-700"
            }`}
            onClick={onNewChat}
          >
            현재 채팅
          </div>
          <div className="space-y-[2px] mt-1">
            {chatHistory.map((chat) => (
              <div
                key={chat.id}
                className={`group text-xs px-1 py-[2px] rounded hover:bg-green-100 cursor-pointer ${
                  currentChatId === chat.id ? "bg-green-50 text-green-800" : "text-gray-700"
                } flex items-center justify-between`}
              >
                {/* 왼쪽: 제목 + 내용 (최대 너비 제한) */}
                <div
                  className="flex-1 min-w-0"
                  onClick={() => onLoadPreviousChat(chat.id)}
                  title={chat.lastMessage}
                >
                  <div className="truncate font-medium max-w-[160px]">{chat.title}</div>
                  <div className="text-[10px] text-gray-500 truncate max-w-[160px]">{chat.lastMessage}</div>
                </div>

                {/* 오른쪽: 수정/삭제 버튼 */}
                <div className="ml-2 shrink-0">
                  <ChatHistoryMenu
                    chat={chat}
                    onEditTitle={onEditChatTitle}
                    onDelete={onDeleteChat}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ===== 메인 채팅 컴포넌트 =====
export default function ChatRoomPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const agent = (searchParams?.get("agent") || "unified_agent") as AgentType
  const initialQuestion = searchParams?.get("question") || ""
  const initialConversationId = searchParams?.get("conversation_id")
    ? Number.parseInt(searchParams.get("conversation_id") as string)
    : null
  const initialProjectId = searchParams?.get("project_id")
    ? Number.parseInt(searchParams.get("project_id") as string)
    : null

  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  // ===== 상태 관리 =====
  const [userId, setUserId] = useState<number | null>(null)
  const [conversationId, setConversationId] = useState<number | null>(initialConversationId)
  const [messages, setMessages] = useState<Message[]>([])
  const [userInput, setUserInput] = useState("")
  const [agentType, setAgentType] = useState<AgentType>(agent)
  const [currentProjectId, setCurrentProjectId] = useState<number | null>(initialProjectId)
  const [projectInfo, setProjectInfo] = useState<any>(null)
  const [isInitialized, setIsInitialized] = useState(false)
  const [sidebarExpanded, setSidebarExpanded] = useState(false)

  // 프로젝트 관련 상태
  const [projects, setProjects] = useState<Project[]>([])
  const [showProjectModal, setShowProjectModal] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | null>(null)

  // 채팅 히스토리 상태
  const [chatHistory, setChatHistory] = useState<ChatHistoryItem[]>([])
  const [currentChatId, setCurrentChatId] = useState<number | null>(null)
  const [chatTitleMap, setChatTitleMap] = useState<{[key: number]: string}>({})

  // 피드백 모달 상태
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [rating, setRating] = useState(0)
  const [comment, setComment] = useState("")
  const [category, setCategory] = useState(agent?.replace("_agent", "") || "general")

  // ===== 로컬 스토리지 관리 =====
  const saveChatTitleMap = (titleMap: {[key: number]: string}) => {
    if (userId) {
      localStorage.setItem(`chatTitleMap_${userId}`, JSON.stringify(titleMap))
    }
  }

  const loadChatTitleMap = (): {[key: number]: string} => {
    if (userId) {
      const saved = localStorage.getItem(`chatTitleMap_${userId}`)
      return saved ? JSON.parse(saved) : {}
    }
    return {}
  }

  // ===== 유틸리티 함수 =====
  const removeDuplicateMessages = (messages: Message[]): Message[] => {
    const seen = new Set<string>()
    return messages.filter((msg) => {
      const key = `${msg.sender}-${msg.text}-${JSON.stringify(msg)}`
      if (seen.has(key)) {
        return false
      }
      seen.add(key)
      return true
    })
  }

  // ===== 초기화 및 데이터 가져오기 함수 =====
  const initializeUser = () => {
    const storedUser = localStorage.getItem("user")
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser)
        setUserId(user.user_id)
      } catch (e) {
        console.error("유저 파싱 오류:", e)
      }
    } else {
      alert("로그인 정보가 없습니다.")
      router.push("/login")
    }
  }

  const fetchProjects = async (currentUserId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/projects?user_id=${currentUserId}`)
      const result = await response.json()
      if (result.success) {
        setProjects(result.data)
      }
    } catch (error) {
      console.error("프로젝트 목록 불러오기 실패:", error)
    }
  }

  const fetchChatHistory = async (currentUserId: number) => {
    try {
      const res = await fetch(`${API_BASE_URL}/conversations/${currentUserId}`)
      const data = await res.json()
      if (data.success) {
        const titleMap = loadChatTitleMap()
        
        // 최신순으로 정렬하되, 표시 번호는 오래된 순서대로
        const sortedConversations = data.data.sort((a: any, b: any) => 
          new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
        )
        
        const formatted = sortedConversations.map((conv: any, index: number) => ({
          id: conv.conversation_id,
          title: titleMap[conv.conversation_id] || `대화 ${data.data.length - sortedConversations.findIndex((c: any) => c.conversation_id === conv.conversation_id)}`,
          lastMessage: "마지막 메시지를 불러오는 중...",
          timestamp: conv.started_at,
          displayNumber: data.data.length - sortedConversations.findIndex((c: any) => c.conversation_id === conv.conversation_id)
        }))
        
        setChatHistory(formatted)

        // 각 대화의 마지막 메시지 갱신
        for (let conv of formatted) {
          const msgRes = await fetch(`${API_BASE_URL}/conversations/${conv.id}/messages?limit=1`)
          const msgData = await msgRes.json()
          if (msgData.success && msgData.data.length > 0) {
            const lastMsg = msgData.data[0]
            setChatHistory((prev) =>
              prev.map((c) =>
                c.id === conv.id ? { ...c, lastMessage: lastMsg.content.slice(0, 30) + (lastMsg.content.length > 30 ? '...' : '') } : c
              )
            )
          }
        }
      }
    } catch (err) {
      console.error("채팅 기록 불러오기 실패:", err)
    }
  }

  const fetchProjectInfo = async (projectId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/projects?user_id=${userId}`)
      const result = await response.json()
      if (result.success) {
        const project = result.data.find((p: any) => p.id === projectId)
        setProjectInfo(project)
      }
    } catch (error) {
      console.error("프로젝트 정보 불러오기 실패:", error)
    }
  }

  // ===== 대화 관련 핸들러 =====
  const startNewConversation = async (newAgent: AgentType = "unified_agent") => {
    if (!userId) return
    try {
      const result = await agentApi.createConversation(userId)
      if (!result.success) throw new Error(result.error)

      const newConvId = result.data?.conversationId
      setConversationId(newConvId)
      setMessages([])
      setAgentType(newAgent)
      setCurrentChatId(null) // 새 대화는 현재 대화로 설정

      // URL 업데이트 (새로고침 방지)
      const newUrl = `/chat/room?conversation_id=${newConvId}&agent=${newAgent}`
      window.history.replaceState({}, '', newUrl)
      
      await fetchChatHistory(userId)
    } catch (err) {
      console.error("대화 세션 생성 실패:", err)
    }
  }

  const loadPreviousChat = async (chatId: number) => {
    try {
      const result = await agentApi.getConversationMessages(chatId)
      if (!result.success || !result.data?.messages) {
        throw new Error(result.error || "메시지를 불러올 수 없습니다")
      }
      
      setMessages(
        result.data.messages.map((msg: ConversationMessage) => ({
          sender: msg.role === "user" ? "user" : "agent",
          text: msg.content,
        }))
      )
      setConversationId(chatId)
      setCurrentChatId(chatId)
      
      // URL 업데이트 (새로고침 방지)
      const newUrl = `/chat/room?conversation_id=${chatId}&agent=${agentType}`
      window.history.replaceState({}, '', newUrl)
    } catch (error) {
      console.error("기존 대화 로드 실패:", error)
      alert("대화를 불러오는데 실패했습니다.")
    }
  }

  // ===== 채팅 관련 핸들러 =====
  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!userInput.trim() || !userId) return

    let currentConversationId = conversationId
    
    // 새 대화 세션이 필요한 경우
    if (!currentConversationId) {
      try {
        const result = await agentApi.createConversation(userId)
        if (!result.success) throw new Error(result.error)
        currentConversationId = result.data?.conversationId
        setConversationId(currentConversationId)
        
        // URL 업데이트
        const newUrl = `/chat/room?conversation_id=${currentConversationId}&agent=${agentType}`
        window.history.replaceState({}, '', newUrl)
      } catch (error) {
        console.error("대화 세션 생성 실패:", error)
        alert("채팅 세션을 생성할 수 없습니다.")
        return
      }
    }

    const currentInput = userInput
    setUserInput("")

    // 사용자 메시지 즉시 표시
    const userMessage: Message = { sender: "user", text: currentInput }
    setMessages((prev) => {
      const newMessages = [...prev, userMessage]
      return removeDuplicateMessages(newMessages)
    })

    try {
      const result = await agentApi.sendQuery(userId, currentConversationId!, currentInput, agentType, currentProjectId)
      if (!result || !result.success || !result.data) {
        throw new Error(result?.error || "응답을 받을 수 없습니다")
      }

      // 에이전트 응답 추가
      const agentMessage: Message = {
        sender: "agent",
        text: result.data.answer,
      }
      setMessages((prev) => {
        const newMessages = [...prev, agentMessage]
        return removeDuplicateMessages(newMessages)
      })

      // 대화 목록 갱신
      await fetchChatHistory(userId)
    } catch (error) {
      console.error("응답 실패:", error)
      alert("서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
      
      // 실패 시 사용자 메시지 제거
      setMessages((prev) => prev.slice(0, -1))
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setUserInput(e.target.value)
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      const scrollHeight = textareaRef.current.scrollHeight
      const maxHeight = 120
      textareaRef.current.style.height = Math.min(scrollHeight, maxHeight) + "px"
    }
  }

  const handleExampleClick = async (text: string) => {
    if (!userId) {
      alert("로그인 정보가 없습니다. 다시 로그인해주세요.")
      return
    }

    setUserInput(text)
    
    // 폼 제출 이벤트 트리거
    setTimeout(() => {
      const form = document.querySelector("form")
      if (form) {
        const event = new Event("submit", { bubbles: true, cancelable: true })
        form.dispatchEvent(event)
      }
    }, 100)
  }

  // ===== 채팅 히스토리 관련 핸들러 =====
  const handleEditChatTitle = (chatId: number, newTitle: string) => {
    const newTitleMap = { ...chatTitleMap, [chatId]: newTitle }
    setChatTitleMap(newTitleMap)
    saveChatTitleMap(newTitleMap)
    
    setChatHistory(prev => 
      prev.map(chat => 
        chat.id === chatId ? { ...chat, title: newTitle } : chat
      )
    )
  }

  const handleDeleteChat = async (chatId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations/${chatId}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        setChatHistory(prev => prev.filter(chat => chat.id !== chatId))
        
        // 삭제된 대화가 현재 대화인 경우 새 대화로 이동
        if (currentChatId === chatId || conversationId === chatId) {
          setCurrentChatId(null)
          setConversationId(null)
          setMessages([])
          router.push('/chat/room')
        }
        
        // 로컬 스토리지에서도 제거
        const newTitleMap = { ...chatTitleMap }
        delete newTitleMap[chatId]
        setChatTitleMap(newTitleMap)
        saveChatTitleMap(newTitleMap)
      }
    } catch (error) {
      console.error('대화 삭제 실패:', error)
      alert('대화 삭제에 실패했습니다.')
    }
  }

  // ===== 프로젝트 관련 핸들러 =====
  const handleCreateProject = async (projectData: { title: string; description: string; category: string }) => {
    if (!userId) return

    try {
      const response = await fetch(`${API_BASE_URL}/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...projectData, user_id: userId }),
      })
      
      const result = await response.json()
      if (result.success) {
        alert("프로젝트가 성공적으로 생성되었습니다.")
        fetchProjects(userId)
        setShowProjectModal(false)
      } else {
        alert(`프로젝트 생성 실패: ${result.error}`)
      }
    } catch (error) {
      console.error("프로젝트 생성 오류:", error)
      alert("프로젝트 생성 중 오류가 발생했습니다.")
    }
  }

  const handleUpdateProject = async (projectData: { title: string; description: string; category: string }) => {
    if (!editingProject || !userId) return

    try {
      const response = await fetch(`${API_BASE_URL}/projects/${editingProject.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...projectData, user_id: userId }),
      })

      const result = await response.json()
      if (result.success) {
        alert("프로젝트가 성공적으로 수정되었습니다.")
        fetchProjects(userId)
        setShowProjectModal(false)
        setEditingProject(null)
      } else {
        alert(`수정 실패: ${result.error}`)
      }
    } catch (error) {
      console.error("프로젝트 수정 오류:", error)
      alert("프로젝트 수정 중 오류가 발생했습니다.")
    }
  }

  const handleDeleteProject = async (projectId: number) => {
    const confirmDelete = window.confirm("이 프로젝트를 삭제하시겠습니까?")
    if (!confirmDelete) return

    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
        method: "DELETE",
      })
      const result = await response.json()

      if (result.success) {
        alert("프로젝트가 성공적으로 삭제되었습니다.")
        setProjects((prev) => prev.filter((p) => p.id !== projectId))
        
        if (currentProjectId === projectId) {
          setCurrentProjectId(null)
        }
      } else {
        alert("삭제 실패: " + result.error)
      }
    } catch (error) {
      console.error("프로젝트 삭제 오류:", error)
      alert("프로젝트 삭제 중 오류가 발생했습니다.")
    }
  }

  const handleAddProject = () => {
    setEditingProject(null)
    setShowProjectModal(true)
  }

  const handleEditProject = (project: Project) => {
    setEditingProject(project)
    setShowProjectModal(true)
  }

  const handleSelectProject = async (projectId: number) => {
    router.push(`/chat/projects/${projectId}`)
  }

  // ===== 사이드바 관련 핸들러 =====
  const handleSidebarSelect = async (type: string) => {
    try {
      if (type === "home") {
        router.push("/chat")
        return
      }

      await startNewConversation(type as AgentType)
    } catch (error) {
      console.error("에이전트 변경 실패:", error)
      alert("에이전트 변경에 실패했습니다. 다시 시도해주세요.")
    }
  }

  const handleNewChat = () => {
    setCurrentChatId(null)
    setConversationId(null)
    setMessages([])
    // URL 업데이트
    window.history.replaceState({}, '', `/chat/room?agent=${agentType}`)
  }

  // ===== 피드백 관련 핸들러 =====
  const handleFeedbackSubmit = async () => {
    if (!conversationId || !userId) {
      alert("로그인 정보가 없습니다.")
      return
    }
    try {
      const result = await agentApi.sendFeedback(userId, conversationId, rating, comment, category)
      if (result.success) {
        alert("피드백이 등록되었습니다!")
      } else {
        alert("피드백 전송에 실패했습니다.")
      }
    } catch (error) {
      console.error("피드백 전송 오류:", error)
      alert("서버 오류로 피드백을 전송하지 못했어요.")
    }

    setShowFeedbackModal(false)
    setRating(0)
    setComment("")
  }

  // ===== useEffect 훅 =====
  // 스크롤 자동 이동
  useEffect(() => {
    if (messagesEndRef.current) {
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ 
          behavior: "smooth",
          block: "end"
        })
      }, 100)
    }
  }, [messages])

  // 사용자 초기화
  useEffect(() => {
    initializeUser()
  }, [])

  // 사용자 ID가 설정된 후 초기화
  useEffect(() => {
    if (userId && !isInitialized) {
      const initialize = async () => {
        try {
          // 로컬 스토리지에서 채팅 제목 맵 로드
          const titleMap = loadChatTitleMap()
          setChatTitleMap(titleMap)
          
          // 프로젝트 및 채팅 히스토리 로드
          await Promise.all([
            fetchProjects(userId),
            fetchChatHistory(userId)
          ])

          // URL에서 대화 ID가 있으면 해당 대화 로드
          if (initialConversationId) {
            await loadPreviousChat(initialConversationId)
          }

          // 프로젝트 정보 로드
          if (currentProjectId) {
            await fetchProjectInfo(currentProjectId)
          }

          // 초기 질문이 있으면 처리
          if (initialQuestion && !initialConversationId) {
            setUserInput(initialQuestion)
            setTimeout(() => {
              const form = document.querySelector("form")
              if (form) {
                const event = new Event("submit", { bubbles: true, cancelable: true })
                form.dispatchEvent(event)
              }
            }, 500)
          }

          setIsInitialized(true)
        } catch (error) {
          console.error("초기화 실패:", error)
        }
      }
      
      initialize()
    }
  }, [userId, isInitialized])

  // ===== JSX 렌더링 =====
  return (
    <div className="flex h-screen overflow-hidden bg-green-50">
      <ChatSidebar
        onSelectAgent={handleSidebarSelect}
        chatHistory={chatHistory}
        currentChatId={currentChatId}
        onLoadPreviousChat={loadPreviousChat}
        onNewChat={handleNewChat}
        onEditChatTitle={handleEditChatTitle}
        onDeleteChat={handleDeleteChat}
        projects={projects}
        onCreateProject={handleAddProject}
        onEditProject={handleEditProject}
        onDeleteProject={handleDeleteProject}
        onSelectProject={handleSelectProject}
        isExpanded={sidebarExpanded}
        setIsExpanded={setSidebarExpanded}
      />

      {/* 메인 컨테이너 - 사이드바 크기에 따라 여백 조정 */}
      <div className={`flex-1 flex flex-col relative transition-all duration-300 ${sidebarExpanded ? 'ml-52' : 'ml-14'}`}>
        {/* 헤더 */}
        <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            {currentProjectId && (
              <Button
                variant="ghost"
                onClick={() => router.push(`/chat/projects/${currentProjectId}`)}
                className="hover:bg-green-100"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                프로젝트로 돌아가기
              </Button>
            )}
            <div>
              <h1 className="text-lg font-semibold text-gray-800">
                {currentProjectId && projectInfo ? projectInfo.title : `${AGENT_CONFIG[agentType]?.name || "통합"} AI 상담`}
              </h1>
              <p className="text-sm text-gray-500">
                {currentProjectId && projectInfo 
                  ? `${projectInfo.description || "프로젝트 상담 중"}` 
                  : `${AGENT_CONFIG[agentType]?.description || "AI와 대화하세요"}`}
              </p>
            </div>
          </div>
        </div>

        {/* 메인 채팅 영역 */}
        <div className="flex-1 flex flex-col min-h-0">
          {/* 채팅 컨테이너 */}
          <div 
            ref={messagesContainerRef}
            className="flex-1 overflow-y-auto px-8 py-6"
          >
            {/* 예시 카드 (새 채팅일 때만) */}
            {messages.length === 0 && !currentProjectId && (
              <>
                <h2 className="font-semibold mb-3 text-gray-800">팅커벨 활용하기 &gt;</h2>
                <div className="flex space-x-3 mb-6 overflow-x-auto">
                  {exampleQuestions.map((item, idx) => (
                    <Card
                      key={idx}
                      className="min-w-[280px] cursor-pointer hover:shadow-md transition-shadow bg-white"
                      onClick={() => handleExampleClick(item.question)}
                    >
                      <CardContent className="p-4">
                        <div className="font-bold mb-2 text-green-600">{item.category}</div>
                        <div className="text-sm text-gray-700">{item.question}</div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </>
            )}

            {/* 채팅 메시지 출력 */}
            <div className="space-y-4">
              {messages.map((msg, idx) => (
                <div key={`${idx}-${msg.sender}-${msg.text.slice(0, 20)}`} className={`flex items-start ${idx === 0 && msg.sender === "user" ? "mt-6" : ""}`}>
                  {/* 사용자 메시지 */}
                  {msg.sender === "user" ? (
                    <div className="flex flex-row-reverse items-end ml-auto space-x-reverse space-x-2 max-w-[80%]">
                      <div className="w-10 h-10 rounded-full bg-green-600 flex items-center justify-center shadow shrink-0">
                        <Image src="/3D_고양이.png" width={36} height={36} alt="사용자" className="rounded-full" />
                      </div>
                      <div className="inline-block overflow-wrap-break-word p-0.5">
                        <div className="bg-green-100 text-green-900 px-4 py-3 rounded-2xl shadow-md whitespace-pre-wrap leading-relaxed">
                          {msg.text}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-end space-x-2 max-w-[80%]">
                      <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center shadow shrink-0">
                        <Image
                          src={AGENT_CONFIG[agentType]?.icon || "/placeholder.svg"}
                          width={36}
                          height={36}
                          alt={AGENT_CONFIG[agentType]?.name || "Agent"}
                          className="rounded-full"
                        />
                      </div>
                      <div className="inline-block overflow-wrap-break-word p-0.5">
                        <div className="bg-white text-gray-800 px-4 py-3 rounded-2xl shadow-md whitespace-pre-wrap leading-relaxed">
                          <ReactMarkdown>{msg.text}</ReactMarkdown>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
              {/* 스크롤 앵커 */}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* 하단 입력창 */}
          <div className="border-t bg-white p-4">
            <form onSubmit={handleSend} className="flex space-x-2">
              <Textarea
                ref={textareaRef}
                value={userInput}
                onChange={handleInputChange}
                placeholder="메시지를 입력하세요..."
                className="flex-1 resize-none overflow-hidden rounded-xl border-2 border-gray-200 focus:border-green-400 shadow-lg"
                rows={1}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault()
                    handleSend(e)
                  }
                }}
              />
              <Button
                type="submit"
                size="icon"
                className="h-full aspect-square rounded-xl bg-green-600 hover:bg-green-700 shadow-lg"
                disabled={!userInput.trim()}
              >
                <Send className="h-5 w-5" />
              </Button>
            </form>
          </div>
        </div>
      </div>

      {/* 프로젝트 모달 */}
      <ProjectModal
        isOpen={showProjectModal}
        onClose={() => {
          setShowProjectModal(false)
          setEditingProject(null)
        }}
        onSubmit={editingProject ? handleUpdateProject : handleCreateProject}
        editingProject={editingProject}
      />

      {/* 피드백 모달 */}
      {showFeedbackModal && (
        <FeedbackModal
          rating={rating}
          setRating={setRating}
          comment={comment}
          setComment={setComment}
          category={category}
          setCategory={setCategory}
          onClose={() => setShowFeedbackModal(false)}
          onSubmit={handleFeedbackSubmit}
        />
      )}
    </div>
  )
}