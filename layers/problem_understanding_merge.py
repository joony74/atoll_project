from __future__ import annotations

from .problem_understanding_vision import normalize_math_text


def merge_ocr_results(text_blocks: dict, math_blocks: dict) -> dict:
    text_lines = [normalize_math_text(line) for line in (text_blocks.get("lines") or []) if normalize_math_text(line)]
    math_expressions = [normalize_math_text(line) for line in (math_blocks.get("latex_expressions") or []) if normalize_math_text(line)]
    combined_parts = []
    seen = set()
    for item in text_lines + math_expressions:
        if item in seen:
            continue
        seen.add(item)
        combined_parts.append(item)

    return {
        "raw_text": "\n".join(text_lines).strip(),
        "math_expressions": math_expressions,
        "combined": "\n".join(combined_parts).strip(),
        "text_line_count": len(text_lines),
        "math_expression_count": len(math_expressions),
    }
