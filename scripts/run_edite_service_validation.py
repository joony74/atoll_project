from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.chat.recovery_card import build_recovery_message
from app.chat.state import (
    INITIAL_STUDY_CARD_KIND,
    load_state,
    persist_document,
    save_state,
)
from app.core.multi_problem_segmenter import save_problem_card_images
from app.core.pipeline import SERVICE_ENGINE_ID, SERVICE_ENGINE_VERSION, run_service_image_analysis


DEFAULT_ROOT = PROJECT_ROOT / "02.학습문제/05.문제은행/01.초등"
DEFAULT_SEGMENT_DIR = PROJECT_ROOT / "data/problem_bank/learned/coco_edite_service_segments"
DEFAULT_REPORT = PROJECT_ROOT / "data/problem_bank/learned/coco_edite_service_validation_report.json"
DEFAULT_TEMPLATE_QUEUE = PROJECT_ROOT / "data/problem_bank/learned/coco_edite_service_template_queue.json"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
DOC_PREFIX = "edite_service__"
ANSWER_KEY_PAGE_STEMS = {
    "초4-1_6단원_규칙찾기_1회_p04",
    "초4-1_6단원_규칙찾기_2회_p04",
    "초4-1_6단원_규칙찾기_3회_p05",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalized(value: str | Path) -> str:
    return unicodedata.normalize("NFC", str(value))


def natural_key(path: Path) -> list[Any]:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", normalized(path))]


def grade_from_path(path: Path) -> int:
    match = re.search(r"/(\d+)학년/", normalized(path))
    return int(match.group(1)) if match else 0


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def collect_edite_pages(root: Path) -> list[dict[str, Any]]:
    paths = sorted(
        [
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES and "/EDITE/" in normalized(path)
            and normalized(path.stem) not in ANSWER_KEY_PAGE_STEMS
        ],
        key=lambda path: (grade_from_path(path), natural_key(path)),
    )
    return [
        {
            "page_index": index,
            "grade": grade_from_path(path),
            "page_path": str(path),
            "page_relative_path": relative(path),
            "page_stem": path.stem,
        }
        for index, path in enumerate(paths, start=1)
    ]


def expand_cards(pages: list[dict[str, Any]], *, segment_dir: Path, clean: bool = False) -> list[dict[str, Any]]:
    if clean:
        shutil.rmtree(segment_dir, ignore_errors=True)
    segment_dir.mkdir(parents=True, exist_ok=True)
    cards: list[dict[str, Any]] = []
    for page in pages:
        page_path = Path(str(page["page_path"]))
        digest = hashlib.sha1(str(page_path.resolve()).encode("utf-8")).hexdigest()[:12]
        output_dir = segment_dir / digest
        shutil.rmtree(output_dir, ignore_errors=True)
        segmented = []
        try:
            segmented = save_problem_card_images(page_path, output_dir, base_name=page_path.stem, minimum_regions=2)
        except Exception as exc:
            page = {**page, "segment_error": f"{type(exc).__name__}: {exc}"}
        if not segmented:
            cards.append(
                {
                    **page,
                    "card_index": 1,
                    "card_label": "page",
                    "image_path": str(page_path),
                    "image_relative_path": relative(page_path),
                    "segment_kind": "unsplit_page",
                }
            )
            continue
        for card in segmented:
            card_path = Path(card.path)
            cards.append(
                {
                    **page,
                    "card_index": card.index,
                    "card_label": card.label,
                    "image_path": str(card_path),
                    "image_relative_path": relative(card_path),
                    "segment_kind": "problem_card",
                    "problem_card_bbox": list(card.bbox),
                }
            )
    for index, card in enumerate(cards, start=1):
        card["index"] = index
        digest_source = f"{card.get('page_relative_path')}::{card.get('card_label')}::{card.get('image_relative_path')}"
        card["doc_id"] = f"{DOC_PREFIX}{hashlib.sha1(digest_source.encode('utf-8')).hexdigest()[:12]}"
    return cards


def model_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def validation_status(analysis: dict[str, Any]) -> str:
    solved = model_dict(analysis.get("solve_result"))
    return str(solved.get("validation_status") or "failed").strip().lower() or "failed"


def visual_template(analysis: dict[str, Any]) -> dict[str, Any]:
    structured = model_dict(analysis.get("structured_problem"))
    metadata = model_dict(structured.get("metadata"))
    template = metadata.get("visual_template")
    return dict(template) if isinstance(template, dict) else {}


def problem_text(analysis: dict[str, Any]) -> str:
    structured = model_dict(analysis.get("structured_problem"))
    return str(structured.get("normalized_problem_text") or "").strip()


def answer_text(analysis: dict[str, Any]) -> str:
    solved = model_dict(analysis.get("solve_result"))
    return str(solved.get("matched_choice") or solved.get("computed_answer") or "").strip()


def issue_codes(card: dict[str, Any], analysis: dict[str, Any], card_message: str) -> list[str]:
    structured = model_dict(analysis.get("structured_problem"))
    metadata = model_dict(structured.get("metadata"))
    status = validation_status(analysis)
    template = visual_template(analysis)
    issues: list[str] = []
    if status == "failed":
        issues.append("service_validation_failed")
    elif status == "needs_review":
        issues.append("service_validation_needs_review")
    if str(metadata.get("school_level") or "") == "elementary" and str(metadata.get("school_profile") or "") == "elementary_visual" and not template:
        issues.append("elementary_visual_template_missing")
    text = problem_text(analysis)
    if not text or len(text) < 5:
        issues.append("problem_text_missing")
    if status != "failed" and not answer_text(analysis):
        issues.append("answer_missing")
    if "원본 대조가 먼저 필요" in card_message:
        issues.append("card_requires_original_review")
    return list(dict.fromkeys(issues))


def upsert_initial_card(state: dict[str, Any], *, doc_id: str, content: str, created_at: float) -> None:
    for item in state.get("chat_history") or []:
        if isinstance(item, dict) and item.get("doc_id") == doc_id and item.get("kind") == INITIAL_STUDY_CARD_KIND:
            item["content"] = content
            item["updated_at"] = created_at
            return
    state.setdefault("chat_history", []).append(
        {
            "role": "assistant",
            "content": content,
            "doc_id": doc_id,
            "kind": INITIAL_STUDY_CARD_KIND,
            "created_at": created_at,
        }
    )


def run_validation(
    *,
    root: Path = DEFAULT_ROOT,
    segment_dir: Path = DEFAULT_SEGMENT_DIR,
    report_path: Path = DEFAULT_REPORT,
    template_queue_path: Path = DEFAULT_TEMPLATE_QUEUE,
    offset: int = 0,
    limit: int = 0,
    clean_segments: bool = False,
    register: bool = True,
    progress_every: int = 0,
) -> dict[str, Any]:
    pages = collect_edite_pages(root)
    cards = expand_cards(pages, segment_dir=segment_dir, clean=clean_segments)
    selected = cards[max(0, offset) : max(0, offset) + limit if limit else None]
    state = load_state()
    results: list[dict[str, Any]] = []
    queue: list[dict[str, Any]] = []
    selected_total = len(selected)
    for selected_index, card in enumerate(selected, start=1):
        started = time.time()
        image_path = str(card["image_path"])
        analysis = run_service_image_analysis(image_path, debug=True)
        metadata = model_dict(model_dict(analysis.get("structured_problem")).get("metadata"))
        metadata["service_validation_source"] = {
            "source": "elementary_edite_registered_file",
            "page_relative_path": card.get("page_relative_path"),
            "image_relative_path": card.get("image_relative_path"),
            "grade": card.get("grade"),
            "card_label": card.get("card_label"),
            "segment_kind": card.get("segment_kind"),
            "problem_card_bbox": card.get("problem_card_bbox"),
        }
        analysis["structured_problem"]["metadata"] = metadata
        document = {
            "doc_id": card["doc_id"],
            "file_name": Path(image_path).name,
            "file_path": image_path,
            "registered_at": time.time(),
            "created_at": time.time(),
            "latest_user_query": "",
            "analysis": analysis,
        }
        card_message = build_recovery_message(document)
        issues = issue_codes(card, analysis, card_message)
        result = {
            **card,
            "status": "ok" if not issues else "review",
            "issues": issues,
            "validation_status": validation_status(analysis),
            "problem_text": problem_text(analysis),
            "answer": answer_text(analysis),
            "visual_template": visual_template(analysis),
            "analysis_engine": analysis.get("analysis_engine") or {},
            "elapsed_seconds": round(time.time() - started, 3),
        }
        results.append(result)
        if issues:
            queue.append(
                {
                    "doc_id": card["doc_id"],
                    "image_path": image_path,
                    "page_relative_path": card.get("page_relative_path"),
                    "grade": card.get("grade"),
                    "issues": issues,
                    "problem_text": result["problem_text"],
                    "answer": result["answer"],
                    "suggested_action": "template_or_ocr_rule_review",
                    "created_at": utc_now(),
                }
            )
        if register:
            persist_document(
                card["doc_id"],
                Path(image_path).name,
                image_path,
                analysis,
                latest_user_query="",
                registered_at=float(document["registered_at"]),
            )
            upsert_initial_card(state, doc_id=card["doc_id"], content=card_message, created_at=float(document["created_at"]))
        if progress_every > 0 and (selected_index % progress_every == 0 or selected_index == selected_total):
            ok_count = sum(1 for item in results if item.get("status") == "ok")
            review_count = sum(1 for item in results if item.get("status") == "review")
            print(
                f"[progress {selected_index}/{selected_total}] ok={ok_count} review={review_count} "
                f"latest={card['doc_id']} status={result['status']}",
                flush=True,
            )

    counts: dict[str, int] = {}
    issue_counts: dict[str, int] = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
        for issue in result.get("issues") or []:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
    report = {
        "schema_version": "coco_edite_service_validation_report.v1",
        "generated_at": utc_now(),
        "engine_id": SERVICE_ENGINE_ID,
        "engine_version": SERVICE_ENGINE_VERSION,
        "page_total": len(pages),
        "card_total": len(cards),
        "selected_total": len(selected),
        "offset": offset,
        "limit": limit,
        "summary": counts,
        "issue_counts": issue_counts,
        "results": results,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    template_queue_path.write_text(
        json.dumps(
            {
                "schema_version": "coco_edite_service_template_queue.v1",
                "generated_at": report["generated_at"],
                "engine_id": SERVICE_ENGINE_ID,
                "engine_version": SERVICE_ENGINE_VERSION,
                "total": len(queue),
                "items": queue,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if register:
        docs_by_id = {str(item.get("doc_id") or ""): item for item in state.get("documents") or [] if isinstance(item, dict)}
        new_docs = []
        now = time.time()
        for index, result in enumerate(results):
            doc_id = str(result["doc_id"])
            new_docs.append(
                {
                    "doc_id": doc_id,
                    "file_name": Path(str(result["image_path"])).name,
                    "file_path": str(result["image_path"]),
                    "created_at": now + index / 1000,
                    "registered_at": now + index / 1000,
                    "last_opened_at": now + index / 1000,
                    "latest_user_query": "",
                    "service_validation": "elementary_edite",
                }
            )
            docs_by_id.pop(doc_id, None)
        state["documents"] = [*new_docs, *docs_by_id.values()]
        if new_docs:
            state["selected_doc_id"] = new_docs[0]["doc_id"]
            state["last_active_doc_id"] = new_docs[0]["doc_id"]
            state["chat_mode"] = "study"
            state["last_active_chat_mode"] = "study"
            state["last_active_at"] = now
        save_state(state)
    report["template_queue_total"] = len(queue)
    return report


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate elementary EDITE files only through CocoApp service registration flow.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--segment-dir", type=Path, default=DEFAULT_SEGMENT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--template-queue", type=Path, default=DEFAULT_TEMPLATE_QUEUE)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--clean-segments", action="store_true")
    parser.add_argument("--no-register", action="store_true")
    parser.add_argument("--count-only", action="store_true")
    parser.add_argument("--progress-every", type=int, default=0)
    return parser


def main() -> None:
    args = create_parser().parse_args()
    if args.count_only:
        pages = collect_edite_pages(args.root)
        cards = expand_cards(pages, segment_dir=args.segment_dir, clean=args.clean_segments)
        print(json.dumps({"page_total": len(pages), "card_total": len(cards)}, ensure_ascii=False))
        return
    report = run_validation(
        root=args.root,
        segment_dir=args.segment_dir,
        report_path=args.report,
        template_queue_path=args.template_queue,
        offset=max(0, args.offset),
        limit=max(0, args.limit),
        clean_segments=args.clean_segments,
        register=not args.no_register,
        progress_every=max(0, args.progress_every),
    )
    print(
        json.dumps(
            {
                "page_total": report["page_total"],
                "card_total": report["card_total"],
                "selected_total": report["selected_total"],
                "summary": report["summary"],
                "issue_counts": report["issue_counts"],
                "template_queue_total": report["template_queue_total"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
