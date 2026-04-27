from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.engines.parser.math_ocr_normalizer import clean_visible_math_text, ocr_noise_score
from app.engines.parser.school_math_taxonomy import topic_label as school_topic_label


INITIAL_STUDY_CARD_PREFIX = "이미지에서 읽은 내용을 먼저 정리했어요."
BROKEN_FRACTIONAL_POWER_DISPLAY_RE = re.compile(r"\d+\s*[\*\?]\s*[xX*]\s*\d+\s*[°º?\*]")
SEQUENCE_LOG_PRODUCT_DISPLAY_RE = re.compile(
    r"sequence_log_product\(base=(?P<base>\d+),start=(?P<start>\d+),increment=(?P<increment>-?\d+),count=(?P<count>\d+)\)"
)
RECTANGLE_METRIC_RE = re.compile(
    r"rectangle_width\s*(?P<width>-?\d+(?:\.\d+)?)\s*"
    r"rectangle_height\s*(?P<height>-?\d+(?:\.\d+)?)\s*"
    r"rectangle_area\s*(?P<area>[-+\d*/().]+)",
    flags=re.IGNORECASE,
)
SIMPLE_EXPRESSION_RE = re.compile(r"^-?\d+(?:/\d+)?(?:[+\-*/]-?\d+(?:/\d+)?)+$")
AVERAGE_EXPRESSION_RE = re.compile(r"^\((?:-?\d+(?:\+-?\d+){2,})\)/\d+$")

KNOWN_TOPICS = (
    "coordinate_geometry",
    "calculus_derivative",
    "calculus_integral",
    "calculus_limit",
    "quadratic_function",
    "counting_probability",
    "linear_equation",
    "radical_power",
    "fraction_ratio",
    "log_sequence",
    "trigonometry",
    "competition_math",
    "probability",
    "polynomial",
    "statistics",
    "measurement",
    "logarithm",
    "quadratic",
    "arithmetic",
    "function",
    "geometry",
    "sequence",
    "pattern",
)
DISPLAY_LABELS = {
    "pattern": "규칙 찾기",
    "measurement": "측정",
    "quadratic_function": "이차함수",
    "polynomial": "다항식",
    "counting_probability": "경우의 수·확률",
    "competition_math": "수학",
}
FUNCTION_DISPLAY_TOPICS = {
    "coordinate_geometry",
    "function",
    "quadratic_function",
    "calculus_limit",
    "calculus_derivative",
    "calculus_integral",
}


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _as_text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item or "").strip() for item in value if str(item or "").strip()]


def _dedupe_text(values: list[str], limit: int = 6) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in values:
        text = str(raw or "").strip()
        if not text or text in seen:
            continue
        cleaned.append(text)
        seen.add(text)
        if len(cleaned) >= limit:
            break
    return cleaned


def _clean_visible_candidate(value: str) -> str:
    text = str(value or "").replace("\\n", " ").replace("\\i", " ")
    sequence_match = SEQUENCE_LOG_PRODUCT_DISPLAY_RE.fullmatch(text.replace(" ", ""))
    if sequence_match:
        base = sequence_match.group("base")
        start = sequence_match.group("start")
        increment = sequence_match.group("increment")
        count = sequence_match.group("count")
        return f"a1={start}, log_{base}(a_(n+1))={increment}+log_{base}(a_n), a1*...*a{count}={base}^k"
    rectangle_match = RECTANGLE_METRIC_RE.search(text)
    if rectangle_match:
        width = rectangle_match.group("width")
        height = rectangle_match.group("height")
        area = rectangle_match.group("area")
        return f"가로={width}, 세로={height}, 넓이={area}"
    text = text.replace("@", " ")
    text = re.sub(r"\\[a-zA-Z]+", " ", text)
    text = clean_visible_math_text(text)
    text = re.sub(r"\s+", " ", text).strip(" .,:;`'\"")
    if len(text) > 72:
        text = f"{text[:69]}..."
    return text


