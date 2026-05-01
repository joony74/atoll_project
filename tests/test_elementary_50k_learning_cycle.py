from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.run_elementary_50k_learning_cycle import (
    build_profile,
    build_report,
    evaluate_candidate,
    fingerprint_text,
)


def normalized_record(*, grade_band: str = "elementary") -> dict[str, object]:
    return {
        "collection_id": "n1",
        "track": "normalized_json",
        "source_type": "external_problem_bank_record",
        "grade": grade_band,
        "bank_id": "sample",
        "record_id": "sample-1",
        "content": {
            "problem_plain": "민지는 사과 3개와 4개를 더 샀습니다. 모두 몇 개인가요?",
            "solution_plain": "3 + 4 = 7 이므로 정답은 7입니다.",
        },
        "answer": {"final_normalized": "7"},
        "taxonomy": {
            "grade_band": grade_band,
            "subject": "Arithmetic",
            "subject_slug": "arithmetic",
            "level_number": 1,
            "tags": ["addition"],
            "concepts": ["addition"],
        },
        "metadata": {"quality": {"needs_review": False}},
    }


class Elementary50kLearningCycleTests(unittest.TestCase):
    def test_normalized_json_with_answer_solution_is_learning_ready(self) -> None:
        seen: set[str] = set()

        item = evaluate_candidate(normalized_record(), seen)

        self.assertEqual(item["status"], "learned_ready")
        self.assertEqual(item["answer_text"], "7")

    def test_non_elementary_normalized_record_goes_to_review(self) -> None:
        seen: set[str] = set()

        item = evaluate_candidate(normalized_record(grade_band="middle"), seen)

        self.assertEqual(item["status"], "review_queued")
        self.assertIn("non_elementary_grade_band", item["reasons"])

    def test_actual_source_is_capture_validation_queued(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "sample.png"
            image.write_bytes(b"png")
            seen: set[str] = set()

            item = evaluate_candidate(
                {
                    "collection_id": "a1",
                    "track": "actual_pdf_capture",
                    "source_type": "previous_capture_card_image",
                    "grade": "1학년",
                    "collected_file_path": str(image),
                    "suffix": ".png",
                    "sha256": "abc123",
                },
                seen,
            )

        self.assertEqual(item["status"], "validation_queued")
        self.assertIn("previous_capture_card_image_requires_coco_capture_validation", item["reasons"])

    def test_duplicate_problem_text_is_rejected(self) -> None:
        seen: set[str] = set()
        first = evaluate_candidate(normalized_record(), seen)
        duplicate = evaluate_candidate(normalized_record(), seen)

        self.assertEqual(first["status"], "learned_ready")
        self.assertEqual(duplicate["status"], "rejected_duplicate")

    def test_template_fingerprint_includes_structured_values(self) -> None:
        seen: set[str] = set()
        base = {
            "track": "template_variant",
            "source_type": "generated_template_candidate",
            "grade": "1학년",
            "lines": ["아래 표의 자료에서 평균을 구하시오."],
            "answer": "5",
            "expected_expression": "(3+5+7)/3",
            "table": [["값", "3", "5", "7"]],
            "validation": {"verified": False},
        }

        first = evaluate_candidate({"collection_id": "t1", **base}, seen)
        second = evaluate_candidate(
            {
                "collection_id": "t2",
                **base,
                "answer": "6",
                "expected_expression": "(4+6+8)/3",
                "table": [["값", "4", "6", "8"]],
            },
            seen,
        )

        self.assertEqual(first["status"], "validation_queued")
        self.assertEqual(second["status"], "validation_queued")

    def test_fingerprint_keeps_unicode_problem_text(self) -> None:
        first = fingerprint_text("简单随机抽样 每个个体机会相等")
        second = fingerprint_text("2019 年元旦是星期二")

        self.assertNotEqual(first, second)

    def test_report_and_profile_summarize_learning_state(self) -> None:
        evaluated = [
            evaluate_candidate(normalized_record(), set()),
            {
                "collection_id": "t1",
                "track": "template_variant",
                "source_type": "generated_template_candidate",
                "status": "validation_queued",
                "reasons": ["template_requires_render_and_solver_validation"],
                "grade": "1학년",
                "bank_id": None,
                "answer_text": "9",
                "taxonomy": {"subject_slug": "arithmetic", "tags": ["addition"], "concepts": ["addition"]},
            },
        ]
        manifest = {"target": 2, "records": [{}, {}]}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_report(
                evaluated,
                manifest=manifest,
                manifest_path=root / "manifest.json",
                workspace=root,
                profile_path=root / "profile.json",
            )
            profile = build_profile(evaluated, manifest_path=root / "manifest.json", report_path=root / "report.json")

        self.assertTrue(report["quality_gates"]["target_loaded"])
        self.assertEqual(report["summary"]["ready_or_queued_total"], 2)
        self.assertEqual(profile["counts"]["by_track"]["normalized_json"], 1)
        self.assertEqual(profile["counts"]["by_track"]["template_variant"], 1)


if __name__ == "__main__":
    unittest.main()
