from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TIMEOUT_SECONDS = 1.5


def _worker_payload(status: str, **values: Any) -> dict[str, Any]:
    payload = {"status": status}
    payload.update(values)
    return payload


def _format_sympy_value(value: Any) -> str:
    text = str(value)
    text = text.replace("**", "^")
    return text


def _parse_expression(sp: Any, expr: str) -> Any:
    locals_map = {
        "x": sp.symbols("x"),
        "y": sp.symbols("y"),
        "z": sp.symbols("z"),
        "sqrt": sp.sqrt,
        "log": sp.log,
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "pi": sp.pi,
        "E": sp.E,
    }
    return sp.sympify(str(expr or ""), locals=locals_map)


def _execute_task(task: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        import sympy as sp
    except Exception as exc:  # pragma: no cover - depends on local runtime
        return _worker_payload("unavailable", error=str(exc))

    try:
        if task == "solve_equation":
            symbol_name = str(payload.get("symbol") or "x")
            symbol = sp.symbols(symbol_name)
            lhs = _parse_expression(sp, str(payload.get("lhs") or ""))
            rhs = _parse_expression(sp, str(payload.get("rhs") or "0"))
            solutions = sp.solve(sp.Eq(lhs, rhs), symbol)
            if not solutions:
                return _worker_payload("no_solution")
            formatted = [_format_sympy_value(sp.simplify(item)) for item in solutions]
            return _worker_payload(
                "ok",
                answer=", ".join(formatted),
                engine_version=str(getattr(sp, "__version__", "")),
                solution_count=len(formatted),
            )

        if task == "evaluate":
            expr = _parse_expression(sp, str(payload.get("expr") or ""))
            simplified = sp.simplify(expr)
            return _worker_payload(
                "ok",
                answer=_format_sympy_value(simplified),
                engine_version=str(getattr(sp, "__version__", "")),
            )
    except Exception as exc:
        return _worker_payload("error", error=str(exc))

    return _worker_payload("error", error=f"unknown task: {task}")


def _run_worker_process(task: str, payload: dict[str, Any], *, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    env = dict(os.environ)
    existing_python_path = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(PROJECT_ROOT) if not existing_python_path else f"{PROJECT_ROOT}{os.pathsep}{existing_python_path}"
    command = [sys.executable, "-m", "app.engines.solver.sympy_worker", "--task", task, "--worker"]
    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            env=env,
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return _worker_payload("timeout", error=f"SymPy worker exceeded {timeout:.2f}s")
    except Exception as exc:
        return _worker_payload("error", error=str(exc))

    if completed.returncode != 0:
        return _worker_payload("error", error=(completed.stderr or completed.stdout or "").strip())
    try:
        result = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as exc:
        return _worker_payload("error", error=f"invalid worker output: {exc}")
    return result if isinstance(result, dict) else _worker_payload("error", error="worker returned non-object payload")


def solve_equation(lhs: str, rhs: str, symbol: str, *, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    return _run_worker_process("solve_equation", {"lhs": lhs, "rhs": rhs, "symbol": symbol}, timeout=timeout)


def evaluate_expression(expr: str, *, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    return _run_worker_process("evaluate", {"expr": expr}, timeout=timeout)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Small isolated SymPy worker for Coco solver tasks.")
    parser.add_argument("--task", required=True, choices=["solve_equation", "evaluate"])
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args(argv)

    if not args.worker:
        parser.error("sympy_worker must be invoked with --worker")
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError as exc:
        print(json.dumps(_worker_payload("error", error=str(exc)), ensure_ascii=False))
        return 1
    result = _execute_task(args.task, payload if isinstance(payload, dict) else {})
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
