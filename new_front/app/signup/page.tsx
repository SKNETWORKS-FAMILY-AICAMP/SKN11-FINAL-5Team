"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import Image from "next/image"
import Link from "next/link"
import { useState, useEffect } from "react"
import { ArrowRight, ArrowLeft } from "lucide-react"
import { useSearchParams } from "next/navigation"

export default function SignupPage() {
  const searchParams = useSearchParams()
  const [currentStep, setCurrentStep] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [socialInfo, setSocialInfo] = useState<{
    provider?: string
    social_id?: string
    email?: string
    username?: string
  } | null>(null)
  const [formData, setFormData] = useState({
    name: "",
    businessType: "",
    startupStatus: "",
  })

  // 로그인 페이지에서 넘어온 소셜 정보 처리
  useEffect(() => {
    const action = searchParams.get('action')
    const provider = searchParams.get('provider')
    const social_id = searchParams.get('social_id')
    const email = searchParams.get('email')
    const username = searchParams.get('username')
    
    if (action === 'signup_required' && provider && social_id) {
      setSocialInfo({ provider, social_id, email: email || '', username: username || '' })
      setFormData(prev => ({
        ...prev,
        name: username || ''
      }))
      setSuccessMessage(`${provider === 'google' ? '구글' : provider === 'kakao' ? '카카오' : '네이버'} 계정으로 로그인하려고 했지만 계정이 없습니다. 기본 정보를 입력하고 회원가입을 완료해주세요.`)
    }
  }, [searchParams])

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleNext = () => {
    if (formData.name && formData.businessType && formData.startupStatus) {
      setCurrentStep(2)
    }
  }

  const handleBack = () => {
    setCurrentStep(1)
  }

  const handleSocialSignup = async (provider: string) => {
    try {
      setIsLoading(true)
      setErrorMessage('')
      setSuccessMessage('')
      
      console.log(`🔍 ${provider} 소셜 회원가입 시작`)
      
      let requestData;
      let requestUrl;
      
      // 로그인 페이지에서 넘어온 소셜 정보가 있는 경우
      if (socialInfo && socialInfo.provider === provider) {
        // 이미 소셜 인증이 완료된 상태이므로 직접 회원가입 요청
        requestUrl = 'http://localhost:8080/social_login'
        requestData = {
          provider: socialInfo.provider,
          social_id: socialInfo.social_id,
          username: formData.name || socialInfo.username,
          email: socialInfo.email
        }
        
        const response = await fetch(requestUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestData)
        })
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        
        const data = await response.json()
        
        if (data.success) {
          console.log('✅ 소셜 회원가입 성공')
          
          // 채팅 페이지로 리다이렉션
          const queryParams = new URLSearchParams({
            user_id: data.data.user_id.toString(),
            provider: data.data.provider || provider,
            email: data.data.email || '',
            username: formData.name || socialInfo.username || ''
          })
          
          window.location.href = `/chat?${queryParams.toString()}`
        } else {
          setErrorMessage(data.message || '회원가입에 실패했습니다.')
        }
      } else {
        // 일반적인 소셜 회원가입 플로우
        requestUrl = `http://localhost:8080/auth/${provider}`
        requestData = {
          intent: 'signup',
          user_data: formData
        }
        
        const response = await fetch(requestUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestData)
        })
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        
        const data = await response.json()
        
        if (data.success && data.data?.auth_url) {
          console.log(`✅ ${provider} 인증 URL 생성 성공`)
          
          // 소셜 로그인 페이지로 리다이렉션
          window.location.href = data.data.auth_url
        } else {
          console.error('❌ 소셜 회원가입 URL 생성 실패:', data.message)
          setErrorMessage(data.message || `${provider} 회원가입 URL 생성에 실패했습니다.`)
        }
      }
      
    } catch (error) {
      console.error('❌ 소셜 회원가입 오류:', error)
      setErrorMessage('소셜 회원가입에 실패했습니다. 다시 시도해주세요.')
    } finally {
      setIsLoading(false)
    }
  }

  const isStep1Complete = formData.name && formData.businessType && formData.startupStatus

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-yellow-50 to-emerald-50">
      {/* Simple Navigation */}
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
          <Link href="/login" className="text-sm text-gray-600 hover:text-green-600 transition-colors">
            로그인
          </Link>
        </div>
      </nav>

      {/* Signup Section */}
      <div className="flex items-center justify-center min-h-[calc(100vh-80px)] px-6">
        <div className="w-full max-w-md">
          {/* Step 1: Basic Info */}
          {currentStep === 1 && (
            <Card className="border-0 shadow-xl bg-white">
              <CardHeader className="text-center pb-6">
                <CardTitle className="text-2xl font-bold text-gray-900">회원가입</CardTitle>
                <p className="text-sm text-gray-600 mt-2">기본 정보를 입력해주세요</p>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* 성공 메시지 표시 */}
                {successMessage && (
                  <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded-md text-sm">
                    {successMessage}
                  </div>
                )}
                
                <div className="space-y-2">
                  <Label htmlFor="name">당신의 이름을 입력하세요</Label>
                  <Input
                    id="name"
                    placeholder="이름을 입력하세요"
                    value={formData.name}
                    onChange={(e) => handleInputChange("name", e.target.value)}
                    className="h-12"
                  />
                </div>

                <div className="space-y-2">
                  <Label>당신의 비즈니스 타입을 선택하세요</Label>
                  <Select onValueChange={(value) => handleInputChange("businessType", value)}>
                    <SelectTrigger className="h-12">
                      <SelectValue placeholder="비즈니스 타입을 선택하세요" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ecommerce">온라인 쇼핑몰</SelectItem>
                      <SelectItem value="beauty">뷰티</SelectItem>
                      <SelectItem value="tech">개발자</SelectItem>
                      <SelectItem value="content">크리에이터</SelectItem>
                      <SelectItem value="other">기타</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>당신의 창업유무를 알려주세요</Label>
                  <Select onValueChange={(value) => handleInputChange("startupStatus", value)}>
                    <SelectTrigger className="h-12">
                      <SelectValue placeholder="창업 상태를 선택하세요" />
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

                <Button
                  onClick={handleNext}
                  className="w-full h-12 bg-green-600 hover:bg-green-700"
                  disabled={!isStep1Complete}
                >
                  Next
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Step 2: Social Login */}
          {currentStep === 2 && (
            <Card className="border-0 shadow-xl bg-white">
              <CardHeader className="text-center pb-6">
                <CardTitle className="text-2xl font-bold text-gray-900">소셜 계정 연결</CardTitle>
                <p className="text-sm text-gray-600 mt-2">소셜 계정으로 간편하게 가입하세요</p>
              </CardHeader>
              <CardContent className="space-y-4">
                {errorMessage && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                    {errorMessage}
                  </div>
                )}
                {successMessage && (
                  <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded-md text-sm">
                    {successMessage}
                  </div>
                )}
                <Button
                  variant="outline"
                  className="w-full h-14 text-left justify-start space-x-4 hover:bg-yellow-50 border-yellow-200 bg-transparent transition-all duration-200"
                  onClick={() => handleSocialSignup('kakao')}
                  disabled={isLoading}
                >
                  <div className="w-6 h-6 bg-yellow-400 rounded-full flex items-center justify-center">
                    <span className="text-sm font-bold text-black">K</span>
                  </div>
                  <span className="font-medium">
                    {socialInfo?.provider === 'kakao' ? 'Kakao 계정으로 회원가입' : 'Kakao로 계속하기'}
                  </span>
                </Button>

                <Button
                  variant="outline"
                  className="w-full h-14 text-left justify-start space-x-4 hover:bg-green-50 border-green-200 bg-transparent transition-all duration-200"
                  onClick={() => handleSocialSignup('naver')}
                  disabled={isLoading}
                >
                  <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                    <span className="text-sm font-bold text-white">N</span>
                  </div>
                  <span className="font-medium">
                    {socialInfo?.provider === 'naver' ? 'Naver 계정으로 회원가입' : 'Naver로 계속하기'}
                  </span>
                </Button>

                <Button
                  variant="outline"
                  className="w-full h-14 text-left justify-start space-x-4 hover:bg-red-50 border-red-200 bg-transparent transition-all duration-200"
                  onClick={() => handleSocialSignup('google')}
                  disabled={isLoading}
                >
                  <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center">
                    <span className="text-sm font-bold text-white">G</span>
                  </div>
                  <span className="font-medium">
                    {socialInfo?.provider === 'google' ? 'Google 계정으로 회원가입' : 'Google로 계속하기'}
                  </span>
                </Button>

                <Button variant="outline" onClick={handleBack} className="w-full h-12 mt-6 bg-transparent">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  이전으로
                </Button>
              </CardContent>
            </Card>
          )}

          <div className="text-center mt-6">
            <p className="text-sm text-gray-600">
              이미 계정이 있으신가요?{" "}
              <Link href="/login" className="text-green-600 hover:underline font-medium">
                로그인
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
