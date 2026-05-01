from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
import unicodedata
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.multi_problem_segmenter import save_problem_card_images
from scripts.generate_curriculum_problem_bank import ProblemSpec, render_problem
from scripts.run_coco_capture_flow_validation import validate_capture
from scripts.run_problem_bank_image_validation_loop import run_single_validation


DEFAULT_WORKSPACE = PROJECT_ROOT / "data" / "problem_bank" / "elementary_50k"
DEFAULT_TEMPLATE_QUEUE = DEFAULT_WORKSPACE / "queues" / "template_render_validation_queue.jsonl"
DEFAULT_ACTUAL_QUEUE = DEFAULT_WORKSPACE / "queues" / "actual_capture_validation_queue.jsonl"
DEFAULT_RENDER_ROOT = DEFAULT_WORKSPACE / "03_template_variants" / "rendered"
DEFAULT_SEGMENT_ROOT = DEFAULT_WORKSPACE / "01_actual_pdf_capture" / "cards"
DEFAULT_REPORT = DEFAULT_WORKSPACE / "06_reports" / "elementary_50k_validation_queue_report.json"
VERIFIED_DIR = DEFAULT_WORKSPACE / "04_verified"
REJECTED_DIR = DEFAULT_WORKSPACE / "05_rejected"
PDF_EDITE_MANIFESTS = (
    PROJECT_ROOT / "data" / "problem_bank" / "sources" / "skai_pdf_edite_manifest.json",
    PROJECT_ROOT / "data" / "problem_bank" / "sources" / "toctoc_pdf_edite_manifest.json",
)
_PDF_EDITE_INDEX: dict[str, list[dict[str, Any]]] | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def project_path(value: str | Path | None, *, default: Path) -> Path:
    if not value:
        return default
    path = Path(str(value)).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def relative_to_project(path: str | Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(PROJECT_ROOT.resolve()))
    except Exception:
        return str(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                records.append(payload)
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def append_unique_jsonl(path: Path, records: list[dict[str, Any]], *, key: str) -> None:
    existing = read_jsonl(path)
    by_key = {str(item.get(key) or ""): item for item in existing if str(item.get(key) or "")}
    for record in records:
        record_key = str(record.get(key) or "")
        if record_key:
            by_key[record_key] = record
    merged = list(by_key.values())
    write_jsonl(path, merged)


def reconcile_status_jsonl(
    *,
    verified_path: Path,
    review_path: Path,
    verified_records: list[dict[str, Any]],
    review_records: list[dict[str, Any]],
    key: str,
) -> None:
    verified_by_key = {
        str(item.get(key) or ""): item
        for item in read_jsonl(verified_path)
        if str(item.get(key) or "")
    }
    review_by_key = {
        str(item.get(key) or ""): item
        for item in read_jsonl(review_path)
        if str(item.get(key) or "")
    }
    for record in verified_records:
        record_key = str(record.get(key) or "")
        if not record_key:
            continue
        verified_by_key[record_key] = record
        review_by_key.pop(record_key, None)
    for record in review_records:
        record_key = str(record.get(key) or "")
        if not record_key:
            continue
        review_by_key[record_key] = record
        verified_by_key.pop(record_key, None)
    write_jsonl(verified_path, list(verified_by_key.values()))
    write_jsonl(review_path, list(review_by_key.values()))


def selected_queue_items(
    items: list[dict[str, Any]],
    *,
    offset: int,
    limit: int,
    processed_ids: set[str],
    resume: bool,
) -> list[dict[str, Any]]:
    selected = items[max(0, offset) :]
    if resume and processed_ids:
        selected = [item for item in selected if str(item.get("collection_id") or "") not in processed_ids]
    return selected[:limit] if limit > 0 else selected


def load_processed_collection_ids(paths: list[Path]) -> set[str]:
    processed: set[str] = set()
    for path in paths:
        for item in read_jsonl(path):
            collection_id = str(item.get("collection_id") or item.get("input_collection_id") or "").strip()
            if collection_id:
                processed.add(collection_id)
    return processed


def load_template_payload(item: dict[str, Any]) -> dict[str, Any]:
    if isinstance(item.get("record"), dict):
        return dict(item["record"])
    source = project_path(item.get("collected_file_path") or item.get("source_path"), default=Path())
    payload = read_json(source)
    if isinstance(payload, dict) and isinstance(payload.get("record"), dict):
        return dict(payload["record"])
    if isinstance(payload, dict):
        return dict(payload)
    raise ValueError(f"template record is not a JSON object: {source}")


def _tuple_table(value: object) -> tuple[tuple[str, ...], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    rows: list[tuple[str, ...]] = []
    for row in value:
        if isinstance(row, (list, tuple)):
            rows.append(tuple(str(cell) for cell in row))
    return tuple(rows)


def template_problem_spec(item: dict[str, Any]) -> ProblemSpec:
    record = load_template_payload(item)
    lines = record.get("lines") or record.get("problem_text") or []
    if isinstance(lines, str):
        lines = tuple(part.strip() for part in lines.splitlines() if part.strip())
    else:
        lines = tuple(str(line) for line in lines if str(line).strip())
    grade = record.get("grade") or item.get("grade") or 1
    if isinstance(grade, str):
        match = re.search(r"[1-6]", grade)
        grade = int(match.group(0)) if match else 1
    return ProblemSpec(
        problem_id=str(record.get("problem_id") or item.get("record_id") or item.get("collection_id") or ""),
        band=str(record.get("band") or "초등"),
        grade=int(grade or 1),
        difficulty=str(record.get("difficulty") or "medium"),
        layout=str(record.get("layout") or "expression"),
        area=str(record.get("area") or "수와 연산"),
        unit=str(record.get("unit") or "초등 50k 템플릿"),
        topic=str(record.get("topic") or item.get("taxonomy", {}).get("subject_slug") or "arithmetic"),
        folder=str(record.get("folder") or f"template_render/{grade}학년"),
        file_name=str(record.get("file_name") or f"{item.get('collection_id') or 'template'}.png"),
        title=str(record.get("title") or f"초등 {grade}학년 템플릿 검증"),
        lines=lines or (str(item.get("problem_text") or ""),),
        expected_answer=str(record.get("expected_answer") or record.get("answer") or item.get("answer_text") or ""),
        expected_expression=str(record.get("expected_expression") or ""),
        table=_tuple_table(record.get("table")),
        diagram=dict(record.get("diagram") or {}),
        source_basis=str(record.get("source_basis") or "Coco elementary 50k template validation queue"),
    )


def template_validation_record(item: dict[str, Any], *, render_root: Path, force_render: bool) -> dict[str, Any]:
    spec = template_problem_spec(item)
    image_path = render_problem(spec, force=force_render, problem_root=render_root)
    record = asdict(spec)
    record["image_path"] = str(image_path)
    record["relative_path"] = relative_to_project(image_path)
    return record


def _safe_template_eval(expr: str) -> float | None:
    cleaned = str(expr or "").replace("^", "**").replace("×", "*").replace("÷", "/")
    cleaned = re.sub(r"\s+", "", cleaned)
    if not cleaned or not re.fullmatch(r"[0-9+\-*/().]+", cleaned):
        return None
    try:
        return float(eval(cleaned, {"__builtins__": {}}, {}))
    except Exception:
        return None


def _numeric_answer(value: str) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(Fraction(text))
    except Exception:
        try:
            return float(text)
        except Exception:
            return None


def source_expression_matches_expected(record: dict[str, Any]) -> bool:
    expected = _numeric_answer(str(record.get("expected_answer") or ""))
    computed = _safe_template_eval(str(record.get("expected_expression") or ""))
    if expected is None or computed is None:
        return False
    return abs(expected - computed) <= 1e-8


def validate_template_item(item: dict[str, Any], *, render_root: Path, force_render: bool) -> dict[str, Any]:
    started = time.time()
    try:
        record = template_validation_record(item, render_root=render_root, force_render=force_render)
        validation = run_single_validation(record)
        passed = str(validation.get("status") or "") == "passed"
        source_verified = False if passed else source_expression_matches_expected(record)
        verified = passed or source_verified
        return {
            **item,
            "input_collection_id": item.get("collection_id"),
            "status": "verified" if verified else "review",
            "validation_track": "template_render",
            "verification_mode": "ocr_pipeline_solver" if passed else "source_expression_solver_after_ocr_review" if source_verified else "review_required",
            "validated_at": utc_now(),
            "elapsed_seconds": round(time.time() - started, 3),
            "rendered_image_path": relative_to_project(record["image_path"]),
            "expected_answer": record.get("expected_answer"),
            "expected_expression": record.get("expected_expression"),
            "computed_answer": validation.get("computed_answer"),
            "matched_choice": validation.get("matched_choice"),
            "solver_name": validation.get("solver_name"),
            "validation_status": validation.get("validation_status"),
            "issues": [] if verified else ["template_solver_mismatch"],
            "warnings": ["ocr_pipeline_needs_followup"] if source_verified else [],
            "validation": validation,
        }
    except Exception as exc:
        return {
            **item,
            "input_collection_id": item.get("collection_id"),
            "status": "error",
            "validation_track": "template_render",
            "validated_at": utc_now(),
            "elapsed_seconds": round(time.time() - started, 3),
            "issues": ["template_render_validation_error"],
            "error": f"{type(exc).__name__}: {exc}",
        }


def grade_number(value: object) -> int:
    match = re.search(r"[1-6]", str(value or ""))
    return int(match.group(0)) if match else 0


def _path_lookup_key(path: str | Path) -> str:
    path_obj = Path(str(path))
    if not path_obj.is_absolute():
        path_obj = PROJECT_ROOT / path_obj
    try:
        path_obj = path_obj.resolve()
    except Exception:
        path_obj = path_obj.absolute()
    return unicodedata.normalize("NFC", str(path_obj))


def pdf_edite_index() -> dict[str, list[dict[str, Any]]]:
    global _PDF_EDITE_INDEX
    if _PDF_EDITE_INDEX is not None:
        return _PDF_EDITE_INDEX
    index: dict[str, list[dict[str, Any]]] = {}
    for manifest_path in PDF_EDITE_MANIFESTS:
        payload = read_json(manifest_path) if manifest_path.exists() else {}
        records = payload.get("records") if isinstance(payload, dict) else payload
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict) or not record.get("pdf_path") or not record.get("image_path"):
                continue
            key = _path_lookup_key(record["pdf_path"])
            index.setdefault(key, []).append(dict(record))
    for records in index.values():
        records.sort(key=lambda item: (int(item.get("source_page") or 0), str(item.get("image_path") or "")))
    _PDF_EDITE_INDEX = index
    return index


def card_records_from_image(
    *,
    item: dict[str, Any],
    image_source: Path,
    folder: Path,
    source_kind: str,
    parent_relative_path: str,
    case_id_prefix: str,
    metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    cards = save_problem_card_images(image_source, folder, base_name=image_source.stem, minimum_regions=2)
    base: dict[str, Any] = {
        "input_collection_id": item.get("collection_id"),
        "band": "초등",
        "grade": grade_number(item.get("grade")),
        "parent_relative_path": parent_relative_path,
    }
    if metadata:
        base.update(metadata)
    records: list[dict[str, Any]] = []
    if not cards:
        records.append(
            {
                **base,
                "case_id": f"{case_id_prefix}_capture",
                "image_path": str(image_source),
                "relative_path": relative_to_project(image_source),
                "source_kind": f"{source_kind}_unsplit",
                "expected_problem_number": 1,
            }
        )
        return records
    for card in cards:
        records.append(
            {
                **base,
                "case_id": f"{case_id_prefix}_q{card.label}",
                "image_path": str(card.path),
                "relative_path": relative_to_project(card.path),
                "source_kind": f"{source_kind}_card",
                "problem_card_index": card.index,
                "problem_card_label": card.label,
                "problem_card_bbox": list(card.bbox),
                "expected_problem_number": card.index,
            }
        )
    return records


def safe_segment_folder_name(item: dict[str, Any]) -> str:
    text = unicodedata.normalize("NFC", str(item.get("collection_id") or item.get("source_path") or "actual"))
    text = re.sub(r"[^\w가-힣.-]+", "_", text, flags=re.UNICODE).strip("._")
    return text or "actual"


def actual_capture_records(item: dict[str, Any], *, segment_root: Path, max_cards: int = 0) -> list[dict[str, Any]]:
    source = project_path(item.get("collected_file_path") or item.get("source_path"), default=Path())
    if not source.exists():
        raise FileNotFoundError(str(source))
    folder = segment_root / safe_segment_folder_name(item)
    if source.suffix.lower() == ".pdf":
        edite_records = pdf_edite_index().get(_path_lookup_key(source), [])
        if not edite_records:
            raise FileNotFoundError(f"no EDITE images found for PDF: {relative_to_project(source)}")
        records: list[dict[str, Any]] = []
        missing_edite_images: list[str] = []
        for page_record in edite_records:
            image_source = project_path(page_record.get("image_path"), default=Path())
            if not image_source.exists():
                missing_edite_images.append(relative_to_project(image_source))
                continue
            page_folder = folder / image_source.stem
            page_prefix = f"{item.get('collection_id') or source.stem}_p{int(page_record.get('source_page') or 0):02d}"
            records.extend(
                card_records_from_image(
                    item=item,
                    image_source=image_source,
                    folder=page_folder,
                    source_kind="pdf_edite_page",
                    parent_relative_path=str(page_record.get("image_path") or ""),
                    case_id_prefix=page_prefix,
                    metadata={
                        "pdf_path": page_record.get("pdf_path"),
                        "source_page": page_record.get("source_page"),
                        "pdf_page_count": page_record.get("page_count"),
                        "pdf_edite_image_path": page_record.get("image_path"),
                    },
                )
            )
        if not records:
            missing_preview = ", ".join(missing_edite_images[:5])
            raise FileNotFoundError(f"no existing EDITE images found for PDF: {relative_to_project(source)}; missing: {missing_preview}")
    else:
        records = card_records_from_image(
            item=item,
            image_source=source,
            folder=folder,
            source_kind="coco_app_capture",
            parent_relative_path=item.get("source_path") or item.get("collected_file_path"),
            case_id_prefix=str(item.get("collection_id") or source.stem),
        )
    return records[:max_cards] if max_cards > 0 else records


def validate_actual_item(item: dict[str, Any], *, segment_root: Path, max_cards: int = 0) -> list[dict[str, Any]]:
    started = time.time()
    try:
        records = actual_capture_records(item, segment_root=segment_root, max_cards=max_cards)
    except Exception as exc:
        return [
            {
                **item,
                "input_collection_id": item.get("collection_id"),
                "case_id": str(item.get("collection_id") or ""),
                "status": "error",
                "validation_track": "actual_capture",
                "validated_at": utc_now(),
                "elapsed_seconds": round(time.time() - started, 3),
                "issues": ["actual_capture_prepare_error"],
                "error": f"{type(exc).__name__}: {exc}",
            }
        ]
    results: list[dict[str, Any]] = []
    for record in records:
        validation = validate_capture(record)
        passed = str(validation.get("status") or "") == "ok"
        results.append(
            {
                **item,
                **{key: value for key, value in record.items() if key not in {"image_path"}},
                "input_collection_id": item.get("collection_id"),
                "status": "verified" if passed else str(validation.get("status") or "review"),
                "validation_track": "actual_capture",
                "validated_at": utc_now(),
                "elapsed_seconds": validation.get("elapsed_seconds"),
                "card_image_path": relative_to_project(record.get("image_path") or ""),
                "display_topic": validation.get("display_topic"),
                "problem_text": validation.get("problem_text"),
                "computed_answer": validation.get("computed_answer"),
                "matched_choice": validation.get("matched_choice"),
                "solver_name": validation.get("solver_name"),
                "validation_status": validation.get("validation_status"),
                "problem_number": validation.get("problem_number"),
                "reference_answer": validation.get("reference_answer"),
                "pdf_card_text": validation.get("pdf_card_text"),
                "issues": validation.get("issues") or [],
                "validation": validation,
            }
        )
    return results


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_status = Counter(str(item.get("status") or "unknown") for item in results)
    by_track = Counter(str(item.get("validation_track") or "unknown") for item in results)
    issue_counts: Counter[str] = Counter()
    for item in results:
        issue_counts.update(str(issue) for issue in item.get("issues") or [])
    return {
        "total": len(results),
        "verified": int(by_status.get("verified") or 0),
        "review": int(by_status.get("review") or 0),
        "error": int(by_status.get("error") or 0),
        "non_problem": int(by_status.get("non_problem") or 0),
        "by_status": dict(sorted(by_status.items())),
        "by_track": dict(sorted(by_track.items())),
        "issue_counts": dict(sorted(issue_counts.items())),
    }


def write_validation_outputs(
    results: list[dict[str, Any]],
    *,
    clean_output: bool,
    report_path: Path,
    options: dict[str, Any],
    started: float,
) -> dict[str, Any]:
    if clean_output:
        for path in (
            VERIFIED_DIR / "template_render_verified.jsonl",
            VERIFIED_DIR / "actual_capture_verified.jsonl",
            REJECTED_DIR / "template_render_review_queue.jsonl",
            REJECTED_DIR / "actual_capture_review_queue.jsonl",
        ):
            path.unlink(missing_ok=True)
    template_verified = [item for item in results if item.get("validation_track") == "template_render" and item.get("status") == "verified"]
    template_review = [item for item in results if item.get("validation_track") == "template_render" and item.get("status") != "verified"]
    actual_verified = [item for item in results if item.get("validation_track") == "actual_capture" and item.get("status") == "verified"]
    actual_review = [item for item in results if item.get("validation_track") == "actual_capture" and item.get("status") != "verified"]
    actual_review_collection_ids = {
        str(item.get("input_collection_id") or item.get("collection_id") or "")
        for item in actual_review
        if str(item.get("input_collection_id") or item.get("collection_id") or "")
    }
    actual_clean_collection_ids = {
        str(item.get("input_collection_id") or item.get("collection_id") or "")
        for item in actual_verified
        if str(item.get("input_collection_id") or item.get("collection_id") or "")
    } - actual_review_collection_ids
    if actual_clean_collection_ids:
        actual_review_path = REJECTED_DIR / "actual_capture_review_queue.jsonl"
        remaining_review_records = [
            item
            for item in read_jsonl(actual_review_path)
            if str(item.get("input_collection_id") or item.get("collection_id") or "") not in actual_clean_collection_ids
        ]
        write_jsonl(actual_review_path, remaining_review_records)
    reconcile_status_jsonl(
        verified_path=VERIFIED_DIR / "template_render_verified.jsonl",
        review_path=REJECTED_DIR / "template_render_review_queue.jsonl",
        verified_records=template_verified,
        review_records=template_review,
        key="input_collection_id",
    )
    reconcile_status_jsonl(
        verified_path=VERIFIED_DIR / "actual_capture_verified.jsonl",
        review_path=REJECTED_DIR / "actual_capture_review_queue.jsonl",
        verified_records=actual_verified,
        review_records=actual_review,
        key="case_id",
    )
    report = {
        "schema_version": "coco_elementary_50k_validation_queue_report.v1",
        "generated_at": utc_now(),
        "elapsed_seconds": round(time.time() - started, 3),
        "options": options,
        "summary": summarize(results),
        "results": results,
    }
    write_json(report_path, report)
    return report


def run_validation_queue(
    *,
    track: str,
    offset: int,
    limit: int,
    resume: bool,
    clean_output: bool,
    force_render: bool,
    max_cards_per_actual: int,
    report_path: Path,
    template_queue_path: Path = DEFAULT_TEMPLATE_QUEUE,
    actual_queue_path: Path = DEFAULT_ACTUAL_QUEUE,
    render_root: Path = DEFAULT_RENDER_ROOT,
    segment_root: Path = DEFAULT_SEGMENT_ROOT,
) -> dict[str, Any]:
    started = time.time()
    if clean_output:
        shutil.rmtree(render_root, ignore_errors=True)
        shutil.rmtree(segment_root, ignore_errors=True)
    results: list[dict[str, Any]] = []
    if track in {"template", "all"}:
        processed = load_processed_collection_ids(
            [
                VERIFIED_DIR / "template_render_verified.jsonl",
                REJECTED_DIR / "template_render_review_queue.jsonl",
            ]
        )
        selected = selected_queue_items(
            read_jsonl(template_queue_path),
            offset=offset if track == "template" else 0,
            limit=limit if track == "template" else 0,
            processed_ids=processed,
            resume=resume,
        )
        for index, item in enumerate(selected, start=1):
            result = validate_template_item(item, render_root=render_root, force_render=force_render)
            results.append(result)
            print(
                f"[template {index}/{len(selected)}] {item.get('collection_id')} "
                f"{result.get('status')} expected={result.get('expected_answer') or item.get('answer_text')} "
                f"got={result.get('matched_choice') or result.get('computed_answer')}",
                flush=True,
            )
    if track in {"actual", "all"}:
        processed = load_processed_collection_ids(
            [
                VERIFIED_DIR / "actual_capture_verified.jsonl",
                REJECTED_DIR / "actual_capture_review_queue.jsonl",
            ]
        )
        selected = selected_queue_items(
            read_jsonl(actual_queue_path),
            offset=offset if track == "actual" else 0,
            limit=limit if track == "actual" else 0,
            processed_ids=processed,
            resume=resume,
        )
        for index, item in enumerate(selected, start=1):
            item_results = validate_actual_item(item, segment_root=segment_root, max_cards=max_cards_per_actual)
            results.extend(item_results)
            item_summary = summarize(item_results)
            print(
                f"[actual {index}/{len(selected)}] {item.get('collection_id')} "
                f"cards={item_summary['total']} verified={item_summary['verified']} "
                f"review={item_summary['review']} error={item_summary['error']}",
                flush=True,
            )
    report = write_validation_outputs(
        results,
        clean_output=clean_output,
        report_path=report_path,
        options={
            "track": track,
            "offset": offset,
            "limit": limit,
            "resume": resume,
            "clean_output": clean_output,
            "force_render": force_render,
            "max_cards_per_actual": max_cards_per_actual,
            "template_queue_path": relative_to_project(template_queue_path),
            "actual_queue_path": relative_to_project(actual_queue_path),
        },
        started=started,
    )
    return report


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Promote Coco elementary 50k validation queues into verified records.")
    parser.add_argument("--track", choices=["template", "actual", "all"], default="template")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=50, help="0 means all selected queue items.")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--clean-output", action="store_true")
    parser.add_argument("--force-render", action="store_true")
    parser.add_argument("--max-cards-per-actual", type=int, default=0)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--template-queue", type=Path, default=DEFAULT_TEMPLATE_QUEUE)
    parser.add_argument("--actual-queue", type=Path, default=DEFAULT_ACTUAL_QUEUE)
    parser.add_argument("--render-root", type=Path, default=DEFAULT_RENDER_ROOT)
    parser.add_argument("--segment-root", type=Path, default=DEFAULT_SEGMENT_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    report = run_validation_queue(
        track=str(args.track),
        offset=max(0, int(args.offset)),
        limit=max(0, int(args.limit)),
        resume=not bool(args.no_resume),
        clean_output=bool(args.clean_output),
        force_render=bool(args.force_render),
        max_cards_per_actual=max(0, int(args.max_cards_per_actual)),
        report_path=project_path(args.report, default=DEFAULT_REPORT),
        template_queue_path=project_path(args.template_queue, default=DEFAULT_TEMPLATE_QUEUE),
        actual_queue_path=project_path(args.actual_queue, default=DEFAULT_ACTUAL_QUEUE),
        render_root=project_path(args.render_root, default=DEFAULT_RENDER_ROOT),
        segment_root=project_path(args.segment_root, default=DEFAULT_SEGMENT_ROOT),
    )
    print(json.dumps({"summary": report["summary"], "report": str(args.report)}, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["error"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
