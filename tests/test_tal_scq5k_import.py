from __future__ import annotations

import unittest

from scripts.import_tal_scq5k_problem_bank import (
    build_record,
    flatten_choice_items,
    infer_subject,
    normalize_answer,
)


class TALSCQ5KImportTests(unittest.TestCase):
    def test_flattens_nested_choice_items(self) -> None:
        choices = flatten_choice_items(
            [
                [{"aoVal": "A", "content": "$$3$$ "}],
                [{"aoVal": "B", "content": "$$4$$ "}],
            ]
        )

        self.assertEqual(choices[0], {"label": "A", "content": "3"})
        self.assertEqual(choices[1], {"label": "B", "content": "4"})

    def test_infers_subject_from_knowledge_route(self) -> None:
        subject, slug = infer_subject(["Knowledge Point->Number Theory Modules->Divisibility Rules"], "")

        self.assertEqual(subject, "Number Theory")
        self.assertEqual(slug, "number_theory")

    def test_builds_problem_bank_record_with_answer_content(self) -> None:
        row = {
            "qid": "1",
            "queId": "abc",
            "difficulty": "1",
            "problem": "If $$5A2A$$ is divisible by $20$, what is $$A$$?",
            "answer_option_list": [
                [{"aoVal": "A", "content": "$$0$$ "}],
                [{"aoVal": "B", "content": "$$1$$ "}],
            ],
            "knowledge_point_routes": [
                "Overseas Competition->Knowledge Point->Number Theory Modules->Division without Remainders"
            ],
            "answer_analysis": ["The last digit must be 0."],
            "answer_value": "A",
        }

        record = build_record(row, split="en_train", index=0, source_url="local", generated_at="2026-04-25T00:00:00+00:00")

        self.assertEqual(record["schema_version"], "problem_bank_record.v1")
        self.assertEqual(record["id"], "tal_scq5k:en_train:number_theory:level_2:00000")
        self.assertEqual(record["answer"]["final_normalized"], "0")
        self.assertIn("A", record["answer"]["candidates"])
        self.assertEqual(record["taxonomy"]["subject_slug"], "number_theory")
        self.assertTrue(record["structure"]["has_choices"])
        self.assertFalse(record["metadata"]["quality"]["needs_review"])

    def test_normalizes_math_choice_markup(self) -> None:
        self.assertEqual(normalize_answer("$$14$$ "), "14")


if __name__ == "__main__":
    unittest.main()
