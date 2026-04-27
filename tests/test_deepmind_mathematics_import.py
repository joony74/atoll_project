from __future__ import annotations

import unittest

from scripts.import_deepmind_mathematics_problem_bank import build_record, infer_answer_type, subject_for_module


class DeepMindMathematicsImportTests(unittest.TestCase):
    def test_maps_module_domain_to_subject(self) -> None:
        subject, slug, domain = subject_for_module("algebra__linear_1d")

        self.assertEqual(subject, "Algebra")
        self.assertEqual(slug, "algebra")
        self.assertEqual(domain, "algebra")

    def test_infers_generated_answer_type(self) -> None:
        self.assertEqual(infer_answer_type("42"), "integer")
        self.assertEqual(infer_answer_type("True"), "boolean")
        self.assertEqual(infer_answer_type("x + 2"), "expression")

    def test_builds_problem_bank_record(self) -> None:
        record = build_record(
            question="Solve x + 2 = 5.",
            answer="3",
            regime="train_easy",
            module_name="algebra__linear_1d",
            index=0,
            generated_at="2026-04-25T00:00:00+00:00",
        )

        self.assertEqual(record["schema_version"], "problem_bank_record.v1")
        self.assertEqual(record["id"], "deepmind_mathematics:train_easy:algebra_linear_1d:00000")
        self.assertEqual(record["answer"]["final_normalized"], "3")
        self.assertEqual(record["taxonomy"]["level_number"], 1)
        self.assertFalse(record["metadata"]["quality"]["needs_review"])


if __name__ == "__main__":
    unittest.main()
