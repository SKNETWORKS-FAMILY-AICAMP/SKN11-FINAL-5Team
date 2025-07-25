"use client"

import React from "react"
import { useState, useEffect, useRef } from "react"
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

// ===== PHQ-9 상태 관리 유틸리티 =====
const PHQ9_STORAGE_KEY = 'phq9_session_state';

interface PHQ9SessionState {
  conversationId: number;
  userId: number;
  isActive: boolean;
  currentQuestionIndex: number;
  responses: number[];
  isCompleted: boolean;
  startTime: number;
}

const PHQ9_QUESTIONS = [
  "일 또는 여가활동을 하는데 흥미나 즐거움을 느끼지 못함",
  "기분이 가라앉거나, 우울하거나, 희망이 없다고 느낌", 
  "잠이 들거나 계속 잠을 자는 것이 어려움, 또는 잠을 너무 많이 잠",
  "피곤하다고 느끼거나 기운이 거의 없음",
  "입맛이 없거나 과식을 함",
  "자신을 부정적으로 봄 — 혹은 자신이 실패자라고 느끼거나 자신 또는 가족을 실망시켰다고 느낌",
  "신문을 읽거나 텔레비전 보는 것과 같은 일에 집중하는 것이 어려움",
  "다른 사람들이 주목할 정도로 너무 느리게 움직이거나 말을 함. 또는 그 반대로 평상시보다 많이 움직여서 가만히 앉아 있을 수 없었음",
  "자신이 죽는 것이 더 낫다고 생각하거나 어떤 식으로든 자신을 해칠 것이라고 생각함"
];

const savePHQ9State = (state: PHQ9SessionState) => {
  try {
    sessionStorage.setItem(PHQ9_STORAGE_KEY, JSON.stringify(state));
  } catch (error) {
    console.error('PHQ-9 상태 저장 실패:', error);
  }
};

const loadPHQ9State = (conversationId: number, userId: number): PHQ9SessionState | null => {
  try {
    const saved = sessionStorage.getItem(PHQ9_STORAGE_KEY);
    if (!saved) return null;
    
    const state: PHQ9SessionState = JSON.parse(saved);
    
    if (state.conversationId === conversationId && state.userId === userId) {
      const now = Date.now();
      if (now - state.startTime < 60 * 60 * 1000) {
        return state;
      }
    }
    
    clearPHQ9State();
    return null;
  } catch (error) {
    console.error('PHQ-9 상태 로드 실패:', error);
    return null;
  }
};

const clearPHQ9State = () => {
  try {
    sessionStorage.removeItem(PHQ9_STORAGE_KEY);
  } catch (error) {
    console.error('PHQ-9 상태 삭제 실패:', error);
  }
};

// ===== 메시지 저장용 상수 및 유틸 =====
const MESSAGES_STORAGE_KEY = 'chat_messages';

const saveMessages = (conversationId: number, messages: ExtendedMessage[]) => {
  try {
    sessionStorage.setItem(MESSAGES_STORAGE_KEY + conversationId, JSON.stringify(messages));
  } catch (error) {
    console.error('메시지 저장 실패:', error);
  }
};

const loadMessages = (conversationId: number): ExtendedMessage[] | null => {
  try {
    const saved = sessionStorage.getItem(MESSAGES_STORAGE_KEY + conversationId);
    return saved ? JSON.parse(saved) : null;
  } catch (error) {
    console.error('메시지 로드 실패:', error);
    return null;
  }
};

// ===== PHQ-9 키워드 감지 함수 =====
const detectPHQ9Keywords = (text: string): boolean => {
  const phq9Keywords = [
    "PHQ-9", "우울증 자가진단", "PHQ 테스트", "설문 시작", "자가진단 시작", "설문", "PHQ", "설문", "자가진단", "진단", "검사", "테스트", "하고싶", "받고싶"
  ];
  
  const normalizedText = text.toLowerCase().replace(/\s+/g, '');
  
  return phq9Keywords.some(keyword => 
    normalizedText.includes(keyword.toLowerCase().replace(/\s+/g, ''))
  );
};

