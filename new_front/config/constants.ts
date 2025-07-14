// API 기본 URL 설정
export const API_BASE_URL = 'http://localhost:8000'

// 에이전트 포트 매핑
export const AGENT_PORTS = {
  unified_agent: 8000,
  planner: 8001,
  marketing: 8002,
  crm: 8003,
  task: 8004,
  mentalcare: 8005,
} as const

// 에이전트 타입
export type AgentType = keyof typeof AGENT_PORTS

// 에이전트 설정
export const AGENT_CONFIG = {
  unified_agent: {
    name: '통합 에이전트',
    description: '모든 분야를 아우르는 통합 AI 상담',
    icon: '/icons/3D_새채팅.png',
  },
  planner: {
    name: '사업기획',
    description: '사업 계획 및 전략 수립 지원',
    icon: '/icons/3D_사업기획.png',
  },
  marketing: {
    name: '마케팅',
    description: '효과적인 마케팅 전략 제안',
    icon: '/icons/3D_마케팅.png',
  },
  crm: {
    name: '고객관리',
    description: '고객 관계 관리 및 서비스 개선',
    icon: '/icons/3D_고객관리.png',
  },
  task: {
    name: '업무지원',
    description: '업무 자동화 및 효율화 지원',
    icon: '/icons/3D_업무관리.png',
  },
  mentalcare: {
    name: '멘탈케어',
    description: '심리 상담 및 스트레스 관리',
    icon: '/icons/3D_멘탈케어.png',
  },
} as const