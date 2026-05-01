from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import shutil
import sys
import unicodedata
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_curriculum_problem_bank import make_problem



DEFAULT_CONFIG = PROJECT_ROOT / "data" / "problem_bank" / "beta" / "elementary_50k_config.json"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data" / "problem_bank" / "elementary_50k" / "00_collected"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
PDF_SUFFIXES = {".pdf"}
JSON_SUFFIXES = {".json"}
LOCAL_SOURCE_ROOTS = (
    PROJECT_ROOT / "02.학습문제" / "05.문제은행" / "01.초등",
    PROJECT_ROOT / "03.학습문제" / "05.문제은행" / "01.초등",
    PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_app_validation_segments",
    PROJECT_ROOT / "data" / "problem_bank" / "elementary_50k" / "01_actual_pdf_capture" / "cards",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def template_uniqueness_key(record: dict[str, Any]) -> str:
    lines = record.get("lines") or []
    problem_text = str(record.get("problem_text") or "\n".join(str(line or "") for line in lines)).strip()
    payload = {
        "problem_text": problem_text,
        "expected_expression": record.get("expected_expression"),
        "answer": record.get("answer") or record.get("expected_answer"),
        "table": record.get("table") or [],
        "diagram": record.get("diagram") or {},
        "layout": record.get("layout"),
        "topic": record.get("topic"),
        "unit": record.get("unit"),
    }
    return hashlib.sha1(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def external_problem_uniqueness_key(record: dict[str, Any]) -> str:
    content = record.get("content") if isinstance(record.get("content"), dict) else {}
    search = record.get("search") if isinstance(record.get("search"), dict) else {}
    problem_text = str(
        content.get("problem_plain")
        or content.get("problem_latex")
        or search.get("problem_text")
        or record.get("id")
        or ""
    )
    text = unicodedata.normalize("NFKC", problem_text).lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w+\-*/=<>()[\]{}.,:% ]+", "", text, flags=re.UNICODE)
    text = text.strip()
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def relative_to_project(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except Exception:
        return str(path)


def project_path(value: str | Path | None, *, default: Path) -> Path:
    if not value:
        return default
    path = Path(str(value)).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def safe_name(value: str, *, limit: int = 160) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    text = re.sub(r"[\\/:*?\"<>|]+", "_", text)
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"_+", "_", text).strip("._ ")
    return (text or "record")[:limit]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def infer_grade(path: Path, record: dict[str, Any] | None = None) -> str:
    if record:
        grade = record.get("grade") or record.get("grade_number")
        if isinstance(grade, int) and 1 <= grade <= 6:
            return f"{grade}학년"
        if isinstance(grade, str) and re.search(r"[1-6]", grade):
            return f"{re.search(r'[1-6]', grade).group(0)}학년"
    text = unicodedata.normalize("NFC", str(path))
    for pattern in (
        r"/([1-6])학년/",
        r"초\s*([1-6])",
        r"g([1-6])",
        r"grade[_-]?([1-6])",
    ):
        match = re.search(pattern, text, flags=re.I)
        if match:
            return f"{match.group(1)}학년"
    return "unknown"


def classify_local_source(path: Path) -> str:
    text = unicodedata.normalize("NFC", str(path))
    if "/PDF/" in text and path.suffix.lower() == ".pdf":
        return "source_pdf"
    if "/EDITE/" in text and path.suffix.lower() in IMAGE_SUFFIXES:
        return "edite_page_image"
    if "coco_app_validation_segments" in text or "01_actual_pdf_capture/cards" in text:
        return "previous_capture_card_image"
    if path.suffix.lower() in IMAGE_SUFFIXES:
        return "local_image"
    return "local_file"


def collect_local_files(roots: Iterable[Path], *, output_root: Path) -> list[dict[str, Any]]:
    candidates: list[Path] = []
    suffixes = PDF_SUFFIXES | IMAGE_SUFFIXES
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in suffixes:
                continue
            if output_root in path.parents:
                continue
            candidates.append(path)

    seen_hashes: set[str] = set()
    records: list[dict[str, Any]] = []
    for path in sorted(candidates, key=lambda item: str(item)):
        try:
            digest = file_sha256(path)
        except Exception:
            continue
        if digest in seen_hashes:
            continue
        seen_hashes.add(digest)
        records.append(
            {
                "collection_id": f"actual_source_{len(records) + 1:05d}",
                "track": "actual_pdf_capture",
                "source_type": classify_local_source(path),
                "school_level": "초등",
                "grade": infer_grade(path),
                "path": relative_to_project(path),
                "suffix": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
                "sha256": digest,
                "status": "source_collected_not_verified",
            }
        )
    return records


def symlink_local_sources(records: list[dict[str, Any]], target_dir: Path) -> None:
    shutil.rmtree(target_dir, ignore_errors=True)
    target_dir.mkdir(parents=True, exist_ok=True)
    for record in records:
        source = PROJECT_ROOT / str(record["path"])
        if not source.exists():
            continue
        grade = safe_name(str(record.get("grade") or "unknown"), limit=24)
        source_type = safe_name(str(record.get("source_type") or "source"), limit=48)
        folder = target_dir / grade / source_type
        folder.mkdir(parents=True, exist_ok=True)
        link = folder / f"{record['collection_id']}_{safe_name(source.name, limit=120)}"
        try:
            if link.exists() or link.is_symlink():
                link.unlink()
            os.symlink(os.path.relpath(source, start=folder), link)
            record["collected_file_path"] = relative_to_project(link)
        except OSError:
            shutil.copy2(source, link)
            record["collected_file_path"] = relative_to_project(link)
            record["collection_copy_mode"] = "copied"


def catalog_banks(config: dict[str, Any]) -> list[dict[str, Any]]:
    source_config = config.get("normalized_json_sources") if isinstance(config.get("normalized_json_sources"), dict) else {}
    catalog_path = project_path(source_config.get("catalog_path"), default=PROJECT_ROOT / "data/problem_bank/catalog.json")
    catalog = read_json(catalog_path)
    allowed = {str(item) for item in source_config.get("candidate_bank_ids") or []}
    banks: list[dict[str, Any]] = []
    for bank in catalog.get("banks") or []:
        if not isinstance(bank, dict):
            continue
        bank_id = str(bank.get("bank_id") or "")
        if allowed and bank_id not in allowed:
            continue
        manifest_path = project_path(bank.get("manifest_path"), default=PROJECT_ROOT / "__missing__.json")
        if manifest_path.exists():
            banks.append({**bank, "manifest_abs_path": manifest_path})
    return banks


def shard_paths_for_bank(bank: dict[str, Any]) -> list[Path]:
    manifest_path = Path(str(bank["manifest_abs_path"]))
    manifest = read_json(manifest_path)
    root = manifest_path.parent
    paths: list[Path] = []
    for shard in manifest.get("shards") or []:
        if not isinstance(shard, dict) or not shard.get("path"):
            continue
        path = root / str(shard["path"])
        if path.exists():
            paths.append(path)
    return paths


def record_priority(record: dict[str, Any]) -> tuple[int, int, int, str]:
    taxonomy = record.get("taxonomy") if isinstance(record.get("taxonomy"), dict) else {}
    structure = record.get("structure") if isinstance(record.get("structure"), dict) else {}
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    quality = metadata.get("quality") if isinstance(metadata.get("quality"), dict) else {}
    grade_band = str(taxonomy.get("grade_band") or "")
    level = int(taxonomy.get("level_number") or 9)
    language = str((record.get("content") or {}).get("language") or "")
    review = bool(quality.get("needs_review"))
    rendering = bool(structure.get("requires_rendering"))
    grade_score = {"elementary": 0, "elementary_middle": 1, "middle": 3}.get(grade_band, 2)
    review_score = 1 if review else 0
    render_score = 1 if rendering else 0
    language_score = 0 if language in {"ko", "en", ""} else 1
    return (review_score, grade_score, max(0, level), render_score + language_score, str(record.get("id") or ""))


def iter_external_records(banks: list[dict[str, Any]]) -> Iterable[tuple[str, dict[str, Any], Path]]:
    for bank in banks:
        bank_id = str(bank.get("bank_id") or "")
        for shard_path in shard_paths_for_bank(bank):
            payload = read_json(shard_path)
            if not isinstance(payload, list):
                continue
            for record in payload:
                if isinstance(record, dict):
                    yield bank_id, record, shard_path


def select_external_records(
    config: dict[str, Any],
    *,
    count: int,
    allowed_grade_bands: set[str] | None = None,
) -> list[dict[str, Any]]:
    banks = catalog_banks(config)
    candidates: list[tuple[tuple[int, int, int, str], str, dict[str, Any], Path]] = []
    for bank_id, record, shard_path in iter_external_records(banks):
        answer = record.get("answer") if isinstance(record.get("answer"), dict) else {}
        if not str(answer.get("final_normalized") or answer.get("final_raw") or "").strip():
            continue
        content = record.get("content") if isinstance(record.get("content"), dict) else {}
        learning = record.get("learning") if isinstance(record.get("learning"), dict) else {}
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        quality = metadata.get("quality") if isinstance(metadata.get("quality"), dict) else {}
        solution_text = str(content.get("solution_plain") or content.get("solution_latex") or "").strip()
        if not solution_text and not any(str(step or "").strip() for step in (learning.get("step_outline") or [])):
            continue
        if solution_text.upper() in {"N/A", "N.A", "NA"}:
            continue
        if bool(quality.get("needs_review")):
            continue
        taxonomy = record.get("taxonomy") if isinstance(record.get("taxonomy"), dict) else {}
        grade_band = str(taxonomy.get("grade_band") or "unknown")
        if allowed_grade_bands is not None and grade_band not in allowed_grade_bands:
            continue
        candidates.append((record_priority(record), bank_id, record, shard_path))
    candidates.sort(key=lambda item: item[0])
    selected: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for _, bank_id, record, shard_path in candidates:
        key = external_problem_uniqueness_key(record)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        taxonomy = record.get("taxonomy") if isinstance(record.get("taxonomy"), dict) else {}
        selected.append(
            {
                "collection_id": f"normalized_json_{len(selected) + 1:05d}",
                "track": "normalized_json",
                "source_type": "external_problem_bank_record",
                "school_level": "초등",
                "grade": str(taxonomy.get("grade_band") or "unknown"),
                "bank_id": bank_id,
                "record_id": record.get("id"),
                "source_shard": relative_to_project(shard_path),
                "status": "candidate_not_verified",
                "record": record,
            }
        )
        if len(selected) >= count:
            break
    return selected


def materialize_json_records(records: list[dict[str, Any]], target_dir: Path, *, record_key: str = "record") -> None:
    shutil.rmtree(target_dir, ignore_errors=True)
    for record in records:
        bank_or_grade = safe_name(str(record.get("bank_id") or record.get("grade") or "records"), limit=64)
        collection_id = safe_name(str(record.get("collection_id") or "record"), limit=80)
        target = target_dir / bank_or_grade / f"{collection_id}.json"
        payload = dict(record)
        inner = payload.pop(record_key, None)
        if inner is not None:
            payload[record_key] = inner
        write_json(target, payload)
        record["collected_file_path"] = relative_to_project(target)


def load_template_records(config: dict[str, Any], *, count: int) -> list[dict[str, Any]]:
    template_config = config.get("template_variant") if isinstance(config.get("template_variant"), dict) else {}
    manifest_path = project_path(
        template_config.get("manifest"),
        default=PROJECT_ROOT / "data/problem_bank/elementary_50k/template_variants_manifest.json",
    )
    payload = read_json(manifest_path)
    records = payload.get("records") if isinstance(payload, dict) else []
    selected: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for raw in records:
        if not isinstance(raw, dict):
            continue
        key = template_uniqueness_key(raw)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        selected.append(
            {
                "collection_id": f"template_variant_{len(selected) + 1:05d}",
                "track": "template_variant",
                "source_type": "generated_template_candidate",
                "school_level": "초등",
                "grade": infer_grade(Path(str(raw.get("file_name") or "")), raw),
                "record_id": raw.get("card_id") or raw.get("problem_id"),
                "status": "candidate_not_verified",
                "record": raw,
            }
        )
        if len(selected) >= count:
            break
    return selected


def make_reserve_payload(*, grade: int, absolute_index: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed + grade * 100_003 + absolute_index * 9_973)
    family = absolute_index % 12
    item = rng.choice(["사탕", "연필", "구슬", "카드", "색종이", "스티커", "공책", "책"])
    person = rng.choice(["민지", "준호", "서연", "도윤", "하린", "지우", "현우", "수아"])
    difficulty = ("easy", "medium", "hard")[absolute_index % 3]

    if grade == 1:
        if family in {0, 6}:
            a, b = rng.randint(1, 9), rng.randint(1, 9)
            answer = a + b
            lines = [f"{person}는 {item} {a}개와 {b}개를 가지고 있습니다.", f"{item}는 모두 몇 개입니까?"]
            expression = f"{a}+{b}"
            topic, unit, area, layout = "arithmetic", "9까지의 수와 덧셈·뺄셈", "수와 연산", "word"
        elif family in {1, 7}:
            a, b = sorted([rng.randint(1, 9), rng.randint(1, 9)])
            answer = a
            lines = [f"{a}와 {b} 중 더 작은 수를 고르시오."]
            expression = f"min({a},{b})"
            topic, unit, area, layout = "comparison", "수의 크기 비교", "수와 연산", "expression"
        elif family in {2, 8}:
            start = rng.randint(1, 4)
            diff = rng.choice([1, 2])
            seq = [start + diff * idx for idx in range(4)]
            answer = seq[-1] + diff
            lines = ["규칙을 찾아 빈칸에 알맞은 수를 쓰시오.", f"{seq[0]}, {seq[1]}, {seq[2]}, {seq[3]}, □"]
            expression = f"{seq[-1]}+{diff}"
            topic, unit, area, layout = "pattern", "규칙 찾기", "변화와 관계", "expression"
        else:
            total = rng.randint(5, 18)
            used = rng.randint(1, total - 1)
            answer = total - used
            lines = [f"{item}가 {total}개 있습니다. 그중 {used}개를 사용했습니다.", f"남은 {item}는 몇 개입니까?"]
            expression = f"{total}-{used}"
            topic, unit, area, layout = "arithmetic", "덧셈과 뺄셈", "수와 연산", "word"
    elif grade == 2:
        if family in {0, 4, 8}:
            a, b = rng.randint(2, 9), rng.randint(2, 9)
            answer = a * b
            lines = [f"{a}개씩 {b}묶음이 있습니다.", "모두 몇 개입니까?"]
            expression = f"{a}*{b}"
            topic, unit, area, layout = "multiplication", "곱셈구구", "수와 연산", "word"
        elif family in {1, 5, 9}:
            hour = rng.randint(1, 10)
            minutes = rng.choice([5, 10, 15, 20, 25, 30, 35, 40, 45, 50])
            add = rng.choice([10, 15, 20, 30, 40])
            total_minutes = minutes + add
            answer = f"{hour + total_minutes // 60}시 {total_minutes % 60}분"
            lines = [f"{hour}시 {minutes}분에서 {add}분 뒤의 시각을 쓰시오."]
            expression = f"{hour}:{minutes}+{add}m"
            topic, unit, area, layout = "time", "시각과 시간", "도형과 측정", "expression"
        elif family in {2, 6, 10}:
            length = rng.randint(20, 120)
            cut = rng.randint(5, min(60, length - 1))
            answer = length - cut
            lines = [f"{length} cm인 끈에서 {cut} cm를 잘랐습니다.", "남은 길이는 몇 cm입니까?"]
            expression = f"{length}-{cut}"
            topic, unit, area, layout = "measurement", "길이", "도형과 측정", "word"
        else:
            a, b, c = rng.randint(100, 800), rng.randint(30, 180), rng.randint(10, 90)
            answer = a + b - c
            lines = ["다음 식의 값을 구하시오.", f"{a} + {b} - {c}"]
            expression = f"{a}+{b}-{c}"
            topic, unit, area, layout = "arithmetic", "세 자리 수", "수와 연산", "expression"
    elif grade == 3:
        if family in {0, 4, 8}:
            divisor = rng.randint(2, 9)
            quotient = rng.randint(3, 30)
            total = divisor * quotient
            answer = quotient
            lines = [f"{total}개를 {divisor}명에게 똑같이 나누어 주려고 합니다.", "한 명이 받는 개수는 몇 개입니까?"]
            expression = f"{total}/{divisor}"
            topic, unit, area, layout = "division", "나눗셈", "수와 연산", "word"
        elif family in {1, 5, 9}:
            denominator = rng.choice([3, 4, 5, 6, 8, 10])
            numerator = rng.randint(1, denominator - 1)
            answer = f"{numerator}/{denominator}"
            lines = [f"전체를 {denominator}등분한 것 중 {numerator}부분을 색칠했습니다.", "색칠한 부분을 분수로 쓰시오."]
            expression = answer
            topic, unit, area, layout = "fraction", "분수", "수와 연산", "visual"
        elif family in {2, 6, 10}:
            radius = rng.randint(2, 12)
            answer = radius * 2
            lines = [f"반지름이 {radius} cm인 원의 지름을 구하시오."]
            expression = f"{radius}*2"
            topic, unit, area, layout = "geometry", "원", "도형과 측정", "geometry"
        else:
            values = [rng.randint(2, 40) for _ in range(4)]
            answer = max(values) - min(values)
            lines = ["다음 자료에서 가장 큰 수와 가장 작은 수의 차를 구하시오.", ", ".join(str(value) for value in values)]
            expression = f"{max(values)}-{min(values)}"
            topic, unit, area, layout = "statistics", "막대그래프", "자료와 가능성", "table"
    elif grade == 4:
        if family in {0, 4, 8}:
            a, b = rng.randint(1000, 90000), rng.randint(1000, 90000)
            answer = a + b
            lines = ["다음 두 수의 합을 구하시오.", f"{a:,} + {b:,}"]
            expression = f"{a}+{b}"
            topic, unit, area, layout = "big_number", "큰 수", "수와 연산", "expression"
        elif family in {1, 5, 9}:
            angle = rng.randint(20, 150)
            add = rng.randint(10, 60)
            answer = angle + add
            lines = [f"{angle}도인 각보다 {add}도 큰 각은 몇 도입니까?"]
            expression = f"{angle}+{add}"
            topic, unit, area, layout = "angle", "각도", "도형과 측정", "geometry"
        elif family in {2, 6, 10}:
            denominator = rng.choice([10, 100, 1000])
            numerator = rng.randint(1, denominator - 1)
            answer = round(numerator / denominator, 3)
            lines = [f"{numerator}/{denominator}을 소수로 나타내시오."]
            expression = f"{numerator}/{denominator}"
            topic, unit, area, layout = "decimal", "분수와 소수", "수와 연산", "expression"
        else:
            values = [rng.randint(10, 90) for _ in range(5)]
            answer = sum(values)
            lines = ["막대그래프에 나타난 수량의 합을 구하시오.", ", ".join(str(value) for value in values)]
            expression = "+".join(str(value) for value in values)
            topic, unit, area, layout = "statistics", "꺾은선그래프와 막대그래프", "자료와 가능성", "table"
    elif grade == 5:
        if family in {0, 4, 8}:
            a, b = rng.randint(12, 96), rng.randint(12, 96)
            answer = math.gcd(a, b)
            lines = [f"{a}와 {b}의 최대공약수를 구하시오."]
            expression = f"gcd({a},{b})"
            topic, unit, area, layout = "factors_multiples", "약수와 배수", "수와 연산", "expression"
        elif family in {1, 5, 9}:
            width, height = rng.randint(6, 40), rng.randint(5, 30)
            answer = width * height
            lines = [f"가로 {width} cm, 세로 {height} cm인 직사각형의 넓이를 구하시오."]
            expression = f"{width}*{height}"
            topic, unit, area, layout = "area", "다각형의 둘레와 넓이", "도형과 측정", "geometry"
        elif family in {2, 6, 10}:
            values = [rng.randint(40, 100) for _ in range(5)]
            answer = sum(values) / len(values)
            lines = ["다음 다섯 수의 평균을 구하시오.", ", ".join(str(value) for value in values)]
            expression = f"({'+'.join(str(value) for value in values)})/5"
            topic, unit, area, layout = "average", "평균", "자료와 가능성", "table"
        else:
            numerator = rng.randint(1, 9)
            denominator = rng.choice([2, 3, 4, 5, 6, 8, 10])
            multiplier = rng.randint(2, 9)
            answer = f"{numerator * multiplier}/{denominator}"
            lines = ["다음 분수의 곱셈을 하시오.", f"{numerator}/{denominator} × {multiplier}"]
            expression = f"{numerator}/{denominator}*{multiplier}"
            topic, unit, area, layout = "fraction", "분수의 계산", "수와 연산", "expression"
    else:
        if family in {0, 4, 8}:
            a, b = rng.randint(2, 18), rng.randint(2, 18)
            scale = rng.randint(2, 9)
            answer = b * scale
            lines = [f"{a}:{b} = {a * scale}:□ 일 때 □ 안에 알맞은 수를 구하시오."]
            expression = f"{b}*{scale}"
            topic, unit, area, layout = "ratio", "비례식과 비율", "변화와 관계", "expression"
        elif family in {1, 5, 9}:
            numerator = rng.randint(2, 9)
            denominator = rng.choice([3, 4, 5, 6, 8, 10, 12])
            divisor = rng.randint(2, 9)
            answer = f"{numerator}/{denominator * divisor}"
            lines = ["다음 분수의 나눗셈을 하시오.", f"{numerator}/{denominator} ÷ {divisor}"]
            expression = f"{numerator}/{denominator}/{divisor}"
            topic, unit, area, layout = "fraction_division", "분수·소수의 나눗셈", "수와 연산", "expression"
        elif family in {2, 6, 10}:
            radius = rng.randint(2, 12)
            height = rng.randint(3, 20)
            answer = 3.14 * radius * radius * height
            lines = [f"반지름 {radius} cm, 높이 {height} cm인 원기둥의 부피를 구하시오. 원주율은 3.14로 합니다."]
            expression = f"3.14*{radius}*{radius}*{height}"
            topic, unit, area, layout = "solid_geometry", "원과 입체도형", "도형과 측정", "geometry"
        else:
            values = [rng.randint(5, 60) for _ in range(4)]
            answer = max(values)
            lines = ["띠그래프에 나타난 항목 중 가장 큰 값을 고르시오.", ", ".join(str(value) for value in values)]
            expression = f"max({','.join(str(value) for value in values)})"
            topic, unit, area, layout = "statistics", "여러 그래프", "자료와 가능성", "table"

    answer_text = str(answer).rstrip("0").rstrip(".") if isinstance(answer, float) else str(answer)
    return {
        "problem_id": f"elementary_reserve_g{grade:02d}_{absolute_index:05d}",
        "band": "초등",
        "grade": grade,
        "difficulty": difficulty,
        "layout": layout,
        "area": area,
        "unit": unit,
        "topic": topic,
        "folder": f"01.초등/{grade}학년/{area}/{unit}",
        "file_name": f"elementary_reserve_g{grade:02d}_{absolute_index:05d}_{layout}_{topic}.png",
        "title": f"초등 {grade}학년 · {unit} · reserve",
        "lines": lines,
        "expected_answer": answer_text,
        "expected_expression": expression,
        "table": [],
        "diagram": {},
        "source_basis": "초등 수학 베타 안정화용 reserve 템플릿",
    }


def generate_template_reserve_records(*, count: int, start_index: int = 0, seed: int = 20260430) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if count <= 0:
        return records
    seen_keys: set[str] = set()
    offset = 0
    attempts = 0
    while len(records) < count and attempts < count * 20:
        absolute_index = start_index + offset + 1
        grade = (offset % 6) + 1
        raw = make_reserve_payload(grade=grade, absolute_index=absolute_index, seed=seed)
        payload = {
            **raw,
            "card_id": f"coco50k_template_reserve_g{grade:02d}_{absolute_index:05d}",
            "track": "template_variant",
            "school_level": "초등",
            "status": "candidate_not_rendered",
            "problem_text": "\n".join(str(line) for line in raw["lines"]),
            "answer": raw["expected_answer"],
            "source": {
                "name": "Coco elementary reserve template variant",
                "policy": "reserve_candidate_only_until_solver_and_render_validation",
                "seed": seed,
            },
            "validation": {
                "render_required": True,
                "solver_required": True,
                "app_capture_required": False,
                "verified": False,
            },
        }
        key = template_uniqueness_key(payload)
        offset += 1
        attempts += 1
        if key in seen_keys:
            continue
        seen_keys.add(key)
        records.append(
            {
                "collection_id": f"template_reserve_{len(records) + 1:05d}",
                "track": "template_variant",
                "source_type": "generated_template_reserve_candidate",
                "school_level": "초등",
                "grade": f"{grade}학년",
                "record_id": payload["card_id"],
                "status": "candidate_not_verified",
                "record": payload,
            }
        )
    if len(records) < count:
        raise RuntimeError(f"could only generate {len(records)} unique reserve templates out of {count}")
    return records


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_track = Counter(str(record.get("track") or "unknown") for record in records)
    by_source_type = Counter(str(record.get("source_type") or "unknown") for record in records)
    by_grade = Counter(str(record.get("grade") or "unknown") for record in records)
    by_bank = Counter(str(record.get("bank_id") or "local_or_template") for record in records)
    return {
        "total_files_prepared": len(records),
        "by_track": dict(sorted(by_track.items())),
        "by_source_type": dict(sorted(by_source_type.items())),
        "by_grade": dict(sorted(by_grade.items())),
        "by_bank": dict(sorted(by_bank.items())),
    }


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            slim = {key: value for key, value in record.items() if key != "record"}
            handle.write(json.dumps(slim, ensure_ascii=False, sort_keys=True) + "\n")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect and materialize Coco elementary 50k source files.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--target", type=int, default=50000)
    parser.add_argument("--template-count", type=int, default=15000)
    parser.add_argument(
        "--allow-non-elementary-reserve",
        action="store_true",
        help="Allow advanced external records only when elementary/elementary-middle sources are not enough.",
    )
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--no-materialize", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    config = read_json(project_path(args.config, default=DEFAULT_CONFIG))
    output_root = project_path(args.output_root, default=DEFAULT_OUTPUT_ROOT)
    if args.clean:
        shutil.rmtree(output_root, ignore_errors=True)
    output_root.mkdir(parents=True, exist_ok=True)

    actual_records = collect_local_files(LOCAL_SOURCE_ROOTS, output_root=output_root)
    template_count = min(max(0, args.template_count), max(0, args.target - len(actual_records)))
    template_records = load_template_records(config, count=template_count)
    remaining = max(0, args.target - len(actual_records) - len(template_records))
    allowed_grade_bands = None if args.allow_non_elementary_reserve else {"elementary", "elementary_middle"}
    normalized_records = select_external_records(config, count=remaining, allowed_grade_bands=allowed_grade_bands)
    reserve_count = max(0, args.target - len(actual_records) - len(normalized_records) - len(template_records))
    reserve_records = generate_template_reserve_records(
        count=reserve_count,
        start_index=len(template_records),
        seed=int(((config.get("template_variant") or {}).get("seed") or 20260429)) + 1,
    )
    records = [*actual_records, *normalized_records, *template_records, *reserve_records]
    records = records[: args.target]

    if not args.no_materialize:
        symlink_local_sources(actual_records, output_root / "actual_source_files")
        materialize_json_records(normalized_records, output_root / "normalized_json")
        materialize_json_records([*template_records, *reserve_records], output_root / "template_variants")

    manifest_records = [{key: value for key, value in record.items() if key != "record"} for record in records]
    summary = summarize(records)
    payload = {
        "schema_version": "coco_elementary_50k_source_collection.v1",
        "generated_at": utc_now(),
        "target": args.target,
        "output_root": relative_to_project(output_root),
        "summary": summary,
        "records_jsonl": relative_to_project(output_root / "records.jsonl"),
        "records": manifest_records,
        "notes": [
            "Actual PDF/image files are collected as symlinks so original sources remain untouched.",
            "External JSON and generated template records are materialized as individual candidate files.",
            "candidate_not_verified records must pass downstream validation before promotion.",
            "Default collection excludes non-elementary external grade bands; shortage is filled by elementary reserve templates.",
        ],
    }
    write_json(output_root / "source_collection_manifest.json", payload)
    write_jsonl(output_root / "records.jsonl", records)
    write_json(PROJECT_ROOT / "data" / "problem_bank" / "learned" / "elementary_50k_source_collection_report.json", payload)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if len(records) >= args.target else 2


if __name__ == "__main__":
    raise SystemExit(main())
