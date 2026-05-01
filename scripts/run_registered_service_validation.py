from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.chat.recovery_card import build_recovery_message
from app.chat.state import (
    DOCS_DIR,
    INITIAL_STUDY_CARD_KIND,
    load_state,
    persist_document,
    save_state,
)
from app.core.pipeline import SERVICE_ENGINE_ID, SERVICE_ENGINE_VERSION, run_service_image_analysis


DEFAULT_REPORT_PATH = PROJECT_ROOT / "data/problem_bank/learned/coco_registered_service_validation_report.json"
DEFAULT_TEMPLATE_QUEUE_PATH = PROJECT_ROOT / "data/problem_bank/learned/coco_registered_template_queue.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_doc(doc_id: str) -> dict[str, Any] | None:
    path = DOCS_DIR / f"{doc_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _status(analysis: dict[str, Any]) -> str:
    solved = analysis.get("solve_result") if isinstance(analysis, dict) else {}
    if not isinstance(solved, dict):
        return "failed"
    return str(solved.get("validation_status") or "failed").strip().lower() or "failed"


def _template_info(analysis: dict[str, Any]) -> dict[str, Any]:
    structured = analysis.get("structured_problem") if isinstance(analysis, dict) else {}
    if not isinstance(structured, dict):
        return {}
    metadata = structured.get("metadata") if isinstance(structured.get("metadata"), dict) else {}
    visual_template = metadata.get("visual_template")
    return dict(visual_template) if isinstance(visual_template, dict) else {}


def _problem_text(analysis: dict[str, Any]) -> str:
    structured = analysis.get("structured_problem") if isinstance(analysis, dict) else {}
    if not isinstance(structured, dict):
        return ""
    return str(structured.get("normalized_problem_text") or "").strip()


def _computed_answer(analysis: dict[str, Any]) -> str:
    solved = analysis.get("solve_result") if isinstance(analysis, dict) else {}
    if not isinstance(solved, dict):
        return ""
    return str(solved.get("matched_choice") or solved.get("computed_answer") or "").strip()


def _issue_codes(document: dict[str, Any], card_message: str) -> list[str]:
    analysis = document.get("analysis") if isinstance(document.get("analysis"), dict) else {}
    status = _status(analysis)
    structured = analysis.get("structured_problem") if isinstance(analysis, dict) else {}
    metadata = structured.get("metadata") if isinstance(structured, dict) and isinstance(structured.get("metadata"), dict) else {}
    template = _template_info(analysis)
    text = _problem_text(analysis)
    answer = _computed_answer(analysis)
    issues: list[str] = []
    if status == "failed":
        issues.append("service_validation_failed")
    elif status == "needs_review":
        issues.append("service_validation_needs_review")
    if str(metadata.get("school_level") or "") == "elementary" and str(metadata.get("school_profile") or "") == "elementary_visual" and not template:
        issues.append("elementary_visual_template_missing")
    if not text or len(text) < 5:
        issues.append("problem_text_missing")
    if status != "failed" and not answer:
        issues.append("answer_missing")
    if "원본 대조가 먼저 필요" in card_message:
        issues.append("card_requires_original_review")
    return list(dict.fromkeys(issues))


def _upsert_initial_card(state: dict[str, Any], document: dict[str, Any], card_message: str, created_at: float) -> None:
    doc_id = str(document.get("doc_id") or "").strip()
    replaced = False
    for item in state.get("chat_history") or []:
        if not isinstance(item, dict):
            continue
        if item.get("doc_id") == doc_id and item.get("kind") == INITIAL_STUDY_CARD_KIND:
            item["content"] = card_message
            item["updated_at"] = created_at
            replaced = True
            break
    if not replaced:
        state.setdefault("chat_history", []).append(
            {
                "role": "assistant",
                "content": card_message,
                "doc_id": doc_id,
                "kind": INITIAL_STUDY_CARD_KIND,
                "created_at": created_at,
            }
        )


