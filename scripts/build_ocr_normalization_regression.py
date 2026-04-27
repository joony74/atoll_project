from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.engines.parser.math_ocr_normalizer import normalize_ocr_math_text
from scripts.build_math_normalization_profile import (
    extract_math_fragments,
    iter_problem_bank_records,
    latex_to_runtime_expr,
    simulated_ocr_pairs,
)


DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_ocr_regression_cases.json"

HIGH_SIGNAL_REASONS = {
    "latex_runtime_rewrite",
    "sqrt_spacing",
    "sqrt_marker_noise",
    "log_spacing",
    "log_read_as_108",
    "power_degree_mark",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def compact(value: str) -> str:
    text = str(value or "")
    text = text.replace("**", "^")
    text = re.sub(r"\s+", "", text)
    return text.strip()


def normalization_contains(noisy: str, expected: str) -> tuple[bool, str]:
    normalized = normalize_ocr_math_text(noisy)
    return compact(expected) in compact(normalized), normalized


def _case_key(noisy: str, expected: str) -> tuple[str, str]:
    return compact(noisy), compact(expected)


def _direct_rewrite_case(fragment: str) -> tuple[str, str, str] | None:
    if not any(token in fragment for token in ("\\frac", "\\sqrt", "\\log", "\\sin", "\\cos", "\\tan", "\\cdot", "\\times")):
        return None
    if "\\frac" in fragment and not re.search(r"\\frac\s*\{[^{}]{1,80}\}\s*\{[^{}]{1,80}\}", fragment):
        return None
    expected = latex_to_runtime_expr(fragment)
    if not expected or compact(expected) == compact(fragment):
        return None
    return fragment, expected, "latex_runtime_rewrite"


def candidate_cases_for_record(record: dict[str, Any]) -> list[dict[str, Any]]:
    content = record.get("content") or {}
    taxonomy = record.get("taxonomy") or {}
    fragments = extract_math_fragments(
        str(content.get("problem_latex") or ""),
        str(content.get("solution_latex") or ""),
        str(content.get("problem_plain") or ""),
        str(content.get("solution_plain") or ""),
    )
    cases: list[dict[str, Any]] = []
    bank_id = str(record.get("_bank_id") or "unknown")
    record_id = str(record.get("id") or "")
    subject_slug = str(taxonomy.get("subject_slug") or taxonomy.get("subject") or "unknown")
    level_number = int(taxonomy.get("level_number") or 0)

    for fragment in fragments[:12]:
        direct = _direct_rewrite_case(fragment)
        generated: list[tuple[str, str, str]] = []
        if direct is not None:
            generated.append(direct)
        generated.extend(
            (pair["noisy"], pair["normalized"], pair["reason"])
            for pair in simulated_ocr_pairs(fragment)
            if pair.get("reason") in HIGH_SIGNAL_REASONS
        )
        for noisy, expected, reason in generated:
            passed, normalized = normalization_contains(noisy, expected)
            if not passed:
                continue
            cases.append(
                {
                    "bank_id": bank_id,
                    "record_id": record_id,
                    "subject_slug": subject_slug,
                    "level_number": level_number,
                    "reason": reason,
                    "source_expression": fragment,
                    "noisy_text": noisy,
                    "expected_contains": expected,
                    "normalized_preview": normalized[:240],
                }
            )
    return cases


def build_regression_payload(max_cases: int = 180, per_reason: int = 40, per_bank: int = 60) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    reason_counts: Counter[str] = Counter()
    reason_bank_counts: Counter[tuple[str, str]] = Counter()
    bank_counts: Counter[str] = Counter()
    subject_counts: Counter[str] = Counter()
    scanned_records = 0
    per_reason_bank = max(2, per_reason // 4)

    for record in iter_problem_bank_records():
        scanned_records += 1
        for case in candidate_cases_for_record(record):
            reason = str(case["reason"])
            bank_id = str(case["bank_id"])
            noisy_key, expected_key = _case_key(str(case["noisy_text"]), str(case["expected_contains"]))
            key = (bank_id, noisy_key, expected_key)
            if key in seen:
                continue
            if reason_bank_counts[(reason, bank_id)] >= per_reason_bank:
                continue
            if bank_counts[bank_id] >= per_bank:
                continue
            seen.add(key)
            reason_counts.update([reason])
            reason_bank_counts.update([(reason, bank_id)])
            bank_counts.update([bank_id])
            subject_counts.update([str(case["subject_slug"])])
            case["case_id"] = f"ocr_norm_{len(cases) + 1:04d}"
            cases.append(case)
            if len(cases) >= max_cases:
                break
        if len(cases) >= max_cases:
            break

    return {
        "schema_version": "coco_ocr_regression_cases.v1",
        "generated_at": utc_now(),
        "source": {
            "scanned_records": scanned_records,
            "max_cases": max_cases,
            "selection": "problem_bank_math_fragments_that_current_normalizer_can_recover",
        },
        "coverage": {
            "case_count": len(cases),
            "by_reason": dict(sorted(reason_counts.items())),
            "by_bank": dict(sorted(bank_counts.items())),
            "by_subject": dict(sorted(subject_counts.items())),
        },
        "cases": cases,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build data-backed OCR normalization regression cases from Coco's problem bank.")
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--max-cases", type=int, default=180)
    parser.add_argument("--per-reason", type=int, default=40)
    parser.add_argument("--per-bank", type=int, default=60)
    args = parser.parse_args()

    payload = build_regression_payload(
        max_cases=max(1, args.max_cases),
        per_reason=max(1, args.per_reason),
        per_bank=max(1, args.per_bank),
    )
    write_json(args.output_path, payload)
    print(f"output={args.output_path}")
    print(f"case_count={payload['coverage']['case_count']}")
    print(f"by_reason={payload['coverage']['by_reason']}")
    print(f"by_bank={payload['coverage']['by_bank']}")
    return 0 if payload["cases"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
