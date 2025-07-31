"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { fetchDashboardData } from "@/lib/api"
import { getStatusBadge, getStatusIcon, getAgentIcon } from "@/lib/data"
import { 
  Activity, 
  Users, 
  MessageSquare, 
  CreditCard,
  Brain,
  Server,
  Database,
  UserPlus,
  FileText,
  Bot
} from "lucide-react"
import type { DashboardData } from "@/lib/data"
import { Badge } from "@/components/ui/badge"

export default function DashboardPanel() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetchDashboardData()
        setData(res)
      } catch (e) {
        setError("대시보드 데이터를 불러오는 데 실패했습니다.")
      } finally {
        setLoading(false)
      }
    }

    load()

    const interval = setInterval(load, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        <Card className="bg-white/95 backdrop-blur-sm border border-emerald-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
              <span className="ml-2 text-emerald-700">데이터 로딩 중...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error || !data) {
    return (
      <Card className="bg-white/95 backdrop-blur-sm border border-red-200">
        <CardContent className="p-6">
          <p className="text-red-700">{error || "데이터를 불러올 수 없습니다."}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* 시스템 상태 */}
      <Card className="shadow-lg bg-white/95 backdrop-blur-sm border border-emerald-200">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 text-emerald-900">
            <Activity className="h-5 w-5 text-emerald-600" />
            <span>시스템 상태</span>
            {getStatusBadge(data.system_health.overall_status)}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-6">
            {/* AI 에이전트 */}
            <div>
              <h4 className="font-medium text-emerald-900 mb-3 flex items-center">
                <Brain className="h-4 w-4 mr-2 text-blue-600" />
                AI 에이전트
              </h4>
              <div className="space-y-2">
                {Object.entries(data.system_health.ai_agents).map(([key, agent]) => (
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

            {/* LLM 서비스 */}
            <div>
              <h4 className="font-medium text-emerald-900 mb-3 flex items-center">
                <Server className="h-4 w-4 mr-2 text-purple-600" />
                LLM 서비스
              </h4>
              <div className="space-y-2">
                {Object.entries(data.system_health.llm_services).map(([key, service]) => (
                  <div key={key} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                    <span className="text-sm text-emerald-800 capitalize">{key}</span>
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

            {/* 데이터베이스 */}
            <div>
              <h4 className="font-medium text-emerald-900 mb-3 flex items-center">
                <Database className="h-4 w-4 mr-2 text-teal-600" />
                데이터베이스
              </h4>
              <div className="space-y-2">
                {Object.entries(data.system_health.databases).map(([dbKey, dbStatus]) => {
                  const labelMap: Record<string, string> = {
                    mysql: "MySQL",
                    chroma_db: "Chroma DB"
                  }
                  const status = dbStatus as { connections?: number; collections?: number }
                  const displayName = labelMap[dbKey.toLowerCase()] ?? dbKey
                  const unitLabel = dbKey.toLowerCase().includes("chroma") ? "컬렉션 수" : "테이블 수"

                  return (
                    <div key={dbKey} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                      <span className="text-sm text-emerald-800 font-medium">{displayName}</span>
                      <span className="text-xs text-emerald-600">
                        연결 수: {status.connections ?? 0} / {unitLabel}: {status.collections ?? 0}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 중간 카드: 오늘 가입자 수 / 오늘 쿼리 / 활성 사용자 */}
      <div className="grid md:grid-cols-3 gap-4">
        {/* 오늘 가입자 수 */}
        <Card className="bg-gradient-to-r from-pink-100 to-red-100 border border-pink-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-pink-700">오늘 가입자 수</p>
                <p className="text-2xl font-bold text-pink-900">
                  {data.real_time_metrics.today_created_users}
                </p>
              </div>
              <UserPlus className="h-8 w-8 text-pink-700" />
            </div>
          </CardContent>
        </Card>

        {/* 오늘 쿼리 */}
        <Card className="bg-gradient-to-r from-blue-100 to-teal-100 border border-blue-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-700">오늘 쿼리</p>
                <p className="text-2xl font-bold text-blue-900">
                  {data.real_time_metrics.queries_today.toLocaleString()}
                </p>
                <p className="text-xs text-blue-600">
                  평균 {data.real_time_metrics.avg_response_time}s
                </p>
              </div>
              <MessageSquare className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        {/* 활성 사용자 */}
        <Card className="bg-gradient-to-r from-emerald-100 to-teal-100 border border-emerald-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-emerald-700">활성 사용자</p>
                <p className="text-2xl font-bold text-emerald-900">
                  {data.real_time_metrics.active_users}
                </p>
                <p className="text-xs text-emerald-600">
                  총 {data.real_time_metrics.total_users.toLocaleString()}명
                </p>
              </div>
              <Users className="h-8 w-8 text-emerald-600" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
