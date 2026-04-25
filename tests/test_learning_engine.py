from __future__ import annotations

import unittest

from app.learning_engine import (
    format_learning_engine_status,
    generate_learning_problem_record,
    normalize_learning_request,
    recommend_problem_candidates,
)


class LearningEngineTests(unittest.TestCase):
    def test_status_reports_loaded_profile(self) -> None:
        reply = format_learning_engine_status()

        self.assertIn("21,292", reply)
        self.assertIn("초등 문장제", reply)
        self.assertIn("학습엔진", reply)
        self.assertIn("수식 정규화", reply)

    def test_normalizes_school_band_subject_and_level(self) -> None:
        request = normalize_learning_request("문제은행 중등 기하 난이도 3", action="search")

        self.assertEqual(request.school_band, "middle")
        self.assertEqual(request.subject_slug, "geometry")
        self.assertEqual(request.level_number, 3)
        self.assertEqual(request.target_level_number, 3)
        self.assertTrue(request.explicit_subject)
        self.assertTrue(request.explicit_level)

    def test_recommends_candidates_with_learning_metadata(self) -> None:
        request = normalize_learning_request("문제은행 초등 문장제", action="search", limit=3)
        results = recommend_problem_candidates(request)

        self.assertEqual(len(results), 3)
        self.assertTrue(all(item.get("learning_score") is not None for item in results))
        self.assertTrue(all(item.get("learning_request") for item in results))
        self.assertEqual(results[0]["subject_slug"], "arithmetic_word_problem")
        self.assertEqual(results[0]["level_number"], 2)

    def test_generated_record_keeps_learning_request_metadata(self) -> None:
        request = normalize_learning_request(
            "문제은행 출제 초등 문장제 난이도 3",
            action="generate",
            subject_slug="arithmetic_word_problem",
            level_number=3,
        )
        record = generate_learning_problem_record(request, seed=42)
        generation = record["metadata"]["generation"]

        self.assertEqual(record["schema_version"], "problem_bank_record.v1")
        self.assertEqual(record["taxonomy"]["subject_slug"], "arithmetic_word_problem")
        self.assertEqual(generation["learning_request"]["target_level_number"], 3)
        self.assertEqual(generation["generation_subject_slug"], "arithmetic_word_problem")


if __name__ == "__main__":
    unittest.main()