def validate_registered_documents(*, write: bool = True, limit: int = 0) -> dict[str, Any]:
    state = load_state()
    documents = [item for item in state.get("documents") or [] if isinstance(item, dict)]
    if limit > 0:
        documents = documents[:limit]

    results: list[dict[str, Any]] = []
    template_queue: list[dict[str, Any]] = []
    for item in documents:
        doc_id = str(item.get("doc_id") or "").strip()
        stored = _load_doc(doc_id)
        if not stored:
            continue
        image_path = str(stored.get("file_path") or item.get("file_path") or "").strip()
        if not image_path or not Path(image_path).exists():
            results.append({"doc_id": doc_id, "status": "missing_file", "image_path": image_path})
            continue

        started = time.time()
        analysis = run_service_image_analysis(image_path, user_query=str(stored.get("latest_user_query") or ""), debug=True)
        document = {
            **stored,
            "analysis": analysis,
        }
        card_message = build_recovery_message(document)
        issues = _issue_codes(document, card_message)
        status = "ok" if not issues else "review"
        result = {
            "doc_id": doc_id,
            "file_name": str(stored.get("file_name") or item.get("file_name") or ""),
            "image_path": image_path,
            "status": status,
            "issues": issues,
            "validation_status": _status(analysis),
            "problem_text": _problem_text(analysis),
            "answer": _computed_answer(analysis),
            "visual_template": _template_info(analysis),
            "analysis_engine": analysis.get("analysis_engine") or {},
            "elapsed_seconds": round(time.time() - started, 3),
        }
        results.append(result)
        if issues:
            template_queue.append(
                {
                    "doc_id": doc_id,
                    "file_name": result["file_name"],
                    "image_path": image_path,
                    "issues": issues,
                    "problem_text": result["problem_text"],
                    "answer": result["answer"],
                    "suggested_action": "template_or_ocr_rule_review",
                    "created_at": _utc_now(),
                }
            )
        if write:
            persist_document(
                doc_id,
                str(stored.get("file_name") or item.get("file_name") or doc_id),
                image_path,
                analysis,
                latest_user_query=str(stored.get("latest_user_query") or ""),
                registered_at=float(stored.get("registered_at") or item.get("registered_at") or time.time()),
            )
            _upsert_initial_card(state, document, card_message, time.time())

    summary_counts: dict[str, int] = {}
    for result in results:
        summary_counts[str(result.get("status") or "unknown")] = summary_counts.get(str(result.get("status") or "unknown"), 0) + 1
    report = {
        "schema_version": "coco_registered_service_validation_report.v1",
        "generated_at": _utc_now(),
        "engine_id": SERVICE_ENGINE_ID,
        "engine_version": SERVICE_ENGINE_VERSION,
        "total": len(results),
        "summary": summary_counts,
        "results": results,
    }
    if write:
        DEFAULT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        DEFAULT_TEMPLATE_QUEUE_PATH.write_text(
            json.dumps(
                {
                    "schema_version": "coco_registered_template_queue.v1",
                    "generated_at": report["generated_at"],
                    "engine_id": SERVICE_ENGINE_ID,
                    "engine_version": SERVICE_ENGINE_VERSION,
                    "total": len(template_queue),
                    "items": template_queue,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        save_state(state)
    report["template_queue_total"] = len(template_queue)
    return report


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate only CocoApp-registered files through the service engine.")
    parser.add_argument("--limit", type=int, default=0, help="Validate only the newest N registered files.")
    parser.add_argument("--dry-run", action="store_true", help="Run validation without updating documents/cards/reports.")
    return parser


def main() -> None:
    args = create_parser().parse_args()
    report = validate_registered_documents(write=not args.dry_run, limit=args.limit)
    print(json.dumps({"total": report["total"], "summary": report["summary"], "template_queue_total": report["template_queue_total"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
