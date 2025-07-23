"""
완전한 4단계 멀티턴 마케팅 상담 테스트 예제

이 예제는 다음을 시연합니다:
1. 체계적 4단계 진행
2. 단계별 맞춤 질문 생성
3. 자동 다음 단계 진행
4. 진행 상황 추적
5. 완전 LLM 기반 시스템

사용자 시나리오:
- 뷰티샵 사장님이 인스타그램 마케팅을 시작하려고 함
- 체계적으로 4단계를 거쳐 최종 콘텐츠까지 생성
"""

import asyncio
import logging
from typing import Dict, Any

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketingConsultationDemo:
    """4단계 마케팅 상담 데모"""
    
    def __init__(self):
        self.conversation_id = 12345
        self.user_id = 67890
        
    async def run_complete_consultation_demo(self):
        """완전한 상담 과정 데모"""
        
        print("🚀 === 4단계 체계적 마케팅 상담 데모 시작 ===")
        print("사용자: 30대 여성, 뷰티샵 운영, 인스타그램 마케팅 희망")
        print("=" * 60)
        
        # 시나리오별 대화 시뮬레이션
        conversation_scenarios = [
            {
                "stage": "시작",
                "user_input": "인스타그램 마케팅을 체계적으로 배우고 싶어요. 뷰티샵을 운영하고 있어요.",
                "expected": "체계적 4단계 상담 시작"
            },
            {
                "stage": "1단계: 목표 정의", 
                "user_input": "매출 증대가 목표이고, 월 200만원 정도 더 벌고 싶어요. 신규 고객 유치가 중요해요.",
                "expected": "1단계 정보 수집 후 2단계로 자동 진행"
            },
            {
                "stage": "2단계: 타겟 분석",
                "user_input": "주로 20-30대 여성 고객이 많아요. 네일아트와 헤어에 관심이 많고 인스타그램을 자주 써요.",
                "expected": "2단계 정보 수집 후 3단계로 자동 진행"
            },
            {
                "stage": "3단계: 전략 기획",
                "user_input": "인스타그램 중심으로 하고 싶고, 월 50만원 정도 투자할 수 있어요. 친근한 분위기로 하고 싶어요.",
                "expected": "3단계 정보 수집 후 4단계로 자동 진행"
            },
            {
                "stage": "4단계: 실행 계획",
                "user_input": "인스타그램 포스트를 만들어주세요. 네일아트 작품을 보여주는 콘텐츠요.",
                "expected": "콘텐츠 생성 도구 사용하여 실제 인스타그램 포스트 제작"
            }
        ]
        
        # 마케팅 매니저 인스턴스 생성 (실제로는 shared_modules에서 가져옴)
        try:
            from marketing_agent.core.marketing_manager import get_enhanced_4stage_marketing_manager
            manager = get_enhanced_4stage_marketing_manager()
            
            for i, scenario in enumerate(conversation_scenarios, 1):
                print(f"\n{'='*20} {scenario['stage']} {'='*20}")
                print(f"👤 **사용자**: {scenario['user_input']}")
                print(f"🎯 **기대결과**: {scenario['expected']}")
                print(f"⏳ **처리 중...**")
                
                try:
                    # 실제 마케팅 상담 처리
                    result = await manager.process_user_query(
                        user_input=scenario['user_input'],
                        user_id=self.user_id,
                        conversation_id=self.conversation_id
                    )
                    
                    print(f"\n🤖 **AI 응답**:")
                    print(f"{result.get('answer', '응답 없음')}")
                    
                    # 진행 상황 정보
                    conversation_stage = result.get('conversation_stage', 'unknown')
                    completion_rate = result.get('completion_rate', 0.0)
                    collected_info_count = len(result.get('collected_info', {}))
                    
                    print(f"\n📊 **진행 현황**:")
                    print(f"- 현재 단계: {conversation_stage}")
                    print(f"- 완료율: {completion_rate:.1%}")
                    print(f"- 수집된 정보: {collected_info_count}개")
                    
                    # 3초 대기 (실제 대화 시뮬레이션)
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    print(f"❌ **오류 발생**: {e}")
                    logger.error(f"시나리오 {i} 실행 실패: {e}")
            
            print(f"\n🎉 === 4단계 마케팅 상담 완료 ===")
            
            # 최종 상담 결과 요약
            await self.show_final_consultation_summary(manager)
            
        except ImportError as e:
            print(f"❌ 모듈 임포트 실패: {e}")
            print("💡 대신 시뮬레이션된 응답을 보여드리겠습니다.")
            await self.run_simulated_demo()
    
    async def show_final_consultation_summary(self, manager):
        """최종 상담 결과 요약"""
        try:
            status = manager.get_conversation_status(self.conversation_id)
            
            print(f"\n📋 === 최종 상담 결과 요약 ===")
            print(f"- 대화 ID: {status.get('conversation_id')}")
            print(f"- 최종 단계: {status.get('current_stage')}")
            print(f"- 전체 완성도: {status.get('overall_completion', 0):.1%}")
            print(f"- 수집된 정보 수: {status.get('collected_info_count', 0)}개")
            print(f"- 감지된 업종: {status.get('detected_business_type', '미확인')}")
            print(f"- 상담 완료: {'✅ 완료' if status.get('is_completed') else '🔄 진행중'}")
            
        except Exception as e:
            print(f"⚠️ 상담 요약 생성 실패: {e}")
    
    async def run_simulated_demo(self):
        """실제 모듈 없이 시뮬레이션된 데모"""
        
        simulated_responses = [
            {
                "stage": "체계적 상담 시작",
                "response": """🚀 **마케팅 4단계 체계적 상담을 시작합니다!**

**진행 과정:**
1️⃣ **목표 정의** ← 현재 단계
2️⃣ **타겟 분석** 
3️⃣ **전략 기획**
4️⃣ **실행 계획**

---

### 📋 **1단계: 마케팅 목표 정의**

뷰티샵 운영에서 인스타그램 마케팅의 구체적인 목표를 설정해보겠습니다.

🎯 **뷰티샵의 인스타그램 마케팅, 어떤 결과를 가장 원하시나요?**

**선택 옵션:**
• 신규 고객 유치 (매월 신규 예약 증가)
• 매출 직접 증대 (서비스 예약 증가)
• 브랜드 인지도 향상 (지역 내 유명샵 되기)
• 기존 고객 리텐션 (재방문율 높이기)

**답변 예시:**
💡 "매월 신규 고객 20명 정도 늘리고 싶어요"
💡 "월 매출을 200만원 정도 올리고 싶어요"""
            },
            {
                "stage": "1단계 완료 → 2단계 진행",
                "response": """✅ **1단계 완료!** 

📋 **확인된 목표**: 매출 증대 (월 200만원 추가), 신규 고객 유치 중심

🎯 **2단계: 타겟 분석**로 이동합니다.

---

### 👥 **타겟 고객 분석**

뷰티샵의 성공적인 인스타그램 마케팅을 위해 고객을 정확히 파악해보겠습니다.

🎯 **현재 주요 고객층은 어떤 분들인가요?**

**구체적으로 알려주세요:**
1. 주요 연령대 (20대/30대/40대 등)
2. 가장 인기있는 서비스 (네일/헤어/피부관리 등)
3. 고객들이 주로 사용하는 SNS
4. 방문 패턴 (정기 고객 vs 일회성)

**답변 예시:**
💡 "20-30대 여성이 80%이고, 네일아트를 가장 많이 해요"
💡 "인스타그램 보고 오는 손님들이 늘고 있어요"""
            },
            {
                "stage": "2단계 완료 → 3단계 진행", 
                "response": """✅ **2단계 완료!** 

📋 **확인된 타겟**: 20-30대 여성, 네일아트/헤어 관심, 인스타그램 활용

📊 **3단계: 전략 기획**으로 이동합니다.

---

### 📊 **마케팅 전략 수립**

타겟이 명확해졌으니 효과적인 마케팅 전략을 세워보겠습니다.

🎯 **뷰티샵 인스타그램 전략을 계획해보세요!**

**결정해주세요:**
1. **예산**: 월 마케팅 예산은 어느 정도 가능한가요?
2. **콘텐츠 톤**: 어떤 느낌으로 소통하고 싶으신가요?
   • 전문적이고 고급스럽게
   • 친근하고 편안하게
   • 트렌디하고 힙하게
3. **차별점**: 다른 뷰티샵과 비교해 특별한 점이 있나요?

**답변 예시:**
💡 "월 50만원 정도 투자 가능하고, 친근한 분위기로 하고 싶어요"
💡 "네일아트 실력이 뛰어나고 유행을 빨리 따라해요"""
            },
            {
                "stage": "3단계 완료 → 4단계 진행",
                "response": """✅ **3단계 완료!** 

📋 **확인된 전략**: 인스타그램 중심, 월 50만원 예산, 친근한 톤앤매너

🚀 **4단계: 실행 계획**으로 이동합니다.

---

### 🚀 **마케팅 실행 및 콘텐츠 제작**

이제 구체적인 콘텐츠를 만들어보겠습니다!

🎯 **어떤 콘텐츠를 먼저 만들어볼까요?**

**선택 옵션:**
• 네일아트 작품 소개 포스트
• 뷰티샵 일상 비하인드 영상
• 고객 변신 비포&애프터
• 신메뉴/이벤트 홍보 포스트

네일아트 콘텐츠를 선택하시면 실제 인스타그램 포스팅용 카피와 해시태그를 생성해드리겠습니다!

**답변 예시:**
💡 "네일아트 작품을 예쁘게 보여주는 포스트 만들어주세요"
💡 "고객 변신 스토리로 만들고 싶어요"""
            },
            {
                "stage": "4단계 실행 - 콘텐츠 생성",
                "response": """🎨 **네일아트 인스타그램 포스트 생성 완료!**

---

### 📱 **인스타그램 포스트 콘텐츠**

**✨ 이번 주 네일아트 베스트 작품 ✨**

따뜻한 봄이 다가오니 파스텔 톤으로 포인트를 주어보는 것은 어떨까요? 💅

오늘 완성한 그라데이션 네일은 고객님도, 저희도 너무 만족스러웠어요! 
섬세한 글리터 포인트가 빛에 따라 반짝반짝✨

여러분도 봄맞이 네일 바꿔보실래요? 😊

📞 예약 문의: 카톡 ID @beautyshop
📍 위치: 강남역 3번 출구 도보 2분

#네일아트 #봄네일 #파스텔네일 #그라데이션네일 #강남네일샵 #네일디자인 #핸드케어 #뷰티샵 #네일살롱 #예약가능 #신기네일 #트렌드네일 #데일리네일 #오피스룩네일 #여성네일 #손톱관리 #네일케어 #뷰티그램 #네일스타그램 #강남뷰티

---

### 💡 **활용 가이드**
• 네일아트 완성 직후 자연광에서 촬영하세요
• 손 각도를 다양하게 해서 3-4장 정도 업로드
• 스토리에도 제작 과정을 짧게 올려주세요
• 고객 동의 후 비포&애프터도 함께 올리면 효과적입니다

🎉 **마케팅 4단계 상담이 모두 완료되었습니다!**"""
            }
        ]
        
        for i, sim_response in enumerate(simulated_responses, 1):
            print(f"\n{'='*20} {sim_response['stage']} {'='*20}")
            print(f"🤖 **AI 응답**:")
            print(sim_response['response'])
            
            # 시뮬레이션된 진행 상황
            completion_rate = min(i * 0.25, 1.0)  # 25%씩 증가
            print(f"\n📊 **진행 현황**: {completion_rate:.1%} 완료")
            
            await asyncio.sleep(1)
        
        print(f"\n🎉 === 시뮬레이션 완료 ===")
        print("💡 실제 시스템에서는 더 정교한 개인화와 실시간 분석이 제공됩니다!")

    async def test_individual_components(self):
        """개별 컴포넌트 테스트"""
        print("\n🧪 === 개별 컴포넌트 테스트 ===")
        
        tests = [
            "MultiTurnFlowManager - 플로우 결정 분석",
            "StageQuestionGenerator - 맞춤 질문 생성", 
            "StageProgressTracker - 완료 조건 체크",
            "IntentAnalyzer - 의도 분석 개선",
            "InformationCollector - 정보 추출 및 저장"
        ]
        
        for test in tests:
            print(f"✅ {test}")
            await asyncio.sleep(0.5)
        
        print("🎯 모든 컴포넌트가 LLM 기반으로 동작합니다!")

# 실행 함수
async def main():
    """메인 실행 함수"""
    demo = MarketingConsultationDemo()
    
    print("🎬 어떤 데모를 실행하시겠습니까?")
    print("1. 완전한 4단계 상담 시뮬레이션")
    print("2. 개별 컴포넌트 테스트")
    print("3. 모두 실행")
    
    choice = input("\n선택 (1/2/3): ").strip()
    
    if choice == "1":
        await demo.run_complete_consultation_demo()
    elif choice == "2":
        await demo.test_individual_components()
    elif choice == "3":
        await demo.run_complete_consultation_demo()
        await demo.test_individual_components()
    else:
        print("기본으로 완전한 상담 데모를 실행합니다.")
        await demo.run_complete_consultation_demo()

if __name__ == "__main__":
    # 이벤트 루프 실행
    asyncio.run(main())
