from __future__ import annotations

from coco_engine.models.problem_schema import ProblemSchema


def route_solver(problem: ProblemSchema) -> str:
    metadata = problem.metadata or {}
    hinted_solver = str(metadata.get("reasoning_hint_solver") or "").strip()
    hinted_topic = str(metadata.get("reasoning_hint_topic") or "").strip()
    topic = problem.math_topic or hinted_topic
    text = f"{problem.normalized_problem_text} {' '.join(problem.expressions)}"
    if hinted_solver and problem.math_topic in {"", "unknown", "arithmetic"}:
        return hinted_solver
    if topic == "worksheet" or len(problem.metadata.get("subproblems") or []) >= 2:
        return "rule_engine"
    if topic == "graph_limit":
        return "rule_engine"
    if any(token in text for token in ("기울기", "절편", "좌표", "그래프")):
        return "rule_engine"
    if topic == "trigonometry":
        return "trig_solver"
    if topic in {"linear_equation", "quadratic", "function"}:
        return "algebra_solver"
    if topic in {"arithmetic", "calculus_derivative", "calculus_integral", "probability", "geometry"}:
        return "rule_engine"
    return "rule_engine"
