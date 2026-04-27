from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.pipeline import run_solve_pipeline
from app.engines.parser.math_ocr_normalizer import normalize_ocr_math_text


MANIFEST_PATH = PROJECT_ROOT / "data" / "learning_test" / "school_math_bank_manifest.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_ocr_actual_cases.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def compact(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "").replace("**", "^")).lower()


def expression_hints(value: str) -> list[str]:
    hints: list[str] = []
    for part in re.split(r";|,", str(value or "")):
        cleaned = part.strip()
        if cleaned and cleaned not in hints:
            hints.append(cleaned)
    return hints


def normalized_contains(noisy_text: str, expected: str) -> tuple[bool, str]:
    normalized = normalize_ocr_math_text(noisy_text)
    return compact(expected) in compact(normalized), normalized


def collect_debug_texts(debug_payload: dict[str, Any]) -> list[tuple[str, str]]:
    texts: list[tuple[str, str]] = []

    def add(label: str, value: Any) -> None:
        text = str(value or "").strip()
        if not text:
            return
        compact_text = compact(text)
        if not compact_text:
            return
        if any(compact(existing) == compact_text for _, existing in texts):
            return
        texts.append((label, text))

    upload = debug_payload.get("upload") or {}
    add("pipeline_raw_text", upload.get("raw_text"))
    add("pipeline_content_text", upload.get("content_text"))
    add("pipeline_repaired_text", upload.get("repaired_text"))
    ocr_debug = (((upload.get("raw_text") or "") and {}) or {})
    # The full OCR details live in structured_problem.metadata, not in the compact
    # upload debug payload. This function also accepts that metadata object.
    if "ocr_debug" in debug_payload:
        ocr_debug = debug_payload.get("ocr_debug") or {}
    else:
        ocr_debug = upload.get("ocr_debug") or {}

    tesseract = ocr_debug.get("tesseract") or {}
    add("tesseract_selected", tesseract.get("text"))
    for index, item in enumerate(tesseract.get("passes") or [], start=1):
        add(f"tesseract_pass_{index}_{item.get('variant') or 'unknown'}", item.get("text"))

    text_repair = ocr_debug.get("text_repair") or {}
    add("text_repair_candidate", text_repair.get("candidate_text"))
    add("text_repair_text", text_repair.get("text"))
    return texts


def _debug_with_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    debug = dict(payload.get("debug") or {})
    problem = payload.get("structured_problem")
    metadata = getattr(problem, "metadata", {}) or {}
    if isinstance(metadata, dict):
        debug["ocr_debug"] = metadata.get("ocr_debug") or {}
    return debug


def select_records(records: list[dict[str, Any]], *, per_grade: int, limit: int, layout: str) -> list[dict[str, Any]]:
    filtered = [item for item in records if not layout or str(item.get("layout") or "") == layout]
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for item in filtered:
        grouped[(str(item.get("band") or ""), int(item.get("grade") or 0))].append(item)

    selected: list[dict[str, Any]] = []
    for key in sorted(grouped):
        selected.extend(grouped[key][:per_grade])
    return selected[:limit] if limit else selected


def capture_cases(records: list[dict[str, Any]], *, max_cases: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cases: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for record in records:
        if len(cases) >= max_cases:
            break
        expected_hints = expression_hints(str(record.get("expected_expression") or ""))
        if not expected_hints:
            continue
        payload = run_solve_pipeline(image_path=str(record["image_path"]), debug=True)
        debug = _debug_with_metadata(payload)
        candidates = collect_debug_texts(debug)
        record_added = False
        for label, noisy_text in candidates:
            for expected in expected_hints:
                key = (compact(noisy_text), compact(expected))
                if key in seen:
                    continue
                passed, normalized = normalized_contains(noisy_text, expected)
                if not passed:
                    continue
                seen.add(key)
                cases.append(
                    {
                        "case_id": f"actual_ocr_{len(cases) + 1:04d}",
                        "source": "school_math_bank_image",
                        "problem_id": str(record.get("problem_id") or ""),
                        "image_path": str(record.get("image_path") or ""),
                        "band": str(record.get("band") or ""),
                        "grade": int(record.get("grade") or 0),
                        "layout": str(record.get("layout") or ""),
                        "difficulty": str(record.get("difficulty") or ""),
                        "ocr_source": label,
                        "noisy_text": noisy_text,
                        "expected_contains": expected,
                        "normalized_preview": normalized[:240],
                    }
                )
                record_added = True
                break
            if record_added or len(cases) >= max_cases:
                break
        if not record_added:
            pending.append(
                {
                    "problem_id": str(record.get("problem_id") or ""),
                    "image_path": str(record.get("image_path") or ""),
                    "expected_expression": str(record.get("expected_expression") or ""),
                    "candidate_count": len(candidates),
                    "candidate_previews": [
                        {"ocr_source": label, "text": text[:240], "normalized": normalize_ocr_math_text(text)[:240]}
                        for label, text in candidates[:4]
                    ],
                }
            )
    return cases, pending


def build_payload(manifest_path: Path, *, per_grade: int, limit: int, max_cases: int, layout: str) -> dict[str, Any]:
    records = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected = select_records(records, per_grade=per_grade, limit=limit, layout=layout)
    started = time.time()
    cases, pending = capture_cases(selected, max_cases=max_cases)
    by_grade = Counter(f"{case['band']}{case['grade']}" for case in cases)
    by_source = Counter(str(case["ocr_source"]) for case in cases)
    return {
        "schema_version": "coco_ocr_actual_cases.v1",
        "generated_at": utc_now(),
        "source": {
            "manifest_path": str(manifest_path.relative_to(PROJECT_ROOT)) if manifest_path.is_relative_to(PROJECT_ROOT) else str(manifest_path),
            "selected_records": len(selected),
            "elapsed_seconds": round(time.time() - started, 3),
            "layout_filter": layout,
        },
        "coverage": {
            "case_count": len(cases),
            "pending_count": len(pending),
            "by_grade": dict(sorted(by_grade.items())),
            "by_ocr_source": dict(sorted(by_source.items())),
        },
        "cases": cases,
        "pending_cases": pending[:80],
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture actual OCR normalization cases from generated school math images.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--per-grade", type=int, default=4)
    parser.add_argument("--limit", type=int, default=64)
    parser.add_argument("--max-cases", type=int, default=48)
    parser.add_argument("--layout", default="expression", choices=["expression", "word", "table", ""])
    args = parser.parse_args()

    payload = build_payload(
        args.manifest,
        per_grade=max(1, args.per_grade),
        limit=max(0, args.limit),
        max_cases=max(1, args.max_cases),
        layout=args.layout,
    )
    write_json(args.output_path, payload)
    print(f"output={args.output_path}")
    print(f"case_count={payload['coverage']['case_count']}")
    print(f"pending_count={payload['coverage']['pending_count']}")
    print(f"by_grade={payload['coverage']['by_grade']}")
    print(f"by_ocr_source={payload['coverage']['by_ocr_source']}")
    return 0 if payload["cases"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
