from __future__ import annotations

import unittest

from app.engines.parser.math_normalization_profile import (
    apply_learned_profile_rewrites,
    profile_summary,
)
from app.engines.parser.math_ocr_normalizer import normalize_ocr_math_text
from scripts.build_math_normalization_profile import latex_to_runtime_expr, simulated_ocr_pairs


class MathNormalizationProfileTests(unittest.TestCase):
    def test_profile_loads_problem_bank_counts(self) -> None:
        summary = profile_summary()

        self.assertEqual(summary["schema_version"], "coco_math_normalization_profile.v1")
        self.assertGreaterEqual(summary["total_records"], 20_000)
        self.assertGreater(summary["runtime_rule_count"], 0)

    def test_profile_rewrites_common_latex_math(self) -> None:
        text = apply_learned_profile_rewrites(r"\frac{x^4+2y^2}{6} + x^{2}")

        self.assertIn("(x^4+2y^2)/(6)", text)
        self.assertIn("x^(2)", text)

    def test_profile_rewrites_are_conservative_for_plain_numbers(self) -> None:
        self.assertEqual(apply_learned_profile_rewrites("177"), "177")

    def test_ocr_normalizer_uses_profile_rewrites(self) -> None:
        normalized = normalize_ocr_math_text(r"\frac{3}{4} + log _5 25 + √ 9")

        self.assertIn("(3)/(4)", normalized)
        self.assertIn("log_5(25)", normalized)
        self.assertIn("sqrt(9)", normalized)

    def test_profile_builder_extracts_simulated_confusions(self) -> None:
        pairs = simulated_ocr_pairs(r"\frac{x^2+1}{6}")
        reasons = {item["reason"] for item in pairs}

        self.assertEqual(latex_to_runtime_expr(r"\sqrt{9}+\frac{1}{2}"), "sqrt(9)+(1)/(2)")
        self.assertIn("latex_fraction_missing_bar", reasons)
        self.assertIn("power_space", reasons)


if __name__ == "__main__":
    unittest.main()
