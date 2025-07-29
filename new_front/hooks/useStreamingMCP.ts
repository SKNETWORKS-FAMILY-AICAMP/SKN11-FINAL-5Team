import { useState, useCallback, useRef } from 'react';

interface MCPService {
  name: string;
  icon: string;
  color: string;
  duration: number;
}

interface MCPStep {
  service: string;
  serviceInfo: MCPService;
  status: 'pending' | 'active' | 'completed' | 'error';
  step: number;
  totalSteps: number;
}

interface StreamingMCPState {
  isStreaming: boolean;
  steps: MCPStep[];
  currentMessage: string;
  finalResponse: string | null;
  error: string | null;
}

export const useStreamingMCP = () => {
  const [state, setState] = useState<StreamingMCPState>({
    isStreaming: false,
    steps: [],
    currentMessage: '',
    finalResponse: null,
    error: null
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  const startStreamingQuery = useCallback(async (
    userId: number,
    conversationId: number,
    message: string,
    agentType: string
  ) => {
    // 기존 요청이 있다면 중단
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // 새로운 AbortController 생성
    abortControllerRef.current = new AbortController();

    setState({
      isStreaming: true,
      steps: [],
      currentMessage: 'AI가 분석을 준비하고 있습니다...',
      finalResponse: null,
      error: null
    });

    try {
      console.log('[DEBUG] 스트리밍 쿼리 시작:', { userId, conversationId, message, agentType });
      
      const response = await fetch('http://localhost:8080/query/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          conversation_id: conversationId,
          message,
          preferred_agent: agentType
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            
            if (data === '[DONE]') {
              setState(prev => ({
                ...prev,
                isStreaming: false
              }));
              break;
            }

            try {
              const parsed = JSON.parse(data);
              console.log('[DEBUG] SSE 이벤트 수신:', parsed.type, parsed);
              
              switch (parsed.type) {
                case 'start':
                  setState(prev => ({
                    ...prev,
                    currentMessage: parsed.message
                  }));
                  break;

                case 'mcp_start':
                  setState(prev => ({
                    ...prev,
                    currentMessage: `${parsed.service_info.name} 중...`,
                    steps: [
                      ...prev.steps.map(step => ({ ...step, status: step.status === 'active' ? 'completed' as const : step.status })),
                      {
                        service: parsed.service,
                        serviceInfo: parsed.service_info,
                        status: 'active' as const,
                        step: parsed.step,
                        totalSteps: parsed.total_steps
                      }
                    ]
                  }));
                  break;

                case 'mcp_complete':
                  setState(prev => ({
                    ...prev,
                    steps: prev.steps.map(step => 
                      step.service === parsed.service 
                        ? { ...step, status: parsed.success ? 'completed' as const : 'error' as const }
                        : step
                    )
                  }));
                  break;

                case 'response_generation':
                  setState(prev => ({
                    ...prev,
                    currentMessage: parsed.message
                  }));
                  break;

                case 'final_response':
                  setState(prev => ({
                    ...prev,
                    finalResponse: parsed.response,
                    currentMessage: '완료되었습니다.'
                  }));
                  break;

                case 'error':
                  setState(prev => ({
                    ...prev,
                    error: parsed.message,
                    isStreaming: false
                  }));
                  break;

                case 'done':
                  setState(prev => ({
                    ...prev,
                    isStreaming: false
                  }));
                  break;
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e, 'Data:', data);
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        console.error('Streaming MCP failed:', error);
        setState(prev => ({
          ...prev,
          error: '네트워크 오류가 발생했습니다.',
          isStreaming: false
        }));
      }
    }
  }, []);

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setState(prev => ({
      ...prev,
      isStreaming: false
    }));
  }, []);

  return {
    state,
    startStreamingQuery,
    stopStreaming
  };
};