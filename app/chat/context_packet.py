from __future__ import annotations

from .contracts import AppState, ChatContextPacket, ChatMessage
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
        "ambiguity_score": len(reasons),
        "ambiguity_reasons": reasons,
        "llm_candidate": llm_candidate,
    }
