from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import ast
import math
from pathlib import Path
from typing import Any

try:
    import sympy as sp
except Exception:
    sp = None

from app.engines.explainer.korean_tutor_explainer import generate_korean_tutor_response
from app.engines.router.solver_router import route_solver
from app.engines.solver import arithmetic_solver, trig_solver
from app.engines.validator.answer_validator import validate_answer
from app.engines.vision.ollama_vision import OllamaVisionClient
from app.models.problem_schema import ProblemSchema
from app.models.solve_result import SolveResult
from app.utils.choice_parser import parse_choices
from app.utils.math_patterns import contains_math_like_tokens, detect_math_signal_score
from app.utils.text_normalizer import normalize_math_text, split_exam_metadata


_QUESTION_SUFFIX_RE = re.compile(r"(의\s*값은\??|값은\??|구하시오\.?|옳은\s*것은\??|정답[은: ]?)", re.IGNORECASE)


def _run_tesseract_ocr(image_path: str) -> dict[str, Any]:
    binary = os.getenv("COCO_TESSERACT_BIN", "/opt/homebrew/bin/tesseract")
    if not Path(binary).exists():
        return {"engine": "tesseract", "available": False, "text": "", "confidence": 0.0, "error": "missing_binary"}

    try:
        proc = subprocess.run(
            [binary, image_path, "stdout", "-l", "kor+eng"],
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        )
        text = normalize_math_text(proc.stdout or "")
        return {
            "engine": "tesseract",
            "available": bool(text),
            "text": text,
            "confidence": 0.62 if text else 0.0,
        }
    except Exception as exc:
        return {"engine": "tesseract", "available": False, "text": "", "confidence": 0.0, "error": str(exc)}


def _select_best_text(image_path: str) -> tuple[str, dict[str, Any]]:
    tesseract_result = _run_tesseract_ocr(image_path)
    vision_result = OllamaVisionClient().interpret_math_image(image_path)
    candidates = [tesseract_result, vision_result]
    ranked = sorted(
        candidates,
        key=lambda item: (
            detect_math_signal_score(item.get("text") or ""),
            item.get("confidence") or 0.0,
            len(item.get("text") or ""),
        ),
        reverse=True,
    )
    best = ranked[0] if ranked else {"text": ""}
    return str(best.get("text") or ""), {
        "tesseract": tesseract_result,
        "vision": vision_result,
        "selected_engine": best.get("engine") or "unknown",
    }


def _detect_math_topic(text: str, expressions: list[str]) -> str:
    joined = f"{text}\n" + "\n".join(expressions)
    lowered = joined.lower()
    if any(token in lowered for token in ("cos(", "sin(", "tan(", "π", "pi")):
        return "trigonometry"
    if "log" in lowered:
        return "logarithm"
    if "=" in lowered and any(var in lowered for var in ("x", "y")):
        return "equation"
    if contains_math_like_tokens(joined):
        return "arithmetic"
    return "unknown"


def _extract_expression_candidates(text: str) -> list[str]:
    expressions: list[str] = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if any(marker in line for marker in ("①", "②", "③", "④", "⑤")):
            continue
        if detect_math_signal_score(line) < 0.15:
            continue
        cleaned = _QUESTION_SUFFIX_RE.sub("", line).strip(" .,:;")
        if cleaned and cleaned not in expressions:
            expressions.append(cleaned)
    return expressions[:5]


