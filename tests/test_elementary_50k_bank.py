from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.prepare_elementary_50k_bank import (
    build_grade_queue,
    collect_files,
    count_by_grade,
    normalize_validation_summary,
)


class Elementary50kBankTests(unittest.TestCase):
    def test_collects_only_requested_file_kind_under_required_part(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "1학년" / "EDITE").mkdir(parents=True)
            (root / "1학년" / "PDF").mkdir(parents=True)
            (root / "1학년" / "EDITE" / "a.png").write_bytes(b"png")
            (root / "1학년" / "PDF" / "b.png").write_bytes(b"png")

            paths = collect_files(root, {".png"}, required_part="EDITE")

        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0].name, "a.png")

    def test_counts_grade_from_path(self) -> None:
        paths = [
            Path("/tmp/1학년/EDITE/a.png"),
            Path("/tmp/2학년/EDITE/b.png"),
            Path("/tmp/2학년/EDITE/c.png"),
        ]

        self.assertEqual(count_by_grade(paths), {"1학년": 1, "2학년": 2})

    def test_normalizes_existing_validation_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text('{"total": 10, "ok": 9, "review": 1, "error": 0}', encoding="utf-8")

            summary = normalize_validation_summary(path)

        self.assertEqual(summary["total"], 10)
        self.assertEqual(summary["ok_rate"], 0.9)

    def test_grade_queue_subtracts_verified_and_pending_images(self) -> None:
        config = {"grade_targets": {"1학년": 100, "2학년": 100}}
        sources = [
            {"status": "verified", "edite_by_grade": {"1학년": 10}},
            {"status": "pending_revalidation", "edite_by_grade": {"1학년": 5, "2학년": 7}},
        ]

        queue = build_grade_queue(config, sources)

        self.assertEqual(queue["1학년"]["verified_or_baseline_images"], 10)
        self.assertEqual(queue["1학년"]["pending_images"], 5)
        self.assertEqual(queue["1학년"]["remaining_after_current_images"], 85)
        self.assertEqual(queue["2학년"]["remaining_after_current_images"], 93)


if __name__ == "__main__":
    unittest.main()
