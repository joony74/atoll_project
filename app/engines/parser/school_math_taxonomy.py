from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class TopicSpec:
    key: str
    label: str
    school_band: str
    patterns: tuple[str, ...]


TOPIC_SPECS: tuple[TopicSpec, ...] = (
    TopicSpec("calculus_integral", "적분", "high", (r"∫|적분|넓이.*함수",)),
    TopicSpec("calculus_derivative", "미분", "high", (r"미분|도함수|접선|극대|극소|f'\(|f′\(",)),
    TopicSpec("trigonometry", "삼각함수", "high", (r"\b(?:sin|cos|tan)\b|삼각함수|사인|코사인|탄젠트|π|pi",)),
    TopicSpec("logarithm", "지수·로그", "high", (r"\blog\b|로그|지수함수|밑",)),
    TopicSpec("sequence", "수열", "high", (r"수열|등차|등비|an\b|a_n|시그마|Σ|sum",)),
    TopicSpec("probability", "확률", "middle_high", (r"확률|경우의 수|순열|조합|P\(|C\(|!",)),
    TopicSpec("statistics", "통계", "middle_high", (r"평균|분산|표준편차|중앙값|최빈값|도수|상관",)),
    TopicSpec("coordinate_geometry", "좌표·그래프", "middle_high", (r"좌표|그래프|기울기|절편|\(\s*-?\d+\s*,\s*-?\d+\s*\)",)),
    TopicSpec("function", "함수", "middle_high", (r"\bf\(|\bg\(|y\s*=|함수|정의역|치역",)),
    TopicSpec("quadratic", "이차방정식", "middle_high", (r"x\s*(?:\^\(?2\)?|²)\b|이차|판별식|근의 공식",)),
    TopicSpec("linear_equation", "일차방정식", "middle", (r"[a-zA-Z]\s*=|=\s*-?\d|방정식|연립",)),
    TopicSpec("geometry", "도형", "elementary_middle", (r"삼각형|사각형|원|반지름|지름|넓이|둘레|부피|각도|평행|수직",)),
    TopicSpec("fraction_ratio", "분수·비율", "elementary_middle", (r"\d+\s*/\s*\d+|분수|비율|비례|퍼센트|%",)),
    TopicSpec("radical_power", "루트·거듭제곱", "middle_high", (r"sqrt|√|\^\(?-?\d|\d+\s*[°º]|제곱|거듭제곱|루트",)),
    TopicSpec("arithmetic", "계산", "elementary", (r"\d+\s*[+\-*/]\s*\d+|값은|계산",)),
)

TOPIC_LABELS = {spec.key: spec.label for spec in TOPIC_SPECS} | {"unknown": "문제 유형 확인 중"}


def topic_label(topic: str) -> str:
    return TOPIC_LABELS.get(str(topic or "unknown"), TOPIC_LABELS["unknown"])


def classify_school_math_topic(text: str, expressions: Iterable[str] = ()) -> tuple[str, float]:
    joined = f"{text or ''}\n" + "\n".join(str(item or "") for item in expressions)
    if not joined.strip():
        return "unknown", 0.0

    best_key = "unknown"
    best_hits = 0
    for spec in TOPIC_SPECS:
        hits = sum(1 for pattern in spec.patterns if re.search(pattern, joined, flags=re.IGNORECASE))
        if hits > best_hits:
            best_key = spec.key
            best_hits = hits

    if best_key == "unknown":
        return "unknown", 0.0
    return best_key, min(0.95, 0.45 + best_hits * 0.2)
