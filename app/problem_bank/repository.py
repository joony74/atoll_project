from __future__ import annotations

import json
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.models.problem_schema import ProblemSchema
from app.models.solve_result import SolveResult


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROBLEM_BANK_ROOT = PROJECT_ROOT / "data" / "problem_bank"
CATALOG_PATH = PROBLEM_BANK_ROOT / "catalog.json"


class ProblemBankError(RuntimeError):
    pass


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProblemBankError(f"problem bank file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProblemBankError(f"problem bank file is not valid JSON: {path}") from exc


def _resolve_path(path_text: str) -> Path:
    path = Path(str(path_text or ""))
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, Any]:
    if not CATALOG_PATH.exists():
        return {"schema_version": "problem_bank_catalog.v1", "banks": []}
    payload = _read_json(CATALOG_PATH)
    if not isinstance(payload, dict):
        raise ProblemBankError("problem bank catalog must be a JSON object")
    payload.setdefault("banks", [])
    return payload


def list_banks() -> list[dict[str, Any]]:
    banks = load_catalog().get("banks") or []
    return [dict(item) for item in banks if isinstance(item, dict)]


def _bank_entry(bank_id: str) -> dict[str, Any]:
    target = str(bank_id or "").strip()
    for bank in list_banks():
        if str(bank.get("bank_id") or "").strip() == target:
            return bank
    raise ProblemBankError(f"unknown problem bank: {target}")


@lru_cache(maxsize=16)
def load_manifest(bank_id: str = "competition_math") -> dict[str, Any]:
    entry = _bank_entry(bank_id)
    manifest_path = _resolve_path(str(entry.get("manifest_path") or ""))
    payload = _read_json(manifest_path)
    if not isinstance(payload, dict):
        raise ProblemBankError(f"problem bank manifest must be a JSON object: {manifest_path}")
    payload["_manifest_path"] = str(manifest_path)
    payload["_bank_root"] = str(manifest_path.parent)
    return payload


@lru_cache(maxsize=16)
def load_index(bank_id: str = "competition_math") -> list[dict[str, Any]]:
    manifest = load_manifest(bank_id)
    bank_root = Path(manifest["_bank_root"])
    index_path = bank_root / str((manifest.get("indexes") or {}).get("lightweight") or "")
    payload = _read_json(index_path)
    if not isinstance(payload, list):
        raise ProblemBankError(f"problem bank index must be a JSON array: {index_path}")
    return [dict(item) for item in payload if isinstance(item, dict)]


@lru_cache(maxsize=128)
def _load_shard(bank_id: str, shard_path: str) -> list[dict[str, Any]]:
    manifest = load_manifest(bank_id)
    path = Path(manifest["_bank_root"]) / shard_path
    payload = _read_json(path)
    if not isinstance(payload, list):
        raise ProblemBankError(f"problem bank shard must be a JSON array: {path}")
    return [dict(item) for item in payload if isinstance(item, dict)]


def _normalize_query(text: str) -> list[str]:
    lowered = str(text or "").lower()
    lowered = re.sub(r"\\[a-zA-Z]+", " ", lowered)
    lowered = re.sub(r"[^a-z0-9가-힣]+", " ", lowered)
    return [token for token in lowered.split() if len(token) >= 2]


def _search_score(item: dict[str, Any], query: str, tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    haystack = " ".join(
        [
            str(item.get("problem_preview") or ""),
            str(item.get("solution_preview") or ""),
            str(item.get("subject") or ""),
            " ".join(str(token) for token in item.get("keywords") or []),
        ]
    ).lower()
    score = 0.0
    compact_query = str(query or "").strip().lower()
    if compact_query and compact_query in haystack:
        score += 8.0
    for token in tokens:
        count = haystack.count(token)
        if count:
            score += min(4.0, 1.0 + count * 0.25)
        if token in [str(key).lower() for key in item.get("keywords") or []]:
            score += 1.5
    if str(item.get("answer") or "").strip() and any(token == str(item.get("answer")).lower() for token in tokens):
        score += 2.0
    return score


def search_problems(
    query: str = "",
    *,
    bank_id: str = "competition_math",
    subject_slug: str | None = None,
    level_number: int | None = None,
    include_review: bool = False,
    include_asy: bool = True,
    limit: int = 20,
) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit or 20), 100))
    subject_filter = str(subject_slug or "").strip()
    level_filter = int(level_number) if level_number else None
    tokens = _normalize_query(query)
    bank_ids = [str(bank.get("bank_id") or "").strip() for bank in list_banks()] if bank_id == "all" else [bank_id]
    scored: list[tuple[float, dict[str, Any]]] = []
    for current_bank_id in bank_ids:
        if not current_bank_id:
            continue
        for item in load_index(current_bank_id):
            if subject_filter and str(item.get("subject_slug") or "") != subject_filter:
                continue
            if level_filter is not None and int(item.get("level_number") or 0) != level_filter:
                continue
            if not include_review and bool(item.get("needs_review")):
                continue
            if not include_asy and bool(item.get("has_asy")):
                continue
            score = _search_score(item, query, tokens)
            if tokens and score <= 0:
                continue
            enriched = dict(item)
            enriched["bank_id"] = str(enriched.get("bank_id") or current_bank_id)
            enriched["score"] = round(score, 4)
            scored.append((score, enriched))
    scored.sort(
        key=lambda pair: (
            pair[0],
            -int(pair[1].get("needs_review") or 0),
            -int(pair[1].get("level_number") or 0),
            str(pair[1].get("id") or ""),
        ),
        reverse=True,
    )
    return [item for _, item in scored[:limit]]


