from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.run_problem_bank_image_validation_loop import (
    answers_match,
    create_parser,
    generate_problem_bank_images,
    selected_records,
)
from scripts.run_coco_app_corpus_validation import classify_issues, is_probably_non_question
from scripts.generate_curriculum_problem_bank import generate_specs


class ProblemBankImageValidationLoopTests(unittest.TestCase):
    def test_answer_matching_accepts_choice_and_fraction_forms(self) -> None:
        self.assertTrue(answers_match("16", "", "④ 16"))
        self.assertTrue(answers_match("1/2", "0.5"))
        self.assertTrue(answers_match("-2, 5", "-2, 5"))
        self.assertFalse(answers_match("-2, 5", "5"))
        self.assertFalse(answers_match("24", "21"))

    def test_parser_defaults_to_safe_single_cycle(self) -> None:
        args = create_parser().parse_args([])

        self.assertFalse(args.loop)
        self.assertEqual(args.max_cycles, 1)
        self.assertFalse(args.app_register)
        self.assertFalse(args.clear_app_generated)

    def test_generates_problem_bank_manifest_under_requested_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "05.문제은행"
            manifest = Path(tmpdir) / "manifest.json"

            records = generate_problem_bank_images(
                output_root=root,
                manifest_path=manifest,
                count_per_grade=1,
                seed=7,
                force=True,
            )

            self.assertEqual(len(records), 12)
            self.assertTrue(manifest.exists())
            self.assertTrue((root / "01.초등" / "1학년").exists())
            self.assertTrue(Path(records[0]["image_path"]).exists())
            self.assertEqual(len(selected_records(records, offset=0, limit=0, band="초등", grade=1, difficulty="")), 1)

    def test_curriculum_generation_includes_visual_layouts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "05.문제은행"
            manifest = Path(tmpdir) / "manifest.json"

            records = generate_problem_bank_images(
                output_root=root,
                manifest_path=manifest,
                count_per_grade=12,
                seed=11,
                force=True,
            )

            layouts = {str(item.get("layout") or "") for item in records}
            self.assertIn("graph", layouts)
            self.assertIn("geometry", layouts)
            self.assertTrue(any(item.get("area") == "도형과 측정" for item in records))

    def test_advanced_topics_do_not_use_generic_table_or_sticker_templates(self) -> None:
        advanced_topics = {
            "calculus_limit",
            "calculus_derivative",
            "calculus_integral",
            "polynomial",
            "logarithm",
            "trigonometry",
            "sequence",
        }

        specs = generate_specs(count_per_grade=20, seed=20260425)
        generic_fragments = ("아래 표의 수량", "스티커")
        bad = [
            spec.problem_id
            for spec in specs
            if spec.band == "고등"
            and spec.topic in advanced_topics
            and any(fragment in " ".join(spec.lines) for fragment in generic_fragments)
        ]

        self.assertEqual(bad, [])

    def test_corpus_validation_separates_answer_key_tiles(self) -> None:
        raw = "4) 6 5) 18-4에 OF 6) 9 7) 15개 8) 준서 9) 8개 14) 6 15) 13-4에 OF"

        self.assertTrue(is_probably_non_question(raw, source_kind="pdf_capture"))

    def test_corpus_validation_stops_issue_classification_for_non_problem_tiles(self) -> None:
        document = {
            "analysis": {
                "structured_problem": {
                    "normalized_problem_text": "단원평가 [3회] 정답",
                    "source_text_candidates": ["단원평가 [3회] 정답 1) 15 2) 8 3) 13"],
                    "expressions": [],
                },
                "solve_result": {
                    "validation_status": "failed",
                    "computed_answer": "",
                },
            }
        }

        self.assertEqual(classify_issues(document, "", source_kind="pdf_capture"), ["non_question_image"])


if __name__ == "__main__":
    unittest.main()
