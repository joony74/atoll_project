from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageStat


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROBLEM_BANK_ROOT = PROJECT_ROOT / "03.학습문제" / "05.문제은행"
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "data" / "problem_bank" / "sources" / "toctoc_pdf_edite_manifest.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "data" / "problem_bank" / "sources" / "toctoc_pdf_edite_quality_report.json"
PDFINFO = shutil.which("pdfinfo")
PDFTOPPM = shutil.which("pdftoppm")
PDFTOTEXT = shutil.which("pdftotext")

WORD_RE = re.compile(
    r'<word xMin="(?P<x_min>[-0-9.]+)" yMin="(?P<y_min>[-0-9.]+)" '
    r'xMax="(?P<x_max>[-0-9.]+)" yMax="(?P<y_max>[-0-9.]+)">(?P<text>.*?)</word>'
)
PAGE_RE = re.compile(r'<page width="(?P<width>[-0-9.]+)" height="(?P<height>[-0-9.]+)">')
QUESTION_KEYWORDS = re.compile(
    r"구하|알맞|써|계산|그려|색칠|표시|고르|찾|나타내|비교|이어|해\s*보|답|식|물음|완성|만들|분류|재어|읽어|세어|묶어|나누|해결|설명|O표|○표|∨"
)


@dataclass
class WordBox:
    text: str
    x_min: float
    y_min: float
    x_max: float
    y_max: float


@dataclass
class EditRecord:
    pdf_path: str
    image_path: str
    grade: int
    source_page: int
    page_count: int
    crop_top_px: int
    crop_reason: str


@dataclass
class SkipRecord:
    pdf_path: str
    source_page: int
    reason: str
    text_preview: str


def run_text(command: list[str]) -> str:
    return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT)


def page_count(pdf_path: Path) -> int:
    if not PDFINFO:
        raise RuntimeError("pdfinfo is required")
    output = run_text([PDFINFO, str(pdf_path)])
    match = re.search(r"^Pages:\s+(\d+)", output, flags=re.MULTILINE)
    if not match:
        raise RuntimeError(f"cannot read page count: {pdf_path}")
    return int(match.group(1))


def page_text(pdf_path: Path, page_number: int) -> str:
    if not PDFTOTEXT:
        return ""
    try:
        return run_text([PDFTOTEXT, "-f", str(page_number), "-l", str(page_number), "-layout", str(pdf_path), "-"])
    except Exception:
        return ""


def page_bbox(pdf_path: Path, page_number: int) -> tuple[float, float, list[WordBox]]:
    if not PDFTOTEXT:
        return 0.0, 0.0, []
    try:
        output = run_text([PDFTOTEXT, "-f", str(page_number), "-l", str(page_number), "-bbox", str(pdf_path), "-"])
    except Exception:
        return 0.0, 0.0, []
    page_match = PAGE_RE.search(output)
    if not page_match:
        return 0.0, 0.0, []
    words: list[WordBox] = []
    for match in WORD_RE.finditer(output):
        words.append(
            WordBox(
                text=html.unescape(match.group("text")).strip(),
                x_min=float(match.group("x_min")),
                y_min=float(match.group("y_min")),
                x_max=float(match.group("x_max")),
                y_max=float(match.group("y_max")),
            )
        )
    return float(page_match.group("width")), float(page_match.group("height")), words


def grade_from_path(pdf_path: Path) -> int:
    match = re.search(r"/([1-6])학년/", str(pdf_path))
    return int(match.group(1)) if match else 0


def answer_start_page(pdf_path: Path, total_pages: int) -> int | None:
    for page_number in range(1, total_pages + 1):
        compact = re.sub(r"\s+", "", page_text(pdf_path, page_number))
        if "정답및풀이" in compact or ("정답" in compact and "풀이" in compact):
            return page_number
    return None


def preview(text: str, limit: int = 160) -> str:
    return re.sub(r"\s+", " ", text).strip()[:limit]


