"""
멀티턴 마케팅 에이전트 사용 예시 (v3.0)
정보 수집 → 분석 → 제안 → 피드백 → 수정 → 최종 결과 플로우
LLM 기반 의도 분석 + MCP 도구 통합 + RAG 전문 지식
"""

from marketing_agent.core.marketing_manager import MarketingAgentManager
import asyncio
import json

def example_simple_usage():
    """간단한 사용법 예시"""
    print("=== 📝 간단한 사용법 ===")
    
    # 마케팅 매니저 초기화
    manager = MarketingAgentManager()
    
    # 단일 쿼리 처리
    result = manager.process_user_query(
        user_input="카페 마케팅 도움이 필요해요",
        user_id=1001,
        conversation_id=None  # 새로운 대화 시작
    )
    
    print(f"응답: {result.get('answer', '')}")
    print(f"대화 단계: {result.get('metadata', {}).get('conversation_stage', 'unknown')}")
    print(f"완료율: {result.get('metadata', {}).get('completion_rate', 0):.1%}")
    
    return result

def example_complete_multiturn_flow():
    """완전한 멀티턴 대화 플로우 예시"""
    print("\n=== 🔄 완전한 멀티턴 대화 플로우 ===")
    
    manager = MarketingAgentManager()
    user_id = 2001
    conversation_id = None
    
    # 멀티턴 대화 시뮬레이션
    conversation_steps = [
        "온라인 쇼핑몰 마케팅 상담 받고 싶어요",
        "핸드메이드 액세서리를 판매하는 온라인 쇼핑몰이고, 20-30대 여성이 주요 고객이에요",
        "브랜드 인지도 향상과 매출 증대가 목표예요. 월 매출 30% 증가를 원해요",
        "예산은 월 100만원 정도이고, 6개월 내에 결과를 보고 싶어요",
        "인스타그램과 네이버 블로그를 활용하고 싶어요",
        "전략이 좋은데, 예산을 80만원으로 줄이고 싶어요",
        "완벽합니다! 최종 전략으로 확정해주세요"
    ]
    
    for i, user_input in enumerate(conversation_steps, 1):
        print(f"\n--- 단계 {i} ---")
        print(f"👤 사용자: {user_input}")
        
        result = manager.process_user_query(
            user_input=user_input,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        # conversation_id 업데이트
        if conversation_id is None:
            conversation_id = result.get('conversation_id')
        
        print(f"🤖 AI: {result.get('answer', '')[:200]}...")
        
        # 메타데이터 출력
        metadata = result.get('metadata', {})
        if metadata.get('multiturn_flow'):
            print(f"📊 단계: {metadata.get('conversation_stage')} | 완료율: {metadata.get('completion_rate', 0):.1%}")
    
    # 최종 상태 확인
    if conversation_id:
        final_status = manager.get_conversation_status(conversation_id)
        print(f"\n📈 최종 상태: {final_status.get('stage')} (완료: {final_status.get('is_completed')})")
    
    return conversation_id

def example_mcp_tools_integration():
    """MCP 도구 통합 예시"""
    print("\n=== 🔧 MCP 도구 통합 ===")
    
    manager = MarketingAgentManager()
    
    # MCP 도구가 필요한 쿼리들
    mcp_queries = [
        {
            "query": "뷰티샵 인스타그램 해시태그 추천해주세요",
            "expected_tools": ["hashtag_analysis"]
        },
        {
            "query": "카페라떼 키워드 트렌드 분석해주세요",
            "expected_tools": ["trend_analysis"]
        },
        {
            "query": "우리 브랜드 인스타그램 콘텐츠 템플릿 만들어주세요",
            "expected_tools": ["content_generation"]
        }
    ]
    
    for i, query_info in enumerate(mcp_queries, 1):
        print(f"\n{i}. {query_info['query']}")
        
        result = manager.process_user_query(
            user_input=query_info["query"],
            user_id=3000 + i
        )
        
        metadata = result.get('metadata', {})
        used_tools = metadata.get('mcp_tools_used', [])
        mcp_results = metadata.get('mcp_results', {})
        
        print(f"사용된 MCP 도구: {used_tools}")
        print(f"실시간 분석: {metadata.get('real_time_analysis', False)}")
        
        # MCP 결과 요약
        for tool in used_tools:
            if tool in mcp_results:
                success = mcp_results[tool].get('success', False)
                print(f"  - {tool}: {'✅ 성공' if success else '❌ 실패'}")

def example_knowledge_base_features():
    """지식 베이스 기능 예시"""
    print("\n=== 📚 지식 베이스 기능 ===")
    
    manager = MarketingAgentManager()
    
    # 1. 토픽 분류 테스트
    test_inputs = [
        "이메일 마케팅 자동화가 필요해요",
        "브랜드 포지셔닝 전략을 세우고 싶어요",
        "바이럴 마케팅 방법을 알고 싶어요"
    ]
    
    print("1️⃣ 토픽 분류:")
    for input_text in test_inputs:
        topics = manager.classify_marketing_topic_with_llm(input_text)
        print(f"  '{input_text}' → {topics}")
    
    # 2. 전문 지식 검색
    print(f"\n2️⃣ 전문 지식 검색:")
    knowledge = manager.get_relevant_knowledge("소셜미디어 전략", ["social_media_marketing"])
    print(f"검색 결과: {len(knowledge)}개 문서")
    if knowledge:
        print(f"첫 번째 결과 미리보기: {knowledge[0][:150]}...")
    
    # 3. 지식 베이스 요약
    print(f"\n3️⃣ 지식 베이스 요약:")
    summary = manager.get_knowledge_summary()
    print(f"문서 수: {summary.get('document_count', 0)}")
    print(f"지식 영역: {', '.join(summary.get('knowledge_areas', []))}")
    print(f"사용 가능한 프롬프트: {sum(summary.get('available_prompts', {}).values())}")

def example_conversation_management():
    """대화 관리 기능 예시"""
    print("\n=== 💬 대화 관리 기능 ===")
    
    manager = MarketingAgentManager()
    
    # 여러 대화 동시 진행
    conversations = []
    
    for i in range(3):
        result = manager.process_user_query(
            user_input=f"비즈니스 {i+1} 마케팅 상담 요청",
            user_id=4000 + i
        )
        conversations.append(result.get('conversation_id'))
        print(f"대화 {i+1} 시작: {result.get('conversation_id')}")
    
    # 각 대화 상태 확인
    print(f"\n대화 상태 확인:")
    for i, conv_id in enumerate(conversations):
        if conv_id:
            status = manager.get_conversation_status(conv_id)
            print(f"대화 {i+1}: {status.get('stage')} ({status.get('completion_rate', 0):.1%})")
    
    # 에이전트 전체 상태
    agent_status = manager.get_agent_status()
    print(f"\n활성 대화 수: {agent_status.get('active_conversations')}")
    print(f"대화 단계별 분포: {agent_status.get('conversation_stages', {})}")

def example_error_handling():
    """오류 처리 예시"""
    print("\n=== ⚠️ 오류 처리 ===")
    
    manager = MarketingAgentManager()
    
    # 정상 처리
    try:
        result = manager.process_user_query(
            user_input="정상적인 마케팅 상담 요청",
            user_id=5001
        )
        print(f"✅ 정상 처리: {result.get('answer', '')[:50]}...")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    # 대화 초기화
    conversation_id = result.get('conversation_id')
    if conversation_id:
        reset_success = manager.reset_conversation(conversation_id)
        print(f"대화 초기화: {'✅ 성공' if reset_success else '❌ 실패'}")

if __name__ == "__main__":
    print("🎉 멀티턴 마케팅 에이전트 v3.0 사용 예시")
    print("정보 수집 → 분석 → 제안 → 피드백 → 수정 → 최종 결과")
    print("=" * 60)
    
    try:
        # 1. 간단한 사용법
        example_simple_usage()
        
        # 2. 완전한 멀티턴 플로우
        example_complete_multiturn_flow()
        
        # 3. MCP 도구 통합
        example_mcp_tools_integration()
        
        # 4. 지식 베이스 기능
        example_knowledge_base_features()
        
        # 5. 대화 관리
        example_conversation_management()
        
        # 6. 오류 처리
        example_error_handling()
        
    except ImportError as e:
        print(f"❌ 모듈 임포트 오류: {e}")
        print("shared_modules와 marketing_agent가 Python 경로에 있는지 확인하세요.")
    except Exception as e:
        print(f"❌ 실행 오류: {e}")
    
    print(f"\n✨ 주요 특징:")
    print("🎯 체계적인 멀티턴 대화 흐름")
    print("🤖 LLM 기반 의도 분석 및 토픽 분류")
    print("🔧 MCP 도구 통합 (해시태그, 트렌드, 콘텐츠)")
    print("📚 RAG 기반 전문 지식 검색")
    print("🔄 실시간 피드백 및 전략 수정")
    print("📊 단계별 진행 상황 추적")
    print("💬 다중 대화 동시 관리")
    
    print(f"\n📖 더 자세한 예시는 example_multiturn_usage.py를 참고하세요!")
