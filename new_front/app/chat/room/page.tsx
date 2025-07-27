"use client"

import React from "react"
import { useState, useEffect, useRef, useCallback } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import ReactMarkdown from "react-markdown"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import Image from "next/image"
import { Send, ArrowLeft, Plus, MoreVertical, X, Edit2, Trash2, ThumbsUp, ThumbsDown } from "lucide-react"
import { agentApi } from "@/app/api/agent"
import { AGENT_CONFIG, type AgentType, API_BASE_URL } from "@/config/constants"
import type { Message, ConversationMessage } from "@/types/messages"
import { FeedbackModal } from "@/components/ui/FeedbackModal"
import remarkGfm from 'remark-gfm' // 이 패키지를 설치해야 합니다: npm install remark-gfm
import rehypeRaw from "rehype-raw"; // npm install rehype-raw --legacy-peer-deps


// ===== 타입 정의 =====
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

interface ExtendedMessage extends Message {
  isTyping?: boolean
  isComplete?: boolean
}

// ===== 상수 =====
const MESSAGES_STORAGE_KEY = 'chat_messages'

// const exampleQuestions = [
//   {
//     category: "사업기획",
//     question: "온라인 쇼핑몰을 운영하려는데 초기 사업계획을 어떻게 세우면 좋을까요?",
//     agent: "planner",
//   },
//   {
//     category: "마케팅",
//     question: "인스타그램에서 제품을 효과적으로 홍보하려면 어떤 팁이 있을까요?",
//     agent: "marketing",
//   },
//   {
//     category: "고객관리",
//     question: "리뷰에 불만 글이 달렸을 때 어떻게 대응해야 좋을까요?",
//     agent: "crm",
//   },
//   {
//     category: "업무지원",
//     question: "매번 반복되는 예약 문자 전송을 자동화할 수 있을까요?",
//     agent: "task",
//   },
//   {
//     category: "멘탈케어",
//     question: "요즘 자주 우울해서 자가 진단 설문을 해보고 싶어요.",
//     agent: "mental_health",
//   },
// ]

// ===== 에이전트별 예시 질문 맵 =====
const exampleQuestionsMap: Record<AgentType, { category: string; question: string; agent: string }[]> = {
  planner: [
    {
      category: "사업기획",
      question: "온라인 쇼핑몰을 시작하려면 어떤 준비가 필요할까요?",
      agent: "planner"
    },
    {
      category: "시장조사",
      question: "타겟 고객을 어떻게 설정하나요?",
      agent: "planner"
    },
    {
      category: "수익모델",
      question: "지속 가능한 비즈니스 모델을 만드는 법은?",
      agent: "planner"
    },
    {
      category: "사업계획서",
      question: "초기 사업계획서는 어떤 식으로 구성해야 하나요?",
      agent: "planner"
    },
    {
      category: "사업 타당성",
      question: "내 아이디어가 실제로 가능한지 검토하려면?",
      agent: "planner"
    }
  ],
  marketing: [
    {
      category: "마케팅",
      question: "인스타그램 마케팅을 효과적으로 하는 법은?",
      agent: "marketing"
    },
    {
      category: "브랜딩",
      question: "브랜드 스토리를 어떻게 만들 수 있나요?",
      agent: "marketing"
    },
    {
      category: "콘텐츠 전략",
      question: "콘텐츠 기획은 어떤 흐름으로 해야 하나요?",
      agent: "marketing"
    },
    {
      category: "광고",
      question: "소규모 예산으로도 광고 효과를 낼 수 있을까요?",
      agent: "marketing"
    },
    {
      category: "이메일 마케팅",
      question: "이메일 오픈율을 높이려면 어떻게 해야 하나요?",
      agent: "marketing"
    }
  ],
  crm: [
    {
      category: "고객관리",
      question: "클레임 고객에게 어떻게 응대하는 게 좋을까요?",
      agent: "crm"
    },
    {
      category: "리뷰관리",
      question: "부정적인 리뷰는 어떻게 처리하나요?",
      agent: "crm"
    },
    {
      category: "재구매 유도",
      question: "단골 고객을 만드는 방법이 궁금해요.",
      agent: "crm"
    },
    {
      category: "CS 자동화",
      question: "고객문의 대응을 자동화할 수 있나요?",
      agent: "crm"
    },
    {
      category: "고객 세분화",
      question: "고객을 유형별로 나누고 대응할 수 있을까요?",
      agent: "crm"
    }
  ],
  task: [
    {
      category: "업무지원",
      question: "매일 반복되는 업무를 자동화할 수 있을까요?",
      agent: "task"
    },
    {
      category: "일정관리",
      question: "캘린더 일정 자동 등록 방법이 궁금해요.",
      agent: "task"
    },
    {
      category: "업무분배",
      question: "팀원들에게 업무를 효율적으로 분배하고 싶어요.",
      agent: "task"
    },
    {
      category: "파일 정리",
      question: "클라우드에 파일 정리를 자동화할 수 있나요?",
      agent: "task"
    },
    {
      category: "보고서 생성",
      question: "정기 보고서를 자동으로 작성할 수 있을까요?",
      agent: "task"
    }
  ],
  mentalcare: [
    {
      category: "멘탈케어",
      question: "요즘 기분이 가라앉는데 어떻게 하면 좋을까요?",
      agent: "mental_health"
    },
    {
      category: "스트레스",
      question: "스트레스를 줄이는 실용적인 방법이 궁금해요.",
      agent: "mental_health"
    },
    {
      category: "자가진단",
      question: "요즘 자주 우울해서 자가 진단 설문을 해보고 싶어요.",
      agent: "mental_health"
    },
    {
      category: "자존감",
      question: "자존감을 높이기 위한 일상 루틴이 있을까요?",
      agent: "mental_health"
    },
    {
      category: "감정관리",
      question: "화가 날 때 침착하게 대처하는 방법은?",
      agent: "mental_health"
    }
  ],
  unified_agent: [
    {
      category: "사업기획",
      question: "온라인 쇼핑몰을 운영하려는데 초기 사업계획을 어떻게 세우면 좋을까요?",
      agent: "planner"
    },
    {
      category: "마케팅",
      question: "인스타그램에서 제품을 효과적으로 홍보하려면 어떤 팁이 있을까요?",
      agent: "marketing"
    },
    {
      category: "고객관리",
      question: "리뷰에 불만 글이 달렸을 때 어떻게 대응해야 좋을까요?",
      agent: "crm"
    },
    {
      category: "업무지원",
      question: "매번 반복되는 예약 문자 전송을 자동화할 수 있을까요?",
      agent: "task"
    },
    {
      category: "멘탈케어",
      question: "요즘 자주 우울해서 자가 진단 설문을 해보고 싶어요.",
      agent: "mental_health"
    }
  ]
}

// ===== 현재 에이전트의 예시 질문 가져오기 함수 =====
const getCurrentAgentExamples = (currentAgent: AgentType) => {
  return exampleQuestionsMap[currentAgent] || exampleQuestionsMap.unified_agent
}

