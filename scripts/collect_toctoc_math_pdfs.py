from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import unicodedata
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import quote


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROBLEM_BANK_ROOT = PROJECT_ROOT / "03.학습문제" / "05.문제은행"
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "data" / "problem_bank" / "sources" / "toctoc_pdf_manifest.json"
BASE_URL = "https://cdn.toctocmath.kr/"


@dataclass(frozen=True)
class SourcePdf:
    grade: int
    semester: int
    title: str
    source_path: str


@dataclass
class DownloadRecord:
    grade: int
    semester: int
    title: str
    source_url: str
    pdf_path: str
    size_bytes: int
    sha256: str


SOURCES = [
    SourcePdf(1, 1, "똑똑수학탐험대_1학년_1학기_함께학습지", "학습지/학년학기별/1학년1학기.pdf"),
    SourcePdf(1, 2, "똑똑수학탐험대_1학년_2학기_함께학습지", "학습지/학년학기별/1학년2학기.pdf"),
    SourcePdf(2, 1, "똑똑수학탐험대_2학년_1학기_함께학습지", "학습지/학년학기별/2학년1학기.pdf"),
    SourcePdf(2, 2, "똑똑수학탐험대_2학년_2학기_함께학습지", "학습지/학년학기별/2학년2학기.pdf"),
    SourcePdf(3, 1, "똑똑수학탐험대_3학년_1학기_함께학습지", "학습지/학년학기별/3학년1학기.pdf"),
    SourcePdf(3, 2, "똑똑수학탐험대_3학년_2학기_함께학습지", "학습지/학년학기별/3학년2학기.pdf"),
    SourcePdf(4, 1, "똑똑수학탐험대_4학년_1학기_함께학습지", "학습지/학년학기별/4학년1학기.pdf"),
    SourcePdf(4, 2, "똑똑수학탐험대_4학년_2학기_함께학습지", "학습지/학년학기별/4학년2학기.pdf"),
    SourcePdf(5, 1, "똑똑수학탐험대_5학년_1학기_함께학습지", "학습지/학년학기별/5학년1학기(240820).pdf"),
    SourcePdf(5, 2, "똑똑수학탐험대_5학년_2학기_함께학습지", "학습지/학년학기별/5학년2학기.pdf"),
    SourcePdf(6, 1, "똑똑수학탐험대_6학년_1학기_함께학습지", "학습지/학년학기별/6학년1학기(240715).pdf"),
    SourcePdf(6, 2, "똑똑수학탐험대_6학년_2학기_함께학습지", "학습지/학년학기별/6학년2학기.pdf"),
]


def sanitize(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    value = re.sub(r"[\\/:*?\"<>|]+", "_", value)
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"_+", "_", value).strip("._ ")
    return value[:120]


def source_url(source_path: str) -> str:
    return BASE_URL + quote(source_path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    part_path = destination.with_suffix(destination.suffix + ".part")
    with urllib.request.urlopen(request, timeout=60) as response, part_path.open("wb") as output:
        shutil.copyfileobj(response, output, length=1024 * 1024)
    part_path.replace(destination)


def target_path(problem_bank_root: Path, source: SourcePdf) -> Path:
    filename = sanitize(f"toctoc_g{source.grade}_s{source.semester}_{source.title}.pdf")
    return problem_bank_root / "01.초등" / f"{source.grade}학년" / "PDF" / filename


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect Toctoc Math elementary PDFs into 03.학습문제.")
    parser.add_argument("--problem-bank-root", type=Path, default=DEFAULT_PROBLEM_BANK_ROOT)
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--redownload", action="store_true", help="Download again even when a PDF already exists.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    problem_bank_root = args.problem_bank_root.resolve()
    manifest_path = args.manifest_path.resolve()

    records: list[DownloadRecord] = []
    failures: list[dict[str, str]] = []
    for index, source in enumerate(SOURCES, start=1):
        url = source_url(source.source_path)
        pdf_path = target_path(problem_bank_root, source)
        try:
            if args.redownload or not pdf_path.exists():
                print(f"download {index}/{len(SOURCES)} grade={source.grade}-{source.semester} {url}")
                download(url, pdf_path)
            size = pdf_path.stat().st_size
            records.append(
                DownloadRecord(
                    grade=source.grade,
                    semester=source.semester,
                    title=source.title,
                    source_url=url,
                    pdf_path=str(pdf_path.relative_to(PROJECT_ROOT)),
                    size_bytes=size,
                    sha256=sha256(pdf_path),
                )
            )
        except Exception as exc:
            failures.append({"title": source.title, "source_url": url, "error": str(exc)})

    payload = {
        "source": "toctoc_math_elementary_semester_pdfs",
        "problem_bank_root": str(problem_bank_root.relative_to(PROJECT_ROOT) if problem_bank_root.is_relative_to(PROJECT_ROOT) else problem_bank_root),
        "pdf_count": len(records),
        "total_size_bytes": sum(record.size_bytes for record in records),
        "records": [asdict(record) for record in records],
        "failures": failures,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("pdf_count", "total_size_bytes")}, ensure_ascii=False, indent=2))
    if failures:
        print(json.dumps({"failures": failures}, ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
