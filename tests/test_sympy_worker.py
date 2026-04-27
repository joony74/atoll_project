from __future__ import annotations

import unittest

from app.engines.solver.sympy_worker import evaluate_expression, solve_equation


class SymPyWorkerTests(unittest.TestCase):
    def test_solves_quadratic_in_isolated_worker(self) -> None:
        result = solve_equation("x**2-5*x+6", "0", "x")

        self.assertEqual(result.get("status"), "ok")
        self.assertEqual(result.get("answer"), "2, 3")
        self.assertTrue(result.get("engine_version"))

    def test_evaluates_exact_radical_expression(self) -> None:
        result = evaluate_expression("sqrt(32)")

        self.assertEqual(result.get("status"), "ok")
        self.assertEqual(result.get("answer"), "4*sqrt(2)")


if __name__ == "__main__":
    unittest.main()
