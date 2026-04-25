from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_URL = (
    "https://huggingface.co/datasets/qwedsacf/competition_math/resolve/main/"
    "data/train-00000-of-00001-7320a6f3aba8ebd2.parquet"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "problem_bank" / "sources" / "competition_math"
CATALOG_PATH = PROJECT_ROOT / "data" / "problem_bank" / "catalog.json"


SUBJECT_SLUGS = {
    "Algebra": "algebra",
    "Counting & Probability": "counting_probability",
    "Geometry": "geometry",
    "Intermediate Algebra": "intermediate_algebra",
    "Number Theory": "number_theory",
    "Prealgebra": "prealgebra",
    "Precalculus": "precalculus",
}

SUBJECT_TAGS = {
    "Algebra": ["algebra", "functions", "equations"],
    "Counting & Probability": ["counting", "probability", "combinatorics"],
    "Geometry": ["geometry", "diagram"],
    "Intermediate Algebra": ["intermediate_algebra", "polynomials", "equations"],
    "Number Theory": ["number_theory", "integers", "modular_arithmetic"],
    "Prealgebra": ["prealgebra", "arithmetic", "ratios"],
    "Precalculus": ["precalculus", "trigonometry", "functions"],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    value = SUBJECT_SLUGS.get(value, value)
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "unknown"


def level_number(level: str) -> int:
    match = re.search(r"(\d+)", str(level or ""))
    return int(match.group(1)) if match else 0


def strip_latex_for_search(text: str) -> str:
    plain = str(text or "")
    plain = plain.replace("\\\\", " ")
    plain = re.sub(r"\\(?:left|right|text|mathrm|operatorname)\b", " ", plain)
    plain = re.sub(r"\\[a-zA-Z]+", " ", plain)
    plain = re.sub(r"[{}$\\]", " ", plain)
    plain = re.sub(r"\s+", " ", plain)
    return plain.strip()


def extract_boxed_answers(solution: str) -> list[str]:
    text = str(solution or "")
    answers: list[str] = []
    index = 0
    for marker in ("\\boxed", "\\fbox"):
        index = 0
        while True:
            start = text.find(marker, index)
            if start < 0:
                break
            brace = text.find("{", start)
            if brace < 0:
                index = start + len(marker)
                continue
            depth = 0
            for pos in range(brace, len(text)):
                char = text[pos]
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        answer = text[brace + 1 : pos].strip()
                        if answer and answer not in answers:
                            answers.append(answer)
                        index = pos + 1
                        break
            else:
                index = start + len(marker)
    return answers


def normalize_answer(answer: str) -> str:
    text = str(answer or "").strip()
    text = text.strip("$ ")
    text = re.sub(r"\\(?:left|right)", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def infer_answer_type(answer: str) -> str:
    text = normalize_answer(answer)
    if not text:
        return "unknown"
    if re.fullmatch(r"[+-]?\d+", text):
        return "integer"
    if re.fullmatch(r"[+-]?\d+/\d+", text) or "\\frac" in text:
        return "fraction"
    if re.fullmatch(r"[+-]?(?:\d+\.\d*|\.\d+)", text):
        return "decimal"
    if any(token in text for token in ("x", "y", "\\sqrt", "^", "=")):
        return "expression"
    if "," in text or "\\{" in text:
        return "list_or_set"
    return "text"


def has_asy(*texts: str) -> bool:
    joined = "\n".join(str(text or "") for text in texts)
    return "[asy]" in joined or "\\begin{asy}" in joined or "import graph" in joined


def has_table(text: str) -> bool:
    lowered = str(text or "").lower()
    return "\\begin{array}" in lowered or "\\begin{tabular}" in lowered or "\\begin{matrix}" in lowered


def build_record(row: dict[str, Any], index: int, source_url: str, generated_at: str) -> dict[str, Any]:
    subject = str(row.get("type") or "Unknown")
    subject_slug = slugify(subject)
    level = str(row.get("level") or "Level ?")
    level_num = level_number(level)
    problem = str(row.get("problem") or "")
    solution = str(row.get("solution") or "")
    boxed = extract_boxed_answers(solution)
    final_raw = boxed[-1] if boxed else ""
    final_normalized = normalize_answer(final_raw)
    record_id = f"competition_math:{subject_slug}:level_{level_num}:{index:05d}"
    tags = [subject_slug, f"level_{level_num}", *SUBJECT_TAGS.get(subject, [])]
    tags = sorted(dict.fromkeys(tag for tag in tags if tag))
    review_reasons: list[str] = []
    if not boxed:
        review_reasons.append("missing_boxed_answer")
    if level_num == 0:
        review_reasons.append("unknown_level")

    record = {
        "schema_version": "problem_bank_record.v1",
        "id": record_id,
        "source": {
            "name": "Competition MATH",
            "dataset_id": "qwedsacf/competition_math",
            "source_url": source_url,
            "license": "MIT",
            "original_index": int(index),
            "split": "train",
            "source_problem_id": f"competition_math_{index:05d}",
        },
        "content": {
            "language": "en",
            "problem_latex": problem,
            "problem_plain": strip_latex_for_search(problem),
            "solution_latex": solution,
            "solution_plain": strip_latex_for_search(solution),
        },
        "answer": {
            "final_raw": final_raw,
            "final_normalized": final_normalized,
            "candidates": [normalize_answer(item) for item in boxed],
            "extraction_method": "boxed" if boxed else "none",
            "answer_type": infer_answer_type(final_normalized),
        },
        "taxonomy": {
            "domain": "competition_math",
            "subject": subject,
            "subject_slug": subject_slug,
            "level": level,
            "level_number": level_num,
            "grade_band": "advanced",
            "concepts": [],
            "tags": tags,
        },
        "structure": {
            "format": "latex_text",
            "has_asy": has_asy(problem, solution),
            "has_diagram": has_asy(problem, solution) or "[asy]" in problem,
            "has_table": has_table(problem) or has_table(solution),
            "has_choices": bool(re.search(r"\\text\{?\\?[A-E]\}?|\\([A-E]\\)", problem)),
            "requires_rendering": any(token in problem for token in ("\\frac", "\\sqrt", "\\begin", "[asy]")),
        },
        "learning": {
            "prerequisites": [],
            "step_outline": [],
            "hints": [],
            "common_mistakes": [],
        },
        "search": {
            "problem_text": strip_latex_for_search(problem),
            "solution_text": strip_latex_for_search(solution),
            "keywords": tags,
        },
        "metadata": {
            "created_at": generated_at,
            "updated_at": generated_at,
            "quality": {
                "solution_available": bool(solution),
                "final_answer_extracted": bool(boxed),
                "needs_review": bool(review_reasons),
                "review_reasons": review_reasons,
            },
        },
    }
    return record


def lightweight_index_item(record: dict[str, Any], shard_path: str) -> dict[str, Any]:
    content = record["content"]
    taxonomy = record["taxonomy"]
    answer = record["answer"]
    structure = record["structure"]
    return {
        "id": record["id"],
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
        "needs_review": record["metadata"]["quality"]["needs_review"],
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def import_bank(source_url: str, output_dir: Path, limit: int = 0) -> dict[str, Any]:
    df = pd.read_parquet(source_url)
    if limit > 0:
        df = df.head(limit)

    generated_at = utc_now()
    records = [build_record(row._asdict() if hasattr(row, "_asdict") else dict(row), int(index), source_url, generated_at) for index, row in df.iterrows()]

    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        taxonomy = record["taxonomy"]
        grouped[(taxonomy["subject_slug"], int(taxonomy["level_number"]))].append(record)

    shards: list[dict[str, Any]] = []
    index_items: list[dict[str, Any]] = []
    for (subject_slug, level_num), shard_records in sorted(grouped.items()):
        shard_path = Path("shards") / subject_slug / f"level_{level_num}.json"
        write_json(output_dir / shard_path, shard_records)
        shards.append(
            {
                "path": str(shard_path),
                "count": len(shard_records),
                "subject": shard_records[0]["taxonomy"]["subject"],
                "subject_slug": subject_slug,
                "level": shard_records[0]["taxonomy"]["level"],
                "level_number": level_num,
            }
        )
        index_items.extend(lightweight_index_item(record, str(shard_path)) for record in shard_records)

    index_items = sorted(index_items, key=lambda item: (item["subject_slug"], item["level_number"], item["id"]))
    index_path = Path("index") / "problem_index.json"
    write_json(output_dir / index_path, index_items)

    by_subject = Counter(record["taxonomy"]["subject"] for record in records)
    by_level = Counter(record["taxonomy"]["level"] for record in records)
    answer_missing = sum(1 for record in records if not record["metadata"]["quality"]["final_answer_extracted"])
    asy_count = sum(1 for record in records if record["structure"]["has_asy"])
    manifest = {
        "schema_version": "problem_bank_manifest.v1",
        "bank_id": "competition_math",
        "generated_at": generated_at,
        "source": {
            "name": "Competition MATH",
            "dataset_id": "qwedsacf/competition_math",
            "source_url": source_url,
            "license": "MIT",
            "notes": "Official hendrycks/competition_math Hugging Face page was unavailable during import; this source URL is the active mirror referenced in local feasibility checks.",
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
            "answer_missing": answer_missing,
            "asy": asy_count,
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
    parser = argparse.ArgumentParser(description="Import Competition MATH into Coco's JSON problem bank.")
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--limit", type=int, default=0, help="Import only the first N rows for smoke tests.")
    args = parser.parse_args()

    manifest = import_bank(args.source_url, args.output_dir, limit=args.limit)
    print(f"bank_id={manifest['bank_id']}")
    print(f"total={manifest['counts']['total']}")
    print(f"answer_missing={manifest['counts']['answer_missing']}")
    print(f"asy={manifest['counts']['asy']}")
    print(f"manifest={args.output_dir / 'manifest.json'}")
    print(f"index={args.output_dir / manifest['indexes']['lightweight']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
