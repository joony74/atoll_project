from __future__ import annotations

import ast
import re
from fractions import Fraction

from app.models.problem_schema import ProblemSchema


TRIG_TABLE = {
    ("cos", "0"): "1",
    ("sin", "0"): "0",
    ("tan", "0"): "0",
    ("cos", "pi/6"): "√3/2",
    ("sin", "pi/6"): "1/2",
    ("tan", "pi/6"): "√3/3",
    ("cos", "pi/4"): "√2/2",
    ("sin", "pi/4"): "√2/2",
    ("tan", "pi/4"): "1",
    ("cos", "pi/3"): "1/2",
    ("sin", "pi/3"): "√3/2",
    ("tan", "pi/3"): "√3",
    ("cos", "pi/2"): "0",
    ("sin", "pi/2"): "1",
    ("cos", "pi"): "-1",
    ("sin", "pi"): "0",
    ("tan", "pi"): "0",
    ("cos", "3pi/2"): "0",
    ("sin", "3pi/2"): "-1",
    ("cos", "2pi"): "1",
    ("sin", "2pi"): "0",
    ("tan", "2pi"): "0",
}


TRIG_CALL_RE = re.compile(r"(cos|sin|tan)\(([^)]+)\)", flags=re.IGNORECASE)


def _normalize_angle(angle: str) -> str:
    normalized = str(angle or "").replace(" ", "")
    normalized = normalized.replace("π", "pi")
    normalized = normalized.replace("1pi", "pi")
    return normalized


def _display_angle(angle: str) -> str:
    return angle.replace("pi", "π")


def _to_sympy_text(value: str) -> str:
    return re.sub(r"√(\d+)", r"sqrt(\1)", value)


def _format_sympy_answer(value: object) -> str:
    text = str(value)
    text = re.sub(r"sqrt\((\d+)\)", r"√\1", text)
    return text


def _eval_fraction_ast(expr: str) -> Fraction:
    def _eval(node) -> Fraction:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return Fraction(node.value)
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
        if isinstance(node, ast.UnaryOp):
            value = _eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return value
            if isinstance(node.op, ast.USub):
                return -value
        raise ValueError("unsupported fraction expression")

    return _eval(ast.parse(expr, mode="eval"))


def _format_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def solve(problem: ProblemSchema) -> dict:
    text = " ".join(problem.expressions or [problem.normalized_problem_text])
    matches = list(TRIG_CALL_RE.finditer(text))
    if not matches:
        return {"computed_answer": "", "steps": [], "confidence": 0.0}

    pieces: list[str] = []
    lookup_steps: list[str] = []
    missing = False

    def _replace(match: re.Match[str]) -> str:
        nonlocal missing
        trig_name = match.group(1).lower()
        angle = _normalize_angle(match.group(2))
        value = TRIG_TABLE.get((trig_name, angle), "")
        if not value:
            missing = True
            return match.group(0)
        lookup_steps.append(f"{trig_name}({_display_angle(angle)})={value}")
        pieces.append(value)
        return f"({_to_sympy_text(value)})"

    expression = TRIG_CALL_RE.sub(_replace, text)
    if missing:
        return {"computed_answer": "", "steps": [], "confidence": 0.0}
    expression = re.sub(r"\s+", "", expression)

    answer = ""
    try:
        import sympy as sp
    except Exception:
        sp = None
    if sp is not None:
        try:
            answer = _format_sympy_answer(sp.simplify(sp.sympify(expression)))
        except Exception:
            answer = ""
    if not answer and all("√" not in piece for piece in pieces) and re.fullmatch(r"[0-9+\-*/().]+", expression):
        try:
            answer = _format_fraction(_eval_fraction_ast(expression))
        except Exception:
            answer = ""
    if not answer:
        return {"computed_answer": "", "steps": [], "confidence": 0.0}

    return {
        "computed_answer": answer,
        "steps": [
            "이건 삼각함수 값 문제야.",
            "단위원의 특수각 값을 각각 읽었어.",
            f"{', '.join(lookup_steps)} 이므로 계산하면 {answer}야.",
        ],
        "confidence": 0.96,
    }
