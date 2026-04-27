from __future__ import annotations

import re


_CHOICE_LABELS = ("①", "②", "③", "④", "⑤")
_OCR_CHOICE_MARKER_RE = re.compile(r"(?:[①②③④⑤]|[®@©]|[0O]\)|[0O]?[1-5]\)|[1-5][).])")


def _parse_ocr_marker_choices(text: str) -> list[str]:
    choices: list[str] = []
    for line in str(text or "").splitlines():
        markers = list(_OCR_CHOICE_MARKER_RE.finditer(line))
        if len(markers) < 4:
            continue
        values: list[str] = []
        for index, marker in enumerate(markers):
            start = marker.end()
            end = markers[index + 1].start() if index + 1 < len(markers) else len(line)
            body = line[start:end].strip()
            match = re.search(r"[-+]?\d+(?:/\d+)?(?:\.\d+)?", body)
            if match:
                values.append(match.group(0))
        if len(values) >= 4:
            for index, value in enumerate(values[:5]):
                choices.append(f"{_CHOICE_LABELS[index]} {value}")
            break
    return choices


def parse_choices(text: str) -> list[str]:
    normalized = str(text or "")
    choices: list[str] = []
    for match in re.finditer(r"(①|②|③|④|⑤)\s*([^①②③④⑤]+)", normalized):
        value = f"{match.group(1)} {match.group(2).strip()}"
        if value.strip():
            choices.append(value.strip())
    if choices:
        return choices[:5]

    for match in re.finditer(r"(ㄱ|ㄴ|ㄷ|ㄹ|ㅁ)\s*([^ㄱㄴㄷㄹㅁ]+)", normalized):
        value = f"{match.group(1)} {match.group(2).strip()}"
        if value.strip():
            choices.append(value.strip())
    if choices:
        return choices[:5]

    numeric_matches = list(re.finditer(r"(?m)^\s*([1-5])[\).]\s*([^\n]+)", normalized))
    has_choice_prompt = bool(re.search(r"(보기|옳은 것은|알맞은 것은|고르시오|선택지)", normalized))
    short_enough = [
        match for match in numeric_matches
        if len(match.group(2).strip()) <= 40
    ]
    if numeric_matches and (has_choice_prompt or len(short_enough) >= 4):
        for match in numeric_matches:
            body = match.group(2).strip()
            if not body or len(body) > 80:
                continue
            value = f"{match.group(1)}. {body}"
            choices.append(value)
    if choices:
        return choices[:5]

    return _parse_ocr_marker_choices(normalized)[:5]
