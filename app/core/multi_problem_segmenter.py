from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class ProblemRegion:
    index: int
    label: str
    bbox: tuple[int, int, int, int]
    column: str


@dataclass(frozen=True)
class ProblemCardImage:
    index: int
    label: str
    path: str
    bbox: tuple[int, int, int, int]


def _orange_mask(image: Image.Image) -> list[list[bool]]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()
    mask: list[list[bool]] = [[False] * width for _ in range(height)]
    for y in range(height):
        row = mask[y]
        for x in range(width):
            r, g, b = pixels[x, y]
            if r >= 190 and 55 <= g <= 170 and b <= 115 and r - g >= 45 and g - b >= 10:
                row[x] = True
    return mask


def _connected_components(mask: list[list[bool]]) -> list[tuple[int, int, int, int, int]]:
    if not mask:
        return []
    height = len(mask)
    width = len(mask[0])
    seen = [[False] * width for _ in range(height)]
    components: list[tuple[int, int, int, int, int]] = []
    for y in range(height):
        for x in range(width):
            if not mask[y][x] or seen[y][x]:
                continue
            stack = [(x, y)]
            seen[y][x] = True
            min_x = max_x = x
            min_y = max_y = y
            area = 0
            while stack:
                cx, cy = stack.pop()
                area += 1
                min_x = min(min_x, cx)
                max_x = max(max_x, cx)
                min_y = min(min_y, cy)
                max_y = max(max_y, cy)
                for nx in (cx - 1, cx, cx + 1):
                    for ny in (cy - 1, cy, cy + 1):
                        if nx < 0 or ny < 0 or nx >= width or ny >= height:
                            continue
                        if seen[ny][nx] or not mask[ny][nx]:
                            continue
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            components.append((min_x, min_y, max_x + 1, max_y + 1, area))
    return components


def _question_marker_components(image: Image.Image) -> list[tuple[int, int, int, int]]:
    width, height = image.size
    components = _connected_components(_orange_mask(image))
    markers: list[tuple[int, int, int, int]] = []
    for x0, y0, x1, y1, area in components:
        box_width = x1 - x0
        box_height = y1 - y0
        if area < 18 or box_width < 4 or box_height < 12:
            continue
        if area > 2600 or box_width > width * 0.12 or box_height > height * 0.08:
            continue
        markers.append((x0, y0, x1, y1))
    return markers