def _visible_candidates(values: list[str], limit: int = 3) -> list[str]:
    candidates: list[str] = []
    has_repaired_fractional_power = any("^(1/" in _clean_visible_candidate(item) for item in values)
    for raw in values:
        text = _clean_visible_candidate(raw)
        compact = text.replace(" ", "")
        if not text:
            continue
        if has_repaired_fractional_power and BROKEN_FRACTIONAL_POWER_DISPLAY_RE.search(text):
            continue
        if re.match(r"answer(?:_text)?\s*=", text, flags=re.IGNORECASE):
            continue
        if re.search(r"[@\\]|(?:19|20)\d{2}", text):
            continue
        if ocr_noise_score(text) >= 4:
            continue
        if len(compact) < 2:
            continue
        if text not in candidates:
            candidates.append(text)
        if len(candidates) >= limit:
            break
    return candidates


def _analysis(document: dict | None) -> dict[str, Any]:
    return _as_dict((document or {}).get("analysis"))


def _structured(document: dict | None) -> dict[str, Any]:
    return _as_dict(_analysis(document).get("structured_problem"))


def _solved(document: dict | None) -> dict[str, Any]:
    return _as_dict(_analysis(document).get("solve_result"))


def _metadata(structured: dict[str, Any]) -> dict[str, Any]:
    return _as_dict(structured.get("metadata"))


def _problem_bank_record(document: dict | None, structured: dict[str, Any]) -> dict[str, Any]:
    analysis = _analysis(document)
    metadata = _metadata(structured)
    for candidate in (
        metadata.get("problem_bank_record"),
        analysis.get("problem_bank_record"),
    ):
        if isinstance(candidate, dict):
            return dict(candidate)
    return {}


def _topic_from_file_text(text: str) -> str:
    haystack = str(text or "").lower()
    stem = Path(haystack).stem
    for topic in sorted(KNOWN_TOPICS, key=len, reverse=True):
        token = topic.lower()
        if stem.endswith(f"_{token}") or f"_{token}_" in stem or f"/{token}/" in haystack:
            return topic
    return ""


def _record_or_file_topic(document: dict | None, structured: dict[str, Any]) -> str:
    metadata = _metadata(structured)
    record = _problem_bank_record(document, structured)
    for value in (
        metadata.get("problem_bank_topic"),
        record.get("topic"),
        record.get("subject_slug"),
        record.get("subject"),
    ):
        topic = str(value or "").strip()
        if topic in KNOWN_TOPICS:
            return topic
    file_text = " ".join(
        str(item or "")
        for item in (
            (document or {}).get("file_name"),
            (document or {}).get("file_path"),
            metadata.get("image_path"),
        )
    )
    return _topic_from_file_text(file_text)


