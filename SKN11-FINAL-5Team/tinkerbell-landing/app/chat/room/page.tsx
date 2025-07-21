"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import ReactMarkdown from "react-markdown"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import Image from "next/image"
import {
  Send,
  ThumbsUp,
  ThumbsDown,
  MessageCircle,
  Plus,
  Home,
  Target,
  TrendingUp,
  Users,
  Zap,
  Heart,
} from "lucide-react"

// 에이전트 포트 매핑
const getAgentPort = (agent: string) => {
  const portMap: { [key: string]: number } = {
    unified_agent: 8080,
    planner: 8001,
    marketing: 8002,
    crm: 8003,
    task: 8004,
    mentalcare: 8005,
  }
  return portMap[agent] || 8080
}

// 에이전트 아이콘 매핑
const agentIcons = {
  planner: Target,
  marketing: TrendingUp,
  crm: Users,
  task: Zap,
  mentalcare: Heart,
}

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

interface Message {
  sender: "user" | "agent"
  text: string
}

interface FeedbackModalProps {
  rating: number
  setRating: (rating: number) => void
  comment: string
  setComment: (comment: string) => void
  category: string
  setCategory: (category: string) => void
  onClose: () => void
  onSubmit: () => void
}

function FeedbackModal({
  rating,
  setRating,
  comment,
  setComment,
  category,
  setCategory,
  onClose,
  onSubmit,
}: FeedbackModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-lg">
        <h3 className="text-lg font-semibold mb-4">상세 피드백</h3>

        <div className="flex space-x-1 mb-4">
          {[1, 2, 3, 4, 5].map((num) => (
            <span
              key={num}
              onClick={() => setRating(num)}
              className={`cursor-pointer text-2xl ${rating >= num ? "text-yellow-400" : "text-gray-300"}`}
            >
              ★
            </span>
          ))}
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">관련 카테고리</label>
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

        <Textarea
          className="w-full border border-gray-300 rounded-md p-2 text-sm resize-none mb-4"
          rows={4}
          placeholder="자세한 피드백을 남겨주세요..."
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />

        <div className="flex justify-end space-x-2">
          <Button variant="ghost" onClick={onClose}>
            취소
          </Button>
          <Button onClick={onSubmit} className="bg-gray-800 hover:bg-gray-700">
            피드백 전송
          </Button>
        </div>
      </div>
    </div>
  )
}

