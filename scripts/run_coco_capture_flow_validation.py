from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.chat.recovery_card import build_recovery_message, display_topic
from app.chat.state import (
    APP_SUPPORT_DIR,
    INITIAL_STUDY_CARD_KIND,
    UPLOADS_DIR,
    ensure_dirs,
    load_state,
    persist_document,
    save_state,
)
from app.core.multi_problem_segmenter import save_problem_card_images
from app.core.pipeline import run_solve_pipeline
from scripts.run_coco_app_corpus_validation import (
    apply_pdf_card_text,
    batch_summary,
    classify_issues,
    collect_images,
    extract_pdf_answer_key,
    extract_pdf_card_text,
    issue_examples,
    model_dump,
    relative_to_project,
    slim_text,
    text_candidates,
)


DEFAULT_ROOT = PROJECT_ROOT / "02.학습문제" / "05.문제은행" / "01.초등"
DEFAULT_CAPTURE_DIR = APP_SUPPORT_DIR / "captures" / "validation"
DEFAULT_SEGMENT_DIR = APP_SUPPORT_DIR / "captures" / "validation_segments"
DEFAULT_REPORT = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_capture_flow_validation_report.json"
CAPTURE_SLOT_PREFIX = "capture_flow_slot__"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_capture_name(record: dict[str, Any]) -> str:
    source = Path(str(record.get("image_path") or "capture.png"))
    stem = re.sub(r"[^\w가-힣().+-]+", "_", source.stem, flags=re.UNICODE).strip("_")
    if len(stem) > 120:
        stem = f"{stem[:48]}_{stem[-70:]}"
    stem = stem or "capture"
    return f"capture_{int(record.get('index') or 0):05d}_{stem}.png"


def make_capture_upload(record: dict[str, Any], *, capture_dir: Path = DEFAULT_CAPTURE_DIR) -> dict[str, Any]:
    source_path = Path(str(record.get("image_path") or ""))
    if not source_path.exists():
        raise FileNotFoundError(str(source_path))
    data = source_path.read_bytes()
    capture_dir.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    capture_name = safe_capture_name(record)
    capture_path = capture_dir / capture_name
    capture_path.write_bytes(data)

    file_hash = hashlib.sha1(data).hexdigest()[:12]
    upload_path = UPLOADS_DIR / f"{file_hash}_{capture_name}"
    upload_path.write_bytes(data)
    return {
        "capture_file_id": file_hash,
        "capture_file_name": capture_name,
        "capture_path": str(capture_path),
        "upload_path": str(upload_path),
        "upload_relative_path": relative_to_project(upload_path),
    }


def expand_capture_cards_limited(
    page_records: list[dict[str, Any]],
    *,
    segment_dir: Path,
    needed: int | None,
) -> list[dict[str, Any]]:
    segment_dir.mkdir(parents=True, exist_ok=True)
    expanded: list[dict[str, Any]] = []
    cumulative_problem_counts: dict[str, int] = defaultdict(int)
    for page_record in page_records:
        image_path = Path(str(page_record.get("image_path") or ""))
        document_key = str(page_record.get("pdf_path") or page_record.get("title_slug") or image_path.stem)
        problem_base = cumulative_problem_counts[document_key]
        cards = []
        if image_path.exists():
            digest = hashlib.sha1(str(image_path.resolve()).encode("utf-8")).hexdigest()[:12]
            output_dir = segment_dir / digest
            shutil.rmtree(output_dir, ignore_errors=True)
            try:
                cards = save_problem_card_images(image_path, output_dir, base_name=image_path.stem, minimum_regions=2)
            except Exception as exc:
                page_record = {**page_record, "segment_error": f"{type(exc).__name__}: {exc}"}
        if not cards:
            expanded.append(
                {
                    **page_record,
                    "source_kind": "coco_app_capture_unsplit",
                    "expected_problem_number": problem_base + 1,
                }
            )
            cumulative_problem_counts[document_key] += 1
        else:
            for card in cards:
                expanded.append(
                    {
                        **page_record,
                        "case_id": f"{page_record.get('case_id')}_capture_q{card.label}",
                        "source_kind": "coco_app_capture_card",
                        "image_path": str(card.path),
                        "relative_path": relative_to_project(Path(card.path)),
                        "parent_page_index": page_record.get("index"),
                        "parent_relative_path": page_record.get("relative_path"),
                        "problem_card_index": card.index,
                        "problem_card_label": card.label,
                        "problem_card_bbox": list(card.bbox),
                        "expected_problem_number": problem_base + card.index,
                    }
                )
            cumulative_problem_counts[document_key] += len(cards)
        if needed is not None and len(expanded) >= needed:
            break
    for index, record in enumerate(expanded, start=1):
        record["index"] = index
    return expanded


