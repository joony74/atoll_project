from __future__ import annotations

from .context_packet import build_chat_context_packet
from .contracts import AppState
from .composer import build_image_capability_reply, is_image_capability_prompt
from .grounding import build_main_chat_grounding
from .llm_slot import maybe_generate_main_chat_reply
from .main_engine import build_main_chat_reply as build_local_main_chat_reply


def build_main_chat_reply(prompt: str, state: AppState | None = None) -> str:
    normalized = str(prompt or "").strip()
    resolved_state = state or {}
    if is_image_capability_prompt(normalized):
        grounding = build_main_chat_grounding(normalized, resolved_state)
        has_documents = bool(resolved_state.get("documents"))
        return build_image_capability_reply(has_documents=has_documents, grounding=grounding)

    packet = build_chat_context_packet(prompt, state=state)
    llm_reply = maybe_generate_main_chat_reply(packet)
    if llm_reply:
        return llm_reply
    return build_local_main_chat_reply(prompt, state=state)
