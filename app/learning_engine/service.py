from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.engines.parser.math_normalization_profile import profile_summary as math_normalization_profile_summary
from app.problem_bank.generator import clear_caches as clear_generator_caches
from app.problem_bank.generator import generate_problem_record, load_generation_profile
from app.problem_bank.repository import clear_caches as clear_repository_caches
from app.problem_bank.repository import list_banks, search_problems


SUBJECT_ALIASES: dict[str, tuple[str, ...]] = {
    "algebra": ("algebra", "대수", "방정식", "일차방정식", "함수"),
    "arithmetic_word_problem": ("arithmetic", "word problem", "gsm8k", "산수", "문장제", "초등"),
    "counting_probability": ("counting probability", "경우의수", "경우의 수", "확률", "순열", "조합"),
    "geometry": ("geometry", "기하", "도형", "삼각형", "사각형", "원"),
    "intermediate_algebra": ("intermediate algebra", "고급대수", "이차방정식", "다항식"),
    "number_theory": ("number theory", "정수론", "정수", "약수", "배수"),
    "prealgebra": ("prealgebra", "기초대수", "초급대수", "중등"),
    "precalculus": ("precalculus", "삼각", "삼각함수", "로그", "수열", "미적분전"),
}

SUBJECT_LABELS: dict[str, str] = {
    "algebra": "대수",
    "arithmetic_word_problem": "초등 문장제",
    "counting_probability": "경우의 수·확률",
    "geometry": "기하",
    "intermediate_algebra": "심화 대수",
    "number_theory": "정수론",
    "prealgebra": "기초 대수",
    "precalculus": "함수·삼각",
}

SCHOOL_BAND_DEFAULTS: dict[str, tuple[str, int]] = {
    "elementary": ("arithmetic_word_problem", 2),
    "middle": ("prealgebra", 3),
    "high": ("algebra", 4),
}

SCHOOL_BAND_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("elementary", ("초등", "초등학교", "초등학생")),
    ("middle", ("중등", "중학교", "중학생")),
    ("high", ("고등", "고등학교", "고등학생", "수능")),
)

TAG_ALIASES: dict[str, tuple[str, ...]] = {
    "addition": ("더하기", "덧셈", "합"),
    "subtraction": ("빼기", "뺄셈", "차"),
    "multiplication": ("곱하기", "곱셈", "배"),
    "division": ("나누기", "나눗셈"),
    "fraction": ("분수", "절반"),
    "decimal": ("소수",),
    "money": ("돈", "원", "가격", "비용"),
    "percent": ("퍼센트", "%", "할인"),
    "ratio": ("비", "비율", "비례"),
    "rate": ("속력", "속도", "단위", "분당", "시간당"),
    "unit_conversion": ("단위", "환산"),
    "equations": ("방정식", "해", "근"),
    "functions": ("함수", "그래프"),
}

LEVEL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:level|lv|l)\s*_?\s*([1-5])\b", re.IGNORECASE),
    re.compile(r"\b레벨\s*([1-5])\b"),
    re.compile(r"\b난이도\s*([1-5])\b"),
)

CONTROL_WORDS_PATTERN = re.compile(
    r"(문제\s*은행|학습\s*엔진|코코|검색|찾기|출제|생성|만들기|새\s*문제|열기|선택|풀기|보기|가져오기|난이도\s*[1-5]|레벨\s*[1-5])",
    re.IGNORECASE,
)

GENERATION_SUPPORTED_SUBJECTS = {"arithmetic_word_problem"}
PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXTERNAL_SOURCE_REGISTRY_PATH = PROJECT_ROOT / "data" / "problem_bank" / "external_math_sources.json"