def _topic_from_problem_cues(combined: str, expressions: list[str]) -> str:
    lowered = combined.lower()
    if "sequence_log_product" in lowered:
        return "log_sequence"
    if re.search(
        r"모으기|가르기|빈칸|알맞은|몇\s*(?:명|개)|더\s*필요|가지고\s*(?:있었|있습니다)|"
        r"받았다면|남아|크기를\s*비교|비교하여|뛰어서\s*세어|숫자로\s*쓰|"
        r"자리\s*숫자|수\s*모형|세\s*자리\s*수|합과\s*차|기념품|개수|"
        r"올림|버림|반올림|천의\s*자리|백의\s*자리|십의\s*자리|자리까지|합을\s*구|몇\s*배|배입니까",
        combined,
    ):
        return "arithmetic"
    if re.search(r"덧셈|뺄셈|곱셈|나눗셈|계산|계산\s*결과", combined):
        return "arithmetic"
    if re.search(r"아래\s*표.{0,30}(?:수량|모두|전체|합계)|수량은\s*모두|모두\s*몇\s*개", combined):
        return "arithmetic"
    if re.search(r"\blim\b|극한|연속", lowered):
        return "calculus_limit"
    if re.search(r"∫|적분", combined) or re.search(r"함수.{0,30}x축.{0,40}구간.{0,20}넓이", combined):
        return "calculus_integral"
    if re.search(r"미분|도함수|접선|순간\s*변화율|순간\s*속도|f'\(|f′\(", combined):
        return "calculus_derivative"
    if re.search(r"\b(?:sin|cos|tan)\b|삼각함수|사인|코사인|탄젠트|π|\\pi\b", lowered):
        return "trigonometry"
    if re.search(r"\blog\b|로그|지수함수", lowered):
        return "logarithm"
    if re.search(r"수열|등차|등비|a_n|시그마|Σ|sum", combined):
        return "sequence"
    if re.search(r"확률|경우의 수|순열|조합|당첨|뽑", combined):
        return "probability"
    if re.search(r"분수|분모|분자|분수의||\ue06d|\d+\s*/\s*\d+", combined):
        return "fraction_ratio"
    if re.search(r"규칙찾기|규칙적인|규칙|수\s*배열표|배열표|차례대로|반복|탁자|의자", combined):
        return "pattern"
    if re.search(r"평균|분산|표준편차|중앙값|최빈값|도수|자료|분류|조사|종류|그래프|표와\s*그래프|날씨", combined) or any(
        AVERAGE_EXPRESSION_RE.fullmatch(expr.replace(" ", "")) for expr in expressions
    ):
        return "statistics"
    if re.search(
        r"\b(?:cm|mm|kg|g|mL|ml|L)\b|시각|시간|날짜|며칠|들이|컵|물병|길이|나무막대|재었|재는|잰|몇\s*번",
        combined,
        flags=re.IGNORECASE,
    ):
        return "measurement"
    if "rectangle_" in lowered or re.search(
        r"직사각형|삼각형|사각형|도형|넓이|둘레|부피|각도|직각|예각|둔각|"
        r"각\s*[ㄱ-ㅎ]|시침|분침|긴바늘|짧은바늘|등분|몇\s*도|반지름|지름|"
        r"직육면체|정육면체|전개도|선분",
        combined,
    ):
        return "geometry"
    if re.search(r"좌표|그래프|기울기|절편|\(\s*-?\d+\s*,\s*-?\d+\s*\)", combined):
        return "coordinate_geometry"
    if re.search(r"\bf\(|\bg\(|y\s*=|함수|정의역|치역", lowered):
        return "function"
    if re.search(r"x\s*(?:\^\(?2\)?|²)|이차", combined):
        return "quadratic"
    if re.search(r"수량|모두 몇|합계|전체 개수|다음 식의 값", combined) or any(
        SIMPLE_EXPRESSION_RE.fullmatch(expr.replace(" ", "")) for expr in expressions
    ):
        return "arithmetic"
    return ""


def display_topic(document: dict | None) -> str:
    structured = _structured(document)
    expressions = _as_text_list(structured.get("expressions"))
    sources = _as_text_list(structured.get("source_text_candidates"))
    metadata = _metadata(structured)
    structured_topic = str(structured.get("math_topic") or "unknown").strip() or "unknown"
    combined = "\n".join(
        [
            str(structured.get("normalized_problem_text") or ""),
            *sources,
            *expressions,
        ]
    )
    cue_topic = _topic_from_problem_cues(combined, expressions)
    if cue_topic:
        elementary_topics = {"arithmetic", "geometry", "measurement", "statistics", "pattern", "fraction_ratio", "probability"}
        if str(metadata.get("school_level") or "") == "elementary" and structured_topic in elementary_topics:
            high_noise_topics = {
                "calculus_limit",
                "calculus_integral",
                "calculus_derivative",
                "trigonometry",
                "logarithm",
                "log_sequence",
                "sequence",
                "function",
                "coordinate_geometry",
                "quadratic",
                "linear_equation",
                "radical_power",
            }
            if cue_topic in high_noise_topics or (structured_topic == "fraction_ratio" and cue_topic == "measurement"):
                return structured_topic
        return cue_topic

    topic_from_source = _record_or_file_topic(document, structured)
    if topic_from_source:
        return topic_from_source

    if structured_topic == "linear_equation" and not any("=" in expr for expr in expressions):
        return "arithmetic"
    return structured_topic


def topic_label(topic: str) -> str:
    topic = str(topic or "unknown").strip() or "unknown"
    label = DISPLAY_LABELS.get(topic) or school_topic_label(topic)
    return f"{label} 문제" if label != "문제 유형 확인 중" and not label.endswith("문제") else label


def _is_weak_problem_text(text: str, topic: str) -> bool:
    compact = re.sub(r"\s+", "", str(text or ""))
    if not compact:
        return True
    if re.fullmatch(r"[-+]?\d+(?:/\d+)?", compact):
        return True
    if compact.lower().startswith("answer="):
        return True
    if len(compact) <= 2:
        return True
    if ocr_noise_score(text) >= 4:
        return True
    if topic == "statistics" and re.search(r"\b(?:SAS|HOS|SSS)\b", text):
        return True
    return False


