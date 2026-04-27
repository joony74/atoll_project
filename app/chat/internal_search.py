from __future__ import annotations

import re
import time
import unicodedata
from urllib.parse import quote, unquote

from .contracts import AppState
from .state import load_document


_COMMAND_RE = re.compile(r"^\s*(?:검색|찾기)\s*[:：]\s*(.+?)\s*$")
_WHITESPACE_RE = re.compile(r"\s+")


def parse_internal_search_command(prompt: str) -> str | None:
    match = _COMMAND_RE.match(str(prompt or ""))
    if not match:
        return None
    query = _WHITESPACE_RE.sub(" ", match.group(1)).strip()
    return query or None


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(text or "")).lower()
    return _WHITESPACE_RE.sub(" ", normalized).strip()


def _compact(text: str) -> str:
    return _normalize(text).replace(" ", "")


def _terms(query: str) -> list[str]:
    tokens = [_normalize(item) for item in re.split(r"[\s,./|]+", query) if _normalize(item)]
    phrase = _normalize(query)
    if phrase and phrase not in tokens:
        tokens.insert(0, phrase)
    return tokens[:6]


def _score(text: str, query: str) -> int:
    haystack = _normalize(text)
    compact_haystack = haystack.replace(" ", "")
    needle = _normalize(query)
    compact_needle = needle.replace(" ", "")
    if not haystack or not needle:
        return 0

    score = 0
    if needle in haystack:
        score += 100
    if compact_needle and compact_needle in compact_haystack:
        score += 80
    for term in _terms(query):
        if not term or term == needle:
            continue
        compact_term = term.replace(" ", "")
        if term in haystack:
            score += 25
        elif compact_term and compact_term in compact_haystack:
            score += 18
    return score


def _snippet(text: str, query: str, limit: int = 96) -> str:
    clean = _WHITESPACE_RE.sub(" ", str(text or "")).strip()
    if len(clean) <= limit:
        return clean

    lowered = clean.lower()
    needle = str(query or "").strip().lower()
    index = lowered.find(needle) if needle else -1
    if index < 0:
        return clean[: limit - 1].rstrip() + "..."

    start = max(0, index - 30)
    end = min(len(clean), start + limit)
    start = max(0, end - limit)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(clean) else ""
    return prefix + clean[start:end].strip() + suffix


def _flatten_text(value: object, *, limit: int = 80) -> list[str]:
    if limit <= 0:
        return []
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, (int, float, bool)):
        return [str(value)]
    if isinstance(value, dict):
        texts: list[str] = []
        for item in value.values():
            texts.extend(_flatten_text(item, limit=limit - len(texts)))
            if len(texts) >= limit:
                break
        return texts
    if isinstance(value, (list, tuple, set)):
        texts = []
        for item in value:
            texts.extend(_flatten_text(item, limit=limit - len(texts)))
            if len(texts) >= limit:
                break
        return texts
    return []


def _doc_name_map(state: AppState) -> dict[str, str]:
    names: dict[str, str] = {}
    for document in state.get("documents", []):
        if not isinstance(document, dict):
            continue
        doc_id = str(document.get("doc_id") or "").strip()
        if not doc_id:
            continue
        names[doc_id] = str(document.get("file_name") or doc_id).strip() or doc_id
    return names


def _study_link(doc_id: str) -> str:
    return f"?doc={quote(str(doc_id), safe='')}"


def _append_result(
    results: list[dict],
    *,
    query: str,
    source: str,
    target_label: str,
    text: str,
    href: str,
    recency: float = 0.0,
    weight: int = 0,
) -> None:
    raw_score = _score(text, query)
    if raw_score <= 0:
        return
    score = raw_score + weight
    results.append(
        {
            "score": score,
            "recency": recency,
            "source": source,
            "target_label": target_label,
            "snippet": _snippet(text, query),
            "href": href,
            "target_type": "main" if href == "?chat=main" else "study",
            "doc_id": unquote(href.removeprefix("?doc=")) if href.startswith("?doc=") else "",
        }
    )


