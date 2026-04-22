from __future__ import annotations


def _type_opening(problem_type: str) -> str:
    return {
        "trigonometry": "이건 삼각함수 문제야.",
        "linear_equation": "이건 일차방정식 문제야.",
        "quadratic": "이건 이차식 문제야.",
        "function": "이건 함수 문제야.",
        "geometry": "이건 도형이나 좌표 쪽 문제야.",
        "probability": "이건 확률 문제야.",
        "calculus_derivative": "이건 미분 문제야.",
        "calculus_integral": "이건 적분 문제야.",
        "sequence": "이건 수열 문제야.",
        "arithmetic": "이건 식 계산 문제야.",
    }.get(problem_type, "이건 수학 문제야.")


def generate_korean_explanation(
    query: str,
    parsed_problem: dict,
    classification: dict,
    solver_result: dict,
    detail_level: str = "normal",
) -> str:
    opening = _type_opening(classification.get("problem_type", ""))
    steps = [str(step).strip() for step in (solver_result.get("steps") or []) if str(step).strip()]
    answer = str(solver_result.get("computed_answer") or "").strip()
    target = str(parsed_problem.get("target_question") or "").strip()

    if not answer:
        return "문제를 끝까지 풀 만한 정보가 아직 부족해. 문제 문장이나 식을 조금 더 또렷하게 주면 바로 이어서 볼게."

    if detail_level == "brief":
        body = steps[:2]
    elif detail_level == "detailed":
        body = steps[:4]
    else:
        body = steps[:3]

    parts = [opening]
    if target and target != "문제 풀이":
        parts.append(f"지금은 {target}를 구하는 걸로 보면 돼.")
    parts.extend(body)
    if query and any(token in query for token in ("왜", "다시", "쉽게")) and len(steps) >= 2:
        parts.append("핵심만 보면 조건을 식으로 바꾼 다음 바로 계산한 거야.")
    parts.append(f"그래서 정답은 {answer}야.")
    return " ".join(part for part in parts if part).strip()
