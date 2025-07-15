"use client"

import React, { createContext, useContext, useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"

type User = {
  user_id: number
  username?: string
  email?: string
  provider?: string
}

type AuthContextType = {
  user: User | null
  setUser: (user: User | null) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const searchParams = useSearchParams()
  const [user, setUser] = useState<User | null>(null)

  const logout = () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("user")
    setUser(null)
    window.location.href = "/" // 완전 새로고침
  }

  useEffect(() => {
    // 히스토리 메소드 패치: pushState/replaceState에 이벤트 바인딩
    const patchHistoryMethod = (method: "pushState" | "replaceState") => {
      const original = history[method]
      history[method] = function (...args) {
        const result = original.apply(this, args)
        window.dispatchEvent(new Event(method))
        return result
      }
    }

    patchHistoryMethod("pushState")
    patchHistoryMethod("replaceState")

    const handleRouteChange = () => {
      const savedUser = localStorage.getItem("user")
      setTimeout(() => {
        setUser(savedUser ? JSON.parse(savedUser) : null)
      }, 0)
    }

    window.addEventListener("popstate", handleRouteChange)
    window.addEventListener("pushState", handleRouteChange)
    window.addEventListener("replaceState", handleRouteChange)
    window.addEventListener("storage", handleRouteChange)

    // 쿼리 파라미터에서 토큰 추출
    const token = searchParams.get("access_token")
    const userId = searchParams.get("user_id")
    const username = searchParams.get("username")
    const provider = searchParams.get("provider")
    const email = searchParams.get("email")

    if (token && userId) {
      const userData = {
        user_id: Number(userId),
        username: username || "",
        provider: provider || "",
        email: email || ""
      }
      localStorage.setItem("access_token", token)
      localStorage.setItem("user", JSON.stringify(userData))
      setUser(userData)
      window.history.replaceState({}, document.title, window.location.pathname)
    } else {
      handleRouteChange()
    }

    return () => {
      window.removeEventListener("popstate", handleRouteChange)
      window.removeEventListener("pushState", handleRouteChange)
      window.removeEventListener("replaceState", handleRouteChange)
      window.removeEventListener("storage", handleRouteChange)
    }
  }, [searchParams])

  return (
    <AuthContext.Provider value={{ user, setUser, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth는 AuthProvider 내에서만 사용되어야 합니다.")
  }
  return context
}
