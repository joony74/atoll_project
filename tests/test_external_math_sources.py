from __future__ import annotations

import json
import unittest
from pathlib import Path

from app.learning_engine import format_learning_engine_status
from app.problem_bank.repository import list_banks, search_problems


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = PROJECT_ROOT / "data" / "problem_bank" / "external_math_sources.json"


class ExternalMathSourcesTests(unittest.TestCase):
    def test_requested_external_sources_are_registered(self) -> None:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        sources = {item["bank_id"]: item for item in registry["sources"]}
        source_ids = set(sources)
        bank_ids = {item["bank_id"] for item in list_banks()}

        self.assertTrue({"deepmind_mathematics", "metamathqa", "tal_scq5k"} <= source_ids)
        self.assertTrue({"deepmind_mathematics", "metamathqa", "tal_scq5k"} <= bank_ids)
        self.assertEqual(sources["deepmind_mathematics"].get("import_status"), "sample_imported")
        self.assertEqual(sources["metamathqa"].get("import_status"), "sample_imported")
        self.assertEqual(sources["tal_scq5k"].get("import_status"), "imported")

    def test_registered_pending_sources_do_not_break_all_bank_search(self) -> None:
        results = search_problems("linear", bank_id="all", limit=3)

        self.assertGreaterEqual(len(results), 1)

    def test_learning_engine_status_reports_external_source_queue(self) -> None:
        status = format_learning_engine_status()

        self.assertIn("등록된 외부 수학 소스: 3개", status)
        self.assertIn("전체 import 대기 소스: 0개", status)


if __name__ == "__main__":
    unittest.main()
