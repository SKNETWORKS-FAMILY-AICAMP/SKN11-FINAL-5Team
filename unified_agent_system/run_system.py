#!/usr/bin/env python3
"""
통합 에이전트 시스템 원클릭 실행 스크립트

이 스크립트는 시스템 설정부터 실행까지 모든 과정을 자동화합니다.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path


def print_banner():
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║           🤖 통합 에이전트 시스템 v1.0               ║
    ║                                                      ║
    ║     5개의 전문 AI 에이전트 통합 플랫폼                ║
    ║     LangGraph 기반 지능형 라우팅 시스템              ║
    ╚══════════════════════════════════════════════════════╝
    """)


def check_python_version():
    """Python 버전 확인"""
    print("🐍 Python 버전 확인 중...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 이상이 필요합니다.")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} 감지됨")


def check_requirements():
    """필수 파일들 확인"""
    print("📋 필수 파일 확인 중...")
    
    required_files = [
        "requirements.txt",
        "main.py",
        ".env",
        "core/workflow.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 필수 파일 없음: {', '.join(missing_files)}")
        sys.exit(1)
    
    print("✅ 모든 필수 파일 확인됨")


def setup_environment():
    """환경 설정"""
    print("🔧 환경 설정 중...")
    
    # 로그 디렉토리 생성
    Path("logs").mkdir(exist_ok=True)
    print("📂 로그 디렉토리 생성됨")


def install_dependencies():
    """의존성 설치"""
    print("📦 의존성 설치 중...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True)
        print("✅ 의존성 설치 완료")
    except subprocess.CalledProcessError as e:
        print(f"❌ 의존성 설치 실패: {e}")
        print("수동으로 설치해주세요: pip install -r requirements.txt")
        sys.exit(1)


def check_ports():
    """포트 사용 확인"""
    print("🔍 포트 사용 상태 확인 중...")
    
    ports_to_check = {
        8080: "통합 시스템",
        8001: "비즈니스 플래닝",
        8002: "고객 서비스", 
        8003: "마케팅",
        8004: "멘탈 헬스",
        8005: "업무 자동화"
    }
    
    busy_ports = []
    
    for port, service in ports_to_check.items():
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                busy_ports.append(f"{port} ({service})")
        except:
            pass
    
    if busy_ports:
        print(f"⚠️  사용 중인 포트: {', '.join(busy_ports)}")
        response = input("계속 진행하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            print("설정을 중단합니다.")
            sys.exit(0)
    else:
        print("✅ 모든 포트 사용 가능")


def start_system():
    """시스템 시작"""
    print("🚀 통합 에이전트 시스템 시작 중...")
    
    # main.py 실행
    try:
        print("서버 시작 중... (Ctrl+C로 중지)")
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n👋 시스템을 종료합니다.")
    except Exception as e:
        print(f"❌ 시스템 시작 실패: {e}")


def test_system():
    """시스템 테스트"""
    print("🧪 시스템 연결 테스트 중...")
    
    time.sleep(3)  # 서버 시작 대기
    
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            print("✅ 시스템 정상 작동 중")
            print("🌐 접속 URL:")
            print("  - 메인 페이지: http://localhost:8080")
            print("  - 테스트 UI: http://localhost:8080/test-ui")
            print("  - API 문서: http://localhost:8080/docs")
            return True
        else:
            print(f"⚠️  응답 코드: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 연결 실패: {e}")
        return False


def main():
    """메인 함수"""
    print_banner()
    
    try:
        # 1. 기본 환경 확인
        check_python_version()
        check_requirements()
        
        # 2. 환경 설정
        setup_environment()
        
        # 3. 의존성 설치
        install_dependencies()
        
        # 4. 포트 확인
        check_ports()
        
        print("\n🎉 설정 완료! 시스템을 시작합니다...")
        print("=" * 60)
        
        # 5. 시스템 시작
        start_system()
        
    except KeyboardInterrupt:
        print("\n👋 설치를 중단합니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
