"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import Image from "next/image"
import Link from "next/link"
import { useState } from "react"
import {
  LogOut,
  CreditCard,
  MessageSquare,
  Users,
  BarChart3,
  Settings,
  Search,
  Eye,
  DollarSign,
  Sparkles,
  Activity,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Star,
  ThumbsDown,
  Zap,
  Brain,
  Heart,
  Target,
  Database,
  Server,
} from "lucide-react"

// 샘플 데이터 (실제로는 API에서 가져올 데이터)
const dashboardData = {
  system_health: {
    overall_status: "healthy",
    ai_agents: {
      business_planning: { status: "healthy", response_time: 1.2 },
      marketing: { status: "healthy", response_time: 1.5 },
      customer_service: { status: "warning", response_time: 3.1 },
      mental_health: { status: "healthy", response_time: 1.8 },
      task_automation: { status: "healthy", response_time: 2.0 },
    },
    llm_services: {
      openai: { status: "healthy", success_rate: 0.98 },
      gemini: { status: "healthy", success_rate: 0.96 },
    },
    databases: {
      postgresql: { status: "healthy", connections: 45 },
      chroma_db: { status: "healthy", collections: 12 },
    },
  },
  real_time_metrics: {
    active_users: 89,
    queries_today: 1547,
    avg_response_time: 2.1,
    error_rate: 0.02,
    total_users: 2456,
    premium_subscribers: 892,
  },
  today_stats: {
    new_signups: 23,
    ai_queries: 1547,
    automation_tasks: 234,
    reports_generated: 67,
  },
}

const usersData = {
  users: [
    {
      user_id: 123,
      email: "user@example.com",
      nickname: "마케터김",
      business_type: "E-COMMERCE",
      business_stage: "STARTUP",
      subscription: {
        plan_type: "PREMIUM",
        status: "active",
        expires_at: "2025-02-15T10:30:00Z",
      },
      usage_stats: {
        total_queries: 234,
        last_active: "2025-01-15T10:30:00Z",
        favorite_agent: "marketing",
      },
      created_at: "2024-12-01T10:30:00Z",
      status: "active",
    },
    {
      user_id: 124,
      email: "business@example.com",
      nickname: "사업가이",
      business_type: "CONSULTING",
      business_stage: "GROWTH",
      subscription: {
        plan_type: "BASIC",
        status: "active",
        expires_at: "2025-02-20T10:30:00Z",
      },
      usage_stats: {
        total_queries: 156,
        last_active: "2025-01-14T15:20:00Z",
        favorite_agent: "business_planning",
      },
      created_at: "2024-11-15T10:30:00Z",
      status: "active",
    },
  ],
  pagination: {
    total: 2456,
    page: 1,
    limit: 20,
    total_pages: 123,
  },
  summary: {
    total_users: 2456,
    active_users: 1987,
    premium_users: 892,
    new_this_month: 234,
  },
}

const subscriptionAnalytics = {
  subscription_overview: {
    total_subscribers: 892,
    basic_subscribers: 456,
    premium_subscribers: 436,
    monthly_revenue: 18950000,
    churn_rate: 0.03,
  },
  revenue_metrics: {
    mrr: 18950000,
    arr: 227400000,
    average_revenue_per_user: 21252,
    lifetime_value: 234500,
  },
  conversion_funnel: {
    trial_users: 234,
    trial_to_paid_rate: 0.32,
    basic_to_premium_rate: 0.18,
    reactivation_rate: 0.12,
  },
  monthly_trends: [
    {
      month: "2025-01",
      new_subscriptions: 89,
      cancellations: 23,
      upgrades: 34,
      downgrades: 12,
      net_growth: 88,
    },
  ],
  payment_issues: {
    failed_payments: 12,
    pending_retries: 8,
    requiring_attention: 4,
  },
}

