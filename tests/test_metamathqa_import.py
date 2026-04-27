from __future__ import annotations

import unittest

from scripts.import_metamathqa_problem_bank import build_record, extract_final_answer, infer_subject


class MetaMathQAImportTests(unittest.TestCase):
    def test_extracts_answer_line_after_boxed_answer(self) -> None:
        final, candidates, method = extract_final_answer(r"Work gives \boxed{\sqrt{5}}.\nThe answer is: \sqrt{5}")

        self.assertEqual(final, r"\sqrt{5}")
        self.assertIn(r"\sqrt{5}", candidates)
        self.assertEqual(method, "answer_line")

    def test_infers_gsm_as_arithmetic_word_problem(self) -> None:
        subject, slug, domain = infer_subject("GSM_Rephrased", "How many apples?", "")

        self.assertEqual(subject, "Grade School Math")
        self.assertEqual(slug, "arithmetic_word_problem")
        self.assertEqual(domain, "grade_school_math")

    def test_builds_problem_bank_record(self) -> None:
        row = {
            "query": "Convert $10101_3$ to a base 10 integer.",
            "response": "$10101_3 = 81 + 9 + 1 = \\boxed{91}$.\nThe answer is: 91",
            "type": "MATH_AnsAug",
            "original_question": "Convert $10101_3$ to a base 10 integer.",
        }

        record = build_record(row, index=3, source_url="local", generated_at="2026-04-25T00:00:00+00:00")

        self.assertEqual(record["schema_version"], "problem_bank_record.v1")
        self.assertEqual(record["answer"]["final_normalized"], "91")
        self.assertEqual(record["source"]["license"], "MIT")
        self.assertIn(record["taxonomy"]["subject_slug"], {"number_theory", "competition_math"})
        self.assertFalse(record["metadata"]["quality"]["needs_review"])


if __name__ == "__main__":
    unittest.main()
