import React from 'react';
import { 
  Search, 
  Hash, 
  ShoppingCart, 
  Youtube, 
  Smartphone, 
  Globe, 
  CheckCircle, 
  XCircle,
  Loader2,
  TrendingUp,
  Sparkles
} from 'lucide-react';

interface MCPService {
  name: string;
  icon: string;
  color: string;
  duration: number;
}

interface MCPStepProps {
  service: string;
  serviceInfo: MCPService;
  status: 'pending' | 'active' | 'completed' | 'error';
  step: number;
  totalSteps: number;
}

const iconMap = {
  'search': Search,
  'hash': Hash,
  'shopping-cart': ShoppingCart,
  'youtube': Youtube,
  'smartphone': Smartphone,
  'globe': Globe,
  'trending-up': TrendingUp,
  'sparkles': Sparkles
};

export const MCPStepIndicator: React.FC<MCPStepProps> = ({
  service,
  serviceInfo,
  status,
  step,
  totalSteps
}) => {
  const IconComponent = iconMap[serviceInfo.icon as keyof typeof iconMap] || Globe;
  
  const getStatusColor = () => {
    switch (status) {
      case 'active':
        return 'border-blue-500 bg-blue-50';
      case 'completed':
        return 'border-green-500 bg-green-50';
      case 'error':
        return 'border-red-500 bg-red-50';
      default:
        return 'border-gray-300 bg-gray-50';
    }
  };

  const getIconColor = () => {
    switch (status) {
      case 'active':
        return 'text-blue-600';
      case 'completed':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className={`flex items-center gap-3 p-3 rounded-lg border-2 transition-all duration-300 ${getStatusColor()}`}>
      {/* 단계 번호 */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
        status === 'active' ? 'bg-blue-500 text-white' :
        status === 'completed' ? 'bg-green-500 text-white' :
        status === 'error' ? 'bg-red-500 text-white' :
        'bg-gray-300 text-gray-600'
      }`}>
        {status === 'completed' ? (
          <CheckCircle className="w-5 h-5" />
        ) : status === 'error' ? (
          <XCircle className="w-5 h-5" />
        ) : (
          step
        )}
      </div>

      {/* 서비스 아이콘 */}
      <div className={`flex-shrink-0 p-2 rounded-full ${getIconColor()}`}
           style={{ backgroundColor: status === 'active' ? `${serviceInfo.color}20` : undefined }}>
        {status === 'active' ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : (
          <IconComponent className="w-5 h-5" />
        )}
      </div>

      {/* 서비스 정보 */}
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium ${
          status === 'active' ? 'text-blue-700' :
          status === 'completed' ? 'text-green-700' :
          status === 'error' ? 'text-red-700' :
          'text-gray-600'
        }`}>
          {serviceInfo.name}
        </p>
        <p className="text-xs text-gray-500">
          {status === 'active' && '진행 중...'}
          {status === 'completed' && '완료됨'}
          {status === 'error' && '오류 발생'}
          {status === 'pending' && '대기 중'}
        </p>
      </div>

      {/* 진행 상태 표시 */}
      {status === 'active' && (
        <div className="flex-shrink-0">
          <div className="w-12 h-1 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-blue-500 rounded-full animate-pulse"
              style={{ 
                width: '70%',
                animation: 'progress-bar 2s ease-in-out infinite'
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};