const feedbackAnalytics = {
  overview: {
    total_feedback: 1456,
    average_rating: 4.2,
    response_rate: 0.68,
    improvement_trend: "+0.3",
  },
  rating_distribution: {
    "5_star": 623,
    "4_star": 489,
    "3_star": 234,
    "2_star": 78,
    "1_star": 32,
  },
  agent_satisfaction: [
    {
      agent_type: "marketing",
      average_rating: 4.5,
      total_feedback: 345,
      satisfaction_trend: "+0.2",
    },
    {
      agent_type: "business_planning",
      average_rating: 4.1,
      total_feedback: 289,
      satisfaction_trend: "-0.1",
    },
    {
      agent_type: "customer_service",
      average_rating: 3.8,
      total_feedback: 267,
      satisfaction_trend: "-0.3",
    },
  ],
  negative_feedback: {
    total_low_ratings: 110,
    common_issues: [
      {
        issue: "응답이 부정확함",
        count: 45,
        percentage: 0.41,
      },
      {
        issue: "응답 시간이 느림",
        count: 32,
        percentage: 0.29,
      },
    ],
    requires_attention: [
      {
        feedback_id: 789,
        user_id: 123,
        rating: 1,
        comment: "AI 응답이 전혀 도움이 되지 않았습니다",
        created_at: "2025-01-15T10:30:00Z",
        status: "pending",
      },
    ],
  },
}

const agentIconMap: Record<string, string> = {
  business_planning: "3D_사업기획",
  marketing: "3D_마케팅",
  customer_service: "3D_고객관리",
  mental_health: "3D_멘탈케어",
  task_automation: "3D_업무관리",
}

