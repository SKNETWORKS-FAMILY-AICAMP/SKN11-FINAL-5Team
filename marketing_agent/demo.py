"""
마케팅 에이전트 데모 - 완전 LLM 기반 버전
자연스럽고 지능적인 멀티턴 마케팅 상담 시연
"""

import asyncio
import logging
from datetime import datetime
from marketing_agent import MarketingAgent

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedMarketingDemo:
    """완전 LLM 기반 마케팅 상담 데모"""
    
    def __init__(self):
        self.agent = MarketingAgent()
        self.demo_scenarios = self._create_llm_demo_scenarios()
    
    def _create_llm_demo_scenarios(self):
        """LLM 기반 데모 시나리오 생성"""
        return {
            "스마트_카페_마케팅": [
                "안녕하세요! 카페 마케팅 상담을 받고 싶어요",
                "홍대에서 감성 카페를 운영하고 있어요. 20-30대 고객들이 주로 와요",
                "매출을 늘리면서 동시에 브랜드 이미지도 좋아지면 좋겠어요",
                "인스타그램 마케팅에 집중하고 싶고, 월 50만원 정도 투자할 수 있어요",
                "따뜻하고 감성적인 인스타그램 포스트를 만들어주세요"
            ],
            "전문_뷰티샵_컨설팅": [
                "네일아트 전문 뷰티샵 사장이에요. 전문적인 마케팅 전략이 필요해요",
                "강남역 근처에 위치하고, 20-40대 직장여성이 주요 고객층이에요", 
                "예약률을 높이고 재방문율을 올리는 것이 목표예요",
                "네이버 블로그와 인스타그램을 활용하고 싶어요",
                "네일아트 트렌드를 반영한 전체 마케팅 전략을 세워주세요"
            ],
            "혁신_온라인쇼핑몰": [
                "패션 온라인쇼핑몰을 런칭하려고 해요. 처음부터 제대로 시작하고 싶어요",
                "20대 여성 타겟의 데일리 캐주얼 브랜드에요",
                "론칭 후 6개월 내 월 매출 5000만원이 목표예요",
                "SNS광고와 인플루언서 마케팅에 집중하려고 해요",
                "론칭 캠페인부터 장기 전략까지 모든 걸 계획해주세요"
            ],
            "자유_상담": [
                "마케팅에 대해 궁금한 게 많아요. 자유롭게 질문해봐도 될까요?"
            ]
        }
    
    async def run_demo(self, scenario_name: str = "스마트_카페_마케팅"):
        """LLM 기반 데모 실행"""
        print(f"\n🎬 === {scenario_name} 데모 시작 ===")
        print("💡 **완전 LLM 기반 자연어 이해 및 응답**")
        print("=" * 60)
        
        if scenario_name not in self.demo_scenarios:
            print(f"❌ 시나리오를 찾을 수 없습니다: {scenario_name}")
            return
        
        messages = self.demo_scenarios[scenario_name]
        user_id = 12345
        conversation_id = None
        
        for i, message in enumerate(messages, 1):
            print(f"\n{'='*20} {i}단계 {'='*20}")
            print(f"👤 **사용자**: {message}")
            print("🤖 **LLM 분석 및 응답 생성 중...**")
            
            try:
                # LLM 기반 마케팅 에이전트 처리
                result = await self.agent.process_message(
                    user_input=message,
                    user_id=user_id,
                    conversation_id=conversation_id
                )
                
                if result.get("success"):
                    data = result["data"]
                    conversation_id = data["conversation_id"]
                    
                    print(f"\n🧠 **AI 마케팅 전문가** (LLM 기반):")
                    print(data["answer"])
                    
                    # 지능형 분석 정보 표시
                    print(f"\n📊 **LLM 분석 결과**:")
                    print(f"  • 현재 단계: {data['current_stage']}")
                    print(f"  • 완료율: {data['completion_rate']:.1%}")
                    print(f"  • 수집된 정보: {len(data['collected_info'])}개")
                    print(f"  • 처리 시간: {data['processing_time']:.2f}초")
                    print(f"  • LLM 기반: {data.get('llm_powered', True)}")
                    
                    # 도구 결과가 있으면 표시
                    if data.get("tool_results"):
                        tool_type = data['tool_results'].get('type', '알 수 없음')
                        print(f"  • 생성된 콘텐츠: {tool_type}")
                        print(f"  • 생성 성공: {data['tool_results'].get('success', False)}")
                
                else:
                    print(f"❌ **오류 발생**: {result.get('error')}")
                
            except Exception as e:
                print(f"❌ **처리 실패**: {e}")
                logger.error(f"데모 {i}단계 실패: {e}")
            
            # 다음 단계까지 딜레이
            await asyncio.sleep(2)
        
        print(f"\n🎉 === {scenario_name} 데모 완료 ===")
        
        # 최종 대화 품질 분석
        if conversation_id:
            await self._show_conversation_quality_analysis(conversation_id)
    
    async def _show_conversation_quality_analysis(self, conversation_id: int):
        """LLM 기반 대화 품질 분석 표시"""
        try:
            print(f"\n🔍 **LLM 기반 대화 품질 분석 중...**")
            
            quality_result = await self.agent.analyze_conversation_quality(conversation_id)
            
            if quality_result.get("success"):
                print(f"\n📈 **대화 품질 분석 결과**:")
                analysis = quality_result.get("quality_analysis", {})
                
                if "raw_response" in analysis:
                    print(analysis["raw_response"])
                else:
                    print("품질 분석이 완료되었습니다.")
            else:
                print(f"⚠️ 품질 분석 실패: {quality_result.get('error')}")
                
        except Exception as e:
            logger.warning(f"품질 분석 표시 실패: {e}")
    
    async def run_interactive_llm_demo(self):
        """완전 LLM 기반 대화형 데모"""
        print("\n💬 === LLM 기반 대화형 마케팅 상담 ===")
        print("🧠 완전히 자연어로 이해하고 전문적으로 응답합니다!")
        print("종료하려면 'quit' 또는 'exit'를 입력하세요.\n")
        
        user_id = 99999
        conversation_id = None
        
        while True:
            try:
                user_input = input("👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '종료', '그만']:
                    print("👋 LLM 기반 마케팅 상담을 종료합니다!")
                    break
                
                if not user_input:
                    continue
                
                print("🤖 LLM 분석 중...")
                
                result = await self.agent.process_message(
                    user_input=user_input,
                    user_id=user_id,
                    conversation_id=conversation_id
                )
                
                if result.get("success"):
                    data = result["data"]
                    conversation_id = data["conversation_id"]
                    
                    print(f"\n🧠 AI: {data['answer']}")
                    print(f"📊 진행률: {data['completion_rate']:.1%} | 단계: {data['current_stage']} | ⚡LLM기반")
                
                else:
                    print(f"❌ 오류: {result.get('error')}")
                
                print("-" * 50)
                
            except KeyboardInterrupt:
                print("\n👋 마케팅 상담을 종료합니다!")
                break
            except Exception as e:
                print(f"❌ 처리 실패: {e}")
    
    def show_llm_demo_menu(self):
        """LLM 기반 데모 메뉴 표시"""
        print("🧠 LLM 기반 마케팅 에이전트 데모 - 완전 지능형 버전")
        print("=" * 60)
        print("🎯 **주요 특징:**")
        print("  • 완전 자연어 이해 및 의도 분석")
        print("  • 맥락적 단계 진행 및 응답 생성")
        print("  • 업종별 맞춤화된 질문 및 조언")
        print("  • 실시간 콘텐츠 생성 및 전략 수립")
        print("-" * 60)
        print("선택 가능한 데모:")
        print("1. 스마트 카페 마케팅 상담")
        print("2. 전문 뷰티샵 컨설팅") 
        print("3. 혁신 온라인쇼핑몰 전략")
        print("4. LLM 기반 대화형 데모 (자유 대화)")
        print("5. 에이전트 지능 상태 확인")
        print("6. 대화 품질 테스트")
        print("0. 종료")
        print("=" * 60)
    
    async def run(self):
        """메인 실행"""
        while True:
            self.show_llm_demo_menu()
            
            try:
                choice = input("선택하세요 (0-6): ").strip()
                
                if choice == "0":
                    print("👋 LLM 기반 데모를 종료합니다!")
                    break
                elif choice == "1":
                    await self.run_demo("스마트_카페_마케팅")
                elif choice == "2":
                    await self.run_demo("전문_뷰티샵_컨설팅")
                elif choice == "3":
                    await self.run_demo("혁신_온라인쇼핑몰")
                elif choice == "4":
                    await self.run_interactive_llm_demo()
                elif choice == "5":
                    await self.show_llm_agent_status()
                elif choice == "6":
                    await self.run_quality_test()
                else:
                    print("❌ 잘못된 선택입니다. 0-6 사이의 숫자를 입력해주세요.")
                
                input("\n계속하려면 Enter를 누르세요...")
                print("\n")
                
            except KeyboardInterrupt:
                print("\n👋 데모를 종료합니다!")
                break
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
    
    async def show_llm_agent_status(self):
        """LLM 기반 에이전트 상태 표시"""
        try:
            status = self.agent.get_agent_status()
            
            print("\n🧠 **LLM 기반 에이전트 상태 정보**")
            print("=" * 50)
            print(f"버전: {status.get('version')}")
            print(f"지능 유형: {status.get('intelligence_type')}")
            print(f"서비스: {status.get('service_name')}")
            print(f"상태: {status.get('status')}")
            print(f"활성 대화: {status.get('active_conversations')}개")
            print(f"사용 가능한 도구: {status.get('available_tools')}개")
            
            print(f"\n🧠 **LLM 기능:**")
            llm_capabilities = status.get('llm_capabilities', [])
            for capability in llm_capabilities:
                print(f"  • {capability}")
            
            print(f"\n🎯 **마케팅 기능:**")
            features = status.get('features', [])
            for feature in features:
                print(f"  • {feature}")
            
            print(f"\n🏢 **지원 업종:**")
            business_types = status.get('supported_business_types', [])
            for biz_type in business_types:
                print(f"  • {biz_type}")
            
            print(f"\n🔬 **대화 지능성:**")
            conv_intelligence = status.get('conversation_intelligence', {})
            for key, value in conv_intelligence.items():
                print(f"  • {key}: {value}")
                
        except Exception as e:
            print(f"❌ 상태 조회 실패: {e}")
    
    async def run_quality_test(self):
        """대화 품질 테스트"""
        print("\n🔬 **LLM 기반 대화 품질 테스트**")
        print("간단한 대화를 통해 LLM의 이해도와 응답 품질을 테스트합니다.")
        print("-" * 50)
        
        test_messages = [
            "패션 쇼핑몰 마케팅을 시작하려고 해요",
            "20대 여성이 타겟이고, 월 100만원 정도 마케팅 비용을 생각하고 있어요",
            "인스타그램 포스트를 하나 만들어주세요"
        ]
        
        user_id = 88888
        conversation_id = None
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n{i}. 테스트 메시지: \"{message}\"")
            
            try:
                result = await self.agent.process_message(
                    user_input=message,
                    user_id=user_id,
                    conversation_id=conversation_id
                )
                
                if result.get("success"):
                    data = result["data"]
                    conversation_id = data["conversation_id"]
                    
                    print("✅ LLM 분석 성공")
                    print(f"   단계: {data['current_stage']}")
                    print(f"   완료율: {data['completion_rate']:.1%}")
                    print(f"   처리시간: {data['processing_time']:.2f}초")
                    print(f"   응답 길이: {len(data['answer'])}자")
                else:
                    print("❌ LLM 분석 실패")
                
            except Exception as e:
                print(f"❌ 테스트 실패: {e}")
        
        # 품질 분석 수행
        if conversation_id:
            print(f"\n🔍 **전체 대화 품질 분석 중...**")
            quality_result = await self.agent.analyze_conversation_quality(conversation_id)
            
            if quality_result.get("success"):
                print("✅ 품질 분석 완료")
            else:
                print("⚠️ 품질 분석 실패")
        
        print("\n🎊 품질 테스트 완료!")

async def main():
    """메인 실행 함수"""
    try:
        demo = AdvancedMarketingDemo()
        await demo.run()
    except Exception as e:
        logger.error(f"데모 실행 실패: {e}")
        print(f"❌ 데모 실행 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    # OpenAI API 키 확인
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 환경변수를 설정해주세요")
        print("export OPENAI_API_KEY='your-api-key-here'")
        exit(1)
    
    print("🧠 완전 LLM 기반 마케팅 에이전트 데모 시작!")
    print("자연어 이해, 맥락적 응답, 지능적 진행 제어를 경험해보세요.\n")
    
    # 데모 실행
    asyncio.run(main())
