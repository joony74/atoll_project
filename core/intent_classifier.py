from __future__ import annotations

import re


FOLLOWUP_PATTERNS = (
    "왜",
    "이해안가",
    "이해가안가",
    "왜이렇게",
    "왜270도",
    "x좌표가왜0",
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", str(text or "")).strip().lower()


def classify_intent(user_text: str) -> str:
    normalized = _normalize(user_text)
    if not normalized:
        return "unknown_intent"

    if "정답만" in normalized:
        return "show_answer_only"
    if "힌트" in normalized:
        return "show_hint"
    if "다시설명" in normalized:
        return "re_explain"
    if "더쉽게" in normalized:
        return "simplify_explanation"
    if "현재문제뭐야" in normalized or "현재문제" in normalized or "이문제뭐야" in normalized:
        return "show_current_problem"
    if "이전문제" in normalized:
        return "previous_problem"
    if "원래문제로" in normalized or "처음부터" in normalized:
        return "return_to_root_problem"
    if "이문제끝" in normalized:
        return "close_problem_session"
    if "비슷한문제" in normalized or "같은수준으로하나더" in normalized:
        return "generate_similar_problem"
    if "선행" in normalized or "더어렵게" in normalized:
        return "generate_next_problem"
    if "다음문제" in normalized:
        return "generate_next_problem"
    if "풀이" in normalized or "풀어줘" in normalized or "해설" in normalized:
        return "show_solution"
    if any(pattern in normalized for pattern in FOLLOWUP_PATTERNS):
        return "followup_question"
    return "unknown_intent"
