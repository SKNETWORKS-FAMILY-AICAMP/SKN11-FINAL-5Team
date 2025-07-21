"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import Image from "next/image"
import Link from "next/link"


export default function LoginPage() {
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
          <Link href="/signup" className="text-sm text-gray-600 hover:text-blue-600 transition-colors">
            회원가입
          </Link>
        </div>
      </nav>

      {/* Login Section */}
      <div className="flex items-center justify-center min-h-[calc(100vh-80px)] px-6">
        <div className="w-full max-w-sm">
          <Card className="border-0 shadow-xl bg-white">
            <CardHeader className="text-center pb-6">
              <CardTitle className="text-2xl font-bold text-gray-900">로그인</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button
                variant="outline"
                className="w-full h-14 text-left justify-start space-x-4 hover:bg-yellow-50 border-yellow-200 bg-transparent transition-all duration-200"
              >
                <div className="w-6 h-6 bg-yellow-400 rounded-full flex items-center justify-center">
                  <span className="text-sm font-bold text-black">K</span>
                </div>
                <span className="font-medium">Kakao로 로그인</span>
              </Button>

              <Button
                variant="outline"
                className="w-full h-14 text-left justify-start space-x-4 hover:bg-green-50 border-green-200 bg-transparent transition-all duration-200"
              >
                <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                  <span className="text-sm font-bold text-white">N</span>
                </div>
                <span className="font-medium">Naver로 로그인</span>
              </Button>

              <Button
                variant="outline"
                className="w-full h-14 text-left justify-start space-x-4 hover:bg-red-50 border-red-200 bg-transparent transition-all duration-200"
              >
                <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center">
                  <span className="text-sm font-bold text-white">G</span>
                </div>
                <span className="font-medium">Google로 로그인</span>
              </Button>
            </CardContent>
          </Card>

          <div className="text-center mt-6">
            <p className="text-sm text-gray-600">
              계정이 없으신가요?{" "}
              <Link href="/signup" className="text-blue-600 hover:underline font-medium">
                회원가입
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
