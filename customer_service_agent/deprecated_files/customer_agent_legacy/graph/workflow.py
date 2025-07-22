from langgraph.graph import StateGraph, END
from .state import CustomerAgentState
from .nodes import analyze_inquiry_node, rag_node, small_talk_node


def create_workflow():
    workflow = StateGraph(CustomerAgentState)
    
    # 노드 등록
    workflow.add_node("classify", analyze_inquiry_node)
    workflow.add_node("small_talk", small_talk_node)
    workflow.add_node("rag", rag_node)
    
    # 엣지 설정
    workflow.set_entry_point("classify")
    
    # 분기 조건
    def route_based_on_type(state):
        if state.get("inquiry_type") in ["인사", "잡담"]:
            return "small_talk"
        return "rag"
    
    workflow.add_conditional_edges(
        "classify",
        route_based_on_type,
        {
            "small_talk": "small_talk",
            "rag": "rag"
        }
    )
    workflow.add_edge("small_talk", END)
    workflow.add_edge("rag", END)
    
    return workflow.compile()

# 워크플로우 인스턴스 생성 (모듈 로드 시 실행)
customer_workflow = create_workflow()
