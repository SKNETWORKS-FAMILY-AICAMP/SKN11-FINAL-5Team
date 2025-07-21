'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authApi } from '@/app/api/auth';

export default function NaverCallback() {
  const router = useRouter();

  useEffect(() => {
    const processNaverLogin = async () => {
      try {
        if (window.naver) {
          const naverLogin = new window.naver.LoginWithNaverId({
            clientId: process.env.NEXT_PUBLIC_NAVER_CLIENT_ID,
            callbackUrl: `${window.location.origin}/auth/naver/callback`,
          });

          await naverLogin.getLoginStatus(async (status: boolean) => {
            if (status) {
              const user = naverLogin.user;
              
              const response = await authApi.socialLogin(
                'naver',
                user.id,
                user.name,
                user.email
              );

              localStorage.setItem('user', JSON.stringify(response));
              router.push('/chat');
            } else {
              alert('네이버 로그인에 실패했습니다.');
              router.push('/login');
            }
          });
        }
      } catch (error) {
        console.error('Naver login callback error:', error);
        alert('네이버 로그인 처리 중 오류가 발생했습니다.');
        router.push('/login');
      }
    };

    processNaverLogin();
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-4">네이버 로그인 처리 중...</h2>
        <p className="text-gray-600">잠시만 기다려주세요.</p>
      </div>
    </div>
  );
}