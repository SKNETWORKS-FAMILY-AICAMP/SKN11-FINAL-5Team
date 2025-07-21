"use client"

import { useEffect, useState } from "react"
import { ChevronDown, ChevronUp, Search, User } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import Link from "next/link"
import Image from "next/image"
import { useRouter, useSearchParams } from "next/navigation"

interface FAQ {
  faq_id: number
  category: string
  question: string
  answer: string
  view_count: number
}

function FAQItem({ question, answer }: { question: string; answer: string }) {
  const [isOpen, setIsOpen] = useState(false)
  return (
    <div className="border-b border-gray-200 last:border-b-0 py-4">
      <button
        className="flex justify-between items-center w-full text-left py-2 px-4 rounded-md hover:bg-gray-50 transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="font-medium text-gray-900">{question}</span>
        {isOpen ? <ChevronUp className="h-5 w-5 text-gray-500" /> : <ChevronDown className="h-5 w-5 text-gray-500" />}
      </button>
      {isOpen && (
        <div className="mt-3 text-gray-700 leading-relaxed bg-gray-50 p-4 rounded-md text-sm">{answer}</div>
      )}
    </div>
  )
}

export default function FAQPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [faqs, setFaqs] = useState<FAQ[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [user, setUser] = useState<any>(null)

  // 로그인 유저 처리
  useEffect(() => {
    const userId = searchParams.get("user_id")
    const provider = searchParams.get("provider")
    const email = searchParams.get("email")
    const username = searchParams.get("username")
    const error = searchParams.get("error")

    if (error) {
      alert("로그인에 실패했습니다. 다시 시도해주세요.")
      router.push("/login")
      return
    }

    if (userId && provider) {
      const userData = {
        user_id: parseInt(userId),
        provider,
        email: email || "",
        username: username || "",
      }
      localStorage.setItem("user", JSON.stringify(userData))
      setUser(userData)
      const newUrl = window.location.pathname
      window.history.replaceState({}, document.title, newUrl)
    } else {
      const savedUser = localStorage.getItem("user")
      if (savedUser) setUser(JSON.parse(savedUser))
    }
  }, [searchParams, router])

  // FAQ 불러오기
  useEffect(() => {
    fetchFaqs("")
  }, [])

  const fetchFaqs = async (query = "") => {
    try {
      const res = await fetch(`http://localhost:8080/faq?search=${encodeURIComponent(query)}`)
      if (!res.ok) throw new Error("FAQ API 요청 실패")
      const data = await res.json()
      setFaqs(data.data || [])
    } catch (error) {
      console.error("FAQ 로드 실패:", error)
      setFaqs([])
    }
  }

  const handleSearch = () => fetchFaqs(searchQuery)

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

          {/* 사용자 정보 or 로그인 버튼 */}
          <div className="flex items-center space-x-4">
            {user ? (
              <div className="flex items-center space-x-3">
                <div
                  className="flex items-center space-x-2 cursor-pointer"
                  onClick={() => router.push("/mypage")}
                >
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-green-600" />
                  </div>
                  <span className="text-sm font-medium text-gray-700 hover:underline">
                    {user.username || user.email || "사용자"}
                  </span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    localStorage.removeItem("user")
                    setUser(null)
                    router.push("/login")
                  }}
                  className="text-sm"
                >
                  로그아웃
                </Button>
              </div>
            ) : (
              <Link href="/login">
                <Button variant="outline" size="sm" className="text-sm">
                  로그인
                </Button>
              </Link>
            )}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="flex flex-col items-center px-4 py-12">
        <div className="text-center mb-12 mt-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">FAQ</h1>
          <p className="text-lg text-gray-600">자주 묻는 질문을 확인해보세요</p>
        </div>

        {/* 검색창 */}
        <div className="flex gap-3 w-full max-w-2xl mb-10">
          <Input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="질문 검색..."
            className="flex-1 h-14 text-lg rounded-full border-2 border-gray-200 focus:border-green-400 shadow-lg pl-6 pr-14"
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
          <Button
            onClick={handleSearch}
            className="px-6 py-3 bg-green-600 text-white rounded-full hover:bg-green-700 shadow-md"
          >
            <Search className="h-5 w-5 mr-2" />
            검색
          </Button>
        </div>

        {/* FAQ 목록 */}
        <Card className="bg-white rounded-xl shadow-lg overflow-hidden w-full max-w-4xl">
          <CardContent className="p-6">
            {faqs.length > 0 ? (
              faqs.map((faq) => <FAQItem key={faq.faq_id} question={faq.question} answer={faq.answer} />)
            ) : (
              <p className="text-gray-500 text-center py-8">검색 결과가 없습니다.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
