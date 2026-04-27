from __future__ import annotations

import unittest

from app.chat.recovery_card import build_recovery_message, display_problem_text, display_topic


def _document(
    *,
    file_name: str = "problem.png",
    topic: str = "linear_equation",
    problem_text: str = "",
    expressions: list[str] | None = None,
    source_text_candidates: list[str] | None = None,
    computed_answer: str = "42",
    matched_choice: str = "",
    metadata: dict | None = None,
    solver_name: str = "test_solver",
) -> dict:
    return {
        "file_name": file_name,
        "file_path": file_name,
        "analysis": {
            "structured_problem": {
                "normalized_problem_text": problem_text,
                "expressions": expressions or [],
                "source_text_candidates": source_text_candidates if source_text_candidates is not None else ([problem_text] if problem_text else []),
                "math_topic": topic,
                "metadata": metadata or {},
            },
            "solve_result": {
                "solver_name": solver_name,
                "computed_answer": computed_answer,
                "matched_choice": matched_choice,
                "validation_status": "verified",
            },
        },
    }


class RecoveryCardTests(unittest.TestCase):
    def test_display_topic_uses_problem_bank_topic_without_changing_answer(self) -> None:
        document = _document(
            file_name="elementary_g01_010_easy_geometry_geometry.png",
            topic="linear_equation",
            problem_text="오른쪽 직사각형의 넓이를 구하시오",
            expressions=["rectangle_width 6 rectangle_height 8 rectangle_area 6*8"],
            computed_answer="48",
            metadata={"problem_bank_topic": "geometry"},
        )

        message = build_recovery_message(document)

        self.assertEqual(display_topic(document), "geometry")
        self.assertIn("- 유형 후보: 도형 문제", message)
        self.assertIn("- 답 후보: 48", message)
        self.assertIn("가로=6, 세로=8, 넓이=6*8", message)
        self.assertNotIn("일차방정식 문제", message)

    def test_noisy_statistics_problem_text_falls_back_to_clean_sentence(self) -> None:
        document = _document(
            file_name="elementary_g02_004_easy_expression_statistics.png",
            topic="coordinate_geometry",
            problem_text="다음 자료의 SAS 구하시오",
            expressions=["(87+75+72+73+95)/5"],
            computed_answer="402/5",
        )

        self.assertEqual(display_topic(document), "statistics")
        self.assertEqual(display_problem_text(document), "다음 자료의 평균 구하시오")
        message = build_recovery_message(document)
        self.assertIn("- 유형 후보: 통계 문제", message)
        self.assertNotIn("SAS", message)

    def test_function_candidates_are_hidden_for_plain_arithmetic_cards(self) -> None:
        document = _document(
            file_name="elementary_g01_001_easy_expression_arithmetic.png",
            topic="linear_equation",
            problem_text="다음 식의 값을 구하시오",
            expressions=["14+15"],
            computed_answer="29",
            metadata={"problem_bank_topic": "arithmetic"},
        )

        message = build_recovery_message(document)

        self.assertIn("- 유형 후보: 계산 문제", message)
        self.assertNotIn("- 함수 후보:", message)

    def test_problem_text_cues_override_stale_problem_bank_topic(self) -> None:
        document = _document(
            file_name="high_g03_018_easy_table_calculus_integral.png",
            topic="calculus_integral",
            problem_text="아래 표의 수량은 모두 몇 개인지 구하시오.",
            expressions=["14+26+16+12"],
            source_text_candidates=[
                "고등 3학년 ㆍ적분ㆍ기본 table ㆍ calculus_integral",
                "아래 표의 수량은 모두 몇 개인지 구하시오.",
            ],
            computed_answer="68",
            metadata={"problem_bank_topic": "calculus_integral"},
        )

        message = build_recovery_message(document)

        self.assertEqual(display_topic(document), "arithmetic")
        self.assertIn("- 유형 후보: 계산 문제", message)
        self.assertNotIn("적분 문제", message)

    def test_long_matched_choice_does_not_replace_clean_computed_answer(self) -> None:
        document = _document(
            file_name="high_g03_020_hard_expression_polynomial.png",
            topic="polynomial",
            problem_text="다항식의 값을 구하시오",
            expressions=["2*3^3-6*3^2+11*3-6"],
            computed_answer="27",
            matched_choice="물론입니다. 긴 OCR 파편이 섞인 후보 문장이 매우 길게 들어왔습니다. 답은 27입니다.",
            metadata={"problem_bank_topic": "polynomial"},
        )

        message = build_recovery_message(document)

        self.assertIn("- 답 후보: 27", message)
        self.assertNotIn("OCR 파편", message)

    def test_visual_template_hides_noisy_ocr_expression_candidates(self) -> None:
        document = _document(
            topic="arithmetic",
            problem_text="14-6에서 6을 4와 2로 가르고 10을 이용해 계산하세요.",
            expressions=["answer_text=빈칸: 8, 4", "14-6ㅋ |", "16-6ㅋ|"],
            computed_answer="빈칸: 8, 4",
            solver_name="visual_template_solver",
            metadata={
                "school_level": "elementary",
                "visual_template": {
                    "rule_id": "generic_make_ten_subtraction_decomposition",
                    "confidence": 0.86,
                },
            },
        )

        message = build_recovery_message(document)

        self.assertIn("- 시각 문항: 원본 그림의 빈칸 도식 기준으로 확인합니다.", message)
        self.assertIn("- 답 후보: 빈칸: 8, 4", message)
        self.assertIn("- 유형 후보: 초등 시각 연산 문제", message)
        self.assertNotIn("14-6ㅋ", message)
        self.assertNotIn("16-6ㅋ", message)


if __name__ == "__main__":
    unittest.main()
