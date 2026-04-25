from __future__ import annotations

import unittest

from scripts.import_competition_math_problem_bank import (
    build_record,
    extract_boxed_answers,
    infer_answer_type,
    slugify,
)


class ProblemBankImportTests(unittest.TestCase):
    def test_extracts_nested_boxed_answer(self) -> None:
        solution = r"Therefore the answer is \boxed{\frac{3}{5}}."

        self.assertEqual(extract_boxed_answers(solution), [r"\frac{3}{5}"])

    def test_subject_slug_is_stable(self) -> None:
        self.assertEqual(slugify("Counting & Probability"), "counting_probability")

    def test_infers_answer_type(self) -> None:
        self.assertEqual(infer_answer_type("42"), "integer")
        self.assertEqual(infer_answer_type(r"\frac{3}{5}"), "fraction")
        self.assertEqual(infer_answer_type("x=2"), "expression")

    def test_build_record_marks_missing_boxed_answer_for_review(self) -> None:
        record = build_record(
            {
                "problem": "What is 2+2?",
                "solution": "It is 4.",
                "level": "Level 1",
                "type": "Prealgebra",
            },
            index=7,
            source_url="https://example.test/data.parquet",
            generated_at="2026-04-25T00:00:00+00:00",
        )

        self.assertEqual(record["schema_version"], "problem_bank_record.v1")
        self.assertEqual(record["taxonomy"]["subject_slug"], "prealgebra")
        self.assertTrue(record["metadata"]["quality"]["needs_review"])
        self.assertIn("missing_boxed_answer", record["metadata"]["quality"]["review_reasons"])


if __name__ == "__main__":
    unittest.main()
