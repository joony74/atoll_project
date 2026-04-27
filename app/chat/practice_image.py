from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - optional runtime dependency guard
    Image = None
    ImageDraw = None
    ImageFont = None


FONT_CANDIDATES = (
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
)


def _font(size: int, *, bold: bool = False) -> Any:
    if ImageFont is None:
        return None
    for path in FONT_CANDIDATES:
        if not Path(path).exists():
            continue
        try:
            return ImageFont.truetype(path, size=size, index=1 if bold and path.endswith(".ttc") else 0)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap_text(draw: Any, text: str, font: Any, max_width: int) -> list[str]:
    words = list(str(text or "").strip())
    lines: list[str] = []
    current = ""
    for char in words:
        candidate = current + char
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if current and bbox[2] - bbox[0] > max_width:
            lines.append(current.rstrip())
            current = char
        else:
            current = candidate
    if current.strip():
        lines.append(current.rstrip())
    return lines or [""]


def _draw_centered_text(draw: Any, box: tuple[int, int, int, int], text: str, font: Any, fill: str) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = box[0] + ((box[2] - box[0]) - width) / 2
    y = box[1] + ((box[3] - box[1]) - height) / 2 - 2
    draw.text((x, y), text, font=font, fill=fill)


def _draw_blank_box(draw: Any, box: tuple[int, int, int, int], font: Any, label: str = "") -> None:
    draw.rounded_rectangle(box, radius=12, outline="#94a3b8", width=3, fill="#ffffff")
    if label:
        _draw_centered_text(draw, box, label, font, "#111827")


def _draw_circle(draw: Any, center: tuple[int, int], radius: int, text: str, font: Any) -> None:
    x, y = center
    box = (x - radius, y - radius, x + radius, y + radius)
    draw.ellipse(box, outline="#334155", width=3, fill="#f8fafc")
    _draw_centered_text(draw, box, text, font, "#111827")


def _numbers(problem_text: str) -> list[int]:
    return [int(item) for item in re.findall(r"-?\d+", str(problem_text or ""))]


def _has_final_sound(value: int) -> bool:
    return abs(int(value)) % 10 in {0, 1, 3, 6, 7, 8}


def _object_particle(value: int) -> str:
    return "을" if _has_final_sound(value) else "를"


def _draw_header(draw: Any, problem_text: str, title_font: Any, body_font: Any) -> int:
    draw.text((34, 24), "코코 연습 문제", font=title_font, fill="#f97316")
    y = 82
    for line in _wrap_text(draw, problem_text, body_font, 640)[:3]:
        draw.text((34, y), line, font=body_font, fill="#111827")
        y += 38
    return max(y + 14, 164)


def _draw_compose_template(draw: Any, problem_text: str, fonts: dict[str, Any]) -> None:
    nums = _numbers(problem_text)
    first, second = (nums + [8, 7])[:2]
    top = _draw_header(draw, problem_text, fonts["title"], fonts["body"])
    cy = top + 40
    _draw_circle(draw, (92, cy), 34, str(first), fonts["large"])
    draw.text((134, cy - 20), "+", font=fonts["large"], fill="#334155")
    _draw_circle(draw, (198, cy), 34, str(second), fonts["large"])
    draw.text((244, cy - 20), "=", font=fonts["large"], fill="#334155")
    _draw_blank_box(draw, (310, cy - 34, 430, cy + 34), fonts["large"])
    draw.text((470, cy - 15), "먼저 모아요", font=fonts["small"], fill="#475569")

    cy2 = cy + 118
    _draw_blank_box(draw, (76, cy2 - 34, 196, cy2 + 34), fonts["large"])
    draw.text((232, cy2 - 20), "=", font=fonts["large"], fill="#334155")
    _draw_blank_box(draw, (292, cy2 - 34, 412, cy2 + 34), fonts["large"], "10")
    draw.text((444, cy2 - 20), "+", font=fonts["large"], fill="#334155")
    _draw_blank_box(draw, (500, cy2 - 34, 620, cy2 + 34), fonts["large"])
    draw.text((76, cy2 + 52), "모은 수를 10과 나머지로 가르세요.", font=fonts["small"], fill="#64748b")


def _draw_addition_template(draw: Any, problem_text: str, fonts: dict[str, Any]) -> None:
    nums = _numbers(problem_text)
    left, right, split_first = (nums + [8, 5, 2])[:3]
    top = _draw_header(draw, problem_text, fonts["title"], fonts["body"])
    cy = top + 42
    draw.text((70, cy - 24), f"{left} + {right} =", font=fonts["large"], fill="#111827")
    _draw_blank_box(draw, (255, cy - 34, 380, cy + 34), fonts["large"])
    draw.text((70, cy + 74), f"{right}{_object_particle(right)} 가르기", font=fonts["small"], fill="#475569")
    _draw_blank_box(draw, (250, cy + 54, 350, cy + 116), fonts["body"], str(split_first))
    draw.text((374, cy + 64), "+", font=fonts["large"], fill="#334155")
    _draw_blank_box(draw, (428, cy + 54, 528, cy + 116), fonts["body"])
    draw.text((70, cy + 150), f"{left}에 {split_first}{_object_particle(split_first)} 더해 10을 먼저 만드세요.", font=fonts["small"], fill="#64748b")


def _draw_subtraction_template(draw: Any, problem_text: str, fonts: dict[str, Any]) -> None:
    nums = _numbers(problem_text)
    left, right, split_first = (nums + [14, 6, 4])[:3]
    top = _draw_header(draw, problem_text, fonts["title"], fonts["body"])
    cy = top + 42
    draw.text((70, cy - 24), f"{left} - {right} =", font=fonts["large"], fill="#111827")
    _draw_blank_box(draw, (255, cy - 34, 380, cy + 34), fonts["large"])
    draw.text((70, cy + 74), f"{right}{_object_particle(right)} 가르기", font=fonts["small"], fill="#475569")
    _draw_blank_box(draw, (250, cy + 54, 350, cy + 116), fonts["body"], str(split_first))
    draw.text((374, cy + 64), "+", font=fonts["large"], fill="#334155")
    _draw_blank_box(draw, (428, cy + 54, 528, cy + 116), fonts["body"])
    draw.text((70, cy + 150), f"{left}에서 {split_first}{_object_particle(split_first)} 먼저 빼서 10을 만드세요.", font=fonts["small"], fill="#64748b")


def render_practice_problem_image(rule_id: str, problem_text: str, output_dir: str | Path, *, key: str = "") -> str:
    if Image is None or ImageDraw is None:
        return ""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(f"{rule_id}\n{problem_text}\n{key}".encode("utf-8")).hexdigest()[:12]
    path = output / f"practice_{digest}.png"
    if path.exists():
        return str(path)

    image = Image.new("RGB", (720, 460), "#ffffff")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((10, 10, 710, 450), radius=24, outline="#cbd5e1", width=2, fill="#ffffff")
    fonts = {
        "title": _font(32, bold=True),
        "body": _font(27),
        "large": _font(36, bold=True),
        "small": _font(21),
    }

    if rule_id == "generic_make_ten_compose_decompose":
        _draw_compose_template(draw, problem_text, fonts)
    elif rule_id == "generic_make_ten_addition_decomposition":
        _draw_addition_template(draw, problem_text, fonts)
    elif rule_id == "generic_make_ten_subtraction_decomposition":
        _draw_subtraction_template(draw, problem_text, fonts)
    else:
        _draw_header(draw, problem_text, fonts["title"], fonts["body"])

    image.save(path, format="PNG")
    return str(path)
