from __future__ import annotations

import json
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, TypedDict

from app.utils.choice_parser import parse_choices
from app.utils.text_normalizer import normalize_math_text
from app.engines.router.school_level_router import normalize_school_level


APP_SUPPORT_DIR = Path.home() / "Library" / "Application Support" / "CocoAIStudy"
DEFAULT_OBSERVATION_PATH = APP_SUPPORT_DIR / "learning" / "ocr_normalization_observations.json"
LEVEL_OBSERVATION_PATHS = {
    "elementary": APP_SUPPORT_DIR / "learning" / "elementary" / "ocr_normalization_observations.json",
    "middle": APP_SUPPORT_DIR / "learning" / "middle" / "ocr_normalization_observations.json",
    "high": APP_SUPPORT_DIR / "learning" / "high" / "ocr_normalization_observations.json",
    "unknown": APP_SUPPORT_DIR / "learning" / "unknown" / "ocr_normalization_observations.json",
}
MAX_OBSERVED_CASES = 500

STACKED_FRACTIONAL_POWER_MARK_RE = re.compile(r"(?<!\d)(\d{1,4})[\*\?][xX*](\d{1,4})[\?°º](?!\d)")
STACKED_FRACTIONAL_POWER_COMPACT_RE = re.compile(r"(?<!\d)(\d{1,4})[\*\?][xX*](\d{1,4})3(?!\d)")
SQRT_CUBERT_PAIR_RE = re.compile(r"(\d+)\s*[\*\?]\s*[xX*]\s*(\d+)\s*[°º]")
SQRT_CUBERT_OCR_COMPACT_RE = re.compile(r"(?<!\d)(\d{1,4})\?\s*[xX*]\s*(\d{1,4})3(?!\d)")
SEQUENCE_LOG_PRODUCT_EXPR_RE = re.compile(
    r"sequence_log_product\(base=(?P<base>\d+),start=(?P<start>\d+),increment=(?P<increment>-?\d+),count=(?P<count>\d+)\)"
)


class AutoNormalizationCandidate(TypedDict, total=False):
    expression: str
    rule_id: str
    source_text: str
    confidence: float


def _compact_text(text: str) -> str:
    return normalize_math_text(text).replace(" ", "")


def _append_candidate(
    candidates: list[AutoNormalizationCandidate],
    *,
    expression: str,
    rule_id: str,
    source_text: str,
    confidence: float,
) -> None:
    cleaned = str(expression or "").replace(" ", "").strip(" .,:;")
    if not cleaned:
        return
    if any(item.get("expression") == cleaned for item in candidates):
        return
    candidates.append(
        {
            "expression": cleaned,
            "rule_id": rule_id,
            "source_text": str(source_text or "").strip()[:240],
            "confidence": confidence,
        }
    )


def _has_fractional_power_pair(candidates: list[AutoNormalizationCandidate], left: str, right: str) -> bool:
    prefix = f"{left}^("
    middle = f"*{right}^("
    return any(str(item.get("expression") or "").startswith(prefix) and middle in str(item.get("expression") or "") for item in candidates)


def _integer_log(value: int, base: int) -> int | None:
    if base <= 1 or value <= 0:
        return None
    power = 0
    current = 1
    while current < value:
        current *= base
        power += 1
    return power if current == value else None


def _choice_numbers(text: str) -> list[int]:
    values: list[int] = []
    for choice in parse_choices(text):
        match = re.search(r"[-+]?\d+", choice)
        if not match:
            continue
        value = int(match.group(0))
        if value not in values:
            values.append(value)
    return values


def _infer_log_sequence_product_count(*, base: int, start: int, increment: int, text: str) -> int | None:
    compact = _compact_text(text)
    explicit_patterns = (
        rf"a[_{{]?\s*(\d+)[]}}]?\s*=\s*{base}\s*\^?\s*k",
        rf"a[,，_]?\s*(\d+)\s*=\s*{base}\s*\^?\s*k",
    )
    for pattern in explicit_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    compact_match = re.search(rf"a(\d+)={base}\^?k", compact, flags=re.IGNORECASE)
    if compact_match:
        return int(compact_match.group(1))

    start_power = _integer_log(start, base)
    if start_power is None:
        return None
    choices = set(_choice_numbers(text))
    if not choices:
        return None
    matched_counts: list[int] = []
    for count in range(2, 41):
        exponent = count * start_power + increment * count * (count - 1) // 2
        if exponent in choices:
            matched_counts.append(count)
    return matched_counts[0] if len(matched_counts) == 1 else None


