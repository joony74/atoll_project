from __future__ import annotations

import re
from typing import Any


_SOLUTION_PROMPT_RE = re.compile(r"풀이|풀어|풀어줘|풀어봐|풀|플이|해설|설명|답|정답")
_SIMILAR_PROBLEM_PROMPT_RE = re.compile(r"다른\s*문제|비슷한\s*문제|유사\s*문제|한\s*문제\s*더|새\s*문제|문제\s*더")
PRACTICE_LIMIT = 10
PRACTICE_BLOCKED_MESSAGE = "먼저 제출된 문제 풀이를 완료하여야 다른 문제가 제출됩니다."
PRACTICE_COMPLETED_MESSAGE = "해당 학습문제를 전부 풀었습니다."


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _is_solution_prompt(prompt: str) -> bool:
    normalized = re.sub(r"\s+", "", str(prompt or ""))
    if not normalized:
        return False
    return bool(_SOLUTION_PROMPT_RE.search(normalized))


def _is_similar_problem_prompt(prompt: str) -> bool:
    normalized = re.sub(r"\s+", "", str(prompt or ""))
    if not normalized:
        return False
    return bool(_SIMILAR_PROBLEM_PROMPT_RE.search(normalized))


def _has_korean_final_sound(value: int) -> bool:
    return abs(int(value)) % 10 in {0, 1, 3, 6, 7, 8}


def _object_particle(value: int) -> str:
    return "을" if _has_korean_final_sound(value) else "를"


def _topic_particle(value: int) -> str:
    return "은" if _has_korean_final_sound(value) else "는"


def _with_particle(value: int) -> str:
    return "과" if _has_korean_final_sound(value) else "와"


def _direction_particle(value: int) -> str:
    return "로" if abs(int(value)) % 10 in {1, 2, 4, 5, 9} else "으로"


def _visual_template_payload(document: dict | None) -> tuple[str, str, str] | None:
    analysis = _as_dict((document or {}).get("analysis"))
    structured = _as_dict(analysis.get("structured_problem"))
    solved = _as_dict(analysis.get("solve_result"))
    metadata = _as_dict(structured.get("metadata"))
    visual_template = _as_dict(metadata.get("visual_template"))
    rule_id = str(visual_template.get("rule_id") or "").strip()
    solver_name = str(solved.get("solver_name") or "").strip()
    answer = str(solved.get("matched_choice") or solved.get("computed_answer") or "").strip()
    problem_text = str(structured.get("normalized_problem_text") or "").strip()
    if not answer or not problem_text:
        return None
    if not rule_id and solver_name != "visual_template_solver":
        return None
    return rule_id, problem_text, answer


def _document_key(document: dict | None, state: dict | None = None) -> str:
    doc_id = str((document or {}).get("doc_id") or "").strip()
    if doc_id:
        return doc_id
    return str((state or {}).get("selected_doc_id") or "").strip()


def _practice_bucket(state: dict | None) -> dict[str, Any] | None:
    if not isinstance(state, dict):
        return None
    bucket = state.setdefault("generated_practice_by_doc", {})
    if not isinstance(bucket, dict):
        bucket = {}
        state["generated_practice_by_doc"] = bucket
    return bucket


def _normalize_practice_session(state: dict | None, document: dict | None) -> dict[str, Any] | None:
    bucket = _practice_bucket(state)
    if bucket is None:
        return None
    doc_id = _document_key(document, state)
    if not doc_id:
        return None
    session = _as_dict(bucket.get(doc_id))
    if not session:
        return None
    items = session.get("items")
    if isinstance(items, list):
        normalized_items = [_as_dict(item) for item in items if isinstance(item, dict)]
        session["items"] = normalized_items
        if normalized_items:
            latest = normalized_items[-1]
            session["rule_id"] = str(latest.get("rule_id") or session.get("rule_id") or "").strip()
            session["problem_text"] = str(latest.get("problem_text") or session.get("problem_text") or "").strip()
            session["answer"] = str(latest.get("answer") or session.get("answer") or "").strip()
            session["current_index"] = int(latest.get("index") or len(normalized_items))
        bucket[doc_id] = session
        return session

    rule_id = str(session.get("rule_id") or "").strip()
    problem_text = str(session.get("problem_text") or "").strip()
    answer = str(session.get("answer") or "").strip()
    if not rule_id or not problem_text or not answer:
        return None
    migrated_item = {
        "index": 1,
        "rule_id": rule_id,
        "problem_text": problem_text,
        "answer": answer,
        "solved": True,
    }
    migrated = {
        "schema_version": "coco_generated_practice_session.v2",
        "doc_id": doc_id,
        "rule_id": rule_id,
        "problem_text": problem_text,
        "answer": answer,
        "current_index": 1,
        "items": [migrated_item],
    }
    bucket[doc_id] = migrated
    return migrated


