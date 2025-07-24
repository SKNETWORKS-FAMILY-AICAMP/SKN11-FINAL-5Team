export interface AutomationTask {
  task_id: number
  user_id: number
  conversation_id?: number
  task_type: string
  title: string
  template_id?: number
  task_data: {
    content: string
    platform: string
    keywords?: string
  }
  status: string
  scheduled_at?: string | null
  executed_at?: string | null
  created_at: string
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
  contentType: string
}

export type EmailContent = {
  id: number
  user_id: number
  title: string
  content: string
  createdAt: string
}

export interface ContentForm {
  title: string
  content: string
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
