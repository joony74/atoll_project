from __future__ import annotations

import re
from typing import Any

from .composer import build_concept_reply
from .contracts import ChatMessage
from .contracts import ChatMessage, ConceptSearchResult, StoredConcept
from .grounding import resolve_known_concept_term, search_concept
from .router import extract_concept_term, is_concept_clarification_prompt, is_content_request_prompt


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
}

_TECH_KEYWORDS = ("기술", "구조", "작동", "원리", "만들어", "만들어졌", "답을 만드는")
_ROLE_KEYWORDS = ("역할", "무엇을 해", "뭘 해", "도와", "기능")
_CONCEPT_CLARIFIERS = ("이란", "란", "뭔데", "뭐지", "쉽게", "다시", "한마디로", "정리", "무슨 말")
_CONCEPT_REFERENCES = ("그게", "그건", "그거", "그 말", "그 뜻", "이게", "이건", "이 말")
_HISTORY_TRIM_MARKERS = (
    "내가 조금",
    "내 설명이",
    "내 답변이",
    "원하면",
    "필요하면",
    "학습리스트를 생성",
    "학습리스트를 만들",
)


def _concept_followup_style(term: str, last_assistant: str, normalized: str) -> str:
    if any(token in normalized for token in ("쉽게", "한마디로", "짧게", "간단히")):
        return "simple"
    if last_assistant.startswith("조금 더 풀어서 말하면,"):
        return "example"
    if last_assistant.startswith("예를 들면,"):
        return "usage"
    if last_assistant.startswith("그래서 ") or "중요한 이유" in last_assistant:
        return "simple"
    return "detail"


def _last_assistant_message(history: list[ChatMessage]) -> str:
    for item in reversed(history):
        if not isinstance(item, dict):
            continue
        if str(item.get("role") or "").strip() != "assistant":
            continue
        content = str(item.get("content") or "").strip()
        if content:
            return content
    return ""


def _is_short_followup(prompt: str) -> bool:
    normalized = str(prompt or "").strip()
    if not normalized:
        return False
    if normalized in _ACK_ONLY:
        return True
    return len(normalized) <= 10


def _last_user_concept_term(
    history: list[ChatMessage],
    current_prompt: str,
    custom_concepts: dict[str, StoredConcept] | None = None,
) -> str | None:
    skipped_current = False
    for item in reversed(history):
        if not isinstance(item, dict):
            continue
        if str(item.get("role") or "").strip() != "user":
            continue
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        if not skipped_current and content == current_prompt:
            skipped_current = True
            continue
        term = extract_concept_term(content) or resolve_known_concept_term(content, custom_concepts=custom_concepts)
        if term:
            return term
    return None


def _last_assistant_concept_term(
    history: list[ChatMessage],
    custom_concepts: dict[str, StoredConcept] | None = None,
) -> str | None:
    assistant = _last_assistant_message(history)
    matched = re.search(r"(.+?)에 대해 쉽게 말하면,", assistant)
    if matched:
        return str(matched.group(1) or "").strip() or None
    return resolve_known_concept_term(assistant, custom_concepts=custom_concepts)


def _clean_history_concept_summary(term: str, assistant: str) -> str:
    text = str(assistant or "").strip()
    if not text:
        return ""

    for prefix in (
        f"{term}에 대해 쉽게 말하면,",
        "조금 더 풀어서 말하면,",
        "예를 들면,",
        "그래서 ",
        "핵심만 다시 잡아보면,",
        "아주 짧게 다시 잡아보면,",
    ):
        if text.startswith(prefix):
            text = text[len(prefix) :].strip()
            break

    for marker in _HISTORY_TRIM_MARKERS:
        index = text.find(marker)
        if index > 0:
            text = text[:index].strip()
            break

    return re.sub(r"\s+", " ", text).strip(" ,.")


def _history_concept_result(term: str, assistant: str) -> dict[str, str] | None:
    summary = _clean_history_concept_summary(term, assistant)
    if not summary:
        return None
    return {
        "term": term,
        "summary": summary,
        "confidence": "low",
        "source": "history",
    }


