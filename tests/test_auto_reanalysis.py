from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.learning_engine.auto_reanalysis import (
    analysis_reanalysis_reasons,
    maybe_upgrade_registered_analysis,
)


def _analysis(
    *,
    text: str = "3+4를 계산하세요.",
    expressions: list[str] | None = None,
    confidence: float = 0.8,
    status: str = "verified",
    answer: str = "7",
) -> dict:
    return {
        "structured_problem": {
            "normalized_problem_text": text,
            "expressions": expressions if expressions is not None else ["3+4"],
            "source_text_candidates": [text] if text else [],
            "confidence": confidence,
            "metadata": {},
        },
        "solve_result": {
            "validation_status": status,
            "computed_answer": answer,
            "steps": ["3+4=7"] if answer else [],
        },
    }


class AutoReanalysisTests(unittest.TestCase):
    def test_healthy_analysis_is_marked_without_recheck(self) -> None:
        calls: list[tuple[str, str]] = []

        result = maybe_upgrade_registered_analysis(
            file_path="/tmp/problem.png",
            initial_analysis=_analysis(),
            analyzer=lambda path, prompt: calls.append((path, prompt)) or _analysis(),
        )

        self.assertEqual(calls, [])
        self.assertEqual(
            result["structured_problem"]["metadata"]["auto_reanalysis"]["status"],
            "healthy",
        )

    def test_failed_analysis_is_upgraded_when_recheck_is_better(self) -> None:
        initial = _analysis(text="", expressions=[], confidence=0.1, status="failed", answer="")
        improved = _analysis(text="8+5를 계산하세요.", expressions=["8+5"], confidence=0.82, status="verified", answer="13")
        calls: list[tuple[str, str]] = []

        def analyzer(path: str, prompt: str) -> dict:
            calls.append((path, prompt))
            return improved

        result = maybe_upgrade_registered_analysis(
            file_path="/tmp/problem.png",
            initial_analysis=initial,
            analyzer=analyzer,
            doc_id="doc-1",
            file_name="problem.png",
        )

        self.assertEqual(len(calls), 1)
        self.assertEqual(result["solve_result"]["computed_answer"], "13")
        metadata = result["structured_problem"]["metadata"]["auto_reanalysis"]
        self.assertEqual(metadata["status"], "upgraded")
        self.assertEqual(metadata["selected_attempt"], 1)

    def test_remaining_failure_is_written_to_review_queue(self) -> None:
        initial = _analysis(text="", expressions=[], confidence=0.1, status="failed", answer="")

        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = Path(tmpdir) / "queue.jsonl"
            result = maybe_upgrade_registered_analysis(
                file_path="/tmp/problem.png",
                initial_analysis=initial,
                analyzer=lambda path, prompt: initial,
                doc_id="doc-1",
                file_name="problem.png",
                review_queue_path=queue_path,
                max_attempts=1,
            )

            self.assertEqual(
                result["structured_problem"]["metadata"]["auto_reanalysis"]["status"],
                "review_queued",
            )
            rows = [json.loads(line) for line in queue_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["doc_id"], "doc-1")
        self.assertIn("solver_failed", rows[0]["reasons"])

    def test_successful_upgrade_removes_stale_review_queue_entry(self) -> None:
        failed = _analysis(text="", expressions=[], confidence=0.1, status="failed", answer="")
        improved = _analysis(text="8+5를 계산하세요.", expressions=["8+5"], confidence=0.82, status="verified", answer="13")

        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = Path(tmpdir) / "queue.jsonl"
            maybe_upgrade_registered_analysis(
                file_path="/tmp/problem.png",
                initial_analysis=failed,
                analyzer=lambda path, prompt: failed,
                doc_id="doc-1",
                file_name="problem.png",
                review_queue_path=queue_path,
                max_attempts=1,
            )
            self.assertTrue(queue_path.read_text(encoding="utf-8").strip())

            result = maybe_upgrade_registered_analysis(
                file_path="/tmp/problem.png",
                initial_analysis=failed,
                analyzer=lambda path, prompt: improved,
                doc_id="doc-1",
                file_name="problem.png",
                review_queue_path=queue_path,
                max_attempts=1,
            )

            self.assertEqual(
                result["structured_problem"]["metadata"]["auto_reanalysis"]["status"],
                "upgraded",
            )
            self.assertEqual(queue_path.read_text(encoding="utf-8"), "")

    def test_reanalysis_reasons_match_study_check_failure_signals(self) -> None:
        reasons = analysis_reanalysis_reasons(
            _analysis(text="", expressions=[], confidence=0.0, status="failed", answer="")
        )

        self.assertIn("missing_recognition", reasons)
        self.assertIn("solver_failed", reasons)
        self.assertIn("missing_solution_signal", reasons)


if __name__ == "__main__":
    unittest.main()
