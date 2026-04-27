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
from app.engines.parser.auto_normalizer import (
    SQRT_CUBERT_PAIR_RE,
    SEQUENCE_LOG_PRODUCT_EXPR_RE,
    infer_auto_expression_candidates,
    is_fractional_power_ocr_statement,
    record_normalization_observation,
)
from app.engines.parser.math_ocr_normalizer import (
    apply_school_ocr_profile,
    clean_visible_math_text,
    is_metadata_or_choice_noise_line,
    normalize_ocr_math_text,
    ocr_noise_score,
)
from app.engines.parser.elementary_visual_templates import infer_elementary_visual_template
from app.engines.parser.school_math_taxonomy import classify_school_math_topic
from app.engines.router.school_level_router import infer_school_profile
from app.engines.router.solver_router import route_solver
from app.engines.solver import arithmetic_solver, trig_solver
from app.engines.solver.sympy_worker import solve_equation as solve_equation_with_sympy_worker
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


def _ocr_numeric_cell(cell: Any) -> str | None:
    binary = os.getenv("COCO_TESSERACT_BIN", "/opt/homebrew/bin/tesseract")
    if ImageOps is None or not Path(binary).exists():
        return None
    try:
        prepared = ImageOps.autocontrast(cell.convert("L"))
        prepared = prepared.resize((prepared.width * 4, prepared.height * 4))
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
            temp_path = Path(handle.name)
        prepared.save(temp_path)
        try:
            proc = subprocess.run(
                [
                    binary,
                    str(temp_path),
                    "stdout",
                    "-l",
                    "eng",
                    "--psm",
                    "7",
                    "-c",
                    "tessedit_char_whitelist=-0123456789",
                ],
                capture_output=True,
                text=True,
                timeout=4,
                check=False,
            )
        finally:
            temp_path.unlink(missing_ok=True)
        match = re.search(r"-?\d+", proc.stdout or "")
        return match.group(0) if match else None
    except Exception:
        return None


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
    if best_text is not None and best_score <= 0.06:
        return best_text
    return _ocr_numeric_cell(cell)


