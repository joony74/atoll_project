from __future__ import annotations

import re

from .problem_understanding_vision import normalize_math_text


def llm_postprocess(ocr_bundle: dict) -> dict:
    """
    외부 LLM이 없을 때도 같은 인터페이스를 유지하기 위한 로컬 후처리기.
    추후 실제 LLM 호출로 교체 가능하게 출력 형식을 고정한다.
    """
    raw_text = normalize_math_text(ocr_bundle.get("raw_text") or "")
    math_expressions = [normalize_math_text(item) for item in (ocr_bundle.get("math_expressions") or []) if normalize_math_text(item)]
    combined = normalize_math_text(ocr_bundle.get("combined") or raw_text)
    lines = [line.strip() for line in combined.splitlines() if line.strip()]
    merged = " ".join(lines).strip() or combined

    coordinates = re.findall(r"[A-Z]?\(\s*-?\d+\s*,\s*-?\d+\s*\)", merged)
    choices = [line for line in lines if re.match(r"^[①-⑤ㄱ-ㅎ1-5@]", line)]
    equations = []
    for line in math_expressions + lines:
        if "=" in line or any(token in line.lower() for token in ("lim", "sin", "cos", "tan", "log", "f(", "g(")):
            equations.append(line)

    return {
        "engine": "local_llm_postprocess",
        "problem_text": merged[:1200],
        "equations": equations[:10],
        "coordinates": coordinates[:10],
        "choices": choices[:5],
        "math_expressions": math_expressions[:10],
        "variables": sorted(set(re.findall(r"\b[xya-z]\b", merged, flags=re.IGNORECASE))),
        "combined_text": combined[:2000],
    }
