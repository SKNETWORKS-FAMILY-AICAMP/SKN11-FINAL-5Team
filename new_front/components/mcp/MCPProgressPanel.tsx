import React from 'react';
import { MCPStepIndicator } from './MCPStepIndicator';
import { CheckCircle, Loader2 } from 'lucide-react';

interface MCPService {
  name: string;
  icon: string;
  color: string;
  duration: number;
}

interface MCPProgressPanelProps {
  steps: Array<{
    service: string;
    serviceInfo: MCPService;
    status: 'pending' | 'active' | 'completed' | 'error';
    step: number;
    totalSteps: number;
  }>;
  currentMessage?: string;
  agentType: string;
}

export const MCPProgressPanel: React.FC<MCPProgressPanelProps> = ({
  steps,
  currentMessage,
  agentType
}) => {
  const completedSteps = steps.filter(step => step.status === 'completed').length;
  const totalSteps = steps.length;
  const progressPercentage = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;

  const getAgentIcon = () => {
    switch (agentType) {
      case 'marketing':
        return '🎯';
      case 'planner':
        return '📋';
      case 'crm':
        return '🤝';
      case 'task':
        return '⚙️';
      case 'mentalcare':
        return '💚';
      default:
        return '🤖';
    }
  };

  const getAgentName = () => {
    switch (agentType) {
      case 'marketing':
        return '마케팅 에이전트';
      case 'planner':
        return '사업기획 에이전트';
      case 'crm':
        return '고객관리 에이전트';
      case 'task':
        return '업무지원 에이전트';
      case 'mentalcare':
        return '멘탈케어 에이전트';
      default:
        return '통합 에이전트';
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-4 shadow-sm">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg">{getAgentIcon()}</span>
          <h3 className="text-sm font-semibold text-gray-800">
            {getAgentName()}가 데이터를 수집하고 있습니다
          </h3>
        </div>
        <div className="text-xs text-gray-500">
          {completedSteps}/{totalSteps} 완료
        </div>
      </div>

      {/* 전체 진행률 */}
      <div className="space-y-1">
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600">전체 진행률</span>
          <span className="text-xs font-medium text-gray-800">{Math.round(progressPercentage)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>

      {/* 현재 상태 메시지 */}
      {currentMessage && (
        <div className="flex items-center gap-2 p-2 bg-blue-50 rounded-md">
          <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
          <p className="text-sm text-blue-700">{currentMessage}</p>
        </div>
      )}

      {/* MCP 단계들 */}
      <div className="space-y-2">
        {steps.map((step, index) => (
          <MCPStepIndicator
            key={`${step.service}-${index}`}
            service={step.service}
            serviceInfo={step.serviceInfo}
            status={step.status}
            step={step.step}
            totalSteps={step.totalSteps}
          />
        ))}
      </div>

      {/* 완료 메시지 */}
      {completedSteps === totalSteps && totalSteps > 0 && (
        <div className="flex items-center gap-2 p-3 bg-green-50 rounded-md border border-green-200">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <p className="text-sm text-green-700 font-medium">
            데이터 수집이 완료되었습니다. 답변을 생성하고 있습니다...
          </p>
        </div>
      )}
    </div>
  );
};