def _extract_rectangle_metric_text(image_path: str) -> str:
    if Image is None or ImageOps is None or np is None:
        return ""
    binary = os.getenv("COCO_TESSERACT_BIN", "/opt/homebrew/bin/tesseract")
    if not Path(binary).exists():
        return ""
    try:
        image = Image.open(image_path).convert("RGB")
    except Exception:
        return ""

    array = np.array(image)
    blue_mask = (array[:, :, 2] > 135) & (array[:, :, 0] < 90) & (array[:, :, 1] < 140)
    ys, xs = np.where(blue_mask)
    if len(xs) < 200:
        return ""
    left, right = int(xs.min()), int(xs.max())
    top, bottom = int(ys.min()), int(ys.max())
    if right - left < 80 or bottom - top < 50:
        return ""

    def _read_dimension(box: tuple[int, int, int, int]) -> int | None:
        left_box, top_box, right_box, bottom_box = box
        left_box = max(0, min(image.width, left_box))
        right_box = max(0, min(image.width, right_box))
        top_box = max(0, min(image.height, top_box))
        bottom_box = max(0, min(image.height, bottom_box))
        if right_box <= left_box or bottom_box <= top_box:
            return None
        box = (left_box, top_box, right_box, bottom_box)
        crop = image.crop(box).convert("L")
        if crop.width <= 0 or crop.height <= 0:
            return None
        prepared = ImageOps.autocontrast(crop)
        prepared = prepared.resize((prepared.width * 4, prepared.height * 4))
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
            temp_path = Path(handle.name)
        prepared.save(temp_path)
        try:
            proc = subprocess.run(
                [
                    binary,
                    str(temp_path),
                    "stdout",
                    "-l",
                    "eng",
                    "--psm",
                    "7",
                    "-c",
                    "tessedit_char_whitelist=0123456789cm",
                ],
                capture_output=True,
                text=True,
                timeout=4,
                check=False,
            )
        finally:
            temp_path.unlink(missing_ok=True)
        match = re.search(r"\d+", proc.stdout or "")
        return int(match.group(0)) if match else None

    width_value = _read_dimension((left, bottom + 2, right, min(image.height, bottom + 90)))
    height_value = _read_dimension((right + 2, top, min(image.width, right + 160), bottom))
    if width_value is None or height_value is None:
        return ""
    return f"rectangle_width {width_value} rectangle_height {height_value} rectangle_area {width_value}*{height_value}"


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
        rectangle_text = _extract_rectangle_metric_text(image_path)
        if rectangle_text:
            passes.append(
                {
                    "engine": "geometry_metric_reader",
                    "variant": "rectangle_metric",
                    "psm": "geometry",
                    "available": True,
                    "text": rectangle_text,
                    "confidence": 0.74,
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


def _normalize_repaired_text(text: str, *, school_level: str | None = None, profile: str | None = None) -> str:
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
    return normalize_ocr_math_text(normalized, school_level=school_level, profile=profile)


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
                r"(표|함수|방정식|구하시오|값|확률|평균|넓이|시속|연필|상자|쪽수|개수|인원|등차|수열|첫째항|공차|로그|자료|규칙|빈칸)",
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


def _infer_elementary_topic(text: str, expressions: list[str]) -> str:
    joined = f"{text or ''}\n" + "\n".join(str(item or "") for item in expressions)
    if not joined.strip():
        return ""
    compact = re.sub(r"\s+", "", joined)
    if re.search(r"여러가지모양|평면도형|입체도형|도형|각도|직각|예각|둔각|직육면체|정육면체|전개도", compact):
        return "geometry"
    if re.search(r"분류하기|표와그래프|분류|조사|종류|자료|그래프|날씨", compact):
        return "statistics"
    if re.search(r"규칙찾기|규칙적인|규칙|수배열표|배열표|차례대로|반복|탁자|의자", compact):
        return "pattern"
    if re.search(r"비교하기|길이|무게|들이|시각|시간|화폐", compact):
        return "measurement"
    if re.search(r"분수|소수|비와비율|비례식||\ue06d", compact):
        return "fraction_ratio"
    if re.search(
        r"9까지의수|50까지의수|100까지의수|100가지의수|세자리수|네자리수|자리수|"
        r"덧셈|뺄셈|곱셈|나눗셈|자연수|약수|배수|혼합계산",
        compact,
    ):
        return "arithmetic"
    if re.search(r"규칙|순서|몇째|번째|차례|왼쪽에서|오른쪽에서|앞에서|뒤에서", compact):
        return "pattern"
    if re.search(
        r"모양|도형|삼각형|사각형|원기둥|직육면체|정육면체|전개도|선분|상자|공|쌓|굴러|평면도형|"
        r"각도|직각|예각|둔각|각[ㄱ-ㅎ]|시침|분침|긴바늘|짧은바늘|등분|몇도|크기가같은각",
        compact,
    ):
        return "geometry"
    if re.search(r"길이|무게|들이|시각|시간|cm|mm|m\b|kg|g\b|L\b|mL\b", joined, flags=re.IGNORECASE):
        return "measurement"
    if re.search(r"분수|분모|분자|\d+\s*/\s*\d+|비율|비례|%", compact):
        return "fraction_ratio"
    if re.search(
        r"수만큼|알맞은수|빈칸|써넣|쓰세요|쓰시오|읽어|세어|몇개|몇명|"
        r"더큰수|더작은수|큰수|작은수|크기를비교|비교하여|알맞게|보다|"
        r"가지고|받았다|남은|뛰어서세어|숫자로쓰|자리숫자|수모형|"
        r"합과차|모으기|가르기|묶|○표|색칠|그려|개수|올림|버림|반올림|"
        r"천의자리|백의자리|십의자리|자리까지|합을구|몇배|배입니까",
        compact,
    ):
        return "arithmetic"
    if re.search(r"선으로|이어|고르|찾아", compact):
        return "arithmetic"
    return ""


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
    normalized = re.sub(r"\bO(?=\s*[xX])", "0", normalized)
    normalized = re.sub(r"(?<=\d)[Kk](?=\s*[+\-])", "x", normalized)
    normalized = re.sub(r"(?<=\d)A[lI1](?=\s|$)", " 41", normalized)
    normalized = normalized.replace("[(", "f(").replace("『(", "f(")
    normalized = normalized.replace("['(", "f'(").replace("『'(", "f'(")
    normalized = re.sub(r"\bA[lI1]?\s*y\s*=", "y =", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(?<!\S)/\s*=", "y =", normalized)
    normalized = re.sub(r">\s*[*xX]", "x", normalized)
    normalized = normalized.replace("”", "*").replace("“", "*")
    normalized = re.sub(r"([+-])\s*0\s*[7>]\s*[*xX]?", r"\g<1>0x", normalized)
    normalized = re.sub(r"(\d+)%\s*\+/\s*(\d+)", r"\1x+\2", normalized)
    normalized = re.sub(r"(\d+)\*\s*\+\s*(\d+)x(?=\s*=)", r"\1x+\2", normalized)
    normalized = re.sub(r"(?<=\d)<\s*\^\s*2", "x^2", normalized)
    normalized = re.sub(r"(\d+)\s*[xX]\s*2(?=\s*[!|]?\s*때)", r"\1x", normalized)
    normalized = re.sub(r"([xX*])\s*=\s*([-+]?\d)2(?=\s*(?:때|일|2[|!]))", r"x = \2", normalized)
    normalized = re.sub(r"([xX*])\s*=\s*([-+]?\d)2[1lI|](?=\s*(?:때|일))", r"x = \2", normalized)
    normalized = re.sub(r"([xX*])\s*=\s*OF\b", "x = 0", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"([xX*])\s*=\s*OS\b", "x = 0", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"([xX])[*\"']\s*2", r"\1^2", normalized)
    normalized = re.sub(r"([xX])\s*[°º]\s*2", r"\1^2", normalized)
    normalized = re.sub(r"(?<=\d)[lI|](?=\s|,|$)", "1", normalized)
    normalized = re.sub(r"([xX]\s*[+\-]\s*\d)2(?=\s*(?:[!|1]\s*)?때)", r"\1", normalized)
    normalized = re.sub(r"(?<![a-zA-Z])[*×]\s*2", "x^2", normalized)
    normalized = re.sub(r"(\d)Xx", r"\1x", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _infer_semantic_expression_candidates(text: str, *, school_level: str | None = None) -> list[str]:
    source = _normalize_semantic_text(text)
    line_source = clean_visible_math_text(text, school_level=school_level)
    line_candidates = [
        cleaned
        for raw_line in str(text or "").splitlines()
        if (cleaned := clean_visible_math_text(raw_line, school_level=school_level))
    ]
    if not line_candidates and line_source:
        line_candidates = [line_source]
    compact = source.replace(" ", "")
    expressions: list[str] = []

    def _append(expr: str) -> None:
        cleaned = str(expr or "").replace(" ", "").strip(" .,:;")
        if cleaned and cleaned not in expressions:
            expressions.append(cleaned)

    def _repair_korean_count_number(value: str) -> int:
        digits = re.sub(r"\D", "", str(value or ""))
        if len(digits) >= 4 and digits.endswith("74"):
            digits = digits[:-2]
        elif len(digits) >= 4 and digits.endswith("7"):
            digits = digits[:-1]
        elif len(digits) >= 3 and int(digits) > 150:
            digits = digits[:-1]
        return int(digits or "0")

    def _clean_linear_rhs(raw_rhs: str) -> str:
        rhs = str(raw_rhs or "").strip()
        rhs = re.sub(r"(?:입니다|입니|에서|일\s*때|때|구하시오|값).*", "", rhs)
        rhs = rhs.replace(" ", "").replace("K", "x").replace("k", "x").replace("%", "x")
        rhs = re.sub(r"(?<=\d)\*(?=[+\-]|$)", "x", rhs)
        rhs = re.sub(r"[^0-9xX+\-*/^().].*$", "", rhs)
        rhs = rhs.replace("X", "x").replace("+-", "-").replace("++", "+")
        if "x" not in rhs.lower():
            simple_line = re.fullmatch(r"([-+]?\d+)([+\-]\d+)", rhs)
            if simple_line:
                coefficient = int(simple_line.group(1))
                constant = int(simple_line.group(2))
                if abs(coefficient) < 10 and abs(constant) < 10:
                    rhs = f"{coefficient}x{constant:+d}".replace("+-", "-")
        return rhs.strip(" .,:;")

    for candidate in infer_auto_expression_candidates(text, school_level=school_level):
        _append(candidate)

    numbers = [int(item) for item in re.findall(r"(?<![a-zA-Z])[-+]?\d+", source)]

    blank_token = r"(?:\[\s*[_ ]?\s*\]|\|\s*[_ ]?\s*\||\(\s*\)|[_ㅣ])"

    def _append_blank_equation_answers() -> None:
        for match in re.finditer(rf"(\d{{1,4}})\s*([+\-])\s*{blank_token}\s*=\s*([-+]?\d{{1,4}})", source):
            left, operator, result = match.groups()
            value = int(result) - int(left) if operator == "+" else int(left) - int(result)
            _append(f"answer={value}")
        for match in re.finditer(rf"{blank_token}\s*([+\-])\s*(\d{{1,4}})\s*=\s*([-+]?\d{{1,4}})", source):
            operator, right, result = match.groups()
            value = int(result) - int(right) if operator == "+" else int(result) + int(right)
            _append(f"answer={value}")
        for match in re.finditer(r"(?<![\d.])([+\-])\s*(\d{1,4})\s*=\s*([-+]?\d{1,4})", source):
            operator, right, result = match.groups()
            value = int(result) - int(right) if operator == "+" else int(result) + int(right)
            if 0 <= value <= 999:
                _append(f"answer={value}")
        for match in re.finditer(r"(\d{1,4})\s*-\s*=\s*([-+]?\d{1,4})", source):
            left, result = match.groups()
            value = int(left) - int(result)
            if 0 <= value <= 999:
                _append(f"answer={value}")

    _append_blank_equation_answers()

    if re.search(r"10\s*을.*?(?:모으기|가르기)|(?:모으기|가르기).*?10", source):
        segments = list(line_candidates)
        segments.extend(match.group(1) for match in re.finditer(r"보세요[^\d]{0,16}(.{0,60})", source))
        for segment in segments:
            stripped = segment.strip()
            if not stripped:
                continue
            if stripped in line_candidates and re.search(r"이용|모으기|가르기|단원|회|정답|문제", stripped):
                continue
            values = [int(item) for item in re.findall(r"(?<!\d)\d{1,2}(?!\d)", stripped)]
            if 10 not in values:
                continue
            ten_index = values.index(10)
            visible = [value for value in values[:ten_index] if 1 <= value <= 9]
            if not visible:
                continue
            _append(f"answer={10 - visible[-1]}")
            break

    for match in re.finditer(r"(\d{1,3})\s*명[이가]?\s*타야\s*출발.{0,80}?지금\s*(\d{1,3})\s*명", source):
        total, current = (int(item) for item in match.groups())
        if total >= current:
            _append(f"answer={total - current}")
            break

    for match in re.finditer(r"(\d{1,3})\s*개.{0,220}?(\d{1,3})\s*개.{0,40}?(?:주었|주었습니다|받았|더\s*받)", source):
        first, second = (int(item) for item in match.groups())
        if first <= 999 and second <= 999:
            _append(f"answer={first + second}")
            break

    for match in re.finditer(r"(\d{1,3})\s*명에게.{0,80}?기념품.{0,80}?(\d{1,3})\s*개.{0,50}?더\s*필요", source):
        total, current = (int(item) for item in match.groups())
        if total >= current:
            _append(f"answer={total - current}")
            break

    def _single_digit_groups_near(pattern: str) -> list[list[int]]:
        groups: list[list[int]] = []
        lines = [line.strip() for line in line_candidates if line.strip()]
        for index, line in enumerate(lines):
            if not re.search(pattern, line, flags=re.IGNORECASE):
                continue
            for follow in lines[index + 1 : index + 4]:
                digits = [int(item) for item in re.findall(r"\b\d\b", follow)]
                if len(digits) >= 4:
                    groups.append(digits[:6])
                    break
        for match in re.finditer(pattern + r".{0,90}?((?:\b\d\b[\s,，|]*){4,6})", source):
            digits = [int(item) for item in re.findall(r"\b\d\b", match.group(1))]
            if len(digits) >= 4:
                groups.append(digits[:6])
        return groups

    minmax_card_pattern = r"가장\s*작은\s*수.*?가장\s*(?:큰|[A-Z]{1,3})\s*(?:수|42\])"
    if re.search(minmax_card_pattern + r".*?(?:합|더|HS|YS|Be)", source, flags=re.IGNORECASE):
        for digits in _single_digit_groups_near(minmax_card_pattern):
            _append(f"answer={min(digits) + max(digits)}")
            break

    if re.search(r"수\s*카드.*?2\s*장.*?가장\s*작은\s*몇십몇", source):
        for digits in _single_digit_groups_near(r"수\s*카드.*?2\s*장.*?가장\s*작은\s*몇십몇"):
            nonzero = sorted(value for value in digits if value > 0)
            if not nonzero:
                continue
            tens = nonzero[0]
            remaining = list(digits)
            remaining.remove(tens)
            ones = min(remaining) if remaining else 0
            _append(f"answer={10 * tens + ones}")
            break

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

    count_row = _row_numbers(r"(?:개수|수량|값|(?<![a-zA-Z])a|(?<![a-zA-Z])at|읽은\s*쪽수|인원|yO\]|HOA\s*yO\])")
    y_row = _row_numbers(r"(?:\by\b|yo|ㄱ)")
    x_row = _row_numbers(r"(?:\bx\b|[*])")
    if not x_row:
        x_row = _row_numbers(r"(?:[*]|x2\]\s*값은\?\s*[*])")
    grid_rows = [
        [int(item) for item in re.findall(r"[-+]?\d+", match.group(1))]
        for match in re.finditer(r"table_row_\d+\s+([-\d\s]+)", source)
    ]
    grid_rows = [row for row in grid_rows if len(row) >= 2]
    if not count_row and ("표" in source or "수량" in source) and any(token in source for token in ("모두", "합", "몇 개")):
        numeric_rows = [
            [int(item) for item in re.findall(r"[-+]?\d+", match.group(1))]
            for match in re.finditer(r"(?<!\d)((?:[-+]?\d+[\s\[\]|:;,.=]+){2,8}[-+]?\d+)(?!\d)", source)
        ]
        numeric_rows = [row for row in numeric_rows if len(row) >= 3]
        if numeric_rows:
            count_row = max(numeric_rows, key=len)
    if grid_rows:
        grid_count_row = grid_rows[-1]
        if not count_row:
            count_row = grid_count_row
        elif not (
            len(count_row) == len(grid_count_row)
            and any(abs(item) < 10 for item in grid_count_row)
            and not any(abs(item) < 10 for item in count_row)
        ):
            count_row = grid_count_row
        if len(grid_rows) >= 2:
            x_row = grid_rows[0]
            y_row = grid_rows[-1]
    if "표" in source or count_row or y_row:
        target_x_match = re.search(r"(?:x|[*])\s*=\s*([-+]?\d+)", source, flags=re.IGNORECASE)
        target_y_match = re.search(r"(?:y\s*가|y7|#가|(?<![a-zA-Z])가)\s*([-+]?\d+)", source, flags=re.IGNORECASE)
        table_lookup_added = False
        if y_row and target_x_match:
            target_x = int(target_x_match.group(1))
            if x_row and len(x_row) == len(y_row) and target_x in x_row:
                _append(f"answer={y_row[x_row.index(target_x)]}")
                table_lookup_added = True
            elif x_row and len(y_row) == len(x_row) - 1 and target_x in x_row:
                target_index = x_row.index(target_x)
                if target_index > 0:
                    _append(f"answer={y_row[target_index - 1]}")
                    table_lookup_added = True
            elif x_row and len(y_row) == len(x_row) + 1 and target_x in x_row:
                target_index = x_row.index(target_x)
                if target_index < len(y_row):
                    _append(f"answer={y_row[target_index]}")
                    table_lookup_added = True
            elif 1 <= target_x <= len(y_row) and re.search(r"(?:일차함수|함수|function)", source, flags=re.IGNORECASE):
                _append(f"answer={y_row[target_x - 1]}")
                table_lookup_added = True
        if y_row and target_y_match:
            target_y = int(target_y_match.group(1))
            if x_row and len(x_row) == len(y_row) and target_y in y_row:
                _append(f"answer={x_row[y_row.index(target_y)]}")
                table_lookup_added = True
        is_pattern_table = bool("규칙" in source or "pattern" in source.lower())
        is_probability_table = bool("확률" in source or "probability" in source.lower())
        if is_pattern_table and y_row:
            target_match = re.search(r"(\d+)\s*(?:번째|째)", source)
            target_index = int(target_match.group(1)) if target_match else len(y_row) + 1
            if len(y_row) >= 4 and abs(y_row[1]) < 10:
                inferred_diff = y_row[2] - y_row[0]
                if inferred_diff % 2 == 0 and y_row[3] - y_row[2] == inferred_diff // 2:
                    y_row = [y_row[0], y_row[0] + inferred_diff // 2, *y_row[2:]]
            base_values = y_row[:3] if len(y_row) >= 3 else y_row
            if len(base_values) >= 3:
                diffs = [b - a for a, b in zip(base_values, base_values[1:])]
                if len(set(diffs)) == 1:
                    _append(f"answer={base_values[0] + (target_index - 1) * diffs[0]}")
                    table_lookup_added = True
        if is_probability_table and count_row:
            total = count_row[-1]
            favorable_candidates = [item for item in count_row[:-1] if 0 < item < total]
            if favorable_candidates:
                _append(f"{max(favorable_candidates)}/{total}")
                table_lookup_added = True

        is_difference_table = bool(re.search(r"차(?:를|이|를\s*구|를\s*구하|$)", source) or "최댓값" in source or "가장 많은" in source)
        if is_difference_table:
            def _repair_dropped_tens(values: list[int]) -> list[int]:
                if any(abs(item) >= 10 for item in values):
                    return [11 if item == 1 else 10 if item == 0 else item for item in values]
                return values

            count_row = _repair_dropped_tens(count_row)
            y_row = _repair_dropped_tens(y_row)
        is_function_table_lookup = bool(table_lookup_added and re.search(r"(?:일차함수|함수|function)", source, flags=re.IGNORECASE))
        if count_row and not is_function_table_lookup and not is_pattern_table and not is_probability_table:
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

    count_unit = r"(?:개|장|명|자루|권|쪽|마리|송이|봉지)"
    sticker_ocr_matches = re.findall(
        rf"스티커를\s*(\d{{1,3}})[8S]\s*(?:가지고|있었|있습니다).*?"
        rf"(\d+)\s*{count_unit}\s*(?:을|를)?\s*(?:더\s*)?(?:받|샀|얻|주웠|넣).*?"
        rf"(?:그중|이\s*중|그\s*중)\s*(\d+)\s*{count_unit}\s*(?:을|를)?\s*(?:사용|썼|먹|주었|꺼냈|뺐|잃)",
        source,
    )
    if sticker_ocr_matches:
        first, added, used = sticker_ocr_matches[-1]
        _append(f"{first}+{added}-{used}")

    mixed_count_matches = re.findall(
        rf"(\d+)\s*{count_unit}\s*(?:가지고|있었|있습니다|있고).*?"
        rf"(\d+)\s*{count_unit}\s*(?:을|를)?\s*(?:더\s*)?(?:받|샀|얻|주웠|넣).*?"
        rf"(?:그중|이\s*중|그\s*중)\s*(\d+)\s*{count_unit}\s*(?:을|를)?\s*(?:사용|썼|먹|주었|꺼냈|뺐|잃)",
        source,
    )
    if mixed_count_matches:
        first, added, used = mixed_count_matches[-1]
        _append(f"{_repair_korean_count_number(first)}+{added}-{used}")

    sticker_count_matches = re.findall(
        r"(?:스티커를|AEA\s*S|AEAS)\s*(\d{2,4})(?:\s*장)?\s*(?:가지고|있었|있습니다).*?"
        r"(\d+)\s*장(?:을|를)?\s*더\s*받.*?"
        r"(?:그중|이\s*중|그\s*중)\s*(\d+)\s*장(?:을|를)?\s*사용",
        source,
    )
    if sticker_count_matches:
        first, added, used = sticker_count_matches[-1]
        _append(f"{_repair_korean_count_number(first)}+{added}-{used}")

    if "규칙" in source or "빈칸" in source or "첫째" in source or "pattern" in source.lower():
        day_match = re.search(
            r"첫째\s*날\s*(\d{1,4})\s*개.*?매일\s*(\d{1,4})\s*(?:개씩|74|7)?\s*더\s*많이.*?(\d{1,2})\s*째",
            source,
        )
        if day_match:
            first, diff, nth = (_repair_korean_count_number(item) for item in day_match.groups())
            _append(f"answer={first + (nth - 1) * diff}")

        sequence_candidates: list[list[int]] = [
            [int(item) for item in re.findall(r"[-+]?\d+", sequence_text)]
            for sequence_text in re.findall(r"[-+]?\d+(?:\s*[,，]\s*[-+]?\d+){2,}", source)
        ]
        sequence_candidates.extend(
            [int(item) for item in re.findall(r"[-+]?\d+", match.group(1))]
            for match in re.finditer(r"(?<!\d)((?:[-+]?\d+\s*[,，]?\s+){3,5}[-+]?\d+)(?!\d)", source)
        )
        sequence_candidates.extend(
            [int(item) for item in re.findall(r"[-+]?\d+", match.group(1))]
            for match in re.finditer(r"(?:MAIC|MAIO|쓰시오)\D{0,20}((?:[-+]?\d+\s*[,，]?\s*){4,6})", source)
        )
        for raw_line in source.splitlines():
            if "학년" in raw_line or "expression" in raw_line.lower():
                continue
            line_numbers = [int(item) for item in re.findall(r"[-+]?\d+", raw_line)]
            if len(line_numbers) >= 4:
                sequence_candidates.append(line_numbers)
        for sequence_numbers in sequence_candidates:
            if len(sequence_numbers) < 3:
                continue
            if len(sequence_numbers) >= 5:
                trial = sequence_numbers[:-1]
                trial_diffs = [b - a for a, b in zip(trial, trial[1:])]
                if trial_diffs and len(set(trial_diffs)) == 1 and sequence_numbers[-1] != trial[-1] + trial_diffs[0]:
                    base_numbers = trial
                else:
                    base_numbers = sequence_numbers
            else:
                base_numbers = sequence_numbers
            if len(base_numbers) < 3:
                continue
            diffs = [b - a for a, b in zip(base_numbers, base_numbers[1:])]
            if diffs and len(set(diffs)) == 1 and diffs[0] != 0:
                _append(f"answer={base_numbers[-1] + diffs[0]}")
                break

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

    measure_match = re.search(
        r"길이가\s*(\d+)\s*(?:cm|cme|cms|0{2,}7|00).*?그중\s*(\d+)\s*(?:cm|cme|cms|0{2,}7|00).*?잘라",
        source,
        flags=re.IGNORECASE,
    )
    if measure_match:
        total, used = measure_match.groups()
        _append(f"{total}-{used}")

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

    line_formula_match = re.search(
        r"(?:직선의\s*식은|일차함수|함수|function|전체\s*개수).*?(?:\by\s*=|식은\s*=|식\s*=)\s*([0-9xXKk+\-*/^().\s]+?)(?:입니다|입니|에서|일\s*때|로\s*구하|을|를|의|[.:;]|$)",
        source,
        flags=re.IGNORECASE,
    )
    if line_formula_match:
        rhs = _clean_linear_rhs(line_formula_match.group(1))
        if rhs and ("x" in rhs.lower() or re.fullmatch(r"[-+]?\d+[+\-]\d+", rhs)):
            _append(f"y={rhs}")
    messy_line_match = re.search(r"\by\s*=\s*([-+]?\d+\s*x\s*[+\-]\s*\d+)", source, flags=re.IGNORECASE)
    if messy_line_match:
        rhs = _clean_linear_rhs(messy_line_match.group(1))
        if rhs and "x" in rhs.lower():
            _append(f"y={rhs}")

    if any(token in source.lower() for token in ("함수", "일차식", "function", "직선")) and re.search(r"\by\s*=", source, flags=re.IGNORECASE):
        match = re.search(r"\by\s*=\s*([0-9xXKk+\-*/^().\s]+?)(?:입니다|입니|에서|일\s*때|로\s*구하|을|를|의|[.:;]|$)", source, flags=re.IGNORECASE)
        if match:
            rhs = _clean_linear_rhs(match.group(1))
            if rhs and ("x" in rhs.lower() or re.fullmatch(r"[-+]?\d+[+\-]\d+", rhs)):
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

    velocity_match = re.search(
        r"(?:v\s*(?:\(|i)?\s*t\s*\)?|속도\s*함수.*?=)\s*([-+]?[\doO]+)\s*t\s*([+-]\s*\d+).*?t\s*=\s*([-+]?\d+)",
        source,
        flags=re.IGNORECASE,
    )
    if velocity_match:
        coefficient, constant, target = velocity_match.groups()
        coefficient = coefficient.replace("o", "6").replace("O", "6")
        _append(f"{coefficient}*{target}{constant.replace(' ', '')}")
    else:
        velocity_formula = re.search(
            r"(?:v\s*(?:\(|i)?\s*t\s*\)?|속도\s*함수.*?=)\s*([-+]?[\doO]+)\s*t\s*([+-]\s*\d+)",
            source,
            flags=re.IGNORECASE,
        )
        velocity_target = re.search(r"t\s*=\s*([-+]?\d+).*?순간속도", source, flags=re.IGNORECASE)
        if velocity_formula and velocity_target:
            coefficient, constant = velocity_formula.groups()
            coefficient = coefficient.replace("o", "6").replace("O", "6")
            _append(f"{coefficient}*{velocity_target.group(1)}{constant.replace(' ', '')}")

    position_match = re.search(
        r"s\s*\(\s*t\s*\)\s*=\s*([-+]?\d+)\s*t\s*(?:\^|\*)\s*2\s*([+-]\s*\d+)?\s*t?.*?t\s*=\s*([-+]?\d+)",
        source,
        flags=re.IGNORECASE,
    )
    if position_match:
        coefficient, constant, target = position_match.groups()
        constant_value = int(str(constant or "0").replace(" ", "") or "0")
        _append(f"2*{coefficient}*{target}{constant_value:+d}")

    integral_match = re.search(
        r"f\s*\(\s*x\s*\)\s*=\s*([-+]?\d{1,3})\]?\s*.*?0\s*<=\s*[x*]\s*<=\s*([-+]?\d+)",
        source,
        flags=re.IGNORECASE,
    )
    if integral_match:
        height_raw, width = integral_match.groups()
        height = height_raw
        if len(height) >= 2 and height.endswith("2"):
            height = height[:-1]
        _append(f"{height}*{width}")

    match = re.search(r"공\s*(\d+)\s*개.*?빨간\s*공이\s*(\d+)\s*개", source)
    if match:
        total, red = match.groups()
        _append(f"{red}/{total}")
    match = re.search(
        r"공이\s*(\d{1,4})(?:\s*(?:개|74|7\]|\]))?\s*있고.*?당첨.*?(\d+)\s*개",
        source,
    )
    if match:
        total, winning = match.groups()
        _append(f"{winning}/{_repair_korean_count_number(total)}")

    fraction_word_match = re.search(
        r"(?:물|=|S)?\s*(\d+)\s*(?:/|7)\s*(\d+)\s*(?:L|l|니다|LS|LB|LO)?\s*와\s*(\d+)\s*(?:/|7)\s*(\d+)",
        source,
        flags=re.IGNORECASE,
    )
    if fraction_word_match:
        a_num, a_den, b_num, b_den = fraction_word_match.groups()
        _append(f"{a_num}/{a_den}+{b_num}/{b_den}")

    for match in re.finditer(r"((?:\d{2,3}[\s,，]+){3,}\d{2,3})\s*의?\s*평균", source):
        average_numbers = [int(item) for item in re.findall(r"\d{2,3}", match.group(1))]
        if len(average_numbers) >= 4:
            _append(f"({'+'.join(str(item) for item in average_numbers)})/{len(average_numbers)}")

    for raw_line in source.splitlines():
        if "평균" not in raw_line or "학년" in raw_line or "statistics" in raw_line.lower():
            continue
        average_numbers = [int(item) for item in re.findall(r"(?<![a-zA-Z])\d{2,3}", raw_line)]
        if len(average_numbers) >= 4:
            _append(f"({'+'.join(str(item) for item in average_numbers)})/{len(average_numbers)}")

    average_block_match = re.search(r"평균.{0,40}?((?:\d{1,3}[\s,，]+){3,}\d{1,3})", source)
    if average_block_match:
        average_numbers = [int(item) for item in re.findall(r"\d{1,3}", average_block_match.group(1))]
        if len(average_numbers) >= 4:
            _append(f"({'+'.join(str(item) for item in average_numbers)})/{len(average_numbers)}")

    statistic_sequences = [
        [int(item) for item in re.findall(r"\d+", match.group(0))]
        for match in re.finditer(r"\d{1,3}(?:\s*,\s*\d{1,3}){3,7}", source)
    ]
    statistic_sequences = [items for items in statistic_sequences if len(items) >= 4]
    if statistic_sequences and ("평균" in source or ("자료" in source and "statistics" in source.lower())):
        average_numbers = max(statistic_sequences, key=lambda items: (len(items), sum(1 for value in items if 10 <= abs(value) <= 150)))
        _append(f"({'+'.join(str(item) for item in average_numbers)})/{len(average_numbers)}")
    elif "평균" in source:
        average_numbers = [int(item) for item in re.findall(r"(?<![a-zA-Z])\d{2,3}", source)]
        if len(average_numbers) >= 3:
            _append(f"({'+'.join(str(item) for item in average_numbers)})/{len(average_numbers)}")

    rect_metric_patterns = (
        (
            r"가로(?:가|는)?\s*([-+]?\d+)\s*(?:cm|㎝|센티미터)?\w*.{0,80}?"
            r"세로(?:가|는)?\s*([-+]?\d+)\s*(?:cm|㎝|센티미터)?\w*.{0,120}?(넓이|둘레)",
            "width_first",
        ),
        (
            r"세로(?:가|는)?\s*([-+]?\d+)\s*(?:cm|㎝|센티미터)?\w*.{0,80}?"
            r"가로(?:가|는)?\s*([-+]?\d+)\s*(?:cm|㎝|센티미터)?\w*.{0,120}?(넓이|둘레)",
            "height_first",
        ),
    )
    for pattern, order in rect_metric_patterns:
        match = re.search(pattern, source, flags=re.IGNORECASE)
        if not match:
            continue
        first, second, metric = match.groups()
        width, height = (first, second) if order == "width_first" else (second, first)
        if metric == "넓이":
            _append(f"{width}*{height}")
        else:
            _append(f"2*({width}+{height})")

    rect_metric_match = re.search(r"rectangle_width\s*(\d+)\s*rectangle_height\s*(\d+)", source, flags=re.IGNORECASE)
    if rect_metric_match:
        width, height = rect_metric_match.groups()
        perimeter_question = bool(re.search(r"직사각형.{0,20}둘레|둘레(?:를|의)\s*구", source))
        area_question = bool(re.search(r"직사각형.{0,20}넓이|넓이(?:를|의)\s*구|rectangle_area", source))
        if perimeter_question and not area_question:
            _append(f"2*({width}+{height})")
        else:
            _append(f"{width}*{height}")

    area_match = re.search(r"f\(\s*x\s*\)\s*=\s*([-+]?\d+).*?0\s*<=\s*(?:x|[*])\s*<=\s*([-+]?\d+).*?넓이", source, flags=re.IGNORECASE)
    if area_match:
        height, width = area_match.groups()
        _append(f"{height}*{width}")

    poly_match = re.search(r"f\(\s*x\s*\)\s*=\s*([0-9xX+\-*/^().%\s]+)", source, flags=re.IGNORECASE)
    eval_match = re.search(r"(?:f\s*)?\(\s*([-+]?\d+)\s*\)\s*(?:의|2[1lI|]|값)", source, flags=re.IGNORECASE)
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

    limit_match = re.search(r"lim\s*x\s*->\s*([-+]?\d+)", source, flags=re.IGNORECASE)
    if limit_match:
        _append(f"x={limit_match.group(1)}")

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


def _merge_expression_candidates(*texts: str, school_level: str | None = None) -> list[str]:
    merged: list[str] = []
    for text in texts:
        for item in [
            *_infer_semantic_expression_candidates(text, school_level=school_level),
            *_extract_expression_candidates(text),
        ]:
            if item and item not in merged:
                merged.append(item)
    return merged[:6]


def _repair_visual_problem_statement_line(line: str, full_text: str) -> str:
    cleaned = str(line or "").strip()
    if "그래프" in cleaned and (
        "y=f(x)" in full_text
        or re.search(r"함수\s*(?:[7/]\s*=|[7/]\s*\()", cleaned)
        or "7=7(2)" in cleaned
    ):
        cleaned = re.sub(r"함수\s+.+?의\s+그래프", "함수 y=f(x)의 그래프", cleaned)
    return cleaned.replace("옮은", "옳은")


def _extract_korean_problem_statement(content_text: str) -> str:
    full_text = str(content_text or "")
    selected: list[str] = []
    for raw_line in full_text.splitlines():
        line = re.sub(r"\s+", " ", str(raw_line or "")).strip(" .,:;")
        if not line or not re.search(r"[가-힣]", line):
            continue
        if re.match(r"^[ㄱ-ㅎ]\s*[.,]", line):
            continue
        if re.match(r"^(?:[①-⑩]|\(?\d+\)|[0O]{1,3}\))", line):
            continue
        if any(token in line for token in ("그래프", "그림", "구하", "값은", "옳은", "옮은", "고른", "함수", "빈칸", "알맞은", "몇")):
            repaired = _repair_visual_problem_statement_line(line, full_text)
            if repaired not in selected:
                selected.append(repaired)
        if len(selected) >= 2:
            break
    return " ".join(selected).strip()


def _is_weak_problem_statement(statement: str, content_text: str) -> bool:
    text = str(statement or "").strip()
    if not text:
        return True
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", text):
        return True
    if re.fullmatch(r"[xy]\s*=\s*[-+]?\d+(?:\.\d+)?", text, flags=re.IGNORECASE):
        return True
    if re.fullmatch(r"answer\s*=\s*[-+]?\d+(?:\.\d+)?", text, flags=re.IGNORECASE):
        return True
    return bool(re.search(r"[가-힣]", str(content_text or ""))) and not bool(re.search(r"[가-힣]", text)) and len(text) <= 8


def _build_problem_text(content_text: str, expressions: list[str]) -> str:
    selected = select_problem_statement(content_text, expressions)
    if _is_weak_problem_statement(selected, content_text):
        statement = _extract_korean_problem_statement(content_text)
        if statement:
            selected = statement
    primary_expression = str((expressions or [""])[0] or "").strip()
    sequence_match = SEQUENCE_LOG_PRODUCT_EXPR_RE.fullmatch(primary_expression.replace(" ", ""))
    if sequence_match:
        base = sequence_match.group("base")
        start = sequence_match.group("start")
        increment = sequence_match.group("increment")
        count = sequence_match.group("count")
        return f"a1={start}, log_{base}(a_(n+1))={increment}+log_{base}(a_n), a1*...*a{count}={base}^k 일 때 k의 값은?"
    if primary_expression and "^(" in primary_expression and is_fractional_power_ocr_statement(selected):
        return f"{primary_expression} 의 값은?"
    return _repair_statement_assignments_from_expressions(selected, expressions)


def _repair_statement_assignments_from_expressions(statement: str, expressions: list[str]) -> str:
    text = str(statement or "").strip()
    if not text:
        return text

    if any(re.match(r"\s*y\s*=", str(expression or ""), flags=re.IGNORECASE) for expression in expressions or []):
        text = re.sub(r"\\+\s*의", "y의", text)

    assignments: dict[str, list[str]] = {}
    for expression in expressions or []:
        match = re.fullmatch(r"\s*([xy])\s*=\s*([+\-]?\d{1,2})(?:\.0+)?\s*", str(expression or ""))
        if not match:
            continue
        variable, value = match.groups()
        assignments.setdefault(variable.lower(), []).append(value)

    if not assignments:
        return text

    def _replace(match: re.Match[str]) -> str:
        variable = match.group(1).lower()
        noisy_value = match.group(2)
        candidates = assignments.get(variable, [])
        for candidate in candidates:
            if noisy_value.startswith(candidate) and len(noisy_value) > len(candidate):
                return f"{variable}={candidate}"
        return match.group(0)

    return re.sub(r"\b([xy])\s*=\s*([+\-]?\d{3,})\b", _replace, text, flags=re.IGNORECASE)


def _expression_variants(expr: str) -> list[str]:
    variants: list[str] = []

    def _append(candidate: str) -> None:
        text = str(candidate or "").strip()
        if text and text not in variants:
            variants.append(text)

    raw = _normalize_repaired_text(expr)
    _append(raw)
    _append(_INLINE_MULTIPLY_RE.sub("*", raw))

    for match in SQRT_CUBERT_PAIR_RE.finditer(raw):
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
        normalized = re.sub(r"(?<![0-9A-Za-z*])\*\s*2", "x**2", normalized)
        normalized = re.sub(r"(?<=\d)\*(?=\s*[+\-=])", "x", normalized)
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


def _is_numeric_solver_candidate(expr: str, raw_source: str) -> bool:
    compact = str(expr or "").strip()
    if not compact:
        return False
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", compact):
        return False
    source = str(raw_source or "")
    if re.search(r"[가-힣]", source) and not re.search(
        r"\d\s*(?:[+\-*/^]|[×÷])\s*\d|(?:sqrt|log)\s*\(|√|\^\s*\(|\d+\s*[°º]",
        source,
        flags=re.IGNORECASE,
    ):
        return False
    identifier_stripped = re.sub(r"\b(?:sqrt|log|pi)\b", "", compact, flags=re.IGNORECASE)
    if re.search(r"[A-Za-z가-힣]", identifier_stripped):
        return False
    return bool(
        re.search(r"(?:\d|\)|pi)\s*(?:\*\*|[+\-*/])\s*(?:\d|\(|sqrt|log|pi)", compact, flags=re.IGNORECASE)
        or re.search(r"(?:sqrt|log)\s*\(", compact, flags=re.IGNORECASE)
    )


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


def _integer_log(value: int, base: int) -> int | None:
    if base <= 1 or value <= 0:
        return None
    power = 0
    current = 1
    while current < value:
        current *= base
        power += 1
    return power if current == value else None


def _solve_sequence_log_product(problem: ProblemSchema) -> dict[str, Any] | None:
    sources = [
        *(str(item or "") for item in problem.expressions or []),
        str(problem.normalized_problem_text or ""),
    ]
    for source in sources:
        match = SEQUENCE_LOG_PRODUCT_EXPR_RE.fullmatch(str(source or "").replace(" ", ""))
        if not match:
            continue
        base = int(match.group("base"))
        start = int(match.group("start"))
        increment = int(match.group("increment"))
        count = int(match.group("count"))
        start_power = _integer_log(start, base)
        if start_power is None:
            continue
        exponent = count * start_power + increment * count * (count - 1) // 2
        computed = str(exponent)
        return {
            "solver_name": "sequence_log_product_solver",
            "computed_answer": computed,
            "steps": [
                f"log_{base}(a_(n+1))={increment}+log_{base}(a_n)이므로 a_(n+1)={base ** increment}*a_n으로 정리했어.",
                f"a1={start}={base}^{start_power}라서 a_n의 지수는 등차수열로 늘어나.",
                f"a1부터 a{count}까지 곱하면 지수 합은 {computed}이야.",
            ],
            "confidence": 0.86,
        }
    return None


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
                if lhs == "x" and re.fullmatch(r"[+\-]?(?:\d+(?:\.\d+)?|\.\d+)", rhs):
                    try:
                        candidate_x = _safe_eval(rhs)
                    except Exception:
                        continue
                    if x_value is None or (abs(x_value) > 50 and abs(candidate_x) <= 50):
                        x_value = candidate_x
                elif lhs == "y" and y_value is None and re.fullmatch(r"[+\-]?(?:\d+(?:\.\d+)?|\.\d+)", rhs):
                    try:
                        y_value = _safe_eval(rhs)
                    except Exception:
                        continue
                elif lhs == "y" and function_rhs is None and "x" in rhs:
                    function_rhs = rhs
            elif variable_rhs is None and "x" in expr:
                variable_rhs = expr

    if function_rhs and "기울기" in str(problem.normalized_problem_text or ""):
        try:
            slope = _safe_eval(function_rhs, {"x": 1.0}) - _safe_eval(function_rhs, {"x": 0.0})
            computed = _format_number(slope)
        except Exception:
            computed = ""
        if computed:
            return {
                "solver_name": "line_slope_solver",
                "computed_answer": computed,
                "steps": [
                    f"직선식을 y={function_rhs} 형태로 정리했어.",
                    f"x의 계수, 즉 기울기는 {computed}야.",
                ],
                "confidence": 0.83,
            }

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


def _requires_visual_graph_reasoning(problem: ProblemSchema) -> bool:
    source = "\n".join(
        [
            str(problem.normalized_problem_text or ""),
            *(str(item or "") for item in problem.expressions or []),
            *(str(item or "") for item in problem.choices or []),
            *(str(item or "") for item in problem.source_text_candidates or []),
        ]
    )
    has_visual_graph = any(token in source for token in ("그래프", "그림")) and re.search(
        r"y\s*=\s*f\s*\(\s*x\s*\)|lim|극한|연속|\|/?f\(",
        source,
        flags=re.IGNORECASE,
    )
    has_statement_choices = problem.question_type == "multiple_choice" or bool(re.search(r"[ㄱㄴㄷ]\s*[.,]", source))
    return bool(has_visual_graph and has_statement_choices)


def _compute_answer(problem: ProblemSchema) -> dict[str, Any]:
    if _requires_visual_graph_reasoning(problem):
        return {
            "solver_name": "visual_graph_guard",
            "computed_answer": "",
            "steps": [
                "그래프의 열린 점과 닫힌 점, 좌우 극한을 원본에서 직접 판정해야 하는 문제야.",
                "기본 OCR만으로는 ㄱ, ㄴ, ㄷ의 참거짓을 안전하게 확정하지 않았어.",
            ],
            "confidence": 0.0,
        }

    trig_source = " ".join([str(problem.normalized_problem_text or ""), *(problem.expressions or [])]).lower()
    if problem.math_topic == "trigonometry" and re.search(r"\b(?:sin|cos|tan)\b|π|\\pi\b", trig_source):
        result = trig_solver.solve(problem)
        result["solver_name"] = "trig_solver"
        return result

    sequence_log_result = _solve_sequence_log_product(problem)
    if sequence_log_result is not None:
        return sequence_log_result

    for source in problem.expressions or []:
        text_answer_match = re.fullmatch(r"\s*answer_text\s*=\s*(.+?)\s*", str(source or ""), flags=re.IGNORECASE)
        if text_answer_match:
            computed = text_answer_match.group(1).strip()
            return {
                "solver_name": "visual_template_solver",
                "computed_answer": computed,
                "steps": [
                    "그림을 직접 조작하는 초등 시각 문제라서 문항 템플릿을 먼저 확인했어.",
                    f"정답 후보는 {computed}야.",
                ],
                "confidence": 0.86,
            }
        answer_match = re.fullmatch(r"\s*answer\s*=\s*([-+]?\d+(?:/\d+)?)\s*", str(source or ""), flags=re.IGNORECASE)
        if answer_match:
            computed = answer_match.group(1)
            return {
                "solver_name": "table_lookup_solver",
                "computed_answer": computed,
                "steps": [
                    "표나 규칙에서 직접 읽어낸 답 후보를 우선 확인했어.",
                    f"값은 {computed}야.",
                ],
                "confidence": 0.88,
            }

    has_quadratic_expression = any(
        re.search(r"x\s*(?:\^|\*)\s*2|x²|(?<![0-9A-Za-z*])\*\s*2", str(source or ""), flags=re.IGNORECASE)
        for source in problem.expressions or []
    )
    if problem.math_topic in {"quadratic", "quadratic_function"} or has_quadratic_expression:
        for source in problem.expressions or []:
            raw_source = str(source or "")
            if not re.search(r"x\s*(?:\^|\*)\s*2|x²|(?<![0-9A-Za-z*])\*\s*2", raw_source, flags=re.IGNORECASE):
                continue
            for variant in _expression_variants(raw_source):
                expr = _normalize_for_sympy(variant)
                if not expr or "=" not in expr:
                    continue
                try:
                    lhs, rhs = expr.split("=", 1)
                    sympy_result = solve_equation_with_sympy_worker(lhs, rhs, "x")
                    computed = str(sympy_result.get("answer") or "").strip() if sympy_result.get("status") == "ok" else ""
                    if not computed:
                        computed = _solve_polynomial_equation(lhs, rhs, "x")
                    if not computed:
                        continue
                    return {
                        "solver_name": "sympy_worker_equation_solver" if sympy_result.get("status") == "ok" else "quadratic_equation_solver",
                        "computed_answer": computed,
                        "steps": [
                            "이차항이 살아 있는 식 후보를 먼저 골랐어.",
                            "x에 대한 이차방정식으로 풀었어.",
                            f"해는 {computed}야.",
                        ],
                        "confidence": 0.88,
                    }
                except Exception:
                    continue

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
                    sympy_result = solve_equation_with_sympy_worker(lhs, rhs, symbol_name)
                    if sympy_result.get("status") == "ok":
                        computed = str(sympy_result.get("answer") or "").strip()
                    if not computed:
                        computed = _solve_polynomial_equation(lhs, rhs, symbol_name)
                    if not computed:
                        continue
                    return {
                        "solver_name": "sympy_worker_equation_solver" if sympy_result.get("status") == "ok" else "equation_solver",
                        "computed_answer": computed,
                        "steps": [
                            "식 양쪽을 같은 변수식으로 정리했어.",
                            f"{symbol_name}에 대한 방정식으로 보고 풀었어.",
                            "SymPy worker로 해를 검산했어." if sympy_result.get("status") == "ok" else "내장 방정식 풀이로 해를 검산했어.",
                            f"해는 {computed}야.",
                        ],
                        "confidence": 0.84,
                        "debug": {
                            "sympy_worker": {
                                "status": sympy_result.get("status"),
                                "engine_version": sympy_result.get("engine_version"),
                                "error": sympy_result.get("error"),
                            }
                        },
                    }

                if not _is_numeric_solver_candidate(expr, str(source or "")):
                    continue

                if "/" in expr and "**" not in expr and re.fullmatch(r"[0-9+\-*/().]+", expr):
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
    school_profile = infer_school_profile(image_path, raw_text)
    raw_text = apply_school_ocr_profile(
        raw_text,
        school_level=school_profile.school_level,
        profile=school_profile.profile,
    )
    content_text, metadata_lines = split_exam_metadata(raw_text)
    repair_debug = debug_sources.get("text_repair") or {}
    repaired_text = str(repair_debug.get("text") or "").strip() if repair_debug.get("accepted") else ""
    if repaired_text:
        repaired_text = apply_school_ocr_profile(
            repaired_text,
            school_level=school_profile.school_level,
            profile=school_profile.profile,
        )
    preferred_content = repaired_text or content_text or raw_text
    choices = parse_choices(repaired_text) or parse_choices(raw_text)
    expressions = _merge_expression_candidates(
        content_text or raw_text,
        repaired_text,
        school_level=school_profile.school_level,
    )
    problem_text = _build_problem_text(preferred_content, expressions)
    for expression in _merge_expression_candidates(
        problem_text,
        f"{problem_text}\n{preferred_content}",
        school_level=school_profile.school_level,
    ):
        if expression not in expressions:
            expressions.append(expression)
    if expressions:
        problem_text = _build_problem_text(preferred_content, expressions)
    math_topic = _detect_math_topic(preferred_content, expressions)
    if school_profile.school_level == "elementary":
        elementary_topic = _infer_elementary_topic(f"{school_profile.unit}\n{preferred_content}\n{problem_text}", expressions)
        if elementary_topic:
            math_topic = elementary_topic
    visual_template = infer_elementary_visual_template(image_path, raw_text=preferred_content)
    if visual_template is not None:
        if visual_template.expression not in expressions:
            expressions.insert(0, visual_template.expression)
        problem_text = visual_template.problem_text
        math_topic = visual_template.topic
        choices = []
    question_type = "multiple_choice" if choices else "subjective"
    confidence = min(
        1.0,
        max(
            detect_math_signal_score(problem_text),
            0.35 if expressions else 0.0,
            0.4 if choices else 0.0,
            0.48 if repaired_text else 0.0,
            visual_template.confidence if visual_template is not None else 0.0,
        ),
    )
    metadata = {
        "image_path": image_path,
        "user_query": user_query,
        "ocr_debug": debug_sources,
        "metadata_lines": metadata_lines,
        "content_hash": hashlib.sha1(Path(image_path).read_bytes()).hexdigest()[:12],
        "school_level": school_profile.school_level,
        "school_profile": school_profile.profile,
        "grade": school_profile.grade,
        "semester": school_profile.semester,
        "unit": school_profile.unit,
        "school_profile_confidence": school_profile.confidence,
        "school_profile_evidence": school_profile.evidence,
    }
    if visual_template is not None:
        metadata["visual_template"] = {
            "rule_id": visual_template.rule_id,
            "confidence": visual_template.confidence,
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
        "school_profile": school_profile.model_dump(),
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
    if solver_name == "trig_solver" and re.search(r"\b(?:sin|cos|tan)\b|π|\\pi\b", trig_source):
        solver_result = trig_solver.solve(problem)
    else:
        solver_result = _compute_answer(problem)
    solver_result["solver_name"] = str(solver_result.get("solver_name") or solver_name)

    solved: SolveResult = validate_answer(problem, solver_result)
    solved.explanation = generate_korean_tutor_response(problem, solved, user_query)
    debug_payload["solver_name"] = solved.solver_name
    debug_payload["computed_answer"] = solved.computed_answer
    debug_payload["validation_status"] = solved.validation_status
    if image_path:
        try:
            record_normalization_observation(
                image_path=image_path,
                structured_problem=problem,
                solve_result=solved,
                debug_payload=debug_payload,
            )
        except Exception as exc:
            debug_payload["normalization_learning_error"] = str(exc)

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
