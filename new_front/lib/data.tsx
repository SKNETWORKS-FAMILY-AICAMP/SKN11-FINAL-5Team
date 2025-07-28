
import { CheckCircle, AlertTriangle, XCircle, Clock } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import Image from "next/image"

// 타입 정의
export type AgentStatus = "healthy" | "warning" | "critical" | string
export type AgentType = "business_planning" | "marketing" | "customer_service" | "mental_health" | "task_automation"
export type LLMType = "openai" | "gemini"
export type DBType = "mysql" | "chroma_db"


export type DatabaseStatus = {
  status: string
  connections?: number
  collections?: number
}

export interface DashboardData {
  system_health: {
    overall_status: "healthy" | "warning" | "critical"
    ai_agents: {
      [key: string]: {
        status: "healthy" | "warning" | "critical"
        response_time: number
      }
    }
    llm_services: {
      openai: {
        status: "healthy" | "warning" | "critical"
        success_rate: number
      }
      gemini: {
        status: "healthy" | "warning" | "critical"
        success_rate: number
      }
    }
    databases: {
      [key in DBType]: DatabaseStatus
    }
  }

  real_time_metrics: {
    active_users: number
    queries_today: number
    avg_response_time: number
    error_rate: number
    total_users: number
    premium_subscribers: number
    visitors_today: number              
    today_created_users: number       
    today_generated_reports: number     
    task_automation_ratio: number       
  }

  today_stats: {
    [agent_type: string]: number
  }
}

export interface ReportData {
  report_id: number
  user_id: number
  conversation_id?: number
  report_type: string
  title: string
  content_data: any
  file_url: string
  created_at: string
}

export interface ReportsData {
  reports: ReportData[]
  total: number
  page: number
  limit: number
}

export interface UserData {
  user_id: number
  email: string
  nickname: string
  business_type: string
  business_stage: string
  subscription: {
    plan_type: string
    status: string
    expires_at: string
    subscription_id: number
    tid?: string
    sid?: string
  }
  usage_stats: {
    total_queries: number
    last_active: string
    favorite_agent: string
  }
  created_at: string
  status: string
}

export interface UsersData {
  users: UserData[]
  pagination: {
    total: number
    page: number
    limit: number
    total_pages: number
  }
  summary: {
    total_users: number
    active_users: number
    premium_users: number
    new_this_month: number
  }
}

export type SubscriptionAnalytics = {
  subscription_overview: {
    total_subscribers: number;
    basic_subscribers: number;
    premium_subscribers: number;
    enterprise_subscribers: number;
    monthly_revenue: number;
    churn_rate: number;
    total_paid_users: number;
  };
  revenue_metrics: {
    mrr: number;
    arr: number;
    average_revenue_per_user: number;
    lifetime_value: number;
  };
  conversion_funnel: {
    trial_users: number;
    trial_to_paid_rate: number;
    basic_to_premium_rate: number;
    reactivation_rate: number;
  };
  monthly_trends: {
    month: string;
    new_subscriptions: number;
    cancellations: number;
    upgrades: number;
    downgrades: number;
    net_growth: number;
  }[];
  behavioral_insights: {
    early_conversion_rate: number;
    avg_basic_duration_days: number;
    upgrade_count: number;
    estimated_ltv: number;
  };
  payment_issues: {
    failed_payments: number;
    pending_retries: number;
    requiring_attention: number;
  };
};


export interface FeedbackAnalytics {
  overview: {
    total_feedback: number
    average_rating: number
    response_rate: number
    improvement_trend: string
  }
  rating_distribution: Record<string, number>
  agent_satisfaction: Array<{
    agent_type: string
    average_rating: number
    total_feedback: number
    satisfaction_trend: string
  }>
  negative_feedback: {
    total_low_ratings: number
    common_issues: Array<{ issue: string; count: number; percentage: number }>
    requires_attention: Array<{
      feedback_id: number
      user_id: number
      rating: number
      comment: string
      created_at: string
      status: string
    }>
  }
}

// 유틸 함수들
export const getStatusIcon = (status: AgentStatus) => {
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

export const getStatusBadge = (status: AgentStatus) => {
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

const agentIconMap: Record<string, string> = {
  business_planning: "3D_사업기획",
  marketing: "3D_마케팅",
  customer_service: "3D_고객관리",
  mental_health: "3D_멘탈케어",
  task_automation: "3D_업무관리",
  task_agent: "3D_업무관리"
}

export const getAgentIcon = (agentType: string) => {
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
