"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { 
  Home, 
  MessageSquare, 
  Zap, 
  User, 
  Settings,
  BarChart3
} from "lucide-react"
import { cn } from "@/lib/utils"

const navigation = [
  {
    name: "홈",
    href: "/",
    icon: Home,
    description: "메인 페이지"
  },
  {
    name: "채팅",
    href: "/chat",
    icon: MessageSquare,
    description: "AI 상담"
  },
  {
    name: "마케팅 자동화",
    href: "/marketing",
    icon: Zap,
    description: "키워드 분석 & 콘텐츠 생성"
  },
  {
    name: "대시보드",
    href: "/admin",
    icon: BarChart3,
    description: "관리자 대시보드"
  },
  {
    name: "마이페이지",
    href: "/mypage",
    icon: User,
    description: "개인 설정"
  }
]

interface NavigationProps {
  className?: string
}

export function Navigation({ className }: NavigationProps) {
  const pathname = usePathname()

  return (
    <nav className={cn("flex items-center space-x-6 lg:space-x-8", className)}>
      {navigation.map((item) => {
        const isActive = pathname === item.href
        const Icon = item.icon
        
        return (
          <Link
            key={item.name}
            href={item.href}
            className={cn(
              "flex items-center gap-2 text-sm font-medium transition-colors hover:text-primary",
              isActive
                ? "text-foreground"
                : "text-muted-foreground"
            )}
          >
            <Icon className="h-4 w-4" />
            <span className="hidden sm:block">{item.name}</span>
          </Link>
        )
      })}
    </nav>
  )
}

interface MobileNavigationProps {
  className?: string
}

export function MobileNavigation({ className }: MobileNavigationProps) {
  const pathname = usePathname()

  return (
    <div className={cn("fixed bottom-0 left-0 right-0 z-50 bg-background border-t", className)}>
      <nav className="flex justify-around items-center py-2 px-4">
        {navigation.slice(0, 4).map((item) => {
          const isActive = pathname === item.href
          const Icon = item.icon
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex flex-col items-center gap-1 p-2 rounded-lg transition-colors",
                isActive
                  ? "text-primary bg-primary/10"
                  : "text-muted-foreground hover:text-primary"
              )}
            >
              <Icon className="h-5 w-5" />
              <span className="text-xs font-medium">{item.name}</span>
            </Link>
          )
        })}
      </nav>
    </div>
  )
}

// 헤더 컴포넌트
interface HeaderProps {
  className?: string
}

export function Header({ className }: HeaderProps) {
  return (
    <header className={cn("sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60", className)}>
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-14 items-center justify-between">
          {/* 로고 */}
          <div className="flex items-center space-x-3">
            <Link href="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">T</span>
              </div>
              <span className="font-bold text-xl text-gray-900">TinkerBell</span>
              <span className="text-xs text-gray-500 font-medium">Business</span>
            </Link>
          </div>

          {/* 데스크톱 네비게이션 */}
          <div className="hidden md:block">
            <Navigation />
          </div>

          {/* 사용자 메뉴 */}
          <div className="flex items-center space-x-4">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/login">로그인</Link>
            </Button>
            <Button size="sm" asChild>
              <Link href="/signup">회원가입</Link>
            </Button>
          </div>
        </div>
      </div>
    </header>
  )
}

// 메인 레이아웃 컴포넌트
interface MainLayoutProps {
  children: React.ReactNode
  showMobileNav?: boolean
}

export function MainLayout({ children, showMobileNav = true }: MainLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className={cn("flex-1", showMobileNav && "pb-16 md:pb-0")}>
        {children}
      </main>
      {showMobileNav && (
        <div className="md:hidden">
          <MobileNavigation />
        </div>
      )}
    </div>
  )
}