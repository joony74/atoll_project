from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.learning_engine.service import clear_caches as clear_learning_engine_caches
from app.learning_engine.service import format_learning_engine_status
from app.problem_bank.generator import clear_caches as clear_generator_caches
from app.problem_bank.generator import generate_problem_record, load_generation_profile
from app.problem_bank.repository import record_to_analysis, record_to_document
from app.problem_bank.chat_commands import parse_problem_bank_command


class ProblemGeneratorTests(unittest.TestCase):
    def _write_profile_fixture(self, root: Path) -> tuple[Path, Path]:
        base_profile = root / "coco_problem_generation_profile.json"
        base_profile.write_text(
            json.dumps(
                {
                    "schema_version": "coco_problem_generation_profile.v1",
                    "source_banks": [],
                    "counts": {"total_records": 12},
                    "domains": {},
                    "generation": {
                        "default_subject_slug": "arithmetic_word_problem",
                        "default_level_number": 2,
                        "strategy": "test_strategy",
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        elementary_profile = root / "coco_elementary_50k_learning_profile.json"
        elementary_profile.write_text(
            json.dumps(
                {
                    "schema_version": "coco_elementary_50k_learning_profile.v1",
                    "generated_at": "2026-04-28T23:07:06+00:00",
                    "counts": {
                        "total_records": 50000,
                        "learning_ready_or_queued": 50000,
                        "by_status": {
                            "learned_ready": 15001,
                            "validation_queued": 34999,
                        },
                    },
                    "routing": {"engine_partition": "elementary"},
                    "quality_gates": {"duplicate_gate_passed": True},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return base_profile, elementary_profile

    def test_generation_profile_loads(self) -> None:
        profile = load_generation_profile()

        self.assertEqual(profile["schema_version"], "coco_problem_generation_profile.v1")
        self.assertIn("generation", profile)

    def test_generation_profile_attaches_elementary_50k_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_profile, elementary_profile = self._write_profile_fixture(Path(tmpdir))
            clear_generator_caches()
            with patch("app.problem_bank.generator.PROFILE_PATH", base_profile), patch(
                "app.problem_bank.generator.ELEMENTARY_50K_PROFILE_PATH",
                elementary_profile,
            ):
                profile = load_generation_profile()

            self.assertIn("elementary_50k", profile)
            self.assertEqual(profile["elementary_50k"]["counts"]["total_records"], 50000)
            self.assertEqual(profile["counts"]["elementary_50k_learning_ready_or_queued"], 50000)
            clear_generator_caches()

    def test_learning_engine_status_mentions_elementary_50k_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_profile, elementary_profile = self._write_profile_fixture(Path(tmpdir))
            clear_learning_engine_caches()
            with patch("app.problem_bank.generator.PROFILE_PATH", base_profile), patch(
                "app.problem_bank.generator.ELEMENTARY_50K_PROFILE_PATH",
                elementary_profile,
            ):
                status = format_learning_engine_status()

            self.assertIn("초등 50k 학습 큐: 50,000개", status)
            self.assertIn("초등 50k 즉시 학습 완료: 15,001개", status)
            self.assertIn("초등 50k 검증 대기: 34,999개", status)
            clear_learning_engine_caches()

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
