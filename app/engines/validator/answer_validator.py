from __future__ import annotations

from app.models.problem_schema import ProblemSchema
from app.models.solve_result import SolveResult


def _normalize(text: str) -> str:
    return str(text or "").strip().replace(" ", "")


def validate_answer(problem: ProblemSchema, solver_result: dict) -> SolveResult:
    answer = str(solver_result.get("computed_answer") or "").strip()
    steps = [str(step).strip() for step in solver_result.get("steps") or [] if str(step).strip()]
    matched_choice = ""
    for choice in problem.choices:
        if answer and _normalize(answer) in _normalize(choice):
            matched_choice = choice
            break

    validation_status = "verified"
    if not answer:
        validation_status = "failed"
    elif problem.choices and not matched_choice:
        validation_status = "needs_review"

    return SolveResult(
        solver_name=str(solver_result.get("solver_name") or "unsolved"),
        computed_answer=answer,
        steps=steps,
        matched_choice=matched_choice,
        confidence=float(solver_result.get("confidence") or 0.0),
        validation_status=validation_status,
    )
