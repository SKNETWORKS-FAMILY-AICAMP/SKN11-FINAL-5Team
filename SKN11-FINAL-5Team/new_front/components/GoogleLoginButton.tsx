// components/GoogleLoginButton.tsx
"use client";

import { useEffect, useState } from 'react';

declare global {
  interface Window {
    google: any;
  }
}

interface GoogleLoginButtonProps {
  onSuccess: (response: any) => void;
  onError: () => void;
}

export default function GoogleLoginButton({ onSuccess, onError }: GoogleLoginButtonProps) {
  const [isGoogleLoaded, setIsGoogleLoaded] = useState(false);

  useEffect(() => {
    // Google Identity Services 라이브러리 로드
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.onload = () => {
      if (window.google && process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID) {
        window.google.accounts.id.initialize({
          client_id: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID,
          callback: onSuccess,
          auto_select: false,
          cancel_on_tap_outside: true,
        });
        setIsGoogleLoaded(true);
      }
    };
    script.onerror = onError;
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, [onSuccess, onError]);

  const handleGoogleLogin = () => {
    if (window.google && isGoogleLoaded) {
      try {
        window.google.accounts.id.prompt();
      } catch (error) {
        console.error('Google login prompt error:', error);
        onError();
      }
    } else {
      onError();
    }
  };

  return (
    <button
      onClick={handleGoogleLogin}
      disabled={!isGoogleLoaded}
      className="w-full h-14 flex items-center space-x-4 border rounded-md px-4 hover:bg-red-50 border-red-200 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center">
        <span className="text-sm font-bold text-white">G</span>
      </div>
      <span className="font-medium">
        {isGoogleLoaded ? 'Google로 로그인' : 'Google 로딩 중...'}
      </span>
    </button>
  );
}
