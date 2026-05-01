from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.run_elementary_50k_validation_queue import (
    actual_capture_records,
    read_jsonl,
    reconcile_status_jsonl,
    run_validation_queue,
    source_expression_matches_expected,
    template_problem_spec,
    write_jsonl,
)


def template_payload(root: Path) -> tuple[dict[str, object], Path]:
    source = root / "template.json"
    payload = {
        "record": {
            "problem_id": "t1",
            "band": "초등",
            "grade": 1,
            "difficulty": "easy",
            "layout": "expression",
            "area": "수와 연산",
            "unit": "덧셈",
            "topic": "arithmetic",
            "folder": "1학년",
            "file_name": "t1.png",
            "title": "초등 1학년",
            "lines": ["다음 식의 값을 구하시오.", "2 + 3"],
            "expected_answer": "5",
            "expected_expression": "2+3",
            "table": [],
            "diagram": {},
        }
    }
    source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    item = {
        "collection_id": "template_variant_00001",
        "track": "template_variant",
        "collected_file_path": str(source),
        "answer_text": "5",
        "grade": "1학년",
    }
    return item, source


class Elementary50kValidationQueueTests(unittest.TestCase):
    def test_template_problem_spec_loads_collected_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            item, _ = template_payload(Path(tmpdir))

            spec = template_problem_spec(item)

        self.assertEqual(spec.problem_id, "t1")
        self.assertEqual(spec.grade, 1)
        self.assertEqual(spec.expected_answer, "5")
        self.assertEqual(spec.lines[-1], "2 + 3")

    def test_template_queue_promotes_passed_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            item, _ = template_payload(root)
            queue = root / "template_queue.jsonl"
            report = root / "report.json"
            verified = root / "verified"
            rejected = root / "rejected"
            rendered = root / "rendered"
            image = root / "rendered.png"
            image.write_bytes(b"png")
            write_jsonl(queue, [item])

            with patch("scripts.run_elementary_50k_validation_queue.VERIFIED_DIR", verified), patch(
                "scripts.run_elementary_50k_validation_queue.REJECTED_DIR",
                rejected,
            ), patch("scripts.run_elementary_50k_validation_queue.render_problem", return_value=image), patch(
                "scripts.run_elementary_50k_validation_queue.run_single_validation",
                return_value={
                    "status": "passed",
                    "computed_answer": "5",
                    "matched_choice": "",
                    "solver_name": "test_solver",
                    "validation_status": "passed",
                },
            ):
                payload = run_validation_queue(
                    track="template",
                    offset=0,
                    limit=1,
                    resume=False,
                    clean_output=False,
                    force_render=False,
                    max_cards_per_actual=0,
                    report_path=report,
                    template_queue_path=queue,
                    render_root=rendered,
                )

            self.assertEqual(payload["summary"]["verified"], 1)
            self.assertEqual(len(read_jsonl(verified / "template_render_verified.jsonl")), 1)

    def test_template_queue_can_verify_from_source_expression_after_ocr_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            item, _ = template_payload(root)
            queue = root / "template_queue.jsonl"
            report = root / "report.json"
            verified = root / "verified"
            rejected = root / "rejected"
            image = root / "rendered.png"
            image.write_bytes(b"png")
            write_jsonl(queue, [item])

            with patch("scripts.run_elementary_50k_validation_queue.VERIFIED_DIR", verified), patch(
                "scripts.run_elementary_50k_validation_queue.REJECTED_DIR",
                rejected,
            ), patch("scripts.run_elementary_50k_validation_queue.render_problem", return_value=image), patch(
                "scripts.run_elementary_50k_validation_queue.run_single_validation",
                return_value={
                    "status": "failed",
                    "computed_answer": "",
                    "matched_choice": "",
                    "solver_name": "arithmetic_solver",
                    "validation_status": "failed",
                },
            ):
                payload = run_validation_queue(
                    track="template",
                    offset=0,
                    limit=1,
                    resume=False,
                    clean_output=False,
                    force_render=False,
                    max_cards_per_actual=0,
                    report_path=report,
                    template_queue_path=queue,
                    render_root=root / "rendered",
                )

            promoted = read_jsonl(verified / "template_render_verified.jsonl")[0]
            self.assertEqual(payload["summary"]["verified"], 1)
            self.assertEqual(promoted["verification_mode"], "source_expression_solver_after_ocr_review")
            self.assertIn("ocr_pipeline_needs_followup", promoted["warnings"])

    def test_source_expression_verifies_fraction_and_decimal_answers(self) -> None:
        self.assertTrue(source_expression_matches_expected({"expected_expression": "(44+23+29+13)/4", "expected_answer": "109/4"}))
        self.assertTrue(source_expression_matches_expected({"expected_expression": "2*3.14*4", "expected_answer": "25.12"}))
        self.assertFalse(source_expression_matches_expected({"expected_expression": "2*3", "expected_answer": "7"}))

    def test_actual_queue_promotes_unsplit_capture_when_pipeline_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            image = root / "source.png"
            image.write_bytes(b"png")
            queue = root / "actual_queue.jsonl"
            report = root / "report.json"
            verified = root / "verified"
            rejected = root / "rejected"
            write_jsonl(
                queue,
                [
                    {
                        "collection_id": "actual_source_00001",
                        "track": "actual_pdf_capture",
                        "collected_file_path": str(image),
                        "source_path": str(image),
                        "grade": "1학년",
                    }
                ],
            )

            with patch("scripts.run_elementary_50k_validation_queue.VERIFIED_DIR", verified), patch(
                "scripts.run_elementary_50k_validation_queue.REJECTED_DIR",
                rejected,
            ), patch("scripts.run_elementary_50k_validation_queue.save_problem_card_images", return_value=[]), patch(
                "scripts.run_elementary_50k_validation_queue.validate_capture",
                return_value={
                    "status": "ok",
                    "elapsed_seconds": 0.01,
                    "issues": [],
                    "display_topic": "덧셈",
                    "problem_text": "2+3",
                    "computed_answer": "5",
                    "matched_choice": "",
                    "solver_name": "test_solver",
                    "validation_status": "passed",
                },
            ):
                payload = run_validation_queue(
                    track="actual",
                    offset=0,
                    limit=1,
                    resume=False,
                    clean_output=False,
                    force_render=False,
                    max_cards_per_actual=0,
                    report_path=report,
                    actual_queue_path=queue,
                    segment_root=root / "segments",
                )

            self.assertEqual(payload["summary"]["verified"], 1)
            self.assertEqual(len(read_jsonl(verified / "actual_capture_verified.jsonl")), 1)

    def test_actual_pdf_skips_missing_edite_manifest_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            pdf = root / "source.pdf"
            missing = root / "missing.png"
            existing = root / "existing.png"
            pdf.write_bytes(b"pdf")
            existing.write_bytes(b"png")
            item = {
                "collection_id": "actual_source_pdf",
                "track": "actual_pdf_capture",
                "collected_file_path": str(pdf),
                "source_path": str(pdf),
            }

            with patch(
                "scripts.run_elementary_50k_validation_queue.pdf_edite_index",
                return_value={
                    str(pdf.resolve()): [
                        {"image_path": str(missing), "source_page": 1, "pdf_path": str(pdf)},
                        {"image_path": str(existing), "source_page": 2, "pdf_path": str(pdf)},
                    ]
                },
            ), patch(
                "scripts.run_elementary_50k_validation_queue.save_problem_card_images",
                return_value=[],
            ):
                records = actual_capture_records(item, segment_root=root / "segments")

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["parent_relative_path"], str(existing))

    def test_reconcile_moves_revalidated_item_out_of_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            verified_path = root / "verified.jsonl"
            review_path = root / "review.jsonl"
            write_jsonl(review_path, [{"input_collection_id": "t1", "status": "review"}])

            reconcile_status_jsonl(
                verified_path=verified_path,
                review_path=review_path,
                verified_records=[{"input_collection_id": "t1", "status": "verified"}],
                review_records=[],
                key="input_collection_id",
            )

            self.assertEqual(len(read_jsonl(verified_path)), 1)
            self.assertEqual(read_jsonl(review_path), [])


if __name__ == "__main__":
    unittest.main()
