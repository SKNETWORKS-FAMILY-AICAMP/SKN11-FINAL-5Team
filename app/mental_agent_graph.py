from langgraph.graph import StateGraph
from app.mental_agent_nodes import (
    node_load_history, node_load_user_context, node_embed_and_retrieve,
    node_emotion_analysis, node_llm_generate, node_postprocess_and_save, node_output,
)

def build_mental_graph():
    g = StateGraph(dict)
    g.add_node("history", node_load_history)
    g.add_node("user_context", node_load_user_context)
    g.add_node("embed", node_embed_and_retrieve)
    g.add_node("emotion", node_emotion_analysis)
    g.add_node("llm", node_llm_generate)
    g.add_node("save", node_postprocess_and_save)
    g.add_node("output", node_output)
    g.add_edge("history", "user_context")
    g.add_edge("user_context", "embed")
    g.add_edge("embed", "emotion")
    g.add_edge("emotion", "llm")
    g.add_edge("llm", "save")
    g.add_edge("save", "output")
    g.set_entry_point("history")
    return g