def _next_concept_stage(previous_stage: str | None, normalized: str, last_assistant: str) -> str:
    if any(token in normalized for token in ("쉽게", "한마디로", "짧게", "간단히")):
        return "simple"
    if previous_stage in {None, "", "intro"}:
        return "detail"
    if previous_stage == "detail":
        return "example"
    if previous_stage == "example":
        return "usage"
    if previous_stage == "usage":
        return "simple"
    return _concept_followup_style("", last_assistant, normalized)


def _build_concept_followup(
    prompt: str,
    history: list[ChatMessage],
    has_documents: bool,
    context: dict[str, Any] | None = None,
    custom_concepts: dict[str, StoredConcept] | None = None,
) -> tuple[str | None, str | None, str | None, ConceptSearchResult | None]:
    normalized = str(prompt or "").strip()
    if not normalized:
        return None, None, None, None
    if normalized not in _ACK_ONLY and is_content_request_prompt(normalized):
        return None, None, None, None

    current_term = extract_concept_term(normalized) or resolve_known_concept_term(normalized, custom_concepts=custom_concepts)
    cached_term = str((context or {}).get("last_concept_term") or "").strip() or None
    cached_stage = str((context or {}).get("last_concept_stage") or "").strip() or None
    cached_intent = str((context or {}).get("last_intent") or "").strip() or None
    assistant_term = _last_assistant_concept_term(history, custom_concepts=custom_concepts)
    previous_term = _last_user_concept_term(history, normalized, custom_concepts=custom_concepts)
    resolved_term = current_term or cached_term or assistant_term or previous_term
    if not resolved_term:
        return None, None, None, None

    last_assistant = _last_assistant_message(history)
    is_concept_thread = (
        cached_intent == "concept"
        or bool(cached_term)
        or bool(previous_term)
        or bool(assistant_term)
        or "에 대해 쉽게 말하면," in last_assistant
        or "관련 개념을 더 깊게" in last_assistant
        or "이어서 설명해볼게요" in last_assistant
    )
    wants_clarify = (
        is_concept_clarification_prompt(normalized)
        or any(token in normalized for token in _CONCEPT_CLARIFIERS + _CONCEPT_REFERENCES)
        or (normalized in _ACK_ONLY and is_concept_thread)
    )
    if not is_concept_thread and not current_term:
        return None, None, None, None
    if not current_term and not wants_clarify:
        return None, None, None, None

    concept = search_concept(resolved_term, custom_concepts=custom_concepts) or _history_concept_result(resolved_term, last_assistant)
    followup_style = _next_concept_stage(cached_stage, normalized, last_assistant)
    return (
        build_concept_reply(
            resolved_term,
            concept=concept,
            has_documents=has_documents,
            followup=True,
            followup_style=followup_style,
        ),
        resolved_term,
        followup_style,
        concept,
    )


