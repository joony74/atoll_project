from __future__ import annotations

import unittest

from app.chat.internal_search import build_internal_search_panel, build_internal_search_reply, parse_internal_search_command


class InternalSearchTests(unittest.TestCase):
    def test_parse_search_command(self) -> None:
        self.assertEqual(parse_internal_search_command("검색: 이차방정식"), "이차방정식")
        self.assertEqual(parse_internal_search_command(" 찾기：  분수 덧셈  "), "분수 덧셈")
        self.assertIsNone(parse_internal_search_command("이차방정식 검색"))

    def test_searches_main_and_study_chat_with_internal_links(self) -> None:
        state = {
            "documents": [{"doc_id": "doc-1", "file_name": "중3_이차방정식.png"}],
            "main_chat_history": [
                {"role": "user", "content": "이차방정식 풀이 기준 정리해줘", "created_at": 10.0},
                {"role": "user", "content": "검색: 이차방정식", "created_at": 20.0},
            ],
            "chat_history": [
                {
                    "role": "assistant",
                    "content": "이미지에서 읽은 문제는 이차방정식 x^2 - 5x + 6 = 0 입니다.",
                    "doc_id": "doc-1",
                    "created_at": 12.0,
                }
            ],
        }

        reply = build_internal_search_reply("검색: 이차방정식", state)

        self.assertIsNotNone(reply)
        assert reply is not None
        self.assertIn("[메인 채팅 열기](?chat=main)", reply)
        self.assertIn("[중3_이차방정식.png 열기](?doc=doc-1)", reply)
        self.assertNotIn("검색: 이차방정식", reply)

    def test_search_panel_deduplicates_same_document_results(self) -> None:
        state = {
            "documents": [{"doc_id": "doc-1", "file_name": "중3_이차방정식.png"}],
            "chat_history": [
                {
                    "role": "assistant",
                    "content": "이차방정식 풀이 카드입니다.",
                    "doc_id": "doc-1",
                    "created_at": 12.0,
                },
                {
                    "role": "user",
                    "content": "이차방정식 풀이해줘",
                    "doc_id": "doc-1",
                    "created_at": 13.0,
                },
            ],
        }

        panel = build_internal_search_panel("검색: 이차방정식", state)

        self.assertIsNotNone(panel)
        assert panel is not None
        results = panel["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["target_type"], "study")
        self.assertEqual(results[0]["doc_id"], "doc-1")

    def test_document_search_does_not_return_unmatched_documents_by_weight_only(self) -> None:
        state = {
            "documents": [
                {
                    "doc_id": "doc-match",
                    "file_name": "문제_14-6.png",
                    "analysis": {
                        "structured_problem": {
                            "normalized_problem_text": "14-6에서 6을 4와 2로 가르고 계산하세요.",
                            "metadata": {"debug": {"confidence": 0.6799999999999999}},
                        }
                    },
                },
                {
                    "doc_id": "doc-other",
                    "file_name": "문제_8+5.png",
                    "analysis": {
                        "structured_problem": {
                            "normalized_problem_text": "8+5에서 5를 2와 3으로 가르고 계산하세요.",
                            "metadata": {"debug": {"confidence": 0.6799999999999999}},
                        }
                    },
                },
            ],
            "chat_history": [],
            "main_chat_history": [],
        }

        panel = build_internal_search_panel("검색: 14-6", state)
        self.assertIsNotNone(panel)
        assert panel is not None
        self.assertEqual([item["doc_id"] for item in panel["results"]], ["doc-match"])

        no_match_panel = build_internal_search_panel("검색: 999999", state)
        self.assertIsNotNone(no_match_panel)
        assert no_match_panel is not None
        self.assertEqual(no_match_panel["results"], [])

    def test_no_result_message_names_search_scope(self) -> None:
        reply = build_internal_search_reply("검색: 확률과통계", {"main_chat_history": [], "chat_history": []})

        self.assertIsNotNone(reply)
        assert reply is not None
        self.assertIn("관련 기록을 아직 찾지 못했어요", reply)
        self.assertIn("메인 채팅, 학습리스트 채팅", reply)


if __name__ == "__main__":
    unittest.main()
