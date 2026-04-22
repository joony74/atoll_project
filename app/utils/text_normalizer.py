from __future__ import annotations

import re


MATH_SYMBOL_NORMALIZATIONS = {
    "×": "*",
    "÷": "/",
    "−": "-",
    "–": "-",
    "—": "-",
    "＝": "=",
    "π": "pi",
    "\\pi": "pi",
    "（": "(",
    "）": ")",
    "{": "(",
    "}": ")",
}


def normalize_math_text(text: str) -> str:
    normalized = str(text or "")
    for source, target in MATH_SYMBOL_NORMALIZATIONS.items():
        normalized = normalized.replace(source, target)
    normalized = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", normalized)

    lines: list[str] = []
    for raw_line in normalized.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"\s+", " ", line)
        line = re.sub(r"(\d)\s*/\s*(\d)", r"\1/\2", line)
        line = re.sub(r"(\d)\s*([a-zA-Z])", r"\1\2", line)
        line = re.sub(r"\bcos\s+([^\s]+)", r"cos(\1)", line, flags=re.IGNORECASE)
        line = re.sub(r"\bsin\s+([^\s]+)", r"sin(\1)", line, flags=re.IGNORECASE)
        line = re.sub(r"\btan\s+([^\s]+)", r"tan(\1)", line, flags=re.IGNORECASE)
        line = re.sub(r"cos\(([^)]+)\s*/\s*([^)]+)\)", r"cos(\1/\2)", line, flags=re.IGNORECASE)
        line = re.sub(r"sin\(([^)]+)\s*/\s*([^)]+)\)", r"sin(\1/\2)", line, flags=re.IGNORECASE)
        line = re.sub(r"tan\(([^)]+)\s*/\s*([^)]+)\)", r"tan(\1/\2)", line, flags=re.IGNORECASE)
        line = re.sub(r"\s{2,}", " ", line)
        lines.append(line)
    return "\n".join(lines).strip()


def split_exam_metadata(text: str) -> tuple[str, list[str]]:
    normalized = normalize_math_text(text)
    metadata: list[str] = []
    content_lines: list[str] = []
    for line in normalized.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.search(r"(학년도|모의고사|배점|문항|번)", stripped):
            metadata.append(stripped)
        else:
            content_lines.append(stripped)
    return "\n".join(content_lines).strip(), metadata
