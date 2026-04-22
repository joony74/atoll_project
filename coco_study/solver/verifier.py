from __future__ import annotations

from typing import Any


ALLOWED_FINAL_STATUSES = {"completed", "failed", "needs_review"}


def verify_solution(problem: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    problem_type = str(result.get("problem_type") or problem.get("problem_type") or "unknown").strip()
    answer = str(result.get("answer") or "").strip()
    steps = [str(step).strip() for step in (result.get("solution_steps") or []) if str(step).strip()]
    status = str(result.get("status") or "").strip().lower()
    verification = dict(result.get("verification") or {})

    if status not in ALLOWED_FINAL_STATUSES:
        status = "failed"
        verification.setdefault("reason", "invalid_status")

    if not answer:
        status = "failed"
        verification.setdefault("reason", "missing_answer")

    if not steps:
        status = "failed"
        verification.setdefault("reason", "missing_steps")

    if problem_type == "linear_function" and "기울기" not in answer:
        status = "needs_review"
        verification.setdefault("reason", "unexpected_linear_answer_format")

    if problem_type == "quadratic_equation" and "x" not in answer:
        status = "needs_review"
        verification.setdefault("reason", "unexpected_quadratic_answer_format")

    if problem_type == "trigonometry_value" and answer == "":
        status = "failed"
        verification.setdefault("reason", "unexpected_trig_answer_format")

    result["status"] = status
    result["verification"] = verification
    result["problem_type"] = problem_type
    result["answer"] = answer
    result["solution_steps"] = steps
    return result

