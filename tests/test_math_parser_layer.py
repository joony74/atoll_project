from __future__ import annotations

import unittest

from app.engines.parser.math_candidate_ranker import extract_expression_texts, select_problem_statement
from app.engines.parser.math_ocr_normalizer import clean_visible_math_text, normalize_ocr_math_text
from app.engines.parser.school_math_taxonomy import classify_school_math_topic, topic_label
from app.core.pipeline import _merge_expression_candidates, run_solve_pipeline
from app.engines.solver import trig_solver
from app.models.problem_schema import ProblemSchema


class MathParserLayerTests(unittest.TestCase):
    def test_normalizes_common_ocr_math_symbols(self) -> None:
        text = normalize_ocr_math_text("2² + √ 9 × 3")

        self.assertIn("2^(2)", text)
        self.assertIn("sqrt(9)", text)
        self.assertIn("*", text)

    def test_cleans_escaped_noise_for_ui(self) -> None:
        text = clean_visible_math_text("1 2014 6 ㅅ1\\n i\\n4* x27° @")

        self.assertNotIn("\\n", text)
        self.assertNotIn("@", text)

    def test_extracts_expression_without_metadata_noise(self) -> None:
        raw = "2024학년도 모의고사\n4* x27° 의 값은?\n(1) 2  (2) 4  (3) 6"

        self.assertEqual(extract_expression_texts(raw), ["4* x27°"])
        self.assertEqual(select_problem_statement(raw, ["4* x27°"]), "4* x27° 의 값은?")

    def test_cleans_unknown_answer_suffix_from_expression(self) -> None:
        raw = "다음 식의 값을 구하시오\n12+8=?7"

        self.assertEqual(extract_expression_texts(raw), ["12+8"])

    def test_classifies_school_math_topics(self) -> None:
        topic, confidence = classify_school_math_topic("f(x)=2x+1 그래프의 기울기")

        self.assertEqual(topic, "coordinate_geometry")
        self.assertGreater(confidence, 0.4)
        self.assertEqual(topic_label("radical_power"), "루트·거듭제곱")

    def test_does_not_treat_ocr_x27_as_quadratic(self) -> None:
        topic, _ = classify_school_math_topic("4* x27° 의 값은?", ["4* x27°"])

        self.assertEqual(topic, "radical_power")

    def test_extracts_function_fragments_from_noisy_middle_ocr(self) -> None:
        raw = "OITLS\n길차함수 y = 2x + 1OA]\nX= 3 일 때 yl 값은?\naa 캡쳐 테스트용"

        self.assertEqual(extract_expression_texts(raw)[:2], ["y=2x+1", "x=3"])

    def test_repairs_ocr_d_as_two_in_linear_function(self) -> None:
        raw = "일차함수 y = Dx + 1에서\nx= 3 일 때 \\의 값은?\nDay 캡쳐 테스트용"

        self.assertEqual(extract_expression_texts(raw)[:2], ["y=2x+1", "x=3"])

    def test_repairs_common_ocr_slash_and_ax_noise(self) -> None:
        self.assertEqual(extract_expression_texts("다음 방정식을 푸시오.\n4Ax+1/=1"), ["4x+17=1"])

    def test_repairs_slash_as_y_in_function_context(self) -> None:
        raw = "일차함수 / = 4x + 9에서\nx= 0일 때 의 값을 구하시오."

        self.assertEqual(extract_expression_texts(raw)[:2], ["y=4x+9", "x=0"])

    def test_solves_function_value_from_formula_and_assignment(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="x=3 일 때 y의 값은?",
            expressions=["y=2x+1", "x=3"],
            math_topic="function",
        )

        payload = run_solve_pipeline(structured_problem=problem)
        solved = payload["solve_result"]

        self.assertEqual(solved.solver_name, "function_value_solver")
        self.assertEqual(solved.computed_answer, "7")

    def test_outputs_fraction_answer_for_fraction_expression(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="답을 기약분수로 나타내시오.",
            expressions=["3/4 + 1/8"],
            math_topic="fraction_ratio",
        )

        payload = run_solve_pipeline(structured_problem=problem)
        solved = payload["solve_result"]

        self.assertEqual(solved.solver_name, "fraction_solver")
        self.assertEqual(solved.computed_answer, "7/8")

    def test_infers_elementary_word_problem_expression(self) -> None:
        raw = "연필이 52자루 있습니다\n그중 14자루를 친구에게 주었습니다\n남은 연필은 몇 자루입니까?"

        self.assertIn("52-14", _merge_expression_candidates(raw))

    def test_infers_middle_equation_word_problem_expression(self) -> None:
        raw = "어떤 수 *에 4를 곱하고 -6를 더했더니 38가 되었습니다\n*의 값을 구하시오."

        self.assertIn("4x+-6=38", _merge_expression_candidates(raw))

    def test_infers_missing_y_value_in_function_table_text(self) -> None:
        raw = "일차식 y = 6x + 4의 값 표입니다.\n가 -50일 때 *의 값은?"

        self.assertIn("y=-50", _merge_expression_candidates(raw))

    def test_infers_table_sum_from_count_row(self) -> None:
        raw = "아래 표의 과일은 모두 몇 개입니까?\n종류 사과 배 귤\n개수 13 14 4"

        self.assertIn("13+14+4", _merge_expression_candidates(raw))

    def test_prefers_grid_table_digits_when_ocr_drops_tens_place(self) -> None:
        raw = "아래 표의 과일은 모두 몇 개입니까?\n개수 10 7 1\ntable_row_2 10 7 11"

        self.assertIn("10+7+11", _merge_expression_candidates(raw))

    def test_infers_function_table_lookup(self) -> None:
        raw = "아래 표는 일차함수의 일부입니다.\nx = 7일 때 y의 값은?\nx 6 7 8\ny 11 13 15"

        self.assertIn("answer=13", _merge_expression_candidates(raw))

    def test_infers_x_when_ocr_reads_variable_as_star_in_equation(self) -> None:
        raw = "다음 방정식을 푸시오.\n3*+-3=-27"

        self.assertIn("3x-3=-27", _merge_expression_candidates(raw))

    def test_prefers_area_expression_over_constant_function_value(self) -> None:
        raw = "함수 f(x) = 2의 그래프와 x축 사이의\n0 <= x <= 4 구간 넓이를 구하시오."

        self.assertEqual(_merge_expression_candidates(raw)[0], "2*4")

    def test_extracts_spaced_log_expression(self) -> None:
        self.assertIn("log _5(25)", _merge_expression_candidates("다음 로그의 값을 구하시오.\nlog _5(25)"))

    def test_infers_quadratic_when_x_squared_is_read_as_times_two(self) -> None:
        self.assertIn("x^2+2x=8", _merge_expression_candidates("다음 식의 값을 구하시오.\n×2+2<=8"))

    def test_infers_quadratic_when_x_squared_has_quote_noise(self) -> None:
        self.assertIn("x^2-2x=8", _merge_expression_candidates('다음 조건을 만족하는 값을 구하시오.\nx"2 +-2x=8'))

    def test_infers_distance_when_km_is_ocr_noise(self) -> None:
        self.assertIn("55*4", _merge_expression_candidates("시속 55 107로 4시간 동안 이동했습니다."))

    def test_infers_table_difference_from_people_row(self) -> None:
        raw = "아래 표에서 가장 많은 반과 가장 적은 반의 인원 차를 구하시오.\n인원 28 26 30 12"

        self.assertIn("30-12", _merge_expression_candidates(raw))

    def test_solves_inverse_linear_function_value(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="y가 -50일 때 x의 값은?",
            expressions=["y=6x+4", "y=-50"],
            math_topic="function",
        )

        payload = run_solve_pipeline(structured_problem=problem)
        solved = payload["solve_result"]

        self.assertEqual(solved.solver_name, "function_inverse_solver")
        self.assertEqual(solved.computed_answer, "-9")

    def test_solves_direct_table_lookup_answer(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="x=7일 때 y의 값은?",
            expressions=["answer=13", "x=7", "y=2x-1"],
            math_topic="function",
        )

        payload = run_solve_pipeline(structured_problem=problem)
        solved = payload["solve_result"]

        self.assertEqual(solved.solver_name, "table_lookup_solver")
        self.assertEqual(solved.computed_answer, "13")

    def test_solves_polynomial_value_with_assignment(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="f(5)의 값을 구하시오.",
            expressions=["1x^2+6x+8", "x=5"],
            math_topic="quadratic",
        )

        payload = run_solve_pipeline(structured_problem=problem)
        solved = payload["solve_result"]

        self.assertEqual(solved.solver_name, "expression_value_solver")
        self.assertEqual(solved.computed_answer, "63")

    def test_infers_derivative_value_from_noisy_prime_text(self) -> None:
        raw = "f(x) = 2x*2 + 0>일 때\nf'(-3)2| 값을 구하시오."

        self.assertIn("2*2*-3+0", _merge_expression_candidates(raw))

    def test_adds_multiple_special_angle_trig_values(self) -> None:
        problem = ProblemSchema(
            expressions=["sin(pi/6) + cos(pi/3)"],
            math_topic="trigonometry",
        )

        result = trig_solver.solve(problem)

        self.assertEqual(result["computed_answer"], "1")


if __name__ == "__main__":
    unittest.main()