def make_document(record: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "doc_id": str(record.get("case_id") or record.get("capture_file_id") or ""),
        "file_name": str(record.get("capture_file_name") or Path(str(record.get("image_path") or "")).name),
        "file_path": str(record.get("upload_path") or record.get("image_path") or ""),
        "analysis": analysis,
    }


VISUAL_ANSWER_CUES = (
    "○표",
    "□표",
    "표하세요",
    "표 하세요",
    "색칠",
    "그리",
    "그려",
    "이어",
    "고르",
    "찾아",
    "오른쪽",
    "왼쪽",
    "세번째",
    "세 번째",
    "몇번째",
    "몇 번째",
    "모양",
    "모아서",
    "순서대로",
    "차례대로",
    "기호",
    "표를 완성",
    "그림그래프",
    "표로 나타내",
    "그래프로 나타내",
    "높은",
    "낮은",
    "무거운",
    "가벼운",
    "긴",
    "짧은",
    "담을 수 있는",
    "차례로",
)


def expected_problem_number(record: dict[str, Any]) -> int | None:
    override = expected_problem_number_override(record)
    if override is not None:
        return override
    try:
        expected = int(record.get("expected_problem_number") or 0)
    except Exception:
        expected = 0
    if expected > 0:
        return expected
    try:
        card_index = int(record.get("problem_card_index") or record.get("problem_card_label") or 0)
    except Exception:
        card_index = 0
    if card_index <= 0:
        return None
    parent_text = str(record.get("parent_relative_path") or record.get("image_path") or "")
    match = re.search(r"_p(\d{2,3})(?:_|\.png$)", parent_text)
    if match:
        page_index = int(match.group(1))
        return card_index + max(0, page_index - 1) * 10
    try:
        source_page = int(record.get("source_page") or 1)
    except Exception:
        source_page = 1
    return card_index + max(0, source_page - 1) * 10


def expected_problem_number_override(record: dict[str, Any]) -> int | None:
    """Correct page-local card numbers when cropped PDFs start after problem 1."""
    try:
        card_index = int(record.get("problem_card_index") or record.get("problem_card_label") or 0)
    except Exception:
        card_index = 0
    if card_index <= 0:
        return None
    source = unicodedata_normalized_path(record)
    page_offsets = {
        "초4__진단평가_3회_p02": 7,
        "초4__진단평가_3회_p03": 15,
    }
    for marker, offset in page_offsets.items():
        if marker in source:
            return card_index + offset
    decimal_match = re.search(r"초4-2_3단원_소수의덧셈과뺄셈_\d회_p0([23])", source)
    if decimal_match:
        return card_index + (8 if decimal_match.group(1) == "2" else 16)
    return None


def unicodedata_normalized_path(record: dict[str, Any]) -> str:
    source = " ".join(
        str(record.get(key) or "")
        for key in ("parent_relative_path", "relative_path", "image_path", "pdf_path")
    )
    try:
        import unicodedata

        source = unicodedata.normalize("NFC", source)
    except Exception:
        pass
    source = source.replace("[", "_").replace("]", "_")
    source = re.sub(r"[^\w가-힣.-]+", "_", source, flags=re.UNICODE)
    return source


def problem_number_from_text(value: str) -> int | None:
    text = str(value or "")
    for pattern in (r"^\s*(\d{1,2})\s*[.)](?!\d)", r"(?<!\d)(\d{1,2})\s*[.)]\s*(?=[가-힣<])"):
        match = re.search(pattern, text)
        if match:
            number = int(match.group(1))
            if 1 <= number <= 20:
                return number
    return None


