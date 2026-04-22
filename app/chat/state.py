from __future__ import annotations

import json
import time
from pathlib import Path

from .contracts import AppState


APP_SUPPORT_DIR = Path.home() / "Library" / "Application Support" / "CocoAIStudy"
UPLOADS_DIR = APP_SUPPORT_DIR / "uploads"
DOCS_DIR = APP_SUPPORT_DIR / "data" / "files"
STATE_PATH = APP_SUPPORT_DIR / "app_state.json"


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


def persist_document(doc_id: str, file_name: str, file_path: str, analysis: dict, latest_user_query: str = "") -> None:
    payload = {
        "doc_id": doc_id,
        "file_name": file_name,
        "file_path": file_path,
        "latest_user_query": latest_user_query,
        "analysis": analysis,
    }
    (DOCS_DIR / f"{doc_id}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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
    for path in sorted(DOCS_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        doc_id = str(payload.get("doc_id") or path.stem).strip()
        if not doc_id:
            continue
        discovered.append(
            {
                "doc_id": doc_id,
                "file_name": str(payload.get("file_name") or doc_id),
                "file_path": str(payload.get("file_path") or ""),
                "created_at": float(path.stat().st_mtime),
                "latest_user_query": str(payload.get("latest_user_query") or ""),
            }
        )
    return discovered


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
            created_at = float(item.get("created_at") or doc_path.stat().st_mtime)
        except Exception:
            created_at = float(doc_path.stat().st_mtime)
        existing_docs.append(
            {
                "doc_id": doc_id,
                "file_name": str(item.get("file_name") or doc_id),
                "file_path": str(item.get("file_path") or ""),
                "created_at": created_at,
                "latest_user_query": str(item.get("latest_user_query") or ""),
            }
        )

    if not existing_docs:
        existing_docs = discover_documents_from_disk()

    existing_docs.sort(key=lambda item: float(item.get("created_at") or 0.0), reverse=True)

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
        clean_history.append(
            {
                "role": role,
                "content": content,
                "doc_id": doc_id,
                "created_at": created_at,
            }
        )
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
        refreshed["created_at"] = time.time()
        documents.pop(index)
        documents.insert(0, refreshed)
        state["documents"] = documents
        state["selected_doc_id"] = target
        return
    state["selected_doc_id"] = target


def append_message(state: AppState, role: str, content: str, doc_id: str | None = None) -> None:
    state.setdefault("chat_history", []).append(
        {
            "role": role,
            "content": content,
            "doc_id": doc_id,
            "created_at": time.time(),
        }
    )
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


def load_all_documents(state: AppState) -> list[dict]:
    loaded: list[dict] = []
    for item in state.get("documents", []):
        doc = load_document(item.get("doc_id"))
        if doc:
            loaded.append(doc)
    return loaded
