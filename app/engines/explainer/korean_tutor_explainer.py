from __future__ import annotations

from app.models.problem_schema import ProblemSchema
from app.models.solve_result import SolveResult


def generate_korean_tutor_response(problem: ProblemSchema, solved: SolveResult, user_query: str) -> str:
    if not solved.computed_answer:
        return "문제를 끝까지 풀 만한 정보가 아직 부족해. 문제 문장이나 식을 조금 더 또렷하게 주면 바로 이어서 볼게."

    opening_map = {
        "trigonometry": "이건 삼각함수 문제야.",
        "linear_equation": "이건 방정식 문제야.",
        "quadratic": "이건 이차방정식 문제야.",
        "function": "이건 함수 문제야.",
        "probability": "이건 확률 문제야.",
        "geometry": "이건 도형이나 좌표 문제야.",
        "calculus_derivative": "이건 미분 문제야.",
        "calculus_integral": "이건 적분 문제야.",
    }
    parts = [opening_map.get(problem.math_topic, "이건 수학 문제야.")]
    parts.extend(solved.steps[:3])
    if "왜" in user_query or "다시" in user_query or "쉽게" in user_query:
        parts.append("핵심은 문제에 있는 식을 계산 가능한 형태로 바로 바꿔서 푼 거야.")
    if solved.matched_choice:
        parts.append(f"선지로 보면 {solved.matched_choice}가 맞아.")
    parts.append(f"그래서 정답은 {solved.computed_answer}야.")
    return " ".join(part for part in parts if part).strip()
