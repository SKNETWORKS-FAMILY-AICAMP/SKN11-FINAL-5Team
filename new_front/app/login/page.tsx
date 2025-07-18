"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { authApi } from "@/app/api/auth"
import Image from "next/image"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { useState, useEffect } from "react"

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const error = searchParams.get('error');
    const action = searchParams.get('action');
    
    if (error) {
      const errorMessages: Record<string, string> = {
        'oauth_failed': '소셜 로그인에 실패했습니다. 다시 시도해주세요.',
        'google_token_failed': '구글 로그인 인증에 실패했습니다.',
        'kakao_token_failed': '카카오 로그인 인증에 실패했습니다.',
        'naver_token_failed': '네이버 로그인 인증에 실패했습니다.',
        'kakao_userinfo_failed': '카카오 사용자 정보를 가져올 수 없습니다.',
        'naver_userinfo_failed': '네이버 사용자 정보를 가져올 수 없습니다.',
        'kakao_process_failed': '카카오 로그인 처리 중 오류가 발생했습니다.',
        'naver_process_failed': '네이버 로그인 처리 중 오류가 발생했습니다.',
        'google_process_failed': '구글 로그인 처리 중 오류가 발생했습니다.'
      };
      setErrorMessage(errorMessages[error] || '로그인 중 오류가 발생했습니다.');
      
      // 5초 후 에러 메시지 자동 숨김
      setTimeout(() => {
        setErrorMessage('');
      }, 5000);
    }
    
    // 로그인 후 회원가입 필요한 경우 메시지 표시
    if (action === 'signup_required') {
      setErrorMessage('계정을 찾을 수 없습니다. 회원가입을 진행해주세요.');
    }
  }, [searchParams]);

  const handleSocialLogin = async (provider: string) => {
    try {
      setIsLoading(true);
      setErrorMessage(''); // 기존 에러 메시지 클리어
      
      console.log(`🔍 ${provider} 소셜 로그인 시작`);
      
      // 백엔드에서 인증 URL 받아오기 (login 의도 표시)
      const apiUrl = `http://localhost:8080/auth/${provider}?intent=login`;
      console.log(`📡 API 호출: ${apiUrl}`);
      
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      console.log(`📊 응답 상태: ${response.status}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('📋 응답 데이터:', data);
      
      if (data.success && data.data?.auth_url) {
        console.log(`✅ ${provider} 인증 URL 생성 성공`);
        console.log(`🔗 리다이렉션: ${data.data.auth_url}`);
        
        // 소셜 로그인 페이지로 리다이렉션
        window.location.href = data.data.auth_url;
      } else {
        console.error('❌ 소셜 로그인 URL 생성 실패:', data.message || '알 수 없는 오류');
        setErrorMessage(data.message || `${provider} 로그인 URL 생성에 실패했습니다.`);
      }
    } catch (error) {
      console.error('❌ 소셜 로그인 오류:', error);
      
      // 에러 타입에 따른 메시지 설정
      let errorMessage = '소셜 로그인에 실패했습니다.';
      
      if (error instanceof TypeError && error.message.includes('fetch')) {
        errorMessage = '서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.';
      } else if (error instanceof Error) {
        if (error.message.includes('404')) {
          errorMessage = 'API 엔드포인트를 찾을 수 없습니다.';
        } else if (error.message.includes('500')) {
          errorMessage = '서버 내부 오류가 발생했습니다.';
        } else {
          errorMessage = `오류: ${error.message}`;
        }
      }
      
      setErrorMessage(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKakaoLogin = () => handleSocialLogin('kakao');
  const handleNaverLogin = () => handleSocialLogin('naver');
  const handleGoogleLogin = () => handleSocialLogin('google');
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
          <Link href="/signup" className="text-sm text-gray-600 hover:text-green-600 transition-colors">
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
              {errorMessage && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                  {errorMessage}
                </div>
              )}
              <Button
                variant="outline"
                className="w-full h-14 text-left justify-start space-x-4 hover:bg-yellow-50 border-yellow-200 bg-transparent transition-all duration-200"
                onClick={handleKakaoLogin}
                disabled={isLoading}
              >
                <div className="w-6 h-6 bg-yellow-400 rounded-full flex items-center justify-center">
                  <span className="text-sm font-bold text-black">K</span>
                </div>
                <span className="font-medium">Kakao로 로그인</span>
              </Button>

              <Button
                variant="outline"
                className="w-full h-14 text-left justify-start space-x-4 hover:bg-green-50 border-green-200 bg-transparent transition-all duration-200"
                onClick={handleNaverLogin}
                disabled={isLoading}
              >
                <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                  <span className="text-sm font-bold text-white">N</span>
                </div>
                <span className="font-medium">Naver로 로그인</span>
              </Button>

              <Button
                variant="outline"
                className="w-full h-14 text-left justify-start space-x-4 hover:bg-red-50 border-red-200 bg-transparent transition-all duration-200"
                onClick={handleGoogleLogin}
                disabled={isLoading}
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
              <Link href="/signup" className="text-green-600 hover:underline font-medium">
                회원가입
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
