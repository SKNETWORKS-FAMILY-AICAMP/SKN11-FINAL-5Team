"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"
import { useState } from "react"
import {
  LogOut,
  CreditCard,
  MessageSquare,
  Users,
  BarChart3,
  Settings,
  Sparkles,
} from "lucide-react"

import DashboardPanel from "@/components/admin/DashboardPanel"
import UsersPanel from "@/components/admin/UsersPanel"
import SubscriptionPanel from "@/components/admin/SubscriptionPanel"
import FeedbackPanel from "@/components/admin/FeedbackPanel"

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState("dashboard")

  const menuItems = [
    { id: "dashboard", label: "대시보드", icon: BarChart3, color: "text-emerald-600" },
    { id: "users", label: "사용자 관리", icon: Users, color: "text-blue-600" },
    { id: "subscriptions", label: "구독 분석", icon: CreditCard, color: "text-purple-600" },
    { id: "feedback", label: "피드백 분석", icon: MessageSquare, color: "text-amber-600" },
    { id: "settings", label: "시스템 설정", icon: Settings, color: "text-teal-600" },
  ]

  const renderContent = () => {
    switch (activeTab) {
      case "dashboard":
        return <DashboardPanel />
      case "users":
        return <UsersPanel />
      case "subscriptions":
        return <SubscriptionPanel />
      case "feedback":
        return <FeedbackPanel />
      case "settings":
        return (
          <Card className="shadow-lg bg-white/95 backdrop-blur-sm border border-emerald-200">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-emerald-900">
                <Settings className="h-5 w-5 text-teal-600" />
                <span>시스템 설정</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-emerald-700">시스템 설정 기능이 곧 추가됩니다.</p>
            </CardContent>
          </Card>
        )
      default:
        return <DashboardPanel />
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-green-50 relative overflow-hidden">
      {/* Magical sparkles background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="sparkle sparkle-1"></div>
        <div className="sparkle sparkle-2"></div>
        <div className="sparkle sparkle-3"></div>
        <div className="sparkle sparkle-4"></div>
      </div>

      <style jsx>{`
        .sparkle {
          position: absolute;
          width: 3px;
          height: 3px;
          border-radius: 50%;
          animation: sparkle 4s infinite;
        }
        
        .sparkle-1 { 
          top: 20%; left: 20%; animation-delay: 0s; 
          background: radial-gradient(circle, #10b981, #059669);
          box-shadow: 0 0 4px #10b981;
        }
        .sparkle-2 { 
          top: 40%; left: 80%; animation-delay: 1s; 
          background: radial-gradient(circle, #3b82f6, #2563eb);
          box-shadow: 0 0 4px #3b82f6;
        }
        .sparkle-3 { 
          top: 70%; left: 30%; animation-delay: 2s; 
          background: radial-gradient(circle, #14b8a6, #0d9488);
          box-shadow: 0 0 4px #14b8a6;
        }
        .sparkle-4 { 
          top: 80%; left: 70%; animation-delay: 1.5s; 
          background: radial-gradient(circle, #fbbf24, #f59e0b);
          box-shadow: 0 0 4px #fbbf24;
        }
        
        @keyframes sparkle {
          0%, 100% { opacity: 0; transform: scale(0); }
          50% { opacity: 0.8; transform: scale(1); }
        }
        
        .magical-glow {
          text-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
        }
      `}</style>

      {/* Header */}
      <nav className="px-6 py-4 bg-white/90 backdrop-blur-sm border-b border-emerald-200 relative z-10">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <Link href="/" className="flex items-center space-x-3">
            <span className="text-xl font-bold text-emerald-900 magical-glow">TinkerBell</span>
            <Badge className="bg-red-100 text-red-700 border-red-300 text-xs">ADMIN</Badge>
          </Link>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-emerald-700">관리자님</span>
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-emerald-100 text-emerald-700">관</AvatarFallback>
            </Avatar>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto p-6 relative z-10">
        <div className="grid lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <Card className="shadow-lg bg-white/95 backdrop-blur-sm border border-emerald-200">
              <CardHeader className="pb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full flex items-center justify-center">
                    <Sparkles className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-emerald-900">관리자 패널</h3>
                    <p className="text-sm text-emerald-600">TinkerBell Admin</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <nav className="space-y-2">
                  {menuItems.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => setActiveTab(item.id)}
                      className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                        activeTab === item.id
                          ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                          : "text-emerald-700 hover:bg-emerald-50"
                      }`}
                    >
                      <item.icon className={`h-4 w-4 ${item.color}`} />
                      <span className="text-sm font-medium">{item.label}</span>
                    </button>
                  ))}
                  <Separator className="my-4 bg-emerald-200" />
                  <button className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left text-red-600 hover:bg-red-50 transition-colors">
                    <LogOut className="h-4 w-4" />
                    <span className="text-sm font-medium">로그아웃</span>
                  </button>
                </nav>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  )
}