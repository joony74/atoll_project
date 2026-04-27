from __future__ import annotations

import unittest

from app.core.pipeline import run_solve_pipeline
from app.engines.parser.elementary_visual_templates import infer_elementary_visual_template
from app.models.problem_schema import ProblemSchema


class ElementaryVisualTemplateTests(unittest.TestCase):
    def test_infers_grade1_numbers_to_9_card_template(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/초1-1_1단원_9까지의수_1회_p01_문항10.png",
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.expression, "answer=6")
        self.assertIn("1 큰 수", template.problem_text)

    def test_infers_grade1_page2_visual_templates(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/초1-1_1단원_9까지의수_1회_p02_문항08.png",
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.expression, "answer_text=(1) 1, 2, 3 / (2) 6, 7, 8")
        self.assertIn("맞는 수", template.problem_text)

    def test_infers_generic_make_ten_compose_decompose_from_ocr_text(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/capture.png",
            raw_text=(
                "1. 10을 이용하여 모으기와 가르기를 한 것입니\n"
                "다. 빈칸에 알맞은 수를 넣어 보세요.\n"
                "9 6\n10\n91 618"
            ),
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.rule_id, "generic_make_ten_compose_decompose")
        self.assertEqual(template.expression, "answer_text=빈칸: 15, 5")

    def test_infers_generic_make_ten_subtraction_from_ocr_text(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/capture.png",
            raw_text="2. □ 안에 알맞은 수를 써넣으시오.\n14-6ㅋ |\n2",
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.rule_id, "generic_make_ten_subtraction_decomposition")
        self.assertEqual(template.expression, "answer_text=빈칸: 8, 4")

    def test_infers_generic_make_ten_addition_from_ocr_text(self) -> None:
        template = infer_elementary_visual_template(
            "/tmp/capture.png",
            raw_text="3. | ㅣ 안에 알맞은 수를 써넣으시오.\n8+5ㅋ |\n2 | |",
        )

        self.assertIsNotNone(template)
        assert template is not None
        self.assertEqual(template.rule_id, "generic_make_ten_addition_decomposition")
        self.assertEqual(template.expression, "answer_text=빈칸: 13, 3")

    def test_solves_text_answer_template_expression(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="수를 두 가지로 읽어 보세요.",
            expressions=["answer_text=(1) 셋, 삼 / (2) 넷, 사"],
            math_topic="arithmetic",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "visual_template_solver")
        self.assertEqual(solved.computed_answer, "(1) 셋, 삼 / (2) 넷, 사")
        self.assertEqual(solved.validation_status, "verified")


if __name__ == "__main__":
    unittest.main()
