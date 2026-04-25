from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "data" / "learning_test" / "school_math_bank_manifest.json"
REPORT_PATH = PROJECT_ROOT / "data" / "learning_test" / "school_math_bank_regression_report.json"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.pipeline import run_solve_pipeline


@dataclass(slots=True)
class BankResult:
    problem_id: str
    image_path: str
    band: str
    grade: int
    difficulty: str
    layout: str
    expected_topic: str
    topic: str
    expected_answer: str
    computed_answer: str
    expected_expression: str
    expressions: list[str]
    solver_name: str
    validation_status: str
    confidence: float
    recognized_text: str
    elapsed_seconds: float
    passed: bool
    bottlenecks: list[str]


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "")).lower()


def _normalize_answer(value: str) -> str:
    text = str(value or "").strip()
    text = text.replace("√", "sqrt")
    text = re.sub(r"\.0+$", "", text)
    return text


def _fraction_or_none(value: str) -> Fraction | None:
    text = _normalize_answer(value)
    if not re.fullmatch(r"[+-]?\d+(?:/\d+|\.\d+)?", text):
        return None
    try:
        return Fraction(text)
    except Exception:
        return None


def _answers_match(expected: str, computed: str) -> bool:
    expected_clean = _normalize_answer(expected)
    computed_clean = _normalize_answer(computed)
    if expected_clean == computed_clean:
        return True
    if any(_answers_match(expected_clean, part) for part in re.split(r"\s*,\s*", computed_clean) if part and part != computed_clean):
        return True
    expected_fraction = _fraction_or_none(expected_clean)
    computed_fraction = _fraction_or_none(computed_clean)
    if expected_fraction is not None and computed_fraction is not None and expected_fraction == computed_fraction:
        return True
    try:
        return abs(float(expected_clean) - float(computed_fraction if computed_fraction is not None else computed_clean)) <= 1e-3
    except Exception:
        return False


def _contains_expression(expressions: list[str], expected_expression: str) -> bool:
    if not expected_expression:
        return True
    hints = [part for part in re.split(r";|,", expected_expression) if part.strip()]
    compact_expressions = [_normalize_text(item) for item in expressions]
    for hint in hints:
        compact_hint = _normalize_text(hint)
        if not compact_hint:
            continue
        if any(compact_hint in expression or expression in compact_hint for expression in compact_expressions):
            return True
    return False


def _topic_close_enough(expected: str, actual: str) -> bool:
    if expected == actual:
        return True
    compatible = {
        ("fraction_ratio", "arithmetic"),
        ("statistics", "arithmetic"),
        ("geometry", "radical_power"),
        ("quadratic", "linear_equation"),
    }
    return (expected, actual) in compatible


def _diagnose(record: dict[str, Any], problem: Any, solved: Any) -> list[str]:
    bottlenecks: list[str] = []
    expressions = list(problem.expressions or [])
    computed_answer = str(getattr(solved, "computed_answer", "") or "")
    matched_choice = str(getattr(solved, "matched_choice", "") or "")
    topic = str(problem.math_topic or "")
    expected_topic = str(record.get("topic") or "")
    expected_answer = str(record.get("expected_answer") or "")
    expected_expression = str(record.get("expected_expression") or "")
    answer_ok = _answers_match(expected_answer, computed_answer) or _answers_match(expected_answer, matched_choice)
    if answer_ok and str(getattr(solved, "validation_status", "") or "") != "failed":
        return bottlenecks

    layout = str(record.get("layout") or "")
    if not _contains_expression(expressions, expected_expression):
        if layout == "word":
            bottlenecks.append("word_problem_parsing")
        elif layout == "table":
            bottlenecks.append("table_parsing")
        else:
            bottlenecks.append("expression_recognition")
    if expected_topic and not _topic_close_enough(expected_topic, topic):
        bottlenecks.append("topic_classification")
    if not answer_ok:
        bottlenecks.append("solver_or_answer")
    if str(getattr(solved, "validation_status", "") or "") == "failed":
        bottlenecks.append("validation_failed")
    return bottlenecks


