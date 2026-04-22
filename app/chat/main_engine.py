from __future__ import annotations

import time

from .contracts import AppState
from .composer import (
    build_app_help_reply,
    build_concept_reply,
    build_content_request_reply,
    build_emotional_reply,
    build_general_reply,
    build_opinion_reply,
    build_self_info_reply,
    build_smalltalk_reply,
)
from .followup import build_followup_reply
from .grounding import build_main_chat_grounding, remember_custom_concept, resolve_known_concept_term, search_concept
from .handoff import build_math_handoff_reply
from .router import classify_main_chat_intent, extract_concept_term


def _main_chat_context(state: AppState) -> dict:
    context = state.setdefault("main_chat_context", {})
    if not isinstance(context, dict):
        context = {}
        state["main_chat_context"] = context
    return context


def _remember_main_chat_intent(
    state: AppState,
    intent: str,
    concept_term: str | None = None,
    concept_stage: str | None = None,
) -> None:
    context = _main_chat_context(state)
    context["last_intent"] = intent
    context["last_updated_at"] = time.time()
    if intent == "concept":
        context["last_concept_term"] = str(concept_term or "").strip() or None
        context["last_concept_stage"] = str(concept_stage or "").strip() or "intro"
        return
    context["last_concept_term"] = None
    context["last_concept_stage"] = None


def build_main_chat_reply(prompt: str, state: AppState | None = None) -> str:
    normalized = str(prompt or "").strip()
    resolved_state = state or {}
    has_documents = bool(resolved_state.get("documents"))
    custom_concepts = resolved_state.get("custom_concepts")
    followup_reply, followup_term, followup_stage, followup_concept = build_followup_reply(
        normalized,
        resolved_state.get("main_chat_history", []),
        has_documents,
        context=_main_chat_context(resolved_state),
        custom_concepts=custom_concepts,
    )
    if followup_reply:
        if followup_term:
            _remember_main_chat_intent(resolved_state, "concept", concept_term=followup_term, concept_stage=followup_stage)
            if followup_concept:
                remember_custom_concept(
                    resolved_state,
                    followup_term,
                    str(followup_concept.get("summary") or followup_reply),
                    source=str(followup_concept.get("source") or "chat"),
                    confidence=str(followup_concept.get("confidence") or "low"),
                )
        else:
            _remember_main_chat_intent(resolved_state, "general")
        return followup_reply
    intent = classify_main_chat_intent(normalized, custom_concepts=custom_concepts)
    grounding = build_main_chat_grounding(normalized, resolved_state)

    if intent == "smalltalk":
        _remember_main_chat_intent(resolved_state, "smalltalk")
        return build_smalltalk_reply(normalized)
    if intent == "self_info":
        _remember_main_chat_intent(resolved_state, "self_info")
        return build_self_info_reply(normalized, has_documents=has_documents)
    if intent == "emotional":
        _remember_main_chat_intent(resolved_state, "emotional")
        return build_emotional_reply(normalized)
    if intent == "app_help":
        _remember_main_chat_intent(resolved_state, "app_help")
        return build_app_help_reply(normalized, has_documents=has_documents, grounding=grounding)
    if intent == "content_request":
        _remember_main_chat_intent(resolved_state, "content_request")
        return build_content_request_reply(normalized)
    if intent == "concept":
        concept_term = (
            extract_concept_term(normalized)
            or resolve_known_concept_term(normalized, custom_concepts=custom_concepts)
            or normalized
        )
        concept = search_concept(concept_term, custom_concepts=custom_concepts)
        _remember_main_chat_intent(resolved_state, "concept", concept_term=concept_term, concept_stage="intro")
        reply = build_concept_reply(
            normalized,
            concept=concept,
            has_documents=has_documents,
        )
        if concept:
            remember_custom_concept(
                resolved_state,
                concept_term,
                str(concept.get("summary") or reply),
                source=str(concept.get("source") or "chat"),
                confidence=str(concept.get("confidence") or "low"),
            )
        return reply
    if intent == "math":
        _remember_main_chat_intent(resolved_state, "math")
        return build_math_handoff_reply(has_documents=has_documents)
    if intent == "opinion":
        _remember_main_chat_intent(resolved_state, "opinion")
        return build_opinion_reply(normalized)
    _remember_main_chat_intent(resolved_state, "general")
    return build_general_reply(normalized, grounding=grounding)
