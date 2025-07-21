#!/bin/bash

# 모든 에이전트를 동시에 실행하는 스크립트

echo "🚀 모든 에이전트 서버 시작"
echo "========================="

# 프로젝트 루트 디렉토리
PROJECT_ROOT="/Users/comet39/SKN_PJT/SKN11-FINAL-5Team_v2"

# 로그 디렉토리 생성
mkdir -p logs

# 각 에이전트를 백그라운드에서 실행
echo "💼 비즈니스 플래닝 에이전트 시작 (포트 8001)..."
cd "$PROJECT_ROOT/buisness_planning_agent"
nohup uvicorn business_planning:app --host 0.0.0.0 --port 8001 > ../unified_agent_system/logs/business_planning.log 2>&1 &
BUSINESS_PID=$!

echo "🤝 고객 서비스 에이전트 시작 (포트 8002)..."
cd "$PROJECT_ROOT/customer_service_agent"
nohup uvicorn customer_agent.main:app --host 0.0.0.0 --port 8002 > ../unified_agent_system/logs/customer_service.log 2>&1 &
CUSTOMER_PID=$!

echo "📢 마케팅 에이전트 시작 (포트 8003)..."
cd "$PROJECT_ROOT/marketing_agent"
nohup uvicorn rag:app --host 0.0.0.0 --port 8003 > ../unified_agent_system/logs/marketing.log 2>&1 &
MARKETING_PID=$!

echo "🧠 멘탈 헬스 에이전트 시작 (포트 8004)..."
cd "$PROJECT_ROOT/mental_agent"
nohup uvicorn main:app --host 0.0.0.0 --port 8004 > ../unified_agent_system/logs/mental_health.log 2>&1 &
MENTAL_PID=$!

echo "⚡ 업무 자동화 에이전트 시작 (포트 8005)..."
cd "$PROJECT_ROOT/task_agent"
nohup uvicorn main:app --host 0.0.0.0 --port 8005 > ../unified_agent_system/logs/task_automation.log 2>&1 &
TASK_PID=$!

# PID 저장
echo "$BUSINESS_PID" > ../unified_agent_system/logs/business_planning.pid
echo "$CUSTOMER_PID" > ../unified_agent_system/logs/customer_service.pid
echo "$MARKETING_PID" > ../unified_agent_system/logs/marketing.pid
echo "$MENTAL_PID" > ../unified_agent_system/logs/mental_health.pid
echo "$TASK_PID" > ../unified_agent_system/logs/task_automation.pid

echo ""
echo "⏳ 에이전트들이 시작되는 동안 10초 대기..."
sleep 10

echo ""
echo "🔍 에이전트 상태 확인 중..."

# 각 에이전트 상태 확인
check_service() {
    local port=$1
    local name=$2
    
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "✅ $name (포트 $port): 정상"
    else
        echo "❌ $name (포트 $port): 연결 실패"
    fi
}

check_service 8001 "비즈니스 플래닝"
check_service 8002 "고객 서비스"
check_service 8003 "마케팅"
check_service 8004 "멘탈 헬스"
check_service 8005 "업무 자동화"

echo ""
echo "🤖 통합 에이전트 시스템 시작 (포트 8000)..."
cd "$PROJECT_ROOT/unified_agent_system"
nohup python main.py > logs/unified_system.log 2>&1 &
UNIFIED_PID=$!
echo "$UNIFIED_PID" > logs/unified_system.pid

echo ""
echo "✅ 모든 서비스가 시작되었습니다!"
echo ""
echo "📊 서비스 URL:"
echo "  - 통합 시스템: http://localhost:8000"
echo "  - API 문서: http://localhost:8000/docs"
echo "  - 비즈니스 플래닝: http://localhost:8001/docs"
echo "  - 고객 서비스: http://localhost:8002/docs"
echo "  - 마케팅: http://localhost:8003/docs"
echo "  - 멘탈 헬스: http://localhost:8004/docs"
echo "  - 업무 자동화: http://localhost:8005/docs"
echo ""
echo "📝 로그 파일:"
echo "  - tail -f logs/unified_system.log"
echo "  - tail -f logs/business_planning.log"
echo "  - tail -f logs/customer_service.log"
echo "  - tail -f logs/marketing.log"
echo "  - tail -f logs/mental_health.log"
echo "  - tail -f logs/task_automation.log"
echo ""
echo "🛑 서비스 중지: ./stop_all.sh"
