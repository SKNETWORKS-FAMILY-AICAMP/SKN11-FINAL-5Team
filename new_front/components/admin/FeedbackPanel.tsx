"use client"

import { useEffect, useState } from "react"
import {
  Card, CardContent, CardHeader, CardTitle,
} from "@/components/ui/card"
import {
  MessageSquare, Star, BarChart3, ThumbsDown,
  AlertTriangle, TrendingUp, TrendingDown
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { fetchFeedbackData } from "@/lib/api"
import type { FeedbackAnalytics } from "@/lib/data"
import { getAgentIcon } from "@/lib/data"

export default function FeedbackPanel() {
  const [data, setData] = useState<FeedbackAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetchFeedbackData()
        setData(res)
      } catch (e) {
        setError("❌ 피드백 데이터를 불러오는 데 실패했습니다.")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <p className="text-center text-emerald-600">⏳ 불러오는 중...</p>
  if (error || !data) return <p className="text-center text-red-600">{error}</p>

  // 누락된 agent_type 채워넣기
  const AGENTS = [
    "business_planning",
    "marketing",
    "customer_service",
    "mental_health",
    "task_agent"
  ]

  const completeSatisfaction = AGENTS.map(type => {
    const found = data.agent_satisfaction.find(a => a.agent_type === type)
    return found ?? {
      agent_type: type,
      average_rating: 0,
      total_feedback: 0,
      satisfaction_trend: "변화없음"
    }
  })

  return (
    <div className="space-y-6">
      {/* 피드백 요약 카드들 */}
      <div className="grid md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-r from-amber-100 to-yellow-100 border border-amber-200">
          <CardContent className="p-4 flex justify-between items-center">
            <div>
              <p className="text-sm text-amber-700">총 피드백</p>
              <p className="text-2xl font-bold text-amber-900">{data.overview.total_feedback}</p>
            </div>
            <MessageSquare className="h-8 w-8 text-amber-600" />
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-emerald-100 to-teal-100 border border-emerald-200">
          <CardContent className="p-4 flex justify-between items-center">
            <div>
              <p className="text-sm text-emerald-700">평균 평점</p>
              <p className="text-2xl font-bold text-emerald-900">{data.overview.average_rating}</p>
              <p className="text-xs text-emerald-600 flex items-center">
                <TrendingUp className="h-3 w-3 mr-1" />
                {data.overview.improvement_trend}
              </p>
            </div>
            <Star className="h-8 w-8 text-emerald-600" />
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-blue-100 to-teal-100 border border-blue-200">
          <CardContent className="p-4 flex justify-between items-center">
            <div>
              <p className="text-sm text-blue-700">코멘트 응답률</p>
              <p className="text-2xl font-bold text-blue-900">{(data.overview.response_rate * 100).toFixed(0)}%</p>
            </div>
            <BarChart3 className="h-8 w-8 text-blue-600" />
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-red-100 to-pink-100 border border-red-200">
          <CardContent className="p-4 flex justify-between items-center">
            <div>
              <p className="text-sm text-red-700">부정적 피드백</p>
              <p className="text-2xl font-bold text-red-900">{data.negative_feedback.total_low_ratings}</p>
            </div>
            <ThumbsDown className="h-8 w-8 text-red-600" />
          </CardContent>
        </Card>
      </div>

      {/* 에이전트별 만족도 */}
      <Card className="border border-emerald-200 bg-white/95 shadow-lg">
        <CardHeader>
          <CardTitle className="text-emerald-900">에이전트별 만족도</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {completeSatisfaction.map((agent) => (
            <div key={agent.agent_type} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
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
                    className={`text-xs flex items-center ${agent.satisfaction_trend.startsWith("+") ? "text-emerald-600" : "text-red-600"}`}
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
        </CardContent>
      </Card>

      {/* 주요 문제 카드 */}
      <Card className="border border-emerald-200 bg-white/95 shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-emerald-900">
            <AlertTriangle className="text-red-600 h-5 w-5" />
            주요 이슈
          </CardTitle>
        </CardHeader>
        <CardContent className="grid md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-emerald-900 mb-2">공통 문제</h4>
            <div className="space-y-2">
              {data.negative_feedback.common_issues.map((issue, i) => (
                <div key={i} className="flex justify-between p-3 bg-red-50 border border-red-200 rounded-lg">
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
            <h4 className="font-medium text-emerald-900 mb-2">처리 필요 피드백</h4>
            <div className="space-y-2">
              {data.negative_feedback.requires_attention.map((fb) => (
                <div key={fb.feedback_id} className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                  <div className="flex justify-between text-sm mb-1">
                    <Badge className="bg-red-100 text-red-700">{fb.rating}점</Badge>
                    <span className="text-orange-600">{new Date(fb.created_at).toLocaleDateString()}</span>
                  </div>
                  <p className="text-orange-800 text-sm mb-1">"{fb.comment}"</p>
                  <div className="flex justify-between text-xs text-orange-600">
                    <span>사용자 ID: {fb.user_id}</span>
                    <Badge className="bg-amber-100 text-amber-700">{fb.status}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
