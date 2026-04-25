from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "설계구조.md"
OUTPUT = ROOT / "docs" / "설계구조.pdf"
FONT_CANDIDATES = [
    Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
    Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
    Path("/System/Library/Fonts/SFNS.ttf"),
]

PAGE_WIDTH = 1654
PAGE_HEIGHT = 2339
MARGIN_X = 120
MARGIN_Y = 120
CONTENT_WIDTH = PAGE_WIDTH - (MARGIN_X * 2)
BG = "white"
FG = "#111827"
SUB_FG = "#374151"
RULE = "#d1d5db"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in FONT_CANDIDATES:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


TITLE_FONT = load_font(54)
H1_FONT = load_font(34)
H2_FONT = load_font(28)
BODY_FONT = load_font(23)
MONO_FONT = load_font(22)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, width: int) -> list[str]:
    words = text.split(" ")
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def wrap_korean_text(draw: ImageDraw.ImageDraw, text: str, font, width: int) -> list[str]:
    if " " in text:
        return wrap_text(draw, text, font, width)
    lines: list[str] = []
    current = ""
    for ch in text:
        trial = current + ch
        if current and draw.textlength(trial, font=font) > width:
            lines.append(current)
            current = ch
        else:
            current = trial
    if current:
        lines.append(current)
    return lines or [text]


def paragraph_lines(draw: ImageDraw.ImageDraw, text: str, font, width: int) -> list[str]:
    segments = []
    for raw in text.splitlines():
        stripped = raw.rstrip()
        if not stripped:
            segments.append("")
            continue
        wrapped = wrap_korean_text(draw, stripped, font, width)
        segments.extend(wrapped)
    return segments


def render_markdown(md_text: str) -> list[Image.Image]:
    pages: list[Image.Image] = []
    image = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    y = MARGIN_Y

    def new_page() -> None:
        nonlocal image, draw, y
        pages.append(image)
        image = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), BG)
        draw = ImageDraw.Draw(image)
        y = MARGIN_Y

    def ensure_space(height: int) -> None:
        nonlocal y
        if y + height > PAGE_HEIGHT - MARGIN_Y:
            new_page()

    lines = md_text.splitlines()
    in_code = False
    for raw in lines:
        line = raw.rstrip("\n")
        if line.strip().startswith("```"):
            in_code = not in_code
            if in_code:
                ensure_space(30)
                draw.line((MARGIN_X, y, PAGE_WIDTH - MARGIN_X, y), fill=RULE, width=2)
                y += 18
            else:
                y += 8
                draw.line((MARGIN_X, y, PAGE_WIDTH - MARGIN_X, y), fill=RULE, width=2)
                y += 24
            continue

        if in_code:
            font = MONO_FONT
            text_lines = paragraph_lines(draw, line, font, CONTENT_WIDTH)
            line_h = 32
            ensure_space(line_h * max(1, len(text_lines)) + 8)
            for t in text_lines:
                draw.text((MARGIN_X + 10, y), t, font=font, fill=SUB_FG)
                y += line_h
            y += 8
            continue

        if line.startswith("# "):
            font = TITLE_FONT
            text = line[2:].strip()
            ensure_space(80)
            draw.text((MARGIN_X, y), text, font=font, fill=FG)
            y += 78
            draw.line((MARGIN_X, y, PAGE_WIDTH - MARGIN_X, y), fill=RULE, width=2)
            y += 28
            continue

        if line.startswith("## "):
            font = H1_FONT
            text = line[3:].strip()
            ensure_space(58)
            draw.text((MARGIN_X, y), text, font=font, fill=FG)
            y += 52
            continue

        if line.startswith("### "):
            font = H2_FONT
            text = line[4:].strip()
            ensure_space(48)
            draw.text((MARGIN_X, y), text, font=font, fill=FG)
            y += 42
            continue

        if line.startswith("- "):
            bullet = "• "
            body = line[2:].strip()
            wrapped = paragraph_lines(draw, body, BODY_FONT, CONTENT_WIDTH - 40)
            line_h = 34
            ensure_space(line_h * len(wrapped) + 4)
            for idx, t in enumerate(wrapped):
                prefix = bullet if idx == 0 else "  "
                draw.text((MARGIN_X, y), prefix, font=BODY_FONT, fill=FG)
                draw.text((MARGIN_X + 30, y), t, font=BODY_FONT, fill=FG)
                y += line_h
            y += 4
            continue

        if re_like_numbered(line):
            body = line.strip()
            wrapped = paragraph_lines(draw, body, BODY_FONT, CONTENT_WIDTH)
            line_h = 34
            ensure_space(line_h * len(wrapped) + 4)
            for t in wrapped:
                draw.text((MARGIN_X, y), t, font=BODY_FONT, fill=FG)
                y += line_h
            y += 4
            continue

        if not line.strip():
            y += 16
            continue

        wrapped = paragraph_lines(draw, line, BODY_FONT, CONTENT_WIDTH)
        line_h = 34
        ensure_space(line_h * len(wrapped) + 8)
        for t in wrapped:
            draw.text((MARGIN_X, y), t, font=BODY_FONT, fill=FG)
            y += line_h
        y += 8

    pages.append(image)
    return pages


def re_like_numbered(text: str) -> bool:
    stripped = text.lstrip()
    if not stripped:
        return False
    head = stripped.split(" ", 1)[0]
    return head.endswith(".") and head[:-1].isdigit()


def main() -> int:
    md_text = SOURCE.read_text(encoding="utf-8")
    pages = render_markdown(md_text)
    if not pages:
        raise RuntimeError("No pages rendered")
    first, *rest = pages
    first.save(OUTPUT, "PDF", resolution=150.0, save_all=True, append_images=rest)
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
