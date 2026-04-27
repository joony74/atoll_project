from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import six

if "object" not in np.__dict__:
    setattr(np, "object", object)

from mathematics_dataset import generate_settings
from mathematics_dataset.modules import modules


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "problem_bank" / "sources" / "deepmind_mathematics"
CATALOG_PATH = PROJECT_ROOT / "data" / "problem_bank" / "catalog.json"
EXTERNAL_SOURCES_PATH = PROJECT_ROOT / "data" / "problem_bank" / "external_math_sources.json"


SUBJECT_MAP = {
    "algebra": ("Algebra", "algebra", "algebra"),
    "arithmetic": ("Arithmetic", "arithmetic", "arithmetic"),
    "calculus": ("Calculus", "calculus", "calculus"),
    "comparison": ("Comparison", "comparison", "comparison"),
    "measurement": ("Measurement", "measurement", "measurement"),
    "numbers": ("Numbers", "numbers", "numbers"),
    "polynomials": ("Polynomials", "polynomials", "polynomials"),
    "probability": ("Probability", "probability", "probability"),
}

REGIME_LEVELS = {
    "train_easy": 1,
    "train_medium": 2,
    "train_hard": 3,
    "interpolate": 4,
    "extrapolate": 5,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "unknown"


def _make_entropy_fn(level: int, num_levels: int):
    lower = level / num_levels
    upper = (level + 1) / num_levels

    def modify_entropy(range_: tuple[float, float]) -> tuple[float, float]:
        length = range_[1] - range_[0]
        return (range_[0] + lower * length, range_[0] + upper * length)

    return modify_entropy


def flatten_modules(modules_: dict[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {}

    def add(submodules: dict[str, Any], prefix: str = "") -> None:
        for key, module_or_function in six.iteritems(submodules):
            full_name = f"{prefix}__{key}" if prefix else key
            if isinstance(module_or_function, dict):
                add(module_or_function, full_name)
            else:
                flat[full_name] = module_or_function

    add(modules_)
    return dict(sorted(flat.items()))


def module_collections() -> dict[str, dict[str, Any]]:
    return {
        "train_easy": flatten_modules(modules.train(_make_entropy_fn(0, 3))),
        "train_medium": flatten_modules(modules.train(_make_entropy_fn(1, 3))),
        "train_hard": flatten_modules(modules.train(_make_entropy_fn(2, 3))),
        "interpolate": flatten_modules(modules.test()),
        "extrapolate": flatten_modules(modules.test_extra()),
    }


def normalize_answer(answer: str) -> str:
    text = str(answer or "").strip()
    text = text.strip("$ ")
    text = re.sub(r"\s+", " ", text)
    return text


def strip_for_search(text: str) -> str:
    plain = str(text or "")
    plain = plain.replace("**", "^")
    plain = re.sub(r"\s+", " ", plain)
    return plain.strip()


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
    if text in {"True", "False"}:
        return "boolean"
    if any(token in text for token in ("x", "y", "^", "=", "**", "sqrt", "(")):
        return "expression"
    return "text"


def subject_for_module(module_name: str) -> tuple[str, str, str]:
    domain = str(module_name or "").split("__", 1)[0]
    return SUBJECT_MAP.get(domain, (domain.title(), slugify(domain), slugify(domain)))


def sample_problem(module: Any, *, max_attempts: int = 40) -> tuple[str, str] | None:
    for _ in range(max_attempts):
        problem = module()
        question = str(problem.question).strip()
        answer = str(problem.answer).strip()
        if not question or not answer:
            continue
        if len(question) > generate_settings.MAX_QUESTION_LENGTH:
            continue
        if len(answer) > generate_settings.MAX_ANSWER_LENGTH:
            continue
        return question, answer
    return None


def build_record(
    *,
    question: str,
    answer: str,
    regime: str,
    module_name: str,
    index: int,
    generated_at: str,
) -> dict[str, Any]:
    subject, subject_slug, domain = subject_for_module(module_name)
    level_num = REGIME_LEVELS.get(regime, 3)
    module_slug = slugify(module_name)
    final_normalized = normalize_answer(answer)
    review_reasons: list[str] = []
    if not question:
        review_reasons.append("missing_question")
    if not final_normalized:
        review_reasons.append("missing_answer")

    record_id = f"deepmind_mathematics:{regime}:{module_slug}:{index:05d}"
    tags = sorted(dict.fromkeys(["deepmind_mathematics", regime, domain, subject_slug, module_slug, f"level_{level_num}"]))
    return {
        "schema_version": "problem_bank_record.v1",
        "id": record_id,
        "source": {
            "name": "DeepMind Mathematics Dataset",
            "dataset_id": "google-deepmind/mathematics_dataset",
            "source_url": "https://github.com/google-deepmind/mathematics_dataset",
            "license": "Apache-2.0",
            "original_index": int(index),
            "split": regime,
            "source_problem_id": f"{regime}_{module_slug}_{index:05d}",
        },
        "content": {
            "language": "en",
            "problem_latex": question,
            "problem_plain": strip_for_search(question),
            "solution_latex": answer,
            "solution_plain": strip_for_search(answer),
        },
        "answer": {
            "final_raw": answer,
            "final_normalized": final_normalized,
            "candidates": [final_normalized],
            "extraction_method": "generator_answer",
            "answer_type": infer_answer_type(final_normalized),
        },
        "taxonomy": {
            "domain": domain,
            "subject": subject,
            "subject_slug": subject_slug,
            "level": f"Level {level_num}",
            "level_number": level_num,
            "grade_band": "elementary_middle" if level_num <= 2 else "middle_high",
            "concepts": [module_slug],
            "tags": tags,
        },
        "structure": {
            "format": "generated_question_answer_text",
            "has_asy": False,
            "has_diagram": False,
            "has_table": False,
            "has_choices": False,
            "requires_rendering": any(token in question for token in ("**", "^", "/", "sqrt")),
        },
        "learning": {
            "prerequisites": [],
            "step_outline": [],
            "hints": [],
            "common_mistakes": [],
        },
        "search": {
            "problem_text": strip_for_search(question),
            "solution_text": strip_for_search(answer),
            "keywords": tags,
        },
        "metadata": {
            "created_at": generated_at,
            "updated_at": generated_at,
            "quality": {
                "solution_available": bool(answer),
                "final_answer_extracted": bool(final_normalized),
                "needs_review": bool(review_reasons),
                "review_reasons": review_reasons,
            },
            "deepmind_mathematics": {
                "regime": regime,
                "module_name": module_name,
                "generator_version": "mathematics_dataset==1.0.1",
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
        "bank_id": "deepmind_mathematics",
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


def update_external_registry(manifest: dict[str, Any], *, per_module: int) -> None:
    if not EXTERNAL_SOURCES_PATH.exists():
        return
    try:
        registry = json.loads(EXTERNAL_SOURCES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return
    for source in registry.get("sources") or []:
        if not isinstance(source, dict) or source.get("bank_id") != manifest["bank_id"]:
            continue
        source["import_status"] = "sample_imported"
        source["import_mode"] = "generator_adapter"
        source["imported_total"] = manifest["counts"]["total"]
        source["per_module_sample"] = per_module
        source["imported_at"] = manifest["generated_at"]
    registry["updated_at"] = utc_now()
    write_json(EXTERNAL_SOURCES_PATH, registry)


def import_bank(output_dir: Path, per_module: int, seed: int = 42) -> dict[str, Any]:
    random.seed(seed)
    np.random.seed(seed)
    generated_at = utc_now()
    records: list[dict[str, Any]] = []
    dropped = 0
    global_index = 0

    for regime, flat_modules in module_collections().items():
        for module_name, module in flat_modules.items():
            for _ in range(per_module):
                try:
                    sampled = sample_problem(module)
                except Exception:
                    sampled = None
                if sampled is None:
                    dropped += 1
                    continue
                question, answer = sampled
                records.append(
                    build_record(
                        question=question,
                        answer=answer,
                        regime=regime,
                        module_name=module_name,
                        index=global_index,
                        generated_at=generated_at,
                    )
                )
                global_index += 1

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

    index_path = Path("index") / "problem_index.json"
    write_json(output_dir / index_path, sorted(index_items, key=lambda item: item["id"]))

    by_subject = Counter(record["taxonomy"]["subject"] for record in records)
    by_level = Counter(record["taxonomy"]["level"] for record in records)
    by_regime = Counter(record["source"]["split"] for record in records)
    answer_missing = sum(1 for record in records if not record["metadata"]["quality"]["final_answer_extracted"])
    manifest = {
        "schema_version": "problem_bank_manifest.v1",
        "bank_id": "deepmind_mathematics",
        "generated_at": generated_at,
        "source": {
            "name": "DeepMind Mathematics Dataset",
            "dataset_id": "google-deepmind/mathematics_dataset",
            "source_url": "https://github.com/google-deepmind/mathematics_dataset",
            "license": "Apache-2.0",
            "raw_sources": {
                "python_package": "mathematics_dataset==1.0.1",
            },
            "notes": "Generated a bounded local sample through the official generator package. Increase --per-module to expand synthetic coverage without storing the full generated corpus.",
        },
        "storage": {
            "format": "json_shards",
            "encoding": "utf-8",
            "record_schema": "../../schema/problem_bank_record.schema.json",
        },
        "counts": {
            "total": len(records),
            "per_module": per_module,
            "by_subject": dict(sorted(by_subject.items())),
            "by_level": dict(sorted(by_level.items())),
            "by_regime": dict(sorted(by_regime.items())),
            "answer_missing": answer_missing,
            "dropped": dropped,
        },
        "shards": shards,
        "indexes": {
            "lightweight": str(index_path),
        },
    }
    write_json(output_dir / "manifest.json", manifest)
    update_catalog(output_dir, manifest)
    update_external_registry(manifest, per_module=per_module)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a DeepMind Mathematics Dataset sample for Coco's problem bank.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--per-module", type=int, default=6, help="Number of generated examples per module/regime.")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    manifest = import_bank(args.output_dir, per_module=max(1, args.per_module), seed=args.seed)
    print(f"bank_id={manifest['bank_id']}")
    print(f"total={manifest['counts']['total']}")
    print(f"by_subject={manifest['counts']['by_subject']}")
    print(f"by_regime={manifest['counts']['by_regime']}")
    print(f"dropped={manifest['counts']['dropped']}")
    print(f"manifest={args.output_dir / 'manifest.json'}")
    print(f"index={args.output_dir / manifest['indexes']['lightweight']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
