from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COLLECTION_MANIFEST = (
    PROJECT_ROOT / "data" / "problem_bank" / "elementary_50k" / "00_collected" / "source_collection_manifest.json"
)
DEFAULT_WORKSPACE = PROJECT_ROOT / "data" / "problem_bank" / "elementary_50k"
DEFAULT_REPORT = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "elementary_50k_learning_report.json"
DEFAULT_PROFILE = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_elementary_50k_learning_profile.json"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
PDF_SUFFIXES = {".pdf"}
ELEMENTARY_GRADES = {f"{grade}학년" for grade in range(1, 7)}
ELEMENTARY_GRADE_BANDS = {"elementary", "elementary_middle"}
MAX_QUEUE_TEXT = 600


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def project_path(value: str | Path | None, *, default: Path) -> Path:
    if not value:
        return default
    path = Path(str(value)).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def relative_to_project(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except Exception:
        return str(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def compact_text(value: str, *, limit: int = MAX_QUEUE_TEXT) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def fingerprint_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w+\-*/=<>()[\]{}.,:% ]+", "", text, flags=re.UNICODE)
    return hashlib.sha1(text.strip().encode("utf-8")).hexdigest()


def template_fingerprint_basis(inner: dict[str, Any], problem_text: str) -> str:
    structured = {
        "problem_text": problem_text,
        "expected_expression": inner.get("expected_expression"),
        "answer": normalized_answer_text(inner),
        "table": inner.get("table") or [],
        "diagram": inner.get("diagram") or {},
        "layout": inner.get("layout"),
        "unit": inner.get("unit"),
        "topic": inner.get("topic"),
    }
    return json.dumps(structured, ensure_ascii=False, sort_keys=True)


def file_exists(path_text: str | None) -> bool:
    if not path_text:
        return False
    return project_path(path_text, default=PROJECT_ROOT).exists()


def load_collection_manifest(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"collection manifest must be an object: {path}")
    return payload


def load_materialized_payload(record: dict[str, Any]) -> dict[str, Any]:
    path_text = str(record.get("collected_file_path") or "")
    if not path_text.endswith(".json"):
        return {}
    path = project_path(path_text, default=PROJECT_ROOT)
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def inner_record(record: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    inner = payload.get("record") if isinstance(payload.get("record"), dict) else None
    if isinstance(inner, dict):
        return inner
    return record


def normalized_problem_text(inner: dict[str, Any]) -> str:
    content = inner.get("content") if isinstance(inner.get("content"), dict) else {}
    search = inner.get("search") if isinstance(inner.get("search"), dict) else {}
    for value in (
        content.get("problem_plain"),
        content.get("problem_latex"),
        search.get("problem_text"),
        inner.get("problem_text"),
    ):
        if str(value or "").strip():
            return str(value)
    lines = inner.get("lines")
    if isinstance(lines, list):
        return "\n".join(str(line or "") for line in lines if str(line or "").strip())
    if isinstance(lines, tuple):
        return "\n".join(str(line or "") for line in lines if str(line or "").strip())
    return ""


def normalized_solution_text(inner: dict[str, Any]) -> str:
    content = inner.get("content") if isinstance(inner.get("content"), dict) else {}
    learning = inner.get("learning") if isinstance(inner.get("learning"), dict) else {}
    for value in (content.get("solution_plain"), content.get("solution_latex")):
        if str(value or "").strip():
            return str(value)
    outline = learning.get("step_outline")
    if isinstance(outline, list):
        return "\n".join(str(step or "") for step in outline if str(step or "").strip())
    return ""


def normalized_answer_text(inner: dict[str, Any]) -> str:
    answer = inner.get("answer")
    if isinstance(answer, dict):
        for value in (
            answer.get("final_normalized"),
            answer.get("final_raw"),
            (answer.get("candidates") or [None])[0] if isinstance(answer.get("candidates"), list) else None,
        ):
            if str(value or "").strip():
                return str(value)
    if str(answer or "").strip():
        return str(answer)
    for key in ("expected_answer", "answer_text"):
        if str(inner.get(key) or "").strip():
            return str(inner.get(key))
    return ""


def taxonomy_for(inner: dict[str, Any]) -> dict[str, Any]:
    taxonomy = inner.get("taxonomy") if isinstance(inner.get("taxonomy"), dict) else {}
    if taxonomy:
        return taxonomy
    return {
        "grade_band": "elementary",
        "subject": str(inner.get("area") or inner.get("topic") or "Elementary Math"),
        "subject_slug": str(inner.get("topic") or "elementary_template"),
        "level_number": inner.get("grade") or 0,
        "tags": [str(inner.get("topic") or "elementary_template")],
        "concepts": [str(inner.get("unit") or inner.get("topic") or "elementary_template")],
    }


def metadata_quality(inner: dict[str, Any]) -> dict[str, Any]:
    metadata = inner.get("metadata") if isinstance(inner.get("metadata"), dict) else {}
    quality = metadata.get("quality") if isinstance(metadata.get("quality"), dict) else {}
    return quality if isinstance(quality, dict) else {}


def is_elementary_grade(value: str) -> bool:
    grade = str(value or "").strip()
    return grade in ELEMENTARY_GRADES or grade in ELEMENTARY_GRADE_BANDS


def grade_bucket(record: dict[str, Any], inner: dict[str, Any]) -> str:
    grade = str(record.get("grade") or "").strip()
    if grade:
        return grade
    raw_grade = inner.get("grade") or inner.get("grade_number")
    if isinstance(raw_grade, int) and 1 <= raw_grade <= 6:
        return f"{raw_grade}학년"
    if isinstance(raw_grade, str):
        match = re.search(r"[1-6]", raw_grade)
        if match:
            return f"{match.group(0)}학년"
    taxonomy = taxonomy_for(inner)
    return str(taxonomy.get("grade_band") or "unknown")


def queue_item(
    record: dict[str, Any],
    inner: dict[str, Any],
    *,
    status: str,
    reasons: list[str],
    fingerprint: str,
    problem_text: str = "",
    answer_text: str = "",
    solution_text: str = "",
) -> dict[str, Any]:
    taxonomy = taxonomy_for(inner)
    return {
        "collection_id": record.get("collection_id"),
        "track": record.get("track"),
        "source_type": record.get("source_type"),
        "status": status,
        "reasons": reasons,
        "grade": grade_bucket(record, inner),
        "bank_id": record.get("bank_id"),
        "record_id": record.get("record_id") or inner.get("id") or inner.get("card_id") or inner.get("problem_id"),
        "collected_file_path": record.get("collected_file_path"),
        "source_path": record.get("path"),
        "sha256": record.get("sha256"),
        "fingerprint": fingerprint,
        "problem_text": compact_text(problem_text),
        "answer_text": compact_text(answer_text, limit=160),
        "solution_text": compact_text(solution_text),
        "taxonomy": {
            "grade_band": taxonomy.get("grade_band"),
            "subject": taxonomy.get("subject"),
            "subject_slug": taxonomy.get("subject_slug"),
            "level_number": taxonomy.get("level_number"),
            "tags": taxonomy.get("tags") or [],
            "concepts": taxonomy.get("concepts") or [],
        },
    }


def evaluate_candidate(record: dict[str, Any], seen: set[str]) -> dict[str, Any]:
    payload = load_materialized_payload(record)
    inner = inner_record(record, payload)
    track = str(record.get("track") or "")
    source_type = str(record.get("source_type") or "")
    problem_text = normalized_problem_text(inner)
    answer_text = normalized_answer_text(inner)
    solution_text = normalized_solution_text(inner)
    reasons: list[str] = []

    if track == "actual_pdf_capture":
        source_path = str(record.get("collected_file_path") or record.get("path") or "")
        suffix = str(record.get("suffix") or Path(source_path).suffix).lower()
        if suffix not in IMAGE_SUFFIXES | PDF_SUFFIXES:
            reasons.append("unsupported_actual_source_suffix")
        if not file_exists(source_path):
            reasons.append("actual_source_missing")
        fingerprint = str(record.get("sha256") or "") or fingerprint_text(source_path)
        if fingerprint in seen:
            return queue_item(
                record,
                inner,
                status="rejected_duplicate",
                reasons=["duplicate_actual_source"],
                fingerprint=fingerprint,
                problem_text=problem_text,
            )
        seen.add(fingerprint)
        status = "validation_queued" if not reasons else "review_queued"
        queue_reason = f"{source_type}_requires_coco_capture_validation"
        return queue_item(
            record,
            inner,
            status=status,
            reasons=[queue_reason, *reasons],
            fingerprint=fingerprint,
            problem_text=problem_text,
        )

    if track == "template_variant":
        fingerprint = fingerprint_text(template_fingerprint_basis(inner, problem_text))
    else:
        fingerprint = fingerprint_text(problem_text or str(record.get("record_id") or record.get("collection_id") or ""))
    if fingerprint in seen:
        return queue_item(
            record,
            inner,
            status="rejected_duplicate",
            reasons=["duplicate_problem_text"],
            fingerprint=fingerprint,
            problem_text=problem_text,
            answer_text=answer_text,
            solution_text=solution_text,
        )
    seen.add(fingerprint)

    if not problem_text:
        reasons.append("problem_text_missing")
    if not answer_text:
        reasons.append("answer_missing")

    if track == "normalized_json":
        taxonomy = taxonomy_for(inner)
        grade_band = str(taxonomy.get("grade_band") or record.get("grade") or "")
        if grade_band not in ELEMENTARY_GRADE_BANDS:
            reasons.append("non_elementary_grade_band")
        quality = metadata_quality(inner)
        if bool(quality.get("needs_review")):
            reasons.append("source_quality_needs_review")
        if not solution_text:
            reasons.append("solution_missing")
        status = "learned_ready" if not reasons else "review_queued"
    elif track == "template_variant":
        if not is_elementary_grade(grade_bucket(record, inner)):
            reasons.append("template_grade_not_elementary")
        validation = inner.get("validation") if isinstance(inner.get("validation"), dict) else {}
        status = "validation_queued" if not reasons else "review_queued"
        if status == "validation_queued":
            reasons.append("template_requires_render_and_solver_validation")
        if validation.get("verified") is True and not reasons:
            status = "learned_ready"
    else:
        status = "review_queued"
        reasons.append("unknown_track")

    return queue_item(
        record,
        inner,
        status=status,
        reasons=reasons,
        fingerprint=fingerprint,
        problem_text=problem_text,
        answer_text=answer_text,
        solution_text=solution_text,
    )


def rate(part: int | float, total: int | float) -> float:
    if not total:
        return 0.0
    return round(float(part) / float(total), 6)


def top(counter: Counter[str], limit: int = 30) -> dict[str, int]:
    return {key: count for key, count in counter.most_common(limit)}


def build_profile(evaluated: list[dict[str, Any]], *, manifest_path: Path, report_path: Path) -> dict[str, Any]:
    ready_or_queued = [
        item
        for item in evaluated
        if item.get("status") in {"learned_ready", "validation_queued"}
    ]
    status_counts = Counter(str(item.get("status") or "unknown") for item in evaluated)
    track_counts = Counter(str(item.get("track") or "unknown") for item in ready_or_queued)
    grade_counts = Counter(str(item.get("grade") or "unknown") for item in ready_or_queued)
    bank_counts = Counter(str(item.get("bank_id") or "local_or_template") for item in ready_or_queued)
    domain_counts: Counter[str] = Counter()
    tag_counts: Counter[str] = Counter()
    concept_counts: Counter[str] = Counter()
    answer_type_counts: Counter[str] = Counter()
    levels: dict[str, Counter[str]] = defaultdict(Counter)

    for item in ready_or_queued:
        taxonomy = item.get("taxonomy") if isinstance(item.get("taxonomy"), dict) else {}
        slug = str(taxonomy.get("subject_slug") or taxonomy.get("subject") or item.get("source_type") or "unknown")
        domain_counts.update([slug])
        for tag in taxonomy.get("tags") or []:
            if str(tag or "").strip():
                tag_counts.update([str(tag)])
        for concept in taxonomy.get("concepts") or []:
            if str(concept or "").strip():
                concept_counts.update([str(concept)])
        level = str(taxonomy.get("level_number") or item.get("grade") or "unknown")
        levels[slug].update([level])
        answer = str(item.get("answer_text") or "")
        if re.fullmatch(r"[+-]?\d+", answer.replace(",", "")):
            answer_type_counts.update(["integer"])
        elif answer:
            answer_type_counts.update(["text_or_numeric"])
        else:
            answer_type_counts.update(["unknown"])

    domains: dict[str, Any] = {}
    for slug, count in sorted(domain_counts.items()):
        domains[slug] = {
            "count": count,
            "levels": dict(sorted(levels[slug].items())),
        }

    return {
        "schema_version": "coco_elementary_50k_learning_profile.v1",
        "generated_at": utc_now(),
        "source": {
            "collection_manifest": relative_to_project(manifest_path),
            "learning_report": relative_to_project(report_path),
            "policy": "elementary_only_static_learning_with_capture_and_template_validation_queues",
        },
        "counts": {
            "total_records": len(evaluated),
            "learning_ready_or_queued": len(ready_or_queued),
            "by_status": dict(sorted(status_counts.items())),
            "by_track": dict(sorted(track_counts.items())),
            "by_grade": dict(sorted(grade_counts.items())),
            "by_bank": dict(sorted(bank_counts.items())),
            "by_domain": dict(sorted(domain_counts.items())),
            "answer_type_counts": dict(sorted(answer_type_counts.items())),
        },
        "domains": domains,
        "top_tags": top(tag_counts, 60),
        "top_concepts": top(concept_counts, 60),
        "routing": {
            "school_level": "초등",
            "engine_partition": "elementary",
            "actual_capture_policy": "validation_queued_until_coco_app_capture_passes",
            "template_policy": "validation_queued_until_render_and_solver_pass",
            "normalized_json_policy": "learned_ready_after_static_answer_solution_grade_filter",
        },
    }


def build_report(
    evaluated: list[dict[str, Any]],
    *,
    manifest: dict[str, Any],
    manifest_path: Path,
    workspace: Path,
    profile_path: Path,
) -> dict[str, Any]:
    target = int(manifest.get("target") or manifest.get("summary", {}).get("total_files_prepared") or len(evaluated))
    status_counts = Counter(str(item.get("status") or "unknown") for item in evaluated)
    track_counts = Counter(str(item.get("track") or "unknown") for item in evaluated)
    source_type_counts = Counter(str(item.get("source_type") or "unknown") for item in evaluated)
    grade_counts = Counter(str(item.get("grade") or "unknown") for item in evaluated)
    bank_counts = Counter(str(item.get("bank_id") or "local_or_template") for item in evaluated)
    reason_counts: Counter[str] = Counter()
    non_elementary_count = 0
    answer_ready = 0
    normalized_total = 0
    normalized_answer_ready = 0

    for item in evaluated:
        reason_counts.update(str(reason) for reason in item.get("reasons") or [])
        if item.get("track") == "normalized_json":
            normalized_total += 1
            if item.get("answer_text"):
                normalized_answer_ready += 1
        if item.get("answer_text"):
            answer_ready += 1
        grade = str(item.get("grade") or "")
        taxonomy = item.get("taxonomy") if isinstance(item.get("taxonomy"), dict) else {}
        grade_band = str(taxonomy.get("grade_band") or grade)
        if item.get("track") == "normalized_json" and grade_band not in ELEMENTARY_GRADE_BANDS:
            non_elementary_count += 1

    duplicate_count = int(status_counts.get("rejected_duplicate", 0))
    duplicate_ratio = rate(duplicate_count, len(evaluated))
    ready_or_queued_count = int(status_counts.get("learned_ready", 0)) + int(status_counts.get("validation_queued", 0))
    quality_gates = {
        "target_loaded": len(evaluated) >= target,
        "no_non_elementary_external_records": non_elementary_count == 0,
        "duplicate_ratio": duplicate_ratio,
        "max_duplicate_ratio": 0.03,
        "duplicate_gate_passed": duplicate_ratio <= 0.03,
        "normalized_json_answer_coverage": rate(normalized_answer_ready, normalized_total),
        "normalized_json_answer_gate_passed": normalized_total == 0 or normalized_answer_ready == normalized_total,
        "static_learning_ingestion_complete": ready_or_queued_count + int(status_counts.get("review_queued", 0)) + duplicate_count == len(evaluated),
    }
    success = (
        quality_gates["target_loaded"]
        and quality_gates["no_non_elementary_external_records"]
        and quality_gates["duplicate_gate_passed"]
        and quality_gates["normalized_json_answer_gate_passed"]
    )
    return {
        "schema_version": "coco_elementary_50k_learning_report.v1",
        "generated_at": utc_now(),
        "success": success,
        "readiness": "static_learning_complete_validation_queues_ready" if success else "learning_needs_review",
        "source_manifest": relative_to_project(manifest_path),
        "profile_path": relative_to_project(profile_path),
        "workspace": relative_to_project(workspace),
        "summary": {
            "target": target,
            "total_records": len(evaluated),
            "learned_ready": int(status_counts.get("learned_ready", 0)),
            "validation_queued": int(status_counts.get("validation_queued", 0)),
            "review_queued": int(status_counts.get("review_queued", 0)),
            "rejected_duplicate": duplicate_count,
            "answer_ready": answer_ready,
            "ready_or_queued_total": ready_or_queued_count,
        },
        "counts": {
            "by_status": dict(sorted(status_counts.items())),
            "by_track": dict(sorted(track_counts.items())),
            "by_source_type": dict(sorted(source_type_counts.items())),
            "by_grade": dict(sorted(grade_counts.items())),
            "by_bank": dict(sorted(bank_counts.items())),
            "top_reasons": top(reason_counts, 40),
        },
        "quality_gates": quality_gates,
        "queues": {
            "learned_ready": relative_to_project(workspace / "queues" / "learned_ready.jsonl"),
            "actual_capture_validation": relative_to_project(workspace / "queues" / "actual_capture_validation_queue.jsonl"),
            "template_render_validation": relative_to_project(workspace / "queues" / "template_render_validation_queue.jsonl"),
            "review": relative_to_project(workspace / "queues" / "review_queue.jsonl"),
            "rejected": relative_to_project(workspace / "queues" / "rejected_queue.jsonl"),
        },
        "next_routine": [
            "Run actual_capture_validation_queue through the Coco app capture flow in small batches.",
            "Render and solver-check template_render_validation_queue before promotion.",
            "Use learned_ready normalized JSON immediately for elementary routing, answer normalization, search, and similar-problem generation.",
        ],
    }


def write_learning_artifacts(
    evaluated: list[dict[str, Any]],
    *,
    workspace: Path,
    report: dict[str, Any],
    profile: dict[str, Any],
    report_path: Path,
    profile_path: Path,
    clean: bool = False,
) -> None:
    queues = workspace / "queues"
    verified = workspace / "04_verified"
    rejected = workspace / "05_rejected"
    reports = workspace / "06_reports"
    if clean:
        for path in (queues, verified, rejected, reports):
            shutil.rmtree(path, ignore_errors=True)
    queues.mkdir(parents=True, exist_ok=True)
    verified.mkdir(parents=True, exist_ok=True)
    rejected.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    learned_ready = [item for item in evaluated if item.get("status") == "learned_ready"]
    actual_queue = [
        item
        for item in evaluated
        if item.get("status") == "validation_queued" and item.get("track") == "actual_pdf_capture"
    ]
    template_queue = [
        item
        for item in evaluated
        if item.get("status") == "validation_queued" and item.get("track") == "template_variant"
    ]
    review_queue = [item for item in evaluated if item.get("status") == "review_queued"]
    rejected_queue = [item for item in evaluated if str(item.get("status") or "").startswith("rejected")]

    write_jsonl(queues / "learned_ready.jsonl", learned_ready)
    write_jsonl(queues / "actual_capture_validation_queue.jsonl", actual_queue)
    write_jsonl(queues / "template_render_validation_queue.jsonl", template_queue)
    write_jsonl(queues / "review_queue.jsonl", review_queue)
    write_jsonl(queues / "rejected_queue.jsonl", rejected_queue)
    write_jsonl(verified / "normalized_json_learning_ready.jsonl", learned_ready)
    write_jsonl(rejected / "rejected_records.jsonl", rejected_queue)
    write_json(reports / "elementary_50k_learning_report.json", report)
    write_json(reports / "coco_elementary_50k_learning_profile.json", profile)
    write_json(report_path, report)
    write_json(profile_path, profile)


def run_learning_cycle(
    *,
    manifest_path: Path = DEFAULT_COLLECTION_MANIFEST,
    workspace: Path = DEFAULT_WORKSPACE,
    report_path: Path = DEFAULT_REPORT,
    profile_path: Path = DEFAULT_PROFILE,
    clean: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = load_collection_manifest(manifest_path)
    raw_records = manifest.get("records")
    if not isinstance(raw_records, list):
        raise ValueError(f"manifest has no records list: {manifest_path}")
    seen: set[str] = set()
    evaluated = [evaluate_candidate(record, seen) for record in raw_records if isinstance(record, dict)]
    report = build_report(
        evaluated,
        manifest=manifest,
        manifest_path=manifest_path,
        workspace=workspace,
        profile_path=profile_path,
    )
    profile = build_profile(evaluated, manifest_path=manifest_path, report_path=report_path)
    write_learning_artifacts(
        evaluated,
        workspace=workspace,
        report=report,
        profile=profile,
        report_path=report_path,
        profile_path=profile_path,
        clean=clean,
    )
    return report, profile


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Coco elementary 50k static learning and validation queue cycle.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_COLLECTION_MANIFEST)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--clean", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    manifest_path = project_path(args.manifest, default=DEFAULT_COLLECTION_MANIFEST)
    workspace = project_path(args.workspace, default=DEFAULT_WORKSPACE)
    report_path = project_path(args.report, default=DEFAULT_REPORT)
    profile_path = project_path(args.profile, default=DEFAULT_PROFILE)
    report, profile = run_learning_cycle(
        manifest_path=manifest_path,
        workspace=workspace,
        report_path=report_path,
        profile_path=profile_path,
        clean=bool(args.clean),
    )
    print(
        json.dumps(
            {
                "readiness": report["readiness"],
                "success": report["success"],
                "summary": report["summary"],
                "quality_gates": report["quality_gates"],
                "profile_total_records": profile["counts"]["total_records"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report.get("success") else 2


if __name__ == "__main__":
    raise SystemExit(main())
