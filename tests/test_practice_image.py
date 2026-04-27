from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.chat.practice_image import render_practice_problem_image


class PracticeImageTests(unittest.TestCase):
    def test_renders_generated_practice_problem_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = render_practice_problem_image(
                "generic_make_ten_compose_decompose",
                "9와 5를 10을 이용하여 모으고 가르세요.",
                tmpdir,
                key="doc-1",
            )

            self.assertTrue(path)
            self.assertTrue(Path(path).exists())
            self.assertGreater(Path(path).stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
