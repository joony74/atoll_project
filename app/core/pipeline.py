from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import ast
import math
import tempfile
from fractions import Fraction
from html import unescape
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

try:
    import sympy as sp
except Exception:
    sp = None

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except Exception:
    Image = None
    ImageDraw = None
    ImageFont = None
    ImageOps = None

try:
    import numpy as np
except Exception:
    np = None

from app.engines.explainer.korean_tutor_explainer import generate_korean_tutor_response
from app.engines.parser.math_candidate_ranker import extract_expression_texts, select_problem_statement
from app.engines.parser.math_ocr_normalizer import (
    clean_visible_math_text,
    is_metadata_or_choice_noise_line,
    normalize_ocr_math_text,
    ocr_noise_score,
)
from app.engines.parser.school_math_taxonomy import classify_school_math_topic
from app.engines.router.solver_router import route_solver
from app.engines.solver import arithmetic_solver, trig_solver
from app.engines.validator.answer_validator import validate_answer
from app.core.config import settings
from app.engines.vision.ollama_vision import OllamaVisionClient
from app.models.problem_schema import ProblemSchema
from app.models.solve_result import SolveResult
from app.utils.choice_parser import parse_choices
from app.utils.math_patterns import detect_math_signal_score
from app.utils.text_normalizer import normalize_math_text, split_exam_metadata


_QUESTION_SUFFIX_RE = re.compile(r"(의\s*값은\??|값은\??|구하시오\.?|옳은\s*것은\??|정답[은: ]?)", re.IGNORECASE)
_HTML_SUP_RE = re.compile(r"<sup>\s*([^<]+?)\s*</sup>", re.IGNORECASE)
_HTML_SUB_RE = re.compile(r"<sub>\s*([^<]+?)\s*</sub>", re.IGNORECASE)
_INLINE_MULTIPLY_RE = re.compile(r"(?<=\d|\))\s*[xX]\s*(?=\d|\()")
_SQRT_CUBERT_PAIR_RE = re.compile(r"(\d+)\s*[\*\?]\s*[xX*]\s*(\d+)\s*[°º]")
_SQRT_MARKER_RE = re.compile(r"(\d+)\s*[\*\?](?!\*)")
_CBRT_MARKER_RE = re.compile(r"(\d+)\s*[°º]")
_GRID_FONT_CANDIDATES = (
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
)
_GRID_DIGIT_TEMPLATES: dict[str, Any] | None = None


def _grid_digit_font() -> Any | None:
    if ImageFont is None:
        return None
    for path in _GRID_FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, 36)
        except Exception:
            continue
    return None


def _dark_bbox(image: Any, threshold: int = 120) -> tuple[int, int, int, int] | None:
    if np is None:
        return None
    array = np.array(image.convert("L"))
    ys, xs = np.where(array < threshold)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)


def _grid_templates() -> dict[str, Any]:
    global _GRID_DIGIT_TEMPLATES
    if _GRID_DIGIT_TEMPLATES is not None:
        return _GRID_DIGIT_TEMPLATES
    templates: dict[str, Any] = {}
    if Image is None or ImageDraw is None:
        _GRID_DIGIT_TEMPLATES = templates
        return templates
    font = _grid_digit_font()
    if font is None:
        _GRID_DIGIT_TEMPLATES = templates
        return templates
    for value in range(-99, 151):
        text = str(value)
        canvas = Image.new("L", (220, 90), 255)
        ImageDraw.Draw(canvas).text((0, 0), text, font=font, fill=0)
        bbox = _dark_bbox(canvas)
        if bbox:
            templates[text] = canvas.crop(bbox)
    _GRID_DIGIT_TEMPLATES = templates
    return templates


def _recognize_grid_number(cell: Any) -> str | None:
    if Image is None or np is None:
        return None
    bbox = _dark_bbox(cell)
    if not bbox:
        return None
    crop = cell.crop(bbox).convert("L")
    templates = _grid_templates()
    if not templates:
        return None
    best_score = 9.0
    best_text: str | None = None
    for text, template in templates.items():
        width = max(crop.width, template.width)
        height = max(crop.height, template.height)
        candidate = Image.new("L", (width, height), 255)
        rendered = Image.new("L", (width, height), 255)
        candidate.paste(crop, (0, 0))
        rendered.paste(template, (0, 0))
        candidate_array = np.array(candidate).astype(float)
        rendered_array = np.array(rendered).astype(float)
        mse = float(((candidate_array - rendered_array) ** 2).mean() / 65025)
        dimension_penalty = abs(crop.width - template.width) / max(width, 1) + abs(crop.height - template.height) / max(height, 1)
        score = mse + 0.12 * dimension_penalty
        if score < best_score:
            best_score = score
            best_text = text
    return best_text if best_text is not None and best_score <= 0.06 else None


