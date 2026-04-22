from __future__ import annotations

from coco_engine.models.problem_schema import ProblemSchema
from coco_engine.models.solve_result import SolveResult


def generate_korean_tutor_response(problem: ProblemSchema, solved: SolveResult, user_query: str) -> str:
    if not solved.computed_answer:
        return "문제를 끝까지 풀 만한 정보가 아직 부족해. 문제 문장이나 식을 조금 더 또렷하게 주면 바로 이어서 볼게."

    if problem.math_topic == "worksheet" or len(problem.metadata.get("subproblems") or []) >= 2:
        parts = ["이건 여러 소문항이 있는 학습지 문제야."]
        parts.extend(solved.steps[:4])
        parts.append(f"정리하면 {solved.computed_answer}")
        return " ".join(part for part in parts if part).strip()

    opening_map = {
        "graph_limit": "이건 그래프형 함수 극한 문제야.",
        "trigonometry": "이건 삼각함수 문제야.",
        "worksheet": "이건 여러 소문항이 있는 학습지 문제야.",
        "linear_equation": "이건 방정식 문제야.",
        "quadratic": "이건 이차방정식 문제야.",
        "function": "이건 함수 문제야.",
        "probability": "이건 확률 문제야.",
        "geometry": "이건 도형이나 좌표 문제야.",
        "calculus_derivative": "이건 미분 문제야.",
        "calculus_integral": "이건 적분 문제야.",
    }
    parts = [opening_map.get(problem.math_topic, "이건 수학 문제야.")]
    parts.extend(solved.steps[:4] if problem.math_topic == "graph_limit" else solved.steps[:3])
    if "왜" in user_query or "다시" in user_query or "쉽게" in user_query:
        parts.append("핵심은 문제에 있는 식을 계산 가능한 형태로 바로 바꿔서 푼 거야.")
    if solved.matched_choice:
        parts.append(f"선지로 보면 {solved.matched_choice}가 맞아.")
    parts.append(f"그래서 정답은 {solved.computed_answer}야.")
    return " ".join(part for part in parts if part).strip()
