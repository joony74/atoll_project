from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlparse
from urllib.request import Request, urlopen

from PIL import Image, ImageStat


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_PDF_ROOT = PROJECT_ROOT / "02.학습문제" / "_pdf_private"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "02.학습문제" / "05.문제은행"
DEFAULT_MANIFEST = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_private_pdf_capture_manifest.json"

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X) CocoAiStudyPrivateBenchmark/1.0"

ORBI_SOURCES = (
    {
        "source_id": "orbi_public_7503_high1_common_math",
        "source": "orbi",
        "band": "고등",
        "grade": 1,
        "unit": "고1 공통수학 문제 분석",
        "page_url": "https://docs.orbi.kr/attach/public/7503",
        "pdf_url": "https://docs.orbi.kr/attach/public/7503",
    },
    {
        "source_id": "orbi_36765784_2",
        "source": "orbi",
        "band": "고등",
        "grade": 2,
        "unit": "수학 II / 함수의 극한과 연속",
        "page_url": "https://orbi.kr/00036765784",
        "pdf_url": "https://orbi.kr/download/united/36765784/2",
    },
    {
        "source_id": "orbi_36765784_3",
        "source": "orbi",
        "band": "고등",
        "grade": 3,
        "unit": "수학 II / 미분",
        "page_url": "https://orbi.kr/00036765784",
        "pdf_url": "https://orbi.kr/download/united/36765784/3",
    },
    {
        "source_id": "orbi_36765784_4",
        "source": "orbi",
        "band": "고등",
        "grade": 3,
        "unit": "수학 II / 적분",
        "page_url": "https://orbi.kr/00036765784",
        "pdf_url": "https://orbi.kr/download/united/36765784/4",
    },
)

SKAI_CATEGORY_BY_GRADE = {
    1: "https://skai.tistory.com/category/" + quote("초등 수학 단원평가") + "/" + quote("초1"),
    2: "https://skai.tistory.com/category/" + quote("초등 수학 단원평가") + "/" + quote("초2"),
    3: "https://skai.tistory.com/category/" + quote("초등 수학 단원평가") + "/" + quote("초3"),
    4: "https://skai.tistory.com/category/" + quote("초등 수학 단원평가") + "/" + quote("초4"),
    5: "https://skai.tistory.com/category/" + quote("초등 수학 단원평가") + "/" + quote("초5"),
    6: "https://skai.tistory.com/category/" + quote("진단평가") + "/" + quote("초6"),
}

AMY_MIDDLE_ARTICLES = {
    1: "https://amy83.tistory.com/531",
    2: "https://amy83.tistory.com/530",
    3: "https://amy83.tistory.com/529",
}


@dataclass(frozen=True, slots=True)
class PdfSource:
    source_id: str
    source: str
    band: str
    grade: int
    unit: str
    page_url: str
    pdf_url: str
    local_pdf: str
    title: str = ""


def _fetch_text(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def _slugify(value: str, fallback: str = "item") -> str:
    value = unquote(value or "").strip()
    value = re.sub(r"[\\/:*?\"<>|]+", "_", value)
    value = re.sub(r"\s+", "_", value)
    value = value.strip("._")
    return value[:120] or fallback


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, target: Path, *, force: bool = False) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 0 and not force:
        return target
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=120) as response, target.open("wb") as output:
        shutil.copyfileobj(response, output)
    return target


def _extract_article_links(category_url: str, *, limit: int) -> list[tuple[str, str]]:
    text = _fetch_text(category_url)
    links: list[tuple[str, str]] = []
    seen: set[str] = set()
    for match in re.finditer(r"<a[^>]+href=\"([^\"]+)\"[^>]*>(.*?)</a>", text, flags=re.I | re.S):
        href = html.unescape(match.group(1))
        label = html.unescape(re.sub(r"<.*?>", " ", match.group(2)))
        label = " ".join(label.split())
        if "/entry/" not in href:
            continue
        full_url = urljoin("https://skai.tistory.com", href)
        if full_url in seen:
            continue
        if not any(token in label for token in ("PDF", "수학", "단원", "진단")):
            continue
        seen.add(full_url)
        links.append((label, full_url))
        if len(links) >= limit:
            break
    return links


