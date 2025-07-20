"""
멀티턴 마케팅 대화 시스템 사용 예제
정보 수집 → 분석 → 제안 → 피드백 → 수정 → 최종 결과 플로우 데모
"""

import asyncio
import json
from typing import Dict, Any

def simulate_multiturn_conversation():
    """멀티턴 대화 시뮬레이션"""
    
    # 마케팅 매니저 초기화
    from marketing_agent.core.marketing_manager import MarketingAgentManager
    
    print("🚀 멀티턴 마케팅 대화 시스템 시작!")
    print("=" * 60)
    
    manager = MarketingAgentManager()
    user_id = 123
    conversation_id = None
    
    # 자유로운 대화 시나리오 (LLM 기반 자연스러운 대화)
    conversation_scenario = [
        {
            "step": 1,
            "user_input": "안녕하세요, 카페 마케팅 도움이 필요해요",
            "description": "자연스러운 첫 인사와 요청"
        },
        {
            "step": 2,
            "user_input": "네, 원두 판매하는 작은 카페를 운영하고 있어요. 20-30대 직장인들이 주요 고객이고, 매출 증대가 목표예요. 월 매출 20% 증가를 원하거든요.",
            "description": "한 번에 여러 정보 제공 (자유로운 방식)"
        },
        {
            "step": 3,
            "user_input": "예산은 월 50만원 정도 생각하고 있고, 3개월 내에 결과를 보고 싶어요. 인스타그램 마케팅이 효과적일까요?",
            "description": "예산, 타임라인, 플랫폼을 자연스럽게 언급"
        },
        {
            "step": 4,
            "user_input": "와, 상세한 분석이네요! 그런데 해시태그 분석 결과에서 #원두커피보다는 #핸드드립이 더 인기가 많다고 하는데, 이것도 활용하면 좋을까요?",
            "description": "분석 결과에 대한 자연스러운 질문과 제안"
        },
        {
            "step": 5,
            "user_input": "전략이 정말 좋네요! 다만 예산을 40만원으로 좀 줄이고, 네이버 블로그도 같이 하면 어떨까요? SEO 효과도 기대하거든요.",
            "description": "구체적인 수정 요청 (예산 조정 + 채널 추가)"
        },
        {
            "step": 6,
            "user_input": "완벽해요! 이 수정된 전략으로 진행하고 싶습니다. 실행 가이드도 포함해서 최종 문서로 만들어주세요.",
            "description": "만족 표현과 최종 문서 요청"
        },
        {
            "step": 7,
            "user_input": "정말 감사합니다! 혹시 실행하면서 궁금한 점이 생기면 다시 질문해도 될까요?",
            "description": "감사 인사와 향후 지원 요청"
        }
    ]
    
    # 대화 진행
    for scenario in conversation_scenario:
        print(f"\n📝 **단계 {scenario['step']}: {scenario['description']}**")
        print(f"👤 사용자: {scenario['user_input']}")
        print("-" * 40)
        
        try:
            # 사용자 쿼리 처리
            response = manager.process_user_query(
                user_input=scenario['user_input'],
                user_id=user_id,
                conversation_id=conversation_id
            )
            
            # conversation_id 업데이트 (첫 번째 응답 후)
            if conversation_id is None:
                conversation_id = response.get('conversation_id')
            
            # 응답 출력
            print(f"🤖 AI 컨설턴트:")
            print(response.get('answer', '응답을 생성할 수 없습니다.'))
            
            # 메타데이터 출력 (디버깅용)
            if response.get('metadata', {}).get('multiturn_flow'):
                stage = response['metadata'].get('conversation_stage', 'unknown')
                completion = response['metadata'].get('completion_rate', 0.0)
                print(f"\n📊 상태: {stage} | 완료율: {completion:.1%}")
                
                # MCP 도구 사용 여부
                if response['metadata'].get('mcp_tools_used'):
                    tools = response['metadata']['mcp_tools_used']
                    print(f"🔧 사용된 도구: {', '.join(tools)}")
            
            print("=" * 60)
            
            # 잠시 대기 (실제 대화처럼 시뮬레이션)
            import time
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            break
    
    # 최종 대화 상태 확인
    if conversation_id:
        print(f"\n📈 **최종 대화 상태**")
        final_status = manager.get_conversation_status(conversation_id)
        print(json.dumps(final_status, ensure_ascii=False, indent=2))

