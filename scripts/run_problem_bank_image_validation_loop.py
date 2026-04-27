from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.chat.state import DOCS_DIR, STATE_PATH, ensure_dirs, load_state, persist_document, save_state
from app.core.pipeline import run_solve_pipeline
from scripts.generate_curriculum_problem_bank import BANDS, ProblemSpec, generate_specs, render_problem


DEFAULT_BANK_ROOT = PROJECT_ROOT / "02.학습문제" / "05.문제은행"
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_problem_bank_image_validation_manifest.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_problem_bank_image_validation_report.json"
APP_DOC_PREFIX = "autobank__"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return dict(value or {}) if isinstance(value, dict) else {}


def _normalize_number_token(token: str) -> str:
    try:
        number = Fraction(token)
        if number.denominator == 1:
            return str(number.numerator)
        return f"{number.numerator}/{number.denominator}"
    except Exception:
        try:
            number_float = float(token)
        except Exception:
            return token.strip()
        rounded = round(number_float)
        if math.isclose(number_float, rounded, rel_tol=0, abs_tol=1e-9):
            return str(int(rounded))
        return f"{number_float:.8g}"


def normalize_answer_values(value: str) -> list[str]:
    text = str(value or "")
    text = re.sub(r"[①②③④⑤⑥⑦⑧⑨⑩]", " ", text)
    text = text.replace(",", "").replace("원", "").replace("개", "").replace("쪽", "").replace("km", "")
    text = re.sub(r"[^0-9+\-./]", " ", text)
    values: list[str] = []
    for match in re.finditer(r"[-+]?\d+(?:/\d+)?(?:\.\d+)?", text):
        normalized = _normalize_number_token(match.group(0))
        if normalized and normalized not in values:
            values.append(normalized)
    return values


def normalize_answer(value: str) -> str:
    values = normalize_answer_values(value)
    return values[0] if values else ""


def answers_match(expected: str, actual: str, matched_choice: str = "") -> bool:
    expected_values = normalize_answer_values(expected)
    actual_values = normalize_answer_values(actual) + normalize_answer_values(matched_choice)
    if not expected_values:
        return False
    if set(expected_values).issubset(set(actual_values)):
        return True
    if len(expected_values) == 1 and expected_values[0] in actual_values:
        return True
    for candidate in actual_values:
        if not candidate:
            continue
        try:
            if len(expected_values) == 1 and Fraction(expected_values[0]) == Fraction(candidate):
                return True
        except Exception:
            pass
    return False


def _relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _record_from_spec(spec: ProblemSpec, image_path: Path) -> dict[str, Any]:
    record = asdict(spec)
    record["image_path"] = str(image_path)
    record["relative_path"] = _relative_path(image_path)
    return record


def generate_problem_bank_images(
    *,
    output_root: Path = DEFAULT_BANK_ROOT,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    count_per_grade: int = 100,
    seed: int = 20260425,
    force: bool = False,
    clean: bool = False,
) -> list[dict[str, Any]]:
    if count_per_grade <= 0:
        raise ValueError("count_per_grade must be positive")
    if clean and output_root.exists():
        for folder_name, _, _ in BANDS:
            target = output_root / folder_name
            if target.exists():
                import shutil

                shutil.rmtree(target)

    specs = generate_specs(count_per_grade, seed)
    records: list[dict[str, Any]] = []
    for spec in specs:
        image_path = render_problem(spec, force=force, problem_root=output_root)
        records.append(_record_from_spec(spec, image_path))

    payload = {
        "schema_version": "coco_problem_bank_image_validation_manifest.v1",
        "generated_at": utc_now(),
        "output_root": str(output_root),
        "count_per_grade": count_per_grade,
        "seed": seed,
        "total": len(records),
        "records": records,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return records


def load_manifest_records(manifest_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, dict)]
    return [dict(item) for item in payload.get("records") or [] if isinstance(item, dict)]


def selected_records(records: list[dict[str, Any]], *, offset: int, limit: int, band: str, grade: int, difficulty: str) -> list[dict[str, Any]]:
    filtered = records
    if band:
        filtered = [item for item in filtered if str(item.get("band") or "") == band]
    if grade:
        filtered = [item for item in filtered if int(item.get("grade") or 0) == grade]
    if difficulty:
        filtered = [item for item in filtered if str(item.get("difficulty") or "") == difficulty]
    if offset > 0:
        filtered = filtered[offset:]
    return filtered[:limit] if limit > 0 else filtered


