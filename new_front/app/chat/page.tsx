"use client"

import type React from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import Image from "next/image"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { useState, useEffect } from "react"
import { Search, Menu, Target, TrendingUp, Users, Zap, Heart, User } from "lucide-react"
import { agentApi } from "@/app/api/agent"

const agents = [
  {
    id: "planner",
    name: "사업기획",
    imageSrc: "/icons/3D_사업기획.png",
  },
  {
    id: "marketing",
    name: "마케팅",
    imageSrc: "/icons/3D_마케팅.png",
  },
  {
    id: "crm",
    name: "고객관리",
    imageSrc: "/icons/3D_고객관리.png",
  },
  {
    id: "task",
    name: "업무지원",
    imageSrc: "/icons/3D_업무관리.png",
  },
  {
    id: "mentalcare",
    name: "멘탈케어",
    imageSrc: "/icons/3D_멘탈케어.png",
  },
]


export default function ChatMainPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [input, setInput] = useState("")
  const [user, setUser] = useState<any>(null)
  const [showProfileMenu, setShowProfileMenu] = useState(false)

  // handleLogout 함수도 추가
  const handleLogout = () => {
    localStorage.clear()
    window.location.href = "/login"
  }

  // OAuth 콜백 후 사용자 정보 처리
  useEffect(() => {
    const userId = searchParams.get('user_id')
    const provider = searchParams.get('provider')
    const email = searchParams.get('email')
    const username = searchParams.get('username')
    const error = searchParams.get('error')

    if (error) {
      alert('로그인에 실패했습니다. 다시 시도해주세요.')
      router.push('/login')
      return
    }

    if (userId && provider) {
      const userData = {
        user_id: parseInt(userId),
        provider,
        email: email || '',
        username: username || ''
      }
      
      // localStorage에 사용자 정보 저장
      localStorage.setItem('user', JSON.stringify(userData))
      setUser(userData)
      
      console.log('로그인 성공:', userData)
      
      // URL에서 쇼리 파라미터 제거 (보안)
      const newUrl = window.location.pathname
      window.history.replaceState({}, document.title, newUrl)
    } else {
      // 기존 localStorage에서 사용자 정보 로드
      const savedUser = localStorage.getItem('user')
      if (savedUser) {
        try {
          setUser(JSON.parse(savedUser))
        } catch (e) {
          console.error('사용자 정보 파싱 오류:', e)
          localStorage.removeItem('user')
        }
      }
    }
  }, [searchParams, router])

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;

    try {
      const result = await agentApi.createConversation(user?.user_id || 3);
      if (result.success) {
        const conversationId = result.data?.conversationId;
        // 질문도 쿼리 파라미터에 추가
        router.push(`/chat/room?agent=unified_agent&conversation_id=${conversationId}&question=${encodeURIComponent(text)}`);
      }
    } catch (error) {
      console.error("대화 세션 생성 실패:", error);
      alert("채팅 시작에 실패했습니다. 다시 시도해주세요.");
    }
  };


  const handleAgentClick = (agentId: string) => {
    router.push(`/chat/room?agent=${agentId}`)
  }


  const handleQuickStart = async () => {
    router.push(`/chat/room?agent=unified_agent`)
}

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-yellow-50 to-emerald-50">
      {/* Header */}

      <nav className="px-6 py-4 sticky top-0 bg-white/90 backdrop-blur-sm border-b border-gray-200 z-50">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <Link href="/" className="flex items-center space-x-3">
            <Image
              src="/3D_고양이.png?height=40&width=40"
              alt="TinkerBell Logo"
              width={40}
              height={40}
              className="rounded-full"
            />
            <span className="text-2xl font-bold text-gray-900">TinkerBell</span>
          </Link>

          <div className="hidden md:flex items-center space-x-8">
            <Link href="/#service" className="text-gray-600 hover:text-green-600 transition-colors font-medium">
              서비스 소개
            </Link>
            <Link href="/chat" className="text-gray-600 hover:text-green-600 transition-colors font-medium">
              상담하기
            </Link>
            <Link href="/faq" className="text-gray-600 hover:text-green-600 transition-colors font-medium">
              FAQ
            </Link>
            {user ? (
              <div className="relative">
                <button
                  onClick={() => setShowProfileMenu(!showProfileMenu)}
                  className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center focus:outline-none"
                >
                  <User className="h-4 w-4 text-green-600" />
                </button>

                {showProfileMenu && (
                  <div className="absolute right-0 mt-2 w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                    <Link
                      href="/mypage"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => setShowProfileMenu(false)}
                    >
                      마이페이지
                    </Link>
                    <Link
                      href="/workspace"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => setShowProfileMenu(false)}
                    >
                      워크스페이스
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                    >
                      로그아웃
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <Link href="/login" className="text-gray-600 hover:text-gray-900 transition-colors">
                로그인
              </Link>
            )}
          </div>
        </div>
      </nav>
      {/* 프로필 메뉴 외부 클릭 감지 */}
      {showProfileMenu && (
        <div 
          className="fixed inset-0 z-30 pointer-events-none" 
          onClick={() => setShowProfileMenu(false)}
        />
      )}

      {/* Main Content */}
      <div className="flex flex-col items-center px-4 py-12">
        {/* Welcome Message */}
        <div className="text-center mb-12 mt-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">무엇을 도와드릴까요?</h1>
          <p className="text-lg text-gray-600">TinkerBell AI가 창업의 모든 순간을 함께합니다</p>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="w-full max-w-2xl mb-8">
          <div className="relative">
            <Input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="질문을 입력해주세요 ..."
              className="h-14 pl-6 pr-14 text-lg rounded-full border-2 border-gray-200 focus:border-green-400 shadow-lg"
            />
            <Button
              type="submit"
              size="sm"
              className="absolute right-2 top-2 h-10 w-10 rounded-full bg-green-600 hover:bg-green-700 p-0"
            >
              <Search className="h-4 w-4" />
            </Button>
          </div>
        </form>

        {/* Quick Start Button */}
        <Button
          onClick={handleQuickStart}
          size="lg"
          className="mb-16 bg-green-600 hover:bg-green-700 text-lg px-8 py-3 rounded-full shadow-lg"
        >
          바로 시작하기
        </Button>

        {/* Agents Section */}
        <div className="w-full max-w-6xl">
          <div className="text-left mb-6">
            <h2 className="text-xl font-semibold text-gray-800 flex items-center">
              에이전트 바로가기
              <span className="ml-2 text-green-600">→</span>
            </h2>
            <p className="text-gray-600 mt-1">전문 분야별 AI 에이전트와 직접 상담하세요</p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            {agents.map((agent) => (
              <Card
                key={agent.id}
                className={`border-0 shadow-lg hover:shadow-xl transition-all duration-200 cursor-pointer bg-white`}
                onClick={() => handleAgentClick(agent.id)}
              >
                <CardContent className="p-6 flex flex-col items-center text-center">
                  <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                    <Image
                      src={agent.imageSrc}
                      alt={agent.name}
                      width={64}
                      height={64}
                    />
                  </div>
                  <h3 className="font-semibold text-gray-900 text-sm">{agent.name}</h3>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Quick Examples */}
        <div className="w-full max-w-4xl mt-16">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 text-center">💡 이런 질문들을 해보세요</h3>
          <div className="grid md:grid-cols-2 gap-4">
            {[
              "온라인 쇼핑몰 창업 절차가 궁금해요",
              "SNS 마케팅 전략을 세우고 싶어요",
              "고객 응대 자동화 방법을 알려주세요",
              "창업 스트레스 관리법이 필요해요",
            ].map((example, index) => (
              <Button
                key={index}
                variant="outline"
                className="h-auto p-4 text-left justify-start bg-white hover:bg-green-50 border-gray-200 hover:border-green-300 transition-all"
                onClick={async () => {
                  try {
                    const result = await agentApi.createConversation(user?.user_id || 3)
                    if (result.success) {
                      setInput(example)
                      const encoded = encodeURIComponent(example)
                      router.push(`/chat/room?agent=unified_agent&question=${encoded}`)
                    }
                  } catch (error) {
                    console.error("대화 세션 생성 실패:", error)
                    alert("채팅 시작에 실패했습니다. 다시 시도해주세요.")
                  }
                }}
              >
                <span className="text-gray-700 text-sm leading-relaxed">"{example}"</span>
              </Button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