@dataclass(frozen=True)
class LearningRequest:
    action: str = "search"
    raw_prompt: str = ""
    query: str = ""
    subject_slug: str | None = None
    level_number: int | None = None
    target_level_number: int = 2
    school_band: str | None = None
    tags: tuple[str, ...] = ()
    limit: int = 5
    include_review: bool = False
    include_visual: bool = False
    explicit_subject: bool = False
    explicit_level: bool = False

    def metadata(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["tags"] = list(self.tags)
        return payload


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _clamp_level(value: object, default: int = 2) -> int:
    try:
        number = int(value or default)
    except Exception:
        number = default
    return max(1, min(number, 5))


def _detect_school_band(text: str) -> str | None:
    for band, keywords in SCHOOL_BAND_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return band
    return None


def _detect_level(text: str) -> int | None:
    for pattern in LEVEL_PATTERNS:
        match = pattern.search(text)
        if match:
            return _clamp_level(match.group(1))
    return None


def _detect_subject(text: str) -> str | None:
    lowered = str(text or "").lower()
    best: tuple[int, str] | None = None
    for slug, aliases in SUBJECT_ALIASES.items():
        for alias in aliases:
            alias_text = alias.lower()
            if alias_text not in lowered:
                continue
            score = len(alias_text)
            if best is None or score > best[0]:
                best = (score, slug)
    return best[1] if best else None


def _strip_control_words(text: str) -> str:
    stripped = CONTROL_WORDS_PATTERN.sub(" ", str(text or ""))
    for aliases in SUBJECT_ALIASES.values():
        for alias in sorted(aliases, key=len, reverse=True):
            stripped = re.sub(re.escape(alias), " ", stripped, flags=re.IGNORECASE)
    for aliases in TAG_ALIASES.values():
        for alias in sorted(aliases, key=len, reverse=True):
            stripped = re.sub(re.escape(alias), " ", stripped, flags=re.IGNORECASE)
    return _compact(stripped)


@lru_cache(maxsize=1)
def _profile() -> dict[str, Any]:
    payload = load_generation_profile()
    return payload if isinstance(payload, dict) else {}


def _profile_default() -> tuple[str, int]:
    generation = _profile().get("generation") or {}
    subject = str(generation.get("default_subject_slug") or "arithmetic_word_problem")
    level = _clamp_level(generation.get("default_level_number"), default=2)
    return subject, level


@lru_cache(maxsize=1)
def _external_source_registry() -> dict[str, Any]:
    if not EXTERNAL_SOURCE_REGISTRY_PATH.exists():
        return {"sources": []}
    try:
        payload = json.loads(EXTERNAL_SOURCE_REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"sources": []}
    return payload if isinstance(payload, dict) else {"sources": []}


def _domain_tags(subject_slug: str | None, level_number: int | None = None) -> set[str]:
    if not subject_slug:
        return set()
    domain = ((_profile().get("domains") or {}).get(subject_slug) or {})
    tags: set[str] = set()
    if isinstance(domain.get("top_tags"), dict):
        tags.update(str(item) for item in domain["top_tags"].keys())
    if isinstance(domain.get("top_concepts"), dict):
        tags.update(str(item) for item in domain["top_concepts"].keys())
    if level_number:
        level = ((domain.get("levels") or {}).get(str(level_number)) or {})
        if isinstance(level.get("top_tags"), dict):
            tags.update(str(item) for item in level["top_tags"].keys())
        if isinstance(level.get("top_concepts"), dict):
            tags.update(str(item) for item in level["top_concepts"].keys())
    return {item for item in tags if item}


def _extract_tags(text: str, subject_slug: str | None, level_number: int | None) -> tuple[str, ...]:
    lowered = str(text or "").lower()
    tags: set[str] = set()
    known_tags = _domain_tags(subject_slug, level_number)
    for tag in known_tags:
        if tag.lower() in lowered:
            tags.add(tag)
    for tag, aliases in TAG_ALIASES.items():
        if tag in known_tags or tag in TAG_ALIASES:
            if any(alias.lower() in lowered for alias in aliases):
                tags.add(tag)
    return tuple(sorted(tags))


def normalize_learning_request(
    raw_prompt: str = "",
    *,
    action: str = "search",
    query: str = "",
    subject_slug: str | None = None,
    level_number: int | None = None,
    limit: int = 5,
    include_review: bool = False,
    include_visual: bool = False,
) -> LearningRequest:
    prompt_text = _compact(raw_prompt)
    query_text = _compact(query)
    combined = _compact(f"{prompt_text} {query_text}")

    school_band = _detect_school_band(combined)
    detected_subject = _detect_subject(combined)
    default_subject, default_level = _profile_default()
    if school_band:
        default_subject, default_level = SCHOOL_BAND_DEFAULTS.get(school_band, (default_subject, default_level))

    resolved_subject = str(subject_slug or detected_subject or "").strip() or None
    explicit_subject = bool(subject_slug or detected_subject)
    if not resolved_subject and action == "generate":
        resolved_subject = default_subject

    detected_level = _detect_level(combined)
    explicit_level = level_number is not None or detected_level is not None
    exact_level = _clamp_level(level_number if level_number is not None else detected_level) if explicit_level else None
    target_level = exact_level if exact_level is not None else default_level

    cleaned_query = query_text or _strip_control_words(prompt_text)
    if resolved_subject and not query_text:
        cleaned_query = _strip_control_words(cleaned_query)

    tags = _extract_tags(combined, resolved_subject, target_level)
    return LearningRequest(
        action=str(action or "search").strip() or "search",
        raw_prompt=prompt_text,
        query=cleaned_query,
        subject_slug=resolved_subject,
        level_number=exact_level,
        target_level_number=_clamp_level(target_level),
        school_band=school_band,
        tags=tags,
        limit=max(1, min(int(limit or 5), 20)),
        include_review=include_review,
        include_visual=include_visual,
        explicit_subject=explicit_subject,
        explicit_level=explicit_level,
    )


def _stable_fraction(text: str) -> float:
    digest = hashlib.sha1(str(text or "").encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _school_bank_bonus(item: dict[str, Any], request: LearningRequest) -> float:
    bank_id = str(item.get("bank_id") or "").strip()
    if request.school_band == "elementary" and bank_id == "gsm8k":
        return 1.5
    if request.school_band in {"middle", "high"} and bank_id == "competition_math":
        return 1.0
    return 0.0


def _score_candidate(item: dict[str, Any], request: LearningRequest) -> tuple[float, list[str]]:
    score = float(item.get("score") or 0.0)
    reasons: list[str] = []
    subject = str(item.get("subject_slug") or "").strip()
    level = _clamp_level(item.get("level_number"), default=0)
    keywords = {str(token or "").strip().lower() for token in item.get("keywords") or [] if str(token or "").strip()}

    if request.subject_slug and subject == request.subject_slug:
        score += 7.0
        reasons.append("domain_match")

    if request.level_number is not None:
        distance = abs(level - request.level_number)
        score += 6.0 if distance == 0 else max(-4.0, 1.5 - distance * 1.5)
        reasons.append("exact_level" if distance == 0 else "near_level")
    else:
        distance = abs(level - request.target_level_number)
        score += max(0.0, 3.5 - distance)
        if distance <= 1:
            reasons.append("target_level")

    tag_hits = [tag for tag in request.tags if tag.lower() in keywords]
    if tag_hits:
        score += len(tag_hits) * 1.25
        reasons.append("tag_match")

    if not bool(item.get("needs_review")):
        score += 2.0
        reasons.append("verified")
    else:
        score -= 5.0

    if bool(item.get("has_asy")) or bool(item.get("requires_rendering")):
        if request.include_visual:
            score += 0.5
            reasons.append("visual_allowed")
        else:
            score -= 1.5

    answer_type = str(item.get("answer_type") or "").strip()
    if request.school_band == "elementary" and answer_type == "integer":
        score += 0.5

    bank_bonus = _school_bank_bonus(item, request)
    if bank_bonus:
        score += bank_bonus
        reasons.append("school_band_source")

    score += _stable_fraction(str(item.get("id") or "")) * 0.01
    return round(score, 4), reasons


def _search_attempts(request: LearningRequest) -> list[dict[str, Any]]:
    attempts: list[dict[str, Any]] = []
    exact_level = request.level_number
    preferred_level = exact_level
    if preferred_level is None and request.subject_slug and not request.query:
        preferred_level = request.target_level_number
    attempts.append(
        {
            "query": request.query,
            "subject_slug": request.subject_slug,
            "level_number": preferred_level,
            "include_asy": request.include_visual,
        }
    )
    if preferred_level is not None:
        attempts.append(
            {
                "query": request.query,
                "subject_slug": request.subject_slug,
                "level_number": None,
                "include_asy": request.include_visual,
            }
        )
    if not request.include_visual:
        attempts.append(
            {
                "query": request.query,
                "subject_slug": request.subject_slug,
                "level_number": preferred_level,
                "include_asy": True,
            }
        )
    if request.subject_slug and request.query:
        attempts.append(
            {
                "query": request.query,
                "subject_slug": None,
                "level_number": exact_level,
                "include_asy": request.include_visual,
            }
        )
    return attempts


def recommend_problem_candidates(request: LearningRequest) -> list[dict[str, Any]]:
    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []
    for attempt in _search_attempts(request):
        results = search_problems(
            str(attempt["query"] or ""),
            bank_id="all",
            subject_slug=attempt["subject_slug"],
            level_number=attempt["level_number"],
            include_review=request.include_review,
            include_asy=bool(attempt["include_asy"]),
            limit=100,
        )
        for item in results:
            problem_id = str(item.get("id") or "").strip()
            if not problem_id or problem_id in seen:
                continue
            seen.add(problem_id)
            score, reasons = _score_candidate(item, request)
            enriched = dict(item)
            enriched["learning_score"] = score
            enriched["learning_reasons"] = reasons
            candidates.append(enriched)
        if len(candidates) >= max(request.limit * 6, 20):
            break

    candidates.sort(
        key=lambda item: (
            float(item.get("learning_score") or 0.0),
            -int(bool(item.get("needs_review"))),
            -int(bool(item.get("has_asy") or item.get("requires_rendering"))),
            str(item.get("id") or ""),
        ),
        reverse=True,
    )
    selected = candidates[: request.limit]
    for index, item in enumerate(selected, start=1):
        item["rank"] = index
        item["learning_request"] = request.metadata()
    return selected


def generate_learning_problem_record(request: LearningRequest, *, seed: int | None = None) -> dict[str, Any]:
    requested_subject = request.subject_slug or "arithmetic_word_problem"
    generation_subject = requested_subject if requested_subject in GENERATION_SUPPORTED_SUBJECTS else "arithmetic_word_problem"
    preferred_tags = list(request.tags)
    if request.query:
        preferred_tags.extend(token for token in re.split(r"\s+", request.query) if token)
    record = generate_problem_record(
        subject_slug=generation_subject,
        level_number=request.level_number or request.target_level_number,
        seed=seed,
        preferred_tags=preferred_tags,
    )
    metadata = record.setdefault("metadata", {})
    generation = metadata.setdefault("generation", {})
    generation["learning_request"] = request.metadata()
    generation["requested_subject_slug"] = requested_subject
    generation["generation_subject_slug"] = generation_subject
    if generation_subject != requested_subject:
        generation["fallback_reason"] = "template_generation_currently_supports_arithmetic_word_problem"
    return record


def format_learning_engine_status() -> str:
    profile = _profile()
    normalization = math_normalization_profile_summary()
    counts = profile.get("counts") or {}
    domains = profile.get("domains") or {}
    source_banks = list_banks()
    registered_external = [
        source
        for source in (_external_source_registry().get("sources") or [])
        if isinstance(source, dict)
    ]
    pending_external = [
        source
        for source in registered_external
        if str(source.get("import_status") or "").strip() == "registered_pending_import"
    ]
    total = int(counts.get("total_records") or 0)
    strategy = str((profile.get("generation") or {}).get("strategy") or "profile_based_selection")

    lines = [
        "코코 학습엔진은 현재 JSON 문제은행과 정규화 프로필을 기준으로 동작해요.",
        "",
        f"- 전체 학습 기준 문항: {total:,}개",
        f"- 연결된 문제은행: {len(source_banks)}개",
        f"- 등록된 외부 수학 소스: {len(registered_external)}개",
        f"- 전체 import 대기 소스: {len(pending_external)}개",
        f"- 수식 정규화 학습 문항: {int(normalization.get('total_records') or 0):,}개",
        f"- 런타임 정규화 규칙: {int(normalization.get('runtime_rule_count') or 0):,}개",
        f"- 출제/추천 전략: {strategy}",
        "",
        "주요 영역",
    ]
    top_domains = sorted(
        (
            (str(slug), int((payload or {}).get("count") or 0))
            for slug, payload in domains.items()
            if isinstance(payload, dict)
        ),
        key=lambda item: item[1],
        reverse=True,
    )[:6]
    for slug, count in top_domains:
        label = SUBJECT_LABELS.get(slug, slug.replace("_", " "))
        lines.append(f"- {label}: {count:,}문항")
    if pending_external:
        lines.extend(["", "등록 완료 / import 대기"])
        for source in pending_external[:6]:
            name = str(source.get("name") or source.get("bank_id") or "").strip()
            mode = str(source.get("import_mode") or "").strip()
            lines.append(f"- {name}: {mode}")
    lines.extend(
        [
            "",
            "채팅에서는 `문제은행 초등 문장제`, `문제은행 기하 난이도 3`, `문제은행 출제 초등 문장제 난이도 3`처럼 쓰면 됩니다.",
        ]
    )
    return "\n".join(lines)


def clear_caches() -> None:
    _profile.cache_clear()
    _external_source_registry.cache_clear()
    clear_repository_caches()
    clear_generator_caches()
