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
DATASET_ROOT = "https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data"
DEFAULT_SPLIT_URLS = {
    "train": f"{DATASET_ROOT}/train.jsonl",
    "test": f"{DATASET_ROOT}/test.jsonl",
}
SOCRATIC_SPLIT_URLS = {
    "train_socratic": f"{DATASET_ROOT}/train_socratic.jsonl",
    "test_socratic": f"{DATASET_ROOT}/test_socratic.jsonl",
}
EXAMPLE_MODEL_SOLUTIONS_URL = f"{DATASET_ROOT}/example_model_solutions.jsonl"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "problem_bank" / "sources" / "gsm8k"
CATALOG_PATH = PROJECT_ROOT / "data" / "problem_bank" / "catalog.json"


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


def remove_calculation_annotations(text: str) -> str:
    cleaned = re.sub(r"<<[^<>]*>>", "", str(text or ""))
    cleaned = re.sub(r"\s+\n", "\n", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned.strip()


def extract_final_answer(answer: str) -> str:
    match = re.search(r"####\s*([^\n]+)\s*$", str(answer or ""))
    return match.group(1).strip() if match else ""


def normalize_answer(answer: str) -> str:
    text = str(answer or "").strip()
    text = text.strip("$ ")
    text = text.replace(",", "")
    text = re.sub(r"\s+", " ", text)
    return text


def infer_answer_type(answer: str) -> str:
    text = normalize_answer(answer)
    if not text:
        return "unknown"
    if re.fullmatch(r"[+-]?\d+", text):
        return "integer"
    if re.fullmatch(r"[+-]?(?:\d+\.\d*|\.\d+)", text):
        return "decimal"
    if re.fullmatch(r"[+-]?\d+/\d+", text):
        return "fraction"
    if re.search(r"\d", text):
        return "numeric_text"
    return "text"


def extract_calculation_results(answer: str) -> list[str]:
    results: list[str] = []
    for match in re.finditer(r"<<([^<>]*)>>", str(answer or "")):
        annotation = match.group(1)
        if "=" not in annotation:
            continue
        result = annotation.rsplit("=", 1)[-1].strip()
        result = normalize_answer(result)
        if result and result not in results:
            results.append(result)
    return results


def solution_steps(answer: str) -> list[str]:
    plain = remove_calculation_annotations(answer)
    plain = re.sub(r"\n?####\s*[^\n]+\s*$", "", plain).strip()
    return [line.strip() for line in plain.splitlines() if line.strip()]


def infer_tags(question: str, answer: str) -> list[str]:
    text = f"{question}\n{answer}".lower()
    tags = ["gsm8k", "arithmetic", "word_problem"]
    patterns = {
        "addition": r"\+| add | total | altogether | sum",
        "subtraction": r"-| less | left | remaining | difference",
        "multiplication": r"\*| x | times | twice | triple | each",
        "division": r"/| divided | half | per | average",
        "fraction": r"\b\d+/\d+\b| half | third | quarter",
        "percent": r"%| percent",
        "decimal": r"\b\d+\.\d+\b",
        "money": r"\$|dollar|cost|price|earn|paid|spend|budget",
        "rate": r"per | an hour|mph|minute|day|week|month|year",
        "ratio": r"\bratio\b| for every ",
        "algebra_equation": r"\blet [a-z]\b|equating|variable",
        "unit_conversion": r"\bml\b|\bliter\b|\bhour\b|\bminute\b|\bmile\b|\bpound\b",
    }
    for tag, pattern in patterns.items():
        if re.search(pattern, text):
            tags.append(tag)
    return sorted(dict.fromkeys(tags))


def infer_level(step_count: int, tags: list[str]) -> int:
    complexity = step_count
    for tag in ("fraction", "percent", "decimal", "ratio", "rate", "unit_conversion", "algebra_equation"):
        if tag in tags:
            complexity += 1
    if complexity <= 2:
        return 1
    if complexity <= 4:
        return 2
    if complexity <= 6:
        return 3
    if complexity <= 8:
        return 4
    return 5


def grade_band_for_level(level_number: int) -> str:
    if level_number <= 2:
        return "elementary"
    if level_number <= 4:
        return "elementary_middle"
    return "middle"


def build_record(row: dict[str, Any], *, split: str, index: int, source_url: str, generated_at: str) -> dict[str, Any]:
    question = str(row.get("question") or "").strip()
    answer = str(row.get("answer") or "").strip()
    final_raw = extract_final_answer(answer)
    final_normalized = normalize_answer(final_raw)
    steps = solution_steps(answer)
    tags = infer_tags(question, answer)
    level_num = infer_level(len(steps), tags)
    review_reasons: list[str] = []
    if not question:
        review_reasons.append("missing_question")
    if not answer:
        review_reasons.append("missing_solution")
    if not final_raw:
        review_reasons.append("missing_final_answer_marker")

    candidates = extract_calculation_results(answer)
    if final_normalized and final_normalized not in candidates:
        candidates.append(final_normalized)

    record_id = f"gsm8k:{split}:level_{level_num}:{index:05d}"
    solution_plain = remove_calculation_annotations(answer)
    return {
        "schema_version": "problem_bank_record.v1",
        "id": record_id,
        "source": {
            "name": "GSM8K",
            "dataset_id": "openai/grade-school-math",
            "source_url": source_url,
            "license": "MIT",
            "original_index": int(index),
            "split": split,
            "source_problem_id": f"gsm8k_{split}_{index:05d}",
        },
        "content": {
            "language": "en",
            "problem_latex": question,
            "problem_plain": question,
            "solution_latex": answer,
            "solution_plain": solution_plain,
        },
        "answer": {
            "final_raw": final_raw,
            "final_normalized": final_normalized,
            "candidates": candidates,
            "extraction_method": "gsm8k_final_marker" if final_raw else "none",
            "answer_type": infer_answer_type(final_normalized),
        },
        "taxonomy": {
            "domain": "grade_school_math",
            "subject": "Arithmetic Word Problems",
            "subject_slug": "arithmetic_word_problem",
            "level": f"Level {level_num}",
            "level_number": level_num,
            "grade_band": grade_band_for_level(level_num),
            "concepts": [tag for tag in tags if tag not in {"gsm8k", "word_problem"}],
            "tags": [*tags, split, f"level_{level_num}"],
        },
        "structure": {
            "format": "plain_text_word_problem",
            "has_asy": False,
            "has_diagram": False,
            "has_table": False,
            "has_choices": False,
            "requires_rendering": False,
        },
        "learning": {
            "prerequisites": ["basic_arithmetic"],
            "step_outline": steps,
            "hints": [],
            "common_mistakes": [],
        },
        "search": {
            "problem_text": question,
            "solution_text": solution_plain,
            "keywords": [*tags, split, grade_band_for_level(level_num)],
        },
        "metadata": {
            "created_at": generated_at,
            "updated_at": generated_at,
            "quality": {
                "solution_available": bool(answer),
                "final_answer_extracted": bool(final_raw),
                "needs_review": bool(review_reasons),
                "review_reasons": review_reasons,
            },
            "gsm8k": {
                "calculation_annotation_count": len(extract_calculation_results(answer)),
                "socratic_variant_available": True,
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
        "bank_id": "gsm8k",
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

    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        taxonomy = record["taxonomy"]
        grouped[(record["source"]["split"], int(taxonomy["level_number"]))].append(record)

    shards: list[dict[str, Any]] = []
    index_items: list[dict[str, Any]] = []
    for (split, level_num), shard_records in sorted(grouped.items()):
        shard_path = Path("shards") / split / f"level_{level_num}.json"
        write_json(output_dir / shard_path, shard_records)
        shards.append(
            {
                "path": str(shard_path),
                "count": len(shard_records),
                "subject": shard_records[0]["taxonomy"]["subject"],
                "subject_slug": shard_records[0]["taxonomy"]["subject_slug"],
                "level": shard_records[0]["taxonomy"]["level"],
                "level_number": level_num,
                "split": split,
            }
        )
        index_items.extend(lightweight_index_item(record, str(shard_path)) for record in shard_records)

    index_items = sorted(index_items, key=lambda item: (item["id"]))
    index_path = Path("index") / "problem_index.json"
    write_json(output_dir / index_path, index_items)

    by_subject = Counter(record["taxonomy"]["subject"] for record in records)
    by_level = Counter(record["taxonomy"]["level"] for record in records)
    by_grade_band = Counter(record["taxonomy"]["grade_band"] for record in records)
    answer_missing = sum(1 for record in records if not record["metadata"]["quality"]["final_answer_extracted"])
    calc_annotated = sum(1 for record in records if record["metadata"]["gsm8k"]["calculation_annotation_count"] > 0)
    manifest = {
        "schema_version": "problem_bank_manifest.v1",
        "bank_id": "gsm8k",
        "generated_at": generated_at,
        "source": {
            "name": "GSM8K",
            "dataset_id": "openai/grade-school-math",
            "source_url": "https://github.com/openai/grade-school-math",
            "license": "MIT",
            "raw_sources": {
                **DEFAULT_SPLIT_URLS,
                **SOCRATIC_SPLIT_URLS,
                "example_model_solutions": EXAMPLE_MODEL_SOLUTIONS_URL,
            },
            "notes": "Imported train/test only as canonical problem records. Socratic files are duplicate prompts with generated subquestions and are tracked as available variants, not imported as separate records.",
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
            "by_split": split_counts,
            "by_grade_band": dict(sorted(by_grade_band.items())),
            "answer_missing": answer_missing,
            "calculation_annotated": calc_annotated,
        },
        "shards": shards,
        "indexes": {
            "lightweight": str(index_path),
        },
    }
    write_json(output_dir / "manifest.json", manifest)
    update_catalog(output_dir, manifest)
    return manifest


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
        }
    )
    catalog = {
        "schema_version": "problem_bank_catalog.v1",
        "updated_at": utc_now(),
        "banks": sorted(banks, key=lambda item: item["bank_id"]),
    }
    write_json(CATALOG_PATH, catalog)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import GSM8K into Coco's JSON problem bank.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--limit-per-split", type=int, default=0, help="Import only the first N rows per split.")
    args = parser.parse_args()

    manifest = import_bank(args.output_dir, limit_per_split=args.limit_per_split)
    print(f"bank_id={manifest['bank_id']}")
    print(f"total={manifest['counts']['total']}")
    print(f"by_split={manifest['counts']['by_split']}")
    print(f"answer_missing={manifest['counts']['answer_missing']}")
    print(f"calculation_annotated={manifest['counts']['calculation_annotated']}")
    print(f"manifest={args.output_dir / 'manifest.json'}")
    print(f"index={args.output_dir / manifest['indexes']['lightweight']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
