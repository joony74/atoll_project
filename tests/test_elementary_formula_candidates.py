from __future__ import annotations

import unittest

from app.core.pipeline import _merge_expression_candidates
from app.engines.parser.elementary_formula_candidates import (
    elementary_formula_catalog_summary,
    infer_elementary_formula_candidates,
)


class ElementaryFormulaCandidateTests(unittest.TestCase):
    def test_catalog_summary_exposes_rule_counts(self) -> None:
        summary = elementary_formula_catalog_summary()

        self.assertEqual(summary["schema_version"], "coco_elementary_formula_catalog.v1")
        self.assertGreaterEqual(summary["rule_count"], 180)
        self.assertGreaterEqual(summary["extractor_family_count"], 20)
        self.assertIn("direct_arithmetic", summary["by_category"])
        self.assertIn("ocr_repair", summary["by_category"])

    def test_infers_blank_addition_equation(self) -> None:
        raw = "□ 안에 알맞은 수를 써넣으세요. 38 + □ = 72"

        candidates = infer_elementary_formula_candidates(raw)

        self.assertEqual(candidates[0].expression, "answer=34")
        self.assertEqual(candidates[0].rule_id, "elementary_blank_equation")
        self.assertIn("answer=34", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_blank_multiplication_equation(self) -> None:
        raw = "□ 안에 알맞은 수를 써넣으세요. 8 × □ = 56"

        self.assertIn("answer=7", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_equal_share_division(self) -> None:
        raw = "사탕 45개를 5명에게 똑같이 나누어 주려고 합니다. 한 명은 몇 개씩 받습니까?"

        self.assertIn("answer=9", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_pack_multiplication(self) -> None:
        raw = "한 상자에 12개씩 들어 있습니다. 7상자에 들어 있는 사과는 모두 몇 개입니까?"

        self.assertIn("12*7", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_more_less_than_number(self) -> None:
        raw = "86보다 13만큼 더 작은 수를 쓰세요."

        self.assertIn("answer=73", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_rectangle_metrics(self) -> None:
        raw = "가로가 8 cm, 세로가 5 cm인 직사각형의 둘레와 넓이를 구하세요."
        expressions = _merge_expression_candidates(raw, school_level="elementary")

        self.assertIn("answer=26", expressions)
        self.assertIn("8*5", expressions)

    def test_infers_average_expression(self) -> None:
        raw = "다음 자료의 평균을 구하세요. 12, 14, 16, 18"

        self.assertIn("(12+14+16+18)/4", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_fraction_arithmetic_answer(self) -> None:
        raw = "분수의 계산을 하세요. 3/4 + 1/8"

        self.assertIn("answer=7/8", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_square_and_triangle_metrics(self) -> None:
        square = "한 변의 길이가 9 cm인 정사각형의 둘레를 구하세요."
        triangle = "삼각형의 밑변의 길이가 10 cm, 높이가 6 cm입니다. 넓이를 구하세요."

        self.assertIn("answer=36", _merge_expression_candidates(square, school_level="elementary"))
        self.assertIn("10*6/2", _merge_expression_candidates(triangle, school_level="elementary"))

    def test_infers_time_and_pattern_candidates(self) -> None:
        time_raw = "3시 40분에서 35분 뒤의 시각을 쓰세요."
        pattern_raw = "규칙을 찾아 다음 수를 쓰세요. 5, 9, 13, 17"

        self.assertIn("answer_text=4시 15분", _merge_expression_candidates(time_raw, school_level="elementary"))
        self.assertIn("answer=21", _merge_expression_candidates(pattern_raw, school_level="elementary"))


if __name__ == "__main__":
    unittest.main()
