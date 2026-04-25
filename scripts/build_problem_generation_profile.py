from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = PROJECT_ROOT / "data" / "problem_bank" / "catalog.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_problem_generation_profile.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(path_text: str) -> Path:
    path = Path(str(path_text or ""))
    return path if path.is_absolute() else PROJECT_ROOT / path


def iter_problem_bank_records() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    catalog = read_json(CATALOG_PATH)
    source_banks: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    for bank in catalog.get("banks") or []:
        if not isinstance(bank, dict):
            continue
        bank_id = str(bank.get("bank_id") or "").strip()
        manifest_path = resolve_path(str(bank.get("manifest_path") or ""))
        manifest = read_json(manifest_path)
        bank_root = manifest_path.parent
        source_banks.append(
            {
                "bank_id": bank_id,
                "name": str(bank.get("name") or manifest.get("source", {}).get("name") or bank_id),
                "total": int((manifest.get("counts") or {}).get("total") or bank.get("total") or 0),
                "license": str((manifest.get("source") or {}).get("license") or ""),
            }
        )
        for shard in manifest.get("shards") or []:
            shard_path = bank_root / str((shard or {}).get("path") or "")
            for record in read_json(shard_path):
                if isinstance(record, dict):
                    enriched = dict(record)
                    enriched["_bank_id"] = bank_id
                    records.append(enriched)
    return source_banks, records


def _step_count(record: dict[str, Any]) -> int:
    outline = ((record.get("learning") or {}).get("step_outline") or [])
    return len([step for step in outline if str(step or "").strip()])


def _top(counter: Counter[str], limit: int = 24) -> dict[str, int]:
    return {key: count for key, count in counter.most_common(limit)}


def build_profile() -> dict[str, Any]:
    source_banks, records = iter_problem_bank_records()
    domain_stats: dict[str, dict[str, Any]] = {}
    level_stats: dict[tuple[str, int], dict[str, Any]] = {}
    bank_counts = Counter(record.get("_bank_id") or "unknown" for record in records)

    for record in records:
        taxonomy = record.get("taxonomy") or {}
        answer = record.get("answer") or {}
        metadata = record.get("metadata") or {}
        quality = metadata.get("quality") or {}
        subject_slug = str(taxonomy.get("subject_slug") or taxonomy.get("subject") or "unknown").strip()
        subject = str(taxonomy.get("subject") or subject_slug).strip()
        try:
            level_number = int(taxonomy.get("level_number") or 0)
        except Exception:
            level_number = 0
        grade_band = str(taxonomy.get("grade_band") or "unknown").strip()
        tags = [str(tag or "").strip() for tag in (taxonomy.get("tags") or []) if str(tag or "").strip()]
        concepts = [str(tag or "").strip() for tag in (taxonomy.get("concepts") or []) if str(tag or "").strip()]
        search_keywords = [
            str(tag or "").strip()
            for tag in ((record.get("search") or {}).get("keywords") or [])
            if str(tag or "").strip()
        ]
        all_tags = sorted(dict.fromkeys([*tags, *concepts, *search_keywords]))

        domain = domain_stats.setdefault(
            subject_slug,
            {
                "subject": subject,
                "subject_slug": subject_slug,
                "count": 0,
                "levels": {},
                "tag_counts": Counter(),
                "concept_counts": Counter(),
                "answer_type_counts": Counter(),
                "grade_band_counts": Counter(),
                "source_bank_counts": Counter(),
            },
        )
        domain["count"] += 1
        domain["tag_counts"].update(all_tags)
        domain["concept_counts"].update(concepts)
        domain["answer_type_counts"].update([str(answer.get("answer_type") or "unknown")])
        domain["grade_band_counts"].update([grade_band])
        domain["source_bank_counts"].update([str(record.get("_bank_id") or "unknown")])

        key = (subject_slug, level_number)
        level = level_stats.setdefault(
            key,
            {
                "count": 0,
                "tag_counts": Counter(),
                "concept_counts": Counter(),
                "answer_type_counts": Counter(),
                "step_count_histogram": Counter(),
                "quality_review_count": 0,
            },
        )
        level["count"] += 1
        level["tag_counts"].update(all_tags)
        level["concept_counts"].update(concepts)
        level["answer_type_counts"].update([str(answer.get("answer_type") or "unknown")])
        level["step_count_histogram"].update([str(_step_count(record))])
        if bool(quality.get("needs_review")):
            level["quality_review_count"] += 1

    for (subject_slug, level_number), level in level_stats.items():
        domain = domain_stats[subject_slug]
        domain["levels"][str(level_number)] = {
            "count": level["count"],
            "top_tags": _top(level["tag_counts"], 18),
            "top_concepts": _top(level["concept_counts"], 18),
            "answer_type_counts": dict(sorted(level["answer_type_counts"].items())),
            "step_count_histogram": dict(sorted(level["step_count_histogram"].items(), key=lambda item: int(item[0]))),
            "quality_review_count": level["quality_review_count"],
        }

    serializable_domains: dict[str, Any] = {}
    for subject_slug, domain in sorted(domain_stats.items()):
        serializable_domains[subject_slug] = {
            "subject": domain["subject"],
            "subject_slug": subject_slug,
            "count": domain["count"],
            "levels": dict(sorted(domain["levels"].items(), key=lambda item: int(item[0]))),
            "top_tags": _top(domain["tag_counts"], 24),
            "top_concepts": _top(domain["concept_counts"], 24),
            "answer_type_counts": dict(sorted(domain["answer_type_counts"].items())),
            "grade_band_counts": dict(sorted(domain["grade_band_counts"].items())),
            "source_bank_counts": dict(sorted(domain["source_bank_counts"].items())),
        }

    return {
        "schema_version": "coco_problem_generation_profile.v1",
        "generated_at": utc_now(),
        "source_banks": source_banks,
        "counts": {
            "total_records": len(records),
            "by_bank": dict(sorted(bank_counts.items())),
            "by_domain": {key: value["count"] for key, value in serializable_domains.items()},
        },
        "domains": serializable_domains,
        "generation": {
            "default_subject_slug": "arithmetic_word_problem",
            "default_level_number": 2,
            "strategy": "weighted_template_generation_from_normalized_problem_bank_profile",
            "notes": (
                "This profile stores normalized distributions and concept weights learned from the JSON problem bank. "
                "Generated problems are new parameterized problems, not copied dataset records."
            ),
        },
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Coco's normalized problem generation profile.")
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    profile = build_profile()
    write_json(args.output_path, profile)
    print(f"profile={args.output_path}")
    print(f"total_records={profile['counts']['total_records']}")
    print(f"domains={len(profile['domains'])}")
    print(f"default={profile['generation']['default_subject_slug']} level {profile['generation']['default_level_number']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
