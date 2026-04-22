from __future__ import annotations

import re


def _normalize(value: str) -> str:
    text = str(value or "").lower().strip()
    text = text.replace(" ", "")
    return text


KEYWORD_GROUPS = (
    ("270도", ("270도", "3π/2", "3pi/2")),
    ("x좌표", ("x좌표", "x값", "코사인")),
    ("인수분해", ("인수분해", "(x-", "x-")),
    ("기울기", ("기울기", "계수", "a=")),
    ("y절편", ("y절편", "x=0", "b=")),
)


def select_relevant_step(solution_steps: list[str], user_question: str) -> str | None:
    steps = [str(step).strip() for step in (solution_steps or []) if str(step).strip()]
    if not steps:
        return None

    normalized_question = _normalize(user_question)

    for _, tokens in KEYWORD_GROUPS:
        if any(_normalize(token) in normalized_question for token in tokens):
            for step in steps:
                normalized_step = _normalize(step)
                if any(_normalize(token) in normalized_step for token in tokens):
                    return step

    quoted = re.findall(r"['\"]([^'\"]+)['\"]", str(user_question or ""))
    for phrase in quoted:
        normalized_phrase = _normalize(phrase)
        for step in steps:
            if normalized_phrase and normalized_phrase in _normalize(step):
                return step

    for step in steps:
        tokens = [token for token in re.split(r"[^0-9A-Za-z가-힣π]+", str(step)) if len(token) >= 2]
        if any(_normalize(token) in normalized_question for token in tokens):
            return step

    if len(steps) >= 2:
        return steps[1]
    return steps[0]

