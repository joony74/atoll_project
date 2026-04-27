from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_mass_learning_cycle_report.json"
CATALOG_PATH = PROJECT_ROOT / "data" / "problem_bank" / "catalog.json"
PROBLEM_PROFILE_PATH = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_problem_generation_profile.json"
MATH_PROFILE_PATH = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_math_normalization_profile.json"
OCR_REGRESSION_PATH = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_ocr_regression_cases.json"
ACTUAL_OCR_PATH = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_ocr_actual_cases.json"
OUTPUT_TAIL_CHARS = 12_000


@dataclass(frozen=True)
class CycleStep:
    name: str
    command: tuple[str, ...]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Coco's sequential mass-learning refresh cycle.")
    parser.add_argument("--python", default=sys.executable, help="Python executable for child steps.")
    parser.add_argument("--metamath-limit", type=int, default=20_000)
    parser.add_argument("--deepmind-per-module", type=int, default=10)
    parser.add_argument("--deepmind-seed", type=int, default=42)
    parser.add_argument("--ocr-max-cases", type=int, default=220)
    parser.add_argument("--ocr-per-reason", type=int, default=48)
    parser.add_argument("--ocr-per-bank", type=int, default=80)
    parser.add_argument("--actual-ocr-per-grade", type=int, default=4)
    parser.add_argument("--actual-ocr-limit", type=int, default=64)
    parser.add_argument("--actual-ocr-max-cases", type=int, default=48)
    parser.add_argument("--actual-ocr-layout", default="expression", choices=["expression", "word", "table", ""])
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--skip-import", action="store_true")
    parser.add_argument("--skip-ocr-regression", action="store_true")
    parser.add_argument("--skip-actual-ocr", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--keep-going", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def script_command(python: str, script_name: str, *args: object) -> tuple[str, ...]:
    return (python, f"scripts/{script_name}", *(str(arg) for arg in args))


def build_steps(args: argparse.Namespace) -> list[CycleStep]:
    python = str(args.python)
    steps: list[CycleStep] = []

    if not args.skip_import:
        steps.extend(
            [
                CycleStep(
                    "Import MetaMathQA sample",
                    script_command(
                        python,
                        "import_metamathqa_problem_bank.py",
                        "--limit",
                        max(1, int(args.metamath_limit)),
                    ),
                ),
                CycleStep(
                    "Generate DeepMind mathematics sample",
                    script_command(
                        python,
                        "import_deepmind_mathematics_problem_bank.py",
                        "--per-module",
                        max(1, int(args.deepmind_per_module)),
                        "--seed",
                        int(args.deepmind_seed),
                    ),
                ),
            ]
        )

    steps.extend(
        [
            CycleStep(
                "Build problem generation profile",
                script_command(python, "build_problem_generation_profile.py"),
            ),
            CycleStep(
                "Build math normalization profile",
                script_command(python, "build_math_normalization_profile.py"),
            ),
        ]
    )

    if not args.skip_ocr_regression:
        steps.append(
            CycleStep(
                "Build OCR normalization regression set",
                script_command(
                    python,
                    "build_ocr_normalization_regression.py",
                    "--max-cases",
                    max(1, int(args.ocr_max_cases)),
                    "--per-reason",
                    max(1, int(args.ocr_per_reason)),
                    "--per-bank",
                    max(1, int(args.ocr_per_bank)),
                ),
            )
        )

    if not args.skip_actual_ocr:
        steps.append(
            CycleStep(
                "Capture actual OCR regression cases",
                script_command(
                    python,
                    "capture_actual_ocr_regression_cases.py",
                    "--per-grade",
                    max(1, int(args.actual_ocr_per_grade)),
                    "--limit",
                    max(0, int(args.actual_ocr_limit)),
                    "--max-cases",
                    max(1, int(args.actual_ocr_max_cases)),
                    "--layout",
                    str(args.actual_ocr_layout),
                ),
            )
        )

    if not args.skip_tests:
        steps.append(
            CycleStep(
                "Run unit test suite",
                (python, "-m", "unittest", "discover", "-s", "tests"),
            )
        )

    return steps


def command_text(command: tuple[str, ...]) -> str:
    return shlex.join(command)


def _tail(value: str) -> str:
    if len(value) <= OUTPUT_TAIL_CHARS:
        return value
    return value[-OUTPUT_TAIL_CHARS:]


def run_step(step: CycleStep, *, dry_run: bool) -> dict[str, Any]:
    started = time.time()
    result: dict[str, Any] = {
        "name": step.name,
        "command": list(step.command),
        "command_text": command_text(step.command),
        "started_at": utc_now(),
    }
    print(f"\n==> {step.name}")
    print(result["command_text"])

    if dry_run:
        result.update(
            {
                "status": "dry_run",
                "returncode": 0,
                "elapsed_seconds": 0.0,
                "stdout_tail": "",
                "stderr_tail": "",
            }
        )
        return result

    completed = subprocess.run(
        step.command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    result.update(
        {
            "status": "passed" if completed.returncode == 0 else "failed",
            "returncode": completed.returncode,
            "elapsed_seconds": round(time.time() - started, 3),
            "stdout_tail": _tail(completed.stdout),
            "stderr_tail": _tail(completed.stderr),
        }
    )
    if completed.stdout:
        print(_tail(completed.stdout).rstrip())
    if completed.stderr:
        print(_tail(completed.stderr).rstrip(), file=sys.stderr)
    print(f"<== {step.name}: {result['status']} ({result['elapsed_seconds']}s)")
    return result


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"error": str(exc)}
    return payload if isinstance(payload, dict) else {"value_type": type(payload).__name__}


def collect_catalog_summary() -> dict[str, Any]:
    catalog = load_json(CATALOG_PATH)
    banks = catalog.get("banks") if isinstance(catalog.get("banks"), list) else []
    totals = {
        str(bank.get("bank_id")): int(bank.get("total") or 0)
        for bank in banks
        if isinstance(bank, dict)
    }
    return {
        "path": str(CATALOG_PATH.relative_to(PROJECT_ROOT)),
        "bank_count": len(totals),
        "total_records": sum(totals.values()),
        "by_bank": dict(sorted(totals.items())),
        "updated_at": catalog.get("updated_at"),
    }


def collect_learned_summary() -> dict[str, Any]:
    problem_profile = load_json(PROBLEM_PROFILE_PATH)
    math_profile = load_json(MATH_PROFILE_PATH)
    ocr_regression = load_json(OCR_REGRESSION_PATH)
    actual_ocr = load_json(ACTUAL_OCR_PATH)
    return {
        "problem_generation_profile": {
            "path": str(PROBLEM_PROFILE_PATH.relative_to(PROJECT_ROOT)),
            "total_records": (problem_profile.get("counts") or {}).get("total_records"),
            "domain_count": len(problem_profile.get("domains") or {}),
        },
        "math_normalization_profile": {
            "path": str(MATH_PROFILE_PATH.relative_to(PROJECT_ROOT)),
            "total_records": (math_profile.get("source") or {}).get("total_records"),
            "runtime_rule_count": len(math_profile.get("runtime_rules") or []),
            "ocr_confusion_pair_count": len(math_profile.get("ocr_confusion_pairs") or []),
        },
        "ocr_regression_cases": {
            "path": str(OCR_REGRESSION_PATH.relative_to(PROJECT_ROOT)),
            "coverage": ocr_regression.get("coverage") or {},
        },
        "actual_ocr_cases": {
            "path": str(ACTUAL_OCR_PATH.relative_to(PROJECT_ROOT)),
            "coverage": actual_ocr.get("coverage") or {},
        },
    }


def options_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload = vars(args).copy()
    payload["report"] = str(payload["report"])
    return dict(sorted(payload.items()))


def build_report(args: argparse.Namespace, step_results: list[dict[str, Any]], elapsed_seconds: float) -> dict[str, Any]:
    failed_steps = [step for step in step_results if int(step.get("returncode") or 0) != 0]
    return {
        "schema_version": "coco_mass_learning_cycle_report.v1",
        "generated_at": utc_now(),
        "project_root": str(PROJECT_ROOT),
        "success": not failed_steps,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "options": options_payload(args),
        "summary": {
            "step_count": len(step_results),
            "failed_step_count": len(failed_steps),
            "failed_steps": [str(step.get("name")) for step in failed_steps],
            "catalog": collect_catalog_summary(),
            "learned": collect_learned_summary(),
        },
        "steps": step_results,
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path = path if path.is_absolute() else PROJECT_ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    started = time.time()
    results: list[dict[str, Any]] = []

    for step in build_steps(args):
        result = run_step(step, dry_run=bool(args.dry_run))
        results.append(result)
        if int(result.get("returncode") or 0) != 0 and not args.keep_going:
            break

    report = build_report(args, results, time.time() - started)
    write_report(args.report, report)
    report_path = args.report if args.report.is_absolute() else PROJECT_ROOT / args.report
    print(f"\nreport={report_path}")
    print(f"success={report['success']}")
    print(f"total_records={report['summary']['catalog']['total_records']}")
    if report["summary"]["failed_steps"]:
        print(f"failed_steps={report['summary']['failed_steps']}")
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
