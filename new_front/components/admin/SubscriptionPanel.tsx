"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DollarSign, TrendingDown, Users, BarChart3, AlertTriangle, TrendingUp, Clock, ArrowUpRight } from "lucide-react"
import { fetchSubscriptionData } from "@/lib/api"
import type { SubscriptionAnalytics } from "@/lib/data"

export default function SubscriptionPanel() {
  const [data, setData] = useState<SubscriptionAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetchSubscriptionData()
        setData(res)
      } catch (e) {
        setError("구독 데이터를 불러오는 데 실패했습니다.")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <p className="text-center text-emerald-600">불러오는 중...</p>
  if (error || !data) return <p className="text-center text-red-600">{error}</p>

  return (
    <div className="space-y-6">
      {/* Overview */}
 {/* 주요 지표 카드 */}
<div className="grid md:grid-cols-4 gap-4">
  {/* 1. 월 매출 */}
  <Card className="bg-gradient-to-r from-emerald-100 to-emerald-200 border border-emerald-300">
    <CardContent className="p-4">
      <div>
        <p className="text-sm text-emerald-700">월 매출 (₩)</p>
        <p className="text-2xl font-bold text-emerald-900">
          ₩{data.subscription_overview.monthly_revenue.toLocaleString()}
        </p>
      </div>
    </CardContent>
  </Card>

  {/* 2. 총 유료 구독자 수 */}
  <Card className="bg-gradient-to-r from-blue-100 to-blue-200 border border-blue-300">
    <CardContent className="p-4">
      <div>
        <p className="text-sm text-blue-700">총 유료 구독자 수</p>
        <p className="text-2xl font-bold text-blue-900">
          {data.subscription_overview.total_paid_users}
        </p>
      </div>
    </CardContent>
  </Card>

  {/* 3. 7일 이내 유료 전환율 */}
  <Card className="bg-gradient-to-r from-indigo-100 to-indigo-200 border border-indigo-300">
    <CardContent className="p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-indigo-700">7일 이내 유료 전환율</p>
          <p className="text-2xl font-bold text-indigo-900">
            {(data.conversion_funnel.trial_to_paid_rate* 100).toFixed(1)}%
          </p>
        </div>
        <TrendingUp className="h-8 w-8 text-indigo-600" />
      </div>
    </CardContent>
  </Card>

  {/* 4. ARPU (평균 유저당 월 매출) */}
  <Card className="bg-gradient-to-r from-pink-100 to-pink-200 border border-pink-300">
    <CardContent className="p-4">
      <div>
        <p className="text-sm text-pink-700">ARPU (평균 유저당 월 매출)</p>
        <p className="text-2xl font-bold text-pink-900">
          ₩{data.revenue_metrics.average_revenue_per_user.toLocaleString()}
        </p>
      </div>
    </CardContent>
  </Card>
</div>


{/* 수익 지표 */}
<Card className="shadow-lg bg-white/95 backdrop-blur-sm border border-emerald-200">
  <CardHeader>
    <CardTitle className="text-emerald-900">수익 지표</CardTitle>
  </CardHeader>
  <CardContent>
    <div className="grid md:grid-cols-2 gap-6">
      {/* 좌측: 구독 현황 */}
      <div>
        <h4 className="font-medium text-emerald-900 mb-4">구독 현황</h4>
        <div className="space-y-3">
          <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
            <span className="text-purple-800">프리미엄 구독자</span>
            <span className="font-bold text-purple-900">
              {data.subscription_overview.premium_subscribers}
            </span>
          </div>
          <div className="flex justify-between items-center p-3 bg-yellow-50 rounded-lg">
            <span className="text-yellow-800">엔터프라이즈 구독자</span>
            <span className="font-bold text-yellow-900">
              {data.subscription_overview.enterprise_subscribers || 0}
            </span>
          </div>
        </div>
      </div>

      {/* 우측: 전환율 */}
      <div>
        <h4 className="font-medium text-emerald-900 mb-4">전환율</h4>
        <div className="space-y-3">
          <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
            <span className="text-blue-800">체험 → 유료 전환율</span>
            <span className="font-bold text-blue-900">
              {(data.conversion_funnel.trial_to_paid_rate * 100).toFixed(1)}%
            </span>
          </div>
          <div className="flex justify-between items-center p-3 bg-pink-50 rounded-lg">
            <span className="text-pink-800">재활성화율</span>
            <span className="font-bold text-pink-900">
              {(data.conversion_funnel.reactivation_rate * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  </CardContent>
</Card>

      {/* Payment Issues */}
      <Card className="shadow-lg bg-white/95 backdrop-blur-sm border border-emerald-200">
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
                {data.payment_issues.failed_payments}
              </p>
              <p className="text-sm text-red-700">결제 실패</p>
            </div>
            <div className="text-center p-4 bg-amber-50 rounded-lg border border-amber-200">
              <p className="text-2xl font-bold text-amber-900">
                {data.payment_issues.pending_retries}
              </p>
              <p className="text-sm text-amber-700">재시도 대기</p>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg border border-orange-200">
              <p className="text-2xl font-bold text-orange-900">
                {data.payment_issues.requiring_attention}
              </p>
              <p className="text-sm text-orange-700">처리 필요</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
