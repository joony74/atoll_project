from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.engines.parser.auto_normalizer import (
    infer_auto_expression_candidates,
    infer_auto_normalization_candidates,
    is_fractional_power_ocr_statement,
    observation_path_for_school_level,
    record_normalization_observation,
)
from app.models.problem_schema import ProblemSchema
from app.models.solve_result import SolveResult


class AutoNormalizerTests(unittest.TestCase):
    def test_infers_stacked_fractional_power_candidate(self) -> None:
        raw = "3 2014 6 B 1\n3 1\n4? x27? 의 값은?\n① 12 ② 15 ③ 18 ④ 21 ⑤ 24"

        candidates = infer_auto_normalization_candidates(raw)

        self.assertEqual(candidates[0]["rule_id"], "stacked_fractional_power")
        self.assertEqual(candidates[0]["expression"], "4^(3/2)*27^(1/3)")
        self.assertEqual(infer_auto_expression_candidates(raw)[0], "4^(3/2)*27^(1/3)")

    def test_does_not_use_exam_metadata_as_stacked_power_numerator(self) -> None:
        raw = "3 2014 6 B 1\n3 1\n4? x27? 의 값은?"

        expressions = infer_auto_expression_candidates(raw)

        self.assertNotIn("4^(3/2)*27^(6/3)", expressions)
        self.assertEqual(expressions[0], "4^(3/2)*27^(1/3)")

    def test_recognizes_fractional_power_ocr_statement(self) -> None:
        self.assertTrue(is_fractional_power_ocr_statement("4? x27? 의 값은?"))
        self.assertFalse(is_fractional_power_ocr_statement("함수 y=f(x)의 그래프가 그림과 같다"))

    def test_infers_log_sequence_product_candidate_from_ocr_choices(self) -> None:
        raw = "\n".join(
            [
                "5 2014 9 ㅅ 8",
                "모든 항이 양수인 수열 (0,) 이 a, =2 이고,",
                "logy a, 4, =1+log,a, (0 주 1)",
                "을 만족시킨다. a, Xa,Xa,X - Xa, =2 일 때 상수 *의 값은?",
                "® 36 ® 40 @ 44 @ 48 © 52",
            ]
        )

        candidates = infer_auto_normalization_candidates(raw)

        self.assertEqual(candidates[0]["rule_id"], "sequence_log_product")
        self.assertEqual(candidates[0]["expression"], "sequence_log_product(base=2,start=2,increment=1,count=8)")

    def test_records_upload_observation_with_rule_summary(self) -> None:
        problem = ProblemSchema(
            source_text_candidates=["3 1\n4? x27? 의 값은?"],
            normalized_problem_text="4^(3/2)*27^(1/3) 의 값은?",
            expressions=["4^(3/2)*27^(1/3)"],
            math_topic="radical_power",
            metadata={"content_hash": "case-hash"},
        )
        solved = SolveResult(
            solver_name="safe_eval_solver",
            computed_answer="24",
            validation_status="verified",
            confidence=0.86,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "observations.json"

            record_normalization_observation(
                image_path="/tmp/problem3.png",
                structured_problem=problem,
                solve_result=solved,
                debug_payload={"upload": {}},
                storage_path=output_path,
            )

            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["summary"]["case_count"], 1)
        self.assertEqual(payload["summary"]["verified_count"], 1)
        self.assertEqual(payload["summary"]["rule_counts"]["stacked_fractional_power"]["verified"], 1)
        self.assertEqual(payload["cases"][0]["computed_answer"], "24")

    def test_records_school_profile_observation_metadata(self) -> None:
        problem = ProblemSchema(
            source_text_candidates=["ㅁ 안에 알맞은 수를 써넣으세요."],
            normalized_problem_text="□보다 1 큰 수는 8입니다. □ 안에 알맞은 수를 쓰세요.",
            expressions=["answer=7"],
            math_topic="arithmetic",
            metadata={
                "content_hash": "elementary-case",
                "school_level": "elementary",
                "school_profile": "elementary_visual",
                "grade": 1,
                "semester": 1,
                "unit": "1단원 9까지의수",
                "visual_template": {"rule_id": "grade1_numbers_to_9_one_less_from_sentence", "confidence": 0.9},
            },
        )
        solved = SolveResult(
            solver_name="visual_template_solver",
            computed_answer="7",
            validation_status="verified",
            confidence=0.9,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "observations.json"

            record_normalization_observation(
                image_path="/tmp/초1-1_1단원_9까지의수_1회_p02_문항03.png",
                structured_problem=problem,
                solve_result=solved,
                debug_payload={"upload": {}},
                storage_path=output_path,
            )

            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["cases"][0]["school_level"], "elementary")
        self.assertEqual(payload["cases"][0]["school_profile"], "elementary_visual")
        self.assertEqual(payload["cases"][0]["normalization_quality"], "template_verified")
        self.assertEqual(payload["summary"]["quality_counts"]["template_verified"], 1)
        self.assertIn("/learning/elementary/", str(observation_path_for_school_level("초등")))


if __name__ == "__main__":
    unittest.main()
