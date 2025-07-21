"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/app/api/auth";

declare global {
  interface Window {
    naver: any;
  }
}

export default function NaverCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const handleNaverCallback = async () => {
      try {
        // 네이버 SDK가 로드될 때까지 대기
        if (!window.naver) {
          const script = document.createElement('script');
          script.src = 'https://static.nid.naver.com/js/naveridlogin_js_sdk_2.0.2.js';
          script.onload = () => {
            processNaverLogin();
          };
          document.head.appendChild(script);
        } else {
          processNaverLogin();
        }
      } catch (error) {
        console.error('Naver callback error:', error);
        alert('네이버 로그인에 실패했습니다.');
        router.push('/login');
      }
    };

    const processNaverLogin = async () => {
      try {
        const naverLogin = new window.naver.LoginWithNaverId({
          clientId: process.env.NEXT_PUBLIC_NAVER_CLIENT_ID,
          callbackUrl: `${window.location.origin}/auth/naver/callback`,
          isPopup: false,
        });
        
        naverLogin.init();
        
        // 로그인 상태 확인
        naverLogin.getLoginStatus(async (status: boolean) => {
          if (status) {
            // 사용자 정보 가져오기
            const userProfile = naverLogin.user;
            console.log('Naver user info:', userProfile);
            
            if (userProfile) {
              try {
                const response = await authApi.socialLogin(
                  'naver',
                  userProfile.id,
                  userProfile.name || userProfile.nickname || 'Naver User',
                  userProfile.email
                );
                
                localStorage.setItem('user', JSON.stringify(response));
                router.push('/chat');
              } catch (apiError) {
                console.error('API error:', apiError);
                alert('서버 연결에 실패했습니다.');
                router.push('/login');
              }
            } else {
              console.error('No user profile received');
              alert('사용자 정보를 가져올 수 없습니다.');
              router.push('/login');
            }
          } else {
            console.error('Naver login status is false');
            alert('네이버 로그인이 완료되지 않았습니다.');
            router.push('/login');
          }
        });
      } catch (error) {
        console.error('Process naver login error:', error);
        alert('네이버 로그인 처리 중 오류가 발생했습니다.');
        router.push('/login');
      }
    };

    handleNaverCallback();
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 via-yellow-50 to-emerald-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
        <p className="text-gray-600">네이버 로그인 처리 중...</p>
      </div>
    </div>
  );
}
