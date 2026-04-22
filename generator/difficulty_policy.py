from __future__ import annotations


DIFFICULTY_MAP = {
    "easy": 1,
    "medium": 2,
    "hard": 3,
    "advanced": 4,
}


def normalize_difficulty(value: int | str | None) -> int:
    if isinstance(value, int):
        return max(1, min(4, value))
    text = str(value or "").strip().lower()
    if text.isdigit():
        return max(1, min(4, int(text)))
    return DIFFICULTY_MAP.get(text, 2)


def get_next_difficulty(current_difficulty: int | str | None, mode: str) -> int:
    current = normalize_difficulty(current_difficulty)
    normalized_mode = str(mode or "similar").strip().lower()
    if normalized_mode == "harder":
        return min(4, current + 1)
    if normalized_mode == "next":
        return min(4, current + 1) if current < 3 else current
    return current
