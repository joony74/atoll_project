from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "data" / "problem_bank" / "beta" / "elementary_beta_config.json"
DEFAULT_REPORT = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "elementary_beta_stabilization_report.json"
DEFAULT_ROOT = PROJECT_ROOT / "03.학습문제" / "05.문제은행" / "01.초등"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}
ACTIVE_SOURCE_STATUSES = {"verified_baseline", "active", "candidate"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def project_path(value: str | Path | None, *, default: Path | None = None) -> Path:
    if not value:
        if default is None:
            raise ValueError("path value is required")
        return default
    raw = Path(str(value)).expanduser()
    if raw.is_absolute():
        return raw
    return PROJECT_ROOT / raw


def relative_to_project(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except Exception:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {"value": payload}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def rate(count: int | float, total: int | float) -> float:
    if not total:
        return 0.0
    return round(float(count) / float(total), 6)


def find_edite_images(root: Path) -> list[Path]:
    if not root.exists():
        return []
    images: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if "EDITE" not in {part.upper() for part in path.parts}:
            continue
        images.append(path)
    return sorted(images)


def grade_from_path(path: Path) -> str:
    for part in path.parts:
        match = re.search(r"([1-6])\s*학년", part)
        if match:
            return f"{match.group(1)}학년"
    match = re.search(r"초\s*([1-6])", path.name)
    if match:
        return f"{match.group(1)}학년"
    return "unknown"


def collect_corpus_summary(root: Path) -> dict[str, Any]:
    images = find_edite_images(root)
    by_grade = Counter(grade_from_path(path) for path in images)
    return {
        "root": relative_to_project(root),
        "root_exists": root.exists(),
        "edite_image_total": len(images),
        "by_grade": dict(sorted(by_grade.items())),
    }


def normalize_validation_summary(payload: dict[str, Any]) -> dict[str, Any]:
    source = payload.get("summary") if isinstance(payload.get("summary"), dict) else payload
    total = int(source.get("total") or source.get("processed_total") or 0)
    ok = int(source.get("ok") or 0)
    review = int(source.get("review") or 0)
    non_problem = int(source.get("non_problem") or 0)
    error = int(source.get("error") or 0)
    issue_counts = source.get("issue_counts") if isinstance(source.get("issue_counts"), dict) else {}
    by_topic = source.get("by_topic") if isinstance(source.get("by_topic"), dict) else {}
    return {
        "total": total,
        "ok": ok,
        "review": review,
        "non_problem": non_problem,
        "error": error,
        "ok_rate": rate(ok, total),
        "review_rate": rate(review, total),
        "error_rate": rate(error, total),
        "issue_counts": issue_counts,
        "by_topic": by_topic,
    }


def collect_source_summary(config: dict[str, Any]) -> dict[str, Any]:
    source_sets = config.get("source_sets") if isinstance(config.get("source_sets"), list) else []
    active_sources: list[dict[str, Any]] = []
    for source in source_sets:
        if not isinstance(source, dict):
            continue
        status = str(source.get("status") or "")
        root = project_path(source.get("root"), default=PROJECT_ROOT)
        report_path = project_path(source.get("summary_report"), default=DEFAULT_REPORT)
        summary = normalize_validation_summary(load_json(report_path))
        record = {
            "id": source.get("id"),
            "label": source.get("label"),
            "status": status,
            "root": relative_to_project(root),
            "root_exists": root.exists(),
            "summary_report": relative_to_project(report_path),
            "validated_cards": summary["total"],
            "ok_rate": summary["ok_rate"],
        }
        if status in ACTIVE_SOURCE_STATUSES:
            active_sources.append(record)
    total_cards = sum(int(source.get("validated_cards") or 0) for source in active_sources)
    weighted_ok = sum(
        int(source.get("validated_cards") or 0) * float(source.get("ok_rate") or 0.0)
        for source in active_sources
    )
    return {
        "active_source_count": len(active_sources),
        "active_validated_cards": total_cards,
        "weighted_ok_rate": round(weighted_ok / total_cards, 6) if total_cards else 0.0,
        "active_sources": active_sources,
    }


def gate(name: str, passed: bool, actual: Any, expected: str) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "actual": actual, "expected": expected}


def evaluate_gates(config: dict[str, Any], baseline: dict[str, Any], source_summary: dict[str, Any]) -> dict[str, Any]:
    thresholds = config.get("thresholds") if isinstance(config.get("thresholds"), dict) else {}
    total = int(baseline.get("total") or 0)
    source_count = int(source_summary.get("active_source_count") or 0)
    source_cards = int(source_summary.get("active_validated_cards") or 0)
    weighted_ok_rate = float(source_summary.get("weighted_ok_rate") or 0.0)

    current = [
        gate(
            "current_source_min_cards",
            total >= int(thresholds.get("current_source_min_cards", 500)),
            total,
            f">= {int(thresholds.get('current_source_min_cards', 500))}",
        ),
        gate(
            "current_source_min_ok_rate",
            float(baseline.get("ok_rate") or 0.0) >= float(thresholds.get("current_source_min_ok_rate", 0.99)),
            baseline.get("ok_rate"),
            f">= {float(thresholds.get('current_source_min_ok_rate', 0.99))}",
        ),
        gate(
            "current_source_max_review_rate",
            float(baseline.get("review_rate") or 0.0) <= float(thresholds.get("current_source_max_review_rate", 0.01)),
            baseline.get("review_rate"),
            f"<= {float(thresholds.get('current_source_max_review_rate', 0.01))}",
        ),
        gate(
            "current_source_max_error_rate",
            float(baseline.get("error_rate") or 0.0) <= float(thresholds.get("current_source_max_error_rate", 0.0)),
            baseline.get("error_rate"),
            f"<= {float(thresholds.get('current_source_max_error_rate', 0.0))}",
        ),
    ]
    beta = [
        gate(
            "beta_min_sources",
            source_count >= int(thresholds.get("beta_min_sources", 3)),
            source_count,
            f">= {int(thresholds.get('beta_min_sources', 3))}",
        ),
        gate(
            "beta_min_cards",
            source_cards >= int(thresholds.get("beta_min_cards", 5000)),
            source_cards,
            f">= {int(thresholds.get('beta_min_cards', 5000))}",
        ),
        gate(
            "beta_min_ok_rate",
            weighted_ok_rate >= float(thresholds.get("beta_min_ok_rate", 0.95)),
            weighted_ok_rate,
            f">= {float(thresholds.get('beta_min_ok_rate', 0.95))}",
        ),
    ]
    service = [
        gate(
            "service_min_sources",
            source_count >= int(thresholds.get("service_min_sources", 5)),
            source_count,
            f">= {int(thresholds.get('service_min_sources', 5))}",
        ),
        gate(
            "service_min_cards",
            source_cards >= int(thresholds.get("service_min_cards", 10000)),
            source_cards,
            f">= {int(thresholds.get('service_min_cards', 10000))}",
        ),
        gate(
            "service_min_ok_rate",
            weighted_ok_rate >= float(thresholds.get("service_min_ok_rate", 0.98)),
            weighted_ok_rate,
            f">= {float(thresholds.get('service_min_ok_rate', 0.98))}",
        ),
    ]
    current_passed = all(item["passed"] for item in current)
    beta_passed = current_passed and all(item["passed"] for item in beta)
    service_passed = beta_passed and all(item["passed"] for item in service)
    return {
        "current_source": {"passed": current_passed, "checks": current},
        "beta": {"passed": beta_passed, "checks": beta},
        "service": {"passed": service_passed, "checks": service},
    }


def readiness_from_gates(gates: dict[str, Any]) -> str:
    if gates.get("service", {}).get("passed"):
        return "service_candidate"
    if gates.get("beta", {}).get("passed"):
        return "beta_candidate"
    if gates.get("current_source", {}).get("passed"):
        return "current_source_pass_needs_more_sources"
    return "needs_fix_before_beta"


def next_actions(readiness: str, gates: dict[str, Any]) -> list[str]:
    if readiness == "service_candidate":
        return [
            "Freeze the current elementary engine as a release candidate.",
            "Run manual Coco capture smoke tests on representative PDF pages before packaging.",
        ]
    if readiness == "beta_candidate":
        return [
            "Open a limited elementary beta with source-level logging enabled.",
            "Keep adding independent PDF sources until service-candidate gates pass.",
        ]
    if readiness == "current_source_pass_needs_more_sources":
        return [
            "Add at least two more independent elementary PDF source sets.",
            "Run the same capture-flow validation for each new source.",
            "Merge validated source summaries into this config before beta approval.",
        ]
    failed = [
        check["name"]
        for group in gates.values()
        for check in group.get("checks", [])
        if not check.get("passed")
    ]
    return [
        "Fix the failed gate checks before adding more volume.",
        f"Failed checks: {', '.join(failed) if failed else 'unknown'}",
    ]


def build_validation_command(args: argparse.Namespace, config: dict[str, Any]) -> list[str]:
    routine = config.get("routine") if isinstance(config.get("routine"), dict) else {}
    report = project_path(args.validation_report or routine.get("validation_report"), default=DEFAULT_REPORT)
    segment_dir = project_path(args.segment_dir or routine.get("segment_dir"), default=PROJECT_ROOT / "tmp" / "elementary_beta_segments")
    capture_dir = project_path(args.capture_dir or routine.get("capture_dir"), default=PROJECT_ROOT / "tmp" / "elementary_beta_uploads")
    command = [
        str(args.python),
        "scripts/run_coco_capture_flow_validation.py",
        "--root",
        str(args.root),
        "--report",
        str(report),
        "--segment-dir",
        str(segment_dir),
        "--capture-dir",
        str(capture_dir),
        "--batch-size",
        str(args.batch_size),
        "--offset",
        str(args.offset),
    ]
    if args.limit:
        command.extend(["--limit", str(args.limit)])
    if args.clean:
        command.append("--clean")
    if args.app_register:
        command.append("--app-register")
    if args.restart_app_after_batch:
        command.append("--restart-app-after-batch")
    if args.write_every_batch:
        command.append("--write-every-batch")
    if args.stop_on_issue:
        command.append("--stop-on-issue")
    return command


def run_validation(args: argparse.Namespace, config: dict[str, Any]) -> dict[str, Any]:
    command = build_validation_command(args, config)
    if args.dry_run:
        return {"status": "dry_run", "command": command, "returncode": 0, "elapsed_seconds": 0.0}
    started = time.time()
    completed = subprocess.run(command, cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "command": command,
        "returncode": completed.returncode,
        "elapsed_seconds": round(time.time() - started, 3),
        "stdout_tail": completed.stdout[-12000:],
        "stderr_tail": completed.stderr[-12000:],
    }


def build_report(
    *,
    config_path: Path,
    config: dict[str, Any],
    root: Path,
    validation_step: dict[str, Any] | None = None,
    baseline_report_override: Path | None = None,
) -> dict[str, Any]:
    baseline_config = config.get("baseline") if isinstance(config.get("baseline"), dict) else {}
    baseline_report = baseline_report_override or project_path(baseline_config.get("summary_report"), default=DEFAULT_REPORT)
    baseline = normalize_validation_summary(load_json(baseline_report))
    corpus_summary = collect_corpus_summary(root)
    source_summary = collect_source_summary(config)
    gates = evaluate_gates(config, baseline, source_summary)
    readiness = readiness_from_gates(gates)
    return {
        "schema_version": "coco_elementary_beta_stabilization_report.v1",
        "generated_at": utc_now(),
        "config_path": relative_to_project(config_path),
        "root": relative_to_project(root),
        "baseline_report": relative_to_project(baseline_report),
        "readiness": readiness,
        "corpus_summary": corpus_summary,
        "baseline_summary": baseline,
        "source_summary": source_summary,
        "gates": gates,
        "next_actions": next_actions(readiness, gates),
        "validation_step": validation_step,
    }


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare and audit Coco elementary beta stabilization gates.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--run-validation", action="store_true")
    parser.add_argument("--validation-report", type=Path)
    parser.add_argument("--segment-dir", type=Path)
    parser.add_argument("--capture-dir", type=Path)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--app-register", action="store_true")
    parser.add_argument("--restart-app-after-batch", action="store_true")
    parser.add_argument("--write-every-batch", action="store_true")
    parser.add_argument("--stop-on-issue", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    config_path = project_path(args.config, default=DEFAULT_CONFIG)
    config = load_json(config_path)
    root = project_path(args.root or config.get("primary_root"), default=DEFAULT_ROOT)
    validation_step: dict[str, Any] | None = None
    baseline_override: Path | None = None
    if args.run_validation:
        validation_step = run_validation(args, config)
        routine = config.get("routine") if isinstance(config.get("routine"), dict) else {}
        baseline_override = project_path(args.validation_report or routine.get("validation_report"), default=DEFAULT_REPORT)
    report = build_report(
        config_path=config_path,
        config=config,
        root=root,
        validation_step=validation_step,
        baseline_report_override=baseline_override,
    )
    write_json(project_path(args.report, default=DEFAULT_REPORT), report)
    print(json.dumps({"readiness": report["readiness"], "gates": report["gates"]}, ensure_ascii=False, indent=2))
    return 1 if validation_step and validation_step.get("returncode") not in (0, None) else 0


if __name__ == "__main__":
    raise SystemExit(main())
