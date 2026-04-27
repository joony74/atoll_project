from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = PROJECT_ROOT / "data" / "problem_bank" / "external_math_sources.json"
CATALOG_PATH = PROJECT_ROOT / "data" / "problem_bank" / "catalog.json"
SOURCES_ROOT = PROJECT_ROOT / "data" / "problem_bank" / "sources"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path, fallback: Any | None = None) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _manifest_for_source(source: dict[str, Any]) -> dict[str, Any]:
    bank_id = str(source.get("bank_id") or "").strip()
    return {
        "schema_version": "problem_bank_manifest.v1",
        "bank_id": bank_id,
        "generated_at": utc_now(),
        "source": {
            "name": source.get("name") or bank_id,
            "dataset_id": source.get("dataset_id") or bank_id,
            "source_url": source.get("source_url") or "",
            "dataset_url": source.get("dataset_url") or "",
            "license": source.get("license") or "",
            "import_status": source.get("import_status") or "registered_pending_import",
            "import_mode": source.get("import_mode") or "manual_adapter",
            "expected_scale": source.get("expected_scale") or "",
            "language": source.get("language") or "",
            "school_bands": source.get("school_bands") or [],
            "domains": source.get("domains") or [],
            "integration_role": source.get("integration_role") or [],
            "notes": source.get("notes") or "",
        },
        "storage": {
            "format": "json_shards",
            "encoding": "utf-8",
            "record_schema": "../../schema/problem_bank_record.schema.json",
        },
        "counts": {
            "total": 0,
            "by_subject": {},
            "by_level": {},
            "imported": 0,
            "registered_only": True,
        },
        "shards": [],
        "indexes": {
            "lightweight": "index/problem_index.json",
        },
    }


def register_sources(*, dry_run: bool = False) -> dict[str, Any]:
    registry = read_json(REGISTRY_PATH, {"sources": []})
    sources = [item for item in registry.get("sources") or [] if isinstance(item, dict)]
    catalog = read_json(CATALOG_PATH, {"schema_version": "problem_bank_catalog.v1", "banks": []})
    banks = [dict(item) for item in catalog.get("banks") or [] if isinstance(item, dict)]
    by_id = {str(item.get("bank_id") or "").strip(): item for item in banks}

    registered: list[dict[str, Any]] = []
    for source in sources:
        bank_id = str(source.get("bank_id") or "").strip()
        if not bank_id:
            continue
        source_dir = SOURCES_ROOT / bank_id
        manifest_rel = f"data/problem_bank/sources/{bank_id}/manifest.json"
        manifest = _manifest_for_source(source)
        catalog_entry = {
            "bank_id": bank_id,
            "name": source.get("name") or bank_id,
            "manifest_path": manifest_rel,
            "total": 0,
            "generated_at": manifest["generated_at"],
            "import_status": source.get("import_status") or "registered_pending_import",
        }
        previous = by_id.get(bank_id)
        if previous and int(previous.get("total") or 0) > 0:
            catalog_entry["total"] = int(previous.get("total") or 0)
            catalog_entry["generated_at"] = previous.get("generated_at") or manifest["generated_at"]
        by_id[bank_id] = catalog_entry
        registered.append(catalog_entry)

        if not dry_run:
            write_json(source_dir / "manifest.json", manifest)
            write_json(source_dir / "index" / "problem_index.json", [])

    ordered_known = []
    for item in banks:
        bank_id = str(item.get("bank_id") or "").strip()
        if bank_id and bank_id in by_id:
            ordered_known.append(by_id.pop(bank_id))
    ordered_new = [by_id[key] for key in sorted(by_id)]
    updated_catalog = {
        "schema_version": "problem_bank_catalog.v1",
        "updated_at": utc_now(),
        "banks": ordered_known + ordered_new,
    }
    if not dry_run:
        write_json(CATALOG_PATH, updated_catalog)
    return {"registered": registered, "catalog": updated_catalog}


def main() -> None:
    parser = argparse.ArgumentParser(description="Register external math datasets as Coco problem-bank sources.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = register_sources(dry_run=bool(args.dry_run))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
