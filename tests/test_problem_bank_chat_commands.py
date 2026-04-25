from __future__ import annotations

import unittest

from app.problem_bank.chat_commands import (
    format_problem_bank_search_results,
    parse_problem_bank_command,
    resolve_problem_bank_selection,
)


class ProblemBankChatCommandTests(unittest.TestCase):
    def test_parses_help_command(self) -> None:
        command = parse_problem_bank_command("문제은행")

        self.assertIsNotNone(command)
        self.assertEqual(command.action, "help")

    def test_parses_search_with_subject_and_level_filters(self) -> None:
        command = parse_problem_bank_command("문제 은행 algebra level 5")

        self.assertIsNotNone(command)
        self.assertEqual(command.action, "search")
        self.assertEqual(command.subject_slug, "algebra")
        self.assertEqual(command.level_number, 5)
        self.assertEqual(command.query, "")

    def test_parses_korean_subject_alias(self) -> None:
        command = parse_problem_bank_command("문제은행 기하 난이도 3")

        self.assertIsNotNone(command)
        self.assertEqual(command.action, "search")
        self.assertEqual(command.subject_slug, "geometry")
        self.assertEqual(command.level_number, 3)

    def test_parses_elementary_word_problem_alias(self) -> None:
        command = parse_problem_bank_command("문제은행 초등 문장제")

        self.assertIsNotNone(command)
        self.assertEqual(command.action, "search")
        self.assertEqual(command.subject_slug, "arithmetic_word_problem")
        self.assertEqual(command.query, "")

    def test_parses_open_command(self) -> None:
        command = parse_problem_bank_command("문제은행 열기 2")

        self.assertIsNotNone(command)
        self.assertEqual(command.action, "open")
        self.assertEqual(command.target, "2")

    def test_resolves_numbered_selection(self) -> None:
        results = [{"id": "first"}, {"id": "second"}]

        self.assertEqual(resolve_problem_bank_selection("2", results), {"id": "second"})
        self.assertIsNone(resolve_problem_bank_selection("3", results))

    def test_formats_search_results_with_open_instruction(self) -> None:
        command = parse_problem_bank_command("문제은행 algebra level 5")
        reply = format_problem_bank_search_results(
            [
                {
                    "id": "competition_math:algebra:level_5:00000",
                    "subject": "Algebra",
                    "level": "Level 5",
                    "problem_preview": "A sample problem",
                    "answer": "42",
                }
            ],
            command,
        )

        self.assertIn("문제은행에서 1개", reply)
        self.assertIn("문제은행 열기 1", reply)
        self.assertIn("답: 42", reply)


if __name__ == "__main__":
    unittest.main()