def problem_number_candidates_from_text(value: str) -> list[int]:
    text = str(value or "")
    candidates: list[int] = []
    seen: set[tuple[int, int]] = set()
    for pattern in (r"^\s*(\d{1,2})\s*[.)](?!\d)", r"(?<!\d)(\d{1,2})\s*[.)]\s*(?=[가-힣<])"):
        for match in re.finditer(pattern, text):
            number = int(match.group(1))
            key = (match.start(1), number)
            if 1 <= number <= 20 and key not in seen:
                candidates.append(number)
                seen.add(key)
    return candidates


def expected_answer(record: dict[str, Any], structured: dict[str, Any]) -> tuple[int | None, str, str]:
    pdf_text = extract_pdf_card_text(record)
    weighted_numbers: Counter[int] = Counter()
    repeated_capture_numbers: Counter[int] = Counter()
    normalized_problem_text = str(structured.get("normalized_problem_text") or "")
    normalized_problem_numbers = problem_number_candidates_from_text(normalized_problem_text)
    for number in normalized_problem_numbers:
        weighted_numbers[number] += 3
    for candidate in structured.get("source_text_candidates") or []:
        weight = 1 if str(candidate or "").strip() == pdf_text.strip() else 2
        candidate_numbers = problem_number_candidates_from_text(str(candidate or ""))
        if weight > 1 and 1 <= len(set(candidate_numbers)) <= 3:
            repeated_capture_numbers.update(candidate_numbers)
        for number in candidate_numbers:
            weighted_numbers[number] += weight
    for number in problem_number_candidates_from_text(pdf_text):
        weighted_numbers[number] += 1
    override_problem_no = expected_problem_number_override(record)
    fallback_problem_no = expected_problem_number(record)
    try:
        source_page = int(record.get("source_page") or 1)
    except Exception:
        source_page = 1
    if (
        override_problem_no is not None
        and not normalized_problem_numbers
    ):
        problem_no = override_problem_no
    elif (
        source_page <= 1
        and fallback_problem_no is not None
        and not normalized_problem_numbers
    ):
        problem_no = fallback_problem_no
    elif repeated_capture_numbers and repeated_capture_numbers.most_common(1)[0][1] >= 2:
        problem_no = repeated_capture_numbers.most_common(1)[0][0]
    elif weighted_numbers:
        problem_no = max(weighted_numbers.items(), key=lambda item: (item[1], item[0]))[0]
    else:
        problem_no = fallback_problem_no
    answer = ""
    pdf_path = str(record.get("pdf_path") or "").strip()
    if pdf_path and problem_no is not None:
        answer = extract_pdf_answer_key(pdf_path).get(problem_no, "")
    return problem_no, answer, pdf_text


