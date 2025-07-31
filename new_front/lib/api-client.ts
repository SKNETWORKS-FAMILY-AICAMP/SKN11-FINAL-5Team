// lib/api-client.ts
/**
 * 백엔드 API와 통신하는 클라이언트
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  timestamp?: string;
}

export interface BlogAutomationConfig {
  enabled: boolean;
  keywords: string[];
  schedule: {
    frequency: 'daily' | 'weekly' | 'monthly' | 'custom';
    time: string;
    days?: string[];
  };
  template?: string;
  auto_publish: boolean;
  target_platform: string;
  blog_id?: string;
  category?: string;
  tags?: string[];
}

export interface InstagramAutomationConfig {
  enabled: boolean;
  hashtags: string[];
  schedule: {
    frequency: 'daily' | 'weekly' | 'monthly' | 'custom';
    time: string;
    days?: string[];
  };
  templates?: string[];
  auto_post: boolean;
  image_folder?: string;
  image_style?: string;
  account_id?: string;
  max_hashtags?: number;
}

export interface ContentGenerationRequest {
  keyword?: string;
  hashtags?: string[];
  template?: string;
  platform: string;
  auto_upload?: boolean;
  auto_post?: boolean;
  image_style?: string;
  blog_config?: any;
  instagram_config?: any;
}

class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<APIResponse<T>> {
    try {
      const url = `${this.baseURL}${endpoint}`;
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  // ============= 블로그 자동화 API =============

  async setupBlogAutomation(config: BlogAutomationConfig): Promise<APIResponse> {
    return this.request('/blog/setup', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getBlogAutomationStatus(): Promise<APIResponse> {
    return this.request('/blog/status');
  }

  async generateBlogContent(request: ContentGenerationRequest): Promise<APIResponse> {
    return this.request('/blog/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getBlogPosts(params: {
    page?: number;
    limit?: number;
    keyword?: string;
    status?: string;
  } = {}): Promise<APIResponse> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, value.toString());
      }
    });
    
    return this.request(`/blog/posts?${searchParams.toString()}`);
  }

  // ============= 인스타그램 자동화 API =============

  async setupInstagramAutomation(config: InstagramAutomationConfig): Promise<APIResponse> {
    return this.request('/instagram/setup', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getInstagramAutomationStatus(): Promise<APIResponse> {
    return this.request('/instagram/status');
  }

  async generateInstagramContent(request: ContentGenerationRequest): Promise<APIResponse> {
    return this.request('/instagram/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getInstagramPosts(params: {
    page?: number;
    limit?: number;
    hashtag?: string;
    status?: string;
  } = {}): Promise<APIResponse> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, value.toString());
      }
    });
    
    return this.request(`/instagram/posts?${searchParams.toString()}`);
  }

  // ============= 키워드 분석 API =============

  async analyzeKeyword(keyword: string): Promise<APIResponse> {
    return this.request(`/keywords/analyze?keyword=${encodeURIComponent(keyword)}`);
  }

  async getKeywords(): Promise<APIResponse> {
    return this.request('/keywords');
  }

  async addKeyword(keyword: string): Promise<APIResponse> {
    return this.request('/keywords', {
      method: 'POST',
      body: JSON.stringify({ keyword }),
    });
  }

  async deleteKeyword(keywordId: string): Promise<APIResponse> {
    return this.request(`/keywords?id=${keywordId}`, {
      method: 'DELETE',
    });
  }

  // ============= 자동화 상태 제어 API =============

  async toggleAutomation(type: 'blog' | 'instagram', action: 'start' | 'pause'): Promise<APIResponse> {
    return this.request('/automation/status', {
      method: 'POST',
      body: JSON.stringify({ type, action }),
    });
  }

  async forceRunAutomation(type: 'blog' | 'instagram'): Promise<APIResponse> {
    return this.request('/automation/status', {
      method: 'PATCH',
      body: JSON.stringify({ type }),
    });
  }

  async getAutomationStatus(): Promise<APIResponse> {
    return this.request('/automation/status');
  }

  // ============= 대시보드 통계 API =============

  async getDashboardStats(params: {
    period?: number;
    detailed?: boolean;
  } = {}): Promise<APIResponse> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, value.toString());
      }
    });
    
    return this.request(`/dashboard/stats?${searchParams.toString()}`);
  }

  async updateMetric(metric: string, value: number, automation?: string): Promise<APIResponse> {
    return this.request('/dashboard/metric', {
      method: 'POST',
      body: JSON.stringify({ metric, value, automation }),
    });
  }

  // ============= 활동 로그 API =============

  async getActivityLogs(params: {
    page?: number;
    limit?: number;
    type?: string;
    status?: string;
  } = {}): Promise<APIResponse> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, value.toString());
      }
    });
    
    return this.request(`/activity/logs?${searchParams.toString()}`);
  }

  // ============= 분석 API =============

  async getBlogAnalytics(startDate: string, endDate: string): Promise<APIResponse> {
    return this.request(`/blog/analytics?start_date=${startDate}&end_date=${endDate}`);
  }

  async getInstagramAnalytics(startDate: string, endDate: string): Promise<APIResponse> {
    return this.request(`/instagram/analytics?start_date=${startDate}&end_date=${endDate}`);
  }

  // ============= 헬스체크 API =============

  async healthCheck(): Promise<APIResponse> {
    return this.request('/');
  }
}

// 싱글톤 인스턴스 생성
export const apiClient = new APIClient();

// 타입 exports
export type { APIResponse, BlogAutomationConfig, InstagramAutomationConfig, ContentGenerationRequest };
