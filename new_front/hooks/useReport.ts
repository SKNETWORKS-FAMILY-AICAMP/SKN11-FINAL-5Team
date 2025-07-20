"use client"

import { useEffect, useState } from "react"

export interface ReportData {
  report_id: number
  report_type: string
  title: string
  status: "completed" | "generating"
  content_data: any
  file_url: string | null
  created_at: string
}

// 단건 조회
export function useReport(reportId?: number) {
  const [data, setData] = useState<ReportData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!reportId) return

    setLoading(true)
    fetch(`http://localhost:8001/reports/${reportId}`)
      .then(async (res) => {
        const result = await res.json()
        if (!res.ok || !result.success) throw new Error(result.detail || "불러오기 실패")
        setData(result.data)
      })
      .catch((err) => {
        console.error(err)
        setError(err.message)
      })
      .finally(() => setLoading(false))
  }, [reportId])

  return { data, loading, error }
}

export function useReportList(
  params: { user_id: number, report_type?: string, status?: string },
  enabled: boolean = true
) {
  const [list, setList] = useState<ReportData[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!enabled || !params.user_id) return  // ✅ 조건 추가됨

    const query = new URLSearchParams()
    query.append("user_id", String(params.user_id))
    if (params.report_type) query.append("report_type", params.report_type)
    if (params.status) query.append("status", params.status)

    setLoading(true)
    fetch(`http://localhost:8001/reports?${query.toString()}`)
      .then(async (res) => {
        const result = await res.json()
        if (!res.ok || !result.success) throw new Error(result.detail || "불러오기 실패")
        setList(result.data)
      })
      .catch((err) => {
        console.error(err)
        setError(err.message)
      })
      .finally(() => setLoading(false))
  }, [params.user_id, params.report_type, params.status, enabled]) // ✅ 의존성에 enabled 포함

  return { list, loading, error }
}

//report_down 브랜치꺼 그대로