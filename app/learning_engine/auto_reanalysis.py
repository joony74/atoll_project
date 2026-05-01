from __future__ import annotations

import copy
import json
import time
from pathlib import Path
from typing import Any, Callable

AnalysisRunner = Callable[[str, str], dict[str, Any]]

REANALYSIS_PROMPTS = (
    "학습점검에서 분석실패가 감지되었습니다. 문제 문장과 수식 후보를 다시 OCR 점검하고 풀이 검증까지 재분석하세요.",
    "수식 복원이 불안정합니다. 숫자, 연산기호, 선택지, 표/그림 단서를 우선하여 같은 이미지의 학습카드를 다시 분석하세요.",
)

READY_STATUSES = {"verified", "completed", "matched", "passed"}
FAILED_STATUSES = {"failed", "needs_review", "review"}


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _as_text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item or "").strip() for item in value if str(item or "").strip()]


def _analysis_parts(analysis: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    structured = _as_dict(analysis.get("structured_problem"))
    solved = _as_dict(analysis.get("solve_result"))
    return structured, solved


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except Exception:
        return 0.0


def analysis_reanalysis_reasons(analysis: dict[str, Any]) -> list[str]:
    structured, solved = _analysis_parts(analysis)
    expressions = _as_text_list(structured.get("expressions"))
    candidates = _as_text_list(structured.get("source_text_candidates"))
    problem_text = str(structured.get("normalized_problem_text") or "").strip()
    confidence = _safe_float(structured.get("confidence"))
    status = str(solved.get("validation_status") or "").strip().lower()
    answer = str(solved.get("matched_choice") or solved.get("computed_answer") or "").strip()
    steps = _as_text_list(solved.get("steps"))

    reasons: list[str] = []
    if not problem_text and not expressions and not candidates:
        reasons.append("missing_recognition")
    elif confidence < 0.45:
        reasons.append("low_recognition_confidence")
    if status in FAILED_STATUSES:
        reasons.append(f"solver_{status}")
    if status not in READY_STATUSES and not answer and not steps:
        reasons.append("missing_solution_signal")
    return reasons


def analysis_quality_score(analysis: dict[str, Any]) -> float:
    structured, solved = _analysis_parts(analysis)
    confidence = _safe_float(structured.get("confidence"))
    problem_text = str(structured.get("normalized_problem_text") or "").strip()
    expressions = _as_text_list(structured.get("expressions"))
    candidates = _as_text_list(structured.get("source_text_candidates"))
    status = str(solved.get("validation_status") or "").strip().lower()
    answer = str(solved.get("matched_choice") or solved.get("computed_answer") or "").strip()
    steps = _as_text_list(solved.get("steps"))

    score = confidence
    if problem_text:
        score += 0.16
    if expressions:
        score += min(0.18, 0.06 * len(expressions))
    if candidates:
        score += min(0.08, 0.02 * len(candidates))
    if status in READY_STATUSES:
        score += 0.38
    elif status in FAILED_STATUSES:
        score -= 0.22
    if answer:
        score += 0.16
    if steps:
        score += min(0.12, 0.03 * len(steps))
    return max(-1.0, min(2.0, score))


def _with_auto_reanalysis_metadata(
    analysis: dict[str, Any],
    *,
    status: str,
    attempts: list[dict[str, Any]],
    initial_reasons: list[str],
    selected_attempt: int | None = None,
) -> dict[str, Any]:
    upgraded = copy.deepcopy(analysis)
    structured = _as_dict(upgraded.get("structured_problem"))
    metadata = _as_dict(structured.get("metadata"))
    metadata["auto_reanalysis"] = {
        "status": status,
        "attempt_count": len(attempts),
        "initial_reasons": initial_reasons,
        "selected_attempt": selected_attempt,
        "attempts": attempts,
        "updated_at": time.time(),
    }
    structured["metadata"] = metadata
    upgraded["structured_problem"] = structured
    return upgraded


def _append_review_queue(
    queue_path: Path,
    *,
    file_path: str,
    doc_id: str,
    file_name: str,
    reasons: list[str],
    analysis: dict[str, Any],
) -> None:
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    structured, solved = _analysis_parts(analysis)
    record = {
        "schema_version": "coco_auto_reanalysis_review.v1",
        "created_at": time.time(),
        "doc_id": doc_id,
        "file_name": file_name,
        "file_path": file_path,
        "reasons": reasons,
        "confidence": structured.get("confidence"),
        "validation_status": solved.get("validation_status"),
        "problem_preview": str(structured.get("normalized_problem_text") or "")[:240],
        "expressions": _as_text_list(structured.get("expressions"))[:8],
    }
    with queue_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _remove_review_queue_entries(queue_path: Path, *, doc_id: str, file_path: str) -> None:
    if not queue_path.exists():
        return
    retained: list[str] = []
    changed = False
    for line in queue_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except Exception:
            retained.append(line)
            continue
        same_doc = bool(doc_id) and str(item.get("doc_id") or "") == doc_id
        same_file = bool(file_path) and str(item.get("file_path") or "") == file_path
        if same_doc or same_file:
            changed = True
            continue
        retained.append(json.dumps(item, ensure_ascii=False))
    if changed:
        queue_path.write_text(("\n".join(retained) + "\n") if retained else "", encoding="utf-8")


def maybe_upgrade_registered_analysis(
    *,
    file_path: str,
    initial_analysis: dict[str, Any],
    analyzer: AnalysisRunner,
    doc_id: str = "",
    file_name: str = "",
    review_queue_path: str | Path | None = None,
    max_attempts: int = 2,
) -> dict[str, Any]:
    initial_reasons = analysis_reanalysis_reasons(initial_analysis)
    queue_path = Path(review_queue_path) if review_queue_path is not None else None

    if not initial_reasons:
        if queue_path is not None:
            _remove_review_queue_entries(queue_path, doc_id=doc_id, file_path=file_path)
        return _with_auto_reanalysis_metadata(
            initial_analysis,
            status="healthy",
            attempts=[],
            initial_reasons=[],
        )

    initial_score = analysis_quality_score(initial_analysis)
    best_analysis = initial_analysis
    best_score = initial_score
    best_attempt: int | None = None
    attempts: list[dict[str, Any]] = []

    for index, prompt in enumerate(REANALYSIS_PROMPTS[: max(0, max_attempts)], start=1):
        try:
            candidate = analyzer(file_path, prompt)
        except Exception as exc:
            attempts.append({"index": index, "status": "error", "error": str(exc), "score": None})
            continue

        candidate_reasons = analysis_reanalysis_reasons(candidate)
        candidate_score = analysis_quality_score(candidate)
        attempts.append(
            {
                "index": index,
                "status": "ok",
                "score": candidate_score,
                "reasons": candidate_reasons,
            }
        )
        if candidate_score > best_score + 0.05:
            best_analysis = candidate
            best_score = candidate_score
            best_attempt = index
        if not candidate_reasons:
            break

    final_reasons = analysis_reanalysis_reasons(best_analysis)
    accepted = best_attempt is not None and best_analysis is not initial_analysis
    status = "upgraded" if accepted else "review_queued" if final_reasons else "rechecked"
    result = _with_auto_reanalysis_metadata(
        best_analysis,
        status=status,
        attempts=attempts,
        initial_reasons=initial_reasons,
        selected_attempt=best_attempt,
    )

    if final_reasons and queue_path is not None:
        _append_review_queue(
            queue_path,
            file_path=file_path,
            doc_id=doc_id,
            file_name=file_name,
            reasons=final_reasons,
            analysis=result,
        )
    elif queue_path is not None:
        _remove_review_queue_entries(queue_path, doc_id=doc_id, file_path=file_path)
    return result
