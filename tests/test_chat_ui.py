from __future__ import annotations

import base64
import tempfile
import unittest
from pathlib import Path

from app.chat.ui import render_conversation


PNG_1X1 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAFgwJ/lx3m7wAAAABJRU5ErkJggg=="
)


class ChatUiTests(unittest.TestCase):
    def test_renders_study_card_preview_with_hover_popover(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "problem.png"
            image_path.write_bytes(base64.b64decode(PNG_1X1))

            markup = render_conversation(
                [
                    {
                        "role": "assistant",
                        "content": "이미지에서 읽은 내용을 먼저 정리했어요.",
                        "preview_image_path": str(image_path),
                    }
                ],
                mode="study",
            )

        self.assertIn("assistant-card with-preview", markup)
        self.assertIn("assistant-image-popover", markup)
        self.assertIn("data:image/png;base64,", markup)
        self.assertIn("원본 1 x 1px", markup)

    def test_renders_custom_preview_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "practice.png"
            image_path.write_bytes(base64.b64decode(PNG_1X1))

            markup = render_conversation(
                [
                    {
                        "role": "assistant",
                        "content": "문제: 9와 5를 10을 이용하여 모으고 가르세요.",
                        "preview_image_path": str(image_path),
                        "preview_image_label": "문제 그림",
                    }
                ],
                mode="study",
            )

        self.assertIn("assistant-card with-preview", markup)
        self.assertIn("문제 그림 1 x 1px", markup)

    def test_renders_safe_internal_links(self) -> None:
        markup = render_conversation(
            [
                {
                    "role": "assistant",
                    "content": "[학습자료 열기](?doc=doc-1)\n[외부 링크](https://example.com)",
                }
            ]
        )

        self.assertIn('<a class="coco-chat-link" href="?doc=doc-1">학습자료 열기</a>', markup)
        self.assertIn("[외부 링크](https://example.com)", markup)


if __name__ == "__main__":
    unittest.main()
