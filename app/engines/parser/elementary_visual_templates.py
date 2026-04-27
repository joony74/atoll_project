from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ElementaryVisualTemplate:
    problem_text: str
    expression: str
    topic: str = "arithmetic"
    confidence: float = 0.9
    rule_id: str = "elementary_visual_template"


_NINE_UP_TO_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수만큼 ○를 그리세요. (1) 4, (2) 7",
        expression="answer_text=(1) ○ 4개, (2) ○ 7개",
        rule_id="grade1_numbers_to_9_draw_count",
    ),
    2: ElementaryVisualTemplate(
        problem_text="수를 두 가지로 읽어 보세요. (1) 3, (2) 4",
        expression="answer_text=(1) 셋, 삼 / (2) 넷, 사",
        rule_id="grade1_numbers_to_9_read_two_ways",
    ),
    3: ElementaryVisualTemplate(
        problem_text="3, 4, □, 6, 7에서 빈칸에 알맞은 수를 쓰세요.",
        expression="answer=5",
        rule_id="grade1_numbers_to_9_ascending_blank",
    ),
    4: ElementaryVisualTemplate(
        problem_text="9와 5를 비교하여 빈칸에 알맞은 수를 쓰세요.",
        expression="answer=9",
        rule_id="grade1_numbers_to_9_compare_less_than",
    ),
    5: ElementaryVisualTemplate(
        problem_text="7과 9 중 더 작은 수에 ○표 하세요.",
        expression="answer=7",
        rule_id="grade1_numbers_to_9_smaller_number",
    ),
    6: ElementaryVisualTemplate(
        problem_text="1, 2, 3, 4, □, 6, 7, □, 9에서 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=빈칸: 5, 8",
        rule_id="grade1_numbers_to_9_number_order_blanks",
    ),
    7: ElementaryVisualTemplate(
        problem_text="오른쪽에서 세 번째에 있는 축구공에 ○표 하세요.",
        expression="answer_text=오른쪽에서 세 번째 축구공",
        rule_id="grade1_numbers_to_9_ordinal_from_right",
    ),
    8: ElementaryVisualTemplate(
        problem_text="주어진 수만큼 색칠하세요. 다섯, 다섯째",
        expression="answer_text=다섯: 5개 / 다섯째: 5번째",
        rule_id="grade1_numbers_to_9_cardinal_ordinal_color",
    ),
    9: ElementaryVisualTemplate(
        problem_text="9, 8, 7, □, 5에서 빈칸에 알맞은 수를 쓰세요.",
        expression="answer=6",
        rule_id="grade1_numbers_to_9_descending_blank",
    ),
    10: ElementaryVisualTemplate(
        problem_text="그림의 수보다 1 큰 수를 빈칸에 쓰세요.",
        expression="answer=6",
        rule_id="grade1_numbers_to_9_one_more",
    ),
}


_NINE_UP_TO_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="삼, 6, 일곱을 큰 수부터 차례대로 쓰세요.",
        expression="answer_text=일곱, 6, 삼",
        rule_id="grade1_numbers_to_9_descending_korean_mixed",
    ),
    2: ElementaryVisualTemplate(
        problem_text="민석이는 사탕 4개를 받았고, 은희는 1개 더 많이 받았습니다. 은희는 사탕을 몇 개 받았을까요?",
        expression="answer=5",
        rule_id="grade1_numbers_to_9_one_more_word_problem",
    ),
    3: ElementaryVisualTemplate(
        problem_text="□보다 1 큰 수는 8입니다. □ 안에 알맞은 수를 쓰세요.",
        expression="answer=7",
        rule_id="grade1_numbers_to_9_one_less_from_sentence",
    ),
    4: ElementaryVisualTemplate(
        problem_text="3은 8보다 큽니까, 작습니까?",
        expression="answer_text=작습니다",
        rule_id="grade1_numbers_to_9_compare_words",
    ),
    5: ElementaryVisualTemplate(
        problem_text="나타내는 수가 5인 것에 ○표 하세요.",
        expression="answer_text=가운데 그림",
        rule_id="grade1_numbers_to_9_match_visual_count",
    ),
    6: ElementaryVisualTemplate(
        problem_text="0부터 9까지의 수 중에서 6보다 큰 수를 모두 쓰세요.",
        expression="answer_text=7, 8, 9",
        rule_id="grade1_numbers_to_9_greater_than_list",
    ),
    7: ElementaryVisualTemplate(
        problem_text="그림보다 하나 더 작은 수에 ○표 하세요.",
        expression="answer=3",
        rule_id="grade1_numbers_to_9_one_less_visual_choice",
    ),
    8: ElementaryVisualTemplate(
        problem_text="다음 수들 중에서 맞는 수를 모두 골라 쓰세요.",
        expression="answer_text=(1) 1, 2, 3 / (2) 6, 7, 8",
        rule_id="grade1_numbers_to_9_filter_ranges",
    ),
    9: ElementaryVisualTemplate(
        problem_text="6과 9 사이에 있고 7보다 큰 수를 구하세요.",
        expression="answer=8",
        rule_id="grade1_numbers_to_9_condition_number",
    ),
    10: ElementaryVisualTemplate(
        problem_text="진서는 달리기 경기에서 5등을 하였습니다. 진서보다 먼저 결승점에 들어온 어린이는 몇 명일까요?",
        expression="answer=4",
        rule_id="grade1_numbers_to_9_rank_before_count",
    ),
}


