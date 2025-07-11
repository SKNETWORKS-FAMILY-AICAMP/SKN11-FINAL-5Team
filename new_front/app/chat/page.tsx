"use client"

import type React from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import Image from "next/image"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { Search, Menu, Target, TrendingUp, Users, Zap, Heart, User } from "lucide-react"

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
  const [input, setInput] = useState("")

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    const encoded = encodeURIComponent(input.trim())
    if (encoded) {
      router.push(`/chat/room?agent=unified_agent&question=${encoded}`)
    }
  }

  const handleAgentClick = (agentId: string) => {
    router.push(`/chat/room?agent=${agentId}`)
  }

  const handleQuickStart = () => {
    router.push(`/chat/room?agent=unified_agent`)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-yellow-50 to-emerald-50">
      {/* Header */}
      <nav className="px-6 py-4 bg-white/90 backdrop-blur-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <Link href="/" className="flex items-center space-x-3">
            <Image
              src="/3D_고양이.png?height=32&width=32"
              alt="TinkerBell Logo"
              width={32}
              height={32}
              className="rounded-full"
            />
            <span className="text-xl font-bold text-gray-900">TinkerBell</span>
          </Link>
          <div className="flex items-center space-x-4">
            <Link href="/mypage" className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              <User className="h-4 w-4 text-green-600" />
            </Link>
            <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <Menu className="w-5 h-5 text-gray-700" />
            </button>
          </div>
        </div>
      </nav>

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
                onClick={() => {
                  setInput(example)
                  const encoded = encodeURIComponent(example)
                  router.push(`/chat/room?agent=unified_agent&question=${encoded}`)
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
