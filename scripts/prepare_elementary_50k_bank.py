from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_curriculum_problem_bank import make_problem


DEFAULT_CONFIG = PROJECT_ROOT / "data" / "problem_bank" / "beta" / "elementary_50k_config.json"
DEFAULT_REPORT = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "elementary_50k_readiness_report.json"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}
PDF_SUFFIXES = {".pdf"}
VERIFIED_STATUSES = {"verified", "verified_baseline"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def project_path(value: str | Path | None, *, default: Path | None = None) -> Path:
    if not value:
        if default is None:
            raise ValueError("path value is required")
        return default
    path = Path(str(value)).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def relative_to_project(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except Exception:
        return str(path)


def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def rate(part: int | float, total: int | float) -> float:
    if not total:
        return 0.0
    return round(float(part) / float(total), 6)


def grade_from_path(path: Path) -> str:
    for part in path.parts:
        match = re.search(r"([1-6])\s*학년", part)
        if match:
            return f"{match.group(1)}학년"
    match = re.search(r"초\s*([1-6])", path.name)
    if match:
        return f"{match.group(1)}학년"
    return "unknown"


def collect_files(root: Path, suffixes: set[str], *, required_part: str | None = None) -> list[Path]:
    if not root.exists():
        return []
    required = str(required_part or "").upper()
    paths: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        if required and required not in {part.upper() for part in path.parts}:
            continue
        paths.append(path)
    return sorted(paths)


def count_by_grade(paths: list[Path]) -> dict[str, int]:
    counts = Counter(grade_from_path(path) for path in paths)
    return dict(sorted(counts.items()))


def normalize_validation_summary(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    source = payload.get("summary") if isinstance(payload, dict) and isinstance(payload.get("summary"), dict) else payload
    if not isinstance(source, dict):
        source = {}
    total = int(source.get("total") or source.get("processed_total") or 0)
    ok = int(source.get("ok") or source.get("passed") or 0)
    review = int(source.get("review") or 0)
    error = int(source.get("error") or 0)
    non_problem = int(source.get("non_problem") or 0)
    return {
        "report": relative_to_project(path),
        "total": total,
        "ok": ok,
        "review": review,
        "error": error,
        "non_problem": non_problem,
        "ok_rate": rate(ok, total),
    }


def summarize_source(source: dict[str, Any]) -> dict[str, Any]:
    root = project_path(source.get("root"), default=PROJECT_ROOT)
    pdfs = collect_files(root, PDF_SUFFIXES, required_part="PDF")
    edite_images = collect_files(root, IMAGE_SUFFIXES, required_part="EDITE")
    summary_report = project_path(source.get("summary_report"), default=PROJECT_ROOT / "__missing__.json")
    validation = normalize_validation_summary(summary_report) if source.get("summary_report") else {}
    status = str(source.get("status") or "")
    verified_cards = int(validation.get("ok") or 0) if status in VERIFIED_STATUSES else 0
    estimated_cards = int(round(len(edite_images) * 1.011)) if edite_images else 0
    return {
        "id": source.get("id"),
        "label": source.get("label"),
        "status": status,
        "root": relative_to_project(root),
        "root_exists": root.exists(),
        "pdf_count": len(pdfs),
        "edite_image_count": len(edite_images),
        "edite_by_grade": count_by_grade(edite_images),
        "estimated_capture_cards": max(estimated_cards, int(validation.get("total") or 0)),
        "verified_capture_cards": verified_cards,
        "validation": validation,
    }


def load_catalog_summary(config: dict[str, Any]) -> dict[str, Any]:
    source_config = config.get("normalized_json_sources") if isinstance(config.get("normalized_json_sources"), dict) else {}
    catalog_path = project_path(source_config.get("catalog_path"), default=PROJECT_ROOT / "data/problem_bank/catalog.json")
    catalog = read_json(catalog_path)
    bank_ids = set(str(item) for item in source_config.get("candidate_bank_ids") or [])
    banks = []
    total = 0
    for bank in catalog.get("banks") or []:
        if not isinstance(bank, dict):
            continue
        bank_id = str(bank.get("bank_id") or "")
        if bank_ids and bank_id not in bank_ids:
            continue
        count = int(bank.get("total") or 0)
        total += count
        banks.append(
            {
                "bank_id": bank_id,
                "name": bank.get("name"),
                "total": count,
                "manifest_path": bank.get("manifest_path"),
                "import_status": bank.get("import_status", "imported"),
            }
        )
    return {
        "catalog_path": relative_to_project(catalog_path),
        "candidate_total": total,
        "filter_status": source_config.get("elementary_filter_status"),
        "banks": banks,
    }


def target_for_track(config: dict[str, Any], track: str) -> int:
    tracks = config.get("tracks") if isinstance(config.get("tracks"), dict) else {}
    return int((tracks.get(track) or {}).get("target") or 0)


def create_workspace(config: dict[str, Any]) -> list[str]:
    workspace = config.get("workspace") if isinstance(config.get("workspace"), dict) else {}
    root = project_path(workspace.get("root"), default=PROJECT_ROOT / "data/problem_bank/elementary_50k")
    created: list[str] = []
    for item in workspace.get("directories") or []:
        path = root / str(item)
        path.mkdir(parents=True, exist_ok=True)
        created.append(relative_to_project(path))
    return created


def template_manifest_path(config: dict[str, Any]) -> Path:
    template = config.get("template_variant") if isinstance(config.get("template_variant"), dict) else {}
    return project_path(template.get("manifest"), default=PROJECT_ROOT / "data/problem_bank/elementary_50k/template_variants_manifest.json")


def template_manifest_count(path: Path) -> int:
    payload = read_json(path)
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        return len(payload.get("records") or [])
    return 0


def build_template_manifest(config: dict[str, Any], *, force: bool = False) -> dict[str, Any]:
    path = template_manifest_path(config)
    if path.exists() and not force:
        payload = read_json(path)
        return {
            "path": relative_to_project(path),
            "created": False,
            "record_count": len((payload or {}).get("records") or []) if isinstance(payload, dict) else 0,
        }

    target = target_for_track(config, "template_variant")
    per_grade = target // 6
    remainder = target % 6
    seed = int(((config.get("template_variant") or {}).get("seed") or 20260429))
    records: list[dict[str, Any]] = []
    for grade in range(1, 7):
        grade_count = per_grade + (1 if grade <= remainder else 0)
        for index in range(1, grade_count + 1):
            spec = make_problem("초등", "01.초등", grade, index, seed)
            payload = asdict(spec)
            payload["card_id"] = f"coco50k_template_g{grade:02d}_{index:05d}"
            payload["track"] = "template_variant"
            payload["school_level"] = "초등"
            payload["status"] = "candidate_not_rendered"
            payload["problem_text"] = "\n".join(spec.lines)
            payload["answer"] = spec.expected_answer
            payload["source"] = {
                "name": "Coco verified-template variant candidate",
                "policy": "candidate_only_until_solver_and_render_validation",
                "seed": seed,
            }
            payload["validation"] = {
                "render_required": True,
                "solver_required": True,
                "app_capture_required": False,
                "verified": False,
            }
            records.append(payload)
    by_grade = Counter(f"{item['grade']}학년" for item in records)
    by_topic = Counter(str(item.get("topic") or "unknown") for item in records)
    manifest = {
        "schema_version": "coco_elementary_50k_template_variants.v1",
        "generated_at": utc_now(),
        "target": target,
        "record_count": len(records),
        "seed": seed,
        "status": "candidate_not_verified",
        "coverage": {
            "by_grade": dict(sorted(by_grade.items())),
            "by_topic": dict(sorted(by_topic.items())),
        },
        "records": records,
    }
    write_json(path, manifest)
    return {"path": relative_to_project(path), "created": True, "record_count": len(records)}


def build_grade_queue(config: dict[str, Any], source_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    grade_targets = {str(k): int(v) for k, v in (config.get("grade_targets") or {}).items()}
    current = Counter()
    pending = Counter()
    for source in source_summaries:
        bucket = current if source.get("status") in VERIFIED_STATUSES else pending
        for grade, count in (source.get("edite_by_grade") or {}).items():
            bucket[str(grade)] += int(count)
    grades: dict[str, Any] = {}
    for grade, target in sorted(grade_targets.items()):
        verified = int(current.get(grade, 0))
        pending_count = int(pending.get(grade, 0))
        grades[grade] = {
            "target_total_cards": target,
            "verified_or_baseline_images": verified,
            "pending_images": pending_count,
            "remaining_after_current_images": max(0, target - verified - pending_count),
        }
    return grades


def build_report(config: dict[str, Any], *, template_step: dict[str, Any] | None = None, created_dirs: list[str] | None = None) -> dict[str, Any]:
    sources = [summarize_source(source) for source in config.get("source_roots") or [] if isinstance(source, dict)]
    actual_target = target_for_track(config, "actual_pdf_capture")
    normalized_target = target_for_track(config, "normalized_json")
    template_target = target_for_track(config, "template_variant")
    normalized = load_catalog_summary(config)
    template_path = template_manifest_path(config)
    template_count = template_manifest_count(template_path)
    verified_actual = sum(int(source.get("verified_capture_cards") or 0) for source in sources)
    estimated_actual = sum(int(source.get("estimated_capture_cards") or 0) for source in sources)
    normalized_available = int(normalized.get("candidate_total") or 0)
    prepared_total = verified_actual + min(normalized_available, normalized_target) + min(template_count, template_target)
    tracks = {
        "actual_pdf_capture": {
            "target": actual_target,
            "verified": verified_actual,
            "estimated_after_pending_sources": estimated_actual,
            "remaining_verified": max(0, actual_target - verified_actual),
            "remaining_estimated_after_pending_sources": max(0, actual_target - estimated_actual),
        },
        "normalized_json": {
            "target": normalized_target,
            "candidate_available": normalized_available,
            "usable_without_more_downloads": min(normalized_available, normalized_target),
            "remaining": max(0, normalized_target - normalized_available),
        },
        "template_variant": {
            "target": template_target,
            "candidate_manifest_records": template_count,
            "manifest": relative_to_project(template_path),
            "remaining": max(0, template_target - template_count),
        },
    }
    if verified_actual >= actual_target and normalized_available >= normalized_target and template_count >= template_target:
        readiness = "50k_candidate_requires_final_quality_gates"
    elif template_count >= template_target and normalized_available >= normalized_target:
        readiness = "source_acquisition_needed_for_actual_capture"
    else:
        readiness = "bootstrap_started"
    return {
        "schema_version": "coco_elementary_50k_readiness_report.v1",
        "generated_at": utc_now(),
        "target_total": int(config.get("target_total") or 50000),
        "readiness": readiness,
        "prepared_or_available_total": prepared_total,
        "remaining_to_50k": max(0, int(config.get("target_total") or 50000) - prepared_total),
        "tracks": tracks,
        "sources": sources,
        "normalized_json_sources": normalized,
        "grade_queue": build_grade_queue(config, sources),
        "created_directories": created_dirs or [],
        "template_step": template_step,
        "next_actions": next_actions(readiness, tracks),
    }


def next_actions(readiness: str, tracks: dict[str, Any]) -> list[str]:
    if readiness == "50k_candidate_requires_final_quality_gates":
        return [
            "Run dedupe across all three tracks.",
            "Run Coco capture validation for actual PDF cards and solver validation for template variants.",
            "Promote only passing records to 04_verified.",
        ]
    return [
        "Revalidate the pending Skai PDF set through the Coco capture flow.",
        "Add more independent elementary PDF sources until actual capture verified cards reach 15000.",
        "Filter external JSON banks down to elementary-suitable normalized records.",
        "Render and solver-test template candidates before counting them as verified.",
    ]


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare Coco's elementary 50k problem-bank plan and readiness report.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--init-dirs", action="store_true")
    parser.add_argument("--build-template-manifest", action="store_true")
    parser.add_argument("--force-template-manifest", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    config_path = project_path(args.config, default=DEFAULT_CONFIG)
    config = read_json(config_path)
    created_dirs = create_workspace(config) if args.init_dirs else []
    template_step = (
        build_template_manifest(config, force=bool(args.force_template_manifest))
        if args.build_template_manifest
        else None
    )
    report = build_report(config, template_step=template_step, created_dirs=created_dirs)
    write_json(project_path(args.report, default=DEFAULT_REPORT), report)
    print(json.dumps({"readiness": report["readiness"], "tracks": report["tracks"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
