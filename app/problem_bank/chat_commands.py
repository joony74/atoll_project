from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProblemBankCommand:
    action: str
    query: str = ""
    target: str = ""
    subject_slug: str | None = None
    level_number: int | None = None


SUBJECT_ALIASES: dict[str, tuple[str, ...]] = {
    "algebra": ("algebra", "대수"),
    "arithmetic_word_problem": ("arithmetic", "arithmetic word problem", "word problem", "gsm8k", "산수", "문장제", "초등"),
    "counting_probability": ("counting probability", "counting_probability", "경우의수", "확률", "조합"),
    "geometry": ("geometry", "기하"),
    "intermediate_algebra": ("intermediate algebra", "intermediate_algebra", "중급대수", "고급대수"),
    "number_theory": ("number theory", "number_theory", "정수론", "정수"),
    "prealgebra": ("prealgebra", "pre algebra", "기초대수", "초급대수"),
    "precalculus": ("precalculus", "pre calculus", "삼각", "함수", "미적분전"),
}

OPEN_WORDS = ("열기", "선택", "풀기", "보기", "가져오기")
SEARCH_WORDS = ("검색", "찾기", "search", "find")
GENERATE_WORDS = ("출제", "생성", "만들기", "새문제", "새 문제")


def parse_problem_bank_command(prompt: str) -> ProblemBankCommand | None:
    text = re.sub(r"\s+", " ", str(prompt or "").strip())
    match = re.match(r"^문제\s*은행(?:\s+(?P<body>.*))?$", text, re.IGNORECASE)
    if not match:
        return None

    body = str(match.group("body") or "").strip()
    if not body:
        return ProblemBankCommand(action="help")

    for word in GENERATE_WORDS:
        if body.lower().startswith(word.lower()):
            body = body[len(word) :].strip()
            query, subject_slug, level_number = _extract_filters(body)
            return ProblemBankCommand(
                action="generate",
                query=query,
                subject_slug=subject_slug,
                level_number=level_number,
            )

    open_match = re.match(rf"^(?:{'|'.join(OPEN_WORDS)})\s*(?P<target>.+)$", body, re.IGNORECASE)
    if open_match:
        return ProblemBankCommand(action="open", target=str(open_match.group("target") or "").strip())
    if re.fullmatch(r"\d{1,3}", body):
        return ProblemBankCommand(action="open", target=body)

    for word in SEARCH_WORDS:
        if body.lower().startswith(word.lower()):
            body = body[len(word) :].strip()
            break
    if not body:
        return ProblemBankCommand(action="help")

    query, subject_slug, level_number = _extract_filters(body)
    return ProblemBankCommand(
        action="search",
        query=query,
        subject_slug=subject_slug,
        level_number=level_number,
    )


def _extract_filters(text: str) -> tuple[str, str | None, int | None]:
    query = str(text or "").strip()
    subject_slug = _detect_subject_slug(query)
    if subject_slug:
        query = _remove_subject_alias(query, subject_slug)

    level_number = None
    level_patterns = [
        r"\b(?:level|lv|l)\s*_?\s*([1-5])\b",
        r"\b레벨\s*([1-5])\b",
        r"\b난이도\s*([1-5])\b",
    ]
    for pattern in level_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if not match:
            continue
        level_number = int(match.group(1))
        query = re.sub(pattern, " ", query, flags=re.IGNORECASE)
        break

    query = re.sub(r"\s+", " ", query).strip()
    return query, subject_slug, level_number


def _detect_subject_slug(text: str) -> str | None:
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


def _remove_subject_alias(text: str, subject_slug: str) -> str:
    query = str(text or "")
    aliases = sorted(SUBJECT_ALIASES.get(subject_slug, ()), key=len, reverse=True)
    for alias in aliases:
        query = re.sub(re.escape(alias), " ", query, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", query).strip()


def resolve_problem_bank_selection(target: str, last_results: list[dict[str, Any]]) -> dict[str, Any] | None:
    clean_target = str(target or "").strip()
    if not clean_target:
        return None

    if re.fullmatch(r"\d{1,3}", clean_target):
        index = int(clean_target) - 1
        if 0 <= index < len(last_results):
            return last_results[index]
        return None

    for item in last_results:
        if str(item.get("id") or "").strip() == clean_target:
            return item
    return None


def format_problem_bank_help(banks: list[dict[str, Any]]) -> str:
    total = sum(
        int(bank.get("total") or (bank.get("stats") or {}).get("total_records") or 0)
        for bank in banks
        if isinstance(bank, dict)
    )
    total_text = f"현재 {total:,}문항이 준비돼 있어요." if total else "문제은행을 사용할 준비가 되어 있어요."
    return "\n".join(
        [
            f"문제은행 모드로 찾을 수 있어요. {total_text}",
            "",
            "예시",
            "- `문제은행 algebra level 5`",
            "- `문제은행 초등 문장제`",
            "- `문제은행 출제 초등 문장제 난이도 3`",
            "- `문제은행 기하 난이도 3`",
            "- `문제은행 piecewise continuous`",
            "- `학습엔진`",
            "",
            "검색 결과가 나오면 `문제은행 열기 1`처럼 번호로 바로 학습에 올릴 수 있어요.",
        ]
    )


def format_problem_bank_search_results(results: list[dict[str, Any]], command: ProblemBankCommand) -> str:
    if not results:
        return "\n".join(
            [
                "조건에 맞는 문제를 찾지 못했어요.",
                "",
                "검색어를 조금 넓히거나 `문제은행 algebra level 5`처럼 과목과 난이도로 찾아보면 좋아요.",
            ]
        )

    criteria: list[str] = []
    if command.subject_slug:
        criteria.append(command.subject_slug.replace("_", " "))
    if command.level_number:
        criteria.append(f"level {command.level_number}")
    if command.query:
        criteria.append(command.query)
    criteria_text = f" ({' / '.join(criteria)})" if criteria else ""

    lines = [
        f"문제은행에서 {len(results)}개를 찾았어요{criteria_text}.",
        "코코 학습엔진 기준으로 학습하기 좋은 순서로 골랐어요.",
        "",
        "원하는 번호를 `문제은행 열기 1`처럼 입력하면 학습으로 가져올게요.",
        "",
    ]
    for index, item in enumerate(results, start=1):
        subject = str(item.get("subject") or item.get("subject_slug") or "Problem").strip()
        level = str(item.get("level") or "").strip()
        answer = str(item.get("answer") or "").strip()
        preview = _truncate(str(item.get("problem_preview") or ""), 150)
        title = " ".join(part for part in (subject, level) if part).strip()
        lines.append(f"{index}. {title}")
        if preview:
            lines.append(f"   {preview}")
        if answer:
            lines.append(f"   답: {answer}")
    return "\n".join(lines)


def _truncate(text: str, limit: int) -> str:
    collapsed = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: max(0, limit - 1)].rstrip() + "..."
