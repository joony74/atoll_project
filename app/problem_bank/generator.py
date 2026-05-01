from __future__ import annotations

import json
import random
import re
import time
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_problem_generation_profile.json"
ELEMENTARY_50K_PROFILE_PATH = (
    PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_elementary_50k_learning_profile.json"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _compact_elementary_50k_profile() -> dict[str, Any] | None:
    if not ELEMENTARY_50K_PROFILE_PATH.exists():
        return None
    try:
        payload = json.loads(ELEMENTARY_50K_PROFILE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}
    routing = payload.get("routing") if isinstance(payload.get("routing"), dict) else {}
    quality_gates = payload.get("quality_gates") if isinstance(payload.get("quality_gates"), dict) else {}
    return {
        "schema_version": payload.get("schema_version"),
        "generated_at": payload.get("generated_at"),
        "counts": counts,
        "routing": routing,
        "quality_gates": quality_gates,
    }


def _attach_elementary_50k_profile(profile: dict[str, Any]) -> dict[str, Any]:
    elementary_profile = _compact_elementary_50k_profile()
    if not elementary_profile:
        return profile
    enriched = dict(profile)
    enriched["elementary_50k"] = elementary_profile
    counts = dict(enriched.get("counts") or {})
    elementary_counts = elementary_profile.get("counts") or {}
    counts["elementary_50k_total_records"] = int(elementary_counts.get("total_records") or 0)
    counts["elementary_50k_learning_ready_or_queued"] = int(
        elementary_counts.get("learning_ready_or_queued") or 0
    )
    enriched["counts"] = counts
    return enriched


@lru_cache(maxsize=1)
def load_generation_profile(path: str | None = None) -> dict[str, Any]:
    profile_path = Path(path) if path else PROFILE_PATH
    if not profile_path.exists():
        fallback = {
            "schema_version": "coco_problem_generation_profile.v1",
            "source_banks": [],
            "counts": {"total_records": 0},
            "domains": {},
            "generation": {
                "default_subject_slug": "arithmetic_word_problem",
                "default_level_number": 2,
                "strategy": "fallback_template_generation",
            },
        }
        return _attach_elementary_50k_profile(fallback) if path is None else fallback
    payload = json.loads(profile_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    return _attach_elementary_50k_profile(payload) if path is None else payload


def _weighted_choice(rng: random.Random, weighted_items: list[tuple[str, int]]) -> str:
    usable = [(item, max(int(weight), 1)) for item, weight in weighted_items if item]
    if not usable:
        return ""
    total = sum(weight for _, weight in usable)
    cursor = rng.randint(1, total)
    for item, weight in usable:
        cursor -= weight
        if cursor <= 0:
            return item
    return usable[-1][0]


def _domain_level_tags(profile: dict[str, Any], subject_slug: str, level_number: int) -> list[str]:
    domain = ((profile.get("domains") or {}).get(subject_slug) or {})
    level = ((domain.get("levels") or {}).get(str(level_number)) or {})
    top_tags = level.get("top_tags") or domain.get("top_tags") or {}
    if isinstance(top_tags, dict):
        return list(top_tags.keys())
    return []


def _select_template(
    rng: random.Random,
    profile: dict[str, Any],
    subject_slug: str,
    level_number: int,
    preferred_tags: list[str] | None = None,
) -> Callable[[random.Random], dict[str, Any]]:
    candidates = [template for template in ARITHMETIC_TEMPLATES if level_number in template["levels"]]
    if not candidates:
        candidates = ARITHMETIC_TEMPLATES
    learned_tags = set(_domain_level_tags(profile, subject_slug, level_number))
    requested = {str(tag or "").strip() for tag in preferred_tags or [] if str(tag or "").strip()}
    weighted: list[tuple[str, int]] = []
    lookup: dict[str, Callable[[random.Random], dict[str, Any]]] = {}
    for template in candidates:
        template_tags = set(template["tags"])
        overlap = len(template_tags & learned_tags) + len(template_tags & requested) * 2
        weight = 1 + overlap
        name = str(template["name"])
        lookup[name] = template["builder"]
        weighted.append((name, weight))
    return lookup[_weighted_choice(rng, weighted)]


def _record(
    *,
    template_name: str,
    level_number: int,
    question: str,
    answer: int | float | str,
    steps: list[str],
    tags: list[str],
    seed: int,
    operands: dict[str, int | float | str],
) -> dict[str, Any]:
    generated_at = utc_now()
    answer_text = str(answer).rstrip("0").rstrip(".") if isinstance(answer, float) else str(answer)
    record_id = f"coco_generated:arithmetic_word_problem:level_{level_number}:{int(time.time() * 1000)}:{seed}"
    solution_plain = "\n".join([*steps, f"따라서 정답은 {answer_text}입니다.", f"#### {answer_text}"])
    return {
        "schema_version": "problem_bank_record.v1",
        "id": record_id,
        "source": {
            "name": "Coco Generated Problem",
            "dataset_id": "coco/generated",
            "source_url": "",
            "license": "generated_from_normalized_profile",
            "original_index": 0,
            "split": "generated",
            "source_problem_id": record_id,
        },
        "content": {
            "language": "ko",
            "problem_latex": question,
            "problem_plain": question,
            "solution_latex": solution_plain,
            "solution_plain": solution_plain,
        },
        "answer": {
            "final_raw": answer_text,
            "final_normalized": answer_text.replace(",", ""),
            "candidates": [answer_text.replace(",", "")],
            "extraction_method": "generated_template",
            "answer_type": "integer" if re.fullmatch(r"[+-]?\d+", answer_text.replace(",", "")) else "numeric_text",
        },
        "taxonomy": {
            "domain": "generated_grade_school_math",
            "subject": "Arithmetic Word Problems",
            "subject_slug": "arithmetic_word_problem",
            "level": f"Level {level_number}",
            "level_number": level_number,
            "grade_band": "elementary" if level_number <= 2 else "elementary_middle" if level_number <= 4 else "middle",
            "concepts": sorted(dict.fromkeys(tags)),
            "tags": sorted(dict.fromkeys(["coco_generated", "arithmetic", "word_problem", *tags, f"level_{level_number}"])),
        },
        "structure": {
            "format": "generated_plain_text_word_problem",
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
            "keywords": sorted(dict.fromkeys(["generated", "arithmetic", "word_problem", *tags])),
        },
        "metadata": {
            "created_at": generated_at,
            "updated_at": generated_at,
            "quality": {
                "solution_available": True,
                "final_answer_extracted": True,
                "needs_review": False,
                "review_reasons": [],
            },
            "generation": {
                "profile_path": str(PROFILE_PATH),
                "template_name": template_name,
                "seed": seed,
                "operands": operands,
            },
        },
    }


def _name(rng: random.Random) -> str:
    return rng.choice(["민지", "준호", "서연", "도윤", "하린", "지우", "현우", "수아"])


def _item(rng: random.Random) -> str:
    return rng.choice(["스티커", "연필", "구슬", "쿠키", "카드", "책갈피", "종이학"])


def _template_add_sub(rng: random.Random) -> dict[str, Any]:
    a = rng.randint(18, 74)
    b = rng.randint(8, 36)
    c = rng.randint(4, min(30, a + b - 1))
    person = _name(rng)
    item = _item(rng)
    answer = a + b - c
    return {
        "template_name": "addition_subtraction_total",
        "level_number": 1,
        "question": f"{person}는 {item}를 {a}개 가지고 있었습니다. 친구에게서 {b}개를 더 받고, 그중 {c}개를 사용했습니다. 남은 {item}는 몇 개인가요?",
        "answer": answer,
        "steps": [
            f"먼저 가진 것과 받은 것을 더하면 {a} + {b} = {a + b}개입니다.",
            f"사용한 {c}개를 빼면 {a + b} - {c} = {answer}개입니다.",
        ],
        "tags": ["addition", "subtraction"],
        "operands": {"a": a, "b": b, "c": c},
    }


def _template_half_more(rng: random.Random) -> dict[str, Any]:
    april = rng.randrange(24, 98, 2)
    may = april // 2
    person = _name(rng)
    item = _item(rng)
    answer = april + may
    return {
        "template_name": "half_more_two_step",
        "level_number": 2,
        "question": f"{person}는 4월에 {item}를 {april}개 팔았습니다. 5월에는 4월의 절반만큼 팔았습니다. 두 달 동안 판 {item}는 모두 몇 개인가요?",
        "answer": answer,
        "steps": [
            f"5월에 판 개수는 {april} ÷ 2 = {may}개입니다.",
            f"두 달 동안 판 개수는 {april} + {may} = {answer}개입니다.",
        ],
        "tags": ["division", "addition", "fraction"],
        "operands": {"april": april, "may": may},
    }


def _template_rate_time(rng: random.Random) -> dict[str, Any]:
    per_hour = rng.choice([6, 8, 9, 12, 15, 18])
    minutes = rng.choice([20, 30, 40, 45, 50])
    person = _name(rng)
    answer = per_hour * minutes // 60 if per_hour * minutes % 60 == 0 else round(per_hour * minutes / 60, 2)
    return {
        "template_name": "rate_time_unit",
        "level_number": 3,
        "question": f"{person}는 한 시간에 {per_hour}쪽을 읽습니다. 같은 속도로 {minutes}분 동안 읽으면 몇 쪽을 읽을 수 있나요?",
        "answer": answer,
        "steps": [
            f"{minutes}분은 {minutes}/60시간입니다.",
            f"읽은 쪽수는 {per_hour} × {minutes}/60 = {answer}쪽입니다.",
        ],
        "tags": ["rate", "multiplication", "division", "unit_conversion"],
        "operands": {"per_hour": per_hour, "minutes": minutes},
    }


def _template_percent_discount(rng: random.Random) -> dict[str, Any]:
    price = rng.randrange(80, 260, 10)
    percent = rng.choice([10, 15, 20, 25, 30])
    extra = rng.randrange(5, 35, 5)
    discount = price * percent // 100
    answer = price - discount + extra
    return {
        "template_name": "percent_discount_money",
        "level_number": 4,
        "question": f"정가가 {price}원인 공책 세트를 {percent}% 할인받아 사고, 배송비 {extra}원을 냈습니다. 모두 얼마를 냈나요?",
        "answer": answer,
        "steps": [
            f"할인 금액은 {price} × {percent}% = {discount}원입니다.",
            f"할인 후 가격은 {price} - {discount} = {price - discount}원입니다.",
            f"배송비를 더하면 {price - discount} + {extra} = {answer}원입니다.",
        ],
        "tags": ["percent", "money", "subtraction", "addition"],
        "operands": {"price": price, "percent": percent, "extra": extra},
    }


def _template_ratio_split(rng: random.Random) -> dict[str, Any]:
    left = rng.randint(2, 5)
    right = rng.randint(left + 1, 8)
    unit = rng.choice([120, 150, 180, 240, 300, 360])
    total = (left + right) * unit
    spent = rng.randrange(20, 160, 10)
    answer = left * unit - spent
    return {
        "template_name": "ratio_split_after_spending",
        "level_number": 5,
        "question": f"두 사람이 {total}원을 {left}:{right}의 비로 나누었습니다. 작은 몫을 받은 사람이 그중 {spent}원을 사용했다면 남은 돈은 얼마인가요?",
        "answer": answer,
        "steps": [
            f"전체 비의 합은 {left} + {right} = {left + right}입니다.",
            f"한 비율 단위는 {total} ÷ {left + right} = {unit}원입니다.",
            f"작은 몫은 {left} × {unit} = {left * unit}원입니다.",
            f"사용한 돈을 빼면 {left * unit} - {spent} = {answer}원입니다.",
        ],
        "tags": ["ratio", "division", "multiplication", "subtraction", "money"],
        "operands": {"left": left, "right": right, "unit": unit, "total": total, "spent": spent},
    }


ARITHMETIC_TEMPLATES: list[dict[str, Any]] = [
    {"name": "addition_subtraction_total", "levels": {1, 2}, "tags": {"addition", "subtraction"}, "builder": _template_add_sub},
    {"name": "half_more_two_step", "levels": {2, 3}, "tags": {"division", "addition", "fraction"}, "builder": _template_half_more},
    {"name": "rate_time_unit", "levels": {3, 4}, "tags": {"rate", "division", "unit_conversion"}, "builder": _template_rate_time},
    {"name": "percent_discount_money", "levels": {4, 5}, "tags": {"percent", "money"}, "builder": _template_percent_discount},
    {"name": "ratio_split_after_spending", "levels": {5}, "tags": {"ratio", "money", "division"}, "builder": _template_ratio_split},
]


def generate_problem_record(
    *,
    subject_slug: str | None = None,
    level_number: int | None = None,
    seed: int | None = None,
    preferred_tags: list[str] | None = None,
) -> dict[str, Any]:
    profile = load_generation_profile()
    generation = profile.get("generation") or {}
    resolved_subject = str(subject_slug or generation.get("default_subject_slug") or "arithmetic_word_problem")
    try:
        resolved_level = int(level_number or generation.get("default_level_number") or 2)
    except Exception:
        resolved_level = 2
    resolved_level = max(1, min(resolved_level, 5))
    resolved_seed = int(seed if seed is not None else time.time() * 1000) % 1_000_000_000
    rng = random.Random(resolved_seed)
    builder = _select_template(rng, profile, resolved_subject, resolved_level, preferred_tags)
    payload = builder(rng)
    payload["level_number"] = resolved_level
    return _record(seed=resolved_seed, **payload)


def clear_caches() -> None:
    load_generation_profile.cache_clear()
