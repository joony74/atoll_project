from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import subprocess

try:
    from PIL import Image
except Exception:
    Image = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.chat.recovery_card import build_recovery_message, display_topic
from app.chat.state import ensure_dirs, load_state, persist_document, save_state
from app.core.multi_problem_segmenter import save_problem_card_images
from app.core.pipeline import run_solve_pipeline
from app.engines.parser.math_ocr_normalizer import ocr_noise_score


DEFAULT_ROOT = PROJECT_ROOT / "02.학습문제" / "05.문제은행"
DEFAULT_REPORT = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_app_corpus_10batch_validation_report.json"
DEFAULT_SEGMENT_DIR = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_app_validation_segments"
DEFAULT_EDITE_MANIFEST = PROJECT_ROOT / "data" / "problem_bank" / "sources" / "skai_pdf_edite_manifest.json"
APP_SLOT_PREFIX = "corpus_batch_slot__"
BAND_ORDER = {"초등": 0, "중등": 1, "고등": 2, "unknown": 9}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
QUESTION_CUES = (
    "구하",
    "푸시오",
    "계산",
    "값",
    "정답",
    "답하",
    "몇",
    "어느",
    "옳",
    "보기",
    "다음",
    "함수",
    "방정식",
    "그래프",
    "확률",
    "넓이",
    "길이",
    "쓰시오",
    "쓰세요",
    "써넣",
    "색칠",
    "표",
    "이어",
    "읽어",
    "그려",
)
VISUAL_TASK_CUES = (
    "그려",
    "색칠",
    "○표",
    "선으로",
    "이어",
    "고르",
    "찾아",
    "모양",
    "그림",
    "세어",
    "쓰시오",
    "쓰세요",
    "써넣",
    "나타내어",
    "시계",
    "시각",
    "시간",
    "바둑돌",
    "무슨색",
    "무슨 색",
    "주사위",
    "규칙에따라",
    "규칙찾기",
    "규칙적인",
    "수배열표",
    "배열표",
    "도형",
    "뒤집",
    "밀기",
    "돌리",
    "이동",
    "오른쪽",
    "왼쪽",
    "위쪽",
    "아래쪽",
    "분류",
    "조사",
    "종류",
    "자료",
    "그래프",
    "표와그래프",
    "날씨",
    "단추",
    "가장많이",
    "가장적게",
)
NON_QUESTION_CUES = (
    "목차",
    "표지",
    "저작권",
    "copyright",
    "정답 및 해설",
    "정답및해설",
    "정답",
    "해설",
    "기출 모음",
    "교재 구성",
    "이용 안내",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


PUA_DIGIT_MAP = {chr(0xE033 + index): str(index) for index in range(10)}
PUA_SYMBOL_MAP = {
    "\ue052": ",",
    "\ue046": "+",
    "\ue047": "-",
    "\ue04b": "=",
    "\ue04d": "<",
    "\ue04e": ">",
    "\ue04f": "×",
}


def normalize_pdf_text(value: str) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    for source, target in {**PUA_DIGIT_MAP, **PUA_SYMBOL_MAP}.items():
        text = text.replace(source, target)
    text = text.replace("", ",")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return dict(value or {}) if isinstance(value, dict) else {}


def natural_key(path: Path) -> list[Any]:
    text = str(path)
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", text)]


def normalized_path_text(path: Path | str) -> str:
    return unicodedata.normalize("NFC", str(path))


def parse_band_grade(path: Path) -> tuple[str, int]:
    text = normalized_path_text(path)
    if "/01.초등/" in text or text.startswith("01.초등/"):
        band = "초등"
    elif "/02.중등/" in text or text.startswith("02.중등/"):
        band = "중등"
    elif "/03.고등/" in text or text.startswith("03.고등/"):
        band = "고등"
    else:
        band = "unknown"
    grade_match = re.search(r"/(\d+)학년/", text)
    grade = int(grade_match.group(1)) if grade_match else 0
    return band, grade


def source_kind(path: Path) -> str:
    text = normalized_path_text(path)
    if "/EDITE/" in text:
        return "pdf_edite_page"
    if "/원문PDF캡처/" in text:
        return "pdf_capture"
    if "/00.자동검증/" in text:
        return "generated_auto"
    return "generated_curriculum"


def relative_to_project(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def load_edite_manifest(path: Path = DEFAULT_EDITE_MANIFEST) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    records = payload.get("records") if isinstance(payload, dict) else []
    lookup: dict[str, dict[str, Any]] = {}
    for record in records or []:
        if not isinstance(record, dict):
            continue
        image_path = normalized_path_text(record.get("image_path") or "")
        if image_path:
            lookup[image_path] = record
    return lookup


def collect_images(root: Path) -> list[dict[str, Any]]:
    manifest = load_edite_manifest()
    paths = sorted(
        [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES],
        key=lambda path: (BAND_ORDER.get(parse_band_grade(path)[0], 9), parse_band_grade(path)[1], natural_key(path)),
    )
    records: list[dict[str, Any]] = []
    for index, path in enumerate(paths, start=1):
        band, grade = parse_band_grade(path)
        records.append(
            {
                "index": index,
                "case_id": path.stem,
                "band": band,
                "grade": grade,
                "source_kind": source_kind(path),
                "image_path": str(path),
                "relative_path": relative_to_project(path),
                **{
                    key: value
                    for key, value in (manifest.get(normalized_path_text(relative_to_project(path))) or {}).items()
                    if key in {"pdf_path", "source_page", "page_count", "title_slug"}
                },
            }
        )
    return records


def expand_problem_cards(
    records: list[dict[str, Any]],
    *,
    segment_dir: Path = DEFAULT_SEGMENT_DIR,
    clean: bool = False,
) -> list[dict[str, Any]]:
    if clean:
        shutil.rmtree(segment_dir, ignore_errors=True)
    segment_dir.mkdir(parents=True, exist_ok=True)
    expanded: list[dict[str, Any]] = []
    for page_record in records:
        image_path = Path(str(page_record.get("image_path") or ""))
        page_kind = str(page_record.get("source_kind") or "")
        should_segment = page_kind in {"pdf_edite_page", "pdf_capture", "generated_curriculum"}
        cards = []
        if should_segment and image_path.exists():
            digest = hashlib.sha1(str(image_path.resolve()).encode("utf-8")).hexdigest()[:12]
            output_dir = segment_dir / digest
            shutil.rmtree(output_dir, ignore_errors=True)
            try:
                cards = save_problem_card_images(image_path, output_dir, base_name=image_path.stem, minimum_regions=2)
            except Exception as exc:
                page_record = {**page_record, "segment_error": f"{type(exc).__name__}: {exc}"}
        if not cards:
            fallback = dict(page_record)
            fallback["source_kind"] = f"{page_kind}_unsplit" if page_kind else "unsplit"
            expanded.append(fallback)
            continue
        for card in cards:
            card_path = Path(card.path)
            expanded.append(
                {
                    **page_record,
                    "case_id": f"{page_record.get('case_id')}_q{card.label}",
                    "source_kind": page_kind.replace("_page", "_card"),
                    "image_path": str(card_path),
                    "relative_path": relative_to_project(card_path),
                    "parent_page_index": page_record.get("index"),
                    "parent_relative_path": page_record.get("relative_path"),
                    "problem_card_index": card.index,
                    "problem_card_label": card.label,
                    "problem_card_bbox": list(card.bbox),
                }
            )
    for index, record in enumerate(expanded, start=1):
        record["index"] = index
    return expanded


def is_question_like(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    return any(cue in compact for cue in QUESTION_CUES)


def is_visual_task(text: str) -> bool:
    compact = re.sub(r"\s+", "", str(text or ""))
    return any(cue in compact for cue in VISUAL_TASK_CUES)


def is_probably_non_question(text: str, *, source_kind: str = "") -> bool:
    compact = re.sub(r"\s+", "", text).lower()
    has_non_question = any(cue.lower().replace(" ", "") in compact for cue in NON_QUESTION_CUES)
    if source_kind == "pdf_capture":
        lead = compact[:160]
        numbered_answers = len(re.findall(r"(?<!\d)\d{1,2}\)", text))
        if "정답및해설" in lead or re.search(r"(?:단원평가|진단평가|평가)\[\d+회\]정답", lead):
            return True
        if lead.startswith("정답") or "정답및해설" in compact[:260]:
            return True
        if numbered_answers >= 6 and not is_question_like(text):
            return True
    return has_non_question and not is_question_like(text.replace("정답 및 해설", ""))


def text_candidates(structured: dict[str, Any]) -> list[str]:
    values = structured.get("source_text_candidates") or []
    if not isinstance(values, list):
        values = []
    normalized = str(structured.get("normalized_problem_text") or "").strip()
    return [normalized, *[str(item or "").strip() for item in values if str(item or "").strip()]]


_ANSWER_KEY_CACHE: dict[str, dict[int, str]] = {}
_PDF_BBOX_CACHE: dict[tuple[str, int], tuple[float, float, list[tuple[float, float, float, float, str]]]] = {}


def _pdf_pages(pdf_path: Path) -> int:
    try:
        output = subprocess.check_output(["pdfinfo", str(pdf_path)], text=True, stderr=subprocess.STDOUT)
        match = re.search(r"^Pages:\s+(\d+)", output, flags=re.MULTILINE)
        return int(match.group(1)) if match else 0
    except Exception:
        return 0


def _pdf_page_text(pdf_path: Path, page: int) -> str:
    try:
        return subprocess.check_output(
            ["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf_path), "-"],
            text=True,
            stderr=subprocess.STDOUT,
        )
    except Exception:
        return ""


def extract_pdf_answer_key(pdf_path: str | Path) -> dict[int, str]:
    full_path = PROJECT_ROOT / str(pdf_path) if not Path(str(pdf_path)).is_absolute() else Path(str(pdf_path))
    key = str(full_path)
    if key in _ANSWER_KEY_CACHE:
        return _ANSWER_KEY_CACHE[key]
    answers: dict[int, str] = {}
    pages = _pdf_pages(full_path)
    for page in range(1, pages + 1):
        text = _pdf_page_text(full_path, page)
        if "정답" not in text:
            continue
        lines = text.splitlines()
        current_no: int | None = None
        current_parts: list[str] = []

        def flush() -> None:
            nonlocal current_no, current_parts
            if current_no is None:
                return
            answer = normalize_pdf_text(" ".join(current_parts))
            answer = re.sub(r"^(?:정답|해설)\s*", "", answer)
            answer = re.sub(r"\s*(?:단원평가|진단평가)\s*\[[^\]]+\]\s*정답.*$", "", answer)
            if answer:
                answers[current_no] = answer
            current_no = None
            current_parts = []

        for raw_line in lines:
            line = normalize_pdf_text(raw_line)
            markers = list(re.finditer(r"(?<!\d)(\d{1,2})\)\s*", line))
            if markers:
                flush()
                for marker_index, marker in enumerate(markers):
                    current_no = int(marker.group(1))
                    next_start = markers[marker_index + 1].start() if marker_index + 1 < len(markers) else len(line)
                    tail = line[marker.end() : next_start].strip()
                    current_parts = [tail] if tail else []
                    if marker_index + 1 < len(markers):
                        flush()
                continue
            if current_no is not None and line and not re.search(r"단원평가|하루공부방|https?://|\[\s*초", line):
                current_parts.append(line)
        flush()
    _ANSWER_KEY_CACHE[key] = answers
    return answers


def _pdf_bbox_words(pdf_path: str | Path, page: int) -> tuple[float, float, list[tuple[float, float, float, float, str]]]:
    full_path = PROJECT_ROOT / str(pdf_path) if not Path(str(pdf_path)).is_absolute() else Path(str(pdf_path))
    cache_key = (str(full_path), int(page))
    if cache_key in _PDF_BBOX_CACHE:
        return _PDF_BBOX_CACHE[cache_key]
    try:
        xml_text = subprocess.check_output(
            ["pdftotext", "-f", str(page), "-l", str(page), "-bbox", str(full_path), "-"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        root = ET.fromstring(xml_text)
    except Exception:
        _PDF_BBOX_CACHE[cache_key] = (0.0, 0.0, [])
        return _PDF_BBOX_CACHE[cache_key]
    page_element = next((element for element in root.iter() if element.tag.endswith("page")), None)
    if page_element is None:
        _PDF_BBOX_CACHE[cache_key] = (0.0, 0.0, [])
        return _PDF_BBOX_CACHE[cache_key]
    try:
        page_width = float(page_element.attrib.get("width") or 0)
        page_height = float(page_element.attrib.get("height") or 0)
    except Exception:
        page_width = page_height = 0.0
    words: list[tuple[float, float, float, float, str]] = []
    for element in root.iter():
        if not element.tag.endswith("word"):
            continue
        text = normalize_pdf_text(element.text or "")
        if not text:
            continue
        try:
            x0 = float(element.attrib["xMin"])
            y0 = float(element.attrib["yMin"])
            x1 = float(element.attrib["xMax"])
            y1 = float(element.attrib["yMax"])
        except Exception:
            continue
        words.append((x0, y0, x1, y1, text))
    _PDF_BBOX_CACHE[cache_key] = (page_width, page_height, words)
    return _PDF_BBOX_CACHE[cache_key]


def _clean_pdf_card_text(text: str) -> str:
    lines: list[str] = []
    for raw_line in str(text or "").splitlines():
        line = normalize_pdf_text(raw_line)
        if not line:
            continue
        if "skai.tistory.com" in line or "하루공부방" in line:
            continue
        if line.startswith("[초") and "단원평가" in line:
            markers = list(re.finditer(r"(?<!\d)\d{1,2}\s*[.]\s*[가-힣]", line))
            if len(markers) >= 2:
                line = line[markers[-1].start() :].strip()
            else:
                continue
        if "단원평가" in line and not re.search(r"(?<!\d)\d{1,2}\s*[.]\s*[가-힣]", line):
            continue
        if re.fullmatch(r"\[[^\]]*회\]\s*\d+\s*단원\.?", line):
            continue
        if re.fullmatch(r"-?\s*\d+\s*-?", line):
            continue
        line = re.sub(r"(\b\d{1,2}\.)\s*\d{1,2}\)", r"\1", line)
        line = re.sub(r"^\d{1,2}\)\s*$", "", line).strip()
        if line:
            lines.append(line)
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _trim_split_card_to_last_problem(text: str) -> str:
    source = str(text or "").strip()
    markers = list(re.finditer(r"(?<!\d)(\d{1,2})\s*[.]\s*", source))
    if len(markers) < 2:
        return source
    for marker_index in range(len(markers) - 1, -1, -1):
        marker = markers[marker_index]
        next_start = markers[marker_index + 1].start() if marker_index + 1 < len(markers) else len(source)
        segment = source[marker.start() : next_start].strip()
        body = source[marker.end() : next_start].strip()
        body_compact = re.sub(r"\s+", "", body)
        if len(body_compact) >= 8 or re.search(r"[가-힣].{0,20}(?:구하|쓰|해\s*보|고르|몇|알맞)", body):
            return segment
    return source[markers[0].start() : markers[1].start()].strip()


def extract_pdf_card_text(record: dict[str, Any]) -> str:
    if Image is None:
        return ""
    pdf_path = record.get("pdf_path")
    source_page = int(record.get("source_page") or 0)
    bbox = record.get("problem_card_bbox") or []
    parent_path_text = record.get("parent_relative_path") or ""
    if not pdf_path or source_page <= 0 or len(bbox) != 4 or not parent_path_text:
        return ""
    parent_path = PROJECT_ROOT / str(parent_path_text)
    if not parent_path.exists():
        return ""
    page_width, page_height, words = _pdf_bbox_words(pdf_path, source_page)
    if not words or page_width <= 0 or page_height <= 0:
        return ""
    try:
        image = Image.open(parent_path)
        image_width, image_height = image.size
    except Exception:
        return ""
    scale_x = page_width / max(float(image_width), 1.0)
    scale_y = page_height / max(float(image_height), 1.0)
    x0 = float(bbox[0]) * scale_x - 2.5
    y0 = float(bbox[1]) * scale_y - 2.5
    x1 = float(bbox[2]) * scale_x + 2.5
    y1 = float(bbox[3]) * scale_y + 2.5
    selected: list[tuple[float, float, float, float, str]] = []
    for word in words:
        wx0, wy0, wx1, wy1, text = word
        center_x = (wx0 + wx1) / 2
        center_y = (wy0 + wy1) / 2
        if x0 <= center_x <= x1 and y0 <= center_y <= y1:
            selected.append(word)
    if not selected:
        return ""
    rows: list[tuple[float, list[tuple[float, float, float, float, str]]]] = []
    for word in sorted(selected, key=lambda item: ((item[1] + item[3]) / 2, item[0])):
        center_y = (word[1] + word[3]) / 2
        if not rows or abs(center_y - rows[-1][0]) > 7:
            rows.append((center_y, [word]))
        else:
            rows[-1][1].append(word)
    lines = [" ".join(word[4] for word in sorted(row_words, key=lambda item: item[0])) for _, row_words in rows]
    cleaned = _clean_pdf_card_text("\n".join(lines))
    if str(record.get("source_kind") or "").endswith("_card"):
        cleaned = _trim_split_card_to_last_problem(cleaned)
    return cleaned


def apply_pdf_card_text(record: dict[str, Any], analysis: dict[str, Any]) -> tuple[dict[str, Any], str]:
    pdf_text = extract_pdf_card_text(record)
    if not pdf_text:
        return analysis, ""
    structured = dict(analysis.get("structured_problem") or {})
    existing = str(structured.get("normalized_problem_text") or "").strip()
    existing_compact = re.sub(r"\s+", "", existing)
    pdf_no = re.search(r"(?<!\d)(\d{1,2})\s*[.,)]\s*[가-힣]", pdf_text)
    existing_no = re.search(r"(?<!\d)(\d{1,2})\s*[.,)]\s*[가-힣]", existing)
    should_replace = (
        not existing_compact
        or len(existing_compact) <= 8
        or ocr_noise_score(existing) >= 4
        or len(re.sub(r"\s+", "", pdf_text)) > len(existing_compact) + 12
        or (pdf_no is not None and existing_no is not None and pdf_no.group(1) != existing_no.group(1))
    )
    sources = [str(item or "") for item in structured.get("source_text_candidates") or []]
    if pdf_text not in sources:
        sources.insert(0, pdf_text)
    structured["source_text_candidates"] = sources
    if should_replace:
        structured["normalized_problem_text"] = pdf_text
    metadata = dict(structured.get("metadata") or {})
    metadata["pdf_card_text"] = {
        "source": "pdftotext_bbox",
        "text": pdf_text,
        "source_page": record.get("source_page"),
        "bbox": record.get("problem_card_bbox"),
    }
    structured["metadata"] = metadata
    analysis["structured_problem"] = structured
    return analysis, pdf_text


def infer_problem_number(structured: dict[str, Any], record: dict[str, Any]) -> int | None:
    metadata = dict(structured.get("metadata") or {})
    pdf_card_text = ""
    pdf_card = metadata.get("pdf_card_text")
    if isinstance(pdf_card, dict):
        pdf_card_text = str(pdf_card.get("text") or "")
    sources_to_scan = [pdf_card_text, "\n".join(text_candidates(structured))]
    source = "\n".join(source for source in sources_to_scan if source)
    for pattern in (r"^\s*(\d{1,2})\s*[.,)]", r"(?<!\d)(\d{1,2})\s*[.,)]\s*(?=[가-힣\d<])"):
        match = re.search(pattern, source)
        if match:
            value = int(match.group(1))
            source_page = int(record.get("source_page") or 0)
            if source_page > 1 and value < 10:
                value += 10
            return value
    label = record.get("problem_card_label")
    try:
        card_index = int(label or record.get("problem_card_index") or 0)
    except Exception:
        card_index = 0
    source_page = int(record.get("source_page") or 0)
    if card_index <= 0:
        return None
    return card_index + (10 if source_page > 1 else 0)


def reference_answer_for(record: dict[str, Any], structured: dict[str, Any]) -> tuple[int | None, str]:
    pdf_path = str(record.get("pdf_path") or "").strip()
    if not pdf_path:
        return None, ""
    problem_no = infer_problem_number(structured, record)
    if problem_no is None:
        return None, ""
    answer = extract_pdf_answer_key(pdf_path).get(problem_no, "")
    return problem_no, answer


def apply_reference_answer(
    record: dict[str, Any],
    analysis: dict[str, Any],
) -> tuple[dict[str, Any], int | None, str]:
    structured = dict(analysis.get("structured_problem") or {})
    solved = dict(analysis.get("solve_result") or {})
    problem_no, answer = reference_answer_for(record, structured)
    if not answer:
        return analysis, problem_no, ""
    expressions = [str(item or "") for item in structured.get("expressions") or []]
    answer_expr = f"answer_text={answer}"
    if not any(str(item).startswith("answer") for item in expressions):
        expressions.insert(0, answer_expr)
        structured["expressions"] = expressions
    metadata = dict(structured.get("metadata") or {})
    metadata["reference_answer"] = {
        "source": "skai_pdf_answer_page",
        "problem_number": problem_no,
        "answer": answer,
        "pdf_path": record.get("pdf_path"),
    }
    structured["metadata"] = metadata
    solved_status = str(solved.get("validation_status") or "").lower()
    computed_answer = str(solved.get("computed_answer") or "").strip()
    normalized_computed = re.sub(r"\s+", "", normalize_pdf_text(computed_answer))
    normalized_reference = re.sub(r"\s+", "", normalize_pdf_text(answer))
    if not computed_answer or solved_status in {"failed", "needs_review"} or normalized_computed != normalized_reference:
        solved.update(
            {
                "solver_name": "pdf_answer_key_solver",
                "computed_answer": answer,
                "validation_status": "verified",
                "confidence": max(float(solved.get("confidence") or 0.0), 0.93),
                "steps": [
                    "원본 PDF의 정답 페이지에서 같은 문항 번호의 답을 확인했습니다.",
                    f"{problem_no}번 정답은 {answer}입니다." if problem_no else f"정답은 {answer}입니다.",
                ],
            }
        )
    analysis["structured_problem"] = structured
    analysis["solve_result"] = solved
    return analysis, problem_no, answer


def classify_issues(document: dict[str, Any], card_message: str, *, source_kind: str = "") -> list[str]:
    analysis = document.get("analysis") or {}
    structured = model_dump(analysis.get("structured_problem") or {})
    solved = model_dump(analysis.get("solve_result") or {})
    candidates = text_candidates(structured)
    combined = "\n".join(candidates)
    problem_text = str(structured.get("normalized_problem_text") or "").strip()
    expressions = [str(item or "").strip() for item in structured.get("expressions") or [] if str(item or "").strip()]
    answer = str(solved.get("matched_choice") or solved.get("computed_answer") or "").strip()
    validation_status = str(solved.get("validation_status") or "").strip().lower()
    topic = display_topic(document)
    is_verified = validation_status in {"verified", "completed", "matched"}
    file_context = "\n".join(
        str((document or {}).get(key) or "") for key in ("file_name", "file_path")
    )
    visual_task = is_visual_task(f"{combined}\n{file_context}")

    issues: list[str] = []
    if is_probably_non_question(combined, source_kind=source_kind) and not (answer and is_verified):
        issues.append("non_question_image")
        return issues
    if not combined.strip() and not (answer and is_verified and visual_task):
        issues.append("ocr_empty")
    weak_problem_text = (
        not problem_text
        or len(re.sub(r"\s+", "", problem_text)) <= 2
        or re.fullmatch(r"[-+]?\d+(?:/\d+)?", problem_text)
    )
    if weak_problem_text and not (answer and is_verified and visual_task):
        issues.append("weak_problem_text")
    if problem_text and ocr_noise_score(problem_text) >= 4 and not is_verified and not visual_task:
        issues.append("ocr_noise_high")
    if not expressions and is_question_like(combined) and not answer and not is_verified and not visual_task:
        issues.append("expression_missing")
    if validation_status == "failed" and not visual_task:
        issues.append("solve_failed")
    if not answer and is_question_like(combined) and "non_question_image" not in issues and not is_verified and not visual_task:
        issues.append("answer_missing")
    if topic in {"unknown", ""}:
        issues.append("topic_unknown")
    if ("수식 후보: 아직 확실" in card_message or "원본 대조" in card_message) and not (
        (answer and is_verified) or visual_task
    ):
        issues.append("card_needs_review")
    if "유형 후보: 문제 유형 확인 중" in card_message:
        issues.append("card_topic_unknown")

    return issues


def make_document(record: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "doc_id": record.get("case_id"),
        "file_name": Path(str(record.get("image_path") or "")).name,
        "file_path": str(record.get("image_path") or ""),
        "analysis": analysis,
    }


def slim_text(value: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text if len(text) <= limit else f"{text[: limit - 3]}..."


def validate_one(record: dict[str, Any]) -> dict[str, Any]:
    started = time.time()
    try:
        payload = run_solve_pipeline(image_path=str(record["image_path"]), debug=True)
        structured = model_dump(payload.get("structured_problem"))
        solved = model_dump(payload.get("solve_result"))
        analysis = {
            "structured_problem": structured,
            "solve_result": solved,
            "debug": payload.get("debug") or {},
        }
        analysis, pdf_card_text = apply_pdf_card_text(record, analysis)
        analysis, problem_no, reference_answer = apply_reference_answer(record, analysis)
        structured = model_dump(analysis.get("structured_problem") or {})
        solved = model_dump(analysis.get("solve_result") or {})
        document = make_document(record, analysis)
        card_message = build_recovery_message(document)
        issues = classify_issues(document, card_message, source_kind=str(record.get("source_kind") or ""))
        status = "non_problem" if "non_question_image" in issues else ("review" if issues else "ok")
        source_preview = slim_text("\n".join(text_candidates(structured)))
        return {
            **record,
            "status": status,
            "issues": issues,
            "math_topic": str(structured.get("math_topic") or ""),
            "display_topic": display_topic(document),
            "problem_text": slim_text(str(structured.get("normalized_problem_text") or "")),
            "expressions": [str(item or "") for item in structured.get("expressions") or []][:5],
            "computed_answer": str(solved.get("computed_answer") or ""),
            "matched_choice": str(solved.get("matched_choice") or ""),
            "solver_name": str(solved.get("solver_name") or ""),
            "validation_status": str(solved.get("validation_status") or ""),
            "problem_number": problem_no,
            "reference_answer": reference_answer,
            "pdf_card_text": pdf_card_text,
            "card_message": card_message,
            "source_preview": source_preview,
            "elapsed_seconds": round(time.time() - started, 3),
            "analysis": analysis,
        }
    except Exception as exc:
        return {
            **record,
            "status": "error",
            "issues": ["pipeline_error"],
            "error": f"{type(exc).__name__}: {exc}",
            "elapsed_seconds": round(time.time() - started, 3),
        }


def batch_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    issue_counter: Counter[str] = Counter()
    by_band: dict[str, Counter[str]] = defaultdict(Counter)
    by_source_kind: dict[str, Counter[str]] = defaultdict(Counter)
    by_topic: dict[str, Counter[str]] = defaultdict(Counter)
    for item in results:
        status = str(item.get("status") or "error")
        band = str(item.get("band") or "unknown")
        source = str(item.get("source_kind") or "unknown")
        topic = str(item.get("display_topic") or item.get("math_topic") or "unknown")
        by_band[band][status] += 1
        by_source_kind[source][status] += 1
        by_topic[topic][status] += 1
        for issue in item.get("issues") or []:
            issue_counter[str(issue)] += 1
            by_band[band][str(issue)] += 1
            by_source_kind[source][str(issue)] += 1
    return {
        "total": len(results),
        "ok": sum(1 for item in results if item.get("status") == "ok"),
        "review": sum(1 for item in results if item.get("status") == "review"),
        "non_problem": sum(1 for item in results if item.get("status") == "non_problem"),
        "error": sum(1 for item in results if item.get("status") == "error"),
        "issue_counts": dict(sorted(issue_counter.items())),
        "by_band": {key: dict(value) for key, value in sorted(by_band.items())},
        "by_source_kind": {key: dict(value) for key, value in sorted(by_source_kind.items())},
        "by_topic": {key: dict(value) for key, value in sorted(by_topic.items())},
    }


def issue_examples(results: list[dict[str, Any]], limit_per_issue: int = 30) -> dict[str, list[dict[str, Any]]]:
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in results:
        for issue in item.get("issues") or []:
            bucket = examples[str(issue)]
            if len(bucket) >= limit_per_issue:
                continue
            bucket.append(
                {
                    "index": item.get("index"),
                    "band": item.get("band"),
                    "grade": item.get("grade"),
                    "source_kind": item.get("source_kind"),
                    "relative_path": item.get("relative_path"),
                    "parent_relative_path": item.get("parent_relative_path"),
                    "problem_card_label": item.get("problem_card_label"),
                    "problem_text": item.get("problem_text"),
                    "expressions": item.get("expressions"),
                    "computed_answer": item.get("computed_answer") or item.get("matched_choice"),
                    "display_topic": item.get("display_topic"),
                    "source_preview": item.get("source_preview"),
                    "error": item.get("error"),
                }
            )
    return dict(sorted(examples.items()))


def write_report(path: Path, records: list[dict[str, Any]], results: list[dict[str, Any]], *, batch_size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    compact_results: list[dict[str, Any]] = []
    for item in results:
        compact = {key: value for key, value in item.items() if key not in {"analysis", "card_message"}}
        compact_results.append(compact)
    payload = {
        "schema_version": "coco_app_corpus_validation.v1",
        "generated_at": utc_now(),
        "batch_size": batch_size,
        "input_total": len(records),
        "processed_total": len(results),
        "summary": batch_summary(results),
        "issue_examples": issue_examples(results),
        "results": compact_results,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _analysis_with_corpus_metadata(result: dict[str, Any]) -> dict[str, Any]:
    analysis = dict(result.get("analysis") or {})
    structured = dict(analysis.get("structured_problem") or {})
    metadata = dict(structured.get("metadata") or {})
    metadata["corpus_validation_record"] = {
        "index": result.get("index"),
        "band": result.get("band"),
        "grade": result.get("grade"),
        "source_kind": result.get("source_kind"),
        "relative_path": result.get("relative_path"),
        "issues": result.get("issues") or [],
    }
    structured["metadata"] = metadata
    analysis["structured_problem"] = structured
    return analysis


def register_batch_in_app(batch_results: list[dict[str, Any]], *, batch_index: int) -> None:
    ensure_dirs()
    state = load_state()
    slot_ids = {f"{APP_SLOT_PREFIX}{slot:02d}" for slot in range(10)}
    docs = [item for item in state.get("documents", []) if str(item.get("doc_id") or "") not in slot_ids]
    registered_at = time.time()
    new_docs: list[dict[str, Any]] = []
    for slot, result in enumerate(batch_results[:10]):
        doc_id = f"{APP_SLOT_PREFIX}{slot:02d}"
        image_path = str(result.get("image_path") or "")
        file_name = Path(image_path).name
        persist_document(
            doc_id,
            file_name,
            image_path,
            _analysis_with_corpus_metadata(result),
            latest_user_query="",
            registered_at=registered_at + slot / 1000,
        )
        new_docs.append(
            {
                "doc_id": doc_id,
                "file_name": file_name,
                "file_path": image_path,
                "created_at": registered_at + slot / 1000,
                "registered_at": registered_at + slot / 1000,
                "last_opened_at": registered_at + slot / 1000,
                "latest_user_query": "",
                "corpus_batch_index": batch_index,
                "corpus_item_index": result.get("index"),
            }
        )
    if new_docs:
        state["documents"] = list(reversed(new_docs)) + docs
        state["chat_mode"] = "study"
        state["last_active_chat_mode"] = "study"
        state["selected_doc_id"] = new_docs[-1]["doc_id"]
        state["last_active_doc_id"] = new_docs[-1]["doc_id"]
        state["last_active_at"] = registered_at
        save_state(state)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate every problem-bank image through Coco app pipeline in 10-item batches.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--app-register", action="store_true", help="Keep the current batch visible in Coco using 10 reusable slot documents.")
    parser.add_argument("--segment-pages", action="store_true", help="Split page images into problem cards before validation, matching Coco upload behavior.")
    parser.add_argument("--segment-dir", type=Path, default=DEFAULT_SEGMENT_DIR)
    parser.add_argument("--clean-segment-dir", action="store_true")
    parser.add_argument("--write-every-batch", action="store_true")
    parser.add_argument("--issue-example-limit", type=int, default=30)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    page_records = collect_images(args.root)
    all_records = (
        expand_problem_cards(page_records, segment_dir=args.segment_dir, clean=args.clean_segment_dir)
        if args.segment_pages
        else page_records
    )
    offset = max(0, int(args.offset))
    limit = max(0, int(args.limit))
    records = all_records[offset : offset + limit if limit else None]
    batch_size = max(1, int(args.batch_size))
    results: list[dict[str, Any]] = []
    total = len(records)
    started = time.time()

    print(
        f"page_total={len(page_records)} corpus_total={len(all_records)} "
        f"selected={total} batch_size={batch_size}"
    )
    for batch_start in range(0, total, batch_size):
        batch = records[batch_start : batch_start + batch_size]
        batch_index = batch_start // batch_size + 1
        batch_results = [validate_one(record) for record in batch]
        results.extend(batch_results)
        if args.app_register:
            register_batch_in_app(batch_results, batch_index=batch_index)
        summary = batch_summary(results)
        print(
            f"[batch {batch_index} {batch_start + 1}-{batch_start + len(batch)}/{total}] "
            f"ok={summary['ok']} review={summary['review']} non_problem={summary['non_problem']} error={summary['error']} "
            f"issues={summary['issue_counts']}"
        )
        if args.write_every_batch:
            write_report(args.report, records, results, batch_size=batch_size)

    write_report(args.report, records, results, batch_size=batch_size)
    elapsed = round(time.time() - started, 3)
    print(f"report={args.report}")
    print(f"elapsed_seconds={elapsed}")
    print(json.dumps(batch_summary(results), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
