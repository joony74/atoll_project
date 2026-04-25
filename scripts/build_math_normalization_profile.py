from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = PROJECT_ROOT / "data" / "problem_bank" / "catalog.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_math_normalization_profile.json"

LATEX_COMMAND_RE = re.compile(r"\\([a-zA-Z]+)")
INLINE_MATH_RE = re.compile(r"\$([^$]+)\$|\\\[(.*?)\\\]|\\\((.*?)\\\)", re.DOTALL)
PLAIN_EXPR_RE = re.compile(
    r"(?<![a-zA-Z])(?:[a-zA-Z]\s*=\s*)?[+-]?(?:\d+(?:\.\d+)?|[a-zA-Z])(?:\s*(?:[+\-*/^=<>]|<=|>=)\s*(?:\d+(?:\.\d+)?|[a-zA-Z]|\([^)]{1,40}\))){1,8}"
)
FRAC_RE = re.compile(r"\\frac\s*\{([^{}]{1,40})\}\s*\{([^{}]{1,40})\}")
SQRT_RE = re.compile(r"\\sqrt\s*(?:\[[^]]+\])?\s*\{([^{}]{1,40})\}")
POWER_RE = re.compile(r"([a-zA-Z0-9)])\s*(?:\^|\*\*)\s*(?:\{([^{}]{1,12})\}|([+-]?\d{1,3}|[a-zA-Z]))")
LOG_RE = re.compile(r"\\log\s*_\s*\{?([0-9a-zA-Z]+)\}?\s*\{?([^{}\s]+)\}?")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_path(path_text: str) -> Path:
    path = Path(str(path_text or ""))
    return path if path.is_absolute() else PROJECT_ROOT / path


def iter_problem_bank_records() -> Iterable[dict[str, Any]]:
    catalog = read_json(CATALOG_PATH)
    for bank in catalog.get("banks") or []:
        if not isinstance(bank, dict):
            continue
        bank_id = str(bank.get("bank_id") or "").strip()
        manifest_path = resolve_path(str(bank.get("manifest_path") or ""))
        manifest = read_json(manifest_path)
        bank_root = manifest_path.parent
        for shard in manifest.get("shards") or []:
            shard_path = bank_root / str((shard or {}).get("path") or "")
            for record in read_json(shard_path):
                if isinstance(record, dict):
                    enriched = dict(record)
                    enriched["_bank_id"] = bank_id
                    yield enriched


def clean_expr(value: str) -> str:
    text = str(value or "").strip()
    text = text.replace("\\left", "").replace("\\right", "")
    text = text.replace("\\,", " ").replace("\\!", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .,:;")


def latex_to_runtime_expr(value: str) -> str:
    text = clean_expr(value)
    text = FRAC_RE.sub(lambda m: f"({m.group(1)})/({m.group(2)})", text)
    text = SQRT_RE.sub(lambda m: f"sqrt({m.group(1)})", text)
    text = re.sub(r"\\(?:cdot|times)", "*", text)
    text = re.sub(r"\\(?:leq|le)", "<=", text)
    text = re.sub(r"\\(?:geq|ge)", ">=", text)
    text = re.sub(r"\\pi", "pi", text)
    text = re.sub(r"\\log", "log", text)
    text = re.sub(r"\\(?:sin|cos|tan)", lambda m: m.group(0)[1:], text)
    text = re.sub(r"([a-zA-Z0-9)])\s*\^\s*\{([^{}]+)\}", r"\1^\2", text)
    text = re.sub(r"\\[a-zA-Z]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .,:;")


def extract_math_fragments(*texts: str) -> list[str]:
    fragments: list[str] = []

    def append(fragment: str) -> None:
        cleaned = clean_expr(fragment)
        if not cleaned or len(cleaned) > 140:
            return
        if not re.search(r"\d|[a-zA-Z]", cleaned):
            return
        if not re.search(r"[+\-*/^=<>]|\\frac|\\sqrt|\\log|\\sin|\\cos|\\tan", cleaned):
            return
        if cleaned not in fragments:
            fragments.append(cleaned)

    for text in texts:
        source = str(text or "")
        for match in INLINE_MATH_RE.finditer(source):
            append(next(group for group in match.groups() if group is not None))
        for match in PLAIN_EXPR_RE.finditer(source):
            append(match.group(0))
    return fragments[:80]


def expression_shape(expr: str) -> str:
    text = latex_to_runtime_expr(expr).lower()
    text = re.sub(r"\d+(?:\.\d+)?", "N", text)
    text = re.sub(r"\b[a-z]\b", "v", text)
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"N+", "N", text)
    return text[:80]