def _extract_pdf_urls(article_url: str) -> list[str]:
    text = _fetch_text(article_url)
    urls: list[str] = []
    seen: set[str] = set()
    patterns = (
        r"https?://[^\"']+?\.pdf(?:\?[^\"']*)?",
        r"href=\"([^\"]+?\.pdf(?:\?[^\"\']*)?)\"",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            raw = match.group(1) if match.lastindex else match.group(0)
            url = html.unescape(raw)
            url = urljoin(article_url, url)
            if url not in seen:
                seen.add(url)
                urls.append(url)
    return urls


def collect_skai_sources(*, per_grade: int, force: bool = False) -> list[PdfSource]:
    sources: list[PdfSource] = []
    for grade, category_url in SKAI_CATEGORY_BY_GRADE.items():
        for article_index, (title, article_url) in enumerate(_extract_article_links(category_url, limit=per_grade), start=1):
            pdf_urls = _extract_pdf_urls(article_url)
            for pdf_index, pdf_url in enumerate(pdf_urls[:1], start=1):
                parsed_name = Path(urlparse(pdf_url).path).name
                file_name = f"skai_g{grade}_{article_index:02d}_{pdf_index:02d}_{_slugify(parsed_name, 'source.pdf')}"
                if not file_name.lower().endswith(".pdf"):
                    file_name += ".pdf"
                local_pdf = PRIVATE_PDF_ROOT / "skai" / file_name
                _download(pdf_url, local_pdf, force=force)
                sources.append(
                    PdfSource(
                        source_id=local_pdf.stem,
                        source="skai",
                        band="초등",
                        grade=grade,
                        unit=title[:80],
                        page_url=article_url,
                        pdf_url=pdf_url,
                        local_pdf=str(local_pdf),
                        title=title,
                    )
                )
            time.sleep(0.2)
    return sources


def collect_orbi_sources(*, force: bool = False) -> list[PdfSource]:
    sources: list[PdfSource] = []
    for item in ORBI_SOURCES:
        local_pdf = PRIVATE_PDF_ROOT / "orbi" / f"{item['source_id']}.pdf"
        _download(str(item["pdf_url"]), local_pdf, force=force)
        sources.append(PdfSource(local_pdf=str(local_pdf), title=str(item["unit"]), **item))
    return sources


def collect_amy_middle_sources(*, per_grade: int, force: bool = False) -> list[PdfSource]:
    sources: list[PdfSource] = []
    for grade, article_url in AMY_MIDDLE_ARTICLES.items():
        pdf_urls = _extract_pdf_urls(article_url)
        for pdf_index, pdf_url in enumerate(pdf_urls[:per_grade], start=1):
            parsed_name = Path(urlparse(pdf_url).path).name
            file_name = f"amy_middle_g{grade}_{pdf_index:02d}_{_slugify(parsed_name, 'source.pdf')}"
            if not file_name.lower().endswith(".pdf"):
                file_name += ".pdf"
            local_pdf = PRIVATE_PDF_ROOT / "amy_middle" / file_name
            _download(pdf_url, local_pdf, force=force)
            sources.append(
                PdfSource(
                    source_id=local_pdf.stem,
                    source="amy_middle",
                    band="중등",
                    grade=grade,
                    unit=_slugify(parsed_name, "중등 수학").replace("_", " ")[:80],
                    page_url=article_url,
                    pdf_url=pdf_url,
                    local_pdf=str(local_pdf),
                    title=parsed_name,
                )
            )
        time.sleep(0.2)
    return sources


def _pdf_page_count(pdf_path: Path) -> int:
    result = subprocess.run(["pdfinfo", str(pdf_path)], check=True, text=True, capture_output=True)
    match = re.search(r"^Pages:\s*(\d+)", result.stdout, flags=re.M)
    if not match:
        raise RuntimeError(f"Could not read page count: {pdf_path}")
    return int(match.group(1))


def _is_blankish(image_path: Path) -> bool:
    image = Image.open(image_path).convert("L")
    stat = ImageStat.Stat(image)
    return stat.mean[0] > 248 and stat.stddev[0] < 8


def _is_front_matter_page(source: PdfSource, page: int) -> bool:
    if source.source == "orbi" and source.source_id.startswith("orbi_36765784"):
        return page <= 3
    if source.source_id == "orbi_public_7503_high1_common_math":
        return page <= 2
    if source.source == "amy_middle":
        return page <= 3
    return False


def _remove_page_outputs(source_dir: Path, source_id: str, page: int) -> None:
    page_stem = f"{source_id}_page_{page:03d}"
    for image_path in source_dir.glob(page_stem + "*.png"):
        image_path.unlink(missing_ok=True)


def _crop_tiles(page_path: Path, *, rows: int, cols: int, min_tile_ratio: float = 0.05) -> list[Path]:
    if rows <= 0 or cols <= 0:
        return []
    image = Image.open(page_path).convert("RGB")
    width, height = image.size
    margin_x = int(width * 0.055)
    margin_y = int(height * 0.065)
    usable = (margin_x, margin_y, width - margin_x, height - margin_y)
    tile_width = (usable[2] - usable[0]) // cols
    tile_height = (usable[3] - usable[1]) // rows
    outputs: list[Path] = []
    for row in range(rows):
        for col in range(cols):
            left = usable[0] + col * tile_width
            upper = usable[1] + row * tile_height
            right = usable[0] + (col + 1) * tile_width if col < cols - 1 else usable[2]
            lower = usable[1] + (row + 1) * tile_height if row < rows - 1 else usable[3]
            tile = image.crop((left, upper, right, lower))
            gray = tile.convert("L")
            stat = ImageStat.Stat(gray)
            if stat.mean[0] > 250 and stat.stddev[0] < 5:
                continue
            if (right - left) * (lower - upper) < width * height * min_tile_ratio:
                continue
            target = page_path.with_name(f"{page_path.stem}_tile_r{row + 1}_c{col + 1}.png")
            tile.save(target)
            outputs.append(target)
    return outputs


def _find_orbi_question_starts(gray: Image.Image, *, x1: int, x2: int, marker_limit: int) -> list[int]:
    width, height = gray.size
    y_start = int(height * 0.08)
    y_end = int(height * 0.92)
    clusters: list[tuple[int, int, int, int, int]] = []
    in_cluster = False
    start = 0
    max_count = 0
    for y in range(y_start, y_end):
        count = sum(1 for x in range(x1, x2) if gray.getpixel((x, y)) < 120)
        if count >= 3:
            if not in_cluster:
                start = y
                max_count = count
                in_cluster = True
            else:
                max_count = max(max_count, count)
        elif in_cluster:
            if y - start >= 8:
                points = [(x, row) for row in range(start, y) for x in range(x1, x2) if gray.getpixel((x, row)) < 120]
                if points:
                    xs = [point[0] for point in points]
                    clusters.append((start, y - 1, max_count, min(xs), max(xs)))
            in_cluster = False
    starts: list[int] = []
    for top, bottom, max_count, min_x, max_x in clusters:
        height = bottom - top + 1
        if min_x >= marker_limit:
            continue
        if height < 14 or height > 42:
            continue
        if max_count < 12:
            continue
        # Ignore unit-title markers like "# 1" on the left page margin.
        if max_x - min_x > 95:
            continue
        if starts and abs(top - starts[-1]) < 70:
            continue
        starts.append(top)
    return starts


def _crop_orbi_questions(page_path: Path) -> list[Path]:
    image = Image.open(page_path).convert("RGB")
    gray = image.convert("L")
    width, height = image.size
    columns = (
        (int(width * 0.045), int(width * 0.490), int(width * 0.078)),
        (int(width * 0.500), int(width * 0.945), int(width * 0.525)),
    )
    outputs: list[Path] = []
    for col_index, (left, right, marker_limit) in enumerate(columns, start=1):
        starts = _find_orbi_question_starts(gray, x1=left, x2=left + int(width * 0.085), marker_limit=marker_limit)
        for item_index, start in enumerate(starts, start=1):
            next_start = starts[item_index] if item_index < len(starts) else int(height * 0.915)
            upper = max(int(height * 0.055), start - int(height * 0.035))
            lower = min(int(height * 0.930), next_start - int(height * 0.018))
            if lower - upper < int(height * 0.10):
                continue
            target = page_path.with_name(f"{page_path.stem}_question_c{col_index}_{item_index:02d}.png")
            image.crop((max(0, left - 8), upper, min(width, right + 8), lower)).save(target)
            if not _is_blankish(target):
                outputs.append(target)
            else:
                target.unlink(missing_ok=True)
    return outputs


def _band_folder(band: str) -> str:
    return {"초등": "01.초등", "중등": "02.중등", "고등": "03.고등"}[band]


def render_pdf_source(
    source: PdfSource,
    *,
    output_root: Path,
    dpi: int,
    max_pages: int,
    tile_rows: int,
    tile_cols: int,
    force: bool = False,
) -> list[dict[str, object]]:
    pdf_path = Path(source.local_pdf)
    page_count = _pdf_page_count(pdf_path)
    render_count = min(page_count, max_pages) if max_pages > 0 else page_count
    source_dir = (
        output_root
        / _band_folder(source.band)
        / f"{source.grade}학년"
        / "원문PDF캡처"
        / source.source
        / _slugify(source.source_id)
    )
    source_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    for page in range(1, render_count + 1):
        page_path = source_dir / f"{source.source_id}_page_{page:03d}.png"
        if force or not page_path.exists():
            prefix = source_dir / f".render_{source.source_id}_{page:03d}"
            for stale in source_dir.glob(prefix.name + "*.png"):
                stale.unlink()
            subprocess.run(
                ["pdftoppm", "-png", "-f", str(page), "-l", str(page), "-singlefile", "-r", str(dpi), str(pdf_path), str(prefix)],
                check=True,
            )
            rendered = Path(str(prefix) + ".png")
            if not rendered.exists():
                matches = sorted(source_dir.glob(prefix.name + "*.png"))
                if not matches:
                    raise RuntimeError(f"pdftoppm did not render page {page}: {pdf_path}")
                rendered = matches[0]
            rendered.replace(page_path)
        if _is_front_matter_page(source, page):
            _remove_page_outputs(source_dir, source.source_id, page)
            continue
        if _is_blankish(page_path):
            _remove_page_outputs(source_dir, source.source_id, page)
            continue
        if source.source == "orbi" and source.source_id.startswith("orbi_36765784"):
            tile_paths = _crop_orbi_questions(page_path)
            tile_kind = "question"
        else:
            tile_paths = _crop_tiles(page_path, rows=tile_rows, cols=tile_cols)
            tile_kind = "tile"
        image_paths = [page_path, *tile_paths]
        for kind_index, image_path in enumerate(image_paths):
            kind = "page" if kind_index == 0 else tile_kind
            try:
                relative_path = str(image_path.relative_to(PROJECT_ROOT))
            except ValueError:
                relative_path = str(image_path)
            records.append(
                {
                    "case_id": f"{source.source_id}_p{page:03d}_{kind_index:02d}",
                    "source_id": source.source_id,
                    "source": source.source,
                    "band": source.band,
                    "grade": source.grade,
                    "unit": source.unit,
                    "layout": f"pdf_{kind}",
                    "page": page,
                    "image_path": str(image_path),
                    "relative_path": relative_path,
                    "local_pdf": str(pdf_path),
                    "pdf_sha256": _sha256(pdf_path),
                    "page_url": source.page_url,
                    "expected_answer": "",
                    "expected_expression": "",
                    "copyright_policy": "private_local_ocr_benchmark_only",
                }
            )
    return records


def write_manifest(path: Path, sources: list[PdfSource], records: list[dict[str, object]], *, output_root: Path) -> None:
    payload = {
        "schema_version": "coco_private_pdf_capture_manifest.v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "policy": "Downloaded PDFs and rendered captures are local/private OCR benchmarks and are intentionally git-ignored.",
        "output_root": str(output_root),
        "source_count": len(sources),
        "image_count": len(records),
        "sources": [asdict(item) for item in sources],
        "records": records,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local/private PDF-capture problem bank for OCR validation.")
    parser.add_argument("--source", choices=("orbi", "skai", "amy_middle", "all"), default="all")
    parser.add_argument("--skai-per-grade", type=int, default=1)
    parser.add_argument("--amy-middle-per-grade", type=int, default=3)
    parser.add_argument("--max-pages-per-pdf", type=int, default=0)
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--tile-rows", type=int, default=3)
    parser.add_argument("--tile-cols", type=int, default=2)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--force-render", action="store_true")
    args = parser.parse_args()

    sources: list[PdfSource] = []
    if args.source in {"orbi", "all"}:
        sources.extend(collect_orbi_sources(force=args.force_download))
    if args.source in {"skai", "all"}:
        sources.extend(collect_skai_sources(per_grade=args.skai_per_grade, force=args.force_download))
    if args.source in {"amy_middle", "all"}:
        sources.extend(collect_amy_middle_sources(per_grade=args.amy_middle_per_grade, force=args.force_download))

    records: list[dict[str, object]] = []
    for source in sources:
        records.extend(
            render_pdf_source(
                source,
                output_root=args.output_root,
                dpi=args.dpi,
                max_pages=args.max_pages_per_pdf,
                tile_rows=args.tile_rows,
                tile_cols=args.tile_cols,
                force=args.force_render,
            )
        )

    write_manifest(args.manifest, sources, records, output_root=args.output_root)
    print(f"sources={len(sources)}")
    print(f"images={len(records)}")
    print(f"manifest={args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
