from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Callable

from app.utils.text_normalizer import normalize_math_text


@dataclass(frozen=True, slots=True)
class ElementaryFormulaCandidate:
    expression: str
    rule_id: str
    category: str
    source_text: str
    confidence: float = 0.82


@dataclass(frozen=True, slots=True)
class ElementaryFormulaRule:
    rule_id: str
    category: str
    description: str
    extractor: Callable[[str], list[ElementaryFormulaCandidate]]


@dataclass(frozen=True, slots=True)
class ElementaryPreparedFormulaRule:
    rule_id: str
    category: str
    description: str
    extractor_family: str


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", normalize_math_text(str(value or "")))


def _source(value: str) -> str:
    return normalize_math_text(str(value or "")).replace("\\n", "\n")


def _append(
    candidates: list[ElementaryFormulaCandidate],
    *,
    expression: str,
    rule_id: str,
    category: str,
    source_text: str,
    confidence: float = 0.82,
) -> None:
    cleaned = str(expression or "").replace(" ", "").strip(" .,:;")
    if cleaned and all(item.expression != cleaned for item in candidates):
        candidates.append(
            ElementaryFormulaCandidate(
                expression=cleaned,
                rule_id=rule_id,
                category=category,
                source_text=str(source_text or "").strip()[:240],
                confidence=confidence,
            )
        )


def _numbers(value: str, *, minimum: int = -9999, maximum: int = 9999) -> list[int]:
    values: list[int] = []
    for token in re.findall(r"(?<!\d)-?\d{1,5}(?!\d)", str(value or "")):
        number = int(token)
        if minimum <= number <= maximum:
            values.append(number)
    return values