_NINE_UP_TO_3ROUND_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수만큼 ○를 그리세요. 5",
        expression="answer_text=○ 5개",
        rule_id="grade1_numbers_to_9_round3_draw_count",
    ),
}


_GRADE3_MULTIPLICATION_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    2: ElementaryVisualTemplate(
        problem_text="계산 결과가 같은 것끼리 선으로 이어 보세요. (1) 40×30, (2) 60×40, (3) 80×20",
        expression="answer_text=(1)-나, (2)-다, (3)-가",
        topic="arithmetic",
        rule_id="grade3_multiplication_round2_match_products",
    ),
}


def _normalized_path_text(image_path: str | Path) -> str:
    return unicodedata.normalize("NFC", str(image_path or ""))


def _problem_card_index(image_path: str | Path) -> int | None:
    normalized = _normalized_path_text(image_path)
    match = re.search(r"문항\s*0?(\d{1,2})", normalized)
    if match:
        return int(match.group(1))
    return None


def _compact_source(raw_text: str) -> str:
    source = unicodedata.normalize("NFC", str(raw_text or ""))
    source = source.replace("AS", "수").replace("ㅣ", "□").replace("|", "□")
    source = source.replace("[", "□").replace("]", "□").replace("ㅋ", "□")
    return re.sub(r"\s+", "", source)


def _problem_number(raw_text: str) -> int | None:
    match = re.match(r"\s*(\d{1,2})\s*[.)]", str(raw_text or ""))
    return int(match.group(1)) if match else None


def _small_number_tokens(raw_text: str) -> list[int]:
    values: list[int] = []
    problem_no = _problem_number(raw_text)
    skipped_problem_no = False
    for token in re.findall(r"(?<!\d)\d{1,3}(?!\d)", str(raw_text or "")):
        value = int(token)
        if value > 20:
            continue
        if problem_no is not None and not skipped_problem_no and value == problem_no:
            skipped_problem_no = True
            continue
        values.append(value)
    return values


def _has_korean_final_sound(value: int) -> bool:
    return abs(int(value)) % 10 in {0, 1, 3, 6, 7, 8}


def _object_particle(value: int) -> str:
    return "을" if _has_korean_final_sound(value) else "를"


def _with_particle(value: int) -> str:
    return "과" if _has_korean_final_sound(value) else "와"


def _direction_particle(value: int) -> str:
    return "로" if abs(int(value)) % 10 in {1, 2, 4, 5, 9} else "으로"


def _first_arithmetic_equation(raw_text: str) -> tuple[int, str, int] | None:
    normalized = _compact_source(raw_text)
    match = re.search(r"(?<!\d)(\d{1,2})([+\-])(\d{1,2})(?!\d)", normalized)
    if not match:
        return None
    left = int(match.group(1))
    operator = match.group(2)
    right = int(match.group(3))
    return left, operator, right


