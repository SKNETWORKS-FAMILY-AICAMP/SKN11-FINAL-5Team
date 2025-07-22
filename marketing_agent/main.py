"""
멀티턴 마케팅 에이전트 메인 실행 파일 (v3.0)
정보 수집 → 분석 → 제안 → 피드백 → 수정 → 최종 결과 플로우 데모
"""

import asyncio
from marketing_agent.core.marketing_manager import MarketingAgentManager

def demo_multiturn_conversation():
    """멀티턴 대화 데모"""
    print("🔄 멀티턴 대화 플로우 데모")
    print("=" * 50)
    
    manager = MarketingAgentManager()
    user_id = 1001
    conversation_id = None
    
    # 시뮬레이션된 사용자 입력
    demo_inputs = [
        "온라인 쇼핑몰 마케팅 도움이 필요해요",
        "핸드메이드 주얼리를 파는 온라인 쇼핑몰이고, 20-30대 여성이 주요 고객층이에요",
        "브랜드 인지도 상승과 매출 증대가 목표입니다. 월 매출 40% 증가를 원해요",
        "예산은 월 80만원 정도이고, 3개월 내에 성과를 보고 싶어요",
        "인스타그램 마케팅에 집중하고 싶어요",
        "좋은 전략이네요! 그런데 예산을 60만원으로 줄일 수 있을까요?",
        "완벽합니다! 이 전략으로 진행하겠습니다"
    ]
    
    for i, user_input in enumerate(demo_inputs, 1):
        print(f"\n📝 단계 {i}")
        print(f"👤 사용자: {user_input}")
        print("-" * 30)
        
        try:
            result = manager.process_user_query(
                user_input=user_input,
                user_id=user_id,
                conversation_id=conversation_id
            )
            
            # conversation_id 업데이트
            if conversation_id is None:
                conversation_id = result.get('conversation_id')
            
            # 응답 출력
            answer = result.get('answer', '')
            if len(answer) > 300:
                print(f"🤖 AI 컨설턴트: {answer[:300]}...")
            else:
                print(f"🤖 AI 컨설턴트: {answer}")
            
            # 진행 상황 표시
            metadata = result.get('metadata', {})
            if metadata.get('multiturn_flow'):
                stage = metadata.get('conversation_stage', 'unknown')
                completion = metadata.get('completion_rate', 0.0)
                print(f"📊 현재 단계: {stage} | 완료율: {completion:.1%}")
                
                # MCP 도구 사용 표시
                mcp_tools = metadata.get('mcp_tools_used', [])
                if mcp_tools:
                    print(f"🔧 사용된 분석 도구: {', '.join(mcp_tools)}")
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            break
        
        # 짧은 대기 (데모용)
        import time
        time.sleep(0.5)
    
    # 최종 상태 출력
    if conversation_id:
        print(f"\n📈 최종 대화 상태")
        print("-" * 30)
        final_status = manager.get_conversation_status(conversation_id)
        print(f"대화 ID: {conversation_id}")
        print(f"단계: {final_status.get('stage', 'unknown')}")
        print(f"완료 여부: {'✅ 완료' if final_status.get('is_completed') else '⏳ 진행중'}")
        print(f"제안 횟수: {final_status.get('total_proposals', 0)}")
        print(f"수정 횟수: {final_status.get('total_refinements', 0)}")
        print(f"피드백 수: {final_status.get('total_feedback', 0)}")

def demo_mcp_tools():
    """MCP 도구 데모"""
    print("\n🔧 MCP 분석 도구 데모")
    print("=" * 50)
    
    manager = MarketingAgentManager()
    
    mcp_examples = [
        {
            "name": "해시태그 분석",
            "query": "카페 신메뉴 라떼에 대한 인스타그램 해시태그를 추천해주세요",
            "expected_tool": "hashtag_analysis"
        },
        {
            "name": "트렌드 분석", 
            "query": "한식 맛집 키워드의 네이버 검색 트렌드를 분석해주세요",
            "expected_tool": "trend_analysis"
        },
        {
            "name": "콘텐츠 생성",
            "query": "우리 브랜드 인스타그램 마케팅 콘텐츠 템플릿을 만들어주세요",
            "expected_tool": "content_generation"
        }
    ]
    
    for i, example in enumerate(mcp_examples, 1):
        print(f"\n{i}️⃣ {example['name']}")
        print(f"질문: {example['query']}")
        print("-" * 30)
        
        try:
            result = manager.process_user_query(
                user_input=example['query'],
                user_id=2000 + i
            )
            
            metadata = result.get('metadata', {})
            mcp_tools_used = metadata.get('mcp_tools_used', [])
            real_time_analysis = metadata.get('real_time_analysis', False)
            
            print(f"🔧 사용된 도구: {', '.join(mcp_tools_used) if mcp_tools_used else '없음'}")
            print(f"📊 실시간 분석: {'✅' if real_time_analysis else '❌'}")
            
            # MCP 결과 요약
            mcp_results = metadata.get('mcp_results', {})
            if mcp_results:
                print("📈 분석 결과:")
                for tool, result_data in mcp_results.items():
                    success = result_data.get('success', False)
                    print(f"   {tool}: {'✅ 성공' if success else '❌ 실패'}")
            
            # 응답 미리보기
            answer = result.get('answer', '')
            if answer:
                preview = answer[:150] + "..." if len(answer) > 150 else answer
                print(f"💬 응답 미리보기: {preview}")
                
        except Exception as e:
            print(f"❌ 오류: {e}")

