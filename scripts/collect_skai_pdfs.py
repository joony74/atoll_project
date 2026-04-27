from __future__ import annotations

import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROBLEM_BANK_ROOT = PROJECT_ROOT / "02.학습문제" / "05.문제은행"
MANIFEST_PATH = PROJECT_ROOT / "data" / "problem_bank" / "sources" / "skai_pdf_manifest.json"
BASE_URL = "https://skai.tistory.com"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X) CocoAi Study PDF Collector"


@dataclass
class PdfRecord:
    grade: int
    title: str
    post_url: str
    pdf_url: str
    relative_path: str
    bytes: int
    sha256: str


def fetch(url: str, *, binary: bool = False, retries: int = 3) -> bytes | str:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Referer": BASE_URL,
                "Accept": "application/pdf,text/html,application/xhtml+xml,*/*",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = response.read()
            return data if binary else data.decode("utf-8", "ignore")
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(0.8 * attempt)
    raise RuntimeError(f"failed to fetch {url}: {last_error}")


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(html.unescape(value).split())


def sanitize_filename(value: str, *, limit: int = 110) -> str:
    decoded = urllib.parse.unquote(value)
    decoded = re.sub(r"[\\/:*?\"<>|]+", "_", decoded)
    decoded = re.sub(r"\s+", "_", decoded).strip("._ ")
    return (decoded or "skai_pdf")[:limit]


def grade_from_text(*values: str) -> int | None:
    text = " ".join(values)
    patterns = (
        r"\[?\s*초(?:등)?\s*([1-6])\s*\]?",
        r"초등\s*([1-6])\s*학년",
        r"([1-6])\s*학년",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None


def absolute_url(href: str) -> str:
    href = html.unescape(href)
    return urllib.parse.urljoin(BASE_URL, href)


def extract_post_links(category_html: str) -> list[tuple[str, str]]:
    posts: list[tuple[str, str]] = []
    seen: set[str] = set()
    for match in re.finditer(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", category_html, re.I | re.S):
        href, label = match.groups()
        if "/entry/" not in href or "/manage/" in href:
            continue
        title = clean_text(label)
        if not title or not re.search(r"(무료|PDF|수학|단원평가|진단평가|초[1-6])", title):
            continue
        url = absolute_url(href.split("#", 1)[0])
        url = url.split("?category=", 1)[0]
        if url in seen:
            continue
        seen.add(url)
        posts.append((url, title))
    return posts


def discover_posts(max_pages: int = 76) -> list[tuple[str, str]]:
    posts: list[tuple[str, str]] = []
    seen: set[str] = set()
    empty_pages = 0
    for page in range(1, max_pages + 1):
        category_url = f"{BASE_URL}/category?page={page}"
        page_posts = extract_post_links(str(fetch(category_url)))
        if not page_posts:
            empty_pages += 1
            if empty_pages >= 3:
                break
            continue
        empty_pages = 0
        for url, title in page_posts:
            if url not in seen:
                seen.add(url)
                posts.append((url, title))
        time.sleep(0.1)
    return posts


def extract_pdf_links(post_html: str) -> list[str]:
    decoded = html.unescape(post_html)
    candidates = set()
    for match in re.finditer(r"https?://[^\s\"'<>]+?\.pdf(?:\?[^\s\"'<>]+)?", decoded, re.I):
        candidates.add(match.group(0).rstrip(").,;"))
    for match in re.finditer(r"href=[\"']([^\"']+?\.pdf(?:\?[^\"']+)?)", decoded, re.I):
        candidates.add(absolute_url(match.group(1)).rstrip(").,;"))
    return sorted(candidates)


def ensure_grade_folders() -> None:
    for grade in range(1, 7):
        (PROBLEM_BANK_ROOT / "01.초등" / f"{grade}학년" / "PDF").mkdir(parents=True, exist_ok=True)
    for band in ("02.중등", "03.고등"):
        for grade in range(1, 4):
            (PROBLEM_BANK_ROOT / band / f"{grade}학년" / "PDF").mkdir(parents=True, exist_ok=True)


def download_pdf(pdf_url: str, title: str, grade: int, counter: int) -> PdfRecord:
    data = fetch(pdf_url, binary=True)
    if not isinstance(data, bytes) or not data.startswith(b"%PDF"):
        raise RuntimeError("downloaded payload is not a PDF")

    digest = hashlib.sha256(data).hexdigest()
    path_part = urllib.parse.urlparse(pdf_url).path
    original_name = Path(urllib.parse.unquote(path_part)).name or f"skai_{counter:04d}.pdf"
    filename = f"skai_{counter:04d}_{sanitize_filename(title, limit=70)}__{sanitize_filename(original_name, limit=50)}"
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"
    output_path = PROBLEM_BANK_ROOT / "01.초등" / f"{grade}학년" / "PDF" / filename
    output_path.write_bytes(data)
    return PdfRecord(
        grade=grade,
        title=title,
        post_url="",
        pdf_url=pdf_url,
        relative_path=str(output_path.relative_to(PROJECT_ROOT)),
        bytes=len(data),
        sha256=digest,
    )


def main() -> None:
    ensure_grade_folders()
    posts = discover_posts()
    records: list[PdfRecord] = []
    failures: list[dict[str, str]] = []
    seen_pdf_hashes: set[str] = set()

    for post_index, (post_url, title) in enumerate(posts, start=1):
        try:
            post_html = str(fetch(post_url))
            pdf_links = extract_pdf_links(post_html)
            if not pdf_links:
                continue
            for pdf_url in pdf_links:
                grade = grade_from_text(title, post_url, urllib.parse.unquote(pdf_url))
                if grade is None:
                    continue
                record = download_pdf(pdf_url, title, grade, len(records) + 1)
                if record.sha256 in seen_pdf_hashes:
                    Path(PROJECT_ROOT / record.relative_path).unlink(missing_ok=True)
                    continue
                seen_pdf_hashes.add(record.sha256)
                record.post_url = post_url
                records.append(record)
        except Exception as exc:
            failures.append({"post_url": post_url, "title": title, "error": str(exc)})
        if post_index % 20 == 0:
            print(f"posts={post_index} pdfs={len(records)} failures={len(failures)}")
        time.sleep(0.15)

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": BASE_URL,
        "category_url": f"{BASE_URL}/category",
        "post_count": len(posts),
        "pdf_count": len(records),
        "by_grade": {str(grade): sum(1 for record in records if record.grade == grade) for grade in range(1, 7)},
        "records": [asdict(record) for record in records],
        "failures": failures,
    }
    MANIFEST_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("post_count", "pdf_count", "by_grade")}, ensure_ascii=False, indent=2))
    if failures:
        print(f"failures={len(failures)} see {MANIFEST_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
