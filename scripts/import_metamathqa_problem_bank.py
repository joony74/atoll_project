from __future__ import annotations

import argparse
import json
import re
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_URL = "https://huggingface.co/datasets/meta-math/MetaMathQA/resolve/main/MetaMathQA-395K.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "problem_bank" / "sources" / "metamathqa"
CATALOG_PATH = PROJECT_ROOT / "data" / "problem_bank" / "catalog.json"
EXTERNAL_SOURCES_PATH = PROJECT_ROOT / "data" / "problem_bank" / "external_math_sources.json"


SUBJECT_PATTERNS = [
    ("geometry", "Geometry", "geometry"),
    ("complex plane", "Geometry", "geometry"),
    ("triangle", "Geometry", "geometry"),
    ("circle", "Geometry", "geometry"),
    ("probability", "Counting & Probability", "counting_probability"),
    ("combinatorics", "Counting & Probability", "counting_probability"),
    ("arrangements", "Counting & Probability", "counting_probability"),
    ("modulo", "Number Theory", "number_theory"),
    ("divisible", "Number Theory", "number_theory"),
    ("integer", "Number Theory", "number_theory"),
    ("base", "Number Theory", "number_theory"),
    ("polynomial", "Intermediate Algebra", "intermediate_algebra"),
    ("quadratic", "Intermediate Algebra", "intermediate_algebra"),
    ("function", "Algebra", "algebra"),
    ("equation", "Algebra", "algebra"),
    ("variable", "Algebra", "algebra"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def iter_json_array_url(url: str, *, limit: int = 0, chunk_size: int = 262_144) -> Iterable[dict[str, Any]]:
    decoder = json.JSONDecoder()
    buffer = ""
    started = False
    yielded = 0
    with urllib.request.urlopen(url, timeout=90) as response:
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            buffer += chunk.decode("utf-8")
            while True:
                buffer = buffer.lstrip()
                if not started:
                    if not buffer:
                        break
                    if buffer[0] != "[":
                        raise RuntimeError("MetaMathQA payload must be a JSON array")
                    buffer = buffer[1:]
                    started = True
                    continue
                buffer = buffer.lstrip()
                if buffer.startswith(","):
                    buffer = buffer[1:].lstrip()
                if buffer.startswith("]"):
                    return
                if not buffer:
                    break
                try:
                    item, end = decoder.raw_decode(buffer)
                except json.JSONDecodeError:
                    break
                buffer = buffer[end:]
                if isinstance(item, dict):
                    yielded += 1
                    yield item
                    if limit > 0 and yielded >= limit:
                        return


def strip_latex_for_search(text: str) -> str:
    plain = str(text or "")
    plain = plain.replace("$$", " ").replace("$", " ")
    plain = plain.replace("\\\\", " ")
    plain = re.sub(r"\\(?:left|right|text|mathrm|operatorname)\b", " ", plain)
    plain = re.sub(r"\\[a-zA-Z]+", " ", plain)
    plain = re.sub(r"[{}\\]", " ", plain)
    plain = re.sub(r"\s+", " ", plain)
    return plain.strip()


def normalize_answer(answer: str) -> str:
    text = str(answer or "").strip()
    text = text.strip("$ ")
    text = re.sub(r"\\(?:left|right)", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .")


def extract_boxed_answers(text: str) -> list[str]:
    source = str(text or "")
    answers: list[str] = []
    index = 0
    for marker in ("\\boxed", "\\fbox"):
        index = 0
        while True:
            start = source.find(marker, index)
            if start < 0:
                break
            brace = source.find("{", start)
            if brace < 0:
                index = start + len(marker)
                continue
            depth = 0
            for pos in range(brace, len(source)):
                char = source[pos]
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        answer = normalize_answer(source[brace + 1 : pos])
                        if answer and answer not in answers:
                            answers.append(answer)
                        index = pos + 1
                        break
            else:
                index = start + len(marker)
    return answers


def extract_answer_line(response: str) -> list[str]:
    answers: list[str] = []
    for pattern in (r"####\s*([^\n]+)", r"The answer is:\s*([^\n]+)"):
        for match in re.finditer(pattern, str(response or ""), flags=re.IGNORECASE):
            answer = normalize_answer(match.group(1))
            if answer and answer not in answers:
                answers.append(answer)
    return answers


def extract_final_answer(response: str) -> tuple[str, list[str], str]:
    boxed = extract_boxed_answers(response)
    answer_lines = extract_answer_line(response)
    candidates = [*boxed, *answer_lines]
    deduped = list(dict.fromkeys(normalize_answer(item) for item in candidates if normalize_answer(item)))
    if answer_lines:
        return answer_lines[-1], deduped, "answer_line"
    if boxed:
        return boxed[-1], deduped, "boxed"
    return "", deduped, "none"


def infer_answer_type(answer: str) -> str:
    text = normalize_answer(answer)
    cleaned = text.replace(",", "")
    if not text:
        return "unknown"
    if re.fullmatch(r"[+-]?\d+", cleaned):
        return "integer"
    if re.fullmatch(r"[+-]?(?:\d+\.\d*|\.\d+)", cleaned):
        return "decimal"
    if re.fullmatch(r"[+-]?\d+/\d+", cleaned) or "\\frac" in text:
        return "fraction"
    if any(token in text for token in ("x", "y", "\\sqrt", "^", "=")):
        return "expression"
    return "text"


def slugify(value: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "unknown"


def infer_subject(row_type: str, query: str, response: str) -> tuple[str, str, str]:
    type_text = str(row_type or "")
    haystack = f"{query}\n{response}".lower()
    if type_text.startswith("GSM"):
        return "Grade School Math", "arithmetic_word_problem", "grade_school_math"
    for needle, subject, slug in SUBJECT_PATTERNS:
        if needle in haystack:
            return subject, slug, "metamathqa"
    if type_text.startswith("MATH"):
        return "Competition Math", "competition_math", "competition_math"
    return "MetaMathQA", "metamathqa", "metamathqa"


def infer_level(row_type: str, subject_slug: str, query: str, response: str) -> int:
    text = f"{query}\n{response}".lower()
    if str(row_type or "").startswith("GSM"):
        base = 2
    elif subject_slug in {"geometry", "number_theory", "counting_probability", "competition_math"}:
        base = 4
    else:
        base = 3
    complexity = len(re.findall(r"\\frac|\\sqrt|\^|log|sin|cos|tan|modulo|polynomial|quadratic", text))
    if complexity >= 5:
        base += 1
    return max(1, min(base, 5))


def split_solution_steps(response: str) -> list[str]:
    cleaned = re.sub(r"\n?####\s*[^\n]+", "", str(response or "")).strip()
    cleaned = re.sub(r"The answer is:\s*[^\n]+", "", cleaned, flags=re.IGNORECASE).strip()
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", cleaned) if part.strip()]
    return parts[:10]


def build_record(row: dict[str, Any], *, index: int, source_url: str, generated_at: str) -> dict[str, Any]:
    query = str(row.get("query") or "").strip()
    response = str(row.get("response") or "").strip()
    row_type = str(row.get("type") or "unknown").strip()
    original_question = str(row.get("original_question") or "").strip()
    final_raw, candidates, extraction_method = extract_final_answer(response)
    final_normalized = normalize_answer(final_raw)
    subject, subject_slug, domain = infer_subject(row_type, query, response)
    level_num = infer_level(row_type, subject_slug, query, response)
    tags = sorted(
        dict.fromkeys(
            [
                "metamathqa",
                slugify(row_type),
                subject_slug,
                domain,
                f"level_{level_num}",
                "cot_reasoning",
            ]
        )
    )
    review_reasons: list[str] = []
    if not query:
        review_reasons.append("missing_query")
    if not response:
        review_reasons.append("missing_response")
    if not final_normalized:
        review_reasons.append("missing_final_answer")

    record_id = f"metamathqa:{slugify(row_type)}:{subject_slug}:level_{level_num}:{index:05d}"
    return {
        "schema_version": "problem_bank_record.v1",
        "id": record_id,
        "source": {
            "name": "MetaMathQA",
            "dataset_id": "meta-math/MetaMathQA",
            "source_url": source_url,
            "license": "MIT",
            "original_index": int(index),
            "split": "sample",
            "source_problem_id": f"metamathqa_{index:05d}",
        },
        "content": {
            "language": "en",
            "problem_latex": query,
            "problem_plain": strip_latex_for_search(query),
            "solution_latex": response,
            "solution_plain": strip_latex_for_search(response),
        },
        "answer": {
            "final_raw": final_raw,
            "final_normalized": final_normalized,
            "candidates": candidates,
            "extraction_method": extraction_method,
            "answer_type": infer_answer_type(final_normalized),
        },
        "taxonomy": {
            "domain": domain,
            "subject": subject,
            "subject_slug": subject_slug,
            "level": f"Level {level_num}",
            "level_number": level_num,
            "grade_band": "middle_high" if level_num <= 3 else "high",
            "concepts": [subject_slug, slugify(row_type)],
            "tags": tags,
        },
        "structure": {
            "format": "instruction_cot_text",
            "has_asy": False,
            "has_diagram": False,
            "has_table": "\\begin{array}" in query or "\\begin{tabular}" in query,
            "has_choices": bool(re.search(r"\([A-E]\)", query)),
            "requires_rendering": any(token in query for token in ("\\frac", "\\sqrt", "\\begin", "$")),
        },
        "learning": {
            "prerequisites": [],
            "step_outline": split_solution_steps(response),
            "hints": [],
            "common_mistakes": [],
        },
        "search": {
            "problem_text": strip_latex_for_search(query),
            "solution_text": strip_latex_for_search(response),
            "keywords": tags,
        },
        "metadata": {
            "created_at": generated_at,
            "updated_at": generated_at,
            "quality": {
                "solution_available": bool(response),
                "final_answer_extracted": bool(final_normalized),
                "needs_review": bool(review_reasons),
                "review_reasons": review_reasons,
            },
            "metamathqa": {
                "type": row_type,
                "original_question": original_question,
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
        "bank_id": "metamathqa",
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
            "import_status": "sample_imported",
        }
    )
    catalog = {
        "schema_version": "problem_bank_catalog.v1",
        "updated_at": utc_now(),
        "banks": sorted(banks, key=lambda item: item["bank_id"]),
    }
    write_json(CATALOG_PATH, catalog)


def update_external_registry(manifest: dict[str, Any], *, sample_limit: int) -> None:
    if not EXTERNAL_SOURCES_PATH.exists():
        return
    try:
        registry = json.loads(EXTERNAL_SOURCES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return
    for source in registry.get("sources") or []:
        if not isinstance(source, dict) or source.get("bank_id") != manifest["bank_id"]:
            continue
        source["license"] = "MIT"
        source["import_status"] = "sample_imported"
        source["import_mode"] = "streaming_json_array_adapter"
        source["imported_total"] = manifest["counts"]["total"]
        source["sample_limit"] = sample_limit
        source["imported_at"] = manifest["generated_at"]
    registry["updated_at"] = utc_now()
    write_json(EXTERNAL_SOURCES_PATH, registry)


def import_bank(source_url: str, output_dir: Path, limit: int) -> dict[str, Any]:
    generated_at = utc_now()
    records = [
        build_record(row, index=index, source_url=source_url, generated_at=generated_at)
        for index, row in enumerate(iter_json_array_url(source_url, limit=limit))
    ]

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
                "split": "sample",
            }
        )
        index_items.extend(lightweight_index_item(record, str(shard_path)) for record in shard_records)

    index_items = sorted(index_items, key=lambda item: item["id"])
    index_path = Path("index") / "problem_index.json"
    write_json(output_dir / index_path, index_items)

    by_subject = Counter(record["taxonomy"]["subject"] for record in records)
    by_level = Counter(record["taxonomy"]["level"] for record in records)
    by_type = Counter(record["metadata"]["metamathqa"]["type"] for record in records)
    answer_missing = sum(1 for record in records if not record["metadata"]["quality"]["final_answer_extracted"])
    manifest = {
        "schema_version": "problem_bank_manifest.v1",
        "bank_id": "metamathqa",
        "generated_at": generated_at,
        "source": {
            "name": "MetaMathQA",
            "dataset_id": "meta-math/MetaMathQA",
            "source_url": "https://github.com/meta-math/MetaMath",
            "dataset_url": "https://huggingface.co/datasets/meta-math/MetaMathQA",
            "license": "MIT",
            "raw_sources": {
                "metamathqa_395k": source_url,
            },
            "notes": "Streaming sample import from the public 395K JSON array. Increase --limit to expand local training coverage without loading the full file into memory.",
        },
        "storage": {
            "format": "json_shards",
            "encoding": "utf-8",
            "record_schema": "../../schema/problem_bank_record.schema.json",
        },
        "counts": {
            "total": len(records),
            "sample_limit": limit,
            "by_subject": dict(sorted(by_subject.items())),
            "by_level": dict(sorted(by_level.items())),
            "by_type": dict(sorted(by_type.items())),
            "answer_missing": answer_missing,
        },
        "shards": shards,
        "indexes": {
            "lightweight": str(index_path),
        },
    }
    write_json(output_dir / "manifest.json", manifest)
    update_catalog(output_dir, manifest)
    update_external_registry(manifest, sample_limit=limit)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Stream-import a MetaMathQA sample into Coco's JSON problem bank.")
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--limit", type=int, default=10_000, help="Number of examples to stream from the 395K JSON file.")
    args = parser.parse_args()

    manifest = import_bank(args.source_url, args.output_dir, limit=args.limit)
    print(f"bank_id={manifest['bank_id']}")
    print(f"total={manifest['counts']['total']}")
    print(f"by_subject={manifest['counts']['by_subject']}")
    print(f"by_type={manifest['counts']['by_type']}")
    print(f"answer_missing={manifest['counts']['answer_missing']}")
    print(f"manifest={args.output_dir / 'manifest.json'}")
    print(f"index={args.output_dir / manifest['indexes']['lightweight']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
