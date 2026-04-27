from __future__ import annotations

import re
import unittest

from app.chat.study_fast_reply import build_fast_study_reply


def _document(rule_id: str, problem_text: str, answer: str, doc_id: str = "doc-1") -> dict:
    return {
        "doc_id": doc_id,
        "analysis": {
            "structured_problem": {
                "normalized_problem_text": problem_text,
                "math_topic": "arithmetic",
                "metadata": {
                    "school_level": "elementary",
                    "visual_template": {
                        "rule_id": rule_id,
                        "confidence": 0.86,
                    },
                },
            },
            "solve_result": {
                "solver_name": "visual_template_solver",
                "computed_answer": answer,
                "validation_status": "verified",
            },
        },
    }


class StudyFastReplyTests(unittest.TestCase):
    def test_make_ten_compose_reply_explains_diagram_without_llm(self) -> None:
        reply = build_fast_study_reply(
            "플이해줘",
            _document(
                "generic_make_ten_compose_decompose",
                "9와 6을 10을 이용하여 모으고 가르세요.",
                "빈칸: 15, 5",
            ),
        )

        self.assertIsNotNone(reply)
        assert reply is not None
        self.assertIn("9 + 6 = 15", reply)
        self.assertIn("9와 6을 모으면", reply)
        self.assertIn("15는 10과 5", reply)
        self.assertIn("15와 5를 쓰면", reply)
        self.assertIn("정답: 빈칸: 15, 5", reply)

    def test_make_ten_addition_reply_explains_split(self) -> None:
        reply = build_fast_study_reply(
            "풀이해줘",
            _document(
                "generic_make_ten_addition_decomposition",
                "8+5에서 5를 2와 3으로 가르고 10을 만들어 계산하세요.",
                "빈칸: 13, 3",
            ),
        )

        self.assertIsNotNone(reply)
        assert reply is not None
        self.assertIn("5를 2와 3으로", reply)
        self.assertIn("8에 2를 더하면 10", reply)
        self.assertIn("정답: 빈칸: 13, 3", reply)

    def test_make_ten_subtraction_reply_explains_split(self) -> None:
        reply = build_fast_study_reply(
            "답 알려줘",
            _document(
                "generic_make_ten_subtraction_decomposition",
                "14-6에서 6을 4와 2로 가르고 10을 이용해 계산하세요.",
                "빈칸: 8, 4",
            ),
        )

        self.assertIsNotNone(reply)
        assert reply is not None
        self.assertIn("6을 4와 2로", reply)
        self.assertIn("14에서 4를 먼저 빼면 10", reply)
        self.assertIn("정답: 빈칸: 8, 4", reply)

    def test_non_solution_prompt_can_use_regular_chat_path(self) -> None:
        reply = build_fast_study_reply(
            "안녕",
            _document(
                "generic_make_ten_compose_decompose",
                "9와 6을 10을 이용하여 모으고 가르세요.",
                "빈칸: 15, 5",
            ),
        )

        self.assertIsNone(reply)

    def test_verified_non_visual_solution_uses_local_reply(self) -> None:
        reply = build_fast_study_reply(
            "풀이해줘",
            {
                "analysis": {
                    "structured_problem": {
                        "normalized_problem_text": "3+4의 값을 구하시오.",
                        "metadata": {},
                    },
                    "solve_result": {
                        "solver_name": "safe_eval_solver",
                        "computed_answer": "7",
                        "validation_status": "verified",
                        "steps": ["3과 4를 더합니다.", "3+4=7입니다."],
                    },
                },
            },
        )

        self.assertIsNotNone(reply)
        assert reply is not None
        self.assertIn("3+4의 값을 구하시오", reply)
        self.assertIn("3+4=7", reply)
        self.assertIn("정답: 7", reply)

    def test_similar_problem_prompt_generates_same_template_problem(self) -> None:
        reply = build_fast_study_reply(
            "다른문제",
            _document(
                "generic_make_ten_compose_decompose",
                "9와 6을 10을 이용하여 모으고 가르세요.",
                "빈칸: 15, 5",
            ),
        )

        self.assertIsNotNone(reply)
        assert reply is not None
        self.assertIn("같은 풀이 기준", reply)
        self.assertIn("문제:", reply)
        self.assertIn("10을 이용하여 모으고 가르세요", reply)
        self.assertNotIn("정답:", reply)

    def test_generated_similar_problem_is_used_by_next_solution_prompt(self) -> None:
        state: dict = {"selected_doc_id": "doc-1"}
        document = _document(
            "generic_make_ten_compose_decompose",
            "9와 6을 10을 이용하여 모으고 가르세요.",
            "빈칸: 15, 5",
            doc_id="doc-1",
        )

        generated = build_fast_study_reply("다른문제", document, state=state)
        self.assertIsNotNone(generated)
        generated_problem = state["generated_practice_by_doc"]["doc-1"]["problem_text"]
        first, second = [int(item) for item in re.findall(r"\d+", generated_problem)[:2]]

        reply = build_fast_study_reply("풀이해줘", document, state=state)

        self.assertIsNotNone(reply)
        assert reply is not None
        self.assertIn(f"{first} + {second} = {first + second}", reply)
        self.assertIn(f"정답: 빈칸: {first + second}, {first + second - 10}", reply)
        self.assertTrue(state["generated_practice_by_doc"]["doc-1"]["items"][-1]["solved"])

    def test_similar_problem_blocks_until_current_generated_problem_is_solved(self) -> None:
        state: dict = {"selected_doc_id": "doc-1"}
        document = _document(
            "generic_make_ten_compose_decompose",
            "9와 6을 10을 이용하여 모으고 가르세요.",
            "빈칸: 15, 5",
            doc_id="doc-1",
        )

        first = build_fast_study_reply("다른문제", document, state=state)
        second = build_fast_study_reply("다른문제", document, state=state)

        self.assertIsNotNone(first)
        self.assertEqual(second, "먼저 제출된 문제 풀이를 완료하여야 다른 문제가 제출됩니다.")
        self.assertEqual(len(state["generated_practice_by_doc"]["doc-1"]["items"]), 1)

    def test_similar_problem_generates_unique_sequence_until_ten_solved(self) -> None:
        state: dict = {"selected_doc_id": "doc-1"}
        document = _document(
            "generic_make_ten_compose_decompose",
            "9와 6을 10을 이용하여 모으고 가르세요.",
            "빈칸: 15, 5",
            doc_id="doc-1",
        )

        generated_texts: list[str] = []
        for index in range(1, 11):
            generated = build_fast_study_reply("다른문제", document, state=state)
            self.assertIsNotNone(generated)
            assert generated is not None
            self.assertIn(f"({index}/10)", generated)
            generated_texts.append(state["generated_practice_by_doc"]["doc-1"]["problem_text"])
            solved = build_fast_study_reply("풀이해줘", document, state=state)
            self.assertIsNotNone(solved)

        self.assertEqual(len(generated_texts), len(set(generated_texts)))
        completed = build_fast_study_reply("다른문제", document, state=state)
        self.assertEqual(completed, "해당 학습문제를 전부 풀었습니다.")


if __name__ == "__main__":
    unittest.main()