// ===== 유틸리티 함수 =====
const saveMessages = (conversationId: number, messages: ExtendedMessage[]) => {
  try {
    sessionStorage.setItem(MESSAGES_STORAGE_KEY + conversationId, JSON.stringify(messages))
  } catch (error) {
    console.error('메시지 저장 실패:', error)
  }
}

const loadMessages = (conversationId: number): ExtendedMessage[] | null => {
  try {
    const saved = sessionStorage.getItem(MESSAGES_STORAGE_KEY + conversationId)
    return saved ? JSON.parse(saved) : null
  } catch (error) {
    console.error('메시지 로드 실패:', error)
    return null
  }
}

// ===== 서브 컴포넌트들 =====
function TypingAnimation() {
  return (
    <div className="flex items-center space-x-1">
      <div className="flex space-x-1">
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
      </div>
      {/* <span className="text-sm text-gray-500 ml-2">답변 중입니다...</span> */}
    </div>
  )
}

// ===== PHQ-9 버튼 컴포넌트 =====
const PHQ9ButtonComponent = React.memo(({ 
  question, 
  onResponse,
  isDisabled = false
}: { 
  question: any
  onResponse: (value: number) => void
  isDisabled?: boolean
}) => {
  console.log("[DEBUG] PHQ9ButtonComponent 렌더링, question:", question)
  
  const responseOptions = [
    { value: 0, label: "전혀 그렇지 않다" },
    { value: 1, label: "며칠 정도 그렇다" },
    { value: 2, label: "일주일 이상 그렇다" },
    { value: 3, label: "거의 매일 그렇다" }
  ]

  return (
    <div className="space-y-4 mt-4">
      <div className="bg-green-50 p-4 rounded-lg border border-green-200">
        <div className="flex justify-between items-center mb-3">
          <span className="text-sm font-medium text-green-600">
            진행률: {question.progress || "1/9"}
          </span>
          <span className="text-sm text-gray-500">PHQ-9 우울증 자가진단</span>
        </div>
        
        <h4 className="text-lg font-semibold text-gray-800 mb-4 leading-relaxed">
          지난 2주 동안, <span className="text-green-700">{question.text || question.question}</span>
        </h4>
        
        <div className="space-y-2">
          {responseOptions.map((option) => (
            <Button
              key={option.value}
              onClick={() => {
                console.log("[DEBUG] PHQ-9 버튼 클릭:", option.value)
                onResponse(option.value)
              }}
              disabled={isDisabled}
              className="w-full p-3 text-left justify-start border-2 transition-all duration-200 bg-white hover:bg-green-50 border-green-300 text-gray-800 font-medium hover:border-green-400 disabled:opacity-50 disabled:cursor-not-allowed"
              variant="outline"
            >
              <span className="flex items-center">
                <span className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center mr-3 text-sm font-bold border border-green-300">
                  {option.value}
                </span>
                {option.label}
              </span>
            </Button>
          ))}
        </div>
        
        <div className="mt-4 p-3 bg-gray-50 rounded-md">
          <p className="text-xs text-gray-600">
            💡 지난 2주간 얼마나 자주 이런 문제들로 고민했는지를 기준으로 선택해주세요.
          </p>
        </div>
      </div>
    </div>
  )
})

function TypingText({ text, speed = 30, onComplete, onTextUpdate }: { text: string, speed?: number, onComplete?: () => void, onTextUpdate?: () => void }) {
  const [displayedText, setDisplayedText] = useState("")
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayedText(prev => prev + text[currentIndex])
        setCurrentIndex(prev => prev + 1)

        // 텍스트가 업데이트될 때마다 스크롤 트리거
        if (onTextUpdate) {
          // 약간의 지연을 주어 DOM 업데이트 후 스크롤
          setTimeout(onTextUpdate, 10)
        }
      }, speed)

      return () => clearTimeout(timer)
    } else if (onComplete) {
      onComplete()
    }
  }, [currentIndex, text, speed, onComplete, onTextUpdate])

  useEffect(() => {
    setDisplayedText("")
    setCurrentIndex(0)
  }, [text])

  return (
    <div className="whitespace-pre-wrap !leading-snug">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]} // GitHub Flavored Markdown 지원
        components={{
          p: ({ children }) => <p className="!m-0 !p-0 !leading-snug">{children}</p>,
          ul: ({ children }) => <ul className="!m-0 !ml-4 !p-0 !leading-snug">{children}</ul>,
          ol: ({ children }) => <ol className="!m-0 !ml-4 !p-0 !leading-snug">{children}</ol>,
          li: ({ children }) => <li className="!m-0 !p-0 !leading-snug">{children}</li>,
          h1: ({ children }) => <h1 className="!text-xl !font-bold !m-0 !p-0 !leading-snug">{children}</h1>,
          h2: ({ children }) => <h2 className="!text-lg !font-bold !m-0 !p-0 !leading-snug">{children}</h2>,
          h3: ({ children }) => <h3 className="!text-base !font-bold !m-0 !p-0 !leading-snug">{children}</h3>,
          strong: ({ children }) => <strong className="!font-semibold !m-0 !p-0">{children}</strong>,
          
          // 테이블 컴포넌트 추가
          table: ({ children }) => (
            <div className="overflow-x-auto my-4">
              <table className="min-w-full border-collapse border border-gray-300 text-sm">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-green-50">
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody className="bg-white divide-y divide-gray-200">
              {children}
            </tbody>
          ),
          tr: ({ children }) => (
            <tr className="hover:bg-gray-50">
              {children}
            </tr>
          ),
          th: ({ children }) => (
            <th className="px-3 py-2 text-left font-semibold text-gray-900 border border-gray-300 bg-green-100">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-3 py-2 text-gray-700 border border-gray-300">
              {children}
            </td>
          ),
          
          // 코드 블록 지원
          code: ({ node, inline, className, children, ...props }: any) => 
            inline ? (
              <code className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono" {...props}>
                {children}
              </code>
            ) : (
              <pre className="bg-gray-100 p-3 rounded-lg overflow-x-auto my-2">
                <code className="text-sm font-mono" {...props}>
                  {children}
                </code>
              </pre>
            )
        }}
      >
        {displayedText}
      </ReactMarkdown>
      {currentIndex < text.length && (
        <span className="inline-block w-0.5 h-4 bg-gray-400 ml-1 animate-pulse"></span>
      )}
    </div>
  )
}