def demonstrate_agent_features():
    """에이전트 기능 데모"""
    
    from marketing_agent.core.marketing_manager import MarketingAgentManager
    
    print("\n🔍 **에이전트 기능 소개**")
    print("=" * 60)
    
    manager = MarketingAgentManager()
    
    # 1. 에이전트 상태 확인
    print("1️⃣ **에이전트 상태**")
    status = manager.get_agent_status()
    print(f"- 버전: {status['version']}")
    print(f"- 대화 시스템: {status['conversation_system']}")
    print(f"- 지원 단계: {', '.join(status['stages'])}")
    print(f"- MCP 도구: {', '.join(status['mcp_tools_available'])}")
    
    # 2. 사용 가능한 토픽
    print(f"\n2️⃣ **지원 토픽** ({len(manager.marketing_topics)}개)")
    for topic_id, topic_name in list(manager.marketing_topics.items())[:5]:
        print(f"- {topic_id}: {topic_name}")
    print("... 및 기타 토픽들")
    
    # 3. 지식 베이스 정보
    print(f"\n3️⃣ **전문 지식 베이스**")
    knowledge_summary = manager.get_knowledge_summary()
    print(f"- 문서 수: {knowledge_summary.get('document_count', 0)}")
    print(f"- 지식 영역: {', '.join(knowledge_summary.get('knowledge_areas', []))}")
    
    print("\n✨ **주요 특징**")
    print("- 🎯 LLM 기반 의도 분석")
    print("- 📊 실시간 트렌드 분석 (MCP 도구)")
    print("- 🔍 벡터 스토어 기반 전문 지식 검색")
    print("- 💬 체계적인 멀티턴 대화 흐름")
    print("- 🔄 피드백 기반 전략 수정")

def advanced_usage_example():
    """고급 사용법 예제"""
    
    print("\n🎓 **고급 사용법**")
    print("=" * 60)
    
    from marketing_agent.core.marketing_manager import MarketingAgentManager
    
    manager = MarketingAgentManager()
    
    # 1. 직접적인 토픽 분류
    print("1️⃣ **토픽 분류 테스트**")
    test_input = "인스타그램 해시태그 전략이 필요해요"
    topics = manager.classify_marketing_topic_with_llm(test_input)
    print(f"입력: {test_input}")
    print(f"분류된 토픽: {topics}")
    
    # 2. 전문 지식 검색
    print(f"\n2️⃣ **전문 지식 검색**")
    knowledge = manager.get_relevant_knowledge("소셜미디어 마케팅", ["social_media_marketing"])
    if knowledge:
        print(f"검색 결과: {len(knowledge)}개 문서")
        print(f"첫 번째 결과: {knowledge[0][:100]}...")
    
    # 3. 대화 상태 관리
    print(f"\n3️⃣ **대화 상태 관리**")
    print("- 대화별 독립적인 상태 관리")
    print("- 단계별 정보 수집 및 진행률 추적")
    print("- 피드백 히스토리 관리")
    print("- 자동 단계 전환")

if __name__ == "__main__":
    print("🎉 멀티턴 마케팅 대화 시스템 데모")
    print("새로운 정보 수집 → 분석 → 제안 → 피드백 → 수정 → 최종 결과 플로우")
    print()
    
    try:
        # 1. 기본 멀티턴 대화 시뮬레이션
        simulate_multiturn_conversation()
        
        # 2. 에이전트 기능 소개
        demonstrate_agent_features()
        
        # 3. 고급 사용법
        advanced_usage_example()
        
    except ImportError as e:
        print(f"❌ 모듈 임포트 오류: {e}")
        print("shared_modules가 Python 경로에 있는지 확인하세요.")
    except Exception as e:
        print(f"❌ 실행 오류: {e}")
    
    print(f"\n✅ 데모 완료!")
    print("실제 사용 시에는 웹 인터페이스나 API를 통해 interact하실 수 있습니다.")
