// UsersPanel.tsx

"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select"
import { Users, Search, Eye } from "lucide-react"
import { fetchUsersData } from "@/lib/api"
import type { UsersData } from "@/lib/data"

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

export default function UsersPanel() {
  const [data, setData] = useState<UsersData | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetchUsersData()
        setData(res)
      } catch (e) {
        setError("사용자 데이터를 불러오는 데 실패했습니다.")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <p className="text-center text-emerald-600">불러오는 중...</p>
  if (error || !data) return <p className="text-center text-red-600">{error}</p>

  return (
    <Card className="shadow-lg bg-white/95 backdrop-blur-sm border border-emerald-200">
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
            <p className="text-lg font-bold text-emerald-900">{data.summary.total_users.toLocaleString()}</p>
            <p className="text-sm text-emerald-700">총 사용자</p>
          </div>
          <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
            <p className="text-lg font-bold text-blue-900">{data.summary.active_users.toLocaleString()}</p>
            <p className="text-sm text-blue-700">활성 사용자</p>
          </div>
          <div className="bg-purple-50 p-3 rounded-lg border border-purple-200">
            <p className="text-lg font-bold text-purple-900">{data.summary.premium_users.toLocaleString()}</p>
            <p className="text-sm text-purple-700">유료 사용자</p>
          </div>
          <div className="bg-amber-50 p-3 rounded-lg border border-amber-200">
            <p className="text-lg font-bold text-amber-900">{data.summary.new_this_month}</p>
            <p className="text-sm text-amber-700">이번 달 신규</p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {data.users.map((user, index) => (
            <Card
              key={`${user.user_id}-${user.subscription?.subscription_id ?? `no-sub-${index}`}`}
              className="border border-emerald-200 hover:shadow-md transition-shadow"
            >
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
            {data.pagination.total.toLocaleString()}명 중 {data.pagination.limit}명 표시
          </p>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm" className="border-emerald-300 text-emerald-700 bg-transparent">
              이전
            </Button>
            <span className="text-sm text-emerald-700">
              {data.pagination.page} / {data.pagination.total_pages}
            </span>
            <Button variant="outline" size="sm" className="border-emerald-300 text-emerald-700 bg-transparent">
              다음
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}