def _build_problem_text(content_text: str, expressions: list[str]) -> str:
    for raw_line in (content_text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "값은" in line or "구하시오" in line or "옳은 것은" in line:
            return line
    if expressions:
        return expressions[0]
    return (content_text or "").strip()


def _normalize_for_sympy(expr: str) -> str:
    normalized = normalize_math_text(expr)
    normalized = _QUESTION_SUFFIX_RE.sub("", normalized).strip()
    normalized = normalized.replace("^", "**")
    normalized = normalized.replace("sqrt", "sqrt")
    normalized = normalized.replace("√", "sqrt")
    normalized = re.sub(r"log_?\s*([0-9]+)\s*\(\s*([^)]+)\s*\)", r"log(\2,\1)", normalized)
    normalized = re.sub(r"log_?\s*([0-9]+)\s*([a-zA-Z0-9()]+)", r"log(\2,\1)", normalized)
    normalized = re.sub(r"(\d)\s*\(", r"\1*(", normalized)
    normalized = re.sub(r"\)\s*\(", r")*(", normalized)
    normalized = re.sub(r"([a-zA-Z])\s*\(", r"\1(", normalized)
    normalized = re.sub(r"\s+", "", normalized)
    return normalized


def _safe_eval(expr: str) -> float:
    allowed_funcs = {
        "sqrt": math.sqrt,
        "log": lambda x, base=math.e: math.log(x, base),
        "pi": math.pi,
    }

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id in allowed_funcs and isinstance(allowed_funcs[node.id], (int, float)):
            return float(allowed_funcs[node.id])
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
            if isinstance(node.op, ast.Pow):
                return left ** right
        if isinstance(node, ast.UnaryOp):
            value = _eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return value
            if isinstance(node.op, ast.USub):
                return -value
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in allowed_funcs:
            args = [_eval(arg) for arg in node.args]
            return float(allowed_funcs[node.func.id](*args))
        raise ValueError(f"Unsupported expression: {ast.dump(node)}")

    tree = ast.parse(expr, mode="eval")
    return float(_eval(tree))


def _format_number(value: float) -> str:
    rounded = round(value)
    if abs(value - rounded) < 1e-9:
        return str(int(rounded))
    return f"{value:.6g}"


def _compute_answer(problem: ProblemSchema) -> dict[str, Any]:
    if problem.math_topic == "trigonometry":
        result = trig_solver.solve(problem)
        result["solver_name"] = "trig_solver"
        return result

    for source in problem.expressions or [problem.normalized_problem_text]:
        expr = _normalize_for_sympy(source)
        if not expr:
            continue
        try:
            if "=" in expr and any(var in expr for var in ("x", "y")) and sp is not None:
                lhs, rhs = expr.split("=", 1)
                symbol_name = "x" if "x" in expr else "y"
                symbol = sp.symbols(symbol_name)
                solutions = sp.solve(sp.Eq(sp.sympify(lhs), sp.sympify(rhs)), symbol)
                if not solutions:
                    continue
                computed = ", ".join(str(item) for item in solutions)
                return {
                    "solver_name": "sympy_equation_solver",
                    "computed_answer": computed,
                    "steps": [
                        "식 양쪽을 같은 변수식으로 정리했어.",
                        f"{symbol_name}에 대한 방정식으로 보고 풀었어.",
                        f"해는 {computed}야.",
                    ],
                    "confidence": 0.84,
                }

            computed_value = _safe_eval(expr)
            computed = _format_number(computed_value)
            return {
                "solver_name": "safe_eval_solver",
                "computed_answer": computed,
                "steps": [
                    "보이는 식을 계산 가능한 형태로 정리했어.",
                    "지수와 괄호를 순서대로 계산했어.",
                    f"값은 {computed}야.",
                ],
                "confidence": 0.86,
            }
        except Exception:
            continue

    fallback = arithmetic_solver.solve(problem)
    fallback["solver_name"] = str(fallback.get("solver_name") or "arithmetic_solver")
    return fallback


def _build_structured_problem(image_path: str, user_query: str = "") -> tuple[ProblemSchema, dict[str, Any]]:
    raw_text, debug_sources = _select_best_text(image_path)
    content_text, metadata_lines = split_exam_metadata(raw_text)
    choices = parse_choices(raw_text)
    expressions = _extract_expression_candidates(content_text or raw_text)
    problem_text = _build_problem_text(content_text, expressions)
    math_topic = _detect_math_topic(content_text or raw_text, expressions)
    question_type = "multiple_choice" if choices else "subjective"
    confidence = min(
        1.0,
        max(
            detect_math_signal_score(problem_text),
            0.35 if expressions else 0.0,
            0.4 if choices else 0.0,
        ),
    )
    metadata = {
        "image_path": image_path,
        "user_query": user_query,
        "ocr_debug": debug_sources,
        "metadata_lines": metadata_lines,
        "content_hash": hashlib.sha1(Path(image_path).read_bytes()).hexdigest()[:12],
    }
    problem = ProblemSchema(
        source_text_candidates=[candidate for candidate in [raw_text, content_text] if candidate],
        normalized_problem_text=problem_text,
        expressions=expressions,
        choices=choices,
        question_type=question_type,
        math_topic=math_topic,
        target_question="문제 풀이",
        confidence=confidence,
        metadata=metadata,
    )
    debug = {
        "raw_text": raw_text,
        "content_text": content_text,
        "expressions": expressions,
        "choices": choices,
        "math_topic": math_topic,
        "question_type": question_type,
    }
    return problem, debug


def run_upload_pipeline(image_path: str, user_query: str = "", debug: bool = False) -> dict[str, Any]:
    structured_problem, debug_payload = _build_structured_problem(image_path, user_query=user_query)
    payload: dict[str, Any] = {
        "route": "solver",
        "structured_problem": structured_problem,
    }
    if debug:
        payload["debug"] = debug_payload
    return payload


def run_solve_pipeline(
    image_path: str | None = None,
    structured_problem: ProblemSchema | None = None,
    user_query: str = "",
    debug: bool = False,
) -> dict[str, Any]:
    debug_payload: dict[str, Any] = {}
    problem = structured_problem
    if problem is None:
        if not image_path:
            raise ValueError("image_path or structured_problem is required")
        upload_payload = run_upload_pipeline(image_path, user_query=user_query, debug=debug)
        problem = upload_payload["structured_problem"]
        debug_payload["upload"] = upload_payload.get("debug", {})

    solver_name = route_solver(problem)
    if solver_name == "trig_solver":
        solver_result = trig_solver.solve(problem)
    else:
        solver_result = _compute_answer(problem)
    solver_result["solver_name"] = str(solver_result.get("solver_name") or solver_name)

    solved: SolveResult = validate_answer(problem, solver_result)
    solved.explanation = generate_korean_tutor_response(problem, solved, user_query)
    debug_payload["solver_name"] = solved.solver_name
    debug_payload["computed_answer"] = solved.computed_answer
    debug_payload["validation_status"] = solved.validation_status

    payload = {
        "structured_problem": problem,
        "solve_result": solved,
    }
    if debug:
        payload["debug"] = debug_payload
    return payload


def dump_debug_payload(payload: dict[str, Any]) -> str:
    serializable: dict[str, Any] = {}
    for key, value in payload.items():
        if hasattr(value, "model_dump"):
            serializable[key] = value.model_dump()
        else:
            serializable[key] = value
    return json.dumps(serializable, ensure_ascii=False, indent=2)
