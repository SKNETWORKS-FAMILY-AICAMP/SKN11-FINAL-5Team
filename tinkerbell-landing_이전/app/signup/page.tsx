"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import Image from "next/image"
import Link from "next/link"
import { useState } from "react"
import { ArrowRight, ArrowLeft } from "lucide-react"

export default function SignupPage() {
  const [currentStep, setCurrentStep] = useState(1)
  const [formData, setFormData] = useState({
    name: "",
    businessType: "",
    startupStatus: "",
  })

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

  const isStep1Complete = formData.name && formData.businessType && formData.startupStatus

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-slate-50 to-gray-100">
      {/* Simple Navigation */}
      <nav className="px-6 py-4 bg-white/90 backdrop-blur-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <Link href="/" className="flex items-center space-x-3">
            <Image
              src="/tinkerbell-logo-final.png"
              alt="TinkerBell Logo"
              width={32}
              height={32}
              className="rounded-full"
            />
            <span className="text-xl font-bold text-gray-900">TinkerBell</span>
          </Link>
          <Link href="/login" className="text-sm text-gray-600 hover:text-blue-600 transition-colors">
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
                      <SelectItem value="preparing">창업 경험 없음</SelectItem>
                      <SelectItem value="preparing">창업 경험 있음</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button
                  onClick={handleNext}
                  className="w-full h-12 bg-blue-600 hover:bg-blue-700"
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
                <Button
                  variant="outline"
                  className="w-full h-14 text-left justify-start space-x-4 hover:bg-yellow-50 border-yellow-200 bg-transparent transition-all duration-200"
                >
                  <div className="w-6 h-6 bg-yellow-400 rounded-full flex items-center justify-center">
                    <span className="text-sm font-bold text-black">K</span>
                  </div>
                  <span className="font-medium">Kakao로 계속하기</span>
                </Button>

                <Button
                  variant="outline"
                  className="w-full h-14 text-left justify-start space-x-4 hover:bg-green-50 border-green-200 bg-transparent transition-all duration-200"
                >
                  <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                    <span className="text-sm font-bold text-white">N</span>
                  </div>
                  <span className="font-medium">Naver로 계속하기</span>
                </Button>

                <Button
                  variant="outline"
                  className="w-full h-14 text-left justify-start space-x-4 hover:bg-red-50 border-red-200 bg-transparent transition-all duration-200"
                >
                  <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center">
                    <span className="text-sm font-bold text-white">G</span>
                  </div>
                  <span className="font-medium">Google로 계속하기</span>
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
              <Link href="/login" className="text-blue-600 hover:underline font-medium">
                로그인
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
