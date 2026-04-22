from __future__ import annotations

from coco_engine.models.problem_schema import ProblemSchema
from coco_engine.models.solve_result import SolveResult


def build_debug_report(
    *,
    ocr_result: dict,
    vision_result: dict,
    merged_result: dict,
    problem: ProblemSchema | None,
    selected_solver: str,
    solved: SolveResult | None,
    route: dict,
    failure_point: str = "",
) -> dict:
    return {
        "ocr_result": ocr_result,
        "vision_result": vision_result,
        "merged_normalized_text": merged_result.get("normalized_problem_text") or merged_result.get("merged_text") or "",
        "learning_retrieval": merged_result.get("learning_retrieval") or {},
        "learning_recovery": merged_result.get("learning_recovery") or {},
        "analysis_flags": merged_result.get("flag_profile") or {},
        "web_enrichment": merged_result.get("web_enrichment") or {},
        "comparison_report": (merged_result.get("web_enrichment") or {}).get("comparison_report") or {},
        "structured_problem_candidate": problem.model_dump() if problem else {},
        "detected_topic": problem.math_topic if problem else "unknown",
        "selected_solver": selected_solver,
        "computed_result": solved.computed_answer if solved else "",
        "final_choice_match": solved.matched_choice if solved else "",
        "confidence_score": solved.confidence if solved else 0.0,
        "route": route,
        "failure_point": failure_point,
    }