def _extract_grid_table_text(image_path: str) -> str:
    if Image is None or np is None:
        return ""
    try:
        image = Image.open(image_path).convert("L")
    except Exception:
        return ""
    dark = np.array(image) < 190
    row_counts = dark.sum(axis=1)
    horizontal_lines: list[int] = []
    in_run = False
    start = 0
    for index, count in enumerate(row_counts):
        if count > image.width * 0.36 and not in_run:
            start = index
            in_run = True
        if in_run and (count <= image.width * 0.36 or index == len(row_counts) - 1):
            end = index
            if end - start <= 6:
                horizontal_lines.append((start + end) // 2)
            in_run = False
    if len(horizontal_lines) < 2:
        return ""
    y_start, y_end = horizontal_lines[0], horizontal_lines[-1]
    span = max(y_end - y_start, 1)
    candidate_columns: list[int] = []
    for x in range(dark.shape[1]):
        run = 0
        best = 0
        for value in dark[max(0, y_start - 5) : min(dark.shape[0], y_end + 5), x]:
            if value:
                run += 1
                best = max(best, run)
            else:
                run = 0
        if best > span * 0.7:
            candidate_columns.append(x)
    column_groups: list[list[int]] = []
    for x in candidate_columns:
        if not column_groups or x > column_groups[-1][-1] + 1:
            column_groups.append([x])
        else:
            column_groups[-1].append(x)
    vertical_lines = [sum(group) // len(group) for group in column_groups if len(group) >= 2]
    if len(vertical_lines) < 2:
        return ""

    rows: list[str] = []
    color_image = Image.open(image_path).convert("RGB")
    for row_index in range(len(horizontal_lines) - 1):
        values: list[str] = []
        for col_index in range(len(vertical_lines) - 1):
            box = (
                vertical_lines[col_index] + 8,
                horizontal_lines[row_index] + 8,
                vertical_lines[col_index + 1] - 8,
                horizontal_lines[row_index + 1] - 8,
            )
            if box[2] <= box[0] or box[3] <= box[1]:
                continue
            value = _recognize_grid_number(color_image.crop(box))
            if value is not None:
                values.append(value)
        if len(values) >= 2:
            rows.append(f"table_row_{row_index + 1} " + " ".join(values))
    return "\n".join(rows)


def _run_tesseract_ocr(image_path: str) -> dict[str, Any]:
    binary = os.getenv("COCO_TESSERACT_BIN", "/opt/homebrew/bin/tesseract")
    if not Path(binary).exists():
        return {"engine": "tesseract", "available": False, "text": "", "confidence": 0.0, "error": "missing_binary"}

    def _run_single_pass(source_path: str, variant: str, psm: str = "6") -> dict[str, Any]:
        try:
            proc = subprocess.run(
                [binary, source_path, "stdout", "-l", "kor+eng", "--psm", psm],
                capture_output=True,
                text=True,
                timeout=20,
                check=True,
            )
            text = normalize_math_text(proc.stdout or "")
            math_score = detect_math_signal_score(text)
            confidence = min(
                0.8,
                0.48
                + min(math_score, 0.22)
                + (0.06 if variant == "preprocessed" and text else 0.0)
                + (0.04 if psm == "4" and text else 0.0),
            )
            return {
                "engine": "tesseract",
                "variant": variant,
                "psm": psm,
                "available": bool(text),
                "text": text,
                "confidence": confidence if text else 0.0,
            }
        except Exception as exc:
            return {
                "engine": "tesseract",
                "variant": variant,
                "psm": psm,
                "available": False,
                "text": "",
                "confidence": 0.0,
                "error": str(exc),
            }

    temp_paths: list[Path] = []
    passes: list[dict[str, Any]] = []
    try:
        original = _run_single_pass(image_path, "original", psm="6")
        passes.append(original)
        original_text = str(original.get("text") or "")
        if (
            "표" in original_text
            or ("일차함수" in original_text and "일부" in original_text)
            or detect_math_signal_score(original_text) < 0.22
        ):
            passes.append(_run_single_pass(image_path, "original_table", psm="4"))

        if Image is not None and ImageOps is not None:
            try:
                image = Image.open(image_path).convert("L")
                image = ImageOps.autocontrast(image)
                image = image.resize((image.width * 4, image.height * 4))
                image = ImageOps.invert(image)
                image = image.point(lambda x: 255 if x > 55 else 0)
                image = ImageOps.invert(image)
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
                    temp_path = Path(handle.name)
                image.save(temp_path)
                temp_paths.append(temp_path)
                passes.append(_run_single_pass(str(temp_path), "preprocessed", psm="6"))
            except Exception as exc:
                passes.append(
                    {
                        "engine": "tesseract",
                        "variant": "preprocessed",
                        "available": False,
                        "text": "",
                        "confidence": 0.0,
                        "error": str(exc),
                    }
                )

        grid_text = _extract_grid_table_text(image_path)
        if grid_text:
            passes.append(
                {
                    "engine": "grid_table_digit_reader",
                    "variant": "grid_table",
                    "psm": "grid",
                    "available": True,
                    "text": grid_text,
                    "confidence": 0.72,
                }
            )

        def _rank_ocr_pass(item: dict[str, Any]) -> tuple[float, int, float, int]:
            text = str(item.get("text") or "")
            digit_count = len(re.findall(r"[-+]?\d+", text))
            table_bonus = 0.0
            if str(item.get("psm") or "") == "4" and re.search(r"(?:개수|쪽수|\by\b).*\d", text, flags=re.IGNORECASE):
                table_bonus += 0.32
            return (
                detect_math_signal_score(text) + table_bonus,
                digit_count,
                item.get("confidence") or 0.0,
                len(text),
            )

        ranked = sorted(
            passes,
            key=_rank_ocr_pass,
            reverse=True,
        )
        best = ranked[0] if ranked else {"engine": "tesseract", "available": False, "text": "", "confidence": 0.0}
        return {
            "engine": "tesseract",
            "variant": best.get("variant") or "original",
            "available": bool(best.get("text")),
            "text": str(best.get("text") or ""),
            "confidence": float(best.get("confidence") or 0.0),
            "passes": passes,
            **({"error": best.get("error")} if best.get("error") else {}),
        }
    finally:
        for temp_path in temp_paths:
            temp_path.unlink(missing_ok=True)


def _normalize_repaired_text(text: str) -> str:
    normalized = unescape(str(text or ""))
    normalized = normalized.replace("$$", "")
    normalized = _HTML_SUP_RE.sub(r"^(\1)", normalized)
    normalized = _HTML_SUB_RE.sub(r"_(\1)", normalized)
    normalized = normalized.replace("\\(", "(").replace("\\)", ")")
    normalized = normalized.replace("\\[", "").replace("\\]", "")
    normalized = re.sub(r"\\frac\(([^()]+)\)\(([^()]+)\)", r"(\1)/(\2)", normalized)
    normalized = normalized.replace("\\cdot", "*").replace("\\times", "*")
    normalized = normalized.replace("\\geq", ">=").replace("\\leq", "<=")
    normalized = normalized.replace("\\log", "log")
    normalized = normalized.replace("\\alpha", "alpha").replace("\\circ", "°")
    normalized = normalized.replace("\\ ", " ")
    normalized = re.sub(r"\(\(([^()]+)\)\)", r"(\1)", normalized)
    return normalize_ocr_math_text(normalized)


def _extract_anchor_numbers(text: str) -> list[str]:
    anchors: list[str] = []
    for token in re.findall(r"\d+", str(text or "")):
        if len(token) >= 4 and token.startswith(("19", "20")):
            continue
        if token.startswith("0") and len(token) > 1:
            continue
        if len(token) <= 1:
            continue
        if token not in anchors:
            anchors.append(token)
    return anchors[:12]


def _anchor_alignment_ratio(raw_text: str, candidate_text: str) -> float:
    source_anchors = _extract_anchor_numbers(raw_text)
    if not source_anchors:
        return 1.0
    candidate_anchors = set(_extract_anchor_numbers(candidate_text))
    matched = sum(1 for token in source_anchors if token in candidate_anchors)
    return matched / max(len(source_anchors), 1)


def _run_text_ocr_repair(raw_text: str) -> dict[str, Any]:
    if not settings.ocr_repair_enabled:
        return {
            "engine": "ollama_text_repair",
            "available": False,
            "accepted": False,
            "text": "",
            "confidence": 0.0,
            "skipped": True,
            "reason": "disabled_by_default",
        }
    cleaned = normalize_math_text(raw_text)
    if not cleaned or detect_math_signal_score(cleaned) < 0.15 or len(cleaned) < 70:
        return {"engine": "ollama_text_repair", "available": False, "accepted": False, "text": "", "confidence": 0.0}

    prompt = (
        "다음은 한국 수학 문제 이미지에서 OCR로 잘못 읽힌 텍스트다. "
        "실제 문제 문장과 보기만 복원해라. "
        "매우 중요: OCR에 보인 숫자와 수식 단서를 최대한 보존하고, 새로운 숫자를 함부로 만들지 마라. "
        "`x`는 곱셈 기호일 수 있고, `*`, `?`, `°`는 위첨자나 루트가 깨진 표기일 수 있다. "
        "문제 번호, 연도, 잡문자는 제거해도 되지만 정답 풀이와 해설은 금지다.\n\n"
        f"OCR:\n{cleaned}"
    )
    body = json.dumps(
        {
            "model": settings.ollama_text_model,
            "stream": False,
            "keep_alive": settings.ocr_repair_keep_alive,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "너는 OCR로 깨진 한국 수학 문제를 보수적으로 복원하는 도우미다. "
                        "숫자와 보기 정보를 최대한 보존하고, 문제 문장과 보기만 출력한다."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "options": {
                "num_ctx": settings.ollama_num_ctx,
            },
        },
        ensure_ascii=False,
    ).encode("utf-8")

    request = Request(
        f"{settings.ollama_base_url.rstrip('/')}/api/chat",
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings.ocr_repair_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = _normalize_repaired_text(((payload or {}).get("message") or {}).get("content") or "")
        signal = detect_math_signal_score(content)
        alignment_ratio = _anchor_alignment_ratio(cleaned, content)
        accepted = bool(content) and signal >= 0.18 and alignment_ratio >= 0.6
        confidence = min(0.74, 0.42 + min(signal, 0.2) + (alignment_ratio * 0.16))
        return {
            "engine": "ollama_text_repair",
            "available": bool(content),
            "accepted": accepted,
            "text": content if accepted else "",
            "candidate_text": content,
            "confidence": confidence if accepted else max(0.0, confidence - 0.12),
            "alignment_ratio": alignment_ratio,
            "raw": payload,
        }
    except Exception as exc:
        return {
            "engine": "ollama_text_repair",
            "available": False,
            "accepted": False,
            "text": "",
            "confidence": 0.0,
            "error": str(exc),
        }


def _select_best_text(image_path: str) -> tuple[str, dict[str, Any]]:
    tesseract_result = _run_tesseract_ocr(image_path)
    if settings.vision_enabled:
        vision_result = OllamaVisionClient().interpret_math_image(image_path)
    else:
        vision_result = {
            "engine": "ollama_vision",
            "available": False,
            "text": "",
            "confidence": 0.0,
            "skipped": True,
            "reason": "disabled_by_default",
        }
    text_repair_result = _run_text_ocr_repair(tesseract_result.get("text") or "")
    candidates = [tesseract_result, vision_result]
    ranked = sorted(
        candidates,
        key=lambda item: (
            detect_math_signal_score(item.get("text") or ""),
            item.get("confidence") or 0.0,
            len(item.get("text") or ""),
        ),
        reverse=True,
    )
    best = ranked[0] if ranked else {"text": ""}

    selected_text = str(best.get("text") or "")
    # Tesseract passes often recover complementary fragments: one pass may read
    # the formula while another keeps the table row or f(5) target. Merge short,
    # math-bearing lines instead of throwing those clues away.
    merged_lines: list[str] = []
    seen_lines: set[str] = set()
    for candidate_text in [
        selected_text,
        *(str(item.get("text") or "") for item in tesseract_result.get("passes", [])),
    ]:
        for raw_line in str(candidate_text or "").splitlines():
            line = normalize_math_text(raw_line).strip()
            if not line:
                continue
            compact = re.sub(r"\s+", "", line)
            if compact in seen_lines:
                continue
            if len(line) > 140 or ocr_noise_score(line) >= 6:
                continue
            if detect_math_signal_score(line) < 0.08 and not re.search(r"\d", line) and not re.search(
                r"(표|함수|방정식|구하시오|값|확률|평균|넓이|시속|연필|상자|쪽수|개수|인원|등차|수열|첫째항|공차|로그|자료)",
                line,
            ):
                continue
            merged_lines.append(line)
            seen_lines.add(compact)
            if len(merged_lines) >= 14:
                break
        if len(merged_lines) >= 14:
            break

    merged_text = normalize_math_text("\n".join(merged_lines)) if merged_lines else selected_text
    return merged_text, {
        "tesseract": tesseract_result,
        "vision": vision_result,
        "text_repair": text_repair_result,
        "selected_engine": best.get("engine") or "unknown",
    }


def _clean_candidate_text(text: str) -> str:
    return clean_visible_math_text(_normalize_repaired_text(text))


def _line_noise_score(text: str) -> int:
    return ocr_noise_score(text)


def _is_metadata_or_choice_noise(line: str) -> bool:
    return is_metadata_or_choice_noise_line(line, math_score=detect_math_signal_score(line))


def _detect_math_topic(text: str, expressions: list[str]) -> str:
    topic, _ = classify_school_math_topic(text, expressions)
    return topic


def _extract_expression_candidates(text: str) -> list[str]:
    return extract_expression_texts(text, limit=5)


def _normalize_semantic_text(text: str) -> str:
    normalized = clean_visible_math_text(text)
    normalized = normalized.replace("Ｌ", "니다")
    normalized = normalized.replace("㎞", "km")
    normalized = normalized.replace("Ｏ", "0").replace("Ｏ", "0")
    normalized = re.sub(r"\bO[FS]\b", "0", normalized, flags=re.IGNORECASE)
    normalized = normalized.replace("ㄱ1", "-1")
    normalized = normalized.replace("--1", "-1")
    normalized = normalized.replace("ㅜ", "")
    normalized = normalized.replace("ㅋ", "x")
    normalized = normalized.replace("[(", "f(").replace("『(", "f(")
    normalized = normalized.replace("['(", "f'(").replace("『'(", "f'(")
    normalized = re.sub(r"(?<!\S)/\s*=", "y =", normalized)
    normalized = re.sub(r">\s*[*xX]", "x", normalized)
    normalized = normalized.replace("”", "*").replace("“", "*")
    normalized = re.sub(r"([+-])\s*0\s*[7>]\s*[*xX]?", r"\g<1>0x", normalized)
    normalized = re.sub(r"(\d+)%\s*\+/\s*(\d+)", r"\1x+\2", normalized)
    normalized = re.sub(r"(\d+)\*\s*\+\s*(\d+)x(?=\s*=)", r"\1x+\2", normalized)
    normalized = re.sub(r"(?<=\d)<\s*\^\s*2", "x^2", normalized)
    normalized = re.sub(r"(\d+)\s*[xX]\s*2(?=\s*[!|]?\s*때)", r"\1x", normalized)
    normalized = re.sub(r"([xX*])\s*=\s*([-+]?\d)2(?=\s*(?:때|일|2[|!]))", r"x = \2", normalized)
    normalized = re.sub(r"([xX*])\s*=\s*OF\b", "x = 0", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"([xX*])\s*=\s*OS\b", "x = 0", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"([xX])[*\"']\s*2", r"\1^2", normalized)
    normalized = re.sub(r"([xX])\s*[°º]\s*2", r"\1^2", normalized)
    normalized = re.sub(r"(?<![a-zA-Z])[*×]\s*2", "x^2", normalized)
    normalized = re.sub(r"(\d)Xx", r"\1x", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _infer_semantic_expression_candidates(text: str) -> list[str]:
    source = _normalize_semantic_text(text)
    compact = source.replace(" ", "")
    expressions: list[str] = []

    def _append(expr: str) -> None:
        cleaned = str(expr or "").replace(" ", "").strip(" .,:;")
        if cleaned and cleaned not in expressions:
            expressions.append(cleaned)

    numbers = [int(item) for item in re.findall(r"(?<![a-zA-Z])[-+]?\d+", source)]

    def _row_numbers(label_pattern: str) -> list[int]:
        matches = list(
            re.finditer(
                label_pattern + r"[\s\[\]|:;,.=]{0,18}((?:[-+]?\d+[\s\[\]|:;,.=]+){1,8}[-+]?\d+)",
                source,
                flags=re.IGNORECASE,
            )
        )
        if not matches:
            return []
        match = max(matches, key=lambda item: len(re.findall(r"[-+]?\d+", item.group(1))))
        values = [int(item) for item in re.findall(r"[-+]?\d+", match.group(1))]
        if len(values) > 4 and ("\\by" in label_pattern or "yO" in label_pattern or "인원" in label_pattern):
            values = values[:4]
        return values

    count_row = _row_numbers(r"(?:개수|읽은\s*쪽수|인원|yO\]|HOA\s*yO\])")
    y_row = _row_numbers(r"(?:\by\b|yo|ㄱ)")
    x_row = _row_numbers(r"(?:\bx\b|[*])")
    if not x_row:
        x_row = _row_numbers(r"(?:[*]|x2\]\s*값은\?\s*[*])")
    grid_rows = [
        [int(item) for item in re.findall(r"[-+]?\d+", match.group(1))]
        for match in re.finditer(r"table_row_\d+\s+([-\d\s]+)", source)
    ]
    grid_rows = [row for row in grid_rows if len(row) >= 2]
    if grid_rows:
        count_row = grid_rows[-1]
        if len(grid_rows) >= 2:
            x_row = grid_rows[0]
            y_row = grid_rows[-1]
    if "표" in source or count_row or y_row:
        target_x_match = re.search(r"(?:x|[*])\s*=\s*([-+]?\d+)", source, flags=re.IGNORECASE)
        target_y_match = re.search(r"(?:y\s*가|y7|#가|(?<![a-zA-Z])가)\s*([-+]?\d+)", source, flags=re.IGNORECASE)
        if y_row and target_x_match:
            target_x = int(target_x_match.group(1))
            if x_row and len(x_row) == len(y_row) and target_x in x_row:
                _append(f"answer={y_row[x_row.index(target_x)]}")
            elif x_row and len(y_row) == len(x_row) - 1 and target_x in x_row:
                target_index = x_row.index(target_x)
                if target_index > 0:
                    _append(f"answer={y_row[target_index - 1]}")
        if y_row and target_y_match:
            target_y = int(target_y_match.group(1))
            if x_row and len(x_row) == len(y_row) and target_y in y_row:
                _append(f"answer={x_row[y_row.index(target_y)]}")
        is_difference_table = bool(re.search(r"차(?:를|이|를\s*구|를\s*구하|$)", source) or "최댓값" in source or "가장 많은" in source)
        if is_difference_table:
            def _repair_dropped_tens(values: list[int]) -> list[int]:
                if any(abs(item) >= 10 for item in values):
                    return [11 if item == 1 else 10 if item == 0 else item for item in values]
                return values

            count_row = _repair_dropped_tens(count_row)
            y_row = _repair_dropped_tens(y_row)
        if count_row:
            if is_difference_table and len(count_row) >= 2:
                _append(f"{max(count_row)}-{min(count_row)}")
            elif "2배" in source:
                _append(f"({'+'.join(str(item) for item in count_row)})*2")
            elif "합" in source or "모두" in source or "구하시오" in source:
                _append("+".join(str(item) for item in count_row))
        if is_difference_table:
            values = y_row or count_row
            if len(values) >= 2:
                _append(f"{max(values)}-{min(values)}")

    if "자루" in source and len(numbers) >= 2:
        mixed_pencil_matches = re.findall(r"연필이\s*(\d+)\s*자루\s*있고\s*(\d+)\s*자루를.*?그중\s*(\d+)\s*자루", source)
        pencil_matches = re.findall(r"연필이\s*(\d+)\s*자루.*?그중\s*(\d+)\s*자루", source)
        if mixed_pencil_matches:
            first, added, used = mixed_pencil_matches[-1]
            _append(f"{first}+{added}-{used}")
        elif pencil_matches:
            total, used = pencil_matches[-1]
            _append(f"{total}-{used}")
        elif "더" in source and any(token in source for token in ("사용", "주었", "주었습니다", "남은")) and len(numbers) >= 3:
            _append(f"{numbers[0]}+{numbers[1]}-{numbers[2]}")
        elif "더" in source or ("있고" in source and not any(token in source for token in ("그중", "주었", "사용", "남은"))):
            _append(f"{numbers[0]}+{numbers[1]}")
        elif any(token in source for token in ("그중", "주었", "주었습니다", "사용", "남은")):
            _append(f"{numbers[0]}-{numbers[1]}")

    match = re.search(r"한\s*상자.*?(\d+)\s*권.*?(\d+)\s*상자", source)
    if match:
        per_box, boxes = match.groups()
        _append(f"{per_box}*{boxes}")

    match = re.search(r"시속\s*(\d+)\s*(?:km|107|0|<7모|로|[^0-9]{1,8}).*?(\d+)\s*시간", source, flags=re.IGNORECASE)
    if match:
        speed, hours = match.groups()
        if len(speed) > 3 and speed.endswith("107"):
            speed = speed[:-3]
        _append(f"{speed}*{hours}")

    matches = re.findall(r"어떤\s*수\s*[xX*]?\s*에\s*([-+]?\d+)를\s*곱하고\s*([-+]?\d+)(를)?\s*더했더니\s*([-+]?\d+)(가)?", source)
    if matches:
        coefficient, constant, _, result, _ = max(matches, key=lambda item: (bool(item[2]), bool(item[4]), -len(item[1]), -len(item[3])))
        _append(f"{coefficient}x+{constant}={result}")
    matches = re.findall(r"어떤\s*수\s*[xX*]?\s*에\s*([-+]?\d+)를\s*[^0-9+\-]{0,16}\s*([-+]?\d+)\s*더했더니\s*([-+]?\d+)", source)
    if matches:
        coefficient, constant, result = matches[-1]
        _append(f"{coefficient}x+{constant}={result}")

    if "방정식" in source:
        match = re.search(r"([-+]?\d+)\s*\*\s*([-+]\s*[-+]?\d+)\s*=\s*([-+]?\d+)", source)
        if match:
            coefficient, constant, result = match.groups()
            compact_constant = constant.replace(" ", "").replace("+-", "-").replace("++", "+")
            joiner = "" if compact_constant.startswith("-") else "+"
            _append(f"{coefficient}x{joiner}{compact_constant}={result}")
        for pattern in (
            r"([-+]?\d+)\s*[%*]+\s*\+\s*\(?\s*([-+]?\d+)\s*=\s*([-+]?\d+)",
            r"([-+]?\d+)\s*x?\s*\+\s*([-+]?\d+)\s*x\s*=\s*([-+]?\d+)",
        ):
            match = re.search(pattern, source, flags=re.IGNORECASE)
            if match:
                coefficient, constant, result = match.groups()
                _append(f"{coefficient}x+{constant}={result}")
    match = re.search(r"([-+]?\d+)x\s*([+-]\s*[-+]?\d+)\s*=\s*([-+]?\d+)", source, flags=re.IGNORECASE)
    if match:
        coefficient, constant, result = match.groups()
        compact_constant = constant.replace(" ", "").replace("+-", "-").replace("++", "+")
        joiner = "" if compact_constant.startswith("-") else "+"
        _append(f"{coefficient}x{joiner}{compact_constant}={result}")

    quadratic_source = source.replace("×", "*")
    match = re.search(r"(?:x\s*(?:\^|\*)?\s*2|[*]\s*2)\s*([-+]\s*[-+]?\d+)\s*x?\s*(?:=|<=)\s*([-+]?\d+)", quadratic_source, flags=re.IGNORECASE)
    if match:
        linear, result = match.groups()
        compact_linear = linear.replace(" ", "").replace("+-", "-").replace("++", "+")
        joiner = "" if compact_linear.startswith("-") else "+"
        if compact_linear.startswith("+"):
            compact_linear = compact_linear[1:]
        _append(f"x^2{joiner}{compact_linear}x={result}")

    if ("함수" in source or "일차식" in source) and re.search(r"\by\s*=", source, flags=re.IGNORECASE):
        match = re.search(r"\by\s*=\s*([0-9xX+\-*/^().\s]+?)(?:에서|일\s*때|$)", source, flags=re.IGNORECASE)
        if match:
            rhs = match.group(1).strip().replace(" ", "").replace("+-", "-")
            _append(f"y={rhs}")
        match = re.search(r"(?:y\s*가|(?<![a-zA-Z])가)\s*([-+]?\d+)\s*일\s*때", source, flags=re.IGNORECASE)
        if match:
            _append(f"y={match.group(1)}")
        match = re.search(r"(?:x|[*])\s*=\s*([-+]?\d+)\s*(?:(?:일\s*)?때|입니다)", source, flags=re.IGNORECASE)
        if match:
            _append(f"x={match.group(1)}")

    match = re.search(r"첫째항이\s*([-+]?\d+).*?공차가\s*([-+]?\d+).*?제\s*([-+]?\d+)\s*항", source)
    if match:
        first, diff, nth = (int(item) for item in match.groups())
        _append(f"{first}+({nth}-1)*{diff}")

    match = re.search(r"공\s*(\d+)\s*개.*?빨간\s*공이\s*(\d+)\s*개", source)
    if match:
        total, red = match.groups()
        _append(f"{red}/{total}")

    if "평균" in source:
        average_numbers = [int(item) for item in re.findall(r"(?<![a-zA-Z])\d{2,3}", source)]
        if len(average_numbers) >= 3:
            _append(f"({'+'.join(str(item) for item in average_numbers)})/{len(average_numbers)}")

    area_match = re.search(r"f\(\s*x\s*\)\s*=\s*([-+]?\d+).*?0\s*<=\s*(?:x|[*])\s*<=\s*([-+]?\d+).*?넓이", source, flags=re.IGNORECASE)
    if area_match:
        height, width = area_match.groups()
        _append(f"{height}*{width}")

    poly_match = re.search(r"f\(\s*x\s*\)\s*=\s*([0-9xX+\-*/^().%\s]+)", source, flags=re.IGNORECASE)
    eval_match = re.search(r"(?:f\s*)?\(\s*([-+]?\d+)\s*\)\s*(?:의|2\||값)", source, flags=re.IGNORECASE)
    if poly_match:
        poly = poly_match.group(1)
        poly = poly.replace("%", "x")
        poly = re.sub(r"[xX]\s*\*\s*2", "x^2", poly)
        poly = re.sub(r"([+-])\s*0\s*[7>]\s*[*xX]?", r"\g<1>0x", poly)
        poly = re.sub(r"(\d+)\s*[xX]\s*2(?=\s*[!|]?\s*때)", r"\1x", poly)
        poly = re.sub(r"([+-]\s*\d+)\s*\*$", r"\1x", poly.strip())
        deriv_eval_match = re.search(r"(?:f|[\[『])'\(\s*([-+]?\d+)\s*\)", source, flags=re.IGNORECASE)
        deriv_poly = poly.replace(" ", "").replace("+-", "-").replace("++", "+")
        deriv_poly = re.sub(r"([+-]\d+)\*$", r"\1x", deriv_poly)
        deriv_coeff_match = re.search(r"([-+]?\d*)x\^2([-+]\d+)?x", deriv_poly, flags=re.IGNORECASE)
        if deriv_eval_match and deriv_coeff_match:
            leading_raw, linear_raw = deriv_coeff_match.groups()
            leading = int(leading_raw) if leading_raw not in {"", "+", None} else 1
            linear = int(linear_raw or "0")
            at = int(deriv_eval_match.group(1))
            _append(f"2*{leading}*{at}+{linear}")
        if "x" in poly.lower() or eval_match:
            _append(poly)
        if eval_match:
            _append(f"x={eval_match.group(1)}")

    deriv_match = re.search(
        r"f\(\s*x\s*\)\s*=\s*([-+]?\d*)\s*x\s*(?:\^|\*)\s*2\s*([-+]\s*\d+)?\s*x.*?(?:f|[\[『])'\(\s*([-+]?\d+)\s*\)",
        source,
        flags=re.IGNORECASE,
    )
    if deriv_match:
        leading_raw, linear_raw, at_raw = deriv_match.groups()
        leading = int(leading_raw) if leading_raw not in {"", "+", None} else 1
        linear = int(str(linear_raw or "+0").replace(" ", ""))
        at = int(at_raw)
        _append(f"2*{leading}*{at}+{linear}")

    log_match = re.search(r"log_?\s*(\d+)\s*\(\s*(\d+)\s*\)", source, flags=re.IGNORECASE)
    if log_match:
        base, value = log_match.groups()
        _append(f"log_{base}({value})")

    return expressions[:6]


def _merge_expression_candidates(*texts: str) -> list[str]:
    merged: list[str] = []
    for text in texts:
        for item in [*_infer_semantic_expression_candidates(text), *_extract_expression_candidates(text)]:
            if item and item not in merged:
                merged.append(item)
    return merged[:6]


def _build_problem_text(content_text: str, expressions: list[str]) -> str:
    return select_problem_statement(content_text, expressions)


def _expression_variants(expr: str) -> list[str]:
    variants: list[str] = []

    def _append(candidate: str) -> None:
        text = str(candidate or "").strip()
        if text and text not in variants:
            variants.append(text)

    raw = _normalize_repaired_text(expr)
    _append(raw)
    _append(_INLINE_MULTIPLY_RE.sub("*", raw))

    for match in _SQRT_CUBERT_PAIR_RE.finditer(raw):
        left, right = match.groups()
        _append(f"({left})**(1/2)*({right})**(1/3)")

    repaired = _SQRT_MARKER_RE.sub(r"(\1)**(1/2)", raw)
    repaired = _CBRT_MARKER_RE.sub(r"(\1)**(1/3)", repaired)
    repaired = _INLINE_MULTIPLY_RE.sub("*", repaired)
    _append(repaired)
    return variants


def _normalize_for_sympy(expr: str) -> str:
    normalized = normalize_math_text(expr)
    normalized = _QUESTION_SUFFIX_RE.sub("", normalized).strip()
    normalized = re.sub(r"=\s*\?\s*\d*$", "", normalized)
    normalized = normalized.strip(" ]}|")
    normalized = re.sub(r"(\d+)\s+7\s*/\s*(\d+)", r"\1/\2", normalized)
    normalized = re.sub(r"(\d{2,})7\s+(\d+)", r"\1/\2", normalized)
    normalized = re.sub(r"(?<=\d)\s+7\s+(?=\d)", "/", normalized)
    normalized = normalized.replace("?", "")
    normalized = re.sub(r"(\d+)\s*[°º]\s*2", r"\1^2", normalized)
    normalized = re.sub(r"(?<=\d)<\s*\^\s*2", "x^2", normalized)
    normalized = normalized.replace("^", "**")
    normalized = normalized.replace("sqrt", "sqrt")
    normalized = normalized.replace("√", "sqrt")
    normalized = re.sub(r"log\s*_?\s*([0-9]+)\s*\(\s*([^)]+)\s*\)", r"log(\2,\1)", normalized)
    normalized = re.sub(r"log\s*_?\s*([0-9]+)\s*([a-zA-Z0-9()]+)", r"log(\2,\1)", normalized)
    normalized = normalized.replace("X", "x")
    normalized = normalized.replace("O", "0")
    normalized = re.sub(r"(?<=\d)\*\s*\+\s*(\d+)ㅋ", r"x+\1", normalized)
    normalized = normalized.replace("%", "x").replace("ㅋ", "x")
    if "=" in normalized:
        normalized = re.sub(r"\bx\s*\*\s*2\b", "x**2", normalized)
        normalized = re.sub(r"(?<!\d)\*\s*\*\*\s*2", "x**2", normalized)
        normalized = re.sub(r"(?<!\d)\*\s*2", "x**2", normalized)
        normalized = re.sub(r"([+\-]\d+)\s*\*(?=\s*(?:=|$))", r"\1x", normalized)
        normalized = re.sub(r"(?<=\d)\*\s*(?=[+=])", "x", normalized)
        normalized = re.sub(r"(?<=\d)\*\s*(?=[+-]\d)", "x", normalized)
    elif "x**2" in normalized:
        normalized = re.sub(r"([+\-]\d+)\s*\*(?=[+\-]|$)", r"\1x", normalized)
    normalized = re.sub(r"(?<=\d)\s*x\s*x", "x", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(?<=\d)x\+\(?\s*([-+]?\d+)", r"x+\1", normalized)
    if "=" in normalized and not re.search(r"[xy]", normalized, flags=re.IGNORECASE):
        lhs, rhs = normalized.split("=", 1)
        if re.search(r"[+\-*/^]", lhs):
            normalized = lhs
    normalized = re.sub(r"([0-9)])\s*([a-zA-Z])", r"\1*\2", normalized)
    normalized = re.sub(r"([xy])\s*(?=\d|\()", r"\1*", normalized)
    normalized = re.sub(r"(\d)\s*\(", r"\1*(", normalized)
    normalized = re.sub(r"\)\s*\(", r")*(", normalized)
    normalized = re.sub(r"([a-zA-Z])\s*\(", r"\1(", normalized)
    normalized = re.sub(r"\s+", "", normalized)
    normalized = normalized.replace("x*x**2", "x**2")
    return normalized


def _safe_eval(expr: str, variables: dict[str, float] | None = None) -> float:
    variable_values = variables or {}
    allowed_funcs = {
        "sqrt": math.sqrt,
        "log": lambda x, base=math.e: math.log(x, base),
        "pi": math.pi,
    }

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id in variable_values:
            return float(variable_values[node.id])
        if isinstance(node, ast.Name) and node.id in allowed_funcs and isinstance(allowed_funcs[node.id], (int, float)):
            return float(allowed_funcs[node.id])
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Pow):
                return left ** right
        if isinstance(node, ast.UnaryOp):
            value = _eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return value
            if isinstance(node.op, ast.USub):
                return -value
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in allowed_funcs:
            args = [_eval(arg) for arg in node.args]
            return float(allowed_funcs[node.func.id](*args))
        raise ValueError(f"Unsupported expression: {ast.dump(node)}")

    tree = ast.parse(expr, mode="eval")
    return float(_eval(tree))


def _solve_linear_equation(lhs: str, rhs: str, symbol_name: str) -> str | None:
    try:
        def _value(at: float) -> float:
            return _safe_eval(lhs, {symbol_name: at}) - _safe_eval(rhs, {symbol_name: at})

        intercept = _value(0.0)
        slope = _value(1.0) - intercept
        if abs(slope) < 1e-12:
            return None
        return _format_number(-intercept / slope)
    except Exception:
        return None


def _solve_polynomial_equation(lhs: str, rhs: str, symbol_name: str) -> str | None:
    try:
        def _value(at: float) -> float:
            return _safe_eval(lhs, {symbol_name: at}) - _safe_eval(rhs, {symbol_name: at})

        c = _value(0.0)
        f1 = _value(1.0)
        fm1 = _value(-1.0)
        a = (f1 + fm1 - 2 * c) / 2
        b = (f1 - fm1) / 2
        if abs(a) < 1e-12:
            return _solve_linear_equation(lhs, rhs, symbol_name)
        discriminant = b * b - 4 * a * c
        if discriminant < -1e-9:
            return None
        if abs(discriminant) < 1e-9:
            return _format_number(-b / (2 * a))
        root = math.sqrt(max(discriminant, 0.0))
        roots = sorted([(-b - root) / (2 * a), (-b + root) / (2 * a)])
        return ", ".join(_format_number(item) for item in roots)
    except Exception:
        return None


def _format_number(value: float) -> str:
    rounded = round(value)
    if abs(value - rounded) < 1e-9:
        return str(int(rounded))
    return f"{value:.6g}"


def _format_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _safe_fraction_eval(expr: str) -> Fraction:
    def _eval(node) -> Fraction:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return Fraction(node.value)
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Pow) and right.denominator == 1:
                return left ** right.numerator
        if isinstance(node, ast.UnaryOp):
            value = _eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return value
            if isinstance(node.op, ast.USub):
                return -value
        raise ValueError("unsupported fraction expression")

    return _eval(ast.parse(expr, mode="eval"))


def _solve_function_value(problem: ProblemSchema) -> dict[str, Any] | None:
    expressions = list(problem.expressions or [])
    if problem.normalized_problem_text:
        expressions.append(problem.normalized_problem_text)

    for source in expressions:
        match = re.fullmatch(r"answer=([+\-]?(?:\d+(?:\.\d+)?|\.\d+))", str(source or "").replace(" ", ""))
        if match:
            computed = _format_number(float(match.group(1)))
            return {
                "solver_name": "table_lookup_solver",
                "computed_answer": computed,
                "steps": [
                    "표에서 목표 조건과 같은 열을 찾았어.",
                    f"그 열의 대응값은 {computed}야.",
                ],
                "confidence": 0.84,
            }

    x_value: float | None = None
    y_value: float | None = None
    function_rhs: str | None = None
    variable_rhs: str | None = None

    for source in expressions:
        for variant in _expression_variants(source):
            expr = _normalize_for_sympy(variant)
            if not expr:
                continue
            if "=" in expr:
                lhs, rhs = expr.split("=", 1)
                if lhs == "x" and x_value is None and re.fullmatch(r"[+\-]?(?:\d+(?:\.\d+)?|\.\d+)", rhs):
                    try:
                        x_value = _safe_eval(rhs)
                    except Exception:
                        continue
                elif lhs == "y" and y_value is None and re.fullmatch(r"[+\-]?(?:\d+(?:\.\d+)?|\.\d+)", rhs):
                    try:
                        y_value = _safe_eval(rhs)
                    except Exception:
                        continue
                elif lhs == "y" and function_rhs is None and "x" in rhs:
                    function_rhs = rhs
            elif variable_rhs is None and "x" in expr:
                variable_rhs = expr

    if x_value is not None and function_rhs:
        try:
            computed = _format_number(_safe_eval(function_rhs, {"x": x_value}))
        except Exception:
            return None

        return {
            "solver_name": "function_value_solver",
            "computed_answer": computed,
            "steps": [
                f"함수식을 y={function_rhs} 형태로 정리했어.",
                f"x={_format_number(x_value)}을 대입했어.",
                f"y의 값은 {computed}야.",
            ],
            "confidence": 0.83,
        }

    if y_value is not None and function_rhs:
        computed = _solve_linear_equation(function_rhs, str(y_value), "x")
        if computed is not None:
            return {
                "solver_name": "function_inverse_solver",
                "computed_answer": computed,
                "steps": [
                    f"함수식을 y={function_rhs} 형태로 정리했어.",
                    f"y={_format_number(y_value)}가 되도록 x를 풀었어.",
                    f"x의 값은 {computed}야.",
                ],
                "confidence": 0.81,
            }

    if x_value is not None and variable_rhs:
        try:
            computed = _format_number(_safe_eval(variable_rhs, {"x": x_value}))
        except Exception:
            return None
        return {
            "solver_name": "expression_value_solver",
            "computed_answer": computed,
            "steps": [
                f"식 {variable_rhs}에 x={_format_number(x_value)}을 대입했어.",
                f"계산하면 {computed}야.",
            ],
            "confidence": 0.82,
        }

    return None


def _compute_answer(problem: ProblemSchema) -> dict[str, Any]:
    trig_source = " ".join([str(problem.normalized_problem_text or ""), *(problem.expressions or [])]).lower()
    if problem.math_topic == "trigonometry" and re.search(r"\b(?:sin|cos|tan)\b|π|pi", trig_source):
        result = trig_solver.solve(problem)
        result["solver_name"] = "trig_solver"
        return result

    first_expression = str((problem.expressions or [""])[0] or "")
    first_expr_normalized = _normalize_for_sympy(first_expression)
    if (
        first_expr_normalized
        and not re.search(r"\d/\s*(?:[+\-=]|$)", first_expression)
        and "/" not in first_expr_normalized
        and not re.search(r"[xy]", first_expr_normalized, flags=re.IGNORECASE)
        and len(re.findall(r"[+\-*/]", first_expr_normalized)) >= 2
    ):
        try:
            computed = _format_number(_safe_eval(first_expr_normalized))
            return {
                "solver_name": "direct_numeric_solver",
                "computed_answer": computed,
                "steps": [
                    "OCR 후보 중 바로 계산 가능한 식을 우선 사용했어.",
                    f"계산하면 {computed}야.",
                ],
                "confidence": 0.84,
            }
        except Exception:
            pass

    if problem.math_topic in {"calculus_derivative", "calculus_integral"}:
        for source in problem.expressions or []:
            expr = _normalize_for_sympy(source)
            if not expr or re.search(r"[xy]", expr, flags=re.IGNORECASE):
                continue
            try:
                computed = _format_number(_safe_eval(expr))
            except Exception:
                continue
            return {
                "solver_name": "calculus_numeric_solver",
                "computed_answer": computed,
                "steps": [
                    "미분/적분 조건에서 필요한 계산식만 먼저 추렸어.",
                    f"계산하면 {computed}야.",
                ],
                "confidence": 0.84,
            }

    function_result = _solve_function_value(problem)
    if function_result is not None:
        return function_result

    for source in problem.expressions or [problem.normalized_problem_text]:
        if re.search(r"\d/\s*(?:[+\-=]|$)", str(source or "")):
            continue
        for variant in _expression_variants(source):
            expr = _normalize_for_sympy(variant)
            if not expr:
                continue
            try:
                if "=" in expr and any(var in expr for var in ("x", "y")):
                    lhs, rhs = expr.split("=", 1)
                    symbol_name = "x" if "x" in expr else "y"
                    computed = None
                    if sp is not None:
                        symbol = sp.symbols(symbol_name)
                        solutions = sp.solve(sp.Eq(sp.sympify(lhs), sp.sympify(rhs)), symbol)
                        if solutions:
                            computed = ", ".join(str(item) for item in solutions)
                    if not computed:
                        computed = _solve_polynomial_equation(lhs, rhs, symbol_name)
                    if not computed:
                        continue
                    return {
                        "solver_name": "equation_solver",
                        "computed_answer": computed,
                        "steps": [
                            "식 양쪽을 같은 변수식으로 정리했어.",
                            f"{symbol_name}에 대한 방정식으로 보고 풀었어.",
                            f"해는 {computed}야.",
                        ],
                        "confidence": 0.84,
                    }

                if "/" in expr and re.fullmatch(r"[0-9+\-*/().]+", expr):
                    computed = _format_fraction(_safe_fraction_eval(expr))
                    return {
                        "solver_name": "fraction_solver",
                        "computed_answer": computed,
                        "steps": [
                            "분수식을 통분해서 계산 가능한 형태로 정리했어.",
                            "마지막 값은 기약분수로 줄였어.",
                            f"값은 {computed}야.",
                        ],
                        "confidence": 0.88,
                    }

                computed_value = _safe_eval(expr)
                computed = _format_number(computed_value)
                return {
                    "solver_name": "safe_eval_solver",
                    "computed_answer": computed,
                    "steps": [
                        "보이는 식을 계산 가능한 형태로 정리했어.",
                        "OCR에서 깨진 지수와 곱셈 표기를 함께 보정했어." if variant != source else "지수와 괄호를 순서대로 계산했어.",
                        f"값은 {computed}야.",
                    ],
                    "confidence": 0.86,
                }
            except Exception:
                continue

    fallback = arithmetic_solver.solve(problem)
    fallback["solver_name"] = str(fallback.get("solver_name") or "arithmetic_solver")
    return fallback


def _build_structured_problem(image_path: str, user_query: str = "") -> tuple[ProblemSchema, dict[str, Any]]:
    raw_text, debug_sources = _select_best_text(image_path)
    content_text, metadata_lines = split_exam_metadata(raw_text)
    repair_debug = debug_sources.get("text_repair") or {}
    repaired_text = str(repair_debug.get("text") or "").strip() if repair_debug.get("accepted") else ""
    preferred_content = repaired_text or content_text or raw_text
    choices = parse_choices(repaired_text) or parse_choices(raw_text)
    expressions = _merge_expression_candidates(content_text or raw_text, repaired_text)
    problem_text = _build_problem_text(preferred_content, expressions)
    math_topic = _detect_math_topic(preferred_content, expressions)
    question_type = "multiple_choice" if choices else "subjective"
    confidence = min(
        1.0,
        max(
            detect_math_signal_score(problem_text),
            0.35 if expressions else 0.0,
            0.4 if choices else 0.0,
            0.48 if repaired_text else 0.0,
        ),
    )
    metadata = {
        "image_path": image_path,
        "user_query": user_query,
        "ocr_debug": debug_sources,
        "metadata_lines": metadata_lines,
        "content_hash": hashlib.sha1(Path(image_path).read_bytes()).hexdigest()[:12],
    }
    problem = ProblemSchema(
        source_text_candidates=[candidate for candidate in [raw_text, content_text, repaired_text] if candidate],
        normalized_problem_text=problem_text,
        expressions=expressions,
        choices=choices,
        question_type=question_type,
        math_topic=math_topic,
        target_question="문제 풀이",
        confidence=confidence,
        metadata=metadata,
    )
    debug = {
        "raw_text": raw_text,
        "content_text": content_text,
        "repaired_text": repaired_text,
        "expressions": expressions,
        "choices": choices,
        "math_topic": math_topic,
        "question_type": question_type,
    }
    return problem, debug


def run_upload_pipeline(image_path: str, user_query: str = "", debug: bool = False) -> dict[str, Any]:
    structured_problem, debug_payload = _build_structured_problem(image_path, user_query=user_query)
    payload: dict[str, Any] = {
        "route": "solver",
        "structured_problem": structured_problem,
    }
    if debug:
        payload["debug"] = debug_payload
    return payload


def run_solve_pipeline(
    image_path: str | None = None,
    structured_problem: ProblemSchema | None = None,
    user_query: str = "",
    debug: bool = False,
) -> dict[str, Any]:
    debug_payload: dict[str, Any] = {}
    problem = structured_problem
    if problem is None:
        if not image_path:
            raise ValueError("image_path or structured_problem is required")
        upload_payload = run_upload_pipeline(image_path, user_query=user_query, debug=debug)
        problem = upload_payload["structured_problem"]
        debug_payload["upload"] = upload_payload.get("debug", {})

    solver_name = route_solver(problem)
    trig_source = " ".join([str(problem.normalized_problem_text or ""), *(problem.expressions or [])]).lower()
    if solver_name == "trig_solver" and re.search(r"\b(?:sin|cos|tan)\b|π|pi", trig_source):
        solver_result = trig_solver.solve(problem)
    else:
        solver_result = _compute_answer(problem)
    solver_result["solver_name"] = str(solver_result.get("solver_name") or solver_name)

    solved: SolveResult = validate_answer(problem, solver_result)
    solved.explanation = generate_korean_tutor_response(problem, solved, user_query)
    debug_payload["solver_name"] = solved.solver_name
    debug_payload["computed_answer"] = solved.computed_answer
    debug_payload["validation_status"] = solved.validation_status

    payload = {
        "structured_problem": problem,
        "solve_result": solved,
    }
    if debug:
        payload["debug"] = debug_payload
    return payload


def dump_debug_payload(payload: dict[str, Any]) -> str:
    serializable: dict[str, Any] = {}
    for key, value in payload.items():
        if hasattr(value, "model_dump"):
            serializable[key] = value.model_dump()
        else:
            serializable[key] = value
    return json.dumps(serializable, ensure_ascii=False, indent=2)