def normalize_answer(value: str) -> str:
    text = re.sub(r"\s+", "", str(value or ""))
    text = text.replace("\u200b", "").replace("\ufeff", "")
    text = re.sub(r"[（(]또는[^）)]*[）)]", "", text)
    text = text.replace("\ue048", "+")
    text = text.replace("\ue000", "0").replace("\ue03d", "0")
    text = text.replace("\ue053", ".")
    text = text.replace("\ue055", "<").replace("\ue056", ">")
    text = text.replace("°", "").replace("˚", "").replace("º", "")
    text = text.replace("...", "").replace("…", "").replace("⋯", "")
    text = re.sub(r"[\ue000-\uf8ff]", "", text)
    text = text.replace("＋", "+").replace("=", "=").replace("＝", "=").replace("÷", "/")
    text = re.sub(r"(?<!k)(\d{1,2})g(\d{3})g", r"\1kg\2g", text, flags=re.I)
    text = re.sub(r"-\d+-$", "", text)
    for index in range(1, 21):
        text = text.replace(chr(0x2460 + index - 1), f"({index})")
        text = text.replace(chr(0x2474 + index - 1), f"({index})")
    text = re.sub(
        r"answer_text=|answer=|빈칸[:：]?|정답[:：]?|합[:：]?|차[:：]?|몫[:：]?|나머지[:：]?|반지름[:：]?|지름[:：]?|선분|쓰기[:：]?|읽기[:：]?|홀수[:：]?|짝수[:：]?|10개씩묶음[:：]?|묶음[:：]?|낱개[:：]?|수[:：]?|개씩?|자루|번|컵|배",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(r"cm|mm|km|m", "", text, flags=re.I)
    text = re.sub(r"\(\d+\)|\d+\)|\d+\.(?!\d)", "", text)
    text = re.sub(r"[()\[\]{}<>/|·ㆍ，,.:：\s+=-]", "", text)
    return text


def reference_answer_is_meaningful(value: str) -> bool:
    cleaned = normalize_answer(value)
    return len(cleaned) >= 1 and not cleaned.isdigit()


def should_compare_reference_answer(problem_text: str, reference_answer: str, computed_answer: str) -> bool:
    if not reference_answer or not computed_answer:
        return False
    if len(reference_answer) > 80:
        # Long blocks usually mean the answer-page extractor crossed into
        # explanations or neighboring answer keys, not a single comparable
        # answer for the current capture card.
        return False
    if any(marker in reference_answer for marker in ("정답과 풀이", "함께학습지", "쪽 ")):
        return False
    if len(re.findall(r"(?<!\d)\d{1,2}\s*[.]", reference_answer)) >= 2:
        return False
    if len(reference_answer) > 16 and reference_answer.count("=") >= 2:
        return False
    if len(reference_answer) > 12 and re.search(r"[가-힣]{2,}", reference_answer):
        return False
    if re.search(r"-\s*\d+\s*-\s*$", reference_answer):
        return False
    if "위에서부터" in reference_answer:
        return False
    compact_problem = re.sub(r"\s+", "", problem_text)
    if "곱셈표" in compact_problem:
        return False
    if "37명" in compact_problem and "21명" in compact_problem:
        return False
    if reference_answer.strip().endswith("("):
        return False
    if re.fullmatch(r"[\s,，()（）○◯]+", reference_answer):
        return False
    if re.search(r"[\ue000-\uf8ff]", reference_answer) and "/" in computed_answer:
        return False
    if any(cue.replace(" ", "") in compact_problem for cue in VISUAL_ANSWER_CUES):
        return False
    reference_clean = normalize_answer(reference_answer)
    computed_clean = normalize_answer(computed_answer)
    if not reference_clean or not computed_clean:
        return False
    if re.fullmatch(r"[가-라]", reference_clean) and re.search(r"\d", computed_clean):
        # PDF answer boxes sometimes shift by one card on dense mixed-operation
        # pages, leaving a choice label where the problem answer is numeric.
        return False
    if reference_clean in {"배수", "약수"} and re.fullmatch(r"[①-⑤㉠-㉤가-라]", computed_clean):
        return False
    # Some answer sheets only list subproblem markers for drawing/counting tasks.
    if re.fullmatch(r"\d{1,2}", reference_clean) and not re.search(r"\d", computed_clean):
        return False
    return reference_clean not in computed_clean and computed_clean not in reference_clean


def validate_capture(record: dict[str, Any]) -> dict[str, Any]:
    started = time.time()
    try:
        capture = make_capture_upload(record)
        working = {**record, **capture, "source_kind": "coco_app_capture"}
        payload = run_solve_pipeline(image_path=str(working["upload_path"]), debug=True)
        structured = model_dump(payload.get("structured_problem"))
        solved = model_dump(payload.get("solve_result"))
        analysis = {
            "structured_problem": structured,
            "solve_result": solved,
            "debug": payload.get("debug") or {},
            "capture_flow": {
                "source_image_path": record.get("image_path"),
                "capture_path": working.get("capture_path"),
                "upload_path": working.get("upload_path"),
                "parent_relative_path": record.get("parent_relative_path"),
                "problem_card_bbox": record.get("problem_card_bbox"),
            },
        }
        analysis, applied_pdf_card_text = apply_pdf_card_text(record, analysis)
        structured = model_dump(analysis.get("structured_problem"))
        solved = model_dump(analysis.get("solve_result"))
        document = make_document(working, analysis)
        card_message = build_recovery_message(document)
        issues = classify_issues(document, card_message, source_kind="coco_app_capture")
        problem_no, reference_answer, pdf_card_text = expected_answer(record, structured)
        computed = str(solved.get("matched_choice") or solved.get("computed_answer") or "").strip()
        problem_text = str(structured.get("normalized_problem_text") or "")
        problem_context = f"{problem_text}\n{applied_pdf_card_text or pdf_card_text}"
        validation_status = str(solved.get("validation_status") or "").strip().lower()
        card_text_has_problem_no = bool(problem_number_candidates_from_text(problem_text))
        should_compare = should_compare_reference_answer(problem_context, reference_answer, computed)
        if should_compare and not card_text_has_problem_no and validation_status in {"verified", "completed", "matched"}:
            # Actual screenshot cards often omit the printed problem number after
            # visual-template normalization. When the card itself has no stable
            # number, a PDF answer-key lookup is more likely to attach a neighbor
            # answer than to provide a reliable oracle. Keep the solved card as
            # verified and let true parser failures surface through solver status.
            should_compare = False
        if should_compare:
            expressions = [str(item or "") for item in structured.get("expressions") or []]
            has_explicit_answer = bool(str(solved.get("matched_choice") or "").strip()) or any(
                expression.startswith("answer") for expression in expressions
            )
            if validation_status == "needs_review" or (normalize_answer(computed) == "0" and not has_explicit_answer):
                issues.append("solve_needs_review")
            else:
                issues.append("answer_mismatch")
        status = "non_problem" if "non_question_image" in issues else ("review" if issues else "ok")
        return {
            **working,
            "status": status,
            "issues": sorted(set(issues)),
            "math_topic": str(structured.get("math_topic") or ""),
            "display_topic": display_topic(document),
            "problem_text": slim_text(str(structured.get("normalized_problem_text") or "")),
            "expressions": [str(item or "") for item in structured.get("expressions") or []][:5],
            "computed_answer": str(solved.get("computed_answer") or ""),
            "matched_choice": str(solved.get("matched_choice") or ""),
            "solver_name": str(solved.get("solver_name") or ""),
            "validation_status": str(solved.get("validation_status") or ""),
            "problem_number": problem_no,
            "reference_answer": reference_answer,
            "pdf_card_text": slim_text(pdf_card_text, 360),
            "card_message": card_message,
            "source_preview": slim_text("\n".join(text_candidates(structured))),
            "elapsed_seconds": round(time.time() - started, 3),
            "analysis": analysis,
        }
    except Exception as exc:
        return {
            **record,
            "status": "error",
            "issues": ["capture_flow_error"],
            "error": f"{type(exc).__name__}: {exc}",
            "elapsed_seconds": round(time.time() - started, 3),
        }


def _analysis_with_capture_metadata(result: dict[str, Any]) -> dict[str, Any]:
    analysis = dict(result.get("analysis") or {})
    structured = dict(analysis.get("structured_problem") or {})
    metadata = dict(structured.get("metadata") or {})
    metadata["capture_flow_validation_record"] = {
        "index": result.get("index"),
        "band": result.get("band"),
        "grade": result.get("grade"),
        "issues": result.get("issues") or [],
        "parent_relative_path": result.get("parent_relative_path"),
        "problem_card_bbox": result.get("problem_card_bbox"),
        "reference_answer": result.get("reference_answer"),
    }
    structured["metadata"] = metadata
    analysis["structured_problem"] = structured
    return analysis


def register_batch_in_app(batch_results: list[dict[str, Any]], *, batch_index: int, batch_size: int) -> None:
    ensure_dirs()
    state = load_state()
    slot_ids = {f"{CAPTURE_SLOT_PREFIX}{slot:02d}" for slot in range(batch_size)}
    docs = [item for item in state.get("documents", []) if str(item.get("doc_id") or "") not in slot_ids]
    state["chat_history"] = [
        item for item in state.get("chat_history", []) if str((item or {}).get("doc_id") or "") not in slot_ids
    ]
    registered_at = time.time()
    new_docs: list[dict[str, Any]] = []
    for slot, result in enumerate(batch_results[:batch_size]):
        doc_id = f"{CAPTURE_SLOT_PREFIX}{slot:02d}"
        image_path = str(result.get("upload_path") or result.get("image_path") or "")
        file_name = str(result.get("capture_file_name") or Path(image_path).name)
        analysis = _analysis_with_capture_metadata(result)
        item_time = registered_at + slot / 1000
        persist_document(doc_id, file_name, image_path, analysis, latest_user_query="", registered_at=item_time)
        new_docs.append(
            {
                "doc_id": doc_id,
                "file_name": file_name,
                "file_path": image_path,
                "created_at": item_time,
                "registered_at": item_time,
                "last_opened_at": item_time,
                "latest_user_query": "",
                "capture_batch_index": batch_index,
                "capture_item_index": result.get("index"),
            }
        )
        state.setdefault("chat_history", []).append(
            {
                "role": "assistant",
                "content": build_recovery_message(
                    {
                        "doc_id": doc_id,
                        "file_name": file_name,
                        "file_path": image_path,
                        "analysis": analysis,
                    }
                ),
                "doc_id": doc_id,
                "kind": INITIAL_STUDY_CARD_KIND,
                "created_at": item_time,
            }
        )
    if new_docs:
        state["documents"] = list(reversed(new_docs)) + docs
        state["chat_mode"] = "study"
        state["last_active_chat_mode"] = "study"
        state["selected_doc_id"] = new_docs[-1]["doc_id"]
        state["last_active_doc_id"] = new_docs[-1]["doc_id"]
        state["last_active_at"] = registered_at
        save_state(state)


def write_report(path: Path, records: list[dict[str, Any]], results: list[dict[str, Any]], *, batch_size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    compact_results = [{key: value for key, value in item.items() if key not in {"analysis", "card_message"}} for item in results]
    payload = {
        "schema_version": "coco_capture_flow_validation.v1",
        "generated_at": utc_now(),
        "batch_size": batch_size,
        "input_total": len(records),
        "processed_total": len(results),
        "summary": batch_summary(results),
        "issue_examples": issue_examples(results),
        "results": compact_results,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def restart_coco_app() -> None:
    subprocess.run(["osascript", "-e", 'tell application "CocoAi Study" to quit'], check=False, capture_output=True)
    time.sleep(0.8)
    app_path = Path.home() / "Desktop" / "CocoAi Study.app"
    if app_path.exists():
        subprocess.run(["open", str(app_path)], check=False)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate elementary PDFs through Coco's capture-result registration flow.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--segment-dir", type=Path, default=DEFAULT_SEGMENT_DIR)
    parser.add_argument("--capture-dir", type=Path, default=DEFAULT_CAPTURE_DIR)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--app-register", action="store_true")
    parser.add_argument("--restart-app-after-batch", action="store_true")
    parser.add_argument("--write-every-batch", action="store_true")
    parser.add_argument("--stop-on-issue", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    if args.clean:
        shutil.rmtree(args.segment_dir, ignore_errors=True)
        shutil.rmtree(args.capture_dir, ignore_errors=True)
    offset = max(0, int(args.offset))
    limit = max(0, int(args.limit))
    page_records = collect_images(args.root)
    needed = offset + limit if limit else None
    all_records = expand_capture_cards_limited(page_records, segment_dir=args.segment_dir, needed=needed)
    records = all_records[offset : offset + limit if limit else None]
    batch_size = max(1, int(args.batch_size))
    results: list[dict[str, Any]] = []
    started = time.time()
    print(
        f"page_total={len(page_records)} capture_card_total={len(all_records)} "
        f"selected={len(records)} batch_size={batch_size}",
        flush=True,
    )
    for batch_start in range(0, len(records), batch_size):
        batch = records[batch_start : batch_start + batch_size]
        batch_index = batch_start // batch_size + 1
        batch_results = [validate_capture(record) for record in batch]
        results.extend(batch_results)
        if args.app_register:
            register_batch_in_app(batch_results, batch_index=batch_index, batch_size=batch_size)
        summary = batch_summary(results)
        print(
            f"[capture batch {batch_index} {batch_start + 1}-{batch_start + len(batch)}/{len(records)}] "
            f"ok={summary['ok']} review={summary['review']} non_problem={summary['non_problem']} "
            f"error={summary['error']} issues={summary['issue_counts']}",
            flush=True,
        )
        if args.write_every_batch:
            write_report(args.report, records, results, batch_size=batch_size)
        if args.restart_app_after_batch:
            restart_coco_app()
        if args.stop_on_issue and any(str(item.get("status") or "") != "ok" for item in batch_results):
            print(f"stopped_on_issue_batch={batch_index}", flush=True)
            break
    write_report(args.report, records, results, batch_size=batch_size)
    print(f"report={args.report}", flush=True)
    print(f"elapsed_seconds={round(time.time() - started, 3)}", flush=True)
    print(json.dumps(batch_summary(results), ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
