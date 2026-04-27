from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROBLEM_BANK_ROOT = PROJECT_ROOT / "02.학습문제" / "05.문제은행"
MANIFEST_PATH = PROJECT_ROOT / "data" / "problem_bank" / "sources" / "skai_pdf_edite_manifest.json"
PDFTOPPM = shutil.which("pdftoppm")
PDFINFO = shutil.which("pdfinfo")
PDFTOTEXT = shutil.which("pdftotext")


@dataclass
class EditRecord:
    pdf_path: str
    image_path: str
    grade: int
    title_slug: str
    source_page: int
    page_count: int
    skipped_answer_pages: int


def run_text(command: list[str]) -> str:
    return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT)


def sanitize(value: str, *, limit: int = 96) -> str:
    value = unicodedata.normalize("NFC", value)
    value = re.sub(r"[\\/:*?\"<>|]+", "_", value)
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"_+", "_", value).strip("._ ")
    return (value or "skai_page")[:limit]


def page_count(pdf_path: Path) -> int:
    if not PDFINFO:
        raise RuntimeError("pdfinfo is required")
    output = run_text([PDFINFO, str(pdf_path)])
    match = re.search(r"^Pages:\s+(\d+)", output, flags=re.MULTILINE)
    if not match:
        raise RuntimeError(f"cannot read page count: {pdf_path}")
    return int(match.group(1))


def pdf_page_text(pdf_path: Path, page_number: int) -> str:
    if not PDFTOTEXT:
        return ""
    try:
        return run_text([PDFTOTEXT, "-f", str(page_number), "-l", str(page_number), "-layout", str(pdf_path), "-"])
    except Exception:
        return ""


def grade_from_path(pdf_path: Path) -> int:
    match = re.search(r"/([1-6])학년/", str(pdf_path))
    return int(match.group(1)) if match else 0


def normalize_unit_title(text: str, fallback_name: str) -> str:
    source = unicodedata.normalize("NFC", f"{text}\n{fallback_name}")
    source = source.replace("_", " ")
    grade_match = re.search(r"\[?\s*초\s*([1-6])\s*-\s*([12])\s*\]?", source)
    unit_match = re.search(r"(?<!\d)([1-6])\s*(?:단원|[.．])\s*([가-힣A-Za-z0-9·()\s]+?)(?:\s*\[|\s*단원평가|\s*[0-9]회|https|$)", source)
    round_match = re.search(r"\[?\s*([1-3])\s*회\s*\]?", source)

    if grade_match and unit_match:
        grade_text = f"초{grade_match.group(1)}-{grade_match.group(2)}"
        unit_number = unit_match.group(1)
        unit_name = re.sub(r"\s+", "", unit_match.group(2)).strip("._-")
        title = f"{grade_text}_{unit_number}단원_{unit_name}"
        if round_match:
            title += f"_{round_match.group(1)}회"
        return sanitize(title)

    compact = re.sub(r"\s+", "_", fallback_name)
    match = re.search(r"(초[1-6]-[12]).*?([1-6])\.([^_\[]+)", compact)
    if match:
        return sanitize(f"{match.group(1)}_{match.group(2)}단원_{match.group(3)}")
    return sanitize(Path(fallback_name).stem)


def is_answer_page(text: str) -> bool:
    compact = re.sub(r"\s+", "", unicodedata.normalize("NFC", text or ""))
    lead = compact[:900]
    if re.search(r"(?:단원평가|진단평가).{0,30}정답", lead):
        return True
    numbered_answers = len(re.findall(r"(?<!\d)\d{1,2}\)", text or ""))
    if "정답" in lead and numbered_answers >= 6:
        return True
    if numbered_answers >= 12 and not re.search(r"구하|알맞|써넣|찾|물음", compact):
        return True
    return False


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


def crop_problem_body(image_path: Path, page_number: int) -> Image.Image:
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    top_ratio = 0.180 if page_number == 1 else 0.082
    bottom_ratio = 0.940
    left_ratio = 0.035
    right_ratio = 0.965
    cropped = image.crop(
        (
            int(width * left_ratio),
            int(height * top_ratio),
            int(width * right_ratio),
            int(height * bottom_ratio),
        )
    )
    return trim_whitespace(cropped)


