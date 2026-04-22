from __future__ import annotations

import re


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
    return choices[:5]