const getAgentIcon = (agentType: string) => {
  const iconName = agentIconMap[agentType] || "default"
  return (
    <Image
      src={`/icons/${iconName}.png`}
      alt={`${agentType} 아이콘`}
      width={20}
      height={20}
      className="rounded-sm"
    />
  )
}

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState("dashboard")
  const [selectedUser, setSelectedUser] = useState(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [businessTypeFilter, setBusinessTypeFilter] = useState("all")

  const menuItems = [
    { id: "dashboard", label: "대시보드", icon: BarChart3, color: "text-emerald-600" },
    { id: "users", label: "사용자 관리", icon: Users, color: "text-blue-600" },
    { id: "subscriptions", label: "구독 분석", icon: CreditCard, color: "text-purple-600" },
    { id: "feedback", label: "피드백 분석", icon: MessageSquare, color: "text-amber-600" },
    { id: "settings", label: "시스템 설정", icon: Settings, color: "text-teal-600" },
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy":
        return <CheckCircle className="h-4 w-4 text-emerald-600" />
      case "warning":
        return <AlertTriangle className="h-4 w-4 text-amber-600" />
      case "critical":
        return <XCircle className="h-4 w-4 text-red-600" />
      default:
        return <Clock className="h-4 w-4 text-gray-600" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "healthy":
        return <Badge className="bg-emerald-100 text-emerald-700 border-emerald-300">정상</Badge>
      case "warning":
        return <Badge className="bg-amber-100 text-amber-700 border-amber-300">주의</Badge>
      case "critical":
        return <Badge className="bg-red-100 text-red-700 border-red-300">위험</Badge>
      default:
        return <Badge variant="secondary">{status}</Badge>
    }
  }

  const getPlanBadge = (planType: string) => {
    switch (planType.toLowerCase()) {
      case "basic":
        return <Badge className="bg-gray-100 text-gray-700 border-gray-300">베이직</Badge>
      case "premium":
        return <Badge className="bg-purple-100 text-purple-700 border-purple-300">프리미엄</Badge>
      case "enterprise":
        return <Badge className="bg-blue-100 text-blue-700 border-blue-300">엔터프라이즈</Badge>
      default:
        return <Badge variant="secondary">{planType}</Badge>
    }
  }



  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-blue-50 via-teal-50 to-green-50 relative overflow-hidden">
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
            <Card className="border-0 shadow-lg bg-white/95 backdrop-blur-sm border border-emerald-200">
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
            {/* Dashboard */}
            {activeTab === "dashboard" && (
              <div className="space-y-6">
                {/* System Health */}
                <Card className="border-0 shadow-lg bg-white/95 backdrop-blur-sm border border-emerald-200">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2 text-emerald-900">
                      <Activity className="h-5 w-5 text-emerald-600" />
                      <span>시스템 상태</span>
                      {getStatusBadge(dashboardData.system_health.overall_status)}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid md:grid-cols-3 gap-6">
                      {/* AI Agents */}
                      <div>
                        <h4 className="font-medium text-emerald-900 mb-3 flex items-center">
                          <Brain className="h-4 w-4 mr-2 text-blue-600" />
                          AI 에이전트
                        </h4>
                        <div className="space-y-2">
                          {Object.entries(dashboardData.system_health.ai_agents).map(([key, agent]) => (
                            <div key={key} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                              <div className="flex items-center space-x-2">
                                {getAgentIcon(key)}
                                <span className="text-sm text-emerald-800">{key.replace("_", " ")}</span>
                              </div>
                              <div className="flex items-center space-x-2">
                                {getStatusIcon(agent.status)}
                                <span className="text-xs text-emerald-600">{agent.response_time}s</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* LLM Services */}
                      <div>
                        <h4 className="font-medium text-emerald-900 mb-3 flex items-center">
                          <Server className="h-4 w-4 mr-2 text-purple-600" />
                          LLM 서비스
                        </h4>
                        <div className="space-y-2">
                          {Object.entries(dashboardData.system_health.llm_services).map(([key, service]) => (
                            <div key={key} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                              <div className="flex items-center space-x-2">
                                <span className="text-sm text-emerald-800 capitalize">{key}</span>
                              </div>
                              <div className="flex items-center space-x-2">
                                {getStatusIcon(service.status)}
                                <span className="text-xs text-emerald-600">
                                  {(service.success_rate * 100).toFixed(1)}%
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Databases */}
                      <div>
                        <h4 className="font-medium text-emerald-900 mb-3 flex items-center">
                          <Database className="h-4 w-4 mr-2 text-teal-600" />
                          데이터베이스
                        </h4>
                        <div className="space-y-2">
                          {Object.entries(dashboardData.system_health.databases).map(([key, db]) => (
                            <div key={key} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                              <div className="flex items-center space-x-2">
                                <span className="text-sm text-emerald-800">{key}</span>
                              </div>
                              <div className="flex items-center space-x-2">
                                {getStatusIcon(db.status)}
                                <span className="text-xs text-emerald-600">
                                  {db.connections ? `${db.connections} conn` : `${db.collections} coll`}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Real-time Metrics */}
                <div className="grid md:grid-cols-3 gap-4">
                  <Card className="bg-gradient-to-r from-emerald-100 to-teal-100 border border-emerald-200">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-emerald-700">활성 사용자</p>
                          <p className="text-2xl font-bold text-emerald-900">
                            {dashboardData.real_time_metrics.active_users}
                          </p>
                          <p className="text-xs text-emerald-600">
                            총 {dashboardData.real_time_metrics.total_users.toLocaleString()}명
                          </p>
                        </div>
                        <Users className="h-8 w-8 text-emerald-600" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-r from-blue-100 to-teal-100 border border-blue-200">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-blue-700">오늘 쿼리</p>
                          <p className="text-2xl font-bold text-blue-900">
                            {dashboardData.real_time_metrics.queries_today.toLocaleString()}
                          </p>
                          <p className="text-xs text-blue-600">
                            평균 {dashboardData.real_time_metrics.avg_response_time}s
                          </p>
                        </div>
                        <MessageSquare className="h-8 w-8 text-blue-600" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-r from-purple-100 to-blue-100 border border-purple-200">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-purple-700">프리미엄 구독자</p>
                          <p className="text-2xl font-bold text-purple-900">
                            {dashboardData.real_time_metrics.premium_subscribers}
                          </p>
                          <p className="text-xs text-purple-600">
                            오류율 {(dashboardData.real_time_metrics.error_rate * 100).toFixed(1)}%
                          </p>
                        </div>
                        <CreditCard className="h-8 w-8 text-purple-600" />
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Today Stats */}
                <Card className="border-0 shadow-lg bg-white/95 backdrop-blur-sm border border-emerald-200">
                  <CardHeader>
                    <CardTitle className="text-emerald-900">오늘의 통계</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid md:grid-cols-4 gap-4">
                      {Object.entries(dashboardData.today_stats).map(([key, value]) => (
                        <div key={key} className="text-center p-4 bg-emerald-50 rounded-lg border border-emerald-200">
                          <p className="text-2xl font-bold text-emerald-900">{value}</p>
                          <p className="text-sm text-emerald-700">{key.replace("_", " ")}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Users Management */}
            {activeTab === "users" && (
              <Card className="border-0 shadow-lg bg-white/95 backdrop-blur-sm border border-emerald-200">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center space-x-2 text-emerald-900">
                      <Users className="h-5 w-5 text-blue-600" />
                      <span>사용자 관리</span>
                    </CardTitle>
                    <div className="flex items-center space-x-2">
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-emerald-500" />
                        <Input
                          placeholder="사용자 검색..."
                          className="pl-10 w-64 border-emerald-300 focus:border-blue-400"
                          value={searchTerm}
                          onChange={(e) => setSearchTerm(e.target.value)}
                        />
                      </div>
                      <Select value={statusFilter} onValueChange={setStatusFilter}>
                        <SelectTrigger className="w-32 border-emerald-300">
                          <SelectValue placeholder="상태" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">전체</SelectItem>
                          <SelectItem value="active">활성</SelectItem>
                          <SelectItem value="inactive">비활성</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid md:grid-cols-4 gap-4 mt-4">
                    <div className="bg-emerald-50 p-3 rounded-lg border border-emerald-200">
                      <p className="text-lg font-bold text-emerald-900">
                        {usersData.summary.total_users.toLocaleString()}
                      </p>
                      <p className="text-sm text-emerald-700">총 사용자</p>
                    </div>
                    <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                      <p className="text-lg font-bold text-blue-900">
                        {usersData.summary.active_users.toLocaleString()}
                      </p>
                      <p className="text-sm text-blue-700">활성 사용자</p>
                    </div>
                    <div className="bg-purple-50 p-3 rounded-lg border border-purple-200">
                      <p className="text-lg font-bold text-purple-900">
                        {usersData.summary.premium_users.toLocaleString()}
                      </p>
                      <p className="text-sm text-purple-700">프리미엄 사용자</p>
                    </div>
                    <div className="bg-amber-50 p-3 rounded-lg border border-amber-200">
                      <p className="text-lg font-bold text-amber-900">{usersData.summary.new_this_month}</p>
                      <p className="text-sm text-amber-700">이번 달 신규</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {usersData.users.map((user) => (
                      <Card key={user.user_id} className="border border-emerald-200 hover:shadow-md transition-shadow">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                              <Avatar className="h-12 w-12">
                                <AvatarFallback className="bg-emerald-100 text-emerald-700">
                                  {user.nickname.charAt(0)}
                                </AvatarFallback>
                              </Avatar>
                              <div>
                                <h4 className="font-medium text-emerald-900">{user.nickname}</h4>
                                <p className="text-sm text-emerald-600">{user.email}</p>
                                <div className="flex items-center space-x-2 mt-1">
                                  <Badge className="bg-teal-100 text-teal-700 border-teal-300 text-xs">
                                    {user.business_type}
                                  </Badge>
                                  <Badge className="bg-blue-100 text-blue-700 border-blue-300 text-xs">
                                    {user.business_stage}
                                  </Badge>
                                </div>
                              </div>
                            </div>

                            <div className="flex items-center space-x-4">
                              {getPlanBadge(user.subscription.plan_type)}
                              <div className="text-right">
                                <p className="text-sm font-medium text-emerald-900">
                                  {user.usage_stats.total_queries} 쿼리
                                </p>
                                <p className="text-xs text-emerald-600">
                                  최근: {new Date(user.usage_stats.last_active).toLocaleDateString()}
                                </p>
                              </div>
                            </div>

                            <div className="flex items-center space-x-2">
                              <Badge
                                className={
                                  user.status === "active"
                                    ? "bg-emerald-100 text-emerald-700 border-emerald-300"
                                    : "bg-gray-100 text-gray-700 border-gray-300"
                                }
                              >
                                {user.status === "active" ? "활성" : "비활성"}
                              </Badge>
                              <Button variant="ghost" size="sm" className="text-emerald-600 hover:bg-emerald-50">
                                <Eye className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  <div className="flex items-center justify-between mt-6 pt-4 border-t border-emerald-200">
                    <p className="text-sm text-emerald-600">
                      {usersData.pagination.total.toLocaleString()}명 중 {usersData.pagination.limit}명 표시
                    </p>
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="border-emerald-300 text-emerald-700 bg-transparent"
                      >
                        이전
                      </Button>
                      <span className="text-sm text-emerald-700">
                        {usersData.pagination.page} / {usersData.pagination.total_pages}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        className="border-emerald-300 text-emerald-700 bg-transparent"
                      >
                        다음
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Subscription Analytics */}
            {activeTab === "subscriptions" && (
              <div className="space-y-6">
                {/* Overview */}
                <div className="grid md:grid-cols-4 gap-4">
                  <Card className="bg-gradient-to-r from-purple-100 to-blue-100 border border-purple-200">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-purple-700">총 구독자</p>
                          <p className="text-2xl font-bold text-purple-900">
                            {subscriptionAnalytics.subscription_overview.total_subscribers}
                          </p>
                        </div>
                        <Users className="h-8 w-8 text-purple-600" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-r from-emerald-100 to-teal-100 border border-emerald-200">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-emerald-700">월 매출</p>
                          <p className="text-2xl font-bold text-emerald-900">
                            ₩{(subscriptionAnalytics.subscription_overview.monthly_revenue / 1000000).toFixed(1)}M
                          </p>
                        </div>
                        <DollarSign className="h-8 w-8 text-emerald-600" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-r from-blue-100 to-teal-100 border border-blue-200">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-blue-700">ARPU</p>
                          <p className="text-2xl font-bold text-blue-900">
                            ₩{(subscriptionAnalytics.revenue_metrics.average_revenue_per_user / 1000).toFixed(0)}K
                          </p>
                        </div>
                        <BarChart3 className="h-8 w-8 text-blue-600" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-r from-amber-100 to-yellow-100 border border-amber-200">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-amber-700">이탈률</p>
                          <p className="text-2xl font-bold text-amber-900">
                            {(subscriptionAnalytics.subscription_overview.churn_rate * 100).toFixed(1)}%
                          </p>
                        </div>
                        <TrendingDown className="h-8 w-8 text-amber-600" />
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Revenue Metrics */}
                <Card className="border-0 shadow-lg bg-white/95 backdrop-blur-sm border border-emerald-200">
                  <CardHeader>
                    <CardTitle className="text-emerald-900">수익 지표</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-medium text-emerald-900 mb-4">구독 현황</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                            <span className="text-emerald-800">베이직 구독자</span>
                            <span className="font-bold text-emerald-900">
                              {subscriptionAnalytics.subscription_overview.basic_subscribers}
                            </span>
                          </div>
                          <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                            <span className="text-purple-800">프리미엄 구독자</span>
                            <span className="font-bold text-purple-900">
                              {subscriptionAnalytics.subscription_overview.premium_subscribers}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div>
                        <h4 className="font-medium text-emerald-900 mb-4">전환율</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                            <span className="text-blue-800">체험→유료 전환율</span>
                            <span className="font-bold text-blue-900">
                              {(subscriptionAnalytics.conversion_funnel.trial_to_paid_rate * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex justify-between items-center p-3 bg-teal-50 rounded-lg">
                            <span className="text-teal-800">베이직→프리미엄</span>
                            <span className="font-bold text-teal-900">
                              {(subscriptionAnalytics.conversion_funnel.basic_to_premium_rate * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Payment Issues */}
                <Card className="border-0 shadow-lg bg-white/95 backdrop-blur-sm border border-emerald-200">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2 text-emerald-900">
                      <AlertTriangle className="h-5 w-5 text-amber-600" />
                      <span>결제 이슈</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid md:grid-cols-3 gap-4">
                      <div className="text-center p-4 bg-red-50 rounded-lg border border-red-200">
                        <p className="text-2xl font-bold text-red-900">
                          {subscriptionAnalytics.payment_issues.failed_payments}
                        </p>
                        <p className="text-sm text-red-700">결제 실패</p>
                      </div>
                      <div className="text-center p-4 bg-amber-50 rounded-lg border border-amber-200">
                        <p className="text-2xl font-bold text-amber-900">
                          {subscriptionAnalytics.payment_issues.pending_retries}
                        </p>
                        <p className="text-sm text-amber-700">재시도 대기</p>
                      </div>
                      <div className="text-center p-4 bg-orange-50 rounded-lg border border-orange-200">
                        <p className="text-2xl font-bold text-orange-900">
                          {subscriptionAnalytics.payment_issues.requiring_attention}
                        </p>
                        <p className="text-sm text-orange-700">처리 필요</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Feedback Analytics */}
            {activeTab === "feedback" && (
              <div className="space-y-6">
                {/* Overview */}
                <div className="grid md:grid-cols-4 gap-4">
                  <Card className="bg-gradient-to-r from-amber-100 to-yellow-100 border border-amber-200">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-amber-700">총 피드백</p>
                          <p className="text-2xl font-bold text-amber-900">
                            {feedbackAnalytics.overview.total_feedback}
                          </p>
                        </div>
                        <MessageSquare className="h-8 w-8 text-amber-600" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-r from-emerald-100 to-teal-100 border border-emerald-200">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-emerald-700">평균 평점</p>
                          <p className="text-2xl font-bold text-emerald-900">
                            {feedbackAnalytics.overview.average_rating}
                          </p>
                          <p className="text-xs text-emerald-600 flex items-center">
                            <TrendingUp className="h-3 w-3 mr-1" />
                            {feedbackAnalytics.overview.improvement_trend}
                          </p>
                        </div>
                        <Star className="h-8 w-8 text-emerald-600" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-r from-blue-100 to-teal-100 border border-blue-200">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-blue-700">응답률</p>
                          <p className="text-2xl font-bold text-blue-900">
                            {(feedbackAnalytics.overview.response_rate * 100).toFixed(0)}%
                          </p>
                        </div>
                        <BarChart3 className="h-8 w-8 text-blue-600" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-r from-red-100 to-pink-100 border border-red-200">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-red-700">부정적 피드백</p>
                          <p className="text-2xl font-bold text-red-900">
                            {feedbackAnalytics.negative_feedback.total_low_ratings}
                          </p>
                        </div>
                        <ThumbsDown className="h-8 w-8 text-red-600" />
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Rating Distribution */}
                <Card className="border-0 shadow-lg bg-white/95 backdrop-blur-sm border border-emerald-200">
                  <CardHeader>
                    <CardTitle className="text-emerald-900">평점 분포</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {Object.entries(feedbackAnalytics.rating_distribution).map(([rating, count]) => {
                        const percentage = ((count / feedbackAnalytics.overview.total_feedback) * 100).toFixed(1)
                        return (
                          <div key={rating} className="flex items-center space-x-4">
                            <div className="flex items-center space-x-1 w-16">
                              <span className="text-sm font-medium text-emerald-900">
                                {rating.replace("_star", "점")}
                              </span>
                            </div>
                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-gradient-to-r from-amber-400 to-yellow-500 h-2 rounded-full"
                                style={{ width: `${percentage}%` }}
                              ></div>
                            </div>
                            <div className="w-20 text-right">
                              <span className="text-sm font-medium text-emerald-900">{count}</span>
                              <span className="text-xs text-emerald-600 ml-1">({percentage}%)</span>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </CardContent>
                </Card>

                {/* Agent Satisfaction */}
                <Card className="border-0 shadow-lg bg-white/95 backdrop-blur-sm border border-emerald-200">
                  <CardHeader>
                    <CardTitle className="text-emerald-900">에이전트별 만족도</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {feedbackAnalytics.agent_satisfaction.map((agent) => (
                        <div
                          key={agent.agent_type}
                          className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                        >
                          <div className="flex items-center space-x-3">
                            {getAgentIcon(agent.agent_type)}
                            <div>
                              <h4 className="font-medium text-emerald-900">{agent.agent_type.replace("_", " ")}</h4>
                              <p className="text-sm text-emerald-600">{agent.total_feedback} 피드백</p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-4">
                            <div className="text-right">
                              <p className="font-bold text-emerald-900">{agent.average_rating}</p>
                              <p
                                className={`text-xs flex items-center ${
                                  agent.satisfaction_trend.startsWith("+") ? "text-emerald-600" : "text-red-600"
                                }`}
                              >
                                {agent.satisfaction_trend.startsWith("+") ? (
                                  <TrendingUp className="h-3 w-3 mr-1" />
                                ) : (
                                  <TrendingDown className="h-3 w-3 mr-1" />
                                )}
                                {agent.satisfaction_trend}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Common Issues */}
                <Card className="border-0 shadow-lg bg-white/95 backdrop-blur-sm border border-emerald-200">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2 text-emerald-900">
                      <AlertTriangle className="h-5 w-5 text-red-600" />
                      <span>주요 이슈</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-medium text-emerald-900 mb-4">공통 문제점</h4>
                        <div className="space-y-3">
                          {feedbackAnalytics.negative_feedback.common_issues.map((issue, index) => (
                            <div
                              key={index}
                              className="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-200"
                            >
                              <span className="text-red-800">{issue.issue}</span>
                              <div className="text-right">
                                <span className="font-bold text-red-900">{issue.count}</span>
                                <span className="text-xs text-red-600 ml-1">
                                  ({(issue.percentage * 100).toFixed(0)}%)
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="font-medium text-emerald-900 mb-4">처리 필요 피드백</h4>
                        <div className="space-y-3">
                          {feedbackAnalytics.negative_feedback.requires_attention.map((feedback) => (
                            <div
                              key={feedback.feedback_id}
                              className="p-3 bg-orange-50 rounded-lg border border-orange-200"
                            >
                              <div className="flex items-center justify-between mb-2">
                                <Badge className="bg-red-100 text-red-700 border-red-300">{feedback.rating}점</Badge>
                                <span className="text-xs text-orange-600">
                                  {new Date(feedback.created_at).toLocaleDateString()}
                                </span>
                              </div>
                              <p className="text-sm text-orange-800 mb-2">"{feedback.comment}"</p>
                              <div className="flex items-center justify-between">
                                <span className="text-xs text-orange-600">사용자 ID: {feedback.user_id}</span>
                                <Badge className="bg-amber-100 text-amber-700 border-amber-300 text-xs">
                                  {feedback.status}
                                </Badge>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Settings */}
            {activeTab === "settings" && (
              <Card className="border-0 shadow-lg bg-white/95 backdrop-blur-sm border border-emerald-200">
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
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