def _infer_sequence_log_product_candidate(text: str) -> AutoNormalizationCandidate | None:
    source = normalize_math_text(str(text or "")).replace("\\n", "\n")
    compact = source.replace(" ", "")
    if not ("수열" in source and "log" in source.lower() and "상수" in source):
        return None
    if not re.search(r"=\s*[-+]?\d+\s*\+\s*log|=\s*1\s*\+\s*log|=1\+log", source, flags=re.IGNORECASE):
        return None
    if not re.search(r"a[,，_1\s]*=\s*\d", source, flags=re.IGNORECASE):
        return None

    start_match = re.search(r"a\s*[,，_1l]*\s*=\s*(\d+)", source, flags=re.IGNORECASE)
    if not start_match:
        return None
    start = int(start_match.group(1))

    increment_match = re.search(r"=\s*([-+]?\d+)\s*\+\s*log|=([-+]?\d+)\+log", source, flags=re.IGNORECASE)
    increment = int(next((item for item in (increment_match.groups() if increment_match else ()) if item), "1"))

    base = 0
    base_match = re.search(r"log[_\s,]*(\d+)", source, flags=re.IGNORECASE)
    if base_match:
        base = int(base_match.group(1))
    elif re.search(r"log[yz]", source, flags=re.IGNORECASE):
        base = 2
    else:
        product_base_match = re.search(r"상수.*?=\s*(\d+)|=\s*(\d+)\s*(?:일|때)\s*상수", source)
        if product_base_match:
            base = int(next(item for item in product_base_match.groups() if item))
    if base <= 1:
        base = start if start > 1 else 2

    count = _infer_log_sequence_product_count(base=base, start=start, increment=increment, text=source)
    if count is None:
        return None

    return {
        "expression": f"sequence_log_product(base={base},start={start},increment={increment},count={count})",
        "rule_id": "sequence_log_product",
        "source_text": source[:240],
        "confidence": 0.83,
    }


@lru_cache(maxsize=8)
def load_upload_learning_summary(path: str | None = None, school_level: str | None = None) -> dict[str, Any]:
    payload = _load_observation_payload(Path(path) if path else observation_path_for_school_level(school_level))
    summary = payload.get("summary") if isinstance(payload, dict) else {}
    return summary if isinstance(summary, dict) else {}


def observation_path_for_school_level(school_level: str | None) -> Path:
    level = normalize_school_level(school_level)
    return LEVEL_OBSERVATION_PATHS.get(level, LEVEL_OBSERVATION_PATHS["unknown"])


def _learned_rule_boost(rule_id: str, school_level: str | None = None) -> tuple[float, dict[str, int]]:
    counts = ((load_upload_learning_summary(school_level=school_level).get("rule_counts") or {}).get(rule_id) or {})
    try:
        seen = int(counts.get("seen") or 0)
        verified = int(counts.get("verified") or 0)
        failed = int(counts.get("failed") or 0)
    except Exception:
        return 0.0, {"seen": 0, "verified": 0, "failed": 0}
    if seen <= 0:
        return 0.0, {"seen": 0, "verified": 0, "failed": 0}
    verified_rate = verified / max(seen, 1)
    failed_rate = failed / max(seen, 1)
    if seen >= 3 and verified_rate >= 0.8:
        return 0.05, {"seen": seen, "verified": verified, "failed": failed}
    if seen >= 3 and failed_rate >= 0.5:
        return -0.12, {"seen": seen, "verified": verified, "failed": failed}
    if verified > 0 and failed == 0:
        return 0.02, {"seen": seen, "verified": verified, "failed": failed}
    return 0.0, {"seen": seen, "verified": verified, "failed": failed}


