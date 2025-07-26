"use client"

import { API_BASE_URL } from "@/config/constants"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import Image from "next/image"
import Link from "next/link"
import { useState, useEffect } from "react"
import { 
  User, 
  LogOut, 
  CreditCard, 
  FileText, 
  HelpCircle, 
  MessageSquare,
  Eye,
  Download,
  Copy,
  Trash2,
  Search,
  RefreshCw,
  Edit,
  Save,
  X,
  ChevronDown
} from "lucide-react"

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
  conversation_id?: number
  description?: string
}

export default function MyPage() {
  const [activeTab, setActiveTab] = useState("profile")
  const [profileData, setProfileData] = useState({
    name: "",
    email: "",
    businessField: "",
    businessYears: "",
  })

  const [templates, setTemplates] = useState<Template[]>([])
  const [filteredTemplates, setFilteredTemplates] = useState<Template[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<number | null>(null)
  const [editData, setEditData] = useState({ title: "", content: "" })
  const [showProfileMenu, setShowProfileMenu] = useState(false)
  const [userId, setUserId] = useState<number | null>(null)
  const [user, setUser] = useState<any>(null)

  const menuItems = [
    { id: "profile", label: "프로필 관리", icon: User },
    { id: "templates", label: "내 템플릿", icon: FileText },
    { id: "subscription", label: "구독 관리", icon: CreditCard },
    { id: "support", label: "고객 지원", icon: HelpCircle },
  ]

  // 사용자 정보 불러오기
  const loadUserInfo = async (user_id: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/user/${user_id}`)
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          const userData = data.data
          setProfileData({
            name: userData.nickname || "",
            email: userData.email || "",
            businessField: userData.business_type || "",
            businessYears: userData.experience === 1 ? "experience" : "preparing"
          })
        }
      }
    } catch (error) {
      console.error("사용자 정보 조회 실패:", error)
    }
  }

  // 프로필 저장
  const handleSaveProfile = async () => {
    try {
      const payload = {
        nickname: profileData.name,
        business_type: profileData.businessField,
        experience: profileData.businessYears === "experience" ? 1 : 0,
      }

      const response = await fetch(`${API_BASE_URL}/user/${userId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })

      const data = await response.json()
      if (data.success) {
        // localStorage 업데이트
        const storedUser = localStorage.getItem("user")
        if (storedUser) {
          const user = JSON.parse(storedUser)
          user.username = profileData.name
          localStorage.setItem("user", JSON.stringify(user))
        }
        alert("저장 완료")
      } else {
        alert("저장 실패")
      }
    } catch (error) {
      console.error("저장 오류:", error)
      alert("저장 중 오류 발생")
    }
  }

  // 템플릿 불러오기
  const fetchTemplates = async () => {
    try {
      setIsLoading(true)
      if (!userId) return

      const response = await fetch(`${API_BASE_URL}/templates?user_id=${userId}`)
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setTemplates(data.data?.templates || [])
        }
      }
    } catch (error) {
      console.error('템플릿 조회 오류:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // 템플릿 수정 시작
  const startEditTemplate = (template: Template) => {
    setEditingTemplate(template.template_id)
    setEditData({
      title: template.title,
      content: template.content
    })
  }

  // 템플릿 수정 취소
  const cancelEditTemplate = () => {
    setEditingTemplate(null)
    setEditData({ title: "", content: "" })
  }

  // 템플릿 수정 저장
  const saveTemplateEdit = async (templateId: number) => {
    try {
      const targetTemplate = templates.find(t => t.template_id === templateId)
      if (!targetTemplate) return

      const isPublic = targetTemplate.user_id === 3
      let response

      if (isPublic) {
        const body = {
          user_id: userId,
          title: editData.title,
          content: editData.content,
          template_type: targetTemplate.template_type,
          channel_type: targetTemplate.channel_type,
          content_type: targetTemplate.content_type || "text",
          is_custom: true
        }

        response = await fetch(`${API_BASE_URL}/templates`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body)
        })
      } else {
        response = await fetch(`${API_BASE_URL}/templates/${templateId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(editData)
        })
      }

      const data = await response.json()
      if (data.success) {
        alert(isPublic ? "복사하여 저장되었습니다." : "템플릿이 수정되었습니다.")
        setEditingTemplate(null)
        setEditData({ title: "", content: "" })
        fetchTemplates()
      }
    } catch (error) {
      console.error("템플릿 저장 실패:", error)
      alert("저장에 실패했습니다.")
    }
  }

  // 템플릿 삭제
  const handleTemplateDelete = async (templateId: number) => {
    if (!confirm('정말 삭제하시겠습니까?')) return
    
    try {
      const response = await fetch(`${API_BASE_URL}/templates/${templateId}`, {
        method: 'DELETE'
      })

      const data = await response.json()
      if (data.success) {
        setTemplates(templates.filter(t => t.template_id !== templateId))
        alert('템플릿이 삭제되었습니다.')
      }
    } catch (error) {
      console.error('삭제 실패:', error)
      alert('삭제에 실패했습니다.')
    }
  }

  // 템플릿 미리보기
  const handleTemplatePreview = (template: Template) => {
    setSelectedTemplate(template)
    setIsPreviewOpen(true)
  }

  // 템플릿 다운로드
  const handleTemplateDownload = (template: Template) => {
    const element = document.createElement('a')
    const file = new Blob([template.content], { 
      type: template.content_type === 'html' ? 'text/html' : 'text/plain' 
    })
    element.href = URL.createObjectURL(file)
    element.download = `${template.title}.${template.content_type === 'html' ? 'html' : 'txt'}`
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  // 템플릿 복사
  const handleTemplateCopy = async (template: Template) => {
    try {
      await navigator.clipboard.writeText(template.content)
      alert('템플릿이 클립보드에 복사되었습니다!')
    } catch (error) {
      console.error('복사 실패:', error)
      alert('복사에 실패했습니다.')
    }
  }

  // 로그아웃 처리
  const handleLogout = () => {
    localStorage.clear()
    window.location.href = "/login"
  }

  // 템플릿 타입 라벨 변환
  const getTemplateTypeLabel = (type: string) => {
    const typeMap: Record<string, string> = {
      'business_plan': '사업계획서',
      'marketing': '마케팅',
      'proposal': '제안서',
      'contract': '계약서',
      'presentation': '프레젠테이션',  
      'other': '기타'
    }
    return typeMap[type] || type
  }

  // 템플릿 타입별 배지 색상
  const getTemplateTypeBadgeColor = (type: string) => {
    const colorMap: Record<string, string> = {
      'business_plan': 'bg-blue-100 text-blue-800',
      'marketing': 'bg-green-100 text-green-800',
      'proposal': 'bg-orange-100 text-orange-800',
      'contract': 'bg-red-100 text-red-800',
      'presentation': 'bg-indigo-100 text-indigo-800',
      'other': 'bg-gray-100 text-gray-800'
    }
    return colorMap[type] || 'bg-gray-100 text-gray-800'
  }

  // 초기 로드
  useEffect(() => {
    const storedUser = localStorage.getItem("user")
    if (storedUser) {
      const user = JSON.parse(storedUser)
      setUserId(user.user_id)
      loadUserInfo(user.user_id)
    } else {
      alert("로그인 정보가 없습니다. 로그인 후 이용해주세요.")
      window.location.href = "/login"
    }
  }, [])

  // 템플릿 탭 활성화 시 데이터 로드
  useEffect(() => {
    if (activeTab === "templates" && userId) {
      fetchTemplates()
    }
  }, [activeTab, userId])

  // 템플릿 검색
  useEffect(() => {
    if (searchQuery.trim() === "") {
      setFilteredTemplates(templates)
    } else {
      const filtered = templates.filter(template => 
        template.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        template.content.toLowerCase().includes(searchQuery.toLowerCase())
      )
      setFilteredTemplates(filtered)
    }
  }, [templates, searchQuery])

  useEffect(() => {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser))
      } catch (e) {
        console.error('사용자 정보 파싱 오류:', e)
        localStorage.removeItem('user')
      }
    }
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-yellow-50 to-emerald-50">
      {/* Header */}
      {/* Navigation - 메인페이지와 동일한 헤더 */}
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
            <span className="text-sm text-gray-500 font-medium">Business</span>
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
              <div className="relative flex items-center space-x-2">
                <div className="relative">
                  <button
                    onClick={() => setShowProfileMenu(!showProfileMenu)}
                    className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center focus:outline-none"
                  >
                    <User className="h-4 w-4 text-green-600" />
                  </button>

                  {showProfileMenu && (
                    <div className="absolute right-0 mt-2 w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                      <Link href="/chat" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" onClick={() => setShowProfileMenu(false)}>
                        상담으로 돌아가기
                      </Link>
                      <Link href="/workspace" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" onClick={() => setShowProfileMenu(false)}>
                        워크스페이스
                      </Link>
                      <button onClick={handleLogout} className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50">
                        로그아웃
                      </button>
                    </div>
                  )}
                </div>

                {user?.username && (
                  <span className="text-base text-gray-600">
                    {user.username} 님
                  </span>
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

      <div className="max-w-7xl mx-auto p-6">
        <div className="grid lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <Card className="border-0 shadow-lg bg-white">
              <CardHeader className="pb-4">
                <div className="flex items-center space-x-3">
                  <Avatar className="h-12 w-12">
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
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="preparing">창업 경험 없음</SelectItem>
                          <SelectItem value="experience">창업 경험 있음</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="flex justify-end space-x-3">
                    <Button variant="outline">취소</Button>
                    <Button className="bg-green-600 hover:bg-green-700" onClick={handleSaveProfile}>저장하기</Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {activeTab === "templates" && (
              <Card className="border-0 shadow-lg bg-white">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <FileText className="h-5 w-5" />
                      <span>내 템플릿</span>
                      <Badge variant="secondary">{filteredTemplates.length}</Badge>
                    </div>
                    <Button 
                      onClick={fetchTemplates} 
                      variant="outline" 
                      size="sm"
                      disabled={isLoading}
                    >
                      <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                      새로고침
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {/* 검색 */}
                  <div className="mb-6">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        placeholder="템플릿 제목이나 내용으로 검색..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                      />
                    </div>
                  </div>

                  {/* 로딩 표시 */}
                  {isLoading ? (
                    <div className="text-center py-12">
                      <RefreshCw className="h-8 w-8 text-gray-400 mx-auto mb-4 animate-spin" />
                      <p className="text-gray-500">템플릿을 불러오는 중...</p>
                    </div>
                  ) : filteredTemplates.length === 0 ? (
                    <div className="text-center py-12">
                      <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">
                        {searchQuery ? "검색 결과가 없습니다" : "템플릿이 없습니다"}
                      </h3>
                      <p className="text-gray-500 mb-4">
                        {searchQuery 
                          ? "다른 키워드로 검색해보세요."
                          : "AI 상담을 통해 템플릿을 생성해보세요!"}
                      </p>
                      {!searchQuery && (
                        <Link href="/chat">
                          <Button className="bg-green-600 hover:bg-green-700">
                            <MessageSquare className="h-4 w-4 mr-2" />
                            AI 상담 받기
                          </Button>
                        </Link>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {filteredTemplates.map((template) => (
                        <Card key={template.template_id} className="border border-gray-200 hover:border-green-300 transition-colors">
                          <CardContent className="p-6">
                            {editingTemplate === template.template_id ? (
                              // 편집 모드
                              <div className="space-y-4">
                                <div>
                                  <Label className="text-sm font-medium mb-2 block">템플릿 제목</Label>
                                  <Input
                                    value={editData.title}
                                    onChange={(e) => setEditData({ ...editData, title: e.target.value })}
                                    placeholder="템플릿 제목을 입력하세요"
                                  />
                                </div>
                                <div>
                                  <Label className="text-sm font-medium mb-2 block">템플릿 내용</Label>
                                  <textarea
                                    className="w-full p-3 border border-gray-300 rounded-md min-h-[300px] resize-y focus:ring-2 focus:ring-green-500 focus:border-transparent"
                                    value={editData.content}
                                    onChange={(e) => setEditData({ ...editData, content: e.target.value })}
                                    placeholder="템플릿 내용을 입력하세요..."
                                  />
                                </div>
                                <div className="flex justify-end space-x-2">
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={cancelEditTemplate}
                                  >
                                    <X className="h-4 w-4 mr-1" />
                                    취소
                                  </Button>
                                  <Button
                                    size="sm"
                                    onClick={() => saveTemplateEdit(template.template_id)}
                                    className="bg-green-600 hover:bg-green-700"
                                  >
                                    <Save className="h-4 w-4 mr-1" />
                                    저장
                                  </Button>
                                </div>
                              </div>
                            ) : (
                              // 일반 보기 모드
                              <>
                                <div className="flex justify-between items-start mb-4">
                                  <div className="flex-1">
                                    <h4 className="font-semibold text-gray-900 text-lg mb-2">{template.title}</h4>
                                    <div className="flex flex-wrap gap-2">
                                      <Badge className={`text-xs ${getTemplateTypeBadgeColor(template.template_type)}`}>
                                        {getTemplateTypeLabel(template.template_type)}
                                      </Badge>
                                      {template.is_custom && (
                                        <Badge variant="outline" className="text-xs">
                                          커스텀
                                        </Badge>
                                      )}
                                      <Badge variant="secondary" className="text-xs">
                                        {template.channel_type}
                                      </Badge>
                                    </div>
                                  </div>
                                  <div className="flex space-x-2">
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => startEditTemplate(template)}
                                      className="text-blue-600 hover:text-blue-700"
                                    >
                                      <Edit className="h-4 w-4" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => handleTemplatePreview(template)}
                                    >
                                      <Eye className="h-4 w-4" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => handleTemplateDownload(template)}
                                    >
                                      <Download className="h-4 w-4" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => handleTemplateCopy(template)}
                                    >
                                      <Copy className="h-4 w-4" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => handleTemplateDelete(template.template_id)}
                                      className="text-red-600 hover:text-red-700"
                                    >
                                      <Trash2 className="h-4 w-4" />
                                    </Button>
                                  </div>
                                </div>

                                <div className="bg-gray-50 p-4 rounded-md mb-4">
                                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                                    {template.content.replace(/<[^>]*>/g, '').substring(0, 300)}
                                    {template.content.length > 300 && '...'}
                                  </p>
                                </div>

                                <div className="text-xs text-gray-500">
                                  생성일: {new Date(template.created_at).toLocaleDateString('ko-KR', {
                                    year: 'numeric',
                                    month: 'long',
                                    day: 'numeric'
                                  })}
                                </div>
                              </>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
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
                        <Link href="/faq">
                          <Button variant="outline" size="sm" className="w-full">
                            바로가기
                          </Button>
                        </Link>
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

      {/* 템플릿 미리보기 다이얼로그 */}
      <Dialog open={isPreviewOpen} onOpenChange={setIsPreviewOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <span>{selectedTemplate?.title}</span>
              <div className="flex space-x-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => selectedTemplate && handleTemplateDownload(selectedTemplate)}
                >
                  <Download className="h-4 w-4 mr-2" />
                  다운로드
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => selectedTemplate && handleTemplateCopy(selectedTemplate)}
                >
                  <Copy className="h-4 w-4 mr-2" />
                  복사
                </Button>
              </div>
            </DialogTitle>
          </DialogHeader>
          <div className="max-h-[60vh] overflow-y-auto">
            {selectedTemplate && (
              <div 
                className="p-4 border rounded-lg bg-white prose max-w-none"
                dangerouslySetInnerHTML={{ __html: selectedTemplate.content }}
              />
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* 프로필 메뉴 외부 클릭 감지 */}
      {showProfileMenu && (
        <div 
          className="fixed inset-0 z-30 pointer-events-none" 
          onClick={() => setShowProfileMenu(false)}
        />
      )}
    </div>
  )
}