def _practice_items(session: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(session, dict):
        return []
    return [_as_dict(item) for item in session.get("items") or [] if isinstance(item, dict)]


def _latest_generated_practice_item(state: dict | None, document: dict | None) -> dict[str, Any] | None:
    session = _normalize_practice_session(state, document)
    items = _practice_items(session)
    return items[-1] if items else None


def _latest_generated_practice(state: dict | None, document: dict | None) -> tuple[str, str, str] | None:
    item = _latest_generated_practice_item(state, document)
    if not item:
        return None
    rule_id = str(item.get("rule_id") or "").strip()
    problem_text = str(item.get("problem_text") or "").strip()
    answer = str(item.get("answer") or "").strip()
    if not rule_id or not problem_text or not answer:
        return None
    return rule_id, problem_text, answer


def _latest_practice_is_unsolved(state: dict | None, document: dict | None) -> bool:
    item = _latest_generated_practice_item(state, document)
    return bool(item and not bool(item.get("solved")))


def _practice_solved_count(state: dict | None, document: dict | None) -> int:
    return sum(1 for item in _practice_items(_normalize_practice_session(state, document)) if bool(item.get("solved")))


def _practice_generated_count(state: dict | None, document: dict | None) -> int:
    return len(_practice_items(_normalize_practice_session(state, document)))


def _used_practice_problem_texts(state: dict | None, document: dict | None) -> set[str]:
    return {
        str(item.get("problem_text") or "").strip()
        for item in _practice_items(_normalize_practice_session(state, document))
        if str(item.get("problem_text") or "").strip()
    }


def _mark_latest_generated_practice_solved(state: dict | None, document: dict | None) -> None:
    session = _normalize_practice_session(state, document)
    items = _practice_items(session)
    if not session or not items:
        return
    items[-1]["solved"] = True
    session["items"] = items


def _store_generated_practice(
    state: dict | None,
    document: dict | None,
    *,
    rule_id: str,
    problem_text: str,
    answer: str,
) -> None:
    bucket = _practice_bucket(state)
    if bucket is None:
        return None
    doc_id = _document_key(document, state)
    if not doc_id:
        return
    session = _normalize_practice_session(state, document) or {
        "schema_version": "coco_generated_practice_session.v2",
        "doc_id": doc_id,
        "items": [],
    }
    items = _practice_items(session)
    index = len(items) + 1
    item = {
        "index": index,
        "rule_id": rule_id,
        "problem_text": problem_text,
        "answer": answer,
        "solved": False,
    }
    items.append(item)
    session["schema_version"] = "coco_generated_practice_session.v2"
    session["doc_id"] = doc_id
    session["rule_id"] = rule_id
    session["problem_text"] = problem_text
    session["answer"] = answer
    session["current_index"] = index
    session["items"] = items[-PRACTICE_LIMIT:]
    bucket[doc_id] = {
        **session,
    }


def _generic_verified_solution_reply(document: dict | None) -> str | None:
    analysis = _as_dict((document or {}).get("analysis"))
    structured = _as_dict(analysis.get("structured_problem"))
    solved = _as_dict(analysis.get("solve_result"))
    status = str(solved.get("validation_status") or "").strip().lower()
    answer = str(solved.get("matched_choice") or solved.get("computed_answer") or "").strip()
    problem_text = str(structured.get("normalized_problem_text") or "").strip()
    if not answer or status in {"", "failed"}:
        return None
    steps = [str(item or "").strip() for item in solved.get("steps") or [] if str(item or "").strip()]
    lines = []
    if problem_text:
        lines.extend([f"현재 문제는 `{problem_text}`로 정리됩니다.", ""])
    if steps:
        lines.append("풀이 흐름은 이렇게 볼 수 있어요.")
        for index, step in enumerate(steps[:4], start=1):
            lines.append(f"{index}. {step}")
        lines.append("")
    lines.append(f"정답: {answer}")
    return "\n".join(lines)


def _generated_problem_reply(problem_text: str, hint: str, index: int | None = None) -> str:
    title = "좋아요. 같은 풀이 기준으로 비슷한 문제를 하나 내볼게요."
    if index is not None:
        title = f"좋아요. 같은 풀이 기준으로 비슷한 문제를 하나 내볼게요. ({index}/{PRACTICE_LIMIT})"
    return "\n".join(
        [
            title,
            "",
            f"문제: {problem_text}",
            "",
            f"힌트: {hint}",
            "풀이가 필요하면 `풀이해줘`라고 해주세요.",
        ]
    )


def _compose_answer(total: int, remainder: int) -> str:
    return f"빈칸: {total}, {remainder}"


def _next_compose_pair(first: int, second: int) -> tuple[int, int]:
    candidates = [(8, 7), (9, 5), (7, 6), (8, 6), (6, 7), (9, 4), (7, 5), (6, 8), (9, 8), (8, 9), (9, 7), (7, 8)]
    start = (first * 3 + second) % len(candidates)
    ordered = candidates[start:] + candidates[:start]
    for candidate in ordered:
        if candidate != (first, second) and sum(candidate) > 10:
            return candidate
    return 8, 7


def _generic_make_ten_compose_candidates(problem_text: str) -> list[tuple[str, str, str]]:
    match = re.search(r"(\d+)\s*[와과]\s*(\d+)", problem_text)
    if not match:
        return []
    original = (int(match.group(1)), int(match.group(2)))
    candidates = [(8, 7), (9, 5), (7, 6), (8, 6), (6, 7), (9, 4), (7, 5), (6, 8), (9, 8), (8, 9), (9, 7), (7, 8)]
    start = (original[0] * 3 + original[1]) % len(candidates)
    ordered = candidates[start:] + candidates[:start]
    generated: list[tuple[str, str, str]] = []
    for first, second in ordered:
        if (first, second) == original or first + second <= 10:
            continue
        total = first + second
        remainder = total - 10
        generated_problem = f"{first}{_with_particle(first)} {second}{_object_particle(second)} 10을 이용하여 모으고 가르세요."
        generated.append(
            (
                generated_problem,
                _compose_answer(total, remainder),
                "두 수를 먼저 모은 다음, 그 수를 10과 나머지로 가르면 됩니다.",
            )
        )
    return generated


def _generic_make_ten_compose_similar(problem_text: str, used_texts: set[str] | None = None) -> tuple[str, str, str] | None:
    used = used_texts or set()
    for generated in _generic_make_ten_compose_candidates(problem_text):
        if generated[0] not in used:
            return generated
    return None


def _next_addition_problem(left: int, right: int) -> tuple[int, int, int, int]:
    new_left = left - 1 if left > 6 else left + 2
    new_left = max(6, min(9, new_left))
    split_first = 10 - new_left
    split_second = max(2, min(8, right - split_first + 1))
    new_right = split_first + split_second
    if new_right > 9:
        split_second = 9 - split_first
        new_right = 9
    return new_left, new_right, split_first, split_second


def _generic_make_ten_addition_candidates(problem_text: str) -> list[tuple[str, str, str]]:
    match = re.search(r"(\d+)\s*\+\s*(\d+)", problem_text)
    if not match:
        return []
    original = (int(match.group(1)), int(match.group(2)))
    candidates: list[tuple[int, int, int, int]] = []
    for left in (8, 9, 7, 6):
        split_first = 10 - left
        for split_second in (3, 4, 5, 2, 6, 7, 8):
            right = split_first + split_second
            if 2 <= right <= 9 and (left, right) != original:
                candidates.append((left, right, split_first, split_second))
    start = (original[0] * 5 + original[1]) % len(candidates) if candidates else 0
    ordered = candidates[start:] + candidates[:start]
    generated: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for left, right, split_first, split_second in ordered:
        total = left + right
        generated_problem = (
            f"{left}+{right}에서 {right}{_object_particle(right)} "
            f"{split_first}{_with_particle(split_first)} {split_second}{_direction_particle(split_second)} "
            "가르고 10을 만들어 계산하세요."
        )
        if generated_problem in seen:
            continue
        seen.add(generated_problem)
        generated.append(
            (
                generated_problem,
                _compose_answer(total, split_second),
                f"{right}{_object_particle(right)} {split_first}{_with_particle(split_first)} {split_second}{_direction_particle(split_second)} 가른 뒤, {left}+{split_first}=10을 먼저 만드세요.",
            )
        )
    return generated


def _generic_make_ten_addition_similar(problem_text: str, used_texts: set[str] | None = None) -> tuple[str, str, str] | None:
    used = used_texts or set()
    for generated in _generic_make_ten_addition_candidates(problem_text):
        if generated[0] not in used:
            return generated
    return None


def _next_subtraction_problem(left: int, split_second: int) -> tuple[int, int, int, int]:
    new_left = left + 1 if left < 18 else left - 1
    new_left = max(12, min(18, new_left))
    split_first = new_left - 10
    split_second = max(1, min(9 - split_first, split_second or 2))
    new_right = split_first + split_second
    return new_left, new_right, split_first, split_second


def _generic_make_ten_subtraction_candidates(problem_text: str) -> list[tuple[str, str, str]]:
    match = re.search(r"(\d+)\s*-\s*(\d+).*?(\d+)\s*[와과]\s*(\d+)", problem_text)
    if not match:
        return []
    original = (int(match.group(1)), int(match.group(2)))
    candidates: list[tuple[int, int, int, int]] = []
    for left in (14, 15, 13, 16, 12, 17, 18):
        split_first = left - 10
        for split_second in (2, 3, 4, 1, 5, 6, 7):
            if split_first + split_second > 9:
                continue
            right = split_first + split_second
            if 2 <= right <= 9 and (left, right) != original:
                candidates.append((left, right, split_first, split_second))
    start = (original[0] * 3 + original[1]) % len(candidates) if candidates else 0
    ordered = candidates[start:] + candidates[:start]
    generated: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for left, right, split_first, split_second in ordered:
        result = 10 - split_second
        generated_problem = (
            f"{left}-{right}에서 {right}{_object_particle(right)} "
            f"{split_first}{_with_particle(split_first)} {split_second}{_direction_particle(split_second)} "
            "가르고 10을 이용해 계산하세요."
        )
        if generated_problem in seen:
            continue
        seen.add(generated_problem)
        generated.append(
            (
                generated_problem,
                _compose_answer(result, split_first),
                f"{right}{_object_particle(right)} {split_first}{_with_particle(split_first)} {split_second}{_direction_particle(split_second)} 가른 뒤, {left}-{split_first}=10을 먼저 만드세요.",
            )
        )
    return generated


def _generic_make_ten_subtraction_similar(problem_text: str, used_texts: set[str] | None = None) -> tuple[str, str, str] | None:
    used = used_texts or set()
    for generated in _generic_make_ten_subtraction_candidates(problem_text):
        if generated[0] not in used:
            return generated
    return None


def _build_visual_similar_problem(
    rule_id: str,
    problem_text: str,
    *,
    state: dict | None = None,
    document: dict | None = None,
    store_generated: bool = True,
) -> str | None:
    if _latest_practice_is_unsolved(state, document):
        return PRACTICE_BLOCKED_MESSAGE
    if _practice_solved_count(state, document) >= PRACTICE_LIMIT:
        return PRACTICE_COMPLETED_MESSAGE

    used_texts = _used_practice_problem_texts(state, document)
    if rule_id == "generic_make_ten_compose_decompose":
        generated = _generic_make_ten_compose_similar(problem_text, used_texts)
    elif rule_id == "generic_make_ten_addition_decomposition":
        generated = _generic_make_ten_addition_similar(problem_text, used_texts)
    elif rule_id == "generic_make_ten_subtraction_decomposition":
        generated = _generic_make_ten_subtraction_similar(problem_text, used_texts)
    else:
        generated = None
    if generated is None:
        return PRACTICE_COMPLETED_MESSAGE if _practice_generated_count(state, document) >= PRACTICE_LIMIT else None
    generated_problem, answer, hint = generated
    if store_generated:
        _store_generated_practice(state, document, rule_id=rule_id, problem_text=generated_problem, answer=answer)
    index = min(_practice_generated_count(state, document) + (0 if store_generated else 1), PRACTICE_LIMIT)
    return _generated_problem_reply(generated_problem, hint, index=index)


def _generic_make_ten_compose_reply(problem_text: str, answer: str) -> str | None:
    match = re.search(r"(\d+)\s*[와과]\s*(\d+)", problem_text)
    answer_values = re.findall(r"-?\d+", answer)
    if not match or len(answer_values) < 2:
        return None
    first = int(match.group(1))
    second = int(match.group(2))
    total = int(answer_values[0])
    remainder = int(answer_values[1])
    return "\n".join(
        [
            "이 문제는 두 수를 먼저 모은 다음, 그 수를 10과 나머지로 가르는 문제예요.",
            "",
            f"1. {first}{_with_particle(first)} {second}{_object_particle(second)} 모으면 {first} + {second} = {total}입니다.",
            f"2. {total}{_topic_particle(total)} 10과 {remainder}로 가를 수 있습니다.",
            "",
            f"따라서 빈칸에는 {total}{_with_particle(total)} {remainder}{_object_particle(remainder)} 쓰면 됩니다.",
            f"정답: {answer}",
        ]
    )


def _generic_make_ten_addition_reply(problem_text: str, answer: str) -> str | None:
    match = re.search(r"(\d+)\s*\+\s*(\d+).*?(\d+)\s*[와과]\s*(\d+)", problem_text)
    answer_values = re.findall(r"-?\d+", answer)
    if not match or len(answer_values) < 2:
        return None
    left = int(match.group(1))
    right = int(match.group(2))
    split_first = int(match.group(3))
    split_second = int(match.group(4))
    total = int(answer_values[0])
    blank_part = int(answer_values[1])
    return "\n".join(
        [
            "이 문제는 10을 먼저 만들어서 더하는 받아올림 덧셈 문제예요.",
            "",
            f"1. {right}{_object_particle(right)} {split_first}{_with_particle(split_first)} {split_second}{_direction_particle(split_second)} 가릅니다.",
            f"2. {left}에 {split_first}를 더하면 10이 됩니다.",
            f"3. 남은 {split_second}를 더하면 10 + {split_second} = {total}입니다.",
            "",
            f"따라서 계산 결과 빈칸은 {total}, 가른 수의 빈칸은 {blank_part}입니다.",
            f"정답: {answer}",
        ]
    )


def _generic_make_ten_subtraction_reply(problem_text: str, answer: str) -> str | None:
    match = re.search(r"(\d+)\s*-\s*(\d+).*?(\d+)\s*[와과]\s*(\d+)", problem_text)
    answer_values = re.findall(r"-?\d+", answer)
    if not match or len(answer_values) < 2:
        return None
    left = int(match.group(1))
    right = int(match.group(2))
    split_first = int(match.group(3))
    split_second = int(match.group(4))
    result = int(answer_values[0])
    blank_part = int(answer_values[1])
    return "\n".join(
        [
            "이 문제는 10을 이용해서 빼는 받아내림 뺄셈 문제예요.",
            "",
            f"1. 빼는 수 {right}{_object_particle(right)} {split_first}{_with_particle(split_first)} {split_second}{_direction_particle(split_second)} 가릅니다.",
            f"2. {left}에서 {split_first}를 먼저 빼면 10이 됩니다.",
            f"3. 남은 {split_second}를 더 빼면 10 - {split_second} = {result}입니다.",
            "",
            f"따라서 계산 결과 빈칸은 {result}, 가른 수의 빈칸은 {blank_part}입니다.",
            f"정답: {answer}",
        ]
    )


def build_fast_study_reply(
    prompt: str,
    document: dict | None,
    *,
    state: dict | None = None,
    store_generated: bool = True,
) -> str | None:
    is_similar_prompt = _is_similar_problem_prompt(prompt)
    is_solution_prompt = _is_solution_prompt(prompt)
    if not is_similar_prompt and not is_solution_prompt:
        return None

    if is_solution_prompt:
        generated_payload = _latest_generated_practice(state, document)
        if generated_payload is not None:
            generated_rule_id, generated_problem_text, generated_answer = generated_payload
            if generated_rule_id == "generic_make_ten_compose_decompose":
                generated_reply = _generic_make_ten_compose_reply(generated_problem_text, generated_answer)
            elif generated_rule_id == "generic_make_ten_addition_decomposition":
                generated_reply = _generic_make_ten_addition_reply(generated_problem_text, generated_answer)
            elif generated_rule_id == "generic_make_ten_subtraction_decomposition":
                generated_reply = _generic_make_ten_subtraction_reply(generated_problem_text, generated_answer)
            else:
                generated_reply = None
            if generated_reply:
                if store_generated:
                    _mark_latest_generated_practice_solved(state, document)
                return generated_reply

    payload = _visual_template_payload(document)
    if payload is None:
        if is_similar_prompt:
            return None
        return _generic_verified_solution_reply(document)
    rule_id, problem_text, answer = payload

    if is_similar_prompt:
        return _build_visual_similar_problem(
            rule_id,
            problem_text,
            state=state,
            document=document,
            store_generated=store_generated,
        )

    if rule_id == "generic_make_ten_compose_decompose":
        reply = _generic_make_ten_compose_reply(problem_text, answer)
    elif rule_id == "generic_make_ten_addition_decomposition":
        reply = _generic_make_ten_addition_reply(problem_text, answer)
    elif rule_id == "generic_make_ten_subtraction_decomposition":
        reply = _generic_make_ten_subtraction_reply(problem_text, answer)
    else:
        reply = None

    if reply:
        return reply

    return _generic_verified_solution_reply(document)