def _select_records(records: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    selected = records
    if args.band:
        selected = [item for item in selected if str(item.get("band")) == args.band]
    if args.grade:
        selected = [item for item in selected if int(item.get("grade") or 0) == args.grade]
    if args.layout:
        selected = [item for item in selected if str(item.get("layout")) == args.layout]
    if args.difficulty:
        selected = [item for item in selected if str(item.get("difficulty")) == args.difficulty]

    if args.sample_per_grade:
        grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
        for item in selected:
            grouped[(str(item.get("band")), int(item.get("grade") or 0))].append(item)
        sampled: list[dict[str, Any]] = []
        for key in sorted(grouped):
            sampled.extend(grouped[key][: args.sample_per_grade])
        selected = sampled

    if args.limit:
        selected = selected[: args.limit]
    return selected


def run_record(record: dict[str, Any]) -> BankResult:
    start = time.time()
    payload = run_solve_pipeline(image_path=str(record["image_path"]), debug=True)
    elapsed = time.time() - start
    problem = payload["structured_problem"]
    solved = payload["solve_result"]
    bottlenecks = _diagnose(record, problem, solved)
    return BankResult(
        problem_id=str(record.get("problem_id") or ""),
        image_path=str(record.get("image_path") or ""),
        band=str(record.get("band") or ""),
        grade=int(record.get("grade") or 0),
        difficulty=str(record.get("difficulty") or ""),
        layout=str(record.get("layout") or ""),
        expected_topic=str(record.get("topic") or ""),
        topic=str(problem.math_topic or ""),
        expected_answer=str(record.get("expected_answer") or ""),
        computed_answer=str(getattr(solved, "computed_answer", "") or ""),
        expected_expression=str(record.get("expected_expression") or ""),
        expressions=list(problem.expressions or []),
        solver_name=str(getattr(solved, "solver_name", "") or ""),
        validation_status=str(getattr(solved, "validation_status", "") or ""),
        confidence=float(getattr(solved, "confidence", 0.0) or 0.0),
        recognized_text=str(problem.normalized_problem_text or ""),
        elapsed_seconds=round(elapsed, 4),
        passed=not bottlenecks,
        bottlenecks=bottlenecks,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CocoAi regression over the generated school math bank.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--sample-per-grade", type=int, default=0)
    parser.add_argument("--band", choices=["초등", "중등", "고등"])
    parser.add_argument("--grade", type=int)
    parser.add_argument("--layout", choices=["expression", "word", "table"])
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard"])
    parser.add_argument("--progress-every", type=int, default=25)
    args = parser.parse_args()

    records = json.loads(args.manifest.read_text(encoding="utf-8"))
    selected = _select_records(records, args)
    if not selected:
        raise SystemExit("No records selected.")

    results: list[BankResult] = []
    started = time.time()
    for index, record in enumerate(selected, start=1):
        result = run_record(record)
        results.append(result)
        if args.progress_every and (index == 1 or index % args.progress_every == 0 or index == len(selected)):
            passed = sum(1 for item in results if item.passed)
            print(f"progress {index}/{len(selected)} pass={passed} fail={len(results) - passed}", flush=True)

    elapsed = time.time() - started
    bottleneck_counts = Counter(reason for item in results for reason in item.bottlenecks)
    by_grade: dict[str, dict[str, int]] = {}
    for item in results:
        key = f"{item.band}{item.grade}"
        bucket = by_grade.setdefault(key, {"total": 0, "pass": 0, "fail": 0})
        bucket["total"] += 1
        if item.passed:
            bucket["pass"] += 1
        else:
            bucket["fail"] += 1

    report = {
        "total": len(results),
        "passed": sum(1 for item in results if item.passed),
        "failed": sum(1 for item in results if not item.passed),
        "elapsed_seconds": round(elapsed, 3),
        "bottlenecks": dict(bottleneck_counts),
        "by_grade": by_grade,
        "results": [asdict(item) for item in results],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"total={report['total']} passed={report['passed']} failed={report['failed']} elapsed={report['elapsed_seconds']}s", flush=True)
    print(f"bottlenecks={dict(bottleneck_counts)}", flush=True)
    print(f"report={args.report}", flush=True)
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