def first_problem_y(page_height: float, words: list[WordBox]) -> float | None:
    if not page_height or not words:
        return None
    candidates: list[float] = []
    lower_bound = page_height * 0.10
    upper_bound = page_height * 0.90
    for index, word in enumerate(words):
        text = word.text
        if not text or word.y_min < lower_bound or word.y_min > upper_bound:
            continue
        nearby = " ".join(item.text for item in words[index : index + 18])
        if re.fullmatch(r"\d{1,2}\.", text):
            candidates.append(word.y_min)
        elif re.fullmatch(r"0[1-9]", text):
            candidates.append(word.y_min)
        elif re.fullmatch(r"(?:[1-9]|1\d|20)", text) and word.x_min < 165 and QUESTION_KEYWORDS.search(nearby):
            candidates.append(word.y_min)
        elif text == "응용문제" and any(re.fullmatch(r"(?:0[1-9]|[1-9]\d?)", item.text) for item in words[index + 1 : index + 4]):
            candidates.append(word.y_min)
    if not candidates:
        return None
    return min(candidates)


def classify_page(
    pdf_path: Path,
    page_number: int,
    total_pages: int,
    answer_start: int | None,
    text: str,
    problem_y: float | None,
) -> str | None:
    compact = re.sub(r"\s+", "", text)
    spaced = preview(text, limit=400)
    if page_number <= 4:
        return "front_matter"
    if answer_start is not None and page_number >= answer_start:
        return "answer_section"
    if "교과활동개념정리하기" in compact or "개념정리하기" in compact:
        return "concept_explanation"
    if "목차" in compact or "단원차시차시명페이지" in compact:
        return "table_of_contents"
    if "참잘했어요" in compact or ("모두했어요" in compact and "응원해" in compact):
        return "progress_tracker"
    if problem_y is not None and not re.search(r"(?<!\d)\d{1,2}\.", text):
        has_question_prompt = re.search(r"세요|응용문제|답|식|보기|물음|○표|O표|∨", compact)
        if not has_question_prompt:
            return "unit_overview"
    if ("함께학습지" in compact or "함께 학습지" in spaced) and problem_y is None:
        return "unit_overview"
    if problem_y is None:
        return "no_problem_marker"
    return None


