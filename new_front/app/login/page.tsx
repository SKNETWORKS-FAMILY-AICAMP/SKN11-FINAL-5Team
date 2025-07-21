"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { authApi } from "@/app/api/auth"
import Image from "next/image"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState, useEffect } from "react"
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google'
import GoogleLoginButton from '@/components/GoogleLoginButton'
import Script from 'next/script'

type SdkLoadState = {
  kakao: boolean;
  naver: boolean;
};


declare global {
  interface Window {
    Kakao: any;
    naver: any;
  }
}

export default function LoginPage() {
  // SDK 스크립트 로드 상태
  const [sdkLoaded, setSdkLoaded] = useState<SdkLoadState>({
    kakao: false,
    naver: false
  });

  // SDK 스크립트 로드 완료 핸들러
  const handleKakaoLoad = () => setSdkLoaded(prev => ({ ...prev, kakao: true }));
  const handleNaverLoad = () => setSdkLoaded(prev => ({ ...prev, naver: true }));
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Kakao SDK 초기화
    if (window.Kakao && !window.Kakao.isInitialized()) {
      window.Kakao.init(process.env.NEXT_PUBLIC_KAKAO_APP_KEY);
    }

    // 네이버 SDK 초기화
    if (window.naver) {
      const naverLogin = new window.naver.LoginWithNaverId({
        clientId: process.env.NEXT_PUBLIC_NAVER_CLIENT_ID,
        callbackUrl: `${window.location.origin}/auth/naver/callback`,
        isPopup: false,
      });
      naverLogin.init();
    }
  }, []);

  const handleKakaoLogin = async () => {
    try {
      setIsLoading(true);
      const response = await window.Kakao.Auth.login({
        success: async (authObj: any) => {
          const userInfo = await window.Kakao.API.request({
            url: '/v2/user/me',
          });
          
          const response = await authApi.socialLogin(
            'kakao',
            userInfo.id.toString(),
            userInfo.properties.nickname,
            userInfo.kakao_account.email
          );

          localStorage.setItem('user', JSON.stringify(response));
          router.push('/chat');
        },
        fail: (error: any) => {
          console.error('Kakao login error:', error);
          alert('카카오 로그인에 실패했습니다.');
        },
      });
    } catch (error) {
      console.error('Kakao login error:', error);
      alert('카카오 로그인에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNaverLogin = () => {
    if (window.naver) {
      const naverLogin = new window.naver.LoginWithNaverId({
        clientId: process.env.NEXT_PUBLIC_NAVER_CLIENT_ID,
        callbackUrl: `${window.location.origin}/auth/naver/callback`,
        isPopup: false,
      });
      naverLogin.getLoginStatus((status: boolean) => {
        if (!status) {
          naverLogin.authorize();
        }
      });
    }
  };

  const handleGoogleLogin = async (credentialResponse: any) => {
    try {
      setIsLoading(true);
      
      // JWT 토큰 디코딩 (간단한 Base64 디코딩)
      if (credentialResponse.credential) {
        const parts = credentialResponse.credential.split('.');
        const payload = JSON.parse(atob(parts[1]));
        
        console.log('Google user info:', payload);
        
        const response = await authApi.socialLogin(
          'google',
          payload.sub, // Google 사용자 ID
          payload.name || 'Google User',
          payload.email
        );

        localStorage.setItem('user', JSON.stringify(response));
        router.push('/chat');
      } else {
        throw new Error('No credential received');
      }
    } catch (error) {
      console.error('Google login error:', error);
      alert('구글 로그인에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
    }
  };
  return (
    <>
      {/* Kakao SDK */}
      <Script
        src="https://developers.kakao.com/sdk/js/kakao.js"
        onLoad={handleKakaoLoad}
      />
      {/* Naver SDK */}
      <Script
        src="https://static.nid.naver.com/js/naveridlogin_js_sdk_2.0.2.js"
        onLoad={handleNaverLoad}
      />
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

              {/* 기본 Google OAuth 구현 */}
              {process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ? (
                <GoogleOAuthProvider 
                  clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID}
                  onScriptLoadError={() => console.error('Google Script Load Error')}
                  onScriptLoadSuccess={() => console.log('Google Script Loaded Successfully')}
                >
                  <div className="w-full h-14 flex items-center space-x-4 border rounded-md px-4 hover:bg-red-50 border-red-200 transition-all duration-200">
                    <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center">
                      <span className="text-sm font-bold text-white">G</span>
                    </div>
                    <GoogleLogin
                      onSuccess={handleGoogleLogin}
                      onError={() => {
                        console.error('Google Login Failed');
                        alert('구글 로그인에 실패했습니다.');
                      }}
                      theme="outline"
                      size="large"
                      type="standard"
                      shape="rectangular"
                      text="signin_with"
                      useOneTap={false}
                      auto_select={false}
                    />
                  </div>
                </GoogleOAuthProvider>
              ) : (
                <div className="w-full h-14 flex items-center justify-center border rounded-md px-4 bg-gray-100 border-gray-300">
                  <span className="text-gray-500">구글 로그인 설정 오류</span>
                </div>
              )}

              {/* 대안 Google Login 구현 (위 코드에서 403 오류 발생시 사용)
              <GoogleLoginButton 
                onSuccess={handleGoogleLogin}
                onError={() => alert('구글 로그인에 실패했습니다.')}
              />
              */}
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
    </>
  )
}
