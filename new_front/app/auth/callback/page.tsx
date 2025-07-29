// app/auth/callback/page.tsx
"use client"

import { useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"

export default function AuthCallbackPage() {
  const router = useRouter()
  const params = useSearchParams()

  useEffect(() => {
    const user_id = params.get("user_id")
    const email = params.get("email")
    const nickname = params.get("nickname")

    console.log("✅ [Callback] 파라미터 확인")
    console.log("user_id:", user_id)
    console.log("email:", email)
    console.log("nickname:", nickname)

    if (user_id) {
      const userData = {
        user_id: Number(user_id),
        email,
        nickname,
      }

      localStorage.setItem("user", JSON.stringify(userData))

      console.log("💾 [Callback] localStorage 저장 완료:", userData)
      console.log("🚀 [Callback] /workspace 로 이동 시작")

      router.replace("/workspace")
    } else {
      console.warn("⚠️ [Callback] user_id 없음 → /login 이동")
      alert("로그인 정보가 유효하지 않습니다. 다시 시도해주세요.")
      router.replace("/login")
    }
  }, [params, router])

  return <p className="text-center mt-20">로그인 처리 중입니다...</p>
}