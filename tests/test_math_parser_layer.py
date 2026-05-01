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

    def test_repairs_elementary_inline_arithmetic_slash_noise(self) -> None:
        raw = "다음 식의 값을 구하시오.\n4/7-+ 28 - 11"

        self.assertIn("47+28-11", _merge_expression_candidates(raw, school_level="elementary"))

    def test_repairs_elementary_missing_digit_slash_noise(self) -> None:
        raw = "다음 식의 값을 구하시오.\n7/+34-9"

        self.assertIn("77+34-9", _merge_expression_candidates(raw, school_level="elementary"))

    def test_repairs_elementary_plus_ocr_noise(self) -> None:
        raw = "다음 식의 값을 구하시오.\n57ㅜ24-7"

        self.assertIn("57+24-7", _merge_expression_candidates(raw, school_level="elementary"))

    def test_repairs_elementary_compound_plus_ocr_noise(self) -> None:
        raw = "다음 식의 값을 구하시오.\n47ㅠ-+22-12"

        self.assertIn("47+22-12", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_length_subtraction_when_cm_reads_as_07(self) -> None:
        raw = "끈의 길이가 39 00입니다. 그중 11 07를 잘라 사용했습니다. 남은 길이는 몇 07입니까?"

        self.assertIn("39-11", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_length_subtraction_when_middle_unit_noise_intervenes(self) -> None:
        raw = "끈의 길이가 56 00입니다. 그중 coms 잘라 사용했습니다. 중 11 07를 잘라 사용했습니다."

        self.assertIn("56-11", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_sticker_word_problem_when_counter_reads_as_s(self) -> None:
        raw = "민지는 AEA S 79S 가지고 있었습니다. 36장을 더 받고, 그중 23장을 사용했습니다. 남은 스티커는 몇 장입니까?"

        self.assertIn("79+36-23", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_sticker_word_problem_when_jang_reads_as_48_or_8(self) -> None:
        raw = (
            "민지는 스티커를 6648 가지고 있었습니다.\n"
            "23장을 더 받고, 그중 24장을 사용했습니다. 남은 스티커는 몇 장입니까?"
        )

        self.assertIn("66+23-24", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_elementary_usage_subtraction_when_geujung_reads_as_as(self) -> None:
        raw = "연필가 1574 있습니다. AS 10개를 사용했습니다. 남은 연필는 몇 개입니까?"

        self.assertIn("answer=5", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_elementary_equal_share_division(self) -> None:
        raw = "75개를 5명에게 똑같이 나누어 주려고 합니다. 한 명이 받는 개수는 몇 개입니까?"

        self.assertIn("answer=15", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_elementary_angle_more_than_problem(self) -> None:
        raw = "138도인 각보다 59도 큰 각은 몇 도입니까?"

        self.assertIn("answer=197", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_elementary_circle_diameter_from_radius(self) -> None:
        raw = "반지름이 10cme! 원의 지름을 구하시오."

        self.assertIn("answer=20", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_elementary_gcd_from_noisy_pair(self) -> None:
        raw = "432) 17의 최대공약수를 구하시오."

        self.assertIn("answer=1", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_elementary_gcd_when_separator_and_suffix_are_noisy(self) -> None:
        raw = "932) 632| 최대공약수를 구하시오."

        self.assertIn("answer=3", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_elementary_time_after_minutes(self) -> None:
        raw = "4A] 45분에서 202 뒤의 시각을 쓰시오."
        problem = ProblemSchema(
            normalized_problem_text=raw,
            expressions=_merge_expression_candidates(raw, school_level="elementary"),
            math_topic="measurement",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertIn("answer_text=5시 5분", problem.expressions)
        self.assertEqual(solved.computed_answer, "5시 5분")

    def test_infers_elementary_max_from_statistics_row(self) -> None:
        raw = "띠그래프에 나타난 항목 중 가장 큰 값을 고르시오.\n5, 17,57, 30"

        self.assertIn("answer=57", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_fraction_division_when_divide_sign_reads_as_plus(self) -> None:
        raw = "초등 6학년ㆍ분수ㆍ소수의 나눗셈 reserve expression fraction_\n6/12 +5"

        self.assertIn("answer=6/60", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_fraction_division_when_divide_sign_reads_as_angle_or_space(self) -> None:
        raw = "초등 6학년ㆍ분수ㆍ소수의 나눗셈 reserve expression fraction_\n3/5 > 7\n4/12 5"

        self.assertIn("answer=3/35", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_fraction_division_when_question_number_glues_to_numerator(self) -> None:
        raw = "\n".join(
            [
                "BS 6학년ㆍ분수ㆍ소수의 LiL: reserve expression ㆍ fraction_",
                "© & -AIS] ㅎ",
                "68/5 9",
                "초등 6학년ㆍ분수ㆍ소수의 Lp Al - reserve expression ㆍ fraction_",
                "8/5+9",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw, school_level="elementary")[0], "answer=8/45")

    def test_infers_fraction_division_when_separator_reads_as_angle_comma(self) -> None:
        raw = "\n".join(
            [
                "AS 6학년ㆍ분수ㆍ소수의 Lf EA! - reserve expression : fraction.",
                "Oo Ei A L_ Oo =",
                "7/5 >, 5",
                "초등 6학년ㆍ분수ㆍ소수의 Lp Al - reserve expression ㆍ fraction_",
                "(2) = = =",
                "7/545",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw, school_level="elementary")[0], "answer=7/25")

    def test_repairs_repeated_slash_digit_as_single_addend(self) -> None:
        raw = "다음 식의 값을 구하시오.\n89ㅜ+7/7-23"

        self.assertIn("89+7-23", _merge_expression_candidates(raw, school_level="elementary"))

    def test_sticker_word_problem_uses_later_cleaner_event_candidate(self) -> None:
        raw = (
            "민지는 스티커를 408 가지고 있었습니다.\n"
            "40장을 더 받고, 그중 27장을 사용했습니다. 남은 스티커는 몇 장입니까?\n"
            "민지는 스티커를 40장 가지고 있었습니다.\n"
            "40장을 더 받고, 그중 21장을 사용했습니다. 남은 스티커는 몇 장입니까?"
        )
        expressions = _merge_expression_candidates(raw, school_level="elementary")
        problem = ProblemSchema(
            normalized_problem_text="남은 스티커는 몇 장입니까?",
            expressions=expressions,
            math_topic="arithmetic",
            source_text_candidates=[raw],
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "59")

    def test_infers_sticker_word_problem_when_added_eleven_reads_as_n(self) -> None:
        raw = "민지는 AAS 472 가지고 있었습니다. Ns 더 받고, 그중 25장을 사용했습니다. 남은 스티커는 몇 장입니까?"

        self.assertIn("47+11-25", _merge_expression_candidates(raw, school_level="elementary"))

    def test_infers_sticker_word_problem_from_areas_alias(self) -> None:
        raw = "민지는 AREAS 4442 가지고 있었습니다. 30장을 더 받고, 그중 3장을 사용했습니다. 남은 스티커는 몇 장입니까?"

        self.assertIn("44+30-3", _merge_expression_candidates(raw, school_level="elementary"))

    def test_direct_numeric_solver_prefers_full_sticker_event(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="남은 스티커는 몇 장입니까?",
            expressions=["57+31-1", "57+31-11", "51+31-1", "51+31-11"],
            math_topic="arithmetic",
            source_text_candidates=[
                "민지는 스티커를 51장 가지고 있었습니다. 31장을 더 받고, 그중 11장을 사용했습니다.\n"
                "민지는 스티커를 57장 가지고 있었습니다. 31장을 더 받고, 그중 1장을 사용했습니다."
            ],
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "direct_numeric_solver")
        self.assertEqual(solved.computed_answer, "71")

    def test_explicit_visual_answer_preempts_noisy_pattern_progression(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="만두 6개를 두 사람이 똑같이 나누어 먹으려고 합니다.",
            expressions=["answer_text=3개"],
            math_topic="arithmetic",
            source_text_candidates=[
                "10. 만두 6 개를 나누어 먹으려고 합니다. 16. 계산 결과가 같은 것에 ○표 하세요. 2 3 4 5 6 7",
            ],
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "visual_template_solver")
        self.assertEqual(solved.computed_answer, "3개")

    def test_visual_template_numeric_answer_preempts_noisy_pattern_progression(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="뺄셈을 해 보세요. 5-5",
            expressions=["answer=0"],
            math_topic="arithmetic",
            source_text_candidates=[
                "10. 만두 6개 11. 풍선 7개 12. 그림 13. 뺄셈 14. 뺄셈식 15. 수 카드 3 5 6 7 8",
            ],
            metadata={"visual_template": {"rule_id": "grade1_add_sub_round2_subtract_five_five"}},
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "table_lookup_solver")
        self.assertEqual(solved.computed_answer, "0")

    def test_direct_numeric_solver_prefers_shorter_repaired_candidate(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="다음 식의 값을 구하시오.",
            expressions=["155+9-7", "15+9-7"],
            math_topic="arithmetic",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "direct_numeric_solver")
        self.assertEqual(solved.computed_answer, "17")

    def test_direct_numeric_solver_prefers_expression_that_survives_in_source_pass(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="다음 식의 값을 구하시오.",
            expressions=["62+22-19", "62+27-19"],
            math_topic="arithmetic",
            source_text_candidates=["다음 식의 값을 구하시오.\n62+2/-19\n62 + 27 - 19"],
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "direct_numeric_solver")
        self.assertEqual(solved.computed_answer, "70")

    def test_direct_numeric_solver_prefers_later_clean_expression_pass(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="다음 식의 값을 구하시오.",
            expressions=["144+32-22", "74+32-22"],
            math_topic="arithmetic",
            source_text_candidates=[
                "다음 식의 값을 구하시오.\n144+ 32-22\n다음 식의 값을 구하시오.\n74 + 32-22"
            ],
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "direct_numeric_solver")
        self.assertEqual(solved.computed_answer, "84")

    def test_direct_numeric_solver_prefers_longer_leading_number_variant(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="다음 식의 값을 구하시오.",
            expressions=["14+32-2", "74+32-2"],
            source_text_candidates=["다음 식의 값을 구하시오.\n74+32-2\n14+32-2"],
            math_topic="geometry",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "direct_numeric_solver")
        self.assertEqual(solved.computed_answer, "104")

    def test_repairs_pattern_sequence_when_seven_reads_as_slash(self) -> None:
        raw = "규칙을 찾아 빈칸에 알맞은 수를 쓰시오.\n3, / 11, 15, □"

        expressions = _merge_expression_candidates(raw, school_level="elementary")

        self.assertIn("answer=19", expressions)

    def test_pattern_solver_repairs_spaced_dot_sequence_separator(self) -> None:
        raw = "규칙을 찾아 빈칸에 알맞은 수를 쓰시오.\n5, / 9. 11,"
        problem = ProblemSchema(
            normalized_problem_text="규칙을 찾아 빈칸에 알맞은 수를 쓰시오.",
            expressions=["answer=11", "5,/9.11"],
            math_topic="pattern",
            source_text_candidates=[raw],
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "pattern_sequence_solver")
        self.assertEqual(solved.computed_answer, "13")

    def test_pattern_solver_uses_progression_instead_of_last_visible_term(self) -> None:
        raw = "규칙을 찾아 빈칸에 알맞은 수를 쓰시오.\n3, 10, 17 24, □"
        problem = ProblemSchema(
            normalized_problem_text="규칙을 찾아 빈칸에 알맞은 수를 쓰시오.",
            expressions=["answer=24"],
            math_topic="pattern",
            source_text_candidates=[raw],
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "pattern_sequence_solver")
        self.assertEqual(solved.computed_answer, "31")

    def test_pattern_answer_candidate_ignores_target_ordinal_noise(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="아래 표의 규칙을 보고 5번째 값을 구하시오.",
            expressions=["answer=5", "answer=19"],
            math_topic="pattern",
            source_text_candidates=["아래 표의 규칙을 보고 5번째 값을 구하시오.\n값 3 7 11 15"],
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "pattern_sequence_solver")
        self.assertEqual(solved.computed_answer, "19")

    def test_pattern_solver_reads_table_row_before_ordinal_noise(self) -> None:
        raw = "아래 표의 규칙을 보고 5번째 값을 구하시오.\ntable_row_1 1 2 3\ntable_row_2 6 9 12 15"
        problem = ProblemSchema(
            normalized_problem_text="아래 표의 규칙을 보고 SHA 값을 구하시오.",
            expressions=["answer=18", "answer=5"],
            math_topic="pattern",
            source_text_candidates=[raw],
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "pattern_sequence_solver")
        self.assertEqual(solved.computed_answer, "18")

    def test_pattern_solver_repairs_dropped_tens_in_table_row(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="아래 표의 규칙을 보고 SHA 값을 구하시오.",
            expressions=["answer=5"],
            math_topic="pattern",
            source_text_candidates=["아래 표의 규칙을 보고 5번째 값을 구하시오.\ntable_row_2 7 1 15 19"],
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "pattern_sequence_solver")
        self.assertEqual(solved.computed_answer, "23")

    def test_repairs_pattern_table_single_digit_ocr_drop(self) -> None:
        raw = "아래 표의 규칙을 보고 5번째 값을 구하시오.\n순서 1 2 3 4\n값 7 9 1 13"

        expressions = _merge_expression_candidates(raw, school_level="elementary")

        self.assertIn("answer=15", expressions)

    def test_average_solver_repairs_comma_sequence_slash_noise(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="다음 자료의 평균을 구하시오.",
            expressions=["(92+60+84+93)/4", "92,7/60,84,93"],
            math_topic="statistics",
            source_text_candidates=["다음 자료의 평균을 구하시오.\n92, 7/60, 84, 93"],
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "average_table_solver")
        self.assertEqual(solved.computed_answer, "406/5")

    def test_average_solver_repairs_leading_seven_as_slash_noise(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="다음 자료의 평균을 구하시오.",
            expressions=["(73+85+78+75)/4", "9/73,85,78,75"],
            math_topic="statistics",
            source_text_candidates=["다음 자료의 평균을 구하시오.\n9/73, 85, 78, 75"],
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "average_table_solver")
        self.assertEqual(solved.computed_answer, "408/5")

    def test_average_solver_prefers_explicit_five_value_expression(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="다음 자료의 평균을 구하시오.",
            expressions=["(67+73+73+61+84)/5", "(73+73+61+84)/4"],
            math_topic="statistics",
            source_text_candidates=["다음 자료의 평균을 구하시오.\n67 73, 73, 61, 84"],
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "average_table_solver")
        self.assertEqual(solved.computed_answer, "358/5")

    def test_average_solver_repairs_table_row_missing_ones_place(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="아래 표의 자료에서 평균을 구하시오.",
            expressions=["34+4+24+2", "(400+0+100+0+161+34+24+27+34+24)/10"],
            math_topic="statistics",
            source_text_candidates=["아래 표의 자료에서 평균을 구하시오.\n값 34 4 24 27\ntable_row_2 34 4 24 2"],
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "average_table_solver")
        self.assertEqual(solved.computed_answer, "63/2")

    def test_average_solver_reads_korean_ocr_syllable_as_forty_one(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="아래 표의 자료에서 평균을 구하시오.",
            expressions=["45+43+4+45", "(2+45+43+4+45)/5", "(45+43+45+45+43+45)/6"],
            math_topic="statistics",
            source_text_candidates=["아래 표의 자료에서 평균을 구하시오.\n값 45 43 시 45\ntable_row_2 45 43 4 45"],
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "average_table_solver")
        self.assertEqual(solved.computed_answer, "87/2")

    def test_average_solver_reads_space_separated_clean_value_line(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="다음 자료의 평균을 구하시오.",
            expressions=["(77+76+72+79)/4", "9/7776,72,79"],
            math_topic="statistics",
            source_text_candidates=["다음 자료의 평균을 구하시오.\n9/7/ 76, 72, 79\n97 77 76, 72, 79"],
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "average_table_solver")
        self.assertEqual(solved.computed_answer, "401/5")

    def test_average_solver_repairs_missing_seven_before_average_value(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="다음 자료의 평균을 구하시오.",
            expressions=["(85+92+98+86)/4", "85,/992,98,86"],
            math_topic="statistics",
            source_text_candidates=["다음 자료의 평균을 구하시오.\n85, /9 92, 98, 86"],
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "average_table_solver")
        self.assertEqual(solved.computed_answer, "88")

    def test_rectangle_area_metric_expression_beats_truncated_product(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="이 밭의 넓이를 구하시오.",
            expressions=["12*1", "12*11", "rectangle_width12rectangle_height11rectangle_area12*11"],
            math_topic="geometry",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "132")

    def test_infers_circle_circumference_from_metric_reader_text(self) -> None:
        raw = "원주율을 3.14로 하여 오른쪽 원의 둘레를 구하시오.\ncircle_radius 4"

        expressions = _merge_expression_candidates(raw, school_level="elementary")
        self.assertIn("2*3.14*4", expressions)

        problem = ProblemSchema(
            normalized_problem_text=raw,
            expressions=expressions,
            math_topic="geometry",
        )
        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "25.12")

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

    def test_average_solver_prefers_average_expression_over_plain_sum(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="아래 표의 자료에서 평균을 구하시오.",
            expressions=["44+23+29+13", "(44+23+29+13)/4"],
            math_topic="statistics",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "average_table_solver")
        self.assertEqual(solved.computed_answer, "109/4")

    def test_average_solver_prefers_clean_sum_over_noisy_ocr_average(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="아래 표의 자료에서 평균을 구하시오.",
            expressions=["19+32+19+39", "(0+19+0+132+0)/5", "(19+0+132+0+19+0+139+19+32+19+39)/11"],
            math_topic="statistics",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "average_table_solver")
        self.assertEqual(solved.computed_answer, "109/4")

    def test_average_solver_handles_ocr_noise_in_average_keyword(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="아래 표의 자료에서 SHS 구하시오.",
            expressions=["31+34+25+25"],
            math_topic="statistics",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "average_table_solver")
        self.assertEqual(solved.computed_answer, "115/4")

    def test_average_solver_prefers_complete_five_value_candidate(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="다섯 번의 점수가 다음과 같습니다. 81, 98, 65, 80, 97의 평균을 구하시오.",
            expressions=["(98+65+80+97)/4", "(81+98+65+80+97)/5"],
            math_topic="statistics",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "average_table_solver")
        self.assertEqual(solved.computed_answer, "421/5")

    def test_average_solver_repairs_trailing_korean_particle_digit_noise(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="다섯 번의 점수가 다음과 같습니다.",
            expressions=["(76+66+72+77+652)/5"],
            math_topic="statistics",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "average_table_solver")
        self.assertEqual(solved.computed_answer, "356/5")

    def test_average_solver_prefers_complete_expression_over_broken_table_row(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="아래 표의 자료에서 평균을 구하시오.",
            expressions=["37+42+37+27", "(430+0+100+0+161+37+42+37+27+37+42+37)/12"],
            source_text_candidates=["값 37 42 37 27\ntable_row_2 37 42 37 2"],
            math_topic="statistics",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "average_table_solver")
        self.assertEqual(solved.computed_answer, "143/4")

    def test_average_solver_prefers_later_clean_ocr_pass_for_average_row(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="다음 자료의 SAS 구하시오",
            expressions=["(66+73+88+66+32)/5"],
            source_text_candidates=[
                "다음 자료의 SAS 구하시오.\n66, 73, 88, 66, 32\n"
                "다음 자료의 BS 구하시오.\n66, 73, 88, 88, 82"
            ],
            math_topic="statistics",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "average_table_solver")
        self.assertEqual(solved.computed_answer, "397/5")

    def test_average_solver_does_not_steal_table_difference_problem(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="아래 표에서 가장 큰 값과 가장 작은 값의 차를 구하시오.",
            expressions=["41-15", "34-4"],
            math_topic="statistics",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertNotEqual(solved.solver_name, "average_table_solver")
        self.assertEqual(solved.computed_answer, "26")

    def test_solves_table_difference_from_source_row_when_expression_is_sum(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="아래 표에서 가장 큰 값과 가장 작은 값의 차를 구하시오.",
            expressions=["13+16+44+36"],
            source_text_candidates=["아래 표에서 가장 큰 값과 가장 작은 값의 APS 구하시오.\nat 13 16 44 36\ntable_row_2 13 16 44 36"],
            math_topic="statistics",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "table_difference_solver")
        self.assertEqual(solved.computed_answer, "31")

    def test_infers_pattern_table_next_value(self) -> None:
        raw = "아래 표의 규칙을 보고 5번째 값을 구하시오.\ntable_row_1 1 2 3\ntable_row_2 5 7 9 1"

        self.assertIn("answer=13", _merge_expression_candidates(raw))

    def test_infers_pattern_word_growth(self) -> None:
        raw = "첫째 날 2개를 만들고 매일 5개씩 더 많이 만듭니다.\n6째 날에는 몇 개를 만듭니까?"

        self.assertIn("answer=27", _merge_expression_candidates(raw))

    def test_infers_pattern_word_growth_from_later_clean_pass(self) -> None:
        raw = (
            "첫째 날 7개를 만들고 매일 6714 더 많이 만듭니다.\n"
            "5째 날에는 몇 개를 만듭니까?\n"
            "첫째 날 7개를 만들고 매일 6개씩 더 많이 만듭니다."
        )

        self.assertEqual(_merge_expression_candidates(raw)[0], "answer=31")

    def test_solves_pattern_sequence_when_ocr_glues_seven_and_nine(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="규칙을 찾아 빈칸에 알맞은 수를 쓰시오.",
            expressions=["=10="],
            source_text_candidates=["규칙을 찾아 빈칸에 알맞은 수를 쓰시오.\n3,5,79, 0"],
            math_topic="pattern",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "pattern_sequence_solver")
        self.assertEqual(solved.computed_answer, "11")

    def test_repairs_difference_table_dropped_ones_place(self) -> None:
        raw = "아래 표에서 가장 큰 값과 가장 작은 값의 차를 구하시오.\ntable_row_2 4 30 34 15"

        self.assertIn("41-15", _merge_expression_candidates(raw))

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

    def test_preserves_elementary_fraction_arithmetic_slashes(self) -> None:
        raw = "초등 4학년 분수 계산\n다음 분수 계산을 하시오.\n3/8 + 1/10"

        expressions = _merge_expression_candidates(raw, school_level="elementary")

        self.assertEqual(expressions[0], "3/8+1/10")

    def test_repairs_condensed_fraction_term_in_fraction_context(self) -> None:
        raw = "초등 4학년 분수 계산\n물 273LO 1/1LS 합쳤습니다.\n전체 물의 양을 구하시오."

        expressions = _merge_expression_candidates(raw, school_level="elementary")

        self.assertIn("2/3+1/1", expressions)

    def test_fraction_solver_prefers_distinct_word_fractions(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="전체 물의 양을 구하시오.",
            expressions=["4/5+4/5", "4/5+1/10"],
            source_text_candidates=["물 4/5L와 1710LS 합쳤습니다.\n전체 물의 양을 구하시오."],
            math_topic="fraction_ratio",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "fraction_solver")
        self.assertEqual(solved.computed_answer, "9/10")

    def test_fraction_solver_prefers_fraction_expression_from_clean_source_pass(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="1/2+3/5",
            expressions=["1/2+3/5", "5/12+3/5"],
            source_text_candidates=["다음 분수 계산을 하시오.\n5/12 + 3/5"],
            math_topic="fraction_ratio",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "fraction_solver")
        self.assertEqual(solved.computed_answer, "61/60")

    def test_fraction_solver_repairs_word_fraction_ocr_suffix_noise(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="전체 물의 양을 구하시오.",
            expressions=["1/59+1/6"],
            source_text_candidates=["물 115 Ｌ와 1/6LS 합쳤습니다.\n전체 물의 양을 구하시오."],
            math_topic="fraction_ratio",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "fraction_solver")
        self.assertEqual(solved.computed_answer, "11/30")

    def test_fraction_solver_prefers_duplicate_fraction_when_clean_source_has_it(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="1/2+5/12",
            expressions=["1/2+5/12", "5/12+5/12"],
            source_text_candidates=["다음 분수 계산을 하시오.\n5/12 + 5/12"],
            math_topic="fraction_ratio",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "fraction_solver")
        self.assertEqual(solved.computed_answer, "5/6")

    def test_fraction_solver_repairs_word_fraction_missing_slash_between_one_and_two(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="전체 물의 양을 구하시오",
            expressions=["1/1+1/1"],
            source_text_candidates=["물 12LO 1/1LS 합쳤습니다.\n전체 물의 양을 구하시오."],
            math_topic="fraction_ratio",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "fraction_solver")
        self.assertEqual(solved.computed_answer, "3/2")

    def test_infers_fraction_word_when_one_liter_loses_denominator(self) -> None:
        raw = "물 1/12 Ｌ와 1LS 합쳤습니다.\n전체 물의 양을 구하시오."

        self.assertIn("1/12+1/1", _merge_expression_candidates(raw))

    def test_fraction_solver_repairs_repeated_denominator_digit_noise(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="전체 물의 양을 구하시오",
            expressions=["1/2+1/44"],
            source_text_candidates=["= 1/2LO) 1/44LS 합쳤습니다.\n= 1/212) 1/4 Ｌ를 합쳤습니다."],
            math_topic="fraction_ratio",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "fraction_solver")
        self.assertEqual(solved.computed_answer, "3/4")

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

    def test_table_difference_solver_wins_over_average_unit_title(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="아래 표에서 가장 큰 값과 가장 작은 값의 차를 구하시오.",
            expressions=["44-14", "(14+37+44+24+14+37+44+24)/8"],
            source_text_candidates=["초등 5학년ㆍ평균과 가능성ㆍ기본 table - statistics\nat 14 37 44 24\ntable_row_2 14 37 44 24"],
            math_topic="statistics",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "table_difference_solver")
        self.assertEqual(solved.computed_answer, "30")

    def test_infers_function_table_lookup(self) -> None:
        raw = "아래 표는 일차함수의 일부입니다.\nx = 7일 때 y의 값은?\nx 6 7 8\ny 11 13 15"

        self.assertIn("answer=13", _merge_expression_candidates(raw))

    def test_repairs_function_table_row_dropped_tens(self) -> None:
        raw = "아래 표는 일차함수의 일부입니다.\nx = 3일 때 y의 값을 구하시오.\ntable_row_1 1 2 3\ntable_row_2 1 6 1 16"

        self.assertIn("answer=11", _merge_expression_candidates(raw))

    def test_does_not_repair_function_table_first_value_when_middle_cell_is_noisy(self) -> None:
        raw = "아래 표는 일차함수의 일부입니다.\nx = 1일 때 y의 값을 구하시오.\ntable_row_1 1 2 3\ntable_row_2 1 6 1 16"

        self.assertIn("answer=1", _merge_expression_candidates(raw))

    def test_repairs_function_table_first_value_dropped_tens(self) -> None:
        raw = "아래 표는 일차함수의 일부입니다.\nx = 1일 때 y의 값을 구하시오.\ntable_row_1 1 2 3\ntable_row_2 1 14 17 20"

        self.assertIn("answer=11", _merge_expression_candidates(raw))

    def test_repairs_function_table_last_value_dropped_tens(self) -> None:
        raw = "아래 표는 일차함수의 일부입니다.\nx = 4일 때 y의 값을 구하시오.\ntable_row_1 1 2 3\ntable_row_2 2 5 8 1"

        self.assertIn("answer=11", _merge_expression_candidates(raw))

    def test_repairs_function_table_middle_value_dropped_tens_without_touching_previous_cell(self) -> None:
        raw = "아래 표는 일차함수의 일부입니다.\nx = 2일 때 y의 값을 구하시오.\nx 1 2 3 4\ny 5 8 1 14\ntable_row_1 1 2 3\ntable_row_2 5 8 1 14"

        self.assertIn("answer=8", _merge_expression_candidates(raw))

    def test_inserts_missing_negative_function_table_value(self) -> None:
        raw = "아래 표는 일차함수의 일부입니다.\nx = 2일 때 y의 값을 구하시오.\ntable_row_1 1 2 3\ntable_row_2 -5 -9 -11"

        self.assertIn("answer=-7", _merge_expression_candidates(raw))

    def test_solver_prefers_repaired_later_table_answer_candidate(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="x = 3일 때 y의 값을 구하시오.",
            expressions=["answer=-5", "answer=-7", "x=3", "table_row_2-3-5-9"],
            math_topic="function",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "table_lookup_solver")
        self.assertEqual(solved.computed_answer, "-7")

    def test_keeps_longer_raw_function_y_row_than_short_grid_row(self) -> None:
        raw = "아래 표는 일차함수의 일부입니다.\nx = 1일 때 y의 값을 구하시오.\nx 1 2 3 4\ny 0 5 10 15\ntable_row_1 1 2 3\ntable_row_2 5 10 15"

        self.assertIn("answer=0", _merge_expression_candidates(raw))

    def test_repairs_function_table_ocr_one_in_last_column(self) -> None:
        raw = "아래 표는 일차함수의 일부입니다.\nx = 3일 때 y의 값을 구하시오.\ny ㄱ 3 7 1\ntable_row_1 1 2 3\ntable_row_2 -1 3 7 1"

        self.assertIn("answer=7", _merge_expression_candidates(raw))

    def test_prefers_shifted_negative_function_table_value(self) -> None:
        raw = "아래 표는 일차함수의 일부입니다.\nx = 3일 때 y의 값을 구하시오.\ntable_row_1 1 2 3\ntable_row_2 -9 -11 -13"

        self.assertEqual(_merge_expression_candidates(raw)[0], "answer=-11")

    def test_prefers_original_shifted_negative_value_before_progression_repair(self) -> None:
        raw = "아래 표는 일차함수의 일부입니다.\nx = 3일 때 y의 값을 구하시오.\ntable_row_1 1 2 3\ntable_row_2 -5 -9 -11"

        self.assertEqual(_merge_expression_candidates(raw)[0], "answer=-9")

    def test_infers_line_formula_when_y_is_read_as_greater_than(self) -> None:
        raw = "오른쪽 직선의 식은 > = -3 + 4입니다.\nx = 3일 때 y의 값을 구하시오."

        self.assertIn("y=-3x+4", _merge_expression_candidates(raw))

    def test_infers_line_formula_when_x_is_percent_and_target_is_korean_giyeok(self) -> None:
        raw = "오른쪽 직선의 식은 y= 4%- 5입니다.\n*=ㄱ일 때 y의 값을 구하시오."
        problem = ProblemSchema(
            normalized_problem_text="*=ㄱ일 때 y의 값을 구하시오.",
            expressions=_merge_expression_candidates(raw),
            math_topic="function",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertIn("y=4x-5", problem.expressions)
        self.assertIn("x=-1", problem.expressions)
        self.assertEqual(solved.solver_name, "function_value_solver")
        self.assertEqual(solved.computed_answer, "-9")

    def test_infers_line_formula_when_y_label_is_read_as_sy_and_four_as_letters(self) -> None:
        raw = "오른쪽 직선의 Sy = -3x +AQLCh a.\nx = 2일 때 y의 값을 구하시오."
        problem = ProblemSchema(
            normalized_problem_text="x = 2일 때 y의 값을 구하시오.",
            expressions=_merge_expression_candidates(raw),
            math_topic="function",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertIn("y=-3x+4", problem.expressions)
        self.assertEqual(solved.computed_answer, "-2")

    def test_infers_line_formula_when_coefficient_one_is_read_as_capital_i(self) -> None:
        raw = "오른쪽 직선의 식은 y = Ix - 4입니다.\nx = 5일 때 y의 값을 구하시오."
        problem = ProblemSchema(
            normalized_problem_text="x = 5일 때 y의 값을 구하시오.",
            expressions=_merge_expression_candidates(raw),
            math_topic="function",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertIn("y=1x-4", problem.expressions)
        self.assertEqual(solved.computed_answer, "1")

    def test_infers_line_formula_trailing_plus_as_zero(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="X= -2일 때 y의 값을 구하시오",
            expressions=["x=-2", "y=3x+"],
            math_topic="function",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "function_value_solver")
        self.assertEqual(solved.computed_answer, "-6")

    def test_repairs_noisy_negative_one_assignment_with_extra_digit(self) -> None:
        raw = "오른쪽 직선의 식은 y= 4x - 2입니다.\nx = -12! 때 y의 값을 구하시오."
        problem = ProblemSchema(
            normalized_problem_text="x = -12! 때 y의 값을 구하시오.",
            expressions=_merge_expression_candidates(raw),
            math_topic="function",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertIn("x=-1", problem.expressions)
        self.assertEqual(solved.computed_answer, "-6")

    def test_prefers_repaired_negative_one_over_negative_ten_assignment(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="x = -10 때 y의 값을 구하시오.",
            expressions=["y=1x-3", "x=1", "x=-10", "x=-1", "x=12"],
            math_topic="function",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "-4")

    def test_infers_line_formula_when_plus_is_read_as_four_between_terms(self) -> None:
        raw = "오른쪽 직선의 식은 y= 3x4 3입니다.\nX= 3일 때 y의 값을 구하시오."
        problem = ProblemSchema(
            normalized_problem_text="X= 3일 때 y의 값을 구하시오.",
            expressions=_merge_expression_candidates(raw),
            math_topic="function",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertIn("y=3x+3", problem.expressions)
        self.assertEqual(solved.computed_answer, "12")

    def test_infers_function_word_formula_from_expression_label(self) -> None:
        raw = "x = 6일 때 전체 개수를 식 y = 2x + 1로 구하시오."
        problem = ProblemSchema(
            normalized_problem_text="x = 6일 때 전체 개수를 식 y = 2x + 1로 구하시오.",
            expressions=_merge_expression_candidates(raw),
            math_topic="function",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertIn("y=2x+1", problem.expressions)
        self.assertEqual(solved.computed_answer, "13")

    def test_infers_function_word_x_when_ocr_reads_x_as_xx(self) -> None:
        raw = "xX = 3일 때 전체 개수를 식 = 2x +1로 구하시오."
        problem = ProblemSchema(
            normalized_problem_text="xX = 3일 때 전체 개수를 식 = 2x +1로 구하시오.",
            expressions=_merge_expression_candidates(raw),
            math_topic="function",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertIn("y=2x+1", problem.expressions)
        self.assertIn("x=3", problem.expressions)
        self.assertEqual(solved.computed_answer, "7")

    def test_repairs_function_word_constant_suffix_noise(self) -> None:
        raw = "날개 7개가 더 있습니다. x = 5일 때 전체 개수를 식 = 2x + 7H 구하시오."
        problem = ProblemSchema(
            normalized_problem_text="x = 5일 때 전체 개수를 식 = 2x + 7H 구하시오.",
            expressions=_merge_expression_candidates(raw),
            math_topic="function",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertIn("y=2x+7", problem.expressions)
        self.assertEqual(solved.computed_answer, "17")

    def test_repairs_function_word_constant_when_eight_reads_as_be(self) -> None:
        raw = "한 묶음에 2개씩 들어 있고 날개 8개가 더 있습니다. x = 5일 때 전체 개수를 식 / = 2x + BE 구하시오."
        problem = ProblemSchema(
            normalized_problem_text="x = 5일 때 전체 개수를 식 / = 2x + BE 구하시오.",
            expressions=_merge_expression_candidates(raw),
            math_topic="function",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertIn("y=2x+8", problem.expressions)
        self.assertEqual(solved.computed_answer, "18")

    def test_prefers_nonzero_function_constant_over_trailing_zero_fallback(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="x = 5일 때 y의 값을 구하시오.",
            expressions=["y=-2x+1", "x=5", "y=-2x+0"],
            math_topic="function",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "-9")

    def test_prefers_later_clean_simple_numeric_expression_from_source(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="다음 식의 값을 구하시오.",
            expressions=["93+8", "53+8"],
            source_text_candidates=["다음 식의 값을 구하시오.\n93 +8\n다음 식의 값을 구하시오.\n53+8"],
            math_topic="function",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "direct_numeric_solver")
        self.assertEqual(solved.computed_answer, "61")


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

    def test_reserve_word_story_does_not_span_into_next_metadata_header(self) -> None:
        raw = "\n".join(
            [
                "： 초등 1학년 ㆍ덧셈과 wal - reserve word : arithmetic",
                "스티커가 1471 있습니다. AS 1271S 사용했습니다.",
                "초등 1학년 ㆍ덧셈과 wal. reserve word ㆍ arithmetic",
                "스티커가 1474 있습니다. 그중 12개를 사용했습니다.",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw)[0], "answer=2")

    def test_reserve_word_story_repairs_count_suffixes(self) -> None:
        raw = "\n".join(
            [
                "： AS 1학년ㆍ덧셈과 WA - reserve word ㆍ arithmetic",
                "공책가 671 있습니다. AS 4715 사용했습니다.",
                "초등 1학년 ㆍ덧셈과 wall - reserve word ㆍ arithmetic",
                "공책가 6개 있습니다. AS 4개를 사용했습니다.",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw)[0], "answer=2")

    def test_reserve_time_delta_trims_percent_noise(self) -> None:
        self.assertEqual(
            _merge_expression_candidates("8시 35분에서 205 뒤의 시각을 쓰시오.")[0],
            "answer_text=8시 55분",
        )
        self.assertEqual(
            _merge_expression_candidates("9시 15분에서 308 뒤의 시각을 쓰시오.")[0],
            "answer_text=9시 45분",
        )
        self.assertEqual(
            _merge_expression_candidates("7시 15분에서 330% 뒤의 시각을 쓰시오.")[0],
            "answer_text=7시 45분",
        )

    def test_reserve_angle_delta_ignores_trailing_ocr_digit(self) -> None:
        self.assertEqual(
            _merge_expression_candidates("31도인 각보다 105 큰 각은 몇 도입니까?")[0],
            "answer=41",
        )
        self.assertEqual(
            _merge_expression_candidates("65도인 각보다 125 큰 각은 몇 도입니까?")[0],
            "answer=77",
        )

    def test_reserve_angle_prefers_clean_question_line_over_noisy_header_passes(self) -> None:
        raw = "\n".join(
            [
                "초등 4학년 - Z2t& - reserve geometry - angle",
                "90도인 각보다 45 큰 각은 B 도입니까?",
                "초등 4학년 ㆍ각도 reserve 8601066ㆍ20812",
                "90도인 각보다 14도 큰 각은 몇 도입니까?",
                "| 초등 4학년 ㆍ각도 - reserve geometry - angle |",
                "90도인 각보다 145 큰 각은 B 도입니까?",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw)[0], "answer=104")

    def test_reserve_angle_repairs_base_when_doin_suffix_reads_as_digits(self) -> None:
        raw = "\n".join(
            [
                "초등 4학년 - Z2t& - reserve geometry - angle",
                "4029! 각보다 285 큰 각은 B 도입니까?",
                "초등 4학년 ㆍ각도 reserve 8601066ㆍ20812",
                "40291 각보다 28도 큰 각은 몇 도입니까?",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw)[0], "answer=68")

    def test_reserve_angle_keeps_three_digit_base_before_noisy_doin_suffix(self) -> None:
        raw = "\n".join(
            [
                "초등 4학년 ㆍ각도 ㆍ「65676geometry - angle",
                "13459! 각보다 60도 큰 각은 몇 도입니까?",
                "초등 4학년 ㆍ각도 reserve 8601066ㆍ20812",
                "134도인 각보다 60도 큰 각은 몇 도입니까?",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw)[0], "answer=194")

    def test_reserve_angle_keeps_six_digit_base_suffix_and_ignores_hyphen_fragment(self) -> None:
        self.assertEqual(
            _merge_expression_candidates("130591 각보다 25S 큰 각은 몇 도입니까.")[0],
            "answer=155",
        )
        raw = "\n".join(
            [
                ". AS 4학년 ㆍ각도 reserve geometry ㆍ angle .",
                "545-91 각보다 12도 큰 각은 몇 도입니까?",
                "초등 4학년 - Z2t& - reserve geometry - angle",
                "54도인 각보다 125 큰 각은 몇 도입니까?",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw)[0], "answer=66")

    def test_reserve_angle_reads_eleven_when_delta_reads_as_ne(self) -> None:
        raw = "\n".join(
            [
                "초등 4학년 ㆍ각도 reserve 8601066ㆍ20812",
                "128도인 각보다 NE 큰 각은 몇 도입니까?",
                ". AS 4학년 ㆍ각도 reserve geometry ㆍ angle .",
                "128도인 각보다 11도 22S 몇 도입니까?",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw)[0], "answer=139")

    def test_reserve_angle_reads_eleven_when_delta_reads_as_ng(self) -> None:
        raw = "\n".join(
            [
                "초등 4학년 ㆍ각도 reserve 8601066ㆍ20812",
                "146도인 각보다 NG 큰 각은 몇 도입니까?",
                ". AS 4학년 ㆍ각도 reserve geometry ㆍ angle .",
                "14629! 각보다 NG 22S 몇 도입니까?",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw)[0], "answer=157")

    def test_reserve_gcd_prefers_repaired_operands_over_short_false_match(self) -> None:
        self.assertEqual(
            _merge_expression_candidates("A12) 562] 최대공약수를 구하시오.\n412) 562| 최대공약수를 구하시오.")[0],
            "answer=1",
        )

    def test_reserve_max_value_splits_joined_leading_one_digit_values(self) -> None:
        self.assertEqual(
            _merge_expression_candidates("띠그래프에 나타난 항목 중 가장 큰 값을 고르시오.\n75, 52, 11")[0],
            "answer=52",
        )

    def test_reserve_average_prefers_row_next_to_prompt_over_noisy_later_row(self) -> None:
        raw = "\n".join(
            [
                "초등 5학년 - Wat - reserve table ㆍ2462「2862",
                "다음 다섯 수의 평균을 구하시오.",
                "85, 82, 42, 75, 90",
                "： AS 5학년 - Wat - reserve table - average ：",
                "85, 32, 42, 75, 90",
            ]
        )
        problem = ProblemSchema(
            normalized_problem_text="다음 다섯 수의 평균을 구하시오.",
            expressions=_merge_expression_candidates(raw),
            source_text_candidates=[raw],
            math_topic="arithmetic",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "74.8")

    def test_reserve_average_repairs_forty_read_as_ao(self) -> None:
        raw = "\n".join(
            [
                "초등 5학년 - Wat - reserve table ㆍ2462「2862",
                "다음 다섯 수의 평균을 구하시오.",
                "AO, 67, 72, 46, 56",
                "AS 5학년 - Wat - reserve table - average",
                "40, 6/, 72, 46, 56",
            ]
        )
        problem = ProblemSchema(
            normalized_problem_text="다음 다섯 수의 평균을 구하시오.",
            expressions=_merge_expression_candidates(raw),
            source_text_candidates=[raw],
            math_topic="arithmetic",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "56.2")

    def test_reserve_average_repairs_glued_trailing_one(self) -> None:
        raw = "\n".join(
            [
                "초등 5학년 - Wat - reserve table ㆍ2462「2862",
                "다음 다섯 수의 평균을 구하시오.",
                "47, 42, 411 54, 50",
                "AS 5학년 - Wat - reserve table - average",
                "4/, 42, 41, 54, 50",
            ]
        )
        problem = ProblemSchema(
            normalized_problem_text="다음 다섯 수의 평균을 구하시오.",
            expressions=_merge_expression_candidates(raw),
            source_text_candidates=[raw],
            math_topic="arithmetic",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "46.8")

    def test_reserve_sum_graph_repairs_slash_and_glued_numbers(self) -> None:
        self.assertEqual(
            _merge_expression_candidates("막대그래프에 나타난 수량의 합을 구하시오.\n86, 5/7 32, 27 89")[0],
            "answer=291",
        )

    def test_reserve_sum_graph_prefers_clean_high_value_row_over_noisy_low_row(self) -> None:
        raw = "\n".join(
            [
                "초등 Ast - YOM eyo) 막대그래프 ㆍ『6ㅇ56146table - statistics",
                "막대그래프에 나타난 수량의 합을 구하시오.",
                "85, 80, 87, 68, 58",
                "초등 AStlal - HOM 7eY TO) Otc Tez - reserve table - statistics",
                "85, 30, 87 68, 58",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw, school_level="elementary")[0], "answer=378")

    def test_reserve_sum_graph_prefers_first_pass_when_later_pass_changes_one_value(self) -> None:
        raw = "\n".join(
            [
                "초등 Ast - YOM eyo) 막대그래프 ㆍ『6ㅇ56146table - statistics",
                "막대그래프에 나타난 수량의 합을 구하시오.",
                "88, 41, 55, 89 36",
                "초등 AStlal - HOM 7eY TO) Otc Tez - reserve table - statistics",
                "88, 41, 55, 39, 36",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw, school_level="elementary")[0], "answer=309")

    def test_reserve_average_reads_forty_one_when_ocr_returns_al(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="다음 다섯 수의 평균을 구하시오.",
            expressions=["(246+286+77+81+76+42+77+81+76+42)/10"],
            source_text_candidates=[
                "초등 5학년 - Wat - reserve table ㆍ2462「2862\n"
                "다음 다섯 수의 평균을 구하시오.\n"
                "77, Al, 81, 76, 42\n"
                "： AS 5학년 - Wat - reserve table - average ：\n"
                "7/ Al, 81, 76, 42"
            ],
            math_topic="statistics",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "63.4")
        self.assertEqual(solved.solver_name, "average_table_solver")

    def test_statistics_sum_solver_prefers_sum_expression_over_single_answer_noise(self) -> None:
        raw = "\n".join(
            [
                "초등 Ast - YOM eyo) 막대그래프 ㆍ『6ㅇ56146table - statistics",
                "막대그래프에 나타난 수량의 합을 구하시오.",
                "15, 70, 56, 68, 86",
                "초등 AStlal - HOM 7eY TO) Otc Tez - reserve table - statistics",
            ]
        )
        problem = ProblemSchema(
            normalized_problem_text="막대그래프에 나타난 수량의 합을 구하시오.",
            expressions=["answer=82", "15+70+56+68+86"],
            source_text_candidates=[raw],
            math_topic="statistics",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.solver_name, "statistics_sum_solver")
        self.assertEqual(solved.computed_answer, "295")

    def test_statistics_sum_solver_uses_answer_when_sum_expression_drops_tens_digit(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="막대그래프에 나타난 수량의 합을 구하시오.",
            expressions=["answer=288", "7+66+52+87+46"],
            source_text_candidates=[
                "막대그래프에 나타난 수량의 합을 구하시오.\n3/7 66, 52, 87 46\n37, 66, 52, 87, 46"
            ],
            math_topic="statistics",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "288")

    def test_statistics_sum_solver_repairs_glued_three_digit_value(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="막대그래프에 나타난 수량의 합을 구하시오.",
            expressions=["answer=173", "20+111+43+34+65"],
            source_text_candidates=[
                "막대그래프에 나타난 수량의 합을 구하시오.\n20, 111 43, 34, 65\n20, 11, 43, 34, 65"
            ],
            math_topic="statistics",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "173")

    def test_statistics_sum_solver_repairs_slash_split_first_value(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="막대그래프에 나타난 수량의 합을 구하시오.",
            expressions=["answer=82", "7+51+75+81+35"],
            source_text_candidates=[
                "막대그래프에 나타난 수량의 합을 구하시오.\n8/7 51, 75, 81, 35\n87 51, 75, 81, 35"
            ],
            math_topic="statistics",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "329")

    def test_statistics_sum_solver_repairs_slash_zero_as_seventy_in_comma_list(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="막대그래프에 나타난 수량의 합을 구하시오.",
            expressions=["answer=237", "40+82+39+46", "40,82,39,46,/0"],
            source_text_candidates=["막대그래프에 나타난 수량의 합을 구하시오.\n40, 82, 39, 46, /0"],
            math_topic="statistics",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "277")
        self.assertEqual(solved.solver_name, "statistics_sum_solver")

    def test_count_story_repairs_used_count_with_trailing_ocr_suffix(self) -> None:
        raw = "\n".join(
            [
                "초등 1학년 ㆍ덧셈과 Beal - reserve word - arithmetic",
                "카드가 16개 있습니다. AS 1371S 사용했습니다.",
            ]
        )

        self.assertIn("answer=3", _merge_expression_candidates(raw, school_level="elementary"))

    def test_reserve_max_graph_prefers_comma_separated_row_over_glued_row(self) -> None:
        raw = "\n".join(
            [
                "초등 6학년 ㆍ여러 그래프 reserve table ㆍ statistics",
                "띠그래프에 나타난 항목 중 가장 큰 값을 DEAL.",
                "9,54, 42, 46",
                "AS 6학년 ㆍ여러 그래프 reserve table ㆍ statistics",
                "띠그래프에 나타난 항목 중 가장 큰 값을 고르시오.",
                "954, 42, 46",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw, school_level="elementary")[0], "answer=54")

    def test_reserve_max_graph_repairs_slash_split_row_before_glued_row(self) -> None:
        raw = "\n".join(
            [
                "초등 6학년 ㆍ여러 그래프 reserve table ㆍ statistics",
                "띠그래프에 나타난 항목 중 가장 큰 값을 DEAL.",
                "34, / 17 28",
                "AS 6학년 ㆍ여러 그래프 reserve table ㆍ statistics",
                "띠그래프에 나타난 항목 중 가장 큰 값을 고르시오.",
                "34,717 28",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw, school_level="elementary")[0], "answer=34")

    def test_reserve_max_graph_prefers_single_digit_row_over_repeated_digit_glue(self) -> None:
        raw = "\n".join(
            [
                "AS 6학년 ㆍ여러 그래프 reserve table ㆍ statistics",
                "띠그래프에 나타난 항목 중 가장 큰 값을 고르시오.",
                "16, 55 16, 44",
                "초등 6학년 ㆍ여러 그래프 reserve table ㆍ statistics",
                "띠그래프에 나타난 항목 중 가장 큰 값을 DEAL.",
                "16, 5 16, 44",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw, school_level="elementary")[0], "answer=44")

    def test_reserve_sum_graph_reads_final_zero_when_ocr_returns_letter_o(self) -> None:
        raw = "\n".join(
            [
                "막대그래프에 나타난 수량의 합을 구하시오.",
                "71, 67, 49, 65, 70",
                "초등 AStlal - HOM 7eY TO) Otc Tez - reserve table - statistics",
                "71, 67, 49, 65, 7O",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw, school_level="elementary")[0], "answer=322")

    def test_direct_numeric_solver_prefers_clean_expression_near_prompt(self) -> None:
        raw = "\n".join(
            [
                "| AS 2학년ㆍ세 자리 + - reserve expression - arithmet",
                "9/0 + 36-55",
                "초등 2학년ㆍ세 자리 + - reserve expression ㆍ arithmet",
                "다음 식의 값을 구하시오.",
                "570 + 36 - 55",
            ]
        )
        problem = ProblemSchema(
            normalized_problem_text="다음 식의 값을 구하시오.",
            expressions=_merge_expression_candidates(raw),
            source_text_candidates=[raw],
            math_topic="arithmetic",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "551")

    def test_direct_numeric_solver_prefers_prompt_line_over_later_noisy_expression(self) -> None:
        raw = "\n".join(
            [
                "초등 2학년ㆍ세 자리 + - reserve expression ㆍ arithmet",
                "다음 식의 값을 구하시오.",
                "537 + 62 - 82",
                "| AS 2학년ㆍ세 자리 + - reserve expression - arithmet",
                "=) © D",
                "937 + 62 - 82",
            ]
        )
        problem = ProblemSchema(
            normalized_problem_text="다음 식의 값을 구하시오.",
            expressions=_merge_expression_candidates(raw),
            source_text_candidates=[raw],
            math_topic="arithmetic",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "517")

    def test_direct_numeric_solver_prefers_corrected_s_pass_over_oe_pass(self) -> None:
        raw = "\n".join(
            [
                "| AS 2학년ㆍ세 자리 + - reserve expression - arithmet",
                "Oe =",
                "다음 식의 값을 구하시오.",
                "921 + 177 - 63",
                "초등 2학년ㆍ세 자리 + - reserve expression ㆍ arithmet",
                "S =",
                "521 + 177 - 63",
            ]
        )
        problem = ProblemSchema(
            normalized_problem_text="다음 식의 값을 구하시오.",
            expressions=_merge_expression_candidates(raw),
            source_text_candidates=[raw],
            math_topic="arithmetic",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "635")

    def test_direct_numeric_solver_prefers_elementary_pass_over_oe_pass(self) -> None:
        raw = "\n".join(
            [
                "AS 2학년ㆍ세 자리 + - reserve expression - arithmet",
                "Oe =",
                "다음 식의 값을 구하시오.",
                "990 + 43 - 42",
                "초등 2학년ㆍ세 자리 + - reserve expression ㆍ arithmet",
                "590 + 43 - 42",
            ]
        )
        problem = ProblemSchema(
            normalized_problem_text="다음 식의 값을 구하시오.",
            expressions=_merge_expression_candidates(raw),
            source_text_candidates=[raw],
            math_topic="arithmetic",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "591")

    def test_direct_numeric_solver_prefers_repaired_elementary_pass_over_noise_pass(self) -> None:
        raw = "\n".join(
            [
                "AS 2학년ㆍ세 자리 + - reserve expression - arithmet",
                "© 2 71s",
                "다음 식의 값을 구하시오.",
                "951 + 122 - 27",
                "초등 2학년ㆍ세 자리 + - reserve expression ㆍ arithmet",
                "(2) =",
                "551+ㅜ122 - 27",
            ]
        )
        problem = ProblemSchema(
            normalized_problem_text="다음 식의 값을 구하시오.",
            expressions=_merge_expression_candidates(raw),
            source_text_candidates=[raw],
            math_topic="arithmetic",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "646")

    def test_gcd_solver_repairs_trailing_parenthesis_noise(self) -> None:
        self.assertEqual(
            _merge_expression_candidates("4892) 542| 최대공약수를 구하시오.")[0],
            "answer=6",
        )
        self.assertEqual(
            _merge_expression_candidates("782) 35의 SHS AES 구하시오.")[0],
            "answer=1",
        )
        self.assertEqual(
            _merge_expression_candidates("402) 132] 최대공약수를 구하시오.")[0],
            "answer=1",
        )
        self.assertEqual(
            _merge_expression_candidates("122) 122] 최대공약수를 구하시오.")[0],
            "answer=12",
        )

    def test_statistics_max_repairs_glued_and_missing_comma_values(self) -> None:
        self.assertEqual(
            _merge_expression_candidates("띠그래프에 나타난 항목 중 가장 큰 값을 고르시오.\n29, 5, / 28")[0],
            "answer=29",
        )
        self.assertEqual(
            _merge_expression_candidates("띠그래프에 나타난 항목 중 가장 큰 값을 고르시오.\n111 38, 27 28")[0],
            "answer=38",
        )
        self.assertEqual(
            _merge_expression_candidates("띠그래프에 나타난 항목 중 가장 큰 값을 DEA.\n7,15, 33, 8")[0],
            "answer=33",
        )
        self.assertEqual(
            _merge_expression_candidates("띠그래프에 나타난 항목 중 가장 큰 값을 DEA.\n27/8944")[0],
            "answer=44",
        )

    def test_statistics_sum_prefers_clean_row_over_slash_noisy_row(self) -> None:
        raw = "\n".join(
            [
                "막대그래프에 나타난 수량의 합을 구하시오.",
                "7/69, 144 63, 20",
                "77, 69 14, 63, 20",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw)[0], "answer=243")

    def test_statistics_sum_prefers_five_value_row_over_split_noisy_row(self) -> None:
        raw = "\n".join(
            [
                "막대그래프에 나타난 수량의 합을 구하시오.",
                "63, 34, 59, 57, 56",
                "63, 34, 599 57 56",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw)[0], "answer=269")

    def test_three_digit_arithmetic_repairs_slash_inside_hundreds_number(self) -> None:
        raw = "\n".join(
            [
                "초등 2학년ㆍ세 자리 + - reserve expression ㆍ arithmet",
                "다음 식의 값을 구하시오.",
                "7/7 + 86-11",
            ]
        )
        problem = ProblemSchema(
            normalized_problem_text="다음 식의 값을 구하시오.",
            expressions=_merge_expression_candidates(raw),
            source_text_candidates=[raw],
            math_topic="arithmetic",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "852")

    def test_three_digit_arithmetic_prefers_repaired_candidate_over_short_candidate(self) -> None:
        problem = ProblemSchema(
            normalized_problem_text="다음 식의 값을 구하시오.",
            expressions=["777+86-11", "7+86-11"],
            source_text_candidates=["초등 2학년ㆍ세 자리 + - reserve expression\n다음 식의 값을 구하시오.\n7/7 + 86-11"],
            math_topic="fraction_ratio",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "852")

    def test_three_digit_arithmetic_penalizes_as_header_ocr_pass(self) -> None:
        raw = "\n".join(
            [
                "| AS 2학년ㆍ세 자리 + - reserve expression - arithmet",
                "© 2 71s",
                "다음 식의 값을 구하시오.",
                "961 + 133 - 25",
                "초등 2학년ㆍ세 자리 + - reserve expression ㆍ arithmet",
                "561 + 133 - 25",
            ]
        )
        problem = ProblemSchema(
            normalized_problem_text="다음 식의 값을 구하시오.",
            expressions=_merge_expression_candidates(raw),
            source_text_candidates=[raw],
            math_topic="arithmetic",
        )

        solved = run_solve_pipeline(structured_problem=problem)["solve_result"]

        self.assertEqual(solved.computed_answer, "669")

    def test_count_story_prefers_two_digit_used_count_when_single_digit_pass_conflicts(self) -> None:
        raw = "\n".join(
            [
                "구슬가 14개 있습니다. 그중 1개를 사용했습니다.",
                "구슬가 1474 있습니다. AS 11개를 사용했습니다.",
            ]
        )

        self.assertEqual(_merge_expression_candidates(raw)[0], "answer=3")


if __name__ == "__main__":
    unittest.main()
