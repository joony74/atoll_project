from __future__ import annotations

import re


MATH_SIGNAL_PATTERNS = (
    r"\bcos\b",
    r"\bsin\b",
    r"\btan\b",
    r"pi|π",
    r"\d+\s*/\s*\d+",
    r"[=+\-*/^]",
    r"√|sqrt",
    r"f\(x\)|g\(x\)|y\s*=",
    r"lim",
    r"기울기|구하시오|값은|옳은 것은|정답",
)

QUESTION_PATTERNS = (
    r"값은\??",
    r"구하시오",
    r"옳은 것은",
    r"보기",
    r"정답",
)

MULTIPLE_CHOICE_PATTERNS = (
    r"[①②③④⑤]",
    r"[ㄱㄴㄷㄹㅁ]",
    r"\b[1-5][\).]",
)


def detect_math_signal_score(text: str) -> float:
    normalized = str(text or "")
    hits = 0
    for pattern in MATH_SIGNAL_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            hits += 1
    if not normalized.strip():
        return 0.0
    return min(hits / max(len(MATH_SIGNAL_PATTERNS) / 2, 1), 1.0)


def contains_math_like_tokens(text: str) -> bool:
    return detect_math_signal_score(text) >= 0.2


def detect_question_pattern(text: str) -> bool:
    normalized = str(text or "")
    return any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in QUESTION_PATTERNS)


def detect_multiple_choice_pattern(text: str) -> bool:
    normalized = str(text or "")
    return any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in MULTIPLE_CHOICE_PATTERNS)


def detect_exam_layout_pattern(text: str) -> bool:
    normalized = str(text or "")
    return bool(re.search(r"(보기|문항|배점|학년도|모의고사|수능)", normalized))
