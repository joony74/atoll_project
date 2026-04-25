from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROFILE_PATH = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_math_normalization_profile.json"

FRAC_BRACE_RE = re.compile(r"\\frac\s*\{([^{}]{1,80})\}\s*\{([^{}]{1,80})\}")
FRAC_PAREN_RE = re.compile(r"\\?frac\s*\(([^()]{1,80})\)\s*\(([^()]{1,80})\)")
SQRT_BRACE_RE = re.compile(r"\\sqrt\s*(?:\[[^]]+\])?\s*\{([^{}]{1,80})\}")
POWER_BRACE_RE = re.compile(r"([a-zA-Z0-9)])\s*\^\s*\{([^{}]{1,24})\}")
LATEX_OPERATOR_REPLACEMENTS = (
    ("\\cdot", "*"),
    ("\\times", "*"),
    ("\\div", "/"),
    ("\\leq", "<="),
    ("\\le", "<="),
    ("\\geq", ">="),
    ("\\ge", ">="),
    ("\\neq", "!="),
    ("\\pi", "pi"),
)


@lru_cache(maxsize=1)
def load_math_normalization_profile(path: str | None = None) -> dict[str, Any]:
    profile_path = Path(path) if path else PROFILE_PATH
    if not profile_path.exists():
        return {
            "schema_version": "coco_math_normalization_profile.v1",
            "source": {"total_records": 0, "bank_counts": {}},
            "counts": {},
            "runtime_rules": [],
        }
    try:
        payload = json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "schema_version": "coco_math_normalization_profile.v1",
            "source": {"total_records": 0, "bank_counts": {}},
            "counts": {},
            "runtime_rules": [],
        }
    return payload if isinstance(payload, dict) else {}


def _pattern_count(name: str) -> int:
    patterns = ((load_math_normalization_profile().get("counts") or {}).get("normalization_patterns") or {})
    try:
        return int(patterns.get(name) or 0)
    except Exception:
        return 0


def profile_summary() -> dict[str, Any]:
    profile = load_math_normalization_profile()
    source = profile.get("source") or {}
    counts = profile.get("counts") or {}
    return {
        "schema_version": profile.get("schema_version"),
        "total_records": int(source.get("total_records") or 0),
        "bank_counts": dict(source.get("bank_counts") or {}),
        "pattern_count": len(counts.get("normalization_patterns") or {}),
        "runtime_rule_count": len(profile.get("runtime_rules") or []),
    }


def apply_learned_profile_rewrites(text: str) -> str:
    normalized = str(text or "")
    if not normalized:
        return ""

    # These rewrites are gated by the learned profile so they stay data-backed,
    # but intentionally remain generic. Exact OCR confusion pairs are too noisy
    # to apply directly to arbitrary learner input.
    if _pattern_count("fraction") > 0:
        normalized = FRAC_BRACE_RE.sub(r"(\1)/(\2)", normalized)
        normalized = FRAC_PAREN_RE.sub(r"(\1)/(\2)", normalized)

    if _pattern_count("radical") > 0:
        normalized = SQRT_BRACE_RE.sub(r"sqrt(\1)", normalized)
        normalized = re.sub(r"√\s*\(?\s*([0-9a-zA-Z+\-*/^]{1,40})\s*\)?", r"sqrt(\1)", normalized)

    if _pattern_count("power") > 0:
        normalized = POWER_BRACE_RE.sub(r"\1^(\2)", normalized)
        normalized = re.sub(r"([xX])\s*[°º]\s*([23])\b", r"\1^\2", normalized)

    if _pattern_count("logarithm") > 0:
        normalized = re.sub(r"\b108\s*_?\s*([0-9a-zA-Z]+)\s*\(?\s*([0-9a-zA-Z]+)\s*\)?", r"log_\1(\2)", normalized)
        normalized = re.sub(r"\blog\s+_?\s*([0-9a-zA-Z]+)\s*\(?\s*([0-9a-zA-Z]+)\s*\)?", r"log_\1(\2)", normalized)

    if _pattern_count("trigonometry") > 0:
        normalized = re.sub(r"\\(sin|cos|tan)\b", r"\1", normalized)

    for before, after in LATEX_OPERATOR_REPLACEMENTS:
        normalized = normalized.replace(before, after)
    return normalized


def clear_caches() -> None:
    load_math_normalization_profile.cache_clear()