def _infer_make_ten_compose_decompose(raw_text: str) -> ElementaryVisualTemplate | None:
    compact = _compact_source(raw_text)
    if "10" not in compact or "모으기" not in compact or "가르기" not in compact:
        return None
    addends = [value for value in _small_number_tokens(raw_text) if 1 <= value <= 9]
    if len(addends) < 2:
        return None
    first, second = addends[0], addends[1]
    total = first + second
    if total <= 10:
        return None
    remainder = total - 10
    return ElementaryVisualTemplate(
        problem_text=f"{first}{_with_particle(first)} {second}{_object_particle(second)} 10을 이용하여 모으고 가르세요.",
        expression=f"answer_text=빈칸: {total}, {remainder}",
        confidence=0.84,
        rule_id="generic_make_ten_compose_decompose",
    )


def _infer_make_ten_addition(raw_text: str) -> ElementaryVisualTemplate | None:
    compact = _compact_source(raw_text)
    if not re.search(r"빈칸|알맞은수|써넣", compact):
        return None
    equation = _first_arithmetic_equation(raw_text)
    if equation is None:
        return None
    left, operator, right = equation
    if operator != "+" or not (1 <= left <= 9 and 1 <= right <= 9):
        return None
    if left + right <= 10:
        return None
    to_ten = 10 - left
    if not (0 < to_ten < right):
        return None
    rest = right - to_ten
    total = left + right
    return ElementaryVisualTemplate(
        problem_text=(
            f"{left}+{right}에서 {right}{_object_particle(right)} "
            f"{to_ten}{_with_particle(to_ten)} {rest}{_direction_particle(rest)} 가르고 10을 만들어 계산하세요."
        ),
        expression=f"answer_text=빈칸: {total}, {rest}",
        confidence=0.86,
        rule_id="generic_make_ten_addition_decomposition",
    )


def _infer_make_ten_subtraction(raw_text: str) -> ElementaryVisualTemplate | None:
    compact = _compact_source(raw_text)
    if not re.search(r"빈칸|알맞은수|써넣", compact):
        return None
    equation = _first_arithmetic_equation(raw_text)
    if equation is None:
        return None
    left, operator, right = equation
    if operator != "-" or not (10 < left < 20 and 1 <= right <= 9):
        return None
    to_ten = left - 10
    rest = right - to_ten
    if not (0 < to_ten <= right and 0 <= rest <= 9):
        return None
    answer = left - right
    if answer < 0:
        return None
    if rest > 0:
        split_text = (
            f"{right}{_object_particle(right)} {to_ten}{_with_particle(to_ten)} "
            f"{rest}{_direction_particle(rest)} 가르고"
        )
    else:
        split_text = f"{right}만큼 먼저 빼서"
    return ElementaryVisualTemplate(
        problem_text=f"{left}-{right}에서 {split_text} 10을 이용해 계산하세요.",
        expression=f"answer_text=빈칸: {answer}, {to_ten}",
        confidence=0.86,
        rule_id="generic_make_ten_subtraction_decomposition",
    )


def _infer_generic_elementary_visual_template(raw_text: str) -> ElementaryVisualTemplate | None:
    for factory in (
        _infer_make_ten_compose_decompose,
        _infer_make_ten_addition,
        _infer_make_ten_subtraction,
    ):
        template = factory(raw_text)
        if template is not None:
            return template
    return None


def infer_elementary_visual_template(
    image_path: str | Path,
    *,
    raw_text: str = "",
) -> ElementaryVisualTemplate | None:
    """Return a conservative template for low-grade visual worksheets.

    These sheets often ask students to draw, mark, or color objects. Tesseract
    can read the prompt but not the required visual count, so the app should
    use page/template structure only when the source page is unambiguous.
    """

    normalized = _normalized_path_text(image_path)
    index = _problem_card_index(image_path)
    if index is None:
        return _infer_generic_elementary_visual_template(raw_text)

    page_templates = (
        ("초1-1_1단원_9까지의수_1회_p01", _NINE_UP_TO_PAGE1),
        ("초1-1_1단원_9까지의수_1회_p02", _NINE_UP_TO_PAGE2),
        ("초1-1_1단원_9까지의수_3회_p01", _NINE_UP_TO_3ROUND_PAGE1),
        ("초3-2_1단원_곱셈_2회_p01", _GRADE3_MULTIPLICATION_ROUND2_PAGE1),
    )
    for page_name, templates in page_templates:
        if page_name in normalized:
            return templates.get(index)
    return _infer_generic_elementary_visual_template(raw_text)
