from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.collect_elementary_50k_sources import (
    collect_local_files,
    external_problem_uniqueness_key,
    generate_template_reserve_records,
    infer_grade,
    safe_name,
    summarize,
    template_uniqueness_key,
)


class CollectElementary50kSourcesTests(unittest.TestCase):
    def test_safe_name_removes_path_separators(self) -> None:
        self.assertEqual(safe_name("초1/2: PDF*문제?.png"), "초1_2_PDF_문제_.png")

    def test_infer_grade_from_path_and_record(self) -> None:
        self.assertEqual(infer_grade(Path("01.초등/3학년/PDF/a.pdf")), "3학년")
        self.assertEqual(infer_grade(Path("foo"), {"grade": 5}), "5학년")

    def test_collect_local_files_dedupes_by_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "01.초등" / "1학년" / "PDF"
            source.mkdir(parents=True)
            (source / "a.pdf").write_bytes(b"%PDF sample")
            (source / "b.pdf").write_bytes(b"%PDF sample")
            records = collect_local_files([root], output_root=root / "out")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["grade"], "1학년")
        self.assertEqual(records[0]["source_type"], "source_pdf")

    def test_summarize_counts_tracks(self) -> None:
        summary = summarize(
            [
                {"track": "actual_pdf_capture", "source_type": "source_pdf", "grade": "1학년"},
                {"track": "normalized_json", "source_type": "external_problem_bank_record", "grade": "elementary"},
            ]
        )

        self.assertEqual(summary["total_files_prepared"], 2)
        self.assertEqual(summary["by_track"]["actual_pdf_capture"], 1)
        self.assertEqual(summary["by_track"]["normalized_json"], 1)

    def test_template_uniqueness_key_includes_structured_values(self) -> None:
        first = {"problem_text": "평균을 구하시오.", "answer": "5", "table": [["값", "3", "5", "7"]]}
        second = {"problem_text": "평균을 구하시오.", "answer": "6", "table": [["값", "4", "6", "8"]]}

        self.assertNotEqual(template_uniqueness_key(first), template_uniqueness_key(second))

    def test_external_problem_uniqueness_normalizes_spacing(self) -> None:
        first = {"content": {"problem_plain": "3 + 4 = ?"}}
        second = {"content": {"problem_plain": " 3   +   4 = ? "}}

        self.assertEqual(external_problem_uniqueness_key(first), external_problem_uniqueness_key(second))

    def test_generate_template_reserve_records_makes_unique_candidates(self) -> None:
        records = generate_template_reserve_records(count=30, seed=20260430)
        keys = [template_uniqueness_key(record["record"]) for record in records]

        self.assertEqual(len(records), 30)
        self.assertEqual(len(keys), len(set(keys)))


if __name__ == "__main__":
    unittest.main()