def demo_agent_capabilities():
    """에이전트 능력 데모"""
    print("\n📊 에이전트 능력 및 상태")
    print("=" * 50)
    
    manager = MarketingAgentManager()
    
    # 에이전트 상태
    status = manager.get_agent_status()
    print(f"🎯 에이전트 버전: {status.get('version')}")
    print(f"🔄 대화 시스템: {status.get('conversation_system')}")
    print(f"📚 지원 토픽: {len(status.get('available_topics', []))}개")
    print(f"🔧 MCP 도구: {', '.join(status.get('mcp_tools_available', []))}")
    print(f"💬 활성 대화: {status.get('active_conversations')}개")
    
    # 지식 베이스 정보
    knowledge_summary = manager.get_knowledge_summary()
    print(f"\n📖 지식 베이스:")
    print(f"   문서 수: {knowledge_summary.get('document_count', 0)}")
    print(f"   지식 영역: {', '.join(knowledge_summary.get('knowledge_areas', []))}")
    
    # 토픽 분류 테스트
    print(f"\n🎯 토픽 분류 테스트:")
    test_cases = [
        "이메일 마케팅 자동화 시스템을 구축하고 싶어요",
        "브랜드 포지셔닝 전략이 필요해요",
        "바이럴 마케팅 캠페인을 기획하고 싶어요"
    ]
    
    for test_input in test_cases:
        topics = manager.classify_marketing_topic_with_llm(test_input)
        print(f"   '{test_input[:30]}...' → {', '.join(topics)}")

def interactive_demo():
    """대화형 데모"""
    print("\n💬 대화형 데모")
    print("=" * 50)
    print("직접 마케팅 상담을 체험해보세요!")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
    print()
    
    manager = MarketingAgentManager()
    user_id = 9999
    conversation_id = None
    
    while True:
        try:
            user_input = input("👤 당신: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '종료', '나가기']:
                print("👋 마케팅 상담을 종료합니다. 감사합니다!")
                break
            
            if not user_input:
                continue
            
            print("🤔 분석 중...")
            
            result = manager.process_user_query(
                user_input=user_input,
                user_id=user_id,
                conversation_id=conversation_id
            )
            
            # conversation_id 업데이트
            if conversation_id is None:
                conversation_id = result.get('conversation_id')
            
            # 응답 출력
            answer = result.get('answer', '응답을 생성할 수 없습니다.')
            print(f"\n🤖 AI 컨설턴트: {answer}")
            
            # 진행 상황 표시
            metadata = result.get('metadata', {})
            if metadata.get('multiturn_flow'):
                stage = metadata.get('conversation_stage', 'unknown')
                completion = metadata.get('completion_rate', 0.0)
                print(f"\n📊 진행 상황: {stage} ({completion:.1%} 완료)")
            
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n👋 대화를 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류가 발생했습니다: {e}")

def main():
    """메인 실행 함수"""
    print("🎉 멀티턴 마케팅 에이전트 v3.0")
    print("정보 수집 → 분석 → 제안 → 피드백 → 수정 → 최종 결과")
    print("=" * 60)
    
    try:
        # 1. 멀티턴 대화 데모
        demo_multiturn_conversation()
        
        # 2. MCP 도구 데모
        demo_mcp_tools()
        
        # 3. 에이전트 능력 데모
        demo_agent_capabilities()
        
        # 4. 대화형 데모 (선택사항)
        print(f"\n🤔 대화형 데모를 시작하시겠습니까? (y/n): ", end="")
        choice = input().strip().lower()
        
        if choice in ['y', 'yes', '네', 'ㅇ']:
            interactive_demo()
        
    except ImportError as e:
        print(f"❌ 모듈 임포트 오류: {e}")
        print("shared_modules와 marketing_agent 패키지가 설치되어 있는지 확인하세요.")
    except Exception as e:
        print(f"❌ 실행 오류: {e}")
    
    print(f"\n✨ 주요 개선사항 (v3.1):")
    print("🤖 완전 LLM 기반 자연스러운 대화")
    print("💬 자유로운 정보 제공 순서")
    print("🔄 지능적 단계 전환 판단")
    print("🔧 MCP 실시간 분석 도구 통합")
    print("📚 RAG 기반 전문 지식 활용")
    print("🎯 개인화된 맞춤형 응답")
    print("🔄 유연한 피드백 및 전략 수정")
    
    print(f"\n📁 추가 예시:")
    print("- python -m marketing_agent.example_usage")
    print("- python -m marketing_agent.example_multiturn_usage")

if __name__ == "__main__":
    main()