def _document_search_text(loaded: dict, doc_name: str) -> str:
    analysis = loaded.get("analysis") if isinstance(loaded, dict) else {}
    structured = analysis.get("structured_problem") if isinstance(analysis, dict) else {}
    solve_result = analysis.get("solve_result") if isinstance(analysis, dict) else {}
    if not isinstance(structured, dict):
        structured = {}
    if not isinstance(solve_result, dict):
        solve_result = {}

    text_parts: list[str] = [
        doc_name,
        str(loaded.get("latest_user_query") or ""),
        str(structured.get("normalized_problem_text") or ""),
        str(structured.get("math_topic") or ""),
        str(structured.get("question_type") or ""),
        str(solve_result.get("computed_answer") or ""),
        str(solve_result.get("matched_choice") or ""),
        str(solve_result.get("explanation") or ""),
    ]
    for key in (
        "expressions",
        "source_text_candidates",
        "problem_text_candidates",
        "function_candidates",
        "coordinate_candidates",
        "answer_candidates",
        "type_candidates",
    ):
        text_parts.extend(_flatten_text(structured.get(key), limit=20))
    for key in ("steps", "answer_candidates"):
        text_parts.extend(_flatten_text(solve_result.get(key), limit=12))
    return " ".join(part for part in text_parts if str(part or "").strip())


def build_internal_search_panel(prompt: str, state: AppState | None) -> dict | None:
    query = parse_internal_search_command(prompt)
    if query is None:
        return None

    resolved_state: AppState = state or {}
    results: list[dict] = []
    doc_names = _doc_name_map(resolved_state)
    prompt_text = str(prompt or "").strip()

    for message in resolved_state.get("main_chat_history", []):
        if not isinstance(message, dict):
            continue
        content = str(message.get("content") or "").strip()
        if not content or content == prompt_text:
            continue
        role = "사용자" if str(message.get("role") or "") == "user" else "코코"
        _append_result(
            results,
            query=query,
            source=f"메인 채팅 / {role}",
            target_label="메인 채팅 열기",
            text=content,
            href="?chat=main",
            recency=float(message.get("created_at") or 0.0),
        )

    for message in resolved_state.get("chat_history", []):
        if not isinstance(message, dict):
            continue
        content = str(message.get("content") or "").strip()
        doc_id = str(message.get("doc_id") or "").strip()
        if not content or not doc_id:
            continue
        role = "사용자" if str(message.get("role") or "") == "user" else "코코"
        doc_name = doc_names.get(doc_id, doc_id)
        _append_result(
            results,
            query=query,
            source=f"학습 대화 / {role} / {doc_name}",
            target_label=f"{doc_name} 열기",
            text=content,
            href=_study_link(doc_id),
            recency=float(message.get("created_at") or 0.0),
        )

    for document in resolved_state.get("documents", []):
        if not isinstance(document, dict):
            continue
        doc_id = str(document.get("doc_id") or "").strip()
        if not doc_id:
            continue
        loaded = load_document(doc_id) or document
        doc_name = str(loaded.get("file_name") or document.get("file_name") or doc_id).strip() or doc_id
        joined_text = _document_search_text(loaded, doc_name)
        _append_result(
            results,
            query=query,
            source=f"학습자료 / {doc_name}",
            target_label=f"{doc_name} 열기",
            text=joined_text,
            href=_study_link(doc_id),
            recency=float(loaded.get("registered_at") or loaded.get("created_at") or 0.0),
            weight=8,
        )

    deduped: list[dict] = []
    seen: set[str] = set()
    for item in sorted(results, key=lambda row: (row["score"], row["recency"]), reverse=True):
        key = str(item["href"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(
            {
                "target_type": item["target_type"],
                "doc_id": item["doc_id"],
                "target_label": item["target_label"],
                "source": item["source"],
                "snippet": item["snippet"],
                "score": item["score"],
            }
        )
        if len(deduped) >= 8:
            break

    return {
        "schema_version": "coco_internal_search_panel.v1",
        "query": query,
        "created_at": time.time(),
        "results": deduped,
    }


def build_internal_search_reply(prompt: str, state: AppState | None) -> str | None:
    panel = build_internal_search_panel(prompt, state)
    if panel is None:
        return None

    query = str(panel.get("query") or "").strip()
    results = [item for item in panel.get("results") or [] if isinstance(item, dict)]
    if not results:
        return (
            f'"{query}" 관련 기록을 아직 찾지 못했어요.\n\n'
            "검색 대상은 현재 저장된 메인 채팅, 학습리스트 채팅, 등록 파일의 분석 텍스트입니다."
        )

    lines = [f'"{query}" 관련 기록을 찾았어요.', ""]
    for index, item in enumerate(results, start=1):
        href = "?chat=main" if item.get("target_type") == "main" else _study_link(str(item.get("doc_id") or ""))
        lines.append(
            f'{index}. [{item["target_label"]}]({href}) - {item["source"]}\n'
            f'   "{item["snippet"]}"'
        )
    return "\n".join(lines)