def _fallback_problem_text(topic: str, expressions: list[str]) -> str:
    expression_text = " ".join(expressions)
    if topic == "geometry":
        if expression_text.startswith("2*("):
            return "도형의 둘레를 구하시오."
        return "도형의 넓이 또는 길이를 구하시오."
    if topic == "statistics":
        return "자료를 보고 필요한 값을 구하시오."
    if topic == "probability":
        return "조건에 맞는 확률을 구하시오."
    if topic == "pattern":
        return "규칙에 맞는 값을 구하시오."
    if topic == "measurement":
        return "측정값을 이용해 물음에 답하시오."
    if topic == "radical_power":
        return "거듭제곱 또는 루트 식의 값을 구하시오."
    if topic == "linear_equation":
        return "방정식의 해를 구하시오."
    if topic in {"quadratic", "quadratic_function"}:
        return "이차식 조건을 이용해 값을 구하시오."
    if topic in {"function", "coordinate_geometry"}:
        return "함수 또는 그래프 조건을 이용해 값을 구하시오."
    if topic == "calculus_limit":
        return "함수의 극한 또는 연속 조건을 해석하시오."
    if topic == "arithmetic":
        return "다음 식의 값을 구하시오."
    return ""


def display_problem_text(document: dict | None, topic: str | None = None) -> str:
    structured = _structured(document)
    resolved_topic = topic or display_topic(document)
    expressions = _as_text_list(structured.get("expressions"))
    raw = _clean_visible_candidate(str(structured.get("normalized_problem_text") or ""))
    raw = raw.replace("SAS", "평균").replace("HOS", "평균")
    if not _is_weak_problem_text(raw, resolved_topic):
        return raw
    return _fallback_problem_text(resolved_topic, expressions)


def _extract_coordinate_candidates(structured: dict[str, Any]) -> list[str]:
    bucket = "\n".join(_as_text_list(structured.get("source_text_candidates")))
    bucket += "\n" + "\n".join(_as_text_list(structured.get("expressions")))
    matches = re.findall(r"\(\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*\)", bucket)
    return _dedupe_text(matches, limit=4)


def _extract_function_candidates(structured: dict[str, Any], topic: str) -> list[str]:
    if topic not in FUNCTION_DISPLAY_TOPICS:
        return []
    expressions = _as_text_list(structured.get("expressions"))
    source_lines: list[str] = []
    for source in _as_text_list(structured.get("source_text_candidates")):
        source_lines.extend(line.strip() for line in source.splitlines() if line.strip())
    candidates: list[str] = []
    for text in [*expressions, *source_lines]:
        cleaned = _clean_visible_candidate(text)
        lowered = cleaned.lower()
        if len(cleaned) > 80 or ocr_noise_score(cleaned) >= 4:
            continue
        if "f(" in lowered or re.search(r"\b[xy]\s*=", lowered) or ("=" in lowered and any(var in lowered for var in ("x", "y"))):
            candidates.append(cleaned)
    return _dedupe_text(candidates, limit=4)


def _analysis_runtime_notes(analysis: dict[str, Any]) -> list[str]:
    structured = _as_dict(analysis.get("structured_problem"))
    solved = _as_dict(analysis.get("solve_result"))
    metadata = _as_dict(structured.get("metadata"))
    ocr_debug = _as_dict(metadata.get("ocr_debug"))
    tesseract_debug = _as_dict(ocr_debug.get("tesseract"))
    vision_debug = _as_dict(ocr_debug.get("vision"))
    repair_debug = _as_dict(ocr_debug.get("text_repair"))

    notes: list[str] = []
    vision_error = str(vision_debug.get("error") or "").strip()
    if vision_debug.get("skipped"):
        notes.append("가벼운 OCR 모드로 문제를 읽었습니다.")
    elif vision_debug and not vision_debug.get("available"):
        if "404" in vision_error:
            notes.append("시각 분석 모델이 설치되지 않아 기본 OCR만 사용했습니다.")
        elif vision_error:
            notes.append("시각 분석 엔진이 응답하지 않아 기본 OCR만 사용했습니다.")
    if str(tesseract_debug.get("variant") or "").strip() == "preprocessed":
        notes.append("기본 OCR 이미지를 보정해서 다시 읽었습니다.")
    if repair_debug.get("accepted"):
        notes.append("읽힌 문제 문장을 텍스트 기준으로 한 번 더 정리했습니다.")
    if str(solved.get("validation_status") or "").strip().lower() == "failed":
        notes.append("복원된 수식이 아직 불안정해서 풀이까지 이어지지 못했습니다.")
    return _dedupe_text(notes, limit=3)


