from __future__ import annotations

import unittest

from app.chat.context_packet import build_study_chat_context_packet
from app.problem_bank.repository import (
    list_banks,
    load_problem,
    record_to_analysis,
    record_to_document,
    search_problems,
)


class ProblemBankRepositoryTests(unittest.TestCase):
    def test_lists_imported_competition_math_bank(self) -> None:
        banks = list_banks()

        self.assertTrue(any(bank.get("bank_id") == "competition_math" for bank in banks))
        self.assertTrue(any(bank.get("bank_id") == "gsm8k" for bank in banks))

    def test_search_returns_lightweight_results(self) -> None:
        results = search_problems("piecewise continuous", subject_slug="algebra", limit=5)

        self.assertGreaterEqual(len(results), 1)
        self.assertIn("id", results[0])
        self.assertIn("problem_preview", results[0])
        self.assertNotIn("solution_latex", results[0])

    def test_search_all_banks_finds_gsm8k_word_problem(self) -> None:
        results = search_problems("Natalia clips", bank_id="all", limit=5)

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["bank_id"], "gsm8k")
        self.assertIn("Natalia", results[0]["problem_preview"])

    def test_load_problem_and_convert_to_analysis(self) -> None:
        result = search_problems("piecewise continuous", subject_slug="algebra", limit=1)[0]
        record = load_problem(result["id"])
        analysis = record_to_analysis(record)

        self.assertEqual(analysis["structured_problem"]["metadata"]["source"], "problem_bank")
        self.assertEqual(analysis["solve_result"]["solver_name"], "problem_bank_solution")
        self.assertIn("reference_solution_latex", analysis["structured_problem"]["metadata"])

    def test_convert_to_document_payload(self) -> None:
        result = search_problems("piecewise continuous", subject_slug="algebra", limit=1)[0]
        record = load_problem(result["id"])
        document = record_to_document(record)

        self.assertTrue(document["doc_id"].startswith("competition_math__"))
        self.assertIn("analysis", document)
        self.assertIn("Competition", document["analysis"]["problem_bank_record"]["source"]["name"])

    def test_problem_bank_document_feeds_reference_solution_to_study_context(self) -> None:
        result = search_problems("piecewise continuous", subject_slug="algebra", limit=1)[0]
        record = load_problem(result["id"])
        document = record_to_document(record)
        packet = build_study_chat_context_packet("풀이 설명해줘", document=document, state={"documents": [document]})

        self.assertEqual(packet["study_source"], "problem_bank")
        self.assertIn("piecewise", packet["study_problem_text"])
        self.assertTrue(packet["study_reference_solution"])

    def test_load_gsm8k_problem_and_convert_to_analysis(self) -> None:
        result = search_problems("Natalia clips", bank_id="all", limit=1)[0]
        record = load_problem(result["id"], bank_id=result["bank_id"])
        analysis = record_to_analysis(record)

        self.assertEqual(record["source"]["name"], "GSM8K")
        self.assertEqual(analysis["solve_result"]["computed_answer"], "72")
        self.assertIn("Natalia", analysis["structured_problem"]["normalized_problem_text"])


if __name__ == "__main__":
    unittest.main()