def run_single_validation(record: dict[str, Any], *, debug: bool = True) -> dict[str, Any]:
    image_path = str(record.get("image_path") or "")
    started = time.time()
    try:
        payload = run_solve_pipeline(image_path=image_path, debug=debug)
        problem = model_dump(payload.get("structured_problem"))
        solved = model_dump(payload.get("solve_result"))
        expected = str(record.get("expected_answer") or "")
        actual = str(solved.get("computed_answer") or "")
        matched_choice = str(solved.get("matched_choice") or "")
        passed = answers_match(expected, actual, matched_choice)
        status = "passed" if passed else "failed"
        error = ""
    except Exception as exc:
        payload = {}
        problem = {}
        solved = {}
        expected = str(record.get("expected_answer") or "")
        actual = ""
        matched_choice = ""
        status = "error"
        error = str(exc)

    return {
        "case_id": str(record.get("problem_id") or ""),
        "band": str(record.get("band") or ""),
        "grade": int(record.get("grade") or 0),
        "difficulty": str(record.get("difficulty") or ""),
        "layout": str(record.get("layout") or ""),
        "topic": str(record.get("topic") or ""),
        "image_path": image_path,
        "expected_answer": expected,
        "expected_expression": str(record.get("expected_expression") or ""),
        "computed_answer": actual,
        "matched_choice": matched_choice,
        "validation_status": str(solved.get("validation_status") or ""),
        "solver_name": str(solved.get("solver_name") or ""),
        "recognized_problem": str(problem.get("normalized_problem_text") or ""),
        "recognized_expressions": [str(item or "") for item in problem.get("expressions") or []],
        "status": status,
        "error": error,
        "elapsed_seconds": round(time.time() - started, 3),
        "analysis": {
            "analysis_started_at": started,
            "analysis_finished_at": time.time(),
            "structured_problem": problem,
            "solve_result": solved,
            "debug": payload.get("debug") if isinstance(payload, dict) else {},
        },
    }


def _app_doc_id(record: dict[str, Any], cycle_index: int) -> str:
    problem_id = str(record.get("problem_id") or Path(str(record.get("image_path") or "")).stem)
    digest = hashlib.sha1(f"{problem_id}:{record.get('image_path')}:{cycle_index}".encode("utf-8")).hexdigest()[:8]
    return f"{APP_DOC_PREFIX}{problem_id}__{digest}"


def _slim_problem_bank_record(record: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "problem_id",
        "band",
        "grade",
        "difficulty",
        "layout",
        "area",
        "unit",
        "topic",
        "file_name",
        "relative_path",
        "expected_answer",
        "expected_expression",
    )
    payload = {key: record.get(key) for key in keys if record.get(key) not in (None, "", [])}
    if record.get("lines"):
        payload["line_count"] = len(record.get("lines") or [])
    return payload


def _analysis_with_problem_bank_context(analysis: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(analysis or {})
    structured = dict(enriched.get("structured_problem") or {})
    metadata = dict(structured.get("metadata") or {})
    metadata["problem_bank_topic"] = str(record.get("topic") or "")
    metadata["problem_bank_record"] = _slim_problem_bank_record(record)
    structured["metadata"] = metadata
    enriched["structured_problem"] = structured
    enriched["problem_bank_record"] = metadata["problem_bank_record"]
    return enriched


def clear_generated_app_docs() -> dict[str, Any]:
    ensure_dirs()
    state = load_state()
    removed_doc_ids = {
        str(item.get("doc_id") or "")
        for item in state.get("documents", [])
        if str(item.get("doc_id") or "").startswith(APP_DOC_PREFIX)
    }
    for doc_path in DOCS_DIR.glob(f"{APP_DOC_PREFIX}*.json"):
        removed_doc_ids.add(doc_path.stem)
        doc_path.unlink(missing_ok=True)

    if removed_doc_ids:
        state["documents"] = [
            item for item in state.get("documents", []) if str(item.get("doc_id") or "") not in removed_doc_ids
        ]
        state["chat_history"] = [
            item for item in state.get("chat_history", []) if str(item.get("doc_id") or "") not in removed_doc_ids
        ]
        if str(state.get("selected_doc_id") or "") in removed_doc_ids:
            state["selected_doc_id"] = None
        if str(state.get("last_active_doc_id") or "") in removed_doc_ids:
            state["last_active_doc_id"] = None
        save_state(state)

    return {"removed_count": len(removed_doc_ids), "removed_doc_ids": sorted(removed_doc_ids)}


def register_app_document(record: dict[str, Any], validation: dict[str, Any], *, cycle_index: int) -> str:
    ensure_dirs()
    state = load_state()
    doc_id = _app_doc_id(record, cycle_index)
    registered_at = time.time()
    file_name = Path(str(record.get("image_path") or record.get("file_name") or doc_id)).name
    analysis = _analysis_with_problem_bank_context(validation.get("analysis") or {}, record)
    persist_document(
        doc_id,
        file_name,
        str(record.get("image_path") or ""),
        analysis,
        latest_user_query="",
        registered_at=registered_at,
    )
    docs = [item for item in state.get("documents", []) if str(item.get("doc_id") or "") != doc_id]
    docs.insert(
        0,
        {
            "doc_id": doc_id,
            "file_name": file_name,
            "file_path": str(record.get("image_path") or ""),
            "created_at": registered_at,
            "registered_at": registered_at,
            "last_opened_at": registered_at,
            "latest_user_query": "",
        },
    )
    state["documents"] = docs
    state["chat_mode"] = "study"
    state["last_active_chat_mode"] = "study"
    state["selected_doc_id"] = doc_id
    state["last_active_doc_id"] = doc_id
    state["last_active_at"] = registered_at
    save_state(state)
    return doc_id


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "total": len(results),
        "passed": sum(1 for item in results if item.get("status") == "passed"),
        "failed": sum(1 for item in results if item.get("status") == "failed"),
        "error": sum(1 for item in results if item.get("status") == "error"),
        "by_band": {},
        "by_topic": {},
    }
    for key in ("by_band", "by_topic"):
        field = "band" if key == "by_band" else "topic"
        buckets: dict[str, dict[str, int]] = {}
        for item in results:
            bucket = buckets.setdefault(str(item.get(field) or "unknown"), {"total": 0, "passed": 0, "failed": 0, "error": 0})
            status = str(item.get("status") or "error")
            bucket["total"] += 1
            bucket[status if status in {"passed", "failed", "error"} else "error"] += 1
        summary[key] = dict(sorted(buckets.items()))
    return summary


