from __future__ import annotations

import re

try:
    import sympy as sp
except Exception:  # pragma: no cover
    sp = None

from app.models.problem_schema import ProblemSchema


def solve(problem: ProblemSchema) -> dict:
    if sp is None:
        return {"computed_answer": "", "steps": [], "confidence": 0.0}
    text = " ".join(problem.expressions or [problem.normalized_problem_text])
    text = text.replace(" ", "").replace("^", "**")
    candidates = re.findall(r"[\d()+\-*/*.]+", text)
    expression = max(candidates, key=len) if candidates else ""
    if not expression:
        return {"computed_answer": "", "steps": [], "confidence": 0.0}
    try:
        computed = sp.simplify(sp.sympify(expression))
        return {
            "computed_answer": str(computed),
            "steps": [
                "이건 식 계산 문제야.",
                "보이는 식을 그대로 정리하면 돼.",
                f"그래서 값은 {computed}야.",
            ],
            "confidence": 0.82,
        }
    except Exception:
        return {"computed_answer": "", "steps": [], "confidence": 0.0}