def load_problem(problem_id: str, *, bank_id: str = "competition_math") -> dict[str, Any]:
    target = str(problem_id or "").strip()
    if not target:
        raise ProblemBankError("problem_id is required")
    if bank_id == "auto" and ":" in target:
        inferred = target.split(":", 1)[0].strip()
        if inferred:
            bank_id = inferred
    for item in load_index(bank_id):
        if str(item.get("id") or "") != target:
            continue
        for record in _load_shard(bank_id, str(item.get("shard_path") or "")):
            if str(record.get("id") or "") == target:
                return record
        raise ProblemBankError(f"problem id is in index but missing from shard: {target}")
    raise ProblemBankError(f"unknown problem id: {target}")


def _solution_steps(record: dict[str, Any], max_steps: int = 4) -> list[str]:
    outline = ((record.get("learning") or {}).get("step_outline") or [])
    steps = [str(item or "").strip() for item in outline if str(item or "").strip()]
    if steps:
        return steps[:max_steps]
    solution_plain = str((record.get("content") or {}).get("solution_plain") or "")
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", solution_plain) if part.strip()]
    return parts[:max_steps] or ["문제은행에 저장된 원풀이를 기준으로 설명할 수 있어요."]


def record_to_analysis(record: dict[str, Any], *, user_query: str = "") -> dict[str, Any]:
    content = record.get("content") or {}
    answer = record.get("answer") or {}
    taxonomy = record.get("taxonomy") or {}
    metadata = record.get("metadata") or {}
    quality = metadata.get("quality") or {}
    problem_text = str(content.get("problem_latex") or content.get("problem_plain") or "")
    final_answer = str(answer.get("final_normalized") or answer.get("final_raw") or "")
    steps = _solution_steps(record)
    status = "verified" if final_answer and not quality.get("needs_review") else "needs_review"

    structured_problem = ProblemSchema(
        source_text_candidates=[problem_text],
        normalized_problem_text=problem_text,
        expressions=[],
        choices=[],
        question_type="subjective",
        math_topic=str(taxonomy.get("subject_slug") or taxonomy.get("subject") or "competition_math"),
        target_question="문제은행 풀이",
        confidence=1.0,
        metadata={
            "source": "problem_bank",
            "problem_bank_record_id": record.get("id"),
            "problem_bank_source": record.get("source"),
            "problem_bank_taxonomy": taxonomy,
            "problem_bank_structure": record.get("structure"),
            "problem_bank_quality": quality,
            "reference_solution_latex": content.get("solution_latex") or "",
            "reference_solution_plain": content.get("solution_plain") or "",
            "user_query": user_query,
        },
    )
    solved = SolveResult(
        solver_name="problem_bank_solution",
        computed_answer=final_answer,
        steps=steps,
        matched_choice="",
        confidence=1.0 if final_answer else 0.75,
        validation_status=status,
        explanation=build_problem_bank_intro(record),
        debug={
            "answer_candidates": answer.get("candidates") or [],
            "answer_extraction_method": answer.get("extraction_method"),
        },
    )
    return {
        "analysis_started_at": time.time(),
        "analysis_finished_at": time.time(),
        "structured_problem": structured_problem.model_dump(),
        "solve_result": solved.model_dump(),
        "problem_bank_record": record,
    }


def record_to_document(record: dict[str, Any], *, user_query: str = "") -> dict[str, Any]:
    record_id = str(record.get("id") or "")
    file_name = problem_display_name(record)
    return {
        "doc_id": record_id.replace(":", "__"),
        "file_name": file_name,
        "file_path": "",
        "registered_at": time.time(),
        "created_at": time.time(),
        "latest_user_query": user_query,
        "analysis": record_to_analysis(record, user_query=user_query),
    }


def problem_display_name(record: dict[str, Any]) -> str:
    taxonomy = record.get("taxonomy") or {}
    source = record.get("source") or {}
    original_index = source.get("original_index")
    subject = str(taxonomy.get("subject") or "Problem")
    level = str(taxonomy.get("level") or "").replace("Level ", "L")
    suffix = f"#{int(original_index):05d}" if isinstance(original_index, int) else str(record.get("id") or "")[-8:]
    return f"{subject} {level} {suffix}".strip()


def build_problem_bank_intro(record: dict[str, Any]) -> str:
    taxonomy = record.get("taxonomy") or {}
    answer = record.get("answer") or {}
    subject = str(taxonomy.get("subject") or "수학")
    level = str(taxonomy.get("level") or "").strip()
    final_answer = str(answer.get("final_normalized") or answer.get("final_raw") or "").strip()
    bits = [f"문제은행의 {subject} {level} 문제예요.".strip()]
    if final_answer:
        bits.append(f"저장된 원풀이 기준 최종답은 {final_answer}입니다.")
    else:
        bits.append("저장된 원풀이는 있지만 최종답 표기는 따로 확인이 필요합니다.")
    bits.append("원문 풀이를 바탕으로 한국어 설명과 힌트를 이어서 만들 수 있어요.")
    return " ".join(bits)


def clear_caches() -> None:
    load_catalog.cache_clear()
    load_manifest.cache_clear()
    load_index.cache_clear()
    _load_shard.cache_clear()