def classify_pattern(expr: str) -> list[str]:
    text = str(expr or "")
    lowered = text.lower()
    patterns: list[str] = []
    if "\\frac" in text or re.search(r"\d+\s*/\s*\d+", text):
        patterns.append("fraction")
    if "\\sqrt" in text or "sqrt" in lowered or "√" in text:
        patterns.append("radical")
    if "^" in text or "**" in text:
        patterns.append("power")
    if "=" in text:
        patterns.append("equation")
    if re.search(r"\bf\s*\(|\bg\s*\(|\by\s*=", lowered):
        patterns.append("function")
    if "\\log" in text or "log" in lowered:
        patterns.append("logarithm")
    if re.search(r"\\(?:sin|cos|tan)\b|\b(?:sin|cos|tan)\b", lowered):
        patterns.append("trigonometry")
    if "<=" in text or ">=" in text or "\\le" in text or "\\ge" in text:
        patterns.append("inequality")
    if not patterns:
        patterns.append("arithmetic")
    return patterns


def simulated_ocr_pairs(expr: str) -> list[dict[str, str]]:
    runtime = latex_to_runtime_expr(expr)
    pairs: list[dict[str, str]] = []

    def add(noisy: str, normalized: str, reason: str) -> None:
        noisy = clean_expr(noisy)
        normalized = clean_expr(normalized)
        if not noisy or not normalized or noisy == normalized:
            return
        if len(noisy) > 80 or len(normalized) > 80:
            return
        item = {"noisy": noisy, "normalized": normalized, "reason": reason}
        if item not in pairs:
            pairs.append(item)

    for match in FRAC_RE.finditer(expr):
        numerator, denominator = match.groups()
        normalized = f"{numerator}/{denominator}"
        add(f"{numerator} {denominator}", normalized, "latex_fraction_missing_bar")
        add(f"{numerator}7{denominator}", normalized, "fraction_bar_read_as_7")

    for match in SQRT_RE.finditer(expr):
        radicand = match.group(1)
        add(f"√ {radicand}", f"sqrt({radicand})", "sqrt_spacing")
        add(f"? {radicand}", f"sqrt({radicand})", "sqrt_marker_noise")

    for match in POWER_RE.finditer(runtime):
        base = match.group(1)
        exponent = match.group(2) or match.group(3) or ""
        if exponent:
            add(f"{base} {exponent}", f"{base}^{exponent}", "power_space")
            add(f"{base}*{exponent}", f"{base}^{exponent}", "power_star")
            add(f"{base}°{exponent}", f"{base}^{exponent}", "power_degree_mark")

    for match in LOG_RE.finditer(expr):
        base, value = match.groups()
        add(f"log _{base} {value}", f"log_{base}({value})", "log_spacing")
        add(f"108 _{base} {value}", f"log_{base}({value})", "log_read_as_108")

    return pairs


def top(counter: Counter[str], limit: int = 40) -> dict[str, int]:
    return {key: count for key, count in counter.most_common(limit)}