def render_page(pdf_path: Path, page_number: int, tmpdir: Path, dpi: int = 180) -> Path:
    if not PDFTOPPM:
        raise RuntimeError("pdftoppm is required")
    output_prefix = tmpdir / f"page_{page_number:03d}"
    subprocess.check_call(
        [PDFTOPPM, "-png", "-r", str(dpi), "-f", str(page_number), "-l", str(page_number), "-singlefile", str(pdf_path), str(output_prefix)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return output_prefix.with_suffix(".png")


def trim_whitespace(image: Image.Image) -> Image.Image:
    gray = image.convert("L")
    width, height = gray.size
    pixels = gray.load()
    xs: list[int] = []
    ys: list[int] = []
    for y in range(0, height, 2):
        for x in range(0, width, 2):
            if pixels[x, y] < 247:
                xs.append(x)
                ys.append(y)
    if not xs or not ys:
        return image
    padding = 24
    left = max(0, min(xs) - padding)
    top = max(0, min(ys) - padding)
    right = min(width, max(xs) + padding)
    bottom = min(height, max(ys) + padding)
    if right <= left or bottom <= top:
        return image
    return image.crop((left, top, right, bottom))


def crop_from_problem_y(image_path: Path, page_height: float, problem_y: float) -> tuple[Image.Image, int]:
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    margin_points = 72.0 * 5.0 / 25.4
    top_points = max(0.0, problem_y - margin_points)
    top = int(top_points / page_height * height) if page_height else 0
    bottom = int(height * 0.975)
    if top >= bottom:
        top = int(height * 0.08)
    cropped = image.crop((int(width * 0.035), top, int(width * 0.965), bottom))
    return trim_whitespace(cropped), top


def collect_pdfs(problem_bank_root: Path) -> list[Path]:
    return sorted(problem_bank_root.glob("01.초등/*학년/PDF/*.pdf"), key=lambda path: str(path))


def clean_edite_folders(problem_bank_root: Path) -> None:
    for edite_dir in problem_bank_root.glob("01.초등/*학년/EDITE"):
        shutil.rmtree(edite_dir)


def image_quality(records: list[EditRecord]) -> dict[str, object]:
    small: list[dict[str, object]] = []
    blank: list[dict[str, object]] = []
    for record in records:
        image_path = PROJECT_ROOT / record.image_path
        with Image.open(image_path) as image:
            width, height = image.size
            stat = ImageStat.Stat(image.convert("L"))
        if width < 320 or height < 240:
            small.append({"image_path": record.image_path, "width": width, "height": height})
        if stat.mean[0] > 252 and stat.stddev[0] < 3:
            blank.append({"image_path": record.image_path, "width": width, "height": height})
    return {"small": small, "blank_like": blank}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and recrop Toctoc elementary EDITE images.")
    parser.add_argument("--problem-bank-root", type=Path, default=DEFAULT_PROBLEM_BANK_ROOT)
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    problem_bank_root = args.problem_bank_root.resolve()
    manifest_path = args.manifest_path.resolve()
    report_path = args.report_path.resolve()

    clean_edite_folders(problem_bank_root)
    records: list[EditRecord] = []
    skipped: list[SkipRecord] = []
    failures: list[dict[str, str]] = []
    pdfs = collect_pdfs(problem_bank_root)

    with tempfile.TemporaryDirectory(prefix="toctoc_validated_crop_") as tmp:
        tmpdir = Path(tmp)
        for pdf_index, pdf_path in enumerate(pdfs, start=1):
            try:
                total_pages = page_count(pdf_path)
                answer_start = answer_start_page(pdf_path, total_pages)
                edite_dir = pdf_path.parent.parent / "EDITE"
                edite_dir.mkdir(parents=True, exist_ok=True)
                for page_number in range(1, total_pages + 1):
                    text = page_text(pdf_path, page_number)
                    _, page_height, words = page_bbox(pdf_path, page_number)
                    problem_y = first_problem_y(page_height, words)
                    skip_reason = classify_page(pdf_path, page_number, total_pages, answer_start, text, problem_y)
                    pdf_rel = str(pdf_path.relative_to(PROJECT_ROOT))
                    if skip_reason:
                        skipped.append(SkipRecord(pdf_rel, page_number, skip_reason, preview(text)))
                        continue
                    if problem_y is None:
                        skipped.append(SkipRecord(pdf_rel, page_number, "no_problem_marker", preview(text)))
                        continue
                    rendered = render_page(pdf_path, page_number, tmpdir)
                    cropped, top = crop_from_problem_y(rendered, page_height, problem_y)
                    image_path = edite_dir / f"{pdf_path.stem}_p{page_number:02d}.png"
                    cropped.save(image_path, optimize=True)
                    records.append(
                        EditRecord(
                            pdf_path=pdf_rel,
                            image_path=str(image_path.relative_to(PROJECT_ROOT)),
                            grade=grade_from_path(pdf_path),
                            source_page=page_number,
                            page_count=total_pages,
                            crop_top_px=top,
                            crop_reason="pdf_text_problem_marker_5mm_margin",
                        )
                    )
            except Exception as exc:
                failures.append({"pdf_path": str(pdf_path.relative_to(PROJECT_ROOT)), "error": str(exc)})
            print(f"pdfs={pdf_index}/{len(pdfs)} images={len(records)} skipped={len(skipped)} failures={len(failures)}")

    by_grade = {str(grade): sum(1 for record in records if record.grade == grade) for grade in range(1, 7)}
    quality = image_quality(records)
    payload = {
        "source": "toctoc_pdf_edite_validated_recrop",
        "problem_bank_root": str(problem_bank_root.relative_to(PROJECT_ROOT) if problem_bank_root.is_relative_to(PROJECT_ROOT) else problem_bank_root),
        "pdf_count": len(pdfs),
        "image_count": len(records),
        "by_grade": by_grade,
        "records": [asdict(record) for record in records],
        "failures": failures,
    }
    report = {
        "source": payload["source"],
        "pdf_count": len(pdfs),
        "image_count": len(records),
        "by_grade": by_grade,
        "skipped_count": len(skipped),
        "skipped_by_reason": {},
        "skipped": [asdict(item) for item in skipped],
        "quality": quality,
        "failures": failures,
    }
    for item in skipped:
        report["skipped_by_reason"][item.reason] = report["skipped_by_reason"].get(item.reason, 0) + 1
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "pdf_count": len(pdfs),
                "image_count": len(records),
                "by_grade": by_grade,
                "skipped_by_reason": report["skipped_by_reason"],
                "small": len(quality["small"]),
                "blank_like": len(quality["blank_like"]),
                "failures": len(failures),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
