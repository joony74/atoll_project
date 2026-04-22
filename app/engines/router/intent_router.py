from __future__ import annotations

from app.core.config import settings
from app.utils.math_patterns import (
    contains_math_like_tokens,
    detect_exam_layout_pattern,
    detect_math_signal_score,
    detect_multiple_choice_pattern,
    detect_question_pattern,
)


def route_intent(user_query: str, merged_text: str, upload_present: bool, active_problem_present: bool = False) -> dict:
    signal_text = f"{user_query} {merged_text}".strip()
    signal_score = detect_math_signal_score(signal_text)
    math_like = (
        contains_math_like_tokens(signal_text)
        or detect_question_pattern(signal_text)
        or detect_multiple_choice_pattern(signal_text)
        or detect_exam_layout_pattern(signal_text)
    )

    if upload_present and (math_like or signal_score >= settings.math_min_signal_score):
        return {"route": "math_problem_pipeline", "confidence": max(signal_score, 0.7)}
    if active_problem_present and (math_like or signal_score >= settings.math_min_signal_score / 2):
        return {"route": "math_followup_pipeline", "confidence": max(signal_score, 0.65)}
    return {"route": "generic_chat", "confidence": signal_score}
