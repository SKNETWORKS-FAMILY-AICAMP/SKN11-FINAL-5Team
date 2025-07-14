"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import Image from "next/image"
import Link from "next/link"
import { useState } from "react"
import { User, LogOut, CreditCard, FileText, HelpCircle, MessageSquare } from "lucide-react"
import { useReportList } from "@/hooks/useReport"
import { useMemo } from "react"

export default function MyPage() {
  const [activeTab, setActiveTab] = useState("profile")
  const [profileData, setProfileData] = useState({
    name: "김창업",
    email: "startup@example.com",
    businessField: "ecommerce",
    businessYears: "1-3years",
    phone: "010-1234-5678",
  })

  const userId = 1  // 실제론 로그인 정보에서 받아와야 함
  const reportParams = useMemo(() => ({
    user_id: userId,
    report_type: undefined,
    status: undefined,
  }), [userId])

  const showReports = activeTab === "report"
  const { list: reports = [], loading: reportLoading, error: reportError } = useReportList(reportParams, showReports)


  const menuItems = [
    { id: "profile", label: "프로필 관리", icon: User },
    { id: "subscription", label: "구독 관리", icon: CreditCard },
    { id: "report", label: "리포트 조회", icon: FileText },
    { id: "support", label: "고객 지원", icon: HelpCircle },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-yellow-50 to-emerald-50">
      {/* Header */}
      <nav className="px-6 py-4 bg-white/90 backdrop-blur-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <Link href="/" className="flex items-center space-x-3">
            <Image
              src="/placeholder.svg?height=32&width=32"
              alt="TinkerBell Logo"
              width={32}
              height={32}
              className="rounded-full"
            />
            <span className="text-xl font-bold text-gray-900">TinkerBell</span>
          </Link>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">안녕하세요, {profileData.name}님</span>
            <Avatar className="h-8 w-8">
              <AvatarImage src="/placeholder.svg?height=32&width=32" />
              <AvatarFallback className="bg-green-100 text-green-600">{profileData.name.charAt(0)}</AvatarFallback>
            </Avatar>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto p-6">
        <div className="grid lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <Card className="border-0 shadow-lg bg-white">
              <CardHeader className="pb-4">
                <div className="flex items-center space-x-3">
                  <Avatar className="h-12 w-12">
                    <AvatarImage src="/placeholder.svg?height=48&width=48" />
                    <AvatarFallback className="bg-green-100 text-green-600 text-lg">
                      {profileData.name.charAt(0)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <h3 className="font-semibold text-gray-900">{profileData.name}</h3>
                    <p className="text-sm text-gray-500">{profileData.email}</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <nav className="space-y-2">
                  {menuItems.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => setActiveTab(item.id)}
                      className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                        activeTab === item.id ? "bg-green-100 text-green-700" : "text-gray-600 hover:bg-gray-100"
                      }`}
                    >
                      <item.icon className="h-4 w-4" />
                      <span className="text-sm font-medium">{item.label}</span>
                    </button>
                  ))}
                  <Separator className="my-4" />
                  <button className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left text-red-600 hover:bg-red-50 transition-colors">
                    <LogOut className="h-4 w-4" />
                    <span className="text-sm font-medium">로그아웃</span>
                  </button>
                </nav>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {activeTab === "profile" && (
              <Card className="border-0 shadow-lg bg-white">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <User className="h-5 w-5" />
                    <span>프로필 관리</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="flex items-center space-x-6">
                    <Avatar className="h-20 w-20">
                      <AvatarImage src="/placeholder.svg?height=80&width=80" />
                      <AvatarFallback className="bg-green-100 text-green-600 text-2xl">
                        {profileData.name.charAt(0)}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <Button variant="outline" size="sm">
                        프로필 사진 변경
                      </Button>
                      <p className="text-xs text-gray-500 mt-1">JPG, PNG 파일만 업로드 가능합니다</p>
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">이름</Label>
                      <Input
                        id="name"
                        value={profileData.name}
                        onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="email">이메일</Label>
                      <Input id="email" type="email" value={profileData.email} disabled className="bg-gray-50" />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="phone">전화번호</Label>
                      <Input
                        id="phone"
                        value={profileData.phone}
                        onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>사업 분야</Label>
                      <Select
                        value={profileData.businessField}
                        onValueChange={(value) => setProfileData({ ...profileData, businessField: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ecommerce">온라인 쇼핑몰</SelectItem>
                          <SelectItem value="cafe">카페/음식점</SelectItem>
                          <SelectItem value="beauty">미용/뷰티</SelectItem>
                          <SelectItem value="consulting">컨설팅</SelectItem>
                          <SelectItem value="education">교육</SelectItem>
                          <SelectItem value="other">기타</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>사업 연차</Label>
                      <Select
                        value={profileData.businessYears}
                        onValueChange={(value) => setProfileData({ ...profileData, businessYears: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="preparing">창업 준비중</SelectItem>
                          <SelectItem value="1year">1년 미만</SelectItem>
                          <SelectItem value="1-3years">1-3년</SelectItem>
                          <SelectItem value="3-5years">3-5년</SelectItem>
                          <SelectItem value="5years+">5년 이상</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="flex justify-end space-x-3">
                    <Button variant="outline">취소</Button>
                    <Button className="bg-green-600 hover:bg-green-700">저장하기</Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {activeTab === "subscription" && (
              <Card className="border-0 shadow-lg bg-white">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <CreditCard className="h-5 w-5" />
                    <span>구독 관리</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="bg-green-50 p-6 rounded-lg">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">현재 플랜</h3>
                        <p className="text-sm text-gray-600">무료 플랜을 이용 중입니다</p>
                      </div>
                      <Badge variant="secondary">FREE</Badge>
                    </div>
                    <div className="space-y-2 text-sm text-gray-600">
                      <p>• 기본 AI 상담 서비스</p>
                      <p>• 월 10회 질문 제한</p>
                      <p>• 커뮤니티 접근</p>
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-4">
                    <Card className="border-2 border-green-200">
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg">프로 플랜</CardTitle>
                          <Badge className="bg-green-600">추천</Badge>
                        </div>
                        <div className="text-2xl font-bold text-green-600">
                          ₩29,000<span className="text-sm font-normal text-gray-500">/월</span>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <ul className="space-y-2 text-sm text-gray-600">
                          <li>• 무제한 AI 상담</li>
                          <li>• 고급 분석 도구</li>
                          <li>• 우선 고객 지원</li>
                          <li>• 자동화 기능</li>
                        </ul>
                        <Button className="w-full bg-green-600 hover:bg-green-700">업그레이드</Button>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">비즈니스 플랜</CardTitle>
                        <div className="text-2xl font-bold text-gray-900">
                          ₩59,000<span className="text-sm font-normal text-gray-500">/월</span>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <ul className="space-y-2 text-sm text-gray-600">
                          <li>• 프로 플랜 모든 기능</li>
                          <li>• 전담 컨설턴트</li>
                          <li>• 맞춤형 솔루션</li>
                          <li>• API 접근</li>
                        </ul>
                        <Button variant="outline" className="w-full bg-transparent">
                          업그레이드
                        </Button>
                      </CardContent>
                    </Card>
                  </div>
                </CardContent>
              </Card>
            )}

            {activeTab === "report" && (
              <Card className="border-0 shadow-lg bg-white">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <FileText className="h-5 w-5" />
                    <span>리포트 조회</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="text-sm text-gray-600">
                    생성된 리포트 목록을 확인하고 다운로드할 수 있어요.
                  </div>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
                    {/* 여기에 API로 불러온 리포트 목록 map 렌더링 */}
                    {reportLoading && <p className="text-sm text-gray-500">불러오는 중...</p>}
                    {reportError && <p className="text-sm text-red-500">{reportError}</p>}
                    {!reportLoading && reports.length === 0 && (
                      <p className="text-sm text-gray-500">생성된 리포트가 없습니다.</p>
                    )}

                    {reports.map((report) => (
                      <div
                        key={report.report_id}
                        className="flex justify-between items-center bg-white p-4 border border-gray-100 rounded-lg shadow-sm"
                      >
                        <div>
                          <p className="font-semibold text-gray-800">{report.title}</p>
                          <p className="text-sm text-gray-500">생성일: {new Date(report.created_at).toLocaleDateString()}</p>
                        </div>
                        {report.file_url ? (
                          <a
                            href={`http://localhost:8001${report.file_url}`}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <Button variant="outline" size="sm">다운로드</Button>
                          </a>
                        ) : (
                          <span className="text-sm text-yellow-600">생성 중...</span>
                        )}
                      </div>
                    ))}

                    
                  </div>
                </CardContent>
              </Card>
            )}

            {activeTab === "support" && (
              <Card className="border-0 shadow-lg bg-white">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <HelpCircle className="h-5 w-5" />
                    <span>고객 지원</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-4">
                    <Card className="border border-gray-200">
                      <CardContent className="p-6 text-center">
                        <FileText className="h-8 w-8 text-green-600 mx-auto mb-3" />
                        <h4 className="font-medium mb-2">도움말 센터</h4>
                        <p className="text-sm text-gray-500 mb-4">자주 묻는 질문과 가이드를 확인하세요</p>
                        <Button variant="outline" size="sm">
                          바로가기
                        </Button>
                      </CardContent>
                    </Card>

                    <Card className="border border-gray-200">
                      <CardContent className="p-6 text-center">
                        <MessageSquare className="h-8 w-8 text-yellow-600 mx-auto mb-3" />
                        <h4 className="font-medium mb-2">1:1 문의</h4>
                        <p className="text-sm text-gray-500 mb-4">개인적인 문의사항을 남겨주세요</p>
                        <Button variant="outline" size="sm">
                          문의하기
                        </Button>
                      </CardContent>
                    </Card>
                  </div>

                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-medium mb-2">연락처 정보</h4>
                    <div className="space-y-1 text-sm text-gray-600">
                      <p>이메일: support@tinkerbell.ai</p>
                      <p>전화: 1588-0000</p>
                      <p>운영시간: 평일 09:00 - 18:00</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