const detectRejectKeywords = (text: string): boolean => {
  const rejectKeywords = [
    "싫어", "싫다", "안해", "안할래", "안하고싶", "안하고 싶",
    "필요없", "필요 없", "관심없", "관심 없", "그만", "중단",
    "취소", "멈춰", "스톱", "stop", "아니", "아니야", "거절",
    "나중에", "다음에", "미뤄", "미룰", "패스", "건너뛰"
  ];
  
  const normalizedText = text.toLowerCase().replace(/\s+/g, '');
  
  return rejectKeywords.some(keyword => 
    normalizedText.includes(keyword.toLowerCase().replace(/\s+/g, ''))
  );
};

// ===== 타이핑 애니메이션 컴포넌트 =====
function TypingAnimation() {
  return (
    <div className="flex items-center space-x-1">
      <div className="flex space-x-1">
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
      </div>
    </div>
  )
}

// ===== 타이핑 텍스트 컴포넌트 =====
function TypingText({ text, speed = 30, onComplete }: { text: string, speed?: number, onComplete?: () => void }) {
  const [displayedText, setDisplayedText] = useState("")
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayedText(prev => prev + text[currentIndex])
        setCurrentIndex(prev => prev + 1)
      }, speed)

      return () => clearTimeout(timer)
    } else if (onComplete) {
      onComplete()
    }
  }, [currentIndex, text, speed, onComplete])

  useEffect(() => {
    setDisplayedText("")
    setCurrentIndex(0)
  }, [text])

  return (
    <div className="whitespace-pre-wrap leading-relaxed">
      <ReactMarkdown>{displayedText}</ReactMarkdown>
      {currentIndex < text.length && (
        <span className="inline-block w-0.5 h-4 bg-gray-400 ml-1 animate-pulse"></span>
      )}
    </div>
  )
}

