from __future__ import annotations

import json
import time
from pathlib import Path

from .contracts import AppState


APP_SUPPORT_DIR = Path.home() / "Library" / "Application Support" / "CocoAIStudy"
UPLOADS_DIR = APP_SUPPORT_DIR / "uploads"
DOCS_DIR = APP_SUPPORT_DIR / "data" / "files"
STATE_PATH = APP_SUPPORT_DIR / "app_state.json"
INITIAL_STUDY_CARD_KIND = "initial_study_card"
INITIAL_STUDY_CARD_PREFIX = "이미지에서 읽은 내용을 먼저 정리했어요."


def default_state() -> AppState:
    return {
        "documents": [],
        "selected_doc_id": None,
        "chat_mode": "main",
        "last_active_chat_mode": "main",
        "last_active_doc_id": None,
        "last_active_at": 0.0,
        "main_chat_history": [],
        "main_chat_context": {
            "last_intent": "general",
            "last_concept_term": None,
            "last_concept_stage": None,
            "last_updated_at": 0.0,
        },
        "custom_concepts": {},
        "chat_history": [],
        "booted_at": time.time(),
    }


def ensure_dirs() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)


def migrate_state(state: dict | None) -> AppState:
    merged: AppState = default_state()
    if isinstance(state, dict):
        merged.update(state)
    if not isinstance(merged.get("documents"), list):
        merged["documents"] = []
    if not isinstance(merged.get("main_chat_history"), list):
        merged["main_chat_history"] = []
    if not isinstance(merged.get("main_chat_context"), dict):
        merged["main_chat_context"] = {}
    if not isinstance(merged.get("custom_concepts"), dict):
        merged["custom_concepts"] = {}
    if not isinstance(merged.get("chat_history"), list):
        merged["chat_history"] = []
    merged["chat_mode"] = "study" if str(merged.get("chat_mode") or "").strip() == "study" else "main"
    merged["last_active_chat_mode"] = (
        "study" if str(merged.get("last_active_chat_mode") or "").strip() == "study" else "main"
    )
    if merged.get("selected_doc_id") is not None:
        merged["selected_doc_id"] = str(merged["selected_doc_id"]).strip() or None
    if merged.get("last_active_doc_id") is not None:
        merged["last_active_doc_id"] = str(merged["last_active_doc_id"]).strip() or None
    try:
        merged["last_active_at"] = float(merged.get("last_active_at") or 0.0)
    except Exception:
        merged["last_active_at"] = 0.0
    try:
        merged["booted_at"] = float(merged.get("booted_at") or time.time())
    except Exception:
        merged["booted_at"] = time.time()
    context = merged.setdefault("main_chat_context", {})
    context["last_intent"] = str(context.get("last_intent") or "general").strip() or "general"
    context["last_concept_term"] = str(context.get("last_concept_term") or "").strip() or None
    context["last_concept_stage"] = str(context.get("last_concept_stage") or "").strip() or None
    try:
        context["last_updated_at"] = float(context.get("last_updated_at") or 0.0)
    except Exception:
        context["last_updated_at"] = 0.0
    normalized_concepts: dict[str, dict] = {}
    for key, value in dict(merged.get("custom_concepts") or {}).items():
        if isinstance(value, str):
            term = str(key or "").strip()
            summary = str(value or "").strip()
            confidence = "low"
            source = "chat"
            updated_at = 0.0
        elif isinstance(value, dict):
            term = str(value.get("term") or key or "").strip()
            summary = str(value.get("summary") or "").strip()
            confidence = str(value.get("confidence") or "low").strip() or "low"
            source = str(value.get("source") or "chat").strip() or "chat"
            try:
                updated_at = float(value.get("updated_at") or 0.0)
            except Exception:
                updated_at = 0.0
        else:
            continue
        if not term or not summary:
            continue
        normalized_concepts[term] = {
            "term": term,
            "summary": summary,
            "confidence": confidence if confidence in {"low", "medium", "high"} else "low",
            "source": source,
            "updated_at": updated_at,
        }
    merged["custom_concepts"] = normalized_concepts
    return merged


def load_state() -> AppState:
    if not STATE_PATH.exists():
        return default_state()
    try:
        payload = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return default_state()
    return migrate_state(payload)


def save_state(state: AppState) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_float(value: object, fallback: float = 0.0) -> float:
    try:
        return float(value or fallback)
    except Exception:
        return fallback


