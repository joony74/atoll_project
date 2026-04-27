from __future__ import annotations

import argparse
import json
import re
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "problem_bank" / "sources" / "tal_scq5k"
CATALOG_PATH = PROJECT_ROOT / "data" / "problem_bank" / "catalog.json"
EXTERNAL_SOURCES_PATH = PROJECT_ROOT / "data" / "problem_bank" / "external_math_sources.json"

RAW_ROOT = "https://raw.githubusercontent.com/math-eval/TAL-SCQ5K/main"
DEFAULT_SPLIT_URLS = {
    "en_train": f"{RAW_ROOT}/en_single_choice_constructed_5K/en_single_choice_train_3K.jsonl",
    "en_test": f"{RAW_ROOT}/en_single_choice_constructed_5K/en_single_choice_test_2K.jsonl",
    "zh_train": f"{RAW_ROOT}/ch_single_choice_constructed_5K/ch_single_choice_train_3K.jsonl",
    "zh_test": f"{RAW_ROOT}/ch_single_choice_constructed_5K/ch_single_choice_test_2K.jsonl",
}

DOMAIN_ALIASES = {
    "number theory": ("Number Theory", "number_theory"),
    "division without remainders": ("Number Theory", "number_theory"),
    "divisibility": ("Number Theory", "number_theory"),
    "geometry": ("Geometry", "geometry"),
    "algebra": ("Algebra", "algebra"),
    "equation": ("Algebra", "algebra"),
    "function": ("Algebra", "algebra"),
    "probability": ("Counting & Probability", "counting_probability"),
    "combinatorics": ("Counting & Probability", "counting_probability"),
    "counting": ("Counting & Probability", "counting_probability"),
    "ratio": ("Prealgebra", "prealgebra"),
    "fraction": ("Prealgebra", "prealgebra"),
    "percent": ("Prealgebra", "prealgebra"),
    "decimal": ("Prealgebra", "prealgebra"),
    "calculation": ("Prealgebra", "prealgebra"),
    "integer": ("Number Theory", "number_theory"),
    "计算": ("Prealgebra", "prealgebra"),
    "小数": ("Prealgebra", "prealgebra"),
    "分数": ("Prealgebra", "prealgebra"),
    "百分": ("Prealgebra", "prealgebra"),
    "比例": ("Prealgebra", "prealgebra"),
    "数论": ("Number Theory", "number_theory"),
    "整数": ("Number Theory", "number_theory"),
    "整除": ("Number Theory", "number_theory"),
    "余数": ("Number Theory", "number_theory"),
    "几何": ("Geometry", "geometry"),
    "图形": ("Geometry", "geometry"),
    "面积": ("Geometry", "geometry"),
    "代数": ("Algebra", "algebra"),
    "方程": ("Algebra", "algebra"),
    "函数": ("Algebra", "algebra"),
    "概率": ("Counting & Probability", "counting_probability"),
    "组合": ("Counting & Probability", "counting_probability"),
    "排列": ("Counting & Probability", "counting_probability"),
    "计数": ("Counting & Probability", "counting_probability"),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_jsonl_url(url: str) -> list[dict[str, Any]]:
    with urllib.request.urlopen(url, timeout=60) as response:
        text = response.read().decode("utf-8")
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"invalid JSONL at {url}:{line_number}") from exc
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def slugify(value: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9가-힣]+", "_", text)
    return text.strip("_") or "unknown"


def strip_latex_for_search(text: str) -> str:
    plain = str(text or "")
    plain = plain.replace("$$", " ").replace("$", " ")
    plain = plain.replace("\\\\", " ")
    plain = re.sub(r"\\(?:left|right|text|mathrm|operatorname|overline|textasciitilde)\b", " ", plain)
    plain = re.sub(r"\\[a-zA-Z]+", " ", plain)
    plain = re.sub(r"[{}\\]", " ", plain)
    plain = re.sub(r"\s+", " ", plain)
    return plain.strip()