def build_profile() -> dict[str, Any]:
    record_count = 0
    bank_counts: Counter[str] = Counter()
    command_counts: Counter[str] = Counter()
    pattern_counts: Counter[str] = Counter()
    shape_counts: Counter[str] = Counter()
    answer_type_counts: Counter[str] = Counter()
    domain_pattern_counts: dict[str, Counter[str]] = defaultdict(Counter)
    domain_shape_counts: dict[str, Counter[str]] = defaultdict(Counter)
    ocr_pair_counts: Counter[tuple[str, str, str]] = Counter()
    runtime_rule_counts: Counter[tuple[str, str, str]] = Counter()
    examples_by_pattern: dict[str, list[str]] = defaultdict(list)

    for record in iter_problem_bank_records():
        record_count += 1
        bank_id = str(record.get("_bank_id") or "unknown")
        bank_counts.update([bank_id])
        content = record.get("content") or {}
        taxonomy = record.get("taxonomy") or {}
        answer = record.get("answer") or {}
        subject_slug = str(taxonomy.get("subject_slug") or "unknown")
        answer_type_counts.update([str(answer.get("answer_type") or "unknown")])

        latex_text = "\n".join(
            [
                str(content.get("problem_latex") or ""),
                str(content.get("solution_latex") or ""),
            ]
        )
        command_counts.update(LATEX_COMMAND_RE.findall(latex_text))

        fragments = extract_math_fragments(
            str(content.get("problem_latex") or ""),
            str(content.get("solution_latex") or ""),
            str(content.get("problem_plain") or ""),
            str(content.get("solution_plain") or ""),
        )
        for fragment in fragments:
            patterns = classify_pattern(fragment)
            shape = expression_shape(fragment)
            if shape:
                shape_counts.update([shape])
                domain_shape_counts[subject_slug].update([shape])
            for pattern in patterns:
                pattern_counts.update([pattern])
                domain_pattern_counts[subject_slug].update([pattern])
                if len(examples_by_pattern[pattern]) < 12:
                    examples_by_pattern[pattern].append(latex_to_runtime_expr(fragment))
            for pair in simulated_ocr_pairs(fragment):
                key = (pair["noisy"], pair["normalized"], pair["reason"])
                ocr_pair_counts.update([key])

    for noisy, normalized, reason in ocr_pair_counts:
        if reason in {
            "power_space",
            "power_star",
            "power_degree_mark",
            "sqrt_spacing",
            "sqrt_marker_noise",
            "log_spacing",
            "log_read_as_108",
            "fraction_bar_read_as_7",
        }:
            runtime_rule_counts.update([(noisy, normalized, reason)])

    return {
        "schema_version": "coco_math_normalization_profile.v1",
        "generated_at": utc_now(),
        "source": {
            "catalog_path": str(CATALOG_PATH.relative_to(PROJECT_ROOT)),
            "total_records": record_count,
            "bank_counts": dict(sorted(bank_counts.items())),
        },
        "counts": {
            "latex_commands": top(command_counts, 60),
            "normalization_patterns": top(pattern_counts, 40),
            "answer_types": dict(sorted(answer_type_counts.items())),
            "expression_shapes": top(shape_counts, 80),
        },
        "domains": {
            slug: {
                "patterns": top(domain_pattern_counts[slug], 30),
                "expression_shapes": top(domain_shape_counts[slug], 30),
            }
            for slug in sorted(domain_pattern_counts)
        },
        "examples": {
            pattern: values
            for pattern, values in sorted(examples_by_pattern.items())
        },
        "ocr_confusion_pairs": [
            {
                "noisy": noisy,
                "normalized": normalized,
                "reason": reason,
                "count": count,
            }
            for (noisy, normalized, reason), count in ocr_pair_counts.most_common(300)
        ],
        "runtime_rules": [
            {
                "noisy": noisy,
                "normalized": normalized,
                "reason": reason,
                "count": count,
            }
            for (noisy, normalized, reason), count in runtime_rule_counts.most_common(120)
            if count >= 1
        ],
        "notes": (
            "This file is learned from normalized problem-bank records. It is intentionally lightweight: "
            "runtime code uses only high-confidence local rewrites, while the larger counts guide future OCR and formula normalization work."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Coco's math OCR/formula normalization profile.")
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    profile = build_profile()
    write_json(args.output_path, profile)
    print(f"profile={args.output_path}")
    print(f"total_records={profile['source']['total_records']}")
    print(f"runtime_rules={len(profile['runtime_rules'])}")
    print(f"ocr_confusion_pairs={len(profile['ocr_confusion_pairs'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