def _stat_registered_fallback(path: Path) -> float:
    try:
        stat = path.stat()
    except Exception:
        return time.time()
    return float(getattr(stat, "st_birthtime", 0.0) or stat.st_mtime)


def _analysis_started_at(payload: dict) -> float:
    analysis = payload.get("analysis") if isinstance(payload, dict) else {}
    if not isinstance(analysis, dict):
        return 0.0
    return _safe_float(analysis.get("analysis_started_at"), 0.0)


def _document_registered_at(payload: dict, path: Path, state_item: dict | None = None) -> float:
    for source in (
        payload.get("registered_at"),
        payload.get("created_at"),
        _analysis_started_at(payload),
        (state_item or {}).get("registered_at"),
        (state_item or {}).get("created_at"),
    ):
        value = _safe_float(source, 0.0)
        if value > 0:
            return value
    return _stat_registered_fallback(path)


def _document_last_opened_at(payload: dict, state_item: dict | None = None) -> float:
    return _safe_float((state_item or {}).get("last_opened_at"), _safe_float(payload.get("last_opened_at"), 0.0))


def _sort_documents_by_registered_at(documents: list[dict]) -> list[dict]:
    return sorted(
        documents,
        key=lambda item: (
            _safe_float(item.get("registered_at"), _safe_float(item.get("created_at"), 0.0)),
            str(item.get("doc_id") or ""),
        ),
        reverse=True,
    )


def persist_document(
    doc_id: str,
    file_name: str,
    file_path: str,
    analysis: dict,
    latest_user_query: str = "",
    registered_at: float | None = None,
) -> None:
    doc_path = DOCS_DIR / f"{doc_id}.json"
    previous: dict = {}
    if doc_path.exists():
        try:
            previous = json.loads(doc_path.read_text(encoding="utf-8"))
        except Exception:
            previous = {}
    if registered_at is None:
        registered_at = _document_registered_at({"analysis": analysis, **previous}, doc_path)
    payload = {
        "doc_id": doc_id,
        "file_name": file_name,
        "file_path": file_path,
        "registered_at": float(registered_at),
        "created_at": float(registered_at),
        "last_opened_at": _safe_float(previous.get("last_opened_at"), 0.0),
        "latest_user_query": latest_user_query,
        "analysis": analysis,
    }
    doc_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_document(doc_id: str | None) -> dict | None:
    if not doc_id:
        return None
    path = DOCS_DIR / f"{doc_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def delete_document(doc_id: str) -> None:
    path = DOCS_DIR / f"{doc_id}.json"
    if path.exists():
        path.unlink()


def discover_documents_from_disk() -> list[dict]:
    discovered: list[dict] = []
    for path in DOCS_DIR.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        doc_id = str(payload.get("doc_id") or path.stem).strip()
        if not doc_id:
            continue
        registered_at = _document_registered_at(payload, path)
        discovered.append(
            {
                "doc_id": doc_id,
                "file_name": str(payload.get("file_name") or doc_id),
                "file_path": str(payload.get("file_path") or ""),
                "created_at": registered_at,
                "registered_at": registered_at,
                "last_opened_at": _document_last_opened_at(payload),
                "latest_user_query": str(payload.get("latest_user_query") or ""),
            }
        )
    return _sort_documents_by_registered_at(discovered)


