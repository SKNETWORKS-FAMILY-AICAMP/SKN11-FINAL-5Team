import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface SocialLoginResponse {
  user_id: number;
  username: string;
  email: string;
  is_new_user: boolean;
}

export const authApi = {
  socialLogin: async (provider: string, socialId: string, username: string, email: string): Promise<SocialLoginResponse> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/social_login`, {
        provider,
        social_id: socialId,
        username,
        email
      });
      
      if (response.data.success) {
        return response.data.data;
      }
      throw new Error(response.data.message || '로그인에 실패했습니다');
    } catch (error) {
      console.error('Social login error:', error);
      throw error;
    }
  }
};