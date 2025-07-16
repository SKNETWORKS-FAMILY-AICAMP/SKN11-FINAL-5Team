"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import ReactMarkdown from "react-markdown"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import Image from "next/image"
import { Send, Menu, User } from "lucide-react"
import { agentApi } from "@/app/api/agent"
import { AGENT_CONFIG, type AgentType } from "@/config/constants"
import html2canvas from "html2canvas";
import jsPDF from "jspdf";

interface Message {
  sender: "user" | "agent"
  text: string
}

interface ConversationMessage {
  role: "user" | "agent"
  content: string
}

interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
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
              className={`cursor-pointer text-2xl transition-colors duration-200 ${rating >= num ? "text-yellow-400" : "text-gray-300"} hover:text-yellow-300`}
              onMouseEnter={() => setRating(num)}
              onMouseLeave={() => setRating(rating)}
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
          <Button onClick={onSubmit} className="bg-green-600 hover:bg-green-700">
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
    {
      icon: "/icons/3D_새채팅.png",
      label: "새 채팅 시작하기",
      type: "unified_agent",
    },
    {
      icon: "/icons/3D_홈.png",
      label: "상담 메인화면",
      type: "home",
    },
    ...Object.entries(AGENT_CONFIG)
      .filter(([key]) => key !== "unified_agent")
      .map(([key, value]) => ({
        icon: value.icon,
        label: `${value.name} 에이전트`,
        type: key,
      })),
  ]

  return (
    <div
      className={`${
        expanded ? "w-52" : "w-14"
      } bg-green-200 flex flex-col py-3 px-1 transition-all duration-300 shrink-0`}
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
    >
      <div className="flex flex-col space-y-2 mb-4">
        {menuItems.map((item, idx) => (
          <div
            key={idx}
            onClick={() => onSelectAgent(item.type)}
            className={`flex items-center gap-1 text-xs transition-all duration-150 ${
              idx === 0 ? "text-green-700 font-semibold hover:bg-green-50" : "text-gray-800 hover:bg-green-100"
            } cursor-pointer ${expanded ? "px-1 py-1 rounded-md" : "justify-center"}`}
          >
            <div
              className="rounded-full bg-white flex items-center justify-center shadow shrink-0"
              style={{ width: "36px", height: "36px" }}
            >
              <Image src={item.icon} alt={item.label} width={24} height={24} className="w-6 h-6" />
            </div>
            {expanded && <span className="whitespace-nowrap">{item.label}</span>}
          </div>
        ))}
      </div>

      {expanded && (
        <div className="px-1">
          <div className="text-[10px] text-gray-500 font-bold px-1 mb-1 mt-3">채팅</div>
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
                className={`text-xs px-1 py-[2px] rounded hover:bg-green-100 cursor-pointer ${
                  currentChatId === chat.id ? "bg-green-50 text-green-800" : "text-gray-700"
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

function extractBodyInnerHtml(fullHtml: string): string {
  const bodyMatch = fullHtml.match(/<body[^>]*>([\s\S]*?)<\/body>/im);
  return bodyMatch ? bodyMatch[1] : fullHtml;
}

function isHtmlContent(content: string): boolean {
  return /<!doctype html|<html|<body/i.test(content.trim());
}


function LeanCanvasPopup({
      html,
      onClose,
      onDownload,
      iframeRef
    }: {
      html: string
      onClose: () => void
      onDownload: () => void
      iframeRef: React.RefObject<HTMLIFrameElement>
    }) {
      //const iframeRef = useRef<HTMLIFrameElement>(null)

      // 버튼 클릭 시 iframe 내부의 다운로드 버튼에 이벤트 연결 (optional)
      useEffect(() => {
        const iframe = iframeRef.current
        if (!iframe) return

        const onLoad = () => {
          const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document
          if (!iframeDoc) return

          const button = iframeDoc.getElementById("downloadBtn")
          if (button) {
            button.addEventListener("click", onDownload)
          }
        }

        iframe.addEventListener("load", onLoad)
        return () => iframe.removeEventListener("load", onLoad)
      }, [html, onDownload])

      return (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
          <div className="bg-white rounded shadow-lg max-w-[90%] max-h-[90%] w-full h-full flex flex-col overflow-hidden">
            <iframe
              ref={iframeRef}
              srcDoc={html}
              title="Lean Canvas Preview"
              style={{ width: "100%", flex: 1, border: "none", borderRadius: "12px" }}
              sandbox="allow-same-origin allow-scripts allow-downloads allow-modals"            />
            <div className="mt-4 flex justify-end space-x-2 p-4 bg-white shrink-0">
              <Button onClick={onDownload} className="bg-green-600 hover:bg-green-700">
                PDF 다운로드
              </Button>
              <Button onClick={onClose} variant="ghost">
                닫기
              </Button>
            </div>
          </div>
        </div>
      )
    }

export default function ChatRoomPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const agent = (searchParams?.get("agent") || "unified_agent") as AgentType
  const initialQuestion = searchParams?.get("question") || ""

  const [userId] = useState(3) // 실제 구현시 로그인 사용자 ID 사용
  const [conversationId, setConversationId] = useState<number | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [userInput, setUserInput] = useState("")
  const [agentType, setAgentType] = useState<AgentType>(agent)

  // html린캐버스
  const [leanCanvasHtml, setLeanCanvasHtml] = useState<string | null>(null)
  const [showCanvasPopup, setShowCanvasPopup] = useState(false)

  
  // 피드백 모달 상태
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [rating, setRating] = useState(0)
  const [comment, setComment] = useState("")
  const [category, setCategory] = useState(agent?.replace("_agent", "") || "general")

  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

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
    const initializeChat = async () => {
      try {
        await startNewConversation(agent)
        if (initialQuestion) {
          setUserInput(initialQuestion)
          setTimeout(() => {
            const form = document.querySelector("form")
            if (form) {
              form.dispatchEvent(new Event("submit", { bubbles: true }))
            }
          }, 100)
        }
      } catch (error) {
        console.error("초기화 실패:", error)
        alert("채팅 초기화에 실패했습니다. 페이지를 새로고침해주세요.")
      }
    }
    initializeChat()
  }, [agent, initialQuestion])


  // PDF 다운로드 함수 _ original
  useEffect(() => {
      const handler = () => setShowCanvasPopup(true);
      window.addEventListener('openLeanCanvasPopup', handler);
      return () => window.removeEventListener('openLeanCanvasPopup', handler);
    }, []);
    
    const iframeRef = useRef<HTMLIFrameElement>(null);

    
    
    async function handleDownloadLeanCanvasPdf() {
      if (!iframeRef.current) return;

      const iframeDoc = iframeRef.current.contentDocument;
      const captureArea = iframeDoc?.getElementById("capture-area");
      const downloadBtn = iframeDoc?.getElementById("downloadBtn");

      if (!captureArea) {
        alert("캡처할 영역을 찾을 수 없습니다.");
        return;
      }

      // 1. textarea → preview 전환 및 formData 수집
      const textareas = captureArea.querySelectorAll("textarea");
      const formData: Record<string, string> = {};
      textareas.forEach((textarea: any) => {
        const wrapper = textarea.closest(".textarea-wrapper");
        const preview = wrapper?.querySelector(".preview-textarea") as HTMLElement;
        preview.textContent = textarea.value;
        textarea.style.display = "none";
        preview.style.display = "block";
        formData[textarea.name] = textarea.value;
      });

      if (downloadBtn) downloadBtn.style.visibility = "hidden";

      // 2. 캡처 및 PDF 생성
      const canvas = await html2canvas(captureArea, {
        scale: 2,
        useCORS: true,
        backgroundColor: null,
      });

      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF({
        orientation: "landscape",
        unit: "px",
        format: [canvas.width, canvas.height],
      });

      const imgProps = pdf.getImageProperties(imgData);
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;

      pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);
      pdf.save("lean-canvas.pdf");

      // pdf.addImage(imgData, "PNG", 0, 0, canvas.width, canvas.height);
      // pdf.save("lean-canvas.pdf");

      if (downloadBtn) downloadBtn.style.visibility = "visible";

      // 3. 서버 전송
      const style = iframeDoc?.querySelector("style")?.innerText || "";
      const html = `
        <html lang="ko">
          <head><meta charset="UTF-8"><style>${style}</style></head>
          <body>${captureArea.innerHTML}</body>
        </html>
      `;

      try {
        const res = await fetch("http://localhost:8001/report/pdf/create", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            html,
            form_data: formData,
            user_id: userId, // <- 상태에서 가져온 ID
            conversation_id: conversationId,
          }),
        });

        const result = await res.json();
        if (result.file_id) {
          console.log("서버에 저장 완료:", result.file_id);
          // window.location.href = `/report/pdf/download/${result.file_id}`;  // 자동 다운로드 원할 시
        } else {
          alert("서버 저장 실패");
        }
      } catch (e) {
        console.error("PDF 서버 전송 실패:", e);
      }

      // 4. 원상 복구
      textareas.forEach((textarea: any) => {
        const wrapper = textarea.closest(".textarea-wrapper");
        const preview = wrapper?.querySelector(".preview-textarea") as HTMLElement;
        textarea.style.display = "block";
        preview.style.display = "none";
      });
    }


  const loadPreviousChat = async (chatId: number) => {
    try {
      const result = await agentApi.getConversationMessages(chatId)
      if (result.status === "success" && result.data.messages) {
        setMessages(
          result.data.messages.map((msg) => ({
            sender: msg.role === "user" ? "user" : "agent",
            text: msg.content,
          }))
        )
        setConversationId(chatId)
        setCurrentChatId(chatId)
      }
    } catch (error) {
      console.error("이전 채팅 로드 실패:", error)
    }
  }


  const startNewConversation = async (newAgent: AgentType = "unified_agent") => {
    try {
      const result = await agentApi.createConversation(userId)
      if (!result.success) {
        throw new Error(result.error || "대화 세션 생성에 실패했습니다")
      }
      if (!result.data?.conversationId) {
        throw new Error("대화 세션 ID를 받지 못했습니다")
      }
      setConversationId(result.data.conversationId)
      setMessages([])
      setUserInput("")
      setAgentType(newAgent)
      setCurrentChatId(null)
    } catch (error) {
      console.error("대화 세션 생성 실패:", error)
      throw error
    }
  }

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!userInput.trim()) return
    
    let currentConversationId = conversationId
    if (!currentConversationId) {
      try {
        const result = await agentApi.createConversation(userId)
        if (!result.success) {
          alert("채팅 세션을 생성할 수 없습니다. 다시 시도해주세요.")
          return
        }
        currentConversationId = result.data?.conversationId || null
        if (!currentConversationId) {
          alert("채팅 세션을 생성할 수 없습니다. 다시 시도해주세요.")
          return
        }
        setConversationId(currentConversationId)
      } catch (error) {
        console.error("대화 세션 생성 실패:", error)
        alert("채팅 시작에 실패했습니다. 다시 시도해주세요.")
        return
      }
    }

    const currentInput = userInput
    setUserInput("")

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
    }

    const userMessage: Message = { sender: "user", text: currentInput }
    setMessages((prev: Message[]) => [...prev, userMessage])

    try {
      if (!currentConversationId) {
        throw new Error("대화 세션이 없습니다")
      }
      
      const result = await agentApi.sendQuery(userId, currentConversationId, currentInput, agentType)

      if (!result.success || !result.data) {
        throw new Error(result.error || "응답을 받지 못했습니다")
      }
      
      console.log("result.data", result.data)
      if (result.data?.answer) {
        const answer = result.data.answer.trim();

        if (isHtmlContent(answer)) {
          // const cleanHtml = extractBodyInnerHtml(answer);
          // setLeanCanvasHtml(cleanHtml);
          setLeanCanvasHtml(result.data.answer);

          const agentMessage: Message = {
            sender: "agent",
            text: "[Lean Canvas] 도착! 클릭하여 수정 및 다운로드 가능합니다.",
          };
          setMessages((prev) => [...prev, agentMessage]);
        } else {
          const agentMessage: Message = {
            sender: "agent",
            text: result.data.answer,
          };
          setMessages((prev) => [...prev, agentMessage]);
        }
      }


                
    } catch (error) {
      console.error("응답 실패:", error)
      const agentMessage: Message = {
        sender: "agent",
        text: "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
      }
      setMessages((prev: Message[]) => [...prev, agentMessage])
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

  const handleExampleClick = async (text: string) => {
    setUserInput(text)
    let currentConversationId = conversationId
    if (!currentConversationId) {
      try {
        const result = await agentApi.createConversation(userId)
        if (!result.success) {
          alert("채팅 세션을 생성할 수 없습니다. 다시 시도해주세요.")
          return
        }
        currentConversationId = result.data?.conversationId || null
        if (!currentConversationId) {
          alert("채팅 세션을 생성할 수 없습니다. 다시 시도해주세요.")
          return
        }
        setConversationId(currentConversationId)
      } catch (error) {
        console.error("대화 세션 생성 실패:", error)
        alert("채팅 시작에 실패했습니다. 다시 시도해주세요.")
        return
      }
    }
    
    try {
      if (!currentConversationId) {
        throw new Error("대화 세션이 없습니다")
      }

      const result = await agentApi.sendQuery(userId, currentConversationId, text, agentType)
      if (!result.success || !result.data) {
        throw new Error(result.error || "메시지 전송에 실패했습니다")
      }

      const userMessage: Message = { sender: "user", text }
      const agentMessage: Message = {
        sender: "agent",
        text: result.data.answer,
      }
      setMessages((prev: Message[]) => [...prev, userMessage, agentMessage])
      setUserInput("")
    } catch (error) {
      console.error("응답 실패:", error)
      alert("서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
    }
  }

  const handleSidebarSelect = async (type: string) => {
    try {
      if (type === "home") {
        router.push("/chat")
        return
      }
      
      await startNewConversation(type as AgentType)
      router.push(`/chat/room?agent=${type}`)
    } catch (error) {
      console.error("에이전트 변경 실패:", error)
      alert("에이전트 변경에 실패했습니다. 다시 시도해주세요.")
    }
  }

  const handleFeedbackSubmit = async () => {
    if (!conversationId) return

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


  return (
    <div className="flex h-screen overflow-hidden bg-green-50">
      <Sidebar
        onSelectAgent={handleSidebarSelect}
        chatHistory={chatHistory}
        currentChatId={currentChatId}
        onLoadPreviousChat={loadPreviousChat}
        onNewChat={() => {
          setCurrentChatId(null)
          startNewConversation(agentType)
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
                    <div className="font-bold mb-2 text-green-600">{item.category}</div>
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
                  <div className="w-10 h-10 rounded-full bg-green-600 flex items-center justify-center shadow shrink-0">
                    <Image src="/3D_고양이.png" width={36} height={36} alt="사용자" className="rounded-full" />
                  </div>
                  <div className="inline-block max-w-[90%] p-0.5">
                    <div className="bg-green-100 text-green-900 px-4 py-3 rounded-2xl shadow-md whitespace-pre-wrap leading-relaxed">
                      {msg.text}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-end space-x-2">
                  <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center shadow shrink-0">
                    <Image
                      src={AGENT_CONFIG[agentType].icon}
                      width={36}
                      height={36}
                      alt={AGENT_CONFIG[agentType].name}
                      className="rounded-full"
                    />
                  </div>
                  <div className="inline-block max-w-[90%] p-0.5">
                    <div className="bg-white text-gray-800 px-4 py-3 rounded-2xl shadow-md whitespace-pre-wrap leading-relaxed">
                      {msg.text === "[Lean Canvas] 도착! 클릭하여 수정 및 다운로드 가능합니다." ? (
                        <>
                          <div className="space-y-2">
                            <div>📦 <strong>Lean Canvas</strong>가 도착했습니다.</div>
                            <Button onClick={() => {
                              setShowCanvasPopup(true); // 팝업
                            }}>
                              미리보기 팝업 열기
                            </Button>
                          </div>
                        </>
                      ) : (
                        <ReactMarkdown>{msg.text}</ReactMarkdown>
                      )}


                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}

          <div ref={scrollRef} />
        </div>
        {showCanvasPopup && leanCanvasHtml && (
          <LeanCanvasPopup
            html={leanCanvasHtml}
            onClose={() => setShowCanvasPopup(false)}
            onDownload={handleDownloadLeanCanvasPdf}
            iframeRef={iframeRef} 
          />
        )}


        {/* 입력 영역 */}
        <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-green-50 via-green-50">
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


// 목표
// 린캔버스 답변이 올 때만 미리보기와 PDF 다운로드 버튼이 자동으로 노출되고, 
// ->  {leanCanvasHtml && ( <div ...   <Button ...

//  leanCanvasHtml 상태에 HTML이 저장됨
// -> if (res.success && res.data && res.data.type === "lean_canvas") { .. }

// 버튼을 누르면 PDF로 변환 및 다운로드가 정상적으로 이뤄집니다. -> downloadLeanCanvasPdf() 
