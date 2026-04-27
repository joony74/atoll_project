from __future__ import annotations

import base64
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from app.chat.context_packet import build_study_chat_context_packet as _build_study_chat_context_packet
from app.chat.internal_search import build_internal_search_panel as _build_internal_search_panel
from app.chat.internal_search import parse_internal_search_command as _parse_internal_search_command
from app.chat.llm_slot import maybe_generate_chat_reply as _maybe_generate_chat_reply
from app.chat.llm_slot import warmup_chat_llm as _warmup_chat_llm
from app.chat.orchestrator import build_main_chat_reply as _build_main_chat_reply
from app.chat.practice_image import render_practice_problem_image as _render_practice_problem_image
from app.chat.recovery_card import build_recovery_message as _build_recovery_card_message
from app.chat.recovery_card import display_problem_text as _display_problem_text
from app.chat.study_fast_reply import build_fast_study_reply as _build_fast_study_reply
from app.chat.state import (
    APP_SUPPORT_DIR,
    DOCS_DIR,
    STATE_PATH,
    UPLOADS_DIR,
    active_chat_mode as _active_chat_mode,
    append_main_message as _append_main_message,
    append_message as _append_message,
    clear_active_chat_history as _clear_active_chat_history,
    delete_document as _delete_document,
    ensure_dirs as _ensure_dirs,
    INITIAL_STUDY_CARD_KIND,
    INITIAL_STUDY_CARD_PREFIX,
    load_all_documents as _load_all_documents,
    load_document as _load_document,
    load_state as _load_state,
    mark_active_target as _mark_active_target,
    persist_document as _persist_document,
    promote_document as _promote_document,
    restore_recent_target as _restore_recent_target,
    save_state as _save_state,
    sync_documents as _sync_documents,
)
from app.chat.ui import (
    render_conversation as _render_conversation,
    scroll_chat_to_latest as _scroll_chat_to_latest,
)
from app.engines.parser.school_math_taxonomy import topic_label as _school_topic_label
from app.core.multi_problem_segmenter import save_problem_card_images as _save_problem_card_images
from app.learning_engine import (
    format_learning_engine_status as _format_learning_engine_status,
    generate_learning_problem_record as _generate_learning_problem_record,
    normalize_learning_request as _normalize_learning_request,
    recommend_problem_candidates as _recommend_learning_problems,
)
from app.problem_bank.chat_commands import (
    format_problem_bank_help as _format_problem_bank_help,
    format_problem_bank_search_results as _format_problem_bank_search_results,
    parse_problem_bank_command as _parse_problem_bank_command,
    resolve_problem_bank_selection as _resolve_problem_bank_selection,
)
from app.problem_bank.repository import (
    ProblemBankError as _ProblemBankError,
    list_banks as _list_problem_banks,
    load_problem as _load_problem_bank_problem,
    record_to_document as _problem_bank_record_to_document,
)


LOGO_PATH = Path(__file__).resolve().parent / "assets" / "cocoai.svg"
DEFAULT_USER_PROMPT = "뭐야?"
PROMPT_PLACEHOLDER = "자료가 없어도 괜찮아요. 수학 개념이나 문제를 그대로 물어보세요."
APP_VERSION = str(os.getenv("COCO_APP_VERSION") or "1.0.0").strip() or "1.0.0"
CHECK_FAULTS_PATH = APP_SUPPORT_DIR / "check_faults.json"
CAPTURES_DIR = APP_SUPPORT_DIR / "captures"
PRACTICE_IMAGES_DIR = APP_SUPPORT_DIR / "generated_practice_images"
OLLAMA_BIN_CANDIDATES = (
    "/opt/homebrew/bin/ollama",
    "/usr/local/bin/ollama",
    "/Applications/Ollama.app/Contents/Resources/ollama",
)
DRAG_UPLOAD_TYPES = ("png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff", "pdf")
CAPTURE_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
BROKEN_FRACTIONAL_POWER_DISPLAY_RE = re.compile(r"\d+\s*[\*\?]\s*[xX*]\s*\d+\s*[°º?\*]")
SIMILAR_PROBLEM_PROMPT_RE = re.compile(r"다른\s*문제|비슷한\s*문제|유사\s*문제|한\s*문제\s*더|새\s*문제|문제\s*더")
SEQUENCE_LOG_PRODUCT_DISPLAY_RE = re.compile(
    r"sequence_log_product\(base=(?P<base>\d+),start=(?P<start>\d+),increment=(?P<increment>-?\d+),count=(?P<count>\d+)\)"
)
UploadItem = tuple[str, str, str]
UploadResult = UploadItem | list[UploadItem]


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)) or default)
    except (TypeError, ValueError):
        return default


LOCAL_STUDY_REPLY_DELAY_SECONDS = max(0.0, _float_env("COCO_LOCAL_STUDY_REPLY_DELAY_SECONDS", 3.0))


def _set_upload_feedback(tone: str, message: str) -> None:
    st.session_state["_upload_feedback"] = {
        "tone": "success" if str(tone).strip() == "success" else "error",
        "message": str(message or "").strip(),
    }


def _upload_widget_key(name: str) -> str:
    nonce_key = f"{name}_nonce"
    nonce = int(st.session_state.get(nonce_key, 0) or 0)
    return f"{name}_{nonce}"


def _reset_upload_widgets() -> None:
    for base in ("upload_find_card",):
        nonce_key = f"{base}_nonce"
        st.session_state[nonce_key] = int(st.session_state.get(nonce_key, 0) or 0) + 1


def _save_uploaded_bytes(file_name: str, data: bytes) -> tuple[str, str, str]:
    safe_name = Path(str(file_name or "upload.png")).name or "upload.png"
    file_hash = hashlib.sha1(data).hexdigest()[:12]
    target_path = UPLOADS_DIR / f"{file_hash}_{safe_name}"
    target_path.write_bytes(data)
    return file_hash, safe_name, str(target_path)


