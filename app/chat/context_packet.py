from __future__ import annotations

from .contracts import AppState, ChatContextPacket, ChatMessage
from .router import classify_main_chat_intent, extract_content_theme
from .state import active_chat_mode


_ACK_ONLY = {
    "그래",
    "응",
    "어",
    "어어",
    "웅",
    "맞아",
    "맞아요",
    "좋아",
    "좋아요",
    "그렇지",
    "그렇구나",
    "오케이",
    "ㅇㅇ",
    "몰라",
}

_CONTENT_OBJECT_TOKENS = ("노래", "음악", "영화", "드라마", "책", "소설", "영상", "가사")


def _recent_main_messages(state: AppState, limit: int = 8) -> list[ChatMessage]:
    history = [item for item in state.get("main_chat_history", []) if isinstance(item, dict)]
    return history[-limit:]


def _recent_study_messages(state: AppState, doc_id: str | None, limit: int = 8) -> list[ChatMessage]:
    target = str(doc_id or "").strip()
    if not target:
        return []
    history = [
        item
        for item in state.get("chat_history", [])
        if isinstance(item, dict) and str(item.get("doc_id") or "").strip() == target
    ]
    return history[-limit:]


def _dedupe_texts(values: list[str] | None, limit: int = 4) -> list[str]:
    unique: list[str] = []
    for item in values or []:
        text = str(item or "").strip()
        if not text or text in unique:
            continue
        unique.append(text)
        if len(unique) >= limit:
            break
    return unique


def _as_text_list(value: object) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [str(item or "").strip() for item in value if str(item or "").strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _ambiguity_reasons(normalized: str, state: AppState) -> list[str]:
    reasons: list[str] = []
    context = state.get("main_chat_context") or {}
    last_concept_term = str(context.get("last_concept_term") or "").strip()

    if normalized in _ACK_ONLY:
        reasons.append("short_ack")
    if len(normalized) <= 4:
        reasons.append("very_short_prompt")
    if normalized.endswith("?") and len(normalized) <= 12:
        reasons.append("underspecified_question")
    if last_concept_term and len(normalized) <= 10:
        reasons.append("depends_on_previous_context")
    if any(token in normalized for token in _CONTENT_OBJECT_TOKENS) and " " not in normalized:
        reasons.append("compound_content_phrase")
    if any(token in normalized for token in ("왜", "어떻게", "뭐야", "뭐지")) and len(normalized) <= 14:
        reasons.append("needs_interpretation")

    unique: list[str] = []
    for item in reasons:
        if item not in unique:
            unique.append(item)
    return unique


def build_chat_context_packet(prompt: str, state: AppState | None = None) -> ChatContextPacket:
    resolved_state = state or {}
    normalized = str(prompt or "").strip()
    context = resolved_state.get("main_chat_context") or {}
    intent_hint = classify_main_chat_intent(normalized, custom_concepts=resolved_state.get("custom_concepts"))
    content_theme = extract_content_theme(normalized)
    reasons = _ambiguity_reasons(normalized, resolved_state)
    recent_messages = _recent_main_messages(resolved_state)
    llm_candidate = bool(reasons)
    if len(recent_messages) >= 2 and len(normalized) <= 14:
        llm_candidate = True

    return {
        "prompt": prompt,
        "normalized_prompt": normalized,
        "recent_messages": recent_messages,
        "active_mode": "study" if active_chat_mode(resolved_state) == "study" else "main",
        "has_documents": bool(resolved_state.get("documents")),
        "document_count": len([item for item in resolved_state.get("documents", []) if isinstance(item, dict)]),
        "custom_concept_count": len(dict(resolved_state.get("custom_concepts") or {})),
        "last_intent": str(context.get("last_intent") or "").strip(),
        "last_concept_term": str(context.get("last_concept_term") or "").strip() or None,
        "last_concept_stage": str(context.get("last_concept_stage") or "").strip() or None,
        "intent_hint": intent_hint,
        "content_theme": content_theme,
        "ambiguity_score": len(reasons),
        "ambiguity_reasons": reasons,
        "llm_candidate": llm_candidate,
    }


def build_study_chat_context_packet(prompt: str, document: dict | None, state: AppState | None = None) -> ChatContextPacket:
    resolved_state = state or {}
    normalized = str(prompt or "").strip()
    analysis = (document or {}).get("analysis") or {}
    structured = analysis.get("structured_problem") or {}
    solved = analysis.get("solve_result") or {}
    doc_id = str((document or {}).get("doc_id") or resolved_state.get("selected_doc_id") or "").strip() or None
    recent_messages = _recent_study_messages(resolved_state, doc_id)
    expressions = _dedupe_texts(_as_text_list(structured.get("expressions")) or _as_text_list(structured.get("source_text_candidates")), limit=4)
    steps = _dedupe_texts(_as_text_list(solved.get("steps")), limit=4)
    problem_text = str(structured.get("normalized_problem_text") or "").strip() or None
    answer_candidate = str(solved.get("matched_choice") or solved.get("computed_answer") or "").strip() or None
    reasons = _ambiguity_reasons(normalized, resolved_state)
    content_theme = extract_content_theme(normalized)
    intent_hint = "math" if (problem_text or expressions or answer_candidate) else "general"

    return {
        "prompt": prompt,
        "normalized_prompt": normalized,
        "recent_messages": recent_messages,
        "active_mode": "study",
        "has_documents": bool(resolved_state.get("documents")),
        "document_count": len([item for item in resolved_state.get("documents", []) if isinstance(item, dict)]),
        "custom_concept_count": len(dict(resolved_state.get("custom_concepts") or {})),
        "last_intent": "study",
        "last_concept_term": None,
        "last_concept_stage": None,
        "intent_hint": intent_hint,
        "content_theme": content_theme,
        "ambiguity_score": len(reasons),
        "ambiguity_reasons": reasons,
        "llm_candidate": True,
        "selected_doc_id": doc_id,
        "selected_doc_name": str((document or {}).get("file_name") or "").strip() or None,
        "study_problem_text": problem_text,
        "study_math_topic": str(structured.get("math_topic") or "").strip() or None,
        "study_answer_candidate": answer_candidate,
        "study_steps": steps,
        "study_expressions": expressions,
        "study_question_type": str(structured.get("question_type") or "").strip() or None,
        "study_latest_user_query": str((document or {}).get("latest_user_query") or "").strip() or None,
    }