def _apply_learned_rule_confidence(
    candidates: list[AutoNormalizationCandidate],
    *,
    school_level: str | None = None,
) -> list[AutoNormalizationCandidate]:
    adjusted: list[AutoNormalizationCandidate] = []
    for candidate in candidates:
        item = dict(candidate)
        rule_id = str(item.get("rule_id") or "")
        boost, counts = _learned_rule_boost(rule_id, school_level=school_level)
        try:
            confidence = float(item.get("confidence") or 0.0)
        except Exception:
            confidence = 0.0
        item["confidence"] = max(0.0, min(0.98, confidence + boost))
        if counts["seen"]:
            item["learned_seen"] = counts["seen"]
            item["learned_verified"] = counts["verified"]
            item["learned_failed"] = counts["failed"]
        adjusted.append(item)
    return sorted(adjusted, key=lambda value: float(value.get("confidence") or 0.0), reverse=True)


def clear_learning_cache() -> None:
    load_upload_learning_summary.cache_clear()


def infer_auto_normalization_candidates(
    text: str,
    *,
    school_level: str | None = None,
) -> list[AutoNormalizationCandidate]:
    """Infer reusable math-expression candidates from OCR layout artifacts.

    This is deliberately pattern-level, not problem-level: it looks for OCR
    structures that recur across uploaded worksheets, then emits normalized
    expression candidates that the solver can validate.
    """

    candidates: list[AutoNormalizationCandidate] = []
    raw_lines = [line.strip() for line in str(text or "").replace("\\n", "\n").splitlines() if line.strip()]

    for index, line in enumerate(raw_lines[:-1]):
        numerator_tokens = re.findall(r"(?<!\d)(\d+)(?!\d)", line)
        if len(numerator_tokens) != 2 or any(len(item) != 1 for item in numerator_tokens):
            continue
        numerators = [int(item) for item in numerator_tokens]
        for candidate_line in raw_lines[index + 1:index + 4]:
            compact_line = _compact_text(candidate_line)
            match = STACKED_FRACTIONAL_POWER_MARK_RE.search(compact_line)
            if not match:
                match = STACKED_FRACTIONAL_POWER_COMPACT_RE.search(compact_line)
            if not match:
                continue
            left, right = match.groups()
            _append_candidate(
                candidates,
                expression=f"{left}^({numerators[0]}/2)*{right}^({numerators[1]}/3)",
                rule_id="stacked_fractional_power",
                source_text=f"{line}\n{candidate_line}",
                confidence=0.91,
            )
            break

    normalized_text = normalize_math_text(str(text or "")).replace("\\n", "\n")
    compact_text = normalized_text.replace(" ", "")
    sequence_candidate = _infer_sequence_log_product_candidate(normalized_text)
    if sequence_candidate:
        _append_candidate(
            candidates,
            expression=sequence_candidate["expression"],
            rule_id=sequence_candidate["rule_id"],
            source_text=sequence_candidate["source_text"],
            confidence=sequence_candidate["confidence"],
        )

    for match in SQRT_CUBERT_PAIR_RE.finditer(normalized_text):
        left, right = match.groups()
        if _has_fractional_power_pair(candidates, left, right):
            continue
        _append_candidate(
            candidates,
            expression=f"{left}^(1/2)*{right}^(1/3)",
            rule_id="sqrt_cubert_marker_pair",
            source_text=match.group(0),
            confidence=0.72,
        )

    for match in SQRT_CUBERT_OCR_COMPACT_RE.finditer(compact_text):
        left, right = match.groups()
        if _has_fractional_power_pair(candidates, left, right):
            continue
        _append_candidate(
            candidates,
            expression=f"{left}^(1/2)*{right}^(1/3)",
            rule_id="sqrt_cubert_compact_ocr",
            source_text=match.group(0),
            confidence=0.68,
        )

    return _apply_learned_rule_confidence(candidates, school_level=school_level)[:6]


def infer_auto_expression_candidates(text: str, *, school_level: str | None = None) -> list[str]:
    return [item["expression"] for item in infer_auto_normalization_candidates(text, school_level=school_level)]


def is_fractional_power_ocr_statement(text: str) -> bool:
    normalized = normalize_math_text(str(text or ""))
    compact = normalized.replace(" ", "")
    return bool(
        SQRT_CUBERT_PAIR_RE.search(normalized)
        or STACKED_FRACTIONAL_POWER_MARK_RE.search(compact)
        or STACKED_FRACTIONAL_POWER_COMPACT_RE.search(compact)
        or SQRT_CUBERT_OCR_COMPACT_RE.search(compact)
    )


def _model_to_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return dict(value or {}) if isinstance(value, dict) else {}


