from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.chat import state as chat_state


class ChatStateSortingTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.docs_dir = Path(self._tempdir.name)
        self._old_docs_dir = chat_state.DOCS_DIR
        chat_state.DOCS_DIR = self.docs_dir

    def tearDown(self) -> None:
        chat_state.DOCS_DIR = self._old_docs_dir
        self._tempdir.cleanup()

    def _write_doc(self, doc_id: str, started_at: float, file_name: str | None = None) -> None:
        payload = {
            "doc_id": doc_id,
            "file_name": file_name or f"{doc_id}.png",
            "file_path": f"/tmp/{doc_id}.png",
            "analysis": {
                "analysis_started_at": started_at,
                "analysis_finished_at": started_at + 1,
            },
        }
        (self.docs_dir / f"{doc_id}.json").write_text(json.dumps(payload), encoding="utf-8")

    def test_discovers_documents_by_registration_time_not_file_mtime(self) -> None:
        self._write_doc("older", 100.0)
        self._write_doc("newer", 200.0)

        docs = chat_state.discover_documents_from_disk()

        self.assertEqual([doc["doc_id"] for doc in docs], ["newer", "older"])

    def test_sync_ignores_click_mutated_created_at_for_legacy_docs(self) -> None:
        self._write_doc("older", 100.0)
        self._write_doc("newer", 200.0)
        state = chat_state.default_state()
        state["documents"] = [
            {"doc_id": "older", "file_name": "older.png", "created_at": 999.0},
            {"doc_id": "newer", "file_name": "newer.png", "created_at": 200.0},
        ]

        chat_state.sync_documents(state)

        self.assertEqual([doc["doc_id"] for doc in state["documents"]], ["newer", "older"])

    def test_promote_document_keeps_registration_sort_order(self) -> None:
        state = chat_state.default_state()
        state["documents"] = [
            {"doc_id": "newer", "file_name": "newer.png", "registered_at": 200.0, "created_at": 200.0},
            {"doc_id": "older", "file_name": "older.png", "registered_at": 100.0, "created_at": 100.0},
        ]

        chat_state.promote_document(state, "older")

        self.assertEqual([doc["doc_id"] for doc in state["documents"]], ["newer", "older"])
        self.assertEqual(state["selected_doc_id"], "older")
        self.assertGreater(state["documents"][1]["last_opened_at"], 0)

    def test_clear_main_chat_removes_everything(self) -> None:
        state = chat_state.default_state()
        state["main_chat_history"] = [
            {"role": "user", "content": "하이", "doc_id": None, "created_at": 1.0},
            {"role": "assistant", "content": "안녕하세요", "doc_id": None, "created_at": 2.0},
        ]
        chat_state.mark_active_target(state, "main")

        chat_state.clear_active_chat_history(state)

        self.assertEqual(state["main_chat_history"], [])

    def test_clear_study_chat_keeps_initial_card_only(self) -> None:
        state = chat_state.default_state()
        state["documents"] = [{"doc_id": "doc-1", "file_name": "doc.png", "registered_at": 1.0, "created_at": 1.0}]
        chat_state.mark_active_target(state, "study", "doc-1")
        chat_state.append_message(
            state,
            "assistant",
            "이미지에서 읽은 내용을 먼저 정리했어요.\n\n- 수식 후보: 1+1",
            doc_id="doc-1",
            kind=chat_state.INITIAL_STUDY_CARD_KIND,
        )
        chat_state.append_message(state, "user", "풀이해줘", doc_id="doc-1")
        chat_state.append_message(state, "assistant", "풀이는 2입니다.", doc_id="doc-1")
        state["generated_practice_by_doc"] = {
            "doc-1": {"items": [{"problem_text": "다른문제", "solved": False}]},
            "doc-2": {"items": [{"problem_text": "다른 카드 문제", "solved": False}]},
        }

        chat_state.clear_active_chat_history(state)

        self.assertEqual(len(state["chat_history"]), 1)
        self.assertEqual(state["chat_history"][0]["kind"], chat_state.INITIAL_STUDY_CARD_KIND)
        self.assertTrue(state["chat_history"][0]["content"].startswith("이미지에서 읽은 내용을"))
        self.assertNotIn("doc-1", state["generated_practice_by_doc"])
        self.assertIn("doc-2", state["generated_practice_by_doc"])

    def test_sync_keeps_study_message_preview_metadata(self) -> None:
        self._write_doc("doc-1", 100.0)
        state = chat_state.default_state()
        state["documents"] = [{"doc_id": "doc-1", "file_name": "doc.png", "registered_at": 100.0, "created_at": 100.0}]
        state["chat_history"] = [
            {
                "role": "assistant",
                "content": "좋아요. 같은 풀이 기준으로 비슷한 문제를 하나 내볼게요.",
                "doc_id": "doc-1",
                "created_at": 10.0,
                "preview_image_path": "/tmp/practice.png",
                "preview_image_label": "문제 그림",
            }
        ]

        chat_state.sync_documents(state)

        self.assertEqual(state["chat_history"][0]["preview_image_path"], "/tmp/practice.png")
        self.assertEqual(state["chat_history"][0]["preview_image_label"], "문제 그림")


if __name__ == "__main__":
    unittest.main()
