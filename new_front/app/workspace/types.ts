export interface AutomationTask {
  task_id: number
  user_id?: number
  task_type: string
  title: string
  task_data: {
    platform: string
    content?: string
    full_content?: string
    post_content?: string
    searched_hashtags?: string[]
    top_keywords?: string[]
    image_url?: string
  }
  status: string
  created_at: string
  scheduled_at?: string
}


export interface ScheduleEvent {
  id: number
  title: string
  date: string
  time: string
  description: string
  type: "manual" | "automation"
}

export interface ContentTemplate {
  id: number
  title: string
  content: string
  createdAt: string       
  contentType: string     
}

export interface EmailTemplate {
  id: number
  user_id: number 
  title: string
  content: string
  createdAt: string
  template_type: string
}

export type EmailContent = {
  id: number
  user_id: number
  title: string
  content: string
  createdAt: string
  template_type: string
}

export interface ContentForm {
    title: string
  content: string
  task_data?: {
    platform: string
    post_content?: string
    full_content?: string
    searched_hashtags?: string[]
    top_keywords?: string[]
  }
}

export interface PublishSchedule {
  date: string
  time: string
  type: "immediate" | "scheduled"
}

export interface NewEvent {
  title: string
  date: string
  time: string
  description: string
}

export interface ContentItem {
  id: number
  title: string
  type: "instagram" | "blog" | "email"
  created_at: string
}

export interface WorkspaceData {
  email_templates: EmailTemplate[],   // 관리자 템플릿
  email_contents: EmailContent[]      // 사용자 콘텐츠
}

export interface AiGeneratedContent extends AutomationTask {
  task_data: {
    content: string
    platform: string
  }
}

export interface InstagramTaskData {
  post_content: string
  selected_hashtags?: string[]
}

export interface BlogTaskData {
  full_content: string
  keywords?: string[]
}

export interface GoogleCalendarEvent {
  id: string
  summary?: string
  description?: string
  start: {
    dateTime?: string
    date?: string
  }
  end: {
    dateTime?: string
    date?: string
  }
  status?: string
  htmlLink?: string
  [key: string]: any // 유연성을 위해 기타 필드 허용
}

export interface EventCreate {
  title: string
  description?: string
  start_time: string // ISO string (e.g., "2025-07-30T15:00:00")
  end_time: string   // ISO string
  calendar_id?: string // optional, default: "primary"
  timezone?: string // optional, default: "Asia/Seoul"
}