from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from app.engines.parser.math_ocr_normalizer import (
    clean_visible_math_text,
    is_metadata_or_choice_noise_line,
    ocr_noise_score,
)
from app.engines.parser.school_math_taxonomy import classify_school_math_topic
from app.utils.math_patterns import detect_math_signal_score


QUESTION_RE = re.compile(r"(값은\??|구하시오|옳은 것은|정답|무엇인가|몇\s*개|얼마)")
QUESTION_SUFFIX_RE = re.compile(r"(의\s*값은\??|값은\??|구하시오\.?|옳은\s*것은\??|정답[은: ]?)", re.IGNORECASE)
FUNCTION_EQUATION_RE = re.compile(r"\b([yY])\s*=\s*([0-9xXdD+\-*/^().\s]+)")
OCR_Y_EQUATION_RE = re.compile(r"(?<!\S)([/\\|])\s*=\s*([0-9xXdD+\-*/^().\s]+)")
VARIABLE_ASSIGNMENT_RE = re.compile(r"\b([xX])\s*=\s*([+-]?\d+(?:\.\d+)?)")


@dataclass(frozen=True, slots=True)
class RankedMathCandidate:
    text: str
    kind: str
    topic: str
    score: float
    source: str = "ocr"


def _candidate_kind(text: str) -> str:
    lowered = text.lower()
    if QUESTION_RE.search(text):
        return "problem"
    if "f(" in lowered or "g(" in lowered or re.search(r"\by\s*=", lowered):
        return "function"
    if "=" in text and re.search(r"[a-zA-Z]", text):
        return "equation"
    if "sqrt" in lowered or "√" in text or "^" in text:
        return "radical_power"
    return "expression"


def _score_candidate(text: str) -> float:
    math_score = detect_math_signal_score(text)
    topic, topic_confidence = classify_school_math_topic(text)
    bonus = 0.0
    if QUESTION_RE.search(text):
        bonus += 0.18
    if re.search(r"\d", text):
        bonus += 0.08
    if any(token in text for token in ("=", "^", "/", "sqrt", "√", "(", ")")):
        bonus += 0.08
    penalty = min(0.35, ocr_noise_score(text) * 0.08)
    if topic == "unknown":
        topic_confidence = 0.0
    return max(0.0, min(1.0, math_score * 0.52 + topic_confidence * 0.32 + bonus - penalty))


def _compact_math_fragment(lhs: str, rhs: str) -> str:
    left = str(lhs or "").strip().lower()
    right = str(rhs or "").strip()
    right = re.sub(r"(?<![a-zA-Z])d\s*(?=[xX])", "2", right, flags=re.IGNORECASE)
    right = re.sub(r"\s+", "", right)
    right = re.sub(r"[^0-9a-zA-Z+\-*/^().].*$", "", right)
    if left and right:
        return f"{left}={right}"
    return ""


def _extract_embedded_math_fragments(line: str) -> list[str]:
    fragments: list[str] = []

    def _append(fragment: str) -> None:
        if fragment and fragment not in fragments:
            fragments.append(fragment)

    for match in FUNCTION_EQUATION_RE.finditer(line):
        _append(_compact_math_fragment(match.group(1), match.group(2)))

    if "함수" in line:
        for match in OCR_Y_EQUATION_RE.finditer(line):
            _append(_compact_math_fragment("y", match.group(2)))

    for match in VARIABLE_ASSIGNMENT_RE.finditer(line):
        _append(_compact_math_fragment(match.group(1), match.group(2)))

    return fragments


def iter_ranked_math_candidates(texts: Iterable[str], source: str = "ocr") -> list[RankedMathCandidate]:
    ranked: list[RankedMathCandidate] = []
    seen: set[str] = set()

    def _append_candidate(text: str, candidate_source: str) -> None:
        if not text or text in seen:
            return
        score = _score_candidate(text)
        if score < 0.2:
            return
        topic, _ = classify_school_math_topic(text)
        ranked.append(
            RankedMathCandidate(
                text=text,
                kind=_candidate_kind(text),
                topic=topic,
                score=score,
                source=candidate_source,
            )
        )
        seen.add(text)

    for text in texts:
        for raw_line in str(text or "").splitlines():
            line = clean_visible_math_text(raw_line)
            if not line:
                continue
            for fragment in _extract_embedded_math_fragments(line):
                _append_candidate(fragment, f"{source}:fragment")
            math_score = detect_math_signal_score(line)
            if is_metadata_or_choice_noise_line(line, math_score=math_score):
                continue
            if len(line) < 3 or ocr_noise_score(line) >= 3:
                continue
            _append_candidate(line, source)
    return sorted(ranked, key=lambda item: (item.score, len(item.text)), reverse=True)


def extract_expression_texts(*texts: str, limit: int = 6) -> list[str]:
    expressions: list[str] = []
    for candidate in iter_ranked_math_candidates(texts):
        if candidate.kind == "problem":
            cleaned = QUESTION_SUFFIX_RE.sub("", candidate.text).strip(" .,:;")
        else:
            cleaned = candidate.text
        cleaned = re.sub(r"=\s*\?\s*\d*$", "", cleaned).strip(" .,:;")
        if re.search(r"[가-힣]", cleaned):
            continue
        if not re.search(r"\d", cleaned):
            continue
        if not re.search(r"[+\-*/=^]|sqrt|√|log|\d+\s*[°º]", cleaned, flags=re.IGNORECASE):
            continue
        if cleaned and cleaned not in expressions:
            expressions.append(cleaned)
        if len(expressions) >= limit:
            break
    return expressions


def select_problem_statement(content_text: str, expressions: list[str] | None = None) -> str:
    ranked = iter_ranked_math_candidates([content_text])
    for candidate in ranked:
        if candidate.kind == "problem" and "|" not in candidate.text:
            return candidate.text
    if expressions:
        return str(expressions[0] or "").strip()
    return ranked[0].text if ranked else clean_visible_math_text(content_text)
