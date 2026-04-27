from __future__ import annotations

import unittest

from app.engines.parser.math_candidate_ranker import extract_expression_texts, select_problem_statement
from app.engines.parser.math_ocr_normalizer import clean_visible_math_text, normalize_ocr_math_text
from app.engines.parser.school_math_taxonomy import classify_school_math_topic, topic_label
from app.core.pipeline import _build_problem_text, _merge_expression_candidates, run_solve_pipeline
from app.engines.solver import trig_solver
from app.models.problem_schema import ProblemSchema
from app.utils.choice_parser import parse_choices


class MathParserLayerTests(unittest.TestCase):
    def test_normalizes_common_ocr_math_symbols(self) -> None:
        text = normalize_ocr_math_text("2² + √ 9 × 3")

        self.assertIn("2^(2)", text)
        self.assertIn("sqrt(9)", text)
        self.assertIn("*", text)

    def test_repairs_coefficient_x_star_as_square(self) -> None:
        text = normalize_ocr_math_text("다항식 f(x) = 3x*2 + -3x + 1")

        self.assertIn("3x^2", text)

    def test_cleans_escaped_noise_for_ui(self) -> None:
        text = clean_visible_math_text("1 2014 6 ㅅ1\\n i\\n4* x27° @")

        self.assertNotIn("\\n", text)
        self.assertNotIn("@", text)

    def test_elementary_korean_repairs_are_profile_scoped(self) -> None:
        raw = "14, 알맞은 말에 OF 하세요\n0부터 9까지의 수 중에서 6보다 큰 +S"

        common = normalize_ocr_math_text(raw)
        elementary = normalize_ocr_math_text(raw, school_level="elementary")

        self.assertIn("OF", common)
        self.assertIn("○표 하세요", elementary)
        self.assertIn("큰 수", elementary)

    def test_extracts_expression_without_metadata_noise(self) -> None:
        raw = "2024학년도 모의고사\n4* x27° 의 값은?\n(1) 2  (2) 4  (3) 6"

        self.assertEqual(extract_expression_texts(raw), ["4* x27°"])
        self.assertEqual(_merge_expression_candidates(raw)[0], "4^(1/2)*27^(1/3)")
        self.assertEqual(select_problem_statement(raw, ["4^(1/2)*27^(1/3)"]), "4* x27° 의 값은?")

    def test_rebuilds_stacked_fractional_power_numerators(self) -> None:
        raw = "3 2014 6 B 1\n3 1\n4? x27? 의 값은?\n① 12 ② 15 ③ 18 ④ 21 ⑤ 24"

        self.assertEqual(_merge_expression_candidates(raw)[0], "4^(3/2)*27^(1/3)")
        self.assertEqual(_build_problem_text(raw, ["4^(3/2)*27^(1/3)"]), "4^(3/2)*27^(1/3) 의 값은?")

    def test_cleans_unknown_answer_suffix_from_expression(self) -> None:
        raw = "다음 식의 값을 구하시오\n12+8=?7"

        self.assertEqual(extract_expression_texts(raw), ["12+8"])

    def test_classifies_school_math_topics(self) -> None:
        topic, confidence = classify_school_math_topic("f(x)=2x+1 그래프의 기울기")

        self.assertEqual(topic, "coordinate_geometry")
        self.assertGreater(confidence, 0.4)
        self.assertEqual(topic_label("radical_power"), "루트·거듭제곱")

        topic, _ = classify_school_math_topic(
            "f(x) = 4x + 22! 때 lim x->1f(x)2| 값을 구하시오.",
            ["4x+2", "x=1"],
        )

        self.assertEqual(topic, "calculus_limit")

        topic, _ = classify_school_math_topic(
            "미분 6단원. 10을 이용하여 모으기와 가르기를 한 것입니다. 빈칸에 알맞은 수를 넣어 보세요.",
            ["answer=3"],
        )

        self.assertEqual(topic, "arithmetic")

    def test_does_not_treat_ocr_x27_as_quadratic(self) -> None:
        topic, _ = classify_school_math_topic("4* x27° 의 값은?", ["4* x27°"])

        self.assertEqual(topic, "radical_power")

    def test_solves_ocr_fractional_power_pair(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="4^(1/2)*27^(1/3) 의 값은?",
            expressions=["4^(1/2)*27^(1/3)", "4* x27°"],
            math_topic="radical_power",
        )

        payload = run_solve_pipeline(structured_problem=problem)
        solved = payload["solve_result"]

        self.assertEqual(solved.solver_name, "safe_eval_solver")
        self.assertEqual(solved.computed_answer, "6")

    def test_solves_stacked_fractional_power_pair(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="4^(3/2)*27^(1/3) 의 값은?",
            expressions=["4^(3/2)*27^(1/3)"],
            math_topic="radical_power",
        )

        payload = run_solve_pipeline(structured_problem=problem)
        solved = payload["solve_result"]

        self.assertEqual(solved.solver_name, "safe_eval_solver")
        self.assertEqual(solved.computed_answer, "24")

    def test_solves_log_sequence_product_template(self) -> None:
        expression = "sequence_log_product(base=2,start=2,increment=1,count=8)"
        problem = ProblemSchema(
            normalized_problem_text=_build_problem_text("", [expression]),
            expressions=[expression],
            choices=["① 36", "② 40", "③ 44", "④ 48", "⑤ 52"],
            question_type="multiple_choice",
            math_topic="log_sequence",
        )

        payload = run_solve_pipeline(structured_problem=problem)
        solved = payload["solve_result"]

        self.assertEqual(problem.normalized_problem_text, "a1=2, log_2(a_(n+1))=1+log_2(a_n), a1*...*a8=2^k 일 때 k의 값은?")
        self.assertEqual(solved.solver_name, "sequence_log_product_solver")
        self.assertEqual(solved.computed_answer, "36")
        self.assertEqual(solved.matched_choice, "① 36")

    def test_parses_ocr_choice_marker_line(self) -> None:
        self.assertEqual(
            parse_choices("0) 36 @ 40 @ 44 04) 48 ® 52"),
            ["① 36", "② 40", "③ 44", "④ 48", "⑤ 52"],
        )

    def test_classifies_fractional_exponents_as_radical_power(self) -> None:
        topic, _ = classify_school_math_topic(
            "4^(1/2)*27^(1/3) 의 값은?",
            ["4^(1/2)*27^(1/3)"],
        )

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

    def test_infers_generic_count_word_problem_expression(self) -> None:
        raw = (
            "민지는 스티커를 32장 가지고 있었습니다.\n"
            "35장을 더 받고, 그중 9장을 사용했습니다. 남은 스티커는 몇 장입니까?"
        )

        self.assertIn("32+35-9", _merge_expression_candidates(raw))

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

    def test_infers_table_sum_when_quantity_label_is_ocr_noise(self) -> None:
        raw = "아래 표의 수량은 모두 몇 개인지 구하시오.\na 42 16 27 18\n항복 0Co |"

        self.assertIn("42+16+27+18", _merge_expression_candidates(raw))

    def test_infers_average_when_first_value_lacks_comma(self) -> None:
        raw = "다음 자료의 평균을 구하시오.\n87 75, 72, 73, 100"

        self.assertEqual(_merge_expression_candidates(raw)[0], "(87+75+72+73+100)/5")

    def test_infers_pattern_table_next_value(self) -> None:
        raw = "아래 표의 규칙을 보고 5번째 값을 구하시오.\ntable_row_1 1 2 3\ntable_row_2 5 7 9 1"

        self.assertIn("answer=13", _merge_expression_candidates(raw))

    def test_infers_pattern_word_growth(self) -> None:
        raw = "첫째 날 2개를 만들고 매일 5개씩 더 많이 만듭니다.\n6째 날에는 몇 개를 만듭니까?"

        self.assertIn("answer=27", _merge_expression_candidates(raw))

    def test_infers_blank_addition_equation_answer(self) -> None:
        raw = "ㅣ 안에 알맞은 수를 써 넣으세요.\n7 + [ ] = 14"

        self.assertIn("answer=7", _merge_expression_candidates(raw))

    def test_infers_blank_subtraction_equation_answer(self) -> None:
        raw = "안에 알맞은 수를 써 넣으세요.\n15-[ _]=7"

        self.assertIn("answer=8", _merge_expression_candidates(raw))

    def test_infers_leading_blank_equation_answer(self) -> None:
        raw = "[ ] 안에 알맞은 수를 써넣으세요.\n+7=15"

        self.assertIn("answer=8", _merge_expression_candidates(raw))

    def test_infers_make_ten_number_bond_answer(self) -> None:
        raw = "10을 이용하여 모으기와 가르기를 한 것입니다.\n빈칸에 알맞은 수를 넣어 보세요.\n7SG 10"

        self.assertIn("answer=3", _merge_expression_candidates(raw))

    def test_infers_make_ten_number_bond_when_ocr_flattens_lines(self) -> None:
        raw = "10을 이용하여 모으기와 가르기를 한 것입니다. 빈칸에 알맞은 수를 넣어 보세요. 9 0\" 10 fo]"

        self.assertIn("answer=1", _merge_expression_candidates(raw))

    def test_answer_only_expression_does_not_replace_problem_statement(self) -> None:
        raw = "10을 이용하여 모으기와 가르기를 한 것입니다.\n빈칸에 알맞은 수를 넣어 보세요.\n7SG 10"

        self.assertIn("빈칸에 알맞은 수", _build_problem_text(raw, ["answer=3"]))

    def test_infers_missing_train_passengers(self) -> None:
        raw = "놀이 공원의 관람 열차에 19명이 타야 출발한다고 합니다. 지금 5명이 타고 있다면 몇 명이 더 타야 합니까?"

        self.assertIn("answer=14", _merge_expression_candidates(raw))

    def test_infers_missing_train_passengers_from_repaired_statement_plus_noisy_ocr(self) -> None:
        raw = "20. 놀이 공원의 관람 열차에 19명이 타야 출발\n20, 놀이 공원의 관람 열차에 1240] 타야 출발한다고 합니다. 지금 5명이 타고 있다면 몇 명"

        self.assertIn("answer=14", _merge_expression_candidates(raw))

    def test_infers_received_items_word_problem(self) -> None:
        raw = "진우는 초콜릿을 7개 가지고 있었는데 예원이가 초콜릿 5개를 진우에게 주었습니다."

        self.assertIn("answer=12", _merge_expression_candidates(raw))

    def test_infers_received_items_when_ocr_interleaves_other_problem(self) -> None:
        raw = (
            "진우는 조콜릿을 7개 가지고 있었는데 예원 "
            "18. 서준이는 색종이 8장과 6장을 가지고 있고 "
            "예원이가 초콜릿 5개를 진우에게 주었습니다."
        )

        self.assertIn("answer=12", _merge_expression_candidates(raw))

    def test_infers_needed_gifts_word_problem(self) -> None:
        raw = "방문객 14명에게 기념품을 한 개씩 나누어 주려고 합니다. 기념품이 6개 있다면 더 필요한 개수는?"

        self.assertIn("answer=8", _merge_expression_candidates(raw))

    def test_infers_min_max_card_digit_sum(self) -> None:
        raw = "가장 작은 수와 가장 큰 수의 합을 구하시오.\n7 0 8 9"

        self.assertIn("answer=9", _merge_expression_candidates(raw))

    def test_infers_smallest_two_digit_from_number_cards(self) -> None:
        raw = "수 카드 중 2장을 뽑아 가장 작은 몇십몇을 만드시오.\n0 4 3 9"

        self.assertIn("answer=30", _merge_expression_candidates(raw))

    def test_infers_fraction_word_sum(self) -> None:
        raw = "물 2/5 L와 1/3L를 합쳤습니다.\n전체 물의 양을 구하시오."

        self.assertIn("2/5+1/3", _merge_expression_candidates(raw))

    def test_infers_probability_table_fraction(self) -> None:
        raw = "공 하나를 뽑을 때 빨간 공일 확률을 구하시오.\ntable_row_2 7 9 1 20"

        self.assertIn("9/20", _merge_expression_candidates(raw))

    def test_infers_derivative_word_velocity(self) -> None:
        raw = "물체의 속도 함수가 v(t)=4t-1입니다.\nt=4에서의 순간속도를 구하시오."

        self.assertIn("4*4-1", _merge_expression_candidates(raw))

    def test_infers_derivative_when_ocr_orders_target_before_formula(self) -> None:
        raw = "t = 4에서의 순간속도를 구하시오.\n물체의 속도 함수가 vit) = 4t - 1입니다."

        self.assertIn("4*4-1", _merge_expression_candidates(raw))

    def test_repairs_integral_constant_with_ocr_tail(self) -> None:
        raw = "함수 f(x)=42] 그래프와 x축 사이의\n0 <= x <= 8 구간 넓이를 구하시오."

        self.assertIn("4*8", _merge_expression_candidates(raw))

    def test_repairs_sticker_count_suffix_noise(self) -> None:
        raw = "민지는 AEAS 374 가지고 있었습니다.\n31장을 더 받고, 그중 15장을 사용했습니다."

        self.assertEqual(_merge_expression_candidates(raw)[0], "37+31-15")

    def test_prefers_labeled_table_row_over_bad_grid_digits(self) -> None:
        raw = "아래 표에서 가장 큰 값과 가장 작은 값의 차를 구하시오.\nat 31 27Al 34\ntable_row_2 31 2 4 34"

        self.assertEqual(_merge_expression_candidates(raw)[0], "41-27")

    def test_infers_function_table_lookup(self) -> None:
        raw = "아래 표는 일차함수의 일부입니다.\nx = 7일 때 y의 값은?\nx 6 7 8\ny 11 13 15"

        self.assertIn("answer=13", _merge_expression_candidates(raw))

    def test_problem_text_uses_repaired_assignment_candidate(self) -> None:
        raw = "오른쪽 직선의 식은 y=2x-4입니다.\nx =-221 때 \\의 값을 구하시오."

        statement = _build_problem_text(raw, ["y=2x-4", "x=-2", "x=-221"])

        self.assertIn("x=-2", statement)
        self.assertIn("y의 값", statement)
        self.assertNotIn("x=-221", statement)

    def test_infers_polynomial_value_from_noisy_f_eval_text(self) -> None:
        raw = "다항식 f(x) = 1x*2 + Ox + 1에서\nf(-3)2| 값을 구하시오."

        self.assertEqual(_merge_expression_candidates(raw)[:2], ["1x^2+0x+1", "x=-3"])

    def test_infers_limit_substitution_from_noisy_text(self) -> None:
        raw = "f(x) = 4x + 22 때\nlim x->1f(x)2| 값을 구하시오."

        self.assertEqual(_merge_expression_candidates(raw)[:2], ["4x+2", "x=1"])

    def test_infers_line_formula_and_slope_from_noisy_graph_text(self) -> None:
        raw = "오른쪽 직선의 식은 y= 3 + 3입니다.\n이 직선의 기울기를 구하시오."
        problem = ProblemSchema(
            normalized_problem_text="이 직선의 기울기를 구하시오.",
            expressions=_merge_expression_candidates(raw),
            math_topic="coordinate_geometry",
        )

        payload = run_solve_pipeline(structured_problem=problem)
        solved = payload["solve_result"]

        self.assertIn("y=3x+3", problem.expressions)
        self.assertEqual(solved.solver_name, "line_slope_solver")
        self.assertEqual(solved.computed_answer, "3")

    def test_prefers_area_from_rectangle_metric_reader_when_unit_mentions_perimeter(self) -> None:
        raw = (
            "초등 5학년ㆍ다각형의 둘레와 넓이ㆍ기본 geometry\n"
            "오른쪽 직사각형의 넓이를 구하시오.\n"
            "rectangle_width 7 rectangle_height 8 rectangle_area 7*8"
        )

        self.assertEqual(_merge_expression_candidates(raw)[0], "7*8")

    def test_replaces_bad_large_x_assignment_with_later_clear_value(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="x=-221 때 y의 값을 구하시오. x=-2일 때 y의 값을 구하시오.",
            expressions=["y=2x-4", "x=-221", "x=-2"],
            math_topic="function",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "-8")

    def test_infers_x_when_ocr_reads_variable_as_star_in_equation(self) -> None:
        raw = "다음 방정식을 푸시오.\n3*+-3=-27"

        self.assertIn("3x-3=-27", _merge_expression_candidates(raw))

    def test_prefers_area_expression_over_constant_function_value(self) -> None:
        raw = "함수 f(x) = 2의 그래프와 x축 사이의\n0 <= x <= 4 구간 넓이를 구하시오."

        self.assertEqual(_merge_expression_candidates(raw)[0], "2*4")

    def test_infers_rectangle_area_from_noisy_ocr_units(self) -> None:
        raw = (
            "가로가 10cm, 세로가 6cme! 직사각형 모양 밭이 있습니다.\n"
            "이 밭의 넓이를 구하시오. 600\n10 007"
        )

        self.assertEqual(_merge_expression_candidates(raw)[0], "10*6")

    def test_infers_rectangle_perimeter_from_word_problem(self) -> None:
        raw = "가로가 8 cm, 세로가 5 cm인 직사각형의 둘레를 구하시오."

        self.assertEqual(_merge_expression_candidates(raw)[0], "2*(8+5)")

    def test_graph_limit_problem_does_not_use_problem_number_as_statement(self) -> None:
        raw = "\n".join(
            [
                "1 2014 6 41",
                "함수 7=7(2)의 그래프가 그림과 같다.",
                "y=f(x)",
                "보기에서 옮은 것을 있는 대로 고른 것은?",
                "ㄱ. lim f(x) =1",
                "L, lim f(z) =-1",
                "ㄷ. 함수 |/(2)|는 ㅜ=2에서 연속이다.",
            ]
        )

        statement = _build_problem_text(raw, ["1", "x=2", "ㄱ. lim f(x) =1"])

        self.assertIn("함수 y=f(x)의 그래프", statement)
        self.assertIn("옳은 것을", statement)

    def test_graph_limit_multiple_choice_is_not_solved_from_noise_number(self) -> None:
        raw = "\n".join(
            [
                "함수 7=7(2)의 그래프가 그림과 같다.",
                "y=f(x)",
                "보기에서 옳은 것을 있는 대로 고른 것은?",
                "ㄱ. lim f(x) =1",
                "ㄴ. lim f(z) =-1",
                "ㄷ. 함수 |/(2)|는 ㅜ=2에서 연속이다.",
            ]
        )
        problem = ProblemSchema(
            source_text_candidates=[raw],
            normalized_problem_text="함수 y=f(x)의 그래프가 그림과 같다. 보기에서 옳은 것을 있는 대로 고른 것은?",
            expressions=["1", "x=2", "ㄱ. lim f(x) =1"],
            choices=["ㄱ . lim f(x) =1\nㄴ. lim f(z) =-1", "ㄷ . 함수 |/(2)|는 ㅜ=2에서 연속이다."],
            question_type="multiple_choice",
            math_topic="coordinate_geometry",
        )

        payload = run_solve_pipeline(structured_problem=problem)
        solved = payload["solve_result"]

        self.assertEqual(solved.solver_name, "visual_graph_guard")
        self.assertEqual(solved.computed_answer, "")
        self.assertEqual(solved.validation_status, "failed")

    def test_extracts_spaced_log_expression(self) -> None:
        self.assertIn("log_5(25)", _merge_expression_candidates("다음 로그의 값을 구하시오.\nlog _5(25)"))

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

    def test_solves_quadratic_equation_with_sympy_worker(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="다음 이차방정식의 해를 구하시오.",
            expressions=["x^2-5x+6=0"],
            math_topic="quadratic",
        )

        payload = run_solve_pipeline(structured_problem=problem)
        solved = payload["solve_result"]

        self.assertEqual(solved.solver_name, "sympy_worker_equation_solver")
        self.assertEqual(solved.computed_answer, "2, 3")

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

    def test_repeated_question_numbers_do_not_become_pattern_answer(self) -> None:
        raw = (
            "3. 점선에 놓인 수에는 ~ 방향으로 갈수록 몇씩 커지는 규칙이 있을까요? "
            "3. 점선에 놓인 수에는 ~, 방향으로 갈수록 wy "
            "3. 점선에 놓인 수에는 \\ 방향으로 갈수록 BA"
        )

        self.assertNotIn("answer=3", _merge_expression_candidates(raw))

    def test_does_not_solve_plain_question_number_as_answer(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="6. 알맞은 말에 O표 하세요.",
            expressions=[],
            math_topic="arithmetic",
        )

        payload = run_solve_pipeline(structured_problem=problem)
        solved = payload["solve_result"]

        self.assertEqual(solved.validation_status, "failed")
        self.assertEqual(solved.computed_answer, "")


if __name__ == "__main__":
    unittest.main()
