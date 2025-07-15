"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowRight, MessageSquare, Phone, Clock, ChevronDown, ChevronUp, User } from "lucide-react"
import Link from "next/link"
import Image from "next/image"


// FAQ 아이템 컴포넌트
function FAQItem({ question, answer }: { question: string; answer: string }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="border-b border-gray-200 py-4">
      <button 
        className="flex justify-between items-center w-full text-left" 
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="font-medium text-gray-900">{question}</span>
        {isOpen ? (
          <ChevronUp className="h-5 w-5 text-gray-500" />
        ) : (
          <ChevronDown className="h-5 w-5 text-gray-500" />
        )}
      </button>
      {isOpen && (
        <div className="mt-3 text-gray-600 leading-relaxed">{answer}</div>
      )}
    </div>
  )
}

import { useAuth } from "@/hooks/authcontext"
// 메인 HomePage 컴포넌트
export default function HomePage() {
  const { user, logout } = useAuth()

  const [showMenu, setShowMenu] = useState(false)

  useEffect(() => {
    // 클라이언트 사이드에서만 실행
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem("access_token")
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("user")
    setShowMenu(false)
    window.location.href = "/" // 홈으로 이동
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-yellow-50 to-emerald-50">
      {/* Navigation */}
      <nav className="px-6 py-4 sticky top-0 bg-white/90 backdrop-blur-sm border-b border-gray-200 z-50">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <Image
              src="/3D_고양이.png?height=40&width=40"
              alt="TinkerBell Logo"
              width={40}
              height={40}
              className="rounded-full"
            />
            <span className="text-2xl font-bold text-gray-900">TinkerBell</span>
            <span className="text-sm text-gray-500 font-medium">Business</span>
          </div>
          <div className="hidden md:flex items-center space-x-8">
            <a href="#service" className="text-gray-600 hover:text-green-600 transition-colors font-medium">
              서비스 소개
            </a>
            <a href="#consultation" className="text-gray-600 hover:text-green-600 transition-colors font-medium">
              상담하기
            </a>
            <a href="#faq" className="text-gray-600 hover:text-green-600 transition-colors font-medium">
              FAQ
            </a>
            {user ? (
              <div className="relative">
                <button
                  onClick={() => setShowMenu(!showMenu)}
                  className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center cursor-pointer hover:bg-green-200 transition-colors"
                >
                  <User className="h-4 w-4 text-green-600" />
                </button>

                {showMenu && (
                  <div className="absolute right-0 mt-2 w-40 bg-white border border-gray-200 shadow-lg rounded-md z-50">
                    <Link
                      href="/mypage"
                      className="block px-4 py-2 text-gray-700 hover:bg-gray-100 text-sm"
                      onClick={() => setShowMenu(false)}
                    >
                      마이페이지
                    </Link>
                    <button
                      onClick={logout}
                      className="w-full text-left px-4 py-2 text-red-500 hover:bg-gray-100 text-sm"
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

      {/* Hero Section */}
      <section className="px-6 py-20">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* 왼쪽 텍스트 영역 */}
            <div className="space-y-8">
              <Badge className="mb-6 bg-yellow-100 text-yellow-800 hover:bg-yellow-100 text-[1.1em]">
                솔로프리너 전용 AI 어시스턴트
              </Badge>
              <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-gray-900 leading-tight">
                혼자서도
                <br />
                <span className="text-green-600">한 팀처럼</span>
              </h1>
              <p className="text-xl text-gray-600 leading-relaxed max-w-lg">
                사업기획부터 마케팅, 고객관리, 자동화, 멘탈케어까지
                <br />
                TinkerBell의 다중 AI 에이전트가 창업의 모든 순간을 함께합니다
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link href="/chat">
                  <Button size="lg" className="bg-green-600 hover:bg-green-700 text-lg px-8 py-3 rounded-full">
                    시작하기
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                </Link>
              </div>
            </div>

            {/* 오른쪽 이미지 영역 */}
            <div className="flex justify-center lg:justify-end">
              <div className="relative">
                <Image
                  src="/tinkerbell-mascot4.png"
                  alt="TinkerBell 마스코트 - 마법 지팡이를 든 귀여운 고양이"
                  width={420}
                  height={420}
                  className="w-full max-w-md lg:max-w-lg xl:max-w-xl"
                  priority
                />
                {/* 배경 장식 요소 */}
                <div className="absolute -top-4 -right-4 w-8 h-8 bg-yellow-200 rounded-full opacity-60 animate-pulse"></div>
                <div className="absolute top-1/4 -left-6 w-4 h-4 bg-green-200 rounded-full opacity-40 animate-bounce"></div>
                <div className="absolute bottom-1/3 -right-8 w-6 h-6 bg-yellow-300 rounded-full opacity-50 animate-pulse delay-1000"></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Problem Statement */}
      <section className="px-6 py-20 bg-gradient-to-r from-red-50 to-orange-50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-6">1인 창업자의 현실적인 고민들</h2>
            <p className="text-xl text-gray-600 max-w-4xl mx-auto leading-relaxed">
              창업 과정에서 마주하는 다양한 도전들을 함께 해결해나가요
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                icon: "/icons/3D_사업기획.png",
                title: "사업 타당성 분석",
                desc: "시장 분석과 사업 계획 수립의 어려움",
                color: "text-red-600",
                bg: "bg-red-100",
              },
              {
                icon: "/icons/3D_마케팅.png",
                title: "홍보/마케팅",
                desc: "효과적인 마케팅 전략 부재",
                color: "text-orange-600",
                bg: "bg-orange-100",
              },
              {
                icon: "/icons/3D_시장정보 획득.png",
                title: "시장정보 획득",
                desc: "트렌드와 경쟁사 정보 부족",
                color: "text-green-600",
                bg: "bg-green-100",
              },
              {
                icon: "/icons/3D_고립감.png",
                title: "사회적 고립감",
                desc: "혼자 일하며 느끼는 외로움과 불안감",
                color: "text-yellow-600",
                bg: "bg-yellow-100",
              },
            ].map((item, index) => (
              <Card key={index} className="border-0 shadow-lg hover:shadow-xl transition-shadow bg-white">
                <CardHeader className="text-center">
                  <div className={`w-20 h-20 ${item.bg} rounded-full flex items-center justify-center mx-auto mb-4`}>
                    <Image
                      src={item.icon}
                      alt={item.title}
                      width={32}
                      height={32}
                      className="w-16 h-16"
                    />
                  </div>
                  <CardTitle className="text-lg">{item.title}</CardTitle>
                </CardHeader>
                <CardContent className="text-center">
                  <p className="text-gray-600">{item.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Service Introduction */}
      <section id="service" className="px-6 py-20 bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-6">TinkerBell이 제공하는 통합 솔루션</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              다중 AI 에이전트가 협업하여 창업의 모든 단계에서 실질적이고 전문적인 도움을 제공합니다
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                title: "스마트 자동화",
                desc: "반복적인 업무를 자동화하여 핵심 비즈니스에 집중할 수 있도록 지원",
                features: ["SNS 자동 포스팅", "일정 관리 및 알림", "고객 응대 자동화"],
                color: "text-yellow-600",
                bg: "bg-yellow-100",
              },
              {
                title: "실시간 상담",
                desc: "24시간 언제든지 사업 관련 질문과 고민을 상담할 수 있는 AI 파트너",
                features: ["사업 기획 상담", "마케팅 전략 수립", "트렌드 분석"],
                color: "text-green-600",
                bg: "bg-green-100",
              },
              {
                title: "멘탈 케어",
                desc: "창업 과정에서 느끼는 스트레스와 외로움을 함께 해결하는 심리적 지원",
                features: ["감정 상담", "동기 부여", "스트레스 관리"],
                color: "text-emerald-600",
                bg: "bg-emerald-100",
              },
            ].map((item, index) => (
              <Card key={index} className="border-0 shadow-lg hover:shadow-xl transition-shadow bg-white">
                <CardHeader>
                  <CardTitle className="text-xl">{item.title}</CardTitle>
                  <p className="text-gray-600 mt-2">{item.desc}</p>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {item.features.map((feature, idx) => (
                      <li key={idx} className="flex items-center text-sm text-gray-600">
                        <div className="w-2 h-2 bg-green-600 rounded-full mr-3"></div>
                        {feature}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Business Scenario */}
      <section className="px-6 py-20 bg-gradient-to-br from-green-50 to-yellow-50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-6">창업 성장 3단계별 맞춤 지원</h2>
            <p className="text-xl text-gray-600">
              <span className="font-bold text-green-600">예시 창업 여정</span>을 통해 TinkerBell의 지원 과정을
              확인해보세요
            </p>
          </div>
          <div className="space-y-16">
            {[
              {
                stage: "1단계",
                title: "창업 준비",
                subtitle: "사업 기획 & 정보 탐색",
                color: "bg-green-500",
                bgGradient: "from-green-50 to-emerald-50",
                questions: [
                  {
                    q: "어떤 마켓에 입점해야 하지?",
                    a: "에이블리, 지그재그 등 입점 절차를 단계별로 안내하며 사업기획까지 함께 도와드립니다",
                  },
                  {
                    q: "요즘 유행하는 스타일은 뭐야?",
                    a: "20대 여성 소비자 트렌드를 분석한 데이터를 기반으로, 상품 기획에 바로 활용할 수 있는 인사이트를 제공합니다",
                  },
                ],
              },
              {
                stage: "2단계",
                title: "초기 운영 & 시장 진출",
                subtitle: "실무 지원 & 고객 관리",
                color: "bg-yellow-500",
                bgGradient: "from-yellow-50 to-amber-50",
                questions: [
                  {
                    q: "나 이번주에 신상 촬영 있어!",
                    a: "중요한 일정이 있을 땐 TinkerBell이 일정을 자동으로 캘린더에 등록하고, 리마인드까지 설정해줍니다",
                  },
                  {
                    q: "배송 지연에 고객이 화났어요",
                    a: "이런 경우에는 고객 응대 에이전트가 상황과 고객에 맞춘 응대 문장을 자동으로 제안합니다",
                  },
                ],
              },
              {
                stage: "3단계",
                title: "시장 정착 & 확장",
                subtitle: "마케팅 자동화 & 멘탈 케어",
                color: "bg-emerald-500",
                bgGradient: "from-emerald-50 to-green-50",
                questions: [
                  {
                    q: "다음주에 신상품 5개 올릴 건데, 인스타 자동 포스팅 해줘!",
                    a: "마케팅 에이전트와 자동화 에이전트가 협업하여 SNS 콘텐츠를 예약 발행합니다",
                  },
                  {
                    q: "주문도 줄고 자신감이 없어요…",
                    a: "사용자가 힘들 때 멘탈케어 에이전트가 따뜻한 위로를 건네고, 일정 조정이나 스트레스 관리까지 함께 도와줍니다",
                  },
                ],
              },
            ].map((stage, index) => (
              <div key={index} className={`bg-gradient-to-r ${stage.bgGradient} rounded-2xl p-8`}>
                <div className="flex flex-col lg:flex-row items-start gap-8">
                  <div className="lg:w-1/3">
                    <div className="flex items-center mb-6">
                      <div
                        className={`w-16 h-16 ${stage.color} rounded-full flex items-center justify-center text-white font-bold text-xl mr-6`}
                      >
                        {index + 1}
                      </div>
                      <div>
                        <Badge className="mb-2 bg-white/80 text-gray-700">{stage.stage}</Badge>
                        <h3 className="text-2xl font-bold text-gray-900">{stage.title}</h3>
                        <p className="text-gray-600">{stage.subtitle}</p>
                      </div>
                    </div>
                  </div>
                  <div className="lg:w-2/3 space-y-4">
                    {stage.questions.map((item, qIndex) => (
                      <Card key={qIndex} className="border-0 shadow-md bg-white/80 backdrop-blur-sm">
                        <CardContent className="pt-6">
                          <div className="mb-3">
                            <span className="text-green-600 font-bold">Q: </span>
                            <span className="text-gray-800 font-medium">"{item.q}"</span>
                          </div>
                          <div>
                            <span className="text-yellow-600 font-bold">A: </span>
                            <span className="text-gray-700">{item.a}</span>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Consultation Section */}
      <section id="consultation" className="px-6 py-20 bg-white">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-6">상담하기</h2>
            <p className="text-xl text-gray-600">창업에 대한 고민이 있으시다면 언제든지 연락해주세요</p>
          </div>
          <div className="grid md:grid-cols-2 gap-8">
            <Card className="border-0 shadow-lg bg-white p-8">
              <div className="text-center">
                {/* 전화 상담 이미지 아이콘 */}
                <Image
                  src="/icons/3D_전화.png"
                  alt="전화 상담"
                  width={48}
                  height={48}
                  className="mx-auto mb-4"
                />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">전화 상담</h3>
                <p className="text-gray-600 mb-4">전문 상담사와 직접 통화</p>
                <p className="text-2xl font-bold text-green-600 mb-4">1588-0000</p>
                <div className="flex items-center justify-center text-sm text-gray-500">
                  <Clock className="h-4 w-4 mr-1" />
                  평일 09:00 - 18:00
                </div>
              </div>
            </Card>

            <Card className="border-0 shadow-lg bg-white p-8">
              <div className="text-center">
                {/* AI 상담 이미지 아이콘 */}
                <Image
                  src="/icons/3D_메세지.png"
                  alt="AI 상담"
                  width={48}
                  height={48}
                  className="mx-auto mb-4"
                />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">AI 상담</h3>
                <p className="text-gray-600 mb-4">24시간 AI 챗봇 상담</p>
                <Link href="/chat">
                  <Button className="bg-yellow-500 hover:bg-yellow-600 w-full mb-4">채팅 시작하기</Button>
                </Link>
                <div className="flex items-center justify-center text-sm text-gray-500">
                  <Clock className="h-4 w-4 mr-1" />
                  24시간 언제든지
                </div>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="px-6 py-20 bg-gray-50">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-6">자주 묻는 질문</h2>
            <p className="text-xl text-gray-600">TinkerBell에 대해 궁금한 점들을 확인해보세요</p>
          </div>
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="space-y-4">
              <FAQItem
                question="TinkerBell은 어떤 서비스인가요?"
                answer="TinkerBell은 1인 창업자를 위한 종합 AI 어시스턴트입니다. 사업 기획부터 마케팅, 고객 관리, 업무 자동화, 멘탈 케어까지 창업의 모든 과정을 지원하는 다중 에이전트 시스템입니다."
              />
              <FAQItem
                question="무료로 사용할 수 있나요?"
                answer="기본적인 상담 서비스는 무료로 제공됩니다. 고급 기능과 자동화 서비스는 유료 플랜을 통해 이용하실 수 있습니다."
              />
              <FAQItem
                question="어떤 업종에 적용할 수 있나요?"
                answer="온라인 쇼핑몰, 카페, 미용실, 컨설팅 등 대부분의 1인 사업에 적용 가능합니다. 업종별 맞춤 솔루션을 제공합니다."
              />
              <FAQItem
                question="다중 AI 에이전트는 어떻게 작동하나요?"
                answer="사업기획, 마케팅, 고객응대, 자동화, 멘탈케어 등 각 분야별 전문 AI 에이전트들이 협업하여 상황에 맞는 최적의 솔루션을 제공합니다."
              />
              <FAQItem
                question="상담은 어떻게 받을 수 있나요?"
                answer="전화, AI 채팅, 이메일을 통해 상담받으실 수 있습니다. AI 채팅은 24시간 이용 가능하며, 전화 상담은 평일 9시부터 6시까지 가능합니다."
              />
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-20 bg-gradient-to-r from-green-600 to-emerald-700">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-6">이제 혼자가 아닙니다</h2>
          <p className="text-xl text-green-100 mb-12 leading-relaxed">
            TinkerBell과 함께 창업의 꿈을 현실로 만들어보세요
            <br />
            <span className="font-bold text-yellow-300">다중 AI 에이전트팀</span>이 24시간 당신을 지원합니다
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/chat">
              <Button size="lg" className="bg-white text-green-600 hover:bg-gray-100 text-lg px-8 py-3 rounded-full">
                시작하기
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link href="#consultation">
              <Button
                variant="outline"
                size="lg"
                className="border-white text-white hover:bg-white hover:text-green-600 text-lg px-8 py-3 rounded-full bg-transparent"
              >
                상담 예약하기
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-12 bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8">
            <div className="md:col-span-2">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                  <Image
                    src="/3D_고양이.png"
                    alt="TinkerBell Logo"
                    width={30}
                    height={30}
                    className="rounded-full"
                  />
                </div>
                <span className="text-2xl font-bold">TinkerBell</span>
                <span className="text-sm text-gray-400">Business</span>
              </div>
              <p className="text-gray-400 mb-4">
                1인 창업자를 위한 AI 어시스턴트
                <br />
                혼자서도 한 팀처럼, 창업의 모든 순간을 함께합니다
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-green-400">서비스</h4>
              <ul className="space-y-2 text-gray-400">
                <li>
                  <a href="#service" className="hover:text-white transition-colors">
                    서비스 소개
                  </a>
                </li>
                <li>
                  <a href="#consultation" className="hover:text-white transition-colors">
                    상담하기
                  </a>
                </li>
                <li>
                  <a href="#faq" className="hover:text-white transition-colors">
                    FAQ
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-green-400">연락처</h4>
              <ul className="space-y-2 text-gray-400">
                <li>전화: 1588-0000</li>
                <li>이메일: contact@tinkerbell.ai</li>
                <li>평일 09:00 - 18:00</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 TinkerBell Business. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}