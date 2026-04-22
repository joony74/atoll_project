from __future__ import annotations

from .answer_validator import validate_answer
from .explanation_generator import generate_korean_explanation
from .math_engine import solve_math_problem
from .model_backend import get_default_backend
from .problem_classifier import classify_problem
from .problem_parser import parse_problem


def handle_math_tutor_chat(query: str, active_doc: dict | None, problem_context: dict, document_bundle: dict, debug: bool = False) -> dict:
    backend = get_default_backend()
    parsed = parse_problem(query, active_doc=active_doc, problem_context=problem_context, document_bundle=document_bundle)
    classified = classify_problem(parsed)
    solved = solve_math_problem(parsed, classified, backend=backend)
    validated = validate_answer(parsed, solved)
    detail = "detailed" if any(token in query for token in ("왜", "다시", "천천히", "자세히")) else "normal"
    answer = generate_korean_explanation(query, parsed, classified, validated, detail_level=detail)
    payload = {
        "answer": answer,
        "parsed_problem": parsed,
        "classification": classified,
        "solver_result": validated,
        "backend": {
            "family": backend.config.family,
            "model_name": backend.config.model_name,
            "mode": backend.config.mode,
        },
    }
    if not debug:
        payload.pop("parsed_problem", None)
        payload.pop("classification", None)
        payload.pop("solver_result", None)
        payload.pop("backend", None)
    return payload
