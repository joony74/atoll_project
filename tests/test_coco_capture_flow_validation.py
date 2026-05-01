from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts import run_coco_app_corpus_validation as corpus_validation
from scripts.run_coco_capture_flow_validation import (
    expected_answer,
    expected_problem_number,
    normalize_answer,
    problem_number_from_text,
    should_compare_reference_answer,
)


class CocoCaptureFlowValidationTests(unittest.TestCase):
    def test_normalizes_private_use_decimal_point(self) -> None:
        self.assertEqual(normalize_answer("2\ue0538"), normalize_answer("2.8"))
        self.assertEqual(normalize_answer("\ue03d\ue0537"), normalize_answer("0.7"))
        self.assertEqual(normalize_answer("2.7 컵"), "27")
        self.assertEqual(normalize_answer("76÷4=19"), "76419")
        self.assertEqual(normalize_answer("몫 13, 나머지 5"), "135")
        self.assertEqual(normalize_answer("85÷3=28 ⋯ 1"), "853281")
        self.assertEqual(normalize_answer("85÷3=28 ... 1"), "853281")

    def test_normalizes_angle_degree_symbols(self) -> None:
        self.assertEqual(normalize_answer("55°"), normalize_answer("55\ue0c8"))
        self.assertEqual(normalize_answer("⑴ 70° ⑵ 55°"), normalize_answer("⑴ 7\ue03d\ue0c8 ⑵ 55\ue0c8"))

    def test_does_not_flag_private_use_decimal_answer_as_mismatch(self) -> None:
        reference = "⑴ \ue03d\ue0532 , 영점 이 ⑵ \ue03d\ue0537 , 영점 칠 ⑶ \ue03d\ue0533 , 영점 삼"
        computed = "⑴ 0.2, 영점 이 ⑵ 0.7, 영점 칠 ⑶ 0.3, 영점 삼"

        self.assertFalse(should_compare_reference_answer("분수를 소수로 나타내세요.", reference, computed))

    def test_skips_private_use_fraction_bar_answer_sheet_noise(self) -> None:
        reference = "\ue06d , \ue03d\ue0535 1\ue03d 4 4 4"
        computed = "7/10, 0.5"

        self.assertFalse(should_compare_reference_answer("사이에 있는 수를 모두 찾으세요.", reference, computed))

    def test_skips_fragmented_private_use_fraction_answer_key(self) -> None:
        reference = "11 , 1\ue03d 5"
        computed = "(1) 5/8, (2) 11/10"

        self.assertFalse(should_compare_reference_answer("분수로 나타내세요.", reference, computed))

    def test_skips_dangling_parenthesis_answer_key_fragment(self) -> None:
        self.assertFalse(should_compare_reference_answer("알맞은 수의 합을 구하세요.", "1216 (", "76"))

    def test_skips_visual_circle_mark_answer_key(self) -> None:
        self.assertFalse(should_compare_reference_answer("나누어떨어지는 나눗셈에 표시하세요.", "( ○ ) ( )", "56÷4"))
        self.assertFalse(should_compare_reference_answer("더 작은 수에 표시하세요.", "( ), ( ○ ), ( )", "가운데 그림"))

    def test_skips_visual_drawing_problem_reference_mismatch(self) -> None:
        self.assertFalse(
            should_compare_reference_answer(
                "2. 수만큼 ○를 그려 보세요.",
                "셋",
                "0",
            )
        )

    def test_skips_choice_label_answer_key_shift_for_numeric_result(self) -> None:
        self.assertFalse(
            should_compare_reference_answer(
                "두 식을 계산한 결과의 차를 구하세요.",
                "가",
                "4",
            )
        )

    def test_skips_answer_key_word_fragment_for_choice_result(self) -> None:
        self.assertFalse(
            should_compare_reference_answer(
                "문제를 식으로 바르게 나타낸 것을 모두 고르세요.",
                "약수",
                "⑤",
            )
        )

    def test_normalizes_answer_key_alternatives_and_geometry_labels(self) -> None:
        reference = "선분 ㄱㅇ(또는 선분ㅇㄱ), 선분 ㄴㅇ(또는 선분 ㅇㄴ)"
        computed = "선분 ㄱㅇ, 선분 ㄴㅇ"

        self.assertEqual(normalize_answer(reference), normalize_answer(computed))
        self.assertFalse(should_compare_reference_answer("반지름을 나타내는 선분을 찾으세요.", reference, computed))
        self.assertFalse(
            should_compare_reference_answer(
                "원의 반지름과 지름을 구하세요.",
                "반지름: 7 cm,\u200b 지름: 14 cm",
                "반지름 7 cm, 지름 14 cm",
            )
        )

    def test_normalizes_missing_kg_unit_in_weight_answer_key(self) -> None:
        self.assertEqual(normalize_answer("4 g 75\ue03d g"), normalize_answer("4 kg 750 g"))
        self.assertFalse(
            should_compare_reference_answer(
                "강아지의 무게 4750 g을 kg과 g으로 나타내세요.",
                "4 g 75\ue03d g",
                "4 kg 750 g",
            )
        )

    def test_skips_pictograph_table_answer_key_comparison(self) -> None:
        self.assertFalse(
            should_compare_reference_answer(
                "그림그래프를 보고 표를 완성하세요.",
                "요일별 팔린 아이스크림의 수 월요일 11 화요일 34 수요일 17 목요일 26 합계 88",
                "월요일 11, 화요일 34, 수요일 17, 목요일 26, 합계 88",
            )
        )

    def test_skips_shifted_long_answer_key_blocks(self) -> None:
        self.assertFalse(should_compare_reference_answer("평균을 구하세요.", "01. 37쪽 02. 평균을 구하기 위해서는 자료의 값을 모두 더한 후 자료의 수로 나누어야 합니다.", "394"))
        self.assertFalse(should_compare_reference_answer("계산해 보세요.", "03. 10, 16 04. 4", "-14124"))
        self.assertFalse(should_compare_reference_answer("소수의 곱셈을 계산하세요.", "=45-38=7 3 72÷(8×", "1 5/24"))
        self.assertFalse(should_compare_reference_answer("남은 귤은 몇 개입니까?", "2 개 - 4 -", "2개"))

    def test_pdf_card_text_does_not_overwrite_visual_template_with_math_symbols(self) -> None:
        template_text = "4×17=★, ★×68=▲일 때 ▲에 알맞은 수를 구하세요."
        shifted_pdf_text = "13. 원 모양의 호수 둘레에 4 m 간격으로 147그루의 나무가 심어져 있습니다."
        analysis = {
            "structured_problem": {
                "normalized_problem_text": template_text,
                "metadata": {"visual_template": {"rule_id": "grade3_2_multiplication_round3_star_triangle_product"}},
                "source_text_candidates": [],
            }
        }

        with patch.object(corpus_validation, "extract_pdf_card_text", return_value=shifted_pdf_text):
            updated, applied = corpus_validation.apply_pdf_card_text({}, analysis)

        structured = updated["structured_problem"]
        self.assertEqual(applied, shifted_pdf_text)
        self.assertEqual(structured["normalized_problem_text"], template_text)
        self.assertEqual(structured["source_text_candidates"][0], shifted_pdf_text)

    def test_offsets_grade4_diagnostic_round3_problem_numbers(self) -> None:
        self.assertEqual(
            expected_problem_number(
                {
                    "problem_card_label": "01",
                    "expected_problem_number": 1,
                    "parent_relative_path": "01.초등/4학년/EDITE/foo_[초4]_진단평가_3회_p02.png",
                }
            ),
            8,
        )
        self.assertEqual(
            expected_problem_number(
                {
                    "problem_card_label": "05",
                    "expected_problem_number": 13,
                    "parent_relative_path": "01.초등/4학년/EDITE/foo_[초4]_진단평가_3회_p03.png",
                }
            ),
            20,
        )

    def test_problem_number_parser_ignores_number_card_commas(self) -> None:
        self.assertIsNone(problem_number_from_text("수 카드 9, 5, 1 중 2장을 뽑아 가장 작은 수를 만드세요."))
        self.assertEqual(problem_number_from_text("14. 수 카드 중 2장을 뽑아 가장 작은 수를 만드세요."), 14)

    def test_problem_number_parser_ignores_leading_decimals(self) -> None:
        self.assertIsNone(problem_number_from_text("4.304에서 ㉠이 나타내는 수는 몇 배입니까?"))
        self.assertIsNone(problem_number_from_text("5.3×6.1<□<32×1.8에서 자연수는 모두 몇 개입니까?"))

    def test_offsets_grade4_decimal_unit_pages_by_eight_problem_blocks(self) -> None:
        self.assertEqual(
            expected_problem_number(
                {
                    "problem_card_label": "03",
                    "expected_problem_number": 3,
                    "parent_relative_path": "01.초등/4학년/EDITE/초4-2_3단원_소수의덧셈과뺄셈_3회_p02.png",
                }
            ),
            11,
        )
        self.assertEqual(
            expected_problem_number(
                {
                    "problem_card_label": "04",
                    "expected_problem_number": 4,
                    "parent_relative_path": "01.초등/4학년/EDITE/초4-2_3단원_소수의덧셈과뺄셈_1회_p03.png",
                }
            ),
            20,
        )

    def test_expected_answer_prefers_decimal_page_override_over_pdf_neighbor(self) -> None:
        problem_no, _, _ = expected_answer(
            {
                "pdf_path": "",
                "expected_problem_number": 3,
                "problem_card_label": "03",
                "source_page": 2,
                "parent_relative_path": "01.초등/4학년/EDITE/초4-2_3단원_소수의덧셈과뺄셈_3회_p02.png",
                "problem_card_bbox": [0, 0, 100, 100],
            },
            {
                "normalized_problem_text": "2.63+5.88=□+2.63에서 □ 안에 알맞은 수를 쓰세요.",
                "source_text_candidates": ["12. 계산 결과를 빈칸에 쓰세요."],
            },
        )

        self.assertEqual(problem_no, 11)

    def test_expected_answer_prefers_repeated_capture_ocr_number_over_pdf_shift(self) -> None:
        problem_no, answer, pdf_text = expected_answer(
            {
                "pdf_path": "",
                "expected_problem_number": 1,
                "source_page": 3,
            },
            {
                "normalized_problem_text": "색연필 7자루에 5자루를 더 받았습니다.",
                "source_text_candidates": [
                    "19. 재희는 파란 구슬 3개, 빨간 구슬 4개, 노란 구슬 7개",
                    "18. 준서는 색연필을 7자루 가지고 있었습니다.",
                    "18. 준서는 색연필을 7자루 가지고 있었습니다.",
                ],
            },
        )

        self.assertEqual(problem_no, 18)
        self.assertEqual(answer, "")
        self.assertEqual(pdf_text, "")

    def test_expected_answer_uses_page_one_card_index_when_pdf_text_is_neighbor(self) -> None:
        problem_no, _, _ = expected_answer(
            {
                "pdf_path": "",
                "expected_problem_number": 3,
                "problem_card_index": 3,
                "source_page": 1,
            },
            {
                "normalized_problem_text": "2와 6을 모으기를 해 보세요.",
                "source_text_candidates": [
                    "4. 가르기를 해 보세요.",
                    "1. 그림을 보고 모으기를 해 보세요. 2. 그림을 보고 가르기를 해 보세요. 3. 모으기를 해 보세요. 4. 가르기를 해 보세요.",
                ],
            },
        )

        self.assertEqual(problem_no, 3)

    def test_expected_answer_prefers_repeated_card_ocr_over_applied_pdf_text(self) -> None:
        problem_no, _, _ = expected_answer(
            {
                "pdf_path": "",
                "expected_problem_number": 7,
                "source_page": 2,
            },
            {
                "normalized_problem_text": "16. 수 카드 5 장 중에서 2 장을 사용하여 두 수의 합이 10이 되도록 만들었습니다.",
                "source_text_candidates": [
                    "16. 수 카드 5 장 중에서 2 장을 사용하여 두 수의 합이 10이 되도록 만들었습니다.",
                    "15. □ 안에 알맞은 수를 써넣으세요. 8+9=17 9+□=17",
                    "15. □ 안에 알맞은 수를 써넣으세요. 8+9=17 9+□=17",
                ],
            },
        )

        self.assertEqual(problem_no, 15)


if __name__ == "__main__":
    unittest.main()
