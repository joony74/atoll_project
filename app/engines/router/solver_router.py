from __future__ import annotations

from app.models.problem_schema import ProblemSchema


def route_solver(problem: ProblemSchema) -> str:
    topic = problem.math_topic
    text = f"{problem.normalized_problem_text} {' '.join(problem.expressions)}"
    if any(token in text for token in ("기울기", "절편", "좌표", "그래프")):
        return "rule_engine"
    if topic == "trigonometry":
        return "trig_solver"
    if topic in {"linear_equation", "quadratic", "function"}:
        return "algebra_solver"
    if topic in {"arithmetic", "calculus_derivative", "calculus_integral", "probability", "geometry"}:
        return "rule_engine"
    return "rule_engine"