def _render_pdf_upload_pages(pdf_path: Path, file_id: str, safe_name: str) -> list[UploadItem]:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("PDF 등록은 pdftoppm 변환 도구가 필요합니다.")

    page_dir = UPLOADS_DIR / f"{file_id}_pdf_pages"
    shutil.rmtree(page_dir, ignore_errors=True)
    page_dir.mkdir(parents=True, exist_ok=True)
    prefix = page_dir / "page"
    result = subprocess.run(
        [pdftoppm, "-png", "-r", "180", str(pdf_path), str(prefix)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(message or "PDF 페이지를 이미지로 변환하지 못했습니다.")

    def _page_number(path: Path) -> int:
        match = re.search(r"-(\d+)\.png$", path.name)
        return int(match.group(1)) if match else 0

    rendered_pages = sorted(page_dir.glob("page-*.png"), key=_page_number)
    if not rendered_pages:
        raise RuntimeError("PDF에서 변환된 페이지 이미지를 찾지 못했습니다.")

    upload_items: list[UploadItem] = []
    stem = Path(safe_name).stem or file_id
    for index, rendered_path in enumerate(rendered_pages, start=1):
        page_id = f"{file_id}_p{index:03d}"
        page_name = f"{stem}_p{index:03d}.png"
        target_path = page_dir / page_name
        if rendered_path != target_path:
            rendered_path.replace(target_path)
        upload_items.append((page_id, page_name, str(target_path)))
    return upload_items


def _save_upload_payload(file_name: str, data: bytes) -> UploadResult:
    file_id, safe_name, file_path = _save_uploaded_bytes(file_name, data)
    if Path(safe_name).suffix.lower() == ".pdf":
        return _render_pdf_upload_pages(Path(file_path), file_id, safe_name)
    return file_id, safe_name, file_path


def _save_uploaded_file(uploaded_file) -> UploadResult:
    data = uploaded_file.getvalue()
    return _save_upload_payload(str(getattr(uploaded_file, "name", "") or "upload.png"), data)


def _problem_card_uploads(file_id: str, file_name: str, file_path: str) -> list[tuple[str, str, str, dict]]:
    suffix = Path(str(file_path or "")).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
        return []
    output_dir = UPLOADS_DIR / f"{file_id}_problem_cards"
    cards = _save_problem_card_images(
        file_path,
        output_dir,
        base_name=Path(file_name).stem or file_id,
        minimum_regions=2,
    )
    if len(cards) < 2:
        shutil.rmtree(output_dir, ignore_errors=True)
        return []
    uploads: list[tuple[str, str, str, dict]] = []
    for card in cards:
        doc_id = f"{file_id}_q{card.index:02d}"
        child_name = f"{Path(file_name).stem}_문항{card.label}.png"
        uploads.append(
            (
                doc_id,
                child_name,
                card.path,
                {
                    "parent_doc_id": file_id,
                    "parent_file_name": file_name,
                    "parent_file_path": file_path,
                    "problem_card_index": card.index,
                    "problem_card_label": card.label,
                    "problem_card_bbox": list(card.bbox),
                },
            )
        )
    return uploads


def _register_uploaded_document(state: dict, file_id: str, file_name: str, file_path: str) -> int:
    registered_at = time.time()
    upload_items = _problem_card_uploads(file_id, file_name, file_path)
    if not upload_items:
        upload_items = [(file_id, file_name, file_path, {})]

    registered_doc_ids = {doc_id for doc_id, _, _, _ in upload_items}
    docs = [item for item in state.get("documents", []) if item.get("doc_id") not in registered_doc_ids]
    new_docs: list[dict] = []
    for offset, (doc_id, doc_name, doc_path, segment_metadata) in enumerate(upload_items):
        analysis = _run_analysis(doc_path)
        if segment_metadata:
            analysis["multi_problem_parent"] = segment_metadata
        item_registered_at = registered_at - offset * 0.001
        document_payload = {
            "doc_id": doc_id,
            "file_name": doc_name,
            "file_path": doc_path,
            "registered_at": item_registered_at,
            "created_at": item_registered_at,
            "latest_user_query": "",
            "analysis": analysis,
        }
        _persist_document(doc_id, doc_name, doc_path, analysis, registered_at=item_registered_at)
        new_docs.append(
            {
                "doc_id": doc_id,
                "file_name": doc_name,
                "file_path": doc_path,
                "created_at": item_registered_at,
                "registered_at": item_registered_at,
                "last_opened_at": item_registered_at,
                "latest_user_query": "",
            }
        )
        _append_message(
            state,
            "assistant",
            _build_recovery_message(document_payload),
            doc_id=doc_id,
            kind=INITIAL_STUDY_CARD_KIND,
        )
    docs = [*new_docs, *docs]
    state["documents"] = docs
    _mark_active_target(state, "study", new_docs[0]["doc_id"] if new_docs else file_id)
    return len(new_docs)


def _problem_bank_context(state: dict) -> dict:
    context = state.setdefault("main_chat_context", {})
    if not isinstance(context, dict):
        context = {}
        state["main_chat_context"] = context
    return context


def _set_problem_bank_last_results(state: dict, results: list[dict]) -> None:
    context = _problem_bank_context(state)
    stored: list[dict] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        stored_item = dict(item)
        stored_item.setdefault("bank_id", "competition_math")
        stored.append(stored_item)
    context["problem_bank_last_results"] = stored
    context["problem_bank_last_updated_at"] = time.time()


def _get_problem_bank_last_results(state: dict) -> list[dict]:
    results = _problem_bank_context(state).get("problem_bank_last_results") or []
    return [dict(item) for item in results if isinstance(item, dict)]


def _is_learning_engine_status_prompt(prompt: str) -> bool:
    compact = re.sub(r"\s+", "", str(prompt or "").strip().lower())
    return compact in {
        "학습엔진",
        "코코학습엔진",
        "학습엔진상태",
        "코코학습엔진상태",
        "문제은행상태",
    }


def _register_problem_bank_document(state: dict, document: dict) -> None:
    doc_id = str(document.get("doc_id") or "").strip()
    if not doc_id:
        raise _ProblemBankError("problem bank document id is empty")

    file_name = str(document.get("file_name") or doc_id)
    file_path = str(document.get("file_path") or "")
    analysis = document.get("analysis") or {}
    registered_at = float(document.get("registered_at") or time.time())
    latest_query = str(document.get("latest_user_query") or "")

    _persist_document(
        doc_id,
        file_name,
        file_path,
        analysis,
        latest_user_query=latest_query,
        registered_at=registered_at,
    )
    docs = [item for item in state.get("documents", []) if item.get("doc_id") != doc_id]
    docs.insert(
        0,
        {
            "doc_id": doc_id,
            "file_name": file_name,
            "file_path": file_path,
            "created_at": registered_at,
            "registered_at": registered_at,
            "last_opened_at": registered_at,
            "latest_user_query": latest_query,
        },
    )
    state["documents"] = docs
    _mark_active_target(state, "study", doc_id)
    _append_message(state, "assistant", _build_problem_bank_open_message(document), doc_id=doc_id)


def _build_problem_bank_open_message(document: dict) -> str:
    analysis = document.get("analysis") or {}
    record = analysis.get("problem_bank_record") or {}
    content = record.get("content") or {}
    answer = record.get("answer") or {}
    solved = analysis.get("solve_result") or {}
    problem_text = str(content.get("problem_plain") or content.get("problem_latex") or "").strip()
    final_answer = str(answer.get("final_normalized") or answer.get("final_raw") or solved.get("computed_answer") or "").strip()

    lines = ["문제은행에서 문제를 가져왔어요.", ""]
    if problem_text:
        lines.append(f"- 문제: {_truncate_text(problem_text, 420)}")
    if final_answer:
        lines.append(f"- 저장된 정답: {final_answer}")
    intro = str(solved.get("explanation") or "").strip()
    if intro:
        lines.extend(["", intro])
    lines.append("")
    lines.append("이제 이 문제 기준으로 풀이 설명, 힌트, 변형 문제를 바로 이어갈 수 있어요.")
    return "\n".join(lines)


def _truncate_text(text: str, limit: int) -> str:
    collapsed = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: max(0, limit - 1)].rstrip() + "..."


def _build_problem_bank_chat_reply(prompt: str, state: dict) -> str | None:
    if _is_learning_engine_status_prompt(prompt):
        return _format_learning_engine_status()

    command = _parse_problem_bank_command(prompt)
    if command is None:
        return None

    try:
        if command.action == "help":
            return _format_problem_bank_help(_list_problem_banks())

        if command.action == "search":
            request = _normalize_learning_request(
                prompt,
                action="search",
                query=command.query,
                subject_slug=command.subject_slug,
                level_number=command.level_number,
                limit=5,
            )
            results = _recommend_learning_problems(request)
            _set_problem_bank_last_results(state, results)
            return _format_problem_bank_search_results(results, command)

        if command.action == "generate":
            request = _normalize_learning_request(
                prompt,
                action="generate",
                query=command.query,
                subject_slug=command.subject_slug or "arithmetic_word_problem",
                level_number=command.level_number,
            )
            record = _generate_learning_problem_record(request)
            document = _problem_bank_record_to_document(record, user_query=prompt)
            _register_problem_bank_document(state, document)
            reply = f"`{document.get('file_name')}` 새 문제를 출제해서 학습리스트에 열었어요."
            generation = ((record.get("metadata") or {}).get("generation") or {})
            if generation.get("fallback_reason"):
                reply += "\n\n현재 자동 출제 템플릿은 초등 문장제를 먼저 안정화하고 있어서, 우선 그 유형으로 열었어요."
            return reply

        if command.action == "open":
            last_results = _get_problem_bank_last_results(state)
            selected = _resolve_problem_bank_selection(command.target, last_results)
            if selected is None and ":" in command.target:
                selected = {"id": command.target, "bank_id": "competition_math"}
            if selected is None:
                return "먼저 `문제은행 검색어`로 문제를 찾은 뒤 `문제은행 열기 1`처럼 번호를 골라주세요."

            problem_id = str(selected.get("id") or "").strip()
            bank_id = str(selected.get("bank_id") or "competition_math").strip() or "competition_math"
            record = _load_problem_bank_problem(problem_id, bank_id=bank_id)
            document = _problem_bank_record_to_document(record, user_query=prompt)
            _register_problem_bank_document(state, document)
            return f"`{document.get('file_name') or problem_id}` 문제를 학습리스트에 열었어요."
    except _ProblemBankError as exc:
        return f"문제은행을 읽는 중 문제가 생겼어요: {exc}"

    return None


def _mac_screen_capture_access_granted() -> bool | None:
    if sys.platform != "darwin":
        return None
    try:
        from Quartz import CGPreflightScreenCaptureAccess

        return bool(CGPreflightScreenCaptureAccess())
    except Exception:
        return None


def _mac_screenshot_search_dirs() -> list[Path]:
    candidates: list[Path] = []
    try:
        result = subprocess.run(
            ["defaults", "read", "com.apple.screencapture", "location"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        configured = str(result.stdout or "").strip()
        if result.returncode == 0 and configured:
            candidates.append(Path(os.path.expandvars(os.path.expanduser(configured))))
    except Exception:
        pass

    home = Path.home()
    candidates.extend([home / "Desktop", home / "Downloads", home / "Pictures"])
    deduped: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen or not candidate.exists() or not candidate.is_dir():
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _snapshot_capture_image_states(search_dirs: list[Path]) -> dict[str, tuple[float, int]]:
    states: dict[str, tuple[float, int]] = {}
    for directory in search_dirs:
        try:
            for path in directory.iterdir():
                if not path.is_file() or path.suffix.lower() not in CAPTURE_IMAGE_SUFFIXES:
                    continue
                stat = path.stat()
                states[str(path)] = (float(stat.st_mtime), int(stat.st_size))
        except Exception:
            continue
    return states


def _new_capture_candidates(
    search_dirs: list[Path],
    baseline: dict[str, tuple[float, int]],
    started_at: float,
) -> list[Path]:
    candidates: list[tuple[float, Path]] = []
    for directory in search_dirs:
        try:
            for path in directory.iterdir():
                if not path.is_file() or path.suffix.lower() not in CAPTURE_IMAGE_SUFFIXES:
                    continue
                stat = path.stat()
                previous = baseline.get(str(path))
                if previous and stat.st_mtime <= previous[0] + 0.05 and stat.st_size == previous[1]:
                    continue
                if stat.st_mtime < started_at - 2 or stat.st_size <= 0:
                    continue
                candidates.append((float(stat.st_mtime), path))
        except Exception:
            continue
    return [path for _, path in sorted(candidates, key=lambda item: item[0], reverse=True)]


def _read_stable_file_bytes(path: Path, *, attempts: int = 10, interval: float = 0.15) -> bytes:
    last_size = -1
    for _ in range(max(1, attempts)):
        stat = path.stat()
        current_size = int(stat.st_size)
        if current_size > 0 and current_size == last_size:
            return path.read_bytes()
        last_size = current_size
        time.sleep(max(interval, 0.02))
    return path.read_bytes()


def _capture_with_system_screenshot_app(capture_name: str) -> tuple[str, str, str] | None:
    search_dirs = _mac_screenshot_search_dirs()
    if not search_dirs:
        _set_upload_feedback("error", "시스템 캡처 저장 위치를 찾지 못했습니다.")
        return None

    baseline = _snapshot_capture_image_states(search_dirs)
    started_at = time.time()
    screenshot_app = Path("/System/Applications/Utilities/Screenshot.app")
    open_command = ["open", str(screenshot_app)] if screenshot_app.exists() else ["open", "-a", "Screenshot"]
    try:
        result = subprocess.run(
            open_command,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception as exc:
        _set_upload_feedback("error", f"시스템 캡처 도구를 열지 못했습니다: {exc}")
        return None

    if result.returncode != 0:
        message = str(result.stderr or result.stdout or result.returncode).strip()
        _set_upload_feedback("error", f"시스템 캡처 도구를 열지 못했습니다: {message}")
        return None

    timeout = float(os.getenv("COCO_SCREENSHOT_APP_TIMEOUT", "90") or "90")
    deadline = time.time() + max(timeout, 10.0)
    while time.time() < deadline:
        candidates = _new_capture_candidates(search_dirs, baseline, started_at)
        if candidates:
            selected = candidates[0]
            try:
                data = _read_stable_file_bytes(selected)
                return _save_uploaded_bytes(capture_name, data)
            except Exception as exc:
                _set_upload_feedback("error", f"캡처 파일을 등록하지 못했습니다: {exc}")
                return None
        time.sleep(0.35)

    _set_upload_feedback("error", "시스템 캡처가 취소되었거나 저장된 캡처 파일을 찾지 못했습니다.")
    return None


def _capture_screen_selection() -> tuple[str, str, str] | None:
    if sys.platform != "darwin":
        _set_upload_feedback("error", "현재 캡처 등록은 macOS 앱 환경에서만 지원합니다.")
        return None

    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    capture_name = f"capture_{time.strftime('%Y%m%d_%H%M%S')}.png"
    capture_path = CAPTURES_DIR / capture_name
    capture_mode = str(os.getenv("COCO_CAPTURE_MODE") or "auto").strip().lower()
    access_granted = _mac_screen_capture_access_granted()
    if capture_mode in {"screenshot", "screenshot_app", "system"} or (
        capture_mode == "auto" and access_granted is not True
    ):
        _set_upload_feedback("success", "시스템 캡처 도구를 열었습니다. 캡처가 끝나면 자동 등록합니다.")
        return _capture_with_system_screenshot_app(capture_name)

    try:
        capture_bin = shutil.which("screencapture") or "/usr/sbin/screencapture"
        result = subprocess.run(
            [capture_bin, "-i", str(capture_path)],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:
        _set_upload_feedback("error", f"캡처를 시작하지 못했습니다: {exc}")
        return None

    if result.returncode != 0 or not capture_path.exists() or capture_path.stat().st_size == 0:
        if capture_path.exists():
            capture_path.unlink(missing_ok=True)
        _set_upload_feedback("error", "캡처가 취소되었거나 저장되지 않았습니다.")
        return None

    try:
        data = capture_path.read_bytes()
        file_id, file_name, file_path = _save_uploaded_bytes(capture_name, data)
        capture_path.unlink(missing_ok=True)
        return file_id, file_name, file_path
    except Exception as exc:
        capture_path.unlink(missing_ok=True)
        _set_upload_feedback("error", f"캡처 파일을 등록하지 못했습니다: {exc}")
        return None


def _choose_local_image_file() -> UploadResult | None:
    if sys.platform != "darwin":
        _set_upload_feedback("error", "현재 파일 찾기는 macOS 앱 환경에서만 지원합니다.")
        return None

    script_lines = [
        'set chosenFile to choose file with prompt "등록할 이미지 또는 PDF를 선택해주세요." of type {"public.image", "com.adobe.pdf"}',
        "POSIX path of chosenFile",
    ]
    try:
        result = subprocess.run(
            ["osascript", *sum([["-e", line] for line in script_lines], [])],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:
        _set_upload_feedback("error", f"파일 선택창을 열지 못했습니다: {exc}")
        return None

    selected_path = Path(str(result.stdout or "").strip())
    error_text = str(result.stderr or "").strip()
    if result.returncode != 0:
        if "User canceled" not in error_text and "-128" not in error_text:
            _set_upload_feedback("error", f"파일 선택창을 열지 못했습니다: {error_text or result.returncode}")
        return None

    if not selected_path.exists() or not selected_path.is_file():
        _set_upload_feedback("error", "선택한 파일을 찾지 못했습니다.")
        return None

    try:
        data = selected_path.read_bytes()
        return _save_upload_payload(selected_path.name, data)
    except Exception as exc:
        _set_upload_feedback("error", f"선택한 파일을 등록하지 못했습니다: {exc}")
        return None


def _run_analysis(file_path: str, user_query: str = "") -> dict:
    from app.core.pipeline import run_solve_pipeline

    started = time.time()
    payload = run_solve_pipeline(image_path=file_path, user_query=user_query, debug=True)
    finished = time.time()
    return {
        "analysis_started_at": started,
        "analysis_finished_at": finished,
        "structured_problem": payload["structured_problem"].model_dump(),
        "solve_result": payload["solve_result"].model_dump(),
        "debug": payload.get("debug", {}),
    }


def _schedule_main_chat_llm_warmup() -> None:
    warmup_enabled = str(os.getenv("COCO_LLM_WARMUP") or "").strip().lower() in {"1", "true", "yes", "on"}
    if not warmup_enabled:
        return
    if st.session_state.get("_main_chat_llm_warmup_started"):
        return
    st.session_state["_main_chat_llm_warmup_started"] = True

    thread = threading.Thread(
        target=_warmup_chat_llm,
        kwargs={"active_mode": "main"},
        daemon=True,
        name="coco-main-chat-llm-warmup",
    )
    thread.start()


def _logo_markup() -> str:
    if not LOGO_PATH.exists():
        return '<div class="coco-logo-fallback">COCOAI</div>'
    encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f'<img class="coco-logo-image" src="data:image/svg+xml;base64,{encoded}" alt="COCOAI 로고">'


def _truncate_label(label: str, limit: int = 22) -> str:
    text = str(label or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit - 1]}…"


def _learning_list_label(item: dict, document: dict | None = None) -> str:
    loaded = document if isinstance(document, dict) else _load_document(str(item.get("doc_id") or ""))
    problem_text = _display_problem_text(loaded) if loaded else ""
    if problem_text:
        return _truncate_label(problem_text, limit=28)
    return _truncate_label(item.get("file_name") or item.get("doc_id") or "학습 자료", limit=28)


def _status_badge(status: str) -> str:
    palette = {
        "정상": ("rgba(34,197,94,0.14)", "#7ce2a6"),
        "보강 필요": ("rgba(251,113,133,0.16)", "#f9a8b3"),
        "재설정필요": ("rgba(251,113,133,0.16)", "#f9a8b3"),
        "실패": ("rgba(248,113,113,0.18)", "#fca5a5"),
    }
    bg, fg = palette.get(status, ("rgba(148,163,184,0.18)", "#cbd5e1"))
    return (
        f'<span class="status-badge" style="background:{bg};color:{fg};">'
        f"{html.escape(status)}</span>"
    )


def _load_check_faults() -> dict[str, bool]:
    if not CHECK_FAULTS_PATH.exists():
        return {}
    try:
        payload = json.loads(CHECK_FAULTS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    normalized: dict[str, bool] = {}
    for key, value in payload.items():
        normalized[str(key).strip()] = bool(value)
    return normalized


def _set_check_fault(name: str, enabled: bool) -> None:
    CHECK_FAULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    faults = _load_check_faults()
    if enabled:
        faults[name] = True
    else:
        faults.pop(name, None)
    if faults:
        CHECK_FAULTS_PATH.write_text(json.dumps(faults, ensure_ascii=False, indent=2), encoding="utf-8")
    elif CHECK_FAULTS_PATH.exists():
        CHECK_FAULTS_PATH.unlink()


def _run_process(command: list[str], timeout: float = 6.0) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:
        return False, str(exc)
    if result.returncode == 0:
        return True, (result.stdout or "").strip()
    return False, (result.stderr or result.stdout or "").strip()


def _resolve_ollama_bin() -> str | None:
    candidates: list[Path] = []

    env_override = str(os.getenv("COCO_OLLAMA_BIN") or "").strip()
    if env_override:
        candidates.append(Path(env_override).expanduser())

    discovered = shutil.which("ollama")
    if discovered:
        candidates.append(Path(discovered))

    candidates.extend(Path(raw) for raw in OLLAMA_BIN_CANDIDATES)

    seen: set[str] = set()
    for candidate in candidates:
        expanded = candidate.expanduser()
        key = str(expanded)
        if key in seen:
            continue
        seen.add(key)
        if expanded.exists() and os.access(expanded, os.X_OK):
            return key
    return None


def _probe_storage_targets() -> tuple[bool, str]:
    targets = [APP_SUPPORT_DIR, UPLOADS_DIR, DOCS_DIR]
    for target in targets:
        if not target.exists():
            return False, f"{target.name} 폴더를 찾을 수 없습니다."
        probe = target / f".coco_check_{int(time.time() * 1000)}.tmp"
        try:
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
        except Exception as exc:
            return False, f"{target.name} 폴더에 접근할 수 없습니다: {exc}"
    return True, "앱 상태 파일과 업로드 폴더에 접근할 수 있습니다."


def _probe_session_restore() -> tuple[bool, str]:
    if not STATE_PATH.parent.exists():
        return False, "세션 저장 폴더를 찾을 수 없습니다."
    if not os.access(STATE_PATH.parent, os.W_OK):
        return False, "세션 저장 폴더에 쓰기 권한이 없습니다."
    if STATE_PATH.exists():
        try:
            json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return False, "세션 상태 파일을 다시 준비해야 합니다."
    return True, "세션 저장과 복원이 정상적으로 준비되었습니다."


def _probe_coco_engine() -> tuple[bool, str]:
    engine_bin = _resolve_ollama_bin()
    if not engine_bin:
        return False, "코코 엔진 실행 파일을 찾지 못했습니다."
    ok, detail = _run_process([engine_bin, "list"], timeout=8.0)
    if ok:
        return True, "코코 대화 엔진이 정상적으로 연결되었습니다."
    if detail:
        return False, "코코 엔진 연결이 끊어졌습니다. 재실행해주세요."
    return False, "코코 엔진을 다시 실행해야 합니다."


def _repair_storage_targets() -> tuple[bool, str]:
    try:
        _ensure_dirs()
        APP_SUPPORT_DIR.mkdir(parents=True, exist_ok=True)
        ok, detail = _probe_storage_targets()
        if ok:
            _set_check_fault("storage", False)
            return True, "저장 공간을 다시 준비했습니다."
        return False, detail
    except Exception as exc:
        return False, f"저장 공간을 다시 준비하지 못했습니다: {exc}"


def _repair_session_restore(state: dict) -> tuple[bool, str]:
    try:
        if STATE_PATH.exists():
            try:
                json.loads(STATE_PATH.read_text(encoding="utf-8"))
            except Exception:
                backup_path = STATE_PATH.with_name(f"{STATE_PATH.stem}.broken-{int(time.time())}.json")
                STATE_PATH.replace(backup_path)
        _save_state(state)
        ok, detail = _probe_session_restore()
        if ok:
            _set_check_fault("session", False)
            return True, "세션 복원을 다시 준비했습니다."
        return False, detail
    except Exception as exc:
        return False, f"세션 복원을 다시 준비하지 못했습니다: {exc}"


def _repair_coco_engine() -> tuple[bool, str]:
    engine_bin = _resolve_ollama_bin()
    if not engine_bin:
        return False, "Ollama 실행 파일을 찾지 못했습니다."
    ok, _ = _run_process([engine_bin, "list"], timeout=8.0)
    if ok:
        _set_check_fault("engine", False)
        return True, "코코 엔진이 이미 정상적으로 연결되어 있습니다."

    try:
        subprocess.Popen(
            [engine_bin, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as exc:
        return False, f"코코 엔진을 다시 실행하지 못했습니다: {exc}"

    deadline = time.time() + 12.0
    while time.time() < deadline:
        ok, _ = _run_process([engine_bin, "list"], timeout=8.0)
        if ok:
            _set_check_fault("engine", False)
            return True, "코코 엔진을 다시 연결했습니다."
        time.sleep(0.8)
    return False, "코코 엔진이 아직 응답하지 않습니다."


def _run_check_action(action_id: str, state: dict) -> tuple[bool, str]:
    if action_id == "storage":
        return _repair_storage_targets()
    if action_id == "session":
        return _repair_session_restore(state)
    if action_id == "engine":
        return _repair_coco_engine()
    return False, "아직 연결되지 않은 점검 액션입니다."


def _assistant_render_delay_seconds(answer: str) -> float:
    compact = re.sub(r"\s+", "", str(answer or ""))
    length_steps = min(12, max(len(compact) // 80, 0))
    return 0.35 + (0.05 * length_steps)


def _is_similar_problem_prompt(prompt: str) -> bool:
    normalized = re.sub(r"\s+", "", str(prompt or ""))
    return bool(normalized and SIMILAR_PROBLEM_PROMPT_RE.search(normalized))


def _latest_generated_practice_item(state: dict | None, document: dict | None) -> dict:
    if not isinstance(state, dict):
        return {}
    doc_id = str((document or {}).get("doc_id") or state.get("selected_doc_id") or "").strip()
    if not doc_id:
        return {}
    bucket = state.get("generated_practice_by_doc")
    if not isinstance(bucket, dict):
        return {}
    item = bucket.get(doc_id)
    if not isinstance(item, dict):
        return {}
    if isinstance(item.get("items"), list) and item.get("items"):
        latest = item["items"][-1]
        if isinstance(latest, dict):
            merged = dict(item)
            merged.update(latest)
            return merged
    return dict(item)


def _generated_practice_preview_path(prompt: str, state: dict | None, document: dict | None, answer: str) -> str:
    if not _is_similar_problem_prompt(prompt):
        return ""
    if "같은 풀이 기준" not in str(answer or ""):
        return ""
    item = _latest_generated_practice_item(state, document)
    rule_id = str(item.get("rule_id") or "").strip()
    problem_text = str(item.get("problem_text") or "").strip()
    if not rule_id or not problem_text:
        return ""
    if problem_text not in str(answer or ""):
        return ""
    key = str(item.get("doc_id") or (document or {}).get("doc_id") or "").strip()
    try:
        return _render_practice_problem_image(rule_id, problem_text, PRACTICE_IMAGES_DIR, key=key)
    except Exception:
        return ""


def _local_fast_study_reply_used(prompt: str, document: dict | None, answer: str, state: dict | None = None) -> bool:
    if not document or not str(answer or "").strip():
        return False
    if _is_similar_problem_prompt(prompt) and (
        "같은 풀이 기준" in str(answer)
        or "먼저 제출된 문제 풀이" in str(answer)
        or "해당 학습문제를 전부 풀었습니다" in str(answer)
    ):
        return True
    try:
        return _build_fast_study_reply(prompt, document, state=state, store_generated=False) == answer
    except Exception:
        return False


def _study_assistant_render_delay_seconds(
    prompt: str,
    document: dict | None,
    answer: str,
    state: dict | None = None,
) -> float:
    base_delay = _assistant_render_delay_seconds(answer)
    if _local_fast_study_reply_used(prompt, document, answer, state=state):
        return max(base_delay, LOCAL_STUDY_REPLY_DELAY_SECONDS)
    return base_delay


def _dedupe_text(values: list[str], limit: int = 6) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in values:
        text = str(raw or "").strip()
        if not text or text in seen:
            continue
        cleaned.append(text)
        seen.add(text)
        if len(cleaned) >= limit:
            break
    return cleaned


def _list_repr(values: list[str], limit: int = 8) -> str:
    compact = _dedupe_text(values, limit=limit)
    if not compact:
        return "[]"
    rendered = []
    for item in compact:
        item = item.replace("\n", "\\n")
        if len(item) > 64:
            item = f"{item[:61]}..."
        rendered.append(repr(item))
    suffix = ", ..." if len(values) > len(compact) else ""
    return f"[{', '.join(rendered)}{suffix}]"


def _clean_visible_candidate(value: str) -> str:
    text = str(value or "").replace("\\n", " ").replace("\\i", " ")
    sequence_match = SEQUENCE_LOG_PRODUCT_DISPLAY_RE.fullmatch(text.replace(" ", ""))
    if sequence_match:
        base = sequence_match.group("base")
        start = sequence_match.group("start")
        increment = sequence_match.group("increment")
        count = sequence_match.group("count")
        return f"a1={start}, log_{base}(a_(n+1))={increment}+log_{base}(a_n), a1*...*a{count}={base}^k"
    text = text.replace("@", " ")
    text = re.sub(r"\\[a-zA-Z]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" .,:;`'\"")
    if len(text) > 72:
        text = f"{text[:69]}..."
    return text


def _visible_candidates(values: list[str], limit: int = 3) -> list[str]:
    candidates: list[str] = []
    has_repaired_fractional_power = any("^(1/" in _clean_visible_candidate(item) for item in values)
    for raw in values:
        text = _clean_visible_candidate(raw)
        if not text:
            continue
        if has_repaired_fractional_power and BROKEN_FRACTIONAL_POWER_DISPLAY_RE.search(text):
            continue
        if re.search(r"[@\\]|(?:19|20)\d{2}", text):
            continue
        if len(text) < 3:
            continue
        if text not in candidates:
            candidates.append(text)
        if len(candidates) >= limit:
            break
    return candidates


def _topic_label(topic: str) -> str:
    label = _school_topic_label(topic)
    return f"{label} 문제" if label != "문제 유형 확인 중" and not label.endswith("문제") else label


def _extract_function_candidates(structured: dict) -> list[str]:
    expressions = [str(item or "") for item in structured.get("expressions") or []]
    raw_candidates = [str(item or "") for item in structured.get("source_text_candidates") or []]
    functionish = []
    for text in expressions + raw_candidates:
        lowered = text.lower()
        if "f(" in lowered or re.search(r"\b[xy]\s*=", lowered) or ("=" in lowered and any(var in lowered for var in ("x", "y"))):
            functionish.append(text)
    return _dedupe_text(functionish, limit=4)


def _extract_coordinate_candidates(structured: dict) -> list[str]:
    bucket = "\n".join(str(item or "") for item in (structured.get("source_text_candidates") or []))
    bucket += "\n" + "\n".join(str(item or "") for item in (structured.get("expressions") or []))
    matches = re.findall(r"\(\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*\)", bucket)
    return _dedupe_text(matches, limit=4)


def _analysis_runtime_notes(analysis: dict | None) -> list[str]:
    structured = (analysis or {}).get("structured_problem") or {}
    solved = (analysis or {}).get("solve_result") or {}
    metadata = structured.get("metadata") or {}
    ocr_debug = metadata.get("ocr_debug") or {}
    tesseract_debug = ocr_debug.get("tesseract") or {}
    vision_debug = ocr_debug.get("vision") or {}
    repair_debug = ocr_debug.get("text_repair") or {}

    notes: list[str] = []
    vision_error = str(vision_debug.get("error") or "").strip()
    if vision_debug.get("skipped"):
        notes.append("가벼운 OCR 모드로 문제를 읽었습니다.")
    elif vision_debug and not vision_debug.get("available"):
        if "404" in vision_error:
            notes.append("시각 분석 모델이 설치되지 않아 기본 OCR만 사용했습니다.")
        elif vision_error:
            notes.append("시각 분석 엔진이 응답하지 않아 기본 OCR만 사용했습니다.")
    if str(tesseract_debug.get("variant") or "").strip() == "preprocessed":
        notes.append("기본 OCR 이미지를 보정해서 다시 읽었습니다.")
    if repair_debug.get("accepted"):
        notes.append("읽힌 문제 문장을 텍스트 기준으로 한 번 더 정리했습니다.")
    if str(solved.get("validation_status") or "").strip().lower() == "failed":
        notes.append("복원된 수식이 아직 불안정해서 풀이까지 이어지지 못했습니다.")
    return _dedupe_text(notes, limit=3)


def _build_recovery_message(document: dict | None) -> str:
    return _build_recovery_card_message(document)


def _build_followup_message(document: dict | None, prompt: str, state: dict | None = None) -> str:
    if not document:
        return "파일을 먼저 올려주면 복원된 식, 문제문장, 답 후보를 이 자리에서 바로 같이 정리할게요."

    fast_reply = _build_fast_study_reply(prompt, document, state=state)
    if fast_reply:
        return fast_reply

    packet = _build_study_chat_context_packet(prompt, document=document, state=state)
    llm_reply = _maybe_generate_chat_reply(packet)
    if llm_reply:
        return llm_reply

    analysis = document.get("analysis") or {}
    structured = analysis.get("structured_problem") or {}
    solved = analysis.get("solve_result") or {}

    problem_text = str(structured.get("normalized_problem_text") or "문제 문장을 아직 또렷하게 복원하는 중이에요.").strip()
    answer = str(solved.get("matched_choice") or solved.get("computed_answer") or "정답 검증 전").strip()
    steps = [str(item or "").strip() for item in solved.get("steps") or [] if str(item or "").strip()]
    explanation = str(solved.get("explanation") or "").strip()
    if not explanation:
        explanation = "지금 복원된 정보 기준으로 보면 이렇게 정리할 수 있어요."

    lines = [
        explanation,
        "",
        f"- 인식된 문제: {problem_text}",
        f"- 현재 답 후보: {answer}",
    ]
    if steps:
        lines.append(f"- 풀이 흐름: {' / '.join(steps[:3])}")
    if prompt:
        lines.append(f"- 방금 질문: {prompt}")
    return "\n".join(lines)


def _is_search_history_message(message: dict) -> bool:
    content = str((message or {}).get("content") or "").strip()
    role = str((message or {}).get("role") or "").strip()
    if role == "user" and _parse_internal_search_command(content) is not None:
        return True
    if role == "assistant":
        if "관련 기록을 찾았어요." in content or "관련 기록을 아직 찾지 못했어요." in content:
            return "검색 대상은 현재 저장된" in content or "열기](" in content
    return False


def _prune_search_history_messages(state: dict) -> None:
    state["main_chat_history"] = [
        item for item in state.get("main_chat_history", []) if not (isinstance(item, dict) and _is_search_history_message(item))
    ]
    state["chat_history"] = [
        item for item in state.get("chat_history", []) if not (isinstance(item, dict) and _is_search_history_message(item))
    ]


def _refresh_search_panel(state: dict) -> None:
    panel = state.get("search_panel")
    if not isinstance(panel, dict):
        return
    query = str(panel.get("query") or "").strip()
    if not query:
        state.pop("search_panel", None)
        return
    refreshed = _build_internal_search_panel(f"검색: {query}", state)
    if refreshed:
        state["search_panel"] = refreshed


def _search_result_button_label(index: int, result: dict) -> str:
    target = str(result.get("target_label") or "결과 열기").strip()
    source = str(result.get("source") or "").strip()
    snippet = re.sub(r"\s+", " ", str(result.get("snippet") or "")).strip()
    label = f"{index}. {target}"
    if source:
        label += f" · {source}"
    if snippet:
        label += f" · {snippet}"
    return _truncate_label(label, limit=86)


def _render_search_panel(state: dict) -> None:
    panel = state.get("search_panel")
    if not isinstance(panel, dict):
        return

    query = str(panel.get("query") or "").strip()
    results = [item for item in panel.get("results") or [] if isinstance(item, dict)]
    count_text = f"{len(results)}개 결과" if results else "결과 없음"
    result_lines: list[str] = []
    for index, result in enumerate(results[:12], start=1):
        label = html.escape(_search_result_button_label(index, result))
        target_type = str(result.get("target_type") or "").strip()
        doc_id = str(result.get("doc_id") or "").strip()
        key_seed = hashlib.sha1(f"{query}|{index}|{target_type}|{doc_id}".encode("utf-8")).hexdigest()[:10]
        result_lines.append(
            f'<a class="search-panel-result" href="#" data-coco-search-action="{key_seed}">{label}</a>'
        )
    if not result_lines:
        result_lines.append(
            '<div class="search-panel-empty">현재 저장된 메인 채팅, 학습리스트 채팅, 분석 텍스트에서 찾지 못했습니다.</div>'
        )

    with st.container(key="search_panel"):
        st.markdown(
            (
                '<div class="search-panel-body">'
                '  <div class="search-panel-summary">'
                "    <strong>검색이 완료됐습니다.</strong>"
                f"    <span>{html.escape(query)} · {html.escape(count_text)} · 마우스를 올리면 펼쳐집니다.</span>"
                "  </div>"
                f'  <div class="search-panel-results">{"".join(result_lines)}</div>'
                '  <div class="search-panel-close-row">'
                '    <a class="search-panel-close-link" href="#" data-coco-search-action="close">닫기</a>'
                "  </div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
    with st.container(key="search_panel_actions"):
        for index, result in enumerate(results[:12], start=1):
            target_type = str(result.get("target_type") or "").strip()
            doc_id = str(result.get("doc_id") or "").strip()
            key_seed = hashlib.sha1(f"{query}|{index}|{target_type}|{doc_id}".encode("utf-8")).hexdigest()[:10]
            if st.button(f"search-action-{key_seed}", key=f"search_action_{key_seed}"):
                if target_type == "main":
                    _mark_active_target(state, "main")
                elif doc_id:
                    _mark_active_target(state, "study", doc_id)
                _save_state(state)
                st.rerun()
        if st.button("search-action-close", key="search_action_close"):
            state.pop("search_panel", None)
            _save_state(state)
            st.rerun()
    _wire_search_panel_actions()


def _wire_search_panel_actions() -> None:
    components.html(
        """
        <script>
        const root = window.parent.document;
        if (root.body && root.body.dataset.cocoSearchBridgeReady !== '1') {
          root.body.dataset.cocoSearchBridgeReady = '1';

          const findActionButton = (action) => {
            const byKey = root.querySelector(`[class*="st-key-search_action_${action}"] button`);
            if (byKey) return byKey;
            const expected = action === 'close' ? 'search-action-close' : `search-action-${action}`;
            const buttons = Array.from(root.querySelectorAll('button'));
            return buttons.find((button) => (button.textContent || '').trim() === expected) || null;
          };

          root.addEventListener('click', (event) => {
            const link = event.target && event.target.closest
              ? event.target.closest('[data-coco-search-action]')
              : null;
            if (!link) return;
            event.preventDefault();
            event.stopPropagation();
            const action = link.getAttribute('data-coco-search-action') || '';
            if (!action) return;
            const clickTarget = () => {
              const target = findActionButton(action);
              if (target) {
                target.click();
                return true;
              }
              return false;
            };
            if (!clickTarget()) {
              setTimeout(clickTarget, 80);
              setTimeout(clickTarget, 220);
            }
          }, true);
        }
        </script>
        """,
        height=0,
    )


def _render_prompt_input(state: dict) -> str | None:
    _render_search_panel(state)
    with st.container(key="floating_reset_button"):
        if st.button("↻", key="floating_reset", help="대화 초기화"):
            st.session_state["_clear_active_chat_requested"] = True
            st.rerun()
    prompt = st.chat_input(PROMPT_PLACEHOLDER, key="prompt_input")
    return str(prompt or "").strip() or None


def _clear_active_chat(state: dict) -> None:
    selected_doc_id = str(state.get("selected_doc_id") or "").strip()
    selected_document = _load_document(selected_doc_id) if selected_doc_id else None
    _clear_active_chat_history(
        state,
        initial_study_message=_build_recovery_message(selected_document) if selected_document else None,
    )


def _build_main_check_items(state: dict) -> list[dict]:
    faults = _load_check_faults()
    runtime_path = Path(sys.executable).resolve()
    runtime_ok = runtime_path.exists()
    storage_ok, storage_body = _probe_storage_targets()
    if faults.get("storage"):
        storage_ok = False
        storage_body = "저장 공간 연결이 중단되었습니다. 다시 준비해주세요."
    session_ready, session_body = _probe_session_restore()
    if faults.get("session"):
        session_ready = False
        session_body = "세션 복원 상태가 중단되었습니다. 다시 준비해주세요."
    engine_ready, engine_body = _probe_coco_engine()
    if faults.get("engine"):
        engine_ready = False
        engine_body = "코코 엔진 연결이 중단되었습니다. 재실행해주세요."
    main_history_count = sum(1 for item in state.get("main_chat_history", []) if isinstance(item, dict))

    return [
        {
            "id": "version",
            "title": "코코 버전",
            "status": "정상",
            "body": f"현재 실행 버전 {APP_VERSION}",
        },
        {
            "id": "runtime",
            "title": "코코 환경",
            "status": "정상" if runtime_ok else "실패",
            "body": (
                "코코 실행 환경이 정상적으로 준비되었습니다."
                if runtime_ok
                else "내장 런타임 경로를 다시 확인해주세요."
            ),
        },
        {
            "id": "server",
            "title": "코코 서버",
            "status": "정상",
            "body": "메인 채팅 화면이 정상적으로 열려 있습니다.",
        },
        {
            "id": "storage",
            "title": "저장 공간",
            "status": "정상" if storage_ok else "실패",
            "body": storage_body if storage_ok else storage_body,
            "action_label": None if storage_ok else "재설정",
        },
        {
            "id": "engine",
            "title": "코코 엔진",
            "status": "정상" if engine_ready else "실패",
            "body": (
                f"기본 대화 엔진 준비 완료 / 현재 대화 기록 {main_history_count}건"
                if engine_ready
                else engine_body
            ),
            "action_label": None if engine_ready else "재실행",
        },
        {
            "id": "session",
            "title": "세션 복원",
            "status": "정상" if session_ready else "실패",
            "body": session_body if session_ready else session_body,
            "action_label": None if session_ready else "재설정",
        },
    ]


def _count_debug_entries(payload: object) -> int:
    if isinstance(payload, dict):
        return len(payload)
    if isinstance(payload, (list, tuple, set)):
        return len(payload)
    return 0


def _build_study_check_items(state: dict, selected: dict | None) -> list[dict]:
    documents = _load_all_documents(state)
    stored_files = len(documents)
    selected_analysis = (selected or {}).get("analysis") or {}
    structured = selected_analysis.get("structured_problem") or {}
    solved = selected_analysis.get("solve_result") or {}
    debug_payload = selected_analysis.get("debug") or {}
    metadata = structured.get("metadata") or {}
    ocr_debug = metadata.get("ocr_debug") or {}
    tesseract_debug = ocr_debug.get("tesseract") or {}
    vision_debug = ocr_debug.get("vision") or {}
    repair_debug = ocr_debug.get("text_repair") or {}

    file_name = str((selected or {}).get("file_name") or "").strip()
    selected_doc_id = str((selected or {}).get("doc_id") or state.get("selected_doc_id") or "").strip()
    selected_chat_count = sum(
        1
        for item in state.get("chat_history", [])
        if isinstance(item, dict) and str(item.get("doc_id") or "").strip() == selected_doc_id
    )

    recognized_signals = _dedupe_text(
        [str(structured.get("normalized_problem_text") or "").strip()]
        + [str(item or "").strip() for item in structured.get("expressions") or []]
        + [str(item or "").strip() for item in structured.get("source_text_candidates") or []],
        limit=8,
    )
    try:
        recognition_confidence = float(structured.get("confidence") or 0.0)
    except Exception:
        recognition_confidence = 0.0
    recognition_ready = bool(recognized_signals) and recognition_confidence >= 0.45

    answer_value = str(solved.get("matched_choice") or solved.get("computed_answer") or "").strip()
    steps = [str(item or "").strip() for item in solved.get("steps") or [] if str(item or "").strip()]
    validation_status = str(solved.get("validation_status") or "").strip().lower()
    solution_failed = validation_status == "failed"
    solution_ready = (not solution_failed) and bool(answer_value or steps or validation_status in {"verified", "completed", "matched"})
    if solution_ready and recognized_signals:
        recognition_ready = True

    storage_ok, storage_body = _probe_storage_targets()
    session_ok, session_body = _probe_session_restore()
    storage_ready = storage_ok and session_ok

    warning_count = _count_debug_entries(debug_payload.get("warnings")) + _count_debug_entries(debug_payload.get("errors"))
    if not recognition_ready:
        warning_count += 1
    if solution_failed:
        warning_count += 1

    file_body = "현재 등록된 학습 자료가 없습니다."
    if file_name:
        file_body = f"현재 자료 {_truncate_label(file_name, limit=20)} / 저장된 자료 {stored_files}건"

    vision_missing = bool(vision_debug) and not bool(vision_debug.get("available"))
    if recognition_ready:
        recognition_body = f"문제 문장과 식 후보 {len(recognized_signals)}개를 확인했습니다."
    elif repair_debug.get("accepted"):
        recognition_body = "기본 OCR을 바탕으로 문제 문장을 다시 정리했고, 식 후보를 더 선명하게 맞추는 중입니다."
    elif vision_missing:
        recognition_body = "시각 분석 모델 연결이 없어 기본 OCR만 사용했고, 문제 문장을 더 선명하게 읽는 중입니다."
    else:
        recognition_body = "문제 문장과 식 후보를 더 선명하게 읽는 중입니다."

    if solution_ready:
        if answer_value:
            solution_body = f"현재 답 후보 {answer_value}"
        else:
            solution_body = f"풀이 단계 {len(steps)}개를 정리했습니다."
    elif validation_status == "failed" and repair_debug.get("accepted"):
        solution_body = "문제 문장은 보강했지만 계산식 확정이 더 필요해서 풀이를 계속 정리하고 있습니다."
    elif validation_status == "failed" and str(tesseract_debug.get("variant") or "").strip() == "preprocessed":
        solution_body = "OCR 보정까지 시도했지만 수식 복원이 부족해서 풀이를 확정하지 못했습니다."
    else:
        solution_body = "풀이 단서를 정리하는 중입니다."

    if selected_chat_count:
        dialogue_body = f"현재 자료 대화 {selected_chat_count}건이 이어지고 있습니다."
    else:
        dialogue_body = "등록 직후 안내 메시지를 준비했습니다."

    storage_message = "학습 파일과 세션 기록이 정상적으로 저장되고 있습니다." if storage_ready else (
        storage_body if not storage_ok else session_body
    )

    error_body = "최근 분석 오류가 없습니다." if warning_count == 0 else f"최근 확인된 분석 경고 {warning_count}건"

    return [
        {
            "id": "study_file",
            "title": "파일 등록",
            "status": "정상" if file_name else "보강 필요",
            "body": file_body,
        },
        {
            "id": "study_recognition",
            "title": "문제 인식",
            "status": "정상" if recognition_ready else "보강 필요",
            "body": recognition_body,
        },
        {
            "id": "study_solution",
            "title": "풀이 결과",
            "status": "정상" if solution_ready else "보강 필요",
            "body": solution_body,
        },
        {
            "id": "study_dialogue",
            "title": "학습 대화",
            "status": "정상",
            "body": dialogue_body,
        },
        {
            "id": "study_storage",
            "title": "저장 상태",
            "status": "정상" if storage_ready else "보강 필요",
            "body": storage_message,
        },
        {
            "id": "study_errors",
            "title": "오류 로그",
            "status": "정상" if warning_count == 0 else "보강 필요",
            "body": error_body,
        },
    ]


def _build_check_items(state: dict, selected: dict | None) -> list[dict]:
    if _active_chat_mode(state) == "main":
        return _build_main_check_items(state)
    return _build_study_check_items(state, selected)


def _build_check_panel_meta(state: dict, selected: dict | None) -> tuple[str, str]:
    if _active_chat_mode(state) == "main":
        return "코코 점검", ""

    file_name = str((selected or {}).get("file_name") or "").strip()
    if file_name:
        return "학습 점검", f"현재 자료 {_truncate_label(file_name, limit=20)}"
    return "학습 점검", "등록된 학습 자료 상태를 확인하고 있습니다."


def _render_check_panel(items: list[dict], state: dict, selected: dict | None) -> None:
    has_red_status = any(str(item.get("status") or "").strip() in {"보강 필요", "실패"} for item in items)
    summary = "재설정필요" if has_red_status else "정상"
    summary_badge = _status_badge(summary)
    feedback = st.session_state.pop("_check_panel_feedback", None)
    panel_title, panel_subtitle = _build_check_panel_meta(state, selected)
    panel_mode = "main" if _active_chat_mode(state) == "main" else "study"
    title_html = html.escape(panel_title)
    subtitle_html = html.escape(panel_subtitle)

    with st.container(key=f"check_panel_{panel_mode}"):
        with st.container(key=f"check_header_{panel_mode}"):
            head_left, head_right = st.columns([1, 0.36], gap="small")
            with head_left:
                st.markdown(f'<div class="check-panel-title">{title_html}</div>', unsafe_allow_html=True)
                if panel_subtitle:
                    st.markdown(f'<div class="check-panel-subtitle">{subtitle_html}</div>', unsafe_allow_html=True)
            with head_right:
                st.markdown(f'<div class="check-summary">{summary_badge}</div>', unsafe_allow_html=True)

        if isinstance(feedback, dict):
            tone = "success" if feedback.get("ok") else "error"
            message = html.escape(str(feedback.get("message") or ""))
            st.markdown(f'<div class="check-feedback {tone}">{message}</div>', unsafe_allow_html=True)

        for index, item in enumerate(items):
            item_id = str(item.get("id") or f"item_{index}")
            row_key = f"check_row_first_{item_id}" if index == 0 else f"check_row_{item_id}"
            title = html.escape(str(item.get("title") or ""))
            title_class = "check-title upload-check-title" if "업로드" in title else "check-title"
            badge = _status_badge(str(item.get("status") or ""))
            body = html.escape(str(item.get("body") or ""))

            with st.container(key=row_key):
                line_left, line_right = st.columns([1, 0.36], gap="small")
                with line_left:
                    st.markdown(f'<div class="{title_class}">{title}</div>', unsafe_allow_html=True)
                with line_right:
                    st.markdown(f'<div class="check-row-badge">{badge}</div>', unsafe_allow_html=True)

                st.markdown(f'<div class="check-body">{body}</div>', unsafe_allow_html=True)

                action_label = str(item.get("action_label") or "").strip()
                if action_label:
                    with st.container(key=f"check_action_{item_id}"):
                        action_left, action_right = st.columns([1, 0.38], gap="small")
                        with action_right:
                            if st.button(action_label, key=f"check_action_button_{item_id}", use_container_width=True):
                                ok, message = _run_check_action(item_id, state)
                                st.session_state["_check_panel_feedback"] = {"ok": ok, "message": message}
                                _save_state(state)
                                st.rerun()


def _render_upload_feedback() -> None:
    feedback = st.session_state.get("_upload_feedback")
    if not isinstance(feedback, dict):
        return
    message = html.escape(str(feedback.get("message") or "").strip())
    if not message:
        return
    tone = "success" if str(feedback.get("tone") or "").strip() == "success" else "error"
    st.markdown(f'<div class="upload-feedback {tone}">{message}</div>', unsafe_allow_html=True)


def _complete_upload_registration(
    state: dict,
    upload_result: UploadResult | None,
    *,
    success_message: str,
) -> bool:
    if not upload_result:
        return False

    try:
        upload_items = [upload_result] if isinstance(upload_result, tuple) else list(upload_result)
        if not upload_items:
            return False
        registered_count = 0
        for file_id, file_name, file_path in reversed(upload_items):
            registered_count += _register_uploaded_document(state, file_id, file_name, file_path)
        _save_state(state)
    except Exception as exc:
        _set_upload_feedback("error", f"이미지를 등록하지 못했습니다: {exc}")
        return False

    if registered_count > len(upload_items):
        _set_upload_feedback("success", f"{registered_count}개 문항 카드로 분리해서 등록했습니다.")
    elif len(upload_items) > 1:
        _set_upload_feedback("success", f"{registered_count}개 PDF 페이지로 등록했습니다.")
    elif registered_count > 1:
        _set_upload_feedback("success", f"{registered_count}개 문항 카드로 분리해서 등록했습니다.")
    else:
        _set_upload_feedback("success", success_message)
    return True


def _process_uploaded_file(state: dict, uploaded_file, *, success_message: str) -> None:
    if uploaded_file is None:
        return

    try:
        with st.spinner("이미지를 등록하고 있어요."):
            upload_result = _save_uploaded_file(uploaded_file)
            if _complete_upload_registration(state, upload_result, success_message=success_message):
                _reset_upload_widgets()
                st.rerun()
    except Exception as exc:
        _set_upload_feedback("error", f"파일을 등록하지 못했습니다: {exc}")
        _reset_upload_widgets()
        st.rerun()


def _run_capture_registration(state: dict) -> None:
    captured = _capture_screen_selection()
    if not captured:
        st.rerun()
        return

    with st.spinner("캡처 이미지를 등록하고 있어요."):
        if _complete_upload_registration(
            state,
            captured,
            success_message="캡처 이미지를 바로 등록했습니다.",
        ):
            _reset_upload_widgets()
            st.rerun()
    st.rerun()


def _run_browse_registration(state: dict) -> None:
    selected = _choose_local_image_file()
    if not selected:
        st.rerun()
        return

    with st.spinner("선택한 이미지를 등록하고 있어요."):
        if _complete_upload_registration(
            state,
            selected,
            success_message="선택한 이미지를 등록했습니다.",
        ):
            _reset_upload_widgets()
            st.rerun()
    st.rerun()


def _render_upload_entry(state: dict) -> None:
    st.markdown('<div class="upload-picker-helper">등록 방식을 선택해 주세요.</div>', unsafe_allow_html=True)

    capture_col, browse_col = st.columns(2, gap="small")

    with capture_col:
        with st.container(key="upload_option_capture"):
            if st.button(
                "캡처\n화면을 드래그해 바로 등록",
                key="upload_capture_trigger",
                use_container_width=True,
            ):
                _set_upload_feedback("success", "캡처할 영역을 선택해주세요.")
                st.session_state["_pending_capture_request"] = True
                st.rerun()

    with browse_col:
        with st.container(key="upload_find_card"):
            if st.button(
                "파일 선택 팝업 열기",
                key="upload_browse_trigger",
                use_container_width=False,
            ):
                _set_upload_feedback("success", "등록할 파일을 선택해주세요.")
                st.session_state["_pending_browse_request"] = True
                st.rerun()
            uploaded_file = st.file_uploader(
                "이미지 또는 PDF를 드래그해서 등록",
                type=list(DRAG_UPLOAD_TYPES),
                accept_multiple_files=False,
                key=_upload_widget_key("upload_find_card"),
                label_visibility="collapsed",
            )
    _process_uploaded_file(
        state,
        uploaded_file,
        success_message="드래그한 파일을 등록했습니다.",
    )

    _render_upload_feedback()

    if st.session_state.pop("_pending_capture_request", False):
        _run_capture_registration(state)
    if st.session_state.pop("_pending_browse_request", False):
        _run_browse_registration(state)


def _is_initial_study_card(message: dict) -> bool:
    if str(message.get("role") or "").strip() != "assistant":
        return False
    if str(message.get("kind") or "").strip() == INITIAL_STUDY_CARD_KIND:
        return True
    return str(message.get("content") or "").strip().startswith(INITIAL_STUDY_CARD_PREFIX)


def _study_card_preview_path(document: dict | None) -> str:
    path = Path(str((document or {}).get("file_path") or "")).expanduser()
    if not path.exists() or not path.is_file():
        return ""
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}:
        return ""
    return str(path)


def _attach_study_card_previews(messages: list[dict], document: dict | None) -> list[dict]:
    preview_path = _study_card_preview_path(document)
    if not preview_path:
        return messages
    doc_id = str((document or {}).get("doc_id") or "").strip()
    decorated: list[dict] = []
    for message in messages:
        item = dict(message)
        if doc_id and str(item.get("doc_id") or "").strip() not in {"", doc_id}:
            decorated.append(item)
            continue
        if _is_initial_study_card(item):
            item["preview_image_path"] = preview_path
        decorated.append(item)
    return decorated


def _conversation_from_state(state: dict) -> list[dict]:
    mode = _active_chat_mode(state)
    if mode == "main":
        history = [item for item in state.get("main_chat_history", []) if isinstance(item, dict)]
        return history[-18:]

    selected_doc_id = str(state.get("selected_doc_id") or "").strip()
    history = [
        item
        for item in state.get("chat_history", [])
        if isinstance(item, dict) and str(item.get("doc_id") or "").strip() == selected_doc_id
    ]
    document = _load_document(selected_doc_id)
    if history:
        return _attach_study_card_previews(history[-18:], document)
    if document:
        return _attach_study_card_previews(
            [
                {
                    "role": "assistant",
                    "content": _build_recovery_message(document),
                    "doc_id": selected_doc_id,
                    "kind": INITIAL_STUDY_CARD_KIND,
                }
            ],
            document,
        )
    return []


def _render_chat_body(state: dict, submitted_prompt: str | None = None) -> None:
    user_prompt = str(submitted_prompt or "").strip()
    submitted = bool(user_prompt)
    mode = _active_chat_mode(state)
    conversation_slot = st.empty()

    if submitted:
        prompt = user_prompt or DEFAULT_USER_PROMPT
        is_problem_bank_prompt = _parse_problem_bank_command(prompt) is not None
        is_learning_engine_prompt = _is_learning_engine_status_prompt(prompt)
        is_internal_search_prompt = _parse_internal_search_command(prompt) is not None
        if is_internal_search_prompt:
            search_panel = _build_internal_search_panel(prompt, state)
            _prune_search_history_messages(state)
            if search_panel:
                state["search_panel"] = search_panel
            _save_state(state)
            st.rerun()

        if mode == "main" or is_problem_bank_prompt or is_learning_engine_prompt:
            _mark_active_target(state, "main")
            _append_main_message(state, "user", prompt)
            _save_state(state)
            mode = _active_chat_mode(state)
            pending_conversation = _conversation_from_state(state) + [{"role": "assistant", "pending": True}]
            conversation_slot.markdown(_render_conversation(pending_conversation, mode=mode), unsafe_allow_html=True)
            _scroll_chat_to_latest()
            started = time.time()
            assistant_reply = (
                _build_problem_bank_chat_reply(prompt, state)
                if (is_problem_bank_prompt or is_learning_engine_prompt)
                else None
            )
            if assistant_reply is None:
                assistant_reply = _build_main_chat_reply(prompt, state=state)
            elapsed = time.time() - started
            remaining = max(_assistant_render_delay_seconds(assistant_reply) - elapsed, 0.0)
            if remaining > 0:
                time.sleep(remaining)
            _append_main_message(
                state,
                "assistant",
                assistant_reply,
            )
        else:
            selected_doc_id = str(state.get("selected_doc_id") or "").strip()
            if not selected_doc_id and state.get("documents"):
                selected_doc_id = str(state["documents"][0].get("doc_id") or "").strip()

            selected_doc_id = selected_doc_id or None
            selected_document = _load_document(selected_doc_id)

            if selected_doc_id:
                _mark_active_target(state, "study", selected_doc_id)
                for item in state.get("documents", []):
                    if item.get("doc_id") == selected_doc_id:
                        item["latest_user_query"] = prompt
                        break
                _promote_document(state, selected_doc_id)

            _append_message(state, "user", prompt, doc_id=selected_doc_id)
            _save_state(state)
            pending_conversation = _conversation_from_state(state) + [{"role": "assistant", "pending": True}]
            conversation_slot.markdown(_render_conversation(pending_conversation, mode=mode), unsafe_allow_html=True)
            _scroll_chat_to_latest()
            started = time.time()
            assistant_reply = _build_followup_message(selected_document, prompt, state=state)
            elapsed = time.time() - started
            remaining = max(
                _study_assistant_render_delay_seconds(prompt, selected_document, assistant_reply, state=state) - elapsed,
                0.0,
            )
            if remaining > 0:
                time.sleep(remaining)
            generated_preview_path = _generated_practice_preview_path(prompt, state, selected_document, assistant_reply)
            _append_message(
                state,
                "assistant",
                assistant_reply,
                doc_id=selected_doc_id,
                preview_image_path=generated_preview_path,
                preview_image_label="문제 그림" if generated_preview_path else None,
            )

            if selected_document:
                selected_document["latest_user_query"] = prompt
                _persist_document(
                    selected_document["doc_id"],
                    selected_document["file_name"],
                    selected_document["file_path"],
                    selected_document["analysis"],
                    latest_user_query=prompt,
                )
        _save_state(state)
        mode = _active_chat_mode(state)

    conversation = _conversation_from_state(state)
    conversation_slot.markdown(_render_conversation(conversation, mode=mode), unsafe_allow_html=True)
    _scroll_chat_to_latest()


def _inject_css() -> None:
    logo_button_bg = "transparent"
    if LOGO_PATH.exists():
        encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
        logo_button_bg = (
            "url(\"data:image/svg+xml;base64,"
            + encoded
            + "\") left center / contain no-repeat transparent"
        )
    css = """
        <style>
        :root {
          --sidebar-bg: #272934;
          --sidebar-border: #393c48;
          --panel-bg: #1b1d24;
          --panel-border: rgba(255, 255, 255, 0.09);
          --text-main: #e5e7eb;
          --text-muted: #aeb5c4;
          --main-bg: #f5f7fb;
          --assistant-border: #d7e0ea;
          --input-bg: #2a2d37;
          --coco-chat-shell-height: calc(100dvh - 150px);
          --coco-chat-scroll-clearance: 96px;
          --coco-chat-body-side-space: 75px;
        }

        html, body, [class*="css"] {
          font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Apple SD Gothic Neo", "Pretendard", sans-serif;
        }

        html,
        body {
          background: var(--main-bg) !important;
        }

        #MainMenu, footer, header[data-testid="stHeader"] {
          display: none !important;
        }

        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"],
        button[title="Close sidebar"],
        button[title="Open sidebar"],
        button[aria-label="Close sidebar"],
        button[aria-label="Open sidebar"] {
          display: none !important;
          visibility: hidden !important;
          width: 0 !important;
          height: 0 !important;
        }

        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > div,
        [data-testid="stMain"],
        [data-testid="stMain"] > div,
        [data-testid="stMain"] section,
        [data-testid="stMainBlockContainer"] {
          background: var(--main-bg) !important;
        }

        [data-testid="stSidebar"] {
          min-width: 310px !important;
          max-width: 310px !important;
          background: linear-gradient(180deg, #2a2c37 0%, #1f2129 100%);
          border-right: 1px solid var(--sidebar-border);
        }

        [data-testid="stSidebar"] > div:first-child {
          background: transparent;
        }

        [data-testid="stSidebarHeader"],
        [data-testid="stSidebarNav"] {
          display: none !important;
          height: 0 !important;
          min-height: 0 !important;
          padding: 0 !important;
          margin: 0 !important;
        }

        [data-testid="stSidebarContent"] {
          padding: 0 18px 28px;
          display: flex;
          flex-direction: column;
          justify-content: flex-start !important;
          align-items: stretch;
          height: 100vh;
          overflow-y: auto;
        }

        [data-testid="stSidebarUserContent"] {
          width: 100%;
          flex: 1 1 auto;
          align-self: flex-start;
          padding-top: 0 !important;
          margin-top: 0 !important;
        }

        [data-testid="stSidebarUserContent"] > div:first-child {
          gap: 0.55rem;
          justify-content: flex-start;
          align-content: flex-start;
          padding-top: 0 !important;
          margin-top: 0 !important;
        }

        [data-testid="stMainBlockContainer"] {
          max-width: none;
          height: 100vh;
          padding: 30px 34px 148px;
          overflow: hidden;
          box-sizing: border-box;
        }

        [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {
          gap: 0 !important;
          row-gap: 0 !important;
        }

        .sidebar-head {
          display: flex;
          align-items: flex-start;
          justify-content: flex-start;
          gap: 0;
          margin-top: 0;
          margin-bottom: 12px;
        }

        .logo-home-link {
          display: block;
          line-height: 0;
          text-decoration: none;
        }

        .st-key-logo_home_button [data-testid="stButton"] {
          margin: 0 !important;
          width: 169px !important;
        }

        .st-key-logo_home_button [data-testid="stButton"] button {
          width: 169px !important;
          min-width: 169px !important;
          max-width: 169px !important;
          height: 54px !important;
          min-height: 54px !important;
          padding: 0 !important;
          margin: 0 !important;
          border: 0 !important;
          border-radius: 0 !important;
          background: __LOGO_BUTTON_BG__ !important;
          box-shadow: none !important;
        }

        .st-key-logo_home_button [data-testid="stButton"] button:hover,
        .st-key-logo_home_button [data-testid="stButton"] button:focus,
        .st-key-logo_home_button [data-testid="stButton"] button:active {
          border: 0 !important;
          background: __LOGO_BUTTON_BG__ !important;
          box-shadow: none !important;
          transform: none !important;
        }

        .st-key-logo_home_button [data-testid="stButton"] button p {
          opacity: 0 !important;
          font-size: 0 !important;
          line-height: 0 !important;
          margin: 0 !important;
        }

        .coco-logo-image {
          display: block;
          width: 169px;
          max-width: 100%;
          height: auto;
          margin-top: 0;
        }

        .coco-logo-fallback {
          font-size: 2.85rem;
          line-height: 0.95;
          font-weight: 900;
          letter-spacing: -0.08em;
          color: #ffb067;
        }

        .upload-picker-helper {
          color: #9ca8bf;
          font-size: 12px;
          line-height: 1.45;
          margin: 2px 4px 10px;
        }

        [data-testid="stSidebar"] [class*="st-key-upload_option_capture"] [data-testid="stButton"] {
          margin: 0 !important;
        }

        [data-testid="stSidebar"] [class*="st-key-upload_option_capture"] [data-testid="stButton"] button {
          min-height: 58px !important;
          height: 58px !important;
          width: 100% !important;
          padding: 0 !important;
          border-radius: 14px !important;
          border: 1px solid rgba(117, 126, 151, 0.34) !important;
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.025) 100%) !important;
          box-shadow: none !important;
          justify-content: center !important;
          align-items: center !important;
          text-align: center !important;
          position: relative !important;
          overflow: hidden !important;
        }

        [data-testid="stSidebar"] [class*="st-key-upload_option_capture"] [data-testid="stButton"] button:hover,
        [data-testid="stSidebar"] [class*="st-key-upload_option_capture"] [data-testid="stButton"] button:focus,
        [data-testid="stSidebar"] [class*="st-key-upload_option_capture"] [data-testid="stButton"] button:active {
          border: 1px solid rgba(143, 156, 185, 0.54) !important;
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.04) 100%) !important;
          box-shadow: none !important;
        }

        [data-testid="stSidebar"] [class*="st-key-upload_option_capture"] [data-testid="stButton"] button::before {
          content: "";
          position: absolute;
          top: 50%;
          left: 50%;
          width: 24px;
          height: 24px;
          transform: translate(-50%, -50%);
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='26' height='26' viewBox='0 0 26 26' fill='none'%3E%3Cpath d='M9.2 7.4L10.5 5.8C10.8 5.43 11.25 5.2 11.73 5.2H14.27C14.75 5.2 15.2 5.43 15.5 5.8L16.8 7.4H19.15C20.34 7.4 21.3 8.36 21.3 9.55V17.45C21.3 18.64 20.34 19.6 19.15 19.6H6.85C5.66 19.6 4.7 18.64 4.7 17.45V9.55C4.7 8.36 5.66 7.4 6.85 7.4H9.2Z' stroke='%23EDF2FF' stroke-width='1.55' stroke-linejoin='round'/%3E%3Ccircle cx='13' cy='13.5' r='3.55' stroke='%23EDF2FF' stroke-width='1.55'/%3E%3Ccircle cx='18.25' cy='10.55' r='0.78' fill='%23EDF2FF'/%3E%3C/svg%3E");
          background-position: center;
          background-repeat: no-repeat;
          background-size: contain;
          pointer-events: none;
        }

        [data-testid="stSidebar"] [class*="st-key-upload_option_capture"] [data-testid="stButton"] button > div,
        [data-testid="stSidebar"] [class*="st-key-upload_option_capture"] [data-testid="stButton"] button [data-testid="stMarkdownContainer"] {
          width: 100% !important;
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
          text-align: center !important;
          margin: 0 !important;
          padding: 0 !important;
        }

        [data-testid="stSidebar"] [class*="st-key-upload_option_capture"] [data-testid="stButton"] button p,
        [data-testid="stSidebar"] [class*="st-key-upload_option_capture"] [data-testid="stButton"] button span {
          color: transparent !important;
          font-size: 0 !important;
          line-height: 0 !important;
          font-weight: 400 !important;
          text-align: center !important;
          white-space: nowrap !important;
        }

        .upload-feedback {
          margin: 6px 0 4px !important;
          padding: 7px 10px !important;
          min-height: 32px !important;
          border-radius: 12px !important;
          font-size: 12px !important;
          line-height: 1.35 !important;
          border: 1px solid transparent !important;
          box-sizing: border-box !important;
        }

        .upload-feedback.success {
          background: rgba(34, 197, 94, 0.12) !important;
          border-color: rgba(74, 222, 128, 0.22) !important;
          color: #9ae6b4 !important;
        }

        .upload-feedback.error {
          background: rgba(248, 113, 113, 0.14) !important;
          border-color: rgba(252, 165, 165, 0.24) !important;
          color: #fecaca !important;
        }

        [data-testid="stSidebar"] [data-testid="stSpinner"] {
          margin: 6px 0 4px !important;
          padding: 0 !important;
          min-height: 32px !important;
          height: 32px !important;
          display: flex !important;
          align-items: center !important;
          overflow: hidden !important;
        }

        [data-testid="stSidebar"] [data-testid="stSpinner"] > div {
          min-height: 32px !important;
          height: 32px !important;
          display: flex !important;
          align-items: center !important;
          gap: 8px !important;
        }

        [data-testid="stSidebar"] [data-testid="stSpinner"] p,
        [data-testid="stSidebar"] [data-testid="stSpinner"] span {
          margin: 0 !important;
          padding: 0 !important;
          font-size: 12px !important;
          line-height: 1.35 !important;
        }

        [data-testid="stFileUploader"] {
          margin: 0 0 5px !important;
          padding: 0 !important;
          border: 0 !important;
          background: transparent !important;
          box-sizing: border-box;
        }

        [data-testid="stFileUploader"] > div {
          margin: 0 !important;
          padding: 0 !important;
          width: 100% !important;
          min-height: 0 !important;
          height: auto !important;
          border: 0 !important;
          background: transparent !important;
          box-sizing: border-box;
        }

        [data-testid="stFileUploader"] label,
        [data-testid="stFileUploader"] [data-testid="stWidgetLabel"] {
          margin: 0 !important;
          padding: 0 !important;
          min-height: 0 !important;
          height: 0 !important;
        }

        [data-testid="stSidebar"] [class*="st-key-upload_find_card"] [data-testid="stFileUploaderDropzone"] {
          min-height: 58px !important;
          height: 58px !important;
          border-radius: 14px !important;
          border: 1px solid rgba(117, 126, 151, 0.34) !important;
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.025) 100%) !important;
        }

        [data-testid="stSidebar"] [class*="st-key-upload_find_card"] {
          position: relative;
        }

        [data-testid="stSidebar"] [class*="st-key-upload_browse_trigger"] {
          position: absolute !important;
          top: 50% !important;
          left: 50% !important;
          width: 44px !important;
          height: 44px !important;
          min-height: 44px !important;
          transform: translate(-50%, -50%) !important;
          z-index: 6 !important;
          margin: 0 !important;
          padding: 0 !important;
        }

        [data-testid="stSidebar"] [class*="st-key-upload_browse_trigger"] [data-testid="stButton"],
        [data-testid="stSidebar"] [class*="st-key-upload_browse_trigger"] [data-testid="stButton"] > div,
        [data-testid="stSidebar"] [class*="st-key-upload_browse_trigger"] button {
          width: 44px !important;
          height: 44px !important;
          min-height: 44px !important;
          margin: 0 !important;
          padding: 0 !important;
        }

        [data-testid="stSidebar"] [class*="st-key-upload_browse_trigger"] button {
          border: 0 !important;
          background: transparent !important;
          color: transparent !important;
          box-shadow: none !important;
          opacity: 0 !important;
          cursor: pointer !important;
        }

        [data-testid="stSidebar"] [class*="st-key-upload_find_card"] [data-testid="stFileUploaderDropzone"]:hover,
        [data-testid="stSidebar"] [class*="st-key-upload_find_card"] [data-testid="stFileUploaderDropzone"]:focus,
        [data-testid="stSidebar"] [class*="st-key-upload_find_card"] [data-testid="stFileUploaderDropzone"]:active {
          border: 1px solid rgba(143, 156, 185, 0.54) !important;
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.04) 100%) !important;
        }

        [data-testid="stSidebar"] [class*="st-key-upload_find_card"] [data-testid="stFileUploaderDropzone"] section,
        [data-testid="stSidebar"] [class*="st-key-upload_find_card"] [data-testid="stFileUploaderDropzone"] > div,
        [data-testid="stSidebar"] [class*="st-key-upload_find_card"] [data-testid="stFileUploaderDropzone"] section > div,
        [data-testid="stSidebar"] [class*="st-key-upload_find_card"] [data-testid="stFileUploaderDropzone"] section > div > div {
          min-height: 58px !important;
          height: 58px !important;
        }

        [data-testid="stSidebar"] [class*="st-key-upload_find_card"] [data-testid="stFileUploaderDropzone"]::before {
          content: "";
          position: absolute;
          top: 50%;
          left: 50%;
          width: 24px;
          height: 24px;
          transform: translate(-50%, -50%);
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='26' height='26' viewBox='0 0 26 26' fill='none'%3E%3Cpath d='M13 6.6V15.5' stroke='%23EDF2FF' stroke-width='1.55' stroke-linecap='round' stroke-linejoin='round'/%3E%3Cpath d='M8.9 10.7L13 6.6L17.1 10.7' stroke='%23EDF2FF' stroke-width='1.55' stroke-linecap='round' stroke-linejoin='round'/%3E%3Cpath d='M7.35 18.15V18.85C7.35 19.72 8.06 20.45 8.95 20.45H17.05C17.94 20.45 18.65 19.72 18.65 18.85V18.15' stroke='%23EDF2FF' stroke-width='1.55' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
          background-position: center;
          background-repeat: no-repeat;
          background-size: contain;
          color: #edf2ff;
          pointer-events: none;
        }

        [data-testid="stSidebar"] [class*="st-key-upload_find_card"] [data-testid="stFileUploaderDropzone"]::after {
          content: none;
        }

        [data-testid="stFileUploaderDropzone"] {
          min-height: 50px !important;
          height: 50px !important;
          width: 100% !important;
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
          border-radius: 14px;
          border: 1px solid #4b4f5f !important;
          background: rgba(255, 255, 255, 0.03) !important;
          margin: 0 !important;
          padding: 0 !important;
          position: relative;
          overflow: hidden;
          box-sizing: border-box;
        }

        [data-testid="stFileUploaderDropzone"] section {
          margin: 0 !important;
          padding: 0 !important;
          min-height: 50px !important;
          width: 100% !important;
          height: 100% !important;
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
          border: 0 !important;
          background: transparent !important;
          box-sizing: border-box;
        }

        [data-testid="stFileUploaderDropzone"] > div {
          min-height: 50px !important;
          width: 100% !important;
          height: 100% !important;
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
          margin: 0 !important;
          padding: 0 !important;
          border: 0 !important;
          background: transparent !important;
          box-sizing: border-box;
        }

        [data-testid="stFileUploaderDropzone"] section > div,
        [data-testid="stFileUploaderDropzone"] section > div > div {
          width: 100% !important;
          height: 100% !important;
          min-height: 50px !important;
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
          margin: 0 !important;
          padding: 0 !important;
          border: 0 !important;
          background: transparent !important;
          box-sizing: border-box;
        }

        [data-testid="stFileUploaderDropzone"] * {
          margin: 0 !important;
          padding: 0 !important;
        }

        [data-testid="stFileUploaderDropzone"] svg,
        [data-testid="stFileUploaderDropzone"] small {
          display: none !important;
        }

        [data-testid="stFileUploaderDropzone"] button {
          position: absolute !important;
          inset: 0 !important;
          z-index: 2 !important;
          display: block !important;
          width: 100% !important;
          height: 100% !important;
          min-height: 100% !important;
          border: 0 !important;
          opacity: 0 !important;
          background: transparent !important;
          cursor: pointer !important;
        }

        [data-testid="stFileUploaderDropzone"] p,
        [data-testid="stFileUploaderDropzone"] span {
          display: none !important;
        }

        [data-testid="stFileUploaderDropzone"]::before {
          content: "";
          position: absolute;
          top: 50%;
          left: 50%;
          width: 24px;
          height: 24px;
          transform: translate(-50%, -50%);
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='26' height='26' viewBox='0 0 26 26' fill='none'%3E%3Cpath d='M13 6.6V15.5' stroke='%23EDF2FF' stroke-width='1.55' stroke-linecap='round' stroke-linejoin='round'/%3E%3Cpath d='M8.9 10.7L13 6.6L17.1 10.7' stroke='%23EDF2FF' stroke-width='1.55' stroke-linecap='round' stroke-linejoin='round'/%3E%3Cpath d='M7.35 18.15V18.85C7.35 19.72 8.06 20.45 8.95 20.45H17.05C17.94 20.45 18.65 19.72 18.65 18.85V18.15' stroke='%23EDF2FF' stroke-width='1.55' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
          background-position: center;
          background-repeat: no-repeat;
          background-size: contain;
          outline: 0 !important;
          background-color: transparent !important;
          box-sizing: border-box;
          pointer-events: none;
        }

        .sidebar-section-title {
          color: #9ca8bf;
          font-size: 1.55rem;
          font-weight: 800;
          letter-spacing: -0.03em;
          margin: 18px 4px 10px;
        }

        .sidebar-section-title.learning-list-title {
          font-size: 14px;
          font-weight: 400;
          padding-left: 1em;
          margin: 9px 4px 10px 0;
        }

        [data-testid="stSidebar"] [data-testid="stButton"] button {
          min-height: 40px !important;
          height: 40px !important;
          border-radius: 14px;
          font-size: 12px !important;
          font-weight: 700;
          box-shadow: none;
          transition: all 0.18s ease;
        }

        [data-testid="stSidebar"] [data-testid="stButton"] button p,
        [data-testid="stSidebar"] [data-testid="stButton"] button span {
          font-size: 12px !important;
          line-height: 1 !important;
        }

        [class*="st-key-doc_select_"] [data-testid="stButton"] button {
          display: flex !important;
          align-items: center !important;
          min-height: 40px !important;
          height: 40px !important;
          justify-content: flex-start !important;
          padding: 0 16px 0 22px !important;
          text-align: left !important;
          font-size: 14px !important;
          position: relative !important;
        }

        [class*="st-key-doc_select_"] [data-testid="stButton"] button > div,
        [class*="st-key-doc_select_"] [data-testid="stButton"] button [data-testid="stMarkdownContainer"] {
          width: 100% !important;
          display: flex !important;
          align-items: center !important;
          justify-content: flex-start !important;
          text-align: left !important;
          margin: 0 !important;
          padding: 0 !important;
        }

        [class*="st-key-doc_select_"] [data-testid="stButton"] button p,
        [class*="st-key-doc_select_"] [data-testid="stButton"] button span {
          width: 100% !important;
          font-size: 14px !important;
          line-height: 1 !important;
          text-align: left !important;
          margin: 0 !important;
        }

        [class*="st-key-doc_select_inactive_"] [data-testid="stButton"] button {
          background: rgba(255, 255, 255, 0.04) !important;
          border: 1px solid #4c5060 !important;
          color: #b4bccb !important;
          box-shadow: inset 5px 0 0 #4b505d !important;
          font-weight: 400 !important;
        }

        [class*="st-key-doc_select_active_"] [data-testid="stButton"] button {
          background: #f3f7ff !important;
          border: 1px solid #3b82f6 !important;
          color: #172033 !important;
          box-shadow: inset 5px 0 0 #3b82f6 !important;
          font-weight: 700 !important;
        }

        [class*="st-key-doc_select_inactive_"] [data-testid="stButton"] button p,
        [class*="st-key-doc_select_inactive_"] [data-testid="stButton"] button span {
          font-weight: 400 !important;
          color: #b4bccb !important;
        }

        [class*="st-key-doc_select_active_"] [data-testid="stButton"] button p,
        [class*="st-key-doc_select_active_"] [data-testid="stButton"] button span {
          font-weight: 700 !important;
          color: #172033 !important;
        }

        [class*="st-key-doc_row_"] div[data-testid="stHorizontalBlock"] {
          gap: 6px !important;
          align-items: center !important;
        }

        [class*="st-key-doc_live_list"] > div,
        [class*="st-key-doc_live_list"] div[data-testid="stVerticalBlock"] {
          gap: 4px !important;
          margin: 0 !important;
          padding: 0 !important;
        }

        [class*="st-key-doc_row_"] {
          margin: 0 !important;
          padding: 0 !important;
        }

        [class*="st-key-doc_row_"] div[data-testid="column"] {
          padding: 0 !important;
          margin: 0 !important;
        }

        [class*="st-key-doc_row_"] div[data-testid="column"]:last-child {
          flex: 0 0 40px !important;
          width: 40px !important;
          min-width: 40px !important;
          max-width: 40px !important;
        }

        [class*="st-key-doc_delete_"] [data-testid="stButton"] {
          display: flex;
          justify-content: flex-start;
        }

        [class*="st-key-doc_delete_"] [data-testid="stButton"] button {
          width: 40px !important;
          min-width: 40px !important;
          max-width: 40px !important;
          min-height: 40px !important;
          height: 40px !important;
          padding: 0 !important;
          margin: 0 !important;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        [class*="st-key-doc_delete_"] [data-testid="stButton"] button p,
        [class*="st-key-doc_delete_"] [data-testid="stButton"] button span {
          font-size: 12px !important;
          line-height: 1 !important;
        }

        [data-testid="stSidebar"] button[kind="secondary"] {
          background: rgba(255, 255, 255, 0.04);
          border: 1px solid #4c5060;
          color: #b4bccb;
        }

        [data-testid="stSidebar"] button[kind="primary"] {
          background: #f3f7ff;
          border: 1px solid #3b82f6;
          color: #172033;
          box-shadow: inset 5px 0 0 #3b82f6;
        }

        [data-testid="stSidebar"] [data-testid="stButton"] button:hover {
          border-color: #6d7488;
        }

        .empty-docs {
          border: 1px dashed #4b4f5f;
          color: #97a0b4;
          border-radius: 16px;
          padding: 16px 18px;
          margin: 2px 4px 8px;
          font-size: 12px;
          font-weight: 300;
        }

        .doc-preview-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
          margin: 4px 0 6px;
        }

        .doc-preview-row {
          display: grid;
          grid-template-columns: minmax(0, 1fr) 40px;
          gap: 10px;
        }

        .doc-preview-label,
        .doc-preview-delete {
          min-height: 40px;
          border-radius: 14px;
          border: 1px solid #4c5060;
          background: rgba(255, 255, 255, 0.04);
          color: #b4bccb;
          font-size: 14px;
          font-weight: 700;
          display: flex;
          align-items: center;
        }

        .doc-preview-label {
          padding: 0 18px;
          overflow: hidden;
          white-space: nowrap;
          text-overflow: ellipsis;
        }

        .doc-preview-delete {
          justify-content: center;
          width: 40px;
          min-width: 40px;
          font-size: 12px;
        }

        .doc-preview-row.selected .doc-preview-label {
          background: #f3f7ff;
          border-color: #3b82f6;
          color: #172033;
          box-shadow: inset 5px 0 0 #3b82f6;
        }

        [class*="st-key-check_panel"] {
          margin-top: 13px;
          background: linear-gradient(180deg, #1a1c23 0%, #171920 100%);
          border: 1px solid var(--panel-border);
          border-radius: 20px;
          padding: 14px 18px 6px;
          color: white;
        }

        [class*="st-key-check_panel_main"] {
          background: linear-gradient(180deg, #19202a 0%, #171c24 100%);
          border-color: rgba(111, 135, 174, 0.2);
          box-shadow: inset 0 1px 0 rgba(182, 204, 239, 0.04);
        }

        [class*="st-key-check_panel_study"] {
          background: linear-gradient(180deg, #141518 0%, #101114 100%);
          border-color: rgba(255, 255, 255, 0.08);
          box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
        }

        [class*="st-key-check_panel"] > div {
          gap: 0 !important;
        }

        [class*="st-key-check_header"] {
          margin-bottom: 6px;
        }

        [class*="st-key-check_header"] div[data-testid="column"] {
          padding: 0 !important;
        }

        [class*="st-key-check_header"] div[data-testid="stHorizontalBlock"] {
          align-items: flex-start !important;
        }

        .check-panel-title {
          font-size: 15px;
          font-weight: 700;
          letter-spacing: -0.03em;
          line-height: 1.2;
        }

        .check-panel-subtitle {
          margin-top: 4px;
          color: rgba(255, 255, 255, 0.54);
          font-size: 11px;
          line-height: 1.4;
          font-weight: 400;
        }

        .check-summary {
          display: flex;
          width: 100%;
          align-items: flex-start;
          justify-content: flex-end;
          padding-top: 2px;
        }

        [class*="st-key-check_row_"],
        [class*="st-key-check_row_first_"] {
          padding: 12px 0;
        }

        [class*="st-key-check_row_"] {
          border-top: 1px solid rgba(255, 255, 255, 0.08);
        }

        [class*="st-key-check_row_first_"] {
          border-top: none;
        }

        [class*="st-key-check_row_"] div[data-testid="column"],
        [class*="st-key-check_row_first_"] div[data-testid="column"] {
          padding: 0 !important;
        }

        .check-title {
          font-size: 13px;
          font-weight: 700;
          line-height: 1.35;
        }

        .check-title.upload-check-title,
        .check-title.upload-check-title * {
          font-weight: 300 !important;
          font-variation-settings: "wght" 300;
        }

        .check-body {
          margin-top: 6px;
          color: rgba(255, 255, 255, 0.72);
          line-height: 1.55;
          font-size: 12px;
          font-weight: 400;
        }

        .check-row-badge {
          display: flex;
          justify-content: flex-end;
          align-items: flex-start;
        }

        .check-feedback {
          margin: 4px 0 8px;
          font-size: 11px;
          line-height: 1.45;
        }

        .check-feedback.success {
          color: #7ce2a6;
        }

        .check-feedback.error {
          color: #f9a8b3;
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          border-radius: 999px;
          min-width: 70px;
          padding: 6px 12px;
          font-size: 10px;
          font-weight: 600;
          line-height: 1;
          white-space: nowrap;
          text-align: center;
        }

        .check-summary .status-badge {
          margin-left: auto;
          min-width: 88px;
        }

        [class*="st-key-check_action_"] {
          margin-top: 8px;
        }

        [class*="st-key-check_action_"] div[data-testid="column"] {
          padding: 0 !important;
        }

        [class*="st-key-check_action_"] [data-testid="stButton"] {
          display: flex;
          justify-content: flex-end;
        }

        [class*="st-key-check_action_"] [data-testid="stButton"] button {
          min-height: 32px !important;
          height: 32px !important;
          border-radius: 999px !important;
          padding: 0 12px !important;
          font-size: 11px !important;
          font-weight: 400 !important;
        }

        .chat-shell {
            max-width: 1110px;
            margin: 0 auto;
      height: var(--coco-chat-shell-height);
      min-height: 0;
      max-height: var(--coco-chat-shell-height);
            padding-top: 0;
            padding-bottom: var(--coco-chat-scroll-clearance);
            padding-left: var(--coco-chat-body-side-space);
            padding-right: var(--coco-chat-body-side-space);
            display: flex;
            flex-direction: column-reverse;
            justify-content: flex-start;
            gap: 6px;
            overflow-y: auto;
            overscroll-behavior: contain;
            scroll-padding-bottom: var(--coco-chat-scroll-clearance);
            box-sizing: border-box;
            border: 0;
            background: transparent;
        }

        .chat-shell.empty-state {
            width: 100%;
      height: var(--coco-chat-shell-height);
      min-height: 0;
      max-height: var(--coco-chat-shell-height);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            padding-top: 18px;
            padding-bottom: 0;
            padding-left: var(--coco-chat-body-side-space);
            padding-right: var(--coco-chat-body-side-space);
            overflow: hidden;
            border: 0;
            background: transparent;
        }

        .chat-row {
          display: flex;
          width: 100%;
          margin: 0;
        }

        .chat-row.assistant {
          justify-content: flex-start;
        }

        .chat-row.user {
          justify-content: flex-end;
        }

.chat-end-anchor {
    width: 100%;
    height: 0;
    flex: 0 0 0;
    scroll-margin-bottom: 0;
    border: 0;
    background: transparent;
    box-sizing: border-box;
}

        .assistant-card {
          max-width: 760px;
          min-height: 36px;
          border: 1px solid var(--assistant-border);
          border-radius: 16px;
          background: white;
          padding: 8px 12px;
          color: #111827;
          line-height: 1.35;
          font-size: 14px;
          box-shadow: 0 1px 0 rgba(148, 163, 184, 0.08);
        }

        .assistant-card .coco-chat-link {
          color: #2563eb;
          font-weight: 700;
          text-decoration: none;
          border-bottom: 1px solid rgba(37, 99, 235, 0.28);
        }

        .assistant-card .coco-chat-link:hover,
        .assistant-card .coco-chat-link:focus {
          color: #1d4ed8;
          border-bottom-color: rgba(29, 78, 216, 0.72);
        }

        .assistant-card.with-preview {
          max-width: min(980px, 100%);
          width: auto;
          display: grid;
          grid-template-columns: minmax(360px, 1fr) 230px;
          gap: 12px;
          align-items: start;
          padding: 10px;
        }

        .assistant-card-body {
          min-width: 0;
          padding: 0 2px;
        }

        .assistant-card-preview {
          width: 230px;
          aspect-ratio: 4 / 5;
          margin: 0;
          position: relative;
          overflow: visible;
          z-index: 2;
        }

        .assistant-card-preview-frame {
          width: 100%;
          height: 100%;
          border: 1px solid #d7e0ed;
          border-radius: 12px;
          overflow: hidden;
          background: #f8fafc;
          box-shadow: inset 0 1px 0 rgba(148, 163, 184, 0.16);
        }

        .assistant-card-preview-frame img {
          width: 100%;
          height: 100%;
          object-fit: contain;
          display: block;
        }

        .assistant-image-popover {
          position: fixed;
          top: clamp(78px, 10vh, 128px);
          right: clamp(18px, 3vw, 52px);
          width: min(860px, max(520px, var(--preview-original-width, 520px)), max(320px, calc(100vw - var(--coco-chat-left) - 72px)));
          height: min(760px, max(360px, var(--preview-original-height, 360px)), calc(100vh - 172px));
          display: block;
          visibility: hidden;
          opacity: 0;
          padding: 8px;
          border: 1px solid #cbd7e6;
          border-radius: 14px;
          background: rgba(255, 255, 255, 0.98);
          box-shadow: 0 22px 50px rgba(15, 23, 42, 0.26);
          pointer-events: none;
          z-index: 5000;
          transition: opacity 0.12s ease, visibility 0.12s ease;
        }

        .assistant-image-pan-frame {
          width: 100%;
          height: calc(100% - 24px);
          overflow: hidden;
          border-radius: 8px;
          background: #ffffff;
          cursor: zoom-in;
        }

        .assistant-image-popover img {
          width: min(var(--preview-original-width, 860px), 1200px);
          min-width: 100%;
          height: auto;
          max-width: none;
          max-height: none;
          object-fit: initial;
          display: block;
          border-radius: 8px;
          transform: translate3d(var(--pan-x, 0px), var(--pan-y, 0px), 0);
          transition: transform 0.04s linear;
          will-change: transform;
        }

        .assistant-image-popover span {
          display: block;
          margin-top: 6px;
          color: #475569;
          font-size: 11px;
          line-height: 1.2;
          text-align: right;
        }

        .assistant-card-preview:hover .assistant-image-popover {
          visibility: visible;
          opacity: 1;
        }

        .assistant-card.pending-card {
          width: 36px;
          min-width: 36px;
          max-width: 36px;
          height: 36px;
          min-height: 36px;
          max-height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 0;
        }

        .typing-dots {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          padding-left: 0;
        }

        .typing-dots span {
          width: 7px;
          height: 7px;
          border-radius: 999px;
          background: #a4afc4;
          opacity: 0.3;
          animation: cocoTypingPulse 1.1s ease-in-out infinite;
        }

        .typing-dots span:nth-child(2) {
          animation-delay: 0.15s;
        }

        .typing-dots span:nth-child(3) {
          animation-delay: 0.3s;
        }

        @keyframes cocoTypingPulse {
          0%, 80%, 100% {
            transform: translateY(0);
            opacity: 0.25;
          }
          40% {
            transform: translateY(-5px);
            opacity: 0.95;
          }
        }

        .user-bubble {
          min-width: 96px;
          min-height: 36px;
          max-width: 560px;
          border: 1px solid #93c5fd;
          border-radius: 15px;
          background: #dbeafe;
          padding: 8px 12px;
          color: #111827;
          font-size: 14px;
          font-weight: 400;
          text-align: left;
          line-height: 1.35;
        }

        .empty-chat {
          color: #7c8597;
          font-size: 1rem;
          text-align: center;
          max-width: 520px;
          line-height: 1.7;
        }

        @media (max-width: 940px) {
          .assistant-card.with-preview {
            grid-template-columns: minmax(0, 1fr);
          }

          .assistant-card-preview {
            width: 100%;
            max-height: 260px;
            aspect-ratio: 16 / 10;
          }
        }

        :root {
          --coco-chat-left: 346px;
          --coco-chat-right: 106px;
          --coco-chat-bottom: 12px;
          --coco-chat-height: 45px;
        }

div[data-testid="stChatInput"] {
  position: fixed !important;
  left: var(--coco-chat-left) !important;
  right: var(--coco-chat-right) !important;
  bottom: var(--coco-chat-bottom) !important;
  height: var(--coco-chat-height) !important;
  min-height: var(--coco-chat-height) !important;
  max-height: var(--coco-chat-height) !important;
  display: block !important;
  z-index: 1002 !important;
  margin: 0 !important;
  padding: 0 !important;
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  overflow: visible !important;
  box-sizing: border-box !important;
    border: 0 !important;
}

div[data-testid="stChatInput"] > div,
div[data-testid="stChatInput"] form,
div[data-testid="stChatInput"] [data-testid="stChatInputForm"],
div[data-testid="stChatInput"] [data-baseweb="textarea"],
div[data-testid="stChatInput"] [data-baseweb="base-input"] {
  width: 100% !important;
  height: var(--coco-chat-height) !important;
  min-height: var(--coco-chat-height) !important;
  max-height: var(--coco-chat-height) !important;
  display: block !important;
  margin: 0 !important;
  padding: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  box-sizing: border-box !important;
  overflow: visible !important;
}

div[data-testid="stChatInput"] > div {
    border: 0 !important;
}

div[data-testid="stChatInput"] form {
    border: 0 !important;
}

div[data-testid="stChatInput"] [data-testid="stChatInputForm"] {
    border: 0 !important;
}

div[data-testid="stChatInput"] [data-baseweb="textarea"],
div[data-testid="stChatInput"] [data-baseweb="base-input"] {
  position: relative !important;
}

div[data-testid="stChatInput"] [data-baseweb="textarea"] {
    border: 0 !important;
}

div[data-testid="stChatInput"] [data-baseweb="base-input"] {
    border: 0 !important;
}

div[data-testid="stChatInput"] textarea,
div[data-testid="stChatInput"] textarea:focus {
  width: 100% !important;
  height: var(--coco-chat-height) !important;
  min-height: var(--coco-chat-height) !important;
  max-height: var(--coco-chat-height) !important;
  margin: 0 !important;
  border-radius: 16px !important;
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  box-sizing: border-box !important;
  color: #e5e7eb !important;
  font-size: 14px !important;
  line-height: 1.4 !important;
  padding: 9px 36px 9px 12px !important;
  resize: none !important;
  overflow-y: auto !important;
  transition: none !important;
  transform: none !important;
  border: 0 !important;
}

        div[data-testid="stChatInput"] textarea::placeholder {
          color: #8f97aa !important;
        }

div[data-testid="stChatInput"] button {
  position: absolute !important;
  top: auto !important;
  bottom: 0 !important;
  right: 12px !important;
  transform: none !important;
  width: 44px !important;
  min-width: 44px !important;
  height: 44px !important;
  min-height: 44px !important;
          margin: 0 !important;
          padding: 0 !important;
          border-radius: 14px !important;
          background: transparent !important;
          border: 0 !important;
          box-shadow: none !important;
          appearance: none !important;
          -webkit-appearance: none !important;
          opacity: 0 !important;
          z-index: 4 !important;
        }

        div[data-testid="stChatInput"] button svg,
        div[data-testid="stChatInput"] button path {
          color: transparent !important;
          fill: transparent !important;
          opacity: 0 !important;
        }

[class*="st-key-search_panel"] {
    position: fixed !important;
    left: var(--coco-chat-left) !important;
    right: var(--coco-chat-right) !important;
    width: auto !important;
    bottom: calc(var(--coco-chat-bottom) + var(--coco-chat-height) + 10px) !important;
    z-index: 1003 !important;
    height: 42px !important;
    max-height: 42px !important;
    overflow: hidden !important;
    border-radius: 14px !important;
    border: 1px solid rgba(148, 163, 184, 0.28) !important;
    background: rgba(25, 28, 36, 0.96) !important;
    box-shadow: 0 14px 34px rgba(15, 23, 42, 0.26) !important;
    padding: 0 12px 10px 12px !important;
    transition: height 0.16s ease, max-height 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease !important;
}

[class*="st-key-search_panel"]:hover {
    height: min(330px, calc(100vh - 170px)) !important;
    max-height: min(330px, calc(100vh - 170px)) !important;
    border-color: rgba(147, 197, 253, 0.42) !important;
    box-shadow: 0 18px 46px rgba(15, 23, 42, 0.34) !important;
    overflow: hidden !important;
}

[class*="st-key-search_panel"] .search-panel-body {
    height: 100%;
    display: flex;
    flex-direction: column;
    min-width: 0;
}

[class*="st-key-search_panel"] .search-panel-summary {
    min-height: 40px;
    height: 40px;
    flex: 0 0 40px;
    display: flex;
    align-items: center;
    gap: 10px;
    color: #e5e7eb;
    line-height: 1.2;
    white-space: nowrap;
    min-width: 0;
}

[class*="st-key-search_panel"] .search-panel-summary strong {
    font-size: 14px;
    font-weight: 800;
    flex: 0 0 auto;
}

[class*="st-key-search_panel"] .search-panel-summary span,
[class*="st-key-search_panel"] .search-panel-empty {
    color: #9ca3af;
    font-size: 13px;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
}

[class*="st-key-search_panel"] .search-panel-empty {
    padding: 8px 2px 10px;
}

[class*="st-key-search_panel"] .search-panel-results {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 2px 0 6px;
}

[class*="st-key-search_panel"] .search-panel-results::-webkit-scrollbar {
    width: 8px;
}

[class*="st-key-search_panel"] .search-panel-results::-webkit-scrollbar-thumb {
    border-radius: 999px;
    background: rgba(148, 163, 184, 0.34);
}

[class*="st-key-search_panel"] .search-panel-result {
    min-height: 34px;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    margin: 3px 0;
    padding: 6px 10px;
    border-radius: 10px;
    border: 1px solid rgba(148, 163, 184, 0.24);
    background: rgba(255, 255, 255, 0.05);
    color: #e5e7eb;
    font-size: 12px;
    font-weight: 700;
    line-height: 1.25;
    text-align: left;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    text-decoration: none;
}

[class*="st-key-search_panel"] .search-panel-result:hover,
[class*="st-key-search_panel"] .search-panel-result:focus {
    background: rgba(59, 130, 246, 0.18);
    border-color: rgba(147, 197, 253, 0.5);
    color: #ffffff;
}

[class*="st-key-search_panel"] .search-panel-close-row {
    flex: 0 0 34px;
    display: flex;
    justify-content: center;
    align-items: center;
    padding-top: 4px;
    margin-top: 2px;
    border-top: 1px solid rgba(148, 163, 184, 0.18);
}

[class*="st-key-search_panel"] .search-panel-close-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 54px;
    height: 28px;
    padding: 0 10px;
    border-radius: 999px;
    border: 1px solid rgba(148, 163, 184, 0.28);
    background: rgba(255, 255, 255, 0.05);
    color: #e5e7eb;
    font-size: 12px;
    font-weight: 800;
    text-decoration: none;
    text-align: center;
}

[class*="st-key-search_panel"] .search-panel-close-link:hover,
[class*="st-key-search_panel"] .search-panel-close-link:focus {
    background: rgba(59, 130, 246, 0.18);
    border-color: rgba(147, 197, 253, 0.5);
    color: #ffffff;
}

[class*="st-key-search_panel_actions"] {
    position: fixed !important;
    left: -10000px !important;
    top: -10000px !important;
    width: 1px !important;
    height: 1px !important;
    overflow: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

[class*="st-key-floating_reset_button"] {
    position: fixed;
    right: 40px;
    bottom: 98px;
    z-index: 1002;
    width: 48px;
    height: 48px;
    margin: 0 !important;
    padding: 0 !important;
    border: 0 !important;
}

[class*="st-key-floating_reset_button"] > div,
[class*="st-key-floating_reset_button"] [data-testid="stButton"] {
    width: 48px !important;
    height: 48px !important;
    margin: 0 !important;
    padding: 0 !important;
}

[class*="st-key-floating_reset_button"] > div {
    border: 0 !important;
}

[class*="st-key-floating_reset_button"] [data-testid="stButton"] {
    border: 0 !important;
}

        [class*="st-key-floating_reset_button"] button {
          width: 48px !important;
          min-width: 48px !important;
          max-width: 48px !important;
          height: 48px !important;
          min-height: 48px !important;
          border-radius: 999px !important;
          background: #2c2f3b !important;
          border: 1px solid rgba(255, 255, 255, 0.08) !important;
          color: #f8a05b !important;
          font-size: 1.5rem !important;
          font-weight: 800 !important;
          padding: 0 !important;
          margin: 0 !important;
          box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18) !important;
        }

        [class*="st-key-floating_reset_button"] button:hover,
        [class*="st-key-floating_reset_button"] button:focus,
        [class*="st-key-floating_reset_button"] button:active {
          background: #2c2f3b !important;
          border: 1px solid rgba(255, 255, 255, 0.16) !important;
          color: #f8a05b !important;
          box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18) !important;
        }

        [class*="st-key-floating_reset_button"] button p {
          font-size: 1.5rem !important;
          line-height: 1 !important;
          margin: 0 !important;
        }

        @media (max-width: 1100px) {
          [data-testid="stSidebar"] {
            min-width: 310px !important;
            max-width: 310px !important;
          }

          :root {
            --coco-chat-left: 328px;
            --coco-chat-right: 88px;
          }
        }

        @media (max-width: 900px) {
          [data-testid="stMainBlockContainer"] {
            padding-left: 18px;
            padding-right: 18px;
            padding-bottom: 148px;
          }

          :root {
            --coco-chat-left: 18px;
            --coco-chat-right: 18px;
            --coco-chat-shell-height: calc(100dvh - 138px);
            --coco-chat-scroll-clearance: 72px;
            --coco-chat-body-side-space: 18px;
          }

            .chat-shell {
        height: var(--coco-chat-shell-height);
        max-height: var(--coco-chat-shell-height);
            }

            .chat-shell.empty-state {
        height: var(--coco-chat-shell-height);
        max-height: var(--coco-chat-shell-height);
            }
        }
        </style>
        """
    st.markdown(css.replace("__LOGO_BUTTON_BG__", logo_button_bg), unsafe_allow_html=True)


st.set_page_config(
    page_title="CocoAi Study",
    page_icon="assets/cocoai_icon_1024_clean.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

_ensure_dirs()
state = _sync_documents(_load_state())
_prune_search_history_messages(state)
_refresh_search_panel(state)
_schedule_main_chat_llm_warmup()

if not st.session_state.get("_recent_target_bootstrapped"):
    st.session_state["_recent_target_bootstrapped"] = True
    _restore_recent_target(state)

if st.query_params.get("chat") == "main":
    _mark_active_target(state, "main")
    _save_state(state)
    st.query_params.clear()
    st.rerun()

doc_query = str(st.query_params.get("doc") or "").strip()
if doc_query:
    known_doc_ids = {str(item.get("doc_id") or "").strip() for item in state.get("documents", []) if isinstance(item, dict)}
    if doc_query in known_doc_ids:
        _mark_active_target(state, "study", doc_query)
        _save_state(state)
    st.query_params.clear()
    st.rerun()

if st.query_params.get("search_close") == "1":
    state.pop("search_panel", None)
    _save_state(state)
    st.query_params.clear()
    st.rerun()

if st.query_params.get("clear") == "1":
    _clear_active_chat(state)
    _save_state(state)
    st.query_params.clear()
    st.rerun()

if st.session_state.pop("_clear_active_chat_requested", False):
    _clear_active_chat(state)
    _save_state(state)
    st.rerun()

_save_state(state)
_inject_css()

with st.sidebar:
    with st.container(key="logo_home_button"):
        if st.button("메인채팅", key="logo_home", use_container_width=False):
            _mark_active_target(state, "main")
            _save_state(state)
            st.rerun()

    _render_upload_entry(state)

    st.markdown('<div class="sidebar-section-title learning-list-title">학습리스트</div>', unsafe_allow_html=True)
    if state.get("documents"):
        is_study_mode = _active_chat_mode(state) == "study"
        loaded_documents = {
            str(item.get("doc_id") or ""): _load_document(str(item.get("doc_id") or ""))
            for item in state.get("documents", [])
            if str(item.get("doc_id") or "").strip()
        }
        with st.container(key="doc_live_list"):
            for item in state.get("documents", []):
                doc_id = item["doc_id"]
                is_doc_active = is_study_mode and state.get("selected_doc_id") == doc_id
                with st.container(key=f"doc_row_{doc_id}"):
                    row_left, row_right = st.columns([1, 0.16], gap="small")
                    with row_left:
                        select_key = f"doc_select_active_{doc_id}" if is_doc_active else f"doc_select_inactive_{doc_id}"
                        with st.container(key=select_key):
                            if st.button(
                                _learning_list_label(item, loaded_documents.get(doc_id)),
                                key=f"select_{doc_id}",
                                use_container_width=True,
                                type="primary" if is_doc_active else "secondary",
                            ):
                                _mark_active_target(state, "study", doc_id)
                                _save_state(state)
                                st.rerun()
                    with row_right:
                        with st.container(key=f"doc_delete_{doc_id}"):
                            if st.button("✕", key=f"delete_{doc_id}", use_container_width=False):
                                _delete_document(doc_id)
                                state["documents"] = [doc for doc in state.get("documents", []) if doc.get("doc_id") != doc_id]
                                state["chat_history"] = [
                                    message for message in state.get("chat_history", []) if message.get("doc_id") != doc_id
                                ]
                                if state.get("selected_doc_id") == doc_id:
                                    next_doc_id = state["documents"][0]["doc_id"] if state["documents"] else None
                                    if next_doc_id:
                                        _mark_active_target(state, "study", next_doc_id)
                                    else:
                                        _mark_active_target(state, "main")
                                if not state["documents"]:
                                    _mark_active_target(state, "main")
                                _save_state(state)
                                st.rerun()
    else:
        st.markdown(
            '<div class="empty-docs">아직 저장된 학습 파일이 없습니다. 위 업로드 영역에 문제 이미지를 넣어주세요.</div>',
            unsafe_allow_html=True,
        )

    selected_for_sidebar = _load_document(state.get("selected_doc_id"))
    _render_check_panel(_build_check_items(state, selected_for_sidebar), state, selected_for_sidebar)

submitted_prompt = _render_prompt_input(state)
_render_chat_body(state, submitted_prompt=submitted_prompt)
