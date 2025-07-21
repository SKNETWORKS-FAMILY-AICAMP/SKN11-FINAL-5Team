#!/bin/bash

# 모든 에이전트 서비스를 중지하는 스크립트

echo "🛑 모든 에이전트 서비스 중지"
echo "=========================="

# PID 파일들이 있는 디렉토리
LOG_DIR="logs"

# 서비스 중지 함수
stop_service() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo "🔴 $service_name 중지 중... (PID: $pid)"
            kill $pid
            
            # 프로세스가 완전히 종료될 때까지 대기
            local count=0
            while ps -p $pid > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # 강제 종료가 필요한 경우
            if ps -p $pid > /dev/null 2>&1; then
                echo "⚠️  $service_name 강제 종료 중..."
                kill -9 $pid
                sleep 1
            fi
            
            echo "✅ $service_name 종료 완료"
        else
            echo "⚪ $service_name 이미 중지됨"
        fi
        rm -f "$pid_file"
    else
        echo "⚪ $service_name PID 파일 없음"
    fi
}

# 통합 시스템 먼저 중지
stop_service "$LOG_DIR/unified_system.pid" "통합 에이전트 시스템"

# 각 에이전트 중지
stop_service "$LOG_DIR/business_planning.pid" "비즈니스 플래닝 에이전트"
stop_service "$LOG_DIR/customer_service.pid" "고객 서비스 에이전트"
stop_service "$LOG_DIR/marketing.pid" "마케팅 에이전트"
stop_service "$LOG_DIR/mental_health.pid" "멘탈 헬스 에이전트"
stop_service "$LOG_DIR/task_automation.pid" "업무 자동화 에이전트"

echo ""
echo "🔍 남은 프로세스 확인 중..."

# 포트 사용 중인 프로세스 확인 및 정리
check_and_kill_port() {
    local port=$1
    local service_name=$2
    
    local pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "⚠️  포트 $port 사용 중인 프로세스 발견 (PID: $pid) - $service_name"
        kill -9 $pid 2>/dev/null
        echo "🔴 포트 $port 프로세스 강제 종료"
    fi
}

check_and_kill_port 8000 "통합 시스템"
check_and_kill_port 8001 "비즈니스 플래닝"
check_and_kill_port 8002 "고객 서비스"
check_and_kill_port 8003 "마케팅"
check_and_kill_port 8004 "멘탈 헬스"
check_and_kill_port 8005 "업무 자동화"

echo ""
echo "✅ 모든 서비스가 중지되었습니다!"
echo ""
echo "📝 로그 파일 확인:"
echo "  - 통합 시스템: tail logs/unified_system.log"
echo "  - 에이전트별 로그: tail logs/*.log"
echo ""
echo "🗑️  로그 파일 삭제: rm -rf logs/*.log"
echo "🚀 다시 시작: ./start_all.sh"
