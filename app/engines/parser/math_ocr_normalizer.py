from __future__ import annotations

import re

from app.engines.parser.math_normalization_profile import apply_learned_profile_rewrites
from app.utils.text_normalizer import normalize_math_text


SUPERSCRIPT_DIGITS = str.maketrans(
    {
        "⁰": "0",
        "¹": "1",
        "²": "2",
        "³": "3",
        "⁴": "4",
        "⁵": "5",
        "⁶": "6",
        "⁷": "7",
        "⁸": "8",
        "⁹": "9",
        "⁺": "+",
        "⁻": "-",
    }
)

OCR_ESCAPE_RE = re.compile(r"\\(?:n|t|r|i|l|b)")
OCR_BACKSLASH_WORD_RE = re.compile(r"\\[a-zA-Z]+")
METADATA_RE = re.compile(r"(학년도|모의고사|수능|문항|배점|번)")
CHOICE_MARKER_RE = re.compile(r"[①②③④⑤]|\(\s*[1-5]\s*\)|\b[1-5]\s*[).]")
NOISE_RE = re.compile(r"(?:\\n|\\i|[@]|[|]{2,}|\\\\)")


def _replace_superscript_run(match: re.Match[str]) -> str:
    exponent = match.group(0).translate(SUPERSCRIPT_DIGITS)
    return f"^({exponent})"


def _repair_elementary_korean_ocr(text: str) -> str:
    """Fix frequent English-looking OCR leaks in elementary Korean prompts."""

    repaired = text
    repaired = re.sub(r"알맞은\s*[+A]S(?=\s|$|[를을])", "알맞은 수", repaired)
    repaired = re.sub(r"큰\s*[+A]S(?=\s|$|[를을])", "큰 수", repaired)
    repaired = re.sub(r"(?<=[가-힣]\s)OF(?=\s*하)", "○표", repaired, flags=re.IGNORECASE)
    repaired = re.sub(r"(?<=[가-힣])OF(?=\s*하)", "○표", repaired, flags=re.IGNORECASE)
    repaired = re.sub(r"\bOME\s+(?=9까지)", "0부터 ", repaired, flags=re.IGNORECASE)
    repaired = re.sub(r"써\s*You(?=\s|$|[.。])", "써 넣으세요", repaired, flags=re.IGNORECASE)
    repaired = re.sub(r"써\s*Yo\](?=\s|$|[.。])", "써 넣으세요", repaired, flags=re.IGNORECASE)
    repaired = re.sub(r"수\s*중에서", "수 중에서", repaired)
    return repaired


def apply_school_ocr_profile(text: str, *, school_level: str | None = None, profile: str | None = None) -> str:
    level = str(school_level or "").strip().lower()
    profile_id = str(profile or "").strip().lower()
    if level == "elementary" or profile_id.startswith("elementary"):
        return _repair_elementary_korean_ocr(text)
    return text


def normalize_ocr_math_text(text: str, *, school_level: str | None = None, profile: str | None = None) -> str:
    normalized = normalize_math_text(text)
    normalized = normalized.replace("\\n", "\n").replace("\\t", " ")
    normalized = apply_learned_profile_rewrites(normalized)
    normalized = OCR_ESCAPE_RE.sub(" ", normalized)
    normalized = OCR_BACKSLASH_WORD_RE.sub(" ", normalized)
    normalized = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+", _replace_superscript_run, normalized)
    normalized = normalized.replace("×", "*").replace("✕", "*").replace("∙", "*")
    normalized = normalized.replace("÷", "/").replace("／", "/")
    normalized = normalized.replace("−", "-").replace("—", "-").replace("–", "-")
    normalized = normalized.replace("＝", "=").replace("≠", "!=")
    normalized = normalized.replace("≤", "<=").replace("≥", ">=")
    normalized = normalized.replace("∠", "angle ")
    normalized = normalized.replace("@", " ")
    normalized = normalized.replace("”", "*").replace("“", "*")
    normalized = re.sub(r"\b108\s*_?\.?\s*(\d+)\s*\(", r"log_\1(", normalized)
    normalized = re.sub(r"(?<=\d)A\s*(?=[xX])", "", normalized)
    normalized = re.sub(r"(?<=\d)/(?=\s|=|$)", "7", normalized)
    normalized = re.sub(r"([xX])\s*[°º]\s*2", r"\1^2", normalized)
    normalized = re.sub(r"(\d+)\s*[°º]\s*2", r"\1^2", normalized)
    normalized = re.sub(r"(?<=\d)([xX])\s*\*\s*([23])\b", r"\1^\2", normalized)
    normalized = re.sub(r"√\s*([0-9a-zA-Z]+)", r"sqrt(\1)", normalized)
    normalized = re.sub(r"(?<=\d|\))\s*[xX]\s*(?=\d|\()", "*", normalized)
    normalized = re.sub(r"(\d+)\s*/\s*(\d+)", r"\1/\2", normalized)
    normalized = apply_school_ocr_profile(normalized, school_level=school_level, profile=profile)
    normalized = re.sub(r"\s+", " ", normalized)
    return "\n".join(line.strip() for line in normalized.splitlines() if line.strip()).strip()


def clean_visible_math_text(text: str, *, school_level: str | None = None, profile: str | None = None) -> str:
    cleaned = normalize_ocr_math_text(text, school_level=school_level, profile=profile)
    cleaned = cleaned.replace("\n", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" .,:;`'\"")


def ocr_noise_score(text: str) -> int:
    line = str(text or "")
    unknown_symbol_count = len(re.findall(r"[^\w\s가-힣()+\-*/=^.,?:①②③④⑤°º√<>!]", line))
    return sum(
        [
            len(NOISE_RE.findall(line)),
            unknown_symbol_count,
            1 if re.search(r"\b(?:19|20)\d{2}\b", line) else 0,
        ]
    )


def is_metadata_line(text: str) -> bool:
    line = str(text or "").strip()
    if not line:
        return True
    compact = re.sub(r"\s+", "", line)
    return bool(METADATA_RE.search(line) or re.fullmatch(r"(?:19|20)\d{2}", compact))


def is_choice_line(text: str) -> bool:
    return bool(CHOICE_MARKER_RE.search(str(text or "")))


def is_metadata_or_choice_noise_line(text: str, math_score: float = 0.0) -> bool:
    line = str(text or "").strip()
    if is_metadata_line(line):
        return True
    return bool(is_choice_line(line) and math_score < 0.35)
