from __future__ import annotations

import unittest

from app.problem_bank.generator import generate_problem_record, load_generation_profile
from app.problem_bank.repository import record_to_analysis, record_to_document
from app.problem_bank.chat_commands import parse_problem_bank_command


class ProblemGeneratorTests(unittest.TestCase):
    def test_generation_profile_loads(self) -> None:
        profile = load_generation_profile()

        self.assertEqual(profile["schema_version"], "coco_problem_generation_profile.v1")
        self.assertIn("generation", profile)

    def test_generates_arithmetic_record(self) -> None:
        record = generate_problem_record(subject_slug="arithmetic_word_problem", level_number=3, seed=1234)

        self.assertEqual(record["schema_version"], "problem_bank_record.v1")
        self.assertEqual(record["source"]["name"], "Coco Generated Problem")
        self.assertEqual(record["taxonomy"]["subject_slug"], "arithmetic_word_problem")
        self.assertEqual(record["taxonomy"]["level_number"], 3)
        self.assertTrue(record["answer"]["final_normalized"])
        self.assertFalse(record["metadata"]["quality"]["needs_review"])

    def test_generated_record_converts_to_study_document(self) -> None:
        record = generate_problem_record(level_number=2, seed=77)
        analysis = record_to_analysis(record)
        document = record_to_document(record)

        self.assertEqual(analysis["solve_result"]["solver_name"], "problem_bank_solution")
        self.assertTrue(document["doc_id"].startswith("coco_generated__"))

    def test_parses_generate_command(self) -> None:
        command = parse_problem_bank_command("문제은행 출제 초등 문장제 난이도 3")

        self.assertIsNotNone(command)
        self.assertEqual(command.action, "generate")
        self.assertEqual(command.subject_slug, "arithmetic_word_problem")
        self.assertEqual(command.level_number, 3)


if __name__ == "__main__":
    unittest.main()
