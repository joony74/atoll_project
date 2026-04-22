from __future__ import annotations

from typing import Any

from math_solver import SYMPY_AVAILABLE


def solve_problem(problem: dict[str, Any]) -> dict[str, Any]:
    from .engine import solve_problem as _solve_problem

    return _solve_problem(problem)


def get_solver_capabilities() -> dict[str, Any]:
    return {
        "sympy_available": SYMPY_AVAILABLE,
        "advanced_symbolic_solver": SYMPY_AVAILABLE,
        "basic_solver_available": True,
    }


__all__ = ["solve_problem", "get_solver_capabilities"]