function DraftPreviewModal({
  userId,
  content,
  onClose,
  onDownload,
}: {
  userId: number | string;
  content: string;
  onClose: () => void;
  onDownload?: () => void;
}) {
  const previewRef = useRef(null);
  const [driveUploading, setDriveUploading] = useState(false);
  const [driveStatus, setDriveStatus] = useState<string | null>(null);
  const [driveUrl, setDriveUrl] = useState<string | null>(null);

  const getPdfBlob = async (element: HTMLElement) => {
    // Check if we're on the client side
    if (typeof window === 'undefined') {
      throw new Error('PDF generation is only available on the client side');
    }
    
    // Dynamic import only when needed
    const html2pdf = (await import('html2pdf.js')).default;
    return await html2pdf()
      .set({
        margin: [10, 10],
        filename: "사업기획서.pdf",
        html2canvas: { scale: 2, backgroundColor: "#fff" },
        jsPDF: { unit: "pt", format: "a4", orientation: "portrait" },
      })
      .from(element)
      .outputPdf('blob');
  };

  const handleDriveUpload = async () => {
    setDriveUploading(true);
    setDriveStatus(null);
    setDriveUrl(null);
    try {
      setDriveStatus("구글 드라이브 업로드 요청 중...");
      if (!previewRef.current) throw new Error("미리보기 영역이 없어요!");
      const pdfBlob = await getPdfBlob(previewRef.current);
      const pdfFile = new File([pdfBlob], "사업기획서.pdf", { type: "application/pdf" });

      const formData = new FormData();
      formData.append("user_id", userId.toString());
      formData.append("file", pdfFile);

      const tempResp = await fetch("http://localhost:8001/drive/upload", {
        method: "POST",
        body: formData,
      });
      const tempData = await tempResp.json();

      if (tempData?.success && tempData.filename) {
        const uploadResp = await fetch("http://localhost:8001/drive/upload/gdrive", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: userId,
            filename: tempData.filename,
            mime_type: pdfFile.type,
          }),
        });
        const uploadData = await uploadResp.json();
        if (uploadData.success) {
          setDriveStatus("구글 드라이브 업로드가 완료됐습니다");
          if (uploadData.webViewLink) setDriveUrl(uploadData.webViewLink);
        } else {
          setDriveStatus("업로드 실패: " + (uploadData.message || uploadData.error));
        }
      } else {
        setDriveStatus("서버 파일 업로드 실패: " + (tempData?.message || ""));
      }
    } catch (err: any) {
      setDriveStatus("에러: " + (err?.message || err));
    } finally {
      setDriveUploading(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!previewRef.current) return;
    try {
      // Check if we're on the client side
      if (typeof window === 'undefined') {
        console.error('PDF download is only available on the client side');
        return;
      }
      
      // Dynamic import only when needed
      const html2pdf = (await import('html2pdf.js')).default;
      await html2pdf()
        .set({
          margin: [10, 10],
          filename: "사업기획서.pdf",
          html2canvas: { scale: 2, backgroundColor: "#fff" },
          jsPDF: { unit: "pt", format: "a4", orientation: "portrait" },
        })
        .from(previewRef.current)
        .save();
    } catch (error) {
      console.error("PDF 다운로드 실패:", error);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-[90%] h-[90%] flex flex-col">
        <div className="flex justify-between items-center p-4 border-b">
          <h2 className="text-xl font-bold">사업기획서 미리보기</h2>
          <div className="flex gap-2">
            <Button onClick={handleDownloadPdf} variant="outline">PDF 다운로드</Button>
            <Button onClick={handleDriveUpload} disabled={driveUploading} variant="outline">
              {driveUploading ? "업로드 중..." : "구글 드라이브 업로드"}
            </Button>
            <Button onClick={onClose} variant="outline">닫기</Button>
          </div>
        </div>
        {driveStatus && (
          <div className="p-4 bg-blue-50 border-b">
            <p className="text-sm text-blue-700">{driveStatus}</p>
            {driveUrl && (
              <a href={driveUrl} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline text-sm">
                구글 드라이브에서 보기
              </a>
            )}
          </div>
        )}
        <div className="flex-1 overflow-auto p-6">
          <div ref={previewRef} className="max-w-4xl mx-auto bg-white">
            <div className="prose prose-lg max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                {content}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


// ===== 프로젝트 모달 컴포넌트 =====
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
  project: Project
  onEdit: (project: Project) => void
  onDelete: (projectId: number) => void 
}) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="icon"
        className="w-4 h-4 p-0 text-gray-400 hover:text-gray-800 ml-1 opacity-0 group-hover:opacity-100"
        onClick={(e) => {
          e.stopPropagation()
          setIsOpen((prev) => !prev)
        }}
      >
        <MoreVertical className="w-3 h-3" />
      </Button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-20 min-w-[120px]">
            <button
              className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100"
              onClick={(e) => {
                e.stopPropagation()
                onEdit(project)
                setIsOpen(false)
              }}
            >
              이름 변경
            </button>
            <button
              className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-100"
              onClick={(e) => {
                e.stopPropagation()
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
  chat: ChatHistoryItem
  onEditTitle: (chatId: number, newTitle: string) => void
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
              setIsOpen((prev) => !prev)
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

// ===== 계정 메뉴 컴포넌트 =====
function AccountMenu({ isExpanded }: { isExpanded: boolean }) {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [userInfo, setUserInfo] = useState<any>(null)
  const router = useRouter()

  useEffect(() => {
    const storedUser = localStorage.getItem("user")
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser)
        setUserInfo(user)
      } catch (e) {
        console.error("유저 정보 파싱 오류:", e)
      }
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem("user")
    router.push("/login")
    setIsMenuOpen(false)
  }

  const handleMyPage = () => {
    router.push("/mypage")
    setIsMenuOpen(false)
  }

  const handleWorkspace = () => {
    router.push("/workspace")
    setIsMenuOpen(false)
  }

  if (!userInfo) return null

  return (
    <div className="relative">
      {isExpanded ? (
        <div className="border-t border-green-200 pt-2">
          <div 
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg cursor-pointer hover:bg-green-100 transition-colors"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            <div className="w-7 h-7 rounded-full bg-green-600 flex items-center justify-center text-white text-xs font-medium">
              {userInfo.username?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-medium text-gray-900 truncate">
                {userInfo.username || '사용자'}
              </div>
            </div>
            <MoreVertical className="w-3 h-3 text-gray-400" />
          </div>

          {isMenuOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setIsMenuOpen(false)} />
              <div className="absolute bottom-full left-3 right-3 mb-2 bg-white border border-gray-200 rounded-lg shadow-lg z-20">
                <button
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-green-50 rounded-t-lg transition-colors"
                  onClick={handleMyPage}
                >
                  마이페이지
                </button>
                <button
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-green-50 border-t border-gray-100 transition-colors"
                  onClick={handleWorkspace}
                >
                  워크스페이스
                </button>
                <button
                  className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-b-lg border-t border-gray-100 transition-colors"
                  onClick={handleLogout}
                >
                  로그아웃
                </button>
              </div>
            </>
          )}
        </div>
      ) : (
        <div className="border-t border-green-200 pt-1.5 flex justify-center">
          <button
            className="w-7 h-7 rounded-full bg-green-600 flex items-center justify-center text-white text-xs font-medium hover:bg-green-700 transition-colors"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            title={`${userInfo.username || '사용자'} 계정`}
          >
            {userInfo.username?.charAt(0)?.toUpperCase() || 'U'}
          </button>

          {isMenuOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setIsMenuOpen(false)} />
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 bg-white border border-gray-200 rounded-lg shadow-lg z-20 min-w-[120px]">
                <button
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-green-50 rounded-t-lg transition-colors"
                  onClick={handleMyPage}
                >
                  마이페이지
                </button>
                <button
                  className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-b-lg border-t border-gray-100 transition-colors"
                  onClick={handleLogout}
                >
                  로그아웃
                </button>
              </div>
            </>
          )}
        </div>
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
      className={`${isExpanded ? "w-64" : "w-14"}
        bg-green-50 border-r-2 border-gray-200 flex flex-col py-3 px-2
        transition-all duration-300 shrink-0 fixed left-0 top-0 h-screen z-30`}
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      {/* 상단 고정 영역 */}
      <div className="flex-shrink-0 pb-2">
        {isExpanded ? (
          <div className="px-2 mb-2 flex items-center justify-between">
            <h1 
              className="text-xl font-bold text-gray-800 cursor-pointer hover:text-green-700 transition-colors"
              onClick={() => router.push("/")}
            >
              TinkerBell
            </h1>
            <button
              onClick={onNewChat}
              className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-3 py-1.5 rounded-md text-sm shadow hover:shadow-lg transition"
            >
              새 채팅
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center mb-2">
            <button
              onClick={onNewChat}
              title="새 채팅 시작하기"
              className="w-9 h-9 rounded-lg bg-gradient-to-r from-green-600 to-emerald-600 flex items-center justify-center shadow-md hover:scale-105"
            >
              <Image
                src="/icons/3D_새채팅.png"
                alt="새 채팅"
                width={20}
                height={20}
              />
            </button>
          </div>
        )}

        {/* 메뉴 아이콘들 */}
        {isExpanded ? (
          <div className="space-y-0 mb-1">
            {menuItems.map((item, idx) => (
              <div
                key={idx}
                onClick={item.action}
                className="flex items-center gap-2 px-2 py-[6px] text-sm rounded-md cursor-pointer transition-all duration-150 text-gray-800 hover:bg-green-100"
              >
                <div className="w-7 h-7 rounded-full flex items-center justify-center bg-white shadow-sm">
                  <Image
                    src={item.icon || "/placeholder.svg"}
                    alt={item.label}
                    width={18}
                    height={18}
                    className="w-4.5 h-4.5"
                  />
                </div>
                <span className="truncate">{item.label}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-1 flex flex-col items-center mb-4">
            {menuItems.map((item, idx) => (
              <div
                key={idx}
                onClick={item.action}
                className="w-10 h-10 rounded-lg flex items-center justify-center cursor-pointer bg-white hover:bg-green-100 shadow-sm"
                title={item.label}
              >
                <Image
                  src={item.icon || "/placeholder.svg"}
                  alt={item.label}
                  width={24}
                  height={24}
                  className="w-6 h-6"
                  style={{ objectFit: 'contain' }}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 스크롤 가능한 중간 영역 */}
      <div className="flex-1 min-h-0 overflow-y-auto scrollbar-hide">
        {isExpanded && (
          <>
            {/* 프로젝트 섹션 */}
            <div className="mt-8">
              <div className="flex items-center justify-between mb-2 px-3">
                <h3 className="text-sm font-semibold text-gray-800">프로젝트</h3>
                <button
                  onClick={onCreateProject}
                  className="p-1 hover:bg-gray-100 rounded transition-colors"
                >
                  <Plus className="h-3 w-3 text-gray-600 hover:text-green-600" />
                </button>
              </div>

              <div className="space-y-1">
                {projects.slice(0, 3).map((project) => (
                  <div
                    key={project.id}
                    className="group flex items-center justify-between px-3 py-2 rounded hover:bg-gray-50 cursor-pointer"
                    onClick={() => onSelectProject(project.id)}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-normal text-gray-800 truncate" title={project.title}>
                        {project.title}
                      </div>
                    </div>
                    <ProjectMenu
                      project={project}
                      onEdit={onEditProject}
                      onDelete={onDeleteProject}
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* 채팅 기록 섹션 */}
            <div className="mt-8">
              <h3 className="text-sm font-semibold text-gray-800 mb-2 px-3">채팅 기록</h3>
              <div className="space-y-1">
                {chatHistory.map((chat) => (
                  <div
                    key={chat.id}
                    className={`group flex items-start justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                      currentChatId === chat.id
                        ? "bg-green-50 border border-green-200 text-green-800"
                        : "hover:bg-gray-50"
                    }`}
                    onClick={() => onLoadPreviousChat(chat.id)}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-normal text-gray-800 truncate" title={chat.title}>
                        {chat.title}
                      </div>
                      <div className="text-xs text-gray-500 truncate mt-1" title={chat.lastMessage}>
                        {chat.lastMessage}
                      </div>
                    </div>
                    <ChatHistoryMenu
                      chat={chat}
                      onEditTitle={onEditChatTitle}
                      onDelete={onDeleteChat}
                    />
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>

      {/* 하단 고정 계정 메뉴 */}
      <div className="flex-shrink-0 pt-1">
        <AccountMenu isExpanded={isExpanded} />
      </div>
    </div>
  )
}

// ===== 메인 채팅 컴포넌트 =====
export default function ChatRoomPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  // URL 파라미터 추출
  const agent = (searchParams?.get("agent") || "unified_agent") as AgentType
  const initialQuestion = searchParams?.get("question") || ""
  const initialConversationId = searchParams?.get("conversation_id")
    ? Number.parseInt(searchParams.get("conversation_id") as string)
    : null
  const initialProjectId = searchParams?.get("project_id")
    ? Number.parseInt(searchParams.get("project_id") as string)
    : null

  // Refs
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const initializeRef = useRef(false)

  // ===== 상태 관리 =====
  const [userId, setUserId] = useState<number | null>(null)
  const [conversationId, setConversationId] = useState<number | null>(initialConversationId)
  const [messages, setMessages] = useState<ExtendedMessage[]>([])
  const [userInput, setUserInput] = useState("")
  const [agentType, setAgentType] = useState<AgentType>(agent)
  const [currentProjectId, setCurrentProjectId] = useState<number | null>(initialProjectId)
  const [projectInfo, setProjectInfo] = useState<any>(null)
  const [isInitialized, setIsInitialized] = useState(false)
  const [sidebarExpanded, setSidebarExpanded] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [showDraftPreview, setShowDraftPreview] = useState(false)
  const [draftContent, setDraftContent] = useState<string | null>(null)

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

  // PHQ-9 설문 관련 상태
  const [phq9Processing, setPhq9Processing] = useState(false)

  // ===== PHQ-9 관련 함수 =====
  const handlePHQ9Response = useCallback(async (responseValue: number) => {
    if (!userId || !conversationId || phq9Processing) return

    console.log("[DEBUG] PHQ-9 응답 처리:", { responseValue, conversationId, userId })
    
    setPhq9Processing(true)
    
    try {

      const responseLabels = ["전혀 그렇지 않다", "며칠 정도 그렇다", "일주일 이상 그렇다", "거의 매일 그렇다"]
      const userResponseText = `[PHQ-9 응답] ${responseValue}: ${responseLabels[responseValue]}`
      
      // 사용자 메시지를 즉시 화면에 표시
      setMessages(prev => [...prev, {
        sender: "user",
        text: userResponseText,
        isComplete: true,
        isTyping: false
      }])

      const startRes = await fetch(`${API_BASE_URL}/mental/conversation/${conversationId}/phq9/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      });
      const startResult = await startRes.json();
      console.log("[DEBUG] PHQ-9 상태 초기화 결과:", startResult);

      const response = await fetch(`${API_BASE_URL}/mental/conversation/${conversationId}/phq9/response`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          response_value: responseValue
        })
      })

      const result = await response.json()
      
      if (result.success) {
        // 🔥 log_message는 이미 위에서 추가했으므로 제거
        // if (result.data.log_message) {
        //   setMessages(prev => [...prev, {
        //     sender: "user",
        //     text: result.data.log_message,
        //     isComplete: false,
        //     isTyping: false
        //   }])
        // }

        if (result.data.end_survey) {
          setMessages(prev => [...prev, {
            sender: "agent",
            text: result.data.response,
            isComplete: false,
            isTyping: false
          }]);
          return;
        }
        
        // PHQ-9 버튼을 비활성화하고 새로운 메시지 추가
        setMessages(prev => {
          const updated = [...prev]
          
          // 🔥 마지막에서 두 번째 메시지(방금 추가한 사용자 메시지 이전)에서 PHQ-9 버튼 찾기
          const lastAgentMsgIndex = updated.slice(0, -1).findLastIndex(msg => 
            msg.sender === "agent" && msg.text.includes("PHQ9_BUTTON")
          )
          
          if (lastAgentMsgIndex !== -1) {
            // 기존 PHQ-9 버튼 메시지를 비활성화된 상태로 변경
            updated[lastAgentMsgIndex] = {
              ...updated[lastAgentMsgIndex],
              text: updated[lastAgentMsgIndex].text.replace(
                '"isDisabled": false', 
                '"isDisabled": true'
              )
            }
          }
          
          return updated
        })

        // 새로운 응답이 있다면 메시지로 추가
        if (result.data.response) {
          const newMessage: ExtendedMessage = {
            sender: "agent",
            text: result.data.response,
            isComplete: false,
            isTyping: false
          }
          setMessages(prev => [...prev, newMessage])
        }
        
        console.log("[DEBUG] PHQ-9 응답 처리 성공:", result.data)
      } else {
        throw new Error(result.error || "PHQ-9 응답 처리 실패")
      }
    } catch (error) {
      console.error("PHQ-9 응답 처리 오류:", error)
      alert("설문 응답 처리 중 오류가 발생했습니다. 다시 시도해주세요.")
      
      // 🔥 오류 발생 시 방금 추가한 사용자 메시지 제거
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setPhq9Processing(false)
    }
  }, [userId, conversationId, phq9Processing])

  // 메시지에서 PHQ-9 컴포넌트 파싱
  const parsePHQ9Component = useCallback((text: string) => {
    try {
      const phq9Match = text.match(/PHQ9_BUTTON:({[\s\S]*?})/)
      if (phq9Match) {
        const phq9Data = JSON.parse(phq9Match[1])
        return {
          isPHQ9: true,
          data: phq9Data,
          textWithoutPHQ9: text.replace(/PHQ9_BUTTON:({[\s\S]*?})/, '').trim()
        }
      }
    } catch (error) {
      console.error("PHQ-9 컴포넌트 파싱 오류:", error)
    }
    return { isPHQ9: false, textWithoutPHQ9: text }
  }, [])

  // ===== 로컬 스토리지 관리 함수 =====
  const saveChatTitleMap = useCallback((titleMap: {[key: number]: string}) => {
    if (userId) {
      localStorage.setItem(`chatTitleMap_${userId}`, JSON.stringify(titleMap))
    }
  }, [userId])

  const loadChatTitleMap = useCallback((): {[key: number]: string} => {
    if (userId) {
      const saved = localStorage.getItem(`chatTitleMap_${userId}`)
      return saved ? JSON.parse(saved) : {}
    }
    return {}
  }, [userId])

  // ===== 초기화 및 데이터 가져오기 함수 =====
  const initializeUser = useCallback(() => {
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
      alert("로그인 정보가 없습니다.")
      router.push("/login")
    }
  }, [router])

  const fetchProjects = useCallback(async (currentUserId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/projects?user_id=${currentUserId}`)
      const result = await response.json()
      if (result.success) {
        setProjects(result.data)
      }
    } catch (error) {
      console.error("프로젝트 목록 불러오기 실패:", error)
    }
  }, [])

  const fetchChatHistory = useCallback(async (currentUserId: number) => {
    try {
      const res = await fetch(`${API_BASE_URL}/conversations/${currentUserId}`)
      const data = await res.json()
      if (data.success) {
        const titleMap = loadChatTitleMap()
        
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

        // 각 대화의 마지막 메시지 가져오기
        for (let conv of formatted) {
          try {
            const msgRes = await fetch(`${API_BASE_URL}/conversations/${conv.id}/messages?limit=1`)
            const msgData = await msgRes.json()
            if (msgData.success && msgData.data.length > 0) {
              const lastMsg = msgData.data[0]
              setChatHistory((prev) =>
                prev.map((c) =>
                  c.id === conv.id 
                    ? { ...c, lastMessage: lastMsg.content.slice(0, 30) + (lastMsg.content.length > 30 ? '...' : '') } 
                    : c
                )
              )
            }
          } catch (error) {
            console.error(`대화 ${conv.id}의 마지막 메시지 가져오기 실패:`, error)
          }
        }
      }
    } catch (err) {
      console.error("채팅 기록 불러오기 실패:", err)
    }
  }, [loadChatTitleMap])

  const fetchProjectInfo = useCallback(async (projectId: number) => {
    if (!userId) return
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
  }, [userId])

  // ===== 대화 관련 핸들러 =====
  const startNewConversation = useCallback(async (newAgent: AgentType = "unified_agent") => {
    if (!userId) return
    try {
      const result = await agentApi.createConversation(userId)
      if (!result.success) throw new Error(result.error)

      const newConvId = result.data?.conversationId
      setConversationId(newConvId)
      setMessages([])
      setAgentType(newAgent)
      setCurrentChatId(null)

      const newUrl = `/chat/room?conversation_id=${newConvId}&agent=${newAgent}`
      window.history.replaceState({}, '', newUrl)
      
      await fetchChatHistory(userId)
    } catch (err) {
      console.error("대화 세션 생성 실패:", err)
      alert("새 대화를 시작할 수 없습니다. 다시 시도해주세요.")
    }
  }, [userId, fetchChatHistory])

  const loadPreviousChat = useCallback(async (chatId: number) => {
    try {
      const result = await agentApi.getConversationMessages(chatId)
      if (!result.success || !result.data?.messages) {
        throw new Error(result.error || "메시지를 불러올 수 없습니다")
      }
      
      const loadedMessages = result.data.messages.map((msg: ConversationMessage) => ({
        sender: msg.role === "user" ? "user" : "agent",
        text: msg.content,
        isComplete: true
      })) as ExtendedMessage[]
      
      setMessages(loadedMessages)
      setConversationId(chatId)
      setCurrentChatId(chatId)

      // 세션 저장된 메시지가 더 많다면 그것을 사용
      const savedMessages = loadMessages(chatId)
      if (savedMessages && savedMessages.length > loadedMessages.length) {
        setMessages(savedMessages)
      }

      const newUrl = `/chat/room?conversation_id=${chatId}&agent=${agentType}`
      window.history.replaceState({}, '', newUrl)
    } catch (error) {
      console.error("이전 대화 불러오기 실패:", error)
      alert("대화를 불러올 수 없습니다.")
    }
  }, [agentType])

  // ===== 메시지 전송 핸들러 =====
  const handleSend = useCallback(async (e?: React.FormEvent, messageOverride?: string) => {
    if (e) e.preventDefault()
    if (isSubmitting) return

    const inputToSend = (messageOverride || userInput).trim()
    if (!inputToSend || !userId) return

    // 사업기획서 보기 버튼 숨기기
    setDraftContent(null)

    // 사용자 메시지 먼저 표시
    const userMessage: ExtendedMessage = {
      sender: "user",
      text: inputToSend,
      isComplete: true,
    }
    setMessages((prev) => [...prev, userMessage])

    setIsSubmitting(true)
    setIsLoading(true)

    if (!messageOverride) setUserInput("")

    // "답변 중입니다..." 메시지 추가
    const loadingMessage: ExtendedMessage = {
      sender: "agent",
      text: "",
      isTyping: true,
      isComplete: false,
    }
    setMessages((prev) => [...prev, loadingMessage])

    try {
      let currentConversationId = conversationId || initialConversationId

      // 대화 세션 없으면 생성
      if (!currentConversationId) {
        const result = await agentApi.createConversation(userId)
        if (!result.success) throw new Error(result.error)

        currentConversationId = result.data?.conversationId
        setConversationId(currentConversationId)
        const newUrl = `/chat/room?conversation_id=${currentConversationId}&agent=${agentType}`
        window.history.replaceState({}, '', newUrl)
      }

      const result = await agentApi.sendQuery(
        userId,
        currentConversationId!,
        inputToSend,
        agentType,
        currentProjectId
      )

      if (!result || !result.success || !result.data) {
        throw new Error(result?.error || "응답을 받을 수 없습니다")
      }

      // 사업기획서 여부 확인
      const isFinalBusinessPlan =
        result.data.metadata?.type === "final_business_plan" ||
        (result.data.answer.includes("## 1. 창업 아이디어 요약") &&
          result.data.answer.includes("## 2. 시장 조사 요약") &&
          result.data.answer.includes("## 3. 비즈니스 모델"))

      if (isFinalBusinessPlan) {
        setDraftContent(result.data.answer)
        localStorage.setItem("idea_validation_content", result.data.answer)
        localStorage.setItem("user_id", String(userId))
        localStorage.setItem("conversation_id", String(currentConversationId))

        // "답변 중입니다..." 메시지를 사업기획서 알림으로 교체
        setMessages((prev) => {
          const updated = [...prev]
          const idx = updated.findIndex((m) => m.isTyping)
          if (idx !== -1) {
            updated[idx] = { sender: "agent", text: "📄 사업기획서가 도착했습니다. '사업 기획서 보기' 버튼을 눌러 확인하세요.", isTyping: false, isComplete: true }
          } else {
            updated.push({ sender: "agent", text: "📄 사업기획서가 도착했습니다. '사업 기획서 보기' 버튼을 눌러 확인하세요.", isTyping: false, isComplete: true })
          }
          return updated
        })
      } else {
        // "답변 중입니다..." 메시지를 실제 응답으로 교체
        setMessages((prev) => {
          const updated = [...prev]
          const idx = updated.findIndex((m) => m.isTyping)
          if (idx !== -1) {
            updated[idx] = { sender: "agent", text: result.data.answer, isTyping: false, isComplete: false }
          } else {
            updated.push({ sender: "agent", text: result.data.answer, isTyping: false, isComplete: false })
          }
          return updated
        })
      }

      // 채팅 히스토리 갱신
      await fetchChatHistory(userId)
    } catch (error) {
      console.error("응답 실패:", error)
      alert("서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")

      // 로딩 메시지 제거
      setMessages((prev) =>
        prev.filter((msg) => !(msg.sender === "agent" && msg.isTyping))
      )

      // 입력 복원
      if (!messageOverride) setUserInput(inputToSend)
    } finally {
      setIsSubmitting(false)
      setIsLoading(false)
    }
  }, [userId, conversationId, initialConversationId, userInput, agentType, currentProjectId, isSubmitting, fetchChatHistory])

  const handleTypingComplete = useCallback((messageIndex: number) => {
    setMessages(prev => 
      prev.map((msg, idx) => 
        idx === messageIndex ? { ...msg, isComplete: true } : msg
      )
    )
  }, [])

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setUserInput(e.target.value)
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      const scrollHeight = textareaRef.current.scrollHeight
      const maxHeight = 120
      textareaRef.current.style.height = Math.min(scrollHeight, maxHeight) + "px"
    }
  }, [])

  const handleExampleClick = useCallback((text: string) => {
    if (!userId || isSubmitting) {
      alert("로그인 정보가 없습니다. 다시 로그인해주세요.")
      return
    }
    setUserInput(text)
  }, [userId, isSubmitting])

  // ===== 채팅 히스토리 관련 핸들러 =====
  const handleEditChatTitle = useCallback((chatId: number, newTitle: string) => {
    const newTitleMap = { ...chatTitleMap, [chatId]: newTitle }
    setChatTitleMap(newTitleMap)
    saveChatTitleMap(newTitleMap)
    
    setChatHistory(prev => 
      prev.map(chat => 
        chat.id === chatId ? { ...chat, title: newTitle } : chat
      )
    )
  }, [chatTitleMap, saveChatTitleMap])

  const handleDeleteChat = useCallback(async (chatId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations/${chatId}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        setChatHistory(prev => prev.filter(chat => chat.id !== chatId))
        
        if (currentChatId === chatId || conversationId === chatId) {
          setCurrentChatId(null)
          setConversationId(null)
          setMessages([])
          router.push('/chat/room')
        }
        
        const newTitleMap = { ...chatTitleMap }
        delete newTitleMap[chatId]
        setChatTitleMap(newTitleMap)
        saveChatTitleMap(newTitleMap)
      }
    } catch (error) {
      console.error('대화 삭제 실패:', error)
      alert('대화 삭제에 실패했습니다.')
    }
  }, [currentChatId, conversationId, chatTitleMap, saveChatTitleMap, router])

  // ===== 프로젝트 관련 핸들러 =====
  const handleCreateProject = useCallback(async (projectData: { title: string; description: string; category: string }) => {
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
        await fetchProjects(userId)
        setShowProjectModal(false)
      } else {
        alert(`프로젝트 생성 실패: ${result.error}`)
      }
    } catch (error) {
      console.error("프로젝트 생성 오류:", error)
      alert("프로젝트 생성 중 오류가 발생했습니다.")
    }
  }, [userId, fetchProjects])

  const handleUpdateProject = useCallback(async (projectData: { title: string; description: string; category: string }) => {
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
        await fetchProjects(userId)
        setShowProjectModal(false)
        setEditingProject(null)
      } else {
        alert(`수정 실패: ${result.error}`)
      }
    } catch (error) {
      console.error("프로젝트 수정 오류:", error)
      alert("프로젝트 수정 중 오류가 발생했습니다.")
    }
  }, [editingProject, userId, fetchProjects])

  const handleDeleteProject = useCallback(async (projectId: number) => {
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
  }, [currentProjectId])

  const handleAddProject = useCallback(() => {
    setEditingProject(null)
    setShowProjectModal(true)
  }, [])

  const handleEditProject = useCallback((project: Project) => {
    setEditingProject(project)
    setShowProjectModal(true)
  }, [])

  const handleSelectProject = useCallback(async (projectId: number) => {
    router.push(`/chat/projects/${projectId}`)
  }, [router])

  // ===== 사이드바 관련 핸들러 =====
  const handleSidebarSelect = useCallback(async (type: string) => {
    try {
      if (type === "home") {
        router.push("/chat")
        return
      }
      setAgentType(type as AgentType)
      setMessages([])
      setConversationId(null)
      setCurrentChatId(null)
      window.history.replaceState({}, '', `/chat/room?agent=${type}`)
    } catch (error) {
      console.error("에이전트 변경 실패:", error)
      alert("에이전트 변경에 실패했습니다. 다시 시도해주세요.")
    }
  }, [router])

  const handleNewChat = useCallback(() => {
    if (isSubmitting) return
    
    setCurrentChatId(null)
    setConversationId(null)
    setMessages([])
    window.history.replaceState({}, '', `/chat/room?agent=${agentType}`)
  }, [isSubmitting, agentType])

  // ===== 피드백 관련 핸들러 =====
  const openFeedbackModal = useCallback((type: "up" | "down", idx: number) => {
    setRating(type === "up" ? 5 : 1)
    setComment(`message_index_${idx}`)
    setShowFeedbackModal(true)
  }, [])

  const handleFeedbackSubmit = useCallback(async () => {
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
  }, [conversationId, userId, rating, comment, category])

    const scrollToBottomInstant = useCallback(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: "auto", // 즉시 스크롤 (애니메이션 없음)
        block: "end" 
      })
    }
  }, [])

  // throttle 함수 구현 (성능 최적화)
  const throttle = useCallback((func: Function, delay: number) => {
    let timeoutId: NodeJS.Timeout | null = null
    let lastExecTime = 0
    
    return function (...args: any[]) {
      const currentTime = Date.now()
      
      if (currentTime - lastExecTime > delay) {
        func(...args)
        lastExecTime = currentTime
      } else {
        if (timeoutId) clearTimeout(timeoutId)
        timeoutId = setTimeout(() => {
          func(...args)
          lastExecTime = Date.now()
        }, delay - (currentTime - lastExecTime))
      }
    }
  }, [])

  // throttled 스크롤 함수
  const throttledScroll = useCallback(
    throttle(() => {
      scrollToBottomInstant()
    }, 100), // 100ms마다 최대 1번만 스크롤
    [scrollToBottomInstant]
  )

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
  }, [initializeUser])

  // 사용자 ID가 설정된 후 초기화 (중복 실행 방지)
  useEffect(() => {
    if (userId && !initializeRef.current) {
      initializeRef.current = true
      
      const titleMap = loadChatTitleMap()
      setChatTitleMap(titleMap)
      
      setIsInitialized(true)
      
      const initializeData = async () => {
        try {
          const promises = [fetchProjects(userId), fetchChatHistory(userId)]
          
          if (initialConversationId && !initialQuestion) {
            promises.push(loadPreviousChat(initialConversationId))
          }
          
          if (initialProjectId) {
            promises.push(fetchProjectInfo(initialProjectId))
          }
          
          await Promise.all(promises)
        } catch (error) {
          console.error("초기화 중 오류:", error)
        } finally {
          initializeRef.current = false
        }
      }
      
      initializeData()
    }
  }, [userId, loadChatTitleMap, fetchProjects, fetchChatHistory, loadPreviousChat, fetchProjectInfo, initialConversationId, initialQuestion, initialProjectId])

  // 메시지 변경 시 세션 저장
  useEffect(() => {
    if (conversationId && messages.length > 0) {
      saveMessages(conversationId, messages)
    }
  }, [messages, conversationId])

  // 초기 질문 자동 전송
  useEffect(() => {
    const sendInitialQuestion = async () => {
      if (
        initialQuestion && 
        userId && 
        messages.length === 0 && 
        !isSubmitting &&
        isInitialized
      ) {
        console.log("[DEBUG] 초기 질문 자동 전송:", initialQuestion)

        const newUrl = initialConversationId
          ? `/chat/room?conversation_id=${initialConversationId}&agent=${agentType}`
          : `/chat/room?agent=${agentType}`
        window.history.replaceState({}, '', newUrl)

        await handleSend(undefined, initialQuestion)
      }
    }
    
    sendInitialQuestion()
  }, [initialQuestion, userId, messages.length, isSubmitting, isInitialized, initialConversationId, agentType, handleSend])

  // 페이지 로드 시 messages 복원
  useEffect(() => {
    if (conversationId && messages.length === 0) {
      const saved = loadMessages(conversationId)
      if (saved && saved.length > 0) {
        setMessages(saved)
      }
    }
  }, [conversationId, messages.length])

  // ===== JSX 렌더링 =====
  return (
    <div className="flex h-screen overflow-hidden bg-white">
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

      {/* 메인 컨테이너 */}
      <div className={`flex-1 min-w-0 flex flex-col relative transition-all duration-300 ${sidebarExpanded ? 'ml-64' : 'ml-14'} bg-white`}>
        {/* 헤더 */}
        <div className="bg-white px-6 py-4 flex items-center justify-between">
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
                <div className="flex space-x-3 mb-6 overflow-x-auto scrollbar-hide pb-2">
                  {getCurrentAgentExamples(agentType).map((item, idx) => (
                    <Card
                      key={idx}
                      className="min-w-[280px] cursor-pointer bg-white flex-shrink-0 transition-all duration-200 hover:bg-green-50 hover:shadow-lg hover:border-green-300 border border-gray-200"
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
            <div className="space-y-3">
              {messages.map((msg, idx) => (
                <div
                  key={`${idx}-${msg.sender}-${msg.text.slice(0, 20)}`}
                  className={`flex items-start ${msg.sender === "user" ? "justify-end" : ""}`}
                >
                  {/* 사용자 메시지 */}
                  {msg.sender === "user" ? (
                    <div className="flex flex-row-reverse items-end ml-auto space-x-reverse space-x-2 max-w-[80%]">
                      <div className="inline-block overflow-wrap-break-word p-0.5">
                        <div className="bg-green-50 px-4 py-2 rounded-2xl whitespace-pre-wrap leading-tight">
                          {msg.text}
                        </div>
                      </div>
                    </div>
                  ) : (
                    /* AI 응답 메시지 */
                    <div className="flex flex-col space-y-2 max-w-[80%]">
                      <div className="flex items-end space-x-2">
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
                          <div className="bg-white text-gray-800 px-4 py-3 rounded-2xl whitespace-pre-wrap leading-relaxed">
                            {/* 로딩 중일 때 */}
                            {msg.isTyping ? (
                              <TypingAnimation />
                            ) : (
                              /* 타이핑 애니메이션 또는 완성된 텍스트 */
                              (() => {
                                const phq9Parse = parsePHQ9Component(msg.text)
                                
                                return msg.isComplete ? (
                                  <div className="!leading-snug">
                                    {/* 일반 텍스트 부분 */}
                                    {phq9Parse.textWithoutPHQ9 && (
                                      <ReactMarkdown
                                        remarkPlugins={[remarkGfm]}
                                        components={{
                                          p: ({ children }) => <p className="!m-0 !p-0 !leading-snug">{children}</p>,
                                          ul: ({ children }) => <ul className="!m-0 !ml-4 !p-0 !leading-snug">{children}</ul>,
                                          ol: ({ children }) => <ol className="!m-0 !ml-4 !p-0 !leading-snug">{children}</ol>,
                                          li: ({ children }) => <li className="!m-0 !p-0 !leading-snug">{children}</li>,
                                          h1: ({ children }) => <h1 className="!text-xl !font-bold !m-0 !p-0 !leading-snug">{children}</h1>,
                                          h2: ({ children }) => <h2 className="!text-lg !font-bold !m-0 !p-0 !leading-snug">{children}</h2>,
                                          h3: ({ children }) => <h3 className="!text-base !font-bold !m-0 !p-0 !leading-snug">{children}</h3>,
                                          strong: ({ children }) => <strong className="!font-semibold !m-0 !p-0">{children}</strong>,
                                          blockquote: ({ children }) => <blockquote className="!border-l-4 !border-gray-300 !pl-3 !m-0 !italic !leading-snug">{children}</blockquote>,

                                          table: ({ children }) => (
                                            <div className="overflow-x-auto my-4">
                                              <table className="min-w-full border-collapse border border-gray-300 text-sm">
                                                {children}
                                              </table>
                                            </div>
                                          ),
                                          thead: ({ children }) => (
                                            <thead className="bg-green-50">
                                              {children}
                                            </thead>
                                          ),
                                          tbody: ({ children }) => (
                                            <tbody className="bg-white divide-y divide-gray-200">
                                              {children}
                                            </tbody>
                                          ),
                                          tr: ({ children }) => (
                                            <tr className="hover:bg-gray-50">
                                              {children}
                                            </tr>
                                          ),
                                          th: ({ children }) => (
                                            <th className="px-3 py-2 text-left font-semibold text-gray-900 border border-gray-300 bg-green-100">
                                              {children}
                                            </th>
                                          ),
                                          td: ({ children }) => (
                                            <td className="px-3 py-2 text-gray-700 border border-gray-300">
                                              {children}
                                            </td>
                                          ),
                                          
                                          // 코드 블록
                                          code: ({ node, inline, className, children, ...props }: any) => 
                                            inline ? (
                                              <code className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono" {...props}>
                                                {children}
                                              </code>
                                            ) : (
                                              <pre className="bg-gray-100 p-3 rounded-lg overflow-x-auto my-2">
                                                <code className="text-sm font-mono" {...props}>
                                                  {children}
                                                </code>
                                              </pre>
                                            )
                                        }}
                                      >
                                        {phq9Parse.textWithoutPHQ9}
                                      </ReactMarkdown>
                                    )}
                                    
                                    {/* PHQ-9 버튼 컴포넌트 */}
                                    {phq9Parse.isPHQ9 && (
                                      <PHQ9ButtonComponent
                                        question={phq9Parse.data}
                                        onResponse={handlePHQ9Response}
                                        isDisabled={phq9Parse.data.isDisabled || phq9Processing}
                                      />
                                    )}
                                  </div>
                                ) : (
                                  <TypingText 
                                    text={phq9Parse.textWithoutPHQ9 || msg.text} 
                                    speed={20}
                                    onComplete={() => handleTypingComplete(idx)}
                                    onTextUpdate={throttledScroll}
                                  />
                                )
                              })()
                            )}
                          </div>
                        </div>
                      </div>

                      {/* 피드백 버튼들 */}
                      {msg.isComplete && !msg.isTyping && (
                        <div className="flex items-center space-x-2 pl-[52px]">
                          <button
                            className="flex items-center justify-center w-8 h-8 rounded-full hover:bg-gray-100 transition-colors"
                            onClick={() => openFeedbackModal("up", idx)}
                            title="좋아요"
                          >
                            <ThumbsUp className="w-4 h-4 text-gray-600" />
                          </button>
                          <button
                            className="flex items-center justify-center w-8 h-8 rounded-full hover:bg-gray-100 transition-colors"
                            onClick={() => openFeedbackModal("down", idx)}
                            title="싫어요"
                          >
                            <ThumbsDown className="w-4 h-4 text-gray-600" />
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {/* 스크롤 앵커 */}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {draftContent && (
            <div className="mt-4 flex justify-center">
              <Button
                onClick={() => setShowDraftPreview(true)}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                사업 기획서 보기
              </Button>
            </div>
          )}

          {/* 하단 입력창 */}
          <div className="w-full max-w-3xl mx-auto bg-white p-6">
            <form onSubmit={handleSend}>
              <div className="relative">
                <Textarea
                  ref={textareaRef}
                  value={userInput}
                  onChange={handleInputChange}
                  placeholder="메시지를 입력하세요..."
                  className="w-full resize-none overflow-hidden rounded-xl border-2 border-gray-200 focus:border-gray-200 focus:ring-0 focus:outline-none focus-visible:outline-none focus-visible:ring-0 pr-12 min-h-[80px] py-4 shadow-none"
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
                  className="absolute bottom-2 right-2 w-9 h-9 rounded-full bg-green-600 hover:bg-green-700 shadow-lg disabled:opacity-50"
                  disabled={!userInput.trim() || isSubmitting || isLoading}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </form>
            
            {/* 하단 안내 문구 */}
            <div className="text-center mt-2">
              <p className="text-xs text-gray-500">
                TinkerBell은 실수를 할 수 있습니다. 중요한 정보는 재차 확인하세요.
              </p>
            </div>
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
    {showDraftPreview && (
        <DraftPreviewModal
          userId={userId || ""}
          content={draftContent || ""}
          onClose={() => setShowDraftPreview(false)}
        />
      )}
    </div>
  )
}