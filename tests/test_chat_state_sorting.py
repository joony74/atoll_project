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


if __name__ == "__main__":
    unittest.main()
