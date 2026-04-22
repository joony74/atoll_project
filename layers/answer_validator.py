from __future__ import annotations

import re


def _normalize_answer_text(text: str) -> str:
    return str(text or "").strip().replace(" ", "")


def _match_choice(answer: str, choices: list[str]) -> str:
    normalized_answer = _normalize_answer_text(answer)
    for choice in choices:
        norm_choice = _normalize_answer_text(choice)
        if normalized_answer and normalized_answer in norm_choice:
            return choice
    return ""


def validate_answer(parsed_problem: dict, solver_output: dict) -> dict:
    result = dict(solver_output or {})
    answer = str(result.get("computed_answer") or "").strip()
    steps = [str(step).strip() for step in (result.get("steps") or []) if str(step).strip()]
    choices = list(parsed_problem.get("choices") or [])

    status = "verified"
    if not answer:
        status = "failed"
    elif not steps:
        status = "needs_review"

    matched_choice = ""
    if choices and answer:
        matched_choice = _match_choice(answer, choices)
        if matched_choice:
            result["matched_choice"] = matched_choice

    if parsed_problem.get("problem_type") == "probability" and answer and not re.search(r"\d", answer):
        status = "needs_review"

    result["validation"] = {
        "status": status,
        "matched_choice": matched_choice,
    }
    result["confidence"] = float(result.get("confidence") or 0.0)
    if status == "failed":
        result["confidence"] = min(result["confidence"], 0.25)
    elif status == "needs_review":
        result["confidence"] = min(max(result["confidence"], 0.45), 0.69)
    else:
        result["confidence"] = max(result["confidence"], 0.72)
    return result
