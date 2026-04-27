from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path


VALID_SCHOOL_LEVELS = {"elementary", "middle", "high", "unknown"}


@dataclass(frozen=True, slots=True)
class SchoolProfile:
    school_level: str = "unknown"
    grade: int | None = None
    semester: int | None = None
    unit: str = ""
    profile: str = "unknown"
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)

    def model_dump(self) -> dict:
        return asdict(self)


def normalize_school_level(value: str | None) -> str:
    cleaned = str(value or "").strip().lower()
    if cleaned in {"초", "초등", "elementary", "elem"}:
        return "elementary"
    if cleaned in {"중", "중등", "middle", "middle_school"}:
        return "middle"
    if cleaned in {"고", "고등", "high", "high_school"}:
        return "high"
    return cleaned if cleaned in VALID_SCHOOL_LEVELS else "unknown"


def _nfc(value: str | Path) -> str:
    return unicodedata.normalize("NFC", str(value or ""))


def _extract_grade_semester(source: str) -> tuple[str, int | None, int | None, str | None]:
    patterns = (
        (r"(초|중|고)\s*([1-6])\s*[-_]\s*([12])", "compact_grade_semester"),
        (r"(초등|중등|고등)[^\d]{0,8}([1-6])\s*학년[^\d]{0,8}([12])\s*학기", "korean_grade_semester"),
        (r"(초|중|고)\s*([1-6])", "compact_grade"),
        (r"(초등|중등|고등)[^\d]{0,8}([1-6])\s*학년", "korean_grade"),
    )
    for pattern, evidence in patterns:
        match = re.search(pattern, source)
        if not match:
            continue
        raw_level = match.group(1)
        grade = int(match.group(2))
        semester = int(match.group(3)) if len(match.groups()) >= 3 and match.group(3) else None
        return normalize_school_level(raw_level), grade, semester, evidence
    return "unknown", None, None, None


def _extract_unit(source: str) -> str:
    match = re.search(r"(\d{1,2})\s*단원[_\s.-]*([^_/.\n]+)", source)
    if not match:
        return ""
    unit_no, unit_name = match.groups()
    unit_name = re.sub(r"\s+", " ", unit_name).strip()
    return f"{unit_no}단원 {unit_name}".strip()


def _path_level(source: str) -> tuple[str, list[str]]:
    evidence: list[str] = []
    for token, level in (
        ("01.초등", "elementary"),
        ("초등", "elementary"),
        ("02.중등", "middle"),
        ("중등", "middle"),
        ("03.고등", "high"),
        ("고등", "high"),
    ):
        if token in source:
            evidence.append(f"path:{token}")
            return level, evidence
    return "unknown", evidence


def _text_level(text: str) -> tuple[str, list[str]]:
    evidence: list[str] = []
    source = str(text or "")
    scores = {"elementary": 0, "middle": 0, "high": 0}

    elementary_hits = re.findall(r"○표|색칠|그림|빈칸|알맞은 수|몇\s*개|몇\s*명|9까지의 수|수만큼|차례대로", source)
    middle_hits = re.findall(r"일차함수|연립방정식|이차방정식|비례식|도형의 닮음|피타고라스|중학교|좌표평면", source)
    high_hits = re.findall(r"\blim\b|미분|적분|수열|로그|지수|등비|등차|확률분포|수능|모의고사", source, flags=re.IGNORECASE)
    scores["elementary"] += len(elementary_hits)
    scores["middle"] += len(middle_hits)
    scores["high"] += len(high_hits)

    if elementary_hits:
        evidence.append(f"text:elementary:{','.join(elementary_hits[:4])}")
    if middle_hits:
        evidence.append(f"text:middle:{','.join(middle_hits[:4])}")
    if high_hits:
        evidence.append(f"text:high:{','.join(high_hits[:4])}")

    best_level, best_score = max(scores.items(), key=lambda item: item[1])
    return (best_level, evidence) if best_score > 0 else ("unknown", evidence)


def _profile_for(level: str, text: str, path_text: str) -> str:
    if level == "elementary":
        if re.search(r"○표|색칠|그림|수만큼|빈칸|알맞은 수|9까지의수|9까지의 수", f"{path_text}\n{text}"):
            return "elementary_visual"
        return "elementary_arithmetic"
    if level == "middle":
        return "middle_symbolic"
    if level == "high":
        return "high_symbolic"
    return "unknown"


def infer_school_profile(image_path: str | Path, text: str = "") -> SchoolProfile:
    path_text = _nfc(image_path)
    source = f"{path_text}\n{_nfc(text)}"
    evidence: list[str] = []

    level, grade, semester, grade_evidence = _extract_grade_semester(source)
    if grade_evidence:
        evidence.append(grade_evidence)

    path_detected, path_evidence = _path_level(path_text)
    evidence.extend(path_evidence)
    if level == "unknown" and path_detected != "unknown":
        level = path_detected

    text_detected, text_evidence = _text_level(text)
    evidence.extend(text_evidence)
    if level == "unknown" and text_detected != "unknown":
        level = text_detected

    unit = _extract_unit(source)
    profile = _profile_for(level, text, path_text)
    confidence = 0.0
    if level != "unknown":
        confidence = 0.55
    if grade is not None:
        confidence += 0.18
    if path_detected != "unknown":
        confidence += 0.12
    if text_detected == level:
        confidence += 0.1
    if unit:
        confidence += 0.05

    return SchoolProfile(
        school_level=level,
        grade=grade,
        semester=semester,
        unit=unit,
        profile=profile,
        confidence=min(confidence, 0.98),
        evidence=evidence[:8],
    )
