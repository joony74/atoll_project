from __future__ import annotations

import unittest

from scripts.import_gsm8k_problem_bank import (
    build_record,
    extract_final_answer,
    normalize_answer,
    remove_calculation_annotations,
)


class GSM8KImportTests(unittest.TestCase):
    def test_extracts_final_answer_marker(self) -> None:
        self.assertEqual(extract_final_answer("work\n#### 1,234"), "1,234")
        self.assertEqual(normalize_answer("1,234"), "1234")

    def test_removes_calculation_annotations_without_losing_visible_answer(self) -> None:
        answer = "Natalia sold 48/2 = <<48/2=24>>24 clips.\n#### 24"

        self.assertEqual(remove_calculation_annotations(answer).splitlines()[0], "Natalia sold 48/2 = 24 clips.")

    def test_builds_problem_bank_record(self) -> None:
        sample = {
            "question": "Natalia sold clips to 48 friends and half as many in May. How many altogether?",
            "answer": (
                "Natalia sold 48/2 = <<48/2=24>>24 clips in May.\n"
                "Natalia sold 48+24 = <<48+24=72>>72 clips altogether.\n"
                "#### 72"
            ),
        }

        record = build_record(sample, split="train", index=0, source_url="local", generated_at="2026-04-25T00:00:00+00:00")

        self.assertEqual(record["id"], "gsm8k:train:level_2:00000")
        self.assertEqual(record["answer"]["final_normalized"], "72")
        self.assertEqual(record["taxonomy"]["subject_slug"], "arithmetic_word_problem")
        self.assertFalse(record["metadata"]["quality"]["needs_review"])


if __name__ == "__main__":
    unittest.main()