def _format_fraction(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _infer_blank_equation(text: str) -> list[ElementaryFormulaCandidate]:
    source = _source(text)
    candidates: list[ElementaryFormulaCandidate] = []
    if not re.search(r"□|ㅁ|빈\s*칸|빈칸|알맞은\s*수", source):
        return candidates
    blank = r"(?:□|ㅁ|\(\s*\)|\[\s*\]|_)"
    patterns = (
        (rf"(?<!\d)(\d{{1,4}})\s*([+\-×xX*/÷])\s*{blank}\s*=\s*(\d{{1,4}})(?!\d)", "right_blank"),
        (rf"{blank}\s*([+\-×xX*/÷])\s*(\d{{1,4}})\s*=\s*(\d{{1,4}})(?!\d)", "left_blank"),
        (rf"(?<!\d)(\d{{1,4}})\s*=\s*(\d{{1,4}})\s*([+\-×xX*/÷])\s*{blank}", "right_blank_reversed"),
        (rf"(?<!\d)(\d{{1,4}})\s*=\s*{blank}\s*([+\-×xX*/÷])\s*(\d{{1,4}})(?!\d)", "left_blank_reversed"),
    )
    for pattern, kind in patterns:
        for match in re.finditer(pattern, source):
            groups = match.groups()
            answer: int | None = None
            if kind == "right_blank":
                left, operator, total = int(groups[0]), groups[1], int(groups[2])
                if operator == "+":
                    answer = total - left
                elif operator == "-":
                    answer = left - total
                elif operator in {"×", "x", "X", "*"} and left:
                    answer = total // left if total % left == 0 else None
                elif operator in {"/", "÷"} and total:
                    answer = left // total if left % total == 0 else None
            elif kind == "left_blank":
                operator, right, total = groups[0], int(groups[1]), int(groups[2])
                if operator == "+":
                    answer = total - right
                elif operator == "-":
                    answer = total + right
                elif operator in {"×", "x", "X", "*"} and right:
                    answer = total // right if total % right == 0 else None
                elif operator in {"/", "÷"}:
                    answer = total * right
            elif kind == "right_blank_reversed":
                total, left, operator = int(groups[0]), int(groups[1]), groups[2]
                if operator == "+":
                    answer = total - left
                elif operator == "-":
                    answer = left - total
                elif operator in {"×", "x", "X", "*"} and left:
                    answer = total // left if total % left == 0 else None
                elif operator in {"/", "÷"} and total:
                    answer = left // total if left % total == 0 else None
            elif kind == "left_blank_reversed":
                total, operator, right = int(groups[0]), groups[1], int(groups[2])
                if operator == "+":
                    answer = total - right
                elif operator == "-":
                    answer = total + right
                elif operator in {"×", "x", "X", "*"} and right:
                    answer = total // right if total % right == 0 else None
                elif operator in {"/", "÷"}:
                    answer = total * right
            if answer is not None and -9999 <= answer <= 9999:
                _append(
                    candidates,
                    expression=f"answer={answer}",
                    rule_id="elementary_blank_equation",
                    category="arithmetic_blank",
                    source_text=match.group(0),
                    confidence=0.88,
                )
    return candidates


def _infer_equal_share(text: str) -> list[ElementaryFormulaCandidate]:
    source = _source(text)
    candidates: list[ElementaryFormulaCandidate] = []
    for match in re.finditer(
        r"(?<!\d)(\d{1,4})\s*(?:개|장|자루|명분|송이)?[^.\n]{0,40}?(\d{1,3})\s*명(?:에게|이|으로)?[^.\n]{0,50}?똑같이\s*나누",
        source,
    ):
        total, people = int(match.group(1)), int(match.group(2))
        if people <= 0:
            continue
        answer = _format_fraction(Fraction(total, people))
        _append(
            candidates,
            expression=f"answer={answer}",
            rule_id="elementary_equal_share_division",
            category="division_word",
            source_text=match.group(0),
            confidence=0.86,
        )
    return candidates


def _infer_pack_multiplication(text: str) -> list[ElementaryFormulaCandidate]:
    source = _source(text)
    candidates: list[ElementaryFormulaCandidate] = []
    patterns = (
        r"(?:한\s*)?(?:상자|봉지|묶음|줄|칸|봉투).{0,32}?(\d{1,4})\s*(?:개|장|자루|송이|명)?씩.{0,80}?(\d{1,4})\s*(?:상자|봉지|묶음|줄|칸|봉투|개)",
        r"(\d{1,4})\s*(?:개|장|자루|송이|명)?씩.{0,80}?(\d{1,4})\s*(?:상자|봉지|묶음|줄|칸|봉투|개)",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, source):
            per, count = int(match.group(1)), int(match.group(2))
            if per > 0 and count > 0:
                _append(
                    candidates,
                    expression=f"{per}*{count}",
                    rule_id="elementary_pack_multiplication",
                    category="multiplication_word",
                    source_text=match.group(0),
                    confidence=0.84,
                )
    return candidates


def _infer_more_less_than(text: str) -> list[ElementaryFormulaCandidate]:
    source = _source(text)
    candidates: list[ElementaryFormulaCandidate] = []
    for match in re.finditer(r"(?<!\d)(\d{1,4})\s*보다\s*(\d{1,4})\s*(?:만큼\s*)?더\s*(큰|작은)\s*수", source):
        base, delta, direction = int(match.group(1)), int(match.group(2)), match.group(3)
        answer = base + delta if direction == "큰" else base - delta
        _append(
            candidates,
            expression=f"answer={answer}",
            rule_id="elementary_more_less_than_number",
            category="number_relation",
            source_text=match.group(0),
            confidence=0.84,
        )
    return candidates


def _infer_rectangle_metric(text: str) -> list[ElementaryFormulaCandidate]:
    source = _source(text)
    candidates: list[ElementaryFormulaCandidate] = []
    if not re.search(r"직사각형|사각형|가로|세로|둘레|넓이", source):
        return candidates
    width_match = re.search(r"가로(?:의\s*길이)?(?:가|는)?\s*(\d{1,4})", source)
    height_match = re.search(r"세로(?:의\s*길이)?(?:가|는)?\s*(\d{1,4})", source)
    if not width_match or not height_match:
        return candidates
    width, height = int(width_match.group(1)), int(height_match.group(1))
    if "둘레" in source:
        _append(
            candidates,
            expression=f"answer={2 * (width + height)}",
            rule_id="elementary_rectangle_perimeter",
            category="geometry_metric",
            source_text=source,
            confidence=0.86,
        )
    if "넓이" in source:
        _append(
            candidates,
            expression=f"{width}*{height}",
            rule_id="elementary_rectangle_area",
            category="geometry_metric",
            source_text=source,
            confidence=0.86,
        )
    return candidates


def _infer_average(text: str) -> list[ElementaryFormulaCandidate]:
    source = _source(text)
    if "평균" not in source:
        return []
    values = [value for value in _numbers(source, minimum=0, maximum=999) if value <= 300]
    if len(values) < 2:
        return []
    if len(values) > 8:
        values = values[-8:]
    expression = f"({'+'.join(str(value) for value in values)})/{len(values)}"
    return [
        ElementaryFormulaCandidate(
            expression=expression,
            rule_id="elementary_average_values",
            category="statistics_average",
            source_text=source[:240],
            confidence=0.82,
        )
    ]


def _infer_direct_arithmetic(text: str) -> list[ElementaryFormulaCandidate]:
    source = _source(text)
    candidates: list[ElementaryFormulaCandidate] = []
    if not re.search(r"계산|값|구하|식|다음", source):
        return candidates
    for match in re.finditer(r"(?<!\d)(\d{1,4})\s*([+\-×xX*/÷])\s*(\d{1,4})(?!\d)", source):
        left, operator, right = int(match.group(1)), match.group(2), int(match.group(3))
        if operator in {"×", "x", "X", "÷"}:
            normalized = "*" if operator in {"×", "x", "X"} else "/"
        else:
            normalized = operator
        if normalized == "/" and right == 0:
            continue
        _append(
            candidates,
            expression=f"{left}{normalized}{right}",
            rule_id="elementary_direct_arithmetic_expression",
            category="direct_arithmetic",
            source_text=match.group(0),
            confidence=0.86,
        )
    return candidates


def _infer_join_change_word_problem(text: str) -> list[ElementaryFormulaCandidate]:
    source = _source(text)
    candidates: list[ElementaryFormulaCandidate] = []
    for match in re.finditer(
        r"(\d{1,4})\s*(?:개|장|자루|명|송이|권)?[^.\n]{0,36}?(\d{1,4})\s*(?:개|장|자루|명|송이|권)?\s*(?:더\s*받|더\s*사|더\s*넣|추가|합|모두)",
        source,
    ):
        a, b = int(match.group(1)), int(match.group(2))
        _append(
            candidates,
            expression=f"{a}+{b}",
            rule_id="elementary_join_change_addition",
            category="addition_word",
            source_text=match.group(0),
            confidence=0.82,
        )
    for match in re.finditer(
        r"(\d{1,4})\s*(?:개|장|자루|명|송이|권)?[^.\n]{0,36}?(?:그중|중에서|사용|주었|먹었|뺐|남은)[^.\n]{0,20}?(\d{1,4})\s*(?:개|장|자루|명|송이|권)?",
        source,
    ):
        total, used = int(match.group(1)), int(match.group(2))
        if total >= used:
            _append(
                candidates,
                expression=f"{total}-{used}",
                rule_id="elementary_join_change_subtraction",
                category="subtraction_word",
                source_text=match.group(0),
                confidence=0.84,
            )
    return candidates


def _infer_compare_difference(text: str) -> list[ElementaryFormulaCandidate]:
    source = _source(text)
    candidates: list[ElementaryFormulaCandidate] = []
    if not re.search(r"얼마나|몇\s*(?:개|장|명|자루)?\s*더|차", source):
        return candidates
    values = [value for value in _numbers(source, minimum=0, maximum=9999)]
    if len(values) >= 2:
        a, b = values[0], values[1]
        _append(
            candidates,
            expression=f"answer={abs(a - b)}",
            rule_id="elementary_compare_difference",
            category="comparison_word",
            source_text=source,
            confidence=0.8,
        )
    return candidates


def _infer_times_as_many(text: str) -> list[ElementaryFormulaCandidate]:
    source = _source(text)
    candidates: list[ElementaryFormulaCandidate] = []
    for match in re.finditer(r"(\d{1,4})\s*(?:개|장|명|자루|송이)?[^.\n]{0,40}?(\d{1,2})\s*배", source):
        base, times = int(match.group(1)), int(match.group(2))
        if times > 1:
            _append(
                candidates,
                expression=f"{base}*{times}",
                rule_id="elementary_times_as_many",
                category="multiplication_word",
                source_text=match.group(0),
                confidence=0.84,
            )
    return candidates


def _infer_time_after_before(text: str) -> list[ElementaryFormulaCandidate]:
    source = _source(text)
    candidates: list[ElementaryFormulaCandidate] = []
    for match in re.finditer(r"(\d{1,2})\s*시\s*(\d{1,2})?\s*분?.{0,20}?(\d{1,3})\s*분\s*(뒤|후|전)", source):
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        delta = int(match.group(3))
        direction = match.group(4)
        total = hour * 60 + minute + (delta if direction in {"뒤", "후"} else -delta)
        answer_hour = (total // 60) % 24
        answer_minute = total % 60
        _append(
            candidates,
            expression=f"answer_text={answer_hour}시 {answer_minute}분",
            rule_id="elementary_time_after_before_minutes",
            category="time_measurement",
            source_text=match.group(0),
            confidence=0.86,
        )
    return candidates


def _infer_unit_conversion(text: str) -> list[ElementaryFormulaCandidate]:
    source = _source(text)
    candidates: list[ElementaryFormulaCandidate] = []
    for match in re.finditer(r"(\d{1,4})\s*(cm|㎝|m|kg|g|L|mL|ml)", source, flags=re.IGNORECASE):
        value = int(match.group(1))
        unit = match.group(2).lower()
        if unit in {"m"}:
            answer = f"{value * 100}cm"
        elif unit in {"cm", "㎝"} and value >= 100:
            m, cm = divmod(value, 100)
            answer = f"{m}m" if cm == 0 else f"{m}m {cm}cm"
        elif unit == "kg":
            answer = f"{value * 1000}g"
        elif unit == "g" and value >= 1000:
            kg, g = divmod(value, 1000)
            answer = f"{kg}kg" if g == 0 else f"{kg}kg {g}g"
        elif unit == "l":
            answer = f"{value * 1000}mL"
        elif unit in {"ml", "ml"} and value >= 1000:
            liters, ml = divmod(value, 1000)
            answer = f"{liters}L" if ml == 0 else f"{liters}L {ml}mL"
        else:
            continue
        _append(
            candidates,
            expression=f"answer_text={answer}",
            rule_id="elementary_unit_conversion",
            category="unit_conversion",
            source_text=match.group(0),
            confidence=0.78,
        )
    return candidates


def _infer_fraction_arithmetic(text: str) -> list[ElementaryFormulaCandidate]:
    source = _source(text)
    candidates: list[ElementaryFormulaCandidate] = []
    if "/" not in source and "분수" not in source:
        return candidates
    for match in re.finditer(r"(\d{1,2})\s*/\s*(\d{1,2})\s*([+\-×xX*/÷])\s*(\d{1,2})\s*/\s*(\d{1,2})", source):
        a_num, a_den, operator, b_num, b_den = match.groups()
        left = Fraction(int(a_num), int(a_den))
        right = Fraction(int(b_num), int(b_den))
        if operator == "+":
            result = left + right
        elif operator == "-":
            result = left - right
        elif operator in {"×", "x", "X", "*"}:
            result = left * right
        elif operator in {"/", "÷"}:
            if right == 0:
                continue
            result = left / right
        else:
            continue
        _append(
            candidates,
            expression=f"answer={_format_fraction(result)}",
            rule_id="elementary_fraction_arithmetic",
            category="fraction_arithmetic",
            source_text=match.group(0),
            confidence=0.9,
        )
    return candidates


def _infer_square_triangle_metric(text: str) -> list[ElementaryFormulaCandidate]:
    source = _source(text)
    candidates: list[ElementaryFormulaCandidate] = []
    square = re.search(r"정사각형.{0,32}?한\s*변(?:의\s*길이)?(?:가|는)?\s*(\d{1,4})", source)
    if square is None:
        square = re.search(r"한\s*변(?:의\s*길이)?(?:가|는)?\s*(\d{1,4}).{0,32}?정사각형", source)
    if square:
        side = int(square.group(1))
        if "둘레" in source:
            _append(candidates, expression=f"answer={side * 4}", rule_id="elementary_square_perimeter", category="geometry_metric", source_text=source, confidence=0.86)
        if "넓이" in source:
            _append(candidates, expression=f"{side}*{side}", rule_id="elementary_square_area", category="geometry_metric", source_text=source, confidence=0.86)
    triangle = re.search(r"삼각형.{0,32}?밑변(?:의\s*길이)?(?:가|는)?\s*(\d{1,4}).{0,32}?높이(?:가|는)?\s*(\d{1,4})", source)
    if triangle and "넓이" in source:
        base, height = int(triangle.group(1)), int(triangle.group(2))
        _append(candidates, expression=f"{base}*{height}/2", rule_id="elementary_triangle_area", category="geometry_metric", source_text=source, confidence=0.84)
    return candidates


def _infer_sequence_pattern(text: str) -> list[ElementaryFormulaCandidate]:
    source = _source(text)
    candidates: list[ElementaryFormulaCandidate] = []
    if not re.search(r"규칙|빈칸|다음\s*수|차례", source):
        return candidates
    values = [value for value in _numbers(source, minimum=-999, maximum=999)]
    if len(values) < 3:
        return candidates
    tail = values[-5:]
    diffs = [b - a for a, b in zip(tail, tail[1:])]
    if len(set(diffs[-2:])) == 1:
        _append(
            candidates,
            expression=f"answer={tail[-1] + diffs[-1]}",
            rule_id="elementary_arithmetic_sequence_next",
            category="pattern_sequence",
            source_text=source,
            confidence=0.82,
        )
    return candidates


def _infer_statistics_extrema(text: str) -> list[ElementaryFormulaCandidate]:
    source = _source(text)
    candidates: list[ElementaryFormulaCandidate] = []
    if not re.search(r"가장\s*(?:큰|작은)|최댓값|최솟값|범위|차이", source):
        return candidates
    values = [value for value in _numbers(source, minimum=-9999, maximum=9999)]
    if len(values) < 2:
        return candidates
    if re.search(r"가장\s*큰|최댓값", source):
        _append(candidates, expression=f"answer={max(values)}", rule_id="elementary_max_value", category="statistics_extrema", source_text=source, confidence=0.82)
    if re.search(r"가장\s*작은|최솟값", source):
        _append(candidates, expression=f"answer={min(values)}", rule_id="elementary_min_value", category="statistics_extrema", source_text=source, confidence=0.82)
    if re.search(r"범위|차이", source):
        _append(candidates, expression=f"answer={max(values) - min(values)}", rule_id="elementary_range_value", category="statistics_extrema", source_text=source, confidence=0.8)
    return candidates


ELEMENTARY_FORMULA_RULES: tuple[ElementaryFormulaRule, ...] = (
    ElementaryFormulaRule("elementary_direct_arithmetic_expression", "direct_arithmetic", "직접 제시된 사칙연산식", _infer_direct_arithmetic),
    ElementaryFormulaRule("elementary_blank_equation", "arithmetic_blank", "□/ㅁ이 들어간 덧셈·뺄셈식", _infer_blank_equation),
    ElementaryFormulaRule("elementary_join_change_addition", "addition_word", "더 받기/추가/합 문장제", _infer_join_change_word_problem),
    ElementaryFormulaRule("elementary_join_change_subtraction", "subtraction_word", "사용/줌/남은 양 문장제", _infer_join_change_word_problem),
    ElementaryFormulaRule("elementary_compare_difference", "comparison_word", "두 양의 차이 비교 문장제", _infer_compare_difference),
    ElementaryFormulaRule("elementary_equal_share_division", "division_word", "똑같이 나누어 주는 나눗셈 문장제", _infer_equal_share),
    ElementaryFormulaRule("elementary_pack_multiplication", "multiplication_word", "몇 개씩 몇 묶음 곱셈 문장제", _infer_pack_multiplication),
    ElementaryFormulaRule("elementary_times_as_many", "multiplication_word", "몇 배 문장제", _infer_times_as_many),
    ElementaryFormulaRule("elementary_more_less_than_number", "number_relation", "어떤 수보다 n만큼 큰/작은 수", _infer_more_less_than),
    ElementaryFormulaRule("elementary_time_after_before_minutes", "time_measurement", "몇 분 뒤/전 시각", _infer_time_after_before),
    ElementaryFormulaRule("elementary_unit_conversion", "unit_conversion", "cm/m, g/kg, L/mL 단위 변환", _infer_unit_conversion),
    ElementaryFormulaRule("elementary_fraction_arithmetic", "fraction_arithmetic", "분수 사칙연산", _infer_fraction_arithmetic),
    ElementaryFormulaRule("elementary_rectangle_perimeter", "geometry_metric", "직사각형 둘레", _infer_rectangle_metric),
    ElementaryFormulaRule("elementary_rectangle_area", "geometry_metric", "직사각형 넓이", _infer_rectangle_metric),
    ElementaryFormulaRule("elementary_square_perimeter", "geometry_metric", "정사각형 둘레", _infer_square_triangle_metric),
    ElementaryFormulaRule("elementary_square_area", "geometry_metric", "정사각형 넓이", _infer_square_triangle_metric),
    ElementaryFormulaRule("elementary_triangle_area", "geometry_metric", "삼각형 넓이", _infer_square_triangle_metric),
    ElementaryFormulaRule("elementary_arithmetic_sequence_next", "pattern_sequence", "등차 수열 다음 수", _infer_sequence_pattern),
    ElementaryFormulaRule("elementary_max_value", "statistics_extrema", "자료의 가장 큰 값", _infer_statistics_extrema),
    ElementaryFormulaRule("elementary_min_value", "statistics_extrema", "자료의 가장 작은 값", _infer_statistics_extrema),
    ElementaryFormulaRule("elementary_range_value", "statistics_extrema", "자료의 범위", _infer_statistics_extrema),
    ElementaryFormulaRule("elementary_average_values", "statistics_average", "자료의 평균", _infer_average),
)


_PREPARED_RULE_GROUPS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    (
        "number_sense",
        "number_relation",
        "수 감각/자리값",
        (
            "one_more", "one_less", "ten_more", "ten_less", "hundred_more", "hundred_less",
            "between_two_numbers", "count_between_numbers", "largest_number", "smallest_number",
            "ascending_order", "descending_order", "place_value_ones", "place_value_tens",
            "place_value_hundreds", "place_value_thousands", "expanded_form", "read_write_number",
            "odd_number", "even_number", "skip_count_2", "skip_count_5", "skip_count_10",
            "round_to_tens", "round_to_hundreds", "compare_sign",
        ),
    ),
    (
        "arithmetic",
        "direct_arithmetic",
        "사칙연산/빈칸식",
        (
            "add_two_numbers", "add_three_numbers", "subtract_two_numbers", "mixed_add_subtract",
            "multiply_two_numbers", "multiply_by_tens", "divide_exact", "divide_with_remainder",
            "blank_add_right", "blank_add_left", "blank_sub_right", "blank_sub_left",
            "blank_mul_right", "blank_mul_left", "blank_div_right", "blank_div_left",
            "vertical_addition", "vertical_subtraction", "vertical_multiplication", "vertical_division",
            "make_ten_addition", "make_ten_subtraction", "carry_addition", "borrow_subtraction",
            "calculation_flow", "same_result", "different_result", "operation_order",
        ),
    ),
    (
        "word_problem",
        "arithmetic_word",
        "문장제",
        (
            "join_change_addition", "join_change_subtraction", "compare_difference",
            "equal_share_division", "pack_multiplication", "times_as_many", "unit_rate_total",
            "remaining_after_use", "received_then_used", "buy_multiple_items", "share_leftover",
            "more_than_relation", "less_than_relation", "sum_and_difference", "age_chain",
            "rank_before_after", "money_change", "ticket_total", "book_pages_read",
            "distance_total", "distance_difference", "capacity_total", "weight_difference",
            "two_step_add_sub", "two_step_mul_add", "two_step_mul_sub", "inverse_operation",
        ),
    ),
    (
        "fraction_decimal",
        "fraction_arithmetic",
        "분수/소수",
        (
            "fraction_add_like_denominator", "fraction_sub_like_denominator",
            "fraction_add_unlike_denominator", "fraction_sub_unlike_denominator",
            "fraction_multiply_integer", "fraction_divide_integer", "fraction_of_quantity",
            "unit_fraction_count", "improper_to_mixed", "mixed_to_improper", "fraction_compare",
            "equivalent_fraction", "decimal_add", "decimal_subtract", "decimal_multiply_integer",
            "decimal_multiply_decimal", "decimal_divide_integer", "decimal_compare",
            "decimal_place_value", "fraction_to_decimal", "decimal_to_fraction", "percent_of_quantity",
            "ratio_equivalent", "ratio_total_parts",
        ),
    ),
    (
        "measurement",
        "measurement",
        "측정/시간/단위",
        (
            "cm_to_m_cm", "m_to_cm", "mm_to_cm", "kg_to_g", "g_to_kg_g", "l_to_ml",
            "ml_to_l_ml", "time_after_minutes", "time_before_minutes", "elapsed_time",
            "clock_read_hour", "clock_read_half", "money_sum", "money_change",
            "length_sum", "length_difference", "weight_sum", "weight_difference",
            "capacity_sum", "capacity_difference", "calendar_days", "temperature_difference",
        ),
    ),
    (
        "geometry",
        "geometry_metric",
        "도형",
        (
            "rectangle_area", "rectangle_perimeter", "square_area", "square_perimeter",
            "triangle_area", "parallelogram_area", "trapezoid_area", "circle_diameter",
            "circle_radius", "circle_circumference", "angle_sum_triangle",
            "angle_sum_quadrilateral", "angle_more_than", "angle_less_than", "right_angle_count",
            "polygon_sides", "polygon_vertices", "cube_edge_sum", "cuboid_edge_sum",
            "volume_cuboid", "surface_area_cuboid", "symmetry_count",
        ),
    ),
    (
        "pattern_statistics",
        "pattern_statistics",
        "규칙/자료/그래프",
        (
            "arithmetic_sequence_next", "arithmetic_sequence_blank", "decreasing_sequence_next",
            "repeating_pattern_next", "table_row_rule", "table_column_rule", "number_array_diagonal",
            "multiplication_table_blank", "addition_table_blank", "bar_graph_total",
            "bar_graph_difference", "pictograph_total", "pictograph_difference", "line_graph_change",
            "average_values", "max_value", "min_value", "range_value", "sum_values",
            "mode_value", "median_value", "category_count", "ratio_from_table", "percent_from_graph",
        ),
    ),
    (
        "ocr_repair",
        "ocr_repair",
        "초등 OCR 보정",
        (
            "plus_read_as_korean_vowel", "minus_read_as_dash_noise", "multiply_read_as_x",
            "divide_read_as_slash", "box_read_as_square", "blank_read_as_parentheses",
            "cm_read_as_07", "jang_read_as_48", "gae_read_as_74", "one_read_as_l",
            "zero_read_as_o", "seven_read_as_slash", "five_read_as_s", "ten_read_as_io",
            "fraction_bar_missing", "mixed_number_spacing", "decimal_point_missing",
            "comma_as_decimal", "question_number_glued", "unit_suffix_glued",
            "choice_number_noise", "table_digit_drop", "repeated_slash_digit",
            "korean_counter_noise",
        ),
    ),
)


def prepared_elementary_formula_rules() -> tuple[ElementaryPreparedFormulaRule, ...]:
    rules: list[ElementaryPreparedFormulaRule] = []
    for group_id, category, group_label, variants in _PREPARED_RULE_GROUPS:
        for variant in variants:
            rules.append(
                ElementaryPreparedFormulaRule(
                    rule_id=f"elementary_{group_id}_{variant}",
                    category=category,
                    description=f"{group_label}: {variant}",
                    extractor_family=group_id,
                )
            )
    return tuple(rules)


def infer_elementary_formula_candidates(text: str) -> list[ElementaryFormulaCandidate]:
    candidates: list[ElementaryFormulaCandidate] = []
    for rule in ELEMENTARY_FORMULA_RULES:
        for candidate in rule.extractor(text):
            if all(item.expression != candidate.expression for item in candidates):
                candidates.append(candidate)
    return sorted(candidates, key=lambda item: item.confidence, reverse=True)[:12]


def elementary_formula_catalog_summary() -> dict[str, object]:
    by_category: dict[str, int] = {}
    prepared_rules = prepared_elementary_formula_rules()
    for rule in prepared_rules:
        by_category[rule.category] = by_category.get(rule.category, 0) + 1
    return {
        "schema_version": "coco_elementary_formula_catalog.v1",
        "rule_count": len(prepared_rules),
        "extractor_family_count": len(ELEMENTARY_FORMULA_RULES),
        "by_category": by_category,
        "rules": [
            {
                "rule_id": rule.rule_id,
                "category": rule.category,
                "description": rule.description,
                "extractor_family": rule.extractor_family,
            }
            for rule in prepared_rules
        ],
    }
