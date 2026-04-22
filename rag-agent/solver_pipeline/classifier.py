from __future__ import annotations

import re


def classify_problem(structured: dict) -> str:
    normalized_formula = str(structured.get("normalized_formula", "") or "")
    original_formula = str(structured.get("original_formula", "") or "")
    problem_text = str(structured.get("problem_text", "") or "")
    equation_text = str(structured.get("equation_text", "") or "")
    question_text = str(structured.get("question_text", "") or "")
    joined = " ".join([normalized_formula, original_formula, problem_text, question_text, equation_text]).lower()

    if any(token in joined for token in ["\\cos", "\\sin", "\\tan", "cos(", "sin(", "tan("]):
        return "trig_value"

    if any(token in joined for token in ["기울기", "y절편", "x절편", "직선", "그래프"]):
        return "linear_function"

    if re.search(r"y\s*=\s*[-+]?\d*\s*x", joined):
        return "linear_function"

    if "=" in joined and any(var in joined for var in ["x", "y"]):
        if "^2" in joined or "x²" in joined or "y²" in joined or "x**2" in joined or "y**2" in joined:
            return "quadratic_equation"
        return "equation"

    return "unknown"
