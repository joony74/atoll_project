from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.run_elementary_beta_stabilization import (
    collect_corpus_summary,
    evaluate_gates,
    normalize_validation_summary,
)


class ElementaryBetaStabilizationTests(unittest.TestCase):
    def test_normalizes_summary_file_shapes(self) -> None:
        summary = normalize_validation_summary(
            {
                "summary": {
                    "total": 20,
                    "ok": 18,
                    "review": 1,
                    "error": 1,
                    "non_problem": 0,
                    "issue_counts": {"ocr_text_loss": 1},
                }
            }
        )

        self.assertEqual(summary["total"], 20)
        self.assertEqual(summary["ok_rate"], 0.9)
        self.assertEqual(summary["review_rate"], 0.05)
        self.assertEqual(summary["error_rate"], 0.05)
        self.assertEqual(summary["issue_counts"], {"ocr_text_loss": 1})

    def test_collects_edite_images_by_grade(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            edite = root / "1학년" / "EDITE"
            pdf = root / "1학년" / "PDF"
            edite.mkdir(parents=True)
            pdf.mkdir(parents=True)
            (edite / "초1_test.png").write_bytes(b"png")
            (pdf / "ignored.png").write_bytes(b"png")

            summary = collect_corpus_summary(root)

        self.assertEqual(summary["edite_image_total"], 1)
        self.assertEqual(summary["by_grade"], {"1학년": 1})

    def test_current_source_can_pass_while_beta_needs_more_sources(self) -> None:
        config = {
            "thresholds": {
                "current_source_min_cards": 500,
                "current_source_min_ok_rate": 0.99,
                "current_source_max_review_rate": 0.01,
                "current_source_max_error_rate": 0.0,
                "beta_min_sources": 3,
                "beta_min_cards": 5000,
                "beta_min_ok_rate": 0.95,
            }
        }
        baseline = {
            "total": 720,
            "ok_rate": 1.0,
            "review_rate": 0.0,
            "error_rate": 0.0,
        }
        source_summary = {
            "active_source_count": 1,
            "active_validated_cards": 720,
            "weighted_ok_rate": 1.0,
        }

        gates = evaluate_gates(config, baseline, source_summary)

        self.assertTrue(gates["current_source"]["passed"])
        self.assertFalse(gates["beta"]["passed"])


if __name__ == "__main__":
    unittest.main()