def _load_observation_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": "coco_upload_ocr_normalization_learning.v1",
            "summary": {"case_count": 0, "rule_counts": {}},
            "cases": [],
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "schema_version": "coco_upload_ocr_normalization_learning.v1",
            "summary": {"case_count": 0, "rule_counts": {}},
            "cases": [],
        }
    return payload if isinstance(payload, dict) else {"cases": []}


def _summarize_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    rule_counts: dict[str, dict[str, int]] = {}
    quality_counts: dict[str, int] = {}
    verified_count = 0
    failed_count = 0
    for case in cases:
        status = str(case.get("validation_status") or "").strip().lower()
        quality = str(case.get("normalization_quality") or "unknown").strip() or "unknown"
        quality_counts[quality] = quality_counts.get(quality, 0) + 1
        verified = status in {"verified", "completed", "matched"}
        if verified:
            verified_count += 1
        elif status == "failed":
            failed_count += 1
        for candidate in case.get("auto_candidates") or []:
            rule_id = str((candidate or {}).get("rule_id") or "unknown")
            bucket = rule_counts.setdefault(rule_id, {"seen": 0, "verified": 0, "failed": 0})
            bucket["seen"] += 1
            if verified:
                bucket["verified"] += 1
            elif status == "failed":
                bucket["failed"] += 1
    return {
        "case_count": len(cases),
        "verified_count": verified_count,
        "failed_count": failed_count,
        "quality_counts": dict(sorted(quality_counts.items())),
        "rule_counts": dict(sorted(rule_counts.items())),
    }


def record_normalization_observation(
    *,
    image_path: str,
    structured_problem: Any,
    solve_result: Any,
    debug_payload: dict[str, Any] | None = None,
    storage_path: Path | None = None,
) -> None:
    problem = _model_to_dict(structured_problem)
    solved = _model_to_dict(solve_result)
    metadata = problem.get("metadata") or {}
    school_level = normalize_school_level(metadata.get("school_level"))
    path = storage_path or observation_path_for_school_level(school_level)
    content_hash = str(metadata.get("content_hash") or "").strip()
    source_text = "\n".join(str(item or "") for item in problem.get("source_text_candidates") or [])
    candidates = infer_auto_normalization_candidates(source_text, school_level=school_level)
    visual_template = metadata.get("visual_template") if isinstance(metadata.get("visual_template"), dict) else {}
    status = str(solved.get("validation_status") or "").strip().lower()
    normalization_quality = (
        "template_verified"
        if visual_template and status in {"verified", "completed", "matched"}
        else "verified"
        if status in {"verified", "completed", "matched"}
        else "failed"
        if status == "failed"
        else "unknown"
    )

    case = {
        "content_hash": content_hash,
        "image_path": str(image_path or ""),
        "updated_at": time.time(),
        "school_level": school_level,
        "school_profile": str(metadata.get("school_profile") or metadata.get("profile") or ""),
        "grade": metadata.get("grade"),
        "semester": metadata.get("semester"),
        "unit": str(metadata.get("unit") or ""),
        "normalization_quality": normalization_quality,
        "visual_template": visual_template,
        "normalized_problem_text": str(problem.get("normalized_problem_text") or ""),
        "expressions": [str(item or "") for item in problem.get("expressions") or []],
        "math_topic": str(problem.get("math_topic") or ""),
        "question_type": str(problem.get("question_type") or ""),
        "solver_name": str(solved.get("solver_name") or ""),
        "computed_answer": str(solved.get("computed_answer") or ""),
        "matched_choice": str(solved.get("matched_choice") or ""),
        "validation_status": str(solved.get("validation_status") or ""),
        "auto_candidates": candidates,
        "raw_text_preview": source_text[:600],
        "debug_keys": sorted((debug_payload or {}).keys()),
    }

    payload = _load_observation_payload(path)
    cases = [item for item in payload.get("cases") or [] if isinstance(item, dict)]
    key = content_hash or str(image_path or "")
    cases = [
        item
        for item in cases
        if (str(item.get("content_hash") or "") or str(item.get("image_path") or "")) != key
    ]
    cases.append(case)
    cases = cases[-MAX_OBSERVED_CASES:]
    payload["schema_version"] = "coco_upload_ocr_normalization_learning.v1"
    payload["updated_at"] = time.time()
    payload["summary"] = _summarize_cases(cases)
    payload["cases"] = cases

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)
    clear_learning_cache()
