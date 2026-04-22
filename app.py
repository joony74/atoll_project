from __future__ import annotations

import base64
import hashlib
import html
import re
import time
from pathlib import Path

import streamlit as st

from app.chat.orchestrator import build_main_chat_reply as _build_main_chat_reply
from app.chat.state import (
    UPLOADS_DIR,
    active_chat_mode as _active_chat_mode,
    append_main_message as _append_main_message,
    append_message as _append_message,
    delete_document as _delete_document,
    ensure_dirs as _ensure_dirs,
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
from app.core.pipeline import run_solve_pipeline


LOGO_PATH = Path(__file__).resolve().parent / "assets" / "cocoai.svg"
DEFAULT_USER_PROMPT = "뭐야?"
PROMPT_PLACEHOLDER = "자료가 없어도 괜찮아요. 수학 개념이나 문제를 그대로 물어보세요."


def _save_uploaded_file(uploaded_file) -> tuple[str, str, str]:
    data = uploaded_file.getvalue()
    file_hash = hashlib.sha1(data).hexdigest()[:12]
    target_path = UPLOADS_DIR / f"{file_hash}_{uploaded_file.name}"
    target_path.write_bytes(data)
    return file_hash, uploaded_file.name, str(target_path)


def _run_analysis(file_path: str, user_query: str = "") -> dict:
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


def _status_badge(status: str) -> str:
    palette = {
        "정상": ("rgba(34,197,94,0.14)", "#7ce2a6"),
        "보강 필요": ("rgba(251,113,133,0.16)", "#f9a8b3"),
        "실패": ("rgba(248,113,113,0.18)", "#fca5a5"),
    }
    bg, fg = palette.get(status, ("rgba(148,163,184,0.18)", "#cbd5e1"))
    return (
        f'<span class="status-badge" style="background:{bg};color:{fg};">'
        f"{html.escape(status)}</span>"
    )


def _assistant_render_delay_seconds(answer: str) -> float:
    compact = re.sub(r"\s+", "", str(answer or ""))
    length_steps = min(12, max(len(compact) // 80, 0))
    return 0.35 + (0.05 * length_steps)


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


def _extract_function_candidates(structured: dict) -> list[str]:
    expressions = [str(item or "") for item in structured.get("expressions") or []]
    raw_candidates = [str(item or "") for item in structured.get("source_text_candidates") or []]
    functionish = []
    for text in expressions + raw_candidates:
        lowered = text.lower()
        if any(token in lowered for token in ("f(", "x", "y", "=")):
            functionish.append(text)
    if not functionish:
        functionish = expressions[:3]
    return _dedupe_text(functionish, limit=4)


def _extract_coordinate_candidates(structured: dict) -> list[str]:
    bucket = "\n".join(str(item or "") for item in (structured.get("source_text_candidates") or []))
    bucket += "\n" + "\n".join(str(item or "") for item in (structured.get("expressions") or []))
    matches = re.findall(r"\(\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*\)", bucket)
    return _dedupe_text(matches, limit=4)


def _build_recovery_message(document: dict | None) -> str:
    if not document:
        return "업로드한 자료가 아직 없습니다.\n\n이미지를 넣으면 복원된 식 후보와 풀이 단서를 이 영역에 정리해둘게요."

    analysis = document.get("analysis") or {}
    structured = analysis.get("structured_problem") or {}
    expressions = [str(item or "") for item in structured.get("expressions") or []]
    source_candidates = [str(item or "") for item in structured.get("source_text_candidates") or []]
    function_candidates = _extract_function_candidates(structured)
    coordinate_candidates = _extract_coordinate_candidates(structured)
    question_goal = str(structured.get("math_topic") or "unknown").strip() or "unknown"
    if question_goal == "unknown":
        question_goal = "unknown"

    lines = [
        "현재 파일에서 복원된 정보는 제한적이지만, 다음은 확인됩니다.",
        "",
        f"- 식 후보: {_list_repr(expressions or source_candidates)}",
        f"- 함수 후보: {_list_repr(function_candidates)}",
        f"- 좌표 후보: {_list_repr(coordinate_candidates)}",
        f"- 질문 목표 후보: {question_goal}",
        "",
        "이 정보를 기반으로 풀이를 진행할 수 있습니다.",
    ]
    return "\n".join(lines)


def _build_followup_message(document: dict | None, prompt: str) -> str:
    if not document:
        return "파일을 먼저 올려주면 복원된 식, 문제문장, 답 후보를 이 자리에서 바로 같이 정리할게요."

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


def _render_prompt_input() -> None:
    with st.container(key="floating_reset_button"):
        if st.button("↻", key="floating_reset", help="대화 초기화"):
            st.session_state["_clear_active_chat_requested"] = True
            st.rerun()
    st.text_input(
        "질문 입력",
        value="",
        key="prompt_input",
        label_visibility="collapsed",
        placeholder=PROMPT_PLACEHOLDER,
    )


def _consume_submitted_prompt() -> str | None:
    current = str(st.session_state.get("prompt_input", "") or "").strip()
    last_seen = str(st.session_state.get("_last_prompt_widget_value", "") or "").strip()

    if current and current != last_seen:
        st.session_state["_last_prompt_widget_value"] = current
        st.session_state["prompt_input"] = ""
        return current

    if not current and last_seen:
        st.session_state["_last_prompt_widget_value"] = ""

    return None


def _clear_active_chat(state: dict) -> None:
    if _active_chat_mode(state) == "main":
        state["main_chat_history"] = []
    else:
        selected_doc_id = str(state.get("selected_doc_id") or "").strip()
        state["chat_history"] = [
            item
            for item in state.get("chat_history", [])
            if str(item.get("doc_id") or "").strip() != selected_doc_id
        ]
        for item in state.get("documents", []):
            if str(item.get("doc_id") or "").strip() == selected_doc_id:
                item["latest_user_query"] = ""
                break


def _build_check_items(state: dict, selected: dict | None) -> list[dict]:
    documents = _load_all_documents(state)
    stored_files = len(documents)
    analyzed_count = max(stored_files, sum(1 for item in state.get("chat_history", []) if item.get("role") == "assistant"))
    recognized_count = sum(
        1
        for doc in documents
        if str(((doc.get("analysis") or {}).get("structured_problem") or {}).get("normalized_problem_text") or "").strip()
    )
    solved_count = sum(
        1
        for doc in documents
        if str(((doc.get("analysis") or {}).get("solve_result") or {}).get("validation_status") or "").strip() == "verified"
    )
    pending_count = max(stored_files - solved_count, 0)
    error_count = sum(
        1
        for doc in documents
        if not str(((doc.get("analysis") or {}).get("structured_problem") or {}).get("normalized_problem_text") or "").strip()
    )

    selected_topic = str(((selected or {}).get("analysis") or {}).get("structured_problem", {}).get("math_topic") or "").strip()
    if selected_topic in {"", "unknown"}:
        selected_topic = "unknown_intent"

    return [
        {"title": "설치/실행", "status": "정상", "body": "첫 실행 시간이 기록되었습니다."},
        {
            "title": "파일 업로드/분석",
            "status": "정상" if stored_files else "보강 필요",
            "body": f"저장된 파일 {stored_files}개, 분석 기록 {analyzed_count}회",
        },
        {
            "title": "문제 인식",
            "status": "정상" if recognized_count else "보강 필요",
            "body": f"구조화된 문제 {recognized_count}개",
        },
        {
            "title": "풀이/검증",
            "status": "정상" if solved_count else "보강 필요",
            "body": f"완료 {solved_count}개 / processing 잔류 {pending_count}개",
        },
        {
            "title": "프롬프트 함수 흐름",
            "status": "정상",
            "body": f"마지막 액션: {selected_topic}",
        },
        {
            "title": "저장/복원",
            "status": "정상",
            "body": "세션 복원 파일과 복원 시간 기록 확인",
        },
        {
            "title": "오류 처리",
            "status": "정상" if error_count == 0 else "보강 필요",
            "body": f"최근 오류 로그 {error_count}건",
        },
    ]


def _render_check_panel(items: list[dict]) -> str:
    needs_attention = any(item.get("status") != "정상" for item in items)
    summary = "추가 수정 필요" if needs_attention else "정상"
    summary_class = "needs-work" if needs_attention else "healthy"
    sections = []
    for item in items:
        title = html.escape(str(item.get("title") or ""))
        title_class = "check-title upload-check-title" if "업로드" in title else "check-title"
        badge = _status_badge(str(item.get("status") or ""))
        body = html.escape(str(item.get("body") or ""))
        sections.append(
            '<div class="check-row">'
            '<div class="check-title-line">'
            f'<div class="{title_class}">{title}</div>'
            f'<div>{badge}</div>'
            '</div>'
            f'<div class="check-body">{body}</div>'
            '</div>'
        )
    return (
        f'<div class="check-panel"><div class="check-panel-head"><div class="check-panel-title">요청 점검</div>'
        f'<div class="check-summary {summary_class}">{html.escape(summary)}</div></div>'
        f'{"".join(sections)}</div>'
    )


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
    if history:
        return history[-18:]

    document = _load_document(selected_doc_id)
    if document:
        return [
            {
                "role": "assistant",
                "content": _build_recovery_message(document),
                "doc_id": selected_doc_id,
            }
        ]
    return []


def _render_chat_body(state: dict, submitted_prompt: str | None = None) -> None:
    user_prompt = str(submitted_prompt or "").strip()
    submitted = bool(user_prompt)
    mode = _active_chat_mode(state)
    conversation_slot = st.empty()

    if submitted:
        prompt = user_prompt or DEFAULT_USER_PROMPT
        if mode == "main":
            _mark_active_target(state, "main")
            _append_main_message(state, "user", prompt)
            _save_state(state)
            pending_conversation = _conversation_from_state(state) + [{"role": "assistant", "pending": True}]
            conversation_slot.markdown(_render_conversation(pending_conversation, mode=mode), unsafe_allow_html=True)
            _scroll_chat_to_latest()
            started = time.time()
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
            assistant_reply = _build_followup_message(selected_document, prompt)
            elapsed = time.time() - started
            remaining = max(_assistant_render_delay_seconds(assistant_reply) - elapsed, 0.0)
            if remaining > 0:
                time.sleep(remaining)
            _append_message(state, "assistant", assistant_reply, doc_id=selected_doc_id)

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
        }

        html, body, [class*="css"] {
          font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Apple SD Gothic Neo", "Pretendard", sans-serif;
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

        [data-testid="stAppViewContainer"] {
          background: var(--main-bg);
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
        [data-testid="stFileUploaderDropzone"] small,
        [data-testid="stFileUploaderDropzone"] button {
          display: none !important;
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
          width: 34px;
          height: 34px;
          transform: translate(-50%, -50%);
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='34' height='34' viewBox='0 0 34 34' fill='none'%3E%3Cpath d='M17 8.5V20.5' stroke='%23EDF2FF' stroke-width='2.7' stroke-linecap='round' stroke-linejoin='round'/%3E%3Cpath d='M11.5 14L17 8.5L22.5 14' stroke='%23EDF2FF' stroke-width='2.7' stroke-linecap='round' stroke-linejoin='round'/%3E%3Cpath d='M9.5 23.5V24.5C9.5 25.6046 10.3954 26.5 11.5 26.5H22.5C23.6046 26.5 24.5 25.6046 24.5 24.5V23.5' stroke='%23EDF2FF' stroke-width='2.7' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
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
          font-size: 16px;
          font-weight: 400;
          padding-left: 1ch;
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

        [class*="st-key-doc_select_"] button[kind="secondary"] {
          box-shadow: inset 5px 0 0 #4b505d !important;
          font-weight: 400 !important;
        }

        [class*="st-key-doc_select_"] button[kind="primary"] {
          box-shadow: inset 5px 0 0 #3b82f6 !important;
          font-weight: 700 !important;
        }

        [class*="st-key-doc_select_"] button[kind="secondary"] p,
        [class*="st-key-doc_select_"] button[kind="secondary"] span {
          font-weight: 400 !important;
        }

        [class*="st-key-doc_select_"] button[kind="primary"] p,
        [class*="st-key-doc_select_"] button[kind="primary"] span {
          font-weight: 700 !important;
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
          font-size: 0.96rem;
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

        .check-panel {
          margin-top: 13px;
          background: #1a1c23;
          border: 1px solid var(--panel-border);
          border-radius: 20px;
          padding: 14px 18px 4px;
          color: white;
        }

        .check-panel-head {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 4px;
        }

        .check-panel-title {
          font-size: 14px;
          font-weight: 400;
          letter-spacing: -0.04em;
        }

        .check-summary {
          font-size: 10px;
          font-weight: 400;
        }

        .check-summary.needs-work {
          color: #9ab0ff;
        }

        .check-summary.healthy {
          color: #7ce2a6;
        }

        .check-row {
          padding: 10px 0;
          border-top: 1px solid rgba(255, 255, 255, 0.08);
        }

        .check-row:first-of-type {
          border-top: none;
        }

        .check-title-line {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 8px;
        }

        .check-title {
          font-size: 14px;
          font-weight: 400;
        }

        .check-title.upload-check-title,
        .check-title.upload-check-title * {
          font-weight: 300 !important;
          font-variation-settings: "wght" 300;
        }

        .check-body {
          margin-top: 4px;
          color: rgba(255, 255, 255, 0.74);
          line-height: 1.45;
          font-size: 12px;
          font-weight: 400;
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          border-radius: 999px;
          padding: 4px 10px;
          font-size: 10px;
          font-weight: 400;
        }

        .chat-shell {
          max-width: 1110px;
          margin: 6px auto 0;
          height: calc(100vh - 220px);
          min-height: calc(100vh - 220px);
          padding-top: 18px;
          padding-bottom: 0;
          display: flex;
          flex-direction: column;
          justify-content: flex-start;
          overflow-y: auto;
          overscroll-behavior: contain;
          box-sizing: border-box;
        }

        .chat-shell.empty-state {
          width: 100%;
          height: calc(100vh - 240px);
          min-height: calc(100vh - 240px);
          display: flex;
          align-items: center;
          justify-content: center;
          padding-top: 0;
          overflow: hidden;
        }

        .chat-row {
          display: flex;
          width: 100%;
        }

        .chat-row.assistant {
          justify-content: flex-start;
          margin: 0 0 56px;
        }

        .chat-row.user {
          justify-content: flex-end;
          margin: 0 0 18px;
        }

        .chat-end-anchor {
          width: 100%;
          height: 220px;
          flex: 0 0 220px;
          scroll-margin-bottom: 180px;
        }

        .assistant-card {
          max-width: 760px;
          border: 1px solid var(--assistant-border);
          border-radius: 16px;
          background: white;
          padding: 22px 24px;
          color: #111827;
          line-height: 1.68;
          font-size: 1rem;
          box-shadow: 0 1px 0 rgba(148, 163, 184, 0.08);
        }

        .assistant-card.pending-card {
          min-height: 96px;
          display: flex;
          align-items: center;
          justify-content: flex-start;
        }

        .typing-dots {
          display: inline-flex;
          align-items: center;
          gap: 10px;
          padding-left: 4px;
        }

        .typing-dots span {
          width: 12px;
          height: 12px;
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
          min-width: 180px;
          max-width: 560px;
          border: 1px solid #93c5fd;
          border-radius: 15px;
          background: #dbeafe;
          padding: 18px 20px;
          color: #111827;
          font-size: 1rem;
          font-weight: 800;
          text-align: left;
        }

        .empty-chat {
          color: #7c8597;
          font-size: 1rem;
          text-align: center;
          max-width: 520px;
          line-height: 1.7;
        }

        div[data-testid="stTextInput"] {
          position: fixed !important;
          left: 310px !important;
          right: 0 !important;
          bottom: 0 !important;
          width: calc(100vw - 310px) !important;
          max-width: calc(100vw - 310px) !important;
          height: 120px !important;
          z-index: 1001 !important;
          display: flex !important;
          justify-content: center !important;
          align-items: center !important;
          margin: 0 !important;
          padding: 0 !important;
          background: rgba(255, 255, 255, 0.02) !important;
          border: 1px solid transparent !important;
          backdrop-filter: blur(8px);
          -webkit-backdrop-filter: blur(8px);
          box-sizing: border-box;
        }

        div[data-testid="stTextInput"] > div,
        div[data-testid="stTextInput"] div[data-testid="stVerticalBlock"],
        div[data-testid="stTextInput"] div[data-testid="stHorizontalBlock"],
        div[data-testid="stTextInput"] section,
        div[data-testid="stTextInput"] label,
        div[data-testid="stTextInput"] div[data-testid="stElementContainer"] {
          width: 100% !important;
          max-width: 100% !important;
          min-width: 0 !important;
          min-height: 0 !important;
          margin: 0 !important;
          padding: 0 !important;
          background: transparent !important;
          border: 1px solid transparent !important;
          box-shadow: none !important;
          box-sizing: border-box;
          gap: 0 !important;
        }

        div[data-testid="stTextInputRootElement"] {
          width: 95% !important;
          max-width: 95% !important;
          flex: 0 0 95% !important;
          height: 72px !important;
          margin: 0 auto !important;
          padding: 0 !important;
          border: 1px solid transparent !important;
          background: transparent !important;
        }

        div[data-testid="stTextInputRootElement"] > div,
        div[data-testid="stTextInput"] div[data-baseweb="base-input"],
        div[data-testid="stTextInput"] div[data-baseweb="base-input"] > div,
        div[data-testid="stTextInput"] div[data-baseweb="base-input"] > div > div {
          min-height: 72px !important;
          height: 72px !important;
          width: 100% !important;
          border-radius: 16px !important;
          background: #2c2f3b !important;
          border: 1px solid rgba(96, 165, 250, 0.95) !important;
          box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18) !important;
          box-sizing: border-box;
        }

        div[data-testid="stTextInput"] div[data-baseweb="base-input"] {
          overflow: hidden !important;
        }

        div[data-testid="stTextInputRootElement"] input {
          background: transparent !important;
          color: #e5e7eb !important;
          font-size: 1.06rem !important;
          height: 72px !important;
          line-height: 72px !important;
          padding: 0 22px !important;
        }

        div[data-testid="stTextInputRootElement"] input::placeholder {
          color: #8f97aa !important;
        }

        [class*="st-key-floating_reset_button"] {
          position: fixed;
          right: 40px;
          bottom: 152px;
          z-index: 1002;
          width: 68px;
          height: 68px;
          margin: 0 !important;
          padding: 0 !important;
        }

        [class*="st-key-floating_reset_button"] > div,
        [class*="st-key-floating_reset_button"] [data-testid="stButton"] {
          width: 68px !important;
          height: 68px !important;
          margin: 0 !important;
          padding: 0 !important;
        }

        [class*="st-key-floating_reset_button"] button {
          width: 68px !important;
          min-width: 68px !important;
          max-width: 68px !important;
          height: 68px !important;
          min-height: 68px !important;
          border-radius: 999px !important;
          background: #2c2f3b !important;
          border: 1px solid rgba(255, 255, 255, 0.08) !important;
          color: #f8a05b !important;
          font-size: 2rem !important;
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
          font-size: 2rem !important;
          line-height: 1 !important;
          margin: 0 !important;
        }

        @media (max-width: 1100px) {
          [data-testid="stSidebar"] {
            min-width: 310px !important;
            max-width: 310px !important;
          }

          div[data-testid="stTextInput"] {
            left: 310px !important;
            right: 0 !important;
            width: calc(100vw - 310px) !important;
            max-width: calc(100vw - 310px) !important;
          }
        }

        @media (max-width: 900px) {
          [data-testid="stMainBlockContainer"] {
            padding-left: 18px;
            padding-right: 18px;
            padding-bottom: 148px;
          }

          div[data-testid="stTextInput"] {
            left: 0 !important;
            width: 100% !important;
            max-width: 100% !important;
            margin: 0 !important;
          }

          .chat-shell {
            height: calc(100vh - 206px);
            min-height: calc(100vh - 206px);
          }

          .chat-shell.empty-state {
            height: calc(100vh - 224px);
            min-height: calc(100vh - 224px);
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

if not st.session_state.get("_recent_target_bootstrapped"):
    st.session_state["_recent_target_bootstrapped"] = True
    _restore_recent_target(state)

if st.query_params.get("chat") == "main":
    _mark_active_target(state, "main")
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

    uploaded_file = st.file_uploader("이미지 업로드", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    if uploaded_file is not None:
        file_id, file_name, file_path = _save_uploaded_file(uploaded_file)
        analysis = _run_analysis(file_path)
        document_payload = {
            "doc_id": file_id,
            "file_name": file_name,
            "file_path": file_path,
            "latest_user_query": "",
            "analysis": analysis,
        }
        _persist_document(file_id, file_name, file_path, analysis)
        docs = [item for item in state.get("documents", []) if item.get("doc_id") != file_id]
        docs.insert(
            0,
            {
                "doc_id": file_id,
                "file_name": file_name,
                "file_path": file_path,
                "created_at": time.time(),
                "latest_user_query": "",
            },
        )
        state["documents"] = docs
        _mark_active_target(state, "study", file_id)
        _append_message(state, "assistant", _build_recovery_message(document_payload), doc_id=file_id)
        _save_state(state)
        st.rerun()

    st.markdown('<div class="sidebar-section-title learning-list-title">학습리스트</div>', unsafe_allow_html=True)
    if state.get("documents"):
        with st.container(key="doc_live_list"):
            for item in state.get("documents", []):
                doc_id = item["doc_id"]
                with st.container(key=f"doc_row_{doc_id}"):
                    row_left, row_right = st.columns([1, 0.16], gap="small")
                    with row_left:
                        with st.container(key=f"doc_select_{doc_id}"):
                            if st.button(
                                _truncate_label(item.get("file_name") or doc_id),
                                key=f"select_{doc_id}",
                                use_container_width=True,
                                type="primary" if state.get("selected_doc_id") == doc_id else "secondary",
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
    st.markdown(_render_check_panel(_build_check_items(state, selected_for_sidebar)), unsafe_allow_html=True)

submitted_prompt = _consume_submitted_prompt()
_render_prompt_input()
_render_chat_body(state, submitted_prompt=submitted_prompt)
