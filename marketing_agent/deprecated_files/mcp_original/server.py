"""
마케팅 워크플로우 실행기
사용자 정의 5단계 플로우 실행
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from .workflow_manager import MarketingWorkflowManager, run_marketing_workflow
from .workflow_config import WorkflowConfig

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_workflow_header():
    """워크플로우 헤더 출력"""
    print("""
🚀 마케팅 워크플로우 자동화 시스템

📋 워크플로우:
1️⃣ 사용자 입력 해석 (LLM)
2️⃣ 플랫폼 선택 (memory)

[Instagram 경로]
3️⃣ 해시태그 추천 (hashtag-mcp)
4️⃣ 콘텐츠 생성 (vibe-marketing + 해시태그 포함)
5️⃣ 자동 포스팅 (meta-post-scheduler-mcp)

[Naver Blog 경로]  
3️⃣ 키워드 추천 (naver-search-mcp)
4️⃣ 콘텐츠 생성 (vibe-marketing + 키워드 포함)
5️⃣ 자동 포스팅 (puppeteer)

""")

async def demo_instagram_workflow():
    """Instagram 워크플로우 데모"""
    print("📱 Instagram 워크플로우 데모")
    print("="*50)
    
    user_request = "천연 성분으로 만든 프리미엄 스킨케어 세럼을 출시했습니다. 민감성 피부에도 안전하고 보습력이 뛰어납니다."
    
    manager = MarketingWorkflowManager()
    
    print(f"🎯 입력: {user_request}")
    print(f"📱 플랫폼: Instagram")
    print()
    
    try:
        # 1단계: 사용자 입력 해석
        print("1️⃣ 사용자 입력 해석 중...")
        interpreted = await manager.step1_interpret_user_input(user_request)
        print(f"✅ 완료: {interpreted[:100]}...")
        print()
        
        # 2단계: 플랫폼 선택
        print("2️⃣ 플랫폼 선택...")
        platform_info = await manager.step2_select_platform("instagram")
        print(f"✅ 완료: {platform_info}")
        print()
        
        # 3단계: 해시태그 추천
        print("3️⃣ 해시태그 추천 중...")
        hashtags = await manager.step3_get_recommendations()
        print(f"✅ 완료: {hashtags}")
        print()
        
        # 4단계: 콘텐츠 생성
        print("4️⃣ 콘텐츠 생성 중...")
        content = await manager.step4_generate_content()
        print(f"✅ 완료:")
        print(content)
        print()
        
        # 5단계: 자동 포스팅
        print("5️⃣ 자동 포스팅 중...")
        posting_result = await manager.step5_auto_posting()
        print(f"✅ 완료: {posting_result}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

async def demo_naver_blog_workflow():
    """네이버 블로그 워크플로우 데모"""
    print("\n📝 네이버 블로그 워크플로우 데모")
    print("="*50)
    
    user_request = "친환경 비건 화장품 라인을 새롭게 출시합니다. 동물실험을 하지 않으며 모든 성분이 자연에서 추출된 것들입니다."
    
    manager = MarketingWorkflowManager()
    
    print(f"🎯 입력: {user_request}")
    print(f"📝 플랫폼: 네이버 블로그")
    print()
    
    try:
        # 1단계: 사용자 입력 해석
        print("1️⃣ 사용자 입력 해석 중...")
        interpreted = await manager.step1_interpret_user_input(user_request)
        print(f"✅ 완료: {interpreted[:100]}...")
        print()
        
        # 2단계: 플랫폼 선택
        print("2️⃣ 플랫폼 선택...")
        platform_info = await manager.step2_select_platform("naver")
        print(f"✅ 완료: {platform_info}")
        print()
        
        # 3단계: 키워드 추천
        print("3️⃣ 키워드 추천 중...")
        keywords = await manager.step3_get_recommendations()
        print(f"✅ 완료: {keywords}")
        print()
        
        # 4단계: 콘텐츠 생성
        print("4️⃣ 콘텐츠 생성 중...")
        content = await manager.step4_generate_content()
        print(f"✅ 완료:")
        print(content)
        print()
        
        # 5단계: 자동 포스팅
        print("5️⃣ 자동 포스팅 중...")
        posting_result = await manager.step5_auto_posting()
        print(f"✅ 완료: {posting_result}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

async def demo_full_workflow():
    """전체 워크플로우 한 번에 실행 데모"""
    print("\n🎯 전체 워크플로우 통합 실행 데모")
    print("="*60)
    
    # Instagram 전체 워크플로우
    print("📱 Instagram 전체 워크플로우")
    instagram_request = "신개념 스마트워치를 출시합니다. 건강 모니터링과 피트니스 트래킹 기능이 뛰어납니다."
    
    instagram_result = await run_marketing_workflow(instagram_request, "instagram")
    
    if instagram_result['success']:
        print("✅ Instagram 워크플로우 성공!")
        print("📊 실행 로그:")
        for log in instagram_result['workflow_log']:
            print(f"  {log}")
        print()
        print("📱 최종 결과:")
        print(instagram_result['final_result']['content'])
    else:
        print("❌ Instagram 워크플로우 실패:")
        print(instagram_result.get('error', '알 수 없는 오류'))
    
    print("\n" + "="*60)
    
    # 네이버 블로그 전체 워크플로우  
    print("📝 네이버 블로그 전체 워크플로우")
    blog_request = "홈카페 원두 구독 서비스를 시작합니다. 매월 다른 나라의 프리미엄 원두를 배송해드립니다."
    
    blog_result = await run_marketing_workflow(blog_request, "blog")
    
    if blog_result['success']:
        print("✅ 네이버 블로그 워크플로우 성공!")
        print("📊 실행 로그:")
        for log in blog_result['workflow_log']:
            print(f"  {log}")
        print()
        print("📝 최종 결과:")
        print(blog_result['final_result']['content'])
    else:
        print("❌ 네이버 블로그 워크플로우 실패:")
        print(blog_result.get('error', '알 수 없는 오류'))

async def interactive_workflow():
    """사용자 인터랙티브 워크플로우"""
    print("\n🤝 인터랙티브 워크플로우")
    print("="*40)
    
    try:
        # 사용자 입력 받기
        user_request = input("📝 마케팅할 제품/서비스를 설명해주세요: ")
        
        if not user_request.strip():
            print("❌ 입력이 없습니다.")
            return
        
        # 플랫폼 선택
        print("\n📱 플랫폼을 선택해주세요:")
        print("1. Instagram")
        print("2. 네이버 블로그")
        
        platform_choice = input("선택 (1 또는 2): ").strip()
        
        if platform_choice == "1":
            platform = "instagram"
        elif platform_choice == "2":
            platform = "blog"
        else:
            print("⚠️  잘못된 선택. Instagram으로 기본 설정합니다.")
            platform = "instagram"
        
        print(f"\n🚀 {platform.upper()} 워크플로우 시작...")
        print("⏳ 처리 중... (최대 1분 소요)")
        
        # 워크플로우 실행
        result = await run_marketing_workflow(user_request, platform)
        
        if result['success']:
            print("\n✅ 워크플로우 완료!")
            print("\n📊 실행 단계:")
            for i, log in enumerate(result['workflow_log'], 1):
                print(f"{i:2d}. {log}")
            
            print("\n🎯 최종 마케팅 콘텐츠:")
            print("-" * 50)
            print(result['final_result']['content'])
            print("-" * 50)
            
            print(f"\n📤 포스팅 결과:")
            print(result['final_result']['posting_result'])
            
        else:
            print(f"\n❌ 워크플로우 실패: {result.get('error', '알 수 없는 오류')}")
            
    except KeyboardInterrupt:
        print("\n⏹️  사용자가 중단했습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")

async def main():
    """메인 실행 함수"""
    print_workflow_header()
    
    print("🎮 실행 모드를 선택해주세요:")
    print("1. Instagram 워크플로우 데모")
    print("2. 네이버 블로그 워크플로우 데모") 
    print("3. 전체 워크플로우 통합 데모")
    print("4. 인터랙티브 모드")
    print("5. 모든 데모 실행")
    
    try:
        choice = input("\n선택 (1-5): ").strip()
        
        start_time = datetime.now()
        
        if choice == "1":
            await demo_instagram_workflow()
        elif choice == "2":
            await demo_naver_blog_workflow()
        elif choice == "3":
            await demo_full_workflow()
        elif choice == "4":
            await interactive_workflow()
        elif choice == "5":
            await demo_instagram_workflow()
            await demo_naver_blog_workflow()
            await demo_full_workflow()
        else:
            print("⚠️  잘못된 선택. Instagram 데모를 실행합니다.")
            await demo_instagram_workflow()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n⏱️  총 실행 시간: {duration:.1f}초")
        print("🎉 워크플로우 시연 완료!")
        
    except KeyboardInterrupt:
        print("\n⏹️  사용자가 중단했습니다.")
    except Exception as e:
        print(f"\n❌ 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
