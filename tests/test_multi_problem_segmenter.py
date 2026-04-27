from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.core.multi_problem_segmenter import detect_problem_regions, save_problem_card_images


def _marker_font() -> ImageFont.ImageFont:
    for path in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, 42)
    try:
        return ImageFont.load_default(size=42)
    except TypeError:  # pragma: no cover - older Pillow fallback
        return ImageFont.load_default()


class MultiProblemSegmenterTests(unittest.TestCase):
    def test_detects_two_column_orange_question_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "worksheet.png"
            image = Image.new("RGB", (1200, 1000), "white")
            draw = ImageDraw.Draw(image)
            font = _marker_font()
            positions = [(50, 80), (50, 350), (50, 640), (670, 80), (670, 350), (670, 640)]
            for index, (x, y) in enumerate(positions, start=1):
                draw.text((x, y), f"{index}.", fill=(238, 120, 43), font=font)
                draw.text((x + 70, y + 12), "문제 내용을 여기에 둡니다.", fill=(20, 20, 20), font=font)
            image.save(image_path)

            regions = detect_problem_regions(image_path)
            self.assertEqual([region.label for region in regions], ["01", "02", "03", "04", "05", "06"])
            self.assertLessEqual(regions[1].bbox[1], 350 - 24)
            self.assertEqual(regions[2].bbox[3], 1000)
            self.assertEqual(regions[5].bbox[3], 1000)

            cards = save_problem_card_images(image_path, Path(tmp) / "cards", base_name="worksheet")
            self.assertEqual(len(cards), 6)
            self.assertTrue(all(Path(card.path).exists() for card in cards))


if __name__ == "__main__":
    unittest.main()