// ===== PHQ-9 버튼 컴포넌트 =====
const PHQ9ButtonComponent = React.memo(({ 
  question, 
  onResponse 
}: { 
  question: any, 
  onResponse: (value: number) => void 
}) => {
  console.log("[DEBUG] PHQ9ButtonComponent 렌더링, question:", question);
  
  const responseOptions = [
    { value: 0, label: "전혀 그렇지 않다" },
    { value: 1, label: "며칠 정도 그렇다" },
    { value: 2, label: "일주일 이상 그렇다" },
    { value: 3, label: "거의 매일 그렇다" }
  ];

  return (
    <div className="space-y-4 mt-4">
      <div className="bg-green-50 p-4 rounded-lg border border-green-200">
        <div className="flex justify-between items-center mb-3">
          <span className="text-sm font-medium text-green-600">
            진행률: {question.progress}
          </span>
          <span className="text-sm text-gray-500">PHQ-9 설문</span>
        </div>
        
        <h4 className="text-lg font-semibold text-gray-800 mb-4 leading-relaxed">
          지난 2주 동안, <span className="text-green-700">{question.text}</span>
        </h4>
        
        <div className="space-y-2">
          {responseOptions.map((option) => (
            <Button
              key={option.value}
              onClick={() => {
                console.log("[DEBUG] 버튼 클릭:", option.value);
                onResponse(option.value);
              }}
              className="w-full p-3 text-left justify-start border-2 transition-all duration-200 bg-white hover:bg-green-50 border-green-300 text-gray-800 font-medium hover:border-green-400"
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
  );
});

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

interface ExtendedMessage extends Message {
  isTyping?: boolean
  isComplete?: boolean
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
function ProjectMenu({ project, onEdit, onDelete }: { project: Project, onEdit: (project: Project) => void, onDelete: (projectId: number) => void }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="icon"
        className="w-4 h-4 p-0 text-gray-400 hover:text-gray-800 ml-1 opacity-0 group-hover:opacity-100"
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen((prev) => !prev);
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
                e.stopPropagation();
                onEdit(project);
                setIsOpen(false);
              }}
            >
              이름 변경
            </button>
            <button
              className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-100"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(project.id);
                setIsOpen(false);
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
              setIsOpen((prev) => !prev);
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
    router.push("/workspace");
    setIsMenuOpen(false);
  };

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
          <div className="space-y-1 mb-4">
            {menuItems.map((item, idx) => (
              <div
                key={idx}
                onClick={item.action}
                className={`flex items-center gap-2 px-3 py-2 text-sm rounded-lg cursor-pointer transition-all duration-200 text-gray-800 hover:bg-green-100`}
              >
                <div className="w-8 h-8 rounded-full flex items-center justify-center bg-white shadow-sm">
                  <Image
                    src={item.icon || "/placeholder.svg"}
                    alt={item.label}
                    width={20}
                    height={20}
                    className="w-5 h-5"
                  />
                </div>
                <span className="font-medium truncate">{item.label}</span>
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
      <div className="flex-1 min-h-0 overflow-y-auto">
        {isExpanded && (
          <>
            {/* 프로젝트 섹션 */}
            <div className="mb-4">
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
                      <div className="text-sm font-medium text-gray-800 truncate" title={project.title}>
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
            <div className="mb-4">
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
                      <div className="text-sm font-medium text-gray-800 truncate" title={chat.title}>
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

  const openFeedbackModal = (type: "up" | "down", idx: number) => {
    setRating(type === "up" ? 5 : 1);
    setComment(`message_index_${idx}`);
    setShowFeedbackModal(true);
  };

  // 중복 실행 방지를 위한 ref
  const initializeRef = useRef(false);

  // ===== PHQ-9 설문 상태 관리 =====
  const [phq9Active, setPhq9Active] = useState(false);
  const [phq9Question, setPhq9Question] = useState<any>(null);
  const [phq9Responses, setPhq9Responses] = useState<number[]>([]);
  const [phq9Completed, setPhq9Completed] = useState(false);
  const [forceUpdate, setForceUpdate] = useState(0);

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

  // ===== PHQ-9 상태 복원 함수 =====
  const restorePHQ9State = (conversationId: number, userId: number) => {
    const savedState = loadPHQ9State(conversationId, userId);
    
    if (savedState && savedState.isActive && !savedState.isCompleted) {
      console.log("[DEBUG] PHQ-9 상태 복원:", savedState);
      
      setPhq9Active(true);
      setPhq9Responses(savedState.responses);
      setPhq9Completed(savedState.isCompleted);
      
      // 현재 질문 설정
      if (savedState.currentQuestionIndex < PHQ9_QUESTIONS.length) {
        setPhq9Question({
          index: savedState.currentQuestionIndex,
          text: PHQ9_QUESTIONS[savedState.currentQuestionIndex],
          progress: `${savedState.currentQuestionIndex + 1}/9`,
          options: [
            {"value": 0, "label": "전혀 그렇지 않다"},
            {"value": 1, "label": "며칠 정도 그렇다"},
            {"value": 2, "label": "일주일 이상 그렇다"},
            {"value": 3, "label": "거의 매일 그렇다"}
          ]
        });
        
        // 현재 질문을 메시지로 추가 (이미 있는지 확인)
        setTimeout(() => {
          setMessages(prev => {
            const currentQuestionText = `**문항 ${savedState.currentQuestionIndex + 1}/9**: 지난 2주 동안, ${PHQ9_QUESTIONS[savedState.currentQuestionIndex]}`;
            const lastMessage = prev[prev.length - 1];
            
            // 마지막 메시지가 현재 질문이 아닌 경우에만 추가
            if (!lastMessage || !lastMessage.text.includes(currentQuestionText)) {
              return [...prev, {
                sender: "agent",
                text: currentQuestionText,
                isComplete: true
              }];
            }
            return prev;
          });
        }, 100);
      }
      
      return true;
    }
    
    return false;
  };

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
      setConversationId(null)
      setMessages([])
      setAgentType(newAgent)
      setCurrentChatId(null)

      const newUrl = `/chat/room?conversation_id=${newConvId}&agent=${newAgent}`
      window.history.replaceState({}, '', newUrl)
      
      //await fetchChatHistory(userId)
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
      
      const loadedMessages = result.data.messages.map((msg: ConversationMessage) => ({
        sender: msg.role === "user" ? "user" : "agent",
        text: msg.content,
        isComplete: true
      }))
      
      setMessages(loadedMessages)
      setConversationId(chatId)
      setCurrentChatId(chatId)

      const savedMessages = loadMessages(chatId);
      if (savedMessages && savedMessages.length > loadedMessages.length) {
        setMessages(savedMessages);
      }

      
      // PHQ-9 상태 복원 시도
      if (userId) {
        restorePHQ9State(chatId, userId);
      }
      
      const newUrl = `/chat/room?conversation_id=${chatId}&agent=${agentType}`
      window.history.replaceState({}, '', newUrl)
    } catch (error) {
      console.error("기존 대화 로드 실패:", error)
      alert("대화를 불러오는데 실패했습니다.")
    }
  }

  // ===== PHQ-9 DB 저장 함수 =====
  const savePHQ9ToDatabase = async (totalScore: number, responses: number[]) => {
    try {
      console.log("[DEBUG] PHQ-9 결과 DB 저장 시작:", totalScore, responses);
      
      let level = 1;
      if (totalScore >= 20) {
        level = 5;
      } else if (totalScore >= 15) {
        level = 4;
      } else if (totalScore >= 10) {
        level = 3;
      } else if (totalScore >= 5) {
        level = 2;
      }
      
      console.log("[DEBUG] 계산된 level:", level);
      
      const response = await fetch(`${API_BASE_URL}/phq9/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          conversation_id: conversationId,
          scores: responses
        }),
      });
      
      console.log("[DEBUG] API 응답 상태:", response.status);
      const data = await response.json();
      console.log("[DEBUG] API 응답 데이터:", data);
      
      if (data.success) {
        console.log("[DEBUG] PHQ-9 결과 DB 저장 성공");
      } else {
        console.log("[DEBUG] PHQ-9 결과 DB 저장 실패:", data.error);
      }
    } catch (error) {
      console.error("[DEBUG] PHQ-9 DB 저장 에러:", error);
    }
  };

  // ===== PHQ-9 설문 핸들러 =====
  // startPHQ9Survey 함수 수정
  const startPHQ9Survey = async () => {
    console.log("[DEBUG] startPHQ9Survey 함수 시작");
    
    if (!conversationId || !userId) {
      console.log("[DEBUG] conversationId 또는 userId가 없음");
      return;
    }
    
    try {
      // 먼저 기존 상태 확인
      if (restorePHQ9State(conversationId, userId)) {
        console.log("[DEBUG] 기존 PHQ-9 세션 복원됨");
        return;
      }
      
      console.log("[DEBUG] 새로운 PHQ-9 세션 시작");
      
      setAgentType("mentalcare");
      setPhq9Active(true);
      setPhq9Responses([]);
      setPhq9Completed(false);
      
      // 설문 시작 안내와 첫 번째 질문을 하나의 메시지로 통합
      const firstQuestion = {
        index: 0,
        text: PHQ9_QUESTIONS[0],
        progress: "1/9",
        options: [
          {"value": 0, "label": "전혀 그렇지 않다"},
          {"value": 1, "label": "며칠 정도 그렇다"},
          {"value": 2, "label": "일주일 이상 그렇다"},
          {"value": 3, "label": "거의 매일 그렇다"}
        ]
      };

      // phq9Question 상태 설정
      setPhq9Question(firstQuestion);
      setForceUpdate(prev => prev + 1);
      
      
      const combinedMessage: ExtendedMessage = {
        sender: "agent",
        text: `📋 **PHQ-9 우울증 자가진단 설문을 시작합니다**\n\n총 9개 문항으로 구성되어 있습니다.\n각 문항에 대해 지난 2주간의 경험을 바탕으로 답변해 주세요.\n\n**문항 1/9**: 지난 2주 동안, ${PHQ9_QUESTIONS[0]}`,
        isComplete: false
      };
      setMessages((prev) => [...prev, combinedMessage]);
      
      // 세션 상태 저장
      const sessionState: PHQ9SessionState = {
        conversationId,
        userId,
        isActive: true,
        currentQuestionIndex: 0,
        responses: [],
        isCompleted: false,
        startTime: Date.now()
      };
      
      savePHQ9State(sessionState);
      
    } catch (error) {
      console.error("[DEBUG] PHQ-9 시작 에러:", error);
      alert("설문을 시작할 수 없습니다.");
    }
  };

  // handlePHQ9Response 함수 수정
  const handlePHQ9Response = async (value: number) => {
    console.log("[DEBUG] handlePHQ9Response 시작, value:", value);
    
    if (!conversationId || !userId) {
      console.log("[DEBUG] conversationId 또는 userId 없음");
      return;
    }
    
    try {
      // 사용자 응답을 채팅에 표시
      const responseLabels = ["전혀 그렇지 않다", "며칠 정도 그렇다", "일주일 이상 그렇다", "거의 매일 그렇다"];
      const responseText = `${value}: ${responseLabels[value]}`;
      const userResponseMessage: ExtendedMessage = {
        sender: "user",
        text: responseText,
        isComplete: true
      };
      setMessages(prev => [...prev, userResponseMessage]);
      
      // 응답 저장
      const newResponses = [...phq9Responses, value];
      setPhq9Responses(newResponses);
      
      // 세션 상태 업데이트
      const sessionState: PHQ9SessionState = {
        conversationId,
        userId,
        isActive: true,
        currentQuestionIndex: newResponses.length,
        responses: newResponses,
        isCompleted: false,
        startTime: Date.now()
      };
      
      if (newResponses.length >= 9) {
        console.log("[DEBUG] 설문 완료!");
        
        // 완료 상태로 업데이트
        sessionState.isCompleted = true;
        sessionState.isActive = false;
        
        setPhq9Active(false);
        setPhq9Question(null);
        setPhq9Completed(true);
        
        // 결과 계산 및 표시
        const totalScore = newResponses.reduce((sum, score) => sum + score, 0);
        let severity, recommendation;
        
        if (totalScore <= 4) {
          severity = "최소 우울";
          recommendation = "현재 우울 증상은 최소 수준입니다.";
        } else if (totalScore <= 9) {
          severity = "경미한 우울";
          recommendation = "경미한 우울 증상이 있습니다. 생활 습관 개선을 권합니다.";
        } else if (totalScore <= 14) {
          severity = "중등도 우울";
          recommendation = "전문가 상담을 권합니다.";
        } else if (totalScore <= 19) {
          severity = "중증 우울";
          recommendation = "전문의 상담을 강력히 권합니다.";
        } else {
          severity = "최중증 우울";
          recommendation = "즉시 전문의 상담을 받으시기 바랍니다.";
        }
        
        // DB에 결과 저장
        await savePHQ9ToDatabase(totalScore, newResponses);
        
        const completionMessage: ExtendedMessage = {
          sender: "agent",
          text: `✅ **PHQ-9 설문 완료**\n\n**총점: ${totalScore}점**\n**평가 결과: ${severity}**\n\n**권장사항**: ${recommendation}`,
          isComplete: true
        };
        setMessages(prev => [...prev, completionMessage]);
        
        // 완료 후 세션 상태 삭제
        setTimeout(() => {
          clearPHQ9State();
        }, 1000);
        
      } else {
        // 다음 질문 설정
        const nextIndex = newResponses.length;
        
        const nextQuestion = {
          index: nextIndex,
          text: PHQ9_QUESTIONS[nextIndex],
          progress: `${nextIndex + 1}/9`,
          options: [
            {"value": 0, "label": "전혀 그렇지 않다"},
            {"value": 1, "label": "며칠 정도 그렇다"},
            {"value": 2, "label": "일주일 이상 그렇다"},
            {"value": 3, "label": "거의 매일 그렇다"}
          ]
        };
        
        // 다음 질문을 메시지로 추가
        const nextQuestionMessage: ExtendedMessage = {
          sender: "agent",
          text: `**문항 ${nextIndex + 1}/9**: 지난 2주 동안, ${PHQ9_QUESTIONS[nextIndex]}`,
          isComplete: true
        };
        setMessages(prev => [...prev, nextQuestionMessage]);
        
        // 상태 업데이트
        setPhq9Question(nextQuestion);
      }
      
      // 세션 상태 저장
      savePHQ9State(sessionState);
      
    } catch (error) {
      console.error("PHQ-9 응답 처리 실패:", error);
      alert("응답 처리에 실패했습니다.");
    }
  };

  // ===== 채팅 관련 핸들러 =====
  const handleSend = async (e?: React.FormEvent, messageOverride?: string) => {
    if (e) e.preventDefault();
    if (isSubmitting) return;

    const inputToSend = (messageOverride || userInput).trim();
    if (!inputToSend || !userId) return;

    // ===== 사용자 메시지 우선 표시 =====
    const userMessage: ExtendedMessage = {
      sender: "user",
      text: inputToSend,
      isComplete: true,
    };
    setMessages((prev) => [...prev, userMessage]);

    // // ===== PHQ-9 활성 상태에서 처리 =====
    // if (phq9Active) {
    //   // 거절 키워드 감지
    //   if (detectRejectKeywords(inputToSend)) {
    //     console.log("[DEBUG] PHQ-9 거절 키워드 감지, 설문 중단");
        
    //     setPhq9Active(false);
    //     setPhq9Question(null);
    //     setPhq9Completed(false);
    //     setPhq9Responses([]);
    //     clearPHQ9State();

    //     // 거절 안내 메시지 추가
    //     const rejectMessage: ExtendedMessage = {
    //       sender: "agent",
    //       text: "알겠습니다. PHQ-9 설문을 중단하겠습니다. 언제든지 다시 설문을 원하시면 말씀해 주세요.",
    //       isComplete: false
    //     };
    //     setMessages((prev) => [...prev, rejectMessage]);
    //     setUserInput("");
    //     return;
    //   }

    //   // 설문 활성 상태에서는 일반 메시지 처리를 차단
    //   console.log("[DEBUG] PHQ-9 설문 활성 상태, 일반 메시지 처리 차단");
    //   const warningMessage: ExtendedMessage = {
    //     sender: "agent",
    //     text: "현재 PHQ-9 설문이 진행 중입니다. 설문 응답 버튼을 선택하거나, 설문을 중단하려면 '취소' 또는 '그만'이라고 입력해주세요.",
    //     isComplete: false
    //   };
    //   setMessages((prev) => [...prev, warningMessage]);
    //   setUserInput("");
    //   return;
    // }

    // // ===== PHQ-9 설문 시작 키워드 감지 =====
    // if (!phq9Active && !phq9Completed && detectPHQ9Keywords(inputToSend)) {
    //   console.log("[DEBUG] PHQ-9 설문 키워드 감지, 설문 시작 준비");
    //   if (!conversationId) {
    //     await startNewConversation("mentalcare");
    //   }
      
    //   // 확인 메시지 표시
    //   const confirmMessage: ExtendedMessage = {
    //     sender: "agent",
    //     text: "PHQ-9 우울증 자가진단 설문을 시작하시겠습니까?\n\n이 설문은 지난 2주간의 우울 증상을 평가하는 9개 문항으로 구성되어 있습니다.\n\n설문을 진행하려면 '네' 또는 '시작'이라고 말씀해 주세요.\n그만두고 싶으시면 '아니요' 또는 '취소'라고 말씀해 주세요.",
    //     isComplete: false
    //   };
    //   setMessages((prev) => [...prev, confirmMessage]);
    //   setUserInput("");
    //   return;
    // }

    // // ===== PHQ-9 설문 시작 확인 처리 =====
    // if (!phq9Active && !phq9Completed && 
    //     (inputToSend.includes("네") || inputToSend.includes("시작") || 
    //     inputToSend.includes("좋아") || inputToSend.includes("응") ||
    //     inputToSend.includes("그래") || inputToSend.includes("ok") ||
    //     inputToSend.includes("OK") || inputToSend.includes("예"))) {
      
    //   console.log("[DEBUG] PHQ-9 시작 확인, 설문 시작");
      
    //   // 즉시 시작하지 않고 약간의 지연 후 시작
    //   setTimeout(() => {
    //     startPHQ9Survey();
    //   }, 300);
      
    //   setUserInput("");
    //   return;
    // }

    // ===== 일반 메시지 처리 =====
    setIsSubmitting(true);
    setIsLoading(true);

    if (!messageOverride) {
      setUserInput("");
    }

    // "답변 중입니다..." 메시지 추가
    const loadingMessage: ExtendedMessage = {
      sender: "agent",
      text: "",
      isTyping: true,
      isComplete: false,
    };
    setMessages((prev) => [...prev, loadingMessage]);

    try {
      let currentConversationId = conversationId || initialConversationId;
      if (!currentConversationId) {
        const result = await agentApi.createConversation(userId);
        if (!result.success) throw new Error(result.error);

        currentConversationId = result.data?.conversationId;
        setConversationId(currentConversationId);
        const newUrl = `/chat/room?conversation_id=${currentConversationId}&agent=${agentType}`;
        window.history.replaceState({}, '', newUrl);
      }

      const result = await agentApi.sendQuery(
        userId,
        currentConversationId!,
        inputToSend,
        agentType,
        currentProjectId
      );

      if (!result || !result.success || !result.data) {
        throw new Error(result?.error || "응답을 받을 수 없습니다");
      }

      // "답변 중입니다..." 메시지를 실제 응답으로 교체
      setMessages((prev) => {
        const updated = [...prev];
        const lastIndex = updated.findIndex(
          (msg) => msg.sender === "agent" && msg.isTyping
        );
        if (lastIndex !== -1) {
          updated[lastIndex] = {
            sender: "agent",
            text: result.data.answer,
            isTyping: false,
            isComplete: false,
          };
        } else {
          updated.push({
            sender: "agent",
            text: result.data.answer,
            isTyping: false,
            isComplete: false,
          });
        }
        return updated;
      });

      await fetchChatHistory(userId);
    } catch (error) {
      console.error("응답 실패:", error);
      alert("서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.");
      setMessages((prev) =>
        prev.filter((msg) => !(msg.sender === "agent" && msg.isTyping))
      );
      if (!messageOverride) setUserInput(inputToSend);
    } finally {
      setIsSubmitting(false);
      setIsLoading(false);
    }
  };

  const handleTypingComplete = (messageIndex: number) => {
    setMessages(prev => 
      prev.map((msg, idx) => 
        idx === messageIndex ? { ...msg, isComplete: true } : msg
      )
    )
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

  const handleExampleClick = (text: string) => {
    if (!userId || isSubmitting) {
      alert("로그인 정보가 없습니다. 다시 로그인해주세요.")
      return
    }
    
    setUserInput(text)
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
        
        if (currentChatId === chatId || conversationId === chatId) {
          setCurrentChatId(null)
          setConversationId(null)
          setMessages([])
          // PHQ-9 상태도 초기화
          setPhq9Active(false)
          setPhq9Question(null)
          setPhq9Responses([])
          setPhq9Completed(false)
          clearPHQ9State()
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
        setAgentType(type as AgentType)
        setMessages([])
        setConversationId(null)
        // PHQ-9 상태 초기화
        setPhq9Active(false)
        setPhq9Question(null)
        setPhq9Responses([])
        setPhq9Completed(false)
        clearPHQ9State()
        window.history.replaceState({}, '', `/chat/room?agent=${type}`)
      } catch (error) {
        console.error("에이전트 변경 실패:", error)
        alert("에이전트 변경에 실패했습니다. 다시 시도해주세요.")
      }
    }

  const handleNewChat = () => {
    if (isSubmitting) return
    
    setCurrentChatId(null)
    setConversationId(null)
    setMessages([])
    setPhq9Active(false)
    setPhq9Question(null)
    setPhq9Responses([])
    setPhq9Completed(false)
    setForceUpdate(0)
    clearPHQ9State()
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

  // 사용자 ID가 설정된 후 초기화 (중복 실행 방지)
  useEffect(() => {
    if (userId && !initializeRef.current) {
      initializeRef.current = true;
      
      const titleMap = loadChatTitleMap();
      setChatTitleMap(titleMap);
      
      if (initialQuestion && !initialConversationId) {
        setUserInput(initialQuestion);
      }
      setIsInitialized(true);
      
      (async () => {
        try {
          const promises = [fetchProjects(userId), fetchChatHistory(userId)];
          
          if (initialConversationId) {
            promises.push(loadPreviousChat(initialConversationId));
          }
          if (currentProjectId) {
            promises.push(fetchProjectInfo(currentProjectId));
          }
          
          await Promise.all(promises);
        } catch (error) {
          console.error("초기화 중 오류:", error);
        } finally {
          initializeRef.current = false;
        }
      })();
    }
  }, [userId]); 

  // ===== 메시지 변경 시 세션 저장 =====
  useEffect(() => {
    if (conversationId && messages.length > 0) {
      saveMessages(conversationId, messages);
    }
  }, [messages, conversationId]);

  // ===== 초기 질문 자동 전송 =====
  useEffect(() => {
    const sendInitialQuestion = async () => {
      if (
        initialQuestion && 
        userId && 
        messages.length === 0 && 
        !isSubmitting
      ) {
        console.log("[DEBUG] 초기 질문 자동 전송:", initialQuestion);

        setIsSubmitting(true);  // 추가: 중복 방지 플래그
        const newUrl = initialConversationId
          ? `/chat/room?conversation_id=${initialConversationId}&agent=${agentType}`
          : `/chat/room?agent=${agentType}`;
        window.history.replaceState({}, '', newUrl);

        await handleSend(undefined, initialQuestion);
        setUserInput(""); // 초기 질문을 비워서 재전송 방지
        setIsSubmitting(false); // 전송 끝나면 해제
      }
    };
    sendInitialQuestion();
  }, [initialQuestion, userId, messages.length]);

  useEffect(() => {
    if (userId && initialConversationId && !initialQuestion) {
      loadPreviousChat(initialConversationId);
    }
  }, [userId, initialConversationId, initialQuestion]);

  // 페이지 로드 시 messages 복원
  useEffect(() => {
    if (conversationId) {
      const saved = loadMessages(conversationId);
      if (saved) {
        setMessages(saved);
      }
    }
  }, [conversationId]);

  useEffect(() => {
    if (userId && !initializeRef.current) {
      initializeRef.current = true;
      
      const titleMap = loadChatTitleMap();
      setChatTitleMap(titleMap);
      
      setIsInitialized(true);
      
      (async () => {
        try {
          const promises = [fetchProjects(userId), fetchChatHistory(userId)];
          
          if (currentProjectId) {
            promises.push(fetchProjectInfo(currentProjectId));
          }
          
          await Promise.all(promises);
        } catch (error) {
          console.error("초기화 중 오류:", error);
        } finally {
          initializeRef.current = false;
        }
      })();
    }
  }, [userId]);

  // PHQ-9 상태 변경 감지
  useEffect(() => {
    console.log("[DEBUG] phq9Question 변경됨:", phq9Question);
    console.log("[DEBUG] phq9Active 상태:", phq9Active);
  }, [phq9Question, phq9Active]);

  // PHQ-9 자동 시작 로직 비활성화
  useEffect(() => {
    // 기존의 자동 시작 로직을 비활성화
    // 이제 키워드 기반으로만 설문이 시작됨
    console.log("[DEBUG] PHQ-9 자동 시작 로직 비활성화됨");
  }, [messages, phq9Active, conversationId, userId]);

  // ===== 페이지 새로고침 시 PHQ-9 상태 복원 =====
  useEffect(() => {
    if (conversationId && userId && messages.length > 0) {
      // 메시지가 로드된 후 PHQ-9 상태 복원 시도
      const restored = restorePHQ9State(conversationId, userId);
      if (restored) {
        console.log("[DEBUG] 페이지 로드 시 PHQ-9 상태 복원됨");
      }
    }
  }, [conversationId, userId, messages.length]);

  useEffect(() => {
    if (userId && !conversationId) {
      console.log("[DEBUG] conversationId가 없어 새 대화 생성");
      startNewConversation(agentType);
    }
  }, [userId, conversationId]);


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

      {/* 메인 컨테이너 - 사이드바 크기에 따라 여백 조정 */}
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
            <div className="space-y-6">
              {messages.map((msg, idx) => (
                <div
                  key={`${idx}-${msg.sender}-${msg.text.slice(0, 20)}`}
                  className={`flex items-start ${msg.sender === "user" ? "justify-end" : ""}`}
                >
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
                              msg.isComplete ? (
                                <ReactMarkdown>{msg.text}</ReactMarkdown>
                              ) : (
                                <TypingText 
                                  text={msg.text} 
                                  speed={20}
                                  onComplete={() => handleTypingComplete(idx)}
                                />
                              )
                            )}
                          </div>
                        </div>
                      </div>

                      {/* PHQ-9 버튼 UI - 마지막 메시지이고 설문이 활성화되었을 때만 표시 */}
                      {msg.sender === "agent" && 
                       phq9Active && 
                       !phq9Completed &&
                       phq9Question && 
                       phq9Question.text &&
                       idx === messages.length - 1 && (
                        <div className="mt-4" key={`phq9-${forceUpdate}`}>
                          <PHQ9ButtonComponent 
                            question={phq9Question}
                            onResponse={handlePHQ9Response}
                          />
                        </div>
                      )}
                      
                      {/* 피드백 버튼들 - PHQ-9가 비활성화일 때만 표시 */}
                      {msg.isComplete && !msg.isTyping && !phq9Active && (
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

          {/* 하단 입력창 */}
          <div className="bg-white p-4">
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
                className="h-full aspect-square rounded-xl bg-green-600 hover:bg-green-700 shadow-lg disabled:opacity-50"
                disabled={!userInput.trim() || isSubmitting || isLoading}
              >
                <Send className="h-5 w-5" />
              </Button>
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
    </div>
  )
}