def _answer_candidate(solved: dict[str, Any]) -> str:
    computed = _clean_visible_candidate(str(solved.get("computed_answer") or ""))
    matched = _clean_visible_candidate(str(solved.get("matched_choice") or ""))
    if matched and (len(matched) <= 40 or not computed):
        return matched
    return computed


def _is_elementary_visual_task(structured: dict[str, Any], problem_text: str, sources: list[str]) -> bool:
    metadata = _metadata(structured)
    if str(metadata.get("school_level") or "").strip() != "elementary":
        return False
    combined = re.sub(r"\s+", "", "\n".join([problem_text, *sources]))
    return bool(
        re.search(
            r"그려|색칠|○표|선으로|이어|고르|찾아|모양|그림|세어|써넣|쓰시오|쓰세요|"
            r"도형|뒤집|밀기|돌리|이동|오른쪽|왼쪽|위쪽|아래쪽|규칙찾기|규칙적인|수배열표|배열표",
            combined,
        )
    )


def _is_visual_template_result(structured: dict[str, Any], solved: dict[str, Any]) -> bool:
    metadata = _metadata(structured)
    visual_template = metadata.get("visual_template")
    if isinstance(visual_template, dict) and visual_template.get("rule_id"):
        return True
    return str(solved.get("solver_name") or "").strip() == "visual_template_solver"


def build_recovery_message(document: dict | None) -> str:
    if not document:
        return "업로드한 자료가 아직 없습니다.\n\n이미지를 넣으면 복원된 식 후보와 풀이 단서를 이 영역에 정리해둘게요."

    analysis = _analysis(document)
    structured = _structured(document)
    solved = _solved(document)
    expressions = _as_text_list(structured.get("expressions"))
    source_candidates = _as_text_list(structured.get("source_text_candidates"))
    topic = display_topic(document)
    problem_text = display_problem_text(document, topic)
    question_goal = topic_label(topic)
    runtime_notes = _analysis_runtime_notes(analysis)
    visible_expressions = _visible_candidates(expressions or source_candidates)
    visible_functions = _visible_candidates(_extract_function_candidates(structured, topic))
    visible_coordinates = _visible_candidates(_extract_coordinate_candidates(structured))
    answer_candidate = _answer_candidate(solved)
    elementary_visual_task = _is_elementary_visual_task(structured, problem_text, source_candidates)
    visual_template_result = _is_visual_template_result(structured, solved)
    if visual_template_result and topic == "arithmetic":
        question_goal = "초등 시각 연산 문제"

    lines = [
        INITIAL_STUDY_CARD_PREFIX,
        "",
    ]
    if runtime_notes:
        lines.extend([f"- 상태: {note}" for note in runtime_notes])
        lines.append("")
    if problem_text:
        lines.append(f"- 읽은 문제: {problem_text}")
    if visual_template_result:
        lines.append("- 시각 문항: 원본 그림의 빈칸 도식 기준으로 확인합니다.")
    elif visible_expressions:
        lines.append(f"- 수식 후보: {', '.join(visible_expressions)}")
    elif elementary_visual_task:
        lines.append("- 시각 문항: 원본 그림 기준으로 확인합니다.")
    else:
        lines.append("- 수식 후보: 아직 확실하지 않아 다시 맞춰보는 중입니다.")
    if visible_functions:
        lines.append(f"- 함수 후보: {', '.join(visible_functions)}")
    if visible_coordinates:
        lines.append(f"- 좌표 후보: {', '.join(visible_coordinates)}")
    if answer_candidate:
        lines.append(f"- 답 후보: {answer_candidate}")
    lines.append(f"- 유형 후보: {question_goal}")
    lines.append("")
    if str(solved.get("validation_status") or "").strip().lower() == "failed":
        lines.append("이 상태에서는 정답 확정보다 원본 대조가 먼저 필요해요.")
    else:
        lines.append("이 상태에서 바로 풀이를 이어갈 수 있어요.")
    return "\n".join(lines)
