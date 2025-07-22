"""
Business Planning Agent - 멀티턴 대화 사용 예제
마케팅 에이전트의 멀티턴 시스템을 참고한 예제
"""

import asyncio
import json
from buisness_planning_agent.core.business_planning_manager import BusinessPlanningAgentManager

async def business_planning_multiturn_demo():
    """비즈니스 기획 멀티턴 대화 데모"""
    
    print("=== 비즈니스 기획 에이전트 멀티턴 대화 데모 ===\n")
    
    # 매니저 초기화
    manager = BusinessPlanningAgentManager()
    
    # 사용자 정보
    user_id = 1001
    conversation_id = None  # 새 대화 시작
    
    # 대화 시나리오
    conversation_flow = [
        "안녕하세요, 창업을 준비하고 있습니다.",
        "온라인 강의 플랫폼을 만들고 싶어요. 프로그래밍을 가르치는 플랫폼입니다.",
        "IT 업계고, 주로 초보 개발자들을 타겟으로 하고 있습니다.",
        "기존 플랫폼과 다르게 1:1 멘토링을 강화하고 싶어요.",
        "아직 아이디어 단계이고, 초기 투자금으로 3000만원 정도 준비했습니다.",
        "6개월 내에 MVP를 만들어서 베타 테스트를 시작하고 싶습니다.",
        "온라인으로 전국 대상이고, 저 혼자 시작할 예정입니다.",
        "웹 개발 경력이 5년 있어서 기술적인 부분은 어느 정도 자신 있습니다.",
        "1년 내에 월 매출 1000만원을 목표로 하고 있어요.",
        "가장 걱정되는 건 초기 고객 확보와 마케팅입니다."
    ]
    
    print("📋 대화 시나리오:")
    for i, message in enumerate(conversation_flow, 1):
        print(f"{i}. {message}")
    print("\n" + "="*60 + "\n")
    
    # 멀티턴 대화 실행
    for step, user_message in enumerate(conversation_flow, 1):
        print(f"🗣️ [사용자 {step}]: {user_message}")
        
        try:
            # 매니저를 통한 쿼리 처리
            result = manager.process_user_query(
                user_input=user_message,
                user_id=user_id,
                conversation_id=conversation_id
            )
            
            # conversation_id 업데이트 (첫 번째 응답에서 받음)
            if conversation_id is None and result.get("conversation_id"):
                conversation_id = result["conversation_id"]
                print(f"📞 새 대화 세션 생성: {conversation_id}")
            
            # 응답 출력
            print(f"🤖 [에이전트]: {result.get('answer', '응답을 받지 못했습니다.')}")
            
            # 대화 상태 정보 출력
            if conversation_id in manager.conversation_states:
                state = manager.conversation_states[conversation_id]
                print(f"📊 [상태] 단계: {state.stage.value}, 완료율: {state.get_completion_rate():.1%}")
            
            print("-" * 60)
            
            # 단계 전환 시 잠시 대기
            if step in [1, 5, 10]:
                print("⏱️ 잠시 대기 중...\n")
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            break
    
    # 최종 대화 상태 출력
    if conversation_id and conversation_id in manager.conversation_states:
        final_state = manager.conversation_states[conversation_id]
        print("\n" + "="*60)
        print("📋 최종 대화 상태:")
        print(f"- 현재 단계: {final_state.stage.value}")
        print(f"- 정보 완료율: {final_state.get_completion_rate():.1%}")
        print(f"- 수집된 정보 개수: {len([v for v in final_state.collected_info.values() if v])}")
        print(f"- 분석 완료: {'예' if final_state.analysis_results.get('analysis_content') else '아니오'}")
        
        print("\n📝 수집된 핵심 정보:")
        for key, value in final_state.collected_info.items():
            if value:
                print(f"- {key}: {value}")

async def single_query_demo():
    """단일 쿼리 데모"""
    print("\n=== 단일 쿼리 데모 ===\n")
    
    manager = BusinessPlanningAgentManager()
    
    test_queries = [
        "린캔버스 템플릿을 보여주세요",
        "카페 창업을 준비하고 있는데 어떤 절차가 필요한가요?",
        "온라인 쇼핑몰 아이디어를 검증하고 싶습니다"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"🗣️ [질문 {i}]: {query}")
        
        result = manager.process_user_query(
            user_input=query,
            user_id=2000 + i,
            conversation_id=None
        )
        
        print(f"🤖 [응답]: {result.get('answer', '응답 없음')[:200]}...")
        print("-" * 60)

if __name__ == "__main__":
    print("Business Planning Agent - 멀티턴 대화 테스트")
    print("공통 모듈과 마케팅 에이전트 구조 기반")
    print("="*60)
    
    # 멀티턴 대화 데모 실행
    asyncio.run(business_planning_multiturn_demo())
    
    # 단일 쿼리 데모 실행
    asyncio.run(single_query_demo())
    
    print("\n✅ 모든 테스트 완료!")