def trim_whitespace(image: Image.Image) -> Image.Image:
    gray = image.convert("L")
    width, height = gray.size
    pixels = gray.load()
    dark_threshold = 245

    xs: list[int] = []
    ys: list[int] = []
    step = 2
    for y in range(0, height, step):
        for x in range(0, width, step):
            if pixels[x, y] < dark_threshold:
                xs.append(x)
                ys.append(y)
    if not xs or not ys:
        return image
    padding = 28
    left = max(0, min(xs) - padding)
    top = max(0, min(ys) - padding)
    right = min(width, max(xs) + padding)
    bottom = min(height, max(ys) + padding)
    if right <= left or bottom <= top:
        return image
    return image.crop((left, top, right, bottom))


def clean_edite_folders() -> None:
    for edite in PROBLEM_BANK_ROOT.glob("01.초등/*학년/EDITE"):
        shutil.rmtree(edite)


def process_pdf(pdf_path: Path, *, clean: bool = False) -> list[EditRecord]:
    grade = grade_from_path(pdf_path)
    grade_root = pdf_path.parents[1]
    edite_dir = grade_root / "EDITE"
    edite_dir.mkdir(parents=True, exist_ok=True)

    total_pages = page_count(pdf_path)
    first_text = pdf_page_text(pdf_path, 1)
    title_slug = normalize_unit_title(first_text, pdf_path.name)
    skipped_answer_pages = 0
    records: list[EditRecord] = []

    with tempfile.TemporaryDirectory(prefix="skai_pdf_crop_") as tmp:
        tmpdir = Path(tmp)
        for page_number in range(1, total_pages + 1):
            text = pdf_page_text(pdf_path, page_number)
            if is_answer_page(text):
                skipped_answer_pages += 1
                continue
            rendered = render_page(pdf_path, page_number, tmpdir)
            cropped = crop_problem_body(rendered, page_number)
            output_name = f"{title_slug}_p{page_number:02d}.png"
            output_path = edite_dir / output_name
            cropped.save(output_path, optimize=True)
            records.append(
                EditRecord(
                    pdf_path=str(pdf_path.relative_to(PROJECT_ROOT)),
                    image_path=str(output_path.relative_to(PROJECT_ROOT)),
                    grade=grade,
                    title_slug=title_slug,
                    source_page=page_number,
                    page_count=total_pages,
                    skipped_answer_pages=skipped_answer_pages,
                )
            )
    for record in records:
        record.skipped_answer_pages = skipped_answer_pages
    return records


def collect_pdfs() -> list[Path]:
    return sorted(PROBLEM_BANK_ROOT.glob("01.초등/*학년/PDF/*.pdf"), key=lambda path: str(path))


def main() -> None:
    if not PDFTOPPM or not PDFINFO:
        raise SystemExit("pdftoppm/pdfinfo is required. Install poppler first.")

    clean_edite_folders()
    records: list[EditRecord] = []
    failures: list[dict[str, str]] = []
    pdfs = collect_pdfs()
    for index, pdf_path in enumerate(pdfs, start=1):
        try:
            records.extend(process_pdf(pdf_path))
        except Exception as exc:
            failures.append({"pdf_path": str(pdf_path.relative_to(PROJECT_ROOT)), "error": str(exc)})
        if index % 20 == 0:
            print(f"pdfs={index}/{len(pdfs)} images={len(records)} failures={len(failures)}")

    by_grade = {str(grade): sum(1 for record in records if record.grade == grade) for grade in range(1, 7)}
    payload = {
        "source": "skai_pdf_edite_crop",
        "pdf_count": len(pdfs),
        "image_count": len(records),
        "by_grade": by_grade,
        "records": [asdict(record) for record in records],
        "failures": failures,
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("pdf_count", "image_count", "by_grade")}, ensure_ascii=False, indent=2))
    if failures:
        print(f"failures={len(failures)} see {MANIFEST_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