function Sidebar({
  onSelectAgent,
  chatHistory,
  currentChatId,
  onLoadPreviousChat,
  onNewChat,
}: {
  onSelectAgent: (type: string) => void
  chatHistory: any[]
  currentChatId: number | null
  onLoadPreviousChat: (chatId: number) => void
  onNewChat: () => void
}) {
  const [expanded, setExpanded] = useState(false)

  const menuItems = [
    { icon: Plus, label: "새 채팅 시작하기", type: "unified_agent", color: "text-blue-600" },
    { icon: Home, label: "상담 메인화면", type: "home", color: "text-green-600" },
    { icon: Target, label: "사업기획 에이전트", type: "planner", color: "text-blue-600" },
    { icon: TrendingUp, label: "마케팅 에이전트", type: "marketing", color: "text-orange-600" },
    { icon: Zap, label: "업무 지원 에이전트", type: "task", color: "text-yellow-600" },
    { icon: Users, label: "고객 관리 에이전트", type: "crm", color: "text-green-600" },
    { icon: Heart, label: "멘탈 케어 에이전트", type: "mentalcare", color: "text-purple-600" },
  ]

  return (
    <div
      className={`${
        expanded ? "w-52" : "w-14"
      } bg-blue-200 flex flex-col py-3 px-1 transition-all duration-300 shrink-0`}
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
    >
      <div className="flex flex-col space-y-2 mb-4">
  {menuItems.map((item, idx) => (
    <div
      key={idx}
      onClick={() => onSelectAgent(item.type)}
      className={`flex items-center gap-1 text-xs transition-all duration-150 ${
        idx === 0
          ? "text-blue-700 font-semibold hover:bg-blue-50"
          : "text-gray-800 hover:bg-blue-100"
        } cursor-pointer ${expanded ? "px-1 py-1 rounded-md" : "justify-center"}`}
        >
        <div className="w-7 h-7 rounded-full bg-white flex items-center justify-center shadow shrink-0">
            <item.icon className={`w-3.5 h-3.5 ${item.color}`} />
        </div>
        {expanded && <span className="whitespace-nowrap">{item.label}</span>}
        </div>
    ))}
    </div>

      {expanded && (
        <div className="px-1">
          <div className="text-[10px] text-gray-500 font-bold px-1 mb-1 mt-3">채팅</div>
          <div
            className={`text-xs px-1 py-[2px] rounded cursor-pointer hover:bg-blue-100 ${
              currentChatId === null ? "text-blue-800 bg-blue-50" : "text-gray-700"
            }`}
            onClick={onNewChat}
          >
            현재 채팅
          </div>
          <div className="space-y-[2px] mt-1">
            {chatHistory.map((chat) => (
              <div
                key={chat.id}
                className={`text-xs px-1 py-[2px] rounded hover:bg-blue-100 cursor-pointer ${
                  currentChatId === chat.id ? "bg-blue-50 text-blue-800" : "text-gray-700"
                }`}
                onClick={() => onLoadPreviousChat(chat.id)}
                title={chat.lastMessage}
              >
                <div className="truncate">{chat.title}</div>
                <div className="text-[10px] text-gray-500 truncate">{chat.lastMessage}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}



export default function ChatRoomPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const agent = searchParams?.get("agent") || "unified_agent"
  const initialQuestion = searchParams?.get("question") || ""

  const [conversationId, setConversationId] = useState(3)
  const [messages, setMessages] = useState<Message[]>([])
  const [userInput, setUserInput] = useState("")
  const [agentConfig, setAgentConfig] = useState({
    type: agent,
    port: getAgentPort(agent),
  })

  // 피드백 모달 상태
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [rating, setRating] = useState(0)
  const [comment, setComment] = useState("")
  const [category, setCategory] = useState(agent?.replace("_agent", "") || "general")

  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  // 기존 상태들 아래에 추가
  const [chatHistory, setChatHistory] = useState([
    {
      id: 1,
      title: "온라인 쇼핑몰 창업 상담",
      lastMessage: "감사합니다! 많은 도움이 되었어요.",
      timestamp: "2024-01-15",
    },
    {
      id: 2,
      title: "인스타그램 마케팅 전략",
      lastMessage: "해시태그 전략에 대해 더 알고 싶어요.",
      timestamp: "2024-01-14",
    },
    { id: 3, title: "고객 응대 자동화", lastMessage: "챗봇 설정 방법을 알려주세요.", timestamp: "2024-01-13" },
    { id: 4, title: "멘탈케어 상담", lastMessage: "스트레스 관리법이 도움됐어요.", timestamp: "2024-01-12" },
    { id: 5, title: "사업 계획서 작성", lastMessage: "계획서 템플릿 감사합니다.", timestamp: "2024-01-11" },
  ])
  const [currentChatId, setCurrentChatId] = useState<number | null>(null)

  // 스크롤 자동 이동
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages])

  // 초기 설정
  useEffect(() => {
    startNewConversation(agent)
    if (initialQuestion) {
      setUserInput(initialQuestion)
      setTimeout(() => {
        const form = document.querySelector("form")
        if (form) {
          form.dispatchEvent(new Event("submit", { bubbles: true }))
        }
      }, 100)
    }
  }, [])

  const loadPreviousChat = async (chatId: number) => {
    try {
      // 실제로는 API에서 해당 채팅 기록을 가져와야 함
      const response = await fetch(`/api/conversations/${chatId}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (response.ok) {
        const result = await response.json()
        if (result.status === "success" && result.data.messages) {
          setMessages(result.data.messages)
          setConversationId(chatId)
          setCurrentChatId(chatId)
          return
        }
      }
    } catch (error) {
      console.warn("이전 채팅 로드 실패, 샘플 데이터 사용:", error)
    }

    // API 실패 시 샘플 데이터 사용
    const sampleMessages: Message[] = [
      { sender: "user", text: "온라인 쇼핑몰을 시작하려고 하는데 어떻게 해야 할까요?" },
      {
        sender: "agent",
        text: "온라인 쇼핑몰 창업을 위해서는 다음과 같은 단계를 거치시면 됩니다:\n\n1. **시장 조사**: 판매하고자 하는 상품의 시장성 분석\n2. **사업자 등록**: 개인사업자 또는 법인 설립\n3. **플랫폼 선택**: 자체 쇼핑몰 vs 오픈마켓 입점\n4. **상품 소싱**: 공급업체 발굴 및 계약\n5. **결제 시스템**: PG사 연동 및 배송 시스템 구축\n\n어떤 부분부터 시작하고 싶으신가요?",
      },
      { sender: "user", text: "시장 조사는 어떻게 하면 좋을까요?" },
      {
        sender: "agent",
        text: "시장 조사를 위한 구체적인 방법들을 알려드릴게요:\n\n**온라인 조사 방법:**\n- 네이버 트렌드, 구글 트렌드로 검색량 확인\n- 쿠팡, 11번가 등에서 유사 상품 판매량 분석\n- 소셜미디어에서 관련 해시태그 인기도 확인\n\n**오프라인 조사 방법:**\n- 타겟 고객층 설문조사\n- 경쟁업체 매장 방문 및 가격 비교\n- 관련 전시회나 박람회 참관\n\n어떤 상품군을 고려하고 계신지 알려주시면 더 구체적인 조사 방법을 제안해드릴 수 있어요!",
      },
    ]

    setMessages(sampleMessages)
    setConversationId(chatId)
    setCurrentChatId(chatId)
  }

  const startNewConversation = async (newAgent = "unified_agent") => {
    try {
      const response = await fetch("/api/conversations", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: 3,
          conversation_type: newAgent.replace("_agent", "") || "general",
        }),
      })

      if (!response.ok) throw new Error("서버 응답 실패")

      const result = await response.json()
      if (result.status === "success") {
        const newId = result.data.conversation_id
        setConversationId(newId)
        setMessages([])
        setUserInput("")
        setAgentConfig({
          type: newAgent,
          port: getAgentPort(newAgent),
        })
        return
      }

      console.warn("대화 세션 생성 실패:", result)
    } catch (error) {
      console.warn("대화 세션 서버 요청 실패, 로컬 ID로 대체:", error)
    }

    const fallbackId = Date.now()
    setConversationId(fallbackId)
    setMessages([])
    setUserInput("")
    setAgentConfig({
      type: newAgent,
      port: getAgentPort(newAgent),
    })
  }

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!userInput.trim()) return

    const currentInput = userInput
    setUserInput("")

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
    }

    const userMessage: Message = { sender: "user", text: currentInput }
    const newMessages = [...messages, userMessage]
    setMessages(newMessages)

    const payload = {
      user_id: 3,
      message: currentInput,
      conversation_id: conversationId,
      persona: "common",
    }

    const endpoint =
      agentConfig.type === "unified_agent"
        ? `http://localhost:${agentConfig.port}/query`
        : `http://localhost:${agentConfig.port}/agent/query`

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      })

      const res = await response.json()

      if (res.success && res.data) {
        const agentMessage: Message = {
          sender: "agent",
          text: res.data.answer,
        }
        setMessages((prev) => [...prev, agentMessage])
      } else {
        const agentMessage: Message = {
          sender: "agent",
          text: "죄송합니다. 답변을 가져오지 못했어요.",
        }
        setMessages((prev) => [...prev, agentMessage])
      }
    } catch (error) {
      console.error("응답 실패:", error)
      const agentMessage: Message = {
        sender: "agent",
        text: "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
      }
      setMessages((prev) => [...prev, agentMessage])
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setUserInput(e.target.value)
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      const scrollHeight = textareaRef.current.scrollHeight
      const maxHeight = 120 // 5줄 높이 (24px * 5)
      textareaRef.current.style.height = Math.min(scrollHeight, maxHeight) + "px"
    }
  }

  const handleExampleClick = (text: string) => {
    setUserInput(text)
    setTimeout(() => {
      const form = document.querySelector("form")
      if (form) {
        form.dispatchEvent(new Event("submit", { bubbles: true }))
      }
    }, 0)
  }

  const handleSidebarSelect = (type: string) => {
    if (type === "home") {
      router.push("/chat")
    } else {
      router.push(`/chat/room?agent=${type}`)
      startNewConversation(type)
    }
  }

  const handleFeedbackSubmit = async () => {
    try {
      const response = await fetch("/api/feedback", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: 2,
          conversation_id: conversationId,
          rating,
          comment,
          category,
        }),
      })

      const result = await response.json()
      console.log("피드백 응답:", result)

      if (result.status === "success") {
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

  return (
    <div className="flex h-screen overflow-hidden bg-gradient-to-br from-blue-50 via-slate-50 to-gray-100">
      <Sidebar
        onSelectAgent={handleSidebarSelect}
        chatHistory={chatHistory}
        currentChatId={currentChatId}
        onLoadPreviousChat={loadPreviousChat}
        onNewChat={() => {
          setCurrentChatId(null)
          startNewConversation(agentConfig.type)
        }}
      />

      <div className="flex-1 flex flex-col px-8 py-6 relative">
        {/* 예시 카드 및 타이틀: 메시지 없을 때만 */}
        {messages.length === 0 && (
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
                    <div className="font-bold mb-2 text-blue-600">{item.category}</div>
                    <div className="text-sm text-gray-700">{item.question}</div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </>
        )}

        {/* 채팅 메시지 영역 */}
        <div className="flex-1 space-y-4 overflow-y-auto pb-24">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex items-start ${idx === 0 && msg.sender === "user" ? "mt-6" : ""}`}>
              {msg.sender === "user" ? (
                <div className="flex flex-row-reverse items-end ml-auto space-x-reverse space-x-2">
                  {/* 고양이 아이콘 */}
                  <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center shadow shrink-0">
                    <Image src="/cat.png" width={24} height={24} alt="사용자" className="rounded-full" />
                  </div>

                  {/* 유저 말풍선 */}
                  <div className="inline-block max-w-[90%] overflow-wrap-break-word word-break-break-word p-0.5">
                    <div className="bg-blue-100 text-blue-900 px-4 py-3 rounded-2xl shadow-md word-break-break-word whitespace-pre-wrap leading-relaxed">
                      {msg.text}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex justify-start w-full">
                  <div className="flex flex-col space-y-2 max-w-[70%] mr-auto">
                    <div className="bg-white text-gray-800 px-4 py-3 rounded-2xl shadow-md border border-gray-200 whitespace-pre-line">
                      <ReactMarkdown>{msg.text}</ReactMarkdown>
                    </div>
                    <div className="mt-3 text-sm text-gray-500 flex items-center space-x-4">
                      <span>이 답변이 도움이 되었나요?</span>
                      <Button variant="ghost" size="sm" className="flex items-center space-x-1 h-auto p-1">
                        <ThumbsUp className="w-4 h-4" />
                        <span>좋아요</span>
                      </Button>
                      <Button variant="ghost" size="sm" className="flex items-center space-x-1 h-auto p-1">
                        <ThumbsDown className="w-4 h-4" />
                        <span>별로예요</span>
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="flex items-center space-x-1 h-auto p-1"
                        onClick={() => setShowFeedbackModal(true)}
                      >
                        <MessageCircle className="w-4 h-4" />
                        <span>상세 피드백</span>
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
          <div ref={scrollRef} />
        </div>

        {/* 입력창 */}
        <form
          className="absolute bottom-4 left-8 right-8 bg-white shadow-lg rounded-2xl px-4 py-3 flex flex-col space-y-2 border border-gray-200"
          onSubmit={handleSend}
        >
          <Textarea
            ref={textareaRef}
            placeholder="추가 질문하기 ..."
            value={userInput}
            onChange={handleInputChange}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                handleSend(e)
              }
            }}
            rows={1}
            className="w-full min-h-[40px] max-h-[120px] bg-white text-sm px-3 py-2 rounded-lg border-none outline-none resize-none overflow-y-auto focus:ring-0 focus:border-none transition-colors"
            style={{ lineHeight: "1.5" }}
          />

          <div className="flex justify-between items-center">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="text-gray-500 hover:text-red-600 text-xs"
              onClick={() => setShowFeedbackModal(true)}
            >
              대화 끝내기
            </Button>
            <Button type="submit" size="sm" className="w-8 h-8 bg-blue-600 hover:bg-blue-700 rounded-full p-0">
              <Send className="w-4 h-4 text-white" />
            </Button>
          </div>
        </form>

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
    </div>
  )
}
