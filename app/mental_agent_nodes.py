from app.crud import create_message, get_conversation_history
from app.mental_agent import (
    get_user_context_from_db, extract_and_save_phq9,
    vectorstore, LLM_POOL, get_llm_choice, get_fallback_llm_name, answer_prompt,
    analyze_emotion, is_depressed_emotion, load_phq9_markdown,
)

def node_load_history(state):
    db = state["db"]
    state["chat_history"] = get_conversation_history(db, state["conversation_id"])
    return state

def node_load_user_context(state):
    db = state["db"]
    state["user_context"] = get_user_context_from_db(db, state["user_id"])
    return state

def node_embed_and_retrieve(state):
    docs = vectorstore.as_retriever().invoke(state["user_input"])
    state["docs"] = docs
    state["context"] = "\n\n".join([d.page_content for d in docs])
    state["references"] = [
        d.metadata.get("source") or d.metadata.get("title") or str(d.metadata) for d in docs
    ]
    return state

def node_emotion_analysis(state):
    state["emotion"] = analyze_emotion(state["user_input"])
    state["depressed"] = is_depressed_emotion(state["emotion"])
    return state

def node_llm_generate(state):
    llm_name = get_llm_choice()
    enhanced_prompt = f"""
당신은 친절하고 공감하는 멘탈 건강 상담사입니다.
항상 같은 인사말(예: '안녕하세요')로 시작하지 말고,
질문에 바로 상담 답변을 해주세요.

아래 이전 대화 내용, 상담 기록, 참고 내용을 종합적으로 고려하여 사용자 질문에 대해 친절하고 이해하기 쉽게 답변해 주세요.
특히 이전 대화에서 언급된 PHQ-9 점수, 감정 상태, 개인적 상황 등을 기억하고 연속성 있는 상담을 제공하세요.
상담자가 우울함을 표시하고 있다면 공감을 표하고 PHQ-9 설문을 제안하세요. PHQ-9 설문 점수가 존재한다면 PHQ-9 점수에 따라 적절한 조치를 안내하세요.
상담 기록 및 참고 내용에 실명이 들어가 있다면 무시해줘.

=== 사용자 세션 정보 ===
{state.get('user_context','')}

=== 최근 대화 내용 ===
{state.get('chat_history','')}

=== 상담 기록 및 참고 내용 ===
{state.get('context','')}

=== 현재 질문 ===
{state['user_input']}

답변:
"""
    try:
        llm = LLM_POOL[llm_name]
        response = llm.invoke(enhanced_prompt)
        state["answer"] = response.content if hasattr(response, "content") else str(response)
        state["llm_used"] = llm_name
        state["llm_error"] = None
        state["fallback_used"] = False
    except Exception as e:
        fallback_llm_name = get_fallback_llm_name(llm_name)
        try:
            llm = LLM_POOL[fallback_llm_name]
            response = llm.invoke(enhanced_prompt)
            state["answer"] = response.content if hasattr(response, "content") else str(response)
            state["llm_used"] = fallback_llm_name
            state["llm_error"] = str(e)
            state["fallback_used"] = True
        except Exception as e2:
            state["answer"] = f"두 모델 모두 오류가 발생했습니다: {e2}"
            state["llm_used"] = None
            state["llm_error"] = f"{e} / {e2}"
            state["fallback_used"] = True
    return state

def node_postprocess_and_save(state):
    db = state["db"]
    refs = state.get("references", [])
    if refs:
        state["answer"] += "\n\n[참고자료]\n" + "\n".join(f"- {r}" for r in refs)
    else:
        state["answer"] += "\n\n[참고자료]\n- (관련 문서 없음)"

    create_message(db, state["conversation_id"], "agent", "mental_agent", state["answer"])
    extract_and_save_phq9(db, state["user_id"], state["conversation_id"], state["user_input"])

    if state.get("depressed") and state.get("phq9_suggested") != True:
        state["answer"] += "\n\n[PHQ-9 설문]\n" + load_phq9_markdown()
        state["phq9_suggested"] = True
    return state

def node_output(state):
    return {"answer": state["answer"]}