def sync_documents(state: AppState) -> AppState:
    existing_docs: list[dict] = []
    for item in state.get("documents", []):
        if not isinstance(item, dict):
            continue
        doc_id = str(item.get("doc_id") or "").strip()
        if not doc_id:
            continue
        doc_path = DOCS_DIR / f"{doc_id}.json"
        if not doc_path.exists():
            continue
        try:
            payload = json.loads(doc_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        try:
            registered_at = _document_registered_at(payload, doc_path, item)
        except Exception:
            registered_at = _stat_registered_fallback(doc_path)
        existing_docs.append(
            {
                "doc_id": doc_id,
                "file_name": str(payload.get("file_name") or item.get("file_name") or doc_id),
                "file_path": str(payload.get("file_path") or item.get("file_path") or ""),
                "created_at": registered_at,
                "registered_at": registered_at,
                "last_opened_at": _document_last_opened_at(payload, item),
                "latest_user_query": str(item.get("latest_user_query") or payload.get("latest_user_query") or ""),
            }
        )

    if not existing_docs:
        existing_docs = discover_documents_from_disk()

    existing_docs = _sort_documents_by_registered_at(existing_docs)

    state["documents"] = existing_docs
    clean_main_history: list[dict] = []
    for item in state.get("main_chat_history", []):
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip()
        content = str(item.get("content") or "").strip()
        if role not in {"assistant", "user"} or not content:
            continue
        try:
            created_at = float(item.get("created_at") or time.time())
        except Exception:
            created_at = time.time()
        clean_main_history.append(
            {
                "role": role,
                "content": content,
                "doc_id": None,
                "created_at": created_at,
            }
        )
    state["main_chat_history"] = clean_main_history[-24:]

    if not existing_docs:
        state["chat_history"] = []
        state["selected_doc_id"] = None
        state["chat_mode"] = "main"
        state["last_active_chat_mode"] = "main"
        state["last_active_doc_id"] = None
        return state

    selected_doc_id = str(state.get("selected_doc_id") or "").strip()
    if not selected_doc_id or not any(doc["doc_id"] == selected_doc_id for doc in existing_docs):
        state["selected_doc_id"] = existing_docs[0]["doc_id"] if existing_docs else None

    clean_history: list[dict] = []
    available_ids = {doc["doc_id"] for doc in existing_docs}
    for item in state.get("chat_history", []):
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip()
        content = str(item.get("content") or "").strip()
        if role not in {"assistant", "user"} or not content:
            continue
        doc_id = str(item.get("doc_id") or "").strip() or None
        if doc_id and doc_id not in available_ids:
            continue
        try:
            created_at = float(item.get("created_at") or time.time())
        except Exception:
            created_at = time.time()
        message = {
            "role": role,
            "content": content,
            "doc_id": doc_id,
            "created_at": created_at,
        }
        kind = str(item.get("kind") or "").strip()
        if kind:
            message["kind"] = kind
        preview_image_path = str(item.get("preview_image_path") or "").strip()
        if preview_image_path:
            message["preview_image_path"] = preview_image_path
        preview_image_label = str(item.get("preview_image_label") or "").strip()
        if preview_image_label:
            message["preview_image_label"] = preview_image_label
        clean_history.append(message)
    state["chat_history"] = clean_history[-24:]
    return state


def active_chat_mode(state: AppState) -> str:
    if not state.get("documents"):
        return "main"
    return "study" if str(state.get("chat_mode") or "").strip() == "study" else "main"


def mark_active_target(state: AppState, mode: str, doc_id: str | None = None) -> None:
    resolved_mode = "study" if mode == "study" and state.get("documents") else "main"
    resolved_doc_id = str(doc_id or "").strip() or None
    if resolved_mode != "study":
        resolved_doc_id = None
    state["chat_mode"] = resolved_mode
    state["selected_doc_id"] = resolved_doc_id
    state["last_active_chat_mode"] = resolved_mode
    state["last_active_doc_id"] = resolved_doc_id
    state["last_active_at"] = time.time()


def restore_recent_target(state: AppState) -> None:
    last_active_mode = str(state.get("last_active_chat_mode") or "").strip()
    last_active_doc_id = str(state.get("last_active_doc_id") or "").strip() or None
    if last_active_mode == "study" and state.get("documents"):
        if last_active_doc_id and any(
            str(doc.get("doc_id") or "").strip() == last_active_doc_id for doc in state["documents"]
        ):
            mark_active_target(state, "study", last_active_doc_id)
            promote_document(state, last_active_doc_id)
            return
    elif last_active_mode == "main":
        mark_active_target(state, "main")
        return

    latest_main_at = 0.0
    for item in reversed(state.get("main_chat_history", [])):
        if not isinstance(item, dict):
            continue
        try:
            latest_main_at = float(item.get("created_at") or 0.0)
        except Exception:
            latest_main_at = 0.0
        if latest_main_at:
            break

    latest_study_at = 0.0
    latest_study_doc_id: str | None = None
    for item in reversed(state.get("chat_history", [])):
        if not isinstance(item, dict):
            continue
        doc_id = str(item.get("doc_id") or "").strip()
        if not doc_id:
            continue
        try:
            latest_study_at = float(item.get("created_at") or 0.0)
        except Exception:
            latest_study_at = 0.0
        latest_study_doc_id = doc_id
        break

    if latest_main_at == 0.0 and latest_study_at == 0.0:
        if state.get("documents"):
            mark_active_target(state, "study", str(state["documents"][0].get("doc_id") or "").strip() or None)
        else:
            mark_active_target(state, "main")
        return

    if latest_study_at > latest_main_at and latest_study_doc_id:
        mark_active_target(state, "study", latest_study_doc_id)
        promote_document(state, latest_study_doc_id)
        return

    mark_active_target(state, "main")


def promote_document(state: AppState, doc_id: str | None) -> None:
    target = str(doc_id or "").strip()
    if not target:
        return
    documents = list(state.get("documents", []))
    for index, item in enumerate(documents):
        if str(item.get("doc_id") or "").strip() != target:
            continue
        refreshed = dict(item)
        refreshed["last_opened_at"] = time.time()
        documents[index] = refreshed
        state["documents"] = _sort_documents_by_registered_at(documents)
        state["selected_doc_id"] = target
        return
    state["selected_doc_id"] = target


def append_message(
    state: AppState,
    role: str,
    content: str,
    doc_id: str | None = None,
    kind: str | None = None,
    preview_image_path: str | None = None,
    preview_image_label: str | None = None,
) -> None:
    message: dict = {
        "role": role,
        "content": content,
        "doc_id": doc_id,
        "created_at": time.time(),
    }
    normalized_kind = str(kind or "").strip()
    if normalized_kind:
        message["kind"] = normalized_kind
    normalized_preview = str(preview_image_path or "").strip()
    if normalized_preview:
        message["preview_image_path"] = normalized_preview
    normalized_preview_label = str(preview_image_label or "").strip()
    if normalized_preview_label:
        message["preview_image_label"] = normalized_preview_label
    state.setdefault("chat_history", []).append(message)
    state["chat_history"] = state["chat_history"][-24:]


def append_main_message(state: AppState, role: str, content: str) -> None:
    state.setdefault("main_chat_history", []).append(
        {
            "role": role,
            "content": content,
            "doc_id": None,
            "created_at": time.time(),
        }
    )
    state["main_chat_history"] = state["main_chat_history"][-24:]


def _is_initial_study_card_message(item: dict, doc_id: str) -> bool:
    if not isinstance(item, dict):
        return False
    if str(item.get("doc_id") or "").strip() != doc_id:
        return False
    if str(item.get("role") or "").strip() != "assistant":
        return False
    if str(item.get("kind") or "").strip() == INITIAL_STUDY_CARD_KIND:
        return True
    return str(item.get("content") or "").strip().startswith(INITIAL_STUDY_CARD_PREFIX)


def clear_active_chat_history(
    state: AppState,
    *,
    initial_study_message: str | None = None,
) -> None:
    if active_chat_mode(state) == "main":
        state["main_chat_history"] = []
        return

    selected_doc_id = str(state.get("selected_doc_id") or "").strip()
    if not selected_doc_id:
        return

    generated_practice = state.get("generated_practice_by_doc")
    if isinstance(generated_practice, dict):
        generated_practice.pop(selected_doc_id, None)

    preserved_initial: dict | None = None
    for item in state.get("chat_history", []):
        if _is_initial_study_card_message(item, selected_doc_id):
            preserved_initial = dict(item)
            preserved_initial["kind"] = INITIAL_STUDY_CARD_KIND
            break

    if preserved_initial is None:
        content = str(initial_study_message or "").strip()
        if content:
            preserved_initial = {
                "role": "assistant",
                "content": content,
                "doc_id": selected_doc_id,
                "created_at": time.time(),
                "kind": INITIAL_STUDY_CARD_KIND,
            }

    state["chat_history"] = [
        item
        for item in state.get("chat_history", [])
        if str((item or {}).get("doc_id") or "").strip() != selected_doc_id
    ]
    if preserved_initial is not None:
        state["chat_history"].append(preserved_initial)
    state["chat_history"] = state["chat_history"][-24:]

    for item in state.get("documents", []):
        if str(item.get("doc_id") or "").strip() == selected_doc_id:
            item["latest_user_query"] = ""
            break


def load_all_documents(state: AppState) -> list[dict]:
    loaded: list[dict] = []
    for item in state.get("documents", []):
        doc = load_document(item.get("doc_id"))
        if doc:
            loaded.append(doc)
    return loaded