def _build_self_info_followup(prompt: str, has_documents: bool) -> str:
    normalized = str(prompt or "").strip()
    wants_tech = any(token in normalized for token in _TECH_KEYWORDS)
    wants_role = any(token in normalized for token in _ROLE_KEYWORDS)

    if wants_tech and not wants_role:
        if has_documents:
            return (
                "좋아요. 기술적인 구조 쪽으로 보면, 나는 메인챗에서는 자연스럽게 대화를 이어가고, "
                "학습리스트가 있을 때는 그 흐름과 연결될 수 있게 설계돼 있어요. 겉으로는 대화처럼 보이지만, "
                "안쪽에서는 질문 성격을 나누고 그에 맞는 답변 흐름을 선택하는 식으로 움직여요. "
                "원하면 다음엔 이 구조를 더 코드 관점으로 풀어볼게요."
            )
        return (
            "좋아요. 기술적인 구조 쪽으로 보면, 나는 메인챗에서 일상적인 대화를 이어가다가 "
            "학습리스트가 생기면 더 깊은 분석 흐름으로 연결되도록 설계돼 있어요. "
            "안쪽에서는 질문 성격을 나누고 그에 맞는 응답 흐름을 선택하는 식으로 움직여요. "
            "원하면 다음엔 이 구조를 더 쉽게 풀어서 말해볼게요."
        )

    if wants_role and not wants_tech:
        return (
            "좋아요. 내가 여기서 하는 역할 쪽으로 보면, 먼저 대화를 자연스럽게 이어가고 사용자가 지금 원하는 흐름을 파악하는 쪽에 가까워요. "
            "가볍게 이야기할 때는 메인챗으로 받고, 수학이나 학습 쪽으로 깊어지면 학습리스트 흐름으로 이어주는 역할도 같이 해요. "
            "원하면 다음엔 메인챗과 학습챗 역할 차이도 더 또렷하게 풀어볼게요."
        )

    return (
        "좋아요. 그러면 둘 다 자연스럽게 이어서 말해볼게요. 나는 코코앱 안에서 대화를 돕는 AI이고, "
        "겉으로는 편하게 대화하지만 안쪽에서는 질문 성격을 나누고 그에 맞는 흐름으로 답을 이어가도록 설계돼 있어요. "
        "한마디로 역할은 대화를 안내하는 쪽이고, 구조는 그 역할을 안정적으로 해내도록 나뉘어 있다고 보면 돼요. "
        "다음엔 기술적인 구조를 더 깊게 볼지, 역할을 더 구체적으로 볼지 하나만 골라줘도 좋아요."
    )


def _build_emotional_followup() -> str:
    return (
        "좋아요. 그럼 너무 길게 말하려고 하지 않아도 괜찮아요. 지금 마음에 가장 크게 남아 있는 장면이나, "
        "오늘 제일 힘들었던 순간 하나만 짧게 말해줘도 거기서부터 같이 이어볼 수 있어요."
    )


def _build_opinion_followup() -> str:
    return (
        "좋아요. 그럼 포인트를 하나씩 좁혀볼게요. 지금 네가 먼저 알고 싶은 게 맞는지 확인하고 싶은 건지, "
        "왜 그런지 이해하고 싶은 건지, 아니면 다음에 어떻게 해야 하는지가 궁금한 건지부터 말해주면 더 자연스럽게 이어갈 수 있어요."
    )


def build_followup_reply(
    prompt: str,
    history: list[ChatMessage],
    has_documents: bool,
    context: dict[str, Any] | None = None,
    custom_concepts: dict[str, StoredConcept] | None = None,
) -> tuple[str | None, str | None, str | None, ConceptSearchResult | None]:
    normalized = str(prompt or "").strip()
    if not normalized:
        return None, None, None, None

    last_assistant = _last_assistant_message(history)
    if not last_assistant:
        return None, None, None, None

    is_ack_followup = normalized in _ACK_ONLY
    concept_followup, concept_term, concept_stage, concept_payload = _build_concept_followup(
        normalized,
        history,
        has_documents=has_documents,
        context=context,
        custom_concepts=custom_concepts,
    )
    if concept_followup:
        return concept_followup, concept_term, concept_stage, concept_payload

    if (
        "기술적인 구조 쪽" in last_assistant
        or "어떤 역할을 하는지" in last_assistant
        or "어떤 역할을 하도록 설계됐는지" in last_assistant
        or "어떤 방식으로 답을 만드는지" in last_assistant
    ):
        if is_ack_followup or any(token in normalized for token in _TECH_KEYWORDS + _ROLE_KEYWORDS + ("둘 다",)):
            return _build_self_info_followup(normalized, has_documents=has_documents), None, None, None

    if any(token in last_assistant for token in ("뭐가 제일 피곤한지", "제일 걱정되는지", "천천히 말해줘도", "감정이 뭔지")):
        if is_ack_followup:
            return _build_emotional_followup(), None, None, None

    if any(token in last_assistant for token in ("가장 고민하는 포인트", "한 줄만 더 붙여주면", "조금만 더 말해주면")):
        if is_ack_followup:
            return _build_opinion_followup(), None, None, None

    return None, None, None, None