def _merge_marker_glyphs(components: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
    glyphs = sorted(components, key=lambda box: ((box[1] + box[3]) / 2, box[0]))
    merged: list[tuple[int, int, int, int]] = []
    for box in glyphs:
        x0, y0, x1, y1 = box
        cy = (y0 + y1) / 2
        joined = False
        for index, existing in enumerate(merged):
            ex0, ey0, ex1, ey1 = existing
            ecy = (ey0 + ey1) / 2
            same_line = abs(cy - ecy) <= max(18, (ey1 - ey0) * 0.75)
            close = 0 <= x0 - ex1 <= 44 or 0 <= ex0 - x1 <= 44
            if same_line and close:
                merged[index] = (min(ex0, x0), min(ey0, y0), max(ex1, x1), max(ey1, y1))
                joined = True
                break
        if not joined:
            merged.append(box)
    return sorted(merged, key=lambda box: (box[1], box[0]))


def _millimeter_margin_px(image: Image.Image, millimeters: float = 5.0) -> int:
    dpi = image.info.get("dpi") if hasattr(image, "info") else None
    dpi_x = 180.0
    if isinstance(dpi, tuple) and dpi:
        try:
            dpi_x = float(dpi[0])
        except Exception:
            dpi_x = 180.0
    return max(24, min(64, int(round(dpi_x * millimeters / 25.4))))


def _has_prompt_ink_right(image: Image.Image, marker_box: tuple[int, int, int, int], column_right: int) -> bool:
    gray = image.convert("L")
    pixels = gray.load()
    width, height = image.size
    x0 = min(width, marker_box[2] + 8)
    x1 = min(width, max(x0, column_right - 18))
    y0 = max(0, marker_box[1] - 8)
    y1 = min(height, marker_box[3] + 30)
    dark_count = 0
    dark_columns: set[int] = set()
    for y in range(y0, y1):
        for x in range(x0, x1):
            if pixels[x, y] < 105:
                dark_count += 1
                dark_columns.add(x)
    return dark_count >= 90 and len(dark_columns) >= 24


def detect_problem_regions(image_path: str | Path, *, minimum_regions: int = 2) -> list[ProblemRegion]:
    opened = Image.open(image_path)
    margin_y = _millimeter_margin_px(opened, 5.0)
    image = opened.convert("RGB")
    width, height = image.size
    markers = _merge_marker_glyphs(_question_marker_components(image))
    markers = [
        box
        for box in markers
        if (box[0] < width * 0.18 or (width * 0.46 < box[0] < width * 0.66))
        and box[2] - box[0] <= max(72, width * 0.06)
        and box[3] - box[1] <= max(46, height * 0.04)
    ]
    if len(markers) < minimum_regions:
        return []

    split_x = width // 2
    marker_x_margin = max(72, min(96, int(width * 0.07)))
    left = [box for box in markers if (box[0] + box[2]) / 2 < split_x]
    right = [box for box in markers if (box[0] + box[2]) / 2 >= split_x]
    left = [box for box in left if box[0] <= marker_x_margin]
    right = [box for box in right if split_x - 20 <= box[0] <= split_x + marker_x_margin]
    left = [box for box in left if _has_prompt_ink_right(image, box, split_x)]
    right = [box for box in right if _has_prompt_ink_right(image, box, width)]
    columns = [("left", 0, split_x, sorted(left, key=lambda box: box[1])), ("right", split_x, width, sorted(right, key=lambda box: box[1]))]

    regions: list[ProblemRegion] = []
    for column_name, x0, x1, boxes in columns:
        if not boxes:
            continue
        for index, box in enumerate(boxes):
            _, marker_top, _, marker_bottom = box
            if index == 0:
                y0 = 0
            else:
                y0 = max(0, marker_top - margin_y)
            if index + 1 < len(boxes):
                next_top = boxes[index + 1][1]
                y1 = min(height, max(marker_bottom + margin_y * 2, next_top - margin_y))
            else:
                y1 = height
            if y1 - y0 < 120:
                continue
            pad_x = 14
            bbox = (max(0, x0 - pad_x), y0, min(width, x1 + pad_x), y1)
            regions.append(
                ProblemRegion(
                    index=0,
                    label="",
                    bbox=bbox,
                    column=column_name,
                )
            )

    regions = sorted(regions, key=lambda region: (0 if region.column == "left" else 1, region.bbox[1], region.bbox[0]))
    normalized: list[ProblemRegion] = []
    for index, region in enumerate(regions, start=1):
        normalized.append(
            ProblemRegion(
                index=index,
                label=f"{index:02d}",
                bbox=region.bbox,
                column=region.column,
            )
        )
    return normalized if len(normalized) >= minimum_regions else []


def save_problem_card_images(
    image_path: str | Path,
    output_dir: str | Path,
    *,
    base_name: str,
    minimum_regions: int = 2,
) -> list[ProblemCardImage]:
    source = Image.open(image_path).convert("RGB")
    regions = detect_problem_regions(image_path, minimum_regions=minimum_regions)
    if not regions:
        return []
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    cards: list[ProblemCardImage] = []
    safe_base = "".join(ch if ch.isalnum() or ch in "._-가-힣" else "_" for ch in base_name).strip("._") or "problem"
    for region in regions:
        crop = source.crop(region.bbox)
        path = output / f"{safe_base}_문항{region.label}.png"
        crop.save(path, optimize=True)
        cards.append(
            ProblemCardImage(
                index=region.index,
                label=region.label,
                path=str(path),
                bbox=region.bbox,
            )
        )
    return cards
