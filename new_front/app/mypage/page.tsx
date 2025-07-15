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
import { User, LogOut, CreditCard, FileText, HelpCircle, MessageSquare, Upload, Loader2 } from "lucide-react"
import { useEffect, useState } from "react"
import { agentApi } from "@/app/api/agent"
import { API_BASE_URL } from "@/config/constants" // 백엔드 주소




import { useAuth } from "@/hooks/authcontext"


interface ProfileData {
  name: string
  email: string
  businessField: string
  businessYears: string
  phone: string
  imageUrl: string
}

// 업데이트된 Template 인터페이스
interface Template {
  template_id: number
  user_id: number
  title: string
  content: string
  template_type: string
  channel_type: string
  content_type?: string
  created_at: string
  is_custom: boolean
}

export default function MyPage() {
  const { user, setUser, logout } = useAuth()

  const [activeTab, setActiveTab] = useState("profile")
  const [isUploading, setIsUploading] = useState(false)
  const [profileData, setProfileData] = useState<ProfileData>({
    name: "",
    email: "",
    businessField: "",
    businessYears: "",
    phone: "",
    imageUrl: "",
  })

  // 템플릿 관련 상태 추가
  const [templates, setTemplates] = useState<Template[]>([])
  const [editingTemplate, setEditingTemplate] = useState<number | null>(null)

  // ✅ user 정보가 없을 때 localStorage에서 복구 시도 (핵심 로직)
  useEffect(() => {
    if (!user) {
      const savedUser = localStorage.getItem("user")
      if (savedUser) {
        const parsed = JSON.parse(savedUser)
        setUser(parsed)  // 전역 상태에 복구
        setProfileData(prev => ({
          ...prev,
          name: parsed.username || "",
          email: parsed.email || ""
        }))
      } else {
        alert("로그인이 필요합니다.")
        window.location.href = "/login"
      }
    } else {
      setProfileData(prev => ({
        ...prev,
        name: user.username || "",
        email: user.email || ""
      }))
    }
  }, [user, setUser])

  // 프로필 정보 로드 (기존 유지)
  useEffect(() => {
    const accessToken = localStorage.getItem("access_token")
    if (!accessToken) return
    
    agentApi.getUserProfile(accessToken)
      .then((res) => {
        if (res.success) {
          const user = res.data
          setProfileData({
            name: user.nickname || "", 
            email: user.email || "",
            businessField: user.business_type?.toLowerCase() || "", 
            businessYears: user.business_stage?.toLowerCase() || "", 
            phone: user.phone || "", 
            imageUrl: user.profile_image || "",
          })
        } else {
          console.warn("❌ 프로필 불러오기 실패:", res.error)
          alert("프로필 정보를 불러오는데 실패했습니다.")
        }
      })
      .catch((err) => {
        console.error("프로필 불러오기 실패", err)
        alert("프로필 정보를 불러오는데 실패했습니다.")
      })
  }, [])

  // 템플릿 정보 로드 (새로 추가)
  useEffect(() => {
    if (activeTab !== "templates") return

    const fetchTemplates = async () => {
      try {
        const accessToken = localStorage.getItem("access_token")
        if (!accessToken) {
          alert("로그인이 필요합니다.")
          return
        }

        const res = await agentApi.getTemplates(accessToken)
        if (res.templates) {
          setTemplates(res.templates)
        }
        
        if (res.data.templates) {
          setTemplates(res.data.templates)
          console.log(`✅ ${res.data.total_count}개 템플릿 로드 완료`)
        } else {
          console.warn("템플릿 데이터가 없습니다:", res.data)
          setTemplates([])
        }
      } catch (err: any) {
        console.error("템플릿 조회 실패:", err)
        
        if (err.response?.status === 401) {
          alert("로그인이 만료되었습니다. 다시 로그인해주세요.")
        } else if (err.response?.status === 500) {
          alert("서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
        } else {
          alert(err.response?.data?.detail || "템플릿을 불러오는데 실패했습니다.")
        }
        setTemplates([])
      }
    }

    fetchTemplates()
  }, [activeTab])

  const handleImageChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // 파일 크기 체크 (5MB 제한)
    if (file.size > 5 * 1024 * 1024) {
      alert("파일 크기는 5MB 이하여야 합니다.")
      return
    }

    // 파일 타입 체크
    if (!file.type.startsWith('image/')) {
      alert("이미지 파일만 업로드 가능합니다.")
      return
    }

    const accessToken = localStorage.getItem("access_token")
    if (!accessToken) {
      alert("로그인이 필요합니다.")
      return
    }

    setIsUploading(true)
    const formData = new FormData()
    formData.append("file", file)

    try {
      const res = await fetch(`${API_BASE_URL}/users/profile/image`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`
          // Content-Type은 FormData 사용 시 자동 설정
        },
        body: formData
        // fetch는 직접적으로 timeout 미지원. 필요 시 AbortController 활용
      })
      const data = await res.json()

      console.log("업로드 응답:", data) // 디버깅용
      
      if (data.success) {
        const imageUrl = data.data.image_url  // 백엔드 응답 구조에 맞춤
        setProfileData(prev => ({ ...prev, imageUrl }))
        alert("프로필 이미지가 성공적으로 변경되었습니다.")
      } else {
        throw new Error(data.message || "이미지 업로드에 실패했습니다.")
      }
    } catch (err: any) {
      console.error("이미지 업로드 실패:", err)

      if (err.response) {
        const status = err.response.status
        const message = err.response.data?.message || err.response.data?.error || "서버 오류가 발생했습니다."

        if (status === 401) {
          alert("로그인이 만료되었습니다. 다시 로그인해주세요.")
        } else if (status === 413) {
          alert("파일 크기가 너무 큽니다.")
        } else if (status === 400) {
          alert(`잘못된 요청: ${message}`)
        } else {
          alert(`업로드 실패: ${message}`)
        }
      } else if (err.request) {
        alert("네트워크 오류가 발생했습니다. 인터넷 연결을 확인해주세요.")
      } else {
        alert(err.message || "이미지 업로드 중 오류가 발생했습니다.")
      }
    } finally {
      setIsUploading(false)
      e.target.value = ""
    }
  }

  const handleSave = async () => {
    const accessToken = localStorage.getItem("access_token")
    if (!accessToken) {
      alert("로그인 정보가 없습니다.")
      return
    }

    try {
      const res = await fetch(`${API_BASE_URL}/users/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          nickname: profileData.name,
          business_type: profileData.businessField.toUpperCase(),
          business_stage: profileData.businessYears.toUpperCase(),
          phone: profileData.phone,
        })
      })
      const data = await res.json()
      if (data.success) {
        alert("프로필이 성공적으로 저장되었습니다!")
      } else {
        alert(data.message || "프로필 저장에 실패했습니다.")
      }
    } catch (err) {
      console.error("프로필 저장 실패:", err)
      alert("프로필 저장 중 오류가 발생했습니다.")
    }
  }

  // 템플릿 관련 함수들 추가
  const saveTemplate = async (templateId: number, templateData: Partial<Template>) => {
    try {
      const accessToken = localStorage.getItem("access_token")
      if (!accessToken) {
        alert("로그인이 필요합니다.")
        return
      }

      const saveres = await fetch(`${API_BASE_URL}/templates/${templateId}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(templateData)
      })

      const savedata = await saveres.json()

      if (savedata.success) {
        alert(savedata.message || "템플릿이 저장되었습니다!")
        setEditingTemplate(null)

        // 목록 새로고침
        if (activeTab === "templates") {
          const res = await fetch(`${API_BASE_URL}/api/v1/templates`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${accessToken}`,
            }
          })
          const data = await res.json()

          if (data.templates) {
            setTemplates(data.templates)
          }
        }
      } else {
        alert("템플릿 저장에 실패했습니다.")
      }
    } catch (err: any) {
      console.error("템플릿 저장 실패:", err)
      alert(err.response?.data?.detail || "템플릿 저장 중 오류가 발생했습니다.")
    }
  }


  const createNewTemplate = async () => {
      try {
        const accessToken = localStorage.getItem("access_token")
        if (!accessToken) {
          alert("로그인이 필요합니다.")
          return
        }
        
        const newTemplateData = {
          title: "새 템플릿",
          content: "템플릿 내용을 입력하세요.",
          template_type: "기획서",
          channel_type: "EMAIL",
          content_type: "html"
        }
        
        const newres = await fetch(`${API_BASE_URL}/api/v1/templates`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(newTemplateData)
        })
        const data = await newres.json()

        
        if (data.success) {
          //alert(data.message || "새 템플릿이 생성되었습니다!")
          
          // 목록 새로고침
          const res = await fetch(`${API_BASE_URL}/api/v1/templates`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${accessToken}`
            }
          })
          const data = await res.json()
          if (data.data?.templates) {
            setTemplates(data.data.templates)
          }
        }
      } 
      catch (err: any) {
        console.error("템플릿 생성 실패:", err)
        alert(err.response?.data?.detail || "템플릿 생성에 실패했습니다.")
      }
    }

  const deleteTemplate = async (templateId: number) => {
    if (!confirm("정말 삭제하시겠습니까?")) return
    
    try {
      const accessToken = localStorage.getItem("access_token")
      const res = await fetch(`${API_BASE_URL}/api/v1/templates/${templateId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      })
      const data = await res.json()

      if (data.success) {
        //alert(data.message || "템플릿이 삭제되었습니다!")
        
        // 목록 새로고침
        const res = await fetch(`${API_BASE_URL}/api/v1/templates`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${accessToken}`
          }
        })
        const data = await res.json()
        if (data.templates) {
          setTemplates(data.templates)
        }

      }
    }
    catch (err: any) {
      console.error("템플릿 삭제 실패:", err)
      
      if (err.response?.status === 400) {
        alert("기본 템플릿은 삭제할 수 없습니다.")
      } else {
        alert(err.response?.data?.detail || "템플릿 삭제에 실패했습니다.")
      }
    }
  }

  const menuItems = [
    { id: "profile", label: "프로필 관리", icon: User },
    { id: "subscription", label: "구독 관리", icon: CreditCard },
    { id: "templates", label: "내 템플릿", icon: FileText },
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
              <AvatarImage src={profileData.imageUrl || "/placeholder.svg?height=80&width=80"} />
              <AvatarFallback className="bg-green-100 text-green-600">
                {profileData.name.charAt(0).toUpperCase() || "?"}
              </AvatarFallback>
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
                    <AvatarImage src={profileData.imageUrl || "/placeholder.svg?height=48&width=48"} />
                    <AvatarFallback className="bg-green-100 text-green-600 text-lg">
                      {profileData.name.charAt(0).toUpperCase() || "?"}
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
                  <button 
                    className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left text-red-600 hover:bg-red-50 transition-colors"
                    onClick={() => {
                      logout()   // useAuth에서 정의된 함수
                      localStorage.clear()
                      window.location.href = "/login"
                    }}  
                  >
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
                    <div className="relative">
                      <Avatar className="h-20 w-20">
                        <AvatarImage src={profileData.imageUrl || "/placeholder.svg?height=80&width=80"} />
                        <AvatarFallback className="bg-green-100 text-green-600 text-2xl">
                          {profileData.name.charAt(0).toUpperCase() || "?"}
                        </AvatarFallback>
                      </Avatar>
                      {isUploading && (
                        <div className="absolute inset-0 bg-black/50 rounded-full flex items-center justify-center">
                          <Loader2 className="h-6 w-6 text-white animate-spin" />
                        </div>
                      )}
                    </div>
                    <div>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        disabled={isUploading}
                        onClick={() => document.getElementById("profile-upload")?.click()}
                        className="flex items-center space-x-2"
                      >
                        {isUploading ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            <span>업로드 중...</span>
                          </>
                        ) : (
                          <>
                            <Upload className="h-4 w-4" />
                            <span>프로필 사진 변경</span>
                          </>
                        )}
                      </Button>
                      <p className="text-xs text-gray-500 mt-1">
                        JPG, PNG 파일만 업로드 가능 (최대 5MB)
                      </p>

                      <Input
                        id="profile-upload"
                        type="file"
                        accept="image/png, image/jpeg, image/jpg"
                        style={{ display: 'none' }}
                        onChange={handleImageChange}
                        disabled={isUploading}
                      />
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
                        placeholder="010-1234-5678"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>사업 분야</Label>
                      <Select
                        value={profileData.businessField}
                        onValueChange={(value) => setProfileData({ ...profileData, businessField: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="사업 분야를 선택하세요" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="e-commerce">온라인 쇼핑몰</SelectItem>
                          <SelectItem value="programmer">개발자</SelectItem>
                          <SelectItem value="beauty">미용/뷰티</SelectItem>
                          <SelectItem value="creator">크리에이터</SelectItem>
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
                          <SelectValue placeholder="사업 연차를 선택하세요" />
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
                    <Button 
                      variant="outline"
                      onClick={() => window.location.reload()}
                    >
                      취소
                    </Button>
                    <Button 
                      className="bg-green-600 hover:bg-green-700" 
                      onClick={handleSave}
                    >
                      저장하기
                    </Button>
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

            {/* 새로 개선된 템플릿 탭 */}
            {activeTab === "templates" && (
              <Card className="border-0 shadow-lg bg-white">
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <CardTitle className="flex items-center space-x-2">
                      <FileText className="h-5 w-5" />
                      <span>내 템플릿</span>
                    </CardTitle>
                    <Button 
                      onClick={createNewTemplate}
                      className="bg-green-600 hover:bg-green-700"
                      size="sm"
                    >
                      새 템플릿 추가
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {templates.length === 0 ? (
                    <div className="text-center py-8">
                      <FileText className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                      <p className="text-sm text-gray-500 mb-2">등록된 템플릿이 없습니다.</p>
                      <p className="text-xs text-gray-400 mb-4">첫 번째 템플릿을 만들어보세요!</p>
                      <Button 
                        onClick={createNewTemplate}
                        variant="outline" 
                        className="flex items-center space-x-2"
                      >
                        <FileText className="h-4 w-4" />
                        <span>첫 번째 템플릿 만들기</span>
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {templates.map((template) => (
                        <Card key={template.template_id} className="border border-gray-200 hover:border-gray-300 transition-colors">
                          <CardContent className="p-4">
                            <div className="flex justify-between items-start mb-3">
                              <div className="flex items-center space-x-2 flex-1">
                                <h4 className="font-medium text-gray-900">{template.title}</h4>
                                <Badge variant={template.is_custom ? "default" : "secondary"} className="text-xs">
                                  {template.is_custom ? "커스텀" : "기본"}
                                </Badge>
                                <Badge variant="outline" className="text-xs">
                                  {template.template_type}
                                </Badge>
                              </div>
                              <div className="flex space-x-2">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => setEditingTemplate(
                                    editingTemplate === template.template_id ? null : template.template_id
                                  )}
                                  className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                                >
                                  {editingTemplate === template.template_id ? "취소" : "편집"}
                                </Button>
                                {template.is_custom && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => deleteTemplate(template.template_id)}
                                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                  >
                                    삭제
                                  </Button>
                                )}
                              </div>
                            </div>

                            {editingTemplate === template.template_id ? (
                              <div className="space-y-4">
                                <div>
                                  <Label htmlFor={`title-${template.template_id}`} className="text-sm font-medium">
                                    템플릿 제목
                                  </Label>
                                  <Input
                                    id={`title-${template.template_id}`}
                                    value={template.title}
                                    onChange={(e) =>
                                      setTemplates((prev) =>
                                        prev.map((t) =>
                                          t.template_id === template.template_id
                                            ? { ...t, title: e.target.value }
                                            : t
                                        )
                                      )
                                    }
                                    className="mt-1"
                                    placeholder="템플릿 제목을 입력하세요"
                                  />
                                </div>
                                <div>
                                  <Label htmlFor={`content-${template.template_id}`} className="text-sm font-medium">
                                    템플릿 내용
                                  </Label>
                                  <textarea
                                    id={`content-${template.template_id}`}
                                    className="w-full mt-1 p-3 border border-gray-300 rounded-md min-h-[200px] resize-y focus:ring-2 focus:ring-green-500 focus:border-transparent"
                                    value={template.content}
                                    onChange={(e) =>
                                      setTemplates((prev) =>
                                        prev.map((t) =>
                                          t.template_id === template.template_id
                                            ? { ...t, content: e.target.value }
                                            : t
                                        )
                                      )
                                    }
                                    placeholder="템플릿 내용을 입력하세요..."
                                  />
                                </div>
                                <div className="flex justify-end space-x-2 pt-2">
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setEditingTemplate(null)}
                                  >
                                    취소
                                  </Button>
                                  <Button
                                    size="sm"
                                    onClick={() => saveTemplate(template.template_id, {
                                      title: template.title,
                                      content: template.content
                                    })}
                                    className="bg-green-600 hover:bg-green-700"
                                  >
                                    저장하기
                                  </Button>
                                </div>
                              </div>
                            ) : (
                              <div className="bg-gray-50 p-4 rounded-md">
                                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                                  {template.content.length > 200 
                                    ? `${template.content.substring(0, 200)}...` 
                                    : template.content
                                  }
                                </p>
                                {template.content.length > 200 && (
                                  <Button
                                    variant="link"
                                    size="sm"
                                    className="p-0 h-auto mt-2 text-blue-600 hover:text-blue-700"
                                    onClick={() => setEditingTemplate(template.template_id)}
                                  >
                                    전체 내용 보기
                                  </Button>
                                )}
                              </div>
                            )}
                            
                            <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
                              <span>
                                생성일: {new Date(template.created_at).toLocaleDateString('ko-KR', {
                                  year: 'numeric',
                                  month: 'short',
                                  day: 'numeric'
                                })}
                              </span>
                              <div className="flex items-center space-x-2">
                                <span className="bg-gray-100 px-2 py-1 rounded text-xs">
                                  {template.channel_type}
                                </span>
                                {template.content_type && (
                                  <span className="bg-gray-100 px-2 py-1 rounded text-xs">
                                    {template.content_type}
                                  </span>
                                )}
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}