def run_validation_cycle(
    records: list[dict[str, Any]],
    *,
    cycle_index: int,
    app_register: bool,
    clear_app_between_items: bool,
    stop_on_failure: bool,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        if clear_app_between_items:
            clear_generated_app_docs()
        validation = run_single_validation(record)
        if app_register:
            validation["app_doc_id"] = register_app_document(record, validation, cycle_index=cycle_index)
        results.append(validation)
        print(
            f"[cycle {cycle_index} #{index}/{len(records)}] "
            f"{validation['case_id']} {validation['status']} "
            f"expected={validation['expected_answer']} got={validation['matched_choice'] or validation['computed_answer']}"
        )
        if stop_on_failure and validation["status"] != "passed":
            break
    return results


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and repeatedly validate Coco problem-bank images.")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_BANK_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--count-per-grade", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260425)
    parser.add_argument("--generate", action="store_true", help="Render the 05.문제은행 image bank before validation.")
    parser.add_argument("--force", action="store_true", help="Overwrite rendered images.")
    parser.add_argument("--clean-generated-images", action="store_true", help="Remove generated 05.문제은행 images before rendering.")
    parser.add_argument("--band", choices=["", "초등", "중등", "고등"], default="")
    parser.add_argument("--grade", type=int, default=0)
    parser.add_argument("--difficulty", choices=["", "easy", "medium", "hard"], default="")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0, help="0 means all selected records.")
    parser.add_argument("--max-cycles", type=int, default=1, help="0 means infinite when --loop is enabled.")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--app-register", action="store_true", help="Write each validation case into Coco's study list.")
    parser.add_argument("--clear-app-generated", action="store_true", help="Clear only autobank study-list docs before starting.")
    parser.add_argument("--clear-app-between-items", action="store_true", help="Clear only autobank docs before each item.")
    parser.add_argument("--stop-on-failure", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.clear_app_generated or args.clear_app_between_items:
        cleared = clear_generated_app_docs()
        print(f"cleared_generated_app_docs={cleared['removed_count']}")

    if args.generate or not args.manifest.exists():
        records = generate_problem_bank_images(
            output_root=args.output_root,
            manifest_path=args.manifest,
            count_per_grade=max(1, int(args.count_per_grade)),
            seed=int(args.seed),
            force=bool(args.force),
            clean=bool(args.clean_generated_images),
        )
    else:
        records = load_manifest_records(args.manifest)

    selected = selected_records(
        records,
        offset=max(0, int(args.offset)),
        limit=max(0, int(args.limit)),
        band=str(args.band or ""),
        grade=max(0, int(args.grade)),
        difficulty=str(args.difficulty or ""),
    )
    if not selected:
        raise SystemExit("No records selected for validation.")

    started = time.time()
    all_results: list[dict[str, Any]] = []
    cycle_index = 0
    while True:
        cycle_index += 1
        all_results.extend(
            run_validation_cycle(
                selected,
                cycle_index=cycle_index,
                app_register=bool(args.app_register),
                clear_app_between_items=bool(args.clear_app_between_items),
                stop_on_failure=bool(args.stop_on_failure),
            )
        )
        failed = any(item.get("status") != "passed" for item in all_results[-len(selected) :])
        if args.stop_on_failure and failed:
            break
        if not args.loop:
            break
        if args.max_cycles > 0 and cycle_index >= args.max_cycles:
            break
        time.sleep(max(0.0, float(args.sleep_seconds)))

    report = {
        "schema_version": "coco_problem_bank_image_validation_report.v1",
        "generated_at": utc_now(),
        "elapsed_seconds": round(time.time() - started, 3),
        "project_root": str(PROJECT_ROOT),
        "manifest": str(args.manifest),
        "output_root": str(args.output_root),
        "options": {
            key: str(value) if isinstance(value, Path) else value
            for key, value in sorted(vars(args).items())
        },
        "selected_count": len(selected),
        "cycle_count": cycle_index,
        "summary": summarize_results(all_results),
        "failures": [item for item in all_results if item.get("status") != "passed"][:200],
        "results": all_results,
    }
    write_report(args.report, report)
    print(f"report={args.report}")
    print(f"summary={report['summary']}")
    return 0 if report["summary"]["failed"] == 0 and report["summary"]["error"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