def normalize_answer(answer: str) -> str:
    text = str(answer or "").strip()
    text = text.strip("$ ")
    text = re.sub(r"^\$+\s*|\s*\$+$", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def infer_answer_type(answer: str) -> str:
    text = normalize_answer(answer)
    if not text:
        return "unknown"
    cleaned = text.replace(",", "")
    if re.fullmatch(r"[+-]?\d+", cleaned):
        return "integer"
    if re.fullmatch(r"[+-]?(?:\d+\.\d*|\.\d+)", cleaned):
        return "decimal"
    if re.fullmatch(r"[+-]?\d+/\d+", cleaned) or "\\frac" in text:
        return "fraction"
    if any(token in text for token in ("x", "y", "\\sqrt", "^", "=")):
        return "expression"
    return "text"


def difficulty_to_level(value: Any) -> int:
    try:
        level = int(str(value or "0").strip()) + 1
    except ValueError:
        level = 3
    return max(1, min(level, 5))


def language_for_split(split: str) -> str:
    return "zh" if split.startswith("zh_") else "en"


def grade_band_for_level(level_number: int) -> str:
    if level_number <= 2:
        return "elementary"
    if level_number <= 4:
        return "middle"
    return "high"


def flatten_choice_items(answer_option_list: Any) -> list[dict[str, str]]:
    choices: list[dict[str, str]] = []
    if not isinstance(answer_option_list, list):
        return choices
    for group in answer_option_list:
        items = group if isinstance(group, list) else [group]
        for item in items:
            if not isinstance(item, dict):
                continue
            label = str(item.get("aoVal") or "").strip()
            content = normalize_answer(str(item.get("content") or ""))
            if label or content:
                choices.append({"label": label, "content": content})
    return choices


def answer_content(choices: list[dict[str, str]], answer_value: str) -> str:
    target = str(answer_value or "").strip()
    for choice in choices:
        if str(choice.get("label") or "").strip() == target:
            return str(choice.get("content") or "").strip()
    return target


def format_choices_for_problem(choices: list[dict[str, str]]) -> str:
    parts = []
    for choice in choices:
        label = str(choice.get("label") or "").strip()
        content = str(choice.get("content") or "").strip()
        if label and content:
            parts.append(f"({label}) {content}")
    return "\n".join(parts)


def split_solution_steps(answer_analysis: Any) -> list[str]:
    if isinstance(answer_analysis, list):
        raw = "\n".join(str(item or "").strip() for item in answer_analysis if str(item or "").strip())
    else:
        raw = str(answer_analysis or "").strip()
    if not raw:
        return []
    parts = [part.strip() for part in re.split(r"(?<=[.!?。！？])\s+", raw) if part.strip()]
    return parts[:8]


def infer_subject(routes: list[str], problem: str) -> tuple[str, str]:
    haystack = " ".join([*routes, problem]).lower()
    for needle, result in DOMAIN_ALIASES.items():
        if needle in haystack:
            return result
    return ("Competition Math", "competition_math")


def route_tags(routes: list[str]) -> list[str]:
    tags: list[str] = []
    for route in routes:
        for part in str(route or "").split("->"):
            slug = slugify(part)
            if slug and slug not in {"overseas_competition", "knowledge_point"}:
                tags.append(slug)
    return sorted(dict.fromkeys(tags))


def build_record(row: dict[str, Any], *, split: str, index: int, source_url: str, generated_at: str) -> dict[str, Any]:
    problem = str(row.get("problem") or "").strip()
    routes = [str(item or "").strip() for item in (row.get("knowledge_point_routes") or []) if str(item or "").strip()]
    choices = flatten_choice_items(row.get("answer_option_list"))
    answer_value = str(row.get("answer_value") or "").strip()
    final_raw = answer_content(choices, answer_value)
    final_normalized = normalize_answer(final_raw)
    solution_latex = "\n".join(str(item or "").strip() for item in (row.get("answer_analysis") or []) if str(item or "").strip())
    level_num = difficulty_to_level(row.get("difficulty"))
    subject, subject_slug = infer_subject(routes, problem)
    language = language_for_split(split)
    choice_text = format_choices_for_problem(choices)
    problem_latex = f"{problem}\n{choice_text}".strip() if choice_text else problem
    tags = sorted(
        dict.fromkeys(
            [
                "tal_scq5k",
                "single_choice",
                split,
                language,
                subject_slug,
                f"level_{level_num}",
                *route_tags(routes),
            ]
        )
    )

    review_reasons: list[str] = []
    if not problem:
        review_reasons.append("missing_problem")
    if not choices:
        review_reasons.append("missing_choices")
    if not answer_value:
        review_reasons.append("missing_answer_value")
    if not final_normalized:
        review_reasons.append("missing_answer_content")
    if not solution_latex:
        review_reasons.append("missing_answer_analysis")

    record_id = f"tal_scq5k:{split}:{subject_slug}:level_{level_num}:{index:05d}"
    return {
        "schema_version": "problem_bank_record.v1",
        "id": record_id,
        "source": {
            "name": "TAL-SCQ5K",
            "dataset_id": "math-eval/TAL-SCQ5K",
            "source_url": source_url,
            "license": "MIT",
            "original_index": int(index),
            "split": split,
            "source_problem_id": str(row.get("queId") or row.get("qid") or f"{split}_{index:05d}"),
        },
        "content": {
            "language": language,
            "problem_latex": problem_latex,
            "problem_plain": strip_latex_for_search(problem_latex),
            "solution_latex": solution_latex,
            "solution_plain": strip_latex_for_search(solution_latex),
        },
        "answer": {
            "final_raw": final_raw,
            "final_normalized": final_normalized,
            "candidates": sorted(dict.fromkeys([answer_value, final_normalized])),
            "extraction_method": "tal_answer_option" if final_normalized else "none",
            "answer_type": infer_answer_type(final_normalized),
        },
        "taxonomy": {
            "domain": "competition_math",
            "subject": subject,
            "subject_slug": subject_slug,
            "level": f"Level {level_num}",
            "level_number": level_num,
            "grade_band": grade_band_for_level(level_num),
            "concepts": route_tags(routes),
            "tags": tags,
        },
        "structure": {
            "format": "multiple_choice_latex_text",
            "has_asy": False,
            "has_diagram": False,
            "has_table": "\\begin{array}" in problem_latex or "\\begin{tabular}" in problem_latex,
            "has_choices": bool(choices),
            "requires_rendering": any(token in problem_latex for token in ("\\frac", "\\sqrt", "\\begin", "$")),
        },
        "learning": {
            "prerequisites": [],
            "step_outline": split_solution_steps(row.get("answer_analysis")),
            "hints": [],
            "common_mistakes": [],
        },
        "search": {
            "problem_text": strip_latex_for_search(problem_latex),
            "solution_text": strip_latex_for_search(solution_latex),
            "keywords": tags,
        },
        "metadata": {
            "created_at": generated_at,
            "updated_at": generated_at,
            "quality": {
                "solution_available": bool(solution_latex),
                "final_answer_extracted": bool(final_normalized),
                "needs_review": bool(review_reasons),
                "review_reasons": review_reasons,
            },
            "tal_scq5k": {
                "qid": str(row.get("qid") or ""),
                "queId": str(row.get("queId") or ""),
                "difficulty": str(row.get("difficulty") or ""),
                "answer_value": answer_value,
                "choices": choices,
                "knowledge_point_routes": routes,
                "competition_source_list": row.get("competition_source_list") or [],
            },
        },
    }


def lightweight_index_item(record: dict[str, Any], shard_path: str) -> dict[str, Any]:
    content = record["content"]
    taxonomy = record["taxonomy"]
    answer = record["answer"]
    structure = record["structure"]
    quality = record["metadata"]["quality"]
    return {
        "id": record["id"],
        "bank_id": "tal_scq5k",
        "shard_path": shard_path,
        "source": record["source"]["name"],
        "subject": taxonomy["subject"],
        "subject_slug": taxonomy["subject_slug"],
        "level": taxonomy["level"],
        "level_number": taxonomy["level_number"],
        "answer": answer["final_normalized"],
        "answer_type": answer["answer_type"],
        "problem_preview": content["problem_plain"][:240],
        "solution_preview": content["solution_plain"][:240],
        "keywords": record["search"]["keywords"],
        "has_asy": structure["has_asy"],
        "requires_rendering": structure["requires_rendering"],
        "needs_review": quality["needs_review"],
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def update_catalog(output_dir: Path, manifest: dict[str, Any]) -> None:
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CATALOG_PATH.exists():
        try:
            catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        except Exception:
            catalog = {}
    else:
        catalog = {}
    banks = [bank for bank in catalog.get("banks", []) if bank.get("bank_id") != manifest["bank_id"]]
    manifest_file = output_dir / "manifest.json"
    try:
        manifest_path = str(manifest_file.relative_to(PROJECT_ROOT))
    except ValueError:
        manifest_path = str(manifest_file)
    banks.append(
        {
            "bank_id": manifest["bank_id"],
            "name": manifest["source"]["name"],
            "manifest_path": manifest_path,
            "total": manifest["counts"]["total"],
            "generated_at": manifest["generated_at"],
            "import_status": "imported",
        }
    )
    catalog = {
        "schema_version": "problem_bank_catalog.v1",
        "updated_at": utc_now(),
        "banks": sorted(banks, key=lambda item: item["bank_id"]),
    }
    write_json(CATALOG_PATH, catalog)


def update_external_registry(manifest: dict[str, Any]) -> None:
    if not EXTERNAL_SOURCES_PATH.exists():
        return
    try:
        registry = json.loads(EXTERNAL_SOURCES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return
    sources = registry.get("sources") if isinstance(registry, dict) else None
    if not isinstance(sources, list):
        return
    for source in sources:
        if not isinstance(source, dict) or source.get("bank_id") != manifest["bank_id"]:
            continue
        source["import_status"] = "imported"
        source["imported_total"] = manifest["counts"]["total"]
        source["imported_at"] = manifest["generated_at"]
        source["import_mode"] = "jsonl_adapter"
    registry["updated_at"] = utc_now()
    write_json(EXTERNAL_SOURCES_PATH, registry)


def import_bank(output_dir: Path, limit_per_split: int = 0) -> dict[str, Any]:
    generated_at = utc_now()
    records: list[dict[str, Any]] = []
    split_counts: dict[str, int] = {}
    for split, url in DEFAULT_SPLIT_URLS.items():
        rows = read_jsonl_url(url)
        if limit_per_split > 0:
            rows = rows[:limit_per_split]
        split_counts[split] = len(rows)
        records.extend(
            build_record(row, split=split, index=index, source_url=url, generated_at=generated_at)
            for index, row in enumerate(rows)
        )

    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        taxonomy = record["taxonomy"]
        grouped[(record["source"]["split"], taxonomy["subject_slug"], int(taxonomy["level_number"]))].append(record)

    shards: list[dict[str, Any]] = []
    index_items: list[dict[str, Any]] = []
    for (split, subject_slug, level_num), shard_records in sorted(grouped.items()):
        shard_path = Path("shards") / split / subject_slug / f"level_{level_num}.json"
        write_json(output_dir / shard_path, shard_records)
        shards.append(
            {
                "path": str(shard_path),
                "count": len(shard_records),
                "subject": shard_records[0]["taxonomy"]["subject"],
                "subject_slug": subject_slug,
                "level": shard_records[0]["taxonomy"]["level"],
                "level_number": level_num,
                "split": split,
            }
        )
        index_items.extend(lightweight_index_item(record, str(shard_path)) for record in shard_records)

    index_items = sorted(index_items, key=lambda item: item["id"])
    index_path = Path("index") / "problem_index.json"
    write_json(output_dir / index_path, index_items)

    by_subject = Counter(record["taxonomy"]["subject"] for record in records)
    by_level = Counter(record["taxonomy"]["level"] for record in records)
    by_split = Counter(record["source"]["split"] for record in records)
    by_language = Counter(record["content"]["language"] for record in records)
    answer_missing = sum(1 for record in records if not record["metadata"]["quality"]["final_answer_extracted"])
    manifest = {
        "schema_version": "problem_bank_manifest.v1",
        "bank_id": "tal_scq5k",
        "generated_at": generated_at,
        "source": {
            "name": "TAL-SCQ5K",
            "dataset_id": "math-eval/TAL-SCQ5K",
            "source_url": "https://github.com/math-eval/TAL-SCQ5K",
            "license": "MIT",
            "raw_sources": DEFAULT_SPLIT_URLS,
            "notes": "Imported English and Chinese single-choice constructed math competition JSONL files from the public GitHub repository.",
        },
        "storage": {
            "format": "json_shards",
            "encoding": "utf-8",
            "record_schema": "../../schema/problem_bank_record.schema.json",
        },
        "counts": {
            "total": len(records),
            "by_subject": dict(sorted(by_subject.items())),
            "by_level": dict(sorted(by_level.items())),
            "by_split": dict(sorted(by_split.items())),
            "by_language": dict(sorted(by_language.items())),
            "answer_missing": answer_missing,
        },
        "shards": shards,
        "indexes": {
            "lightweight": str(index_path),
        },
    }
    write_json(output_dir / "manifest.json", manifest)
    update_catalog(output_dir, manifest)
    update_external_registry(manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Import TAL-SCQ5K into Coco's JSON problem bank.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--limit-per-split", type=int, default=0, help="Import only the first N rows per split.")
    args = parser.parse_args()

    manifest = import_bank(args.output_dir, limit_per_split=args.limit_per_split)
    print(f"bank_id={manifest['bank_id']}")
    print(f"total={manifest['counts']['total']}")
    print(f"by_split={manifest['counts']['by_split']}")
    print(f"by_language={manifest['counts']['by_language']}")
    print(f"answer_missing={manifest['counts']['answer_missing']}")
    print(f"manifest={args.output_dir / 'manifest.json'}")
    print(f"index={args.output_dir / manifest['indexes']['lightweight']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
