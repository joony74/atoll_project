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


_NINE_UP_TO_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수만큼 ○를 그리세요. (1) 3, (2) 6",
        expression="answer_text=(1) ○ 3개, (2) ○ 6개",
        rule_id="grade1_numbers_to_9_round2_draw_count",
    ),
    2: ElementaryVisualTemplate(
        problem_text="1을 두 가지 방법으로 쓰세요.",
        expression="answer_text=하나, 일",
        rule_id="grade1_numbers_to_9_round2_read_one_two_ways",
    ),
    3: ElementaryVisualTemplate(
        problem_text="7과 8 중 더 큰 수에 ○표 하세요.",
        expression="answer=8",
        rule_id="grade1_numbers_to_9_round2_larger_number",
    ),
    4: ElementaryVisualTemplate(
        problem_text="4보다 작은 수를 찾아 모두 쓰세요.",
        expression="answer_text=1, 2, 3",
        rule_id="grade1_numbers_to_9_round2_numbers_less_than_four",
    ),
    5: ElementaryVisualTemplate(
        problem_text="수를 세어 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer=6",
        rule_id="grade1_numbers_to_9_round2_count_six_candies",
    ),
    6: ElementaryVisualTemplate(
        problem_text="3만큼 묶을 때, 묶지 않은 것의 수를 세어 보세요.",
        expression="answer=6",
        rule_id="grade1_numbers_to_9_round2_ungrouped_after_three",
    ),
    7: ElementaryVisualTemplate(
        problem_text="순서에 맞게 선으로 이어 보세요.",
        expression="answer_text=첫째-나, 셋째-가, 넷째-다, 둘째-라, 다섯째-마",
        rule_id="grade1_numbers_to_9_round2_ordinal_match_lines",
    ),
    8: ElementaryVisualTemplate(
        problem_text="순서에 맞게 알맞은 말을 써넣으세요. 다섯째, □, 일곱째, □",
        expression="answer_text=빈칸: 여섯째, 여덟째",
        rule_id="grade1_numbers_to_9_round2_ordinal_words_blanks",
    ),
    9: ElementaryVisualTemplate(
        problem_text="오른쪽 그림에서 위에서 여섯째에 있는 과일은 어느 것입니까?",
        expression="answer_text=수박",
        rule_id="grade1_numbers_to_9_round2_sixth_fruit_from_top",
    ),
}


_NINE_UP_TO_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="오른쪽에서 두 번째에 있는 사탕에 ○표 하세요.",
        expression="answer_text=오른쪽에서 두 번째 사탕",
        rule_id="grade1_numbers_to_9_round2_ordinal_from_right",
    ),
    2: ElementaryVisualTemplate(
        problem_text="순서에 맞게 빈칸에 알맞은 수를 쓰세요. 3, □, 5, 6, 7, □",
        expression="answer_text=빈칸: 4, 8",
        rule_id="grade1_numbers_to_9_round2_order_blanks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="순서를 거꾸로 하여 빈칸에 알맞은 수를 써 넣으세요.",
        expression="answer_text=빈칸: 9, 6, 5, 3, 2",
        rule_id="grade1_numbers_to_9_round2_reverse_order_blanks",
    ),
    4: ElementaryVisualTemplate(
        problem_text="□보다 1만큼 더 큰 수는 7입니다. □ 안에 알맞은 수를 써 넣으세요.",
        expression="answer=6",
        rule_id="grade1_numbers_to_9_round2_one_less_from_sentence",
    ),
    5: ElementaryVisualTemplate(
        problem_text="수박의 수보다 1 큰 수를 써 보세요.",
        expression="answer=7",
        rule_id="grade1_numbers_to_9_round2_one_more_watermelon_count",
    ),
    6: ElementaryVisualTemplate(
        problem_text="빈칸에 1 작은 수와 1 큰 수를 써 넣으세요. 가운데 수는 2입니다.",
        expression="answer_text=빈칸: 1, 3",
        rule_id="grade1_numbers_to_9_round2_neighbors_of_two",
    ),
    7: ElementaryVisualTemplate(
        problem_text="2, 9, 4를 큰 수부터 차례대로 써 보세요.",
        expression="answer_text=9, 4, 2",
        rule_id="grade1_numbers_to_9_round2_descending_order",
    ),
    8: ElementaryVisualTemplate(
        problem_text="3보다 크고 7보다 작은 수는 모두 몇 개입니까?",
        expression="answer_text=3개",
        rule_id="grade1_numbers_to_9_round2_count_between_three_and_seven",
    ),
    9: ElementaryVisualTemplate(
        problem_text="나머지 둘과 다른 수를 말한 친구는 누구일까요?",
        expression="answer_text=민수",
        rule_id="grade1_numbers_to_9_round2_different_number_speaker",
    ),
    10: ElementaryVisualTemplate(
        problem_text="구슬을 가장 적게 가지고 있는 친구는 누구일까요?",
        expression="answer_text=나영",
        rule_id="grade1_numbers_to_9_round2_least_marble_owner",
    ),
    11: ElementaryVisualTemplate(
        problem_text="다영이는 6살입니다. 진희는 다영이보다 1살 더 많고, 세희는 진희보다 1살 더 많습니다. 세희는 몇 살일까요?",
        expression="answer_text=8살",
        rule_id="grade1_numbers_to_9_round2_age_chain",
    ),
}


_NINE_UP_TO_3ROUND_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수만큼 ○를 그리세요. 5",
        expression="answer_text=○ 5개",
        rule_id="grade1_numbers_to_9_round3_draw_count",
    ),
    2: ElementaryVisualTemplate(
        problem_text="수를 세어 ○ 안에 알맞은 수를 쓰고 읽어 보세요.",
        expression="answer_text=5 / 다섯, 오",
        rule_id="grade1_numbers_to_9_round3_count_five_read_two_ways",
    ),
    3: ElementaryVisualTemplate(
        problem_text="6과 7 중 더 큰 수에 ○표 하세요.",
        expression="answer=7",
        rule_id="grade1_numbers_to_9_round3_larger_number",
    ),
    4: ElementaryVisualTemplate(
        problem_text="6보다 큰 수를 찾아 모두 쓰세요.",
        expression="answer_text=7, 8, 9",
        rule_id="grade1_numbers_to_9_round3_numbers_greater_than_six",
    ),
    5: ElementaryVisualTemplate(
        problem_text="수를 세어 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer=8",
        rule_id="grade1_numbers_to_9_round3_count_eight_boats",
    ),
    6: ElementaryVisualTemplate(
        problem_text="2만큼 묶을 때, 묶지 않은 것의 수를 세어 보세요.",
        expression="answer=7",
        rule_id="grade1_numbers_to_9_round3_ungrouped_after_two",
    ),
    7: ElementaryVisualTemplate(
        problem_text="순서에 맞게 선으로 이어 보세요.",
        expression="answer_text=첫째-다, 둘째-나, 셋째-라, 넷째-마, 다섯째-가",
        rule_id="grade1_numbers_to_9_round3_ordinal_match_lines",
    ),
    8: ElementaryVisualTemplate(
        problem_text="여섯째에 색칠해 보세요.",
        expression="answer_text=왼쪽에서 여섯째 꽃",
        rule_id="grade1_numbers_to_9_round3_color_sixth_flower",
    ),
    9: ElementaryVisualTemplate(
        problem_text="여덟째는 어떤 수로 나타내는지 쓰세요.",
        expression="answer=8",
        rule_id="grade1_numbers_to_9_round3_eighth_as_number",
    ),
    10: ElementaryVisualTemplate(
        problem_text="순서에 맞게 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 3, 6",
        rule_id="grade1_numbers_to_9_round3_order_blanks_page1",
    ),
}


_NINE_UP_TO_3ROUND_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="순서를 거꾸로 하여 빈칸에 알맞은 수를 써 넣으세요.",
        expression="answer_text=빈칸: 7, 6, 4, 1",
        rule_id="grade1_numbers_to_9_round3_reverse_order_blanks",
    ),
    2: ElementaryVisualTemplate(
        problem_text="□보다 1만큼 더 작은 수는 7입니다. □ 안에 알맞은 수를 써 넣으세요.",
        expression="answer=8",
        rule_id="grade1_numbers_to_9_round3_one_more_from_sentence",
    ),
    3: ElementaryVisualTemplate(
        problem_text="오이의 수보다 1 큰 수를 써 보세요.",
        expression="answer=6",
        rule_id="grade1_numbers_to_9_round3_one_more_cucumber_count",
    ),
    4: ElementaryVisualTemplate(
        problem_text="빈칸에 1 작은 수와 1 큰 수를 써 넣으세요. 가운데 수는 5입니다.",
        expression="answer_text=빈칸: 4, 6",
        rule_id="grade1_numbers_to_9_round3_neighbors_of_five",
    ),
    5: ElementaryVisualTemplate(
        problem_text="수 카드를 작은 수부터 차례대로 늘어놓을 때 왼쪽에서 둘째에 놓이는 수를 쓰세요.",
        expression="answer=1",
        rule_id="grade1_numbers_to_9_round3_second_after_ascending_sort",
    ),
    6: ElementaryVisualTemplate(
        problem_text="4보다 크고 8보다 작은 수는 모두 몇 개입니까?",
        expression="answer_text=3개",
        rule_id="grade1_numbers_to_9_round3_count_between_four_and_eight",
    ),
    7: ElementaryVisualTemplate(
        problem_text="민서는 6살입니다. 승우는 민서보다 1살 더 적습니다. 승우의 나이는 몇 살입니까?",
        expression="answer_text=5살",
        rule_id="grade1_numbers_to_9_round3_one_less_age",
    ),
    8: ElementaryVisualTemplate(
        problem_text="밤을 선영이는 4개 주웠고, 은희는 선영이보다 1개 더 많이 주웠습니다. 은희가 주운 밤의 수를 쓰세요.",
        expression="answer_text=5개",
        rule_id="grade1_numbers_to_9_round3_one_more_word_problem",
    ),
    9: ElementaryVisualTemplate(
        problem_text="9명의 친구가 달리기 시합을 하였습니다. 연수는 결승점에 뒤에서 둘째로 들어왔습니다. 연수는 앞에서 몇째로 들어왔나요?",
        expression="answer_text=여덟째",
        rule_id="grade1_numbers_to_9_round3_ordinal_from_back",
    ),
    10: ElementaryVisualTemplate(
        problem_text="수학 문제집을 지수는 5쪽 풀었고, 영민이는 6쪽 풀었습니다. 수학 문제집을 더 적게 푼 친구는 누구일까요?",
        expression="answer_text=지수",
        rule_id="grade1_numbers_to_9_round3_less_pages_word_problem",
    ),
}


_GRADE3_MULTIPLICATION_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="70×80, 90×60, 60×90 중 계산 결과가 다른 하나를 찾으세요.",
        expression="answer_text=가",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round2_different_product",
    ),
    2: ElementaryVisualTemplate(
        problem_text="638×4를 나타내는 수가 다른 하나를 고르세요.",
        expression="answer_text=④",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round2_different_representation",
    ),
    3: ElementaryVisualTemplate(
        problem_text="계산 결과가 같은 것끼리 선으로 이어 보세요. (1) 40×30, (2) 60×40, (3) 80×20",
        expression="answer_text=(1)-나, (2)-다, (3)-가",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round2_match_products",
    ),
    4: ElementaryVisualTemplate(
        problem_text="삼각형 안의 두 수 203과 2의 곱을 구하세요.",
        expression="answer=406",
        topic="geometry",
        rule_id="grade3_2_multiplication_round2_triangle_numbers_product",
    ),
    5: ElementaryVisualTemplate(
        problem_text="초콜릿이 한 봉지에 122개씩 들어 있습니다. 4봉지에 들어 있는 초콜릿은 모두 몇 개입니까?",
        expression="answer_text=488 개",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round2_chocolates_total",
    ),
    6: ElementaryVisualTemplate(
        problem_text="세로셈 □□2×4=80□에서 □ 안에 알맞은 수를 쓰세요.",
        expression="answer_text=2, 0, 8",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round2_vertical_202_times_4_blanks",
    ),
}


_GRADE3_2_MULTIPLICATION_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="43×25와 92×38을 계산하세요.",
        expression="answer_text=⑴ 1075 ⑵ 3496",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round2_vertical_products",
    ),
    2: ElementaryVisualTemplate(
        problem_text="3씩 3묶음인 수와 10이 2개, 1이 7개인 수의 곱을 구하세요.",
        expression="answer=243",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round2_place_value_product",
    ),
    3: ElementaryVisualTemplate(
        problem_text="24×50=24×□×10=□×10=□에서 □ 안에 알맞은 수를 쓰세요.",
        expression="answer_text=5, 120, 1200",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round2_24_times_50_decomposition",
    ),
    4: ElementaryVisualTemplate(
        problem_text="731×2와 73×21, 52×17과 28×31의 곱을 비교하세요.",
        expression="answer_text=⑴ < ⑵ >",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round2_compare_products",
    ),
    5: ElementaryVisualTemplate(
        problem_text="사탕을 9개씩 194명에게 나누어 주고 4개가 남았을 때 처음 사탕 수를 구하세요.",
        expression="answer_text=1750 개",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round2_candies_initial_total",
    ),
    6: ElementaryVisualTemplate(
        problem_text="637×4 > □에 들어갈 수 있는 자연수 중 가장 큰 수를 구하세요.",
        expression="answer=2547",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round2_largest_natural_under_product",
    ),
    7: ElementaryVisualTemplate(
        problem_text="51×□0 < 30×70에 들어갈 수 있는 자연수 중 가장 큰 수를 구하세요.",
        expression="answer=4",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round2_largest_digit_inequality",
    ),
    8: ElementaryVisualTemplate(
        problem_text="길이 124 cm 색 테이프 9장을 15 cm씩 겹쳐 이어 붙인 전체 길이를 구하세요.",
        expression="answer_text=996 cm",
        topic="measurement",
        rule_id="grade3_2_multiplication_round2_tape_overlap_total_length",
    ),
}


_GRADE3_2_MULTIPLICATION_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="1분은 60초입니다. 한 시간은 몇 초인지 구하세요.",
        expression="answer_text=3600 초",
        topic="measurement",
        rule_id="grade3_2_multiplication_round2_seconds_in_hour",
    ),
    2: ElementaryVisualTemplate(
        problem_text="파란 색종이 45장씩 40묶음과 노란 색종이 1750장을 비교하세요.",
        expression="answer_text=파란 색종이, 50 장",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round2_colored_paper_difference",
    ),
    3: ElementaryVisualTemplate(
        problem_text="철사를 7 cm씩 자른 93도막과 9 cm씩 자른 74도막 중 어느 것이 몇 cm 더 긴지 구하세요.",
        expression="answer_text=9 cm씩 자른 철사, 15 cm",
        topic="measurement",
        rule_id="grade3_2_multiplication_round2_wire_length_difference",
    ),
    4: ElementaryVisualTemplate(
        problem_text="하루에 자동차를 56대 생산하는 공장이 3주 동안 쉬는 날 없이 생산한 자동차 수를 구하세요.",
        expression="answer_text=1176 대",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round2_cars_three_weeks",
    ),
    5: ElementaryVisualTemplate(
        problem_text="어떤 수에 14를 곱해야 하는데 14를 빼었더니 34가 되었습니다. 바르게 계산한 값을 구하세요.",
        expression="answer=672",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round2_wrong_subtract_instead_multiply",
    ),
    6: ElementaryVisualTemplate(
        problem_text="숫자 카드 3, 5, 6, 8로 가장 큰 두 자리 수와 가장 작은 두 자리 수의 곱을 구하세요.",
        expression="answer=3010",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round2_largest_smallest_two_digit_product",
    ),
}


_GRADE3_2_MULTIPLICATION_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="10이 2개인 수와 10이 9개인 수의 곱을 구하세요.",
        expression="answer=1800",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round3_tens_count_product",
    ),
    2: ElementaryVisualTemplate(
        problem_text="330×2, 210×3, 110×6 중 계산 결과가 나머지와 다른 것을 찾으세요.",
        expression="answer_text=나",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round3_find_different_product",
    ),
    3: ElementaryVisualTemplate(
        problem_text="146×3, 236×4, 234×3의 계산 결과를 찾아 이어 보세요.",
        expression="answer_text=(1)-다, (2)-나, (3)-가",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round3_match_products",
    ),
    4: ElementaryVisualTemplate(
        problem_text="1개에 230원인 지우개 3개와 2개에 120원인 자 4개의 값은 모두 얼마입니까?",
        expression="answer_text=930 원",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round3_eraser_ruler_total_price",
    ),
    5: ElementaryVisualTemplate(
        problem_text="4□2×□=824가 되도록 □ 안에 알맞은 수를 쓰세요.",
        expression="answer_text=1, 2",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round3_vertical_412_times_2_blanks",
    ),
    6: ElementaryVisualTemplate(
        problem_text="83×50의 잘못된 계산을 찾아 바르게 계산하세요.",
        expression="answer=4150",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round3_correct_83_times_50",
    ),
}


_GRADE3_2_MULTIPLICATION_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="27×60과 36×30의 두 곱의 합을 구하세요.",
        expression="answer=2700",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round3_sum_two_products",
    ),
    2: ElementaryVisualTemplate(
        problem_text="6□×30=□□60이 되도록 □ 안에 알맞은 수를 쓰세요.",
        expression="answer_text=2, 1, 8",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round3_62_times_30_blanks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="1부터 9까지의 수 중 158×□<800에 들어갈 수 있는 가장 큰 수를 구하세요.",
        expression="answer=5",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round3_largest_digit_under_800",
    ),
    4: ElementaryVisualTemplate(
        problem_text="52에서 ×28로 가는 결과와, 52에서 ×4 후 ×7로 가는 결과를 구하세요.",
        expression="answer_text=1456, 208",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round3_operation_path_blanks",
    ),
    5: ElementaryVisualTemplate(
        problem_text="4×17=★, ★×68=▲일 때 ▲에 알맞은 수를 구하세요.",
        expression="answer=4624",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round3_star_triangle_product",
    ),
    6: ElementaryVisualTemplate(
        problem_text="□>83×69에 들어갈 수 있는 수를 고르세요.",
        expression="answer_text=④, ⑤",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round3_numbers_greater_than_product",
    ),
    7: ElementaryVisualTemplate(
        problem_text="원 모양 호수 둘레에 4 m 간격으로 147그루의 나무가 심어져 있을 때 호수의 둘레를 구하세요.",
        expression="answer_text=588 m",
        topic="measurement",
        rule_id="grade3_2_multiplication_round3_circle_trees_circumference",
    ),
}


_GRADE3_2_MULTIPLICATION_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="218에 어떤 수를 곱해야 하는데 잘못하여 그 수를 더했더니 225가 되었습니다. 바르게 계산한 값을 구하세요.",
        expression="answer=1526",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round3_wrong_add_instead_multiply",
    ),
    2: ElementaryVisualTemplate(
        problem_text="750원짜리 공책 5개와 90원짜리 클립 14개를 사고 5000원을 냈을 때 더 내야 하는 돈을 구하세요.",
        expression="answer_text=10 원",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round3_stationery_shortfall",
    ),
    3: ElementaryVisualTemplate(
        problem_text="파란 색종이는 한 묶음에 5장씩 63묶음, 빨간 색종이는 한 묶음에 7장씩 52묶음입니다. 어느 색종이가 몇 장 더 많은지 구하세요.",
        expression="answer_text=빨간 색종이, 49 장",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round3_colored_paper_more",
    ),
    4: ElementaryVisualTemplate(
        problem_text="한 변이 18 cm인 정사각형 5개를 이어 붙인 도형의 굵은 선 길이를 구하세요.",
        expression="answer_text=216 cm",
        topic="measurement",
        rule_id="grade3_2_multiplication_round3_polyomino_perimeter",
    ),
    5: ElementaryVisualTemplate(
        problem_text="하루에 47쪽씩 4주 동안 책을 읽었을 때 모두 몇 쪽을 읽었는지 구하세요.",
        expression="answer_text=1316 쪽",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round3_pages_read_four_weeks",
    ),
    6: ElementaryVisualTemplate(
        problem_text="한 봉지에 15개씩 든 초콜릿이 모두 330개일 때 몇 봉지를 샀는지 구하세요.",
        expression="answer_text=22 봉지",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round3_chocolate_bags",
    ),
    7: ElementaryVisualTemplate(
        problem_text="45권씩 묶인 공책 30묶음을 25권씩 다시 묶어 47묶음을 팔았을 때 남은 공책 수를 구하세요.",
        expression="answer_text=175 권",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round3_notebooks_remaining",
    ),
}


_GRADE3_2_DIVISION_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림을 보고 60÷3의 몫을 구하세요.",
        expression="answer=20",
        topic="arithmetic",
        rule_id="grade3_2_division_round1_60_divided_by_3_picture",
    ),
    2: ElementaryVisualTemplate(
        problem_text="98÷7의 몫을 구하세요.",
        expression="answer=14",
        topic="arithmetic",
        rule_id="grade3_2_division_round1_98_divided_by_7",
    ),
    3: ElementaryVisualTemplate(
        problem_text="60÷3, 90÷6, 70÷5의 몫이 큰 것부터 기호를 쓰세요.",
        expression="answer_text=가, 나, 다",
        topic="arithmetic",
        rule_id="grade3_2_division_round1_order_quotients",
    ),
    4: ElementaryVisualTemplate(
        problem_text="70 cm 막대를 똑같이 7칸으로 나누었을 때 한 칸의 길이를 구하세요.",
        expression="answer_text=10 cm",
        topic="measurement",
        rule_id="grade3_2_division_round1_70cm_equal_parts",
    ),
    5: ElementaryVisualTemplate(
        problem_text="□÷8에서 나머지가 될 수 없는 수를 고르세요.",
        expression="answer_text=①",
        topic="arithmetic",
        rule_id="grade3_2_division_round1_impossible_remainder_divide_by_8",
    ),
    6: ElementaryVisualTemplate(
        problem_text="1부터 9까지의 수 중 21을 나누어떨어지게 하는 수를 모두 구하세요.",
        expression="answer_text=1, 3, 7",
        topic="arithmetic",
        rule_id="grade3_2_division_round1_divisors_of_21",
    ),
    7: ElementaryVisualTemplate(
        problem_text="84÷6, 54÷3, 85÷5 중 몫이 18인 것을 찾으세요.",
        expression="answer_text=나",
        topic="arithmetic",
        rule_id="grade3_2_division_round1_quotient_18",
    ),
    8: ElementaryVisualTemplate(
        problem_text="20보다 크고 40보다 작은 두 자리 수 중에서 5로 나누어떨어지는 수를 모두 고르세요.",
        expression="answer_text=①, ③, ⑤",
        topic="arithmetic",
        rule_id="grade3_2_division_round1_multiples_of_5_between_20_40",
    ),
}


_GRADE3_2_DIVISION_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="56÷4와 37÷5 중 나누어떨어지는 나눗셈에 표시하세요.",
        expression="answer_text=56÷4",
        topic="arithmetic",
        rule_id="grade3_2_division_round1_exact_division",
    ),
    2: ElementaryVisualTemplate(
        problem_text="55÷6, 59÷6, 58÷6, 57÷6, 56÷6 중 나머지가 가장 큰 것을 고르세요.",
        expression="answer_text=②",
        topic="arithmetic",
        rule_id="grade3_2_division_round1_largest_remainder",
    ),
    3: ElementaryVisualTemplate(
        problem_text="432÷6의 세로셈 빈칸을 채우세요.",
        expression="answer_text=7, 2, 4, 2, 1, 2, 1, 2, 0",
        topic="arithmetic",
        rule_id="grade3_2_division_round1_432_divided_by_6_vertical",
    ),
    4: ElementaryVisualTemplate(
        problem_text="1부터 9까지의 자연수 중 6×□<48÷2에 들어갈 수 있는 수의 개수를 구하세요.",
        expression="answer_text=3 개",
        topic="arithmetic",
        rule_id="grade3_2_division_round1_inequality_count",
    ),
    5: ElementaryVisualTemplate(
        problem_text="네 변의 길이의 합이 56 cm인 정사각형의 한 변의 길이를 구하세요.",
        expression="answer_text=14 cm",
        topic="measurement",
        rule_id="grade3_2_division_round1_square_side_from_perimeter",
    ),
    6: ElementaryVisualTemplate(
        problem_text="양과 오리의 다리 수가 모두 210개이고 오리가 63마리일 때 양의 수를 구하세요.",
        expression="answer_text=21 마리",
        topic="arithmetic",
        rule_id="grade3_2_division_round1_sheep_duck_legs",
    ),
    7: ElementaryVisualTemplate(
        problem_text="사탕 60개를 6개의 봉지에 똑같이 나누어 담을 때 한 봉지의 사탕 수를 구하세요.",
        expression="answer_text=10 개",
        topic="arithmetic",
        rule_id="grade3_2_division_round1_candies_per_bag",
    ),
    8: ElementaryVisualTemplate(
        problem_text="어떤 수에 4를 곱했더니 96이 되었습니다. 어떤 수를 6으로 나눈 몫을 구하세요.",
        expression="answer=4",
        topic="arithmetic",
        rule_id="grade3_2_division_round1_unknown_times_4_then_divide_6",
    ),
}


_GRADE3_2_DIVISION_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수 카드 4, 5, 8 중 두 장으로 가장 큰 두 자리 수를 만들고, 남은 수로 나눈 몫과 나머지를 구하세요.",
        expression="answer_text=몫 21, 나머지 1",
        topic="arithmetic",
        rule_id="grade3_2_division_round1_largest_two_digit_divide_remainder",
    ),
    2: ElementaryVisualTemplate(
        problem_text="빵 42개를 한 봉지에 5개씩 넣어 팔 때 팔 수 있는 봉지 수와 남는 빵 수를 구하세요.",
        expression="answer_text=8 봉지, 2 개",
        topic="arithmetic",
        rule_id="grade3_2_division_round1_bread_bags_remainder",
    ),
    3: ElementaryVisualTemplate(
        problem_text="사탕 79개를 9사람에게 똑같이 나누어 주려면 적어도 몇 개가 더 있어야 하는지 구하세요.",
        expression="answer_text=2 개",
        topic="arithmetic",
        rule_id="grade3_2_division_round1_candies_needed_for_equal_share",
    ),
    4: ElementaryVisualTemplate(
        problem_text="길이 56 m인 도로 한쪽에 처음부터 끝까지 4 m 간격으로 가로수를 심을 때 필요한 가로수 수를 구하세요.",
        expression="answer_text=15 그루",
        topic="measurement",
        rule_id="grade3_2_division_round1_trees_along_road",
    ),
}


_GRADE3_2_DIVISION_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="30÷3과 60÷6의 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=10, 10",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_related_quotients",
    ),
    2: ElementaryVisualTemplate(
        problem_text="60÷5의 잘못된 계산을 찾아 바르게 계산하세요.",
        expression="answer=12",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_correct_60_divided_by_5",
    ),
    3: ElementaryVisualTemplate(
        problem_text="60÷2, 80÷8, 60÷6, 50÷5 중 나눗셈의 몫이 다른 것을 찾으세요.",
        expression="answer_text=ㄱ",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_different_quotient",
    ),
    4: ElementaryVisualTemplate(
        problem_text="15×4=★, ★÷3=▲일 때 ▲에 알맞은 수를 구하세요.",
        expression="answer=20",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_star_triangle_quotient",
    ),
    5: ElementaryVisualTemplate(
        problem_text="□÷6에서 나머지가 될 수 없는 수를 고르세요.",
        expression="answer_text=⑤",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_impossible_remainder_divide_by_6",
    ),
    6: ElementaryVisualTemplate(
        problem_text="75÷3의 세로셈 빈칸을 채우세요.",
        expression="answer_text=3, 5, 6",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_75_divided_by_3_vertical",
    ),
    7: ElementaryVisualTemplate(
        problem_text="96÷8, 92÷4, 88÷4 중 큰 수를 작은 수로 나눈 몫이 23인 것을 찾으세요.",
        expression="answer_text=나",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_quotient_23",
    ),
    8: ElementaryVisualTemplate(
        problem_text="30보다 크고 50보다 작은 두 자리 수 중에서 7로 나누어떨어지는 수의 개수를 구하세요.",
        expression="answer_text=3 개",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_multiples_of_7_between_30_50",
    ),
}


_GRADE3_2_DIVISION_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="42÷7, 39÷5, 19÷2, 56÷9, 39÷6 중 나머지가 가장 큰 것을 고르세요.",
        expression="answer_text=②",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_largest_remainder",
    ),
    2: ElementaryVisualTemplate(
        problem_text="74÷4와 78÷3 중 나누어떨어지는 나눗셈에 표시하세요.",
        expression="answer_text=78÷3",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_exact_division",
    ),
    3: ElementaryVisualTemplate(
        problem_text="1부터 9까지의 자연수 중 3×□<84÷4에 들어갈 수 있는 수의 개수를 구하세요.",
        expression="answer_text=6 개",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_inequality_count",
    ),
    4: ElementaryVisualTemplate(
        problem_text="66÷6, 36÷3, 26÷2의 몫과 관계있는 것끼리 이으세요.",
        expression="answer_text=(1)-①, (2)-②, (3)-③",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_match_quotients",
    ),
    5: ElementaryVisualTemplate(
        problem_text="717÷7의 세로셈 빈칸을 채우세요.",
        expression="answer_text=1, 0, 2, 7, 1, 7, 1, 4, 3",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_717_divided_by_7_vertical",
    ),
    6: ElementaryVisualTemplate(
        problem_text="세 변의 길이의 합이 66 cm인 정삼각형의 한 변의 길이를 구하세요.",
        expression="answer_text=22 cm",
        topic="measurement",
        rule_id="grade3_2_division_round2_equilateral_side_from_perimeter",
    ),
    7: ElementaryVisualTemplate(
        problem_text="말과 닭의 다리 수가 모두 214개이고 말이 33마리일 때 닭의 수를 구하세요.",
        expression="answer_text=41 마리",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_horse_chicken_legs",
    ),
    8: ElementaryVisualTemplate(
        problem_text="어떤 수에 3을 곱했더니 84가 되었습니다. 어떤 수를 4로 나눈 몫을 구하세요.",
        expression="answer=7",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_unknown_times_3_then_divide_4",
    ),
}


_GRADE3_2_DIVISION_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="색종이 38장을 한 사람에게 7장씩 나누어 줄 때 몇 명이 가지고 몇 장이 남는지 구하세요.",
        expression="answer_text=5 명, 3 장",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_colored_paper_share_remainder",
    ),
    2: ElementaryVisualTemplate(
        problem_text="숫자 카드 4, 6, 7을 한 번씩 모두 사용하여 몫이 가장 큰 나눗셈식을 만드세요.",
        expression="answer_text=76÷4=19",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_largest_quotient_number_cards",
    ),
    3: ElementaryVisualTemplate(
        problem_text="귤 59개를 여섯 명에게 똑같이 나누어 주려면 적어도 몇 개가 더 있어야 하는지 구하세요.",
        expression="answer_text=1 개",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_tangerines_needed_for_equal_share",
    ),
    4: ElementaryVisualTemplate(
        problem_text="53보다 크고 83보다 작은 수 중 6으로 나누었을 때 나머지가 5인 수의 개수를 구하세요.",
        expression="answer_text=4 개",
        topic="arithmetic",
        rule_id="grade3_2_division_round2_remainder_5_count",
    ),
}


_GRADE3_2_DIVISION_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림을 보고 90÷3의 몫을 구하세요.",
        expression="answer=30",
        topic="arithmetic",
        rule_id="grade3_2_division_round3_90_divided_by_3_picture",
    ),
    2: ElementaryVisualTemplate(
        problem_text="78÷6의 몫을 구하세요.",
        expression="answer=13",
        topic="arithmetic",
        rule_id="grade3_2_division_round3_78_divided_by_6",
    ),
    3: ElementaryVisualTemplate(
        problem_text="16×5=★, ★÷2=▲일 때 ▲에 알맞은 수를 구하세요.",
        expression="answer=40",
        topic="arithmetic",
        rule_id="grade3_2_division_round3_star_triangle_quotient",
    ),
    4: ElementaryVisualTemplate(
        problem_text="30÷2의 잘못된 계산을 찾아 바르게 고쳐 계산하세요.",
        expression="answer=15",
        topic="arithmetic",
        rule_id="grade3_2_division_round3_correct_30_divided_by_2",
    ),
    5: ElementaryVisualTemplate(
        problem_text="80÷5, 30÷2, 90÷5의 몫이 큰 것부터 차례로 기호를 쓰세요.",
        expression="answer_text=다, 가, 나",
        topic="arithmetic",
        rule_id="grade3_2_division_round3_order_quotients",
    ),
    6: ElementaryVisualTemplate(
        problem_text="어떤 수를 6으로 나누었을 때 나머지가 될 수 없는 수를 찾으세요.",
        expression="answer_text=6",
        topic="arithmetic",
        rule_id="grade3_2_division_round3_impossible_remainder_divide_by_6",
    ),
    7: ElementaryVisualTemplate(
        problem_text="93÷3, 99÷9, 64÷2의 몫과 관계있는 것끼리 이으세요.",
        expression="answer_text=(1)-②, (2)-①, (3)-③",
        topic="arithmetic",
        rule_id="grade3_2_division_round3_match_quotients",
    ),
    8: ElementaryVisualTemplate(
        problem_text="52÷2의 세로셈 빈칸을 채우세요.",
        expression="answer_text=2, 6, 4",
        topic="arithmetic",
        rule_id="grade3_2_division_round3_52_divided_by_2_vertical",
    ),
}


_GRADE3_2_DIVISION_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="75÷3, 52÷2, 96÷4 중 큰 수를 작은 수로 나눈 몫이 24인 것을 찾으세요.",
        expression="answer_text=다",
        topic="arithmetic",
        rule_id="grade3_2_division_round3_quotient_24",
    ),
    2: ElementaryVisualTemplate(
        problem_text="20보다 크고 40보다 작은 두 자리 수 중에서 6으로 나누어떨어지는 수를 모두 고르세요.",
        expression="answer_text=②, ③, ④",
        topic="arithmetic",
        rule_id="grade3_2_division_round3_multiples_of_6_between_20_40",
    ),
    3: ElementaryVisualTemplate(
        problem_text="어떤 수를 8로 나누었더니 몫이 11이고 나머지가 7이었습니다. 어떤 수를 구하세요.",
        expression="answer=95",
        topic="arithmetic",
        rule_id="grade3_2_division_round3_number_from_quotient_remainder",
    ),
    4: ElementaryVisualTemplate(
        problem_text="사탕 10개씩 6봉지를 3사람에게 똑같이 나누어 줄 때 한 사람에게 몇 개씩 주어야 하는지 구하세요.",
        expression="answer_text=20 개",
        topic="arithmetic",
        rule_id="grade3_2_division_round3_candies_per_person",
    ),
    5: ElementaryVisualTemplate(
        problem_text="네 변의 길이의 합이 68 cm인 정사각형의 한 변의 길이를 구하세요.",
        expression="answer_text=17 cm",
        topic="measurement",
        rule_id="grade3_2_division_round3_square_side_from_perimeter",
    ),
    6: ElementaryVisualTemplate(
        problem_text="어떤 수를 6으로 나누어야 할 것을 잘못하여 6을 더했더니 89가 되었습니다. 바르게 계산한 몫과 나머지를 구하세요.",
        expression="answer_text=몫 13, 나머지 5",
        topic="arithmetic",
        rule_id="grade3_2_division_round3_wrong_add_instead_divide",
    ),
    7: ElementaryVisualTemplate(
        problem_text="초콜릿 80개를 한 사람에게 6개씩 주면 몇 명에게 줄 수 있고 몇 개가 남는지 구하세요.",
        expression="answer_text=13 명, 2 개",
        topic="arithmetic",
        rule_id="grade3_2_division_round3_chocolate_share_remainder",
    ),
    8: ElementaryVisualTemplate(
        problem_text="수 카드 3, 5, 8을 한 번씩만 사용하여 몫이 가장 큰 두 자리 수 나누기 한 자리 수를 만들고 몫과 나머지를 구하세요.",
        expression="answer_text=85÷3=28 ... 1",
        topic="arithmetic",
        rule_id="grade3_2_division_round3_largest_quotient_number_cards",
    ),
}


_GRADE3_2_DIVISION_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="길이 60 m인 산책로 양쪽에 5 m 간격으로 시작 지점부터 끝까지 나무를 심을 때 필요한 나무 수를 구하세요.",
        expression="answer_text=26 그루",
        topic="measurement",
        rule_id="grade3_2_division_round3_trees_both_sides_path",
    ),
    2: ElementaryVisualTemplate(
        problem_text="볼펜 77자루를 여섯 명에게 똑같이 나누어 주려면 적어도 몇 자루가 더 있어야 하는지 구하세요.",
        expression="answer_text=1 자루",
        topic="arithmetic",
        rule_id="grade3_2_division_round3_pens_needed_for_equal_share",
    ),
    3: ElementaryVisualTemplate(
        problem_text="㉠◆㉡=(㉠÷㉡)+(㉠÷4)일 때 80◆5의 값을 구하세요.",
        expression="answer=36",
        topic="arithmetic",
        rule_id="grade3_2_division_round3_custom_operation",
    ),
    4: ElementaryVisualTemplate(
        problem_text="40보다 크고 60보다 작으며, 4로 나누면 나머지가 3이고 5로 나누어떨어지는 수를 구하세요.",
        expression="answer=55",
        topic="arithmetic",
        rule_id="grade3_2_division_round3_remainder_and_multiple_condition",
    ),
}


_GRADE3_2_CIRCLE_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림에서 원의 반지름을 구하세요.",
        expression="answer_text=7 cm",
        topic="geometry",
        rule_id="grade3_2_circle_round1_radius_from_picture",
    ),
    2: ElementaryVisualTemplate(
        problem_text="컴퍼스를 이용하여 주어진 원과 크기가 같은 원을 그리세요.",
        expression="answer_text=그리기 문제",
        topic="geometry",
        rule_id="grade3_2_circle_round1_draw_same_size_circle",
    ),
    3: ElementaryVisualTemplate(
        problem_text="누름 못과 띠 종이를 이용하여 가장 작은 원을 그리려면 어느 곳에 연필을 넣어야 하는지 고르세요.",
        expression="answer_text=㉠",
        topic="geometry",
        rule_id="grade3_2_circle_round1_smallest_circle_hole",
    ),
    4: ElementaryVisualTemplate(
        problem_text="컴퍼스를 이용하여 원 모양 피자 조각의 원래 피자 모양을 그리세요.",
        expression="answer_text=그리기 문제",
        topic="geometry",
        rule_id="grade3_2_circle_round1_draw_original_pizza_circle",
    ),
    5: ElementaryVisualTemplate(
        problem_text="두 원의 지름의 차를 구하세요.",
        expression="answer_text=8 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round1_diameter_difference",
    ),
    6: ElementaryVisualTemplate(
        problem_text="직사각형 안에 그릴 수 있는 가장 큰 원의 지름을 구하세요.",
        expression="answer_text=9 cm",
        topic="geometry",
        rule_id="grade3_2_circle_round1_largest_circle_in_rectangle",
    ),
}


_GRADE3_2_CIRCLE_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="반지름 6 cm인 원, 지름 10 cm인 원, 지름 14 cm인 원을 큰 원부터 순서대로 쓰세요.",
        expression="answer_text=다, 가, 나",
        topic="geometry",
        rule_id="grade3_2_circle_round1_order_circle_sizes",
    ),
    2: ElementaryVisualTemplate(
        problem_text="원에 대한 설명 중 틀린 것을 고르세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade3_2_circle_round1_false_circle_statement",
    ),
    3: ElementaryVisualTemplate(
        problem_text="큰 원의 지름이 24 cm일 때 그림 속 작은 원의 반지름을 구하세요.",
        expression="answer_text=6 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round1_small_circle_radius",
    ),
    4: ElementaryVisualTemplate(
        problem_text="반지름이 12 cm인 원 안에 크기가 같은 원 3개를 겹쳐 그렸을 때 작은 원의 반지름을 구하세요.",
        expression="answer_text=6 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round1_three_small_circles_radius",
    ),
    5: ElementaryVisualTemplate(
        problem_text="원의 지름을 6 cm 늘려 그리려면 컴퍼스를 몇 cm만큼 더 벌려야 하는지 구하세요.",
        expression="answer_text=3 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round1_compass_radius_increase",
    ),
    6: ElementaryVisualTemplate(
        problem_text="반지름이 8 cm인 원과 6 cm인 원이 맞닿아 있을 때 선분 ㄱㄴ의 길이를 구하세요.",
        expression="answer_text=28 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round1_centers_distance",
    ),
}


_GRADE3_2_CIRCLE_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림에서 가장 큰 원의 반지름을 구하세요.",
        expression="answer_text=9 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round1_largest_circle_radius",
    ),
    2: ElementaryVisualTemplate(
        problem_text="직사각형 안에 반지름 10 cm인 같은 원 5개를 이어 붙였을 때 직사각형 네 변의 길이의 합을 구하세요.",
        expression="answer_text=240 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round1_rectangle_perimeter_with_five_circles",
    ),
    3: ElementaryVisualTemplate(
        problem_text="안쪽 원의 지름이 8 cm이고 두 원 사이 간격이 3 cm일 때 큰 원의 반지름을 구하세요.",
        expression="answer_text=7 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round1_concentric_circle_outer_radius",
    ),
    4: ElementaryVisualTemplate(
        problem_text="원의 중심이 지나도록 만든 삼각형의 세 변 길이의 합을 구하세요.",
        expression="answer_text=20 cm",
        topic="geometry",
        rule_id="grade3_2_circle_round1_triangle_sum_with_center",
    ),
    5: ElementaryVisualTemplate(
        problem_text="반지름이 5 cm인 원 3개의 중심을 이어 만든 정삼각형의 세 변의 길이의 합을 구하세요.",
        expression="answer_text=30 cm",
        topic="geometry",
        rule_id="grade3_2_circle_round1_triangle_of_three_centers",
    ),
    6: ElementaryVisualTemplate(
        problem_text="크기가 같은 원 4개를 직사각형 안에 꼭 맞게 그리려면 원의 지름을 몇 cm로 해야 하는지 구하세요.",
        expression="answer_text=3 cm",
        topic="geometry",
        rule_id="grade3_2_circle_round1_four_circles_in_rectangle",
    ),
}


_GRADE3_2_CIRCLE_ROUND1_PAGE4: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="원의 중심은 같게 하고 반지름을 다르게 하여 그린 모양을 고르세요.",
        expression="answer_text=나",
        topic="geometry",
        rule_id="grade3_2_circle_round1_same_center_different_radius",
    ),
    2: ElementaryVisualTemplate(
        problem_text="원을 이용하여 그린 모양의 규칙을 바르게 설명한 사람을 고르세요.",
        expression="answer_text=정국",
        topic="geometry",
        rule_id="grade3_2_circle_round1_circle_pattern_explanation",
    ),
}


_GRADE3_2_CIRCLE_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="점 ㅇ이 원의 중심일 때 원의 반지름을 나타내는 선분을 모두 찾으세요.",
        expression="answer_text=선분 ㄱㅇ, 선분 ㄴㅇ",
        topic="geometry",
        rule_id="grade3_2_circle_round2_radius_segments",
    ),
    2: ElementaryVisualTemplate(
        problem_text="원의 반지름과 지름을 각각 구하세요.",
        expression="answer_text=반지름 7 cm, 지름 14 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round2_radius_and_diameter",
    ),
    3: ElementaryVisualTemplate(
        problem_text="점 ㅇ을 원의 중심으로 하고 주어진 선분을 반지름으로 하는 원을 그리세요.",
        expression="answer_text=그리기 문제",
        topic="geometry",
        rule_id="grade3_2_circle_round2_draw_circle_given_radius",
    ),
    4: ElementaryVisualTemplate(
        problem_text="누름 못과 띠 종이를 이용하여 가장 큰 원을 그리려면 어느 곳에 연필을 넣어야 하는지 고르세요.",
        expression="answer_text=㉤",
        topic="geometry",
        rule_id="grade3_2_circle_round2_largest_circle_hole",
    ),
    5: ElementaryVisualTemplate(
        problem_text="그림과 같이 컴퍼스를 벌려서 그린 원의 반지름을 구하세요.",
        expression="answer_text=2 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round2_compass_radius",
    ),
    6: ElementaryVisualTemplate(
        problem_text="원에 대한 설명 중에서 틀린 것을 고르세요.",
        expression="answer_text=④",
        topic="geometry",
        rule_id="grade3_2_circle_round2_false_circle_statement",
    ),
}


_GRADE3_2_CIRCLE_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="가장 큰 원과 가장 작은 원의 반지름의 차를 구하세요.",
        expression="answer_text=20 mm",
        topic="measurement",
        rule_id="grade3_2_circle_round2_radius_difference",
    ),
    2: ElementaryVisualTemplate(
        problem_text="점 ㄱ, 점 ㄴ이 원의 중심일 때 선분 ㄱㄴ의 길이를 구하세요.",
        expression="answer_text=7 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round2_center_segment_length",
    ),
    3: ElementaryVisualTemplate(
        problem_text="그림에서 선분 ㄱㄴ의 길이를 구하세요.",
        expression="answer_text=28 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round2_segment_length_two_tangent_circles",
    ),
    4: ElementaryVisualTemplate(
        problem_text="크기가 같은 원 3개를 이어 붙였을 때 선분 ㄱㄴ의 길이를 구하세요.",
        expression="answer_text=32 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round2_three_equal_circles_segment",
    ),
    5: ElementaryVisualTemplate(
        problem_text="큰 원의 지름이 48 cm이고 작은 원의 크기가 모두 같을 때 작은 원의 반지름을 구하세요.",
        expression="answer_text=8 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round2_small_circle_radius_in_large_circle",
    ),
    6: ElementaryVisualTemplate(
        problem_text="직사각형 안에 크기가 같은 원 6개를 이어 붙였을 때 직사각형 네 변의 길이의 합을 구하세요.",
        expression="answer_text=60 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round2_rectangle_perimeter_with_six_circles",
    ),
}


_GRADE3_2_CIRCLE_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="선분 ㄱㄴ의 길이가 34 cm일 때 가장 작은 원의 지름을 구하세요.",
        expression="answer_text=6 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round2_smallest_circle_diameter",
    ),
    2: ElementaryVisualTemplate(
        problem_text="원의 반지름이 6 cm일 때 삼각형 ㄱㄴㅇ의 세 변의 길이의 합을 구하세요.",
        expression="answer_text=21 cm",
        topic="geometry",
        rule_id="grade3_2_circle_round2_triangle_perimeter_with_radius",
    ),
    3: ElementaryVisualTemplate(
        problem_text="컴퍼스의 침과 연필심 사이를 가장 적게 벌려야 하는 원을 고르세요.",
        expression="answer_text=나",
        topic="geometry",
        rule_id="grade3_2_circle_round2_smallest_compass_opening",
    ),
    4: ElementaryVisualTemplate(
        problem_text="삼각형 6개의 세 변의 길이가 모두 같을 때 원의 지름을 구하세요.",
        expression="answer_text=18 cm",
        topic="geometry",
        rule_id="grade3_2_circle_round2_hexagon_circle_diameter",
    ),
    5: ElementaryVisualTemplate(
        problem_text="그림과 같은 모양을 그리기 위하여 컴퍼스의 침을 꽂아야 할 곳은 모두 몇 군데인지 구하세요.",
        expression="answer_text=4 군데",
        topic="geometry",
        rule_id="grade3_2_circle_round2_compass_centers_count",
    ),
    6: ElementaryVisualTemplate(
        problem_text="직사각형 안에 두 가지 종류의 원을 맞닿게 그렸을 때 선분 ㄱㄹ의 길이를 구하세요.",
        expression="answer_text=45 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round2_mixed_circles_segment_length",
    ),
}


_GRADE3_2_CIRCLE_ROUND2_PAGE4: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="원의 중심을 옮기지 않고 반지름을 다르게 하여 그린 모양을 고르세요.",
        expression="answer_text=다",
        topic="geometry",
        rule_id="grade3_2_circle_round2_same_center_different_radius",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그림을 보고 규칙을 찾아 원의 중심과 반지름이 어떻게 변하는지 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=1, 1",
        topic="pattern",
        rule_id="grade3_2_circle_round2_circle_growth_pattern",
    ),
}


_GRADE3_2_CIRCLE_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="원의 반지름과 지름을 각각 구하세요.",
        expression="answer_text=반지름 6 cm, 지름 12 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round3_radius_and_diameter",
    ),
    2: ElementaryVisualTemplate(
        problem_text="점 ㅇ을 원의 중심으로 하고 반지름이 1 cm 5 mm인 원을 그리세요.",
        expression="answer_text=그리기 문제",
        topic="geometry",
        rule_id="grade3_2_circle_round3_draw_circle_radius_1cm_5mm",
    ),
    3: ElementaryVisualTemplate(
        problem_text="두 원의 지름의 차를 구하세요.",
        expression="answer_text=3 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round3_diameter_difference",
    ),
    4: ElementaryVisualTemplate(
        problem_text="정사각형 안에 가장 큰 원을 그렸을 때 정사각형의 한 변의 길이를 구하세요.",
        expression="answer_text=10 cm",
        topic="geometry",
        rule_id="grade3_2_circle_round3_square_side_from_inscribed_circle",
    ),
    5: ElementaryVisualTemplate(
        problem_text="반지름과 지름에 대한 설명 중 옳지 않은 것을 고르세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade3_2_circle_round3_false_radius_diameter_statement",
    ),
    6: ElementaryVisualTemplate(
        problem_text="다음 중 가장 큰 원을 고르세요.",
        expression="answer_text=④",
        topic="geometry",
        rule_id="grade3_2_circle_round3_largest_circle_choice",
    ),
}


_GRADE3_2_CIRCLE_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="가장 큰 원과 가장 작은 원의 반지름의 차를 구하세요.",
        expression="answer_text=20 mm",
        topic="measurement",
        rule_id="grade3_2_circle_round3_radius_difference",
    ),
    2: ElementaryVisualTemplate(
        problem_text="점 ㄱ, 점 ㄴ이 원의 중심일 때 선분 ㄱㄴ의 길이를 구하세요.",
        expression="answer_text=6 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round3_center_segment_length",
    ),
    3: ElementaryVisualTemplate(
        problem_text="점 ㄴ, 점 ㄷ이 원의 중심일 때 선분 ㄱㄷ의 길이를 구하세요.",
        expression="answer_text=11 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round3_segment_giyeok_digeut",
    ),
    4: ElementaryVisualTemplate(
        problem_text="크기가 같은 원 4개를 서로 원의 중심이 지나도록 겹쳐 그렸을 때 선분 ㄱㄴ의 길이를 구하세요.",
        expression="answer_text=15 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round3_overlapped_four_circles_segment",
    ),
    5: ElementaryVisualTemplate(
        problem_text="큰 원의 지름이 36 cm이고 작은 원의 크기가 모두 같을 때 작은 원의 반지름을 구하세요.",
        expression="answer_text=6 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round3_small_circle_radius_in_large_circle",
    ),
    6: ElementaryVisualTemplate(
        problem_text="점 ㄱ, 점 ㄴ, 점 ㄷ이 원의 중심일 때 선분 ㄴㄹ의 길이를 구하세요.",
        expression="answer_text=18 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round3_segment_nieun_rieul",
    ),
}


_GRADE3_2_CIRCLE_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="크기가 같은 원 4개의 중심이 ㄱ, ㄴ, ㄷ, ㄹ일 때 선분 ㄱㄹ의 길이를 구하세요.",
        expression="answer_text=12 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round3_four_equal_circles_segment",
    ),
    2: ElementaryVisualTemplate(
        problem_text="선분 ㄱㄴ의 길이가 40 cm일 때 가장 작은 원의 지름을 구하세요.",
        expression="answer_text=8 cm",
        topic="measurement",
        rule_id="grade3_2_circle_round3_smallest_circle_diameter",
    ),
    3: ElementaryVisualTemplate(
        problem_text="삼각형 ㅇㄱㄴ의 세 변의 길이의 합이 25 cm일 때 원의 지름을 구하세요.",
        expression="answer_text=16 cm",
        topic="geometry",
        rule_id="grade3_2_circle_round3_circle_diameter_from_triangle_perimeter",
    ),
    4: ElementaryVisualTemplate(
        problem_text="반지름 9 cm인 크기가 같은 두 원이 겹쳐 있을 때 사각형 ㄱㄴㄷㄹ의 네 변의 길이의 합을 구하세요.",
        expression="answer_text=36 cm",
        topic="geometry",
        rule_id="grade3_2_circle_round3_quadrilateral_perimeter_two_circles",
    ),
    5: ElementaryVisualTemplate(
        problem_text="크기가 같은 원 4개의 중심을 이어 만든 사각형의 네 변의 길이의 합을 구하세요.",
        expression="answer_text=56 cm",
        topic="geometry",
        rule_id="grade3_2_circle_round3_quadrilateral_perimeter_four_centers",
    ),
    6: ElementaryVisualTemplate(
        problem_text="자와 컴퍼스를 사용하여 그린 무늬에서 원의 중심은 모두 몇 개인지 구하세요.",
        expression="answer_text=4 개",
        topic="geometry",
        rule_id="grade3_2_circle_round3_pattern_centers_count",
    ),
}


_GRADE3_2_CIRCLE_ROUND3_PAGE4: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림을 그린 규칙에 알맞은 것을 고르세요.",
        expression="answer_text=㉠",
        topic="pattern",
        rule_id="grade3_2_circle_round3_circle_pattern_rule",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그림을 보고 규칙을 찾아 원의 중심이 옮겨 가는 칸 수와 반지름이 줄어드는 칸 수를 쓰세요.",
        expression="answer_text=2, 1",
        topic="pattern",
        rule_id="grade3_2_circle_round3_circle_shrink_pattern",
    ),
}


_GRADE3_2_FRACTION_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="연필 8개를 2개씩 묶으면 2는 8의 얼마인지 분수로 나타내세요.",
        expression="answer_text=1/4",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_pencils_two_of_eight",
    ),
    2: ElementaryVisualTemplate(
        problem_text="54를 9씩 묶으면 18은 54의 얼마인지 분수로 나타내세요.",
        expression="answer_text=2/6",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_18_of_54_grouped_by_9",
    ),
    3: ElementaryVisualTemplate(
        problem_text="귤 전체를 똑같이 3부분으로 나누면 한 부분은 몇 개인지 구하세요.",
        expression="answer_text=4 개",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_oranges_one_third",
    ),
    4: ElementaryVisualTemplate(
        problem_text="사과 56개 중 40개는 전체의 얼마인지 분수로 나타내세요.",
        expression="answer_text=5/7",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_apples_forty_of_fifty_six",
    ),
    5: ElementaryVisualTemplate(
        problem_text="색칠한 부분은 전체의 몇 분의 몇인지 구하세요.",
        expression="answer_text=5/16",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_shaded_fraction",
    ),
    6: ElementaryVisualTemplate(
        problem_text="하루의 1/3만큼 회사에서 일할 때 일하는 시간을 구하세요.",
        expression="answer_text=8 시간",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_one_third_of_day",
    ),
    7: ElementaryVisualTemplate(
        problem_text="연필 12자루 중 1/3을 동생에게 주었을 때 준 연필 수를 구하세요.",
        expression="answer_text=4 자루",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_one_third_of_twelve_pencils",
    ),
    8: ElementaryVisualTemplate(
        problem_text="36의 2/4와 42의 4/7의 크기를 비교하세요.",
        expression="answer_text=<",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_compare_fraction_values",
    ),
}


_GRADE3_2_FRACTION_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="성민이와 유진이 중 더 긴 리본을 가지고 있는 사람을 구하세요.",
        expression="answer_text=유진",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_longer_ribbon",
    ),
    2: ElementaryVisualTemplate(
        problem_text="9는 어떤 수의 3/5일 때 어떤 수를 구하세요.",
        expression="answer=15",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_find_whole_from_three_fifths",
    ),
    3: ElementaryVisualTemplate(
        problem_text="45 cm 색 테이프의 3/5을 사용했을 때 남은 색 테이프의 길이를 구하세요.",
        expression="answer_text=18 cm",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_remaining_tape",
    ),
    4: ElementaryVisualTemplate(
        problem_text="분모가 9인 분수 중에서 2/9보다 큰 진분수의 개수를 구하세요.",
        expression="answer_text=6 개",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_proper_fractions_greater_than_two_ninths",
    ),
    5: ElementaryVisualTemplate(
        problem_text="숫자 카드 2장을 골라 분모가 9인 진분수를 만들 때 만들 수 있는 진분수의 개수를 구하세요.",
        expression="answer_text=4 개",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_proper_fraction_cards",
    ),
    6: ElementaryVisualTemplate(
        problem_text="㉠+㉡의 값을 구하세요.",
        expression="answer=35",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_unit_fraction_count_sum",
    ),
    7: ElementaryVisualTemplate(
        problem_text="㉮와 ㉯에 알맞은 수 중 더 큰 것의 기호를 쓰세요.",
        expression="answer_text=가",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_larger_mixed_number_part",
    ),
    8: ElementaryVisualTemplate(
        problem_text="분수의 크기를 잘못 비교한 것을 찾아 기호를 쓰세요.",
        expression="answer_text=라",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_wrong_fraction_comparison",
    ),
}


_GRADE3_2_FRACTION_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="1부터 9까지의 자연수 중 빈칸에 들어갈 수 있는 수는 모두 몇 개인지 구하세요.",
        expression="answer_text=5 개",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_numbers_between_fractions",
    ),
    2: ElementaryVisualTemplate(
        problem_text="다음 중 잘못 설명한 친구의 이름을 쓰세요.",
        expression="answer_text=영수",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_wrong_fraction_explanation",
    ),
    3: ElementaryVisualTemplate(
        problem_text="달걀 전체의 1/6을 삶고 남은 달걀의 3/5을 빵 만드는 데 사용했을 때 사용한 달걀 수를 구하세요.",
        expression="answer_text=45 개",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_eggs_used_for_bread",
    ),
    4: ElementaryVisualTemplate(
        problem_text="미주와 하나 중 누가 동화책을 몇 쪽 더 많이 읽었는지 구하세요.",
        expression="answer_text=하나, 9 쪽",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round1_more_pages_read",
    ),
}


_GRADE3_2_FRACTION_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="꽃 12송이를 4개씩 묶으면 4는 12의 얼마인지 분수로 나타내세요.",
        expression="answer_text=1/3",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_flowers_four_of_twelve",
    ),
    2: ElementaryVisualTemplate(
        problem_text="18의 4/9는 얼마인지 구하세요.",
        expression="answer=8",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_four_ninths_of_18",
    ),
    3: ElementaryVisualTemplate(
        problem_text="20은 35의 4/㉠일 때 ㉠에 알맞은 수를 구하세요.",
        expression="answer=7",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_find_denominator",
    ),
    4: ElementaryVisualTemplate(
        problem_text="참외 36개 중 28개는 전체의 얼마인지 분수로 나타내세요.",
        expression="answer_text=7/9",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_melons_twenty_eight_of_thirty_six",
    ),
    5: ElementaryVisualTemplate(
        problem_text="쿠키 20개 중 아몬드 쿠키 8개는 전체의 몇 분의 몇인지 분수로 나타내세요.",
        expression="answer_text=2/5",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_cookies_eight_of_twenty",
    ),
    6: ElementaryVisualTemplate(
        problem_text="64의 3/8과 28의 1/4의 합을 구하세요.",
        expression="answer=31",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_sum_fraction_values",
    ),
    7: ElementaryVisualTemplate(
        problem_text="사탕 20개 중 1/4을 주었을 때 준 사탕의 수를 구하세요.",
        expression="answer_text=5 개",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_one_quarter_of_twenty_candies",
    ),
    8: ElementaryVisualTemplate(
        problem_text="다음 중 나타내는 수가 다른 하나를 고르세요.",
        expression="answer_text=⑤",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_different_fraction_value_choice",
    ),
}


_GRADE3_2_FRACTION_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="빈칸에 알맞은 수가 가장 큰 것을 찾아 기호를 쓰세요.",
        expression="answer_text=ㄱ",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_largest_blank_value",
    ),
    2: ElementaryVisualTemplate(
        problem_text="2/5 m는 몇 cm인지 구하세요.",
        expression="answer_text=40 cm",
        topic="measurement",
        rule_id="grade3_2_fraction_round2_two_fifths_meter_to_cm",
    ),
    3: ElementaryVisualTemplate(
        problem_text="하루 24시간의 1/8만큼 그림을 그렸을 때 그린 시간을 구하세요.",
        expression="answer_text=3 시간",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_one_eighth_of_day",
    ),
    4: ElementaryVisualTemplate(
        problem_text="분모와 분자의 합이 22이고 차가 8인 진분수를 구하세요.",
        expression="answer_text=7/15",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_proper_fraction_sum_diff",
    ),
    5: ElementaryVisualTemplate(
        problem_text="3장의 수 카드 중 2장을 사용하여 만들 수 있는 가분수의 개수를 구하세요.",
        expression="answer_text=6 개",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_improper_fraction_cards",
    ),
    6: ElementaryVisualTemplate(
        problem_text="대분수의 빈칸에 공통으로 들어갈 수 있는 자연수를 구하세요.",
        expression="answer=6",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_common_mixed_number_blank",
    ),
    7: ElementaryVisualTemplate(
        problem_text="㉠+㉡+㉢을 구하세요.",
        expression="answer=157",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_unit_fraction_count_sum",
    ),
    8: ElementaryVisualTemplate(
        problem_text="가분수를 대분수로 나타낸 식에서 ㉠에 알맞은 수를 구하세요.",
        expression="answer=5",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_improper_to_mixed_denominator",
    ),
}


_GRADE3_2_FRACTION_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="가장 큰 분수와 가장 작은 분수를 차례로 기호로 쓰세요.",
        expression="answer_text=다, 가",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_largest_smallest_fractions",
    ),
    2: ElementaryVisualTemplate(
        problem_text="빈칸에 공통으로 들어갈 수 있는 자연수들의 합을 구하세요.",
        expression="answer=12",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_common_natural_numbers_sum",
    ),
    3: ElementaryVisualTemplate(
        problem_text="서준이와 승민이 중 더 긴 철사를 가지고 있는 사람을 구하세요.",
        expression="answer_text=승민",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_longer_wire",
    ),
    4: ElementaryVisualTemplate(
        problem_text="준영이와 시후 중 누가 몇 권 더 많이 가졌는지 구하세요.",
        expression="answer_text=시후, 1 권",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round2_more_notebooks",
    ),
}


_GRADE3_2_FRACTION_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="16의 3/4은 얼마인지 구하세요.",
        expression="answer=12",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_three_quarters_of_16",
    ),
    2: ElementaryVisualTemplate(
        problem_text="5는 8의 얼마인지, 11은 10의 얼마인지 분수로 나타내세요.",
        expression="answer_text=(1) 5/8, (2) 11/10",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_write_fractions",
    ),
    3: ElementaryVisualTemplate(
        problem_text="떡 6조각 중 5조각을 먹었을 때 먹은 떡은 전체의 몇 분의 몇인지 쓰세요.",
        expression="answer_text=5/6",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_five_of_six_rice_cake",
    ),
    4: ElementaryVisualTemplate(
        problem_text="딸기 전체를 똑같이 2부분으로 나누면 한 부분은 몇 개인지 구하세요.",
        expression="answer_text=5 개",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_half_of_strawberries",
    ),
    5: ElementaryVisualTemplate(
        problem_text="색칠한 부분은 전체의 몇 분의 몇인지 구하세요.",
        expression="answer_text=2/9",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_shaded_fraction",
    ),
    6: ElementaryVisualTemplate(
        problem_text="40의 6/8과 72의 4/9에 알맞은 수의 차를 구하세요.",
        expression="answer=2",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_fraction_values_difference",
    ),
    7: ElementaryVisualTemplate(
        problem_text="나타내는 수가 나머지와 다른 하나를 고르세요.",
        expression="answer_text=④",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_different_fraction_value_choice",
    ),
}


_GRADE3_2_FRACTION_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="큰 것부터 차례로 쓰세요.",
        expression="answer_text=나, 가, 라, 다",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_order_fraction_values",
    ),
    2: ElementaryVisualTemplate(
        problem_text="학생 32명 중 3/4은 여학생이고 여학생 중 5/6은 안경을 썼을 때 안경 쓴 여학생 수를 구하세요.",
        expression="answer_text=20 명",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_girls_with_glasses",
    ),
    3: ElementaryVisualTemplate(
        problem_text="어떤 수의 3/4은 21일 때 어떤 수의 1/14은 얼마인지 구하세요.",
        expression="answer=2",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_find_one_fourteenth",
    ),
    4: ElementaryVisualTemplate(
        problem_text="▲의 4/5는 24이고 ■의 6/8은 ▲일 때 ■에 알맞은 수를 구하세요.",
        expression="answer=40",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_nested_fraction_unknown",
    ),
    5: ElementaryVisualTemplate(
        problem_text="17/20 m는 몇 cm인지 구하세요.",
        expression="answer_text=85 cm",
        topic="measurement",
        rule_id="grade3_2_fraction_round3_seventeen_twentieths_meter_to_cm",
    ),
    6: ElementaryVisualTemplate(
        problem_text="하루 24시간의 4/12만큼 그림을 그렸을 때 그린 시간을 구하세요.",
        expression="answer_text=8 시간",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_four_twelfths_of_day",
    ),
    7: ElementaryVisualTemplate(
        problem_text="분수의 개수가 더 많은 것의 기호를 쓰세요.",
        expression="answer_text=나",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_more_fractions_choice",
    ),
    8: ElementaryVisualTemplate(
        problem_text="수 카드 4장 중 3장을 사용하여 만들 수 있는 대분수 중 분모가 6인 대분수의 개수를 구하세요.",
        expression="answer_text=4 개",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_mixed_numbers_denominator_six",
    ),
}


_GRADE3_2_FRACTION_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="다음 중 틀린 것을 고르세요.",
        expression="answer_text=③",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_wrong_mixed_fraction_conversion",
    ),
    2: ElementaryVisualTemplate(
        problem_text="매일 1/5 km씩 2주일 동안 산책하는 거리를 대분수로 나타내세요.",
        expression="answer_text=2 4/5 km",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_two_weeks_walk_distance",
    ),
    3: ElementaryVisualTemplate(
        problem_text="빈칸에 들어갈 수 있는 자연수는 모두 몇 개인지 구하세요.",
        expression="answer_text=9 개",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_numbers_between_mixed_fractions",
    ),
    4: ElementaryVisualTemplate(
        problem_text="세훈이와 정현이 중 과자를 누가 몇 개 더 많이 먹었는지 구하세요.",
        expression="answer_text=세훈, 3 개",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_more_cookies_eaten",
    ),
    5: ElementaryVisualTemplate(
        problem_text="공이 떨어진 높이의 4/7만큼 튀어 오를 때 98 cm 높이에서 떨어뜨린 공이 두 번째로 튀어 오르는 높이를 구하세요.",
        expression="answer_text=32 cm",
        topic="fraction_ratio",
        rule_id="grade3_2_fraction_round3_second_bounce_height",
    ),
}


_GRADE3_2_VOLUME_WEIGHT_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="(가) 그릇의 물을 (나) 그릇에 옮겨 담았더니 물이 넘쳤습니다. 어느 그릇의 들이가 더 많은지 쓰세요.",
        expression="answer_text=(가)",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_larger_capacity_bowl",
    ),
    2: ElementaryVisualTemplate(
        problem_text="컵, 세숫대야, 냄비, 숟가락을 들이가 큰 것부터 차례로 기호를 쓰세요.",
        expression="answer_text=가, 다, 라, 나",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_order_capacity_objects",
    ),
    3: ElementaryVisualTemplate(
        problem_text="2 L의 물이 들어 있는 물통에 900 mL의 물을 더 부었습니다. 모두 몇 L 몇 mL인지 쓰세요.",
        expression="answer_text=2 L 900 mL",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_two_liters_plus_900ml",
    ),
    4: ElementaryVisualTemplate(
        problem_text="들이를 비교하여 ○ 안에 >, =, <를 알맞게 써넣으세요.",
        expression="answer_text=(1) >, (2) <",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_compare_capacity_units",
    ),
    5: ElementaryVisualTemplate(
        problem_text="무게를 비교하여 무거운 것부터 차례로 기호를 쓰세요.",
        expression="answer_text=라, 가, 나, 다",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_order_weights_heaviest",
    ),
    6: ElementaryVisualTemplate(
        problem_text="들이가 2 L인 간장 병의 들이를 가장 가깝게 어림한 친구를 쓰세요.",
        expression="answer_text=재민",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_estimate_two_liters_friend",
    ),
    7: ElementaryVisualTemplate(
        problem_text="주어진 물건의 무게로 알맞은 것을 고르세요.",
        expression="answer_text=가",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_choose_reasonable_weight",
    ),
}


_GRADE3_2_VOLUME_WEIGHT_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="6 L 600 mL를 몇 L 몇 mL인지 알맞게 나타내세요.",
        expression="answer_text=6, 600",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_split_capacity_l_ml",
    ),
    2: ElementaryVisualTemplate(
        problem_text="두 음료의 양을 비교하여 어느 것이 몇 병 더 많은지 쓰세요.",
        expression="answer_text=사과 주스, 2 병",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_compare_drink_bottles",
    ),
    3: ElementaryVisualTemplate(
        problem_text="mL와 L 단위 관계에 알맞은 수를 빈칸에 쓰세요.",
        expression="answer_text=100, 2",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_capacity_unit_blanks",
    ),
    4: ElementaryVisualTemplate(
        problem_text="주어진 들이를 mL로 나타내세요.",
        expression="answer_text=3400 mL",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_convert_l_ml_to_ml",
    ),
    5: ElementaryVisualTemplate(
        problem_text="물건의 무게를 비교하여 더 무거운 것을 쓰세요.",
        expression="answer_text=수박",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_heavier_object",
    ),
    6: ElementaryVisualTemplate(
        problem_text="저울이 가리키는 무게를 g 단위로 쓰세요.",
        expression="answer_text=350 g",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_read_scale_350g",
    ),
    7: ElementaryVisualTemplate(
        problem_text="주어진 무게를 kg 단위로 알맞게 나타내세요.",
        expression="answer_text=500 kg",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_write_500kg",
    ),
    8: ElementaryVisualTemplate(
        problem_text="무게를 비교하여 알맞은 기호를 쓰세요.",
        expression="answer_text=나",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_choose_weight_comparison",
    ),
}


_GRADE3_2_VOLUME_WEIGHT_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="귤의 무게를 바르게 읽은 것을 찾아 기호를 쓰세요.",
        expression="answer_text=나",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_read_orange_weight",
    ),
    2: ElementaryVisualTemplate(
        problem_text="계산에서 □ 안의 수 1이 실제로 나타내는 무게는 몇 g인지 쓰세요.",
        expression="answer_text=1000 g",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_place_value_kg_digit",
    ),
    3: ElementaryVisualTemplate(
        problem_text="7 kg 600 g과 3200 g의 합과 차를 각각 구하세요.",
        expression="answer_text=합: 10 kg 800 g, 차: 4 kg 400 g",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_weight_sum_difference",
    ),
    4: ElementaryVisualTemplate(
        problem_text="㉠과 ㉡의 차는 몇 kg 몇 g인지 구하세요.",
        expression="answer_text=5 kg 300 g",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_unknown_weights_difference",
    ),
    5: ElementaryVisualTemplate(
        problem_text="가방을 메고 잰 무게와 가방을 메지 않고 잰 무게의 차로 가방의 무게를 구하세요.",
        expression="answer_text=1 kg 300 g",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round1_bag_weight_difference",
    ),
}


_GRADE3_2_VOLUME_WEIGHT_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="가, 나, 다 병에 물을 가득 채운 뒤 같은 그릇에 옮겨 담았습니다. 들이가 가장 적은 병을 고르세요.",
        expression="answer_text=다",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_least_capacity_bottle",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그릇에 물을 가득 채울 때 가 컵은 4번, 나 컵은 3번, 다 컵은 5번 부어야 합니다. 들이가 많은 컵부터 차례로 고르세요.",
        expression="answer_text=④",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_order_cup_capacity",
    ),
    3: ElementaryVisualTemplate(
        problem_text="들이 단위 변환식 중 잘못된 것을 모두 고르세요.",
        expression="answer_text=①, ④",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_wrong_capacity_conversions",
    ),
    4: ElementaryVisualTemplate(
        problem_text="5030 mL, 5 L 300 mL, 5003 mL, 5 L 35 mL를 들이가 적은 것부터 순서대로 쓰세요.",
        expression="answer_text=다, 가, 라, 나",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_order_capacity_values",
    ),
    5: ElementaryVisualTemplate(
        problem_text="오렌지 주스는 1860 mL, 포도 주스는 1 L 680 mL 있습니다. 더 많은 주스를 쓰세요.",
        expression="answer_text=오렌지 주스",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_more_juice",
    ),
    6: ElementaryVisualTemplate(
        problem_text="보기에서 물건을 선택하여 700 mL, 200 mL, 300 L에 알맞은 문장을 완성하세요.",
        expression="answer_text=(1) 분무기, (2) 종이컵, (3) 욕조",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_match_capacity_objects",
    ),
    7: ElementaryVisualTemplate(
        problem_text="5 L 100 mL+1 L 850 mL와 4700 mL+2150 mL 중 들이가 더 적은 것의 기호를 쓰세요.",
        expression="answer_text=나",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_smaller_capacity_expression",
    ),
}


_GRADE3_2_VOLUME_WEIGHT_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="□ L 900 mL+3 L □ mL=13 L 600 mL가 되도록 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=9, 700",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_capacity_addition_blanks",
    ),
    2: ElementaryVisualTemplate(
        problem_text="700 mL 들이 그릇으로 4번, 400 mL 들이 그릇으로 6번 부어 양동이를 가득 채웠습니다. 양동이의 들이를 구하세요.",
        expression="answer_text=5 L 200 mL",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_bucket_capacity",
    ),
    3: ElementaryVisualTemplate(
        problem_text="400 mL에 3000원인 딸기맛 아이스크림 800 mL와 600 mL에 4100원인 초코맛 아이스크림 2 L 400 mL의 값을 모두 구하세요.",
        expression="answer_text=22400 원",
        topic="arithmetic",
        rule_id="grade3_2_volume_weight_round2_ice_cream_total_price",
    ),
    4: ElementaryVisualTemplate(
        problem_text="4 L-3 L 800 mL 계산에서 잘못된 곳을 찾아 바르게 계산하세요.",
        expression="answer_text=200 mL",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_fix_capacity_subtraction",
    ),
    5: ElementaryVisualTemplate(
        problem_text="4 L 600 mL와 3 L 700 mL의 물 중 화분에 주고 남은 물이 6 L 400 mL일 때 화분에 준 물의 양을 구하세요.",
        expression="answer_text=1 L 900 mL",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_water_used",
    ),
    6: ElementaryVisualTemplate(
        problem_text="전자레인지, 클립, 냉장고, 수학책을 무게가 가벼운 것부터 순서대로 쓰세요.",
        expression="answer_text=나, 라, 가, 다",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_order_objects_lightest",
    ),
    7: ElementaryVisualTemplate(
        problem_text="양팔 저울과 바둑돌 수를 사용하여 연필, 볼펜, 색연필을 무거운 것부터 차례로 쓰세요.",
        expression="answer_text=볼펜, 색연필, 연필",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_order_stationery_heaviest",
    ),
    8: ElementaryVisualTemplate(
        problem_text="3 kg의 포도 상자에 650 g인 포도 1개를 더 넣었습니다. 포도 상자의 무게를 g으로 구하세요.",
        expression="answer_text=3650 g",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_grape_box_weight",
    ),
}


_GRADE3_2_VOLUME_WEIGHT_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="7000 kg=㉠ t, ㉡ g=18 kg일 때 ㉠과 ㉡에 알맞은 수의 합을 구하세요.",
        expression="answer=18007",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_unit_relation_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="2 kg, 2 kg 5 g, 2050 g, 2500 g, 2 kg 50 g 중 가장 무거운 것을 고르세요.",
        expression="answer_text=④",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_heaviest_choice",
    ),
    3: ElementaryVisualTemplate(
        problem_text="혜리는 29 kg 800 g이고 준기는 혜리보다 3 kg 800 g 더 무겁습니다. 두 사람의 몸무게의 합을 구하세요.",
        expression="answer_text=63 kg 400 g",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_body_weight_sum",
    ),
    4: ElementaryVisualTemplate(
        problem_text="무게 계산식 셋 중 결과가 다른 하나를 찾아 기호를 쓰세요.",
        expression="answer_text=가",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_different_weight_expression",
    ),
    5: ElementaryVisualTemplate(
        problem_text="음료수 캔 4개를 담은 상자의 무게가 1 kg 650 g이고 상자만의 무게가 450 g일 때 캔 1개의 무게를 구하세요.",
        expression="answer_text=300 g",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round2_one_can_weight",
    ),
}


_GRADE3_2_VOLUME_WEIGHT_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="세 그릇 가, 나, 다의 물을 같은 그릇에 옮겨 담았습니다. 들이가 많은 것부터 차례로 쓰세요.",
        expression="answer_text=나, 가, 다",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_order_capacity_containers",
    ),
    2: ElementaryVisualTemplate(
        problem_text="가 항아리는 15컵, 나 항아리는 5컵이 들어갑니다. 가 항아리의 들이는 나 항아리의 몇 배인지 구하세요.",
        expression="answer_text=3 배",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_capacity_ratio_jars",
    ),
    3: ElementaryVisualTemplate(
        problem_text="1 L의 물이 들어 있는 물통에 600 mL의 물을 더 부었습니다. 모두 몇 L 몇 mL인지 쓰세요.",
        expression="answer_text=1 L 600 mL",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_one_liter_plus_600ml",
    ),
    4: ElementaryVisualTemplate(
        problem_text="3080 mL, 3 L 700 mL, 3800 mL, 4 L, 4 L 100 mL 중 들이가 가장 많은 것을 고르세요.",
        expression="answer_text=⑤",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_largest_capacity_choice",
    ),
    5: ElementaryVisualTemplate(
        problem_text="월요일 960 mL, 화요일 1 L 200 mL, 수요일 1090 mL 중 물을 가장 많이 마신 요일을 쓰세요.",
        expression="answer_text=화요일",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_most_water_day",
    ),
    6: ElementaryVisualTemplate(
        problem_text="세제 통의 들이를 가장 적절히 어림한 친구를 쓰세요.",
        expression="answer_text=주경",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_best_detergent_capacity_estimate",
    ),
}


_GRADE3_2_VOLUME_WEIGHT_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="4400 mL, 2 L 600 mL, 5700 mL, 3 L 900 mL 중 들이가 가장 많은 것과 가장 적은 것의 합을 구하세요.",
        expression="answer_text=8300 mL",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_largest_smallest_capacity_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="□ L 800 mL+5 L □ mL=11 L 400 mL가 되도록 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=5, 600",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_capacity_addition_blanks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="1 L 500 mL의 물이 들어 있는 그릇에 500 mL 컵으로 4번 더 부었습니다. 이 그릇의 들이를 구하세요.",
        expression="answer_text=3 L 500 mL",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_bowl_capacity_after_four_cups",
    ),
    4: ElementaryVisualTemplate(
        problem_text="처음 병에 들어 있던 우유의 절반을 마시고, 나머지의 절반을 마셨더니 650 mL가 남았습니다. 처음 우유의 양을 구하세요.",
        expression="answer_text=2 L 600 mL",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_initial_milk_amount",
    ),
    5: ElementaryVisualTemplate(
        problem_text="세 식의 들이를 많은 순서대로 기호를 쓰세요.",
        expression="answer_text=다, 나, 가",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_order_capacity_expressions",
    ),
    6: ElementaryVisualTemplate(
        problem_text="9 L의 수조에서 200 mL 그릇으로 4번, 400 mL 그릇으로 6번 덜어 냈습니다. 남은 물의 양을 구하세요.",
        expression="answer_text=5 L 800 mL",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_tank_remaining_water",
    ),
    7: ElementaryVisualTemplate(
        problem_text="화분, 공책, 서랍장을 무게가 무거운 물건부터 차례대로 기호를 쓰세요.",
        expression="answer_text=다, 가, 나",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_order_objects_heaviest",
    ),
}


_GRADE3_2_VOLUME_WEIGHT_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="양팔 저울과 바둑돌 수를 사용하여 방울토마토, 살구, 딸기를 무거운 물건부터 차례로 쓴 것을 고르세요.",
        expression="answer_text=④",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_balance_scale_choice",
    ),
    2: ElementaryVisualTemplate(
        problem_text="강아지의 무게 4750 g을 kg과 g으로 나타내세요.",
        expression="answer_text=4 kg 750 g",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_4750g_to_kg_g",
    ),
    3: ElementaryVisualTemplate(
        problem_text="무게 단위 사이의 관계가 틀린 것을 모두 고르세요.",
        expression="answer_text=③, ⑤",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_wrong_weight_conversions",
    ),
    4: ElementaryVisualTemplate(
        problem_text="4 kg 100 g, 5000 g, 5 kg 700 g, 4650 g을 무게가 무거운 것부터 차례로 쓰세요.",
        expression="answer_text=다, 나, 라, 가",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_order_weight_values",
    ),
    5: ElementaryVisualTemplate(
        problem_text="2 kg 800 g+3 kg 400 g과 4 kg 700 g+1 kg 500 g을 비교하여 알맞은 부등호를 쓰세요.",
        expression="answer_text==",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_compare_weight_sums",
    ),
    6: ElementaryVisualTemplate(
        problem_text="16 kg-7 kg 30 g+4 kg 570 g을 계산하세요.",
        expression="answer_text=13 kg 540 g",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_weight_expression_result",
    ),
    7: ElementaryVisualTemplate(
        problem_text="600 g 상자에 400 g 동화책 3권과 450 g 위인전 6권을 넣었을 때 전체 무게를 구하세요.",
        expression="answer_text=4 kg 500 g",
        topic="measurement",
        rule_id="grade3_2_volume_weight_round3_books_box_total_weight",
    ),
}


_GRADE3_2_PICTOGRAPH_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="배우고 싶어 하는 운동별 학생 수 그림그래프를 보고 표를 완성하세요.",
        expression="answer_text=남학생: 수영 3, 태권도 4, 야구 4, 축구 5, 합계 16 / 여학생: 수영 6, 태권도 3, 야구 2, 축구 3, 합계 14",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_sports_table",
    ),
    2: ElementaryVisualTemplate(
        problem_text="음료수 판매량 그림그래프를 보고 다음 달에 가장 많이 준비하면 좋은 음료수를 쓰세요.",
        expression="answer_text=사이다",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_most_sold_drink",
    ),
    3: ElementaryVisualTemplate(
        problem_text="동별 강아지를 기르는 가구 수 그림그래프에서 3동이 21가구일 때 2동의 가구 수를 구하세요.",
        expression="answer_text=43 가구",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_dog_households_building_two",
    ),
    4: ElementaryVisualTemplate(
        problem_text="3학년 학생들이 좋아하는 김밥 그림그래프에서 가장 많은 학생들이 좋아하는 김밥을 쓰세요.",
        expression="answer_text=참치 김밥",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_favorite_gimbap",
    ),
}


_GRADE3_2_PICTOGRAPH_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="요일별 팔린 아이스크림의 수 그림그래프를 보고 표를 완성하세요.",
        expression="answer_text=월요일 11, 화요일 34, 수요일 17, 목요일 26, 합계 88",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_ice_cream_table",
    ),
    2: ElementaryVisualTemplate(
        problem_text="취미별 학생 수 그림그래프에서 취미가 독서인 학생은 운동인 학생보다 몇 명 더 많은지 구하세요.",
        expression="answer_text=8 명",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_reading_more_than_sports",
    ),
    3: ElementaryVisualTemplate(
        problem_text="학생별 1년 동안 읽은 책의 수 그림그래프에서 학생들이 읽은 책은 모두 몇 권인지 구하세요.",
        expression="answer_text=220 권",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_total_books_read",
    ),
    4: ElementaryVisualTemplate(
        problem_text="가게별 판매한 사탕 수 그림그래프에서 가장 많이 판 가게와 가장 적게 판 가게의 차를 구하세요.",
        expression="answer_text=210 개",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_candy_difference",
    ),
}


_GRADE3_2_PICTOGRAPH_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="과수원별 사과 생산량 그림그래프를 보고 표를 완성하세요.",
        expression="answer_text=가 320, 나 240, 다 300, 라 430, 합계 1290",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_apple_table",
    ),
    2: ElementaryVisualTemplate(
        problem_text="6월 감자 생산량 그림그래프를 보고 7월 신선 농장과 푸른 농장의 생산량을 구하세요.",
        expression="answer_text=신선 농장: 23 상자, 푸른 농장: 48 상자",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_potato_july_production",
    ),
    3: ElementaryVisualTemplate(
        problem_text="학예회 종목별 참가 학생 수 그림그래프에서 합창 여학생이 27명이면 합창 남학생 수를 구하세요.",
        expression="answer_text=19 명",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_choir_boys",
    ),
    4: ElementaryVisualTemplate(
        problem_text="마을별 학생 수 그림그래프에서 샛별 마을의 남학생이 62명일 때 여학생 수를 구하세요.",
        expression="answer_text=69 명",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_saetbyeol_girls",
    ),
}


_GRADE3_2_PICTOGRAPH_ROUND1_PAGE4: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="농장별 기르고 있는 소의 수 그림그래프에서 별 농장의 소는 구름 농장의 소의 몇 배인지 구하세요.",
        expression="answer_text=3 배",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_cows_ratio",
    ),
    2: ElementaryVisualTemplate(
        problem_text="훌라후프 횟수 그림그래프를 보고 알 수 있는 내용을 모두 고르세요.",
        expression="answer_text=①, ③",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_hula_hoop_true_statements",
    ),
    3: ElementaryVisualTemplate(
        problem_text="문구점별 팔린 공책 수 그림그래프에서 힘찬 문구점이 315권일 때 네 문구점에서 팔린 공책 수를 모두 구하세요.",
        expression="answer_text=1221 권",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_notebooks_total",
    ),
    4: ElementaryVisualTemplate(
        problem_text="월별 입장객 수 그림그래프에서 4월과 5월 입장객이 모두 490명일 때 3월과 6월 입장객의 합을 구하세요.",
        expression="answer_text=440 명",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_visitors_march_june",
    ),
}


_GRADE3_2_PICTOGRAPH_ROUND1_PAGE5: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="기증한 책 종류별 책 수 그림그래프에서 가장 많은 책과 두 번째로 많은 책의 권수의 합을 구하세요.",
        expression="answer_text=74 권",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_donated_books_top_two",
    ),
    2: ElementaryVisualTemplate(
        problem_text="4일 동안 당근 판매량 그림그래프에서 화요일은 28개이고 당근 가격이 1000원일 때 4일 동안 모두 판 가격을 구하세요.",
        expression="answer_text=112000 원",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_carrot_total_price",
    ),
    3: ElementaryVisualTemplate(
        problem_text="월별 비 온 날수 그림그래프에서 비 온 날수를 각각 구하세요.",
        expression="answer_text=7월: 18일, 8월: 12일, 9월: 14일, 10월: 8일",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_rainy_days",
    ),
    4: ElementaryVisualTemplate(
        problem_text="서점별 팔린 책 수 표와 그림그래프를 완성하세요.",
        expression="answer_text=가 130, 나 250, 다 120, 라 300, 합계 800",
        topic="statistics",
        rule_id="grade3_2_pictograph_round1_bookstore_table_graph",
    ),
}


_GRADE3_2_PICTOGRAPH_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="학년별 지각한 학생 수 그림그래프에서 지각한 학생 수가 가장 적은 학년을 쓰세요.",
        expression="answer_text=3 학년",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_least_late_grade",
    ),
    2: ElementaryVisualTemplate(
        problem_text="학생별 빚은 만두 수 그림그래프에서 4명이 빚은 만두가 114개일 때 성희가 빚은 만두 수를 구하세요.",
        expression="answer_text=26 개",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_seonghui_dumplings",
    ),
    3: ElementaryVisualTemplate(
        problem_text="한 달 동안 팔린 종류별 책의 수 그림그래프를 보고 표로 나타내세요.",
        expression="answer_text=소설책 230, 유아 서적 340, 학습지 160, 잡지 250, 합계 980",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_books_table",
    ),
    4: ElementaryVisualTemplate(
        problem_text="반별 가꾼 화분 수 그림그래프에서 화분이 많은 반부터 차례대로 쓰세요.",
        expression="answer_text=2 반, 1 반, 3 반",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_order_flowerpots",
    ),
}


_GRADE3_2_PICTOGRAPH_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="일주일 동안 팔린 종류별 음식의 수 그림그래프를 보고 표로 나타내세요.",
        expression="answer_text=칼국수 26, 짜장면 62, 비빔밥 44, 합계 132",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_food_table",
    ),
    2: ElementaryVisualTemplate(
        problem_text="간식별 학생 수 그림그래프에서 김밥보다 더 많은 학생들이 좋아하는 간식을 쓰세요.",
        expression="answer_text=토스트",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_snack_more_than_gimbap",
    ),
    3: ElementaryVisualTemplate(
        problem_text="마을별 마을버스 수 그림그래프에서 가장 많은 마을은 가장 적은 마을보다 몇 대 더 많은지 구하세요.",
        expression="answer_text=9 대",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_bus_difference",
    ),
    4: ElementaryVisualTemplate(
        problem_text="마을별 학생 수 그림그래프에서 나 마을 학생 9명이 라 마을로 전학하면 나 마을과 라 마을 학생 수를 구하세요.",
        expression="answer_text=나 마을: 15 명, 라 마을: 24 명",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_students_after_transfer",
    ),
}


_GRADE3_2_PICTOGRAPH_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="2월 책 판매량에서 3월에는 유아 서적이 120권 덜 팔리고 학습지가 120권 더 팔렸습니다. 3월 유아 서적과 학습지 판매량을 구하세요.",
        expression="answer_text=유아 서적: 220 권, 학습지: 280 권",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_march_books",
    ),
    2: ElementaryVisualTemplate(
        problem_text="위인별 존경하는 학생 수 그림그래프에서 세종대왕을 존경하는 여학생이 4명이면 남학생 수를 구하세요.",
        expression="answer_text=6 명",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_sejong_boys",
    ),
    3: ElementaryVisualTemplate(
        problem_text="농장별 딸기 생산량 그림그래프에서 가 농장의 생산량은 나 농장의 몇 배인지 구하세요.",
        expression="answer_text=2 배",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_strawberry_ratio",
    ),
    4: ElementaryVisualTemplate(
        problem_text="윗몸일으키기 횟수 그림그래프를 보고 알 수 있는 내용을 모두 찾아 기호를 쓰세요.",
        expression="answer_text=가, 다",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_situps_true_statements",
    ),
}


_GRADE3_2_PICTOGRAPH_ROUND2_PAGE4: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="빵집에서 하루 동안 팔린 빵의 수 그림그래프에서 가장 적게 팔린 빵과 그 개수를 쓰세요.",
        expression="answer_text=식빵, 19 개",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_least_sold_bread",
    ),
    2: ElementaryVisualTemplate(
        problem_text="모둠별 학생 수 그림그래프에서 학생들에게 공책을 3권씩 나누어 주려면 공책이 모두 몇 권 필요한지 구하세요.",
        expression="answer_text=93 권",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_notebooks_needed",
    ),
    3: ElementaryVisualTemplate(
        problem_text="색깔별 좋아하는 학생 수 그림그래프에서 파란색을 좋아하는 학생은 주황색을 좋아하는 학생의 2/3일 때 초록색을 좋아하는 학생 수를 구하세요.",
        expression="answer_text=8 명",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_green_favorite_students",
    ),
    4: ElementaryVisualTemplate(
        problem_text="종류별 주스 판매량 그림그래프에서 자몽 주스를 210잔 팔았고 모든 주스 가격이 1000원일 때 네 종류의 주스를 모두 판 가격을 구하세요.",
        expression="answer_text=8400000 원",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_juice_total_price",
    ),
}


_GRADE3_2_PICTOGRAPH_ROUND2_PAGE5: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="색깔을 좋아하는 학생 수 조건과 그림그래프에서 빨간색을 좋아하는 학생 수를 구하세요.",
        expression="answer_text=22 명",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_red_favorite_students",
    ),
    2: ElementaryVisualTemplate(
        problem_text="월별 강수량 그림그래프에서 바로 전 달과 비교하여 강수량의 차가 가장 큰 달을 쓰세요.",
        expression="answer_text=9 월",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_largest_rainfall_change_month",
    ),
    3: ElementaryVisualTemplate(
        problem_text="빵집의 빵 판매량에서 가장 많이 팔린 빵과 가장 적게 팔린 빵의 차가 14개일 때 가장 많이 팔린 빵은 모두 몇 개인지 구하세요.",
        expression="answer_text=76 개",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_most_sold_bread_count",
    ),
    4: ElementaryVisualTemplate(
        problem_text="마을별 나무 수 표와 그림그래프에서 나 마을의 그림그래프를 완성하세요.",
        expression="answer_text=나 마을: 35 그루",
        topic="statistics",
        rule_id="grade3_2_pictograph_round2_village_tree_graph",
    ),
}


_GRADE3_2_PICTOGRAPH_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="키우고 싶어 하는 동물별 학생 수 그림그래프를 보고 표를 완성하세요.",
        expression="answer_text=여학생: 강아지 3, 고양이 5, 앵무새 3, 햄스터 4, 합계 15 / 남학생: 강아지 4, 고양이 4, 앵무새 5, 햄스터 3, 합계 16",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_pet_table",
    ),
    2: ElementaryVisualTemplate(
        problem_text="중국 음식별 학생 수 그림그래프에서 다음 주에 가장 많이 준비해야 하는 음식을 쓰세요.",
        expression="answer_text=짜장면",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_chinese_food_most",
    ),
    3: ElementaryVisualTemplate(
        problem_text="체육복 색깔별 학생 수 그림그래프에서 가장 많은 학생이 좋아하는 색을 쓰세요.",
        expression="answer_text=연두색",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_uniform_color_most",
    ),
    4: ElementaryVisualTemplate(
        problem_text="회사별 자동차 수출량 그림그래프를 보고 자동차는 모두 몇 대인지 구하세요.",
        expression="answer_text=1240 대",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_car_exports_total",
    ),
}


_GRADE3_2_PICTOGRAPH_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="과일 가게에서 팔린 월별 사과의 수 그림그래프를 보고 표를 완성하세요.",
        expression="answer_text=9월 45, 10월 51, 11월 72, 12월 28, 합계 196",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_monthly_apples_table",
    ),
    2: ElementaryVisualTemplate(
        problem_text="마을별 기르고 있는 돼지의 수 그림그래프에서 돼지는 모두 몇 마리인지 구하세요.",
        expression="answer_text=1340 마리",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_pigs_total",
    ),
    3: ElementaryVisualTemplate(
        problem_text="마을별 학생 수 그림그래프에서 가 마을은 나 마을보다 학생이 몇 명 더 많은지 구하세요.",
        expression="answer_text=86 명",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_students_difference",
    ),
    4: ElementaryVisualTemplate(
        problem_text="종류별 주스 판매량 그림그래프에서 4월 딸기 주스와 포도 주스 판매량을 구하세요.",
        expression="answer_text=딸기 주스: 38 병, 포도 주스: 40 병",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_juice_april_sales",
    ),
}


_GRADE3_2_PICTOGRAPH_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="기계별 밀가루 생산량 그림그래프에서 이번 주 가 기계와 라 기계의 밀가루 생산량을 각각 구하세요.",
        expression="answer_text=가 기계: 35 kg, 라 기계: 48 kg",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_flour_machines",
    ),
    2: ElementaryVisualTemplate(
        problem_text="학교 행사별 학생 수 그림그래프에서 운동회가 가장 기억에 남는 남학생이 15명일 때 여학생 수를 구하세요.",
        expression="answer_text=16 명",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_school_event_girls",
    ),
    3: ElementaryVisualTemplate(
        problem_text="혈액형별 학생 수 그림그래프에서 O형 학생 수는 AB형 학생 수의 몇 배인지 구하세요.",
        expression="answer_text=2 배",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_blood_type_ratio",
    ),
    4: ElementaryVisualTemplate(
        problem_text="계절별 학생 수 그림그래프에서 여름을 좋아하는 여학생이 17명이면 여름을 좋아하는 남학생 수를 구하세요.",
        expression="answer_text=15 명",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_summer_boys",
    ),
}


_GRADE3_2_PICTOGRAPH_ROUND3_PAGE4: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="혈액형별 학생 수 그림그래프를 보고 알 수 있는 내용을 모두 고르세요.",
        expression="answer_text=나, 다",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_blood_type_true_statements",
    ),
    2: ElementaryVisualTemplate(
        problem_text="간식별 학생 수 그림그래프에서 과자를 좋아하는 학생은 사탕과 젤리를 좋아하는 학생보다 몇 명 더 적은지 구하세요.",
        expression="answer_text=4 명",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_snack_difference",
    ),
    3: ElementaryVisualTemplate(
        problem_text="학년별 학생 수 그림그래프에서 3학년부터 6학년까지 학생들에게 연필을 2자루씩 나누어 주려면 필요한 연필 수를 구하세요.",
        expression="answer_text=1142 자루",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_pencils_needed",
    ),
    4: ElementaryVisualTemplate(
        problem_text="취미별 좋아하는 학생 수 그림그래프에서 그림그리기가 취미인 학생 수를 구하세요.",
        expression="answer_text=9 명",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_drawing_hobby_students",
    ),
}


_GRADE3_2_PICTOGRAPH_ROUND3_PAGE5: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="4일 동안 사과 판매량 그림그래프에서 수요일에는 38개를 팔았고 사과 가격이 2000원일 때 4일 동안 모두 판 가격을 구하세요.",
        expression="answer_text=2280000 원",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_apple_sales_price",
    ),
    2: ElementaryVisualTemplate(
        problem_text="색깔별 좋아하는 학생 수 조건과 그림그래프에서 파란색을 좋아하는 학생 수를 구하세요.",
        expression="answer_text=23 명",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_blue_favorite_students",
    ),
    3: ElementaryVisualTemplate(
        problem_text="일주일 동안 팔린 종류별 음식의 수 그림그래프에서 비빔밥과 냉면은 각각 몇 그릇인지 구하세요.",
        expression="answer_text=비빔밥: 430 그릇, 냉면: 150 그릇",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_food_sales_counts",
    ),
    4: ElementaryVisualTemplate(
        problem_text="마을별 인터넷 사용 가구 수 표를 보고 그림그래프로 나타내세요.",
        expression="answer_text=가 마을: 150 가구, 다 마을: 130 가구",
        topic="statistics",
        rule_id="grade3_2_pictograph_round3_internet_households_graph",
    ),
}


_GRADE3_2_MULTIPLICATION_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="70×40=㉠00, 60×80=㉡00일 때 ㉠과 ㉡에 알맞은 수의 합을 구하세요.",
        expression="answer=76",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round1_tens_products_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="413×2와 331×3의 계산 결과를 관계있는 것끼리 선으로 이으세요.",
        expression="answer_text=(1)-③, (2)-①",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round1_match_products",
    ),
    3: ElementaryVisualTemplate(
        problem_text="20×30, 20×90의 빈 곳에 알맞은 수를 쓰세요.",
        expression="answer_text=600, 1800",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round1_table_blanks",
    ),
    4: ElementaryVisualTemplate(
        problem_text="762×2, 797×2, 344×5, 234×7, 536×3 중 곱이 가장 큰 것을 고르세요.",
        expression="answer_text=③",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round1_largest_product_choice",
    ),
    5: ElementaryVisualTemplate(
        problem_text="한 변이 211 cm인 정사각형의 네 변의 길이의 합을 구하세요.",
        expression="answer_text=844 cm",
        topic="measurement",
        rule_id="grade3_2_multiplication_round1_square_perimeter_211cm",
    ),
    6: ElementaryVisualTemplate(
        problem_text="세로셈 □22×2=84□에서 □ 안에 알맞은 수를 쓰세요.",
        expression="answer_text=4, 4",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round1_vertical_422_times_2_blanks",
    ),
    7: ElementaryVisualTemplate(
        problem_text="19×64와 73×17을 계산하세요.",
        expression="answer_text=⑴ 1216 ⑵ 1241",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round1_vertical_products",
    ),
}


_GRADE3_2_MULTIPLICATION_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="10이 6개, 1이 3개인 수와 10이 8개인 수의 곱을 구하세요.",
        expression="answer=5040",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round1_place_value_product",
    ),
    2: ElementaryVisualTemplate(
        problem_text="4×72, 6×47, 8×33의 계산 결과가 작은 순서대로 기호를 쓰세요.",
        expression="answer_text=다, 나, 가",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round1_order_products_ascending",
    ),
    3: ElementaryVisualTemplate(
        problem_text="35, 57, 18, 41 중 가장 큰 수와 가장 작은 수의 곱을 구하세요.",
        expression="answer=1026",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round1_largest_smallest_product",
    ),
    4: ElementaryVisualTemplate(
        problem_text="24×32를 바르게 계산하세요.",
        expression="answer=768",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round1_correct_24_times_32",
    ),
    5: ElementaryVisualTemplate(
        problem_text="147 cm 리본 6개와 218 cm 리본 4개를 이어 붙인 전체 길이를 구하세요.",
        expression="answer_text=1754 cm",
        topic="measurement",
        rule_id="grade3_2_multiplication_round1_ribbon_total_length",
    ),
    6: ElementaryVisualTemplate(
        problem_text="540번씩 7일, 485번씩 8일 줄넘기를 했을 때 누가 몇 번 더 했는지 구하세요.",
        expression="answer_text=인영, 100 번",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round1_jump_rope_difference",
    ),
    7: ElementaryVisualTemplate(
        problem_text="숫자 카드 2, 3, 6, 7로 (세 자리 수)×(한 자리 수)의 가장 작은 곱을 구하세요.",
        expression="answer=734",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round1_min_three_digit_times_one_digit",
    ),
}


_GRADE3_2_MULTIPLICATION_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="매일 윗몸일으키기를 90번씩 4월 한 달 동안 했을 때 모두 몇 번인지 구하세요.",
        expression="answer_text=2700 번",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round1_situps_april_total",
    ),
    2: ElementaryVisualTemplate(
        problem_text="남학생 13명, 여학생 12명에게 젤리를 40개씩 나누어 줄 때 필요한 젤리 수를 구하세요.",
        expression="answer_text=1000 개",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round1_jellies_for_class",
    ),
    3: ElementaryVisualTemplate(
        problem_text="전봇대 6그루가 79 m 간격으로 세워져 있을 때 도로의 길이를 구하세요.",
        expression="answer_text=395 m",
        topic="measurement",
        rule_id="grade3_2_multiplication_round1_poles_road_length",
    ),
    4: ElementaryVisualTemplate(
        problem_text="지우개가 한 상자에 58개씩 24상자에 들어 있을 때 모두 몇 개인지 구하세요.",
        expression="answer_text=1392 개",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round1_erasers_total",
    ),
    5: ElementaryVisualTemplate(
        problem_text="사과 34개씩 50상자 중 24개씩 64상자를 판 뒤 남은 사과 수를 구하세요.",
        expression="answer_text=164 개",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round1_apples_remaining",
    ),
    6: ElementaryVisualTemplate(
        problem_text="가♥나=(가×나)+(7×나)일 때 47♥65를 계산하세요.",
        expression="answer=3510",
        topic="arithmetic",
        rule_id="grade3_2_multiplication_round1_custom_heart_operation",
    ),
}


_GRADE3_MULTIPLICATION_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="2×60, 4×60, 6×60의 값을 구하세요.",
        expression="answer_text=120, 240, 360",
        rule_id="grade3_multiplication_round1_multiples_of_60",
    ),
    2: ElementaryVisualTemplate(
        problem_text="30×□=90×2에서 □ 안에 알맞은 수를 구하세요.",
        expression="answer=6",
        rule_id="grade3_multiplication_round1_missing_factor_equal_product",
    ),
    3: ElementaryVisualTemplate(
        problem_text="31×3과 계산 결과가 다른 것은 어느 것입니까?",
        expression="answer_text=⑤",
        rule_id="grade3_multiplication_round1_different_expression_choice",
    ),
    4: ElementaryVisualTemplate(
        problem_text="계산 흐름도에서 빈칸 ㉠, ㉡에 알맞은 수를 쓰세요.",
        expression="answer_text=㉠ 24, ㉡ 48",
        rule_id="grade3_multiplication_round1_times_two_flow",
    ),
    5: ElementaryVisualTemplate(
        problem_text="30×3과 23×3의 곱의 크기를 비교하세요.",
        expression="answer_text=>",
        rule_id="grade3_multiplication_round1_compare_products",
    ),
    6: ElementaryVisualTemplate(
        problem_text="세로셈에서 □ 안에 알맞은 숫자를 쓰세요.",
        expression="answer_text=㉠ 2, ㉡ 9",
        rule_id="grade3_multiplication_round1_vertical_multiplication_blanks",
    ),
    7: ElementaryVisualTemplate(
        problem_text="곱셈표의 빈칸 ㉠, ㉡, ㉢에 알맞은 수를 쓰세요.",
        expression="answer_text=㉠ 106, ㉡ 128, ㉢ 144",
        rule_id="grade3_multiplication_round1_table_row_times_2",
    ),
    8: ElementaryVisualTemplate(
        problem_text="곱셈식에서 □ 안의 숫자 3이 나타내는 수를 구하세요.",
        expression="answer=30",
        rule_id="grade3_multiplication_round1_digit_value_in_multiplication",
    ),
    9: ElementaryVisualTemplate(
        problem_text="곱셈표에서 ㉠, ㉡, ㉢, ㉣에 알맞은 수를 구하세요.",
        expression="answer_text=㉠ 84, ㉡ 144, ㉢ 56, ㉣ 216",
        rule_id="grade3_multiplication_round1_multiplication_grid",
    ),
}


_GRADE3_MULTIPLICATION_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="75×4와 64×4를 계산하세요.",
        expression="answer_text=(1) 300, (2) 256",
        rule_id="grade3_multiplication_round1_vertical_products",
    ),
    2: ElementaryVisualTemplate(
        problem_text="33×7, 19×5, 64×2, 26×3의 계산 결과가 큰 것부터 차례대로 쓰세요.",
        expression="answer_text=가, 다, 나, 라",
        rule_id="grade3_multiplication_round1_order_products_desc",
    ),
    3: ElementaryVisualTemplate(
        problem_text="한 변의 길이가 19 cm인 정사각형의 네 변의 길이의 합을 구하세요.",
        expression="answer_text=76 cm",
        topic="measurement",
        rule_id="grade3_multiplication_round1_square_perimeter",
    ),
    4: ElementaryVisualTemplate(
        problem_text="어떤 수에 36을 더한 수는 어떤 수에 4를 곱한 수와 같습니다. 어떤 수를 구하세요.",
        expression="answer=12",
        rule_id="grade3_multiplication_round1_unknown_number_equation",
    ),
    5: ElementaryVisualTemplate(
        problem_text="꿀 12개씩 4묶음과 사과 23개씩 2묶음을 모두 합하면 몇 개인지 구하세요.",
        expression="answer_text=94 개",
        rule_id="grade3_multiplication_round1_total_honey_apples",
    ),
    6: ElementaryVisualTemplate(
        problem_text="하루에 30분씩 3일 동안 아침 운동을 한 시간은 모두 몇 분입니까?",
        expression="answer_text=90 분",
        topic="measurement",
        rule_id="grade3_multiplication_round1_exercise_minutes",
    ),
    7: ElementaryVisualTemplate(
        problem_text="철희는 한 시간 동안 21개, 지우는 32개의 딱지를 접습니다. 두 사람이 2시간 동안 접은 딱지는 모두 몇 개입니까?",
        expression="answer_text=106 개",
        rule_id="grade3_multiplication_round1_paper_ttakji_total",
    ),
    8: ElementaryVisualTemplate(
        problem_text="위인전을 하루에 63쪽씩 3일 동안 읽었습니다. 모두 몇 쪽을 읽었습니까?",
        expression="answer_text=189 쪽",
        rule_id="grade3_multiplication_round1_pages_read",
    ),
    9: ElementaryVisualTemplate(
        problem_text="색종이가 한 상자에 42장씩 3상자 있습니다. 한 상자에 21장씩 담으면 몇 상자가 되는지 구하세요.",
        expression="answer_text=6 상자",
        rule_id="grade3_multiplication_round1_colored_paper_boxes",
    ),
    10: ElementaryVisualTemplate(
        problem_text="어떤 수에 8을 곱해야 할 것을 잘못하여 더하였더니 20이 되었습니다. 바르게 계산하면 얼마입니까?",
        expression="answer=96",
        rule_id="grade3_multiplication_round1_wrong_add_instead_of_multiply",
    ),
    11: ElementaryVisualTemplate(
        problem_text="승용차 바퀴 150개 중 바퀴가 4개인 승용차 28대에 달고 남은 바퀴는 몇 개입니까?",
        expression="answer_text=38 개",
        rule_id="grade3_multiplication_round1_remaining_car_wheels",
    ),
}


_GRADE3_MULTIPLICATION_ROUND2_PAGE1_FULL: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="40×6을 계산하세요.",
        expression="answer=240",
        rule_id="grade3_multiplication_round2_40_times_6",
    ),
    2: ElementaryVisualTemplate(
        problem_text="21과 4의 곱을 빈 곳에 쓰세요.",
        expression="answer=84",
        rule_id="grade3_multiplication_round2_21_times_4",
    ),
    3: ElementaryVisualTemplate(
        problem_text="94와 2의 곱을 구하세요.",
        expression="answer=188",
        rule_id="grade3_multiplication_round2_94_times_2",
    ),
    4: ElementaryVisualTemplate(
        problem_text="계산 결과에 맞게 선으로 이어 보세요.",
        expression="answer_text=26×3-78, 14×6-84, 38×2-76",
        rule_id="grade3_multiplication_round2_match_products",
    ),
    5: ElementaryVisualTemplate(
        problem_text="32×8과 답이 같은 것을 찾아 ○표 하세요.",
        expression="answer_text=가운데 식에 ○표",
        rule_id="grade3_multiplication_round2_same_product_choice",
    ),
    6: ElementaryVisualTemplate(
        problem_text="계산 흐름도에서 21에 2를 곱하고 3을 곱한 값을 구하세요.",
        expression="answer=126",
        rule_id="grade3_multiplication_round2_times_flow",
    ),
    7: ElementaryVisualTemplate(
        problem_text="16, 6, 29, 9 중 가장 큰 수와 두 번째로 작은 수의 곱을 구하세요.",
        expression="answer=261",
        rule_id="grade3_multiplication_round2_largest_second_smallest_product",
    ),
    8: ElementaryVisualTemplate(
        problem_text="46×3 계산에서 잘못된 부분을 찾아 바르게 고치세요.",
        expression="answer=138",
        rule_id="grade3_multiplication_round2_fix_46_times_3",
    ),
    9: ElementaryVisualTemplate(
        problem_text="52×3과 71×4를 곱하여 두 계산 결과의 합을 구하세요.",
        expression="answer=440",
        rule_id="grade3_multiplication_round2_sum_two_products",
    ),
    10: ElementaryVisualTemplate(
        problem_text="23×6, 61×3, 53×4 중 곱이 200보다 큰 것에 ○표 하세요.",
        expression="answer_text=오른쪽 식에 ○표",
        rule_id="grade3_multiplication_round2_product_greater_than_200",
    ),
}


_GRADE3_MULTIPLICATION_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="50×□<450에서 □ 안에 들어갈 수 있는 가장 큰 자연수를 구하세요.",
        expression="answer=8",
        rule_id="grade3_multiplication_round2_largest_blank_under_450",
    ),
    2: ElementaryVisualTemplate(
        problem_text="공책은 13권씩 3묶음, 연필은 12자루씩 4타 있습니다. 연필은 공책보다 몇 자루 더 많습니까?",
        expression="answer_text=9 자루",
        rule_id="grade3_multiplication_round2_pencils_more_than_notebooks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="학생들이 12명씩 7줄로 서 있습니다. 모두 몇 명입니까?",
        expression="answer_text=84 명",
        rule_id="grade3_multiplication_round2_students_rows",
    ),
    4: ElementaryVisualTemplate(
        problem_text="동화책을 하루에 37쪽씩 5일 동안 읽으면 모두 몇 쪽을 읽습니까?",
        expression="answer_text=185 쪽",
        rule_id="grade3_multiplication_round2_book_pages",
    ),
    5: ElementaryVisualTemplate(
        problem_text="어머니의 연세가 37세이고 할머니의 연세가 2배이면 할머니의 연세는 몇 세입니까?",
        expression="answer_text=74 세",
        rule_id="grade3_multiplication_round2_age_double",
    ),
    6: ElementaryVisualTemplate(
        problem_text="한 변의 길이가 33 cm인 정사각형을 만드는 데 사용한 철사의 길이를 구하세요.",
        expression="answer_text=132 cm",
        topic="measurement",
        rule_id="grade3_multiplication_round2_square_wire_length",
    ),
    7: ElementaryVisualTemplate(
        problem_text="초콜릿이 한 봉지에 20개씩 4봉지 있습니다. 14개를 먹고 남은 초콜릿은 모두 몇 개입니까?",
        expression="answer_text=66 개",
        rule_id="grade3_multiplication_round2_remaining_chocolates",
    ),
    8: ElementaryVisualTemplate(
        problem_text="두발자전거 34대와 세발자전거 21대의 바퀴는 모두 몇 개입니까?",
        expression="answer_text=131 개",
        rule_id="grade3_multiplication_round2_bicycle_wheels",
    ),
    9: ElementaryVisualTemplate(
        problem_text="여학생 17명, 남학생 18명에게 한 사람에게 연필 4자루씩 나누어 주려면 모두 몇 자루 필요합니까?",
        expression="answer_text=140 자루",
        rule_id="grade3_multiplication_round2_pencils_for_students",
    ),
    10: ElementaryVisualTemplate(
        problem_text="길이가 39 cm인 색 테이프 5장을 겹치는 부분의 길이를 같게 하여 183 cm가 되게 이었습니다. 몇 cm씩 겹치게 이었습니까?",
        expression="answer_text=3 cm",
        topic="measurement",
        rule_id="grade3_multiplication_round2_tape_overlap_length",
    ),
}


_GRADE3_MULTIPLICATION_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="50×8을 계산하세요.",
        expression="answer=400",
        rule_id="grade3_multiplication_round3_50_times_8",
    ),
    2: ElementaryVisualTemplate(
        problem_text="33과 3의 곱을 빈 곳에 쓰세요.",
        expression="answer=99",
        rule_id="grade3_multiplication_round3_33_times_3",
    ),
    3: ElementaryVisualTemplate(
        problem_text="73과 2의 곱을 구하세요.",
        expression="answer=146",
        rule_id="grade3_multiplication_round3_73_times_2",
    ),
    4: ElementaryVisualTemplate(
        problem_text="계산 결과에 맞게 선으로 이어 보세요.",
        expression="answer_text=28×2-56, 16×5-80, 18×4-72",
        rule_id="grade3_multiplication_round3_match_products",
    ),
    5: ElementaryVisualTemplate(
        problem_text="26×4와 답이 같은 것을 찾아 ○표 하세요.",
        expression="answer_text=오른쪽 식에 ○표",
        rule_id="grade3_multiplication_round3_same_product_choice",
    ),
    6: ElementaryVisualTemplate(
        problem_text="계산 흐름도에서 21에 4를 곱하고 2를 곱한 값을 구하세요.",
        expression="answer=168",
        rule_id="grade3_multiplication_round3_times_flow",
    ),
    7: ElementaryVisualTemplate(
        problem_text="3, 26, 5, 9, 12 중 가장 큰 수와 세 번째로 작은 수의 곱을 구하세요.",
        expression="answer=234",
        rule_id="grade3_multiplication_round3_largest_third_smallest_product",
    ),
    8: ElementaryVisualTemplate(
        problem_text="53×5 계산에서 잘못된 부분을 찾아 바르게 고치세요.",
        expression="answer=265",
        rule_id="grade3_multiplication_round3_fix_53_times_5",
    ),
    9: ElementaryVisualTemplate(
        problem_text="42×4와 62×2를 곱하여 두 계산 결과의 차를 구하세요.",
        expression="answer=44",
        rule_id="grade3_multiplication_round3_difference_two_products",
    ),
    10: ElementaryVisualTemplate(
        problem_text="31×7, 65×3, 24×9 중 곱이 200보다 작은 것에 ○표 하세요.",
        expression="answer_text=가운데 식에 ○표",
        rule_id="grade3_multiplication_round3_product_less_than_200",
    ),
}


_GRADE3_MULTIPLICATION_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="31×7, 65×3, 24×9 중 곱이 200보다 작은 것에 ○표 하세요.",
        expression="answer_text=가운데 식에 ○표",
        rule_id="grade3_multiplication_round3_product_less_than_200_page2",
    ),
    2: ElementaryVisualTemplate(
        problem_text="59×□<400에서 □ 안에 들어갈 수 있는 가장 큰 자연수를 구하세요.",
        expression="answer=6",
        rule_id="grade3_multiplication_round3_largest_blank_under_400",
    ),
    3: ElementaryVisualTemplate(
        problem_text="필통 한 개에 연필이 14자루씩 들어갑니다. 필통 2개에는 모두 몇 자루를 넣을 수 있습니까?",
        expression="answer_text=28 자루",
        rule_id="grade3_multiplication_round3_pencils_two_cases",
    ),
    4: ElementaryVisualTemplate(
        problem_text="학급 문고에 위인전이 15권씩 5칸에 꽂혀 있습니다. 위인전은 모두 몇 권입니까?",
        expression="answer_text=75 권",
        rule_id="grade3_multiplication_round3_biographies_bookshelf",
    ),
    5: ElementaryVisualTemplate(
        problem_text="6명이 한 사람당 종이학을 75마리씩 접었습니다. 모두 몇 마리입니까?",
        expression="answer_text=450 마리",
        rule_id="grade3_multiplication_round3_paper_cranes_total",
    ),
    6: ElementaryVisualTemplate(
        problem_text="한 통에 18가지 색이 들어 있는 크레파스를 5통 샀습니다. 모두 몇 개입니까?",
        expression="answer_text=90 개",
        rule_id="grade3_multiplication_round3_crayons_total",
    ),
    7: ElementaryVisualTemplate(
        problem_text="한 변의 길이가 21 cm인 정사각형 모양을 만드는 데 필요한 철사의 길이를 구하세요.",
        expression="answer_text=84 cm",
        topic="measurement",
        rule_id="grade3_multiplication_round3_square_wire_length",
    ),
    8: ElementaryVisualTemplate(
        problem_text="계란 30개씩 들어 있는 판 3판과 낱개 5개를 모두 합하면 몇 개입니까?",
        expression="answer_text=95 개",
        rule_id="grade3_multiplication_round3_eggs_total",
    ),
    9: ElementaryVisualTemplate(
        problem_text="12점짜리 4문제와 8점짜리 11문제를 맞추었습니다. 모두 몇 점입니까?",
        expression="answer_text=136 점",
        rule_id="grade3_multiplication_round3_test_score_total",
    ),
    10: ElementaryVisualTemplate(
        problem_text="사과가 한 상자에 69개씩 들어 있습니다. 34상자 중 27상자가 남았을 때 오늘 판 사과는 모두 몇 개입니까?",
        expression="answer_text=483 개",
        rule_id="grade3_multiplication_round3_sold_apples",
    ),
    11: ElementaryVisualTemplate(
        problem_text="길이가 28 cm인 색 테이프 8장을 일정한 간격으로 겹쳐 전체 길이가 161 cm가 되었습니다. 몇 cm씩 겹치게 붙인 것입니까?",
        expression="answer_text=9 cm",
        topic="measurement",
        rule_id="grade3_multiplication_round3_tape_overlap_length",
    ),
}


_GRADE3_LENGTH_TIME_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="82 mm를 cm와 mm로 나타내세요.",
        expression="answer_text=8, 2",
        topic="measurement",
        rule_id="grade3_length_time_round1_82mm_to_cm_mm",
    ),
    2: ElementaryVisualTemplate(
        problem_text="2분 40초를 초로 나타내세요.",
        expression="answer=160",
        topic="measurement",
        rule_id="grade3_length_time_round1_2m40s_to_seconds",
    ),
    3: ElementaryVisualTemplate(
        problem_text="연필의 길이와 키에 알맞은 단위 cm와 mm를 쓰세요.",
        expression="answer_text=mm, cm",
        topic="measurement",
        rule_id="grade3_length_time_round1_units_cm_mm",
    ),
    4: ElementaryVisualTemplate(
        problem_text="같은 길이끼리 선으로 이어 보세요.",
        expression="answer_text=6km400m-6400m, 6km40m-6040m, 6km4m-6004m",
        topic="measurement",
        rule_id="grade3_length_time_round1_match_lengths",
    ),
    5: ElementaryVisualTemplate(
        problem_text="15 cm보다 6 mm 더 긴 연필의 길이를 cm와 mm, mm 두 가지 방법으로 나타내세요.",
        expression="answer_text=㉠ 15 cm 6 mm, ㉡ 156 mm",
        topic="measurement",
        rule_id="grade3_length_time_round1_pencil_length_two_units",
    ),
    6: ElementaryVisualTemplate(
        problem_text="cm와 mm 덧셈 표의 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=㉠ 13, ㉡ 4, ㉢ 4, ㉣ 3",
        topic="measurement",
        rule_id="grade3_length_time_round1_cm_mm_addition_table",
    ),
    7: ElementaryVisualTemplate(
        problem_text="7 km 940 m와 6 km 680 m의 합을 구하세요.",
        expression="answer_text=14 km 620 m",
        topic="measurement",
        rule_id="grade3_length_time_round1_km_m_sum",
    ),
    8: ElementaryVisualTemplate(
        problem_text="cm와 mm 뺄셈 표의 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=㉠ 1, ㉡ 7, ㉢ 3, ㉣ 8",
        topic="measurement",
        rule_id="grade3_length_time_round1_cm_mm_subtraction_table",
    ),
}


_GRADE3_LENGTH_TIME_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="4 km 750 m+2 km 300 m와 9 km 250 m-1 km 700 m 중 길이가 더 긴 곳의 기호를 쓰세요.",
        expression="answer_text=나",
        topic="measurement",
        rule_id="grade3_length_time_round1_longer_length_choice",
    ),
    2: ElementaryVisualTemplate(
        problem_text="직사각형에서 긴 변과 짧은 변의 길이의 차를 구하세요.",
        expression="answer_text=6 cm 6 mm",
        topic="measurement",
        rule_id="grade3_length_time_round1_rectangle_side_difference",
    ),
    3: ElementaryVisualTemplate(
        problem_text="4분 20초를 초로 나타내세요.",
        expression="answer_text=240, 260",
        topic="measurement",
        rule_id="grade3_length_time_round1_4m20s_to_seconds_steps",
    ),
    4: ElementaryVisualTemplate(
        problem_text="시계가 나타내는 시각의 초를 쓰세요.",
        expression="answer=25",
        topic="measurement",
        rule_id="grade3_length_time_round1_analog_clock_seconds",
    ),
    5: ElementaryVisualTemplate(
        problem_text="디지털 시계 08:16:23을 시, 분, 초로 읽어 보세요.",
        expression="answer_text=8, 16, 23",
        topic="measurement",
        rule_id="grade3_length_time_round1_read_digital_clock",
    ),
    6: ElementaryVisualTemplate(
        problem_text="370초와 5분 50초의 시간 길이를 비교하세요.",
        expression="answer_text=>",
        topic="measurement",
        rule_id="grade3_length_time_round1_compare_seconds_minutes",
    ),
    7: ElementaryVisualTemplate(
        problem_text="5시 32분 46초와 2시간 51분 36초를 더하세요.",
        expression="answer_text=8 시간 24 분 22 초",
        topic="measurement",
        rule_id="grade3_length_time_round1_time_addition",
    ),
    8: ElementaryVisualTemplate(
        problem_text="4시 32분 42초에서 1시간 22분 50초를 빼세요.",
        expression="answer_text=3 시 9 분 52 초",
        topic="measurement",
        rule_id="grade3_length_time_round1_time_subtraction",
    ),
    9: ElementaryVisualTemplate(
        problem_text="107 mm를 cm와 mm로 나타내세요.",
        expression="answer_text=10 cm 7 mm",
        topic="measurement",
        rule_id="grade3_length_time_round1_107mm_to_cm_mm",
    ),
}


_GRADE3_LENGTH_TIME_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="3 km보다 800 m 더 먼 거리를 m로 나타내세요.",
        expression="answer_text=3800 m",
        topic="measurement",
        rule_id="grade3_length_time_round1_3km_plus_800m",
    ),
    2: ElementaryVisualTemplate(
        problem_text="오후 3시 24분 13초에 시작해서 2시간 5분 48초 뒤에 끝난 시각을 구하세요.",
        expression="answer_text=5 시 30 분 1 초",
        topic="measurement",
        rule_id="grade3_length_time_round1_soccer_end_time",
    ),
    3: ElementaryVisualTemplate(
        problem_text="영어와 수학을 공부한 시간의 합을 구하세요.",
        expression="answer_text=3 시간 31 분 38 초",
        topic="measurement",
        rule_id="grade3_length_time_round1_study_time_total",
    ),
}


_GRADE3_LENGTH_TIME_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="길이를 잘못 읽은 것을 고르세요.",
        expression="answer_text=③",
        topic="measurement",
        rule_id="grade3_length_time_round2_wrong_length_reading",
    ),
    2: ElementaryVisualTemplate(
        problem_text="연필의 길이를 mm 단위까지 재어 cm와 mm로 나타내세요.",
        expression="answer_text=6, 7",
        topic="measurement",
        rule_id="grade3_length_time_round2_pencil_length_cm_mm",
    ),
    3: ElementaryVisualTemplate(
        problem_text="시각을 읽어 시, 분, 초를 쓰세요.",
        expression="answer_text=9, 22, 56",
        topic="measurement",
        rule_id="grade3_length_time_round2_read_clock",
    ),
    4: ElementaryVisualTemplate(
        problem_text="1 cm의 길이와 같은 것에 ○표 하세요.",
        expression="answer_text=10 mm",
        topic="measurement",
        rule_id="grade3_length_time_round2_1cm_same_length",
    ),
    5: ElementaryVisualTemplate(
        problem_text="수직선을 보고 □ 안에 알맞은 m 수를 쓰세요.",
        expression="answer_text=2600 m",
        topic="measurement",
        rule_id="grade3_length_time_round2_number_line_meters",
    ),
    6: ElementaryVisualTemplate(
        problem_text="다음 시각 중 초를 쓰기에 알맞은 경우를 고르세요.",
        expression="answer_text=④",
        topic="measurement",
        rule_id="grade3_length_time_round2_seconds_context",
    ),
    7: ElementaryVisualTemplate(
        problem_text="7 cm 9 mm를 mm로 나타내세요.",
        expression="answer=79",
        topic="measurement",
        rule_id="grade3_length_time_round2_7cm9mm_to_mm",
    ),
    8: ElementaryVisualTemplate(
        problem_text="10분 30초를 초로 나타내세요.",
        expression="answer=630",
        topic="measurement",
        rule_id="grade3_length_time_round2_10m30s_to_seconds",
    ),
    9: ElementaryVisualTemplate(
        problem_text="다음 중 틀린 것을 고르세요.",
        expression="answer_text=③",
        topic="measurement",
        rule_id="grade3_length_time_round2_wrong_comparison",
    ),
}


_GRADE3_LENGTH_TIME_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="13 km 160 m와 14 km 982 m의 합을 km와 m로 나타내세요.",
        expression="answer_text=28 km 142 m",
        topic="measurement",
        rule_id="grade3_length_time_round2_two_lengths_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="다음 중 단위의 사용이 바른 것을 고르세요.",
        expression="answer_text=②",
        topic="measurement",
        rule_id="grade3_length_time_round2_correct_unit_usage",
    ),
    3: ElementaryVisualTemplate(
        problem_text="단위 사이의 관계를 잘못 나타낸 것을 모두 찾으세요.",
        expression="answer_text=㉠, ㉣",
        topic="measurement",
        rule_id="grade3_length_time_round2_wrong_unit_relations",
    ),
    4: ElementaryVisualTemplate(
        problem_text="4시간 40분 27초와 1시간 35분 46초의 합을 구하세요.",
        expression="answer_text=6 시간 16 분 13 초",
        topic="measurement",
        rule_id="grade3_length_time_round2_time_addition",
    ),
    5: ElementaryVisualTemplate(
        problem_text="연필의 길이 8 cm 2 mm를 mm로 나타내세요.",
        expression="answer_text=82 mm",
        topic="measurement",
        rule_id="grade3_length_time_round2_pencil_length_mm",
    ),
    6: ElementaryVisualTemplate(
        problem_text="1 km보다 200 m 더 먼 거리를 m로 나타내세요.",
        expression="answer_text=1200 m",
        topic="measurement",
        rule_id="grade3_length_time_round2_1km_plus_200m",
    ),
    7: ElementaryVisualTemplate(
        problem_text="12시 10분 15초부터 25분 32초 동안 점심을 먹었습니다. 끝난 시각을 구하세요.",
        expression="answer_text=12 시 35 분 47 초",
        topic="measurement",
        rule_id="grade3_length_time_round2_lunch_end_time",
    ),
    8: ElementaryVisualTemplate(
        problem_text="2분 53초와 2분 26초의 차를 초로 구하세요.",
        expression="answer_text=27 초",
        topic="measurement",
        rule_id="grade3_length_time_round2_running_time_difference",
    ),
    9: ElementaryVisualTemplate(
        problem_text="54 km 185 m 중 51 km 지점까지 왔을 때 남은 거리를 m로 구하세요.",
        expression="answer_text=3185 m",
        topic="measurement",
        rule_id="grade3_length_time_round2_remaining_distance",
    ),
    10: ElementaryVisualTemplate(
        problem_text="첫 번째 수업이 오후 4시 20분에 시작하고 50분 수업, 15분 휴식일 때 두 번째 수업 시작 시각을 구하세요.",
        expression="answer_text=오후 5 시 25 분",
        topic="measurement",
        rule_id="grade3_length_time_round2_second_class_start",
    ),
    11: ElementaryVisualTemplate(
        problem_text="7 cm 2 mm인 철사로 같은 크기의 정사각형 2개를 만들 때 한 변의 길이를 mm로 구하세요.",
        expression="answer_text=9 mm",
        topic="measurement",
        rule_id="grade3_length_time_round2_square_side_from_wire",
    ),
}


_GRADE3_LENGTH_TIME_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="길이를 잘못 읽은 것을 고르세요.",
        expression="answer_text=②",
        topic="measurement",
        rule_id="grade3_length_time_round3_wrong_length_reading",
    ),
    2: ElementaryVisualTemplate(
        problem_text="색테이프의 길이는 6 cm보다 몇 mm 더 긴지 쓰세요.",
        expression="answer=4",
        topic="measurement",
        rule_id="grade3_length_time_round3_tape_length_extra_mm",
    ),
    3: ElementaryVisualTemplate(
        problem_text="시각을 읽어 시, 분, 초를 쓰세요.",
        expression="answer_text=12, 53, 28",
        topic="measurement",
        rule_id="grade3_length_time_round3_read_clock",
    ),
    4: ElementaryVisualTemplate(
        problem_text="100 mm의 길이와 같은 것에 ○표 하세요.",
        expression="answer_text=10 cm",
        topic="measurement",
        rule_id="grade3_length_time_round3_100mm_same_length",
    ),
    5: ElementaryVisualTemplate(
        problem_text="수직선을 보고 □ 안에 알맞은 m 수를 쓰세요.",
        expression="answer_text=4800 m",
        topic="measurement",
        rule_id="grade3_length_time_round3_number_line_meters",
    ),
    6: ElementaryVisualTemplate(
        problem_text="다음 중 1초 동안 할 수 있는 일로 알맞은 것을 고르세요.",
        expression="answer_text=②",
        topic="measurement",
        rule_id="grade3_length_time_round3_one_second_context",
    ),
    7: ElementaryVisualTemplate(
        problem_text="25 cm 3 mm를 mm로 나타내세요.",
        expression="answer=253",
        topic="measurement",
        rule_id="grade3_length_time_round3_25cm3mm_to_mm",
    ),
    8: ElementaryVisualTemplate(
        problem_text="15분 35초를 초로 나타내세요.",
        expression="answer=935",
        topic="measurement",
        rule_id="grade3_length_time_round3_15m35s_to_seconds",
    ),
    9: ElementaryVisualTemplate(
        problem_text="다음 중 틀린 것을 고르세요.",
        expression="answer_text=②",
        topic="measurement",
        rule_id="grade3_length_time_round3_wrong_comparison",
    ),
}


_GRADE3_LENGTH_TIME_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="5 km 500 m와 7 km 900 m의 합을 km와 m로 나타내세요.",
        expression="answer_text=13 km 400 m",
        topic="measurement",
        rule_id="grade3_length_time_round3_two_lengths_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="다음 중 길이가 약 5 mm인 것을 고르세요.",
        expression="answer_text=⑤",
        topic="measurement",
        rule_id="grade3_length_time_round3_about_5mm_choice",
    ),
    3: ElementaryVisualTemplate(
        problem_text="단위를 잘못 사용한 것을 모두 찾으세요.",
        expression="answer_text=㉡, ㉣",
        topic="measurement",
        rule_id="grade3_length_time_round3_wrong_unit_usage",
    ),
    4: ElementaryVisualTemplate(
        problem_text="영화가 3시 45분에 시작하여 130분 후에 끝났습니다. 끝난 시각을 구하세요.",
        expression="answer_text=5 시 55 분",
        topic="measurement",
        rule_id="grade3_length_time_round3_movie_end_time",
    ),
    5: ElementaryVisualTemplate(
        problem_text="발의 길이 21 cm 4 mm를 mm로 나타내세요.",
        expression="answer_text=214 mm",
        topic="measurement",
        rule_id="grade3_length_time_round3_foot_length_mm",
    ),
    6: ElementaryVisualTemplate(
        problem_text="2 km보다 800 m 더 먼 거리를 m로 나타내세요.",
        expression="answer_text=2800 m",
        topic="measurement",
        rule_id="grade3_length_time_round3_2km_plus_800m",
    ),
    7: ElementaryVisualTemplate(
        problem_text="4시 20분 33초부터 35분 14초 동안 숙제를 했습니다. 끝낸 시각을 구하세요.",
        expression="answer_text=4 시 55 분 47 초",
        topic="measurement",
        rule_id="grade3_length_time_round3_homework_end_time",
    ),
    8: ElementaryVisualTemplate(
        problem_text="시계가 17:08:25를 나타내고, 1시간 10분 동안 피아노를 쳤다면 시작한 시각을 구하세요.",
        expression="answer_text=오후 3 시 58 분 25 초",
        topic="measurement",
        rule_id="grade3_length_time_round3_piano_start_time",
    ),
    9: ElementaryVisualTemplate(
        problem_text="마라톤 42 km 195 m 중 40 km 지점을 통과했을 때 남은 거리를 m로 구하세요.",
        expression="answer_text=2195 m",
        topic="measurement",
        rule_id="grade3_length_time_round3_marathon_remaining_distance",
    ),
    10: ElementaryVisualTemplate(
        problem_text="첫 번째 수업이 오후 7시 20분에 시작하고 35분 수업, 15분 휴식일 때 세 번째 수업 시작 시각을 구하세요.",
        expression="answer_text=오후 9 시",
        topic="measurement",
        rule_id="grade3_length_time_round3_third_class_start",
    ),
    11: ElementaryVisualTemplate(
        problem_text="36 cm짜리 철사로 같은 크기의 정삼각형 2개를 만들 때 한 변의 길이를 mm로 구하세요.",
        expression="answer_text=60 mm",
        topic="measurement",
        rule_id="grade3_length_time_round3_triangle_side_from_wire",
    ),
}


_GRADE3_FRACTION_DECIMAL_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="도형을 똑같이 몇으로 나눈 것인지 쓰세요.",
        expression="answer_text=⑴ 3 ⑵ 8",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round1_equal_parts_count",
    ),
    2: ElementaryVisualTemplate(
        problem_text="분수를 소수로 나타내고 소수를 읽어 보세요.",
        expression="answer_text=⑴ 0.2, 영점 이 ⑵ 0.7, 영점 칠 ⑶ 0.3, 영점 삼",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round1_tenths_to_decimals",
    ),
    3: ElementaryVisualTemplate(
        problem_text="분수가 단위분수 몇 개인지 □ 안에 알맞은 수를 쓰세요.",
        expression="answer_text=⑴ 2 ⑵ 4 ⑶ 5",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round1_unit_fraction_count",
    ),
    4: ElementaryVisualTemplate(
        problem_text="0.1이 몇 개인지 비교하여 2.8과 2.5 중 더 큰 소수를 쓰세요.",
        expression="answer_text=28, 25, 2.8",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round1_decimal_tenths_compare",
    ),
    5: ElementaryVisualTemplate(
        problem_text="케이크의 1/5을 먹었을 때 남은 케이크는 먹은 케이크의 몇 배인지 구하세요.",
        expression="answer_text=4 배",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round1_remaining_cake_multiple",
    ),
    6: ElementaryVisualTemplate(
        problem_text="전체를 똑같이 3으로 나눈 것 중 2를 색칠한 것을 찾아 기호를 쓰세요.",
        expression="answer_text=다",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round1_two_thirds_shape",
    ),
}


_GRADE3_FRACTION_DECIMAL_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림을 보고 색칠한 부분을 분수와 소수로 나타내세요.",
        expression="answer_text=분수: 4/10, 소수: 0.4",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round1_shaded_circle_fraction_decimal",
    ),
    2: ElementaryVisualTemplate(
        problem_text="전체에 대하여 색칠한 부분의 크기를 분수로 나타내고 읽어 보세요.",
        expression="answer_text=3/4, 사분의 삼",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round1_shaded_triangle_fraction",
    ),
    3: ElementaryVisualTemplate(
        problem_text="색칠하지 않은 부분이 전체의 5/9가 되도록 더 색칠해야 하는 칸 수를 구하세요.",
        expression="answer=2",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round1_make_unshaded_five_ninths",
    ),
    4: ElementaryVisualTemplate(
        problem_text="사탕 10개 중 4개와 2개를 주었을 때 남은 사탕을 분수와 소수로 나타내세요.",
        expression="answer_text=⑴ 4/10 ⑵ 0.4",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round1_remaining_candy_fraction_decimal",
    ),
    5: ElementaryVisualTemplate(
        problem_text="단위분수를 모두 찾아 쓰세요.",
        expression="answer_text=1/6, 1/2, 1/4",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round1_find_unit_fractions",
    ),
    6: ElementaryVisualTemplate(
        problem_text="다음 중 가장 작은 분수를 쓰세요.",
        expression="answer_text=1/9",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round1_smallest_unit_fraction",
    ),
    7: ElementaryVisualTemplate(
        problem_text="2/10와 0.8 사이에 있는 수를 모두 찾으세요.",
        expression="answer_text=7/10, 0.5",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round1_numbers_between_two_tenths_and_point8",
    ),
    8: ElementaryVisualTemplate(
        problem_text="분수의 크기를 비교하여 큰 수부터 차례로 쓰세요.",
        expression="answer_text=4/5, 4/7, 4/9",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round1_order_same_numerator",
    ),
    9: ElementaryVisualTemplate(
        problem_text="8 mm를 cm로, 0.7 cm를 mm로 나타내세요.",
        expression="answer_text=⑴ 0.8 ⑵ 7",
        topic="measurement",
        rule_id="grade3_fraction_decimal_round1_mm_cm_decimal_conversion",
    ),
}


_GRADE3_FRACTION_DECIMAL_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="주스가 몇 컵인지 소수로 나타내세요.",
        expression="answer_text=2.7 컵",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round1_juice_cups_decimal",
    ),
    2: ElementaryVisualTemplate(
        problem_text="분자 1이고 1/5보다 작고 1/7보다 큰 분수를 구하세요.",
        expression="answer_text=1/6",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round1_unit_fraction_between",
    ),
    3: ElementaryVisualTemplate(
        problem_text="20 cm 연필을 매일 4 mm씩 3일 동안 썼을 때 남은 길이를 cm 소수로 나타내세요.",
        expression="answer_text=18.8 cm",
        topic="measurement",
        rule_id="grade3_fraction_decimal_round1_pencil_remaining_decimal_cm",
    ),
    4: ElementaryVisualTemplate(
        problem_text="0.1 cm씩 자른 테이프의 개수를 비교하여 가장 많이 사용한 사람과 길이를 구하세요.",
        expression="answer_text=희수, 2.8 cm",
        topic="measurement",
        rule_id="grade3_fraction_decimal_round1_most_used_tape",
    ),
    5: ElementaryVisualTemplate(
        problem_text="조건에 맞는 소수를 ■, ▲와 같은 형태로 구하세요.",
        expression="answer_text=0.7",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round1_decimal_condition",
    ),
}


_GRADE3_FRACTION_DECIMAL_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="전체를 똑같이 넷으로 나눈 것에 ○표 하세요.",
        expression="answer_text=②, ⑤",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round2_equal_fourths_shapes",
    ),
    2: ElementaryVisualTemplate(
        problem_text="색칠한 부분은 전체를 똑같이 12로 나눈 것 중 몇인지 구하세요.",
        expression="answer=4",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round2_shaded_twelfths_count",
    ),
    3: ElementaryVisualTemplate(
        problem_text="색칠한 부분을 분수로 나타내세요.",
        expression="answer_text=4/6",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round2_shaded_hexagon_fraction",
    ),
    4: ElementaryVisualTemplate(
        problem_text="그림을 보고 소수로 나타내세요.",
        expression="answer_text=3.4",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round2_decimal_blocks",
    ),
    5: ElementaryVisualTemplate(
        problem_text="초콜릿의 2/10을 먹었을 때 남은 양은 먹은 양의 몇 배인지 구하세요.",
        expression="answer_text=4 배",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round2_chocolate_remaining_multiple",
    ),
    6: ElementaryVisualTemplate(
        problem_text="다음 설명이 잘못된 것을 고르세요.",
        expression="answer_text=③",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round2_wrong_decimal_explanation",
    ),
    7: ElementaryVisualTemplate(
        problem_text="단위분수이고 분자와 분모의 합이 15인 분수를 쓰세요.",
        expression="answer_text=1/14",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round2_unit_fraction_sum_15",
    ),
    8: ElementaryVisualTemplate(
        problem_text="색 테이프 전체 길이의 1/3만큼이 6 cm일 때 전체 길이를 구하세요.",
        expression="answer_text=18 cm",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round2_tape_whole_from_third",
    ),
    9: ElementaryVisualTemplate(
        problem_text="1/6 m의 3배를 m로 나타내세요.",
        expression="answer_text=3/6 m",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round2_three_times_one_sixth_meter",
    ),
}


_GRADE3_FRACTION_DECIMAL_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="분수가 단위분수 몇 개인지 □ 안에 알맞은 수를 쓰세요.",
        expression="answer_text=3, 5, 4",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round2_unit_fraction_counts",
    ),
    2: ElementaryVisualTemplate(
        problem_text="가장 작은 분수에 ○표 하세요.",
        expression="answer_text=1/11",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round2_smallest_same_denominator",
    ),
    3: ElementaryVisualTemplate(
        problem_text="다음 중 단위분수가 아닌 것에 ○표 하세요.",
        expression="answer_text=2/10",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round2_not_unit_fraction",
    ),
    4: ElementaryVisualTemplate(
        problem_text="1/5와 1/7 사이에 알맞은 비교 기호를 쓰세요.",
        expression="answer_text=>",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round2_compare_unit_fractions",
    ),
    5: ElementaryVisualTemplate(
        problem_text="카드 8, 3, 5, 1 중 2장을 골라 만들 수 있는 가장 작은 단위분수를 구하세요.",
        expression="answer_text=1/8",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round2_smallest_unit_fraction_from_cards",
    ),
    6: ElementaryVisualTemplate(
        problem_text="수들을 수직선 위에 나타낼 때 가장 오른쪽에 있는 수에 ○표 하세요.",
        expression="answer_text=1",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round2_rightmost_number_line_value",
    ),
    7: ElementaryVisualTemplate(
        problem_text="8 cm 4 mm를 cm 소수로 나타내세요.",
        expression="answer_text=8.4 cm",
        topic="measurement",
        rule_id="grade3_fraction_decimal_round2_8cm4mm_decimal_cm",
    ),
    8: ElementaryVisualTemplate(
        problem_text="132 cm보다 8 mm 더 큰 키를 cm 소수로 나타내세요.",
        expression="answer_text=132.8 cm",
        topic="measurement",
        rule_id="grade3_fraction_decimal_round2_height_plus_8mm_decimal_cm",
    ),
    9: ElementaryVisualTemplate(
        problem_text="수 카드 8, 1, 2, 7 중 2장으로 소수 한 자리수를 만들 때 7보다 큰 수의 개수를 구하세요.",
        expression="answer_text=6 개",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round2_decimal_numbers_greater_than_7",
    ),
    10: ElementaryVisualTemplate(
        problem_text="피자 9조각 중 4조각을 먹었을 때 남은 피자는 전체의 몇 분의 몇인지 구하세요.",
        expression="answer_text=5/9",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round2_remaining_pizza_fraction",
    ),
    11: ElementaryVisualTemplate(
        problem_text="둘레가 0.1 km인 산책길을 3 km 걸으려면 몇 바퀴 돌아야 하는지 구하세요.",
        expression="answer_text=30 바퀴",
        topic="measurement",
        rule_id="grade3_fraction_decimal_round2_walk_laps",
    ),
}


_GRADE3_FRACTION_DECIMAL_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="전체를 똑같이 둘로 나눈 것에 ○표 하세요.",
        expression="answer_text=③, ④",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round3_equal_halves_shapes",
    ),
    2: ElementaryVisualTemplate(
        problem_text="색칠한 부분은 전체를 똑같이 10으로 나눈 것 중 몇인지 구하세요.",
        expression="answer=5",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round3_shaded_tenths_count",
    ),
    3: ElementaryVisualTemplate(
        problem_text="색칠한 부분을 분수로 나타내세요.",
        expression="answer_text=2/5",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round3_shaded_pentagon_fraction",
    ),
    4: ElementaryVisualTemplate(
        problem_text="그림을 보고 소수로 나타내세요.",
        expression="answer_text=2.5",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round3_decimal_blocks",
    ),
    5: ElementaryVisualTemplate(
        problem_text="초콜릿의 3/12을 먹었을 때 남은 양은 먹은 양의 몇 배인지 구하세요.",
        expression="answer_text=3 배",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round3_chocolate_remaining_multiple",
    ),
    6: ElementaryVisualTemplate(
        problem_text="0.1이 20개인 수와 같지 않은 것을 고르세요.",
        expression="answer_text=②",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round3_not_equal_twenty_tenths",
    ),
    7: ElementaryVisualTemplate(
        problem_text="단위분수이고 분자와 분모의 합이 8인 분수를 쓰세요.",
        expression="answer_text=1/7",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round3_unit_fraction_sum_8",
    ),
    8: ElementaryVisualTemplate(
        problem_text="색 테이프 전체 길이의 1/7만큼이 2 cm일 때 전체 길이를 구하세요.",
        expression="answer_text=14 cm",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round3_tape_whole_from_seventh",
    ),
}


_GRADE3_FRACTION_DECIMAL_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="피자의 1/6과 5/6을 비교하여 몇 배인지 구하세요.",
        expression="answer_text=5 배",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round3_pizza_fraction_multiple",
    ),
    2: ElementaryVisualTemplate(
        problem_text="□ 안에 알맞은 수들의 합을 구하세요.",
        expression="answer=10",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round3_fraction_count_blanks_sum",
    ),
    3: ElementaryVisualTemplate(
        problem_text="7/10보다 큰 분수에 ○표 하세요.",
        expression="answer_text=8/10",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round3_greater_than_seven_tenths",
    ),
    4: ElementaryVisualTemplate(
        problem_text="분모가 5인 단위분수를 쓰세요.",
        expression="answer_text=1/5",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round3_unit_fraction_denominator_5",
    ),
    5: ElementaryVisualTemplate(
        problem_text="1/3과 1/6 사이에 알맞은 비교 기호를 쓰세요.",
        expression="answer_text=>",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round3_compare_one_third_one_sixth",
    ),
    6: ElementaryVisualTemplate(
        problem_text="수 카드 9, 7, 2 중 2장을 사용하여 분모가 9인 가장 큰 분수를 구하세요.",
        expression="answer_text=7/9",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round3_largest_fraction_denominator_9",
    ),
    7: ElementaryVisualTemplate(
        problem_text="가장 큰 수를 골라 ○표 하세요.",
        expression="answer_text=9/10",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round3_largest_tenths_value",
    ),
    8: ElementaryVisualTemplate(
        problem_text="14 mm를 cm로 나타내세요.",
        expression="answer_text=1.4 cm",
        topic="measurement",
        rule_id="grade3_fraction_decimal_round3_14mm_to_decimal_cm",
    ),
    9: ElementaryVisualTemplate(
        problem_text="6 cm와 5 mm를 모두 cm로 나타내세요.",
        expression="answer_text=6.5 cm",
        topic="measurement",
        rule_id="grade3_fraction_decimal_round3_6cm5mm_to_decimal_cm",
    ),
    10: ElementaryVisualTemplate(
        problem_text="수 카드 7, 3, 5, 9 중 2장으로 소수 한 자리수를 만들 때 8보다 큰 수의 개수를 구하세요.",
        expression="answer_text=3 개",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round3_decimal_numbers_greater_than_8",
    ),
    11: ElementaryVisualTemplate(
        problem_text="전체의 6/11을 걸어서 가고 나머지를 뛰어서 갔을 때 뛰어서 간 거리를 분수로 구하세요.",
        expression="answer_text=5/11",
        topic="fraction_ratio",
        rule_id="grade3_fraction_decimal_round3_remaining_distance_fraction",
    ),
    12: ElementaryVisualTemplate(
        problem_text="철사 1 m를 10도막으로 나누어 4도막을 주었을 때 남은 철사를 m 소수로 나타내세요.",
        expression="answer_text=0.6 m",
        topic="measurement",
        rule_id="grade3_fraction_decimal_round3_remaining_wire_decimal_m",
    ),
}


_GRADE3_ADD_SUB_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수 모형을 보고 413+210의 값을 구하세요.",
        expression="answer=623",
        rule_id="grade3_add_sub_round1_base_ten_addition",
    ),
    2: ElementaryVisualTemplate(
        problem_text="461과 278의 차를 구하세요.",
        expression="answer=183",
        rule_id="grade3_add_sub_round1_difference_461_278",
    ),
    3: ElementaryVisualTemplate(
        problem_text="357+896을 계산하세요.",
        expression="answer=1253",
        rule_id="grade3_add_sub_round1_357_plus_896",
    ),
    4: ElementaryVisualTemplate(
        problem_text="□+287=665에서 □ 안에 알맞은 수를 구하세요.",
        expression="answer=378",
        rule_id="grade3_add_sub_round1_missing_addend",
    ),
    5: ElementaryVisualTemplate(
        problem_text="745, 675, 656 중 가장 큰 수와 가장 작은 수의 합을 구하세요.",
        expression="answer=1401",
        rule_id="grade3_add_sub_round1_largest_smallest_sum",
    ),
    6: ElementaryVisualTemplate(
        problem_text="세로셈의 빈칸 ㉠, ㉡에 알맞은 수를 쓰세요.",
        expression="answer_text=㉠ 7, ㉡ 9",
        rule_id="grade3_add_sub_round1_vertical_addition_blanks",
    ),
    7: ElementaryVisualTemplate(
        problem_text="596+878의 값을 구하세요.",
        expression="answer=1474",
        rule_id="grade3_add_sub_round1_596_plus_878",
    ),
    8: ElementaryVisualTemplate(
        problem_text="덧셈 표에서 빈칸 ㉠과 ㉡에 알맞은 수를 쓰세요.",
        expression="answer_text=㉠ 437, ㉡ 783",
        rule_id="grade3_add_sub_round1_addition_grid_small",
    ),
    9: ElementaryVisualTemplate(
        problem_text="덧셈 표에서 빈칸 ㉠, ㉡, ㉢, ㉣에 알맞은 수를 쓰세요.",
        expression="answer_text=㉠ 466, ㉡ 1115, ㉢ 910, ㉣ 671",
        rule_id="grade3_add_sub_round1_addition_grid_large",
    ),
}


_GRADE3_ADD_SUB_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="사각형 안에 있는 수의 합을 구하세요.",
        expression="answer=1421",
        rule_id="grade3_add_sub_round1_shape_sum_rectangles",
    ),
    2: ElementaryVisualTemplate(
        problem_text="314, 500, 326 중 가장 큰 수와 가장 작은 수의 차를 구하세요.",
        expression="answer=186",
        rule_id="grade3_add_sub_round1_largest_smallest_difference",
    ),
    3: ElementaryVisualTemplate(
        problem_text="359와 674의 합과 차를 각각 구하세요.",
        expression="answer_text=합: 1033, 차: 315",
        rule_id="grade3_add_sub_round1_sum_difference_359_674",
    ),
    4: ElementaryVisualTemplate(
        problem_text="802-348 계산에서 틀린 부분을 찾아 바르게 계산하세요.",
        expression="answer=454",
        rule_id="grade3_add_sub_round1_fix_subtraction",
    ),
    5: ElementaryVisualTemplate(
        problem_text="720-251과 936-439의 계산 결과를 비교하세요.",
        expression="answer_text=<",
        rule_id="grade3_add_sub_round1_compare_subtractions",
    ),
    6: ElementaryVisualTemplate(
        problem_text="수 카드 3, 1, 8로 만들 수 있는 가장 큰 세 자리 수와 374의 차를 구하세요.",
        expression="answer=457",
        rule_id="grade3_add_sub_round1_largest_card_number_minus_374",
    ),
    7: ElementaryVisualTemplate(
        problem_text="분식집에서 어제 327접시, 오늘 486접시 판 만두는 모두 몇 접시인지 구하세요.",
        expression="answer_text=813 접시",
        rule_id="grade3_add_sub_round1_dumpling_total",
    ),
    8: ElementaryVisualTemplate(
        problem_text="어떤 수에서 548을 뺐더니 674가 되었습니다. 어떤 수를 구하세요.",
        expression="answer=1222",
        rule_id="grade3_add_sub_round1_unknown_before_subtract",
    ),
    9: ElementaryVisualTemplate(
        problem_text="어제 812명, 오늘 536명이 놀이공원을 방문했습니다. 어제 방문한 사람은 오늘보다 몇 명 더 많습니까?",
        expression="answer_text=276 명",
        rule_id="grade3_add_sub_round1_park_visitors_difference",
    ),
    10: ElementaryVisualTemplate(
        problem_text="집에서 도서관까지의 거리는 도서관에서 공원까지의 거리보다 몇 m 더 멉니까?",
        expression="answer_text=267 m",
        topic="measurement",
        rule_id="grade3_add_sub_round1_distance_difference",
    ),
    11: ElementaryVisualTemplate(
        problem_text="강당 의자 983개 중 학생 627명과 203명이 앉았습니다. 빈 의자는 몇 개인지 구하세요.",
        expression="answer_text=153 개",
        rule_id="grade3_add_sub_round1_empty_chairs",
    ),
}


_GRADE3_ADD_SUB_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="두 색 테이프의 길이 515 cm와 372 cm의 합을 구하세요.",
        expression="answer_text=887 cm",
        topic="measurement",
        rule_id="grade3_add_sub_round2_tape_lengths_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="731에서 321을 뺀 값을 쓰세요.",
        expression="answer=410",
        rule_id="grade3_add_sub_round2_subtract_321",
    ),
    3: ElementaryVisualTemplate(
        problem_text="446+361을 계산하세요.",
        expression="answer=807",
        rule_id="grade3_add_sub_round2_446_plus_361",
    ),
    4: ElementaryVisualTemplate(
        problem_text="436-183을 계산하세요.",
        expression="answer=253",
        rule_id="grade3_add_sub_round2_436_minus_183",
    ),
    5: ElementaryVisualTemplate(
        problem_text="349+433 계산에서 잘못된 부분을 찾아 바르게 계산하세요.",
        expression="answer=782",
        rule_id="grade3_add_sub_round2_fix_349_plus_433",
    ),
    6: ElementaryVisualTemplate(
        problem_text="639+137과 276+455의 계산 결과를 비교하세요.",
        expression="answer_text=>",
        rule_id="grade3_add_sub_round2_compare_additions",
    ),
    7: ElementaryVisualTemplate(
        problem_text="216에 357을 더하고 439를 더한 값을 구하세요.",
        expression="answer=1012",
        rule_id="grade3_add_sub_round2_chain_addition",
    ),
    8: ElementaryVisualTemplate(
        problem_text="357, 168, 372, 299 중 두 수의 합이 가장 크게 되는 두 수의 합을 구하세요.",
        expression="answer=729",
        rule_id="grade3_add_sub_round2_largest_pair_sum",
    ),
    9: ElementaryVisualTemplate(
        problem_text="823, 772, 509, 465 중 가장 큰 수와 가장 작은 수의 차를 구하세요.",
        expression="answer=358",
        rule_id="grade3_add_sub_round2_largest_smallest_difference",
    ),
    10: ElementaryVisualTemplate(
        problem_text="삼각형에 있는 수의 차를 구하세요.",
        expression="answer=655",
        topic="geometry",
        rule_id="grade3_add_sub_round2_triangle_numbers_difference",
    ),
}


_GRADE3_ADD_SUB_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림을 보고 빈칸에 알맞은 수를 쓰세요.",
        expression="answer=544",
        rule_id="grade3_add_sub_round2_bar_model_missing",
    ),
    2: ElementaryVisualTemplate(
        problem_text="536-□=258에서 □ 안에 알맞은 수를 구하세요.",
        expression="answer=278",
        rule_id="grade3_add_sub_round2_missing_subtrahend",
    ),
    3: ElementaryVisualTemplate(
        problem_text="세로셈의 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=5, 8",
        rule_id="grade3_add_sub_round2_vertical_addition_blanks",
    ),
    4: ElementaryVisualTemplate(
        problem_text="수직선을 보고 가에서 라까지의 길이를 구하세요.",
        expression="answer=745",
        topic="measurement",
        rule_id="grade3_add_sub_round2_number_line_length",
    ),
    5: ElementaryVisualTemplate(
        problem_text="계산 결과가 큰 것부터 차례대로 기호를 쓰세요.",
        expression="answer_text=㉠, ㉢, ㉡",
        rule_id="grade3_add_sub_round2_order_results_desc",
    ),
    6: ElementaryVisualTemplate(
        problem_text="양계장에서 어제 523개, 오늘 397개 낳은 달걀은 모두 몇 개인지 구하세요.",
        expression="answer_text=920 개",
        rule_id="grade3_add_sub_round2_eggs_total",
    ),
    7: ElementaryVisualTemplate(
        problem_text="영수는 284장, 철희는 347장 모았습니다. 누가 몇 장 더 많이 모았는지 쓰세요.",
        expression="answer_text=철희, 63 장",
        rule_id="grade3_add_sub_round2_stickers_more",
    ),
    8: ElementaryVisualTemplate(
        problem_text="어떤 수에서 178을 뺐더니 276이 되었습니다. 어떤 수를 구하세요.",
        expression="answer=454",
        rule_id="grade3_add_sub_round2_unknown_before_subtract",
    ),
    9: ElementaryVisualTemplate(
        problem_text="도서관에서 찬우네 집까지 786 m, 연희네 집까지 912 m입니다. 누구네 집이 몇 m 더 먼지 구하세요.",
        expression="answer_text=연희, 126 m",
        topic="measurement",
        rule_id="grade3_add_sub_round2_library_distance_difference",
    ),
    10: ElementaryVisualTemplate(
        problem_text="수 카드 1, 7, 8로 만들 수 있는 가장 큰 수와 가장 작은 수의 차를 구하세요.",
        expression="answer=693",
        rule_id="grade3_add_sub_round2_digit_cards_difference",
    ),
}


_GRADE3_ADD_SUB_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="563+214를 계산하세요.",
        expression="answer=777",
        rule_id="grade3_add_sub_round3_563_plus_214",
    ),
    2: ElementaryVisualTemplate(
        problem_text="456-134를 계산하세요.",
        expression="answer=322",
        rule_id="grade3_add_sub_round3_456_minus_134",
    ),
    3: ElementaryVisualTemplate(
        problem_text="382에 594를 더한 값을 구하세요.",
        expression="answer=976",
        rule_id="grade3_add_sub_round3_chain_addition",
    ),
    4: ElementaryVisualTemplate(
        problem_text="817-453을 계산하세요.",
        expression="answer=364",
        rule_id="grade3_add_sub_round3_817_minus_453",
    ),
    5: ElementaryVisualTemplate(
        problem_text="528+264 계산에서 잘못된 부분을 찾아 바르게 계산하세요.",
        expression="answer=792",
        rule_id="grade3_add_sub_round3_fix_528_plus_264",
    ),
    6: ElementaryVisualTemplate(
        problem_text="384+395와 537+228의 계산 결과를 비교하세요.",
        expression="answer_text=>",
        rule_id="grade3_add_sub_round3_compare_additions",
    ),
    7: ElementaryVisualTemplate(
        problem_text="487에 285를 더하고 379를 더한 값을 구하세요.",
        expression="answer=1151",
        rule_id="grade3_add_sub_round3_chain_addition_487",
    ),
    8: ElementaryVisualTemplate(
        problem_text="169, 218, 401, 521 중 두 수의 합이 가장 작게 되는 두 수의 합을 구하세요.",
        expression="answer=387",
        rule_id="grade3_add_sub_round3_smallest_pair_sum",
    ),
    9: ElementaryVisualTemplate(
        problem_text="669, 703, 598, 524 중 가장 큰 수와 가장 작은 수의 차를 구하세요.",
        expression="answer=179",
        rule_id="grade3_add_sub_round3_largest_smallest_difference",
    ),
    10: ElementaryVisualTemplate(
        problem_text="사각형에 있는 수의 차를 구하세요.",
        expression="answer=624",
        topic="geometry",
        rule_id="grade3_add_sub_round3_quadrilateral_numbers_difference",
    ),
}


_GRADE3_ADD_SUB_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림을 보고 빈칸에 알맞은 수를 쓰세요.",
        expression="answer=457",
        rule_id="grade3_add_sub_round3_bar_model_missing",
    ),
    2: ElementaryVisualTemplate(
        problem_text="□+376=634에서 □ 안에 알맞은 수를 구하세요.",
        expression="answer=258",
        rule_id="grade3_add_sub_round3_missing_addend",
    ),
    3: ElementaryVisualTemplate(
        problem_text="세로셈의 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=2, 7",
        rule_id="grade3_add_sub_round3_vertical_addition_blanks",
    ),
    4: ElementaryVisualTemplate(
        problem_text="수직선을 보고 가에서 라까지의 길이를 구하세요.",
        expression="answer=632",
        topic="measurement",
        rule_id="grade3_add_sub_round3_number_line_length",
    ),
    5: ElementaryVisualTemplate(
        problem_text="계산 결과가 큰 것부터 차례대로 기호를 쓰세요.",
        expression="answer_text=㉡, ㉢, ㉠",
        rule_id="grade3_add_sub_round3_order_results_desc",
    ),
    6: ElementaryVisualTemplate(
        problem_text="지난주 287쪽, 이번 주 347쪽 읽은 책은 모두 몇 쪽인지 구하세요.",
        expression="answer_text=634 쪽",
        rule_id="grade3_add_sub_round3_book_pages_total",
    ),
    7: ElementaryVisualTemplate(
        problem_text="어제 762명, 오늘 614명이 놀이공원을 방문했습니다. 어제 방문한 사람은 오늘보다 몇 명 더 많습니까?",
        expression="answer_text=148 명",
        rule_id="grade3_add_sub_round3_visitors_difference",
    ),
    8: ElementaryVisualTemplate(
        problem_text="어떤 수에서 329를 뺐더니 714가 되었습니다. 어떤 수를 구하세요.",
        expression="answer=1043",
        rule_id="grade3_add_sub_round3_unknown_before_subtract",
    ),
    9: ElementaryVisualTemplate(
        problem_text="위인전과 과학책의 권수 차이를 비교하여 어느 책이 몇 권 더 많은지 구하세요.",
        expression="answer_text=위인전, 134 권",
        rule_id="grade3_add_sub_round3_book_count_difference",
    ),
    10: ElementaryVisualTemplate(
        problem_text="수 카드 2, 7, 9로 만들 수 있는 가장 큰 수와 가장 작은 수의 차를 구하세요.",
        expression="answer=495",
        rule_id="grade3_add_sub_round3_digit_cards_difference",
    ),
}


_GRADE3_PLANE_SHAPES_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림에서 반직선과 직선 수의 차는 몇 개인지 구하세요.",
        expression="answer_text=2 개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_line_ray_difference",
    ),
    2: ElementaryVisualTemplate(
        problem_text="네 점을 이용하여 그을 수 있는 직선은 모두 몇 개인지 구하세요.",
        expression="answer_text=6 개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_lines_from_four_points",
    ),
    3: ElementaryVisualTemplate(
        problem_text="그림에서 찾을 수 있는 직선은 모두 몇 개인지 구하세요.",
        expression="answer_text=6 개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_line_count",
    ),
    4: ElementaryVisualTemplate(
        problem_text="□ 안에 알맞은 말을 써 넣으세요.",
        expression="answer_text=㉠ 변, ㉡ 꼭짓점, ㉢ 변",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_edge_vertex_blanks",
    ),
    5: ElementaryVisualTemplate(
        problem_text="다음 설명이 옳으면 ○, 틀리면 ×라고 쓰세요.",
        expression="answer_text=⑴ ○ ⑵ × ⑶ × ⑷ ○",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_true_false_shapes_a",
    ),
    6: ElementaryVisualTemplate(
        problem_text="다음 설명이 옳으면 ○, 틀리면 ×라고 쓰세요.",
        expression="answer_text=⑴ ○ ⑵ × ⑶ × ⑷ ○",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_true_false_shapes_b",
    ),
}


_GRADE3_PLANE_SHAPES_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="직각의 수가 가장 많은 도형과 가장 적은 도형을 각각 고르세요.",
        expression="answer_text=10 개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_right_angle_extremes",
    ),
    2: ElementaryVisualTemplate(
        problem_text="다음 도형에서 직각은 모두 몇 개입니까?",
        expression="answer_text=다",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_right_angle_count_choice",
    ),
    3: ElementaryVisualTemplate(
        problem_text="오후 6시에서 11시 사이 중 시계의 긴바늘과 짧은바늘이 직각인 시각을 구하세요.",
        expression="answer_text=9 시",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_clock_right_angle_time_a",
    ),
    4: ElementaryVisualTemplate(
        problem_text="오후 6시에서 11시 사이 중 시계의 긴바늘과 짧은바늘이 직각인 시각을 구하세요.",
        expression="answer_text=9 시",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_clock_right_angle_time_b",
    ),
    5: ElementaryVisualTemplate(
        problem_text="삼각형의 꼭짓점을 옮겨 직각삼각형을 만들 때 알맞은 것을 고르세요.",
        expression="answer_text=②",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_make_right_triangle",
    ),
    6: ElementaryVisualTemplate(
        problem_text="도형의 이름을 쓰세요.",
        expression="answer_text=직각삼각형",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_name_right_triangle",
    ),
    7: ElementaryVisualTemplate(
        problem_text="그림에서 찾을 수 있는 직각삼각형은 모두 몇 개인지 구하세요.",
        expression="answer_text=3 개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_right_triangle_count_a",
    ),
    8: ElementaryVisualTemplate(
        problem_text="그림에서 찾을 수 있는 직각삼각형은 모두 몇 개인지 구하세요.",
        expression="answer_text=3 개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_right_triangle_count_b",
    ),
}


_GRADE3_PLANE_SHAPES_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="도형이 직사각형이 아닌 까닭을 완성하세요.",
        expression="answer_text=직각",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_rectangle_reason",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그림에서 찾을 수 있는 크고 작은 직사각형은 모두 몇 개인지 구하세요.",
        expression="answer_text=10 개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_rectangle_count",
    ),
    3: ElementaryVisualTemplate(
        problem_text="정사각형에 대한 설명이 잘못된 것을 찾아 기호를 쓰세요.",
        expression="answer_text=다",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_square_wrong_explanation_a",
    ),
    4: ElementaryVisualTemplate(
        problem_text="정사각형에 대한 설명이 잘못된 것을 찾아 기호를 쓰세요.",
        expression="answer_text=다",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_square_wrong_explanation_b",
    ),
    5: ElementaryVisualTemplate(
        problem_text="도형의 둘레 또는 변의 길이를 구하세요.",
        expression="answer_text=15 cm",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_side_length_15cm",
    ),
    6: ElementaryVisualTemplate(
        problem_text="도형의 둘레 또는 변의 길이를 구하세요.",
        expression="answer_text=13 cm",
        topic="geometry",
        rule_id="grade3_plane_shapes_round1_side_length_13cm",
    ),
}


_GRADE3_PLANE_SHAPES_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="도형을 바르게 읽은 것에 ○표 하세요.",
        expression="answer_text=직선 ㄷㄹ",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_read_line",
    ),
    2: ElementaryVisualTemplate(
        problem_text="직선과 선분의 개수의 차는 몇 개인지 구하세요.",
        expression="answer_text=5개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_line_segment_difference",
    ),
    3: ElementaryVisualTemplate(
        problem_text="반직선 ㄱㄴ에 대한 설명으로 옳은 것의 기호를 쓰세요.",
        expression="answer_text=ㄴ",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_ray_description",
    ),
    4: ElementaryVisualTemplate(
        problem_text="직선을 찾아 이름을 바르게 쓰세요.",
        expression="answer_text=직선 ㄷㄹ",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_find_line_name",
    ),
    5: ElementaryVisualTemplate(
        problem_text="6개의 점을 이어 그릴 수 있는 선분은 모두 몇 개인지 구하세요.",
        expression="answer_text=15개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_segments_from_six_points",
    ),
    6: ElementaryVisualTemplate(
        problem_text="각이 없는 것에 ○표 하세요.",
        expression="answer_text=첫째, 셋째",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_no_angle_shapes",
    ),
    7: ElementaryVisualTemplate(
        problem_text="도형에서 각은 모두 몇 개인지 구하세요.",
        expression="answer_text=3개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_angle_count",
    ),
    8: ElementaryVisualTemplate(
        problem_text="다음 도형에서 □ 안에 알맞은 말을 쓰세요.",
        expression="answer_text=변, 꼭짓점",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_edge_vertex_labels",
    ),
}


_GRADE3_PLANE_SHAPES_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림에서 찾을 수 있는 크고 작은 각은 모두 몇 개인지 구하세요.",
        expression="answer_text=10개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_all_angles_count",
    ),
    2: ElementaryVisualTemplate(
        problem_text="다음 중 직각이 있는 도형은 몇 개인지 구하세요.",
        expression="answer_text=3개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_shapes_with_right_angle",
    ),
    3: ElementaryVisualTemplate(
        problem_text="직각을 그리기 위해서는 점 ㄱ과 어느 점을 이어야 하는지 구하세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_draw_right_angle_point",
    ),
    4: ElementaryVisualTemplate(
        problem_text="다음 도형에는 직각이 모두 몇 개 있는지 구하세요.",
        expression="answer_text=8개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_right_angles_in_rectangle",
    ),
    5: ElementaryVisualTemplate(
        problem_text="시계의 두 바늘이 직각을 이루는 시각을 고르세요.",
        expression="answer_text=④",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_clock_right_angle_choice",
    ),
    6: ElementaryVisualTemplate(
        problem_text="설명을 읽고 알맞은 도형의 이름을 쓰세요.",
        expression="answer_text=직각삼각형",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_shape_from_description",
    ),
    7: ElementaryVisualTemplate(
        problem_text="직각삼각형은 어느 것인지 고르세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_find_right_triangle",
    ),
    8: ElementaryVisualTemplate(
        problem_text="도형에서 크고 작은 직각삼각형은 모두 몇 개인지 구하세요.",
        expression="answer_text=4개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_right_triangle_total",
    ),
}


_GRADE3_PLANE_SHAPES_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="다음 중 직사각형을 모두 고르세요.",
        expression="answer_text=①, ④, ⑤",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_choose_rectangles",
    ),
    2: ElementaryVisualTemplate(
        problem_text="네 각이 모두 직각이고 두 변의 길이가 4 cm, 9 cm인 사각형의 네 변의 길이의 합을 구하세요.",
        expression="answer_text=26 cm",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_rectangle_perimeter",
    ),
    3: ElementaryVisualTemplate(
        problem_text="다음 중 옳은 것을 모두 고르세요.",
        expression="answer_text=④, ⑤",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_correct_statements",
    ),
    4: ElementaryVisualTemplate(
        problem_text="두 도형에 있는 직각의 수의 차는 몇 개인지 구하세요.",
        expression="answer_text=3개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round2_right_angle_difference",
    ),
}


_GRADE3_PLANE_SHAPES_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="도형을 바르게 읽은 것에 ○표 하세요.",
        expression="answer_text=선분 ㄷㄹ",
        topic="geometry",
        rule_id="grade3_plane_shapes_round3_read_segment",
    ),
    2: ElementaryVisualTemplate(
        problem_text="직선과 선분의 개수의 차는 몇 개인지 구하세요.",
        expression="answer_text=0개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round3_line_segment_difference",
    ),
    3: ElementaryVisualTemplate(
        problem_text="선분 ㄱㄴ에 대한 설명으로 잘못된 것의 기호를 쓰세요.",
        expression="answer_text=ㄴ",
        topic="geometry",
        rule_id="grade3_plane_shapes_round3_segment_wrong_description",
    ),
    4: ElementaryVisualTemplate(
        problem_text="반직선을 찾아 이름을 바르게 쓰세요.",
        expression="answer_text=반직선 ㄷㄹ",
        topic="geometry",
        rule_id="grade3_plane_shapes_round3_find_ray_name",
    ),
    5: ElementaryVisualTemplate(
        problem_text="6개의 점 중에서 2개의 점을 이어 그을 수 있는 직선 중 점 ㅁ을 지나는 직선은 모두 몇 개인지 구하세요.",
        expression="answer_text=5개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round3_lines_through_point",
    ),
    6: ElementaryVisualTemplate(
        problem_text="각을 찾아 ○표 하세요.",
        expression="answer_text=셋째",
        topic="geometry",
        rule_id="grade3_plane_shapes_round3_find_angle_shape",
    ),
    7: ElementaryVisualTemplate(
        problem_text="도형에서 각은 모두 몇 개인지 구하세요.",
        expression="answer_text=6개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round3_hexagon_angle_count",
    ),
    8: ElementaryVisualTemplate(
        problem_text="각을 바르게 읽어 보세요.",
        expression="answer_text=각 ㅁㅂㅅ",
        topic="geometry",
        rule_id="grade3_plane_shapes_round3_read_angle",
    ),
}


_GRADE3_PLANE_SHAPES_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="도형이 직사각형이 아닌 맞는 이유의 기호를 쓰세요.",
        expression="answer_text=ㄴ",
        topic="geometry",
        rule_id="grade3_plane_shapes_round3_not_rectangle_reason",
    ),
    2: ElementaryVisualTemplate(
        problem_text="네 변의 길이의 합이 50 cm인 직사각형의 가로가 13 cm일 때 세로의 길이를 구하세요.",
        expression="answer_text=12 cm",
        topic="geometry",
        rule_id="grade3_plane_shapes_round3_rectangle_missing_side",
    ),
    3: ElementaryVisualTemplate(
        problem_text="다음 중 옳은 것을 모두 고르세요.",
        expression="answer_text=②, ④",
        topic="geometry",
        rule_id="grade3_plane_shapes_round3_correct_statements",
    ),
    4: ElementaryVisualTemplate(
        problem_text="두 도형에 있는 직각의 수의 합은 몇 개인지 구하세요.",
        expression="answer_text=8개",
        topic="geometry",
        rule_id="grade3_plane_shapes_round3_right_angle_sum",
    ),
}


_GRADE4_SHAPE_MOVEMENT_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="도형을 밀었을 때 변하는 것은 무엇인지 고르세요.",
        expression="answer_text=③ 위치",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_translation_changes_position",
    ),
    2: ElementaryVisualTemplate(
        problem_text="무늬 만들기에 사용되지 않는 방법을 모두 고르세요.",
        expression="answer_text=④, ⑤",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_pattern_unused_methods",
    ),
    3: ElementaryVisualTemplate(
        problem_text="시계 방향으로 90°만큼 15번 돌렸을 때의 모양과 같은 모양이 되려면 적어도 몇 번 돌려야 하는지 구하세요.",
        expression="answer_text=3번",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_rotation_modulo",
    ),
    4: ElementaryVisualTemplate(
        problem_text="도형을 오른쪽으로 밀었을 때의 도형을 그리세요.",
        expression="answer_text=오른쪽으로 민 도형",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_translate_right",
    ),
    5: ElementaryVisualTemplate(
        problem_text="도형을 밀 때 옳은 설명의 기호를 쓰세요.",
        expression="answer_text=가",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_translation_statement",
    ),
    6: ElementaryVisualTemplate(
        problem_text="주어진 모양으로 밀기를 이용하여 규칙적인 무늬를 만드세요.",
        expression="answer_text=보기 모양을 오른쪽으로 이어 민 무늬",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_translation_pattern",
    ),
    7: ElementaryVisualTemplate(
        problem_text="도형을 왼쪽으로 3번 밀었을 때의 도형을 그리세요.",
        expression="answer_text=왼쪽으로 3칸 민 도형",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_translate_left_three",
    ),
    8: ElementaryVisualTemplate(
        problem_text="두 자리 수가 적힌 카드를 아래쪽으로 뒤집었을 때 만들어지는 수를 구하세요.",
        expression="answer_text=51",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_flip_number_card",
    ),
}


_GRADE4_SHAPE_MOVEMENT_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="규칙에 따라 모양을 늘어놓은 것입니다. 빈칸에 알맞은 모양을 그리세요.",
        expression="answer_text=아래쪽으로 뒤집은 65",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_pattern_blank_number_card",
    ),
    2: ElementaryVisualTemplate(
        problem_text="도장을 찍었을 때 주어진 모양이 나오도록 도장을 새기는 방법을 그리세요.",
        expression="answer_text=좌우로 뒤집어 새긴 파도",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_stamp_mirror",
    ),
    3: ElementaryVisualTemplate(
        problem_text="주어진 한글 자음 중 왼쪽으로 뒤집어도 처음 모양과 같은 것은 모두 몇 개인지 구하세요.",
        expression="answer_text=8개",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_symmetric_consonants",
    ),
    4: ElementaryVisualTemplate(
        problem_text="도형을 위쪽으로 4번 뒤집고 시계 방향으로 90°만큼 6번 돌린 도형을 그리세요.",
        expression="answer_text=시계 방향으로 180° 돌린 도형",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_flip_rotate_grid",
    ),
    5: ElementaryVisualTemplate(
        problem_text="도형을 시계 반대 방향으로 270°만큼 돌린 도형을 그리세요.",
        expression="answer_text=시계 방향으로 90° 돌린 도형",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_rotate_counterclockwise_270",
    ),
    6: ElementaryVisualTemplate(
        problem_text="모양 조각을 위쪽으로 뒤집고 시계 반대 방향으로 90°만큼 돌렸을 때의 모양을 고르세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_flip_rotate_choice",
    ),
    7: ElementaryVisualTemplate(
        problem_text="글자를 오른쪽으로 뒤집고 시계 방향으로 270°만큼 돌렸을 때 만들어지는 글자를 쓰세요.",
        expression="answer_text=오른쪽으로 뒤집은 뒤 시계 방향으로 270° 돌린 아",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_transform_letter",
    ),
}


_GRADE4_SHAPE_MOVEMENT_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="도형을 어느 방향으로 밀거나 뒤집거나 돌렸을 때 생기는 모양이 처음 모양과 항상 같은 것을 고르세요.",
        expression="answer_text=②",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_always_same_shape",
    ),
    2: ElementaryVisualTemplate(
        problem_text="다음 모양으로 돌리기 방법을 이용하여 무늬를 만들 때 나올 수 없는 모양을 고르세요.",
        expression="answer_text=⑤",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_rotation_impossible_pattern",
    ),
    3: ElementaryVisualTemplate(
        problem_text="다음 중 뒤집기를 이용하여 만들 수 없는 무늬를 고르세요.",
        expression="answer_text=나",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_flip_impossible_pattern",
    ),
    4: ElementaryVisualTemplate(
        problem_text="다음 모양을 뒤집기의 방법을 이용하여 무늬를 만들 때 나올 수 있는 모양을 모두 고르세요.",
        expression="answer_text=①, ②, ③, ④",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_flip_possible_shapes",
    ),
    5: ElementaryVisualTemplate(
        problem_text="두 자리 수가 적힌 카드를 아래쪽으로 뒤집었을 때 만들어지는 수와 처음 수의 차를 구하세요.",
        expression="answer_text=27",
        topic="geometry",
        rule_id="grade4_shape_movement_round1_flip_number_difference",
    ),
}


_GRADE4_SHAPE_MOVEMENT_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="뒤집었을 때 생기는 모양이 서로 같게 되는 방향끼리 짝지은 것을 고르세요.",
        expression="answer_text=②",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_same_flip_direction_pair",
    ),
    2: ElementaryVisualTemplate(
        problem_text="어떤 도형을 보기와 같이 몇 번 돌리면 처음 도형과 같은 모양이 되는지 고르세요.",
        expression="answer_text=②",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_rotation_same_shape_count",
    ),
    3: ElementaryVisualTemplate(
        problem_text="시계 반대 방향으로 180°만큼 11번 돌렸을 때의 모양과 같은 모양이 되려면 적어도 몇 번 돌려야 하는지 구하세요.",
        expression="answer_text=1번",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_rotation_180_modulo",
    ),
    4: ElementaryVisualTemplate(
        problem_text="도형을 왼쪽으로 뒤집었을 때의 도형을 그리세요.",
        expression="answer_text=왼쪽으로 뒤집은 도형",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_flip_left_grid",
    ),
    5: ElementaryVisualTemplate(
        problem_text="도형 뒤집기에 대한 설명으로 옳은 것을 모두 찾아 기호를 쓰세요.",
        expression="answer_text=ㄱ, ㄷ",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_flip_true_statements",
    ),
    6: ElementaryVisualTemplate(
        problem_text="오른쪽 모양으로 돌리기를 이용하여 규칙적인 무늬를 만드세요.",
        expression="answer_text=보기 모양을 돌려 이어 만든 무늬",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_rotation_pattern",
    ),
    7: ElementaryVisualTemplate(
        problem_text="도형을 오른쪽으로 2번 뒤집었을 때의 도형을 그리세요.",
        expression="answer_text=처음과 같은 도형",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_flip_right_twice",
    ),
}


_GRADE4_SHAPE_MOVEMENT_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="글자 공이 글자 운이 되도록 뒤집는 방법을 고르세요.",
        expression="answer_text=위쪽",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_letter_flip_method",
    ),
    2: ElementaryVisualTemplate(
        problem_text="규칙에 따라 모양을 늘어놓은 것입니다. 빈칸에 알맞은 모양을 그리세요.",
        expression="answer_text=3",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_number_pattern_blank",
    ),
    3: ElementaryVisualTemplate(
        problem_text="도장을 찍었을 때 주어진 모양이 나오도록 도장을 어떻게 새겨야 하는지 고르세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_stamp_choice",
    ),
    4: ElementaryVisualTemplate(
        problem_text="주어진 한글 모음 중 오른쪽으로 뒤집어도 처음 모양과 같은 것은 모두 몇 개인지 구하세요.",
        expression="answer_text=4개",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_symmetric_vowels",
    ),
    5: ElementaryVisualTemplate(
        problem_text="도형의 이동 방법을 설명하세요.",
        expression="answer_text=왼쪽으로 7 cm 밀었습니다",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_describe_translation",
    ),
    6: ElementaryVisualTemplate(
        problem_text="도형을 시계 방향으로 90°만큼 돌린 도형을 그리세요.",
        expression="answer_text=시계 방향으로 90° 돌린 도형",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_rotate_clockwise_90",
    ),
    7: ElementaryVisualTemplate(
        problem_text="모양 조각을 아래쪽으로 뒤집고 시계 방향으로 90°만큼 돌렸을 때의 모양을 고르세요.",
        expression="answer_text=②",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_flip_down_rotate_choice",
    ),
}


_GRADE4_SHAPE_MOVEMENT_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="도형을 위쪽으로 뒤집은 다음 시계 방향으로 90°만큼 돌렸을 때 생기는 도형을 그리세요.",
        expression="answer_text=위쪽으로 뒤집은 뒤 시계 방향으로 90° 돌린 도형",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_flip_up_rotate_90",
    ),
    2: ElementaryVisualTemplate(
        problem_text="화살표 종이를 왼쪽으로 민 다음 시계 반대 방향으로 90°만큼 11번 돌렸을 때 화살표가 가리키는 방향을 구하세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_arrow_after_rotation",
    ),
    3: ElementaryVisualTemplate(
        problem_text="다음 무늬는 어떤 모양을 뒤집기의 방법을 이용하여 만든 것인지 고르세요.",
        expression="answer_text=②",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_flip_pattern_base",
    ),
    4: ElementaryVisualTemplate(
        problem_text="다음 중 주어진 모양으로 돌리기만을 이용하여 만든 모양을 찾아 기호를 쓰세요.",
        expression="answer_text=나",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_rotation_only_pattern",
    ),
    5: ElementaryVisualTemplate(
        problem_text="다음 모양을 돌리기 방법을 이용하여 무늬를 만들 때 나올 수 없는 모양을 모두 고르세요.",
        expression="answer_text=②, ⑤",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_rotation_impossible_shapes",
    ),
    6: ElementaryVisualTemplate(
        problem_text="수 카드를 시계 반대 방향으로 180°만큼 돌렸을 때 만들어지는 수와 처음 수의 차를 구하세요.",
        expression="answer_text=99",
        topic="geometry",
        rule_id="grade4_shape_movement_round2_rotate_number_difference",
    ),
}


_GRADE4_SHAPE_MOVEMENT_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="위쪽으로 1번 뒤집은 모양은 아래쪽으로 몇 번 뒤집은 모양과 같은지 고르세요.",
        expression="answer_text=②",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_up_down_flip_equivalence",
    ),
    2: ElementaryVisualTemplate(
        problem_text="도형을 위쪽으로 밀었을 때와 같은 도형이 되도록 돌리는 방법을 고르세요.",
        expression="answer_text=④",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_translate_same_rotation",
    ),
    3: ElementaryVisualTemplate(
        problem_text="도형을 같은 방향으로 2번 뒤집었을 때의 도형은 시계 방향으로 몇 도만큼 돌렸을 때의 도형과 같은지 쓰세요.",
        expression="answer_text=360°",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_double_flip_degrees",
    ),
    4: ElementaryVisualTemplate(
        problem_text="도형을 오른쪽으로 7 cm 밀고 위쪽으로 1 cm 밀었을 때의 도형을 그리세요.",
        expression="answer_text=오른쪽으로 7 cm, 위쪽으로 1 cm 민 도형",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_translate_7cm_1cm",
    ),
    5: ElementaryVisualTemplate(
        problem_text="도형 돌리기에 대한 설명으로 옳지 않은 것을 모두 고르세요.",
        expression="answer_text=②, ⑤",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_rotation_wrong_statements",
    ),
    6: ElementaryVisualTemplate(
        problem_text="주어진 모양으로 돌리기를 이용하여 규칙적인 무늬를 만드세요.",
        expression="answer_text=보기 모양을 돌려 이어 만든 무늬",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_rotation_pattern",
    ),
    7: ElementaryVisualTemplate(
        problem_text="어떤 도형을 시계 방향으로 180°만큼 돌린 도형입니다. 처음 도형을 그리세요.",
        expression="answer_text=보기를 시계 방향으로 180° 돌린 처음 도형",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_find_original_after_180",
    ),
}


_GRADE4_SHAPE_MOVEMENT_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="도형을 시계 방향으로 180°만큼 돌린 도형이 처음 도형과 같은 것을 고르세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_word_rotate_same_a",
    ),
    2: ElementaryVisualTemplate(
        problem_text="도형을 시계 방향으로 180°만큼 돌린 도형이 처음 도형과 같은 것을 고르세요.",
        expression="answer_text=①",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_word_rotate_same_b",
    ),
    3: ElementaryVisualTemplate(
        problem_text="도형을 왼쪽으로 뒤집었을 때의 도형을 그리세요.",
        expression="answer_text=왼쪽으로 뒤집은 도형",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_flip_left_letter",
    ),
    4: ElementaryVisualTemplate(
        problem_text="주어진 알파벳 대문자 중 왼쪽으로 뒤집어도 처음 모양과 같은 것은 모두 몇 개인지 구하세요.",
        expression="answer_text=4개",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_symmetric_capitals",
    ),
    5: ElementaryVisualTemplate(
        problem_text="도형을 위쪽으로 4번 뒤집었을 때의 도형을 그리세요.",
        expression="answer_text=처음과 같은 도형",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_flip_up_four",
    ),
    6: ElementaryVisualTemplate(
        problem_text="시계 반대 방향으로 90°만큼 돌린 도형의 처음 도형을 찾아 기호를 쓰세요.",
        expression="answer_text=나",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_find_original_after_ccw90",
    ),
    7: ElementaryVisualTemplate(
        problem_text="모양 조각을 아래쪽으로 뒤집고 시계 반대 방향으로 180°만큼 돌렸을 때의 모양을 찾아 쓰세요.",
        expression="answer_text=가",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_flip_down_rotate_180_choice",
    ),
}


_GRADE4_SHAPE_MOVEMENT_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="알파벳 대문자를 시계 반대 방향으로 180°만큼 돌리고 오른쪽으로 뒤집었을 때 처음과 같은 알파벳을 모두 고르세요.",
        expression="answer_text=①, ②, ④, ⑥",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_letter_rotate_flip_same",
    ),
    2: ElementaryVisualTemplate(
        problem_text="보기와 같은 규칙으로 수 카드를 움직였을 때 빈 곳에 들어갈 모양을 그리세요.",
        expression="answer_text=84를 같은 규칙으로 움직인 모양",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_number_card_pattern",
    ),
    3: ElementaryVisualTemplate(
        problem_text="다음 중 돌리기만을 이용하여 만든 무늬가 아닌 것을 고르세요.",
        expression="answer_text=⑤",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_not_rotation_pattern",
    ),
    4: ElementaryVisualTemplate(
        problem_text="밀기 방법을 이용하여 만든 무늬가 아닌 것을 찾아 기호를 쓰세요.",
        expression="answer_text=ㄱ",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_not_translation_pattern",
    ),
    5: ElementaryVisualTemplate(
        problem_text="다음 무늬는 어떤 모양을 뒤집기의 방법을 이용하여 만든 것인지 고르세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_flip_pattern_base",
    ),
    6: ElementaryVisualTemplate(
        problem_text="수 카드를 위쪽으로 뒤집었을 때 만들어지는 수와 처음 수의 합을 구하세요.",
        expression="answer_text=776",
        topic="geometry",
        rule_id="grade4_shape_movement_round3_flip_number_sum",
    ),
}


_GRADE3_DIVISION_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="72÷9의 몫을 구하세요.",
        expression="answer=8",
        rule_id="grade3_division_round1_72_div_9_quotient",
    ),
    2: ElementaryVisualTemplate(
        problem_text="32-8-8-8-8=0을 나눗셈식으로 나타내세요.",
        expression="answer_text=32 ÷ 8 = 4",
        rule_id="grade3_division_round1_repeated_subtraction_to_division",
    ),
    3: ElementaryVisualTemplate(
        problem_text="사과 8개를 4곳에 똑같이 나누는 나눗셈식으로 나타내세요.",
        expression="answer_text=8 ÷ 4 = 2",
        rule_id="grade3_division_round1_8_apples_4_places",
    ),
    4: ElementaryVisualTemplate(
        problem_text="사과 6개를 2곳에 똑같이 나누는 나눗셈식으로 나타내세요.",
        expression="answer_text=6 ÷ 2 = 3",
        rule_id="grade3_division_round1_6_apples_2_places",
    ),
    5: ElementaryVisualTemplate(
        problem_text="사탕 12개를 3개씩 묶으면 4묶음입니다. 나눗셈식으로 나타내세요.",
        expression="answer_text=12 ÷ 3 = 4",
        rule_id="grade3_division_round1_12_candies_groups_of_3",
    ),
    6: ElementaryVisualTemplate(
        problem_text="18÷3=6을 뺄셈식으로 바르게 나타낸 것의 기호를 쓰세요.",
        expression="answer_text=가",
        rule_id="grade3_division_round1_18_div_3_repeated_subtraction_choice",
    ),
    7: ElementaryVisualTemplate(
        problem_text="36÷9=4를 설명한 것 중 옳지 않은 것을 찾아 기호를 쓰세요.",
        expression="answer_text=다",
        rule_id="grade3_division_round1_36_div_9_wrong_explanation",
    ),
}


_GRADE3_DIVISION_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="대화를 읽고 두 사람 중 가진 스티커의 수가 더 많은 사람의 이름을 쓰세요.",
        expression="answer_text=준수",
        rule_id="grade3_division_round1_more_stickers",
    ),
    2: ElementaryVisualTemplate(
        problem_text="6×7=42를 2개의 나눗셈식으로 바꾸어 보세요.",
        expression="answer_text=빈칸: 6, 7, 42, 7, 6",
        rule_id="grade3_division_round1_multiplication_to_two_divisions",
    ),
    3: ElementaryVisualTemplate(
        problem_text="4×5=20으로 만들 수 있는 나눗셈식을 모두 고르세요.",
        expression="answer_text=②, ④",
        rule_id="grade3_division_round1_pick_division_facts",
    ),
    4: ElementaryVisualTemplate(
        problem_text="□ 안에 알맞은 수를 순서대로 쓰세요. 5×□=25, 7×□=56, □×9=45",
        expression="answer_text=5, 8, 5",
        rule_id="grade3_division_round1_missing_multiplication_factors",
    ),
    5: ElementaryVisualTemplate(
        problem_text="24÷6=□의 몫을 구할 때 필요한 곱셈식을 찾으세요.",
        expression="answer_text=다",
        rule_id="grade3_division_round1_24_div_6_needed_multiplication",
    ),
    6: ElementaryVisualTemplate(
        problem_text="나눗셈 표의 빈 곳 ㉠, ㉡에 알맞은 수를 쓰세요.",
        expression="answer_text=㉠ 3, ㉡ 4",
        rule_id="grade3_division_round1_division_table_blanks",
    ),
    7: ElementaryVisualTemplate(
        problem_text="딸기 49개를 7상자에 똑같이 나누어 담았습니다. 상자 한 개에 담은 딸기는 몇 개입니까?",
        expression="answer_text=7 개",
        rule_id="grade3_division_round1_49_strawberries_7_boxes",
    ),
    8: ElementaryVisualTemplate(
        problem_text="꽃 16송이를 2명에게 똑같이 나누어 주면 한 명에게 몇 송이씩 줄 수 있습니까?",
        expression="answer_text=8 송이",
        rule_id="grade3_division_round1_16_flowers_2_people",
    ),
}


_GRADE3_DIVISION_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="계산 흐름도에서 빈 곳 ㉠, ㉡에 알맞은 수를 쓰세요.",
        expression="answer_text=㉠ 9, ㉡ 6",
        rule_id="grade3_division_round1_flowchart_blanks",
    ),
    2: ElementaryVisualTemplate(
        problem_text="32에 어떤 수를 더해야 할 것을 잘못하여 어떤 수로 나누었더니 8이 되었습니다. 바르게 계산하면 얼마입니까?",
        expression="answer=36",
        rule_id="grade3_division_round1_wrong_operation_correct_result",
    ),
    3: ElementaryVisualTemplate(
        problem_text="24÷3=56÷□에서 □ 안에 알맞은 수를 쓰세요.",
        expression="answer=7",
        rule_id="grade3_division_round1_equal_quotients_blank",
    ),
    4: ElementaryVisualTemplate(
        problem_text="몫이 작은 것부터 차례대로 기호를 써 보세요.",
        expression="answer_text=나, 가, 다",
        rule_id="grade3_division_round1_order_by_quotient",
    ),
    5: ElementaryVisualTemplate(
        problem_text="길이가 18 m인 종이띠를 3명이 똑같이 나누어 가지려고 합니다. 한 명이 몇 m씩 가져야 합니까?",
        expression="answer_text=6 m",
        topic="measurement",
        rule_id="grade3_division_round1_18m_paper_3_people",
    ),
}


_GRADE3_DIVISION_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="사탕 16개를 4명에게 똑같이 나누어 주면 한 명에게 몇 개씩 나누어 줄 수 있습니까?",
        expression="answer_text=4 개",
        rule_id="grade3_division_round2_16_candies_4_people",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그림을 보고 20÷4의 몫을 구하세요.",
        expression="answer=5",
        rule_id="grade3_division_round2_20_div_4_visual",
    ),
    3: ElementaryVisualTemplate(
        problem_text="27-9-9-9=0을 나눗셈식으로 나타내세요.",
        expression="answer_text=27 ÷ 9 = 3",
        rule_id="grade3_division_round2_repeated_subtraction_to_division",
    ),
    4: ElementaryVisualTemplate(
        problem_text="56÷7의 몫을 구하세요.",
        expression="answer=8",
        rule_id="grade3_division_round2_56_div_7_quotient",
    ),
    5: ElementaryVisualTemplate(
        problem_text="40-★-★-★-★-★=0에서 ★의 값을 구하세요.",
        expression="answer=8",
        rule_id="grade3_division_round2_star_repeated_subtraction",
    ),
    6: ElementaryVisualTemplate(
        problem_text="색종이 24장을 봉투 한 개에 6장씩 담으려면 봉투는 모두 몇 개 있어야 하는지 나눗셈식으로 쓰세요.",
        expression="answer_text=24 ÷ 6 = 4",
        rule_id="grade3_division_round2_colored_paper_envelopes",
    ),
    7: ElementaryVisualTemplate(
        problem_text="40÷8과 32÷4의 몫의 크기를 비교하세요.",
        expression="answer_text=<",
        rule_id="grade3_division_round2_compare_quotients",
    ),
    8: ElementaryVisualTemplate(
        problem_text="귤 63개를 봉지 7개에 똑같이 나누어 담으면 한 봉지에 몇 개씩 담아야 합니까?",
        expression="answer_text=9 개",
        rule_id="grade3_division_round2_63_tangerines_7_bags",
    ),
    9: ElementaryVisualTemplate(
        problem_text="수 카드 4, 6, 2 중 한 장을 넣어 12÷□의 몫이 가장 클 때 몫을 구하세요.",
        expression="answer=6",
        rule_id="grade3_division_round2_largest_quotient_card",
    ),
}


_GRADE3_DIVISION_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="12÷4=□÷7에서 □ 안에 알맞은 수를 쓰세요.",
        expression="answer=21",
        rule_id="grade3_division_round2_equal_quotients_blank",
    ),
    2: ElementaryVisualTemplate(
        problem_text="1에서 9까지의 수 중에서 18÷6<□ 안에 들어갈 수 있는 수는 모두 몇 개인지 구하세요.",
        expression="answer_text=6 개",
        rule_id="grade3_division_round2_count_numbers_greater_than_three",
    ),
    3: ElementaryVisualTemplate(
        problem_text="계산 흐름도에서 빈 곳에 알맞은 수를 써 넣으세요.",
        expression="answer_text=42, 6",
        rule_id="grade3_division_round2_flowchart_blanks",
    ),
    4: ElementaryVisualTemplate(
        problem_text="곱셈식 4×12=48을 나눗셈식으로 바르게 나타낸 것에 ○표 하세요.",
        expression="answer_text=가운데 식에 ○표",
        rule_id="grade3_division_round2_pick_correct_division_sentence",
    ),
    5: ElementaryVisualTemplate(
        problem_text="54개의 장난감을 6시간 동안 일정한 빠르기로 만들 때 1시간 동안 만들 수 있는 장난감은 몇 개인지 구하세요.",
        expression="answer_text=9 개",
        rule_id="grade3_division_round2_toys_per_hour",
    ),
    6: ElementaryVisualTemplate(
        problem_text="승용차 바퀴 수가 모두 36개일 때 주차장에 있는 승용차는 모두 몇 대입니까?",
        expression="answer_text=9 대",
        rule_id="grade3_division_round2_cars_from_wheels",
    ),
    7: ElementaryVisualTemplate(
        problem_text="수 카드 3, 8, 7, 2로 만든 가장 큰 두 자리 수와 가장 작은 두 자리 수의 차를 8로 나눈 몫을 구하세요.",
        expression="answer=8",
        rule_id="grade3_division_round2_digit_cards_difference_divided_by_8",
    ),
    8: ElementaryVisualTemplate(
        problem_text="색연필 25자루와 15자루를 한 필통에 8자루씩 담으려면 몇 개의 필통이 필요한지 구하세요.",
        expression="answer_text=5 개",
        rule_id="grade3_division_round2_colored_pencils_cases",
    ),
    9: ElementaryVisualTemplate(
        problem_text="구슬 84개 중 39개를 주고 남은 구슬을 5명에게 똑같이 나누면 한 명에게 몇 개씩 나누어 줍니까?",
        expression="answer_text=9 개",
        rule_id="grade3_division_round2_marbles_remaining_divided_by_5",
    ),
    10: ElementaryVisualTemplate(
        problem_text="어떤 수를 6으로 나누었을 때의 몫은 4입니다. 어떤 수를 3으로 나누면 몫은 얼마입니까?",
        expression="answer=8",
        rule_id="grade3_division_round2_unknown_number_divide_by_3",
    ),
    11: ElementaryVisualTemplate(
        problem_text="가로 12 cm, 세로 4 cm인 직사각형을 같은 작은 직사각형 4개로 나누었습니다. 작은 직사각형의 네 변의 길이의 합을 구하세요.",
        expression="answer_text=14 cm",
        topic="measurement",
        rule_id="grade3_division_round2_small_rectangle_perimeter",
    ),
}


_GRADE3_DIVISION_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="딸기 35개를 접시 5개에 똑같이 나누어 담으면 한 접시에 몇 개씩 담아야 합니까?",
        expression="answer_text=7 개",
        rule_id="grade3_division_round3_35_strawberries_5_plates",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그림을 보고 15÷3의 몫을 구하세요.",
        expression="answer=5",
        rule_id="grade3_division_round3_15_div_3_visual",
    ),
    3: ElementaryVisualTemplate(
        problem_text="28-7-7-7-7=0을 나눗셈식으로 나타내세요.",
        expression="answer_text=28 ÷ 7 = 4",
        rule_id="grade3_division_round3_repeated_subtraction_to_division",
    ),
    4: ElementaryVisualTemplate(
        problem_text="48÷8의 몫을 구하세요.",
        expression="answer=6",
        rule_id="grade3_division_round3_48_div_8_quotient",
    ),
    5: ElementaryVisualTemplate(
        problem_text="42-★-★-★-★-★-★=0에서 ★의 값을 구하세요.",
        expression="answer=7",
        rule_id="grade3_division_round3_star_repeated_subtraction",
    ),
    6: ElementaryVisualTemplate(
        problem_text="꽃 36송이를 꽃병 한 개에 9송이씩 꽂으면 필요한 꽃병은 모두 몇 개인지 나눗셈식으로 쓰세요.",
        expression="answer_text=36 ÷ 9 = 4",
        rule_id="grade3_division_round3_flowers_vases",
    ),
    7: ElementaryVisualTemplate(
        problem_text="24÷3과 45÷5의 몫의 크기를 비교하세요.",
        expression="answer_text=<",
        rule_id="grade3_division_round3_compare_quotients",
    ),
    8: ElementaryVisualTemplate(
        problem_text="학생 30명을 한 줄에 5명씩 세우면 몇 줄로 세워야 합니까?",
        expression="answer_text=6 줄",
        rule_id="grade3_division_round3_students_rows",
    ),
    9: ElementaryVisualTemplate(
        problem_text="수 카드 9, 6, 2 중 한 장을 넣어 18÷□의 몫이 가장 작을 때 몫을 구하세요.",
        expression="answer=2",
        rule_id="grade3_division_round3_smallest_quotient_card",
    ),
}


_GRADE3_DIVISION_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="30÷6=40÷□에서 □ 안에 알맞은 수를 쓰세요.",
        expression="answer=8",
        rule_id="grade3_division_round3_equal_quotients_blank",
    ),
    2: ElementaryVisualTemplate(
        problem_text="1에서 9까지의 수 중에서 45÷9>□ 안에 들어갈 수 있는 수는 모두 몇 개인지 구하세요.",
        expression="answer_text=4 개",
        rule_id="grade3_division_round3_count_numbers_less_than_five",
    ),
    3: ElementaryVisualTemplate(
        problem_text="계산 흐름도에서 빈 곳에 알맞은 수를 써 넣으세요.",
        expression="answer_text=7, 7",
        rule_id="grade3_division_round3_flowchart_blanks",
    ),
    4: ElementaryVisualTemplate(
        problem_text="곱셈식 9×5=45를 나눗셈식으로 바르게 나타낸 것에 ○표 하세요.",
        expression="answer_text=왼쪽 식에 ○표",
        rule_id="grade3_division_round3_pick_correct_division_sentence",
    ),
    5: ElementaryVisualTemplate(
        problem_text="24개의 피자빵을 3시간 동안 일정한 빠르기로 만들 때 1시간 동안 만들 수 있는 피자빵은 몇 개인지 구하세요.",
        expression="answer_text=8 개",
        rule_id="grade3_division_round3_pizza_bread_per_hour",
    ),
    6: ElementaryVisualTemplate(
        problem_text="세발자전거의 바퀴 수가 모두 24개일 때 세발자전거는 몇 대 있습니까?",
        expression="answer_text=8 대",
        rule_id="grade3_division_round3_tricycles_from_wheels",
    ),
    7: ElementaryVisualTemplate(
        problem_text="수 카드 8, 3, 5, 9로 만든 가장 큰 두 자리 수와 가장 작은 두 자리 수의 차를 7로 나눈 몫을 구하세요.",
        expression="answer=9",
        rule_id="grade3_division_round3_digit_cards_difference_divided_by_7",
    ),
    8: ElementaryVisualTemplate(
        problem_text="농구공 21개와 배구공 35개를 한 바구니에 7개씩 나누어 담으면 몇 개의 바구니가 필요한지 구하세요.",
        expression="answer_text=8 개",
        rule_id="grade3_division_round3_balls_baskets",
    ),
    9: ElementaryVisualTemplate(
        problem_text="전체 90쪽인 동화책을 오늘 27쪽 읽고 나머지를 일주일 동안 똑같이 나누어 읽으면 하루에 몇 쪽씩 읽어야 합니까?",
        expression="answer_text=9 쪽",
        rule_id="grade3_division_round3_book_pages_per_day",
    ),
    10: ElementaryVisualTemplate(
        problem_text="어떤 수를 3으로 나누었더니 몫이 8이었습니다. 이 수를 6으로 나누면 몫은 얼마입니까?",
        expression="answer=4",
        rule_id="grade3_division_round3_unknown_number_divide_by_6",
    ),
    11: ElementaryVisualTemplate(
        problem_text="가로 25 cm, 세로 8 cm인 직사각형을 같은 작은 직사각형 5개로 나누었습니다. 작은 직사각형의 네 변의 길이의 합을 구하세요.",
        expression="answer_text=26 cm",
        topic="measurement",
        rule_id="grade3_division_round3_small_rectangle_perimeter",
    ),
}


_GRADE3_DIAGNOSTIC_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="325를 백, 십, 일의 개수로 나타내세요.",
        expression="answer_text=3, 2, 5",
        rule_id="grade3_diagnostic_round3_place_value_325",
    ),
    2: ElementaryVisualTemplate(
        problem_text="752보다 10만큼 더 작은 수와 100만큼 더 큰 수를 쓰세요.",
        expression="answer_text=742, 852",
        rule_id="grade3_diagnostic_round3_752_neighbors",
    ),
    3: ElementaryVisualTemplate(
        problem_text="삼각형과 사다리꼴의 변의 수, 꼭짓점의 수, 도형의 이름을 쓰세요.",
        expression="answer_text=삼각형: 변 3개, 꼭짓점 3개 / 사다리꼴: 변 4개, 꼭짓점 4개",
        topic="geometry",
        rule_id="grade3_diagnostic_round3_shape_table",
    ),
    4: ElementaryVisualTemplate(
        problem_text="45에서 17을 더하고 28을 뺀 값을 쓰세요.",
        expression="answer_text=62, 34",
        rule_id="grade3_diagnostic_round3_operation_path",
    ),
    5: ElementaryVisualTemplate(
        problem_text="93-29와 28+37 중 계산 결과가 더 큰 것에 ○표 하세요.",
        expression="answer_text=28+37에 ○표",
        rule_id="grade3_diagnostic_round3_larger_result",
    ),
    6: ElementaryVisualTemplate(
        problem_text="한 칸의 길이가 1 cm일 때 주어진 6 cm만큼 색칠하세요.",
        expression="answer_text=6칸 색칠",
        topic="measurement",
        rule_id="grade3_diagnostic_round3_color_6cm",
    ),
    7: ElementaryVisualTemplate(
        problem_text="클립 5개의 길이와 같은 길이의 연필에 ○표 하세요.",
        expression="answer_text=첫 번째에 ○표",
        topic="measurement",
        rule_id="grade3_diagnostic_round3_clip_length_pencil",
    ),
    8: ElementaryVisualTemplate(
        problem_text="사과, 오렌지, 망고, 키위 주스를 같은 수로 준비하려고 합니다. 어느 주스를 몇 개 더 준비해야 하는지 구하세요.",
        expression="answer_text=오렌지, 4",
        topic="statistics",
        rule_id="grade3_diagnostic_round3_juice_shortage",
    ),
}


_GRADE3_DIAGNOSTIC_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="ㄱ×5=30, 9×ㄴ=36일 때 ㄱ과 ㄴ에 알맞은 수의 합을 구하세요.",
        expression="answer=10",
        rule_id="grade3_diagnostic_round3_unknown_factor_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="7씩 3묶음은 7의 몇 배이고, 7+7+7은 얼마인지 쓰세요.",
        expression="answer_text=3, 7, 7, 7, 21",
        rule_id="grade3_diagnostic_round3_repeated_addition",
    ),
    3: ElementaryVisualTemplate(
        problem_text="3852를 보고 빈칸에 각 자리의 숫자를 써넣으세요.",
        expression="answer_text=3, 8, 5, 2",
        rule_id="grade3_diagnostic_round3_place_digits_3852",
    ),
    4: ElementaryVisualTemplate(
        problem_text="5671과 5195의 크기를 비교하여 ○ 안에 > 또는 <를 쓰세요.",
        expression="answer_text=>",
        rule_id="grade3_diagnostic_round3_compare_5671_5195",
    ),
    5: ElementaryVisualTemplate(
        problem_text="두 곱셈구구의 곱이 같을 때 3×□ = 2×9에서 □ 안에 알맞은 수를 구하세요.",
        expression="answer=6",
        rule_id="grade3_diagnostic_round3_equal_product_blank",
    ),
    6: ElementaryVisualTemplate(
        problem_text="0부터 9까지의 수 중에서 4×□ < 24의 □ 안에 들어갈 수 있는 수를 모두 쓰세요.",
        expression="answer_text=0, 1, 2, 3, 4, 5",
        rule_id="grade3_diagnostic_round3_inequality_possible_digits",
    ),
    7: ElementaryVisualTemplate(
        problem_text="3 m 10 cm와 130 cm의 길이를 비교하여 ○ 안에 >, =, <를 쓰세요.",
        expression="answer_text=>",
        topic="measurement",
        rule_id="grade3_diagnostic_round3_compare_lengths",
    ),
    8: ElementaryVisualTemplate(
        problem_text="길이가 같은 것에 ○표 하세요.",
        expression="answer_text=③",
        topic="measurement",
        rule_id="grade3_diagnostic_round3_same_length_choice",
    ),
    9: ElementaryVisualTemplate(
        problem_text="시계를 보고 □ 안에 알맞은 수를 써넣으세요.",
        expression="answer_text=11 시 55 분",
        topic="measurement",
        rule_id="grade3_diagnostic_round3_clock_time",
    ),
}


_GRADE3_DIAGNOSTIC_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="정국이네 반 학생들이 배우고 있는 운동 표에서 테니스는 모두 몇 명이 배우고 있는지 구하세요.",
        expression="answer_text=7명",
        topic="statistics",
        rule_id="grade3_diagnostic_round3_table_missing_tennis",
    ),
    2: ElementaryVisualTemplate(
        problem_text="규칙에 따라 쌓기나무를 쌓았습니다. 다음에 이어질 모양에 쌓을 쌓기나무는 모두 몇 개입니까?",
        expression="answer_text=10개",
        topic="pattern",
        rule_id="grade3_diagnostic_round3_cube_pattern_next",
    ),
    3: ElementaryVisualTemplate(
        problem_text="4시 55분에서 6시 50분까지는 몇 분입니까?",
        expression="answer_text=115분",
        topic="measurement",
        rule_id="grade3_diagnostic_round3_elapsed_minutes",
    ),
}


_GRADE4_DIAGNOSTIC_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="772+148과 287+698의 계산 결과를 비교하여 ○ 안에 알맞은 부등호를 쓰세요.",
        expression="answer_text=<",
        rule_id="grade4_diagnostic_round2_compare_sums",
    ),
    2: ElementaryVisualTemplate(
        problem_text="수 카드 2, 3, 8을 한 번씩만 사용하여 만들 수 있는 가장 큰 세 자리 수와 가장 작은 세 자리 수의 차를 구하세요.",
        expression="answer_text=594",
        rule_id="grade4_diagnostic_round2_digit_cards_difference",
    ),
    3: ElementaryVisualTemplate(
        problem_text="도형을 보고 선분, 직선, 반직선의 이름을 바르게 쓰세요.",
        expression="answer_text=(1) 선분 ㄷㄹ, (2) 직선 ㄷㄹ, (3) 반직선 ㄷㄹ",
        topic="geometry",
        rule_id="grade4_diagnostic_round2_line_names",
    ),
    4: ElementaryVisualTemplate(
        problem_text="24-6-6-6-6=0 뺄셈식을 보고 나눗셈식으로 나타내세요.",
        expression="answer_text=24÷6=4",
        rule_id="grade4_diagnostic_round2_repeated_subtraction_division",
    ),
    5: ElementaryVisualTemplate(
        problem_text="색종이 32장을 봉투 한 개에 4장씩 담으려면 봉투가 모두 몇 개 필요한지 구하세요.",
        expression="answer_text=8 개",
        rule_id="grade4_diagnostic_round2_envelopes_needed",
    ),
    6: ElementaryVisualTemplate(
        problem_text="34×4와 53×2를 계산하여 두 계산 결과의 차를 구하세요.",
        expression="answer_text=30",
        rule_id="grade4_diagnostic_round2_product_difference",
    ),
    7: ElementaryVisualTemplate(
        problem_text="위인전을 하루에 42쪽씩 7일 동안 읽으면 모두 몇 쪽을 읽는지 구하세요.",
        expression="answer_text=294 쪽",
        rule_id="grade4_diagnostic_round2_pages_read",
    ),
    8: ElementaryVisualTemplate(
        problem_text="12 km 230 m와 15 km 974 m의 합과 차를 구하세요.",
        expression="answer_text=합 28 km 204 m, 차 3 km 744 m",
        topic="measurement",
        rule_id="grade4_diagnostic_round2_length_sum_difference",
    ),
}


_GRADE4_DIAGNOSTIC_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="12시 15분 32초부터 23분 48초 동안 점심을 먹었을 때 다 먹은 시각을 구하세요.",
        expression="answer_text=12 시 39 분 20 초",
        topic="measurement",
        rule_id="grade4_diagnostic_round2_lunch_finish_time",
    ),
    2: ElementaryVisualTemplate(
        problem_text="1/3과 1/7을 비교하여 ○ 안에 알맞은 부등호를 쓰세요.",
        expression="answer_text=>",
        topic="fraction_ratio",
        rule_id="grade4_diagnostic_round2_compare_unit_fractions",
    ),
    3: ElementaryVisualTemplate(
        problem_text="계산 결과가 같은 것끼리 선으로 이으세요.",
        expression="answer_text=471×6 ↔ 2826, 326×4 ↔ 1304",
        rule_id="grade4_diagnostic_round2_match_products",
    ),
    4: ElementaryVisualTemplate(
        problem_text="사탕을 한 사람에게 7개씩 186명에게 나누어 주었더니 5개가 남았습니다. 처음에 있던 사탕은 모두 몇 개인지 구하세요.",
        expression="answer_text=1307 개",
        rule_id="grade4_diagnostic_round2_candy_total",
    ),
    5: ElementaryVisualTemplate(
        problem_text="나눗셈 계산 결과를 찾아 선으로 이으세요.",
        expression="answer_text=44÷4 ↔ 11, 39÷3 ↔ 13, 24÷2 ↔ 12",
        rule_id="grade4_diagnostic_round2_match_divisions",
    ),
    6: ElementaryVisualTemplate(
        problem_text="네 변의 길이의 합이 48 cm인 정사각형의 한 변의 길이를 구하세요.",
        expression="answer_text=12 cm",
        topic="measurement",
        rule_id="grade4_diagnostic_round2_square_side_from_perimeter",
    ),
    7: ElementaryVisualTemplate(
        problem_text="두 원의 지름의 차는 몇 cm인지 구하세요.",
        expression="answer_text=3 cm",
        topic="geometry",
        rule_id="grade4_diagnostic_round2_circle_diameter_difference",
    ),
    8: ElementaryVisualTemplate(
        problem_text="20은 35의 4/㉠입니다. ㉠에 알맞은 수를 구하세요.",
        expression="answer_text=7",
        topic="fraction_ratio",
        rule_id="grade4_diagnostic_round2_fraction_denominator",
    ),
}


_GRADE4_DIAGNOSTIC_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="분모와 분자의 합이 14인 진분수를 찾아 ○표 하세요.",
        expression="answer_text=5/9 에 ○표",
        topic="fraction_ratio",
        rule_id="grade4_diagnostic_round2_proper_fraction_sum14",
    ),
    2: ElementaryVisualTemplate(
        problem_text="2 L의 물이 들어 있는 물통에 900 mL를 더 부었을 때 물의 양을 L와 mL로 나타내세요.",
        expression="answer_text=2 L 900 mL",
        topic="measurement",
        rule_id="grade4_diagnostic_round2_water_total_l_ml",
    ),
    3: ElementaryVisualTemplate(
        problem_text="무게 단위 사이의 관계가 틀린 것을 모두 고르세요.",
        expression="answer_text=③, ⑤",
        topic="measurement",
        rule_id="grade4_diagnostic_round2_wrong_weight_conversions",
    ),
    4: ElementaryVisualTemplate(
        problem_text="사탕 판매량 그림그래프에서 전체 판매량이 177개일 때 달 모양 사탕의 판매량을 구하세요.",
        expression="answer_text=51 개",
        topic="statistics",
        rule_id="grade4_diagnostic_round2_moon_candy_count",
    ),
}


_GRADE4_DIAGNOSTIC_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="429+574와 524-179를 계산하세요.",
        expression="answer_text=(1) 1003, (2) 345",
        rule_id="grade4_diagnostic_round1_add_subtract",
    ),
    2: ElementaryVisualTemplate(
        problem_text="정국이는 스티커를 292장, 지민이는 314장 모았습니다. 누가 몇 장 더 많이 모았는지 쓰세요.",
        expression="answer_text=지민, 22 장",
        rule_id="grade4_diagnostic_round1_sticker_difference",
    ),
    3: ElementaryVisualTemplate(
        problem_text="네 변의 길이의 합이 24 cm인 정사각형의 한 변의 길이를 구하세요.",
        expression="answer_text=6 cm",
        topic="measurement",
        rule_id="grade4_diagnostic_round1_square_side_from_perimeter",
    ),
    4: ElementaryVisualTemplate(
        problem_text="35에서 같은 수를 5번 빼서 0이 될 때 같은 수의 값을 구하세요.",
        expression="answer_text=7",
        rule_id="grade4_diagnostic_round1_repeated_subtraction_star",
    ),
    5: ElementaryVisualTemplate(
        problem_text="귤 72개를 봉지 9개에 똑같이 나누어 담으려면 한 봉지에 몇 개씩 담아야 하는지 구하세요.",
        expression="answer_text=8 개",
        rule_id="grade4_diagnostic_round1_tangerines_per_bag",
    ),
    6: ElementaryVisualTemplate(
        problem_text="26, 13, 29, 8 중 가장 큰 수와 가장 작은 수의 곱을 구하세요.",
        expression="answer_text=232",
        rule_id="grade4_diagnostic_round1_largest_smallest_product",
    ),
    7: ElementaryVisualTemplate(
        problem_text="여학생 15명, 남학생 17명에게 연필을 5자루씩 나누어 주려면 필요한 연필 수를 구하세요.",
        expression="answer_text=160 자루",
        rule_id="grade4_diagnostic_round1_pencils_needed",
    ),
    8: ElementaryVisualTemplate(
        problem_text="길이를 잘못 읽은 것을 고르세요.",
        expression="answer_text=④",
        topic="measurement",
        rule_id="grade4_diagnostic_round1_wrong_length_reading",
    ),
}


_GRADE4_DIAGNOSTIC_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="전체를 똑같이 셋으로 나눈 것에 ○표 하세요.",
        expression="answer_text=세 번째에 ○표",
        topic="geometry",
        rule_id="grade4_diagnostic_round1_equal_thirds_choice",
    ),
    2: ElementaryVisualTemplate(
        problem_text="단위분수이고 분자와 분모의 합이 13인 분수를 쓰세요.",
        expression="answer_text=1/12",
        topic="fraction_ratio",
        rule_id="grade4_diagnostic_round1_unit_fraction_sum13",
    ),
    3: ElementaryVisualTemplate(
        problem_text="계산 결과가 같은 것끼리 선으로 이으세요.",
        expression="answer_text=40×30 ↔ 1200, 20×80 ↔ 1600, 60×40 ↔ 2400",
        rule_id="grade4_diagnostic_round1_match_products",
    ),
    4: ElementaryVisualTemplate(
        problem_text="지우개가 한 상자에 62개씩 들어 있습니다. 24상자에 들어 있는 지우개는 모두 몇 개인지 구하세요.",
        expression="answer_text=1488",
        rule_id="grade4_diagnostic_round1_erasers_total",
    ),
    5: ElementaryVisualTemplate(
        problem_text="60÷5, 30÷3, 80÷4의 몫이 큰 것부터 차례로 기호를 쓰세요.",
        expression="answer_text=다, 가, 나",
        rule_id="grade4_diagnostic_round1_quotient_order",
    ),
    6: ElementaryVisualTemplate(
        problem_text="사탕 90개를 5개의 봉지에 똑같이 나누어 담으면 한 봉지에는 몇 개를 담아야 하는지 구하세요.",
        expression="answer_text=18 개",
        rule_id="grade4_diagnostic_round1_candies_per_bag",
    ),
    7: ElementaryVisualTemplate(
        problem_text="원의 반지름과 지름은 각각 몇 cm인지 구하세요.",
        expression="answer_text=반지름 7 cm, 지름 14 cm",
        topic="geometry",
        rule_id="grade4_diagnostic_round1_circle_radius_diameter",
    ),
    8: ElementaryVisualTemplate(
        problem_text="사과 전체를 똑같이 3부분으로 나누면 한 부분은 몇 개인지 구하세요.",
        expression="answer_text=5 개",
        rule_id="grade4_diagnostic_round1_apples_one_third",
    ),
}


_GRADE4_DIAGNOSTIC_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="24의 1/8과 24의 5/8에 알맞은 수를 써넣으세요.",
        expression="answer_text=3, 15",
        topic="fraction_ratio",
        rule_id="grade4_diagnostic_round1_fraction_of_24",
    ),
    2: ElementaryVisualTemplate(
        problem_text="물병을 가득 채우는 데 가 컵은 5컵, 나 컵은 9컵이 필요했습니다. 어느 쪽의 들이가 더 많은지 쓰세요.",
        expression="answer_text=가 컵",
        topic="measurement",
        rule_id="grade4_diagnostic_round1_larger_cup_capacity",
    ),
    3: ElementaryVisualTemplate(
        problem_text="6000 kg=㉠ t, ㉡ g=16 kg일 때 ㉠과 ㉡에 알맞은 수의 합을 구하세요.",
        expression="answer_text=16006",
        topic="measurement",
        rule_id="grade4_diagnostic_round1_weight_unit_sum",
    ),
    4: ElementaryVisualTemplate(
        problem_text="음료수 판매량 그림그래프를 보고 다음 달에 가장 많이 준비하면 좋은 음료수를 쓰세요.",
        expression="answer_text=사이다",
        topic="statistics",
        rule_id="grade4_diagnostic_round1_drink_most_sold",
    ),
}


_GRADE4_BIG_NUMBER_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="각 자리의 숫자가 나타내는 값의 합으로 나타내세요.",
        expression="answer_text=(1) 80000, 30, 1, (2) 40000+3000+1",
        rule_id="grade4_big_number_round1_place_value_expansion",
    ),
    2: ElementaryVisualTemplate(
        problem_text="10000은 어떤 수보다 1 큰 수입니다. 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=9999",
        rule_id="grade4_big_number_round1_before_10000",
    ),
    3: ElementaryVisualTemplate(
        problem_text="81006, 82008, 팔만 백육십을 보고 빈칸에 알맞은 수나 말을 쓰세요.",
        expression="answer_text=팔만 이천팔, 80160",
        rule_id="grade4_big_number_round1_write_read_table",
    ),
    4: ElementaryVisualTemplate(
        problem_text="57019와 이만삼천팔십칠을 읽고 쓴 말 중 잘못 말한 사람을 고르세요.",
        expression="answer_text=영수",
        rule_id="grade4_big_number_round1_wrong_statement",
    ),
    5: ElementaryVisualTemplate(
        problem_text="48357680095에서 ㉠이 나타내는 값은 ㉡이 나타내는 값의 몇 배인지 구하세요.",
        expression="answer_text=100000 배",
        rule_id="grade4_big_number_round1_place_value_ratio",
    ),
    6: ElementaryVisualTemplate(
        problem_text="58762의 만의 자리 숫자와 890320912의 십만의 자리 숫자를 구하세요.",
        expression="answer_text=(1) 5, (2) 3",
        rule_id="grade4_big_number_round1_place_digits",
    ),
    7: ElementaryVisualTemplate(
        problem_text="수를 1000배씩 한 규칙에서 ㉠에 알맞은 수를 구하세요.",
        expression="answer_text=8400",
        topic="pattern",
        rule_id="grade4_big_number_round1_times_1000_chain",
    ),
    8: ElementaryVisualTemplate(
        problem_text="숫자 카드 2, 9, 6, 5, 3을 한 번씩 사용하여 가장 큰 다섯 자리 수를 만드세요.",
        expression="answer_text=96532",
        rule_id="grade4_big_number_round1_largest_five_digit",
    ),
    9: ElementaryVisualTemplate(
        problem_text="21085479 < 2108□614가 되도록 □ 안에 들어갈 수 있는 숫자를 모두 쓰세요.",
        expression="answer_text=5, 6, 7, 8, 9",
        rule_id="grade4_big_number_round1_inequality_digits",
    ),
}


_GRADE4_BIG_NUMBER_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="20984, 8793, 188942, 87554의 크기를 비교하여 큰 수부터 차례로 기호를 쓰세요.",
        expression="answer_text=다, 라, 가, 나",
        rule_id="grade4_big_number_round1_order_numbers",
    ),
    2: ElementaryVisualTemplate(
        problem_text="10만이 32개, 1만이 21개, 1000이 30개, 100이 1개인 수를 구하세요.",
        expression="answer_text=3440100",
        rule_id="grade4_big_number_round1_place_value_total",
    ),
    3: ElementaryVisualTemplate(
        problem_text="990000보다 10000 큰 수는 9999보다 1 큰 수의 몇 배인지 구하세요.",
        expression="answer_text=100 배",
        rule_id="grade4_big_number_round1_number_ratio",
    ),
    4: ElementaryVisualTemplate(
        problem_text="3조 450억에서 50억씩 10번 뛰어서 센 수를 구하세요.",
        expression="answer_text=3 조 950 억",
        rule_id="grade4_big_number_round1_counting_by_50eok",
    ),
    5: ElementaryVisualTemplate(
        problem_text="149600000 km의 100배는 몇 km인지 읽어 보세요.",
        expression="answer_text=백사십구억 육천만 킬로미터",
        rule_id="grade4_big_number_round1_sun_earth_distance_reading",
    ),
    6: ElementaryVisualTemplate(
        problem_text="30000개의 사과를 한 상자에 1000개씩 담으면 상자가 몇 개 필요한지 구하세요.",
        expression="answer_text=30 개",
        rule_id="grade4_big_number_round1_apple_boxes",
    ),
    7: ElementaryVisualTemplate(
        problem_text="서로 같은 것끼리 선으로 이으세요.",
        expression="answer_text=700만의 1000배 ↔ 70억, 7000만의 10배 ↔ 7억, 7억의 100배 ↔ 700억",
        rule_id="grade4_big_number_round1_match_large_number_products",
    ),
    8: ElementaryVisualTemplate(
        problem_text="3270억에서 10억씩 5번, 65만에서 10배씩 6번, 550억에서 10배씩 4번 뛰어 센 수 중 더 큰 수의 기호를 쓰세요.",
        expression="answer_text=다",
        rule_id="grade4_big_number_round1_larger_counting_rule",
    ),
    9: ElementaryVisualTemplate(
        problem_text="10000원 13장, 1000원 9장, 100원 7개를 냈을 때 물건값을 구하세요.",
        expression="answer_text=139700 원",
        rule_id="grade4_big_number_round1_money_total",
    ),
    10: ElementaryVisualTemplate(
        problem_text="두께가 25 mm인 위인전 40만 권의 두께를 km로 구하세요.",
        expression="answer_text=10 km",
        topic="measurement",
        rule_id="grade4_big_number_round1_books_thickness_km",
    ),
    11: ElementaryVisualTemplate(
        problem_text="숫자 카드 2, 9, 6, 0, 3을 각각 3장씩 사용하여 만들 수 있는 가장 작은 10자리 수에서 십만의 자리 숫자가 나타내는 수를 구하세요.",
        expression="answer_text=200000",
        rule_id="grade4_big_number_round1_smallest_ten_digit_place_value",
    ),
}


_GRADE4_BIG_NUMBER_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="10000은 7000보다 몇 큰 수인지 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=3000",
        rule_id="grade4_big_number_round2_difference_from_7000_to_10000",
    ),
    2: ElementaryVisualTemplate(
        problem_text="10000이 5개, 1000이 2개, 100이 9개, 10이 7개, 1이 4개인 수를 쓰고 읽으세요.",
        expression="answer_text=오만이천구백칠십사, 52974",
        rule_id="grade4_big_number_round2_write_read_place_value",
    ),
    3: ElementaryVisualTemplate(
        problem_text="0에서 5까지의 수를 한 번씩만 사용하여 만의 자리 숫자가 3인 가장 작은 수를 만드세요.",
        expression="answer_text=130245",
        rule_id="grade4_big_number_round2_smallest_number_ten_thousands_digit_3",
    ),
    4: ElementaryVisualTemplate(
        problem_text="13250, 80352, 32214, 10743, 13874 중 3이 나타내는 수가 가장 큰 것을 고르세요.",
        expression="answer_text=③",
        rule_id="grade4_big_number_round2_largest_place_value_of_3",
    ),
    5: ElementaryVisualTemplate(
        problem_text="75264920에서 숫자 6은 어떤 자리를 나타내는지 쓰세요.",
        expression="answer_text=만의 자리",
        rule_id="grade4_big_number_round2_digit_6_place",
    ),
    6: ElementaryVisualTemplate(
        problem_text="73268942에서 숫자 7이 나타내는 값은 3748318에서 숫자 7이 나타내는 값의 몇 배인지 구하세요.",
        expression="answer_text=100 배",
        rule_id="grade4_big_number_round2_place_value_ratio_of_7",
    ),
    7: ElementaryVisualTemplate(
        problem_text="32000000은 100만이 몇 개인 수인지 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=32",
        rule_id="grade4_big_number_round2_millions_in_32000000",
    ),
    8: ElementaryVisualTemplate(
        problem_text="9999만보다 1만만큼 더 큰 수는 얼마인지 구하세요.",
        expression="answer_text=1억",
        rule_id="grade4_big_number_round2_one_man_more_than_9999man",
    ),
    9: ElementaryVisualTemplate(
        problem_text="1조는 9999억보다 몇 억 큰 수인지 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=1 억",
        rule_id="grade4_big_number_round2_one_jo_more_than_9999eok",
    ),
    10: ElementaryVisualTemplate(
        problem_text="3000억을 10배 한 수를 수로 나타내세요.",
        expression="answer_text=3000000000000",
        rule_id="grade4_big_number_round2_3000eok_times_10",
    ),
}


_GRADE4_BIG_NUMBER_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="조가 3015, 억이 8426, 만이 597, 일이 43인 수를 쓰세요.",
        expression="answer_text=3015842605970043",
        rule_id="grade4_big_number_round2_write_grouped_large_number",
    ),
    2: ElementaryVisualTemplate(
        problem_text="3729348710000000에서 십조의 자리 숫자를 찾아 쓰세요.",
        expression="answer_text=2",
        rule_id="grade4_big_number_round2_ten_jo_digit",
    ),
    3: ElementaryVisualTemplate(
        problem_text="삼백칠억 칠십오만 이백칠을 수로 나타내면 숫자 0은 모두 몇 개인지 구하세요.",
        expression="answer_text=5 개",
        rule_id="grade4_big_number_round2_count_zero_digits",
    ),
    4: ElementaryVisualTemplate(
        problem_text="360억에서 10억씩 4번 뛰어서 세면 얼마인지 구하세요.",
        expression="answer_text=400억",
        rule_id="grade4_big_number_round2_count_by_10eok",
    ),
    5: ElementaryVisualTemplate(
        problem_text="10000원짜리 3장, 1000원짜리 37장, 100원짜리 42개, 10원짜리 21개를 저금한 돈은 모두 얼마인지 구하세요.",
        expression="answer_text=71410 원",
        rule_id="grade4_big_number_round2_money_total",
    ),
    6: ElementaryVisualTemplate(
        problem_text="하루에 단추를 70000개씩 만드는 공장에서 30일 동안 만들 수 있는 단추는 모두 몇 개인지 구하세요.",
        expression="answer_text=2100000 개",
        rule_id="grade4_big_number_round2_buttons_30_days",
    ),
    7: ElementaryVisualTemplate(
        problem_text="3750000원을 만 원짜리 지폐로 모두 찾으려면 몇 장을 찾아야 하는지 구하세요.",
        expression="answer_text=375 장",
        rule_id="grade4_big_number_round2_ten_thousand_won_bills",
    ),
    8: ElementaryVisualTemplate(
        problem_text="이익금 12억 3천만 원을 1000명의 직원에게 똑같이 나누어 주면 한 사람이 받는 금액은 얼마인지 구하세요.",
        expression="answer_text=1230000 원",
        rule_id="grade4_big_number_round2_profit_split_1000",
    ),
    9: ElementaryVisualTemplate(
        problem_text="2020년도 수출량은 2000만 개이고 해마다 5000개씩 더 수출했다면 2024년의 수출량은 몇 개인지 구하세요.",
        expression="answer_text=20020000 개",
        rule_id="grade4_big_number_round2_export_count_2024",
    ),
    10: ElementaryVisualTemplate(
        problem_text="23628□290<236283190에서 □ 안에 들어갈 수 있는 한 자리 숫자를 모두 구하세요.",
        expression="answer_text=0, 1, 2",
        rule_id="grade4_big_number_round2_inequality_missing_digit",
    ),
}


_GRADE4_BIG_NUMBER_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="9800보다 몇 큰 수가 10000인지 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=200",
        rule_id="grade4_big_number_round3_difference_from_9800_to_10000",
    ),
    2: ElementaryVisualTemplate(
        problem_text="10000이 4개, 1000이 37개, 100이 57개, 1이 4925개인 수를 쓰세요.",
        expression="answer_text=87625",
        rule_id="grade4_big_number_round3_write_place_value_total",
    ),
    3: ElementaryVisualTemplate(
        problem_text="숫자 카드 5, 3, 9, 2, 4를 한 번씩 사용하여 가장 작은 다섯 자리 수를 만드세요.",
        expression="answer_text=23459",
        rule_id="grade4_big_number_round3_smallest_five_digit",
    ),
    4: ElementaryVisualTemplate(
        problem_text="1000만보다 1 작은 수를 고르세요.",
        expression="answer_text=①",
        rule_id="grade4_big_number_round3_one_less_than_1000man",
    ),
    5: ElementaryVisualTemplate(
        problem_text="36872437에서 숫자 6은 어떤 자리를 나타내는지 쓰세요.",
        expression="answer_text=백만의 자리",
        rule_id="grade4_big_number_round3_digit_6_place",
    ),
    6: ElementaryVisualTemplate(
        problem_text="32742175에서 숫자 3이 나타내는 값은 132680에서 숫자 3이 나타내는 값의 몇 배인지 구하세요.",
        expression="answer_text=1000 배",
        rule_id="grade4_big_number_round3_place_value_ratio_of_3",
    ),
    7: ElementaryVisualTemplate(
        problem_text="65000000은 10만이 몇 개인 수인지 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=650",
        rule_id="grade4_big_number_round3_hundred_thousands_in_65000000",
    ),
    8: ElementaryVisualTemplate(
        problem_text="9000만보다 1000만만큼 더 큰 수는 얼마인지 구하세요.",
        expression="answer_text=1억",
        rule_id="grade4_big_number_round3_1000man_more_than_9000man",
    ),
    9: ElementaryVisualTemplate(
        problem_text="1조는 9990억보다 몇 억 큰 수인지 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=10 억",
        rule_id="grade4_big_number_round3_one_jo_more_than_9990eok",
    ),
    10: ElementaryVisualTemplate(
        problem_text="3245억 42만 8을 1000배 한 수를 수로 나타내세요.",
        expression="answer_text=324500420008000",
        rule_id="grade4_big_number_round3_number_times_1000",
    ),
}


_GRADE4_BIG_NUMBER_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="조가 5026, 억이 9370, 만이 3629, 일이 2534인 수를 쓰세요.",
        expression="answer_text=5026937036292534",
        rule_id="grade4_big_number_round3_write_grouped_large_number",
    ),
    2: ElementaryVisualTemplate(
        problem_text="2513843213000000에서 백조의 자리 숫자를 찾아 쓰세요.",
        expression="answer_text=5",
        rule_id="grade4_big_number_round3_hundred_jo_digit",
    ),
    3: ElementaryVisualTemplate(
        problem_text="칠조 삼천오십억 삼백이만 오십을 수로 나타내면 숫자 0은 모두 몇 개인지 구하세요.",
        expression="answer_text=7 개",
        rule_id="grade4_big_number_round3_count_zero_digits",
    ),
    4: ElementaryVisualTemplate(
        problem_text="8800만에서 100만씩 몇 번 뛰어서 세면 9500만이 되는지 구하세요.",
        expression="answer_text=7 번",
        rule_id="grade4_big_number_round3_count_by_100man",
    ),
    5: ElementaryVisualTemplate(
        problem_text="10000원짜리 5장, 1000원짜리 11장, 100원짜리 43개, 10원짜리 15개를 모은 돈은 모두 얼마인지 구하세요.",
        expression="answer_text=65450 원",
        rule_id="grade4_big_number_round3_money_total",
    ),
    6: ElementaryVisualTemplate(
        problem_text="하루에 인형을 40000개씩 만드는 공장에서 20일 동안 만들 수 있는 인형은 모두 몇 개인지 구하세요.",
        expression="answer_text=800000 개",
        rule_id="grade4_big_number_round3_dolls_20_days",
    ),
    7: ElementaryVisualTemplate(
        problem_text="24700000원을 만 원짜리 지폐로 모두 찾으려면 몇 장을 찾아야 하는지 구하세요.",
        expression="answer_text=2470 장",
        rule_id="grade4_big_number_round3_ten_thousand_won_bills",
    ),
    8: ElementaryVisualTemplate(
        problem_text="지구와 태양 사이의 거리는 1억 4960만 km입니다. 이 거리는 1억 m의 몇 배인지 구하세요.",
        expression="answer_text=1496 배",
        topic="measurement",
        rule_id="grade4_big_number_round3_sun_distance_meter_ratio",
    ),
    9: ElementaryVisualTemplate(
        problem_text="2021년도 수출량은 2000만 개이고 해마다 2000개씩 더 수출한다면 2025년의 수출량은 몇 개인지 구하세요.",
        expression="answer_text=20008000 개",
        rule_id="grade4_big_number_round3_export_count_2025",
    ),
    10: ElementaryVisualTemplate(
        problem_text="8274556008<82745□7023에서 □ 안에 들어갈 수 있는 한 자리 숫자를 모두 구하세요.",
        expression="answer_text=5, 6, 7, 8, 9",
        rule_id="grade4_big_number_round3_inequality_missing_digit",
    ),
}


_GRADE4_ANGLE_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="큰 각부터 차례로 기호를 쓰세요.",
        expression="answer_text=나, 다, 가, 라",
        topic="geometry",
        rule_id="grade4_angle_round1_order_angles_largest_to_smallest",
    ),
    2: ElementaryVisualTemplate(
        problem_text="각도기를 보고 각도를 구하세요.",
        expression="answer_text=55°",
        topic="geometry",
        rule_id="grade4_angle_round1_measure_protractor_55",
    ),
    3: ElementaryVisualTemplate(
        problem_text="다음 각을 어림하고 각도기로 재어 확인하세요.",
        expression="answer_text=어림한 각도 : 125° 잰 각도: 125°",
        topic="geometry",
        rule_id="grade4_angle_round1_estimate_and_measure_125",
    ),
    4: ElementaryVisualTemplate(
        problem_text="각도기를 보고 각도를 읽으세요.",
        expression="answer_text=⑴ 70° ⑵ 55°",
        topic="geometry",
        rule_id="grade4_angle_round1_read_two_angles",
    ),
    5: ElementaryVisualTemplate(
        problem_text="예각, 직각, 둔각을 바르게 찾아 기호를 쓰세요.",
        expression="answer_text=가, 다, 나",
        topic="geometry",
        rule_id="grade4_angle_round1_classify_acute_right_obtuse",
    ),
    6: ElementaryVisualTemplate(
        problem_text="각도기를 이용하여 빈칸에 알맞은 각도를 쓰세요.",
        expression="answer_text=가. 85 나. 100",
        topic="geometry",
        rule_id="grade4_angle_round1_fill_two_angles",
    ),
}


_GRADE4_ANGLE_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="각도 목록에서 둔각과 예각이 각각 모두 몇 개인지 구하세요.",
        expression="answer_text=⑴ 3 ⑵ 4",
        topic="geometry",
        rule_id="grade4_angle_round1_count_obtuse_and_acute",
    ),
    2: ElementaryVisualTemplate(
        problem_text="시계에서 시침과 분침이 이루는 각을 예각, 직각, 둔각으로 구분하세요.",
        expression="answer_text=⑴ 둔각 ⑵ 직각",
        topic="geometry",
        rule_id="grade4_angle_round1_clock_angle_types",
    ),
    3: ElementaryVisualTemplate(
        problem_text="175°와 25° 두 각도의 합과 차를 구하세요.",
        expression="answer_text=⑴ 200° ⑵ 150°",
        topic="geometry",
        rule_id="grade4_angle_round1_angle_sum_difference",
    ),
    4: ElementaryVisualTemplate(
        problem_text="180°를 같은 크기의 6개의 각으로 나눈 그림에서 크고 작은 예각은 모두 몇 개인지 구하세요.",
        expression="answer_text=11 개",
        topic="geometry",
        rule_id="grade4_angle_round1_count_acute_angles_in_six_parts",
    ),
    5: ElementaryVisualTemplate(
        problem_text="시계의 긴바늘과 짧은 바늘이 이루는 작은 쪽의 각이 예각인 것을 고르세요.",
        expression="answer_text=나",
        topic="geometry",
        rule_id="grade4_angle_round1_clock_acute_choice",
    ),
    6: ElementaryVisualTemplate(
        problem_text="두 직각삼각자를 이용하여 만든 그림에서 빈칸에 알맞은 각도를 쓰세요.",
        expression="answer_text=15°",
        topic="geometry",
        rule_id="grade4_angle_round1_set_square_angle",
    ),
    7: ElementaryVisualTemplate(
        problem_text="108°+97°와 102°-24°를 계산하세요.",
        expression="answer_text=⑴ 205° ⑵ 78°",
        topic="geometry",
        rule_id="grade4_angle_round1_angle_calculation",
    ),
    8: ElementaryVisualTemplate(
        problem_text="110°와 85°가 주어진 그림에서 □ 안에 알맞은 각을 구하세요.",
        expression="answer_text=25°",
        topic="geometry",
        rule_id="grade4_angle_round1_missing_angle_110_85",
    ),
}


_GRADE4_ANGLE_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="삼각형의 세 꼭짓점을 한 점에 모이도록 이어 붙인 그림에서 ㉠의 각도를 구하세요.",
        expression="answer_text=55°",
        topic="geometry",
        rule_id="grade4_angle_round1_triangle_angles_at_point",
    ),
    2: ElementaryVisualTemplate(
        problem_text="삼각형에서 35°와 120°가 주어졌을 때 ㉠의 각도를 구하세요.",
        expression="answer_text=85°",
        topic="geometry",
        rule_id="grade4_angle_round1_triangle_exterior_angle",
    ),
    3: ElementaryVisualTemplate(
        problem_text="사각형에서 80°와 130°가 주어졌을 때 ㉠과 ㉡의 각도의 합을 구하세요.",
        expression="answer_text=150°",
        topic="geometry",
        rule_id="grade4_angle_round1_quadrilateral_unknown_sum",
    ),
    4: ElementaryVisualTemplate(
        problem_text="도형에서 100°와 115°가 주어졌을 때 ㉮의 크기를 구하세요.",
        expression="answer_text=35°",
        topic="geometry",
        rule_id="grade4_angle_round1_shape_missing_angle_35",
    ),
    5: ElementaryVisualTemplate(
        problem_text="정삼각형과 정사각형을 겹치지 않게 붙인 그림에서 각 ㉮의 크기를 구하세요.",
        expression="answer_text=150°",
        topic="geometry",
        rule_id="grade4_angle_round1_triangle_square_join_angle",
    ),
    6: ElementaryVisualTemplate(
        problem_text="직각을 크기가 같은 각 5개로 나눈 그림에서 각 ㄱㅇㄴ의 크기를 구하세요.",
        expression="answer_text=18°",
        topic="geometry",
        rule_id="grade4_angle_round1_right_angle_five_equal_parts",
    ),
}


_GRADE4_ANGLE_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="큰 각부터 차례로 기호를 쓰세요.",
        expression="answer_text=㉠, ㉣, ㉢, ㉡",
        topic="geometry",
        rule_id="grade4_angle_round2_order_angles_largest_to_smallest",
    ),
    2: ElementaryVisualTemplate(
        problem_text="두 변이 벌어진 정도에 따라 결정되는 것을 고르세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade4_angle_round2_angle_size_definition",
    ),
    3: ElementaryVisualTemplate(
        problem_text="시계의 시침과 분침이 이루는 작은 쪽의 각의 크기가 가장 작은 것을 고르세요.",
        expression="answer_text=⑤",
        topic="geometry",
        rule_id="grade4_angle_round2_smallest_clock_angle_choice",
    ),
    4: ElementaryVisualTemplate(
        problem_text="각도기를 보고 각도를 읽으세요.",
        expression="answer_text=50°",
        topic="geometry",
        rule_id="grade4_angle_round2_read_protractor_50",
    ),
    5: ElementaryVisualTemplate(
        problem_text="각의 크기를 각도기로 재어 보세요.",
        expression="answer_text=65°",
        topic="geometry",
        rule_id="grade4_angle_round2_measure_angle_65",
    ),
    6: ElementaryVisualTemplate(
        problem_text="3시에서 시계의 짧은바늘과 긴바늘이 이루는 작은 각을 고르세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade4_angle_round2_three_oclock_right_angle",
    ),
    7: ElementaryVisualTemplate(
        problem_text="각도 목록에서 둔각은 모두 몇 개인지 구하세요.",
        expression="answer_text=3 개",
        topic="geometry",
        rule_id="grade4_angle_round2_count_obtuse_angles",
    ),
    8: ElementaryVisualTemplate(
        problem_text="270°+25°의 합을 구하세요.",
        expression="answer_text=295°",
        topic="geometry",
        rule_id="grade4_angle_round2_angle_sum_270_25",
    ),
}


_GRADE4_ANGLE_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="135°-47°의 차를 구하세요.",
        expression="answer_text=88°",
        topic="geometry",
        rule_id="grade4_angle_round2_angle_difference_135_47",
    ),
    2: ElementaryVisualTemplate(
        problem_text="105°+30°와 160°-35°의 계산 결과를 비교하세요.",
        expression="answer_text=>",
        topic="geometry",
        rule_id="grade4_angle_round2_compare_angle_calculations",
    ),
    3: ElementaryVisualTemplate(
        problem_text="130°, 50°, 110°, 45°, 100° 중 가장 큰 각도와 가장 작은 각도의 차를 구하세요.",
        expression="answer_text=85°",
        topic="geometry",
        rule_id="grade4_angle_round2_largest_smallest_difference",
    ),
    4: ElementaryVisualTemplate(
        problem_text="그림에서 ㉠과 ㉡의 각도의 합을 구하세요.",
        expression="answer_text=60°",
        topic="geometry",
        rule_id="grade4_angle_round2_sum_marked_triangle_angles",
    ),
    5: ElementaryVisualTemplate(
        problem_text="사각형에서 60°, 110°, 100°가 주어졌을 때 ㉠에 알맞은 수를 구하세요.",
        expression="answer_text=90°",
        topic="geometry",
        rule_id="grade4_angle_round2_quadrilateral_missing_angle",
    ),
    6: ElementaryVisualTemplate(
        problem_text="180°를 5등분한 그림에서 각 ㄴㅇㅁ의 크기를 구하세요.",
        expression="answer_text=108°",
        topic="geometry",
        rule_id="grade4_angle_round2_180_five_parts_angle",
    ),
    7: ElementaryVisualTemplate(
        problem_text="삼각형의 세 각의 크기가 될 수 없는 것을 고르세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade4_angle_round2_impossible_triangle_angles",
    ),
    8: ElementaryVisualTemplate(
        problem_text="사각형의 네 각의 크기를 바르게 잰 것에 ○표 하세요.",
        expression="answer_text=( ○ ) ( )",
        topic="geometry",
        rule_id="grade4_angle_round2_valid_quadrilateral_angle_sum",
    ),
    9: ElementaryVisualTemplate(
        problem_text="두 직각삼각자를 겹치지 않게 이어 붙여 만들 수 있는 각도 중 두 번째로 큰 각도를 구하세요.",
        expression="answer_text=150°",
        topic="geometry",
        rule_id="grade4_angle_round2_second_largest_set_square_angle",
    ),
}


_GRADE4_ANGLE_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="시계의 긴바늘과 짧은바늘이 이루는 작은 쪽의 각을 구하세요.",
        expression="answer_text=120°",
        topic="geometry",
        rule_id="grade4_angle_round2_clock_small_angle_120",
    ),
    2: ElementaryVisualTemplate(
        problem_text="두 시계의 긴바늘과 짧은바늘이 이루는 작은 쪽의 각의 차를 구하세요.",
        expression="answer_text=90°",
        topic="geometry",
        rule_id="grade4_angle_round2_clock_angle_difference_90",
    ),
    3: ElementaryVisualTemplate(
        problem_text="원 안의 105°와 125°가 주어진 그림에서 ㉠과 ㉡의 각도의 합을 구하세요.",
        expression="answer_text=130°",
        topic="geometry",
        rule_id="grade4_angle_round2_circle_marked_angle_sum",
    ),
}


_GRADE4_ANGLE_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="가장 큰 각에 ○표 하세요.",
        expression="answer_text=( ) ( ) ( ○ ) ( )",
        topic="geometry",
        rule_id="grade4_angle_round3_mark_largest_angle",
    ),
    2: ElementaryVisualTemplate(
        problem_text="각도에 대한 설명으로 옳지 않은 것을 고르세요.",
        expression="answer_text=②",
        topic="geometry",
        rule_id="grade4_angle_round3_incorrect_angle_description",
    ),
    3: ElementaryVisualTemplate(
        problem_text="시계의 시침과 분침이 이루는 작은 쪽의 각이 둔각인 것을 고르세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade4_angle_round3_clock_obtuse_choice",
    ),
    4: ElementaryVisualTemplate(
        problem_text="주어진 각도 130°를 각도기 위에 그리세요.",
        expression="answer_text=130°",
        topic="geometry",
        rule_id="grade4_angle_round3_draw_130_degree",
    ),
    5: ElementaryVisualTemplate(
        problem_text="각의 크기를 각도기로 재어 보세요.",
        expression="answer_text=40°",
        topic="geometry",
        rule_id="grade4_angle_round3_measure_angle_40",
    ),
    6: ElementaryVisualTemplate(
        problem_text="직각, 예각, 둔각을 각도가 큰 것부터 차례대로 쓰세요.",
        expression="answer_text=둔각, 직각, 예각",
        topic="geometry",
        rule_id="grade4_angle_round3_order_angle_types",
    ),
    7: ElementaryVisualTemplate(
        problem_text="각도 목록에서 예각은 모두 몇 개인지 구하세요.",
        expression="answer_text=5 개",
        topic="geometry",
        rule_id="grade4_angle_round3_count_acute_angles",
    ),
    8: ElementaryVisualTemplate(
        problem_text="185°+37°의 합을 구하세요.",
        expression="answer_text=222°",
        topic="geometry",
        rule_id="grade4_angle_round3_angle_sum_185_37",
    ),
}


_GRADE4_ANGLE_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="132°-75°의 차를 구하세요.",
        expression="answer_text=57°",
        topic="geometry",
        rule_id="grade4_angle_round3_angle_difference_132_75",
    ),
    2: ElementaryVisualTemplate(
        problem_text="75°+35°와 130°-25°의 계산 결과를 비교하세요.",
        expression="answer_text=>",
        topic="geometry",
        rule_id="grade4_angle_round3_compare_angle_calculations",
    ),
    3: ElementaryVisualTemplate(
        problem_text="270°-95°=90°+□에서 □ 안에 알맞은 수를 쓰세요.",
        expression="answer_text=85°",
        topic="geometry",
        rule_id="grade4_angle_round3_missing_addend_angle",
    ),
    4: ElementaryVisualTemplate(
        problem_text="삼각형에서 70°가 주어졌을 때 ㉠과 ㉡의 각도의 합을 구하세요.",
        expression="answer_text=110°",
        topic="geometry",
        rule_id="grade4_angle_round3_triangle_unknown_sum",
    ),
    5: ElementaryVisualTemplate(
        problem_text="사각형에서 직각 2개와 100°가 주어졌을 때 ㉠에 알맞은 수를 구하세요.",
        expression="answer_text=80°",
        topic="geometry",
        rule_id="grade4_angle_round3_quadrilateral_missing_angle",
    ),
    6: ElementaryVisualTemplate(
        problem_text="직각을 크기가 같은 각 5개로 나눈 그림에서 각 ㄴㅇㅁ의 크기를 구하세요.",
        expression="answer_text=54°",
        topic="geometry",
        rule_id="grade4_angle_round3_right_angle_five_parts_three_angle",
    ),
    7: ElementaryVisualTemplate(
        problem_text="삼각형의 세 각의 크기가 될 수 없는 것을 고르세요.",
        expression="answer_text=④",
        topic="geometry",
        rule_id="grade4_angle_round3_impossible_triangle_angles",
    ),
    8: ElementaryVisualTemplate(
        problem_text="□ 안에 알맞은 수를 쓰세요.",
        expression="answer_text=35",
        topic="geometry",
        rule_id="grade4_angle_round3_perpendicular_line_missing_angle",
    ),
    9: ElementaryVisualTemplate(
        problem_text="두 직각삼각자를 겹치지 않게 이어 붙여 만들 수 있는 각도 중 가장 작은 각도를 구하세요.",
        expression="answer_text=75°",
        topic="geometry",
        rule_id="grade4_angle_round3_smallest_set_square_angle",
    ),
}


_GRADE4_ANGLE_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="시계의 긴바늘과 짧은바늘이 이루는 작은 쪽의 각을 구하세요.",
        expression="answer_text=60°",
        topic="geometry",
        rule_id="grade4_angle_round3_clock_small_angle_60",
    ),
    2: ElementaryVisualTemplate(
        problem_text="두 시계의 긴바늘과 짧은바늘이 이루는 작은 쪽의 각의 차를 구하세요.",
        expression="answer_text=30°",
        topic="geometry",
        rule_id="grade4_angle_round3_clock_angle_difference_30",
    ),
    3: ElementaryVisualTemplate(
        problem_text="원 안의 105°와 125°가 주어진 그림에서 ㉠과 ㉡의 각도의 합을 구하세요.",
        expression="answer_text=132°",
        topic="geometry",
        rule_id="grade4_angle_round3_circle_marked_angle_sum",
    ),
}


_GRADE4_MULT_DIV_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="20×900, 30×500, 40×600, 60×500, 80×400 중 곱이 가장 작은 것을 고르세요.",
        expression="answer_text=②",
        rule_id="grade4_mult_div_round1_smallest_product_choice",
    ),
    2: ElementaryVisualTemplate(
        problem_text="500×80과 900×50 두 곱의 차를 구하세요.",
        expression="answer_text=5000",
        rule_id="grade4_mult_div_round1_difference_two_products",
    ),
    3: ElementaryVisualTemplate(
        problem_text="500원짜리 동전 40개를 1000원짜리 지폐 몇 장으로 바꿀 수 있는지 구하세요.",
        expression="answer_text=20 장",
        rule_id="grade4_mult_div_round1_coin_to_bills",
    ),
    4: ElementaryVisualTemplate(
        problem_text="470×50과 470×20의 차는 470에 얼마를 곱한 수와 같은지 구하세요.",
        expression="answer_text=30",
        rule_id="grade4_mult_div_round1_common_factor_difference",
    ),
    5: ElementaryVisualTemplate(
        problem_text="달걀 한 판은 30개입니다. 달걀 351판은 모두 몇 개인지 구하세요.",
        expression="answer_text=10530 개",
        rule_id="grade4_mult_div_round1_egg_trays",
    ),
    6: ElementaryVisualTemplate(
        problem_text="연필이 한 상자에 35타씩 들어 있고 6상자에 들어 있는 연필은 모두 몇 자루인지 구하세요. 연필 1타는 12자루입니다.",
        expression="answer_text=2520 자루",
        rule_id="grade4_mult_div_round1_pencil_boxes",
    ),
    7: ElementaryVisualTemplate(
        problem_text="하루에 725 km씩 달리는 버스가 30일 동안 달리면 모두 몇 km를 달리는지 구하세요.",
        expression="answer_text=21750 km",
        topic="measurement",
        rule_id="grade4_mult_div_round1_bus_distance",
    ),
    8: ElementaryVisualTemplate(
        problem_text="5, 0, 2, 3을 한 번씩 사용하여 만들 수 있는 가장 작은 세 자리 수와 가장 큰 두 자리 수의 곱을 구하세요.",
        expression="answer_text=10759",
        rule_id="grade4_mult_div_round1_digit_cards_product",
    ),
    9: ElementaryVisualTemplate(
        problem_text="길이 200 cm인 색 테이프 13개를 48 cm씩 겹쳐 한 줄로 이어 붙였을 때 전체 길이를 구하세요.",
        expression="answer_text=2024 cm",
        topic="measurement",
        rule_id="grade4_mult_div_round1_tape_total_length",
    ),
    10: ElementaryVisualTemplate(
        problem_text="668×□의 곱이 20000에 가장 가까운 수가 되도록 하는 두 자리 수를 구하세요.",
        expression="answer_text=30",
        rule_id="grade4_mult_div_round1_nearest_product_to_20000",
    ),
}


_GRADE4_MULT_DIV_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="180÷20, 210÷30, 300÷50, 320÷40, 350÷70 중 몫이 가장 큰 것을 고르세요.",
        expression="answer_text=①",
        rule_id="grade4_mult_div_round1_largest_quotient_choice",
    ),
    2: ElementaryVisualTemplate(
        problem_text="길이가 1 m 40 cm인 리본을 똑같이 20도막으로 자르면 한 도막의 길이는 몇 cm인지 구하세요.",
        expression="answer_text=7 cm",
        topic="measurement",
        rule_id="grade4_mult_div_round1_ribbon_piece_length",
    ),
    3: ElementaryVisualTemplate(
        problem_text="787÷80의 몫과 나머지를 구하세요.",
        expression="answer_text=몫 : 9, 나머지 : 67",
        rule_id="grade4_mult_div_round1_787_div_80",
    ),
    4: ElementaryVisualTemplate(
        problem_text="귤을 50명의 학생에게 7개씩 나누어 주었더니 10개가 남았습니다. 귤은 모두 몇 개인지 구하세요.",
        expression="answer_text=360 개",
        rule_id="grade4_mult_div_round1_oranges_total",
    ),
    5: ElementaryVisualTemplate(
        problem_text="16과 96에서 큰 수를 작은 수로 나누었을 때의 몫을 구하세요.",
        expression="answer_text=6",
        rule_id="grade4_mult_div_round1_divide_larger_by_smaller",
    ),
    6: ElementaryVisualTemplate(
        problem_text="78÷24, 84÷17, 76÷33을 계산하고 나머지가 큰 것부터 차례대로 기호를 쓰세요.",
        expression="answer_text=나, 다, 가",
        rule_id="grade4_mult_div_round1_order_by_remainder",
    ),
    7: ElementaryVisualTemplate(
        problem_text="구슬 84개를 한 봉지에 18개씩 나누어 담고 남은 것을 동생에게 주었습니다. 동생에게 준 구슬은 몇 개인지 구하세요.",
        expression="answer_text=12 개",
        rule_id="grade4_mult_div_round1_marble_remainder",
    ),
    8: ElementaryVisualTemplate(
        problem_text="어떤 수를 34로 나눌 때 나올 수 있는 나머지 중에서 가장 큰 수를 구하세요.",
        expression="answer_text=33",
        rule_id="grade4_mult_div_round1_largest_remainder_divisor_34",
    ),
    9: ElementaryVisualTemplate(
        problem_text="204÷25와 154÷17의 몫의 크기를 비교하세요.",
        expression="answer_text=<",
        rule_id="grade4_mult_div_round1_compare_quotients",
    ),
    10: ElementaryVisualTemplate(
        problem_text="길이 276 cm인 색 테이프를 한 도막이 32 cm가 되게 자르면 몇 개를 만들 수 있고 남는 길이는 몇 cm인지 구하세요.",
        expression="answer_text=8 개, 20 cm",
        topic="measurement",
        rule_id="grade4_mult_div_round1_tape_cutting",
    ),
}


_GRADE4_MULT_DIV_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="40×900과 계산 결과가 같은 것을 고르세요.",
        expression="answer_text=③",
        rule_id="grade4_mult_div_round2_same_product_choice",
    ),
    2: ElementaryVisualTemplate(
        problem_text="416×50을 바르게 계산하세요.",
        expression="answer_text=20800",
        rule_id="grade4_mult_div_round2_correct_416_times_50",
    ),
    3: ElementaryVisualTemplate(
        problem_text="500원짜리 동전 60개와 100원짜리 동전 90개를 1000원짜리 지폐로 바꿀 때 받은 지폐 수의 합을 구하세요.",
        expression="answer_text=39 장",
        rule_id="grade4_mult_div_round2_coin_bill_sum",
    ),
    4: ElementaryVisualTemplate(
        problem_text="360×70과 360×50의 차는 360에 얼마를 곱한 수와 같은지 구하세요.",
        expression="answer_text=20",
        rule_id="grade4_mult_div_round2_common_factor_difference",
    ),
    5: ElementaryVisualTemplate(
        problem_text="만 80세가 된 사람의 태어난 날부터 어제까지의 날짜를 1년 365일로 계산하세요.",
        expression="answer_text=29200 일",
        rule_id="grade4_mult_div_round2_age_days",
    ),
    6: ElementaryVisualTemplate(
        problem_text="한 상자에 27개씩 든 사과 210상자 중 3000개를 팔고 남은 사과는 몇 개인지 구하세요.",
        expression="answer_text=2670 개",
        rule_id="grade4_mult_div_round2_apples_remaining",
    ),
    7: ElementaryVisualTemplate(
        problem_text="한 시간에 700 m씩 가는 토끼가 60시간 동안 갈 수 있는 거리를 구하세요.",
        expression="answer_text=42000 m",
        topic="measurement",
        rule_id="grade4_mult_div_round2_rabbit_distance",
    ),
    8: ElementaryVisualTemplate(
        problem_text="3, 5, 1, 9, 4를 한 번씩 사용하여 가장 큰 세 자리 수와 가장 작은 두 자리 수의 곱을 구하세요.",
        expression="answer_text=12402",
        rule_id="grade4_mult_div_round2_digit_cards_product",
    ),
    9: ElementaryVisualTemplate(
        problem_text="길이 300 cm인 색 테이프 13개를 57 cm씩 겹쳐 이어 붙였을 때 전체 길이를 구하세요.",
        expression="answer_text=3216 cm",
        topic="measurement",
        rule_id="grade4_mult_div_round2_tape_total_length",
    ),
    10: ElementaryVisualTemplate(
        problem_text="275×□<3350이 되도록 □ 안에 들어갈 수 있는 가장 큰 자연수를 구하세요.",
        expression="answer_text=12",
        rule_id="grade4_mult_div_round2_largest_natural_275_product",
    ),
}


_GRADE4_MULT_DIV_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="320÷80, 480÷80, 810÷90, 640÷80, 560÷80 중 몫이 가장 작은 것을 고르세요.",
        expression="answer_text=①",
        rule_id="grade4_mult_div_round2_smallest_quotient_choice",
    ),
    2: ElementaryVisualTemplate(
        problem_text="길이가 90 cm인 색 테이프를 한 도막이 30 cm가 되도록 자르려면 몇 번 잘라야 하는지 구하세요.",
        expression="answer_text=2 번",
        topic="measurement",
        rule_id="grade4_mult_div_round2_tape_cuts",
    ),
    3: ElementaryVisualTemplate(
        problem_text="638÷70에서 계산이 잘못된 곳을 찾아 몫을 바르게 계산하세요.",
        expression="answer_text=9",
        rule_id="grade4_mult_div_round2_correct_wrong_division",
    ),
    4: ElementaryVisualTemplate(
        problem_text="길이 431 cm인 철사로 90 cm가 필요한 집 모양을 몇 개까지 만들 수 있고 몇 cm가 남는지 구하세요.",
        expression="answer_text=4 개, 71 cm",
        topic="measurement",
        rule_id="grade4_mult_div_round2_wire_house_shapes",
    ),
    5: ElementaryVisualTemplate(
        problem_text="75, 17, 85, 68 중 가장 큰 수를 가장 작은 수로 나눈 몫을 구하세요.",
        expression="answer_text=5",
        rule_id="grade4_mult_div_round2_largest_divided_by_smallest",
    ),
    6: ElementaryVisualTemplate(
        problem_text="□÷17의 나머지가 될 수 있는 수를 모두 고르세요.",
        expression="answer_text=①, ②",
        rule_id="grade4_mult_div_round2_possible_remainders",
    ),
    7: ElementaryVisualTemplate(
        problem_text="초콜릿 82개를 한 봉지에 13개씩 담으면 모두 담기 위해 적어도 몇 봉지가 필요한지 구하세요.",
        expression="answer_text=7 봉지",
        rule_id="grade4_mult_div_round2_chocolate_bags",
    ),
    8: ElementaryVisualTemplate(
        problem_text="어떤 자연수를 11로 나누었을 때 나올 수 있는 나머지의 합을 구하세요.",
        expression="answer_text=55",
        rule_id="grade4_mult_div_round2_sum_possible_remainders_11",
    ),
    9: ElementaryVisualTemplate(
        problem_text="378÷57의 몫과 나머지를 구하세요.",
        expression="answer_text=몫 : 6, 나머지 : 36",
        rule_id="grade4_mult_div_round2_378_div_57",
    ),
    10: ElementaryVisualTemplate(
        problem_text="찹쌀떡 226개를 한 상자에 23개씩 담으면 모두 몇 상자가 되고 몇 개가 남는지 구하세요.",
        expression="answer_text=9 상자, 19 개",
        rule_id="grade4_mult_div_round2_rice_cake_boxes",
    ),
}


_GRADE4_MULT_DIV_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="60×300, 70×200, 300×90, 400×70, 80×500 중 계산 결과가 가장 큰 것을 고르세요.",
        expression="answer_text=⑤",
        rule_id="grade4_mult_div_round3_largest_product_choice",
    ),
    2: ElementaryVisualTemplate(
        problem_text="183×□0의 세로셈에서 ㉠, ㉡, ㉢에 알맞은 수를 구하세요.",
        expression="answer_text=㉠ 5, ㉡ 9, ㉢ 1",
        rule_id="grade4_mult_div_round3_vertical_multiplication_blanks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="종혁이는 하루에 우유를 200 mL씩 마십니다. 종혁이가 40일 동안 마신 우유는 모두 몇 mL인지 구하세요.",
        expression="answer_text=8000 mL",
        topic="measurement",
        rule_id="grade4_mult_div_round3_milk_40_days",
    ),
    4: ElementaryVisualTemplate(
        problem_text="530×80과 530×50의 차는 530에 얼마를 곱한 수와 같은지 구하세요.",
        expression="answer_text=30",
        rule_id="grade4_mult_div_round3_common_factor_difference",
    ),
    5: ElementaryVisualTemplate(
        problem_text="사과를 한 상자에 127개씩 담았습니다. 50상자에 담은 사과의 수를 구하세요.",
        expression="answer_text=6350 개",
        rule_id="grade4_mult_div_round3_apples_50_boxes",
    ),
    6: ElementaryVisualTemplate(
        problem_text="일주일에 5일 동안 일하는 공장에서 8명이 일을 하고 있습니다. 한 사람이 하루에 25개의 물건을 만든다면 5주 동안에는 모두 몇 개의 물건을 만들겠습니까?",
        expression="answer_text=5000 개",
        rule_id="grade4_mult_div_round3_factory_items",
    ),
    7: ElementaryVisualTemplate(
        problem_text="어떤 수에 50을 곱하였더니 45000이 되었습니다. 어떤 수는 얼마입니까?",
        expression="answer_text=900",
        rule_id="grade4_mult_div_round3_unknown_times_50",
    ),
    8: ElementaryVisualTemplate(
        problem_text="2, 4, 6, 3, 8을 한 번씩만 사용하여 만들 수 있는 가장 큰 세 자리 수와 가장 작은 두 자리 수의 곱을 구하세요.",
        expression="answer_text=19872",
        rule_id="grade4_mult_div_round3_digit_cards_product",
    ),
    9: ElementaryVisualTemplate(
        problem_text="길이가 142 cm인 색 테이프 14개를 23 cm씩 겹쳐서 한 줄로 길게 이어 붙였습니다. 이어 붙인 색 테이프의 전체 길이는 몇 cm입니까?",
        expression="answer_text=1689 cm",
        topic="measurement",
        rule_id="grade4_mult_div_round3_tape_total_length",
    ),
    10: ElementaryVisualTemplate(
        problem_text="자연수 중에서 350×□>3600의 □ 안에 들어갈 수 있는 가장 작은 수를 구하세요.",
        expression="answer_text=11",
        rule_id="grade4_mult_div_round3_smallest_natural_350_product",
    ),
}


_GRADE4_MULT_DIV_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="280÷70, 180÷20, 420÷60, 320÷40의 몫이 작은 것부터 차례로 기호를 쓰세요.",
        expression="answer_text=가, 다, 라, 나",
        rule_id="grade4_mult_div_round3_order_quotients",
    ),
    2: ElementaryVisualTemplate(
        problem_text="사과가 350개 있습니다. 이 사과를 한 상자에 50개씩 넣으려면 상자는 모두 몇 개 필요합니까?",
        expression="answer_text=7 개",
        rule_id="grade4_mult_div_round3_apple_boxes",
    ),
    3: ElementaryVisualTemplate(
        problem_text="30과 274 중 큰 수를 작은 수로 나누었을 때의 몫과 나머지를 각각 구하세요.",
        expression="answer_text=몫 : 9, 나머지 : 4",
        rule_id="grade4_mult_div_round3_274_div_30",
    ),
    4: ElementaryVisualTemplate(
        problem_text="연필 260자루를 40명의 학생에게 똑같이 나누어 주려고 하였더니 몇 자루가 모자랐습니다. 남는 연필이 없이 똑같이 나누어 주려면 적어도 몇 자루의 연필이 더 필요한지 구하세요.",
        expression="answer_text=20 자루",
        rule_id="grade4_mult_div_round3_pencils_needed",
    ),
    5: ElementaryVisualTemplate(
        problem_text="70÷14, 76÷19, 92÷46, 84÷28 중 몫이 가장 큰 것을 찾아 기호를 쓰세요.",
        expression="answer_text=가",
        rule_id="grade4_mult_div_round3_largest_quotient_symbol",
    ),
    6: ElementaryVisualTemplate(
        problem_text="15×□<84의 □ 안에 들어갈 수 있는 자연수 중에서 가장 큰 수를 구하세요.",
        expression="answer_text=5",
        rule_id="grade4_mult_div_round3_largest_natural_15_product",
    ),
    7: ElementaryVisualTemplate(
        problem_text="축구는 11명이 한 팀입니다. 95명의 선수를 똑같이 나누어 축구팀을 만들려고 합니다. 남는 선수가 없도록 팀을 만들려면 몇 명이 더 있어야 합니까?",
        expression="answer_text=4 명",
        rule_id="grade4_mult_div_round3_soccer_players_needed",
    ),
    8: ElementaryVisualTemplate(
        problem_text="어떤 수를 77로 나누었을 때 나올 수 있는 나머지 중에서 가장 큰 수를 11로 나누었습니다. 이때 나머지는 얼마입니까?",
        expression="answer_text=10",
        rule_id="grade4_mult_div_round3_largest_remainder_then_divide",
    ),
    9: ElementaryVisualTemplate(
        problem_text="291÷39=㉠…18, 263÷46=5…㉡일 때 ㉠과 ㉡에 알맞은 수의 합을 구하세요.",
        expression="answer_text=40",
        rule_id="grade4_mult_div_round3_sum_quotient_remainder_blanks",
    ),
    10: ElementaryVisualTemplate(
        problem_text="어떤 수를 16으로 나누었더니 몫이 7이고 나머지는 14보다 크다고 합니다. 어떤 수를 구하세요.",
        expression="answer_text=127",
        rule_id="grade4_mult_div_round3_unknown_division",
    ),
}


_GRADE4_BAR_GRAPH_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="연우네 반 학생들이 좋아하는 과일을 조사한 결과를 표로 정리하세요.",
        expression="answer_text=사과 5 명, 배 4 명, 포도 2 명, 감 4 명, 합계 15 명",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_fruit_table_counts",
    ),
    2: ElementaryVisualTemplate(
        problem_text="표를 보고 좋아하는 과일별 학생 수를 막대그래프로 나타내세요.",
        expression="answer_text=사과 5 명, 배 4 명, 포도 2 명, 감 4 명 막대그래프",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_fruit_bar_graph",
    ),
    3: ElementaryVisualTemplate(
        problem_text="경아네 반 학생들이 좋아하는 계절 막대그래프에서 세로 눈금 한 칸은 몇 명을 나타내는지 구하세요.",
        expression="answer_text=2 명",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_season_graph_scale",
    ),
    4: ElementaryVisualTemplate(
        problem_text="과수원별 사과 수확량 막대그래프를 보고 표로 나타내세요.",
        expression="answer_text=가 140 상자, 나 100 상자, 다 220 상자, 라 200 상자, 합계 660 상자",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_orchard_table_from_graph",
    ),
    5: ElementaryVisualTemplate(
        problem_text="초등학교별 수학 경시 대회 참가 학생 수 막대그래프에서 힘찬 초등학교 학생 수를 구하세요.",
        expression="answer_text=16 명",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_math_contest_himchan_count",
    ),
}


_GRADE4_BAR_GRAPH_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="스마트폰을 가장 길게 사용한 사람은 가장 짧게 사용한 사람보다 몇 분 더 사용했는지 구하세요.",
        expression="answer_text=60 분",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_smartphone_time_difference",
    ),
    2: ElementaryVisualTemplate(
        problem_text="세로 눈금 한 칸이 5분을 나타내는 막대그래프로 바꾸어 그릴 때 서우의 스마트폰 사용 시간은 몇 칸으로 그려야 하는지 구하세요.",
        expression="answer_text=16 칸",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_convert_seowoo_time_to_grid",
    ),
    3: ElementaryVisualTemplate(
        problem_text="막대그래프에 대한 설명으로 틀린 것을 고르세요.",
        expression="answer_text=④",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_wrong_description_choice",
    ),
    4: ElementaryVisualTemplate(
        problem_text="월별 비 온 날수를 나타낸 표와 막대그래프에서 막대그래프가 표보다 편리한 점을 고르세요.",
        expression="answer_text=나",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_graph_advantage_choice",
    ),
    5: ElementaryVisualTemplate(
        problem_text="대륙별 참가 선수 수가 같도록 선수를 더 선발할 때 가장 많은 선수를 선발해야 하는 대륙을 고르세요.",
        expression="answer_text=오세아니아",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_continent_most_extra_needed",
    ),
}


_GRADE4_BAR_GRAPH_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="크림빵과 소보로빵의 개수가 같아지려면 어느 빵을 몇 개 더 만들어야 하는지 구하세요.",
        expression="answer_text=크림빵, 16 개",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_bread_equalize",
    ),
    2: ElementaryVisualTemplate(
        problem_text="월별 비 온 날수를 나타낸 막대그래프에서 7월에 비가 오지 않은 날은 며칠인지 구하세요.",
        expression="answer_text=13 일",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_no_rain_days_july",
    ),
    3: ElementaryVisualTemplate(
        problem_text="월별 기온과 물 사용량 막대그래프를 보고 기온과 한 가구당 물 사용량의 관계를 고르세요.",
        expression="answer_text=①",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_temperature_water_relation",
    ),
    4: ElementaryVisualTemplate(
        problem_text="동물별 학생 수 표를 막대그래프로 나타낼 때 하마의 막대가 5칸이면 돌고래는 몇 칸으로 그려야 하는지 구하세요.",
        expression="answer_text=6 칸",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_dolphin_bar_height",
    ),
    5: ElementaryVisualTemplate(
        problem_text="충치 수별 학생 수 막대그래프에서 충치가 3개인 학생 수는 막대그래프에 몇 칸으로 나타내야 하는지 구하세요.",
        expression="answer_text=7 칸",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_three_cavities_bar_height",
    ),
    6: ElementaryVisualTemplate(
        problem_text="막대그래프로 나타내는 순서에 맞게 기호를 쓰세요.",
        expression="answer_text=다, 나, 가, 라",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_bar_graph_steps",
    ),
}


_GRADE4_BAR_GRAPH_ROUND1_PAGE4: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="바나나 맛 우유를 좋아하는 학생은 초콜릿 맛 우유를 좋아하는 학생보다 6명 더 많고 전체가 28명일 때 표의 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=4, 10",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_milk_flavor_table_blanks",
    ),
    2: ElementaryVisualTemplate(
        problem_text="반별 달리기 대회 참가 학생 수 막대그래프를 보고 참가 학생 모두에게 공책을 2권씩 나누어 주려면 공책을 몇 권 준비해야 하는지 구하세요.",
        expression="answer_text=92 권",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_running_notebooks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="태어난 계절별 학생 수 막대그래프에서 봄에 태어난 학생 수가 겨울보다 5명 더 많을 때 전체 학생 수를 구하세요.",
        expression="answer_text=26 명",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_birth_season_total",
    ),
    4: ElementaryVisualTemplate(
        problem_text="연도별 전입과 전출 인구 막대그래프에서 알 수 있는 사실을 찾아 기호를 쓰세요.",
        expression="answer_text=다",
        topic="statistics",
        rule_id="grade4_bar_graph_round1_population_fact_choice",
    ),
}


_GRADE4_BAR_GRAPH_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="3월부터 6월까지 비가 온 날은 모두 며칠인지 구하세요.",
        expression="answer_text=32 일",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_total_rain_days",
    ),
    2: ElementaryVisualTemplate(
        problem_text="6월은 30일까지 있습니다. 6월 중 비가 오지 않은 날은 며칠인지 구하세요.",
        expression="answer_text=18 일",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_june_no_rain_days",
    ),
    3: ElementaryVisualTemplate(
        problem_text="표를 보고 막대그래프로 나타낼 때 알맞은 제목을 쓰세요.",
        expression="answer_text=월별 비가 온 날수",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_graph_title",
    ),
    4: ElementaryVisualTemplate(
        problem_text="3월부터 6월 중에서 비가 온 날수가 많은 월부터 차례대로 쓰세요.",
        expression="answer_text=6 월, 4 월, 5 월, 3 월",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_order_rain_months",
    ),
    5: ElementaryVisualTemplate(
        problem_text="민기의 시험 성적 막대그래프에서 세로 눈금 한 칸은 몇 점을 나타내는지 구하세요.",
        expression="answer_text=10 점",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_score_graph_scale",
    ),
    6: ElementaryVisualTemplate(
        problem_text="계절별 결석생 수 막대그래프를 보고 표로 나타내세요.",
        expression="answer_text=봄 24 명, 여름 16 명, 가을 28 명, 겨울 34 명, 합계 102 명",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_absence_table",
    ),
}


_GRADE4_BAR_GRAPH_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="연도별 1인당 쌀 소비량 막대그래프에서 2000년의 1인당 쌀 소비량을 구하세요.",
        expression="answer_text=90 kg",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_rice_2000",
    ),
    2: ElementaryVisualTemplate(
        problem_text="수학 공부를 한 시간 막대그래프에 대한 설명으로 틀린 것을 고르세요.",
        expression="answer_text=③",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_wrong_statement",
    ),
    3: ElementaryVisualTemplate(
        problem_text="일주일 동안 민규네 집에서 버려진 쓰레기의 양은 정호네 집에서 버려진 쓰레기의 양의 몇 배인지 구하세요.",
        expression="answer_text=2 배",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_trash_ratio",
    ),
    4: ElementaryVisualTemplate(
        problem_text="가축을 더 사 와서 종류별 가축의 수가 같도록 하려면 가장 많이 사 와야 하는 가축을 구하세요.",
        expression="answer_text=닭",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_livestock_most_to_buy",
    ),
}


_GRADE4_BAR_GRAPH_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="11월의 날씨에 따른 날수 막대그래프에서 흐린 날과 눈 온 날의 차를 구하세요.",
        expression="answer_text=1 일",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_weather_difference",
    ),
    2: ElementaryVisualTemplate(
        problem_text="사무실별 컴퓨터 수 막대그래프에서 세로 눈금 한 칸이 4대를 나타낼 때 컴퓨터가 가장 많은 사무실의 컴퓨터 수를 구하세요.",
        expression="answer_text=28 대",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_office_computer_most",
    ),
    3: ElementaryVisualTemplate(
        problem_text="기온과 아이스크림 판매량 막대그래프를 보고 관계를 고르세요.",
        expression="answer_text=①",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_temperature_icecream_relation",
    ),
    4: ElementaryVisualTemplate(
        problem_text="색깔별 학생 수 표를 막대그래프로 나타낼 때 빨간색 막대는 세로 눈금 몇 칸으로 그려야 하는지 구하세요.",
        expression="answer_text=3 칸",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_red_bar_height",
    ),
    5: ElementaryVisualTemplate(
        problem_text="과수원별 사과나무 수 막대그래프에서 B 과수원의 사과나무 수는 몇 칸으로 나타내어야 하는지 구하세요.",
        expression="answer_text=3 칸",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_orchard_b_bar_height",
    ),
}


_GRADE4_BAR_GRAPH_ROUND2_PAGE4: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="막대그래프를 나타내는 순서에 맞게 기호를 쓰세요.",
        expression="answer_text=다, 라, 가, 나",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_bar_graph_steps",
    ),
    2: ElementaryVisualTemplate(
        problem_text="좋아하는 운동별 학생 수 표에서 야구와 탁구를 좋아하는 학생 수를 각각 구하세요.",
        expression="answer_text=야구 7 명, 탁구 6 명",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_sports_table_blanks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="과목별 시험 성적 막대그래프에서 70점보다 더 얻은 점수만큼 받는 칭찬 붙임 딱지는 모두 몇 장인지 구하세요.",
        expression="answer_text=30 장",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_praise_stickers",
    ),
    4: ElementaryVisualTemplate(
        problem_text="현장체험학습 장소별 학생 수 막대그래프에서 역사박물관이 과학관보다 4명 더 많을 때 전체 학생 수를 구하세요.",
        expression="answer_text=23 명",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_field_trip_total",
    ),
    5: ElementaryVisualTemplate(
        problem_text="올림픽 개최지별 우리나라가 획득한 메달 수 막대그래프에서 가장 많은 금메달을 획득한 개최지를 구하세요.",
        expression="answer_text=29회 베이징",
        topic="statistics",
        rule_id="grade4_bar_graph_round2_olympic_most_gold",
    ),
}


_GRADE4_BAR_GRAPH_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="방과 후 활동별 학생 수 표에서 그림 그리기를 하는 학생은 몇 명인지 구하세요.",
        expression="answer_text=11 명",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_art_activity_count",
    ),
    2: ElementaryVisualTemplate(
        problem_text="방과 후 활동별 학생 수 표를 보고 막대그래프로 나타내세요.",
        expression="answer_text=방과 후 활동별 학생 수",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_draw_activity_bar_graph",
    ),
    3: ElementaryVisualTemplate(
        problem_text="학생 수가 많은 방과 후 활동부터 차례대로 쓰세요.",
        expression="answer_text=그림 그리기, 바둑, 수영, 종이접기",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_order_activities",
    ),
    4: ElementaryVisualTemplate(
        problem_text="학생 수가 많은 방과 후 활동부터 차례대로 알아볼 때 한눈에 쉽게 알아볼 수 있는 것은 표와 막대그래프 중 어느 것인지 쓰세요.",
        expression="answer_text=막대그래프",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_table_or_bar_graph",
    ),
    5: ElementaryVisualTemplate(
        problem_text="학생들이 책을 읽은 시간 막대그래프에서 가로 눈금 한 칸은 몇 분을 나타내는지 구하세요.",
        expression="answer_text=20 분",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_reading_time_scale",
    ),
    6: ElementaryVisualTemplate(
        problem_text="안경 쓴 학생 수 막대그래프를 보고 표로 나타내세요.",
        expression="answer_text=3학년 30 명, 4학년 40 명, 5학년 45 명, 6학년 60 명, 합계 175 명",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_glasses_table",
    ),
}


_GRADE4_BAR_GRAPH_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="좋아하는 과목별 학생 수 막대그래프에서 32명보다 많은 학생들이 좋아하는 과목을 모두 고르세요.",
        expression="answer_text=②, ③",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_subjects_more_than_32",
    ),
    2: ElementaryVisualTemplate(
        problem_text="혈액형별 학생 수 막대그래프에 대한 설명으로 틀린 것을 고르세요.",
        expression="answer_text=③",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_blood_type_wrong_statement",
    ),
    3: ElementaryVisualTemplate(
        problem_text="전통 놀이별 학생 수 막대그래프를 보고 표로 나타내세요.",
        expression="answer_text=윷놀이 9 명, 팽이치기 7 명, 제기차기 4 명, 연날리기 4 명, 합계 24 명",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_traditional_game_table",
    ),
    4: ElementaryVisualTemplate(
        problem_text="반별 수학경시 대회 참가 학생 수 막대그래프에서 참가 학생 수가 같도록 하려면 가장 많이 선발해야 하는 반을 구하세요.",
        expression="answer_text=2반",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_math_contest_class",
    ),
}


_GRADE4_BAR_GRAPH_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="숙제를 한 시간 막대그래프에서 가장 오래 숙제한 사람은 가장 짧게 숙제한 사람보다 몇 분 더 많이 했는지 구하세요.",
        expression="answer_text=50 분",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_homework_time_difference",
    ),
    2: ElementaryVisualTemplate(
        problem_text="지역별 자동차 수 막대그래프에서 가로 눈금 한 칸이 100대를 나타낼 때 자동차가 가장 많은 지역의 자동차 수를 구하세요.",
        expression="answer_text=1100 대",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_cars_most_region",
    ),
    3: ElementaryVisualTemplate(
        problem_text="기온과 전기 사용량 막대그래프를 보고 관계를 고르세요.",
        expression="answer_text=①",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_temperature_electricity_relation",
    ),
    4: ElementaryVisualTemplate(
        problem_text="표를 보고 막대그래프를 그릴 때 학생 수를 나타내는 세로 눈금 한 칸이 1명을 나타낸다면 세로 눈금은 적어도 몇 칸 있어야 하는지 구하세요.",
        expression="answer_text=26 칸",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_min_vertical_ticks",
    ),
    5: ElementaryVisualTemplate(
        problem_text="좋아하는 과목별 학생 수 막대그래프에서 수학을 좋아하는 학생 수는 몇 칸으로 나타내야 하는지 구하세요.",
        expression="answer_text=5 칸",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_math_bar_height",
    ),
    6: ElementaryVisualTemplate(
        problem_text="막대그래프를 나타내는 순서에 맞게 기호를 쓰세요.",
        expression="answer_text=다, 가, 나, 라",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_bar_graph_steps",
    ),
}


_GRADE4_BAR_GRAPH_ROUND3_PAGE4: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="좋아하는 운동별 학생 수 표에서 야구와 탁구를 좋아하는 학생 수를 각각 구하세요.",
        expression="answer_text=야구 7 명, 탁구 6 명",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_sports_table_blanks",
    ),
    2: ElementaryVisualTemplate(
        problem_text="과목별 시험 성적 막대그래프에서 70점보다 더 얻은 점수만큼 받는 칭찬 붙임 딱지는 모두 몇 장인지 구하세요.",
        expression="answer_text=30 장",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_praise_stickers",
    ),
    3: ElementaryVisualTemplate(
        problem_text="현장체험학습 장소별 학생 수 막대그래프에서 역사박물관이 과학관보다 4명 더 많을 때 전체 학생 수를 구하세요.",
        expression="answer_text=23 명",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_field_trip_total",
    ),
    4: ElementaryVisualTemplate(
        problem_text="올림픽 개최지별 우리나라가 획득한 메달 수 막대그래프에서 가장 많은 금메달을 획득한 개최지를 구하세요.",
        expression="answer_text=29회 베이징",
        topic="statistics",
        rule_id="grade4_bar_graph_round3_olympic_most_gold",
    ),
}


_GRADE4_RULES_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="규칙적인 수의 배열에서 ●, ▲에 알맞은 수를 각각 구하세요.",
        expression="answer_text=● 2038, ▲ 2058",
        topic="pattern",
        rule_id="grade4_rules_round1_number_sequence_symbols",
    ),
    2: ElementaryVisualTemplate(
        problem_text="수 배열표에서 분홍색으로 색칠된 칸에 나타난 규칙을 설명할 때 알맞은 수를 고르세요.",
        expression="answer_text=⑤",
        topic="pattern",
        rule_id="grade4_rules_round1_table_diagonal_rule",
    ),
    3: ElementaryVisualTemplate(
        problem_text="규칙에 따라 수를 배열했습니다. 다음에 올 수를 구하세요.",
        expression="answer_text=47",
        topic="pattern",
        rule_id="grade4_rules_round1_next_number",
    ),
    4: ElementaryVisualTemplate(
        problem_text="규칙을 찾아 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=486",
        topic="pattern",
        rule_id="grade4_rules_round1_divide_by_three",
    ),
    5: ElementaryVisualTemplate(
        problem_text="수 배열표의 일부가 찢어졌습니다. 규칙에 따라 빈칸에 알맞은 수를 구하세요.",
        expression="answer_text=4412",
        topic="pattern",
        rule_id="grade4_rules_round1_torn_table_number",
    ),
    6: ElementaryVisualTemplate(
        problem_text="수 배열표를 보고 ㄱ, ㄴ, ㄷ에 알맞은 수를 각각 구하세요.",
        expression="answer_text=ㄱ 12, ㄴ 80, ㄷ 18",
        topic="pattern",
        rule_id="grade4_rules_round1_double_table_blanks",
    ),
    7: ElementaryVisualTemplate(
        problem_text="수 배열표를 보고 규칙적인 수의 배열에서 색칠된 칸에 알맞은 수를 구하세요.",
        expression="answer_text=■ 0, ● 9",
        topic="pattern",
        rule_id="grade4_rules_round1_addition_table_blanks",
    ),
}


_GRADE4_RULES_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="도형의 배열을 보고 여섯 번째에 올 도형에서 사각형의 개수를 구하세요.",
        expression="answer_text=11 개",
        topic="pattern",
        rule_id="grade4_rules_round1_sixth_shape_square_count",
    ),
    2: ElementaryVisualTemplate(
        problem_text="규칙에 따라 도형을 배열했습니다. 다음에 올 모양의 색과 도형을 구하세요.",
        expression="answer_text=초록색, 사각형",
        topic="pattern",
        rule_id="grade4_rules_round1_next_color_shape",
    ),
    3: ElementaryVisualTemplate(
        problem_text="도형의 배열을 보고 다섯째에 올 모양에서 사각형의 수를 구하세요.",
        expression="answer_text=15 개",
        topic="pattern",
        rule_id="grade4_rules_round1_fifth_triangular_squares",
    ),
    4: ElementaryVisualTemplate(
        problem_text="덧셈식의 규칙에 따라 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=325, 767",
        topic="pattern",
        rule_id="grade4_rules_round1_addition_pattern_blanks",
    ),
    5: ElementaryVisualTemplate(
        problem_text="규칙에 따라 바둑돌을 늘어놓았습니다. 40째에 놓이는 바둑돌은 무슨 색인지 고르세요.",
        expression="answer_text=①",
        topic="pattern",
        rule_id="grade4_rules_round1_go_stone_40th",
    ),
    6: ElementaryVisualTemplate(
        problem_text="도형의 배열을 보고 빨간색 사각형이 100개인 모양은 몇째인지 고르세요.",
        expression="answer_text=③",
        topic="pattern",
        rule_id="grade4_rules_round1_red_squares_100",
    ),
    7: ElementaryVisualTemplate(
        problem_text="수 배열표를 보고 빈칸에 알맞은 식을 써넣으세요.",
        expression="answer_text=550 + 460 = 560 + 450",
        topic="pattern",
        rule_id="grade4_rules_round1_number_table_equation",
    ),
}


_GRADE4_RULES_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="계산식을 보고 설명에 맞는 계산식을 찾아 기호를 쓰세요.",
        expression="answer_text=라",
        topic="pattern",
        rule_id="grade4_rules_round1_matching_equation_rule",
    ),
    2: ElementaryVisualTemplate(
        problem_text="도형의 배열에서 조건에 맞는 모양을 고르세요.",
        expression="answer_text=⑤",
        topic="pattern",
        rule_id="grade4_rules_round1_shape_order_choice",
    ),
    3: ElementaryVisualTemplate(
        problem_text="수의 규칙을 찾아 빈칸에 알맞은 두 수를 쓰세요.",
        expression="answer_text=9000002, 999999",
        topic="pattern",
        rule_id="grade4_rules_round1_large_number_blanks",
    ),
    4: ElementaryVisualTemplate(
        problem_text="규칙에 따라 배열된 보기 중 알맞은 것을 고르세요.",
        expression="answer_text=나",
        topic="pattern",
        rule_id="grade4_rules_round1_rule_choice",
    ),
    5: ElementaryVisualTemplate(
        problem_text="연속한 세 수의 합이 가운데 수의 몇 배인지 보고 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=3, 3, 3, 214",
        topic="pattern",
        rule_id="grade4_rules_round1_three_consecutive_numbers",
    ),
    6: ElementaryVisualTemplate(
        problem_text="달력에서 같은 모양 안의 9개 수의 합을 보고 가운데 수를 구하세요.",
        expression="answer_text=18",
        topic="pattern",
        rule_id="grade4_rules_round1_calendar_center_number",
    ),
}


_GRADE4_RULES_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="규칙적인 수의 배열에서 ■, ●에 알맞은 수를 각각 구하세요.",
        expression="answer_text=■ 3307, ● 5307",
        topic="pattern",
        rule_id="grade4_rules_round2_number_sequence_symbols",
    ),
    2: ElementaryVisualTemplate(
        problem_text="수 배열표에서 연두색으로 색칠된 칸의 규칙을 찾아 알맞은 수를 구하세요.",
        expression="answer_text=900",
        topic="pattern",
        rule_id="grade4_rules_round2_colored_table_rule",
    ),
    3: ElementaryVisualTemplate(
        problem_text="분수의 규칙을 찾아 빈칸에 알맞은 분수를 써넣으세요.",
        expression="answer_text=11/15, 20/27",
        topic="pattern",
        rule_id="grade4_rules_round2_fraction_sequence",
    ),
    4: ElementaryVisualTemplate(
        problem_text="수 배열의 규칙에 맞게 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=324",
        topic="pattern",
        rule_id="grade4_rules_round2_multiply_by_three",
    ),
    5: ElementaryVisualTemplate(
        problem_text="수 배열표를 보고 수 배열의 규칙에 맞게 색칠된 칸에 알맞은 수를 구하세요.",
        expression="answer_text=42094",
        topic="pattern",
        rule_id="grade4_rules_round2_torn_table_number",
    ),
    6: ElementaryVisualTemplate(
        problem_text="수 배열표를 보고 ㄱ, ㄴ, ㄷ에 알맞은 수를 각각 구하세요.",
        expression="answer_text=ㄱ 27, ㄴ 108, ㄷ 405",
        topic="pattern",
        rule_id="grade4_rules_round2_multiplication_table_blanks",
    ),
    7: ElementaryVisualTemplate(
        problem_text="수 배열표를 보고 규칙적인 수의 배열에서 색칠된 칸에 알맞은 수를 구하세요.",
        expression="answer_text=■ 8, ● 9",
        topic="pattern",
        rule_id="grade4_rules_round2_addition_table_blanks",
    ),
}


_GRADE4_RULES_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="도형의 배열을 보고 다섯 번째에 올 도형에서 사각형의 개수를 구하세요.",
        expression="answer_text=13 개",
        topic="pattern",
        rule_id="grade4_rules_round2_fifth_shape_square_count",
    ),
    2: ElementaryVisualTemplate(
        problem_text="규칙에 따라 도형을 배열했습니다. 다음에 올 모양의 색과 도형을 구하세요.",
        expression="answer_text=보라색, 삼각형",
        topic="pattern",
        rule_id="grade4_rules_round2_next_color_shape",
    ),
    3: ElementaryVisualTemplate(
        problem_text="도형의 배열을 보고 다섯째에 알맞은 모양에서 도형의 개수를 구하세요.",
        expression="answer_text=10 개",
        topic="pattern",
        rule_id="grade4_rules_round2_fifth_l_shape_count",
    ),
    4: ElementaryVisualTemplate(
        problem_text="분홍색 도형이 48개인 모양은 몇째에 알맞은 모양인지 고르세요.",
        expression="answer_text=③",
        topic="pattern",
        rule_id="grade4_rules_round2_pink_shape_48",
    ),
    5: ElementaryVisualTemplate(
        problem_text="규칙에 따라 바둑돌을 늘어놓았습니다. 65째에 놓이는 바둑돌의 색을 고르세요.",
        expression="answer_text=②",
        topic="pattern",
        rule_id="grade4_rules_round2_go_stone_65th",
    ),
    6: ElementaryVisualTemplate(
        problem_text="덧셈식의 규칙에 따라 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=350, 1150",
        topic="pattern",
        rule_id="grade4_rules_round2_addition_pattern_blanks",
    ),
    7: ElementaryVisualTemplate(
        problem_text="계산식을 보고 설명에 맞는 계산식을 찾아 기호를 쓰세요.",
        expression="answer_text=다",
        topic="pattern",
        rule_id="grade4_rules_round2_matching_equation_rule",
    ),
}


_GRADE4_RULES_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="규칙적인 계산식을 보고 여섯째에 알맞은 계산식을 구하세요.",
        expression="answer_text=350 + 220 - 100 = 470",
        topic="pattern",
        rule_id="grade4_rules_round2_sixth_calculation",
    ),
    2: ElementaryVisualTemplate(
        problem_text="덧셈식에서 규칙을 찾아 다섯째에 알맞은 덧셈식을 쓰세요.",
        expression="answer_text=12 + 15 + 18 = 45",
        topic="pattern",
        rule_id="grade4_rules_round2_fifth_addition_sequence",
    ),
    3: ElementaryVisualTemplate(
        problem_text="덧셈식의 규칙을 잘못 설명한 것을 찾아 기호를 쓰세요.",
        expression="answer_text=다",
        topic="pattern",
        rule_id="grade4_rules_round2_wrong_rule_explanation",
    ),
    4: ElementaryVisualTemplate(
        problem_text="덧셈식의 규칙에 따라 값이 11111111이 되는 덧셈식을 구하세요.",
        expression="answer_text=1111112, 9999999",
        topic="pattern",
        rule_id="grade4_rules_round2_large_addition_blanks",
    ),
    5: ElementaryVisualTemplate(
        problem_text="연속한 세 수의 합이 가운데 수의 몇 배인지 보고 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=3, 3, 3, 329",
        topic="pattern",
        rule_id="grade4_rules_round2_three_consecutive_numbers",
    ),
    6: ElementaryVisualTemplate(
        problem_text="달력에서 같은 모양 안의 9개 수의 합을 보고 가운데 수를 구하세요.",
        expression="answer_text=17",
        topic="pattern",
        rule_id="grade4_rules_round2_calendar_center_number",
    ),
}


_GRADE4_RULES_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="규칙적인 수의 배열에서 ■, ●에 알맞은 수를 각각 구하세요.",
        expression="answer_text=2202, 2402",
        topic="pattern",
        rule_id="grade4_rules_round3_number_sequence_symbols",
    ),
    2: ElementaryVisualTemplate(
        problem_text="수 배열표에서 색칠한 수는 3105에서부터 어느 방향으로 몇씩 커지는 규칙인지 고르세요.",
        expression="answer_text=④",
        topic="pattern",
        rule_id="grade4_rules_round3_colored_table_rule",
    ),
    3: ElementaryVisualTemplate(
        problem_text="일부가 찢어진 수 배열표에서 색칠된 세로줄에 나타난 규칙을 찾아 기호를 쓰세요.",
        expression="answer_text=다",
        topic="pattern",
        rule_id="grade4_rules_round3_vertical_rule_choice",
    ),
    4: ElementaryVisualTemplate(
        problem_text="수 배열의 규칙에 맞게 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=164",
        topic="pattern",
        rule_id="grade4_rules_round3_number_sequence_blank",
    ),
    5: ElementaryVisualTemplate(
        problem_text="수 배열표를 보고 수 배열의 규칙에 맞게 색칠된 칸에 알맞은 수를 구하세요.",
        expression="answer_text=20292",
        topic="pattern",
        rule_id="grade4_rules_round3_torn_table_number",
    ),
    6: ElementaryVisualTemplate(
        problem_text="수 배열표를 보고 ㄱ, ㄴ, ㄷ에 알맞은 수를 각각 구하세요.",
        expression="answer_text=ㄱ 64, ㄴ 256, ㄷ 384",
        topic="pattern",
        rule_id="grade4_rules_round3_multiplication_table_blanks",
    ),
}


_GRADE4_RULES_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수 배열표를 보고 규칙적인 수의 배열에서 색칠된 칸에 알맞은 수를 구하세요.",
        expression="answer_text=● 2, ▲ 3",
        topic="pattern",
        rule_id="grade4_rules_round3_addition_table_blanks",
    ),
    2: ElementaryVisualTemplate(
        problem_text="도형의 배열을 보고 여섯 번째에 올 도형에서 사각형의 개수를 구하세요.",
        expression="answer_text=16 개",
        topic="pattern",
        rule_id="grade4_rules_round3_sixth_shape_square_count",
    ),
    3: ElementaryVisualTemplate(
        problem_text="연두색 도형이 45개인 모양은 몇째에 알맞은 모양인지 고르세요.",
        expression="answer_text=③",
        topic="pattern",
        rule_id="grade4_rules_round3_green_shape_45",
    ),
    4: ElementaryVisualTemplate(
        problem_text="규칙에 따라 도형을 배열했습니다. 다음에 올 모양의 색과 도형을 구하세요.",
        expression="answer_text=초록색, 사각형",
        topic="pattern",
        rule_id="grade4_rules_round3_next_color_shape",
    ),
    5: ElementaryVisualTemplate(
        problem_text="모양의 배열을 보고 여섯째에 올 모양에서 사각형은 몇 개인지 구하세요.",
        expression="answer_text=36 개",
        topic="pattern",
        rule_id="grade4_rules_round3_sixth_triangle_squares",
    ),
    6: ElementaryVisualTemplate(
        problem_text="계산식을 보고 설명에 맞는 계산식을 찾아 기호를 쓰세요.",
        expression="answer_text=라",
        topic="pattern",
        rule_id="grade4_rules_round3_matching_equation_rule",
    ),
}


_GRADE4_RULES_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="규칙에 따라 바둑돌을 늘어놓았습니다. 65째에 놓이는 바둑돌의 색을 고르세요.",
        expression="answer_text=②",
        topic="pattern",
        rule_id="grade4_rules_round3_go_stone_65th",
    ),
    2: ElementaryVisualTemplate(
        problem_text="덧셈식의 규칙에 따라 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=3900, 5400",
        topic="pattern",
        rule_id="grade4_rules_round3_addition_pattern_blanks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="덧셈식의 규칙을 잘못 설명한 것을 찾아 기호를 쓰세요.",
        expression="answer_text=나",
        topic="pattern",
        rule_id="grade4_rules_round3_wrong_rule_explanation",
    ),
    4: ElementaryVisualTemplate(
        problem_text="덧셈식에서 규칙에 따라 다섯째에 알맞은 덧셈식을 고르세요.",
        expression="answer_text=③",
        topic="pattern",
        rule_id="grade4_rules_round3_fifth_addition_choice",
    ),
    5: ElementaryVisualTemplate(
        problem_text="계산식 배열의 규칙에 맞게 빈칸에 알맞은 식을 써넣으세요.",
        expression="answer_text=6600 - 2400 = 4200",
        topic="pattern",
        rule_id="grade4_rules_round3_subtraction_pattern_blank",
    ),
    6: ElementaryVisualTemplate(
        problem_text="덧셈식의 규칙에 따라 값이 10000001이 되는 덧셈식을 구하세요.",
        expression="answer_text=6666662, 3333339",
        topic="pattern",
        rule_id="grade4_rules_round3_large_addition_blanks",
    ),
}


_GRADE4_RULES_ROUND3_PAGE4: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="연속한 세 수의 합이 가운데 수의 몇 배인지 보고 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=3, 3, 3, 158",
        topic="pattern",
        rule_id="grade4_rules_round3_three_consecutive_numbers",
    ),
    2: ElementaryVisualTemplate(
        problem_text="달력에서 같은 모양 안의 9개 수의 합을 보고 가운데 수를 구하세요.",
        expression="answer_text=22",
        topic="pattern",
        rule_id="grade4_rules_round3_calendar_center_number",
    ),
}


_GRADE4_FRACTION_ADD_SUB_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="2 3/4+1 2/4와 1-3/5을 계산하세요.",
        expression="answer_text=(1) 4 1/4, (2) 2/5",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round1_calculate_mixed_and_subtract",
    ),
    2: ElementaryVisualTemplate(
        problem_text="8/23, 13/23, 2/23, 17/23 중 가장 큰 수와 가장 작은 수의 합을 구하세요.",
        expression="answer_text=19/23",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round1_largest_smallest_sum",
    ),
    3: ElementaryVisualTemplate(
        problem_text="1 3/6에서 2 1/6을 더하고 다시 1 5/6을 더해 빈칸에 쓰세요.",
        expression="answer_text=3 4/6, 5 3/6",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round1_chain_mixed_addition",
    ),
    4: ElementaryVisualTemplate(
        problem_text="분모가 20인 진분수 중에서 가장 작은 분수와 두 번째로 작은 분수의 합을 구하세요.",
        expression="answer_text=3/20",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round1_two_smallest_denominator_20",
    ),
    5: ElementaryVisualTemplate(
        problem_text="4/15, 8/15, 7/15, 3/15 중 세 수를 골라 합이 1이 되도록 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=4, 8, 3",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round1_three_fractions_sum_one",
    ),
    6: ElementaryVisualTemplate(
        problem_text="1/7이 6개인 수와 1/7이 4개인 수의 합을 구하세요.",
        expression="answer_text=1 3/7",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round1_unit_fraction_counts_sum",
    ),
    7: ElementaryVisualTemplate(
        problem_text="우석이는 철사를 5/9 m, 지호는 6/9 m 사용했습니다. 두 사람이 사용한 철사는 모두 몇 m인지 구하세요.",
        expression="answer_text=1 2/9 m",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round1_wire_total",
    ),
}


_GRADE4_FRACTION_ADD_SUB_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="가로가 9/13 m, 세로가 5/13 m인 직사각형의 네 변의 길이의 합은 몇 m인지 구하세요.",
        expression="answer_text=2 2/13 m",
        topic="measurement",
        rule_id="grade4_fraction_add_sub_round1_rectangle_perimeter",
    ),
    2: ElementaryVisualTemplate(
        problem_text="□-4/9=3/9일 때 □ 안에 알맞은 분수를 구하세요.",
        expression="answer_text=7/9",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round1_unknown_minus_fraction",
    ),
    3: ElementaryVisualTemplate(
        problem_text="지호는 역사책을 전체의 6/15만큼, 승희는 전체의 9/15만큼 읽었습니다. 누가 전체의 얼마만큼 더 많이 읽었는지 구하세요.",
        expression="answer_text=승희, 3/15",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round1_more_read_history_book",
    ),
    4: ElementaryVisualTemplate(
        problem_text="㉠+㉡=1 6/13, ㉠-㉡=3/13을 만족하는 분모가 13인 분수 ㉠과 ㉡을 각각 구하세요.",
        expression="answer_text=㉠ 11/13, ㉡ 8/13",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round1_two_fraction_unknowns",
    ),
    5: ElementaryVisualTemplate(
        problem_text="경진이는 문제집을 전체의 7/11만큼 풀었습니다. 문제집을 모두 풀려면 전체의 얼마만큼을 더 풀어야 하는지 구하세요.",
        expression="answer_text=4/11",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round1_remaining_workbook",
    ),
    6: ElementaryVisualTemplate(
        problem_text="어제는 퍼즐 전체의 4/12, 오늘은 7/12를 맞췄습니다. 남은 퍼즐 조각이 15개라면 전체 조각 수를 구하세요.",
        expression="answer_text=180 조각",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round1_puzzle_total_pieces",
    ),
    7: ElementaryVisualTemplate(
        problem_text="2+3 3/8과 2 1/8+3 3/8의 크기를 비교하세요.",
        expression="answer_text=<",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round1_compare_mixed_sums",
    ),
    8: ElementaryVisualTemplate(
        problem_text="2 2/8+1 5/8<□/8일 때 □ 안에 들어갈 수 있는 수 중에서 가장 작은 자연수를 구하세요.",
        expression="answer_text=32",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round1_smallest_numerator_inequality",
    ),
}


_GRADE4_FRACTION_ADD_SUB_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="명균이는 철사를 1 3/6 m, 세영이는 2 5/6 m 사용했습니다. 두 사람이 사용한 철사는 모두 몇 m인지 구하세요.",
        expression="answer_text=4 2/6 m",
        topic="measurement",
        rule_id="grade4_fraction_add_sub_round1_wire_art_total",
    ),
    2: ElementaryVisualTemplate(
        problem_text="사과와 복숭아, 복숭아와 배, 사과와 배의 무게의 합이 각각 주어졌을 때 사과, 복숭아, 배의 무게의 합을 구하세요.",
        expression="answer_text=2 11/17 kg",
        topic="measurement",
        rule_id="grade4_fraction_add_sub_round1_three_fruits_total_weight",
    ),
    3: ElementaryVisualTemplate(
        problem_text="두 수도꼭지를 동시에 틀어 한 시간 동안 받을 수 있는 물의 양을 구하세요.",
        expression="answer_text=14 5/7 L",
        topic="measurement",
        rule_id="grade4_fraction_add_sub_round1_two_faucets_one_hour",
    ),
    4: ElementaryVisualTemplate(
        problem_text="길이가 13 cm인 색 테이프 4장을 1 1/7 cm씩 겹쳐 이어 붙였을 때 전체 길이를 구하세요.",
        expression="answer_text=48 4/7 cm",
        topic="measurement",
        rule_id="grade4_fraction_add_sub_round1_tape_overlap_total",
    ),
    5: ElementaryVisualTemplate(
        problem_text="진우와 수지가 사용하고 남은 끈의 길이를 비교하여 누구의 끈이 몇 m 더 많이 남았는지 구하세요.",
        expression="answer_text=수지, 4/5 m",
        topic="measurement",
        rule_id="grade4_fraction_add_sub_round1_remaining_rope_compare",
    ),
}


_GRADE4_FRACTION_ADD_SUB_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="4/17+11/17과 13/17의 크기를 비교하세요.",
        expression="answer_text=>",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round2_compare_fraction_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="2 2/3에서 1 1/3을 빼서 빈칸에 쓰세요.",
        expression="answer_text=1 1/3",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round2_mixed_subtraction_chain",
    ),
    3: ElementaryVisualTemplate(
        problem_text="같은 모양은 같은 수를 나타낼 때 ●+●+●=1 5/7입니다. ● 모양에 알맞은 수를 구하세요.",
        expression="answer_text=4/7",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round2_same_shape_fraction",
    ),
    4: ElementaryVisualTemplate(
        problem_text="수직선에서 ㉠과 ㉡이 나타내는 분수의 합을 구하세요.",
        expression="answer_text=1 2/7",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round2_number_line_sum",
    ),
    5: ElementaryVisualTemplate(
        problem_text="어제 7/15, 오늘 4/15를 읽었고 읽은 쪽수가 77쪽일 때 만화책의 전체 쪽수를 구하세요.",
        expression="answer_text=105 쪽",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round2_comic_total_pages",
    ),
    6: ElementaryVisualTemplate(
        problem_text="세 변이 4/6 m, 4/6 m, 5/6 m인 삼각형의 세 변의 길이의 합을 구하세요.",
        expression="answer_text=2 1/6 m",
        topic="measurement",
        rule_id="grade4_fraction_add_sub_round2_triangle_perimeter",
    ),
    7: ElementaryVisualTemplate(
        problem_text="□-4/11=5/11일 때 □ 안에 알맞은 분수를 구하세요.",
        expression="answer_text=9/11",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round2_unknown_minus_fraction",
    ),
}


_GRADE4_FRACTION_ADD_SUB_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="딸기 11/12 kg 중 6/12 kg, 방울토마토 9/12 kg 중 5/12 kg을 먹었을 때 남은 것 중 어느 것이 몇 kg 더 무거운지 구하세요.",
        expression="answer_text=딸기, 1/12 kg",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round2_remaining_strawberry_tomato",
    ),
    2: ElementaryVisualTemplate(
        problem_text="분모가 15인 진분수 두 개의 합이 1 6/15이고 차가 7/15일 때 두 진분수를 구하세요.",
        expression="answer_text=14/15, 7/15",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round2_two_proper_fractions",
    ),
    3: ElementaryVisualTemplate(
        problem_text="1-7/8, 1-5/8, 1-8/9 중 계산 결과가 가장 큰 것을 고르세요.",
        expression="answer_text=나",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round2_largest_subtraction_result",
    ),
    4: ElementaryVisualTemplate(
        problem_text="만화책을 어제 7/14, 오늘 6/14 읽고 남은 쪽수가 35쪽일 때 전체 쪽수를 구하세요.",
        expression="answer_text=490 쪽",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round2_comic_total_pages",
    ),
    5: ElementaryVisualTemplate(
        problem_text="분모가 9인 가분수 두 개의 합이 4 2/9이고 차가 8/9일 때 두 가분수를 구하세요.",
        expression="answer_text=23/9, 15/9",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round2_two_improper_fractions",
    ),
    6: ElementaryVisualTemplate(
        problem_text="같은 길이의 색 테이프 3장을 1 3/5 cm씩 겹쳐 이어 붙였더니 전체 길이가 21 2/5 cm가 되었습니다. 색 테이프 한 장의 길이를 구하세요.",
        expression="answer_text=8 1/5 cm",
        topic="measurement",
        rule_id="grade4_fraction_add_sub_round2_original_tape_length",
    ),
    7: ElementaryVisualTemplate(
        problem_text="2 9/13, 2 5/13, 2 7/13 중 분수 카드 2장을 골라 합이 가장 큰 덧셈식을 만들고 계산하세요.",
        expression="answer_text=식: 2 9/13+2 7/13, 답: 5 3/13",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round2_largest_sum_cards",
    ),
    8: ElementaryVisualTemplate(
        problem_text="1/9이 61개인 수와 3 5/9의 차를 구하세요.",
        expression="answer_text=3 2/9",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round2_unit_fraction_count_difference",
    ),
}


_GRADE4_FRACTION_ADD_SUB_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="대분수로만 만들어진 뺄셈식 5□/7-4▲/7=1 3/7에서 ■+▲가 가장 클 때의 값을 구하세요.",
        expression="answer_text=9",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round2_largest_blank_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="8, 4/9, 5, 6 1/9, 2 2/9 중 가장 큰 수와 가장 작은 수의 차를 구하세요.",
        expression="answer_text=7 5/9",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round2_largest_smallest_difference",
    ),
    3: ElementaryVisualTemplate(
        problem_text="감자 12 7/9 kg 중 요리에 4 3/9 kg을 사용했습니다. 남은 감자는 몇 kg인지 구하세요.",
        expression="answer_text=8 4/9 kg",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round2_potatoes_remaining",
    ),
    4: ElementaryVisualTemplate(
        problem_text="길이가 20 5/7 cm인 끈과 15 6/7 cm인 끈을 한 번 묶은 후 길이가 28 2/7 cm가 되었습니다. 묶기 전 길이의 합보다 몇 cm 줄었는지 구하세요.",
        expression="answer_text=8 2/7 cm",
        topic="measurement",
        rule_id="grade4_fraction_add_sub_round2_rope_length_decrease",
    ),
    5: ElementaryVisualTemplate(
        problem_text="네 면의 벽을 칠하기 위해 페인트 9 5/8 L를 샀고 한 면에 3 2/8 L가 필요합니다. 페인트를 몇 L 더 사야 하는지 구하세요.",
        expression="answer_text=3 3/8 L",
        topic="measurement",
        rule_id="grade4_fraction_add_sub_round2_paint_more_needed",
    ),
}


_GRADE4_FRACTION_ADD_SUB_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="3 2/7+2 5/7과 4-3 1/3을 계산하세요.",
        expression="answer_text=(1) 6, (2) 2/3",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round3_calculate_mixed",
    ),
    2: ElementaryVisualTemplate(
        problem_text="5/16+7/16과 9/16의 크기를 비교하세요.",
        expression="answer_text=>",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round3_compare_fraction_sum",
    ),
    3: ElementaryVisualTemplate(
        problem_text="분모가 11인 진분수 중 가장 작은 분수와 두 번째로 작은 분수의 합을 구하세요.",
        expression="answer_text=3/11",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round3_two_smallest_denominator_11",
    ),
    4: ElementaryVisualTemplate(
        problem_text="1과 2/7의 차를 구하세요.",
        expression="answer_text=5/7",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round3_difference_one_and_two_sevenths",
    ),
    5: ElementaryVisualTemplate(
        problem_text="3 5/8에서 11/8을 빼고 1 7/8을 더한 값을 구하세요.",
        expression="answer_text=4 1/8",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round3_chain_mixed_calculation",
    ),
    6: ElementaryVisualTemplate(
        problem_text="분모가 6인 진분수의 합을 구하세요.",
        expression="answer_text=2 3/6",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round3_sum_proper_fractions_denominator_6",
    ),
    7: ElementaryVisualTemplate(
        problem_text="어제 5/12, 오늘 4/12를 읽었고 읽은 쪽수가 72쪽일 때 소설책 전체 쪽수를 구하세요.",
        expression="answer_text=96 쪽",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round3_novel_total_pages",
    ),
    8: ElementaryVisualTemplate(
        problem_text="세로가 4/7 cm이고 가로가 세로보다 2/7 cm 더 긴 직사각형의 네 변의 길이의 합을 구하세요.",
        expression="answer_text=2 6/7 cm",
        topic="measurement",
        rule_id="grade4_fraction_add_sub_round3_rectangle_perimeter",
    ),
}


_GRADE4_FRACTION_ADD_SUB_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="숫자 카드 5, 3, 7 중 한 장을 사용하여 분모가 9인 진분수를 만들 때 가장 큰 진분수와 가장 작은 진분수의 합을 구하세요.",
        expression="answer_text=1 1/9",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round3_digit_card_fraction_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="수지가 키운 강낭콩은 17/20 cm이고 민경이가 키운 강낭콩은 11/20 cm입니다. 수지가 키운 강낭콩은 몇 cm 더 큰지 구하세요.",
        expression="answer_text=6/20 cm",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round3_bean_height_difference",
    ),
    3: ElementaryVisualTemplate(
        problem_text="밀가루 17/20 kg으로 빵 한 개에 3/20 kg씩 사용할 때 만들 수 있는 빵의 개수와 남는 밀가루를 구하세요.",
        expression="answer_text=5 개, 2/20 kg",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round3_flour_bread_remainder",
    ),
    4: ElementaryVisualTemplate(
        problem_text="★+★=2 8/9일 때 ★ 모양에 알맞은 수를 구하세요.",
        expression="answer_text=1 4/9",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round3_same_star_value",
    ),
    5: ElementaryVisualTemplate(
        problem_text="2 8/11+2 9/11-3 5/11을 계산하세요.",
        expression="answer_text=2 1/11",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round3_mixed_expression",
    ),
    6: ElementaryVisualTemplate(
        problem_text="지호의 몸무게는 27 3/8 kg이고 경수는 지호보다 1 4/8 kg 더 무겁습니다. 두 사람의 몸무게의 합을 구하세요.",
        expression="answer_text=56 2/8 kg",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round3_weight_sum",
    ),
    7: ElementaryVisualTemplate(
        problem_text="무게가 똑같은 멜론 4통의 무게가 3 2/7 kg일 때 12통의 무게를 구하세요.",
        expression="answer_text=9 6/7 kg",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round3_melon_weight",
    ),
}


_GRADE4_FRACTION_ADD_SUB_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="길이가 23 5/6 cm인 양초가 4 3/6 cm만큼 탔습니다. 타고 남은 양초의 길이를 구하세요.",
        expression="answer_text=19 2/6 cm",
        topic="measurement",
        rule_id="grade4_fraction_add_sub_round3_candle_remaining_length",
    ),
    2: ElementaryVisualTemplate(
        problem_text="수직선에서 ㄱ에서 ㄹ까지의 거리를 구하세요. ㄱㄷ은 2 5/7 km, ㄴㄷ은 10/7 km, ㄴㄹ은 3 1/7 km입니다.",
        expression="answer_text=4 3/7 km",
        topic="measurement",
        rule_id="grade4_fraction_add_sub_round3_number_line_total_distance",
    ),
    3: ElementaryVisualTemplate(
        problem_text="3-24/10, 3-7/10, 4-2 6/10, 6-4 3/10 중 계산 결과가 가장 작은 것의 기호를 고르세요.",
        expression="answer_text=ㄱ",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round3_smallest_result_choice",
    ),
    4: ElementaryVisualTemplate(
        problem_text="막대를 연못 바닥까지 넣었다가 꺼내 재니 젖은 부분이 2 3/9 m였고, 막대를 거꾸로 넣었다가 꺼내 재니 두 번 젖은 부분이 1 2/9 m였습니다. 막대의 길이를 구하세요.",
        expression="answer_text=3 5/9 m",
        topic="measurement",
        rule_id="grade4_fraction_add_sub_round3_stick_length_from_wet_parts",
    ),
    5: ElementaryVisualTemplate(
        problem_text="어떤 대분수에서 3/8을 빼야 할 것을 잘못하여 더했더니 4가 되었습니다. 바르게 계산한 값을 구하세요.",
        expression="answer_text=3 2/8",
        topic="fraction_ratio",
        rule_id="grade4_fraction_add_sub_round3_wrong_add_instead_of_subtract",
    ),
}


_GRADE4_TRIANGLE_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="삼각형 ㄱㄴㄷ의 꼭짓점 ㄱ을 옮겨 이등변삼각형을 만들 때 꼭짓점 ㄱ을 옮길 점을 고르세요.",
        expression="answer_text=④",
        topic="geometry",
        rule_id="grade4_triangle_round1_move_vertex_to_isosceles",
    ),
    2: ElementaryVisualTemplate(
        problem_text="세 변의 길이의 합이 16 cm인 이등변삼각형에서 밑변이 6 cm일 때 변 ㄱ의 길이를 구하세요.",
        expression="answer_text=5 cm",
        topic="geometry",
        rule_id="grade4_triangle_round1_isosceles_side_from_perimeter",
    ),
    3: ElementaryVisualTemplate(
        problem_text="삼각형을 변의 길이에 따라 분류하고 이름을 쓰세요.",
        expression="answer_text=다, 라, 나, 라, 이등변삼각형, 정삼각형",
        topic="geometry",
        rule_id="grade4_triangle_round1_classify_by_side_lengths",
    ),
    4: ElementaryVisualTemplate(
        problem_text="두 변의 길이가 각각 11 cm와 7 cm인 이등변삼각형에서 나머지 한 변의 길이가 될 수 있는 것을 모두 쓰세요.",
        expression="answer_text=7 cm, 11 cm",
        topic="geometry",
        rule_id="grade4_triangle_round1_possible_third_side_lengths",
    ),
    5: ElementaryVisualTemplate(
        problem_text="둘레가 각각 26 cm인 두 이등변삼각형에서 ㄱ과 ㄴ에 알맞은 수의 합을 구하세요.",
        expression="answer_text=20",
        topic="geometry",
        rule_id="grade4_triangle_round1_sum_unknown_sides",
    ),
    6: ElementaryVisualTemplate(
        problem_text="네 변의 길이의 합이 24 cm인 정사각형 모양 색종이를 잘라 정삼각형을 만들 때 만들 수 있는 가장 큰 정삼각형의 세 변의 길이의 합을 구하세요.",
        expression="answer_text=18 cm",
        topic="geometry",
        rule_id="grade4_triangle_round1_largest_equilateral_from_square",
    ),
}


_GRADE4_TRIANGLE_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="세 변의 길이의 합이 12 cm인 정삼각형 6개를 붙여 만든 도형에서 굵은 선의 길이를 구하세요.",
        expression="answer_text=24 cm",
        topic="geometry",
        rule_id="grade4_triangle_round1_hexagon_bold_line_length",
    ),
    2: ElementaryVisualTemplate(
        problem_text="길이가 50 cm인 철사를 겹치지 않게 사용하여 정삼각형을 만들고 5 cm가 남았습니다. 만든 정삼각형의 한 변의 길이를 구하세요.",
        expression="answer_text=15 cm",
        topic="geometry",
        rule_id="grade4_triangle_round1_equilateral_wire_side",
    ),
    3: ElementaryVisualTemplate(
        problem_text="예각삼각형, 둔각삼각형, 직각삼각형을 그림에 맞게 쓰세요.",
        expression="answer_text=직, 예, 둔",
        topic="geometry",
        rule_id="grade4_triangle_round1_classify_by_angles",
    ),
    4: ElementaryVisualTemplate(
        problem_text="도형에서 찾을 수 있는 크고 작은 이등변삼각형은 모두 몇 개인지 구하세요.",
        expression="answer_text=13 개",
        topic="geometry",
        rule_id="grade4_triangle_round1_count_isosceles_triangles",
    ),
    5: ElementaryVisualTemplate(
        problem_text="삼각형 ㄱㄴㄷ은 이등변삼각형입니다. 변 ㄴㄱ과 변 ㄴㄷ의 길이가 같고 각 ㄱ이 75°일 때 각 ㄱㄴㄷ의 크기를 구하세요.",
        expression="answer_text=30°",
        topic="geometry",
        rule_id="grade4_triangle_round1_isosceles_vertex_angle",
    ),
    6: ElementaryVisualTemplate(
        problem_text="그림의 삼각형에서 세 변의 길이의 합을 구하세요.",
        expression="answer_text=87 cm",
        topic="geometry",
        rule_id="grade4_triangle_round1_triangle_perimeter_with_equal_angles",
    ),
    7: ElementaryVisualTemplate(
        problem_text="삼각형 ㄱㄴㄷ은 이등변삼각형입니다. 각 ㄴㅂㄷ의 크기를 구하세요.",
        expression="answer_text=108°",
        topic="geometry",
        rule_id="grade4_triangle_round1_crossed_isosceles_angle",
    ),
    8: ElementaryVisualTemplate(
        problem_text="직사각형 모양의 종이를 점선을 따라 오려서 삼각형을 만들었습니다. 예각삼각형은 모두 몇 개인지 구하세요.",
        expression="answer_text=4 개",
        topic="geometry",
        rule_id="grade4_triangle_round1_count_acute_triangles_from_rectangle",
    ),
}


_GRADE4_TRIANGLE_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="삼각형의 세 각 중 두 각의 크기를 나타낸 것 중 예각삼각형이 되는 것을 고르세요.",
        expression="answer_text=④",
        topic="geometry",
        rule_id="grade4_triangle_round1_acute_triangle_angle_choice",
    ),
    2: ElementaryVisualTemplate(
        problem_text="다음 설명 중 잘못 설명한 것을 고르세요.",
        expression="answer_text=⑤",
        topic="geometry",
        rule_id="grade4_triangle_round1_incorrect_triangle_statement",
    ),
    3: ElementaryVisualTemplate(
        problem_text="그림에서 찾을 수 있는 크고 작은 예각삼각형은 모두 몇 개인지 구하세요.",
        expression="answer_text=4 개",
        topic="geometry",
        rule_id="grade4_triangle_round1_count_acute_triangles",
    ),
    4: ElementaryVisualTemplate(
        problem_text="삼각형을 보고 이등변삼각형이면서 둔각삼각형인 것을 찾으세요.",
        expression="answer_text=바",
        topic="geometry",
        rule_id="grade4_triangle_round1_isosceles_obtuse_choice",
    ),
    5: ElementaryVisualTemplate(
        problem_text="삼각형 ㄱㄴㄷ은 정삼각형이고 삼각형 ㄹㄷㅁ은 이등변삼각형입니다. ㉠의 크기를 구하세요.",
        expression="answer_text=80°",
        topic="geometry",
        rule_id="grade4_triangle_round1_equilateral_isosceles_angle",
    ),
    6: ElementaryVisualTemplate(
        problem_text="삼각형 ㄱㄴㄷ은 정삼각형이고 삼각형 ㄱㄷㄹ은 이등변삼각형입니다. 각 ㄴㄱㄹ의 크기를 구하세요.",
        expression="answer_text=110°",
        topic="geometry",
        rule_id="grade4_triangle_round1_equilateral_isosceles_outer_angle",
    ),
}


_GRADE4_TRIANGLE_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="이등변삼각형의 세 변의 길이의 합이 18 cm이고 한 변이 5 cm일 때 변 ㄴㄷ의 길이를 구하세요.",
        expression="answer_text=8 cm",
        topic="geometry",
        rule_id="grade4_triangle_round2_isosceles_unknown_side",
    ),
    2: ElementaryVisualTemplate(
        problem_text="이등변삼각형 ㄱㄴㄷ과 ㄹㄴㄷ의 둘레가 각각 34 cm와 20 cm일 때 색칠한 도형의 둘레를 구하세요.",
        expression="answer_text=38 cm",
        topic="geometry",
        rule_id="grade4_triangle_round2_shaded_perimeter",
    ),
    3: ElementaryVisualTemplate(
        problem_text="이등변삼각형과 정삼각형에 대한 설명으로 틀린 것을 찾아 기호를 쓰세요.",
        expression="answer_text=다",
        topic="geometry",
        rule_id="grade4_triangle_round2_incorrect_statement_symbol",
    ),
    4: ElementaryVisualTemplate(
        problem_text="그림에서 찾을 수 있는 크고 작은 이등변삼각형은 모두 몇 개인지 구하세요.",
        expression="answer_text=8 개",
        topic="geometry",
        rule_id="grade4_triangle_round2_count_isosceles_triangles_square",
    ),
    5: ElementaryVisualTemplate(
        problem_text="세 변의 길이의 합이 45 cm인 정삼각형의 한 변의 길이를 구하세요.",
        expression="answer_text=15 cm",
        topic="geometry",
        rule_id="grade4_triangle_round2_equilateral_side_from_perimeter",
    ),
    6: ElementaryVisualTemplate(
        problem_text="이등변삼각형과 정삼각형의 세 변의 길이의 합이 같을 때 변 ㄱㄴ의 길이를 구하세요.",
        expression="answer_text=14 cm",
        topic="geometry",
        rule_id="grade4_triangle_round2_equal_perimeter_side",
    ),
    7: ElementaryVisualTemplate(
        problem_text="정삼각형 세 개를 붙여 만든 도형의 둘레의 길이를 구하세요.",
        expression="answer_text=20 cm",
        topic="geometry",
        rule_id="grade4_triangle_round2_three_equilateral_perimeter",
    ),
}


_GRADE4_TRIANGLE_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="이등변삼각형 ㄴㄷㄹ과 정삼각형 ㄱㄴㄹ을 겹치지 않게 이어 붙여 만든 사각형의 네 변의 길이의 합이 32 cm일 때 변 ㄱㄴ의 길이를 구하세요.",
        expression="answer_text=10 cm",
        topic="geometry",
        rule_id="grade4_triangle_round2_quadrilateral_side_from_perimeter",
    ),
    2: ElementaryVisualTemplate(
        problem_text="삼각형 ㄱㄴㄷ은 이등변삼각형입니다. ㉠과 ㉡의 각도를 각각 구하세요.",
        expression="answer_text=㉠: 80°, ㉡: 140°",
        topic="geometry",
        rule_id="grade4_triangle_round2_isosceles_angles_a_b",
    ),
    3: ElementaryVisualTemplate(
        problem_text="㉠과 ㉡의 크기의 합은 몇 도인지 구하세요.",
        expression="answer_text=240°",
        topic="geometry",
        rule_id="grade4_triangle_round2_angle_sum_a_b",
    ),
    4: ElementaryVisualTemplate(
        problem_text="삼각형 ㄱㄴㄷ과 삼각형 ㄷㄹㅁ이 이등변삼각형일 때 각 ㄱㄷㅁ의 크기를 구하세요.",
        expression="answer_text=80°",
        topic="geometry",
        rule_id="grade4_triangle_round2_adjacent_isosceles_angle",
    ),
    5: ElementaryVisualTemplate(
        problem_text="직사각형 모양의 종이를 점선을 따라 오렸습니다. 둔각삼각형은 모두 몇 개인지 구하세요.",
        expression="answer_text=2 개",
        topic="geometry",
        rule_id="grade4_triangle_round2_count_obtuse_triangles",
    ),
    6: ElementaryVisualTemplate(
        problem_text="도형을 선분을 따라 잘랐을 때 만들어지는 예각삼각형과 둔각삼각형의 개수를 각각 구하세요.",
        expression="answer_text=㉠ 1 개, ㉡ 3 개",
        topic="geometry",
        rule_id="grade4_triangle_round2_count_acute_obtuse_cut_shape",
    ),
    7: ElementaryVisualTemplate(
        problem_text="삼각형 ㄱㄴㄷ과 삼각형 ㄱㄹㄷ은 각각 이등변삼각형입니다. 삼각형 ㄱㄹㄴ의 종류를 쓰세요.",
        expression="answer_text=둔각삼각형",
        topic="geometry",
        rule_id="grade4_triangle_round2_classify_triangle_angle_type",
    ),
}


_GRADE4_TRIANGLE_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림의 삼각형 이름이 될 수 있는 것을 모두 찾아 기호를 쓰세요.",
        expression="answer_text=가, 다",
        topic="geometry",
        rule_id="grade4_triangle_round2_possible_triangle_names",
    ),
    2: ElementaryVisualTemplate(
        problem_text="이등변삼각형이면서 예각삼각형인 것은 세 변의 길이가 모두 다른 삼각형이면서 둔각삼각형인 것보다 몇 개 더 많은지 구하세요.",
        expression="answer_text=1 개",
        topic="geometry",
        rule_id="grade4_triangle_round2_more_isosceles_acute_than_scalene_obtuse",
    ),
    3: ElementaryVisualTemplate(
        problem_text="원 위에 일정한 간격으로 점 6개를 찍었습니다. 원 위의 세 점을 연결하여 만들 수 있는 예각삼각형은 모두 몇 개인지 구하세요.",
        expression="answer_text=2 개",
        topic="geometry",
        rule_id="grade4_triangle_round2_circle_six_points_acute_triangles",
    ),
    4: ElementaryVisualTemplate(
        problem_text="삼각형의 두 각의 크기를 나타낸 것 중 둔각삼각형이 되는 것을 고르세요.",
        expression="answer_text=④",
        topic="geometry",
        rule_id="grade4_triangle_round2_obtuse_triangle_angle_choice",
    ),
    5: ElementaryVisualTemplate(
        problem_text="삼각형 ㄱㄴㄷ은 정삼각형입니다. 각 ㄱㄴㄹ의 크기를 구하세요.",
        expression="answer_text=15°",
        topic="geometry",
        rule_id="grade4_triangle_round2_equilateral_angle_with_ray",
    ),
    6: ElementaryVisualTemplate(
        problem_text="도형에서 삼각형 ㄱㄴㄷ은 이등변삼각형이고 삼각형 ㄹㄴㄷ은 정삼각형입니다. 각 ㄱㄷㄹ의 크기를 구하세요.",
        expression="answer_text=15°",
        topic="geometry",
        rule_id="grade4_triangle_round2_isosceles_equilateral_angle",
    ),
}


_GRADE4_TRIANGLE_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="다음 이등변삼각형의 세 변의 길이의 합을 구하세요.",
        expression="answer_text=33 cm",
        topic="geometry",
        rule_id="grade4_triangle_round3_isosceles_perimeter",
    ),
    2: ElementaryVisualTemplate(
        problem_text="이등변삼각형과 정사각형을 겹치지 않게 이어 붙여 만든 도형에서 이등변삼각형의 둘레가 32 cm일 때 도형의 둘레를 구하세요.",
        expression="answer_text=48 cm",
        topic="geometry",
        rule_id="grade4_triangle_round3_attached_square_perimeter",
    ),
    3: ElementaryVisualTemplate(
        problem_text="이등변삼각형과 정삼각형에 대한 설명 중 잘못 설명한 것을 찾아 기호를 쓰세요.",
        expression="answer_text=라",
        topic="geometry",
        rule_id="grade4_triangle_round3_incorrect_statement_symbol",
    ),
    4: ElementaryVisualTemplate(
        problem_text="같은 크기의 정삼각형 16개를 이어 붙인 도형에서 굵은 선의 길이가 144 cm일 때 가장 작은 정삼각형의 한 변의 길이를 구하세요.",
        expression="answer_text=12 cm",
        topic="geometry",
        rule_id="grade4_triangle_round3_small_equilateral_side_from_bold_line",
    ),
    5: ElementaryVisualTemplate(
        problem_text="삼각형 ㄱㄴㄷ은 이등변삼각형입니다. 빈칸에 알맞은 각도를 구하세요.",
        expression="answer_text=80°",
        topic="geometry",
        rule_id="grade4_triangle_round3_isosceles_exterior_angle",
    ),
    6: ElementaryVisualTemplate(
        problem_text="이등변삼각형 ㄴㄷㄹ과 정삼각형 ㄱㄴㄹ을 이어 붙여 만든 사각형의 네 변의 길이의 합이 38 cm일 때 변 ㄱㄴ의 길이를 구하세요.",
        expression="answer_text=12 cm",
        topic="geometry",
        rule_id="grade4_triangle_round3_quadrilateral_side_from_perimeter",
    ),
}


_GRADE4_TRIANGLE_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="삼각형 ㄱㄴㄷ과 삼각형 ㄱㄷㄹ은 이등변삼각형입니다. 각 ㄱㄹㄷ의 크기를 구하세요.",
        expression="answer_text=15°",
        topic="geometry",
        rule_id="grade4_triangle_round3_adjacent_isosceles_angle",
    ),
    2: ElementaryVisualTemplate(
        problem_text="다음 설명 중 바르지 못한 것을 고르세요.",
        expression="answer_text=⑤",
        topic="geometry",
        rule_id="grade4_triangle_round3_incorrect_description_choice",
    ),
    3: ElementaryVisualTemplate(
        problem_text="직각삼각형과 이등변삼각형이 겹친 그림에서 각 ㄴㄹㄷ의 크기를 구하세요.",
        expression="answer_text=100°",
        topic="geometry",
        rule_id="grade4_triangle_round3_right_isosceles_angle",
    ),
    4: ElementaryVisualTemplate(
        problem_text="삼각형 모양의 종이를 접은 그림에서 각 ㄱㅂㄹ의 크기를 구하세요.",
        expression="answer_text=70°",
        topic="geometry",
        rule_id="grade4_triangle_round3_folded_triangle_angle",
    ),
    5: ElementaryVisualTemplate(
        problem_text="예각삼각형에서 예각의 수와 둔각삼각형에서 둔각의 수를 각각 구하세요.",
        expression="answer_text=㉠ 3, ㉡ 1",
        topic="geometry",
        rule_id="grade4_triangle_round3_acute_obtuse_angle_counts",
    ),
    6: ElementaryVisualTemplate(
        problem_text="삼각형 가, 나, 다에서 찾을 수 있는 예각은 모두 몇 개인지 구하세요.",
        expression="answer_text=7 개",
        topic="geometry",
        rule_id="grade4_triangle_round3_count_acute_angles",
    ),
    7: ElementaryVisualTemplate(
        problem_text="삼각형을 변과 각의 성질에 따라 분류하세요.",
        expression="answer_text=라, 마, 나 / 가, 다, 바",
        topic="geometry",
        rule_id="grade4_triangle_round3_classify_triangles_table",
    ),
}


_GRADE4_TRIANGLE_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="길이가 같은 빨대 3개를 세 변으로 하여 만들 수 있는 삼각형을 모두 고르세요.",
        expression="answer_text=①, ②, ③",
        topic="geometry",
        rule_id="grade4_triangle_round3_equal_straw_triangle_choices",
    ),
    2: ElementaryVisualTemplate(
        problem_text="도형에서 찾을 수 있는 크고 작은 둔각삼각형은 모두 몇 개인지 구하세요.",
        expression="answer_text=3 개",
        topic="geometry",
        rule_id="grade4_triangle_round3_count_obtuse_triangles",
    ),
    3: ElementaryVisualTemplate(
        problem_text="직사각형 모양의 종이를 점선을 따라 잘랐을 때 만들어지는 예각삼각형은 둔각삼각형보다 몇 개 더 많은지 구하세요.",
        expression="answer_text=2 개",
        topic="geometry",
        rule_id="grade4_triangle_round3_acute_minus_obtuse_from_rectangle",
    ),
    4: ElementaryVisualTemplate(
        problem_text="이등변삼각형 두 개로 이루어진 도형에서 삼각형 ㄱㄹㄴ이 예각삼각형, 둔각삼각형, 직각삼각형 중 어떤 삼각형인지 쓰세요.",
        expression="answer_text=예각삼각형",
        topic="geometry",
        rule_id="grade4_triangle_round3_classify_inner_triangle",
    ),
    5: ElementaryVisualTemplate(
        problem_text="한 각의 크기가 40°인 이등변삼각형이 예각삼각형일 때 나머지 두 각의 크기를 각각 구하세요.",
        expression="answer_text=70°, 70°",
        topic="geometry",
        rule_id="grade4_triangle_round3_isosceles_acute_remaining_angles",
    ),
    6: ElementaryVisualTemplate(
        problem_text="정삼각형과 이등변삼각형이 함께 있는 그림에서 각 ㄱㄴㄹ의 크기를 구하세요.",
        expression="answer_text=30°",
        topic="geometry",
        rule_id="grade4_triangle_round3_equilateral_isosceles_angle",
    ),
    7: ElementaryVisualTemplate(
        problem_text="삼각형 ㄱㄷㄹ은 정삼각형입니다. 각 ㄴㄷㄱ의 크기를 구하세요.",
        expression="answer_text=120°",
        topic="geometry",
        rule_id="grade4_triangle_round3_equilateral_outer_angle",
    ),
}


_GRADE4_DECIMAL_ADD_SUB_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="전체 크기가 1인 모눈종이에서 색칠된 부분의 크기를 분수와 소수로 나타내세요.",
        expression="answer_text=48/100, 0.48",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round1_grid_fraction_decimal",
    ),
    2: ElementaryVisualTemplate(
        problem_text="35/1000를 소수로 쓰고 읽으세요.",
        expression="answer_text=0.035, 영점영삼오",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round1_fraction_to_decimal_reading",
    ),
    3: ElementaryVisualTemplate(
        problem_text="3.075에서 7은 어느 자리 숫자인지 쓰고 나타내는 수를 구하세요.",
        expression="answer_text=소수 둘째, 0.07",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round1_place_value_3075",
    ),
    4: ElementaryVisualTemplate(
        problem_text="0.7의 10배와 7/100을 소수로 쓰세요.",
        expression="answer_text=7, 0.07",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round1_ten_times_and_one_tenth",
    ),
    5: ElementaryVisualTemplate(
        problem_text="소수점 위치가 10배씩 변하는 표의 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=6, 0.6, 0.06, 0.006",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round1_place_shift_table_down",
    ),
    6: ElementaryVisualTemplate(
        problem_text="1/10배와 10배 관계를 보고 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=0.03, 0.3, 3, 30, 300 / 0.002, 0.02, 0.2, 2, 20",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round1_place_shift_table_two_rows",
    ),
    7: ElementaryVisualTemplate(
        problem_text="1이 20개, 0.1이 5개, 0.01이 12개인 수를 소수로 쓰세요.",
        expression="answer_text=20.62",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round1_decimal_from_unit_counts",
    ),
    8: ElementaryVisualTemplate(
        problem_text="5.808에서 ㉠이 나타내는 수는 ㉡이 나타내는 수의 몇 배인지 구하세요.",
        expression="answer_text=100 배",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round1_place_value_ratio",
    ),
}


_GRADE4_DECIMAL_ADD_SUB_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="단위 사이의 관계를 잘못 나타낸 것을 고르세요.",
        expression="answer_text=③",
        topic="measurement",
        rule_id="grade4_decimal_round1_wrong_unit_relation",
    ),
    2: ElementaryVisualTemplate(
        problem_text="0.27보다 0.79 큰 수를 구하세요.",
        expression="answer_text=1.06",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round1_add_027_079",
    ),
    3: ElementaryVisualTemplate(
        problem_text="1.5, 0.9, 1.9, 0.6 중 가장 큰 소수와 가장 작은 소수의 합을 구하세요.",
        expression="answer_text=2.5",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round1_largest_smallest_sum",
    ),
    4: ElementaryVisualTemplate(
        problem_text="2.15+4.96과 3.49+5.86의 계산 결과를 구하세요.",
        expression="answer_text=7.11, 9.35",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round1_addition_table",
    ),
    5: ElementaryVisualTemplate(
        problem_text="2 m 73 cm, 57 cm, 두 길이의 합을 m 단위 소수로 나타내세요.",
        expression="answer_text=2.73, 0.57, 3.3",
        topic="measurement",
        rule_id="grade4_decimal_round1_length_sum_meters",
    ),
    6: ElementaryVisualTemplate(
        problem_text="영준이는 우유를 350 mL씩 3번 마셨습니다. 마신 우유를 L 단위 소수로 나타내세요.",
        expression="answer_text=1.05 L",
        topic="measurement",
        rule_id="grade4_decimal_round1_milk_liters",
    ),
    7: ElementaryVisualTemplate(
        problem_text="계산 결과가 작은 것부터 차례로 기호를 쓰세요.",
        expression="answer_text=ㄴ, ㄹ, ㄱ, ㄷ",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round1_subtraction_order",
    ),
    8: ElementaryVisualTemplate(
        problem_text="0.01이 72개인 수와 0.01이 37개인 수의 차를 구하세요.",
        expression="answer_text=0.35",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round1_hundredth_count_difference",
    ),
}


_GRADE4_DECIMAL_ADD_SUB_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="카드 2, 5, 7과 소수점을 한 번씩 모두 사용하여 소수 두 자리 수를 만들 때 가장 큰 수와 가장 작은 수의 합을 구하세요.",
        expression="answer_text=10.09",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round1_card_largest_smallest_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="길이가 28.6 cm인 색 테이프 2장을 2.47 cm가 겹치도록 이어 붙였을 때 전체 길이를 구하세요.",
        expression="answer_text=54.73 cm",
        topic="measurement",
        rule_id="grade4_decimal_round1_tape_overlap_total_length",
    ),
    3: ElementaryVisualTemplate(
        problem_text="어떤 수에 0.29를 더해야 할 것을 잘못하여 뺐더니 0.8이 되었습니다. 바르게 계산한 값을 구하세요.",
        expression="answer_text=1.38",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round1_wrong_subtract_instead_of_add",
    ),
    4: ElementaryVisualTemplate(
        problem_text="동훈이는 찰흙 5.37 kg과 지점토 4.62 kg을 사용하고, 재희는 찰흙 5.89 kg과 지점토 4.36 kg을 사용했습니다. 누가 몇 kg 더 무겁게 사용했는지 구하세요.",
        expression="answer_text=재희, 0.26 kg",
        topic="measurement",
        rule_id="grade4_decimal_round1_art_material_weight_difference",
    ),
}


_GRADE4_DECIMAL_ADD_SUB_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="전체 크기가 1인 모눈종이에서 색칠된 부분의 크기를 분수와 소수로 나타내세요.",
        expression="answer_text=74/100, 0.74",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round2_grid_fraction_decimal",
    ),
    2: ElementaryVisualTemplate(
        problem_text="빈칸에 알맞은 수를 쓰세요. 4의 1/10과 1/100을 소수로 나타내세요.",
        expression="answer_text=0.4, 0.04",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round2_tenth_hundredth_of_4",
    ),
    3: ElementaryVisualTemplate(
        problem_text="소수점 위치가 1/10배씩 변하는 표의 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=7, 0.7, 0.07, 0.007",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round2_place_shift_table_down",
    ),
    4: ElementaryVisualTemplate(
        problem_text="2.037에서 밑줄 친 숫자 7이 나타내는 수를 쓰세요.",
        expression="answer_text=0.007",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round2_place_value_2037",
    ),
    5: ElementaryVisualTemplate(
        problem_text="1이 4개, 0.01이 35개인 수를 구하세요.",
        expression="answer_text=4.35",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round2_decimal_from_unit_counts",
    ),
    6: ElementaryVisualTemplate(
        problem_text="6.9의 1/100배, 0.609의 1000배, 690의 1/1000배, 0.69의 100배, 60.9의 1/10배 중 가장 작은 수를 고르세요.",
        expression="answer_text=①",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round2_smallest_scaled_decimal",
    ),
    7: ElementaryVisualTemplate(
        problem_text="4.304에서 ㉠이 나타내는 수는 ㉡이 나타내는 수의 몇 배인지 구하세요.",
        expression="answer_text=1000 배",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round2_place_value_ratio",
    ),
    8: ElementaryVisualTemplate(
        problem_text="어떤 수의 1/100을 해야 할 것을 잘못하여 10배를 하였더니 837이 되었습니다. 바르게 구하면 얼마입니까?",
        expression="answer_text=0.837",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round2_wrong_times_instead_of_hundredth",
    ),
}


_GRADE4_DECIMAL_ADD_SUB_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="단위 사이의 관계를 바르게 나타낸 것을 고르세요.",
        expression="answer_text=③",
        topic="measurement",
        rule_id="grade4_decimal_round2_correct_unit_relation",
    ),
    2: ElementaryVisualTemplate(
        problem_text="덧셈식 3.□ + □.8 = □2.6에서 □ 안에 알맞은 수를 구하세요.",
        expression="answer_text=8, 8, 1",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round2_vertical_addition_blanks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="0.01이 536개인 수와 0.01이 379개인 수의 합을 구하세요.",
        expression="answer_text=9.15",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round2_hundredth_count_sum",
    ),
    4: ElementaryVisualTemplate(
        problem_text="0.54+1.7, 0.84+0.79, 1.83+1.29, 1.48+0.9의 계산 결과가 큰 것부터 차례대로 기호를 쓰세요.",
        expression="answer_text=다, 라, 가, 나",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round2_addition_order_desc",
    ),
    5: ElementaryVisualTemplate(
        problem_text="집에서 학교까지 1800 m, 학교에서 은행까지 2.36 km, 은행에서 우체국까지 1750 m입니다. 전체 거리를 km로 구하세요.",
        expression="answer_text=5.91 km",
        topic="measurement",
        rule_id="grade4_decimal_round2_mixed_distance_sum",
    ),
    6: ElementaryVisualTemplate(
        problem_text="0.56-0.28과 0.63-0.35의 계산 결과를 비교하여 ○ 안에 알맞은 기호를 쓰세요.",
        expression="answer_text==",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round2_subtraction_compare",
    ),
    7: ElementaryVisualTemplate(
        problem_text="15의 1/10인 수와 1.47의 10배인 수의 차를 구하세요.",
        expression="answer_text=13.2",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round2_decimal_scale_difference",
    ),
    8: ElementaryVisualTemplate(
        problem_text="6.26보다 5.18 작은 수, 8.7보다 7.31 작은 수, 0.27보다 0.13 큰 수 중 가장 큰 수의 기호를 쓰세요.",
        expression="answer_text=나",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round2_largest_expression_choice",
    ),
}


_GRADE4_DECIMAL_ADD_SUB_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="귤 상자는 8.23 kg이고 한라봉 상자는 10.29 kg입니다. 어느 것이 몇 kg 더 무거운지 구하세요.",
        expression="answer_text=한라봉, 2.06 kg",
        topic="measurement",
        rule_id="grade4_decimal_round2_fruit_box_weight_difference",
    ),
    2: ElementaryVisualTemplate(
        problem_text="음료수가 2.7 L 있었습니다. 어제 0.7 L를 마시고 오늘은 어제보다 0.46 L 더 적게 마셨습니다. 남은 음료수는 몇 L입니까?",
        expression="answer_text=1.76 L",
        topic="measurement",
        rule_id="grade4_decimal_round2_remaining_drink_liters",
    ),
    3: ElementaryVisualTemplate(
        problem_text="어떤 수에 5.3을 더했더니 8.4가 되었습니다. 어떤 수는 얼마입니까?",
        expression="answer_text=3.1",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round2_unknown_addend_decimal",
    ),
    4: ElementaryVisualTemplate(
        problem_text="카드 ., 3, 6, 8을 모두 한 번씩 사용하여 만들 수 있는 소수 두 자리 수 중 가장 큰 수와 가장 작은 수의 차를 구하세요.",
        expression="answer_text=4.95",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round2_decimal_card_difference",
    ),
}


_GRADE4_DECIMAL_ADD_SUB_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="2708/1000을 소수로 쓰고 읽으세요.",
        expression="answer_text=2.708, 이점칠영팔",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round3_fraction_to_decimal_reading",
    ),
    2: ElementaryVisualTemplate(
        problem_text="2.359에서 9는 어느 자리 숫자이고 얼마를 나타내는지 쓰세요.",
        expression="answer_text=소수 셋째, 0.009",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round3_place_value_2359",
    ),
    3: ElementaryVisualTemplate(
        problem_text="2.45의 10배와 100배를 구하세요.",
        expression="answer_text=24.5, 245",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round3_times_10_100",
    ),
    4: ElementaryVisualTemplate(
        problem_text="1/10배와 10배 관계를 보고 표의 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=0.2, 2, 20, 200, 2000 / 0.05, 0.5, 5, 50, 500",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round3_place_shift_table",
    ),
    5: ElementaryVisualTemplate(
        problem_text="10이 21개, 1이 8개, 0.1이 5개, 0.01이 34개인 수는 얼마입니까?",
        expression="answer_text=218.84",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round3_decimal_from_unit_counts",
    ),
    6: ElementaryVisualTemplate(
        problem_text="어떤 수의 1/10은 0.098입니다. 어떤 수를 구하세요.",
        expression="answer_text=0.98",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round3_unknown_from_tenth",
    ),
    7: ElementaryVisualTemplate(
        problem_text="12.641에서 ㉠이 나타내는 수는 ㉡이 나타내는 수의 몇 배인지 구하세요.",
        expression="answer_text=10000 배",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round3_place_value_ratio",
    ),
    8: ElementaryVisualTemplate(
        problem_text="0.079의 10배, 7의 1/10배, 98의 1/100배, 0.008의 100배, 799의 1/1000배 중 가장 큰 수를 고르세요.",
        expression="answer_text=③",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round3_largest_scaled_decimal",
    ),
}


_GRADE4_DECIMAL_ADD_SUB_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="단위 사이의 관계를 잘못 나타낸 것을 고르세요.",
        expression="answer_text=④",
        topic="measurement",
        rule_id="grade4_decimal_round3_wrong_unit_relation",
    ),
    2: ElementaryVisualTemplate(
        problem_text="3.56+3.21, 4.36+2.52, 2.35+4.13 중 계산 결과가 가장 작은 것의 기호를 쓰세요.",
        expression="answer_text=다",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round3_smallest_addition_choice",
    ),
    3: ElementaryVisualTemplate(
        problem_text="2.63+5.88=□+2.63에서 □ 안에 알맞은 수를 쓰세요.",
        expression="answer_text=5.88",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round3_addition_commutative_blank",
    ),
    4: ElementaryVisualTemplate(
        problem_text="0.82에서 1.35를 더하고 0.87을 뺐을 때의 계산 결과를 빈칸에 쓰세요.",
        expression="answer_text=2.17, 1.3",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round3_chain_add_sub",
    ),
    5: ElementaryVisualTemplate(
        problem_text="수직선을 보고 ㉠+㉡의 값을 구하세요.",
        expression="answer_text=3.4",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round3_number_line_sum",
    ),
    6: ElementaryVisualTemplate(
        problem_text="은지네 집에서 학교까지 0.2 km이고 학교에서 공원까지 0.5 km입니다. 은지네 집에서 학교를 지나 공원까지의 거리는 몇 km입니까?",
        expression="answer_text=0.7 km",
        topic="measurement",
        rule_id="grade4_decimal_round3_distance_sum_km",
    ),
    7: ElementaryVisualTemplate(
        problem_text="0.1이 36개인 수와 0.1이 81개인 수의 차를 구하세요.",
        expression="answer_text=4.5",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round3_tenth_count_difference",
    ),
    8: ElementaryVisualTemplate(
        problem_text="철사를 민주가 2.35 m 가지고 있고 동진이는 민주보다 1.08 m 적게 가지고 있습니다. 동진이가 가진 철사의 길이는 몇 m입니까?",
        expression="answer_text=1.27 m",
        topic="measurement",
        rule_id="grade4_decimal_round3_wire_length_difference",
    ),
}


_GRADE4_DECIMAL_ADD_SUB_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="연수의 키는 1.45 m이고 사물함의 높이는 137 cm입니다. 연수의 키는 사물함의 높이보다 몇 m 더 큽니까?",
        expression="answer_text=0.08 m",
        topic="measurement",
        rule_id="grade4_decimal_round3_height_difference_m",
    ),
    2: ElementaryVisualTemplate(
        problem_text="빨간색 공의 무게는 32.45 g이고 노란색 공은 빨간색 공보다 2.57 g 더 가볍습니다. 두 공의 무게의 합은 몇 g입니까?",
        expression="answer_text=62.33 g",
        topic="measurement",
        rule_id="grade4_decimal_round3_ball_weight_sum",
    ),
    3: ElementaryVisualTemplate(
        problem_text="카드 ., 1, 3, 4, 8을 한 번씩 모두 사용하여 40에 가장 가까운 소수 두 자리 수를 만드세요.",
        expression="answer_text=41.38",
        topic="fraction_ratio",
        rule_id="grade4_decimal_round3_card_closest_to_40",
    ),
    4: ElementaryVisualTemplate(
        problem_text="음료수가 3.6 L 있었습니다. 어제 0.6 L를 마시고 오늘은 어제보다 0.38 L 더 적게 마셨습니다. 남아 있는 음료수는 몇 L입니까?",
        expression="answer_text=2.78 L",
        topic="measurement",
        rule_id="grade4_decimal_round3_remaining_drink_liters",
    ),
}


_GRADE4_QUADRILATERAL_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="직선 다에 대한 수선을 찾아 쓰세요.",
        expression="answer_text=직선 가",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_perpendicular_line_to_da",
    ),
    2: ElementaryVisualTemplate(
        problem_text="도형에서 선분 ㄴㄷ에 대한 수선을 고르세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_perpendicular_segment_choice",
    ),
    3: ElementaryVisualTemplate(
        problem_text="직선 가와 나는 서로 수직입니다. ㉠의 크기를 구하세요.",
        expression="answer_text=60°",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_perpendicular_angle",
    ),
    4: ElementaryVisualTemplate(
        problem_text="변 ㅁㄷ이 변 ㄱㄹ과 변 ㄴㄷ에 대한 수선일 때 각 ㄴㄷㄹ의 크기를 구하세요.",
        expression="answer_text=123°",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_parallel_perpendicular_angle",
    ),
    5: ElementaryVisualTemplate(
        problem_text="도형에서 평행한 변은 모두 몇 쌍인지 구하세요.",
        expression="answer_text=4 쌍",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_parallel_side_pairs",
    ),
    6: ElementaryVisualTemplate(
        problem_text="서로 수직인 선분도 있고 평행한 선분도 있는 글자가 아닌 것을 고르세요.",
        expression="answer_text=①",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_letter_parallel_perpendicular",
    ),
}


_GRADE4_QUADRILATERAL_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="직선 가와 직선 나는 서로 평행합니다. 평행선 사이의 거리는 몇 cm입니까?",
        expression="answer_text=5 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_parallel_distance_5cm",
    ),
    2: ElementaryVisualTemplate(
        problem_text="직선 가, 나, 다가 서로 평행할 때 직선 나와 직선 다 사이의 거리는 몇 cm입니까?",
        expression="answer_text=6 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_parallel_distance_between_na_da",
    ),
    3: ElementaryVisualTemplate(
        problem_text="직선 ㄱㄴ에 평행이고 평행선 사이의 거리가 2 cm인 직선은 모두 몇 개 그을 수 있습니까?",
        expression="answer_text=2 개",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_count_parallel_lines_distance_2cm",
    ),
    4: ElementaryVisualTemplate(
        problem_text="사다리꼴을 모두 고르세요.",
        expression="answer_text=②, ③, ⑤",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_trapezoid_choices",
    ),
    5: ElementaryVisualTemplate(
        problem_text="사다리꼴 ㄱㄴㄷㄹ에서 평행선 사이의 거리는 몇 cm입니까?",
        expression="answer_text=6 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_trapezoid_height",
    ),
    6: ElementaryVisualTemplate(
        problem_text="직사각형 모양의 종이를 한 번 접은 다음 자르고 펼쳤을 때 만들어지는 사각형의 이름을 쓰세요.",
        expression="answer_text=사다리꼴",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_cut_paper_shape",
    ),
}


_GRADE4_QUADRILATERAL_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="세 변의 길이의 합이 15 cm인 정삼각형 4개를 겹치지 않게 이어 붙여 만든 정삼각형의 세 변의 길이의 합을 구하세요.",
        expression="answer_text=30 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_equilateral_joined_perimeter",
    ),
    2: ElementaryVisualTemplate(
        problem_text="평행사변형을 모두 고르세요.",
        expression="answer_text=①, ③",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_parallelogram_choices",
    ),
    3: ElementaryVisualTemplate(
        problem_text="평행사변형 ㄱㄴㄷㄹ의 네 변의 길이의 합을 구하세요.",
        expression="answer_text=48 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_parallelogram_perimeter",
    ),
    4: ElementaryVisualTemplate(
        problem_text="사다리꼴에서 변 ㄱㄹ에 평행한 선분 ㄴㅁ을 그었을 때 선분 ㅁㄷ의 길이를 구하세요.",
        expression="answer_text=9 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_trapezoid_parallel_segment_length",
    ),
    5: ElementaryVisualTemplate(
        problem_text="45 cm 철사로 긴 변 5 cm, 짧은 변 3 cm인 평행사변형 2개를 만들고 남은 철사의 길이를 구하세요.",
        expression="answer_text=13 cm",
        topic="measurement",
        rule_id="grade4_quadrilateral_round1_wire_remaining_after_parallelograms",
    ),
    6: ElementaryVisualTemplate(
        problem_text="크기가 다른 직사각형 종이 띠를 겹쳤을 때 ㉠의 크기를 구하세요.",
        expression="answer_text=135°",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_crossed_rectangles_angle",
    ),
}


_GRADE4_QUADRILATERAL_ROUND1_PAGE4: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="평행사변형에서 한 각의 크기가 이웃한 각의 4배일 때 각의 크기를 구하세요.",
        expression="answer_text=36°",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_parallelogram_angle_ratio",
    ),
    2: ElementaryVisualTemplate(
        problem_text="한 변이 16 cm인 정삼각형의 둘레와 마름모의 둘레가 같습니다. 마름모의 한 변의 길이를 구하세요.",
        expression="answer_text=12 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round1_rhombus_side_from_triangle_perimeter",
    ),
}


_GRADE4_QUADRILATERAL_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="직선 가에 대한 수선은 어느 것입니까?",
        expression="answer_text=②",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_perpendicular_to_line_ga",
    ),
    2: ElementaryVisualTemplate(
        problem_text="도형에서 선분 ㄴㄷ에 대한 수선을 찾아 쓰세요.",
        expression="answer_text=선분 ㄱㄹ",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_perpendicular_segment_to_nd",
    ),
    3: ElementaryVisualTemplate(
        problem_text="선분 ㅁㄴ은 선분 ㄹㄴ에 대한 수선입니다. 각 ㅁㄴㄱ의 크기를 구하세요.",
        expression="answer_text=80°",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_perpendicular_angle",
    ),
    4: ElementaryVisualTemplate(
        problem_text="서로 평행한 직선 두 개를 고르세요.",
        expression="answer_text=④, ⑥",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_parallel_lines_choice",
    ),
    5: ElementaryVisualTemplate(
        problem_text="도형에서 변 ㄴㄷ과 평행한 변을 모두 찾으세요.",
        expression="answer_text=③, ⑤, ⑦",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_edges_parallel_to_nd",
    ),
    6: ElementaryVisualTemplate(
        problem_text="도형에서 평행선 사이의 거리는 몇 cm입니까?",
        expression="answer_text=12 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_parallel_distance",
    ),
}


_GRADE4_QUADRILATERAL_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="직선 가, 나, 다가 서로 평행합니다. 직선 가와 직선 다 사이가 14 cm일 때 직선 나와 직선 다 사이의 거리를 구하세요.",
        expression="answer_text=6 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_three_parallel_distance",
    ),
    2: ElementaryVisualTemplate(
        problem_text="변 ㄱㄴ과 변 ㄱㄹ이 서로 수직인 도형에서 평행선 사이의 거리를 구하세요.",
        expression="answer_text=12 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_parallel_distance_in_shape",
    ),
    3: ElementaryVisualTemplate(
        problem_text="네 변, 네 각, 마주 보는 한 쌍의 변이 서로 평행한 도형의 이름을 쓰세요.",
        expression="answer_text=사다리꼴",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_shape_name_trapezoid",
    ),
    4: ElementaryVisualTemplate(
        problem_text="사다리꼴에서 평행선 사이의 거리는 몇 cm입니까?",
        expression="answer_text=12 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_trapezoid_height",
    ),
    5: ElementaryVisualTemplate(
        problem_text="직사각형 모양의 종이를 점선을 따라 잘랐을 때 만들어지는 사각형 중 사다리꼴은 모두 몇 개입니까?",
        expression="answer_text=5 개",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_cut_rectangle_trapezoids",
    ),
    6: ElementaryVisualTemplate(
        problem_text="사다리꼴에서 각 ㄴㄷㄹ의 크기를 구하세요.",
        expression="answer_text=65°",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_trapezoid_angle",
    ),
}


_GRADE4_QUADRILATERAL_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="세 변의 길이의 합이 18 cm인 정삼각형 8개를 겹치지 않게 이어 붙여 만든 평행사변형의 네 변의 길이의 합을 구하세요.",
        expression="answer_text=48 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_triangle_tiling_parallelogram_perimeter",
    ),
    2: ElementaryVisualTemplate(
        problem_text="여러 가지 사각형을 보고 평행한 변의 수에 따라 분류하고 평행사변형을 모두 찾으세요.",
        expression="answer_text=평행한 변이 1쌍: 나, 다, 라 / 평행한 변이 2쌍: 가, 마, 바 / 평행사변형: 가, 마, 바",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_classify_parallel_sides",
    ),
    3: ElementaryVisualTemplate(
        problem_text="평행사변형 ㄱㄴㄷㄹ의 둘레를 구하세요.",
        expression="answer_text=68 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_parallelogram_perimeter",
    ),
    4: ElementaryVisualTemplate(
        problem_text="사다리꼴에서 선분 ㄹㄷ에 평행한 선분 ㅁㄴ을 그으면 선분 ㄱㅁ의 길이는 몇 cm입니까?",
        expression="answer_text=13 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_trapezoid_parallel_segment_length",
    ),
    5: ElementaryVisualTemplate(
        problem_text="두 평행사변형의 네 변의 길이의 합이 같을 때 변 ㄱㄴ의 길이를 구하세요.",
        expression="answer_text=5 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_equal_perimeter_unknown_side",
    ),
}


_GRADE4_QUADRILATERAL_ROUND2_PAGE4: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="마름모에 대한 설명 중 옳지 않은 것을 고르세요.",
        expression="answer_text=④",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_rhombus_wrong_statement",
    ),
    2: ElementaryVisualTemplate(
        problem_text="마름모에서 한 각의 크기가 이웃한 각의 3배일 때 각의 크기를 구하세요.",
        expression="answer_text=45°",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_rhombus_angle_ratio",
    ),
    3: ElementaryVisualTemplate(
        problem_text="마주 보는 변의 길이가 같고 네 각의 크기가 같으며 이웃하는 두 변의 길이가 다른 사각형의 이름을 쓰세요.",
        expression="answer_text=직사각형",
        topic="geometry",
        rule_id="grade4_quadrilateral_round2_rectangle_description",
    ),
}


_GRADE4_QUADRILATERAL_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="직선 가에 수직인 직선은 모두 몇 개입니까?",
        expression="answer_text=3 개",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_count_perpendicular_lines",
    ),
    2: ElementaryVisualTemplate(
        problem_text="수직인 변이 가장 많은 도형을 고르세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_most_perpendicular_sides",
    ),
    3: ElementaryVisualTemplate(
        problem_text="직선 가와 나는 서로 수직입니다. □ 안에 알맞은 각도를 쓰세요.",
        expression="answer_text=40°",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_perpendicular_angle_blank",
    ),
    4: ElementaryVisualTemplate(
        problem_text="변 ㅁㄷ이 변 ㄱㄹ과 변 ㄴㄷ에 대한 수선일 때 각 ㄴㄷㄹ의 크기를 구하세요.",
        expression="answer_text=135°",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_parallel_perpendicular_angle",
    ),
    5: ElementaryVisualTemplate(
        problem_text="직선 가와 평행한 직선을 고르세요.",
        expression="answer_text=④",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_line_parallel_to_ga",
    ),
    6: ElementaryVisualTemplate(
        problem_text="변 ㄱㅇ과 평행한 변을 모두 고르세요.",
        expression="answer_text=②, ④, ⑤",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_parallel_edges_choice",
    ),
}


_GRADE4_QUADRILATERAL_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="평행한 직선 가와 나 사이의 거리는 몇 cm입니까?",
        expression="answer_text=6 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_parallel_lines_distance",
    ),
    2: ElementaryVisualTemplate(
        problem_text="평행선 사이의 거리를 나타내려고 합니다. 점 ㄱ과 어느 점을 이어야 합니까?",
        expression="answer_text=점 ㄹ",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_parallel_lines_perpendicular_point",
    ),
    3: ElementaryVisualTemplate(
        problem_text="도형에서 변 ㄱㄹ과 변 ㄴㄷ은 서로 평행합니다. 평행선 사이의 거리는 몇 cm입니까?",
        expression="answer_text=9 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_trapezoid_parallel_distance",
    ),
    4: ElementaryVisualTemplate(
        problem_text="다음 중 사다리꼴의 특징을 바르게 설명한 것을 고르세요.",
        expression="answer_text=①",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_trapezoid_feature_choice",
    ),
    5: ElementaryVisualTemplate(
        problem_text="직사각형 모양의 종이를 오려 각 조각에 사각형의 이름을 붙이려고 합니다. 사다리꼴은 모두 몇 개입니까?",
        expression="answer_text=6 개",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_cut_rectangle_trapezoids",
    ),
    6: ElementaryVisualTemplate(
        problem_text="사다리꼴에서 각 ㄱ의 크기를 구하세요.",
        expression="answer_text=125°",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_trapezoid_angle",
    ),
}


_GRADE4_QUADRILATERAL_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="세 변의 길이의 합이 6 cm인 정삼각형 8개를 이어 붙여 만든 사다리꼴의 네 변의 길이의 합을 구하세요.",
        expression="answer_text=16 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_triangle_tiling_trapezoid_perimeter",
    ),
    2: ElementaryVisualTemplate(
        problem_text="평행사변형에 대한 설명으로 옳은 것을 모두 고르세요.",
        expression="answer_text=가, 나",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_parallelogram_true_statements",
    ),
    3: ElementaryVisualTemplate(
        problem_text="평행사변형 ㄱㄴㄷㄹ의 네 변의 길이의 합을 구하세요.",
        expression="answer_text=32 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_parallelogram_perimeter",
    ),
    4: ElementaryVisualTemplate(
        problem_text="정사각형과 평행사변형을 맞닿게 붙였을 때 빨간색 선의 길이를 구하세요.",
        expression="answer_text=92 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_square_parallelogram_red_line",
    ),
    5: ElementaryVisualTemplate(
        problem_text="평행사변형에서 각 ㄱ의 크기를 구하세요.",
        expression="answer_text=55°",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_parallelogram_angle",
    ),
    6: ElementaryVisualTemplate(
        problem_text="평행사변형과 마름모를 이어 붙인 도형에서 사각형의 네 변의 길이의 합을 구하세요.",
        expression="answer_text=36 cm",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_parallelogram_rhombus_perimeter",
    ),
}


_GRADE4_QUADRILATERAL_ROUND3_PAGE4: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="마주 보는 두 쌍의 변이 평행하고, 네 변의 길이와 네 각의 크기가 모두 같은 사각형의 이름을 쓰세요.",
        expression="answer_text=정사각형",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_square_properties",
    ),
    2: ElementaryVisualTemplate(
        problem_text="평행사변형과 직사각형을 이어 붙인 도형에서 각 ㄱ의 크기를 구하세요.",
        expression="answer_text=70°",
        topic="geometry",
        rule_id="grade4_quadrilateral_round3_joined_parallelogram_rectangle_angle",
    ),
}


_GRADE5_DIAGNOSTIC_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수를 읽어 보세요.",
        expression="answer_text=육천칠백사만",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round3_read_large_number",
    ),
    2: ElementaryVisualTemplate(
        problem_text="㉠이 나타내는 값은 ㉡이 나타내는 값의 몇 배입니까?",
        expression="answer_text=1000 배",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round3_place_value_ratio",
    ),
    3: ElementaryVisualTemplate(
        problem_text="각도를 비교하여 ○ 안에 >, =, <를 알맞게 써넣으세요.",
        expression="answer_text=>",
        topic="measurement",
        rule_id="grade5_diagnostic_round3_angle_compare",
    ),
    4: ElementaryVisualTemplate(
        problem_text="탁구공은 한 상자에 250개씩 60상자가 있고, 야구공은 한 상자에 145개씩 92상자가 있습니다. 탁구공은 야구공보다 몇 개 더 많습니까?",
        expression="answer_text=1660 개",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round3_ball_count_difference",
    ),
    5: ElementaryVisualTemplate(
        problem_text="몫이 큰 것부터 차례대로 기호를 쓰세요.",
        expression="answer_text=㉡, ㉢, ㉣, ㉠",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round3_order_by_quotient",
    ),
    6: ElementaryVisualTemplate(
        problem_text="수 카드를 아래쪽으로 뒤집고 오른쪽으로 뒤집었을 때 만들어지는 수를 구하세요.",
        expression="answer_text=95",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round3_flip_number_card",
    ),
    7: ElementaryVisualTemplate(
        problem_text="막대그래프에서 세로 눈금 한 칸은 몇 권을 나타냅니까?",
        expression="answer_text=20 권",
        topic="statistics",
        rule_id="grade5_diagnostic_round3_bar_graph_scale",
    ),
}


_GRADE5_DIAGNOSTIC_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="막대그래프에서 2015년의 1인당 쌀 소비량은 2000년보다 몇 kg 줄었습니까?",
        expression="answer_text=30 kg",
        topic="statistics",
        rule_id="grade5_diagnostic_round3_rice_consumption_difference",
    ),
    2: ElementaryVisualTemplate(
        problem_text="빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=3, 3, 510",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round3_consecutive_sum_blanks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="한쪽 모서리에 1명씩 앉을 수 있는 탁자를 한 줄로 붙여 의자를 놓으려고 합니다. 12개의 탁자에 필요한 의자의 개수를 구하세요.",
        expression="answer_text=26 개",
        topic="pattern",
        rule_id="grade5_diagnostic_round3_tables_chairs",
    ),
    4: ElementaryVisualTemplate(
        problem_text="대분수의 덧셈과 뺄셈을 계산하세요.",
        expression="answer_text=6 1/3",
        topic="fraction_ratio",
        rule_id="grade5_diagnostic_round3_mixed_fraction_add_sub",
    ),
    5: ElementaryVisualTemplate(
        problem_text="철사를 이용하여 만들기를 할 때 사용한 철사는 모두 몇 m입니까?",
        expression="answer_text=1 2/9 m",
        topic="fraction_ratio",
        rule_id="grade5_diagnostic_round3_fraction_wire_total",
    ),
    6: ElementaryVisualTemplate(
        problem_text="직사각형 모양의 종이를 점선을 따라 잘랐을 때 만들어지는 예각삼각형은 둔각삼각형보다 몇 개 더 많습니까?",
        expression="answer_text=2 개",
        topic="geometry",
        rule_id="grade5_diagnostic_round3_triangle_count_difference",
    ),
    7: ElementaryVisualTemplate(
        problem_text="0.001이 250개인 수를 소수로 쓰세요.",
        expression="answer_text=0.25",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round3_thousandths_to_decimal",
    ),
}


_GRADE5_DIAGNOSTIC_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="주어진 두 수의 합을 구하세요.",
        expression="answer_text=9.04",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round3_decimal_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="주어진 설명은 어떤 사각형에 대한 설명입니까?",
        expression="answer_text=직사각형",
        topic="geometry",
        rule_id="grade5_diagnostic_round3_rectangle_description",
    ),
    3: ElementaryVisualTemplate(
        problem_text="네 변의 길이의 합이 88 cm인 마름모의 한 변의 길이를 구하세요.",
        expression="answer_text=22 cm",
        topic="geometry",
        rule_id="grade5_diagnostic_round3_rhombus_side_length",
    ),
    4: ElementaryVisualTemplate(
        problem_text="꺾은선그래프에서 온도가 가장 많이 변한 때를 고르세요.",
        expression="answer_text=④",
        topic="statistics",
        rule_id="grade5_diagnostic_round3_line_graph_largest_change",
    ),
    5: ElementaryVisualTemplate(
        problem_text="육각형의 변의 수와 정이십각형의 꼭짓점 수의 합을 구하세요.",
        expression="answer_text=26",
        topic="geometry",
        rule_id="grade5_diagnostic_round3_polygon_vertices_sum",
    ),
    6: ElementaryVisualTemplate(
        problem_text="주어진 설명은 어떤 도형에 대한 설명입니까?",
        expression="answer_text=마름모",
        topic="geometry",
        rule_id="grade5_diagnostic_round3_rhombus_description",
    ),
}


_GRADE5_DIAGNOSTIC_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="보기와 같이 수를 각 자리의 값의 합으로 나타내세요.",
        expression="answer_text=70000, 1000, 600, 80, 4",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round2_place_value_expansion",
    ),
    2: ElementaryVisualTemplate(
        problem_text="21650000은 10000이 몇 개인 수입니까?",
        expression="answer_text=2165",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round2_ten_thousand_units",
    ),
    3: ElementaryVisualTemplate(
        problem_text="주어진 각이 예각, 둔각 중 어느 것인지 각각 쓰세요.",
        expression="answer_text=예각, 둔각, 예각",
        topic="measurement",
        rule_id="grade5_diagnostic_round2_angle_types",
    ),
    4: ElementaryVisualTemplate(
        problem_text="가장 큰 수와 가장 작은 수의 곱을 구하세요.",
        expression="answer_text=31440",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round2_largest_smallest_product",
    ),
    5: ElementaryVisualTemplate(
        problem_text="어떤 수를 57로 나눌 때 나머지가 될 수 없는 수를 고르세요.",
        expression="answer_text=③",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round2_impossible_remainder",
    ),
    6: ElementaryVisualTemplate(
        problem_text="도형을 왼쪽으로 뒤집었을 때의 도형을 그리세요.",
        expression="answer_text=왼쪽으로 뒤집은 도형",
        topic="geometry",
        rule_id="grade5_diagnostic_round2_left_flip_shape",
    ),
    7: ElementaryVisualTemplate(
        problem_text="막대그래프에 대한 설명으로 틀린 것을 고르세요.",
        expression="answer_text=③",
        topic="statistics",
        rule_id="grade5_diagnostic_round2_bar_graph_wrong_statement",
    ),
}


_GRADE5_DIAGNOSTIC_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="막대그래프에서 참가한 학생이 가장 많은 학교와 가장 적은 학교의 참가 학생 수의 차를 구하세요.",
        expression="answer_text=10 명",
        topic="statistics",
        rule_id="grade5_diagnostic_round2_math_contest_bar_graph_difference",
    ),
    2: ElementaryVisualTemplate(
        problem_text="규칙에 따라 계산 결과가 777779가 되는 뺄셈식을 구하세요.",
        expression="answer_text=2000000 - 1222221 = 777779",
        topic="pattern",
        rule_id="grade5_diagnostic_round2_subtraction_pattern",
    ),
    3: ElementaryVisualTemplate(
        problem_text="도형의 배열에서 다섯째 모양의 사각형 수를 구하세요.",
        expression="answer_text=15 개",
        topic="pattern",
        rule_id="grade5_diagnostic_round2_shape_pattern_fifth",
    ),
    4: ElementaryVisualTemplate(
        problem_text="㉠과 ㉡의 차를 구하세요.",
        expression="answer_text=1 7/8",
        topic="fraction_ratio",
        rule_id="grade5_diagnostic_round2_mixed_fraction_difference",
    ),
    5: ElementaryVisualTemplate(
        problem_text="가장 큰 수 카드와 두 번째로 큰 수 카드의 차를 구하세요.",
        expression="answer_text=3/9",
        topic="fraction_ratio",
        rule_id="grade5_diagnostic_round2_fraction_card_difference",
    ),
    6: ElementaryVisualTemplate(
        problem_text="잘못 설명한 것을 찾아 기호를 쓰세요.",
        expression="answer_text=라",
        topic="geometry",
        rule_id="grade5_diagnostic_round2_wrong_triangle_statement",
    ),
}


_GRADE5_DIAGNOSTIC_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="□ 안에 알맞은 수가 다른 하나를 찾아 기호를 쓰세요.",
        expression="answer_text=㉠",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round2_decimal_scale_different",
    ),
    2: ElementaryVisualTemplate(
        problem_text="계산 결과를 비교하여 ○ 안에 >, =, <를 알맞게 써넣으세요.",
        expression="answer_text=<",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round2_decimal_sum_compare",
    ),
    3: ElementaryVisualTemplate(
        problem_text="도형에서 평행선은 모두 몇 쌍입니까?",
        expression="answer_text=4 쌍",
        topic="geometry",
        rule_id="grade5_diagnostic_round2_parallel_line_pairs",
    ),
    4: ElementaryVisualTemplate(
        problem_text="평행사변형의 네 변의 길이의 합이 48 cm일 때 변 ㄱㄹ의 길이를 구하세요.",
        expression="answer_text=15 cm",
        topic="geometry",
        rule_id="grade5_diagnostic_round2_parallelogram_side_length",
    ),
    5: ElementaryVisualTemplate(
        problem_text="꺾은선그래프에 대한 설명으로 잘못된 것을 모두 고르세요.",
        expression="answer_text=③, ④",
        topic="statistics",
        rule_id="grade5_diagnostic_round2_line_graph_wrong_statements",
    ),
    6: ElementaryVisualTemplate(
        problem_text="주어진 도형의 이름을 쓰세요.",
        expression="answer_text=정육각형",
        topic="geometry",
        rule_id="grade5_diagnostic_round2_regular_hexagon_description",
    ),
    7: ElementaryVisualTemplate(
        problem_text="두 다각형의 대각선은 모두 몇 개입니까?",
        expression="answer_text=5 개",
        topic="geometry",
        rule_id="grade5_diagnostic_round2_polygon_diagonal_total",
    ),
}


_GRADE5_DIAGNOSTIC_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="나타내는 값이 700000000인 것을 찾아 기호를 쓰세요.",
        expression="answer_text=㉡",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round1_large_number_place_value",
    ),
    2: ElementaryVisualTemplate(
        problem_text="가장 큰 수를 찾아 기호를 쓰세요.",
        expression="answer_text=㉢",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round1_largest_number_choice",
    ),
    3: ElementaryVisualTemplate(
        problem_text="가장 큰 각을 찾아 기호를 쓰세요.",
        expression="answer_text=㉢",
        topic="measurement",
        rule_id="grade5_diagnostic_round1_largest_angle_choice",
    ),
    4: ElementaryVisualTemplate(
        problem_text="곱의 크기를 비교하여 ○ 안에 >, =, <를 알맞게 써넣으세요.",
        expression="answer_text=>",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round1_product_compare",
    ),
    5: ElementaryVisualTemplate(
        problem_text="어떤 수를 49로 나누었더니 몫이 17이고 나머지가 36이었습니다. 어떤 수를 구하세요.",
        expression="answer_text=869",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round1_division_original_number",
    ),
    6: ElementaryVisualTemplate(
        problem_text="도형을 오른쪽으로 7 cm 밀고 위쪽으로 1 cm 밀었을 때의 도형을 그리세요.",
        expression="answer_text=오른쪽 7 cm, 위쪽 1 cm 이동한 도형",
        topic="geometry",
        rule_id="grade5_diagnostic_round1_translate_shape",
    ),
    7: ElementaryVisualTemplate(
        problem_text="막대그래프에 대한 설명으로 틀린 것을 고르세요.",
        expression="answer_text=④",
        topic="statistics",
        rule_id="grade5_diagnostic_round1_bar_graph_wrong_statement",
    ),
}


_GRADE5_DIAGNOSTIC_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="막대그래프에서 선수 수가 같도록 하려면 가장 많은 선수를 선발해야 하는 대륙을 쓰세요.",
        expression="answer_text=오세아니아",
        topic="statistics",
        rule_id="grade5_diagnostic_round1_continent_bar_graph_minimum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="수 배열표에서 분홍색 칸에 나타난 규칙을 설명할 때 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=1100",
        topic="pattern",
        rule_id="grade5_diagnostic_round1_number_table_diagonal_rule",
    ),
    3: ElementaryVisualTemplate(
        problem_text="도형의 배열에서 여섯 번째에 올 도형의 사각형 개수를 구하세요.",
        expression="answer_text=16 개",
        topic="pattern",
        rule_id="grade5_diagnostic_round1_shape_pattern_sixth",
    ),
    4: ElementaryVisualTemplate(
        problem_text="빈칸에 계산 결과를 쓰세요.",
        expression="answer_text=4 1/8",
        topic="fraction_ratio",
        rule_id="grade5_diagnostic_round1_mixed_fraction_chain",
    ),
    5: ElementaryVisualTemplate(
        problem_text="어떤 수를 더해 4 5/10가 되었을 때 어떤 수를 구하세요.",
        expression="answer_text=2 3/10",
        topic="fraction_ratio",
        rule_id="grade5_diagnostic_round1_fraction_missing_addend",
    ),
    6: ElementaryVisualTemplate(
        problem_text="선분 ㄱㄴ과 한 점을 이어 둔각삼각형을 만들 때 이어야 할 점을 고르세요.",
        expression="answer_text=①",
        topic="geometry",
        rule_id="grade5_diagnostic_round1_obtuse_triangle_point",
    ),
    7: ElementaryVisualTemplate(
        problem_text="두 이등변삼각형에서 ㉠과 ㉡에 알맞은 수의 합을 구하세요.",
        expression="answer_text=18",
        topic="geometry",
        rule_id="grade5_diagnostic_round1_isosceles_triangle_blanks_sum",
    ),
}


_GRADE5_DIAGNOSTIC_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="0.59보다 0.23 큰 수를 구하세요.",
        expression="answer_text=0.82",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round1_decimal_add_description",
    ),
    2: ElementaryVisualTemplate(
        problem_text="㉠이 나타내는 수는 ㉡이 나타내는 수의 몇 배입니까?",
        expression="answer_text=1000 배",
        topic="arithmetic",
        rule_id="grade5_diagnostic_round1_decimal_place_value_ratio",
    ),
    3: ElementaryVisualTemplate(
        problem_text="직선 가에 수직인 직선은 모두 몇 개입니까?",
        expression="answer_text=3 개",
        topic="geometry",
        rule_id="grade5_diagnostic_round1_count_perpendicular_lines",
    ),
    4: ElementaryVisualTemplate(
        problem_text="다음 설명 중에서 틀린 것을 모두 고르세요.",
        expression="answer_text=④, ⑤",
        topic="geometry",
        rule_id="grade5_diagnostic_round1_wrong_shape_statements",
    ),
    5: ElementaryVisualTemplate(
        problem_text="꺾은선그래프에 대한 설명으로 잘못된 것을 모두 고르세요.",
        expression="answer_text=③, ④",
        topic="statistics",
        rule_id="grade5_diagnostic_round1_line_graph_wrong_statements",
    ),
    6: ElementaryVisualTemplate(
        problem_text="다음 중 다각형인 도형으로 짝지어진 것을 고르세요.",
        expression="answer_text=④",
        topic="geometry",
        rule_id="grade5_diagnostic_round1_polygon_pair_choice",
    ),
}


_GRADE5_NATURAL_MIXED_CALC_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="65-(100-88)을 계산하세요.",
        expression="answer_text=53",
        topic="arithmetic",
        rule_id="grade5_natural_mixed_calc_round1_page1_parentheses_subtraction",
    ),
    2: ElementaryVisualTemplate(
        problem_text="45×21÷27÷7을 계산하세요.",
        expression="answer_text=5",
        topic="arithmetic",
        rule_id="grade5_natural_mixed_calc_round1_page1_multiply_divide_chain",
    ),
    3: ElementaryVisualTemplate(
        problem_text="두 식 19-8-2와 19-(8-2)를 계산한 결과의 차를 구하세요.",
        expression="answer_text=4",
        topic="arithmetic",
        rule_id="grade5_natural_mixed_calc_round1_page1_difference_parentheses",
    ),
    4: ElementaryVisualTemplate(
        problem_text="76-12×5+54÷9를 계산하세요.",
        expression="answer_text=22",
        topic="arithmetic",
        rule_id="grade5_natural_mixed_calc_round1_page1_mixed_ops",
    ),
    5: ElementaryVisualTemplate(
        problem_text="6×8+(51-7)÷2를 계산하세요.",
        expression="answer_text=70",
        topic="arithmetic",
        rule_id="grade5_natural_mixed_calc_round1_page1_parentheses_division",
    ),
    6: ElementaryVisualTemplate(
        problem_text="43+7-18과 56-(15+8)의 계산 결과를 비교하세요.",
        expression="answer_text=<",
        topic="arithmetic",
        rule_id="grade5_natural_mixed_calc_round1_page1_compare_results",
    ),
    7: ElementaryVisualTemplate(
        problem_text="47-(15+8)을 바르게 계산한 사람을 고르세요.",
        expression="answer_text=민선",
        topic="arithmetic",
        rule_id="grade5_natural_mixed_calc_round1_page1_correct_calculator",
    ),
    8: ElementaryVisualTemplate(
        problem_text="18÷3×5의 계산 과정을 보고 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=빈칸: 6, 30",
        topic="arithmetic",
        rule_id="grade5_natural_mixed_calc_round1_page1_flow_chart",
    ),
    9: ElementaryVisualTemplate(
        problem_text="괄호를 어느 곳에 넣어 계산하여도 결과가 항상 같은 것을 모두 고르세요.",
        expression="answer_text=②, ④",
        topic="arithmetic",
        rule_id="grade5_natural_mixed_calc_round1_page1_parentheses_invariant",
    ),
}


_GRADE5_NATURAL_MIXED_CALC_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="계산 결과를 찾아 선으로 이어 보세요.",
        expression="answer_text=13+8×6-5→56 / (13+8)×6-5→121 / 13+8×(6-5)→21",
        topic="arithmetic",
        rule_id="grade5_natural_mixed_calc_round1_page2_match_results",
    ),
    2: ElementaryVisualTemplate(
        problem_text="2×3=6, 192÷6=32, 32÷4=8의 계산 과정에 맞는 식을 고르세요.",
        expression="answer_text=나",
        topic="arithmetic",
        rule_id="grade5_natural_mixed_calc_round1_page2_process_expression_choice",
    ),
    3: ElementaryVisualTemplate(
        problem_text="60÷(20÷2)×5보다 큰 가장 작은 자연수를 구하세요.",
        expression="answer_text=31",
        topic="arithmetic",
        rule_id="grade5_natural_mixed_calc_round1_page2_smallest_natural_greater_than",
    ),
    4: ElementaryVisualTemplate(
        problem_text="(14+5)×13-9와 14+5×13-9의 계산 결과의 차를 구하세요.",
        expression="answer_text=168",
        topic="arithmetic",
        rule_id="grade5_natural_mixed_calc_round1_page2_difference_with_parentheses",
    ),
    5: ElementaryVisualTemplate(
        problem_text="계산 결과가 같은 식끼리 이어 보세요.",
        expression="answer_text=(1)-다, (2)-나, (3)-가",
        topic="arithmetic",
        rule_id="grade5_natural_mixed_calc_round1_page2_match_equivalent_expressions",
    ),
    6: ElementaryVisualTemplate(
        problem_text="150 cm 리본에서 70 cm와 45 cm를 사용했습니다. 남은 리본의 길이를 구하세요.",
        expression="answer_text=35 cm",
        topic="measurement",
        rule_id="grade5_natural_mixed_calc_round1_page2_ribbon_remaining",
    ),
    7: ElementaryVisualTemplate(
        problem_text="63에 어떤 수를 더하고 45를 빼야 할 것을 63에서 어떤 수를 빼었더니 34가 되었습니다. 바르게 계산한 값을 구하세요.",
        expression="answer_text=47",
        topic="arithmetic",
        rule_id="grade5_natural_mixed_calc_round1_page2_correct_wrong_operation",
    ),
    8: ElementaryVisualTemplate(
        problem_text="88÷□-4+9=16에서 □ 안에 알맞은 수를 쓰세요.",
        expression="answer_text=8",
        topic="arithmetic",
        rule_id="grade5_natural_mixed_calc_round1_page2_missing_divisor",
    ),
}


_GRADE5_NATURAL_MIXED_CALC_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="한 변이 21 cm인 정사각형과 둘레가 같은 정삼각형의 한 변의 길이를 구하세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade5_natural_mixed_calc_round1_page3_square_triangle_perimeter",
    ),
    2: ElementaryVisualTemplate(
        problem_text="18+45÷9-4=3이 성립하도록 괄호를 표시할 알맞은 곳을 고르세요.",
        expression="answer_text=①",
        topic="arithmetic",
        rule_id="grade5_natural_mixed_calc_round1_page3_parentheses_position",
    ),
    3: ElementaryVisualTemplate(
        problem_text="길이 40 cm인 색 테이프 4장을 겹쳐 이었을 때 전체 길이를 구하세요.",
        expression="answer_text=154 cm",
        topic="measurement",
        rule_id="grade5_natural_mixed_calc_round1_page3_tape_overlap_total_length",
    ),
}


_GRADE6_DIAGNOSTIC_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="36-17+14의 계산 과정에서 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=19, 33, 33",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round3_page1_add_sub_flow",
    ),
    2: ElementaryVisualTemplate(
        problem_text="34와 21의 차에 5를 곱하고 24를 더한 수를 식으로 세우고 계산하세요.",
        expression="answer_text=식: (34-21)×5+24 / 답: 89",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round3_page1_word_expression",
    ),
    3: ElementaryVisualTemplate(
        problem_text="15와 30의 공약수를 작은 수부터 모두 구하세요.",
        expression="answer_text=1, 3, 5, 15",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round3_page1_common_divisors",
    ),
    4: ElementaryVisualTemplate(
        problem_text="77과 49의 최대공약수와 최소공배수를 각각 구하세요.",
        expression="answer_text=7, 539",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round3_page1_gcd_lcm",
    ),
    5: ElementaryVisualTemplate(
        problem_text="누나의 나이와 연도 사이의 대응 관계를 바르게 나타낸 식을 고르세요.",
        expression="answer_text=⑤",
        topic="sequence",
        rule_id="grade6_diagnostic_round3_page1_age_year_relation",
    ),
    6: ElementaryVisualTemplate(
        problem_text="7/15와 9/20을 분모의 최소공배수 60을 공통분모로 하여 통분하세요.",
        expression="answer_text=28/60, 27/60",
        topic="fraction_ratio",
        rule_id="grade6_diagnostic_round3_page1_common_denominator",
    ),
    7: ElementaryVisualTemplate(
        problem_text="18/25와 0.75의 크기를 비교하세요.",
        expression="answer_text=<",
        topic="fraction_ratio",
        rule_id="grade6_diagnostic_round3_page1_fraction_decimal_compare",
    ),
}


_GRADE6_DIAGNOSTIC_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="계산 결과를 찾아 선으로 이어 보세요.",
        expression="answer_text=2 1/6+2 6/7→5 1/42 / 3 5/14+1 1/3→4 29/42",
        topic="fraction_ratio",
        rule_id="grade6_diagnostic_round3_page2_mixed_fraction_match",
    ),
    2: ElementaryVisualTemplate(
        problem_text="계산 결과가 1보다 작은 것의 기호를 쓰세요.",
        expression="answer_text=㉡",
        topic="fraction_ratio",
        rule_id="grade6_diagnostic_round3_page2_fraction_difference_less_than_one",
    ),
    3: ElementaryVisualTemplate(
        problem_text="윗변 6 cm, 아랫변 11 cm, 높이 8 cm인 사다리꼴의 넓이를 구하세요.",
        expression="answer_text=68 cm²",
        topic="geometry",
        rule_id="grade6_diagnostic_round3_page2_trapezoid_area",
    ),
    4: ElementaryVisualTemplate(
        problem_text="24 이하인 수에 모두 ○표 하세요.",
        expression="answer_text=6, 24, 16",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round3_page2_numbers_at_most_24",
    ),
    5: ElementaryVisualTemplate(
        problem_text="올림하여 백의 자리까지 나타낸 수가 잘못된 것의 기호를 쓰세요.",
        expression="answer_text=㉡",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round3_page2_round_up_hundreds_wrong",
    ),
    6: ElementaryVisualTemplate(
        problem_text="ㄱ과 ㄴ의 계산한 값의 차를 구하세요.",
        expression="answer_text=2 3/4",
        topic="fraction_ratio",
        rule_id="grade6_diagnostic_round3_page2_product_difference",
    ),
    7: ElementaryVisualTemplate(
        problem_text="가장 큰 분수와 가장 작은 분수의 곱을 구하세요.",
        expression="answer_text=11 11/12",
        topic="fraction_ratio",
        rule_id="grade6_diagnostic_round3_page2_largest_smallest_mixed_product",
    ),
    8: ElementaryVisualTemplate(
        problem_text="선대칭도형에서 □ 안에 알맞은 수를 쓰세요.",
        expression="answer_text=왼쪽에서부터 5, 90",
        topic="geometry",
        rule_id="grade6_diagnostic_round3_page2_line_symmetric_shape",
    ),
}


_GRADE6_DIAGNOSTIC_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="84×24=2016일 때 84×0.024의 값을 구하세요.",
        expression="answer_text=2.016",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round3_page3_decimal_place_value_product",
    ),
    2: ElementaryVisualTemplate(
        problem_text="5.3×6.1<□<32×1.8에서 □ 안에 들어갈 수 있는 자연수는 모두 몇 개인지 구하세요.",
        expression="answer_text=25 개",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round3_page3_natural_numbers_between_products",
    ),
    3: ElementaryVisualTemplate(
        problem_text="정육면체에 대한 설명으로 틀린 것을 고르세요.",
        expression="answer_text=㉣",
        topic="geometry",
        rule_id="grade6_diagnostic_round3_page3_cube_wrong_statement",
    ),
    4: ElementaryVisualTemplate(
        problem_text="직육면체의 면, 모서리, 꼭짓점의 수의 합을 구하세요.",
        expression="answer_text=26 개",
        topic="geometry",
        rule_id="grade6_diagnostic_round3_page3_rectangular_prism_counts",
    ),
    5: ElementaryVisualTemplate(
        problem_text="일이 일어날 가능성이 확실하다인 경우를 모두 고르세요.",
        expression="answer_text=㉡, ㉣",
        topic="statistics",
        rule_id="grade6_diagnostic_round3_page3_certain_events",
    ),
}


_GRADE6_DIAGNOSTIC_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="(72-23)-9×4+8에서 가장 먼저 계산해야 하는 부분을 찾으세요.",
        expression="answer_text=가",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round2_page1_first_calculation_part",
    ),
    2: ElementaryVisualTemplate(
        problem_text="계산 결과를 찾아 선으로 이어 보세요.",
        expression="answer_text=70÷7-2+5→13 / 70÷7-(2+5)→3 / 70÷(7-2)+5→19",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round2_page1_match_mixed_results",
    ),
    3: ElementaryVisualTemplate(
        problem_text="16과 40의 공약수가 아닌 것을 고르세요.",
        expression="answer_text=④",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round2_page1_not_common_divisor",
    ),
    4: ElementaryVisualTemplate(
        problem_text="35와 14의 최소공배수를 구하고 공배수를 작은 수부터 3개 쓰세요.",
        expression="answer_text=최소공배수: 70 / 공배수: 70, 140, 210",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round2_page1_lcm_and_common_multiples",
    ),
    5: ElementaryVisualTemplate(
        problem_text="도형의 배열을 보고 다음에 이어질 알맞은 모양을 그리세요.",
        expression="answer_text=사각형 5개와 삼각형 5개가 이어진 모양",
        topic="pattern",
        rule_id="grade6_diagnostic_round2_page1_shape_pattern_next",
    ),
    6: ElementaryVisualTemplate(
        problem_text="분모가 48인 진분수 중에서 약분하면 5/8가 되는 분수를 쓰세요.",
        expression="answer_text=30/48",
        topic="fraction_ratio",
        rule_id="grade6_diagnostic_round2_page1_equivalent_fraction_denominator_48",
    ),
    7: ElementaryVisualTemplate(
        problem_text="3/5와 4/7의 크기를 비교하세요.",
        expression="answer_text=>",
        topic="fraction_ratio",
        rule_id="grade6_diagnostic_round2_page1_fraction_compare",
    ),
    8: ElementaryVisualTemplate(
        problem_text="계산 결과가 가장 큰 것을 찾아 기호를 쓰세요.",
        expression="answer_text=㉠",
        topic="fraction_ratio",
        rule_id="grade6_diagnostic_round2_page1_largest_fraction_expression",
    ),
}


_GRADE6_DIAGNOSTIC_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="길이가 각각 1 3/4 m인 색 테이프 3장을 7/16 m씩 겹쳐 이어 붙인 전체 길이를 구하세요.",
        expression="answer_text=4 3/8 m",
        topic="measurement",
        rule_id="grade6_diagnostic_round2_page2_tape_overlap_length",
    ),
    2: ElementaryVisualTemplate(
        problem_text="넓이가 넓은 것부터 차례대로 기호를 쓰세요.",
        expression="answer_text=㉢, ㉠, ㉡",
        topic="geometry",
        rule_id="grade6_diagnostic_round2_page2_area_order",
    ),
    3: ElementaryVisualTemplate(
        problem_text="27 이상 32 미만인 자연수를 모두 쓰세요.",
        expression="answer_text=27, 28, 29, 30, 31",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round2_page2_range_natural_numbers",
    ),
    4: ElementaryVisualTemplate(
        problem_text="6317을 올림하여 천의 자리까지 나타낸 수와 버림하여 십의 자리까지 나타낸 수의 합을 구하세요.",
        expression="answer_text=13310",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round2_page2_rounding_sum",
    ),
    5: ElementaryVisualTemplate(
        problem_text="계산 결과가 같은 것끼리 선으로 이어 보세요.",
        expression="answer_text=2/9×3/8→1/4×1/3 / 4×7/8→5×7/10",
        topic="fraction_ratio",
        rule_id="grade6_diagnostic_round2_page2_match_equal_products",
    ),
    6: ElementaryVisualTemplate(
        problem_text="어떤 수를 9로 나누었더니 1 5/6가 되었습니다. 어떤 수를 구하세요.",
        expression="answer_text=16 1/2",
        topic="fraction_ratio",
        rule_id="grade6_diagnostic_round2_page2_find_original_from_division",
    ),
    7: ElementaryVisualTemplate(
        problem_text="점대칭도형의 둘레를 구하세요.",
        expression="answer_text=40 cm",
        topic="geometry",
        rule_id="grade6_diagnostic_round2_page2_point_symmetric_perimeter",
    ),
    8: ElementaryVisualTemplate(
        problem_text="6.18×㉠=6180, 618×㉡=61.8일 때 ㉠은 ㉡의 몇 배인지 구하세요.",
        expression="answer_text=10000배",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round2_page2_decimal_ratio",
    ),
}


_GRADE6_DIAGNOSTIC_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="가장 큰 수와 가장 작은 수의 곱을 구하세요.",
        expression="answer_text=39.33",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round2_page3_largest_smallest_decimal_product",
    ),
    2: ElementaryVisualTemplate(
        problem_text="직육면체의 모든 모서리 길이의 합을 구하세요.",
        expression="answer_text=64 cm",
        topic="geometry",
        rule_id="grade6_diagnostic_round2_page3_rectangular_prism_edge_sum",
    ),
    3: ElementaryVisualTemplate(
        problem_text="전개도를 접어서 직육면체를 만들었을 때 면 나와 수직인 면이 아닌 것을 고르세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade6_diagnostic_round2_page3_net_not_perpendicular_face",
    ),
    4: ElementaryVisualTemplate(
        problem_text="모둠의 줄넘기 기록 평균이 86회일 때 서아의 줄넘기 기록을 구하세요.",
        expression="answer_text=88회",
        topic="statistics",
        rule_id="grade6_diagnostic_round2_page3_missing_average_value",
    ),
}


_GRADE6_DIAGNOSTIC_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="보기와 같이 계산 순서를 나타내고 53-(10+12)를 계산하세요.",
        expression="answer_text=31",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round1_page1_parentheses_calculation_order",
    ),
    2: ElementaryVisualTemplate(
        problem_text="초콜릿 96개를 세영이네 반 3명씩 8모둠 학생들에게 똑같이 나누어 줄 때 바른 식을 고르세요.",
        expression="answer_text=⑤",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round1_page1_word_expression_choice",
    ),
    3: ElementaryVisualTemplate(
        problem_text="35=1×35, 35=5×7을 보고 빈칸에 알맞은 말을 쓰세요.",
        expression="answer_text=배수, 약수",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round1_page1_multiple_divisor_words",
    ),
    4: ElementaryVisualTemplate(
        problem_text="36=2×2×3×3, 21=3×7을 보고 36과 21의 최소공배수를 구하세요.",
        expression="answer_text=252",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round1_page1_lcm_from_factorization",
    ),
    5: ElementaryVisualTemplate(
        problem_text="도형의 배열을 보고 다음에 이어질 알맞은 모양을 그려 보세요.",
        expression="answer_text=사각형 4개와 원 8개가 이어진 모양",
        topic="pattern",
        rule_id="grade6_diagnostic_round1_page1_shape_pattern_next",
    ),
    6: ElementaryVisualTemplate(
        problem_text="4/5와 크기가 같은 분수를 만들도록 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=8, 15, 16",
        topic="fraction_ratio",
        rule_id="grade6_diagnostic_round1_page1_equivalent_fraction_blanks",
    ),
}


_GRADE6_DIAGNOSTIC_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="3/4과 5/6를 분모의 곱과 분모의 최소공배수를 공통분모로 하여 통분하세요.",
        expression="answer_text=(1) 18/24, 20/24 / (2) 9/12, 10/12",
        topic="fraction_ratio",
        rule_id="grade6_diagnostic_round1_page2_common_denominator_two_ways",
    ),
    2: ElementaryVisualTemplate(
        problem_text="1/3에 2/5를 더하고 5/9를 빼는 계산에서 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=8/45",
        topic="fraction_ratio",
        rule_id="grade6_diagnostic_round1_page2_fraction_flow_blank",
    ),
    3: ElementaryVisualTemplate(
        problem_text="혜진이는 2/7 kg, 경희는 4/9 kg의 귤을 먹었습니다. 먹은 귤은 모두 몇 kg인지 구하세요.",
        expression="answer_text=46/63 kg",
        topic="measurement",
        rule_id="grade6_diagnostic_round1_page2_fraction_weight_sum",
    ),
    4: ElementaryVisualTemplate(
        problem_text="단위를 잘못 나타낸 것을 찾아 기호를 쓰세요.",
        expression="answer_text=㉡",
        topic="measurement",
        rule_id="grade6_diagnostic_round1_page2_wrong_area_unit",
    ),
    5: ElementaryVisualTemplate(
        problem_text="주어진 수 중에서 32 초과인 수를 모두 쓰세요.",
        expression="answer_text=44, 32.7, 40, 35",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round1_page2_numbers_greater_than_32",
    ),
    6: ElementaryVisualTemplate(
        problem_text="5192를 올림, 버림, 반올림하여 백의 자리까지 나타내세요.",
        expression="answer_text=5200, 5100, 5200",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round1_page2_rounding_hundreds",
    ),
    7: ElementaryVisualTemplate(
        problem_text="보기와 같은 방법으로 1 7/8×3을 계산하세요.",
        expression="answer_text=5 5/8",
        topic="fraction_ratio",
        rule_id="grade6_diagnostic_round1_page2_mixed_fraction_multiply",
    ),
}


_GRADE6_DIAGNOSTIC_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="바나나가 한 봉지에 6/7 kg씩 들어 있습니다. 14봉지의 무게를 구하세요.",
        expression="answer_text=12 kg",
        topic="measurement",
        rule_id="grade6_diagnostic_round1_page3_banana_weight_total",
    ),
    2: ElementaryVisualTemplate(
        problem_text="합동인 두 사각형에서 변 ㄴㄷ의 길이를 구하세요.",
        expression="answer_text=5 cm",
        topic="geometry",
        rule_id="grade6_diagnostic_round1_page3_congruent_quadrilateral_side",
    ),
    3: ElementaryVisualTemplate(
        problem_text="계산 결과를 찾아 선으로 이어 보세요.",
        expression="answer_text=0.3×0.27→0.081 / 0.76×0.35→0.266",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round1_page3_decimal_product_match",
    ),
    4: ElementaryVisualTemplate(
        problem_text="1.6×2.9와 1.52×3.4의 계산 결과를 비교하세요.",
        expression="answer_text=<",
        topic="arithmetic",
        rule_id="grade6_diagnostic_round1_page3_decimal_product_compare",
    ),
    5: ElementaryVisualTemplate(
        problem_text="직육면체를 모두 고르세요.",
        expression="answer_text=가, 다, 라",
        topic="geometry",
        rule_id="grade6_diagnostic_round1_page3_rectangular_prisms",
    ),
    6: ElementaryVisualTemplate(
        problem_text="전개도를 접어서 정육면체를 만들었을 때 선분 ㄱㄴ과 겹치는 선분을 고르세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade6_diagnostic_round1_page3_cube_net_matching_edge",
    ),
    7: ElementaryVisualTemplate(
        problem_text="고리 던지기 기록의 평균을 구하세요.",
        expression="answer_text=6회",
        topic="statistics",
        rule_id="grade6_diagnostic_round1_page3_average_ring_toss",
    ),
}


_GRADE4_DIAGNOSTIC_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수민이네 집에서 할머니 댁까지의 거리는 82 km 274 m입니다. 79 km 지점까지 왔을 때 더 가야 할 거리를 m로 구하세요.",
        expression="answer_text=3274 m",
        topic="measurement",
        rule_id="grade4_diagnostic_round3_distance_remaining_meters",
    ),
    2: ElementaryVisualTemplate(
        problem_text="분수는 단위분수가 몇 개인지 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=5, 3, 2",
        topic="fraction_ratio",
        rule_id="grade4_diagnostic_round3_unit_fraction_counts",
    ),
    3: ElementaryVisualTemplate(
        problem_text="색 테이프 전체 길이의 1/4만큼이 7 cm일 때 색 테이프의 전체 길이를 구하세요.",
        expression="answer_text=28 cm",
        topic="measurement",
        rule_id="grade4_diagnostic_round3_tape_total_length",
    ),
    4: ElementaryVisualTemplate(
        problem_text="27, 59, 32, 47 중 가장 큰 수와 가장 작은 수의 곱을 구하세요.",
        expression="answer_text=1593",
        rule_id="grade4_diagnostic_round3_largest_smallest_product",
    ),
    5: ElementaryVisualTemplate(
        problem_text="어떤 수를 7로 나누었을 때 나머지가 될 수 없는 수에 ○표 하세요.",
        expression="answer_text=7 에 ○표",
        rule_id="grade4_diagnostic_round3_impossible_remainder",
    ),
    6: ElementaryVisualTemplate(
        problem_text="수 카드 3, 4, 8 중 두 장을 골라 가장 큰 두 자리 수를 만들고 나머지 한 수로 나눈 몫을 구하세요.",
        expression="answer_text=28",
        rule_id="grade4_diagnostic_round3_largest_two_digit_divide",
    ),
    7: ElementaryVisualTemplate(
        problem_text="반지름과 지름이 주어진 원 중 가장 큰 원을 고르세요.",
        expression="answer_text=④",
        topic="geometry",
        rule_id="grade4_diagnostic_round3_largest_circle_choice",
    ),
    8: ElementaryVisualTemplate(
        problem_text="점 ㄱ, 점 ㄴ은 원의 중심입니다. 선분 ㄱㄴ은 몇 cm인지 구하세요.",
        expression="answer_text=5 cm",
        topic="geometry",
        rule_id="grade4_diagnostic_round3_circle_centers_segment",
    ),
}


_GRADE4_DIAGNOSTIC_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="35의 4/7와 56의 2/□에 알맞은 수를 각각 구하세요.",
        expression="answer_text=㉠ 20, ㉡ 7",
        topic="fraction_ratio",
        rule_id="grade4_diagnostic_round3_fraction_of_number",
    ),
    2: ElementaryVisualTemplate(
        problem_text="대분수와 가분수를 같은 것끼리 선으로 이으세요.",
        expression="answer_text=6 2/7 ↔ 44/7, 46/7 ↔ 6 4/7, 7 1/7 ↔ 50/7",
        topic="fraction_ratio",
        rule_id="grade4_diagnostic_round3_mixed_improper_match",
    ),
    3: ElementaryVisualTemplate(
        problem_text="들이 단위 변환에서 잘못된 것을 모두 고르세요.",
        expression="answer_text=①, ④",
        topic="measurement",
        rule_id="grade4_diagnostic_round3_volume_conversion_wrong_choices",
    ),
    4: ElementaryVisualTemplate(
        problem_text="무게가 다른 하나를 찾아 기호를 쓰세요.",
        expression="answer_text=나",
        topic="measurement",
        rule_id="grade4_diagnostic_round3_weight_difference_choice",
    ),
    5: ElementaryVisualTemplate(
        problem_text="한 달 동안 팔린 종류별 책의 수 그림그래프를 보고 표로 나타내세요.",
        expression="answer_text=소설책 230, 유아 서적 340, 학습지 160, 잡지 250, 합계 980",
        topic="statistics",
        rule_id="grade4_diagnostic_round3_books_table",
    ),
}


_GRADE3_DIAGNOSTIC_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="847에서 밑줄 친 숫자는 얼마를 나타내는지 쓰세요.",
        expression="answer=40",
        rule_id="grade3_diagnostic_round2_underlined_digit_value",
    ),
    2: ElementaryVisualTemplate(
        problem_text="백의 자리 숫자가 9, 십의 자리 숫자가 2, 일의 자리 숫자가 5인 수를 쓰세요.",
        expression="answer=925",
        rule_id="grade3_diagnostic_round2_place_digits_make_number",
    ),
    3: ElementaryVisualTemplate(
        problem_text="오른쪽 그림과 같은 모양의 이름을 쓰세요.",
        expression="answer_text=원",
        topic="geometry",
        rule_id="grade3_diagnostic_round2_circle_shape_name",
    ),
    4: ElementaryVisualTemplate(
        problem_text="47과 9의 합과 차를 각각 구하세요.",
        expression="answer_text=56, 38",
        rule_id="grade3_diagnostic_round2_sum_difference",
    ),
    5: ElementaryVisualTemplate(
        problem_text="빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=81, 18",
        rule_id="grade3_diagnostic_round2_number_machine_blanks",
    ),
    6: ElementaryVisualTemplate(
        problem_text="막대기의 길이는 몇 뼘인지 구하세요.",
        expression="answer_text=3뼘",
        topic="measurement",
        rule_id="grade3_diagnostic_round2_span_length",
    ),
    7: ElementaryVisualTemplate(
        problem_text="5 cm를 나타내지 않는 것을 찾아 ○표 하세요.",
        expression="answer_text=세 번째에 ○표",
        topic="measurement",
        rule_id="grade3_diagnostic_round2_not_5cm_choice",
    ),
}


_GRADE3_DIAGNOSTIC_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="좋아하는 직업 조사표를 보고 가장 적은 직업과 그 수를 구하세요.",
        expression="answer_text=연예인, 3",
        topic="statistics",
        rule_id="grade3_diagnostic_round2_job_table_least",
    ),
    2: ElementaryVisualTemplate(
        problem_text="곱셈식을 보고 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=6, 18",
        rule_id="grade3_diagnostic_round2_multiplication_blanks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="5의 3배를 바르게 나타낸 것이 아닌 것을 찾아 기호를 쓰세요.",
        expression="answer_text=㉢",
        rule_id="grade3_diagnostic_round2_wrong_multiple_expression",
    ),
    4: ElementaryVisualTemplate(
        problem_text="8734를 읽어 보세요.",
        expression="answer_text=팔천칠백삼십사",
        rule_id="grade3_diagnostic_round2_read_8734",
    ),
    5: ElementaryVisualTemplate(
        problem_text="각 자리 수 조건에 맞는 네 자리 수를 쓰세요.",
        expression="answer=7928",
        rule_id="grade3_diagnostic_round2_make_four_digit_number",
    ),
    6: ElementaryVisualTemplate(
        problem_text="시각을 나타내는 것이 아닌 것을 고르세요.",
        expression="answer_text=⑤",
        topic="measurement",
        rule_id="grade3_diagnostic_round2_not_time_choice",
    ),
    7: ElementaryVisualTemplate(
        problem_text="두 곱셈구구의 곱이 같을 때 6×□ = 9×4에서 □ 안에 알맞은 수를 구하세요.",
        expression="answer=6",
        rule_id="grade3_diagnostic_round2_equal_product_blank",
    ),
    8: ElementaryVisualTemplate(
        problem_text="0부터 9까지의 수 중에서 □ 안에 들어갈 수 있는 수를 모두 구하세요.",
        expression="answer=10",
        rule_id="grade3_diagnostic_round2_possible_digit_count",
    ),
}


_GRADE3_DIAGNOSTIC_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="500과 7을 이용해 알맞은 수를 쓰세요.",
        expression="answer_text=500, 7",
        rule_id="grade3_diagnostic_round2_hundreds_and_ones",
    ),
    2: ElementaryVisualTemplate(
        problem_text="시계를 보고 알맞은 시각을 쓰세요.",
        expression="answer_text=5 시 35 분",
        topic="measurement",
        rule_id="grade3_diagnostic_round2_clock_535",
    ),
    3: ElementaryVisualTemplate(
        problem_text="시각을 보고 몇 시 몇 분인지 쓰세요.",
        expression="answer_text=8 시 55 분",
        topic="measurement",
        rule_id="grade3_diagnostic_round2_clock_855",
    ),
    4: ElementaryVisualTemplate(
        problem_text="표를 완성하고 합계를 구하세요.",
        expression="answer_text=3, 2, 3, 4, 12",
        topic="statistics",
        rule_id="grade3_diagnostic_round2_table_complete",
    ),
    5: ElementaryVisualTemplate(
        problem_text="규칙에 따라 다음 모양의 개수를 구하세요.",
        expression="answer_text=7개",
        topic="pattern",
        rule_id="grade3_diagnostic_round2_pattern_next_count",
    ),
}


_GRADE3_DIAGNOSTIC_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="칠백이를 수로 써 보세요.",
        expression="answer=702",
        rule_id="grade3_diagnostic_round1_write_702",
    ),
    2: ElementaryVisualTemplate(
        problem_text="100이 8개, 10이 7개, 1이 1개인 수를 쓰세요.",
        expression="answer=871",
        rule_id="grade3_diagnostic_round1_place_value_871",
    ),
    3: ElementaryVisualTemplate(
        problem_text="삼각형은 모두 몇 개인가요?",
        expression="answer_text=2개",
        topic="geometry",
        rule_id="grade3_diagnostic_round1_count_triangles",
    ),
    4: ElementaryVisualTemplate(
        problem_text="53과 8의 합과 차를 각각 구하세요.",
        expression="answer_text=61, 45",
        rule_id="grade3_diagnostic_round1_sum_difference",
    ),
    5: ElementaryVisualTemplate(
        problem_text="63-7과 48+8의 크기를 비교하여 알맞은 기호를 쓰세요.",
        expression="answer_text==",
        rule_id="grade3_diagnostic_round1_compare_equal_expressions",
    ),
    6: ElementaryVisualTemplate(
        problem_text="나무막대는 손으로 몇 번인지 구하세요.",
        expression="answer_text=5번",
        topic="measurement",
        rule_id="grade3_diagnostic_round1_hand_span_count",
    ),
    7: ElementaryVisualTemplate(
        problem_text="빨간 선의 길이는 몇 cm인지 쓰세요.",
        expression="answer_text=3 cm",
        topic="measurement",
        rule_id="grade3_diagnostic_round1_red_line_length",
    ),
    8: ElementaryVisualTemplate(
        problem_text="구멍이 2개인 단추는 모두 몇 개인가요?",
        expression="answer_text=4개",
        topic="geometry",
        rule_id="grade3_diagnostic_round1_two_hole_button_count",
    ),
}


_GRADE3_DIAGNOSTIC_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="3을 9번 더한 식을 곱셈식으로 나타내세요.",
        expression="answer_text=9, 27",
        rule_id="grade3_diagnostic_round1_repeated_three",
    ),
    2: ElementaryVisualTemplate(
        problem_text="나타내는 수가 작은 것부터 차례로 기호를 쓰세요.",
        expression="answer_text=㉡, ㉢, ㉠",
        rule_id="grade3_diagnostic_round1_order_multiple_expressions",
    ),
    3: ElementaryVisualTemplate(
        problem_text="수 모형이 나타내는 수를 써 보세요.",
        expression="answer=443",
        rule_id="grade3_diagnostic_round1_base_ten_blocks",
    ),
    4: ElementaryVisualTemplate(
        problem_text="더 큰 수에 ○표 하세요.",
        expression="answer_text=오른쪽에 ○표",
        rule_id="grade3_diagnostic_round1_larger_number_choice",
    ),
    5: ElementaryVisualTemplate(
        problem_text="□×8=8, 2×□=2에 공통으로 들어가는 수를 쓰세요.",
        expression="answer=1",
        rule_id="grade3_diagnostic_round1_common_factor_one",
    ),
    6: ElementaryVisualTemplate(
        problem_text="빈칸에 알맞은 수를 써넣어 곱셈표를 완성하세요.",
        expression="answer_text=곱셈표 완성",
        rule_id="grade3_diagnostic_round1_multiplication_table_fill",
    ),
    7: ElementaryVisualTemplate(
        problem_text="5 m는 몇 cm인지 쓰세요.",
        expression="answer=500",
        topic="measurement",
        rule_id="grade3_diagnostic_round1_5m_to_cm",
    ),
    8: ElementaryVisualTemplate(
        problem_text="3 m보다 35 cm 더 긴 길이는 몇 m 몇 cm인지 구하세요.",
        expression="answer_text=3 m 35 cm",
        topic="measurement",
        rule_id="grade3_diagnostic_round1_3m_plus_35cm",
    ),
    9: ElementaryVisualTemplate(
        problem_text="시각을 써 보세요.",
        expression="answer_text=4 시 50 분",
        topic="measurement",
        rule_id="grade3_diagnostic_round1_clock_450",
    ),
}


_GRADE3_DIAGNOSTIC_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="시계가 나타내는 시각에서 20분 후의 시각을 쓰세요.",
        expression="answer_text=10 시 35 분",
        topic="measurement",
        rule_id="grade3_diagnostic_round1_clock_20_minutes_later",
    ),
    2: ElementaryVisualTemplate(
        problem_text="12월 날씨 조사표에서 비가 온 날은 모두 며칠인지 구하세요.",
        expression="answer_text=8일",
        topic="statistics",
        rule_id="grade3_diagnostic_round1_weather_rain_days",
    ),
    3: ElementaryVisualTemplate(
        problem_text="규칙을 찾아 빈칸에 알맞은 모양을 그리고 색칠하세요.",
        expression="answer_text=초록색 삼각형",
        topic="pattern",
        rule_id="grade3_diagnostic_round1_shape_pattern_next",
    ),
}


_SHAPES_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    4: ElementaryVisualTemplate(
        problem_text="상자 모양, 둥근기둥 모양, 공 모양 중에서 가장 적은 모양은 어느 것인지 ○표 하세요.",
        expression="answer_text=상자 모양",
        topic="geometry",
        rule_id="grade1_shapes_round2_least_shape",
    ),
}


_GRADE1_1_SHAPES_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="상자 모양 물건은 모두 몇 개인지 구하세요.",
        expression="answer_text=3개",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_box_count",
    ),
    2: ElementaryVisualTemplate(
        problem_text="둥근기둥 모양 물건은 모두 몇 개인지 구하세요.",
        expression="answer_text=3개",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_cylinder_count",
    ),
    3: ElementaryVisualTemplate(
        problem_text="공 모양 물건은 모두 몇 개인지 구하세요.",
        expression="answer_text=3개",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_sphere_count",
    ),
    4: ElementaryVisualTemplate(
        problem_text="상자 모양, 둥근기둥 모양, 공 모양 중에서 가장 많은 모양을 고르세요.",
        expression="answer_text=상자 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_most_shape",
    ),
    5: ElementaryVisualTemplate(
        problem_text="오른쪽 상자 안의 물건은 어떤 모양인지 알맞은 모양에 ○표 하세요.",
        expression="answer_text=둥근기둥 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_box_hole_shape",
    ),
    6: ElementaryVisualTemplate(
        problem_text="모양이 같은 것끼리 선으로 이어 보세요.",
        expression="answer_text=풍선-공 모양, 음료수 캔-둥근기둥 모양, 휴지상자-상자 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_match_same_shapes",
    ),
    7: ElementaryVisualTemplate(
        problem_text="왼쪽 물건과 같은 모양을 찾아 기호를 쓰세요.",
        expression="answer_text=다",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_same_box_shape_choice",
    ),
    8: ElementaryVisualTemplate(
        problem_text="굴렸을 때 어느 방향으로도 잘 굴러가지 않는 모양의 물건을 쓰세요.",
        expression="answer_text=휴지상자",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_does_not_roll",
    ),
}


_GRADE1_1_SHAPES_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="가와 나 중에서 주어진 물건과 같은 모양끼리 모은 것의 기호를 쓰세요.",
        expression="answer_text=나",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_same_group_as_gift_box",
    ),
    2: ElementaryVisualTemplate(
        problem_text="모양이 같은 것끼리 모은 것을 찾아 기호를 쓰세요.",
        expression="answer_text=가",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_same_shape_group",
    ),
    3: ElementaryVisualTemplate(
        problem_text="같은 모양끼리 선으로 이어 보세요.",
        expression="answer_text=야구공-공 모양, 전자레인지-상자 모양, 롤티슈-둥근기둥 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_match_objects",
    ),
    4: ElementaryVisualTemplate(
        problem_text="그림에서 이용한 모양을 모두 골라 ○표 하세요.",
        expression="answer_text=상자 모양, 둥근기둥 모양, 공 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_used_shapes_all",
    ),
    5: ElementaryVisualTemplate(
        problem_text="오른쪽 상자 안의 물건과 같은 모양의 물건을 고르세요.",
        expression="answer_text=롤티슈",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_same_cylinder_object",
    ),
    6: ElementaryVisualTemplate(
        problem_text="모양을 보고 알맞게 선으로 이어 보세요.",
        expression="answer_text=상자 모양-상자, 둥근기둥 모양-둥근기둥, 공 모양-공",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_match_shapes",
    ),
    7: ElementaryVisualTemplate(
        problem_text="네 개의 퍼즐을 완성했을 때 나오는 모양을 고르세요.",
        expression="answer_text=공 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_puzzle_shape",
    ),
    8: ElementaryVisualTemplate(
        problem_text="보이는 모양을 보고 이 모양에 대해 잘못 설명한 학생의 이름을 쓰세요.",
        expression="answer_text=은아",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_wrong_description",
    ),
}


_GRADE1_1_SHAPES_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="둥근기둥 모양을 모두 몇 개 이용했는지 세어 보세요.",
        expression="answer_text=2개",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_cylinder_used_count",
    ),
    2: ElementaryVisualTemplate(
        problem_text="다음 모양을 만드는 데 이용하지 않은 모양을 고르세요.",
        expression="answer_text=공 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_unused_shape",
    ),
    3: ElementaryVisualTemplate(
        problem_text="그림에서 상자 모양, 둥근기둥 모양, 공 모양을 각각 몇 개 이용했는지 세어 보세요.",
        expression="answer_text=상자 모양 1개, 둥근기둥 모양 4개, 공 모양 2개",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_shape_counts",
    ),
    4: ElementaryVisualTemplate(
        problem_text="다음 모양을 만드는 데 사용한 모양의 개수가 3개인 것을 고르세요.",
        expression="answer_text=공 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round1_shape_count_three",
    ),
}


_GRADE1_1_SHAPES_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="상자 모양 물건은 모두 몇 개인지 구하세요.",
        expression="answer_text=4개",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_box_count",
    ),
    2: ElementaryVisualTemplate(
        problem_text="둥근기둥 모양 물건은 모두 몇 개인지 구하세요.",
        expression="answer_text=1개",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_cylinder_count",
    ),
    3: ElementaryVisualTemplate(
        problem_text="공 모양 물건은 모두 몇 개인지 구하세요.",
        expression="answer_text=2개",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_sphere_count",
    ),
    4: ElementaryVisualTemplate(
        problem_text="상자 모양, 둥근기둥 모양, 공 모양 중에서 가장 적은 모양을 고르세요.",
        expression="answer_text=둥근기둥 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_least_shape",
    ),
    5: ElementaryVisualTemplate(
        problem_text="오른쪽 상자 안의 물건은 어떤 모양인지 알맞은 모양에 ○표 하세요.",
        expression="answer_text=둥근기둥 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_box_hole_shape",
    ),
    6: ElementaryVisualTemplate(
        problem_text="모양이 같은 것끼리 선으로 이어 보세요.",
        expression="answer_text=참치캔-둥근기둥 모양, 농구공-공 모양, 지우개-상자 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_match_same_shapes",
    ),
    7: ElementaryVisualTemplate(
        problem_text="왼쪽 물건과 같은 모양을 찾아 기호를 쓰세요.",
        expression="answer_text=나",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_same_sphere_choice",
    ),
}


_GRADE1_1_SHAPES_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="둥근 부분이 있으면서 어느 방향으로도 잘 굴러가는 모양의 물건을 쓰세요.",
        expression="answer_text=축구공",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_rolls_well_object",
    ),
    2: ElementaryVisualTemplate(
        problem_text="가와 나 중에서 주어진 물건과 같은 모양끼리 모은 것의 기호를 쓰세요.",
        expression="answer_text=나",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_same_group_as_glue",
    ),
    3: ElementaryVisualTemplate(
        problem_text="모양이 같은 것끼리 모은 것을 찾아 기호를 쓰세요.",
        expression="answer_text=나",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_same_shape_group",
    ),
    4: ElementaryVisualTemplate(
        problem_text="같은 모양끼리 선으로 이어 보세요.",
        expression="answer_text=상자-상자 모양, 원기둥-둥근기둥 모양, 공-공 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_match_shapes",
    ),
    5: ElementaryVisualTemplate(
        problem_text="그림에서 이용한 모양을 모두 골라 ○표 하세요.",
        expression="answer_text=상자 모양, 둥근기둥 모양, 공 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_used_shapes_all",
    ),
    6: ElementaryVisualTemplate(
        problem_text="오른쪽 상자 안의 물건과 같은 모양의 물건을 고르세요.",
        expression="answer_text=선물상자",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_same_box_object",
    ),
    7: ElementaryVisualTemplate(
        problem_text="모양을 보고 알맞게 선으로 이어 보세요.",
        expression="answer_text=상자 모양-상자, 둥근기둥 모양-둥근기둥, 공 모양-공",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_match_shape_pictures",
    ),
    8: ElementaryVisualTemplate(
        problem_text="네 개의 퍼즐을 완성했을 때 나오는 모양을 고르세요.",
        expression="answer_text=상자 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_puzzle_shape",
    ),
}


_GRADE1_1_SHAPES_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="보이는 모양을 보고 이 모양에 대해 잘못 설명한 학생의 이름을 쓰세요.",
        expression="answer_text=동준",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_wrong_description",
    ),
    2: ElementaryVisualTemplate(
        problem_text="상자 모양을 모두 몇 개 이용했는지 세어 보세요.",
        expression="answer_text=2개",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_box_used_count",
    ),
    3: ElementaryVisualTemplate(
        problem_text="다음 모양을 만드는 데 이용하지 않은 모양을 고르세요.",
        expression="answer_text=공 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_unused_shape",
    ),
    4: ElementaryVisualTemplate(
        problem_text="그림에서 상자 모양, 둥근기둥 모양, 공 모양을 각각 몇 개 이용했는지 세어 보세요.",
        expression="answer_text=상자 모양 1개, 둥근기둥 모양 4개, 공 모양 2개",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_shape_counts",
    ),
    5: ElementaryVisualTemplate(
        problem_text="다음 모양을 만드는 데 사용한 모양의 개수가 4개인 것을 고르세요.",
        expression="answer_text=둥근기둥 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round2_shape_count_four",
    ),
}


_GRADE1_1_SHAPES_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="상자 모양 물건은 모두 몇 개인지 구하세요.",
        expression="answer_text=2개",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_box_count",
    ),
    2: ElementaryVisualTemplate(
        problem_text="둥근기둥 모양 물건은 모두 몇 개인지 구하세요.",
        expression="answer_text=2개",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_cylinder_count",
    ),
    3: ElementaryVisualTemplate(
        problem_text="공 모양 물건은 모두 몇 개인지 구하세요.",
        expression="answer_text=2개",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_sphere_count",
    ),
    4: ElementaryVisualTemplate(
        problem_text="상자 모양, 둥근기둥 모양, 공 모양 중에서 가장 적은 모양을 고르세요.",
        expression="answer_text=공 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_least_shape",
    ),
    5: ElementaryVisualTemplate(
        problem_text="오른쪽 상자 안의 물건은 어떤 모양인지 알맞은 모양에 ○표 하세요.",
        expression="answer_text=상자 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_box_hole_shape",
    ),
    6: ElementaryVisualTemplate(
        problem_text="모양이 같은 것끼리 선으로 이어 보세요.",
        expression="answer_text=축구공-공 모양, 동화책-상자 모양, 통-둥근기둥 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_match_same_shapes",
    ),
    7: ElementaryVisualTemplate(
        problem_text="왼쪽 물건과 같은 모양을 찾아 기호를 쓰세요.",
        expression="answer_text=가",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_same_cylinder_choice",
    ),
}


_GRADE1_1_SHAPES_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="잘 쌓을 수 있고 잘 굴러가지 않는 모양의 물건을 쓰세요.",
        expression="answer_text=휴지상자",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_stack_not_roll_object",
    ),
    2: ElementaryVisualTemplate(
        problem_text="가와 나 중에서 주어진 물건과 같은 모양끼리 모은 것의 기호를 쓰세요.",
        expression="answer_text=가",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_same_group_as_watermelon",
    ),
    3: ElementaryVisualTemplate(
        problem_text="모양이 같은 것끼리 모은 것을 찾아 기호를 쓰세요.",
        expression="answer_text=나",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_same_shape_group",
    ),
    4: ElementaryVisualTemplate(
        problem_text="같은 모양끼리 선으로 이어 보세요.",
        expression="answer_text=풍선-공 모양, 음료수 캔-둥근기둥 모양, 휴지상자-상자 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_match_shapes",
    ),
    5: ElementaryVisualTemplate(
        problem_text="그림에서 이용한 모양을 모두 골라 ○표 하세요.",
        expression="answer_text=상자 모양, 둥근기둥 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_used_shapes",
    ),
    6: ElementaryVisualTemplate(
        problem_text="오른쪽 상자 안의 물건과 같은 모양의 물건을 고르세요.",
        expression="answer_text=연필꽂이",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_same_cylinder_object",
    ),
    7: ElementaryVisualTemplate(
        problem_text="모양을 보고 알맞게 선으로 이어 보세요.",
        expression="answer_text=상자 모양-상자, 둥근기둥 모양-둥근기둥, 공 모양-공",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_match_shape_pictures",
    ),
    8: ElementaryVisualTemplate(
        problem_text="네 개의 퍼즐을 완성했을 때 나오는 모양을 고르세요.",
        expression="answer_text=상자 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_puzzle_shape",
    ),
}


_GRADE1_1_SHAPES_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="보이는 모양을 보고 이 모양에 대해 잘못 설명한 학생의 이름을 쓰세요.",
        expression="answer_text=찬우",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_wrong_description",
    ),
    2: ElementaryVisualTemplate(
        problem_text="공 모양을 모두 몇 개 이용했는지 세어 보세요.",
        expression="answer_text=3개",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_sphere_used_count",
    ),
    3: ElementaryVisualTemplate(
        problem_text="다음 모양을 만드는 데 이용하지 않은 모양을 고르세요.",
        expression="answer_text=공 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_unused_shape",
    ),
    4: ElementaryVisualTemplate(
        problem_text="그림에서 상자 모양, 둥근기둥 모양, 공 모양을 각각 몇 개 이용했는지 세어 보세요.",
        expression="answer_text=상자 모양 1개, 둥근기둥 모양 5개, 공 모양 4개",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_shape_counts",
    ),
    5: ElementaryVisualTemplate(
        problem_text="다음 모양을 만드는 데 사용한 모양의 개수가 4개인 것을 고르세요.",
        expression="answer_text=둥근기둥 모양",
        topic="geometry",
        rule_id="grade1_1_shapes_round3_shape_count_four",
    ),
}


_GRADE1_2_SHAPES_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="○ 모양을 모두 색칠하고, □ 모양이 아닌 카드를 찾으세요.",
        expression="answer_text=1번: ○ 모양 2개 색칠 / 2번: 세모 모양 카드",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page1_circle_and_non_square_card",
    ),
    2: ElementaryVisualTemplate(
        problem_text="왼쪽과 같은 모양의 물건을 찾아 ○표 하세요.",
        expression="answer_text=옷걸이",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page1_matching_triangle_object",
    ),
    3: ElementaryVisualTemplate(
        problem_text="각 모양의 개수를 써 보세요.",
        expression="answer_text=□ 2개, △ 2개, ○ 2개",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page1_shape_counts",
    ),
    4: ElementaryVisualTemplate(
        problem_text="그림에서 □ 모양은 모두 몇 개인지 구하세요.",
        expression="answer=2",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page1_square_count",
    ),
    5: ElementaryVisualTemplate(
        problem_text="가장 많은 모양은 어느 것인지 고르세요.",
        expression="answer_text=□ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page1_most_common_shape",
    ),
    6: ElementaryVisualTemplate(
        problem_text="모양 조각 중 ○ 모양은 몇 개인지 구하세요.",
        expression="answer=5",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page1_circle_piece_count",
    ),
}


_GRADE1_2_SHAPES_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="모양이 나머지와 다른 하나에 ○표 하세요.",
        expression="answer_text=주차금지 표지판",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page2_different_circle_object",
    ),
    2: ElementaryVisualTemplate(
        problem_text="같은 모양끼리 모은 것입니다. 잘못 모은 곳에 ○표 하세요.",
        expression="answer_text=첫 번째 묶음",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page2_wrong_group",
    ),
    3: ElementaryVisualTemplate(
        problem_text="찰흙에 찍었을 때 ○ 모양이 나오는 것을 찾으세요.",
        expression="answer_text=원기둥",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page2_circle_stamp",
    ),
    4: ElementaryVisualTemplate(
        problem_text="뾰족한 곳이 모두 4군데인 모양을 고르세요.",
        expression="answer_text=□ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page2_four_corners",
    ),
    5: ElementaryVisualTemplate(
        problem_text="뾰족한 곳이 있고 편평한 선이 모두 3군데인 모양을 고르세요.",
        expression="answer_text=△ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page2_three_sides",
    ),
    6: ElementaryVisualTemplate(
        problem_text="본뜬 모양이 다른 하나를 찾아 ○표 하세요.",
        expression="answer_text=가운데 물건",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page2_different_traced_face",
    ),
    7: ElementaryVisualTemplate(
        problem_text="본뜬 모양을 찾으세요.",
        expression="answer_text=□ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page2_traced_square",
    ),
    8: ElementaryVisualTemplate(
        problem_text="△ 모양의 특징을 알맞게 이야기한 친구의 이름을 쓰세요.",
        expression="answer_text=혜진",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page2_triangle_feature_speaker",
    ),
    9: ElementaryVisualTemplate(
        problem_text="어떤 모양의 부분을 나타낸 그림인지 알맞은 모양을 찾으세요.",
        expression="answer_text=○ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page2_partial_circle",
    ),
}


_GRADE1_2_SHAPES_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="점선을 따라 자르면 △ 모양은 □ 모양보다 몇 개 더 많은지 구하세요.",
        expression="answer=2",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page3_triangle_square_difference",
    ),
    2: ElementaryVisualTemplate(
        problem_text="□, △, ○ 모양 중 한 가지 모양만 이용해 꾸민 모양에서 이용한 모양을 찾으세요.",
        expression="answer_text=△ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page3_single_shape_used",
    ),
    3: ElementaryVisualTemplate(
        problem_text="이용한 모양을 고르세요.",
        expression="answer_text=△ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page3_single_shape_option",
    ),
    4: ElementaryVisualTemplate(
        problem_text="모양을 꾸미는 데 □ 모양을 몇 개 이용했는지 세어 보세요.",
        expression="answer=5",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page3_square_shape_count",
    ),
    5: ElementaryVisualTemplate(
        problem_text="주어진 모양을 모두 이용하여 꾸민 모양을 찾으세요.",
        expression="answer_text=오른쪽 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round1_page3_uses_all_given_shapes",
    ),
}


_GRADE1_2_SHAPES_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="□ 모양을 모두 찾아 색칠하세요.",
        expression="answer_text=□ 모양 2개 색칠",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page1_square_color",
    ),
    2: ElementaryVisualTemplate(
        problem_text="○ 모양에 ○표 하세요.",
        expression="answer_text=시디",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page1_circle_object",
    ),
    3: ElementaryVisualTemplate(
        problem_text="왼쪽과 같은 모양의 물건을 찾아 ○표 하세요.",
        expression="answer_text=자석",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page1_matching_square_object",
    ),
    4: ElementaryVisualTemplate(
        problem_text="각 모양의 개수를 써 보세요.",
        expression="answer_text=□ 2개, △ 3개, ○ 1개",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page1_shape_counts",
    ),
    5: ElementaryVisualTemplate(
        problem_text="그림에서 △ 모양은 모두 몇 개인지 구하세요.",
        expression="answer=3",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page1_triangle_count",
    ),
    6: ElementaryVisualTemplate(
        problem_text="가장 많은 모양은 어느 것인지 고르세요.",
        expression="answer_text=○ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page1_most_common_shape",
    ),
    7: ElementaryVisualTemplate(
        problem_text="모양 조각 중 □ 모양은 몇 개인지 구하세요.",
        expression="answer=4",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page1_square_piece_count",
    ),
}


_GRADE1_2_SHAPES_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="모양이 나머지와 다른 하나에 ○표 하세요.",
        expression="answer_text=동화책",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page2_different_rectangle_object",
    ),
    2: ElementaryVisualTemplate(
        problem_text="같은 모양끼리 모은 것입니다. 잘못 모은 곳에 ○표 하세요.",
        expression="answer_text=첫 번째 묶음",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page2_wrong_group",
    ),
    3: ElementaryVisualTemplate(
        problem_text="찰흙에 찍었을 때 □ 모양이 나오는 것을 찾으세요.",
        expression="answer_text=상자",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page2_square_stamp",
    ),
    4: ElementaryVisualTemplate(
        problem_text="뾰족한 곳이 모두 3군데인 모양을 고르세요.",
        expression="answer_text=△ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page2_three_corners",
    ),
    5: ElementaryVisualTemplate(
        problem_text="뾰족한 곳이 없고 둥근 부분이 있는 모양을 고르세요.",
        expression="answer_text=○ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page2_round_part",
    ),
    6: ElementaryVisualTemplate(
        problem_text="고무찰흙에 찍을 때 나오는 모양이 다른 하나를 찾아 ○표 하세요.",
        expression="answer_text=세 번째 물건",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page2_different_stamp_shape",
    ),
    7: ElementaryVisualTemplate(
        problem_text="본뜬 모양을 찾아 보세요.",
        expression="answer_text=□ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page2_traced_square",
    ),
    8: ElementaryVisualTemplate(
        problem_text="□ 모양의 특징을 알맞게 이야기한 친구의 이름을 쓰세요.",
        expression="answer_text=우주",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page2_square_feature_speaker",
    ),
    9: ElementaryVisualTemplate(
        problem_text="어떤 모양의 부분을 나타낸 그림인지 알맞은 모양을 찾으세요.",
        expression="answer_text=△ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page2_partial_triangle",
    ),
}


_GRADE1_2_SHAPES_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="점선을 따라 자르면 △ 모양은 □ 모양보다 몇 개 더 많은지 구하세요.",
        expression="answer=5",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page3_triangle_square_difference",
    ),
    2: ElementaryVisualTemplate(
        problem_text="□, △, ○ 모양 중 한 가지 모양만 이용해 꾸민 모양에서 이용한 모양을 찾으세요.",
        expression="answer_text=○ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page3_single_shape_used",
    ),
    3: ElementaryVisualTemplate(
        problem_text="이용한 모양을 고르세요.",
        expression="answer_text=○ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page3_single_shape_option",
    ),
    4: ElementaryVisualTemplate(
        problem_text="모양을 꾸미는 데 △ 모양을 몇 개 이용했는지 세어 보세요.",
        expression="answer=6",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page3_triangle_shape_count",
    ),
    5: ElementaryVisualTemplate(
        problem_text="주어진 모양을 모두 이용하여 꾸민 모양을 찾으세요.",
        expression="answer_text=오른쪽 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round2_page3_uses_all_given_shapes",
    ),
}


_GRADE1_2_SHAPES_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="○ 모양에 ○표 하세요.",
        expression="answer_text=동전",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page1_circle_object",
    ),
    2: ElementaryVisualTemplate(
        problem_text="△ 모양을 모두 찾아 색칠하고, □ 모양에 ○표 하세요.",
        expression="answer_text=2번: △ 모양 2개 색칠 / 3번: 첫 번째 물건",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page1_triangle_color_and_square_mark",
    ),
    3: ElementaryVisualTemplate(
        problem_text="왼쪽과 같은 모양의 물건을 찾아 ○표 하세요.",
        expression="answer_text=동전",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page1_matching_circle_object",
    ),
    4: ElementaryVisualTemplate(
        problem_text="각 모양의 개수를 써 보세요.",
        expression="answer_text=□ 1개, △ 2개, ○ 3개",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page1_shape_counts",
    ),
    5: ElementaryVisualTemplate(
        problem_text="그림에서 ○ 모양은 모두 몇 개인지 구하세요.",
        expression="answer=3",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page1_circle_count",
    ),
    6: ElementaryVisualTemplate(
        problem_text="모양 조각 중 △ 모양은 몇 개인지 구하세요.",
        expression="answer=2",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page1_triangle_piece_count",
    ),
}


_GRADE1_2_SHAPES_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="모양이 나머지와 다른 하나에 ○표 하세요.",
        expression="answer_text=시계",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page2_different_circle_object",
    ),
    2: ElementaryVisualTemplate(
        problem_text="같은 모양끼리 모은 것입니다. 잘못 모은 곳에 ○표 하세요.",
        expression="answer_text=세 번째 묶음",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page2_wrong_group",
    ),
    3: ElementaryVisualTemplate(
        problem_text="찰흙에 찍었을 때 △ 모양이 나오는 것을 찾으세요.",
        expression="answer_text=첫 번째 물건",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page2_triangle_stamp",
    ),
    4: ElementaryVisualTemplate(
        problem_text="뾰족한 곳이 없는 모양을 고르세요.",
        expression="answer_text=○ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page2_no_corners",
    ),
    5: ElementaryVisualTemplate(
        problem_text="뾰족한 곳이 있고 편평한 선이 모두 4군데인 모양을 고르세요.",
        expression="answer_text=□ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page2_four_sides",
    ),
    6: ElementaryVisualTemplate(
        problem_text="물감을 묻혀 찍을 때 나오는 모양이 다른 하나를 찾아 ○표 하세요.",
        expression="answer_text=첫 번째 물건",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page2_different_print_shape",
    ),
    7: ElementaryVisualTemplate(
        problem_text="본뜬 모양을 찾아 보세요.",
        expression="answer_text=○ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page2_traced_circle",
    ),
    8: ElementaryVisualTemplate(
        problem_text="○ 모양의 특징을 알맞게 이야기한 친구의 이름을 쓰세요.",
        expression="answer_text=지훈",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page2_circle_feature_speaker",
    ),
}


_GRADE1_2_SHAPES_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="어떤 모양의 부분을 나타낸 그림인지 알맞은 모양을 찾으세요.",
        expression="answer_text=□ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page3_partial_square",
    ),
    2: ElementaryVisualTemplate(
        problem_text="알맞은 모양을 고르세요.",
        expression="answer_text=□ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page3_partial_square_option",
    ),
    3: ElementaryVisualTemplate(
        problem_text="점선을 따라 자르면 □ 모양은 △ 모양보다 몇 개 더 많은지 구하세요.",
        expression="answer=3",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page3_square_triangle_difference",
    ),
    4: ElementaryVisualTemplate(
        problem_text="□, △, ○ 모양 중 한 가지 모양만 이용해 꾸민 모양에서 이용한 모양을 찾으세요.",
        expression="answer_text=○ 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page3_single_shape_used",
    ),
    5: ElementaryVisualTemplate(
        problem_text="모양을 꾸미는 데 ○ 모양을 몇 개 이용했는지 세어 보세요.",
        expression="answer=3",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page3_circle_shape_count",
    ),
    6: ElementaryVisualTemplate(
        problem_text="주어진 모양을 모두 이용하여 꾸민 모양을 찾으세요.",
        expression="answer_text=오른쪽 모양",
        topic="geometry",
        rule_id="grade1_2_shapes_round3_page3_uses_all_given_shapes",
    ),
}


_GRADE1_2_CLOCK_PATTERN_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="시각을 읽어 보세요.",
        expression="answer_text=5시",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round1_page1_read_500",
    ),
    2: ElementaryVisualTemplate(
        problem_text="왼쪽 시계가 나타내는 시각을 오른쪽 시계에 나타내세요.",
        expression="answer_text=4시",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round1_page1_draw_400",
    ),
    3: ElementaryVisualTemplate(
        problem_text="규칙에 따라 빈칸에 알맞은 그림을 그리세요.",
        expression="answer_text=귤",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round1_page1_fruit_pattern",
    ),
    4: ElementaryVisualTemplate(
        problem_text="시각을 읽어 보세요.",
        expression="answer_text=1시 30분",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round1_page1_read_130",
    ),
    5: ElementaryVisualTemplate(
        problem_text="왼쪽 시계가 나타내는 시각을 오른쪽 시계에 나타내세요.",
        expression="answer_text=2시 30분",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round1_page1_draw_230",
    ),
    6: ElementaryVisualTemplate(
        problem_text="규칙에 따라 빈칸에 알맞은 그림을 그리세요.",
        expression="answer_text=윗줄: 삼각형, 별 / 아랫줄: 별, 삼각형",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round1_page1_shape_grid_pattern",
    ),
    7: ElementaryVisualTemplate(
        problem_text="1시 30분을 나타내는 시계에 ○표 하세요.",
        expression="answer_text=오른쪽 시계",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round1_page1_choose_130",
    ),
    8: ElementaryVisualTemplate(
        problem_text="시계의 긴바늘이 한 바퀴 움직였을 때의 시각을 써 보세요.",
        expression="answer_text=1시",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round1_page1_one_hour_later",
    ),
}


_GRADE1_2_CLOCK_PATTERN_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="규칙에 따라 검은색 바둑돌과 흰색 바둑돌을 놓았습니다. 빈칸의 바둑돌은 무슨 색인지 구하세요.",
        expression="answer_text=검은색",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round1_page2_stone_pattern",
    ),
    2: ElementaryVisualTemplate(
        problem_text="거울에 비친 시계가 나타내는 시각을 써 보세요.",
        expression="answer_text=2시",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round1_page2_mirror_clock_200",
    ),
    3: ElementaryVisualTemplate(
        problem_text="시작한 시각과 끝난 시각을 각각 시계에 나타내세요.",
        expression="answer_text=시작: 7시 30분 / 끝: 9시",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round1_page2_start_end_times",
    ),
    4: ElementaryVisualTemplate(
        problem_text="규칙에 따라 빈칸에 알맞은 주사위를 그리고 수를 써넣으세요.",
        expression="answer_text=주사위: 3, 3 / 수: 3, 3",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round1_page2_dice_pattern",
    ),
    5: ElementaryVisualTemplate(
        problem_text="지금 시각은 6시 30분입니다. 시계의 긴바늘이 가리키는 숫자는 무엇입니까?",
        expression="answer=6",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round1_page2_minute_hand_number",
    ),
    6: ElementaryVisualTemplate(
        problem_text="규칙에 따라 빈칸에 색칠해 보세요.",
        expression="answer_text=초록색, 노란색, 노란색",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round1_page2_color_pattern",
    ),
    7: ElementaryVisualTemplate(
        problem_text="규칙에 따라 빈칸에 그림을 그리세요.",
        expression="answer_text=위: 왼쪽 위 파란 삼각형, 왼쪽 아래 파란 삼각형 / 아래: 왼쪽 위, 왼쪽 아래가 번갈아 반복",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round1_page2_triangle_tile_pattern",
    ),
    8: ElementaryVisualTemplate(
        problem_text="어떤 모양을 이용하여 만든 규칙적인 무늬인지 찾으세요.",
        expression="answer_text=③",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round1_page2_checker_tile",
    ),
    9: ElementaryVisualTemplate(
        problem_text="규칙에 따라 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=21, 31",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round1_page2_number_pattern_plus_five",
    ),
}


_GRADE1_2_CLOCK_PATTERN_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="규칙에 따라 빈칸에 수를 배열해 보세요.",
        expression="answer_text=13, 16, 19, 22, 25, 28",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round1_page3_plus_three_sequence",
    ),
    2: ElementaryVisualTemplate(
        problem_text="긴바늘이 한 바퀴 움직였을 때 저녁 식사를 끝낸 시각을 쓰세요.",
        expression="answer_text=6시 30분",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round1_page3_dinner_one_hour_later",
    ),
    3: ElementaryVisualTemplate(
        problem_text="색칠한 수에 있는 규칙을 찾아 빈칸에 알맞은 수를 넣으세요.",
        expression="answer=9",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round1_page3_colored_numbers_plus_nine",
    ),
}


_GRADE1_2_CLOCK_PATTERN_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="시각을 읽어 보세요.",
        expression="answer_text=2시",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round2_page1_read_200",
    ),
    2: ElementaryVisualTemplate(
        problem_text="왼쪽 시계가 나타내는 시각을 오른쪽 시계에 나타내세요.",
        expression="answer_text=11시",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round2_page1_draw_1100",
    ),
    3: ElementaryVisualTemplate(
        problem_text="규칙에 따라 빈칸에 알맞은 그림을 그리세요.",
        expression="answer_text=수박",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round2_page1_fruit_pattern",
    ),
    4: ElementaryVisualTemplate(
        problem_text="시각을 읽어 보세요.",
        expression="answer_text=10시 30분",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round2_page1_read_1030",
    ),
    5: ElementaryVisualTemplate(
        problem_text="왼쪽 시계가 나타내는 시각을 오른쪽 시계에 나타내세요.",
        expression="answer_text=5시 30분",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round2_page1_draw_530",
    ),
    6: ElementaryVisualTemplate(
        problem_text="규칙에 따라 빈칸에 알맞은 모양을 그리세요.",
        expression="answer_text=위: 도넛, 도넛 / 아래: 초록 사각형, 빨간 삼각형, 빨간 삼각형, 초록 사각형",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round2_page1_shape_pattern",
    ),
    7: ElementaryVisualTemplate(
        problem_text="11시 30분을 나타내는 시계에 ○표 하세요.",
        expression="answer_text=오른쪽 시계",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round2_page1_choose_1130",
    ),
    8: ElementaryVisualTemplate(
        problem_text="시계의 긴바늘이 한 바퀴 움직였을 때의 시각을 써 보세요.",
        expression="answer_text=10시",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round2_page1_one_hour_later",
    ),
}


_GRADE1_2_CLOCK_PATTERN_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="규칙에 따라 검은색 바둑돌과 흰색 바둑돌을 놓았습니다. 빈칸의 바둑돌은 무슨 색인지 구하세요.",
        expression="answer_text=흰색",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round2_page2_stone_pattern",
    ),
    2: ElementaryVisualTemplate(
        problem_text="거울에 비친 시계가 나타내는 시각을 써 보세요.",
        expression="answer_text=1시 30분",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round2_page2_mirror_clock_130",
    ),
    3: ElementaryVisualTemplate(
        problem_text="시작한 시각과 끝난 시각을 각각 시계에 나타내세요.",
        expression="answer_text=시작: 9시 / 끝: 1시 30분",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round2_page2_start_end_times",
    ),
    4: ElementaryVisualTemplate(
        problem_text="규칙에 따라 빈칸에 알맞은 주사위를 그리고 수를 써넣으세요.",
        expression="answer_text=주사위: 3, 1 / 수: 3, 1",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round2_page2_dice_pattern",
    ),
    5: ElementaryVisualTemplate(
        problem_text="지금 시각은 11시입니다. 시계의 긴바늘이 가리키는 숫자는 무엇입니까?",
        expression="answer=12",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round2_page2_minute_hand_number",
    ),
    6: ElementaryVisualTemplate(
        problem_text="규칙에 따라 빈칸에 색칠해 보세요.",
        expression="answer_text=노란색, 노란색, 노란색",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round2_page2_color_pattern",
    ),
    7: ElementaryVisualTemplate(
        problem_text="규칙에 따라 빈칸에 그림을 그리세요.",
        expression="answer_text=노란 삼각형 무늬를 왼쪽 위, 오른쪽 위가 번갈아 반복",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round2_page2_triangle_tile_pattern",
    ),
    8: ElementaryVisualTemplate(
        problem_text="어떤 모양을 이용하여 만든 규칙적인 무늬인지 찾으세요.",
        expression="answer_text=①",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round2_page2_stripe_tile",
    ),
    9: ElementaryVisualTemplate(
        problem_text="규칙에 따라 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=9, 6",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round2_page2_number_pattern_minus_three",
    ),
}


_GRADE1_2_CLOCK_PATTERN_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="시각을 읽어 보세요.",
        expression="answer_text=8시",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round3_page1_read_800",
    ),
    2: ElementaryVisualTemplate(
        problem_text="왼쪽 시계가 나타내는 시각을 오른쪽 시계에 나타내세요.",
        expression="answer_text=7시",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round3_page1_draw_700",
    ),
    3: ElementaryVisualTemplate(
        problem_text="규칙에 따라 빈칸에 알맞은 그림을 그리세요.",
        expression="answer_text=사과",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round3_page1_fruit_pattern",
    ),
    4: ElementaryVisualTemplate(
        problem_text="시각을 읽어 보세요.",
        expression="answer_text=11시 30분",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round3_page1_read_1130",
    ),
    5: ElementaryVisualTemplate(
        problem_text="왼쪽 시계가 나타내는 시각을 오른쪽 시계에 나타내세요.",
        expression="answer_text=9시 30분",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round3_page1_draw_930",
    ),
    6: ElementaryVisualTemplate(
        problem_text="규칙에 따라 빈칸에 알맞은 모양을 그리세요.",
        expression="answer_text=위: 버섯, 가지, 버섯 / 아래: 분홍 원, 파란 삼각형, 파란 삼각형",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round3_page1_shape_pattern",
    ),
    7: ElementaryVisualTemplate(
        problem_text="6시 30분을 나타내는 시계에 ○표 하세요.",
        expression="answer_text=오른쪽 시계",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round3_page1_choose_630",
    ),
    8: ElementaryVisualTemplate(
        problem_text="시계의 긴바늘이 한 바퀴 움직였을 때의 시각을 써 보세요.",
        expression="answer_text=1시",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round3_page1_one_hour_later",
    ),
    9: ElementaryVisualTemplate(
        problem_text="규칙에 따라 검은색 바둑돌과 흰색 바둑돌을 놓았습니다. 빈칸의 바둑돌은 무슨 색인지 구하세요.",
        expression="answer_text=흰색",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round3_page1_stone_pattern",
    ),
}


_GRADE1_2_CLOCK_PATTERN_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="규칙에 따라 검은색 바둑돌과 흰색 바둑돌을 놓았습니다. 빈칸의 바둑돌은 무슨 색인지 구하세요.",
        expression="answer_text=흰색",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round3_page2_stone_pattern",
    ),
    2: ElementaryVisualTemplate(
        problem_text="거울에 비친 시계가 나타내는 시각을 써 보세요.",
        expression="answer_text=11시 30분",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round3_page2_mirror_clock_1130",
    ),
    3: ElementaryVisualTemplate(
        problem_text="시작한 시각과 끝난 시각을 각각 시계에 나타내세요.",
        expression="answer_text=시작: 5시 30분 / 끝: 7시",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round3_page2_start_end_times",
    ),
    4: ElementaryVisualTemplate(
        problem_text="규칙에 따라 빈칸에 알맞은 주사위를 그리고 수를 써넣으세요.",
        expression="answer_text=주사위: 2, 2 / 수: 2, 2",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round3_page2_dice_pattern",
    ),
    5: ElementaryVisualTemplate(
        problem_text="지금 시각은 9시 30분입니다. 시계의 긴바늘이 가리키는 숫자는 무엇입니까?",
        expression="answer=6",
        topic="measurement",
        rule_id="grade1_2_clock_pattern_round3_page2_minute_hand_number",
    ),
    6: ElementaryVisualTemplate(
        problem_text="규칙에 따라 빈칸에 색칠해 보세요.",
        expression="answer_text=빨간색, 흰색, 빨간색",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round3_page2_color_pattern",
    ),
    7: ElementaryVisualTemplate(
        problem_text="규칙에 따라 빈칸에 그림을 그리세요.",
        expression="answer_text=보라색 삼각형 무늬를 위, 아래가 번갈아 반복",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round3_page2_triangle_tile_pattern",
    ),
    8: ElementaryVisualTemplate(
        problem_text="어떤 모양을 이용하여 만든 규칙적인 무늬인지 찾으세요.",
        expression="answer_text=①",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round3_page2_diagonal_tile",
    ),
}


_GRADE1_2_CLOCK_PATTERN_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="46부터 시작하여 5씩 커지는 규칙에 따라 빈칸에 수를 배열하세요.",
        expression="answer_text=51, 56, 61, 66, 71",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round3_page3_increasing_by_5",
    ),
    4: ElementaryVisualTemplate(
        problem_text="색칠한 수에 있는 규칙을 찾아 빈칸에 알맞은 수를 넣으세요.",
        expression="answer=3",
        topic="pattern",
        rule_id="grade1_2_clock_pattern_round3_page3_colored_numbers_plus_three",
    ),
}


_ADDITION_SUBTRACTION_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림을 보고 2와 3을 모으세요.",
        expression="answer=5",
        rule_id="grade1_add_sub_round1_compose_two_and_three",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그림을 보고 6을 3과 빈칸으로 가르세요.",
        expression="answer=3",
        rule_id="grade1_add_sub_round1_decompose_six",
    ),
    3: ElementaryVisualTemplate(
        problem_text="1과 4를 모으기를 해 보세요.",
        expression="answer=5",
        rule_id="grade1_add_sub_round1_compose_one_and_four",
    ),
    4: ElementaryVisualTemplate(
        problem_text="4를 3과 빈칸으로 가르기를 해 보세요.",
        expression="answer=1",
        rule_id="grade1_add_sub_round1_decompose_four",
    ),
    5: ElementaryVisualTemplate(
        problem_text="그림을 보고 알맞은 덧셈식을 써 보세요.",
        expression="answer_text=2 + 3 = 5",
        rule_id="grade1_add_sub_round1_picture_addition",
    ),
    6: ElementaryVisualTemplate(
        problem_text="덧셈을 해 보세요. 3+5",
        expression="answer=8",
        rule_id="grade1_add_sub_round1_add_three_five",
    ),
    7: ElementaryVisualTemplate(
        problem_text="덧셈식으로 나타내어 보세요. 2 더하기 5는 7과 같습니다.",
        expression="answer_text=2 + 5 = 7",
        rule_id="grade1_add_sub_round1_sentence_to_addition",
    ),
    8: ElementaryVisualTemplate(
        problem_text="위와 아래의 두 수를 모아서 9가 되도록 빈칸을 채우세요.",
        expression="answer_text=빈칸: 3, 7",
        rule_id="grade1_add_sub_round1_make_nine_blanks",
    ),
    9: ElementaryVisualTemplate(
        problem_text="두 수를 모은 수가 가장 큰 것을 찾아 기호를 쓰세요.",
        expression="answer_text=다",
        rule_id="grade1_add_sub_round1_largest_sum_choice",
    ),
}


_ADDITION_SUBTRACTION_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="영준이는 바둑돌 8개를 양손에 나누어 쥐었습니다. 오른손에 5개 쥐었다면 왼손에는 몇 개를 쥐었습니까?",
        expression="answer_text=3개",
        rule_id="grade1_add_sub_round1_split_eight_word_problem",
    ),
    2: ElementaryVisualTemplate(
        problem_text="주희는 초콜릿 9개 중에서 4개를 동생에게 주고 2개를 언니에게 주었습니다. 남은 초콜릿은 몇 개입니까?",
        expression="answer_text=3개",
        rule_id="grade1_add_sub_round1_subtract_two_steps_word_problem",
    ),
    3: ElementaryVisualTemplate(
        problem_text="그림을 보고 알맞은 뺄셈식을 써 보세요.",
        expression="answer_text=7 - 4 = 3",
        rule_id="grade1_add_sub_round1_picture_subtraction",
    ),
    4: ElementaryVisualTemplate(
        problem_text="뺄셈을 해 보세요. 5-3",
        expression="answer=2",
        rule_id="grade1_add_sub_round1_subtract_five_three",
    ),
    5: ElementaryVisualTemplate(
        problem_text="뺄셈식으로 나타내어 보세요. 7 빼기 4는 3과 같습니다.",
        expression="answer_text=7 - 4 = 3",
        rule_id="grade1_add_sub_round1_sentence_to_subtraction",
    ),
    6: ElementaryVisualTemplate(
        problem_text="3장의 수 카드 중에서 가장 큰 수와 가장 작은 수의 합과 차를 각각 구해 보세요.",
        expression="answer_text=합: 6 / 차: 4",
        rule_id="grade1_add_sub_round1_largest_smallest_sum_difference",
    ),
    7: ElementaryVisualTemplate(
        problem_text="계산 결과가 같은 것에 ○표 하세요.",
        expression="answer_text=두 번째, 네 번째",
        rule_id="grade1_add_sub_round1_same_result_choices",
    ),
    8: ElementaryVisualTemplate(
        problem_text="빈칸에 알맞은 수를 써 넣으세요. 6에서 6을 빼고 3을 더합니다.",
        expression="answer_text=빈칸: 0, 3",
        rule_id="grade1_add_sub_round1_operation_path",
    ),
    9: ElementaryVisualTemplate(
        problem_text="수 카드 중에서 3장을 골라 차가 가장 큰 뺄셈식을 만들어 보세요.",
        expression="answer_text=8 - 2 = 6",
        rule_id="grade1_add_sub_round1_largest_difference_cards",
    ),
    10: ElementaryVisualTemplate(
        problem_text="만두를 정국이는 3개 먹고 미경이는 6개 먹었습니다. 미경이는 정국이보다 만두를 몇 개 더 먹었을까요?",
        expression="answer_text=3개",
        rule_id="grade1_add_sub_round1_difference_word_problem",
    ),
    11: ElementaryVisualTemplate(
        problem_text="4명이 타고 있던 열차에서 아무도 내리지 않았습니다. 열차에 몇 명이 남아 있는지 뺄셈식을 만들어 보세요.",
        expression="answer_text=4 - 0 = 4",
        rule_id="grade1_add_sub_round1_subtract_zero_word_problem",
    ),
}


_ADDITION_SUBTRACTION_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림을 보고 4와 3을 모으세요.",
        expression="answer=7",
        rule_id="grade1_add_sub_round2_compose_four_and_three",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그림을 보고 5를 2와 빈칸으로 가르세요.",
        expression="answer=3",
        rule_id="grade1_add_sub_round2_decompose_five",
    ),
    3: ElementaryVisualTemplate(
        problem_text="2와 6을 모으기를 해 보세요.",
        expression="answer=8",
        rule_id="grade1_add_sub_round2_compose_two_and_six",
    ),
    4: ElementaryVisualTemplate(
        problem_text="7을 2와 빈칸으로 가르기를 해 보세요.",
        expression="answer=5",
        rule_id="grade1_add_sub_round2_decompose_seven",
    ),
    5: ElementaryVisualTemplate(
        problem_text="그림을 보고 알맞은 덧셈식을 써 보세요.",
        expression="answer_text=2 + 4 = 6",
        rule_id="grade1_add_sub_round2_picture_addition",
    ),
    6: ElementaryVisualTemplate(
        problem_text="덧셈을 해 보세요. 1+5",
        expression="answer=6",
        rule_id="grade1_add_sub_round2_add_one_five",
    ),
    7: ElementaryVisualTemplate(
        problem_text="덧셈식으로 나타내어 보세요. 2 더하기 6은 8과 같습니다.",
        expression="answer_text=2 + 6 = 8",
        rule_id="grade1_add_sub_round2_sentence_to_addition",
    ),
    8: ElementaryVisualTemplate(
        problem_text="위와 아래의 두 수를 모아서 7이 되도록 빈칸을 채우세요.",
        expression="answer_text=빈칸: 3, 5",
        rule_id="grade1_add_sub_round2_make_seven_blanks",
    ),
    9: ElementaryVisualTemplate(
        problem_text="두 수를 모은 수가 가장 큰 것을 찾아 기호를 쓰세요.",
        expression="answer_text=다",
        rule_id="grade1_add_sub_round2_largest_sum_choice",
    ),
}


_ADDITION_SUBTRACTION_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="만두 6개를 영준이와 영호가 똑같이 나누어 먹으려고 합니다. 영준이가 먹을 수 있는 만두는 몇 개입니까?",
        expression="answer_text=3개",
        rule_id="grade1_add_sub_round2_equal_split_word_problem",
    ),
    2: ElementaryVisualTemplate(
        problem_text="희수는 풍선 7개 중에서 3개를 언니에게 주고 2개를 동생에게 주었습니다. 남은 풍선은 몇 개일까요?",
        expression="answer_text=2개",
        rule_id="grade1_add_sub_round2_subtract_two_steps_word_problem",
    ),
    3: ElementaryVisualTemplate(
        problem_text="그림을 보고 알맞은 뺄셈식을 써 보세요.",
        expression="answer_text=5 - 3 = 2",
        rule_id="grade1_add_sub_round2_picture_subtraction",
    ),
    4: ElementaryVisualTemplate(
        problem_text="뺄셈을 해 보세요. 5-5",
        expression="answer=0",
        rule_id="grade1_add_sub_round2_subtract_five_five",
    ),
    5: ElementaryVisualTemplate(
        problem_text="뺄셈식으로 나타내어 보세요. 8 빼기 4는 4와 같습니다.",
        expression="answer_text=8 - 4 = 4",
        rule_id="grade1_add_sub_round2_sentence_to_subtraction",
    ),
    6: ElementaryVisualTemplate(
        problem_text="3장의 수 카드 중에서 가장 큰 수와 가장 작은 수의 합과 차를 각각 구해 보세요.",
        expression="answer_text=합: 9 / 차: 5",
        rule_id="grade1_add_sub_round2_largest_smallest_sum_difference",
    ),
    7: ElementaryVisualTemplate(
        problem_text="계산 결과가 같은 것에 ○표 하세요.",
        expression="answer_text=첫 번째, 세 번째",
        rule_id="grade1_add_sub_round2_same_result_choices",
    ),
    8: ElementaryVisualTemplate(
        problem_text="빈칸에 알맞은 수를 써 넣으세요. 7에서 6을 빼고 4를 더합니다.",
        expression="answer_text=빈칸: 1, 5",
        rule_id="grade1_add_sub_round2_operation_path",
    ),
    9: ElementaryVisualTemplate(
        problem_text="수 카드 중에서 3장을 골라 차가 가장 큰 뺄셈식을 만들어 보세요.",
        expression="answer_text=8 - 3 = 5",
        rule_id="grade1_add_sub_round2_largest_difference_cards",
    ),
    10: ElementaryVisualTemplate(
        problem_text="사탕을 민수는 2개 먹고 미숙이는 6개 먹었습니다. 미숙이는 민수보다 사탕을 몇 개 더 먹었을까요?",
        expression="answer_text=4개",
        rule_id="grade1_add_sub_round2_difference_word_problem",
    ),
    11: ElementaryVisualTemplate(
        problem_text="6명이 타고 있던 버스에서 아무도 내리지 않았습니다. 버스에 몇 명이 남아 있는지 뺄셈식을 만들어 보세요.",
        expression="answer_text=6 - 0 = 6",
        rule_id="grade1_add_sub_round2_subtract_zero_word_problem",
    ),
}


_ADDITION_SUBTRACTION_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림을 보고 2와 4를 모으세요.",
        expression="answer=6",
        rule_id="grade1_add_sub_round3_compose_two_and_four",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그림을 보고 7을 3과 빈칸으로 가르세요.",
        expression="answer=4",
        rule_id="grade1_add_sub_round3_decompose_seven",
    ),
    3: ElementaryVisualTemplate(
        problem_text="3과 2를 모으기를 해 보세요.",
        expression="answer=5",
        rule_id="grade1_add_sub_round3_compose_three_and_two",
    ),
    4: ElementaryVisualTemplate(
        problem_text="5를 1과 빈칸으로 가르기를 해 보세요.",
        expression="answer=4",
        rule_id="grade1_add_sub_round3_decompose_five",
    ),
    5: ElementaryVisualTemplate(
        problem_text="그림을 보고 알맞은 덧셈식을 써 보세요.",
        expression="answer_text=1 + 3 = 4",
        rule_id="grade1_add_sub_round3_picture_addition",
    ),
    6: ElementaryVisualTemplate(
        problem_text="덧셈을 해 보세요. 2+4",
        expression="answer=6",
        rule_id="grade1_add_sub_round3_add_two_four",
    ),
    7: ElementaryVisualTemplate(
        problem_text="덧셈식으로 나타내어 보세요. 3 더하기 5는 8과 같습니다.",
        expression="answer_text=3 + 5 = 8",
        rule_id="grade1_add_sub_round3_sentence_to_addition",
    ),
    8: ElementaryVisualTemplate(
        problem_text="위와 아래의 두 수를 모아서 5가 되도록 빈칸을 채우세요.",
        expression="answer_text=빈칸: 2, 3",
        rule_id="grade1_add_sub_round3_make_five_blanks",
    ),
    9: ElementaryVisualTemplate(
        problem_text="두 수를 모은 수가 가장 작은 것을 찾아 기호를 쓰세요.",
        expression="answer_text=나",
        rule_id="grade1_add_sub_round3_smallest_sum_choice",
    ),
}


_ADDITION_SUBTRACTION_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="희선이는 연필 9자루 중에서 5자루를 동생에게 주었습니다. 남은 연필은 몇 자루입니까?",
        expression="answer_text=4자루",
        rule_id="grade1_add_sub_round3_subtract_pencils_word_problem",
    ),
    2: ElementaryVisualTemplate(
        problem_text="영철이는 연필 9자루 중에서 3자루를 동준이에게 주고 2자루는 민준이에게 주었습니다. 남은 연필은 몇 자루일까요?",
        expression="answer_text=4자루",
        rule_id="grade1_add_sub_round3_subtract_two_steps_word_problem",
    ),
    3: ElementaryVisualTemplate(
        problem_text="그림을 보고 알맞은 뺄셈식을 써 보세요.",
        expression="answer_text=4 - 2 = 2",
        rule_id="grade1_add_sub_round3_picture_subtraction",
    ),
    4: ElementaryVisualTemplate(
        problem_text="뺄셈을 해 보세요. 6-3",
        expression="answer=3",
        rule_id="grade1_add_sub_round3_subtract_six_three",
    ),
    5: ElementaryVisualTemplate(
        problem_text="뺄셈식으로 나타내어 보세요. 7 빼기 1은 6과 같습니다.",
        expression="answer_text=7 - 1 = 6",
        rule_id="grade1_add_sub_round3_sentence_to_subtraction",
    ),
    6: ElementaryVisualTemplate(
        problem_text="3장의 수 카드 중에서 가장 큰 수와 가장 작은 수의 합과 차를 각각 구해 보세요.",
        expression="answer_text=합: 5 / 차: 3",
        rule_id="grade1_add_sub_round3_largest_smallest_sum_difference",
    ),
    7: ElementaryVisualTemplate(
        problem_text="계산 결과가 같은 것에 ○표 하세요.",
        expression="answer_text=두 번째, 세 번째",
        rule_id="grade1_add_sub_round3_same_result_choices",
    ),
    8: ElementaryVisualTemplate(
        problem_text="빈칸에 알맞은 수를 써 넣으세요. 8에서 5를 빼고 2를 더합니다.",
        expression="answer_text=빈칸: 3, 5",
        rule_id="grade1_add_sub_round3_operation_path",
    ),
    9: ElementaryVisualTemplate(
        problem_text="수 카드 중에서 3장을 골라 차가 가장 큰 뺄셈식을 만들어 보세요.",
        expression="answer_text=9 - 3 = 6",
        rule_id="grade1_add_sub_round3_largest_difference_cards",
    ),
    10: ElementaryVisualTemplate(
        problem_text="유영이는 종이배를 4개 접었고, 희주는 종이배를 6개 접었습니다. 희주는 유영이보다 종이배를 몇 개 더 접었을까요?",
        expression="answer_text=2개",
        rule_id="grade1_add_sub_round3_difference_word_problem",
    ),
    11: ElementaryVisualTemplate(
        problem_text="사과나무에 열려 있던 사과 8개가 모두 땅으로 떨어졌습니다. 사과나무에 남아 있는 사과는 몇 개인지 뺄셈식을 만들어 보세요.",
        expression="answer_text=8 - 8 = 0",
        rule_id="grade1_add_sub_round3_subtract_all_word_problem",
    ),
}


_COMPARISON_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="더 긴 것에 ○표 하세요.",
        expression="answer_text=위쪽",
        topic="measurement",
        rule_id="grade1_comparison_round1_longer",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그림을 보고 알맞은 말에 ○표 하세요. 줄넘기의 길이는 우산의 길이보다 더 짧습니다.",
        expression="answer_text=짧습니다",
        topic="measurement",
        rule_id="grade1_comparison_round1_shorter_word",
    ),
    3: ElementaryVisualTemplate(
        problem_text="짧은 것부터 순서대로 1, 2, 3을 써 보세요.",
        expression="answer_text=위에서부터 2, 1, 3",
        topic="measurement",
        rule_id="grade1_comparison_round1_order_by_short_length",
    ),
    4: ElementaryVisualTemplate(
        problem_text="세 색연필의 길이에 대한 설명 중 틀린 것을 찾아 기호를 쓰세요.",
        expression="answer_text=가",
        topic="measurement",
        rule_id="grade1_comparison_round1_wrong_length_statement",
    ),
    5: ElementaryVisualTemplate(
        problem_text="담을 수 있는 양을 비교할 때 쓰는 말로 바르게 짝지어진 것에 ○표 하세요.",
        expression="answer_text=많다, 적다",
        topic="measurement",
        rule_id="grade1_comparison_round1_capacity_terms",
    ),
    6: ElementaryVisualTemplate(
        problem_text="더 짧은 것에 ○표 하세요.",
        expression="answer_text=위쪽",
        topic="measurement",
        rule_id="grade1_comparison_round1_shorter",
    ),
}


_COMPARISON_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="가장 높은 것에 ○표, 가장 낮은 것에 △표 하세요.",
        expression="answer_text=가운데 ○표, 오른쪽 △표",
        topic="measurement",
        rule_id="grade1_comparison_round1_highest_lowest",
    ),
    2: ElementaryVisualTemplate(
        problem_text="높은 것부터 순서대로 1, 2, 3을 써 보세요.",
        expression="answer_text=위치순: 2, 3, 1",
        topic="measurement",
        rule_id="grade1_comparison_round1_order_by_height",
    ),
    3: ElementaryVisualTemplate(
        problem_text="더 무거운 것에 ○표 하세요.",
        expression="answer_text=수박",
        topic="measurement",
        rule_id="grade1_comparison_round1_heavier",
    ),
    4: ElementaryVisualTemplate(
        problem_text="민석이와 선아가 시소를 타고 있습니다. 더 무거운 사람은 누구입니까?",
        expression="answer_text=민석",
        topic="measurement",
        rule_id="grade1_comparison_round1_seesaw_heavier",
    ),
    5: ElementaryVisualTemplate(
        problem_text="똑같은 상자에 같은 무게의 책을 각각 3권, 7권 넣었습니다. 더 가벼운 상자를 골라 ○표 하세요.",
        expression="answer_text=3권 넣은 상자",
        topic="measurement",
        rule_id="grade1_comparison_round1_lighter_book_box",
    ),
    6: ElementaryVisualTemplate(
        problem_text="가벼운 것부터 차례로 1, 2, 3을 써 보세요.",
        expression="answer_text=위치순: 2, 1, 3",
        topic="measurement",
        rule_id="grade1_comparison_round1_order_by_light_weight",
    ),
    7: ElementaryVisualTemplate(
        problem_text="가장 넓은 것에 ○표 하세요.",
        expression="answer_text=신문",
        topic="measurement",
        rule_id="grade1_comparison_round1_widest",
    ),
    8: ElementaryVisualTemplate(
        problem_text="징, 꽹과리, 북 중에서 가장 좁은 것은 무엇일까요?",
        expression="answer_text=꽹과리",
        topic="measurement",
        rule_id="grade1_comparison_round1_narrowest_instrument",
    ),
    9: ElementaryVisualTemplate(
        problem_text="물을 더 많이 담을 수 있는 용기에 ○표 하세요.",
        expression="answer_text=큰 물통",
        topic="measurement",
        rule_id="grade1_comparison_round1_larger_capacity_container",
    ),
}


_COMPARISON_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="왼쪽 컵보다 담긴 주스의 양이 더 적은 것을 찾아 ○표 하세요.",
        expression="answer_text=오른쪽 컵",
        topic="measurement",
        rule_id="grade1_comparison_round1_less_juice_than_left",
    ),
    2: ElementaryVisualTemplate(
        problem_text="은영과 동준이가 똑같은 컵에 주스를 가득 따라 각각 마셨습니다. 주스를 더 많이 마신 사람은 누구입니까?",
        expression="answer_text=동준",
        topic="measurement",
        rule_id="grade1_comparison_round1_more_juice_drinker",
    ),
    3: ElementaryVisualTemplate(
        problem_text="음료가 많이 담긴 것부터 차례로 1, 2, 3을 써 보세요.",
        expression="answer_text=위치순: 2, 1, 3",
        topic="measurement",
        rule_id="grade1_comparison_round1_order_by_drink_amount",
    ),
    4: ElementaryVisualTemplate(
        problem_text="다음 용기에 담긴 물의 높이가 모두 같습니다. 담긴 물의 양이 많은 것부터 차례로 1, 2, 3을 써 보세요.",
        expression="answer_text=위치순: 2, 3, 1",
        topic="measurement",
        rule_id="grade1_comparison_round1_order_by_water_amount_same_height",
    ),
    5: ElementaryVisualTemplate(
        problem_text="다음은 무엇을 비교하려는 것인지 보기에서 찾아 써 보세요. 내 컵에 물을 가득 채워 다른 빈 컵에 부어 봅니다.",
        expression="answer_text=담을 수 있는 양",
        topic="measurement",
        rule_id="grade1_comparison_round1_capacity_concept",
    ),
}


_COMPARISON_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="더 긴 것에 ○표 하세요.",
        expression="answer_text=오른쪽",
        topic="measurement",
        rule_id="grade1_comparison_round2_longer",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그림을 보고 알맞은 말에 ○표 하세요. 포크의 길이는 숟가락의 길이보다 더 깁니다.",
        expression="answer_text=깁니다",
        topic="measurement",
        rule_id="grade1_comparison_round2_longer_word",
    ),
    3: ElementaryVisualTemplate(
        problem_text="짧은 것부터 순서대로 1, 2, 3을 써 보세요.",
        expression="answer_text=위에서부터 3, 1, 2",
        topic="measurement",
        rule_id="grade1_comparison_round2_order_by_short_length",
    ),
    4: ElementaryVisualTemplate(
        problem_text="다음 그림에 대한 설명 중 틀린 것을 찾아 기호를 쓰세요.",
        expression="answer_text=나",
        topic="measurement",
        rule_id="grade1_comparison_round2_wrong_length_statement",
    ),
    5: ElementaryVisualTemplate(
        problem_text="길이를 비교할 때 쓰는 말로 바르게 짝지어진 것에 ○표 하세요.",
        expression="answer_text=길다, 짧다",
        topic="measurement",
        rule_id="grade1_comparison_round2_length_terms",
    ),
    6: ElementaryVisualTemplate(
        problem_text="더 짧은 것에 ○표 하세요.",
        expression="answer_text=아래쪽",
        topic="measurement",
        rule_id="grade1_comparison_round2_shorter",
    ),
    7: ElementaryVisualTemplate(
        problem_text="가장 높은 것에 ○표, 가장 낮은 것에 △표 하세요.",
        expression="answer_text=왼쪽 △표, 가운데 ○표",
        topic="measurement",
        rule_id="grade1_comparison_round2_highest_lowest",
    ),
}


_COMPARISON_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="낮은 것부터 순서대로 1, 2, 3을 써 보세요.",
        expression="answer_text=위치순: 1, 2, 3",
        topic="measurement",
        rule_id="grade1_comparison_round2_order_by_low_height",
    ),
    2: ElementaryVisualTemplate(
        problem_text="더 무거운 것에 ○표 하세요.",
        expression="answer_text=호박",
        topic="measurement",
        rule_id="grade1_comparison_round2_heavier",
    ),
    3: ElementaryVisualTemplate(
        problem_text="야구공과 테니스공을 양팔 저울에 올렸습니다. 더 무거운 것은 무엇입니까?",
        expression="answer_text=야구공",
        topic="measurement",
        rule_id="grade1_comparison_round2_balance_heavier",
    ),
    4: ElementaryVisualTemplate(
        problem_text="똑같은 상자에 같은 무게의 벽돌이 각각 5개, 3개 들어 있습니다. 더 가벼운 상자를 골라 ○표 하세요.",
        expression="answer_text=3개 들어 있는 상자",
        topic="measurement",
        rule_id="grade1_comparison_round2_lighter_brick_box",
    ),
    5: ElementaryVisualTemplate(
        problem_text="가벼운 것부터 차례로 1, 2, 3을 써 보세요.",
        expression="answer_text=위치순: 1, 3, 2",
        topic="measurement",
        rule_id="grade1_comparison_round2_order_by_light_weight",
    ),
    6: ElementaryVisualTemplate(
        problem_text="가장 넓은 것에 ○표 하세요.",
        expression="answer_text=왼쪽 도형",
        topic="measurement",
        rule_id="grade1_comparison_round2_widest_shape",
    ),
    7: ElementaryVisualTemplate(
        problem_text="놀이터, 운동장, 공원의 넓이를 비교하였습니다. 가장 넓은 곳은 어디입니까?",
        expression="answer_text=공원",
        topic="measurement",
        rule_id="grade1_comparison_round2_widest_place",
    ),
    8: ElementaryVisualTemplate(
        problem_text="물을 더 많이 담을 수 있는 용기에 ○표 하세요.",
        expression="answer_text=오른쪽 병",
        topic="measurement",
        rule_id="grade1_comparison_round2_larger_capacity_container",
    ),
}


_COMPARISON_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="왼쪽 컵보다 담긴 우유의 양이 더 많은 것을 찾아 ○표 하세요.",
        expression="answer_text=첫 번째 컵",
        topic="measurement",
        rule_id="grade1_comparison_round2_more_milk_than_left",
    ),
    2: ElementaryVisualTemplate(
        problem_text="지연이와 수지가 똑같은 컵에 주스를 가득 따라 각각 마셨습니다. 주스를 더 적게 마신 사람은 누구입니까?",
        expression="answer_text=수지",
        topic="measurement",
        rule_id="grade1_comparison_round2_less_juice_drinker",
    ),
    3: ElementaryVisualTemplate(
        problem_text="음료가 적게 담긴 것부터 차례로 1, 2, 3을 써 보세요.",
        expression="answer_text=위치순: 3, 1, 2",
        topic="measurement",
        rule_id="grade1_comparison_round2_order_by_less_drink_amount",
    ),
    4: ElementaryVisualTemplate(
        problem_text="다음 용기에 담긴 물의 높이가 모두 같습니다. 담긴 물의 양이 많은 것부터 차례로 1, 2, 3을 써 보세요.",
        expression="answer_text=위치순: 2, 1, 3",
        topic="measurement",
        rule_id="grade1_comparison_round2_order_by_water_amount_same_height",
    ),
    5: ElementaryVisualTemplate(
        problem_text="다음은 무엇을 비교하려는 것인지 보기에서 찾아 써 보세요. 사진을 액자에 넣을 수 있는지 겹쳐 보았습니다.",
        expression="answer_text=넓이",
        topic="measurement",
        rule_id="grade1_comparison_round2_area_concept",
    ),
}


_COMPARISON_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="더 짧은 것에 ○표 하세요.",
        expression="answer_text=위쪽",
        topic="measurement",
        rule_id="grade1_comparison_round3_shorter",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그림을 보고 알맞은 말에 ○표 하세요. 자의 길이는 연필의 길이보다 더 깁니다.",
        expression="answer_text=깁니다",
        topic="measurement",
        rule_id="grade1_comparison_round3_longer_word",
    ),
    3: ElementaryVisualTemplate(
        problem_text="긴 것부터 순서대로 1, 2, 3을 써 보세요.",
        expression="answer_text=위에서부터 3, 2, 1",
        topic="measurement",
        rule_id="grade1_comparison_round3_order_by_long_length",
    ),
    4: ElementaryVisualTemplate(
        problem_text="세 우산의 길이에 대한 설명 중 틀린 것을 찾아 기호를 쓰세요.",
        expression="answer_text=가",
        topic="measurement",
        rule_id="grade1_comparison_round3_wrong_length_statement",
    ),
    5: ElementaryVisualTemplate(
        problem_text="무게를 비교할 때 쓰는 말로 바르게 짝지어진 것에 ○표 하세요.",
        expression="answer_text=무겁다, 가볍다",
        topic="measurement",
        rule_id="grade1_comparison_round3_weight_terms",
    ),
    6: ElementaryVisualTemplate(
        problem_text="더 긴 것에 ○표 하세요.",
        expression="answer_text=위쪽",
        topic="measurement",
        rule_id="grade1_comparison_round3_longer",
    ),
}


_COMPARISON_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="가장 높은 것에 ○표, 가장 낮은 것에 △표 하세요.",
        expression="answer_text=셋째 △표, 넷째 ○표",
        topic="measurement",
        rule_id="grade1_comparison_round3_highest_lowest",
    ),
    2: ElementaryVisualTemplate(
        problem_text="높은 것부터 순서대로 1, 2, 3을 써 보세요.",
        expression="answer_text=위치순: 1, 3, 2",
        topic="measurement",
        rule_id="grade1_comparison_round3_order_by_height",
    ),
    3: ElementaryVisualTemplate(
        problem_text="더 가벼운 것에 ○표 하세요.",
        expression="answer_text=왼쪽",
        topic="measurement",
        rule_id="grade1_comparison_round3_lighter",
    ),
    4: ElementaryVisualTemplate(
        problem_text="귤과 사과를 양팔 저울에 올렸습니다. 더 가벼운 과일은 무엇입니까?",
        expression="answer_text=귤",
        topic="measurement",
        rule_id="grade1_comparison_round3_balance_lighter",
    ),
    5: ElementaryVisualTemplate(
        problem_text="똑같은 상자에 같은 무게의 우유가 각각 4컵, 8컵 들어 있습니다. 더 무거운 상자를 골라 ○표 하세요.",
        expression="answer_text=8컵 들어 있는 상자",
        topic="measurement",
        rule_id="grade1_comparison_round3_heavier_milk_box",
    ),
    6: ElementaryVisualTemplate(
        problem_text="가벼운 것부터 차례로 1, 2, 3을 써 보세요.",
        expression="answer_text=위치순: 1, 3, 2",
        topic="measurement",
        rule_id="grade1_comparison_round3_order_by_light_weight",
    ),
    7: ElementaryVisualTemplate(
        problem_text="가장 넓은 것에 ○표 하세요.",
        expression="answer_text=신문",
        topic="measurement",
        rule_id="grade1_comparison_round3_widest",
    ),
    8: ElementaryVisualTemplate(
        problem_text="방, 운동장, 농구장의 넓이를 비교하였습니다. 가장 좁은 곳은 어디입니까?",
        expression="answer_text=방",
        topic="measurement",
        rule_id="grade1_comparison_round3_narrowest_place",
    ),
    9: ElementaryVisualTemplate(
        problem_text="물을 더 많이 담을 수 있는 용기에 ○표 하세요.",
        expression="answer_text=왼쪽 물통",
        topic="measurement",
        rule_id="grade1_comparison_round3_larger_capacity_container",
    ),
}


_COMPARISON_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="왼쪽 병보다 담긴 물의 양이 더 적은 것을 찾아 ○표 하세요.",
        expression="answer_text=오른쪽 병",
        topic="measurement",
        rule_id="grade1_comparison_round3_less_water_than_left",
    ),
    2: ElementaryVisualTemplate(
        problem_text="하은이와 준호가 똑같은 컵에 주스를 가득 따라 각각 마셨습니다. 주스를 더 많이 마신 사람은 누구입니까?",
        expression="answer_text=하은",
        topic="measurement",
        rule_id="grade1_comparison_round3_more_juice_drinker",
    ),
    3: ElementaryVisualTemplate(
        problem_text="물이 많이 담긴 것부터 차례로 1, 2, 3을 써 보세요.",
        expression="answer_text=위치순: 2, 3, 1",
        topic="measurement",
        rule_id="grade1_comparison_round3_order_by_water_amount",
    ),
    4: ElementaryVisualTemplate(
        problem_text="다음 용기에 담긴 물의 높이가 모두 같습니다. 담긴 물의 양이 많은 것부터 차례로 1, 2, 3을 써 보세요.",
        expression="answer_text=위치순: 3, 1, 2",
        topic="measurement",
        rule_id="grade1_comparison_round3_order_by_water_amount_same_height",
    ),
    5: ElementaryVisualTemplate(
        problem_text="다음은 무엇을 비교하려는 것인지 보기에서 찾아 써 보세요. 친구와 시소의 양쪽에 앉아 어느 쪽으로 내려가는지 알아봅니다.",
        expression="answer_text=무게",
        topic="measurement",
        rule_id="grade1_comparison_round3_weight_concept",
    ),
}


_NUMBERS_TO_50_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수를 세어 쓰고 읽어 보세요. 토마토는 모두 12개입니다.",
        expression="answer_text=쓰기: 12 / 읽기: 십이, 열둘",
        rule_id="grade1_numbers_to_50_round1_count_write_read",
    ),
    2: ElementaryVisualTemplate(
        problem_text="모으기와 가르기를 해 보세요. 8과 7을 모으고, 13을 6과 7로 가릅니다.",
        expression="answer_text=빈칸: 15, 6",
        rule_id="grade1_numbers_to_50_round1_compose_decompose",
    ),
    3: ElementaryVisualTemplate(
        problem_text="열부터 거꾸로 세어 보려고 합니다. 열, 아홉, 여덟, 일곱, 여섯, 다섯 순서입니다.",
        expression="answer_text=여덟",
        rule_id="grade1_numbers_to_50_round1_count_backwards_word",
    ),
    4: ElementaryVisualTemplate(
        problem_text="10을 바르게 가르기 한 사람의 이름을 써 보세요. 7과 3으로 가른 민희가 맞습니다.",
        expression="answer_text=민희",
        rule_id="grade1_numbers_to_50_round1_decompose_ten_name",
    ),
    5: ElementaryVisualTemplate(
        problem_text="주어진 수보다 1만큼 더 작은 수와 1만큼 더 큰 수를 쓰세요. 17의 앞뒤 수와 11의 앞뒤 수를 씁니다.",
        expression="answer_text=빈칸: 16, 18, 10, 12",
        rule_id="grade1_numbers_to_50_round1_one_less_one_more",
    ),
    6: ElementaryVisualTemplate(
        problem_text="바둑돌의 수를 세어 빈칸에 알맞은 수를 써넣으세요. 10개씩 묶음 2개와 낱개 7개입니다.",
        expression="answer_text=10개씩 묶음: 2 / 낱개: 7 / 수: 27",
        rule_id="grade1_numbers_to_50_round1_tens_ones_count",
    ),
    7: ElementaryVisualTemplate(
        problem_text="28, 29, □, □, 32에서 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=빈칸: 30, 31",
        rule_id="grade1_numbers_to_50_round1_number_line_blanks",
    ),
    8: ElementaryVisualTemplate(
        problem_text="알맞게 선으로 이어 보세요. 12는 십이, 13은 열셋, 19는 십구입니다.",
        expression="answer_text=12-십이 / 13-열셋 / 19-십구",
        rule_id="grade1_numbers_to_50_round1_match_number_word",
    ),
}


_NUMBERS_TO_50_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="모으기를 하여 14가 되는 것에 ○표 하세요. 5와 9를 모으면 14입니다.",
        expression="answer_text=가운데 ○표",
        rule_id="grade1_numbers_to_50_round1_make_fourteen",
    ),
    2: ElementaryVisualTemplate(
        problem_text="□ 안에 알맞은 수나 말을 써 넣으세요. 37은 10개씩 묶음 3개와 낱개 7개이며 삼십칠이라고 읽습니다.",
        expression="answer_text=빈칸: 7, 삼십칠",
        rule_id="grade1_numbers_to_50_round1_write_read_37",
    ),
    3: ElementaryVisualTemplate(
        problem_text="보기를 보고 □ 안을 채워 쓰세요. 50은 10개씩 묶음 5개이고, 딸기가 10개씩 5묶음 있으면 50개입니다.",
        expression="answer_text=빈칸: 5, 50, 5, 50",
        rule_id="grade1_numbers_to_50_round1_fill_50_tens",
    ),
    4: ElementaryVisualTemplate(
        problem_text="22, 35, 19 중 가장 큰 수에 ○표 하세요.",
        expression="answer=35",
        rule_id="grade1_numbers_to_50_round1_largest_number",
    ),
    5: ElementaryVisualTemplate(
        problem_text="35보다 1만큼 더 큰 수와 46보다 1만큼 더 작은 수를 쓰세요.",
        expression="answer_text=빈칸: 36, 45",
        rule_id="grade1_numbers_to_50_round1_one_more_one_less",
    ),
    6: ElementaryVisualTemplate(
        problem_text="달걀을 10개씩 묶음 4개 사 오셨습니다. 달걀은 모두 몇 개인지 구하세요.",
        expression="answer_text=40개",
        rule_id="grade1_numbers_to_50_round1_four_tens",
    ),
    7: ElementaryVisualTemplate(
        problem_text="연필 36자루를 한 상자에 10자루씩 담으면 3상자가 되고 6자루가 남습니다.",
        expression="answer_text=빈칸: 3, 6",
        rule_id="grade1_numbers_to_50_round1_36_tens_ones",
    ),
    8: ElementaryVisualTemplate(
        problem_text="빈 병을 한 상자에 10개씩 담으니 3상자가 되고 낱개 6개가 남았습니다. 빈 병은 모두 36개입니다.",
        expression="answer_text=36개",
        rule_id="grade1_numbers_to_50_round1_three_tens_six_ones",
    ),
    9: ElementaryVisualTemplate(
        problem_text="25, 47, 35, 13, 38을 작은 수부터 순서대로 쓰세요.",
        expression="answer_text=13, 25, 35, 38, 47",
        rule_id="grade1_numbers_to_50_round1_order_ascending",
    ),
}


_NUMBERS_TO_50_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="40과 50 사이에 있고 낱개의 수가 7인 수는 47입니다.",
        expression="answer=47",
        rule_id="grade1_numbers_to_50_round1_described_number_47",
    ),
    2: ElementaryVisualTemplate(
        problem_text="번호 순서대로 줄을 섰을 때 은희가 37번이면 은희 바로 앞에 서 있는 사람은 36번입니다.",
        expression="answer_text=36번",
        rule_id="grade1_numbers_to_50_round1_number_before_37",
    ),
    3: ElementaryVisualTemplate(
        problem_text="10개씩 묶음 3개와 낱개 4개인 수보다 작고 30보다 큰 수는 31, 32, 33으로 모두 3개입니다.",
        expression="answer_text=3개",
        rule_id="grade1_numbers_to_50_round1_between_30_and_34",
    ),
}


_NUMBERS_TO_50_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수를 세어 쓰고 읽어 보세요. 귤은 모두 11개입니다.",
        expression="answer_text=쓰기: 11 / 읽기: 십일, 열하나",
        rule_id="grade1_numbers_to_50_round2_count_write_read",
    ),
    2: ElementaryVisualTemplate(
        problem_text="모으기와 가르기를 해 보세요. 6과 5를 모으고, 18을 9와 9로 가릅니다.",
        expression="answer_text=빈칸: 11, 9",
        rule_id="grade1_numbers_to_50_round2_compose_decompose",
    ),
    3: ElementaryVisualTemplate(
        problem_text="열부터 거꾸로 세어 보려고 합니다. 열, 아홉, 여덟, 일곱, 여섯, 다섯 순서입니다.",
        expression="answer_text=다섯",
        rule_id="grade1_numbers_to_50_round2_count_backwards_word",
    ),
    4: ElementaryVisualTemplate(
        problem_text="10을 바르게 가르기 한 사람의 이름을 써 보세요. 1과 9로 가른 연희가 맞습니다.",
        expression="answer_text=연희",
        rule_id="grade1_numbers_to_50_round2_decompose_ten_name",
    ),
    5: ElementaryVisualTemplate(
        problem_text="주어진 수보다 1만큼 더 작은 수와 1만큼 더 큰 수를 쓰세요. 13의 앞뒤 수와 16의 앞뒤 수를 씁니다.",
        expression="answer_text=빈칸: 12, 14, 15, 17",
        rule_id="grade1_numbers_to_50_round2_one_less_one_more",
    ),
    6: ElementaryVisualTemplate(
        problem_text="달걀의 수를 세어 빈칸에 알맞은 수를 써넣으세요. 10개씩 묶음 1개와 낱개 4개입니다.",
        expression="answer_text=10개씩 묶음: 1 / 낱개: 4 / 수: 14",
        rule_id="grade1_numbers_to_50_round2_tens_ones_count",
    ),
    7: ElementaryVisualTemplate(
        problem_text="37, □, 39, □, 41에서 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=빈칸: 38, 40",
        rule_id="grade1_numbers_to_50_round2_number_line_blanks",
    ),
    8: ElementaryVisualTemplate(
        problem_text="알맞게 선으로 이어 보세요. 33은 삼십삼, 27은 스물일곱, 46은 마흔여섯입니다.",
        expression="answer_text=33-삼십삼 / 27-스물일곱 / 46-마흔여섯",
        rule_id="grade1_numbers_to_50_round2_match_number_word",
    ),
}


_NUMBERS_TO_50_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="모으기를 하여 15가 되는 것에 ○표 하세요. 8과 7을 모으면 15입니다.",
        expression="answer_text=왼쪽 ○표",
        rule_id="grade1_numbers_to_50_round2_make_fifteen",
    ),
    2: ElementaryVisualTemplate(
        problem_text="□ 안에 알맞은 수나 말을 써 넣으세요. 48은 10개씩 묶음 4개와 낱개 8개이며 사십팔이라고 읽습니다.",
        expression="answer_text=빈칸: 8, 사십팔",
        rule_id="grade1_numbers_to_50_round2_write_read_48",
    ),
    3: ElementaryVisualTemplate(
        problem_text="30은 10개씩 묶음 3개이고, 40은 10개씩 묶음 4개입니다.",
        expression="answer_text=빈칸: 3, 40",
        rule_id="grade1_numbers_to_50_round2_tens_30_40",
    ),
    4: ElementaryVisualTemplate(
        problem_text="23, 40, 19 중 가장 작은 수에 ○표 하세요.",
        expression="answer=19",
        rule_id="grade1_numbers_to_50_round2_smallest_number",
    ),
    5: ElementaryVisualTemplate(
        problem_text="28보다 1만큼 더 큰 수와 33보다 1만큼 더 작은 수를 쓰세요.",
        expression="answer_text=빈칸: 29, 32",
        rule_id="grade1_numbers_to_50_round2_one_more_one_less",
    ),
    6: ElementaryVisualTemplate(
        problem_text="장미꽃을 10송이씩 묶음 3개 사 왔습니다. 장미꽃은 모두 30송이입니다.",
        expression="answer_text=30송이",
        rule_id="grade1_numbers_to_50_round2_three_tens_flowers",
    ),
    7: ElementaryVisualTemplate(
        problem_text="엽서 42장을 한 상자에 10장씩 담으면 4상자가 되고 2장이 남습니다.",
        expression="answer_text=빈칸: 4, 2",
        rule_id="grade1_numbers_to_50_round2_42_tens_ones",
    ),
    8: ElementaryVisualTemplate(
        problem_text="컵을 한 상자에 10개씩 담으니 4상자가 되고 낱개 3개가 남았습니다. 컵은 모두 43개입니다.",
        expression="answer_text=43개",
        rule_id="grade1_numbers_to_50_round2_four_tens_three_ones",
    ),
    9: ElementaryVisualTemplate(
        problem_text="29, 12, 43, 39, 32를 작은 수부터 순서대로 쓰세요.",
        expression="answer_text=12, 29, 32, 39, 43",
        rule_id="grade1_numbers_to_50_round2_order_ascending",
    ),
    10: ElementaryVisualTemplate(
        problem_text="30과 40 사이에 있고 낱개의 수가 3인 수는 33입니다.",
        expression="answer=33",
        rule_id="grade1_numbers_to_50_round2_described_number_33",
    ),
    11: ElementaryVisualTemplate(
        problem_text="서준이가 47번이라면 바로 앞에 번호표를 뽑은 사람은 46번입니다.",
        expression="answer_text=46번",
        rule_id="grade1_numbers_to_50_round2_number_before_47",
    ),
    12: ElementaryVisualTemplate(
        problem_text="10개씩 묶음 4개와 낱개 5개인 수보다 작고 40보다 큰 수는 41, 42, 43, 44로 모두 4개입니다.",
        expression="answer_text=4개",
        rule_id="grade1_numbers_to_50_round2_between_40_and_45",
    ),
}


_NUMBERS_TO_50_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수를 세어 쓰고 읽어 보세요. 딸기는 모두 10개입니다.",
        expression="answer_text=쓰기: 10 / 읽기: 십, 열",
        rule_id="grade1_numbers_to_50_round3_count_write_read",
    ),
    2: ElementaryVisualTemplate(
        problem_text="모으기와 가르기를 해 보세요. 7과 9를 모으고, 11을 2와 9로 가릅니다.",
        expression="answer_text=빈칸: 16, 9",
        rule_id="grade1_numbers_to_50_round3_compose_decompose",
    ),
    3: ElementaryVisualTemplate(
        problem_text="열부터 거꾸로 세어 보려고 합니다. 열, 아홉, 여덟, 일곱, 여섯 순서입니다.",
        expression="answer_text=일곱",
        rule_id="grade1_numbers_to_50_round3_count_backwards_word",
    ),
    4: ElementaryVisualTemplate(
        problem_text="바르게 모으기 하여 10이 된 사람의 이름을 써 보세요. 4와 6을 모은 서준이 맞습니다.",
        expression="answer_text=서준",
        rule_id="grade1_numbers_to_50_round3_make_ten_name",
    ),
    5: ElementaryVisualTemplate(
        problem_text="주어진 수보다 1만큼 더 작은 수와 1만큼 더 큰 수를 쓰세요. 15의 앞뒤 수와 18의 앞뒤 수를 씁니다.",
        expression="answer_text=빈칸: 14, 16, 17, 19",
        rule_id="grade1_numbers_to_50_round3_one_less_one_more",
    ),
    6: ElementaryVisualTemplate(
        problem_text="축구공의 수를 세어 빈칸에 알맞은 수를 써넣으세요. 10개씩 묶음 2개와 낱개 4개입니다.",
        expression="answer_text=10개씩 묶음: 2 / 낱개: 4 / 수: 24",
        rule_id="grade1_numbers_to_50_round3_tens_ones_count",
    ),
    7: ElementaryVisualTemplate(
        problem_text="13, 14, □, □, 17에서 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=빈칸: 15, 16",
        rule_id="grade1_numbers_to_50_round3_number_line_blanks",
    ),
    8: ElementaryVisualTemplate(
        problem_text="알맞게 선으로 이어 보세요. 11은 열하나, 24는 이십사, 37은 서른일곱입니다.",
        expression="answer_text=11-열하나 / 24-이십사 / 37-서른일곱",
        rule_id="grade1_numbers_to_50_round3_match_number_word",
    ),
}


_NUMBERS_TO_50_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="모으기를 하여 17이 되는 것에 ○표 하세요. 8과 9를 모으면 17입니다.",
        expression="answer_text=오른쪽 ○표",
        rule_id="grade1_numbers_to_50_round3_make_seventeen",
    ),
    2: ElementaryVisualTemplate(
        problem_text="□ 안에 알맞은 수나 말을 써 넣으세요. 29는 10개씩 묶음 2개와 낱개 9개이며 스물아홉이라고 읽습니다.",
        expression="answer_text=빈칸: 9, 스물아홉",
        rule_id="grade1_numbers_to_50_round3_write_read_29",
    ),
    3: ElementaryVisualTemplate(
        problem_text="50은 10개씩 묶음 5개이고, 20은 10개씩 묶음 2개입니다.",
        expression="answer_text=빈칸: 5, 20",
        rule_id="grade1_numbers_to_50_round3_tens_50_20",
    ),
    4: ElementaryVisualTemplate(
        problem_text="41, 39, 28 중 가장 큰 수에 ○표 하세요.",
        expression="answer=41",
        rule_id="grade1_numbers_to_50_round3_largest_number",
    ),
    5: ElementaryVisualTemplate(
        problem_text="19보다 1만큼 더 큰 수와 40보다 1만큼 더 작은 수를 쓰세요.",
        expression="answer_text=빈칸: 20, 39",
        rule_id="grade1_numbers_to_50_round3_one_more_one_less",
    ),
    6: ElementaryVisualTemplate(
        problem_text="꽃감을 10개씩 묶음 5개 사 오셨습니다. 꽃감은 모두 50개입니다.",
        expression="answer_text=50개",
        rule_id="grade1_numbers_to_50_round3_five_tens",
    ),
    7: ElementaryVisualTemplate(
        problem_text="볼펜 27자루를 한 상자에 10자루씩 담으면 2상자가 되고 7자루가 남습니다.",
        expression="answer_text=빈칸: 2, 7",
        rule_id="grade1_numbers_to_50_round3_27_tens_ones",
    ),
    8: ElementaryVisualTemplate(
        problem_text="색종이를 한 봉지에 10장씩 담으니 2봉지가 되고 낱장이 7장 남았습니다. 색종이는 모두 27장입니다.",
        expression="answer_text=27장",
        rule_id="grade1_numbers_to_50_round3_two_tens_seven_ones",
    ),
    9: ElementaryVisualTemplate(
        problem_text="33, 28, 42, 21, 19를 작은 수부터 순서대로 쓰세요.",
        expression="answer_text=19, 21, 28, 33, 42",
        rule_id="grade1_numbers_to_50_round3_order_ascending",
    ),
}


_NUMBERS_TO_50_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="10과 20 사이에 있고 낱개의 수가 6인 수는 16입니다.",
        expression="answer=16",
        rule_id="grade1_numbers_to_50_round3_described_number_16",
    ),
    2: ElementaryVisualTemplate(
        problem_text="예서네 가족이 23번이라면 바로 앞에 번호표를 뽑은 사람은 22번입니다.",
        expression="answer_text=22번",
        rule_id="grade1_numbers_to_50_round3_number_before_23",
    ),
    3: ElementaryVisualTemplate(
        problem_text="10개씩 묶음 4개와 낱개 1개인 수보다 작고 35보다 큰 수는 36, 37, 38, 39, 40으로 모두 5개입니다.",
        expression="answer_text=5개",
        rule_id="grade1_numbers_to_50_round3_between_35_and_41",
    ),
}


_NUMBERS_TO_100_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수를 세어 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=10개씩 묶음: 6, 낱개: 2 / 62",
        rule_id="grade1_numbers_to_100_round1_count_base_ten_62",
    ),
    2: ElementaryVisualTemplate(
        problem_text="연필이 한 상자에 10자루씩 들어 있습니다. 연필을 60자루 사려면 6상자를 사야 합니다.",
        expression="answer_text=6상자",
        rule_id="grade1_numbers_to_100_round1_boxes_for_60_pencils",
    ),
    3: ElementaryVisualTemplate(
        problem_text="10개씩 묶음 6개, 7개, 8개, 9개를 알맞은 수와 읽는 말로 이어 보세요.",
        expression="answer_text=6묶음-60-육십/예순, 7묶음-70-칠십/일흔, 8묶음-80-팔십/여든, 9묶음-90-구십/아흔",
        rule_id="grade1_numbers_to_100_round1_tens_match",
    ),
    4: ElementaryVisualTemplate(
        problem_text="10개씩 묶음 8개가 나타내는 수를 쓰고 읽어 보세요.",
        expression="answer_text=80 / 팔십, 여든",
        rule_id="grade1_numbers_to_100_round1_write_read_80",
    ),
    5: ElementaryVisualTemplate(
        problem_text="빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=53: 5묶음 3낱개 / 78: 7묶음 8낱개 / 84",
        rule_id="grade1_numbers_to_100_round1_table_blanks",
    ),
    6: ElementaryVisualTemplate(
        problem_text="초콜릿이 10개 묶음 8개와 낱개 15개가 있습니다. 초콜릿은 모두 95개입니다.",
        expression="answer_text=95개",
        rule_id="grade1_numbers_to_100_round1_8_tens_15_ones",
    ),
    7: ElementaryVisualTemplate(
        problem_text="수를 잘못 읽은 것을 고르세요.",
        expression="answer_text=⑤",
        rule_id="grade1_numbers_to_100_round1_wrong_reading_choice",
    ),
    8: ElementaryVisualTemplate(
        problem_text="나타내는 수가 다른 하나를 찾아 ○표 하세요.",
        expression="answer_text=예순",
        rule_id="grade1_numbers_to_100_round1_different_number_word",
    ),
    9: ElementaryVisualTemplate(
        problem_text="10개씩 묶음 4개와 낱개 14개로 나타낸 수를 올바르게 읽은 것에 ○표 하세요.",
        expression="answer_text=54 / 오십사, 쉰넷",
        rule_id="grade1_numbers_to_100_round1_4_tens_14_ones",
    ),
}


_NUMBERS_TO_100_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수를 세어 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=10개씩 묶음: 8, 낱개: 4 / 84",
        rule_id="grade1_numbers_to_100_round2_count_base_ten_84",
    ),
    2: ElementaryVisualTemplate(
        problem_text="지우개가 한 상자에 10개씩 들어 있습니다. 지우개를 70개 사려면 7상자를 사야 합니다.",
        expression="answer_text=7상자",
        rule_id="grade1_numbers_to_100_round2_boxes_for_70_erasers",
    ),
    3: ElementaryVisualTemplate(
        problem_text="수를 바르게 나타낸 것에 ○표 하세요.",
        expression="answer_text=칠십-70",
        rule_id="grade1_numbers_to_100_round2_correct_reading_match",
    ),
    4: ElementaryVisualTemplate(
        problem_text="10개씩 묶음 6개가 나타내는 수를 쓰고 읽어 보세요.",
        expression="answer_text=60 / 육십, 예순",
        rule_id="grade1_numbers_to_100_round2_write_read_60",
    ),
    5: ElementaryVisualTemplate(
        problem_text="빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=64: 6묶음 4낱개 / 59: 5묶음 9낱개 / 97",
        rule_id="grade1_numbers_to_100_round2_table_blanks",
    ),
    6: ElementaryVisualTemplate(
        problem_text="사탕이 10개 묶음 5개와 낱개 28개가 있습니다. 사탕은 모두 78개입니다.",
        expression="answer_text=78개",
        rule_id="grade1_numbers_to_100_round2_5_tens_28_ones",
    ),
    7: ElementaryVisualTemplate(
        problem_text="수를 바르게 읽은 것을 고르세요.",
        expression="answer_text=①, ③, ④, ⑤",
        rule_id="grade1_numbers_to_100_round2_correct_reading_choices",
    ),
    8: ElementaryVisualTemplate(
        problem_text="나타내는 수가 다른 하나를 찾아 ○표 하세요.",
        expression="answer_text=여든",
        rule_id="grade1_numbers_to_100_round2_different_number_word",
    ),
    9: ElementaryVisualTemplate(
        problem_text="10개씩 묶음 6개와 낱개 27개로 나타낸 수를 올바르게 읽은 것에 ○표 하세요.",
        expression="answer_text=87 / 팔십칠, 여든일곱",
        rule_id="grade1_numbers_to_100_round2_6_tens_27_ones",
    ),
}


_NUMBERS_TO_100_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수를 세어 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=10개씩 묶음: 7, 낱개: 5 / 75",
        rule_id="grade1_numbers_to_100_round3_count_base_ten_75",
    ),
    2: ElementaryVisualTemplate(
        problem_text="사탕이 한 상자에 10개씩 들어 있습니다. 사탕을 90개 사려면 9상자를 사야 합니다.",
        expression="answer_text=9상자",
        rule_id="grade1_numbers_to_100_round3_boxes_for_90_candies",
    ),
    3: ElementaryVisualTemplate(
        problem_text="수로 바르게 나타낸 것에 ○표 하세요.",
        expression="answer_text=팔십-80",
        rule_id="grade1_numbers_to_100_round3_correct_reading_match",
    ),
    4: ElementaryVisualTemplate(
        problem_text="10개씩 묶음 9개가 나타내는 수를 쓰고 읽어 보세요.",
        expression="answer_text=90 / 구십, 아흔",
        rule_id="grade1_numbers_to_100_round3_write_read_90",
    ),
    5: ElementaryVisualTemplate(
        problem_text="빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=87: 8묶음 7낱개 / 67: 6묶음 7낱개 / 77",
        rule_id="grade1_numbers_to_100_round3_table_blanks",
    ),
    6: ElementaryVisualTemplate(
        problem_text="색종이가 10장씩 묶음 6개와 낱개 19장이 있습니다. 색종이는 모두 79장입니다.",
        expression="answer_text=79장",
        rule_id="grade1_numbers_to_100_round3_6_tens_19_ones",
    ),
    7: ElementaryVisualTemplate(
        problem_text="수를 잘못 읽은 것을 고르세요.",
        expression="answer_text=①",
        rule_id="grade1_numbers_to_100_round3_wrong_reading_choice",
    ),
    8: ElementaryVisualTemplate(
        problem_text="나타내는 수가 다른 하나를 찾아 ○표 하세요.",
        expression="answer_text=아흔",
        rule_id="grade1_numbers_to_100_round3_different_number_word",
    ),
    9: ElementaryVisualTemplate(
        problem_text="빈칸에 알맞은 수를 써넣고 옳게 읽은 것에 ○표 하세요.",
        expression="answer_text=71 / 칠십일, 일흔하나",
        rule_id="grade1_numbers_to_100_round3_5_tens_21_ones",
    ),
    10: ElementaryVisualTemplate(
        problem_text="왼쪽 수보다 1만큼 더 큰 수를 찾아 써 보세요.",
        expression="answer_text=94",
        rule_id="grade1_numbers_to_100_round3_one_more_than_93",
    ),
}


_NUMBERS_TO_100_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="86보다 1만큼 더 큰 수를 찾으세요.",
        expression="answer=87",
        rule_id="grade1_numbers_to_100_round1_one_more_choice",
    ),
    2: ElementaryVisualTemplate(
        problem_text="수의 순서를 거꾸로 하여 쓰려고 합니다. 63, 62, □, □, 59에서 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=빈칸: 61, 60",
        rule_id="grade1_numbers_to_100_round1_descending_blanks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="68과 86의 크기를 비교하여 알맞은 부등호를 쓰세요.",
        expression="answer_text=<",
        rule_id="grade1_numbers_to_100_round1_compare_sign",
    ),
    4: ElementaryVisualTemplate(
        problem_text="79, 89, 95 중 가장 큰 수에 ○표, 가장 작은 수에 △표 하세요.",
        expression="answer_text=95에 ○표, 79에 △표",
        rule_id="grade1_numbers_to_100_round1_largest_smallest_marks",
    ),
    5: ElementaryVisualTemplate(
        problem_text="10개씩 묶음 9개와 낱개 9개가 나타내는 수보다 1만큼 더 큰 수를 구하세요.",
        expression="answer=100",
        rule_id="grade1_numbers_to_100_round1_one_more_than_99",
    ),
    6: ElementaryVisualTemplate(
        problem_text="색종이 91장에 9장을 더 받으면 모두 100장입니다.",
        expression="answer_text=100장",
        rule_id="grade1_numbers_to_100_round1_91_plus_9",
    ),
    7: ElementaryVisualTemplate(
        problem_text="수를 순서대로 쓸 때 54와 58 사이에 있는 수를 모두 쓰세요.",
        expression="answer_text=55, 56, 57",
        rule_id="grade1_numbers_to_100_round1_between_54_58",
    ),
    8: ElementaryVisualTemplate(
        problem_text="0부터 9까지의 수 중에서 7□ < 72를 만족하는 수를 모두 구하세요.",
        expression="answer_text=0, 1",
        rule_id="grade1_numbers_to_100_round1_digit_inequality",
    ),
    9: ElementaryVisualTemplate(
        problem_text="수 카드 3, 7, 4 중에서 2장을 골라 한 번씩만 사용하여 만들 수 있는 수 중 가장 큰 수를 구하세요.",
        expression="answer=74",
        rule_id="grade1_numbers_to_100_round1_largest_two_digit_card",
    ),
    10: ElementaryVisualTemplate(
        problem_text="6, 82, 27, 38, 51, 58에서 홀수와 짝수는 각각 몇 개인지 구하세요.",
        expression="answer_text=홀수: 2개 / 짝수: 4개",
        rule_id="grade1_numbers_to_100_round1_odd_even_count",
    ),
    11: ElementaryVisualTemplate(
        problem_text="28, 63, 71, 88 중 홀수를 찾아 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=63, 71",
        rule_id="grade1_numbers_to_100_round1_odd_numbers",
    ),
}


_NUMBERS_TO_100_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="53보다 1만큼 더 작은 수를 찾으세요.",
        expression="answer=52",
        rule_id="grade1_numbers_to_100_round2_one_less_choice",
    ),
    2: ElementaryVisualTemplate(
        problem_text="수의 순서를 거꾸로 하여 쓰려고 합니다. 78, □, 76, □, 74에서 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=빈칸: 77, 75",
        rule_id="grade1_numbers_to_100_round2_descending_blanks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="59와 61의 크기를 비교하여 알맞은 부등호를 쓰세요.",
        expression="answer_text=<",
        rule_id="grade1_numbers_to_100_round2_compare_sign",
    ),
    4: ElementaryVisualTemplate(
        problem_text="81, 98, 78 중 가장 큰 수에 ○표, 가장 작은 수에 △표 하세요.",
        expression="answer_text=98에 ○표, 78에 △표",
        rule_id="grade1_numbers_to_100_round2_largest_smallest_marks",
    ),
    5: ElementaryVisualTemplate(
        problem_text="10개씩 묶음 7개와 낱개 9개가 나타내는 수보다 1만큼 더 큰 수를 구하세요.",
        expression="answer=80",
        rule_id="grade1_numbers_to_100_round2_one_more_than_79",
    ),
    6: ElementaryVisualTemplate(
        problem_text="상자에 구슬 98개가 있습니다. 구슬 2개를 더 넣으면 모두 100개입니다.",
        expression="answer_text=100개",
        rule_id="grade1_numbers_to_100_round2_98_plus_2",
    ),
    7: ElementaryVisualTemplate(
        problem_text="수를 순서대로 쓸 때 69와 72 사이에 있는 수를 모두 쓰세요.",
        expression="answer_text=70, 71",
        rule_id="grade1_numbers_to_100_round2_between_69_72",
    ),
    8: ElementaryVisualTemplate(
        problem_text="0부터 9까지의 수 중에서 8□ < 84를 만족하는 수를 모두 구하세요.",
        expression="answer_text=0, 1, 2, 3",
        rule_id="grade1_numbers_to_100_round2_digit_inequality",
    ),
    9: ElementaryVisualTemplate(
        problem_text="수 카드 9, 3, 6 중에서 2장을 골라 한 번씩만 사용하여 만들 수 있는 수 중 가장 큰 수를 구하세요.",
        expression="answer=96",
        rule_id="grade1_numbers_to_100_round2_largest_two_digit_card",
    ),
    10: ElementaryVisualTemplate(
        problem_text="9, 69, 29, 60, 52, 89에서 홀수와 짝수는 각각 몇 개인지 구하세요.",
        expression="answer_text=홀수: 4개 / 짝수: 2개",
        rule_id="grade1_numbers_to_100_round2_odd_even_count",
    ),
    11: ElementaryVisualTemplate(
        problem_text="27, 72, 57, 52 중 홀수를 찾아 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=27, 57",
        rule_id="grade1_numbers_to_100_round2_odd_numbers",
    ),
}


_NUMBERS_TO_100_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수의 순서를 거꾸로 하여 쓰려고 합니다. 89, 88, □, □, 85에서 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=빈칸: 87, 86",
        rule_id="grade1_numbers_to_100_round3_descending_blanks",
    ),
    2: ElementaryVisualTemplate(
        problem_text="79와 78의 크기를 비교하여 알맞은 부등호를 쓰세요.",
        expression="answer_text=>",
        rule_id="grade1_numbers_to_100_round3_compare_sign",
    ),
    3: ElementaryVisualTemplate(
        problem_text="59, 95, 85 중 가장 큰 수에 ○표, 가장 작은 수에 △표 하세요.",
        expression="answer_text=95에 ○표, 59에 △표",
        rule_id="grade1_numbers_to_100_round3_largest_smallest_marks",
    ),
    4: ElementaryVisualTemplate(
        problem_text="10개씩 묶음 8개와 낱개 9개가 나타내는 수보다 1만큼 더 큰 수를 구하세요.",
        expression="answer=90",
        rule_id="grade1_numbers_to_100_round3_one_more_than_89",
    ),
    5: ElementaryVisualTemplate(
        problem_text="상자에 탁구공 95개가 있습니다. 탁구공 5개를 더 넣으면 모두 100개입니다.",
        expression="answer_text=100개",
        rule_id="grade1_numbers_to_100_round3_95_plus_5",
    ),
    6: ElementaryVisualTemplate(
        problem_text="수를 순서대로 쓸 때 88과 93 사이에 있는 수를 모두 쓰세요.",
        expression="answer_text=89, 90, 91, 92",
        rule_id="grade1_numbers_to_100_round3_between_88_93",
    ),
    7: ElementaryVisualTemplate(
        problem_text="0부터 9까지의 수 중에서 9□ < 93을 만족하는 수를 모두 구하세요.",
        expression="answer_text=0, 1, 2",
        rule_id="grade1_numbers_to_100_round3_digit_inequality",
    ),
    8: ElementaryVisualTemplate(
        problem_text="수 카드 2, 9, 8 중에서 2장을 골라 한 번씩만 사용하여 만들 수 있는 수 중 가장 작은 수를 구하세요.",
        expression="answer=28",
        rule_id="grade1_numbers_to_100_round3_smallest_two_digit_card",
    ),
    9: ElementaryVisualTemplate(
        problem_text="1, 52, 33, 62, 78, 99에서 홀수와 짝수는 각각 몇 개인지 구하세요.",
        expression="answer_text=홀수: 3개 / 짝수: 3개",
        rule_id="grade1_numbers_to_100_round3_odd_even_count",
    ),
    10: ElementaryVisualTemplate(
        problem_text="68, 51, 86, 89 중 짝수를 찾아 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=68, 86",
        rule_id="grade1_numbers_to_100_round3_even_numbers",
    ),
}


_ADD_SUB_100_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림을 보고 30 + □ = □에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 10, 40",
        rule_id="grade1_add_sub_100_round1_visual_30_plus_10",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그림을 보고 49 - 4 = □에 알맞은 수를 써넣으세요.",
        expression="answer=45",
        rule_id="grade1_add_sub_100_round1_visual_49_minus_4",
    ),
    3: ElementaryVisualTemplate(
        problem_text="5와 52의 합을 구하세요.",
        expression="answer=57",
        rule_id="grade1_add_sub_100_round1_sum_5_52",
    ),
    4: ElementaryVisualTemplate(
        problem_text="30 + 23과 22 + 32 중 합이 더 큰 곳에 ○표 하세요.",
        expression="answer_text=22 + 32에 ○표",
        rule_id="grade1_add_sub_100_round1_larger_sum",
    ),
    5: ElementaryVisualTemplate(
        problem_text="65 - 40의 값을 구하세요.",
        expression="answer=25",
        rule_id="grade1_add_sub_100_round1_65_minus_40",
    ),
    6: ElementaryVisualTemplate(
        problem_text="□6 + 3□ = 78에서 □ 안에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 4, 2",
        rule_id="grade1_add_sub_100_round1_vertical_addition_blanks",
    ),
    7: ElementaryVisualTemplate(
        problem_text="덧셈을 해 보고 바로 다음에 올 덧셈식을 쓰세요.",
        expression="answer_text=35, 36, 37, 38 / 32 + 7 = 39",
        rule_id="grade1_add_sub_100_round1_next_addition_pattern",
    ),
}


_ADD_SUB_100_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="뺄셈을 해 보고 바로 다음에 올 뺄셈식을 쓰세요.",
        expression="answer_text=55, 54, 53 / 56 - 4 = 52",
        rule_id="grade1_add_sub_100_round1_next_subtraction_pattern",
    ),
    2: ElementaryVisualTemplate(
        problem_text="수 카드 3, 6, 9를 한 번씩만 사용하여 합이 가장 큰 덧셈식을 만들고 합을 구하세요.",
        expression="answer=99",
        rule_id="grade1_add_sub_100_round1_largest_sum_cards",
    ),
    3: ElementaryVisualTemplate(
        problem_text="보기와 같은 방법으로 47 - 23을 계산하세요.",
        expression="answer_text=빈칸: 20, 27, 27, 3, 24",
        rule_id="grade1_add_sub_100_round1_decompose_subtraction",
    ),
    4: ElementaryVisualTemplate(
        problem_text="37에서 3을 빼고 4를 더하세요.",
        expression="answer_text=34, 38",
        rule_id="grade1_add_sub_100_round1_minus_then_plus",
    ),
    5: ElementaryVisualTemplate(
        problem_text="60 + 10과 80 - 20의 계산 결과를 비교하세요.",
        expression="answer_text=>",
        rule_id="grade1_add_sub_100_round1_compare_results",
    ),
    6: ElementaryVisualTemplate(
        problem_text="두 수를 골라 합이 50이 되도록 덧셈식을 쓰세요.",
        expression="answer_text=20 + 30 = 50",
        rule_id="grade1_add_sub_100_round1_make_50",
    ),
    7: ElementaryVisualTemplate(
        problem_text="23, 56, 11, 40 중 가장 큰 수와 가장 작은 수의 합과 차를 구하세요.",
        expression="answer_text=합: 67 / 차: 45",
        rule_id="grade1_add_sub_100_round1_largest_smallest_sum_difference",
    ),
    8: ElementaryVisualTemplate(
        problem_text="계산 결과가 큰 것부터 차례대로 기호를 쓰세요.",
        expression="answer_text=가, 나, 다",
        rule_id="grade1_add_sub_100_round1_order_by_result",
    ),
    9: ElementaryVisualTemplate(
        problem_text="지영이는 책을 아침에 10쪽, 저녁에 30쪽 읽었습니다. 모두 40쪽 읽었습니다.",
        expression="answer_text=40쪽",
        rule_id="grade1_add_sub_100_round1_pages_read",
    ),
}


_ADD_SUB_100_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="모자를 쓴 학생이 23명, 모자를 쓰지 않은 학생이 15명입니다. 교실에 있는 학생은 모두 38명입니다.",
        expression="answer_text=38명",
        rule_id="grade1_add_sub_100_round1_students_total",
    ),
    2: ElementaryVisualTemplate(
        problem_text="희수는 사탕 19개, 지윤이는 사탕 8개를 가지고 있습니다. 희수는 지윤이보다 11개 더 가지고 있습니다.",
        expression="answer_text=11개",
        rule_id="grade1_add_sub_100_round1_candy_difference",
    ),
    3: ElementaryVisualTemplate(
        problem_text="도서관에 동화책이 58권 있었고 32권 남았습니다. 빌려간 동화책은 26권입니다.",
        expression="answer_text=26권",
        rule_id="grade1_add_sub_100_round1_books_borrowed",
    ),
    4: ElementaryVisualTemplate(
        problem_text="축구공이 68개, 배구공이 33개 있습니다. 축구공이 35개 더 많습니다.",
        expression="answer_text=축구공, 35개",
        rule_id="grade1_add_sub_100_round1_ball_difference",
    ),
}


_ADD_SUB_100_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림을 보고 30 + □ = □에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 7, 37",
        rule_id="grade1_add_sub_100_round2_visual_30_plus_7",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그림을 보고 37 - 3 = □에 알맞은 수를 써넣으세요.",
        expression="answer=34",
        rule_id="grade1_add_sub_100_round2_visual_37_minus_3",
    ),
    3: ElementaryVisualTemplate(
        problem_text="82와 3의 합을 구하세요.",
        expression="answer=85",
        rule_id="grade1_add_sub_100_round2_sum_82_3",
    ),
    4: ElementaryVisualTemplate(
        problem_text="20 + 56과 50 + 24 중 합이 더 큰 곳에 ○표 하세요.",
        expression="answer_text=20 + 56에 ○표",
        rule_id="grade1_add_sub_100_round2_larger_sum",
    ),
    5: ElementaryVisualTemplate(
        problem_text="89 - 50의 값을 구하세요.",
        expression="answer=39",
        rule_id="grade1_add_sub_100_round2_89_minus_50",
    ),
    6: ElementaryVisualTemplate(
        problem_text="□2 + 3□ = 95에서 □ 안에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 6, 3",
        rule_id="grade1_add_sub_100_round2_vertical_addition_blanks",
    ),
    7: ElementaryVisualTemplate(
        problem_text="덧셈을 해 보고 바로 다음에 올 덧셈식을 쓰세요.",
        expression="answer_text=23, 24, 25, 26 / 21 + 6 = 27",
        rule_id="grade1_add_sub_100_round2_next_addition_pattern",
    ),
    8: ElementaryVisualTemplate(
        problem_text="뺄셈을 해 보고 바로 다음에 올 뺄셈식을 쓰세요.",
        expression="answer_text=77, 76, 75 / 78 - 4 = 74",
        rule_id="grade1_add_sub_100_round2_next_subtraction_pattern",
    ),
}


_ADD_SUB_100_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수 카드 1, 4, 7을 한 번씩만 사용하여 합이 가장 큰 덧셈식을 만들고 합을 구하세요.",
        expression="answer=75",
        rule_id="grade1_add_sub_100_round2_largest_sum_cards",
    ),
    2: ElementaryVisualTemplate(
        problem_text="보기와 같은 방법으로 54 - 13을 계산하세요.",
        expression="answer_text=빈칸: 10, 44, 44, 3, 41",
        rule_id="grade1_add_sub_100_round2_decompose_subtraction",
    ),
    3: ElementaryVisualTemplate(
        problem_text="그림의 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 78, 23",
        rule_id="grade1_add_sub_100_round2_operation_grid",
    ),
    4: ElementaryVisualTemplate(
        problem_text="50 + 30과 70 - 10의 계산 결과를 비교하세요.",
        expression="answer_text=>",
        rule_id="grade1_add_sub_100_round2_compare_results",
    ),
    5: ElementaryVisualTemplate(
        problem_text="두 수를 골라 차가 40이 되도록 뺄셈식을 쓰세요.",
        expression="answer_text=70 - 30 = 40",
        rule_id="grade1_add_sub_100_round2_make_difference_40",
    ),
    6: ElementaryVisualTemplate(
        problem_text="36, 22, 75, 43 중 가장 큰 수와 가장 작은 수의 합과 차를 구하세요.",
        expression="answer_text=합: 97 / 차: 53",
        rule_id="grade1_add_sub_100_round2_largest_smallest_sum_difference",
    ),
    7: ElementaryVisualTemplate(
        problem_text="계산 결과가 큰 것부터 차례대로 기호를 쓰세요.",
        expression="answer_text=다, 가, 나",
        rule_id="grade1_add_sub_100_round2_order_by_result",
    ),
    8: ElementaryVisualTemplate(
        problem_text="클립이 한 통에 30개 들어 있습니다. 2통에는 모두 60개가 들어 있습니다.",
        expression="answer_text=60개",
        rule_id="grade1_add_sub_100_round2_clips_total",
    ),
    9: ElementaryVisualTemplate(
        problem_text="줄넘기를 하는 학생 37명과 피구를 하는 학생 21명이 있습니다. 모두 58명입니다.",
        expression="answer_text=58명",
        rule_id="grade1_add_sub_100_round2_students_total",
    ),
}


_ADD_SUB_100_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="연필 48자루 중 12자루를 주었습니다. 남은 연필은 36자루입니다.",
        expression="answer_text=36자루",
        rule_id="grade1_add_sub_100_round2_pencils_left",
    ),
    2: ElementaryVisualTemplate(
        problem_text="희선이네 반 학생은 26명이고 우진이네 반 학생은 22명입니다. 희선이네 반이 4명 더 많습니다.",
        expression="answer_text=4명",
        rule_id="grade1_add_sub_100_round2_class_difference",
    ),
    3: ElementaryVisualTemplate(
        problem_text="닭장 안에는 닭이 24마리, 닭장 밖에는 13마리 있습니다. 닭장 안에 11마리 더 많습니다.",
        expression="answer_text=닭장 안, 11마리",
        rule_id="grade1_add_sub_100_round2_chicken_difference",
    ),
}


_ADD_SUB_100_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림을 보고 40 + □ = □에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 6, 46",
        rule_id="grade1_add_sub_100_round3_visual_40_plus_6",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그림을 보고 35 - 2 = □에 알맞은 수를 써넣으세요.",
        expression="answer=33",
        rule_id="grade1_add_sub_100_round3_visual_35_minus_2",
    ),
    3: ElementaryVisualTemplate(
        problem_text="23과 6의 합을 구하세요.",
        expression="answer=29",
        rule_id="grade1_add_sub_100_round3_sum_23_6",
    ),
    4: ElementaryVisualTemplate(
        problem_text="30 + 45와 32 + 44 중 합이 더 큰 곳에 ○표 하세요.",
        expression="answer_text=32 + 44에 ○표",
        rule_id="grade1_add_sub_100_round3_larger_sum",
    ),
    5: ElementaryVisualTemplate(
        problem_text="62 - 20의 값을 구하세요.",
        expression="answer=42",
        rule_id="grade1_add_sub_100_round3_62_minus_20",
    ),
    6: ElementaryVisualTemplate(
        problem_text="덧셈을 해 보고 바로 다음에 올 덧셈식을 쓰세요.",
        expression="answer_text=82, 83, 84, 85 / 81 + 5 = 86",
        rule_id="grade1_add_sub_100_round3_next_addition_pattern",
    ),
    7: ElementaryVisualTemplate(
        problem_text="뺄셈을 해 보고 바로 다음에 올 뺄셈식을 쓰세요.",
        expression="answer_text=66, 65, 64, 63 / 64 - 2 = 62",
        rule_id="grade1_add_sub_100_round3_next_subtraction_pattern",
    ),
}


_ADD_SUB_100_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="□ 안에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 6, 3",
        rule_id="grade1_add_sub_100_round3_vertical_addition_blanks",
    ),
    2: ElementaryVisualTemplate(
        problem_text="수 카드 2, 3, 6을 한 번씩만 사용하여 합이 가장 큰 덧셈식을 만들고 합을 구하세요.",
        expression="answer=29",
        rule_id="grade1_add_sub_100_round3_largest_sum_cards",
    ),
    3: ElementaryVisualTemplate(
        problem_text="보기와 같은 방법으로 86 - 24를 계산하세요.",
        expression="answer_text=빈칸: 20, 60, 6, 2, 60, 62",
        rule_id="grade1_add_sub_100_round3_decompose_subtraction",
    ),
    4: ElementaryVisualTemplate(
        problem_text="그림의 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 88, 32",
        rule_id="grade1_add_sub_100_round3_operation_grid",
    ),
    5: ElementaryVisualTemplate(
        problem_text="30 + 20과 90 - 30의 계산 결과를 비교하세요.",
        expression="answer_text=<",
        rule_id="grade1_add_sub_100_round3_compare_results",
    ),
    6: ElementaryVisualTemplate(
        problem_text="두 수를 골라 합이 60이 되도록 덧셈식을 쓰세요.",
        expression="answer_text=20 + 40 = 60",
        rule_id="grade1_add_sub_100_round3_make_60",
    ),
    7: ElementaryVisualTemplate(
        problem_text="21, 48, 65, 23 중 가장 큰 수와 가장 작은 수의 합과 차를 구하세요.",
        expression="answer_text=합: 86 / 차: 44",
        rule_id="grade1_add_sub_100_round3_largest_smallest_sum_difference",
    ),
    8: ElementaryVisualTemplate(
        problem_text="계산 결과가 작은 것부터 차례대로 기호를 쓰세요.",
        expression="answer_text=나, 가, 다",
        rule_id="grade1_add_sub_100_round3_order_by_result",
    ),
    9: ElementaryVisualTemplate(
        problem_text="초콜릿이 한 봉지에 40개 들어 있습니다. 2봉지에는 모두 80개가 들어 있습니다.",
        expression="answer_text=80개",
        rule_id="grade1_add_sub_100_round3_chocolates_total",
    ),
}


_ADD_SUB_100_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="화단에 장미 64송이와 튤립 25송이가 있습니다. 화단에 있는 꽃은 모두 89송이입니다.",
        expression="answer_text=89송이",
        rule_id="grade1_add_sub_100_round3_flowers_total",
    ),
    2: ElementaryVisualTemplate(
        problem_text="빵집에 식빵이 35개 있었고 15개를 팔았습니다. 남은 식빵은 20개입니다.",
        expression="answer_text=20개",
        rule_id="grade1_add_sub_100_round3_bread_left",
    ),
    3: ElementaryVisualTemplate(
        problem_text="진우는 연필 32자루, 색연필 47자루를 가지고 있습니다. 색연필을 연필보다 15자루 더 많이 가지고 있습니다.",
        expression="answer_text=15자루",
        rule_id="grade1_add_sub_100_round3_pencil_difference",
    ),
    4: ElementaryVisualTemplate(
        problem_text="영희는 사탕 47개, 승윤이는 사탕 31개를 가지고 있습니다. 영희의 사탕이 16개 더 많습니다.",
        expression="answer_text=영희, 16개",
        rule_id="grade1_add_sub_100_round3_candy_difference",
    ),
}


_ADD_SUB_10_THREE_TERMS_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림에 알맞은 식을 만들고 계산하세요.",
        expression="answer_text=빈칸: 3, 3, 2, 8",
        rule_id="grade1_add_sub_10_three_terms_round1_fruit_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그림을 보고 □ + □ = 10에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 4, 6",
        rule_id="grade1_add_sub_10_three_terms_round1_vegetable_make_10",
    ),
    3: ElementaryVisualTemplate(
        problem_text="그림을 보고 10 - □ = □에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 2, 8",
        rule_id="grade1_add_sub_10_three_terms_round1_visual_10_minus_2",
    ),
    4: ElementaryVisualTemplate(
        problem_text="3 + 2 + 3과 1 + 5 + 1의 합을 구하세요.",
        expression="answer_text=빈칸: 8, 7",
        rule_id="grade1_add_sub_10_three_terms_round1_three_addends",
    ),
    5: ElementaryVisualTemplate(
        problem_text="4 + 8 + 2와 3 + 3 + 7의 계산 결과를 비교하세요.",
        expression="answer_text=>",
        rule_id="grade1_add_sub_10_three_terms_round1_compare_sums",
    ),
    6: ElementaryVisualTemplate(
        problem_text="8 + 3, 9 + 1, 3 + 6 중 합이 10이 되는 식에 ○표 하세요.",
        expression="answer_text=9 + 1에 ○표",
        rule_id="grade1_add_sub_10_three_terms_round1_make_10_choice",
    ),
    7: ElementaryVisualTemplate(
        problem_text="5 - 3 - 1과 6 - 4 - 2의 차를 구하세요.",
        expression="answer_text=빈칸: 1, 0",
        rule_id="grade1_add_sub_10_three_terms_round1_three_subtractions",
    ),
    8: ElementaryVisualTemplate(
        problem_text="3 + 2 + 3의 중간 계산과 결과를 써넣으세요.",
        expression="answer_text=빈칸: 5, 8, 8",
        rule_id="grade1_add_sub_10_three_terms_round1_addition_steps",
    ),
}


_ADD_SUB_10_THREE_TERMS_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="6 + 4 + 2와 1 + 4 + 9 중 세 수의 합이 더 큰 쪽에 ○표 하세요.",
        expression="answer_text=1 + 4 + 9에 ○표",
        rule_id="grade1_add_sub_10_three_terms_round1_larger_three_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="9 - 4 - 2의 중간 계산과 결과를 써넣으세요.",
        expression="answer_text=빈칸: 5, 3, 3",
        rule_id="grade1_add_sub_10_three_terms_round1_subtraction_steps",
    ),
    3: ElementaryVisualTemplate(
        problem_text="7 - 3 - 2와 6 - 2 - 1의 계산 결과를 비교하세요.",
        expression="answer_text=<",
        rule_id="grade1_add_sub_10_three_terms_round1_compare_differences",
    ),
    4: ElementaryVisualTemplate(
        problem_text="9 - 7 - 1과 3 + 1 + 4 중 계산 결과가 짝수인 것에 ○표 하세요.",
        expression="answer_text=3 + 1 + 4에 ○표",
        rule_id="grade1_add_sub_10_three_terms_round1_even_result_choice",
    ),
    5: ElementaryVisualTemplate(
        problem_text="같은 모양은 같은 수입니다. 하트가 나타내는 수를 구하세요.",
        expression="answer=6",
        rule_id="grade1_add_sub_10_three_terms_round1_shape_value",
    ),
    6: ElementaryVisualTemplate(
        problem_text="7 + 6의 계산 결과 13을 오른쪽에서 찾아 ○표 하세요.",
        expression="answer_text=13에 ○표",
        rule_id="grade1_add_sub_10_three_terms_round1_find_result",
    ),
    7: ElementaryVisualTemplate(
        problem_text="9 + □ = 17에서 □ 안에 알맞은 수를 써넣으세요.",
        expression="answer=8",
        rule_id="grade1_add_sub_10_three_terms_round1_addition_blank",
    ),
    8: ElementaryVisualTemplate(
        problem_text="수 카드 4, 5, 6, 1, 3 중 4와 6을 사용하여 합이 10이 되었습니다. 남은 세 수의 합을 구하세요.",
        expression="answer=9",
        rule_id="grade1_add_sub_10_three_terms_round1_remaining_cards_sum",
    ),
}


_ADD_SUB_10_THREE_TERMS_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="연필을 6자루 더 넣었더니 10자루가 되었습니다. 처음 상자에 들어 있던 연필은 4자루입니다.",
        expression="answer_text=4자루",
        rule_id="grade1_add_sub_10_three_terms_round1_initial_pencils",
    ),
    2: ElementaryVisualTemplate(
        problem_text="어항에 물고기가 7마리 있습니다. 4마리를 더 넣으면 모두 11마리입니다.",
        expression="answer_text=11마리",
        rule_id="grade1_add_sub_10_three_terms_round1_fish_total",
    ),
    3: ElementaryVisualTemplate(
        problem_text="동화책 5권, 위인전 5권, 역사책 3권을 읽었습니다. 모두 13권입니다.",
        expression="answer_text=13권",
        rule_id="grade1_add_sub_10_three_terms_round1_books_total",
    ),
    4: ElementaryVisualTemplate(
        problem_text="버스에 7명이 타고 있었습니다. 박물관 앞에서 3명, 동물원 앞에서 2명이 내렸습니다. 남은 사람은 2명입니다.",
        expression="answer_text=2명",
        rule_id="grade1_add_sub_10_three_terms_round1_bus_left",
    ),
}


_ADD_SUB_10_THREE_TERMS_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림에 알맞은 식을 만들고 계산하세요.",
        expression="answer_text=빈칸: 2, 2, 3, 7",
        rule_id="grade1_add_sub_10_three_terms_round2_candy_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그림을 보고 □ + □ = 10에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 3, 7",
        rule_id="grade1_add_sub_10_three_terms_round2_make_10",
    ),
    3: ElementaryVisualTemplate(
        problem_text="그림을 보고 10 - □ = □에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 3, 7",
        rule_id="grade1_add_sub_10_three_terms_round2_visual_10_minus_3",
    ),
    4: ElementaryVisualTemplate(
        problem_text="2 + 4 + 3과 2 + 1 + 5의 합을 구하세요.",
        expression="answer_text=빈칸: 9, 8",
        rule_id="grade1_add_sub_10_three_terms_round2_three_addends",
    ),
    5: ElementaryVisualTemplate(
        problem_text="4 + 6 + 2와 5 + 5 + 3의 계산 결과를 비교하세요.",
        expression="answer_text=<",
        rule_id="grade1_add_sub_10_three_terms_round2_compare_sums",
    ),
    6: ElementaryVisualTemplate(
        problem_text="8 + 2, 9 + 2, 4 + 7 중 합이 10이 되는 식에 ○표 하세요.",
        expression="answer_text=8 + 2에 ○표",
        rule_id="grade1_add_sub_10_three_terms_round2_make_10_choice",
    ),
    7: ElementaryVisualTemplate(
        problem_text="8 - 3 - 3과 9 - 1 - 3의 차를 구하세요.",
        expression="answer_text=빈칸: 2, 5",
        rule_id="grade1_add_sub_10_three_terms_round2_three_subtractions",
    ),
    8: ElementaryVisualTemplate(
        problem_text="2 + 5 + 1의 중간 계산과 결과를 써넣으세요.",
        expression="answer_text=빈칸: 7, 8, 8",
        rule_id="grade1_add_sub_10_three_terms_round2_addition_steps",
    ),
}


_ADD_SUB_10_THREE_TERMS_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="3 + 1 + 7과 2 + 3 + 8 중 세 수의 합이 더 작은 쪽에 ○표 하세요.",
        expression="answer_text=3 + 1 + 7에 ○표",
        rule_id="grade1_add_sub_10_three_terms_round2_smaller_three_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="7 - 2 - 1의 중간 계산과 결과를 써넣으세요.",
        expression="answer_text=빈칸: 5, 4, 4",
        rule_id="grade1_add_sub_10_three_terms_round2_subtraction_steps",
    ),
    3: ElementaryVisualTemplate(
        problem_text="7 - 1 - 6과 9 - 4 - 4의 계산 결과를 비교하세요.",
        expression="answer_text=<",
        rule_id="grade1_add_sub_10_three_terms_round2_compare_differences",
    ),
    4: ElementaryVisualTemplate(
        problem_text="9 - 1 - 1과 2 + 1 + 5 중 계산 결과가 홀수인 것에 ○표 하세요.",
        expression="answer_text=9 - 1 - 1에 ○표",
        rule_id="grade1_add_sub_10_three_terms_round2_odd_result_choice",
    ),
    5: ElementaryVisualTemplate(
        problem_text="같은 모양은 같은 수입니다. 하트가 나타내는 수를 구하세요.",
        expression="answer=8",
        rule_id="grade1_add_sub_10_three_terms_round2_shape_value",
    ),
    6: ElementaryVisualTemplate(
        problem_text="8 + 7의 계산 결과 15를 오른쪽에서 찾아 ○표 하세요.",
        expression="answer_text=15에 ○표",
        rule_id="grade1_add_sub_10_three_terms_round2_find_result",
    ),
    7: ElementaryVisualTemplate(
        problem_text="9 + □ = 16에서 □ 안에 알맞은 수를 써넣으세요.",
        expression="answer=7",
        rule_id="grade1_add_sub_10_three_terms_round2_addition_blank",
    ),
    8: ElementaryVisualTemplate(
        problem_text="수 카드 2, 7, 1, 8, 1 중 2와 8을 사용하여 합이 10이 되었습니다. 남은 세 수의 합을 구하세요.",
        expression="answer=9",
        rule_id="grade1_add_sub_10_three_terms_round2_remaining_cards_sum",
    ),
    9: ElementaryVisualTemplate(
        problem_text="선아는 8살입니다. 10살이 되려면 2살을 더 먹어야 합니다.",
        expression="answer_text=2살",
        rule_id="grade1_add_sub_10_three_terms_round2_age_to_10",
    ),
}


_ADD_SUB_10_THREE_TERMS_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="지난주에 칭찬스티커 8장을 모았고 이번주에 4장을 더 모았습니다. 모두 12장입니다.",
        expression="answer_text=12장",
        rule_id="grade1_add_sub_10_three_terms_round2_stickers_total",
    ),
    2: ElementaryVisualTemplate(
        problem_text="딸기 맛 사탕 2개, 수박 맛 사탕 5개, 포도 맛 사탕 8개를 가지고 있습니다. 모두 15개입니다.",
        expression="answer_text=15개",
        rule_id="grade1_add_sub_10_three_terms_round2_candies_total",
    ),
    3: ElementaryVisualTemplate(
        problem_text="운동장에 8명의 학생이 있었습니다. 2명은 교실로, 3명은 체육관으로 갔습니다. 남은 학생은 3명입니다.",
        expression="answer_text=3명",
        rule_id="grade1_add_sub_10_three_terms_round2_students_left",
    ),
}


_ADD_SUB_10_THREE_TERMS_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림에 알맞은 식을 만들고 계산하세요.",
        expression="answer_text=빈칸: 4, 3, 2, 9",
        rule_id="grade1_add_sub_10_three_terms_round3_vegetable_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그림을 보고 □ + □ = 10에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 5, 5",
        rule_id="grade1_add_sub_10_three_terms_round3_make_10",
    ),
    3: ElementaryVisualTemplate(
        problem_text="그림을 보고 10 - □ = □에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 4, 6",
        rule_id="grade1_add_sub_10_three_terms_round3_visual_10_minus_4",
    ),
    4: ElementaryVisualTemplate(
        problem_text="4 + 1 + 1과 2 + 3 + 2의 합을 구하세요.",
        expression="answer_text=빈칸: 6, 7",
        rule_id="grade1_add_sub_10_three_terms_round3_three_addends",
    ),
    5: ElementaryVisualTemplate(
        problem_text="7 + 3 + 5와 3 + 4 + 6의 계산 결과를 비교하세요.",
        expression="answer_text=>",
        rule_id="grade1_add_sub_10_three_terms_round3_compare_sums",
    ),
    6: ElementaryVisualTemplate(
        problem_text="4 + 5, 6 + 4, 7 + 2 중 합이 10이 되는 식에 ○표 하세요.",
        expression="answer_text=6 + 4에 ○표",
        rule_id="grade1_add_sub_10_three_terms_round3_make_10_choice",
    ),
    7: ElementaryVisualTemplate(
        problem_text="9 - 2 - 3과 8 - 4 - 1의 차를 구하세요.",
        expression="answer_text=빈칸: 4, 3",
        rule_id="grade1_add_sub_10_three_terms_round3_three_subtractions",
    ),
    8: ElementaryVisualTemplate(
        problem_text="3 + 1 + 3의 중간 계산과 결과를 써넣으세요.",
        expression="answer_text=빈칸: 4, 7, 7",
        rule_id="grade1_add_sub_10_three_terms_round3_addition_steps",
    ),
}


_ADD_SUB_10_THREE_TERMS_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="5 + 4 + 5와 9 + 3 + 1 중 세 수의 합이 더 큰 쪽에 ○표 하세요.",
        expression="answer_text=5 + 4 + 5에 ○표",
        rule_id="grade1_add_sub_10_three_terms_round3_larger_three_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="8 - 3 - 2의 중간 계산과 결과를 써넣으세요.",
        expression="answer_text=빈칸: 5, 3, 3",
        rule_id="grade1_add_sub_10_three_terms_round3_subtraction_steps",
    ),
    3: ElementaryVisualTemplate(
        problem_text="9 - 3 - 3과 8 - 3 - 1의 계산 결과를 비교하세요.",
        expression="answer_text=<",
        rule_id="grade1_add_sub_10_three_terms_round3_compare_differences",
    ),
    4: ElementaryVisualTemplate(
        problem_text="8 - 1 - 2와 2 + 3 + 3 중 계산 결과가 짝수인 것에 ○표 하세요.",
        expression="answer_text=2 + 3 + 3에 ○표",
        rule_id="grade1_add_sub_10_three_terms_round3_even_result_choice",
    ),
    5: ElementaryVisualTemplate(
        problem_text="같은 모양은 같은 수입니다. 하트가 나타내는 수를 구하세요.",
        expression="answer=7",
        rule_id="grade1_add_sub_10_three_terms_round3_shape_value",
    ),
    6: ElementaryVisualTemplate(
        problem_text="9 + 3의 계산 결과 12를 오른쪽에서 찾아 ○표 하세요.",
        expression="answer_text=12에 ○표",
        rule_id="grade1_add_sub_10_three_terms_round3_find_result",
    ),
    7: ElementaryVisualTemplate(
        problem_text="9 + □ = 15에서 □ 안에 알맞은 수를 써넣으세요.",
        expression="answer=6",
        rule_id="grade1_add_sub_10_three_terms_round3_addition_blank",
    ),
    8: ElementaryVisualTemplate(
        problem_text="수 카드 2, 7, 4, 1, 3 중 7과 3을 사용하여 합이 10이 되었습니다. 남은 세 수의 합을 구하세요.",
        expression="answer=7",
        rule_id="grade1_add_sub_10_three_terms_round3_remaining_cards_sum",
    ),
    9: ElementaryVisualTemplate(
        problem_text="지우개가 7개 들어 있는 상자에 몇 개의 지우개를 더 넣으면 10개가 될까요?",
        expression="answer_text=3개",
        rule_id="grade1_add_sub_10_three_terms_round3_erasers_to_10",
    ),
}


_ADD_SUB_10_THREE_TERMS_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="색연필 7자루에 5자루를 더 받았습니다. 모두 12자루입니다.",
        expression="answer_text=12자루",
        rule_id="grade1_add_sub_10_three_terms_round3_pencils_total",
    ),
    2: ElementaryVisualTemplate(
        problem_text="파란 구슬 3개, 빨간 구슬 4개, 노란 구슬 7개를 가지고 있습니다. 모두 14개입니다.",
        expression="answer_text=14개",
        rule_id="grade1_add_sub_10_three_terms_round3_beads_total",
    ),
    3: ElementaryVisualTemplate(
        problem_text="굴 6개 중 아침에 2개, 점심에 2개를 먹었습니다. 남은 굴은 2개입니다.",
        expression="answer_text=2개",
        rule_id="grade1_add_sub_10_three_terms_round3_oysters_left",
    ),
}


_CLOCK_PATTERN_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="시각을 읽어 보세요.",
        expression="answer_text=5시",
        topic="measurement",
        rule_id="grade1_clock_pattern_round1_read_5_oclock",
    ),
}


_CLOCK_PATTERN_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="시각을 읽어 보세요.",
        expression="answer_text=2시",
        topic="measurement",
        rule_id="grade1_clock_pattern_round2_read_2_oclock",
    ),
}


_CLOCK_PATTERN_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="37부터 시작하여 2씩 작아지는 규칙에 따라 빈칸에 수를 배열하세요.",
        expression="answer_text=35, 33, 31, 29, 27",
        topic="pattern",
        rule_id="grade1_clock_pattern_round2_decreasing_by_2",
    ),
    2: ElementaryVisualTemplate(
        problem_text="2시 30분에서 긴바늘이 한 바퀴 움직였을 때의 시각을 쓰세요.",
        expression="answer_text=3시 30분",
        topic="measurement",
        rule_id="grade1_clock_pattern_round2_one_hour_later",
    ),
    3: ElementaryVisualTemplate(
        problem_text="색칠한 수는 13부터 시작하여 몇씩 커지는지 구하세요.",
        expression="answer=4",
        topic="pattern",
        rule_id="grade1_clock_pattern_round2_colored_numbers_step",
    ),
}


_CLOCK_PATTERN_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="시계를 보고 시각을 읽으세요.",
        expression="answer_text=8시",
        topic="measurement",
        rule_id="grade1_clock_pattern_round3_read_8_oclock",
    ),
}


_CLOCK_PATTERN_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="46부터 시작하여 5씩 커지는 규칙에 따라 빈칸에 수를 배열하세요.",
        expression="answer_text=51, 56, 61, 66, 71",
        topic="pattern",
        rule_id="grade1_clock_pattern_round3_increasing_by_5",
    ),
    2: ElementaryVisualTemplate(
        problem_text="4시 30분에서 긴바늘이 한 바퀴 움직였을 때의 시각을 쓰세요.",
        expression="answer_text=5시 30분",
        topic="measurement",
        rule_id="grade1_clock_pattern_round3_one_hour_later",
    ),
    3: ElementaryVisualTemplate(
        problem_text="색칠한 수는 11부터 시작하여 몇씩 커지는지 구하세요.",
        expression="answer=3",
        topic="pattern",
        rule_id="grade1_clock_pattern_round3_colored_numbers_step",
    ),
}


_ADD_SUB_20_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="10을 이용하여 모으기와 가르기를 한 것입니다. 빈칸에 알맞은 수를 넣으세요.",
        expression="answer_text=빈칸: 12, 12, 2",
        rule_id="grade1_add_sub_20_round1_make_ten_compose",
    ),
    2: ElementaryVisualTemplate(
        problem_text="16 - 9의 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 7, 6",
        rule_id="grade1_add_sub_20_round1_16_minus_9",
    ),
    3: ElementaryVisualTemplate(
        problem_text="6 + 5의 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 11, 1",
        rule_id="grade1_add_sub_20_round1_6_plus_5",
    ),
    4: ElementaryVisualTemplate(
        problem_text="합이 11인 덧셈식을 모두 찾아 색칠하세요.",
        expression="answer_text=8 + 3, 3 + 8",
        rule_id="grade1_add_sub_20_round1_sum_11_choices",
    ),
    5: ElementaryVisualTemplate(
        problem_text="15 - 6의 값을 구하세요.",
        expression="answer=9",
        rule_id="grade1_add_sub_20_round1_15_minus_6",
    ),
    6: ElementaryVisualTemplate(
        problem_text="5 + 9의 값을 구하세요.",
        expression="answer=14",
        rule_id="grade1_add_sub_20_round1_5_plus_9",
    ),
    7: ElementaryVisualTemplate(
        problem_text="8 + □ = 15에서 □ 안에 알맞은 수를 쓰세요.",
        expression="answer=7",
        rule_id="grade1_add_sub_20_round1_addition_blank",
    ),
    8: ElementaryVisualTemplate(
        problem_text="6, 7, 5, 4 중 가장 작은 수와 가장 큰 수의 합을 구하세요.",
        expression="answer=11",
        rule_id="grade1_add_sub_20_round1_min_max_sum",
    ),
    9: ElementaryVisualTemplate(
        problem_text="9에서 7을 더하고 8을 빼세요.",
        expression="answer_text=빈칸: 16, 8",
        rule_id="grade1_add_sub_20_round1_plus_then_minus",
    ),
    10: ElementaryVisualTemplate(
        problem_text="16 - 9와 5 + 6의 계산 결과를 비교하세요.",
        expression="answer_text=<",
        rule_id="grade1_add_sub_20_round1_compare_results",
    ),
}


_ADD_SUB_20_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="9 + 6, 8 + 6, 7 + 6, 6 + 6의 빈칸을 채우고 알맞은 말에 ○표 하세요.",
        expression="answer_text=15, 14, 13, 12 / 작아집니다에 ○표",
        rule_id="grade1_add_sub_20_round1_decreasing_sums",
    ),
    2: ElementaryVisualTemplate(
        problem_text="15 - 6, 15 - 7, 15 - 8, 15 - 9의 빈칸을 채우고 알맞은 말에 ○표 하세요.",
        expression="answer_text=9, 8, 7, 6 / 작아집니다에 ○표",
        rule_id="grade1_add_sub_20_round1_decreasing_differences",
    ),
    3: ElementaryVisualTemplate(
        problem_text="12 - □ = 6, 12 - □ = 5, 12 - □ = 4, 12 - □ = 3에 알맞은 수를 쓰세요.",
        expression="answer_text=6, 7, 8, 9",
        rule_id="grade1_add_sub_20_round1_subtraction_blanks",
    ),
    4: ElementaryVisualTemplate(
        problem_text="수 카드 8, 4, 1 중 2장을 뽑아 가장 작은 몇십몇을 만들었습니다. 만든 수와 남은 수의 차를 구하세요.",
        expression="answer=6",
        rule_id="grade1_add_sub_20_round1_card_difference",
    ),
    5: ElementaryVisualTemplate(
        problem_text="11 - 6, 15 - 7, 7 + 4 중 계산 결과가 8인 것을 찾으세요.",
        expression="answer_text=15 - 7에 ○표",
        rule_id="grade1_add_sub_20_round1_find_result_8",
    ),
    6: ElementaryVisualTemplate(
        problem_text="11에서 어떤 수를 뺐더니 5가 되었습니다. 어떤 수를 구하세요.",
        expression="answer=6",
        rule_id="grade1_add_sub_20_round1_missing_subtrahend",
    ),
    7: ElementaryVisualTemplate(
        problem_text="스티커 6개를 붙인 후 5개를 더 붙였습니다. 모두 11개입니다.",
        expression="answer_text=11개",
        rule_id="grade1_add_sub_20_round1_stickers_total",
    ),
    8: ElementaryVisualTemplate(
        problem_text="수호는 딸기 7개와 귤 6개, 유진이는 딸기 9개와 귤 3개를 먹었습니다. 먹은 과일 수의 합이 더 큰 학생은 수호입니다.",
        expression="answer_text=수호",
        rule_id="grade1_add_sub_20_round1_more_fruit",
    ),
    9: ElementaryVisualTemplate(
        problem_text="사탕 12개 중 5개를 먹었습니다. 남은 사탕은 7개입니다.",
        expression="answer_text=7개",
        rule_id="grade1_add_sub_20_round1_candy_left",
    ),
    10: ElementaryVisualTemplate(
        problem_text="학생 14명에게 연필을 한 자루씩 나누어 주려고 합니다. 연필이 9자루 있으면 더 필요한 연필은 5자루입니다.",
        expression="answer_text=5자루",
        rule_id="grade1_add_sub_20_round1_pencils_needed",
    ),
}


_ADD_SUB_20_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="10을 이용하여 모으기와 가르기를 한 것입니다. 빈칸에 알맞은 수를 넣으세요.",
        expression="answer_text=빈칸: 16, 16, 6",
        rule_id="grade1_add_sub_20_round2_make_ten_compose",
    ),
    2: ElementaryVisualTemplate(
        problem_text="11 - 5의 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 6, 1",
        rule_id="grade1_add_sub_20_round2_11_minus_5",
    ),
    3: ElementaryVisualTemplate(
        problem_text="7 + 6의 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 13, 3",
        rule_id="grade1_add_sub_20_round2_7_plus_6",
    ),
    4: ElementaryVisualTemplate(
        problem_text="합이 12인 덧셈식을 모두 찾아 색칠하세요.",
        expression="answer_text=6 + 6, 7 + 5",
        rule_id="grade1_add_sub_20_round2_sum_12_choices",
    ),
    5: ElementaryVisualTemplate(
        problem_text="17 - 8의 값을 구하세요.",
        expression="answer=9",
        rule_id="grade1_add_sub_20_round2_17_minus_8",
    ),
    6: ElementaryVisualTemplate(
        problem_text="7 + 8의 값을 구하세요.",
        expression="answer=15",
        rule_id="grade1_add_sub_20_round2_7_plus_8",
    ),
    7: ElementaryVisualTemplate(
        problem_text="9 + □ = 12에서 □ 안에 알맞은 수를 쓰세요.",
        expression="answer=3",
        rule_id="grade1_add_sub_20_round2_addition_blank",
    ),
    8: ElementaryVisualTemplate(
        problem_text="6, 4, 3, 9 중 가장 작은 수와 가장 큰 수의 합을 구하세요.",
        expression="answer=12",
        rule_id="grade1_add_sub_20_round2_min_max_sum",
    ),
    9: ElementaryVisualTemplate(
        problem_text="7에서 8을 더하고 9를 빼세요.",
        expression="answer_text=빈칸: 15, 6",
        rule_id="grade1_add_sub_20_round2_plus_then_minus",
    ),
    10: ElementaryVisualTemplate(
        problem_text="17 - 8과 7 + 8의 계산 결과를 비교하세요.",
        expression="answer_text=<",
        rule_id="grade1_add_sub_20_round2_compare_results",
    ),
}


_ADD_SUB_20_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="8 + 9, 7 + 9, 6 + 9, 5 + 9의 빈칸을 채우고 알맞은 말에 ○표 하세요.",
        expression="answer_text=17, 16, 15, 14 / 작아집니다에 ○표",
        rule_id="grade1_add_sub_20_round2_decreasing_sums",
    ),
    2: ElementaryVisualTemplate(
        problem_text="11 - 5, 12 - 6, 13 - 7, 14 - 8의 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=6, 6, 6, 6",
        rule_id="grade1_add_sub_20_round2_same_differences",
    ),
    3: ElementaryVisualTemplate(
        problem_text="14 - □ = 6, 14 - □ = 7, 14 - □ = 8, 14 - □ = 9에 알맞은 수를 쓰세요.",
        expression="answer_text=8, 7, 6, 5",
        rule_id="grade1_add_sub_20_round2_subtraction_blanks",
    ),
    4: ElementaryVisualTemplate(
        problem_text="수 카드 1, 4, 6 중 2장을 뽑아 가장 작은 몇십몇을 만들었습니다. 만든 수와 남은 수의 차를 구하세요.",
        expression="answer=8",
        rule_id="grade1_add_sub_20_round2_card_difference",
    ),
    5: ElementaryVisualTemplate(
        problem_text="14 - 8, 8 + 6, 12 - 3 중 계산 결과가 9인 것을 찾으세요.",
        expression="answer_text=12 - 3에 ○표",
        rule_id="grade1_add_sub_20_round2_find_result_9",
    ),
    6: ElementaryVisualTemplate(
        problem_text="13에서 어떤 수를 뺐더니 7이 되었습니다. 어떤 수를 구하세요.",
        expression="answer=6",
        rule_id="grade1_add_sub_20_round2_missing_subtrahend",
    ),
    7: ElementaryVisualTemplate(
        problem_text="진우는 초콜릿 7개를 가지고 있었고 예원이 초콜릿 5개를 주었습니다. 모두 12개입니다.",
        expression="answer_text=12개",
        rule_id="grade1_add_sub_20_round2_chocolates_total",
    ),
    8: ElementaryVisualTemplate(
        problem_text="서준이는 색종이 8장과 6장, 윤서는 9장과 4장을 가지고 있습니다. 색종이 수의 합이 더 큰 학생은 서준입니다.",
        expression="answer_text=서준",
        rule_id="grade1_add_sub_20_round2_more_colored_paper",
    ),
    9: ElementaryVisualTemplate(
        problem_text="학생 15명 중 7명이 교실로 들어갔습니다. 남은 학생은 8명입니다.",
        expression="answer_text=8명",
        rule_id="grade1_add_sub_20_round2_students_left",
    ),
    10: ElementaryVisualTemplate(
        problem_text="방문객 14명에게 기념품을 나누어 주려고 합니다. 기념품이 6개 있으면 더 필요한 기념품은 8개입니다.",
        expression="answer_text=8개",
        rule_id="grade1_add_sub_20_round2_gifts_needed",
    ),
}


_ADD_SUB_20_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="10을 이용하여 모으기와 가르기를 한 것입니다. 빈칸에 알맞은 수를 넣으세요.",
        expression="answer_text=빈칸: 15, 15, 5",
        rule_id="grade1_add_sub_20_round3_make_ten_compose",
    ),
    2: ElementaryVisualTemplate(
        problem_text="14 - 6의 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 8, 4",
        rule_id="grade1_add_sub_20_round3_14_minus_6",
    ),
    3: ElementaryVisualTemplate(
        problem_text="8 + 5의 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=빈칸: 13, 3",
        rule_id="grade1_add_sub_20_round3_8_plus_5",
    ),
    4: ElementaryVisualTemplate(
        problem_text="합이 14인 덧셈식을 모두 찾아 색칠하세요.",
        expression="answer_text=7 + 7, 6 + 8",
        rule_id="grade1_add_sub_20_round3_sum_14_choices",
    ),
    5: ElementaryVisualTemplate(
        problem_text="14 - 6의 값을 구하세요.",
        expression="answer=8",
        rule_id="grade1_add_sub_20_round3_14_minus_6_value",
    ),
    6: ElementaryVisualTemplate(
        problem_text="8 + 7의 값을 구하세요.",
        expression="answer=15",
        rule_id="grade1_add_sub_20_round3_8_plus_7",
    ),
    7: ElementaryVisualTemplate(
        problem_text="7 + □ = 14에서 □ 안에 알맞은 수를 쓰세요.",
        expression="answer=7",
        rule_id="grade1_add_sub_20_round3_addition_blank",
    ),
    8: ElementaryVisualTemplate(
        problem_text="7, 6, 8, 9 중 가장 작은 수와 가장 큰 수의 합을 구하세요.",
        expression="answer=15",
        rule_id="grade1_add_sub_20_round3_min_max_sum",
    ),
    9: ElementaryVisualTemplate(
        problem_text="6에서 5를 더하고 4를 빼세요.",
        expression="answer_text=빈칸: 11, 7",
        rule_id="grade1_add_sub_20_round3_plus_then_minus",
    ),
    10: ElementaryVisualTemplate(
        problem_text="12 - 3과 4 + 7의 계산 결과를 비교하세요.",
        expression="answer_text=<",
        rule_id="grade1_add_sub_20_round3_compare_results",
    ),
}


_ADD_SUB_20_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="□ + 7 = 15, 14, 13, 12에 알맞은 수를 쓰세요.",
        expression="answer_text=8, 7, 6, 5",
        rule_id="grade1_add_sub_20_round3_addition_blanks",
    ),
    2: ElementaryVisualTemplate(
        problem_text="11 - 2, 11 - 3, 11 - 4, 11 - 5의 빈칸을 채우고 알맞은 말에 ○표 하세요.",
        expression="answer_text=9, 8, 7, 6 / 작아집니다에 ○표",
        rule_id="grade1_add_sub_20_round3_decreasing_differences",
    ),
    3: ElementaryVisualTemplate(
        problem_text="15 - □ = 9, 8, 7, 6에 알맞은 수를 쓰세요.",
        expression="answer_text=6, 7, 8, 9",
        rule_id="grade1_add_sub_20_round3_subtraction_blanks",
    ),
    4: ElementaryVisualTemplate(
        problem_text="수 카드 9, 5, 1 중 2장을 뽑아 가장 작은 몇십몇을 만들었습니다. 만든 수와 남은 수의 차를 구하세요.",
        expression="answer=6",
        rule_id="grade1_add_sub_20_round3_card_difference",
    ),
    5: ElementaryVisualTemplate(
        problem_text="11 - 7, 15 - 8, 13 - 4 중 계산 결과가 가장 큰 것을 찾으세요.",
        expression="answer_text=13 - 4에 ○표",
        rule_id="grade1_add_sub_20_round3_find_largest_result",
    ),
    6: ElementaryVisualTemplate(
        problem_text="18에서 어떤 수를 뺐더니 9가 되었습니다. 어떤 수를 구하세요.",
        expression="answer=9",
        rule_id="grade1_add_sub_20_round3_missing_subtrahend",
    ),
    7: ElementaryVisualTemplate(
        problem_text="접시에 현미 과자 6개와 초콜릿 과자 9개가 있습니다. 모두 15개입니다.",
        expression="answer_text=15개",
        rule_id="grade1_add_sub_20_round3_cookies_total",
    ),
    8: ElementaryVisualTemplate(
        problem_text="준서는 우표 7장과 9장, 세하는 우표 8장과 7장을 모았습니다. 모은 우표 수의 합이 더 큰 학생은 준서입니다.",
        expression="answer_text=준서",
        rule_id="grade1_add_sub_20_round3_more_stamps",
    ),
    9: ElementaryVisualTemplate(
        problem_text="굴 17개 중 9개를 먹었습니다. 남은 굴은 8개입니다.",
        expression="answer_text=8개",
        rule_id="grade1_add_sub_20_round3_oysters_left",
    ),
    10: ElementaryVisualTemplate(
        problem_text="관람 열차에 12명이 타야 출발합니다. 지금 5명이 타고 있으면 7명이 더 타야 합니다.",
        expression="answer_text=7명",
        rule_id="grade1_add_sub_20_round3_people_needed",
    ),
}


_GRADE2_THREE_DIGITS_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="다음을 숫자로 쓰세요. (1) 이백팔십칠, (2) 오백칠, (3) 구백이십, (4) 사백십일",
        expression="answer_text=(1) 287 / (2) 507 / (3) 920 / (4) 411",
        rule_id="grade2_three_digits_round1_korean_number_to_digits",
    ),
    2: ElementaryVisualTemplate(
        problem_text="519, □, 539, 549, □, 569를 10씩 뛰어 세어 보세요.",
        expression="answer_text=빈칸: 529, 559",
        rule_id="grade2_three_digits_round1_count_by_tens",
    ),
    3: ElementaryVisualTemplate(
        problem_text="100이 40개인 수를 쓰세요.",
        expression="answer=400",
        rule_id="grade2_three_digits_round1_forty_hundreds",
    ),
    4: ElementaryVisualTemplate(
        problem_text="백의 자리 숫자가 3인 수는 어느 것입니까? 234, 133, 331, 183, 930",
        expression="answer_text=③",
        rule_id="grade2_three_digits_round1_hundreds_digit_three",
    ),
    5: ElementaryVisualTemplate(
        problem_text="백 모형 4개, 십 모형 6개, 일 모형 8개가 나타내는 수를 쓰고 읽어 보세요.",
        expression="answer_text=468, 사백육십팔",
        rule_id="grade2_three_digits_round1_base_ten_blocks_write_read",
    ),
    6: ElementaryVisualTemplate(
        problem_text="298에서 밑줄 친 숫자 9는 얼마를 나타내는지 써 보세요.",
        expression="answer=90",
        rule_id="grade2_three_digits_round1_underlined_tens_digit",
    ),
    7: ElementaryVisualTemplate(
        problem_text="숫자 카드 7, 2, 0, 9, 3을 가지고 세 자리 수를 만들 때 가장 큰 수와 가장 작은 수를 구하세요.",
        expression="answer_text=(1) 973 / (2) 203",
        rule_id="grade2_three_digits_round1_largest_smallest_cards",
    ),
    8: ElementaryVisualTemplate(
        problem_text="100이 7개, 10이 13개, 1이 7인 수를 쓰고 읽어 보세요.",
        expression="answer_text=837, 팔백삼십칠",
        rule_id="grade2_three_digits_round1_hundreds_tens_ones_write_read",
    ),
    9: ElementaryVisualTemplate(
        problem_text="이백팔십오를 숫자로 쓰고 백의 자리, 십의 자리, 일의 자리에 알맞은 수를 써넣으세요.",
        expression="answer_text=285, 2, 8, 5",
        rule_id="grade2_three_digits_round1_place_value_of_285",
    ),
}


_GRADE2_THREE_DIGITS_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="478, 488, □, □, 518을 뛰어서 세어 보고 □ 안에 알맞은 수를 써 넣으세요.",
        expression="answer_text=빈칸: 498, 508",
        rule_id="grade2_three_digits_round1_number_line_by_tens",
    ),
    2: ElementaryVisualTemplate(
        problem_text="783에서 100씩 거꾸로 4번 뛰어서 센 수는 얼마입니까?",
        expression="answer=383",
        rule_id="grade2_three_digits_round1_count_back_by_hundreds",
    ),
    3: ElementaryVisualTemplate(
        problem_text="307은 370보다 작고, 578은 378보다 큽니다. >, <를 사용하여 나타내세요.",
        expression="answer_text=(1) 307 < 370 / (2) 578 > 378",
        rule_id="grade2_three_digits_round1_compare_three_digit_numbers",
    ),
    4: ElementaryVisualTemplate(
        problem_text="903 > 90□, 775 < 7□3에서 □ 안에 들어갈 수 있는 숫자를 모두 고르세요.",
        expression="answer_text=(1) 0, 1, 2 / (2) 8, 9",
        rule_id="grade2_three_digits_round1_possible_comparison_digits",
    ),
    5: ElementaryVisualTemplate(
        problem_text="숫자 카드 7, 3, 1을 한 번씩만 사용하여 만들 수 있는 가장 큰 수와 가장 작은 수를 쓰세요.",
        expression="answer_text=(1) 731 / (2) 137",
        rule_id="grade2_three_digits_round1_largest_smallest_731_137",
    ),
    6: ElementaryVisualTemplate(
        problem_text="797보다 크고 803보다 작은 수를 모두 쓰세요.",
        expression="answer_text=798, 799, 800, 801, 802",
        rule_id="grade2_three_digits_round1_numbers_between_797_803",
    ),
    7: ElementaryVisualTemplate(
        problem_text="0에서 9까지의 숫자 카드 10장 중 3장을 뽑아 세 자리 수를 만들 때, 백의 자리 숫자가 3인 수 중에서 가장 큰 수를 쓰세요.",
        expression="answer=398",
        rule_id="grade2_three_digits_round1_largest_with_hundreds_digit_three",
    ),
    8: ElementaryVisualTemplate(
        problem_text="세 자리 수이고, 백의 자리 숫자는 1이며, 각 자리 숫자의 합은 19인 수를 구하세요.",
        expression="answer=199",
        rule_id="grade2_three_digits_round1_digit_sum_condition",
    ),
    9: ElementaryVisualTemplate(
        problem_text="바구니에 귤을 93개 담았습니다. 바구니에 귤을 100개 담으려면 몇 개를 더 담아야 할까요?",
        expression="answer_text=7개",
        rule_id="grade2_three_digits_round1_oranges_to_100",
    ),
    10: ElementaryVisualTemplate(
        problem_text="꽃을 100송이씩 묶어 한 다발을 만들었습니다. 3다발에는 꽃이 모두 몇 송이인가요?",
        expression="answer_text=300송이",
        rule_id="grade2_three_digits_round1_three_hundreds_flowers",
    ),
    11: ElementaryVisualTemplate(
        problem_text="성희는 100원짜리 동전 5개와 10원짜리 동전 14개를 가지고 있고, 희주는 620원을 가지고 있습니다. 누가 돈을 더 많이 가지고 있습니까?",
        expression="answer_text=성희",
        rule_id="grade2_three_digits_round1_compare_money",
    ),
}


_GRADE2_THREE_DIGITS_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="460이 나타내는 수를 읽어 보세요.",
        expression="answer_text=사백육십",
        rule_id="grade2_three_digits_round2_read_460",
    ),
    2: ElementaryVisualTemplate(
        problem_text="918, 928, □, □, □를 10씩 뛰어 세어 보세요.",
        expression="answer_text=938, 948, 958, 968",
        rule_id="grade2_three_digits_round2_count_by_tens_from_918",
    ),
    3: ElementaryVisualTemplate(
        problem_text="10이 □개이면 600입니다. □ 안에 알맞은 수를 써 넣으세요.",
        expression="answer=60",
        rule_id="grade2_three_digits_round2_tens_in_600",
    ),
    4: ElementaryVisualTemplate(
        problem_text="숫자 5가 50을 나타내는 수를 모두 찾아 ○표 하세요.",
        expression="answer_text=450, 750에 ○표",
        rule_id="grade2_three_digits_round2_tens_digit_five",
    ),
    5: ElementaryVisualTemplate(
        problem_text="수 모형이 나타내는 수를 써 보세요.",
        expression="answer=346",
        rule_id="grade2_three_digits_round2_base_ten_blocks_346",
    ),
    6: ElementaryVisualTemplate(
        problem_text="100은 □보다 20만큼 더 큰 수입니다. □ 안에 알맞은 수를 써 넣으세요.",
        expression="answer=80",
        rule_id="grade2_three_digits_round2_twenty_less_than_100",
    ),
    7: ElementaryVisualTemplate(
        problem_text="숫자 카드 6, 2, 5, 0을 가지고 세 자리 수를 만들 때 가장 큰 수를 구하세요.",
        expression="answer=652",
        rule_id="grade2_three_digits_round2_largest_card_number",
    ),
    8: ElementaryVisualTemplate(
        problem_text="835와 673에서 십의 자리 숫자가 나타내는 값의 차를 구하세요.",
        expression="answer=40",
        rule_id="grade2_three_digits_round2_difference_tens_value",
    ),
    9: ElementaryVisualTemplate(
        problem_text="555에서 숫자 5가 나타내는 값이 가장 작은 것에 □표 하세요.",
        expression="answer_text=일의 자리 5",
        rule_id="grade2_three_digits_round2_smallest_value_digit_five",
    ),
    10: ElementaryVisualTemplate(
        problem_text="580, 630, □, □, □를 50씩 뛰어서 세어 보세요.",
        expression="answer_text=680, 730, 780, 830",
        rule_id="grade2_three_digits_round2_count_by_fifties",
    ),
}


_GRADE2_THREE_DIGITS_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="670에서 출발하여 10씩 거꾸로 뛰어서 세어 보세요.",
        expression="answer_text=660, 650, 640",
        rule_id="grade2_three_digits_round2_count_back_by_tens",
    ),
    2: ElementaryVisualTemplate(
        problem_text="100이 5개인 수보다 10 작은 수는 얼마입니까?",
        expression="answer=490",
        rule_id="grade2_three_digits_round2_ten_less_than_500",
    ),
    3: ElementaryVisualTemplate(
        problem_text="100이 5개, 1이 9개인 수와 오백이십 중 더 큰 수에 ○표 하세요.",
        expression="answer_text=오백이십",
        rule_id="grade2_three_digits_round2_larger_509_520",
    ),
    4: ElementaryVisualTemplate(
        problem_text="759, 559, 595의 크기를 비교하여 큰 수부터 차례로 쓰세요.",
        expression="answer_text=759, 595, 559",
        rule_id="grade2_three_digits_round2_order_descending",
    ),
    5: ElementaryVisualTemplate(
        problem_text="104번과 110번 사이에 있는 사람은 모두 몇 명입니까?",
        expression="answer_text=5명",
        rule_id="grade2_three_digits_round2_people_between_numbers",
    ),
    6: ElementaryVisualTemplate(
        problem_text="십의 자리 숫자가 2인 세 자리 수 중에서 가장 큰 수를 쓰세요.",
        expression="answer=928",
        rule_id="grade2_three_digits_round2_largest_tens_digit_two",
    ),
    7: ElementaryVisualTemplate(
        problem_text="어떤 수보다 10만큼 더 작은 수는 458입니다. 어떤 수보다 100만큼 더 큰 수는 얼마일까요?",
        expression="answer=568",
        rule_id="grade2_three_digits_round2_unknown_plus_hundred",
    ),
    8: ElementaryVisualTemplate(
        problem_text="상자에 연필을 97자루 넣었습니다. 100자루가 되려면 몇 자루를 더 넣어야 할까요?",
        expression="answer_text=3자루",
        rule_id="grade2_three_digits_round2_pencils_to_100",
    ),
    9: ElementaryVisualTemplate(
        problem_text="우표를 100장씩 5묶음, 10장씩 6묶음, 낱개로 5장 가지고 있습니다. 우표는 모두 몇 장입니까?",
        expression="answer_text=565장",
        rule_id="grade2_three_digits_round2_stamp_total",
    ),
    10: ElementaryVisualTemplate(
        problem_text="100원짜리 4개와 10원짜리 29개를 가지고 있습니다. 모두 얼마입니까?",
        expression="answer_text=690원",
        rule_id="grade2_three_digits_round2_money_total",
    ),
}


_GRADE2_THREE_DIGITS_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="100이 5개, 1이 8개인 수를 써 보세요.",
        expression="answer=508",
        rule_id="grade2_three_digits_round3_hundreds_ones_508",
    ),
    2: ElementaryVisualTemplate(
        problem_text="716, □, 736, 746, □, □의 뛰어서 세는 규칙을 찾아 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=726, 756, 766",
        rule_id="grade2_three_digits_round3_count_by_tens_with_gaps",
    ),
    3: ElementaryVisualTemplate(
        problem_text="100이 □개이면 800입니다. □ 안에 알맞은 수를 써 넣으세요.",
        expression="answer=8",
        rule_id="grade2_three_digits_round3_hundreds_in_800",
    ),
    4: ElementaryVisualTemplate(
        problem_text="백의 자리 숫자가 7, 십의 자리 숫자가 6, 일의 자리 숫자가 5이면 □ 안에 알맞은 수를 써넣으세요.",
        expression="answer=765",
        rule_id="grade2_three_digits_round3_place_value_765",
    ),
    5: ElementaryVisualTemplate(
        problem_text="수 모형이 나타내는 수를 써 보세요. 10 모형 10개입니다.",
        expression="answer=100",
        rule_id="grade2_three_digits_round3_base_ten_blocks_100",
    ),
    6: ElementaryVisualTemplate(
        problem_text="100은 □보다 1만큼 더 큰 수입니다. □ 안에 알맞은 수를 써 넣으세요.",
        expression="answer=99",
        rule_id="grade2_three_digits_round3_one_less_than_100",
    ),
    7: ElementaryVisualTemplate(
        problem_text="숫자 카드 8, 1, 5, 7을 가지고 세 자리 수를 만들 때 가장 작은 수를 구하세요.",
        expression="answer=157",
        rule_id="grade2_three_digits_round3_smallest_card_number",
    ),
    8: ElementaryVisualTemplate(
        problem_text="613과 947에서 십의 자리 숫자가 나타내는 값의 차를 구하세요.",
        expression="answer=30",
        rule_id="grade2_three_digits_round3_difference_tens_value",
    ),
    9: ElementaryVisualTemplate(
        problem_text="222에서 숫자 2가 20을 나타내는 값에 □표 하세요.",
        expression="answer_text=십의 자리 2",
        rule_id="grade2_three_digits_round3_digit_two_tens_value",
    ),
    10: ElementaryVisualTemplate(
        problem_text="360, 390, □, □, □, □를 30씩 뛰어서 세어 보세요.",
        expression="answer_text=410, 440, 470, 500",
        rule_id="grade2_three_digits_round3_count_by_thirties",
    ),
}


_GRADE2_THREE_DIGITS_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="500에서 출발하여 1씩 거꾸로 뛰어서 세어 보세요.",
        expression="answer_text=499, 498, 497",
        rule_id="grade2_three_digits_round3_count_back_by_ones",
    ),
    2: ElementaryVisualTemplate(
        problem_text="100이 7개인 수보다 10 큰 수는 얼마입니까?",
        expression="answer=710",
        rule_id="grade2_three_digits_round3_ten_more_than_700",
    ),
    3: ElementaryVisualTemplate(
        problem_text="982와 928의 계산 결과를 비교하여 >, =, <를 알맞게 써넣으세요.",
        expression="answer_text=>",
        rule_id="grade2_three_digits_round3_compare_982_928",
    ),
    4: ElementaryVisualTemplate(
        problem_text="숫자 카드 8, 2, 1을 한 번씩만 사용하여 만들 수 있는 가장 큰 수와 가장 작은 수를 쓰세요.",
        expression="answer_text=821, 128",
        rule_id="grade2_three_digits_round3_largest_smallest_821_128",
    ),
    5: ElementaryVisualTemplate(
        problem_text="211번과 218번 사이에 있는 사람은 모두 몇 명입니까?",
        expression="answer_text=6명",
        rule_id="grade2_three_digits_round3_people_between_numbers",
    ),
    6: ElementaryVisualTemplate(
        problem_text="백의 자리 숫자가 6인 세 자리 수 중에서 가장 작은 수를 쓰세요.",
        expression="answer=601",
        rule_id="grade2_three_digits_round3_smallest_hundreds_digit_six",
    ),
    7: ElementaryVisualTemplate(
        problem_text="백의 자리 숫자는 5이고, 십의 자리 수는 6보다 크고 8보다 작으며, 일의 자리 숫자는 8인 세 자리 수를 쓰세요.",
        expression="answer=578",
        rule_id="grade2_three_digits_round3_condition_number_578",
    ),
    8: ElementaryVisualTemplate(
        problem_text="상자에 지우개를 93개 넣었습니다. 100개가 되려면 몇 개를 더 넣어야 할까요?",
        expression="answer_text=7개",
        rule_id="grade2_three_digits_round3_erasers_to_100",
    ),
    9: ElementaryVisualTemplate(
        problem_text="사과가 100개씩 들어 있는 상자가 8상자, 낱개로 7개가 있습니다. 사과는 모두 몇 개입니까?",
        expression="answer_text=807개",
        rule_id="grade2_three_digits_round3_apples_total",
    ),
    10: ElementaryVisualTemplate(
        problem_text="시윤이는 100원짜리 동전 6개와 10원짜리 동전 24개, 희선이는 100원짜리 동전 5개와 10원짜리 동전 35개를 가지고 있습니다. 누가 돈을 더 많이 가지고 있습니까?",
        expression="answer_text=희선",
        rule_id="grade2_three_digits_round3_compare_money",
    ),
}


_GRADE2_SHAPES_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="똑같은 모양으로 쌓으려면 쌓기나무가 몇 개 필요합니까?",
        expression="answer_text=4개",
        topic="geometry",
        rule_id="grade2_shapes_round2_same_shape_blocks_needed",
    ),
    2: ElementaryVisualTemplate(
        problem_text="그림에서 찾을 수 있는 도형의 이름을 써 보세요.",
        expression="answer_text=원",
        topic="geometry",
        rule_id="grade2_shapes_round2_circle_in_clock",
    ),
    3: ElementaryVisualTemplate(
        problem_text="다음 모양에서 쌓기나무의 합은 모두 몇 개입니까?",
        expression="answer_text=8개",
        topic="geometry",
        rule_id="grade2_shapes_round2_total_blocks",
    ),
    4: ElementaryVisualTemplate(
        problem_text="<보기>와 똑같은 모양으로 쌓으려고 합니다. 쌓기나무를 더 놓아야 하는 곳은 어느 곳입니까?",
        expression="answer_text=①",
        topic="geometry",
        rule_id="grade2_shapes_round2_add_block_location",
    ),
    5: ElementaryVisualTemplate(
        problem_text="왼쪽 모양을 오른쪽 모양과 똑같이 만들려고 합니다. 빼야 하는 쌓기나무는 어느 것입니까?",
        expression="answer_text=㉡",
        topic="geometry",
        rule_id="grade2_shapes_round2_remove_block_location",
    ),
}


_GRADE2_SHAPES_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="원을 모두 찾아 기호를 쓰세요.",
        expression="answer_text=다, 마",
        topic="geometry",
        rule_id="grade2_shapes_round1_circles",
    ),
    2: ElementaryVisualTemplate(
        problem_text="점 종이에 점을 이어 서로 다른 삼각형을 2개 그리세요.",
        expression="answer_text=서로 다른 삼각형 2개",
        topic="geometry",
        rule_id="grade2_shapes_round1_draw_two_triangles",
    ),
    3: ElementaryVisualTemplate(
        problem_text="□ 안에 알맞은 말을 써 넣으세요.",
        expression="answer_text=㉠ 꼭짓점, ㉡ 변",
        topic="geometry",
        rule_id="grade2_shapes_round1_vertex_edge_labels",
    ),
    4: ElementaryVisualTemplate(
        problem_text="삼각형과 사각형 중 어느 것이 몇 개 더 많습니까?",
        expression="answer_text=삼각형이 2개 더 많습니다",
        topic="geometry",
        rule_id="grade2_shapes_round1_triangle_quadrilateral_compare",
    ),
    5: ElementaryVisualTemplate(
        problem_text="사각형에 대한 설명으로 옳은 것을 모두 골라 기호를 쓰세요.",
        expression="answer_text=가, 다",
        topic="geometry",
        rule_id="grade2_shapes_round1_quadrilateral_descriptions",
    ),
    6: ElementaryVisualTemplate(
        problem_text="삼각형과 사각형의 공통점을 모두 찾아 기호를 쓰세요.",
        expression="answer_text=가, 라",
        topic="geometry",
        rule_id="grade2_shapes_round1_common_features",
    ),
    7: ElementaryVisualTemplate(
        problem_text="오각형을 찾아 기호를 쓰세요.",
        expression="answer_text=다",
        topic="geometry",
        rule_id="grade2_shapes_round1_pentagon",
    ),
    8: ElementaryVisualTemplate(
        problem_text="사각형, 오각형, 육각형의 변의 수와 꼭짓점의 수를 써넣으세요.",
        expression="answer_text=사각형: 변 4, 꼭짓점 4 / 오각형: 변 5, 꼭짓점 5 / 육각형: 변 6, 꼭짓점 6",
        topic="geometry",
        rule_id="grade2_shapes_round1_sides_vertices_table",
    ),
}


_GRADE2_SHAPES_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="도형을 보고 변이 6개인 도형의 기호를 모두 쓰세요.",
        expression="answer_text=사",
        topic="geometry",
        rule_id="grade2_shapes_round1_page2_six_sides",
    ),
    2: ElementaryVisualTemplate(
        problem_text="도형을 점선을 따라 자르면 어떤 도형이 몇 개 생기는지 차례로 써 보세요.",
        expression="answer_text=삼각형 3개",
        topic="geometry",
        rule_id="grade2_shapes_round1_page2_cut_triangle_count",
    ),
    3: ElementaryVisualTemplate(
        problem_text="그림에는 삼각형이 몇 개 사용되었습니까?",
        expression="answer=4",
        topic="geometry",
        rule_id="grade2_shapes_round1_page2_boat_triangle_count",
    ),
    4: ElementaryVisualTemplate(
        problem_text="삼각형과 사각형 조각은 몇 개인지 차례로 구하세요.",
        expression="answer_text=삼각형 5개, 사각형 2개",
        topic="geometry",
        rule_id="grade2_shapes_round1_page2_tangram_shape_counts",
    ),
    5: ElementaryVisualTemplate(
        problem_text="똑같은 모양을 찾아 기호를 쓰세요.",
        expression="answer_text=(1) 다, (2) 가, (3) 나",
        topic="geometry",
        rule_id="grade2_shapes_round1_page2_matching_blocks",
    ),
    6: ElementaryVisualTemplate(
        problem_text="주어진 도형 조각을 모두 이용하여 사각형을 만들 수 있는 것을 찾아 기호를 쓰세요.",
        expression="answer_text=나",
        topic="geometry",
        rule_id="grade2_shapes_round1_page2_make_quadrilateral",
    ),
}


_GRADE2_SHAPES_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="똑같은 모양으로 쌓으려면 쌓기나무가 몇 개 필요합니까?",
        expression="answer_text=(1) 4개, (2) 5개",
        topic="geometry",
        rule_id="grade2_shapes_round1_page3_same_shape_blocks",
    ),
    2: ElementaryVisualTemplate(
        problem_text="칠교판의 조각 중 6조각을 이용하여 오각형 모양을 만들었습니다. 이용하지 않은 조각의 번호를 쓰세요.",
        expression="answer=6",
        topic="geometry",
        rule_id="grade2_shapes_round1_page3_unused_tangram_piece",
    ),
    3: ElementaryVisualTemplate(
        problem_text="색종이를 점선을 따라 자르면 어떤 도형이 만들어지는지 모두 고르세요.",
        expression="answer_text=삼각형, 사각형",
        topic="geometry",
        rule_id="grade2_shapes_round1_page3_cut_paper_shapes",
    ),
    4: ElementaryVisualTemplate(
        problem_text="왼쪽 모양을 오른쪽 모양과 똑같이 쌓으려면 더 필요한 쌓기나무는 적어도 몇 개입니까?",
        expression="answer_text=3개",
        topic="geometry",
        rule_id="grade2_shapes_round1_page3_more_blocks_needed",
    ),
    5: ElementaryVisualTemplate(
        problem_text="<보기>와 똑같은 모양으로 쌓으려고 합니다. 쌓기나무를 더 놓아야 하는 곳은 어느 곳입니까?",
        expression="answer_text=②",
        topic="geometry",
        rule_id="grade2_shapes_round1_page3_add_block_location",
    ),
    6: ElementaryVisualTemplate(
        problem_text="쌓기나무 6개로 만든 모양에 대한 설명입니다. 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=1층 3개, 2층 2개, 3층 1개",
        topic="geometry",
        rule_id="grade2_shapes_round1_page3_stair_layers",
    ),
}


_GRADE2_SHAPES_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="원을 찾아 기호를 써 보세요.",
        expression="answer_text=마",
        topic="geometry",
        rule_id="grade2_shapes_round2_circle",
    ),
    2: ElementaryVisualTemplate(
        problem_text="삼각형을 모두 찾아 기호를 써 보세요.",
        expression="answer_text=가, 라, 바",
        topic="geometry",
        rule_id="grade2_shapes_round2_triangles",
    ),
    3: ElementaryVisualTemplate(
        problem_text="삼각형의 변과 꼭짓점은 각각 몇 개인지 써 보세요.",
        expression="answer_text=변 3개, 꼭짓점 3개",
        topic="geometry",
        rule_id="grade2_shapes_round2_triangle_sides_vertices",
    ),
    4: ElementaryVisualTemplate(
        problem_text="색종이를 선을 따라 자르면 어떤 도형이 몇 개 생기는지 차례로 쓰세요.",
        expression="answer_text=삼각형 4개, 사각형 1개",
        topic="geometry",
        rule_id="grade2_shapes_round2_cut_paper_counts",
    ),
    5: ElementaryVisualTemplate(
        problem_text="삼각형에 대한 설명으로 옳은 것을 모두 골라 기호를 쓰세요.",
        expression="answer_text=나, 다",
        topic="geometry",
        rule_id="grade2_shapes_round2_triangle_descriptions",
    ),
    6: ElementaryVisualTemplate(
        problem_text="사각형에 대한 설명으로 옳지 않은 것을 고르세요.",
        expression="answer_text=③",
        topic="geometry",
        rule_id="grade2_shapes_round2_wrong_quadrilateral_description",
    ),
    7: ElementaryVisualTemplate(
        problem_text="오각형의 변의 수와 꼭짓점의 수를 구하세요.",
        expression="answer_text=변 5개, 꼭짓점 5개",
        topic="geometry",
        rule_id="grade2_shapes_round2_pentagon_sides_vertices",
    ),
}


_GRADE2_SHAPES_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="5개의 곧은 선으로 둘러싸인 도형의 변의 수와 꼭짓점의 수의 합을 구하세요.",
        expression="answer=10",
        topic="geometry",
        rule_id="grade2_shapes_round2_page2_pentagon_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="육각형은 삼각형보다 변이 몇 개 더 많고, 사각형은 오각형보다 꼭짓점이 몇 개 더 적습니까?",
        expression="answer_text=3개, 1개",
        topic="geometry",
        rule_id="grade2_shapes_round2_page2_shape_difference",
    ),
    3: ElementaryVisualTemplate(
        problem_text="색종이를 선을 따라 잘랐을 때 생기는 도형의 이름을 모두 쓰세요.",
        expression="answer_text=삼각형, 육각형",
        topic="geometry",
        rule_id="grade2_shapes_round2_page2_cut_shape_names",
    ),
    4: ElementaryVisualTemplate(
        problem_text="칠교판 조각을 이용하여 만든 모양에서 삼각형과 사각형 조각은 각각 몇 개인지 구하세요.",
        expression="answer_text=삼각형 4개, 사각형 2개",
        topic="geometry",
        rule_id="grade2_shapes_round2_page2_tangram_counts",
    ),
    5: ElementaryVisualTemplate(
        problem_text="원은 모두 몇 개인지 구하세요.",
        expression="answer_text=5개",
        topic="geometry",
        rule_id="grade2_shapes_round2_page2_circle_count",
    ),
    6: ElementaryVisualTemplate(
        problem_text="칠교판에서 삼각형과 사각형 조각의 차를 구하세요.",
        expression="answer_text=3개",
        topic="geometry",
        rule_id="grade2_shapes_round2_page2_triangle_quadrilateral_difference",
    ),
    7: ElementaryVisualTemplate(
        problem_text="다음과 똑같은 모양으로 쌓은 것을 찾으세요.",
        expression="answer_text=오른쪽",
        topic="geometry",
        rule_id="grade2_shapes_round2_page2_matching_stack",
    ),
    8: ElementaryVisualTemplate(
        problem_text="주어진 도형을 만들 때 사용한 조각을 찾아 ○표 하세요.",
        expression="answer_text=사각형, 삼각형, 평행사변형",
        topic="geometry",
        rule_id="grade2_shapes_round2_page2_used_pieces",
    ),
}


_GRADE2_SHAPES_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="원을 모두 찾아 써 보세요.",
        expression="answer_text=다, 라",
        topic="geometry",
        rule_id="grade2_shapes_round3_circles",
    ),
    2: ElementaryVisualTemplate(
        problem_text="삼각형을 모두 찾아 기호를 써 보세요.",
        expression="answer_text=나, 라",
        topic="geometry",
        rule_id="grade2_shapes_round3_triangles",
    ),
    3: ElementaryVisualTemplate(
        problem_text="삼각형과 사각형 중 어느 것이 몇 개 더 많습니까?",
        expression="answer_text=사각형이 1개 더 많습니다",
        topic="geometry",
        rule_id="grade2_shapes_round3_triangle_quadrilateral_compare",
    ),
    4: ElementaryVisualTemplate(
        problem_text="사각형의 변과 삼각형의 꼭짓점의 차는 몇인지 쓰세요.",
        expression="answer=1",
        topic="geometry",
        rule_id="grade2_shapes_round3_sides_vertices_difference",
    ),
    5: ElementaryVisualTemplate(
        problem_text="삼각형의 곧은 선과 사각형의 굽은 선은 각각 몇 개인지 쓰세요.",
        expression="answer_text=삼각형의 곧은 선 3개, 사각형의 굽은 선 0개",
        topic="geometry",
        rule_id="grade2_shapes_round3_straight_curved_edges",
    ),
    6: ElementaryVisualTemplate(
        problem_text="삼각형에 대한 설명으로 옳지 않은 것을 고르세요.",
        expression="answer_text=①, ②",
        topic="geometry",
        rule_id="grade2_shapes_round3_wrong_triangle_descriptions",
    ),
    7: ElementaryVisualTemplate(
        problem_text="오각형에 대한 설명으로 틀린 것의 기호를 쓰세요.",
        expression="answer_text=다",
        topic="geometry",
        rule_id="grade2_shapes_round3_wrong_pentagon_description",
    ),
}


_GRADE2_SHAPES_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="3개의 곧은 선으로 둘러싸인 도형의 변의 수와 4개의 곧은 선으로 둘러싸인 도형의 꼭짓점의 수의 합을 구하세요.",
        expression="answer=7",
        topic="geometry",
        rule_id="grade2_shapes_round3_page2_triangle_quadrilateral_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="육각형은 사각형보다 변이 몇 개 더 많고, 오각형은 삼각형보다 꼭짓점이 몇 개 더 많습니까?",
        expression="answer_text=2개, 2개",
        topic="geometry",
        rule_id="grade2_shapes_round3_page2_shape_difference",
    ),
    3: ElementaryVisualTemplate(
        problem_text="색종이를 선을 따라 잘랐을 때 생기는 도형의 이름을 모두 쓰세요.",
        expression="answer_text=삼각형, 사각형",
        topic="geometry",
        rule_id="grade2_shapes_round3_page2_cut_shape_names",
    ),
    4: ElementaryVisualTemplate(
        problem_text="그림에서 찾을 수 있는 크고 작은 삼각형의 개수를 모두 구하세요.",
        expression="answer_text=큰 삼각형 2개, 작은 삼각형 4개",
        topic="geometry",
        rule_id="grade2_shapes_round3_page2_triangle_counts",
    ),
    5: ElementaryVisualTemplate(
        problem_text="칠교판 조각을 이용하여 만든 모양에서 삼각형과 사각형 조각은 각각 몇 개인지 구하세요.",
        expression="answer_text=삼각형 4개, 사각형 3개",
        topic="geometry",
        rule_id="grade2_shapes_round3_page2_tangram_counts",
    ),
    6: ElementaryVisualTemplate(
        problem_text="칠교판 조각을 이용하여 만든 모양에서 삼각형과 사각형 조각의 합을 구하세요.",
        expression="answer_text=7개",
        topic="geometry",
        rule_id="grade2_shapes_round3_page2_tangram_total",
    ),
    7: ElementaryVisualTemplate(
        problem_text="다음과 똑같은 모양으로 쌓은 것을 찾으세요.",
        expression="answer_text=가운데",
        topic="geometry",
        rule_id="grade2_shapes_round3_page2_matching_stack",
    ),
}


_GRADE2_SHAPES_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="색종이를 선을 따라 자르면 어떤 도형이 만들어지는지 모두 쓰세요.",
        expression="answer_text=삼각형, 사각형, 오각형",
        topic="geometry",
        rule_id="grade2_shapes_round3_page3_cut_paper_shapes",
    ),
    2: ElementaryVisualTemplate(
        problem_text="똑같은 모양으로 쌓으려면 쌓기나무가 몇 개 필요합니까?",
        expression="answer_text=5개",
        topic="geometry",
        rule_id="grade2_shapes_round3_page3_same_shape_blocks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="빨간색 쌓기나무의 왼쪽에 있는 쌓기나무의 기호를 쓰세요.",
        expression="answer_text=나",
        topic="geometry",
        rule_id="grade2_shapes_round3_page3_left_of_red_block",
    ),
    4: ElementaryVisualTemplate(
        problem_text="왼쪽 모양을 오른쪽 모양과 똑같이 쌓으려면 더 필요한 쌓기나무는 적어도 몇 개입니까?",
        expression="answer_text=2개",
        topic="geometry",
        rule_id="grade2_shapes_round3_page3_more_blocks_needed",
    ),
    5: ElementaryVisualTemplate(
        problem_text="쌓기나무 4개로 만든 모양을 찾으세요.",
        expression="answer_text=오른쪽",
        topic="geometry",
        rule_id="grade2_shapes_round3_page3_four_block_shape",
    ),
    6: ElementaryVisualTemplate(
        problem_text="설명에 맞게 쌓기나무를 쌓으려고 합니다. 쌓기나무를 놓아야 하는 곳의 기호를 쓰세요.",
        expression="answer_text=ㄴ",
        topic="geometry",
        rule_id="grade2_shapes_round3_page3_add_block_for_layers",
    ),
}


_GRADE2_FOUR_DIGITS_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="900보다 100만큼 더 큰 수를 쓰세요.",
        expression="answer=1000",
        rule_id="grade2_four_digits_round1_900_plus_100",
    ),
    2: ElementaryVisualTemplate(
        problem_text="수 모형이 나타내는 수를 쓰세요.",
        expression="answer=2125",
        rule_id="grade2_four_digits_round1_base_ten_blocks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="3825는 1000, 100, 10, 1이 각각 몇 개인지 쓰세요.",
        expression="answer_text=3, 8, 2, 5",
        rule_id="grade2_four_digits_round1_place_value_counts",
    ),
    4: ElementaryVisualTemplate(
        problem_text="2947의 각 자리 숫자를 쓰세요.",
        expression="answer_text=2, 9, 4, 7",
        rule_id="grade2_four_digits_round1_digits_by_place",
    ),
    5: ElementaryVisualTemplate(
        problem_text="2450부터 100씩 뛰어 세어 빈칸을 채우세요.",
        expression="answer_text=2550, 2650, 2850",
        rule_id="grade2_four_digits_round1_count_by_100",
    ),
    6: ElementaryVisualTemplate(
        problem_text="8796과 8769의 크기를 비교하세요.",
        expression="answer_text=>",
        rule_id="grade2_four_digits_round1_compare_8796_8769",
    ),
    7: ElementaryVisualTemplate(
        problem_text="3이 10인 수, 30이 10인 수, 300이 10인 수를 쓰세요.",
        expression="answer_text=30, 300, 3000",
        rule_id="grade2_four_digits_round1_times_ten",
    ),
    8: ElementaryVisualTemplate(
        problem_text="두 수 중 더 큰 수를 아래 빈 곳에 쓰세요.",
        expression="answer_text=7432, 6501, 7432",
        rule_id="grade2_four_digits_round1_larger_number_bracket",
    ),
}


_GRADE2_FOUR_DIGITS_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="육천이백구십오에서 숫자 9가 나타내는 값은 얼마인지 구하세요.",
        expression="answer=90",
        rule_id="grade2_four_digits_round1_digit_value_9",
    ),
    2: ElementaryVisualTemplate(
        problem_text="백의 자리 숫자가 가장 작은 수를 찾아 ○표 하세요.",
        expression="answer_text=두 번째에 ○표",
        rule_id="grade2_four_digits_round1_smallest_hundreds_digit",
    ),
    3: ElementaryVisualTemplate(
        problem_text="밑줄 친 숫자가 나타내는 값의 크기를 비교하세요.",
        expression="answer_text=<",
        rule_id="grade2_four_digits_round1_compare_underlined_values",
    ),
    4: ElementaryVisualTemplate(
        problem_text="65□8 > 6582가 되도록 □ 안에 들어갈 수 있는 숫자는 모두 몇 개인지 구하세요.",
        expression="answer_text=2개",
        rule_id="grade2_four_digits_round1_digit_blank_count",
    ),
    5: ElementaryVisualTemplate(
        problem_text="8, 1, 5, 3을 한 번씩 사용하여 만들 수 있는 가장 큰 수와 가장 작은 수를 구하세요.",
        expression="answer_text=8531, 1358",
        rule_id="grade2_four_digits_round1_largest_smallest_digits",
    ),
    6: ElementaryVisualTemplate(
        problem_text="2638부터 1000번씩 5번 뛰어 세면 얼마가 되는지 구하세요.",
        expression="answer=7638",
        rule_id="grade2_four_digits_round1_2638_plus_5000",
    ),
    7: ElementaryVisualTemplate(
        problem_text="2364부터 뛰어 세는 규칙을 찾아 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=2374, 2394",
        rule_id="grade2_four_digits_round1_counting_pattern",
    ),
    8: ElementaryVisualTemplate(
        problem_text="이천구십일과 육천이백을 수로 썼을 때 0은 모두 몇 개인지 구하세요.",
        expression="answer_text=3개",
        rule_id="grade2_four_digits_round1_count_zeros",
    ),
    9: ElementaryVisualTemplate(
        problem_text="2046부터 50씩 3번 뛰어 세면 얼마인지 구하세요.",
        expression="answer=2196",
        rule_id="grade2_four_digits_round1_2046_plus_150",
    ),
    10: ElementaryVisualTemplate(
        problem_text="구슬 350개에서 1000개가 되려면 몇 개를 더 모아야 하는지 구하세요.",
        expression="answer_text=650개",
        rule_id="grade2_four_digits_round1_marbles_to_1000",
    ),
    11: ElementaryVisualTemplate(
        problem_text="1316명, 1995명, 2025명 중 사람이 가장 많이 사는 마을을 구하세요.",
        expression="answer_text=금빛마을",
        rule_id="grade2_four_digits_round1_largest_village_population",
    ),
    12: ElementaryVisualTemplate(
        problem_text="한 상자에 색연필이 100개씩 들어 있을 때 50상자의 색연필 수를 구하세요.",
        expression="answer_text=5000개",
        rule_id="grade2_four_digits_round1_colored_pencils_boxes",
    ),
}


_GRADE2_FOUR_DIGITS_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수 모형이 나타내는 수를 쓰세요.",
        expression="answer=4357",
        rule_id="grade2_four_digits_round2_base_ten_blocks",
    ),
    2: ElementaryVisualTemplate(
        problem_text="1000이 4개인 수를 쓰세요.",
        expression="answer=4000",
        rule_id="grade2_four_digits_round2_four_thousands",
    ),
    3: ElementaryVisualTemplate(
        problem_text="1000이 8개, 100이 4개, 10이 0개, 1이 6개이면 얼마인지 쓰세요.",
        expression="answer=8406",
        rule_id="grade2_four_digits_round2_place_value_compose",
    ),
    4: ElementaryVisualTemplate(
        problem_text="8012를 읽는 말을 쓰세요.",
        expression="answer_text=팔천십이",
        rule_id="grade2_four_digits_round2_read_8012",
    ),
    5: ElementaryVisualTemplate(
        problem_text="3109, 3209, 3309, 3409는 얼마씩 뛰어 센 것인지 구하세요.",
        expression="answer=100",
        rule_id="grade2_four_digits_round2_count_step_100",
    ),
    6: ElementaryVisualTemplate(
        problem_text="5370, 6247, 2916 중 가장 큰 수와 가장 작은 수를 표시하세요.",
        expression="answer_text=6247에 ○표, 2916에 △표",
        rule_id="grade2_four_digits_round2_largest_smallest_mark",
    ),
    7: ElementaryVisualTemplate(
        problem_text="나타내는 수가 다른 하나에 ○표 하세요.",
        expression="answer_text=세 번째에 ○표",
        rule_id="grade2_four_digits_round2_different_value",
    ),
    8: ElementaryVisualTemplate(
        problem_text="1000이 4개, 100이 27개, 10이 5개, 1이 8개가 나타내는 네 자리 수를 구하세요.",
        expression="answer=6758",
        rule_id="grade2_four_digits_round2_compose_6758",
    ),
    9: ElementaryVisualTemplate(
        problem_text="천의 자리 숫자가 3인 수를 고르세요.",
        expression="answer_text=⑤",
        rule_id="grade2_four_digits_round2_thousands_digit_3",
    ),
    10: ElementaryVisualTemplate(
        problem_text="3512에서 밑줄 친 숫자 5가 나타내는 값을 쓰세요.",
        expression="answer=500",
        rule_id="grade2_four_digits_round2_digit_5_value",
    ),
}


_GRADE2_FOUR_DIGITS_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="1289와 6428에서 밑줄 친 숫자가 나타내는 값의 크기를 비교하세요.",
        expression="answer_text=>",
        rule_id="grade2_four_digits_round2_compare_underlined_values",
    ),
    2: ElementaryVisualTemplate(
        problem_text="9235 > 9□78이 되도록 □ 안에 들어갈 수 있는 숫자는 모두 몇 개인지 구하세요.",
        expression="answer_text=2개",
        rule_id="grade2_four_digits_round2_digit_blank_count",
    ),
    3: ElementaryVisualTemplate(
        problem_text="2, 4, 3, 9를 한 번씩 사용하여 만들 수 있는 가장 큰 수와 가장 작은 수를 구하세요.",
        expression="answer_text=9432, 2349",
        rule_id="grade2_four_digits_round2_largest_smallest_digits",
    ),
    4: ElementaryVisualTemplate(
        problem_text="4392부터 100씩 7번 뛰어 세면 얼마가 되는지 구하세요.",
        expression="answer=5092",
        rule_id="grade2_four_digits_round2_4392_plus_700",
    ),
    5: ElementaryVisualTemplate(
        problem_text="5037부터 뛰어 세는 규칙을 찾아 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=5047, 5067",
        rule_id="grade2_four_digits_round2_counting_pattern",
    ),
    6: ElementaryVisualTemplate(
        problem_text="육천이백일과 삼천구 중 수로 썼을 때 00이 더 많은 쪽에 ○표 하세요.",
        expression="answer_text=두 번째에 ○표",
        rule_id="grade2_four_digits_round2_more_double_zero",
    ),
    7: ElementaryVisualTemplate(
        problem_text="2865부터 2000씩 3번 뛰어 세면 얼마인지 구하세요.",
        expression="answer=8865",
        rule_id="grade2_four_digits_round2_2865_plus_6000",
    ),
    8: ElementaryVisualTemplate(
        problem_text="1000원씩 4번 받은 용돈은 얼마인지 구하세요.",
        expression="answer_text=4000원",
        rule_id="grade2_four_digits_round2_allowance_1000_four_times",
    ),
    9: ElementaryVisualTemplate(
        problem_text="천원짜리 지폐 6장과 백원짜리 동전 9개의 금액을 구하세요.",
        expression="answer_text=6900원",
        rule_id="grade2_four_digits_round2_money_6900",
    ),
    10: ElementaryVisualTemplate(
        problem_text="2700원에서 매일 100원씩 4일 동안 저금하면 얼마인지 구하세요.",
        expression="answer_text=3100원",
        rule_id="grade2_four_digits_round2_savings_3100",
    ),
}


_GRADE2_FOUR_DIGITS_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="1000이 5개인 수를 쓰세요.",
        expression="answer=5000",
        rule_id="grade2_four_digits_round3_five_thousands",
    ),
    2: ElementaryVisualTemplate(
        problem_text="800보다 200만큼 더 큰 수를 쓰세요.",
        expression="answer=1000",
        rule_id="grade2_four_digits_round3_800_plus_200",
    ),
    3: ElementaryVisualTemplate(
        problem_text="1000이 5개, 100이 1개, 10이 8개, 1이 3개이면 얼마인지 쓰세요.",
        expression="answer=5183",
        rule_id="grade2_four_digits_round3_place_value_compose",
    ),
    4: ElementaryVisualTemplate(
        problem_text="구천칠백사를 숫자로 쓰세요.",
        expression="answer=9704",
        rule_id="grade2_four_digits_round3_write_9704",
    ),
    5: ElementaryVisualTemplate(
        problem_text="4056부터 1000씩 뛰어 세는 규칙을 찾아 빈칸을 채우세요.",
        expression="answer_text=6056, 7056, 9056",
        rule_id="grade2_four_digits_round3_count_by_1000",
    ),
    6: ElementaryVisualTemplate(
        problem_text="1000이 5개, 1이 9개인 수와 사천팔백이십구 중 더 큰 수에 ○표 하세요.",
        expression="answer_text=첫 번째에 ○표",
        rule_id="grade2_four_digits_round3_larger_written_number",
    ),
    7: ElementaryVisualTemplate(
        problem_text="수를 잘못 읽은 것을 찾아 ○표 하세요.",
        expression="answer_text=두 번째에 ○표",
        rule_id="grade2_four_digits_round3_wrong_reading",
    ),
    8: ElementaryVisualTemplate(
        problem_text="1000이 3개, 100이 7개, 10이 14개, 1이 9개가 나타내는 네 자리 수를 구하세요.",
        expression="answer=3846",
        rule_id="grade2_four_digits_round3_compose_3846",
    ),
    9: ElementaryVisualTemplate(
        problem_text="100이 75개인 수를 100이 70개와 나머지로 나누어 나타내세요.",
        expression="answer_text=7000, 5, 500, 7500",
        rule_id="grade2_four_digits_round3_hundreds_75",
    ),
}


_GRADE2_FOUR_DIGITS_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="숫자 6이 나타내는 값이 다른 하나를 찾아 ○표 하세요.",
        expression="answer_text=첫 번째에 ○표",
        rule_id="grade2_four_digits_round3_digit_6_different_value",
    ),
    2: ElementaryVisualTemplate(
        problem_text="3201과 9387에서 밑줄 친 숫자가 나타내는 값의 크기를 비교하세요.",
        expression="answer_text=>",
        rule_id="grade2_four_digits_round3_compare_underlined_values",
    ),
    3: ElementaryVisualTemplate(
        problem_text="2□05 > 2709가 되도록 □ 안에 들어갈 수 있는 숫자는 모두 몇 개인지 구하세요.",
        expression="answer_text=2개",
        rule_id="grade2_four_digits_round3_digit_blank_count",
    ),
    4: ElementaryVisualTemplate(
        problem_text="5, 7, 4, 8을 한 번씩 사용하여 만들 수 있는 가장 큰 수와 가장 작은 수를 구하세요.",
        expression="answer_text=8754, 4578",
        rule_id="grade2_four_digits_round3_largest_smallest_digits",
    ),
    5: ElementaryVisualTemplate(
        problem_text="4576부터 100씩 6번 뛰어 세면 얼마인지 구하세요.",
        expression="answer=5176",
        rule_id="grade2_four_digits_round3_4576_plus_600",
    ),
    6: ElementaryVisualTemplate(
        problem_text="8427부터 뛰어 세는 규칙을 찾아 빈칸에 알맞은 수를 쓰세요.",
        expression="answer_text=8428, 8430",
        rule_id="grade2_four_digits_round3_counting_pattern",
    ),
    7: ElementaryVisualTemplate(
        problem_text="칠천이와 칠천백 중 숫자가 더 큰 쪽에 ○표 하세요.",
        expression="answer_text=두 번째에 ○표",
        rule_id="grade2_four_digits_round3_larger_written_number",
    ),
    8: ElementaryVisualTemplate(
        problem_text="6210부터 20씩 4번 뛰어 세면 얼마인지 구하세요.",
        expression="answer=6290",
        rule_id="grade2_four_digits_round3_6210_plus_80",
    ),
    9: ElementaryVisualTemplate(
        problem_text="1000원씩 6번 저금한 돈은 모두 얼마인지 구하세요.",
        expression="answer_text=6000원",
        rule_id="grade2_four_digits_round3_savings_6000",
    ),
    10: ElementaryVisualTemplate(
        problem_text="한 상자에 연필이 100자루씩 있을 때 20상자의 연필 수를 구하세요.",
        expression="answer_text=2000자루",
        rule_id="grade2_four_digits_round3_pencils_2000",
    ),
    11: ElementaryVisualTemplate(
        problem_text="500원짜리 초콜릿을 2300원으로 몇 개까지 살 수 있는지 구하세요.",
        expression="answer_text=4개",
        rule_id="grade2_four_digits_round3_chocolates_500_won",
    ),
}


_GRADE2_ADD_SUB_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="48 + 5의 덧셈을 해 보세요.",
        expression="answer=53",
        rule_id="grade2_add_sub_round1_48_plus_5",
    ),
    2: ElementaryVisualTemplate(
        problem_text="덧셈 표의 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=㉠ 119, ㉡ 34, ㉢ 80, ㉣ 73",
        rule_id="grade2_add_sub_round1_addition_table",
    ),
    3: ElementaryVisualTemplate(
        problem_text="세로 덧셈에서 □ 안에 알맞은 수를 써넣으세요.",
        expression="answer_text=㉠ 6, ㉡ 8",
        rule_id="grade2_add_sub_round1_column_addition_blanks",
    ),
    4: ElementaryVisualTemplate(
        problem_text="47 + 22와 18 + 52의 계산 결과를 비교하세요.",
        expression="answer_text=<",
        rule_id="grade2_add_sub_round1_compare_additions",
    ),
    5: ElementaryVisualTemplate(
        problem_text="60과 17의 차를 구하세요.",
        expression="answer=43",
        rule_id="grade2_add_sub_round1_difference_60_17",
    ),
    6: ElementaryVisualTemplate(
        problem_text="6과 42의 합과 차를 구하세요.",
        expression="answer_text=합: 48 / 차: 36",
        rule_id="grade2_add_sub_round1_sum_difference_6_42",
    ),
    7: ElementaryVisualTemplate(
        problem_text="28, 76, 53에 7을 더한 수를 빈칸에 써넣으세요.",
        expression="answer_text=35, 83, 60",
        rule_id="grade2_add_sub_round1_add_seven_table",
    ),
    8: ElementaryVisualTemplate(
        problem_text="72 - 7과 75 - 9의 계산 결과를 비교하세요.",
        expression="answer_text=<",
        rule_id="grade2_add_sub_round1_compare_subtractions",
    ),
}


_GRADE2_ADD_SUB_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="1에서 9까지의 수 중 37 + □ < 41의 □ 안에 들어갈 수 있는 수를 모두 쓰세요.",
        expression="answer_text=1, 2, 3",
        rule_id="grade2_add_sub_round1_37_plus_blank_less_41",
    ),
    2: ElementaryVisualTemplate(
        problem_text="세로 뺄셈에서 □ 안에 알맞은 수를 써넣으세요.",
        expression="answer_text=㉠ 6, ㉡ 4",
        rule_id="grade2_add_sub_round1_column_subtraction_blanks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="60, 41, 72에서 각각 23을 빼세요.",
        expression="answer_text=37, 18, 49",
        rule_id="grade2_add_sub_round1_subtract_23_table",
    ),
    4: ElementaryVisualTemplate(
        problem_text="71, 65, 53, 48을 이용한 뺄셈 표의 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=㉠ 6, ㉡ 5, ㉢ 18, ㉣ 17",
        rule_id="grade2_add_sub_round1_subtraction_table",
    ),
    5: ElementaryVisualTemplate(
        problem_text="47 + 5 = 52를 덧셈식과 뺄셈식으로 나타내어 보세요.",
        expression="answer_text=㉠ 47, ㉡ 5, ㉢ 52, ㉣ 47",
        rule_id="grade2_add_sub_round1_fact_family",
    ),
    6: ElementaryVisualTemplate(
        problem_text="53, 68, 35, 92, 41에서 가장 큰 수와 가장 작은 수의 차를 구하세요.",
        expression="answer=57",
        rule_id="grade2_add_sub_round1_largest_smallest_difference",
    ),
    7: ElementaryVisualTemplate(
        problem_text="놀이터에 9명의 어린이가 있고 13명의 어린이가 더 왔습니다. 모두 몇 명입니까?",
        expression="answer_text=22명",
        rule_id="grade2_add_sub_round1_playground_total",
    ),
    8: ElementaryVisualTemplate(
        problem_text="줄넘기를 96번 넘으려고 합니다. 지금까지 49번 넘었다면 앞으로 몇 번을 더 넘으면 됩니까?",
        expression="answer_text=47번",
        rule_id="grade2_add_sub_round1_jump_rope_remaining",
    ),
    9: ElementaryVisualTemplate(
        problem_text="버스에 승객이 31명 있습니다. 14명이 내리고 7명이 탔습니다. 지금 승객은 몇 명입니까?",
        expression="answer_text=24명",
        rule_id="grade2_add_sub_round1_bus_passengers",
    ),
    10: ElementaryVisualTemplate(
        problem_text="어떤 수보다 19 작은 수는 28과 34의 합과 같습니다. 어떤 수는 얼마입니까?",
        expression="answer=81",
        rule_id="grade2_add_sub_round1_unknown_from_sum",
    ),
    11: ElementaryVisualTemplate(
        problem_text="62 - 27 = ●, ● + 16 = ◆일 때 ◆의 값을 구하세요.",
        expression="answer=51",
        rule_id="grade2_add_sub_round1_symbol_value",
    ),
    12: ElementaryVisualTemplate(
        problem_text="한 달 동안 20권의 책을 읽기로 했습니다. 어제까지 14권, 오늘 2권을 읽었습니다. 남은 책은 몇 권입니까?",
        expression="answer_text=4권",
        rule_id="grade2_add_sub_round1_books_remaining",
    ),
}


_GRADE2_ADD_SUB_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="68과 49에 각각 9를 더한 수를 쓰세요.",
        expression="answer_text=77, 58",
        rule_id="grade2_add_sub_round2_add_nine_table",
    ),
    2: ElementaryVisualTemplate(
        problem_text="86 + 35를 계산해 보세요.",
        expression="answer=121",
        rule_id="grade2_add_sub_round2_86_plus_35",
    ),
    3: ElementaryVisualTemplate(
        problem_text="64 + 27 = 60 + 20 + 4 + □ = 80 + □ = □에서 빈칸을 채우세요.",
        expression="answer_text=7, 11, 91",
        rule_id="grade2_add_sub_round2_decompose_64_plus_27",
    ),
    4: ElementaryVisualTemplate(
        problem_text="42 + □ = 61에서 □ 안에 알맞은 수를 써넣으세요.",
        expression="answer=19",
        rule_id="grade2_add_sub_round2_missing_addend",
    ),
    5: ElementaryVisualTemplate(
        problem_text="27 + 58 = 85를 뺄셈식으로 나타내어 보세요.",
        expression="answer_text=85, 58, 27 / 85, 27, 58",
        rule_id="grade2_add_sub_round2_fact_family_subtractions",
    ),
    6: ElementaryVisualTemplate(
        problem_text="47과 9의 합과 차를 구하세요.",
        expression="answer_text=합: 56 / 차: 38",
        rule_id="grade2_add_sub_round2_sum_difference_47_9",
    ),
    7: ElementaryVisualTemplate(
        problem_text="56과 32에서 각각 8과 4를 뺀 수를 써넣으세요.",
        expression="answer_text=48, 28",
        rule_id="grade2_add_sub_round2_subtraction_table",
    ),
    8: ElementaryVisualTemplate(
        problem_text="세로 덧셈에서 □ 안에 알맞은 수를 써넣으세요.",
        expression="answer=9",
        rule_id="grade2_add_sub_round2_column_addition_blank",
    ),
    9: ElementaryVisualTemplate(
        problem_text="49 + □ > 74가 되도록 □ 안에 들어갈 수 있는 수를 모두 골라 ○표 하세요.",
        expression="answer_text=26, 27에 ○표",
        rule_id="grade2_add_sub_round2_possible_addends",
    ),
    10: ElementaryVisualTemplate(
        problem_text="63 - 7과 48 + 8의 크기를 비교하여 >, =, <를 써 넣으세요.",
        expression="answer_text==",
        rule_id="grade2_add_sub_round2_compare_results_equal",
    ),
}


_GRADE2_ADD_SUB_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="62 + 88 = 20 + □에서 □ 안에 알맞은 수를 써 넣으세요.",
        expression="answer=130",
        rule_id="grade2_add_sub_round2_decompose_62_plus_88",
    ),
    2: ElementaryVisualTemplate(
        problem_text="94 - 4□ = 46에서 □ 안에 알맞은 수를 써넣으세요.",
        expression="answer=8",
        rule_id="grade2_add_sub_round2_column_subtraction_blank",
    ),
    3: ElementaryVisualTemplate(
        problem_text="29 + 46 - 37과 41의 크기를 비교하세요.",
        expression="answer_text=<",
        rule_id="grade2_add_sub_round2_compare_three_term_expression",
    ),
    4: ElementaryVisualTemplate(
        problem_text="35, 74, 28에서 가장 큰 수에서 가장 작은 수를 뺀 후 나머지 한 수를 더한 값을 구하세요.",
        expression="answer=81",
        rule_id="grade2_add_sub_round2_largest_minus_smallest_plus_rest",
    ),
    5: ElementaryVisualTemplate(
        problem_text="28, 37, 55, 49에서 가장 큰 수와 가장 작은 수를 골라 차를 구하세요.",
        expression="answer=27",
        rule_id="grade2_add_sub_round2_largest_smallest_difference",
    ),
    6: ElementaryVisualTemplate(
        problem_text="10이 8개, 1이 5개인 수와 10이 6개, 1이 8개인 수의 합을 구하세요.",
        expression="answer=153",
        rule_id="grade2_add_sub_round2_sum_85_68",
    ),
    7: ElementaryVisualTemplate(
        problem_text="수 카드 4, 0, 7, 5, 8을 한 번씩만 사용하여 만들 수 있는 가장 큰 몇십과 가장 작은 몇십몇의 차를 구하세요.",
        expression="answer=35",
        rule_id="grade2_add_sub_round2_card_number_difference",
    ),
    8: ElementaryVisualTemplate(
        problem_text="줄넘기를 어제 68번, 오늘 77번 하였습니다. 모두 몇 번 하였습니까?",
        expression="answer_text=145번",
        rule_id="grade2_add_sub_round2_jump_rope_total",
    ),
    9: ElementaryVisualTemplate(
        problem_text="84쪽짜리 만화책을 47쪽까지 읽었습니다. 끝까지 읽으려면 몇 쪽을 더 읽으면 됩니까?",
        expression="answer_text=37쪽",
        rule_id="grade2_add_sub_round2_pages_remaining",
    ),
    10: ElementaryVisualTemplate(
        problem_text="연필 16자루에서 8자루를 주고 13자루를 받았습니다. 연필은 모두 몇 자루입니까?",
        expression="answer_text=21자루",
        rule_id="grade2_add_sub_round2_pencils_total",
    ),
}


_GRADE2_ADD_SUB_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="58과 39에 각각 8과 4를 더한 수를 쓰세요.",
        expression="answer_text=66, 43",
        rule_id="grade2_add_sub_round3_add_table",
    ),
    2: ElementaryVisualTemplate(
        problem_text="38 + 79를 계산해 보세요.",
        expression="answer=117",
        rule_id="grade2_add_sub_round3_38_plus_79",
    ),
    3: ElementaryVisualTemplate(
        problem_text="58 + 37 = 50 + 30 + 8 + □ = 80 + □ = □에서 빈칸을 채우세요.",
        expression="answer_text=7, 15, 95",
        rule_id="grade2_add_sub_round3_decompose_58_plus_37",
    ),
    4: ElementaryVisualTemplate(
        problem_text="37 + □ = 55에서 □ 안에 알맞은 수를 쓰세요.",
        expression="answer=18",
        rule_id="grade2_add_sub_round3_missing_addend",
    ),
    5: ElementaryVisualTemplate(
        problem_text="43 + 49 = 92를 뺄셈식으로 나타내어 보세요.",
        expression="answer_text=92, 43, 49 / 92, 49, 43",
        rule_id="grade2_add_sub_round3_fact_family_subtractions",
    ),
    6: ElementaryVisualTemplate(
        problem_text="25와 8의 합과 차를 구하세요.",
        expression="answer_text=합: 33 / 차: 17",
        rule_id="grade2_add_sub_round3_sum_difference_25_8",
    ),
    7: ElementaryVisualTemplate(
        problem_text="63과 25에서 각각 7을 뺀 수를 써넣으세요.",
        expression="answer_text=56, 18",
        rule_id="grade2_add_sub_round3_subtract_seven_table",
    ),
    8: ElementaryVisualTemplate(
        problem_text="세로 덧셈에서 □ 안에 알맞은 수를 써넣으세요.",
        expression="answer=5",
        rule_id="grade2_add_sub_round3_column_addition_blank",
    ),
    9: ElementaryVisualTemplate(
        problem_text="78 + □ > 94가 되도록 □ 안에 들어갈 수 있는 수를 모두 골라 ○표 하세요.",
        expression="answer_text=17, 18에 ○표",
        rule_id="grade2_add_sub_round3_possible_addends",
    ),
    10: ElementaryVisualTemplate(
        problem_text="47 + 7과 61 - 6의 크기를 비교하여 >, =, <를 써 넣으세요.",
        expression="answer_text=<",
        rule_id="grade2_add_sub_round3_compare_results_less",
    ),
}


_GRADE2_ADD_SUB_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="83 + 77 = 30 + □에서 □ 안에 알맞은 수를 써 넣으세요.",
        expression="answer=130",
        rule_id="grade2_add_sub_round3_decompose_83_plus_77",
    ),
    2: ElementaryVisualTemplate(
        problem_text="□3 - 37 = 26에서 □ 안에 알맞은 수를 써넣으세요.",
        expression="answer=6",
        rule_id="grade2_add_sub_round3_column_subtraction_blank",
    ),
    3: ElementaryVisualTemplate(
        problem_text="38 + 84 - 26과 95의 크기를 비교하세요.",
        expression="answer_text=>",
        rule_id="grade2_add_sub_round3_compare_three_term_expression",
    ),
    4: ElementaryVisualTemplate(
        problem_text="18, 25, 53에서 가장 큰 수에서 나머지 한 수를 뺀 후 가장 작은 수를 더한 값을 구하세요.",
        expression="answer=46",
        rule_id="grade2_add_sub_round3_largest_minus_middle_plus_smallest",
    ),
    5: ElementaryVisualTemplate(
        problem_text="69, 34, 52, 71에서 가장 큰 수와 가장 작은 수를 골라 차를 구하세요.",
        expression="answer=37",
        rule_id="grade2_add_sub_round3_largest_smallest_difference",
    ),
    6: ElementaryVisualTemplate(
        problem_text="10이 5개, 1이 4개인 수와 10이 8개, 1이 7개인 수의 합을 구하세요.",
        expression="answer=141",
        rule_id="grade2_add_sub_round3_sum_54_87",
    ),
    7: ElementaryVisualTemplate(
        problem_text="수 카드 9, 5, 0, 2, 7을 한 번씩만 사용하여 만들 수 있는 가장 큰 몇십과 가장 작은 몇십몇의 차를 구하세요.",
        expression="answer=65",
        rule_id="grade2_add_sub_round3_card_number_difference",
    ),
    8: ElementaryVisualTemplate(
        problem_text="학급 문고에는 동화책 78권, 위인전 56권이 있습니다. 모두 몇 권입니까?",
        expression="answer_text=134권",
        rule_id="grade2_add_sub_round3_library_books_total",
    ),
    9: ElementaryVisualTemplate(
        problem_text="소영이는 붙임 딱지를 17개, 윤철이는 32개 모았습니다. 누가 몇 개를 더 모았습니까?",
        expression="answer_text=윤철, 15개",
        rule_id="grade2_add_sub_round3_sticker_difference",
    ),
    10: ElementaryVisualTemplate(
        problem_text="운동장에 학생이 44명 있었습니다. 15명이 교실로 들어가고 28명이 운동장에 나왔다면 모두 몇 명입니까?",
        expression="answer_text=57명",
        rule_id="grade2_add_sub_round3_playground_students",
    ),
}


_GRADE2_LENGTH_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="색 테이프의 긴 쪽의 길이는 뼘으로 몇 번입니까?",
        expression="answer_text=5번",
        topic="measurement",
        rule_id="grade2_length_round1_handspan_tape",
    ),
    2: ElementaryVisualTemplate(
        problem_text="크레파스의 길이는 약 몇 cm인가요?",
        expression="answer_text=6 cm",
        topic="measurement",
        rule_id="grade2_length_round1_crayon_centimeters",
    ),
    3: ElementaryVisualTemplate(
        problem_text="색 테이프의 길이는 클립으로 몇 번인가요?",
        expression="answer_text=5번",
        topic="measurement",
        rule_id="grade2_length_round1_clip_tape",
    ),
    4: ElementaryVisualTemplate(
        problem_text="자를 보고 큰 눈금 한 칸의 길이를 읽고 나타내세요.",
        expression="answer_text=1 센티미터, 1 cm",
        topic="measurement",
        rule_id="grade2_length_round1_ruler_unit",
    ),
    5: ElementaryVisualTemplate(
        problem_text="길이를 재는 데 더 정확한 단위는 어느 것인지 기호를 쓰세요.",
        expression="answer_text=나",
        topic="measurement",
        rule_id="grade2_length_round1_more_exact_unit",
    ),
    6: ElementaryVisualTemplate(
        problem_text="선의 길이를 어림하고 자로 길이를 재어 보세요.",
        expression="answer_text=어림한 길이: (예) 7 cm / 자로 잰 길이: 6 cm",
        topic="measurement",
        rule_id="grade2_length_round1_estimate_and_measure_line",
    ),
    7: ElementaryVisualTemplate(
        problem_text="옷핀의 길이를 더 잘 어림한 사람을 고르세요.",
        expression="answer_text=지훈",
        topic="measurement",
        rule_id="grade2_length_round1_better_estimate_pin",
    ),
    8: ElementaryVisualTemplate(
        problem_text="책상의 짧은 쪽의 길이는 길이가 1 cm인 지우개로 32번입니다. 몇 cm입니까?",
        expression="answer_text=32 cm",
        topic="measurement",
        rule_id="grade2_length_round1_eraser_units",
    ),
}


_GRADE2_LENGTH_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="보기에서 알맞은 길이를 골라 문장을 완성하세요. 볼펜과 새끼손가락 길이를 고르세요.",
        expression="answer_text=(1) 다, (2) 가",
        topic="measurement",
        rule_id="grade2_length_round1_choose_length_sentences",
    ),
    2: ElementaryVisualTemplate(
        problem_text="길이를 자로 바르게 잰 것을 찾아 기호를 쓰세요.",
        expression="answer_text=나",
        topic="measurement",
        rule_id="grade2_length_round1_correct_ruler_position",
    ),
    3: ElementaryVisualTemplate(
        problem_text="나사못의 길이는 몇 cm입니까?",
        expression="answer_text=7 cm",
        topic="measurement",
        rule_id="grade2_length_round1_screw_length",
    ),
    4: ElementaryVisualTemplate(
        problem_text="길이가 다른 것을 찾아 기호를 쓰세요.",
        expression="answer_text=나",
        topic="measurement",
        rule_id="grade2_length_round1_different_length",
    ),
    5: ElementaryVisualTemplate(
        problem_text="길이가 14 cm인 테이프를 하루에 1 cm씩 잘라서 사용하면 며칠 동안 사용할 수 있습니까?",
        expression="answer_text=14일",
        topic="measurement",
        rule_id="grade2_length_round1_tape_days",
    ),
    6: ElementaryVisualTemplate(
        problem_text="찬우와 지혜 중에서 더 긴 우산을 가지고 있는 사람을 고르세요.",
        expression="answer_text=찬우",
        topic="measurement",
        rule_id="grade2_length_round1_longer_umbrella",
    ),
    7: ElementaryVisualTemplate(
        problem_text="선 ㄱ의 길이와 선 ㄴ의 길이의 합은 몇 cm입니까?",
        expression="answer_text=7 cm",
        topic="measurement",
        rule_id="grade2_length_round1_sum_two_segments",
    ),
    8: ElementaryVisualTemplate(
        problem_text="물건의 긴 쪽의 길이를 비교하여 가장 긴 물건을 고르세요.",
        expression="answer_text=냉장고",
        topic="measurement",
        rule_id="grade2_length_round1_longest_object",
    ),
}


_GRADE2_LENGTH_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="피아노의 긴 쪽의 길이를 뼘으로 재어 나타낸 표에서 뼘의 길이가 가장 긴 사람을 고르세요.",
        expression="answer_text=유진",
        topic="measurement",
        rule_id="grade2_length_round1_longest_handspan_person",
    ),
    2: ElementaryVisualTemplate(
        problem_text="작은 사각형의 한 변이 1 cm일 때 굵은 선의 길이를 구하세요.",
        expression="answer_text=8 cm",
        topic="measurement",
        rule_id="grade2_length_round1_l_shape_length",
    ),
    3: ElementaryVisualTemplate(
        problem_text="가의 길이가 2 cm일 때 나의 길이는 몇 cm입니까?",
        expression="answer_text=8 cm",
        topic="measurement",
        rule_id="grade2_length_round1_scaled_segment_length",
    ),
    4: ElementaryVisualTemplate(
        problem_text="연필의 길이를 가장 가깝게 어림한 사람을 고르세요.",
        expression="answer_text=은희",
        topic="measurement",
        rule_id="grade2_length_round1_closest_pencil_estimate",
    ),
}


_GRADE2_LENGTH_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="손을 이용하여 나무막대의 길이를 잰 것입니다. 나무막대는 손으로 몇 번입니까?",
        expression="answer_text=6번",
        topic="measurement",
        rule_id="grade2_length_round2_hand_wood_stick",
    ),
    2: ElementaryVisualTemplate(
        problem_text="주어진 선의 길이는 엄지손톱으로 몇 번입니까?",
        expression="answer_text=7번",
        topic="measurement",
        rule_id="grade2_length_round2_thumbnail_line",
    ),
    3: ElementaryVisualTemplate(
        problem_text="막대기의 길이는 몇 뼘인가요?",
        expression="answer_text=3뼘",
        topic="measurement",
        rule_id="grade2_length_round2_handspan_stick",
    ),
    4: ElementaryVisualTemplate(
        problem_text="클립 4개의 길이와 같은 길이의 연필에 ○표 하세요.",
        expression="answer_text=세 번째에 ○표",
        topic="measurement",
        rule_id="grade2_length_round2_four_clips_pencil",
    ),
    5: ElementaryVisualTemplate(
        problem_text="길이가 가장 짧은 것을 찾아 ○표 하세요.",
        expression="answer_text=세 번째에 ○표",
        topic="measurement",
        rule_id="grade2_length_round2_shortest_bar",
    ),
    6: ElementaryVisualTemplate(
        problem_text="연필의 길이를 어림하고 자로 재어 확인하세요.",
        expression="answer_text=약 5 cm / 5 cm",
        topic="measurement",
        rule_id="grade2_length_round2_estimate_pencil",
    ),
    7: ElementaryVisualTemplate(
        problem_text="연필로 줄넘기와 지팡이의 길이를 재었습니다. 더 긴 것을 고르세요.",
        expression="answer_text=줄넘기",
        topic="measurement",
        rule_id="grade2_length_round2_jump_rope_cane",
    ),
    8: ElementaryVisualTemplate(
        problem_text="재희와 민석이가 다른 길이의 막대로 사물함의 긴 쪽을 재었습니다. 막대가 더 긴 사람을 고르세요.",
        expression="answer_text=재희",
        topic="measurement",
        rule_id="grade2_length_round2_longer_measuring_stick",
    ),
}


_GRADE2_LENGTH_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="하은이와 지수가 각자의 뼘으로 창문의 긴 쪽을 재었습니다. 한 뼘의 길이가 더 짧은 사람을 쓰세요.",
        expression="answer_text=지수",
        topic="measurement",
        rule_id="grade2_length_round2_shorter_handspan_person",
    ),
    2: ElementaryVisualTemplate(
        problem_text="빨간 선의 길이는 몇 cm인지 쓰세요.",
        expression="answer_text=3 cm",
        topic="measurement",
        rule_id="grade2_length_round2_red_line_length",
    ),
    3: ElementaryVisualTemplate(
        problem_text="연필의 길이는 1 cm로 몇 번입니까?",
        expression="answer_text=6번",
        topic="measurement",
        rule_id="grade2_length_round2_pencil_one_cm_units",
    ),
    4: ElementaryVisualTemplate(
        problem_text="가장 큰 사각형의 가로의 길이는 몇 cm입니까?",
        expression="answer_text=5 cm",
        topic="measurement",
        rule_id="grade2_length_round2_rectangle_width",
    ),
    5: ElementaryVisualTemplate(
        problem_text="한 칸의 길이가 1 cm일 때 주어진 길이만큼 색칠하세요.",
        expression="answer_text=4칸 색칠",
        topic="measurement",
        rule_id="grade2_length_round2_color_four_centimeters",
    ),
    6: ElementaryVisualTemplate(
        problem_text="공책의 긴 쪽의 길이는 길이가 1 cm인 주사위로 20번입니다. 몇 cm입니까?",
        expression="answer_text=20 cm",
        topic="measurement",
        rule_id="grade2_length_round2_notebook_dice_units",
    ),
    7: ElementaryVisualTemplate(
        problem_text="5 cm를 나타내지 않는 것을 찾아 ○표 하세요.",
        expression="answer_text=세 번째에 ○",
        topic="measurement",
        rule_id="grade2_length_round2_not_five_cm",
    ),
    8: ElementaryVisualTemplate(
        problem_text="끈의 길이는 약 몇 cm인지 쓰세요.",
        expression="answer_text=약 7 cm",
        topic="measurement",
        rule_id="grade2_length_round2_string_estimate",
    ),
}


_GRADE2_LENGTH_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="실제 길이가 20 cm인 공책의 길이를 희주와 서윤이가 어림했습니다. 실제 길이에 더 가깝게 어림한 사람을 고르세요.",
        expression="answer_text=서윤",
        topic="measurement",
        rule_id="grade2_length_round2_closest_notebook_estimate",
    ),
    2: ElementaryVisualTemplate(
        problem_text="옷핀의 실제 길이에 가장 가까운 것을 찾아 ○표 하세요.",
        expression="answer_text=3 cm에 ○표",
        topic="measurement",
        rule_id="grade2_length_round2_safety_pin_actual_length",
    ),
    3: ElementaryVisualTemplate(
        problem_text="손으로 포장용지의 길이를 재었을 때 긴 쪽의 길이는 짧은 쪽의 길이보다 몇 번 더 깁니까?",
        expression="answer_text=3번",
        topic="measurement",
        rule_id="grade2_length_round2_wrapping_paper_ratio",
    ),
    4: ElementaryVisualTemplate(
        problem_text="연필, 젓가락, 풀을 길이가 긴 것부터 차례로 쓰세요.",
        expression="answer_text=젓가락, 연필, 풀",
        topic="measurement",
        rule_id="grade2_length_round2_order_objects_by_length",
    ),
}


_GRADE2_LENGTH_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="손을 이용하여 나무막대의 길이를 잰 것입니다. 나무막대는 손으로 몇 번입니까?",
        expression="answer_text=5번",
        topic="measurement",
        rule_id="grade2_length_round3_hand_wood_stick",
    ),
    2: ElementaryVisualTemplate(
        problem_text="주어진 선의 길이는 엄지손톱으로 몇 번입니까?",
        expression="answer_text=8번",
        topic="measurement",
        rule_id="grade2_length_round3_thumbnail_line",
    ),
    3: ElementaryVisualTemplate(
        problem_text="우산의 길이는 몇 뼘인가요?",
        expression="answer_text=4뼘",
        topic="measurement",
        rule_id="grade2_length_round3_umbrella_handspan",
    ),
    4: ElementaryVisualTemplate(
        problem_text="풀 5개의 길이와 같은 길이의 색 테이프에 ○표 하세요.",
        expression="answer_text=파란색에 ○표",
        topic="measurement",
        rule_id="grade2_length_round3_five_glues_tape",
    ),
    5: ElementaryVisualTemplate(
        problem_text="길이가 긴 것부터 차례대로 번호를 쓰세요.",
        expression="answer_text=(위에서부터) 2, 1, 3",
        topic="measurement",
        rule_id="grade2_length_round3_order_bars_long_to_short",
    ),
    6: ElementaryVisualTemplate(
        problem_text="막대의 길이를 어림하고 자로 재어 확인하세요.",
        expression="answer_text=약 4 cm / 4 cm",
        topic="measurement",
        rule_id="grade2_length_round3_estimate_stick",
    ),
    7: ElementaryVisualTemplate(
        problem_text="빨대로 잰 횟수가 초록색 막대는 6번, 노란색 막대는 7번입니다. 더 짧은 막대를 고르세요.",
        expression="answer_text=초록색",
        topic="measurement",
        rule_id="grade2_length_round3_shorter_bar_by_straw",
    ),
}


_GRADE2_LENGTH_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="수영이와 민호가 다른 길이의 연필로 책상의 긴 쪽을 재었습니다. 연필의 길이가 더 짧은 사람을 고르세요.",
        expression="answer_text=민호",
        topic="measurement",
        rule_id="grade2_length_round3_shorter_pencil_person",
    ),
    2: ElementaryVisualTemplate(
        problem_text="설희와 지은이가 각자의 뼘으로 문의 짧은 쪽 길이를 재었습니다. 한 뼘의 길이가 더 긴 사람을 쓰세요.",
        expression="answer_text=지은",
        topic="measurement",
        rule_id="grade2_length_round3_longer_handspan_person",
    ),
    3: ElementaryVisualTemplate(
        problem_text="빨간 선의 길이는 몇 cm인지 쓰세요.",
        expression="answer_text=1 cm",
        topic="measurement",
        rule_id="grade2_length_round3_red_line_length",
    ),
    4: ElementaryVisualTemplate(
        problem_text="나무 막대의 길이는 1 cm로 몇 번입니까?",
        expression="answer_text=5번",
        topic="measurement",
        rule_id="grade2_length_round3_wood_stick_one_cm_units",
    ),
    5: ElementaryVisualTemplate(
        problem_text="가장 큰 사각형의 세로의 길이는 몇 cm입니까?",
        expression="answer_text=2 cm",
        topic="measurement",
        rule_id="grade2_length_round3_rectangle_height",
    ),
    6: ElementaryVisualTemplate(
        problem_text="한 칸의 길이가 1 cm일 때 주어진 길이만큼 색칠하세요.",
        expression="answer_text=6칸 색칠",
        topic="measurement",
        rule_id="grade2_length_round3_color_six_centimeters",
    ),
    7: ElementaryVisualTemplate(
        problem_text="막대사탕의 길이는 길이가 1 cm인 주사위로 6번입니다. 몇 cm입니까?",
        expression="answer_text=6 cm",
        topic="measurement",
        rule_id="grade2_length_round3_lollipop_dice_units",
    ),
    8: ElementaryVisualTemplate(
        problem_text="3 cm를 나타내지 않는 것을 찾아 ○표 하세요.",
        expression="answer_text=첫 번째에 ○표",
        topic="measurement",
        rule_id="grade2_length_round3_not_three_cm",
    ),
}


_GRADE2_LENGTH_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="크레파스의 길이는 약 몇 cm인지 쓰세요.",
        expression="answer_text=약 6 cm",
        topic="measurement",
        rule_id="grade2_length_round3_crayon_estimate",
    ),
    2: ElementaryVisualTemplate(
        problem_text="실제 길이가 7 cm인 막대 과자의 길이를 더 가깝게 어림한 사람을 고르세요.",
        expression="answer_text=희철",
        topic="measurement",
        rule_id="grade2_length_round3_closest_cookie_stick_estimate",
    ),
    3: ElementaryVisualTemplate(
        problem_text="필통의 실제 길이에 가장 가까운 것을 찾아 ○표 하세요.",
        expression="answer_text=20 cm에 ○표",
        topic="measurement",
        rule_id="grade2_length_round3_pencil_case_actual_length",
    ),
    4: ElementaryVisualTemplate(
        problem_text="모형을 가장 길게 연결한 모양에 ○표 하세요.",
        expression="answer_text=첫 번째에 ○표",
        topic="measurement",
        rule_id="grade2_length_round3_longest_connected_blocks",
    ),
    5: ElementaryVisualTemplate(
        problem_text="1 cm가 몇 번이면 9 cm인지, 5센티미터는 몇 cm가 5번인지, 1 cm가 7번이면 몇 cm인지 쓰세요.",
        expression="answer_text=9, 1, 7",
        topic="measurement",
        rule_id="grade2_length_round3_centimeter_blanks",
    ),
}


_GRADE2_LENGTH_2_2_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="4 m는 몇 cm인지 쓰세요.",
        expression="answer=400",
        topic="measurement",
        rule_id="grade2_2_length_round1_m_to_cm",
    ),
    2: ElementaryVisualTemplate(
        problem_text="1 m보다 45 cm 더 긴 길이는 몇 m 몇 cm인지 구하세요.",
        expression="answer_text=1 m 45 cm",
        topic="measurement",
        rule_id="grade2_2_length_round1_1m_plus_45cm",
    ),
    3: ElementaryVisualTemplate(
        problem_text="5 m는 몇 cm이고 700 cm는 몇 m인지 쓰세요.",
        expression="answer_text=500, 7",
        topic="measurement",
        rule_id="grade2_2_length_round1_cm_m_conversion",
    ),
    4: ElementaryVisualTemplate(
        problem_text="1 m짜리 테이프는 10 cm 길이의 자로 몇 번 잰 것과 같은지 쓰세요.",
        expression="answer=10",
        topic="measurement",
        rule_id="grade2_2_length_round1_ten_cm_units",
    ),
    5: ElementaryVisualTemplate(
        problem_text="m 단위로 나타내기에 가장 알맞은 것에 ○표 하세요.",
        expression="answer_text=첫 번째에 ○표",
        topic="measurement",
        rule_id="grade2_2_length_round1_best_meter_unit",
    ),
    6: ElementaryVisualTemplate(
        problem_text="줄넘기의 길이를 cm와 m cm 두 가지 방법으로 나타내세요.",
        expression="answer_text=160, 1, 60",
        topic="measurement",
        rule_id="grade2_2_length_round1_jump_rope_length",
    ),
    7: ElementaryVisualTemplate(
        problem_text="길이를 바르게 나타낸 것을 고르세요.",
        expression="answer_text=③",
        topic="measurement",
        rule_id="grade2_2_length_round1_correct_length_expression",
    ),
    8: ElementaryVisualTemplate(
        problem_text="1 m 1 cm와 110 cm의 길이를 비교하세요.",
        expression="answer_text=<",
        topic="measurement",
        rule_id="grade2_2_length_round1_compare_1m1cm_110cm",
    ),
    9: ElementaryVisualTemplate(
        problem_text="4 m 50 cm와 7 m 43 cm를 더하세요.",
        expression="answer_text=11 m 93 cm",
        topic="measurement",
        rule_id="grade2_2_length_round1_add_lengths",
    ),
}


_GRADE2_LENGTH_2_2_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="320 cm와 1 m 55 cm의 합은 몇 m 몇 cm인지 구하세요.",
        expression="answer_text=4 m 75 cm",
        topic="measurement",
        rule_id="grade2_2_length_round1_blackboard_sum",
    ),
    2: ElementaryVisualTemplate(
        problem_text="7 m 70 cm에서 4 m 55 cm를 빼세요.",
        expression="answer_text=3 m 15 cm",
        topic="measurement",
        rule_id="grade2_2_length_round1_subtract_lengths",
    ),
    3: ElementaryVisualTemplate(
        problem_text="5 m 76 cm에서 343 cm를 빼세요.",
        expression="answer_text=2 m 33 cm",
        topic="measurement",
        rule_id="grade2_2_length_round1_subtract_cm",
    ),
    4: ElementaryVisualTemplate(
        problem_text="3 m 10 cm와 1 m 50 cm를 합친 색 테이프의 전체 길이를 구하세요.",
        expression="answer_text=4 m 60 cm",
        topic="measurement",
        rule_id="grade2_2_length_round1_tape_total",
    ),
    5: ElementaryVisualTemplate(
        problem_text="전체 8 m 64 cm에서 3 m 48 cm를 뺀 길이를 구하세요.",
        expression="answer_text=5 m 16 cm",
        topic="measurement",
        rule_id="grade2_2_length_round1_remaining_length",
    ),
    6: ElementaryVisualTemplate(
        problem_text="680 cm는 7 m보다 몇 cm 더 짧은지 구하세요.",
        expression="answer_text=20 cm",
        topic="measurement",
        rule_id="grade2_2_length_round1_680cm_shorter_than_7m",
    ),
    7: ElementaryVisualTemplate(
        problem_text="공원과 정류장 중 집에서 어느 곳이 얼마나 더 가까운지 구하세요.",
        expression="answer_text=정류장, 15 m 50 cm",
        topic="measurement",
        rule_id="grade2_2_length_round1_closer_place",
    ),
    8: ElementaryVisualTemplate(
        problem_text="손바닥 폭 10 cm가 약 10번일 때 나무 막대 길이는 약 몇 m인지 구하세요.",
        expression="answer_text=1 m",
        topic="measurement",
        rule_id="grade2_2_length_round1_hand_span_meter",
    ),
}


_GRADE2_LENGTH_2_2_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="길이를 어림할 때 m를 사용하는 것을 고르세요.",
        expression="answer_text=②",
        topic="measurement",
        rule_id="grade2_2_length_round1_meter_estimation_choice",
    ),
    2: ElementaryVisualTemplate(
        problem_text="1 m 75 cm는 1 m 23 cm보다 몇 cm 더 큰지 구하세요.",
        expression="answer_text=52 cm",
        topic="measurement",
        rule_id="grade2_2_length_round1_height_difference",
    ),
    3: ElementaryVisualTemplate(
        problem_text="12 cm인 손의 길이의 약 6배인 책상 가로 길이를 구하세요.",
        expression="answer_text=72 cm",
        topic="measurement",
        rule_id="grade2_2_length_round1_desk_width_estimate",
    ),
}


_GRADE2_LENGTH_2_2_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="9 m는 몇 cm인지 쓰세요.",
        expression="answer=900",
        topic="measurement",
        rule_id="grade2_2_length_round2_9m_to_cm",
    ),
    2: ElementaryVisualTemplate(
        problem_text="5 m 29 cm를 바르게 읽어 보세요.",
        expression="answer_text=5 미터 29 센티미터",
        topic="measurement",
        rule_id="grade2_2_length_round2_read_5m29cm",
    ),
    3: ElementaryVisualTemplate(
        problem_text="3 m는 몇 cm이고 400 cm는 몇 m인지 쓰세요.",
        expression="answer_text=300, 4",
        topic="measurement",
        rule_id="grade2_2_length_round2_m_cm_conversion",
    ),
    4: ElementaryVisualTemplate(
        problem_text="1 m는 1 cm를 몇 번 이은 것과 같은지 쓰세요.",
        expression="answer=100",
        topic="measurement",
        rule_id="grade2_2_length_round2_one_meter_centimeter_count",
    ),
    5: ElementaryVisualTemplate(
        problem_text="길이가 10 cm인 연필 10개를 맞대어 이어 붙인 길이는 몇 m인지 구하세요.",
        expression="answer_text=1 m",
        topic="measurement",
        rule_id="grade2_2_length_round2_ten_pencils_one_meter",
    ),
    6: ElementaryVisualTemplate(
        problem_text="나무막대의 길이를 cm와 m cm 두 가지 방법으로 나타내세요.",
        expression="answer_text=190, 1, 90",
        topic="measurement",
        rule_id="grade2_2_length_round2_stick_length_two_ways",
    ),
    7: ElementaryVisualTemplate(
        problem_text="303 cm와 길이가 같은 것을 고르세요.",
        expression="answer_text=④",
        topic="measurement",
        rule_id="grade2_2_length_round2_same_as_303cm",
    ),
    8: ElementaryVisualTemplate(
        problem_text="51 m 1 cm와 510 cm의 길이를 비교하세요.",
        expression="answer_text=>",
        topic="measurement",
        rule_id="grade2_2_length_round2_compare_51m1cm_510cm",
    ),
    9: ElementaryVisualTemplate(
        problem_text="3 m 37 cm와 7 m 54 cm를 더하세요.",
        expression="answer_text=10 m 91 cm",
        topic="measurement",
        rule_id="grade2_2_length_round2_add_lengths",
    ),
}


_GRADE2_LENGTH_2_2_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="가로 120 cm와 세로 1 m 50 cm인 식탁의 가로와 세로 길이의 합은 몇 m 몇 cm인지 구하세요.",
        expression="answer_text=2 m 70 cm",
        topic="measurement",
        rule_id="grade2_2_length_round2_table_total_length",
    ),
    2: ElementaryVisualTemplate(
        problem_text="5 m 37 cm에서 4 m 12 cm를 빼세요.",
        expression="answer_text=1 m 25 cm",
        topic="measurement",
        rule_id="grade2_2_length_round2_subtract_lengths",
    ),
    3: ElementaryVisualTemplate(
        problem_text="8 m 42 cm에서 336 cm를 빼세요.",
        expression="answer_text=5 m 6 cm",
        topic="measurement",
        rule_id="grade2_2_length_round2_subtract_cm",
    ),
    4: ElementaryVisualTemplate(
        problem_text="3 m 32 cm와 4 m 33 cm를 이어 붙인 색 테이프의 전체 길이를 구하세요.",
        expression="answer_text=7 m 65 cm",
        topic="measurement",
        rule_id="grade2_2_length_round2_tape_total",
    ),
    5: ElementaryVisualTemplate(
        problem_text="7 m 23 cm에서 4 m 36 cm를 뺀 길이를 구하세요.",
        expression="answer_text=2 m 87 cm",
        topic="measurement",
        rule_id="grade2_2_length_round2_remaining_length",
    ),
    6: ElementaryVisualTemplate(
        problem_text="410 cm는 4 m보다 몇 cm 더 긴지 구하세요.",
        expression="answer_text=10 cm",
        topic="measurement",
        rule_id="grade2_2_length_round2_410cm_longer_than_4m",
    ),
    7: ElementaryVisualTemplate(
        problem_text="집과 병원 중에서 어느 곳이 서점에서 얼마나 더 가까운지 구하세요.",
        expression="answer_text=집, 5 m 88 cm",
        topic="measurement",
        rule_id="grade2_2_length_round2_closer_place",
    ),
}


_GRADE2_LENGTH_2_2_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="한 걸음이 50 cm이고 나무막대의 길이가 약 4걸음일 때 나무막대의 길이는 약 몇 m인지 구하세요.",
        expression="answer_text=약 2 m",
        topic="measurement",
        rule_id="grade2_2_length_round2_step_estimate_meter",
    ),
    2: ElementaryVisualTemplate(
        problem_text="내 양팔 사이의 길이보다 긴 것을 고르세요.",
        expression="answer_text=①",
        topic="measurement",
        rule_id="grade2_2_length_round2_longer_than_arm_span",
    ),
    3: ElementaryVisualTemplate(
        problem_text="동생의 색 테이프 2 m 70 cm는 희수의 색 테이프 2 m 30 cm보다 몇 cm 더 긴지 구하세요.",
        expression="answer_text=40 cm",
        topic="measurement",
        rule_id="grade2_2_length_round2_tape_difference",
    ),
    4: ElementaryVisualTemplate(
        problem_text="운동장의 가로 길이를 한 걸음 50 cm로 재었더니 10걸음이었습니다. 운동장의 가로 길이는 약 몇 m인지 구하세요.",
        expression="answer_text=5 m",
        topic="measurement",
        rule_id="grade2_2_length_round2_playground_width_estimate",
    ),
}


_GRADE2_LENGTH_2_2_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="800 cm는 몇 m인지 쓰세요.",
        expression="answer=8",
        topic="measurement",
        rule_id="grade2_2_length_round3_800cm_to_m",
    ),
    2: ElementaryVisualTemplate(
        problem_text="3 m보다 20 cm 더 긴 길이는 몇 m 몇 cm인지 구하세요.",
        expression="answer_text=3 m 20 cm",
        topic="measurement",
        rule_id="grade2_2_length_round3_3m_plus_20cm",
    ),
    3: ElementaryVisualTemplate(
        problem_text="9 m는 몇 cm이고 300 cm는 몇 m인지 쓰세요.",
        expression="answer_text=900, 3",
        topic="measurement",
        rule_id="grade2_2_length_round3_m_cm_conversion",
    ),
    4: ElementaryVisualTemplate(
        problem_text="30 cm 길이의 자로 3번 잰 후 10 cm가 더 길었다면 책상의 가로 길이는 몇 m인지 구하세요.",
        expression="answer_text=1 m",
        topic="measurement",
        rule_id="grade2_2_length_round3_desk_width_one_meter",
    ),
    5: ElementaryVisualTemplate(
        problem_text="cm 단위를 써서 나타내기에 가장 알맞은 것에 ○표 하세요.",
        expression="answer_text=숟가락의 길이에 ○표",
        topic="measurement",
        rule_id="grade2_2_length_round3_best_centimeter_unit",
    ),
    6: ElementaryVisualTemplate(
        problem_text="나무막대의 길이를 cm와 m cm 두 가지 방법으로 나타내세요.",
        expression="answer_text=130, 1, 30",
        topic="measurement",
        rule_id="grade2_2_length_round3_stick_length_two_ways",
    ),
    7: ElementaryVisualTemplate(
        problem_text="성냥개비의 길이는 약 몇 cm인지 고르세요.",
        expression="answer_text=5 cm",
        topic="measurement",
        rule_id="grade2_2_length_round3_matchstick_length",
    ),
    8: ElementaryVisualTemplate(
        problem_text="6 m와 600 cm의 길이를 비교하세요.",
        expression="answer_text==",
        topic="measurement",
        rule_id="grade2_2_length_round3_compare_6m_600cm",
    ),
    9: ElementaryVisualTemplate(
        problem_text="3 m 30 cm와 5 m 42 cm의 길이의 합을 구하세요.",
        expression="answer_text=8 m 72 cm",
        topic="measurement",
        rule_id="grade2_2_length_round3_add_lengths",
    ),
}


_GRADE2_LENGTH_2_2_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="2 m 16 cm와 4 m 62 cm인 두 색 테이프의 길이는 모두 몇 cm인지 구하세요.",
        expression="answer_text=678 cm",
        topic="measurement",
        rule_id="grade2_2_length_round3_tape_total_cm",
    ),
    2: ElementaryVisualTemplate(
        problem_text="4 m 86 cm에서 2 m 32 cm를 빼세요.",
        expression="answer_text=2 m 54 cm",
        topic="measurement",
        rule_id="grade2_2_length_round3_subtract_lengths",
    ),
    3: ElementaryVisualTemplate(
        problem_text="6 m 82 cm에서 264 cm를 빼세요.",
        expression="answer_text=4 m 18 cm",
        topic="measurement",
        rule_id="grade2_2_length_round3_subtract_cm",
    ),
    4: ElementaryVisualTemplate(
        problem_text="1 m 10 cm와 1 m 30 cm를 이어 붙인 색 테이프의 전체 길이를 구하세요.",
        expression="answer_text=2 m 40 cm",
        topic="measurement",
        rule_id="grade2_2_length_round3_tape_total",
    ),
    5: ElementaryVisualTemplate(
        problem_text="4 m 27 cm에서 1 m 64 cm를 뺀 길이를 구하세요.",
        expression="answer_text=2 m 63 cm",
        topic="measurement",
        rule_id="grade2_2_length_round3_remaining_length",
    ),
    6: ElementaryVisualTemplate(
        problem_text="9 m보다 30 cm 짧은 길이는 몇 cm인지 구하세요.",
        expression="answer_text=870 cm",
        topic="measurement",
        rule_id="grade2_2_length_round3_30cm_shorter_than_9m",
    ),
    7: ElementaryVisualTemplate(
        problem_text="도서관과 서점 중에서 어느 곳이 학교에서 얼마나 더 가까운지 구하세요.",
        expression="answer_text=도서관, 8 m 75 cm",
        topic="measurement",
        rule_id="grade2_2_length_round3_closer_place",
    ),
}


_GRADE2_LENGTH_2_2_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="가로등과 가로등 사이의 길이가 5 m로 일정할 때 도로의 길이는 약 몇 m인지 구하세요.",
        expression="answer_text=약 30 m",
        topic="measurement",
        rule_id="grade2_2_length_round3_street_lamp_estimate",
    ),
    2: ElementaryVisualTemplate(
        problem_text="내 양팔 사이의 길이보다 짧은 것을 고르세요.",
        expression="answer_text=④",
        topic="measurement",
        rule_id="grade2_2_length_round3_shorter_than_arm_span",
    ),
    3: ElementaryVisualTemplate(
        problem_text="준수와 희철이의 키는 각각 1 m 30 cm, 1 m 11 cm입니다. 두 사람의 키의 차는 몇 cm인지 구하세요.",
        expression="answer_text=19 cm",
        topic="measurement",
        rule_id="grade2_2_length_round3_height_difference",
    ),
    4: ElementaryVisualTemplate(
        problem_text="손의 길이가 15 cm인 손으로 텔레비전의 가로와 세로를 재었을 때 가로는 9번, 세로는 7번이었습니다. 가로 길이는 세로 길이보다 몇 cm 더 긴지 구하세요.",
        expression="answer_text=30 cm",
        topic="measurement",
        rule_id="grade2_2_length_round3_tv_width_difference",
    ),
}


_GRADE2_TIME_2_2_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="시계를 보고 시각을 쓰세요.",
        expression="answer_text=5, 35",
        topic="measurement",
        rule_id="grade2_2_time_round1_read_clock",
    ),
    2: ElementaryVisualTemplate(
        problem_text="짧은 바늘이 8과 9 사이를 가리키고 긴바늘이 5를 가리키면 몇 시 몇 분인지 쓰세요.",
        expression="answer_text=8, 25",
        topic="measurement",
        rule_id="grade2_2_time_round1_hand_description",
    ),
    3: ElementaryVisualTemplate(
        problem_text="호석이가 30분 동안 피아노를 치고 난 뒤 시각이 10시 15분입니다. 시작한 시각을 구하세요.",
        expression="answer_text=9 시 45 분",
        topic="measurement",
        rule_id="grade2_2_time_round1_start_time_before_30min",
    ),
    4: ElementaryVisualTemplate(
        problem_text="시계의 긴바늘과 짧은바늘을 그려 2시 39분을 나타내세요.",
        expression="answer_text=2 시 39 분",
        topic="measurement",
        rule_id="grade2_2_time_round1_draw_2_39",
    ),
    5: ElementaryVisualTemplate(
        problem_text="거울에 비친 시계를 보고 이 시계가 나타내는 시각을 쓰세요.",
        expression="answer_text=2, 55, 3, 5",
        topic="measurement",
        rule_id="grade2_2_time_round1_mirror_clock",
    ),
    6: ElementaryVisualTemplate(
        problem_text="시계가 나타내는 시각에서 20분 후의 시각을 쓰세요.",
        expression="answer_text=5, 10",
        topic="measurement",
        rule_id="grade2_2_time_round1_20_minutes_later",
    ),
    7: ElementaryVisualTemplate(
        problem_text="1일 6시간과 26시간 중 더 긴 시간에 ○표 하세요.",
        expression="answer_text=1일 6시간에 ○표",
        topic="measurement",
        rule_id="grade2_2_time_round1_longer_duration",
    ),
    8: ElementaryVisualTemplate(
        problem_text="밤 10시 40분은 오전인지 오후인지 쓰세요.",
        expression="answer_text=오후",
        topic="measurement",
        rule_id="grade2_2_time_round1_pm_choice",
    ),
}


_GRADE2_TIME_2_2_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="1주일 6일과 15일 중 기간이 더 긴 쪽에 ○표 하세요.",
        expression="answer_text=15일에 ○표",
        topic="measurement",
        rule_id="grade2_2_time_round1_longer_days",
    ),
    2: ElementaryVisualTemplate(
        problem_text="8시 15분에 출발하여 8시 27분에 도착했습니다. 걸린 시간은 몇 분인지 구하세요.",
        expression="answer_text=12 분",
        topic="measurement",
        rule_id="grade2_2_time_round1_elapsed_minutes",
    ),
    3: ElementaryVisualTemplate(
        problem_text="3시 40분에 시작하여 5시에 끝냈습니다. 공부한 시간은 몇 시간 몇 분인지 구하세요.",
        expression="answer_text=1 시간 20 분",
        topic="measurement",
        rule_id="grade2_2_time_round1_elapsed_hours_minutes",
    ),
    4: ElementaryVisualTemplate(
        problem_text="시계의 짧은 바늘이 숫자 2에서 7까지 움직이는 동안 긴 바늘은 모두 몇 바퀴 도는지 구하세요.",
        expression="answer_text=5 바퀴",
        topic="measurement",
        rule_id="grade2_2_time_round1_hour_hand_two_to_seven",
    ),
    5: ElementaryVisualTemplate(
        problem_text="시계의 짧은 바늘이 한 바퀴를 돌면 몇 시간인지 구하세요.",
        expression="answer_text=12 시간",
        topic="measurement",
        rule_id="grade2_2_time_round1_hour_hand_one_turn",
    ),
    6: ElementaryVisualTemplate(
        problem_text="다음 중 잘못 나타낸 것을 고르세요.",
        expression="answer_text=④",
        topic="measurement",
        rule_id="grade2_2_time_round1_wrong_time_expression",
    ),
    7: ElementaryVisualTemplate(
        problem_text="오늘 오후 4시부터 내일 오후 4시까지는 몇 시간인지 구하세요.",
        expression="answer_text=24 시간",
        topic="measurement",
        rule_id="grade2_2_time_round1_one_day_hours",
    ),
    8: ElementaryVisualTemplate(
        problem_text="1주일 4일은 며칠인지 쓰세요.",
        expression="answer=11",
        topic="measurement",
        rule_id="grade2_2_time_round1_week_four_days",
    ),
    9: ElementaryVisualTemplate(
        problem_text="6월 7일이 목요일일 때 같은 해 6월의 셋째 토요일은 며칠인지 구하세요.",
        expression="answer_text=16 일",
        topic="measurement",
        rule_id="grade2_2_time_round1_third_saturday",
    ),
    10: ElementaryVisualTemplate(
        problem_text="7월 9일에서 16일 후는 무슨 요일인지 구하세요.",
        expression="answer_text=토요일",
        topic="measurement",
        rule_id="grade2_2_time_round1_calendar_after_16_days",
    ),
    11: ElementaryVisualTemplate(
        problem_text="4월, 5월, 6월 세 달 동안 하루도 빠짐없이 줄넘기를 했습니다. 줄넘기를 한 날은 모두 며칠인지 구하세요.",
        expression="answer_text=91 일",
        topic="measurement",
        rule_id="grade2_2_time_round1_three_month_days",
    ),
    12: ElementaryVisualTemplate(
        problem_text="4월 달력에서 이달의 셋째 토요일은 며칠인지 구하세요.",
        expression="answer_text=16 일",
        topic="measurement",
        rule_id="grade2_2_time_round1_april_third_saturday",
    ),
}


_GRADE2_TIME_2_2_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="시계를 보고 시각을 쓰세요.",
        expression="answer_text=12, 15",
        topic="measurement",
        rule_id="grade2_2_time_round2_read_clock",
    ),
    2: ElementaryVisualTemplate(
        problem_text="짧은 바늘이 7과 8 사이를 가리키고 긴바늘이 1을 가리키면 몇 시 몇 분인지 쓰세요.",
        expression="answer_text=7, 5",
        topic="measurement",
        rule_id="grade2_2_time_round2_hand_description",
    ),
    3: ElementaryVisualTemplate(
        problem_text="정아가 50분 동안 TV를 보고 난 뒤 시각이 9시 40분입니다. 시작한 시각을 구하세요.",
        expression="answer_text=8 시 50 분",
        topic="measurement",
        rule_id="grade2_2_time_round2_start_time_before_50min",
    ),
    4: ElementaryVisualTemplate(
        problem_text="시계의 긴바늘과 짧은바늘을 그려 6시 12분을 나타내세요.",
        expression="answer_text=6 시 12 분",
        topic="measurement",
        rule_id="grade2_2_time_round2_draw_6_12",
    ),
    5: ElementaryVisualTemplate(
        problem_text="거울에 비친 시계를 보고 이 시계가 나타내는 시각을 쓰세요.",
        expression="answer_text=10, 45, 11, 15",
        topic="measurement",
        rule_id="grade2_2_time_round2_mirror_clock",
    ),
    6: ElementaryVisualTemplate(
        problem_text="시계가 나타내는 시각에서 30분 후의 시각을 쓰세요.",
        expression="answer_text=3, 5",
        topic="measurement",
        rule_id="grade2_2_time_round2_30_minutes_later",
    ),
    7: ElementaryVisualTemplate(
        problem_text="40시간과 1일 11시간 중 더 긴 시간에 ○표 하세요.",
        expression="answer_text=40시간에 ○표",
        topic="measurement",
        rule_id="grade2_2_time_round2_longer_duration",
    ),
    8: ElementaryVisualTemplate(
        problem_text="아침 10시 10분은 오전인지 오후인지 쓰세요.",
        expression="answer_text=오전",
        topic="measurement",
        rule_id="grade2_2_time_round2_am_choice",
    ),
}


_GRADE2_TIME_2_2_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="20일과 2주일 5일 중 기간이 더 긴 쪽에 ○표 하세요.",
        expression="answer_text=20일에 ○표",
        topic="measurement",
        rule_id="grade2_2_time_round2_longer_days",
    ),
    2: ElementaryVisualTemplate(
        problem_text="3시 25분에서 6시 50분까지는 몇 분인지 구하세요.",
        expression="answer_text=205 분",
        topic="measurement",
        rule_id="grade2_2_time_round2_elapsed_minutes",
    ),
    3: ElementaryVisualTemplate(
        problem_text="2시 40분에 시작하여 4시 10분에 끝냈습니다. 걸린 시간은 몇 시간 몇 분인지 구하세요.",
        expression="answer_text=1 시간 30 분",
        topic="measurement",
        rule_id="grade2_2_time_round2_elapsed_hours_minutes",
    ),
    4: ElementaryVisualTemplate(
        problem_text="시계의 짧은 바늘이 숫자 6에서 10까지 움직이는 동안 긴 바늘은 모두 몇 바퀴 도는지 구하세요.",
        expression="answer_text=4 바퀴",
        topic="measurement",
        rule_id="grade2_2_time_round2_hour_hand_six_to_ten",
    ),
    5: ElementaryVisualTemplate(
        problem_text="시계의 짧은 바늘이 두 바퀴를 돌면 몇 시간인지 구하세요.",
        expression="answer_text=24 시간",
        topic="measurement",
        rule_id="grade2_2_time_round2_hour_hand_two_turns",
    ),
    6: ElementaryVisualTemplate(
        problem_text="다음 중 바르지 못한 것을 고르세요.",
        expression="answer_text=①",
        topic="measurement",
        rule_id="grade2_2_time_round2_wrong_time_expression",
    ),
    7: ElementaryVisualTemplate(
        problem_text="오전 6시에서 오후 6시가 되려면 몇 시간이 지나야 하는지 구하세요.",
        expression="answer_text=12 시간",
        topic="measurement",
        rule_id="grade2_2_time_round2_am_to_pm_hours",
    ),
    8: ElementaryVisualTemplate(
        problem_text="2주일 2일은 며칠인지 쓰세요.",
        expression="answer=16",
        topic="measurement",
        rule_id="grade2_2_time_round2_two_weeks_two_days",
    ),
    9: ElementaryVisualTemplate(
        problem_text="3월 2일이 화요일일 때 같은 해 3월의 넷째 금요일은 며칠인지 구하세요.",
        expression="answer_text=26 일",
        topic="measurement",
        rule_id="grade2_2_time_round2_fourth_friday",
    ),
    10: ElementaryVisualTemplate(
        problem_text="5월 13일에서 5일 전은 무슨 요일인지 구하세요.",
        expression="answer_text=일요일",
        topic="measurement",
        rule_id="grade2_2_time_round2_calendar_5_days_before",
    ),
    11: ElementaryVisualTemplate(
        problem_text="8월과 9월 두 달 동안 매일 수학 문제집을 풀었습니다. 문제집을 푼 날은 모두 며칠인지 구하세요.",
        expression="answer_text=61 일",
        topic="measurement",
        rule_id="grade2_2_time_round2_two_month_days",
    ),
    12: ElementaryVisualTemplate(
        problem_text="2월 달력에서 이달의 넷째 목요일은 며칠인지 구하세요.",
        expression="answer_text=23 일",
        topic="measurement",
        rule_id="grade2_2_time_round2_february_fourth_thursday",
    ),
}


_GRADE2_TIME_2_2_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="시계를 보고 시각을 쓰세요.",
        expression="answer_text=3, 45",
        topic="measurement",
        rule_id="grade2_2_time_round3_read_clock",
    ),
    2: ElementaryVisualTemplate(
        problem_text="짧은 바늘이 6과 7 사이를 가리키고 긴바늘이 9를 가리키면 몇 시 몇 분인지 쓰세요.",
        expression="answer_text=6, 45",
        topic="measurement",
        rule_id="grade2_2_time_round3_hand_description",
    ),
    3: ElementaryVisualTemplate(
        problem_text="윤석이가 40분 동안 숙제를 하고 난 뒤 시각이 1시 55분입니다. 시작한 시각을 구하세요.",
        expression="answer_text=1 시 15 분",
        topic="measurement",
        rule_id="grade2_2_time_round3_start_time_before_40min",
    ),
    4: ElementaryVisualTemplate(
        problem_text="시계의 긴바늘과 짧은바늘을 그려 9시 26분을 나타내세요.",
        expression="answer_text=9 시 26 분",
        topic="measurement",
        rule_id="grade2_2_time_round3_draw_9_26",
    ),
    5: ElementaryVisualTemplate(
        problem_text="거울에 비친 시계를 보고 이 시계가 나타내는 시각을 쓰세요.",
        expression="answer_text=4, 45, 5, 15",
        topic="measurement",
        rule_id="grade2_2_time_round3_mirror_clock",
    ),
    6: ElementaryVisualTemplate(
        problem_text="시계가 나타내는 시각에서 20분 전의 시각을 쓰세요.",
        expression="answer_text=3, 45",
        topic="measurement",
        rule_id="grade2_2_time_round3_20_minutes_before",
    ),
    7: ElementaryVisualTemplate(
        problem_text="2일 5시간과 50시간 중 더 긴 시간에 ○표 하세요.",
        expression="answer_text=2일 5시간에 ○표",
        topic="measurement",
        rule_id="grade2_2_time_round3_longer_duration",
    ),
    8: ElementaryVisualTemplate(
        problem_text="밤 11시 40분은 오전인지 오후인지 쓰세요.",
        expression="answer_text=오후",
        topic="measurement",
        rule_id="grade2_2_time_round3_pm_choice",
    ),
}


_GRADE2_TIME_2_2_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="3주일 3일과 25일 중 기간이 더 긴 쪽에 ○표 하세요.",
        expression="answer_text=25일에 ○표",
        topic="measurement",
        rule_id="grade2_2_time_round3_longer_days",
    ),
    2: ElementaryVisualTemplate(
        problem_text="4시 5분에 출발하여 4시 35분에 도착했습니다. 걸린 시간은 몇 분인지 구하세요.",
        expression="answer_text=30 분",
        topic="measurement",
        rule_id="grade2_2_time_round3_elapsed_minutes",
    ),
    3: ElementaryVisualTemplate(
        problem_text="2시 10분에 출발하여 3시 20분에 도착했습니다. 걸린 시간은 몇 시간 몇 분인지 구하세요.",
        expression="answer_text=1 시간 10 분",
        topic="measurement",
        rule_id="grade2_2_time_round3_elapsed_hours_minutes",
    ),
    4: ElementaryVisualTemplate(
        problem_text="시계의 짧은 바늘이 12에서 3까지 가는 동안 긴 바늘은 몇 바퀴를 도는지 구하세요.",
        expression="answer_text=3 바퀴",
        topic="measurement",
        rule_id="grade2_2_time_round3_hour_hand_twelve_to_three",
    ),
    5: ElementaryVisualTemplate(
        problem_text="시계의 짧은 바늘이 시계를 한 바퀴 돌면 긴 바늘은 몇 바퀴 도는지 구하세요.",
        expression="answer_text=12 바퀴",
        topic="measurement",
        rule_id="grade2_2_time_round3_hour_hand_one_turn_long_hand",
    ),
    6: ElementaryVisualTemplate(
        problem_text="다음 중 바르지 못한 것을 고르세요.",
        expression="answer_text=⑤",
        topic="measurement",
        rule_id="grade2_2_time_round3_wrong_time_expression",
    ),
    7: ElementaryVisualTemplate(
        problem_text="오전 3시에서 오후 3시가 되려면 몇 시간이 지나야 하는지 구하세요.",
        expression="answer_text=12 시간",
        topic="measurement",
        rule_id="grade2_2_time_round3_am_to_pm_hours",
    ),
    8: ElementaryVisualTemplate(
        problem_text="3주일 4일은 며칠인지 쓰세요.",
        expression="answer_text=25 일",
        topic="measurement",
        rule_id="grade2_2_time_round3_three_weeks_four_days",
    ),
    9: ElementaryVisualTemplate(
        problem_text="2월 4일이 수요일일 때 같은 해 2월의 셋째 목요일은 며칠인지 구하세요.",
        expression="answer_text=19 일",
        topic="measurement",
        rule_id="grade2_2_time_round3_third_thursday",
    ),
    10: ElementaryVisualTemplate(
        problem_text="2월 27일에서 9일 전은 무슨 요일인지 구하세요.",
        expression="answer_text=화요일",
        topic="measurement",
        rule_id="grade2_2_time_round3_calendar_9_days_before",
    ),
    11: ElementaryVisualTemplate(
        problem_text="9월과 10월 두 달 동안 매일 운동을 했습니다. 운동한 날은 모두 며칠인지 구하세요.",
        expression="answer_text=61 일",
        topic="measurement",
        rule_id="grade2_2_time_round3_two_month_days",
    ),
    12: ElementaryVisualTemplate(
        problem_text="11월 달력에서 이달의 셋째 금요일은 며칠인지 구하세요.",
        expression="answer_text=17 일",
        topic="measurement",
        rule_id="grade2_2_time_round3_november_third_friday",
    ),
}


_GRADE2_TABLE_GRAPH_2_2_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="10월 날씨 표에서 비가 온 날은 모두 며칠인지 구하세요.",
        expression="answer_text=8일",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_rainy_days_october",
    ),
    2: ElementaryVisualTemplate(
        problem_text="악기별 학생 수 표를 보고 그래프의 가로 한 칸이 한 명일 때 가로를 적어도 몇 칸으로 나누어야 하는지 구하세요.",
        expression="answer_text=6칸",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_graph_width_cells",
    ),
    3: ElementaryVisualTemplate(
        problem_text="학용품 그림을 보고 학용품의 수를 표로 나타내세요.",
        expression="answer_text=연필 3, 지우개 3, 가위 2, 공책 2, 합계 10",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_stationery_table",
    ),
    4: ElementaryVisualTemplate(
        problem_text="학용품의 개수는 모두 몇 개인지 구하세요.",
        expression="answer_text=10개",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_stationery_total",
    ),
    5: ElementaryVisualTemplate(
        problem_text="지우개와 가위의 차는 몇 개인지 구하세요.",
        expression="answer=1",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_eraser_scissors_difference",
    ),
    6: ElementaryVisualTemplate(
        problem_text="6월 날씨 표에서 비가 내린 날은 모두 며칠인지 구하세요.",
        expression="answer_text=13일",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_june_rainy_days",
    ),
    7: ElementaryVisualTemplate(
        problem_text="6월 날씨 중 가장 적은 날씨와 며칠인지 쓰세요.",
        expression="answer_text=맑음, 7일",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_least_weather",
    ),
}


_GRADE2_TABLE_GRAPH_2_2_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="동물 그림을 보고 좋아하는 동물에 ○표 하세요.",
        expression="answer_text=에 ○표",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_favorite_animal_mark",
    ),
    2: ElementaryVisualTemplate(
        problem_text="코끼리를 좋아하는 학생의 이름을 모두 쓰세요.",
        expression="answer_text=서연, 태민",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_elephant_names",
    ),
    3: ElementaryVisualTemplate(
        problem_text="좋아하는 동물 자료를 보고 표로 나타내세요.",
        expression="answer_text=사자 3명, 코끼리 2명, 기린 3명, 판다 4명, 합계 12명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_animal_table",
    ),
    4: ElementaryVisualTemplate(
        problem_text="기린을 좋아하는 학생은 몇 명인지 구하세요.",
        expression="answer_text=3명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_giraffe_count",
    ),
    5: ElementaryVisualTemplate(
        problem_text="모둠 학생은 모두 몇 명인지 구하세요.",
        expression="answer_text=12명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_total_students",
    ),
    6: ElementaryVisualTemplate(
        problem_text="주사위 눈의 횟수를 표로 나타내세요.",
        expression="answer_text=1: 2번, 2: 1번, 3: 3번, 4: 1번, 5: 2번, 6: 3번, 합계 12번",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_dice_table",
    ),
    7: ElementaryVisualTemplate(
        problem_text="표를 보고 ○를 이용하여 그래프로 나타내세요.",
        expression="answer_text=주사위 눈 1:2, 2:1, 3:3, 4:1, 5:2, 6:3",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_dice_graph",
    ),
    8: ElementaryVisualTemplate(
        problem_text="위 그래프의 가로에 나타낸 것은 무엇일까요?",
        expression="answer_text=주사위의 눈",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_graph_horizontal_axis",
    ),
}


_GRADE2_TABLE_GRAPH_2_2_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="자료를 보고 학생들이 맞힌 문제 수를 세어 표로 나타내세요.",
        expression="answer_text=준혁 2개, 가영 3개, 승민 2개, 수진 4개",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_page2_student_correct_table",
    ),
    2: ElementaryVisualTemplate(
        problem_text="자료를 보고 문제를 맞힌 학생 수를 세어 표로 나타내세요.",
        expression="answer_text=1번 2명, 2번 3명, 3번 2명, 4번 4명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_page2_problem_correct_table",
    ),
    3: ElementaryVisualTemplate(
        problem_text="표를 보고 ○를 이용하여 악기별 학생 수 그래프로 나타내세요.",
        expression="answer_text=피아노 6명, 기타 2명, 바이올린 5명, 플루트 4명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_page2_instrument_graph",
    ),
    4: ElementaryVisualTemplate(
        problem_text="현진이네 반 학생은 모두 몇 명인지 구하세요.",
        expression="answer_text=17명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_page2_total_students",
    ),
    5: ElementaryVisualTemplate(
        problem_text="가장 많이 배우고 있는 악기는 무엇인지 구하세요.",
        expression="answer_text=피아노",
        topic="statistics",
        rule_id="grade2_2_table_graph_round1_page2_most_instrument",
    ),
}


_GRADE2_TABLE_GRAPH_2_2_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="선우가 좋아하는 꽃에 ○표 하세요.",
        expression="answer_text=데이지에 ○표",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_sunwoo_flower_mark",
    ),
    2: ElementaryVisualTemplate(
        problem_text="해바라기를 좋아하는 학생의 이름을 모두 쓰세요.",
        expression="answer_text=준호, 윤호, 민서",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_sunflower_names",
    ),
    3: ElementaryVisualTemplate(
        problem_text="서아네 모둠 학생은 모두 몇 명인지 구하세요.",
        expression="answer_text=12명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_page1_total_students_split",
    ),
    4: ElementaryVisualTemplate(
        problem_text="장미를 좋아하는 학생은 몇 명인지 구하세요.",
        expression="answer_text=4명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_rose_count",
    ),
    5: ElementaryVisualTemplate(
        problem_text="서아네 모둠 학생은 모두 몇 명인지 구하세요.",
        expression="answer_text=12명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_total_students",
    ),
    8: ElementaryVisualTemplate(
        problem_text="위 그래프의 가로에 나타낸 것은 무엇일까요?",
        expression="answer_text=책",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_graph_horizontal_axis",
    ),
}


_GRADE2_TABLE_GRAPH_2_2_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="단추를 색깔별로 세어 표로 나타내세요.",
        expression="answer_text=빨강 6개, 노랑 5개, 초록 2개, 파랑 5개, 합계 18개",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_page2_button_color_table",
    ),
    2: ElementaryVisualTemplate(
        problem_text="위 그래프의 가로에 나타낸 것을 구하세요.",
        expression="answer_text=3",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_page2_graph_axis_1",
    ),
    3: ElementaryVisualTemplate(
        problem_text="위 그래프의 가로에 나타낸 것을 구하세요.",
        expression="answer_text=3",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_page2_graph_axis_2",
    ),
    4: ElementaryVisualTemplate(
        problem_text="키위는 몇 개를 먹었는지 구하세요.",
        expression="answer_text=4개",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_page2_kiwi_count",
    ),
    5: ElementaryVisualTemplate(
        problem_text="튤립을 좋아하는 학생과 백합을 좋아하는 학생은 모두 몇 명인지 구하세요.",
        expression="answer_text=10명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_page2_flower_total_1",
    ),
    6: ElementaryVisualTemplate(
        problem_text="튤립을 좋아하는 학생과 백합을 좋아하는 학생은 모두 몇 명인지 구하세요.",
        expression="answer_text=10명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_page2_flower_total_2",
    ),
}


_GRADE2_TABLE_GRAPH_2_2_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="표를 보고 ○를 이용하여 취미별 학생 수 그래프로 나타내세요.",
        expression="answer_text=독서 3명, 게임 4명, 운동 6명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_page3_hobby_graph",
    ),
    2: ElementaryVisualTemplate(
        problem_text="가장 많이 좋아하는 취미는 무엇인지 구하세요.",
        expression="answer_text=운동",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_page3_most_hobby",
    ),
    3: ElementaryVisualTemplate(
        problem_text="간식별 학생 수 그래프의 가로를 적어도 몇 칸으로 나누어야 하는지 구하세요.",
        expression="answer_text=8칸",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_page3_snack_graph_width_1",
    ),
    4: ElementaryVisualTemplate(
        problem_text="간식별 학생 수 그래프의 가로를 적어도 몇 칸으로 나누어야 하는지 구하세요.",
        expression="answer_text=8칸",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_page3_snack_graph_width_2",
    ),
    5: ElementaryVisualTemplate(
        problem_text="단추를 색깔별로 세어 표로 나타내세요.",
        expression="answer_text=빨강 6개, 노랑 5개, 초록 2개, 파랑 5개, 합계 18개",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_page3_button_color_table",
    ),
    6: ElementaryVisualTemplate(
        problem_text="빨간색 단추의 개수는 모두 몇 개인지 구하세요.",
        expression="answer_text=6개",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_page3_red_button_count",
    ),
    7: ElementaryVisualTemplate(
        problem_text="키위는 몇 개를 먹었는지 구하세요.",
        expression="answer_text=4개",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_page3_kiwi_count",
    ),
    8: ElementaryVisualTemplate(
        problem_text="가장 적게 먹은 과일은 무엇이고 몇 개를 먹었는지 쓰세요.",
        expression="answer_text=감, 1개",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_page3_least_fruit",
    ),
    9: ElementaryVisualTemplate(
        problem_text="가장 적게 먹은 과일은 무엇이고 몇 개를 먹었는지 쓰세요.",
        expression="answer_text=감, 1개",
        topic="statistics",
        rule_id="grade2_2_table_graph_round2_page3_least_fruit_split",
    ),
}


_GRADE2_TABLE_GRAPH_2_2_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="윤희가 좋아하는 곤충에 ○표 하세요.",
        expression="answer_text=에 ○표",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_yunhee_insect_mark",
    ),
    2: ElementaryVisualTemplate(
        problem_text="잠자리를 좋아하는 학생의 이름을 모두 쓰세요.",
        expression="answer_text=서연, 선아, 시연",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_dragonfly_names",
    ),
    3: ElementaryVisualTemplate(
        problem_text="자료를 보고 표로 나타내세요.",
        expression="answer_text=2, 3, 1, 2, 8",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_insect_table",
    ),
    4: ElementaryVisualTemplate(
        problem_text="무당벌레를 좋아하는 학생은 몇 명인지 구하세요.",
        expression="answer_text=2명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_ladybug_count",
    ),
    5: ElementaryVisualTemplate(
        problem_text="준호네 모둠 학생은 모두 몇 명인지 구하세요.",
        expression="answer_text=8명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_total_students",
    ),
    6: ElementaryVisualTemplate(
        problem_text="혈액형을 조사한 자료를 보고 표로 나타내세요.",
        expression="answer_text=A형 3명, B형 3명, AB형 2명, O형 1명, 합계 9명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_blood_type_table",
    ),
    7: ElementaryVisualTemplate(
        problem_text="위 표를 보고 ○를 이용하여 그래프로 나타내세요.",
        expression="answer_text=A형 3명, B형 3명, AB형 2명, O형 1명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_blood_type_graph",
    ),
    8: ElementaryVisualTemplate(
        problem_text="위 그래프의 가로에 나타낸 것은 무엇일까요?",
        expression="answer_text=혈액형",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_graph_horizontal_axis",
    ),
}


_GRADE2_TABLE_GRAPH_2_2_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="자료를 보고 학생들이 맞힌 문제 수를 세어 표로 나타내세요.",
        expression="answer_text=12명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_page2_student_correct_table",
    ),
    2: ElementaryVisualTemplate(
        problem_text="자료를 보고 문제를 맞힌 학생 수를 세어 표로 나타내세요.",
        expression="answer_text=1, 3, 3, 4, 2",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_page2_problem_correct_table",
    ),
    3: ElementaryVisualTemplate(
        problem_text="표를 보고 ○를 이용하여 나라별 학생 수 그래프로 나타내세요.",
        expression="answer_text=중국 3명, 미국 3명, 호주 2명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_page2_country_graph",
    ),
    4: ElementaryVisualTemplate(
        problem_text="진우네 모둠 학생은 모두 몇 명인지 구하세요.",
        expression="answer_text=8명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_page2_total_students",
    ),
    5: ElementaryVisualTemplate(
        problem_text="수학을 좋아하는 학생은 몇 명인지 구하세요.",
        expression="answer_text=17명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_page2_math_students_1",
    ),
    6: ElementaryVisualTemplate(
        problem_text="수학을 좋아하는 학생은 몇 명인지 구하세요.",
        expression="answer_text=17명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_page2_math_students_2",
    ),
}


_GRADE2_TABLE_GRAPH_2_2_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="장난감별 학생 수 표를 보고 그래프의 가로 한 칸이 한 명일 때 가로를 적어도 몇 칸으로 나누어야 하는지 구하세요.",
        expression="answer_text=6칸",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_graph_width_cells",
    ),
    2: ElementaryVisualTemplate(
        problem_text="과일 그림을 보고 과일의 종류를 세어 표로 나타내세요.",
        expression="answer_text=딸기 4, 귤 3, 바나나 3, 멜론 2, 합계 12",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_fruit_table",
    ),
    3: ElementaryVisualTemplate(
        problem_text="딸기의 개수는 모두 몇 개인지 구하세요.",
        expression="answer_text=4개",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_strawberry_total",
    ),
    4: ElementaryVisualTemplate(
        problem_text="과일 전체의 개수는 모두 몇 개인지 구하세요.",
        expression="answer_text=12개",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_fruit_total",
    ),
    5: ElementaryVisualTemplate(
        problem_text="태권도는 모두 몇 명이 배우고 있는지 구하세요.",
        expression="answer_text=12명",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_taekwondo_students",
    ),
    6: ElementaryVisualTemplate(
        problem_text="가장 많이 배우고 있는 운동과 가장 적게 배우고 있는 운동의 차를 구하세요.",
        expression="answer=9",
        topic="statistics",
        rule_id="grade2_2_table_graph_round3_sports_difference",
    ),
}


_GRADE2_CLASSIFICATION_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    5: ElementaryVisualTemplate(
        problem_text="칠판에 붙어 있는 자석을 보고 알맞은 분류 기준을 쓰세요.",
        expression="answer_text=알파벳과 숫자",
        topic="statistics",
        rule_id="grade2_classification_round1_magnets_letters_numbers",
    ),
    6: ElementaryVisualTemplate(
        problem_text="학급 문고의 책을 종류에 따라 분류했습니다. 어떤 종류의 책을 더 사면 좋을까요?",
        expression="answer_text=사회, 과학",
        topic="statistics",
        rule_id="grade2_classification_round1_book_types_to_buy",
    ),
}


_GRADE2_CLASSIFICATION_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="공을 사용하는 운동과 사용하지 않는 운동을 차례대로 고르세요.",
        expression="answer_text=③ 축구, 수영",
        topic="statistics",
        rule_id="grade2_classification_round1_page2_ball_sports",
    ),
    2: ElementaryVisualTemplate(
        problem_text="주사위를 던졌을 때 나온 눈의 수에 따라 몇 가지로 분류할 수 있는지 구하세요.",
        expression="answer=6",
        topic="statistics",
        rule_id="grade2_classification_round1_page2_dice_categories",
    ),
    3: ElementaryVisualTemplate(
        problem_text="두 주사위 눈의 수의 합이 6이 되는 것을 모두 찾아 기호를 쓰세요.",
        expression="answer_text=가, 라",
        topic="statistics",
        rule_id="grade2_classification_round1_page2_dice_sum_six",
    ),
    4: ElementaryVisualTemplate(
        problem_text="사야 하는 재료를 보고 과일 코너에서 사야 하는 것을 분류하세요.",
        expression="answer_text=바나나, 오렌지, 사과, 딸기",
        topic="statistics",
        rule_id="grade2_classification_round1_page2_fruits_to_buy",
    ),
    5: ElementaryVisualTemplate(
        problem_text="도형을 보고 알맞은 수를 써넣으세요.",
        expression="answer_text=삼각형 3개, 파란색이면서 삼각형 2개",
        topic="statistics",
        rule_id="grade2_classification_round1_page2_shape_counts",
    ),
    6: ElementaryVisualTemplate(
        problem_text="색깔에 따라 학생 수를 세어 표에 써넣으세요.",
        expression="answer_text=노란색 3명, 파란색 4명, 보라색 2명, 빨간색 3명",
        topic="statistics",
        rule_id="grade2_classification_round1_page2_color_counts",
    ),
    7: ElementaryVisualTemplate(
        problem_text="장래 희망을 조사한 자료에서 가장 많이 희망하는 내용을 쓰세요.",
        expression="answer_text=연예인, 5명",
        topic="statistics",
        rule_id="grade2_classification_round1_page2_future_job_most",
    ),
}


_GRADE2_CLASSIFICATION_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림을 보고 알맞은 수를 써넣으세요.",
        expression="answer_text=안경 쓴 학생 5명, 안경 쓴 학생 중 모자 쓴 학생 2명",
        topic="statistics",
        rule_id="grade2_classification_round1_page3_students_glasses_hats",
    ),
    2: ElementaryVisualTemplate(
        problem_text="책 20권을 종류별로 분류했습니다. 빈 곳에 알맞은 수를 써넣으세요.",
        expression="answer_text=과학책 6권",
        topic="statistics",
        rule_id="grade2_classification_round1_page3_science_books",
    ),
    3: ElementaryVisualTemplate(
        problem_text="동물을 다리가 2개인 동물과 4개인 동물로 분류하여 세어 보세요.",
        expression="answer_text=다리가 2개인 동물 5마리, 다리가 4개인 동물 7마리",
        topic="statistics",
        rule_id="grade2_classification_round1_page3_animal_legs",
    ),
    4: ElementaryVisualTemplate(
        problem_text="식당에서 오늘 낮에 팔린 음식을 조사했습니다. 가장 많이 팔린 음식을 구하세요.",
        expression="answer_text=라면",
        topic="statistics",
        rule_id="grade2_classification_round1_page3_most_sold_food",
    ),
    5: ElementaryVisualTemplate(
        problem_text="좋아하는 과일을 분류했을 때 수가 같은 것은 무엇과 무엇인지 쓰세요.",
        expression="answer_text=포도와 딸기, 바나나와 멜론",
        topic="statistics",
        rule_id="grade2_classification_round1_page3_same_fruit_counts",
    ),
    6: ElementaryVisualTemplate(
        problem_text="좋아하는 운동을 조사했습니다. 가장 많은 학생들이 좋아하는 운동을 구하세요.",
        expression="answer_text=축구",
        topic="statistics",
        rule_id="grade2_classification_round1_page3_favorite_sport",
    ),
    7: ElementaryVisualTemplate(
        problem_text="학용품을 종류에 따라 분류했습니다. 학용품 수가 종류별로 같으려면 무엇을 몇 개 더 사야 하는지 쓰세요.",
        expression="answer_text=색연필 8개",
        topic="statistics",
        rule_id="grade2_classification_round1_page3_stationery_equal_count",
    ),
}


_GRADE2_CLASSIFICATION_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="분류 기준으로 알맞은 것에 ○표 하세요.",
        expression="answer_text=모양",
        topic="statistics",
        rule_id="grade2_classification_round2_page1_button_criterion",
    ),
    2: ElementaryVisualTemplate(
        problem_text="구멍이 2개인 단추는 모두 몇 개인지 구하세요.",
        expression="answer_text=2개",
        topic="statistics",
        rule_id="grade2_classification_round2_page1_two_holes",
    ),
    3: ElementaryVisualTemplate(
        problem_text="구멍이 3개인 단추는 모두 몇 개인지 구하세요.",
        expression="answer_text=3개",
        topic="statistics",
        rule_id="grade2_classification_round2_page1_three_holes",
    ),
    4: ElementaryVisualTemplate(
        problem_text="구멍의 수에 따라 분류하고 그 수를 세어 보세요.",
        expression="answer_text=구멍 2개: 2개, 구멍 4개: 5개",
        topic="statistics",
        rule_id="grade2_classification_round2_page1_hole_table",
    ),
    5: ElementaryVisualTemplate(
        problem_text="모양에 따라 분류하여 번호를 써 보세요.",
        expression="answer_text=삼각형: 1, 4, 8 / 사각형: 3, 6, 7 / 원: 2, 5, 10 / 별: 9",
        topic="statistics",
        rule_id="grade2_classification_round2_page1_shape_numbers",
    ),
    6: ElementaryVisualTemplate(
        problem_text="모양에 따라 분류했을 때 가장 많은 모양을 구하세요.",
        expression="answer_text=사각형",
        topic="statistics",
        rule_id="grade2_classification_round2_page1_most_shape",
    ),
    7: ElementaryVisualTemplate(
        problem_text="곡선으로 되어 있는 모양은 모두 몇 개인지 구하세요.",
        expression="answer_text=3개",
        topic="statistics",
        rule_id="grade2_classification_round2_page1_curved_shapes",
    ),
}


_GRADE2_CLASSIFICATION_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="물건을 분류 기준에 따라 분류하여 번호를 써 보세요.",
        expression="answer_text=색깔/모양에 따라 분류",
        topic="statistics",
        rule_id="grade2_classification_round2_page2_object_classification",
    ),
    2: ElementaryVisualTemplate(
        problem_text="문자를 종류에 따라 분류하세요.",
        expression="answer_text=한글: ㅇ, ㄱ / 숫자: 5, 6, 7 / 영어: A, B, C",
        topic="statistics",
        rule_id="grade2_classification_round2_page2_letters_numbers_english",
    ),
    3: ElementaryVisualTemplate(
        problem_text="분류한 문자의 개수가 다른 하나를 고르세요.",
        expression="answer_text=한글",
        topic="statistics",
        rule_id="grade2_classification_round2_page2_different_count",
    ),
    4: ElementaryVisualTemplate(
        problem_text="동물을 다리가 있는 것과 없는 것으로 분류하세요.",
        expression="answer_text=다리가 있는 것: 타조, 악어, 펭귄, 고양이 / 다리가 없는 것: 뱀, 달팽이, 돌고래",
        topic="statistics",
        rule_id="grade2_classification_round2_page2_animals_legs",
    ),
    5: ElementaryVisualTemplate(
        problem_text="책꽂이를 표와 같이 정리할 때 위인전은 몇째 칸에 분류해야 하는지 구하세요.",
        expression="answer_text=세째 칸",
        topic="statistics",
        rule_id="grade2_classification_round2_page2_book_shelf",
    ),
    6: ElementaryVisualTemplate(
        problem_text="좋아하는 음식을 조사했습니다. 가장 많이 좋아하는 음식을 구하세요.",
        expression="answer_text=짜장면",
        topic="statistics",
        rule_id="grade2_classification_round2_page2_favorite_food",
    ),
}


_GRADE2_CLASSIFICATION_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="학생들이 좋아하는 우유를 조사했습니다. 맛에 따라 분류하고 개수를 세세요.",
        expression="answer_text=초코맛 3개, 딸기맛 4개, 바나나맛 3개",
        topic="statistics",
        rule_id="grade2_classification_round2_page3_milk_counts",
    ),
    2: ElementaryVisualTemplate(
        problem_text="학생들이 가장 좋아하는 우유는 무슨 맛인지 쓰세요.",
        expression="answer_text=딸기맛",
        topic="statistics",
        rule_id="grade2_classification_round2_page3_favorite_milk",
    ),
    3: ElementaryVisualTemplate(
        problem_text="장래 희망을 조사했습니다. 연예인과 선생님 중 어느 것이 몇 명 더 많습니까?",
        expression="answer_text=연예인, 2명",
        topic="statistics",
        rule_id="grade2_classification_round2_page3_jobs_difference",
    ),
    4: ElementaryVisualTemplate(
        problem_text="빵 30개를 종류별로 분류했습니다. 빈 곳에 알맞은 수를 써넣으세요.",
        expression="answer_text=소세지빵 11개",
        topic="statistics",
        rule_id="grade2_classification_round2_page3_bread_count",
    ),
    5: ElementaryVisualTemplate(
        problem_text="같은 수로 우유를 준비하려고 합니다. 어느 맛 우유를 몇 개 더 준비해야 하는지 구하세요.",
        expression="answer_text=초코맛 1개, 바나나맛 1개",
        topic="statistics",
        rule_id="grade2_classification_round2_page3_more_milk",
    ),
    6: ElementaryVisualTemplate(
        problem_text="보기의 동물을 활동하는 곳에 따라 분류하세요.",
        expression="answer_text=땅: 참새, 개, 토끼, 사자 / 물속: 상어, 돌고래, 잉어 / 하늘: 호랑이 없음, 녹대 없음",
        topic="statistics",
        rule_id="grade2_classification_round2_page3_animal_habitat",
    ),
    7: ElementaryVisualTemplate(
        problem_text="분류한 개수가 가장 많은 것과 가장 적은 것의 차를 구하세요.",
        expression="answer=3",
        topic="statistics",
        rule_id="grade2_classification_round2_page3_count_difference",
    ),
}


_GRADE2_CLASSIFICATION_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="분류 기준으로 알맞은 것에 ○표 하세요.",
        expression="answer_text=모양",
        topic="statistics",
        rule_id="grade2_classification_round3_page1_button_criterion",
    ),
    2: ElementaryVisualTemplate(
        problem_text="구멍이 3개인 단추는 모두 몇 개인지 구하세요.",
        expression="answer_text=3개",
        topic="statistics",
        rule_id="grade2_classification_round3_page1_three_holes",
    ),
    3: ElementaryVisualTemplate(
        problem_text="구멍이 4개인 단추는 모두 몇 개인지 구하세요.",
        expression="answer_text=5개",
        topic="statistics",
        rule_id="grade2_classification_round3_page1_four_holes",
    ),
    4: ElementaryVisualTemplate(
        problem_text="구멍의 수에 따라 분류하고 그 수를 세어 보세요.",
        expression="answer_text=구멍 2개: 2개, 구멍 4개: 5개",
        topic="statistics",
        rule_id="grade2_classification_round3_page1_hole_table",
    ),
    5: ElementaryVisualTemplate(
        problem_text="색깔에 따라 분류하여 번호를 써 보세요.",
        expression="answer_text=빨간색: 3, 4, 6, 9 / 초록색: 2, 10 / 파란색: 1, 5, 7, 8",
        topic="statistics",
        rule_id="grade2_classification_round3_page1_color_numbers",
    ),
    6: ElementaryVisualTemplate(
        problem_text="색깔에 따라 분류했을 때 가장 적은 색깔을 구하세요.",
        expression="answer_text=초록색",
        topic="statistics",
        rule_id="grade2_classification_round3_page1_least_color",
    ),
    7: ElementaryVisualTemplate(
        problem_text="사각형이면서 파란색인 붙임 딱지는 몇 개인지 구하세요.",
        expression="answer_text=2개",
        topic="statistics",
        rule_id="grade2_classification_round3_page1_blue_squares",
    ),
}


_GRADE2_CLASSIFICATION_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="인형을 모양에 따라 분류하려고 합니다. 어떻게 분류할 수 있는지 바르게 쓴 것에 ○표 하세요.",
        expression="answer_text=모양에 따라 분류",
        topic="statistics",
        rule_id="grade2_classification_round3_page2_doll_shapes",
    ),
    2: ElementaryVisualTemplate(
        problem_text="문자를 종류에 따라 분류하세요.",
        expression="answer_text=한글, 숫자, 영어로 분류",
        topic="statistics",
        rule_id="grade2_classification_round3_page2_letters_numbers_english",
    ),
    3: ElementaryVisualTemplate(
        problem_text="분류한 문자의 개수가 가장 많은 것은 무엇인지 구하세요.",
        expression="answer_text=한글",
        topic="statistics",
        rule_id="grade2_classification_round3_page2_most_letters",
    ),
    4: ElementaryVisualTemplate(
        problem_text="동물을 먹이가 풀인 것과 고기인 것으로 분류하세요.",
        expression="answer_text=먹이가 풀인 것: 소, 양, 염소, 기린 / 먹이가 고기인 것: 호랑이, 사자, 하이에나",
        topic="statistics",
        rule_id="grade2_classification_round3_page2_animal_food",
    ),
    5: ElementaryVisualTemplate(
        problem_text="서랍장을 표와 같이 정리할 때 윗옷은 몇째 칸에 분류해야 하는지 구하세요.",
        expression="answer_text=둘째 칸",
        topic="statistics",
        rule_id="grade2_classification_round3_page2_clothes_shelf",
    ),
    6: ElementaryVisualTemplate(
        problem_text="좋아하는 곤충을 조사했습니다. 가장 많이 좋아하는 곤충을 구하세요.",
        expression="answer_text=잠자리",
        topic="statistics",
        rule_id="grade2_classification_round3_page2_favorite_insect",
    ),
}


_GRADE2_CLASSIFICATION_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="채소를 색깔에 따라 분류하고 각 개수를 세어 보세요.",
        expression="answer_text=초록색 5개, 빨간색 2개, 보라색 1개",
        topic="statistics",
        rule_id="grade2_classification_round3_page3_vegetable_colors",
    ),
    2: ElementaryVisualTemplate(
        problem_text="가장 많은 색깔은 무엇인지 쓰세요.",
        expression="answer_text=초록색",
        topic="statistics",
        rule_id="grade2_classification_round3_page3_most_color",
    ),
    3: ElementaryVisualTemplate(
        problem_text="승용차와 트럭 중에서 어느 것이 몇 대 더 많은지 쓰세요.",
        expression="answer_text=승용차, 3대",
        topic="statistics",
        rule_id="grade2_classification_round3_page3_vehicle_difference",
    ),
    4: ElementaryVisualTemplate(
        problem_text="학용품 20개를 종류별로 분류했습니다. 빈 곳에 알맞은 수를 써넣으세요.",
        expression="answer_text=지우개 4개",
        topic="statistics",
        rule_id="grade2_classification_round3_page3_erasers",
    ),
    5: ElementaryVisualTemplate(
        problem_text="주스를 준비하려고 합니다. 어느 주스를 몇 개 더 준비하면 좋을까요?",
        expression="answer_text=오렌지 주스 4개",
        topic="statistics",
        rule_id="grade2_classification_round3_page3_juice_more",
    ),
    6: ElementaryVisualTemplate(
        problem_text="보기를 채소와 과일로 분류하세요.",
        expression="answer_text=채소: 파프리카, 오이 / 과일: 사과, 딸기, 귤, 감, 배",
        topic="statistics",
        rule_id="grade2_classification_round3_page3_vegetables_fruits",
    ),
    7: ElementaryVisualTemplate(
        problem_text="분류한 개수가 어느 것이 몇 개 더 많은지 구하세요.",
        expression="answer_text=과일, 3개",
        topic="statistics",
        rule_id="grade2_classification_round3_page3_fruit_difference",
    ),
}


_GRADE2_RULES_2_2_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="덧셈표의 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=3, 4, 2, 5",
        topic="pattern",
        rule_id="grade2_2_rules_round1_addition_table_blanks",
    ),
    2: ElementaryVisualTemplate(
        problem_text="빗금 친 수에는 아래쪽으로 내려갈수록 몇씩 커지는 규칙이 있을까요?",
        expression="answer=1",
        topic="pattern",
        rule_id="grade2_2_rules_round1_shaded_down_step",
    ),
    3: ElementaryVisualTemplate(
        problem_text="점선에 놓인 수에는 ↘ 방향으로 갈수록 몇씩 커지는 규칙이 있을까요?",
        expression="answer=2",
        topic="pattern",
        rule_id="grade2_2_rules_round1_diagonal_step",
    ),
    4: ElementaryVisualTemplate(
        problem_text="곱셈표의 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=4, 2, 15, 12",
        topic="pattern",
        rule_id="grade2_2_rules_round1_multiplication_table_blanks",
    ),
    5: ElementaryVisualTemplate(
        problem_text="빗금 친 수의 규칙을 찾아 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=5",
        topic="pattern",
        rule_id="grade2_2_rules_round1_shaded_right_step",
    ),
    6: ElementaryVisualTemplate(
        problem_text="곱셈표를 점선을 따라 접으면 만나는 수들은 서로 같습니까, 다릅니까?",
        expression="answer_text=같습니다에 ○표",
        topic="pattern",
        rule_id="grade2_2_rules_round1_multiplication_symmetry",
    ),
}


_GRADE2_RULES_2_2_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="곱셈표를 선을 따라 접었을 때 만나는 수가 서로 같도록 선을 그으세요.",
        expression="answer_text=서로 같은 수끼리 선 연결",
        topic="pattern",
        rule_id="grade2_2_rules_round1_page2_multiplication_fold_line",
    ),
    2: ElementaryVisualTemplate(
        problem_text="덧셈표에서 규칙을 찾아 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=13, 12, 13",
        topic="pattern",
        rule_id="grade2_2_rules_round1_page2_addition_table_blanks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="곱셈표에서 규칙을 찾아 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=24, 20, 25",
        topic="pattern",
        rule_id="grade2_2_rules_round1_page2_multiplication_table_blanks",
    ),
    4: ElementaryVisualTemplate(
        problem_text="규칙을 찾아 알맞은 모양을 그리고 색칠하세요.",
        expression="answer_text=초록색 원",
        topic="pattern",
        rule_id="grade2_2_rules_round1_page2_next_shape",
    ),
    5: ElementaryVisualTemplate(
        problem_text="규칙을 찾아 다음에 올 동물에 ○표 하세요.",
        expression="answer_text=곰에 ○표",
        topic="pattern",
        rule_id="grade2_2_rules_round1_page2_next_animal",
    ),
    6: ElementaryVisualTemplate(
        problem_text="규칙을 찾아 반복되는 모양을 그리고 색칠하세요.",
        expression="answer_text=파랑, 노랑, 빨강 반복",
        topic="pattern",
        rule_id="grade2_2_rules_round1_page2_repeating_color_pattern",
    ),
    7: ElementaryVisualTemplate(
        problem_text="그림을 보고 규칙을 찾아 모양을 수로 바꾸어 나타내세요.",
        expression="answer_text=1 3 2 2 1 3 2 2 1 3 2 2 1 3 2 2 1 3 2 2 1",
        topic="pattern",
        rule_id="grade2_2_rules_round1_page2_shape_number_pattern",
    ),
}


_GRADE2_RULES_2_2_ROUND1_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="사각형 안에 점을 규칙에 맞게 그리세요.",
        expression="answer_text=왼쪽 아래에 점",
        topic="pattern",
        rule_id="grade2_2_rules_round1_page3_dot_pattern",
    ),
    2: ElementaryVisualTemplate(
        problem_text="규칙에 따라 쌓기나무를 쌓았습니다. 다음에 이어질 모양에 쌓을 쌓기나무는 모두 몇 개인지 구하세요.",
        expression="answer_text=7개",
        topic="pattern",
        rule_id="grade2_2_rules_round1_page3_stacking_blocks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="달력에서 규칙을 찾아 빨간색 선에 놓인 수가 몇씩 커지는지 구하세요.",
        expression="answer_text=6씩",
        topic="pattern",
        rule_id="grade2_2_rules_round1_page3_calendar_diagonal_step",
    ),
    4: ElementaryVisualTemplate(
        problem_text="12월 달력에서 일요일 날짜를 모두 쓰세요.",
        expression="answer_text=5, 12, 19, 26일",
        topic="pattern",
        rule_id="grade2_2_rules_round1_page3_december_sundays",
    ),
    5: ElementaryVisualTemplate(
        problem_text="시계의 규칙을 찾아 마지막 시계에 시곗바늘을 알맞게 그리세요.",
        expression="answer_text=2시 30분",
        topic="pattern",
        rule_id="grade2_2_rules_round1_page3_clock_pattern",
    ),
    6: ElementaryVisualTemplate(
        problem_text="의자 번호의 규칙을 찾아 빈칸에 쓰여질 수의 합을 구하세요.",
        expression="answer_text=30",
        topic="pattern",
        rule_id="grade2_2_rules_round1_page3_chair_number_sum",
    ),
    7: ElementaryVisualTemplate(
        problem_text="승강기 숫자판에서 위쪽으로 갈수록 커지는 수와 ↙ 방향으로 갈수록 작아지는 수를 쓰세요.",
        expression="answer_text=3, 4",
        topic="pattern",
        rule_id="grade2_2_rules_round1_elevator_pattern",
    ),
}


_GRADE2_RULES_2_2_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="덧셈표의 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=8, 4, 4, 10, 16",
        topic="pattern",
        rule_id="grade2_2_rules_round2_addition_table_blanks",
    ),
    2: ElementaryVisualTemplate(
        problem_text="빗금 친 수에는 아래쪽으로 내려갈수록 몇씩 커지는 규칙이 있을까요?",
        expression="answer=2",
        topic="pattern",
        rule_id="grade2_2_rules_round2_shaded_down_step",
    ),
    3: ElementaryVisualTemplate(
        problem_text="점선에 놓인 수에는 ↘ 방향으로 갈수록 몇씩 커지는 규칙이 있을까요?",
        expression="answer=4",
        topic="pattern",
        rule_id="grade2_2_rules_round2_diagonal_step",
    ),
    4: ElementaryVisualTemplate(
        problem_text="곱셈표의 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=1, 21, 25, 7",
        topic="pattern",
        rule_id="grade2_2_rules_round2_multiplication_table_blanks",
    ),
    5: ElementaryVisualTemplate(
        problem_text="빗금 친 수의 규칙을 찾아 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=2",
        topic="pattern",
        rule_id="grade2_2_rules_round2_shaded_down_step_text",
    ),
    6: ElementaryVisualTemplate(
        problem_text="곱셈표에 있는 수들은 모두 짝수입니까, 홀수입니까?",
        expression="answer_text=홀수에 ○표",
        topic="pattern",
        rule_id="grade2_2_rules_round2_odd_numbers",
    ),
}


_GRADE2_RULES_2_2_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="곱셈표를 선을 따라 접었을 때 만나는 수가 서로 같도록 선을 그으세요.",
        expression="answer_text=5번",
        topic="pattern",
        rule_id="grade2_2_rules_round2_page2_multiplication_fold_line",
    ),
    2: ElementaryVisualTemplate(
        problem_text="덧셈표에서 규칙을 찾아 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=68",
        topic="pattern",
        rule_id="grade2_2_rules_round2_page2_addition_table_blanks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="곱셈표에서 규칙을 찾아 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=68",
        topic="pattern",
        rule_id="grade2_2_rules_round2_page2_multiplication_table_blanks",
    ),
    4: ElementaryVisualTemplate(
        problem_text="규칙을 찾아 알맞은 모양을 그리고 색칠하세요.",
        expression="answer_text=초록색 삼각형",
        topic="pattern",
        rule_id="grade2_2_rules_round2_page2_next_shape",
    ),
    5: ElementaryVisualTemplate(
        problem_text="규칙을 찾아 다음에 올 꽃에 ○표 하세요.",
        expression="answer_text=노란색 꽃에 ○표",
        topic="pattern",
        rule_id="grade2_2_rules_round2_page2_next_flower",
    ),
    6: ElementaryVisualTemplate(
        problem_text="규칙을 찾아 반복되는 모양을 그리고 색칠하세요.",
        expression="answer_text=원, 삼각형, 마름모 반복",
        topic="pattern",
        rule_id="grade2_2_rules_round2_page2_repeating_shape_pattern",
    ),
    7: ElementaryVisualTemplate(
        problem_text="그림을 보고 규칙을 찾아 모양을 수로 바꾸어 나타내세요.",
        expression="answer_text=1 2 2 3 1 2 2 3 1 2 2 3 1 2 2 3 1 2",
        topic="pattern",
        rule_id="grade2_2_rules_round2_page2_shape_number_pattern",
    ),
}


_GRADE2_RULES_2_2_ROUND2_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="사각형 안에 점을 규칙에 맞게 그리세요.",
        expression="answer_text=왼쪽 아래에 점 3개",
        topic="pattern",
        rule_id="grade2_2_rules_round2_page3_dot_pattern",
    ),
    2: ElementaryVisualTemplate(
        problem_text="규칙에 따라 쌓기나무를 쌓았습니다. 다음에 이어질 모양에 쌓을 쌓기나무는 모두 몇 개인지 구하세요.",
        expression="answer_text=10개",
        topic="pattern",
        rule_id="grade2_2_rules_round2_page3_stacking_blocks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="10월 달력에서 일요일은 모두 몇 번 있는지 구하세요.",
        expression="answer_text=5번",
        topic="pattern",
        rule_id="grade2_2_rules_round2_page3_october_sundays",
    ),
    4: ElementaryVisualTemplate(
        problem_text="달력에서 규칙을 찾아 빨간색 선에 놓인 수가 몇씩 커지는지 구하세요.",
        expression="answer_text=5번",
        topic="pattern",
        rule_id="grade2_2_rules_round2_page3_calendar_diagonal_step",
    ),
    5: ElementaryVisualTemplate(
        problem_text="시계의 규칙을 찾아 마지막 시계에 시곗바늘을 알맞게 그리세요.",
        expression="answer_text=5시 30분",
        topic="pattern",
        rule_id="grade2_2_rules_round2_page3_clock_pattern",
    ),
    6: ElementaryVisualTemplate(
        problem_text="자리 번호의 규칙을 찾아 빈칸에 쓰여질 수의 합을 구하세요.",
        expression="answer_text=68",
        topic="pattern",
        rule_id="grade2_2_rules_round2_page3_seat_number_sum",
    ),
    7: ElementaryVisualTemplate(
        problem_text="자물쇠 수 배열에서 ↗ 방향과 왼쪽 방향의 규칙을 쓰세요.",
        expression="answer_text=5, 4",
        topic="pattern",
        rule_id="grade2_2_rules_round2_page3_lock_number_pattern",
    ),
}


_GRADE2_RULES_2_2_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="덧셈표의 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=8, 6, 8, 14",
        topic="pattern",
        rule_id="grade2_2_rules_round3_addition_table_blanks",
    ),
    2: ElementaryVisualTemplate(
        problem_text="빗금 친 수에는 오른쪽으로 갈수록 몇씩 커지는 규칙이 있을까요?",
        expression="answer=2",
        topic="pattern",
        rule_id="grade2_2_rules_round3_shaded_right_step",
    ),
    3: ElementaryVisualTemplate(
        problem_text="점선에 놓인 수에는 ↘ 방향으로 갈수록 몇씩 커지는 규칙이 있을까요?",
        expression="answer=4",
        topic="pattern",
        rule_id="grade2_2_rules_round3_diagonal_step",
    ),
    4: ElementaryVisualTemplate(
        problem_text="곱셈표의 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=8, 24, 32",
        topic="pattern",
        rule_id="grade2_2_rules_round3_multiplication_table_blanks",
    ),
    5: ElementaryVisualTemplate(
        problem_text="빗금 친 수의 규칙을 찾아 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=4",
        topic="pattern",
        rule_id="grade2_2_rules_round3_shaded_step_text",
    ),
    6: ElementaryVisualTemplate(
        problem_text="곱셈표에 있는 수들은 모두 짝수입니까, 홀수입니까?",
        expression="answer_text=짝수에 ○표",
        topic="pattern",
        rule_id="grade2_2_rules_round3_even_numbers",
    ),
}


_GRADE2_RULES_2_2_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="곱셈표를 선을 따라 접었을 때 만나는 수가 서로 같도록 선을 그으세요.",
        expression="answer_text=4번",
        topic="pattern",
        rule_id="grade2_2_rules_round3_page2_multiplication_fold_line",
    ),
    2: ElementaryVisualTemplate(
        problem_text="덧셈표에서 규칙을 찾아 빈칸에 알맞은 수를 써넣으세요.",
        expression="answer_text=13, 12, 13",
        topic="pattern",
        rule_id="grade2_2_rules_round3_page2_addition_table_blanks",
    ),
    3: ElementaryVisualTemplate(
        problem_text="규칙을 찾아 알맞은 모양을 그리고 색칠하세요.",
        expression="answer_text=이어지는 모양",
        topic="pattern",
        rule_id="grade2_2_rules_round3_page2_next_shape_1",
    ),
    4: ElementaryVisualTemplate(
        problem_text="규칙을 찾아 알맞은 모양을 그리고 색칠하세요.",
        expression="answer_text=이어지는 모양",
        topic="pattern",
        rule_id="grade2_2_rules_round3_page2_next_shape_2",
    ),
    5: ElementaryVisualTemplate(
        problem_text="규칙을 찾아 다음에 올 것에 ○표 하세요.",
        expression="answer_text=에 ○표",
        topic="pattern",
        rule_id="grade2_2_rules_round3_page2_next_item",
    ),
    6: ElementaryVisualTemplate(
        problem_text="규칙을 찾아 반복되는 모양을 그리고 색칠하세요.",
        expression="answer_text=반복되는 모양",
        topic="pattern",
        rule_id="grade2_2_rules_round3_page2_repeating_shape_pattern",
    ),
    7: ElementaryVisualTemplate(
        problem_text="그림을 보고 규칙을 찾아 모양을 수로 바꾸어 나타내세요.",
        expression="answer_text=순서대로",
        topic="pattern",
        rule_id="grade2_2_rules_round3_page2_shape_number_pattern_1",
    ),
    8: ElementaryVisualTemplate(
        problem_text="사각형 안에 점을 규칙에 맞게 그리세요.",
        expression="answer_text=순서대로",
        topic="pattern",
        rule_id="grade2_2_rules_round3_page2_dot_pattern",
    ),
}


_GRADE2_RULES_2_2_ROUND3_PAGE3: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="규칙에 따라 쌓기나무를 쌓았습니다. 다음에 이어질 모양에 쌓을 쌓기나무는 모두 몇 개인지 구하세요.",
        expression="answer_text=7개",
        topic="pattern",
        rule_id="grade2_2_rules_round3_page3_stacking_blocks",
    ),
    2: ElementaryVisualTemplate(
        problem_text="4월 달력에서 목요일은 모두 몇 번 있는지 구하세요.",
        expression="answer_text=4번",
        topic="pattern",
        rule_id="grade2_2_rules_round3_page3_april_thursdays_1",
    ),
    3: ElementaryVisualTemplate(
        problem_text="4월 달력에서 목요일은 모두 몇 번 있는지 구하세요.",
        expression="answer_text=4번",
        topic="pattern",
        rule_id="grade2_2_rules_round3_page3_april_thursdays_2",
    ),
    4: ElementaryVisualTemplate(
        problem_text="시계의 규칙을 찾아 마지막 시계에 시곗바늘을 알맞게 그리세요.",
        expression="answer_text=시곗바늘 그리기",
        topic="pattern",
        rule_id="grade2_2_rules_round3_page3_clock_pattern",
    ),
    5: ElementaryVisualTemplate(
        problem_text="숫자판에서 찾을 수 있는 규칙을 쓰세요.",
        expression="answer_text=2, 3",
        topic="pattern",
        rule_id="grade2_2_rules_round3_page3_number_panel_pattern_1",
    ),
    6: ElementaryVisualTemplate(
        problem_text="숫자판에서 찾을 수 있는 규칙을 쓰세요.",
        expression="answer_text=2, 3",
        topic="pattern",
        rule_id="grade2_2_rules_round3_page3_number_panel_pattern_2",
    ),
}


_GRADE2_MULTIPLICATION_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="그림을 보고 과자는 6씩 3묶음임을 쓰세요.",
        expression="answer_text=6, 3",
        rule_id="grade2_multiplication_round1_cookie_groups",
    ),
    2: ElementaryVisualTemplate(
        problem_text="3의 7배는 얼마입니까?",
        expression="answer=21",
        rule_id="grade2_multiplication_round1_three_times_seven",
    ),
    3: ElementaryVisualTemplate(
        problem_text="8을 7번 더한 식을 곱셈식으로 나타내세요.",
        expression="answer_text=56, 8, 7, 56",
        rule_id="grade2_multiplication_round1_repeated_eight",
    ),
    4: ElementaryVisualTemplate(
        problem_text="사탕은 4개씩 몇 묶음, 8개씩 몇 묶음인지 쓰세요.",
        expression="answer_text=4, 2",
        rule_id="grade2_multiplication_round1_candy_groups",
    ),
    5: ElementaryVisualTemplate(
        problem_text="수직선을 보고 곱셈식의 빈칸을 채우세요.",
        expression="answer_text=6, 4, 24",
        rule_id="grade2_multiplication_round1_number_line_six_four",
    ),
    6: ElementaryVisualTemplate(
        problem_text="관계있는 것끼리 선으로 이으세요. 2의 8배, 5의 4배, 6의 7배",
        expression="answer_text=(1) 16, (2) 20, (3) 42",
        rule_id="grade2_multiplication_round1_match_products",
    ),
    7: ElementaryVisualTemplate(
        problem_text="6 곱하기 7은 42와 같습니다를 곱셈식으로 나타내세요.",
        expression="answer_text=6 × 7 = 42",
        rule_id="grade2_multiplication_round1_sentence_to_expression",
    ),
    8: ElementaryVisualTemplate(
        problem_text="수직선에서 4씩 다섯 번 뛰면 어떤 수가 나옵니까?",
        expression="answer=20",
        rule_id="grade2_multiplication_round1_number_line_five_jumps",
    ),
    9: ElementaryVisualTemplate(
        problem_text="7×5와 6+6+6+6+6+6의 계산 결과를 비교하세요.",
        expression="answer_text=<",
        rule_id="grade2_multiplication_round1_compare_product_sum",
    ),
}


_GRADE2_MULTIPLICATION_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="5씩 4묶음, 7씩 8묶음, 3씩 8묶음과 관계있는 수를 이으세요.",
        expression="answer_text=5씩 4묶음-20, 7씩 8묶음-56, 3씩 8묶음-24",
        rule_id="grade2_multiplication_round1_match_group_counts",
    ),
    2: ElementaryVisualTemplate(
        problem_text="곱셈식으로 나타내어 구한 곱이 36인 것을 모두 고르세요.",
        expression="answer_text=②, ⑤",
        rule_id="grade2_multiplication_round1_product_36_choices",
    ),
    3: ElementaryVisualTemplate(
        problem_text="딸기의 수를 3, 6, 9의 몇 배인지 쓰세요.",
        expression="answer_text=(1) 6, (2) 3, (3) 2",
        rule_id="grade2_multiplication_round1_strawberry_multiples",
    ),
    4: ElementaryVisualTemplate(
        problem_text="2를 7번 더한 덧셈식을 곱셈식으로 나타내세요.",
        expression="answer_text=2 × 7 = 14",
        rule_id="grade2_multiplication_round1_repeated_two",
    ),
    5: ElementaryVisualTemplate(
        problem_text="9×5=45와 다른 것을 찾아 기호를 쓰세요.",
        expression="answer_text=라",
        rule_id="grade2_multiplication_round1_not_equivalent_to_9x5",
    ),
    6: ElementaryVisualTemplate(
        problem_text="곱셈식으로 나타내어 구한 곱이 가장 작은 것을 고르세요.",
        expression="answer_text=①",
        rule_id="grade2_multiplication_round1_smallest_product_choice",
    ),
    7: ElementaryVisualTemplate(
        problem_text="종이로 가려진 부분에는 몇 개의 점이 있습니까?",
        expression="answer_text=25개",
        rule_id="grade2_multiplication_round1_hidden_dots",
    ),
    8: ElementaryVisualTemplate(
        problem_text="한수의 나이는 8살이고 어머니의 나이는 한수 나이의 5배입니다.",
        expression="answer_text=40살",
        rule_id="grade2_multiplication_round1_mother_age",
    ),
    9: ElementaryVisualTemplate(
        problem_text="한 학년에 7반이 있고 1학년부터 6학년까지 모두 몇 반인지 구하세요.",
        expression="answer_text=42반",
        rule_id="grade2_multiplication_round1_total_classes",
    ),
    10: ElementaryVisualTemplate(
        problem_text="수철이의 나이는 동생보다 3살 많고 어머니의 나이는 동생 나이의 6배입니다. 수철이가 9살일 때 어머니의 나이를 구하세요.",
        expression="answer_text=36살",
        rule_id="grade2_multiplication_round1_family_age",
    ),
    11: ElementaryVisualTemplate(
        problem_text="젤리를 4개씩 6봉지에 담았더니 3개가 남았습니다. 젤리는 모두 몇 개입니까?",
        expression="answer_text=27개",
        rule_id="grade2_multiplication_round1_jelly_total",
    ),
}


_GRADE2_MULTIPLICATION_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="귤을 4개씩 3묶음으로 세면 모두 몇 개인지 쓰세요.",
        expression="answer_text=12개",
        rule_id="grade2_multiplication_round2_orange_groups",
    ),
    2: ElementaryVisualTemplate(
        problem_text="사탕을 2씩 묶은 그림을 보고 묶음 수와 전체 수를 쓰세요.",
        expression="answer_text=4, 8",
        rule_id="grade2_multiplication_round2_candy_pairs",
    ),
    3: ElementaryVisualTemplate(
        problem_text="4를 7번 더한 덧셈식을 곱셈식으로 나타내세요.",
        expression="answer_text=28, 4, 7, 28",
        rule_id="grade2_multiplication_round2_repeated_four",
    ),
    4: ElementaryVisualTemplate(
        problem_text="9와 4의 곱은 36입니다를 곱셈식으로 나타내세요.",
        expression="answer_text=9 × 4 = 36",
        rule_id="grade2_multiplication_round2_sentence_to_expression",
    ),
    5: ElementaryVisualTemplate(
        problem_text="멜론이 모두 몇 개인지 여러 가지 곱셈식으로 나타내세요.",
        expression="answer_text=2, 7, 14 / 7, 2, 14",
        rule_id="grade2_multiplication_round2_melon_array",
    ),
    6: ElementaryVisualTemplate(
        problem_text="5의 3배를 바르게 나타낸 것이 아닌 것을 고르세요.",
        expression="answer_text=㉢",
        rule_id="grade2_multiplication_round2_not_five_times_three",
    ),
    7: ElementaryVisualTemplate(
        problem_text="48은 6의 몇 배인지 쓰세요.",
        expression="answer=8",
        rule_id="grade2_multiplication_round2_48_is_6_times",
    ),
    8: ElementaryVisualTemplate(
        problem_text="수직선을 보고 3을 몇 번 더했는지 곱셈식을 완성하세요.",
        expression="answer_text=7, 21",
        rule_id="grade2_multiplication_round2_number_line_three_times_seven",
    ),
    9: ElementaryVisualTemplate(
        problem_text="성냥개비로 만든 삼각형 그림을 보고 곱셈식을 완성하세요.",
        expression="answer_text=6, 18",
        rule_id="grade2_multiplication_round2_triangle_matches",
    ),
    10: ElementaryVisualTemplate(
        problem_text="㉠×5=30, 9×㉡=36일 때 ㉠과 ㉡의 합을 구하세요.",
        expression="answer=10",
        rule_id="grade2_multiplication_round2_unknown_factors_sum",
    ),
}


_GRADE2_MULTIPLICATION_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="4×8과 7×5의 계산 결과를 비교하세요.",
        expression="answer_text=<",
        rule_id="grade2_multiplication_round2_compare_4x8_7x5",
    ),
    2: ElementaryVisualTemplate(
        problem_text="계산 결과가 다른 하나에 ○표 하세요.",
        expression="answer_text=두 번째에 ○표",
        rule_id="grade2_multiplication_round2_different_product",
    ),
    3: ElementaryVisualTemplate(
        problem_text="㉠, ㉡, ㉢을 계산 결과가 작은 것부터 차례로 쓰세요.",
        expression="answer_text=㉡, ㉢, ㉠",
        rule_id="grade2_multiplication_round2_order_products",
    ),
    4: ElementaryVisualTemplate(
        problem_text="가려진 딸기까지 모두 몇 개인지 구하세요.",
        expression="answer_text=36개",
        rule_id="grade2_multiplication_round2_hidden_strawberries",
    ),
    5: ElementaryVisualTemplate(
        problem_text="사자 8마리의 다리는 모두 몇 개인지 구하세요.",
        expression="answer_text=32개",
        rule_id="grade2_multiplication_round2_lion_legs",
    ),
    6: ElementaryVisualTemplate(
        problem_text="현서가 8살이고 이모의 나이가 현서 나이의 5배일 때 이모의 나이를 구하세요.",
        expression="answer_text=40살",
        rule_id="grade2_multiplication_round2_aunt_age",
    ),
    7: ElementaryVisualTemplate(
        problem_text="6명이 모두 가위를 냈을 때 펼친 손가락은 모두 몇 개인지 구하세요.",
        expression="answer_text=12개",
        rule_id="grade2_multiplication_round2_scissors_fingers",
    ),
    8: ElementaryVisualTemplate(
        problem_text="사과 42개를 한 봉지에 6개씩 담으면 모두 몇 봉지인지 구하세요.",
        expression="answer_text=7봉지",
        rule_id="grade2_multiplication_round2_apple_bags",
    ),
    9: ElementaryVisualTemplate(
        problem_text="강아지 4마리와 병아리 3마리의 다리는 모두 몇 개인지 구하세요.",
        expression="answer_text=22개",
        rule_id="grade2_multiplication_round2_dog_chick_legs",
    ),
    10: ElementaryVisualTemplate(
        problem_text="초콜릿을 2개씩 6묶음 만들고 2묶음을 주었을 때 남은 초콜릿은 몇 개인지 구하세요.",
        expression="answer_text=8개",
        rule_id="grade2_multiplication_round2_remaining_chocolates",
    ),
}


_GRADE2_MULTIPLICATION_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="딸기는 모두 몇 개인지 2씩 뛰어 세어 보세요.",
        expression="answer_text=10개",
        rule_id="grade2_multiplication_round3_count_strawberries_by_two",
    ),
    2: ElementaryVisualTemplate(
        problem_text="딸기 그림을 보고 3씩 몇 묶음인지, 모두 몇 개인지 쓰세요.",
        expression="answer_text=4, 12",
        rule_id="grade2_multiplication_round3_strawberry_groups",
    ),
    3: ElementaryVisualTemplate(
        problem_text="6을 8번 더한 덧셈식을 곱셈식으로 나타내세요.",
        expression="answer_text=48, 6, 8, 48",
        rule_id="grade2_multiplication_round3_repeated_six",
    ),
    4: ElementaryVisualTemplate(
        problem_text="7×4=28을 덧셈식으로 나타내세요.",
        expression="answer_text=7 + 7 + 7 + 7 = 28",
        rule_id="grade2_multiplication_round3_product_to_repeated_addition",
    ),
    5: ElementaryVisualTemplate(
        problem_text="지우개 그림을 덧셈식과 곱셈식으로 나타내세요.",
        expression="answer_text=8 / 2, 4, 8",
        rule_id="grade2_multiplication_round3_eraser_array",
    ),
    6: ElementaryVisualTemplate(
        problem_text="7씩 3묶음은 7의 몇 배이고, 덧셈식은 무엇인지 쓰세요.",
        expression="answer_text=3, 7, 7, 7, 21",
        rule_id="grade2_multiplication_round3_three_groups_of_seven",
    ),
    7: ElementaryVisualTemplate(
        problem_text="어떤 수의 6묶음은 42입니다. 어떤 수를 구하세요.",
        expression="answer=7",
        rule_id="grade2_multiplication_round3_six_groups_make_42",
    ),
    8: ElementaryVisualTemplate(
        problem_text="수직선을 보고 곱셈식을 완성하세요.",
        expression="answer_text=3, 27",
        rule_id="grade2_multiplication_round3_number_line_nine_times_three",
    ),
    9: ElementaryVisualTemplate(
        problem_text="오각형 그림을 보고 곱셈식을 완성하세요.",
        expression="answer_text=5, 25",
        rule_id="grade2_multiplication_round3_pentagon_sides",
    ),
}


_GRADE2_MULTIPLICATION_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="㉠×6=36, 7×㉡=49일 때 ㉠과 ㉡의 차를 구하세요.",
        expression="answer=1",
        rule_id="grade2_multiplication_round3_unknown_factor_difference",
    ),
    2: ElementaryVisualTemplate(
        problem_text="6씩 4묶음과 5의 4배의 계산 결과를 비교하세요.",
        expression="answer_text=>",
        rule_id="grade2_multiplication_round3_compare_6x4_5x4",
    ),
    3: ElementaryVisualTemplate(
        problem_text="나타내는 수가 다른 하나에 ○표 하세요.",
        expression="answer_text=세 번째에 ○표",
        rule_id="grade2_multiplication_round3_different_product",
    ),
    4: ElementaryVisualTemplate(
        problem_text="나타내는 수가 큰 것부터 차례로 기호를 쓰세요.",
        expression="answer_text=㉠, ㉢, ㉡",
        rule_id="grade2_multiplication_round3_order_products_desc",
    ),
    5: ElementaryVisualTemplate(
        problem_text="가려진 클립은 모두 몇 개인지 구하세요.",
        expression="answer_text=9개",
        rule_id="grade2_multiplication_round3_hidden_clips",
    ),
    6: ElementaryVisualTemplate(
        problem_text="거미 7마리의 다리는 모두 몇 개인지 구하세요.",
        expression="answer_text=56개",
        rule_id="grade2_multiplication_round3_spider_legs",
    ),
    7: ElementaryVisualTemplate(
        problem_text="영준이가 9살이고 삼촌의 나이가 영준이 나이의 4배일 때 삼촌의 나이를 구하세요.",
        expression="answer_text=36살",
        rule_id="grade2_multiplication_round3_uncle_age",
    ),
    8: ElementaryVisualTemplate(
        problem_text="5명이 모두 보를 냈을 때 펼친 손가락은 모두 몇 개인지 구하세요.",
        expression="answer_text=25개",
        rule_id="grade2_multiplication_round3_paper_fingers",
    ),
    9: ElementaryVisualTemplate(
        problem_text="딸기가 한 팩에 8개씩 들어 있고 모두 40개일 때 몇 팩인지 구하세요.",
        expression="answer_text=5팩",
        rule_id="grade2_multiplication_round3_strawberry_packs",
    ),
    10: ElementaryVisualTemplate(
        problem_text="참새 6마리와 고양이 3마리의 다리는 모두 몇 개인지 구하세요.",
        expression="answer_text=24개",
        rule_id="grade2_multiplication_round3_bird_cat_legs",
    ),
    11: ElementaryVisualTemplate(
        problem_text="서진이가 사탕을 2개씩 3묶음 가지고 있고 형은 그 3배를 가지고 있을 때 형의 사탕 수를 구하세요.",
        expression="answer_text=18개",
        rule_id="grade2_multiplication_round3_brother_candies",
    ),
}


_GRADE2_TIMES_TABLE_ROUND1_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="별은 모두 몇 개인지 곱셈식으로 나타내세요.",
        expression="answer_text=6, 12",
        rule_id="grade2_times_table_round1_stars",
    ),
    2: ElementaryVisualTemplate(
        problem_text="축구공 12개를 보고 2×□=12, 4×□=12의 빈칸을 채우세요.",
        expression="answer_text=6, 3",
        rule_id="grade2_times_table_round1_soccer_balls",
    ),
    3: ElementaryVisualTemplate(
        problem_text="1×9와 3×3의 곱을 비교하세요.",
        expression="answer_text==",
        rule_id="grade2_times_table_round1_compare_1x9_3x3",
    ),
    4: ElementaryVisualTemplate(
        problem_text="7에 4와 7을 각각 곱한 값을 쓰세요.",
        expression="answer_text=28, 49",
        rule_id="grade2_times_table_round1_seven_times",
    ),
    5: ElementaryVisualTemplate(
        problem_text="병아리 8마리의 다리는 모두 몇 개인지 구하세요.",
        expression="answer_text=16개",
        rule_id="grade2_times_table_round1_chick_legs",
    ),
    6: ElementaryVisualTemplate(
        problem_text="농구에서 선수 5명이 한 팀입니다. 9팀이면 모두 몇 명인지 구하세요.",
        expression="answer_text=45명",
        rule_id="grade2_times_table_round1_basketball_players",
    ),
    7: ElementaryVisualTemplate(
        problem_text="우유가 6갑씩 7줄 놓여 있을 때 모두 몇 갑인지 구하세요.",
        expression="answer_text=42갑",
        rule_id="grade2_times_table_round1_milk_cartons",
    ),
    8: ElementaryVisualTemplate(
        problem_text="6×7은 6×6보다 얼마나 더 큰지 구하세요.",
        expression="answer=6",
        rule_id="grade2_times_table_round1_difference_6x7_6x6",
    ),
    9: ElementaryVisualTemplate(
        problem_text="성냥개비 3개로 삼각형 한 개를 만들 때 삼각형 7개에 필요한 성냥개비 수를 구하세요.",
        expression="answer_text=21개",
        rule_id="grade2_times_table_round1_matchstick_triangles",
    ),
    10: ElementaryVisualTemplate(
        problem_text="거미 한 마리의 다리가 8개일 때 거미 6마리의 다리 수를 구하세요.",
        expression="answer_text=48개",
        rule_id="grade2_times_table_round1_spider_legs",
    ),
    11: ElementaryVisualTemplate(
        problem_text="□×8=8, 2×□=2에 공통으로 들어가는 수를 쓰세요.",
        expression="answer=1",
        rule_id="grade2_times_table_round1_common_factor_one",
    ),
}


_GRADE2_TIMES_TABLE_ROUND1_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="9에서 ×1, ×7 순서로 계산한 빈칸을 채우세요.",
        expression="answer_text=9, 63",
        rule_id="grade2_times_table_round1_chain_9_times",
    ),
    2: ElementaryVisualTemplate(
        problem_text="8×□ < 40이 되도록 □ 안에 들어갈 수 있는 수를 모두 쓰세요.",
        expression="answer_text=0, 1, 2, 3, 4",
        rule_id="grade2_times_table_round1_blank_less_than_40",
    ),
    3: ElementaryVisualTemplate(
        problem_text="계산 결과가 6×5와 같지 않은 것을 고르세요.",
        expression="answer_text=⑤",
        rule_id="grade2_times_table_round1_not_equal_6x5",
    ),
    4: ElementaryVisualTemplate(
        problem_text="3×□와 2×9의 곱이 같을 때 □ 안에 알맞은 수를 구하세요.",
        expression="answer=6",
        rule_id="grade2_times_table_round1_equal_products_blank",
    ),
    5: ElementaryVisualTemplate(
        problem_text="곱셈표에서 0, 3, 6과 2, 5, 7의 곱을 채우세요.",
        expression="answer_text=0, 0, 0 / 6, 15, 21 / 12, 30, 42",
        rule_id="grade2_times_table_round1_multiplication_table",
    ),
    6: ElementaryVisualTemplate(
        problem_text="단추가 3개씩 달린 옷 6벌에서 단추 6개가 떨어졌을 때 남은 단추 수를 구하세요.",
        expression="answer_text=12개",
        rule_id="grade2_times_table_round1_buttons_remaining",
    ),
    7: ElementaryVisualTemplate(
        problem_text="현정이가 9살이고 아버지 나이는 현정이 나이의 4배보다 5살 많을 때 아버지 나이를 구하세요.",
        expression="answer_text=41세",
        rule_id="grade2_times_table_round1_father_age",
    ),
    8: ElementaryVisualTemplate(
        problem_text="0점 3번, 1점 2번, 3점 2번 맞혔을 때 총점을 구하세요.",
        expression="answer_text=8점",
        rule_id="grade2_times_table_round1_game_score",
    ),
    9: ElementaryVisualTemplate(
        problem_text="바둑돌이 6개씩 4줄과 3개씩 5줄로 놓여 있을 때 모두 몇 개인지 구하세요.",
        expression="answer_text=39개",
        rule_id="grade2_times_table_round1_stones_total",
    ),
}


_GRADE2_TIMES_TABLE_ROUND2_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="딸기는 모두 몇 개인지 곱셈식으로 나타내세요.",
        expression="answer_text=3, 15",
        rule_id="grade2_times_table_round2_strawberries",
    ),
    2: ElementaryVisualTemplate(
        problem_text="우산 18개를 보고 2×□=18, 3×□=18의 빈칸을 채우세요.",
        expression="answer_text=9, 6",
        rule_id="grade2_times_table_round2_umbrellas",
    ),
    3: ElementaryVisualTemplate(
        problem_text="8×4와 5×7의 곱을 비교하세요.",
        expression="answer_text=<",
        rule_id="grade2_times_table_round2_compare_8x4_5x7",
    ),
    4: ElementaryVisualTemplate(
        problem_text="8에 2와 8을 각각 곱한 값을 쓰세요.",
        expression="answer_text=16, 64",
        rule_id="grade2_times_table_round2_eight_times",
    ),
    5: ElementaryVisualTemplate(
        problem_text="신발 7켤레는 모두 몇 짝인지 구하세요.",
        expression="answer_text=14짝",
        rule_id="grade2_times_table_round2_shoes_pairs",
    ),
    6: ElementaryVisualTemplate(
        problem_text="한 대에 5명씩 탈 수 있는 놀이기구 8대에 탈 수 있는 사람 수를 구하세요.",
        expression="answer_text=40명",
        rule_id="grade2_times_table_round2_ride_people",
    ),
    7: ElementaryVisualTemplate(
        problem_text="한 학생에게 7자루씩 연필을 8명에게 나누어 주려면 필요한 연필 수를 구하세요.",
        expression="answer_text=56자루",
        rule_id="grade2_times_table_round2_pencils_students",
    ),
    8: ElementaryVisualTemplate(
        problem_text="6×9=(6×□)+6이 되도록 □ 안에 알맞은 수를 쓰세요.",
        expression="answer=8",
        rule_id="grade2_times_table_round2_decompose_6x9",
    ),
    9: ElementaryVisualTemplate(
        problem_text="성냥개비 4개로 사각형 한 개를 만들 때 사각형 9개에 필요한 성냥개비 수를 구하세요.",
        expression="answer_text=36개",
        rule_id="grade2_times_table_round2_matchstick_squares",
    ),
    10: ElementaryVisualTemplate(
        problem_text="문어 한 마리의 다리가 8개일 때 문어 8마리의 다리 수를 구하세요.",
        expression="answer_text=64개",
        rule_id="grade2_times_table_round2_octopus_legs",
    ),
}


_GRADE2_TIMES_TABLE_ROUND2_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="□×5=0, 7×□=0에 공통으로 들어가는 수를 쓰세요.",
        expression="answer=0",
        rule_id="grade2_times_table_round2_common_zero",
    ),
    2: ElementaryVisualTemplate(
        problem_text="3에서 ×3, ×6 순서로 계산한 빈칸을 채우세요.",
        expression="answer_text=9, 54",
        rule_id="grade2_times_table_round2_chain_3_times",
    ),
    3: ElementaryVisualTemplate(
        problem_text="4×□ < 24가 되도록 □ 안에 들어갈 수 있는 수를 모두 쓰세요.",
        expression="answer_text=0, 1, 2, 3, 4, 5",
        rule_id="grade2_times_table_round2_blank_less_than_24",
    ),
    4: ElementaryVisualTemplate(
        problem_text="4의 단 곱셈구구에서는 곱이 얼마씩 커지는지 구하세요.",
        expression="answer=4",
        rule_id="grade2_times_table_round2_four_table_step",
    ),
    5: ElementaryVisualTemplate(
        problem_text="6×□와 9×4의 곱이 같을 때 □ 안에 알맞은 수를 구하세요.",
        expression="answer=6",
        rule_id="grade2_times_table_round2_equal_products_blank",
    ),
    6: ElementaryVisualTemplate(
        problem_text="곱셈표에서 1, 2, 7과 0, 3, 5의 곱을 채우세요.",
        expression="answer_text=0, 3, 5 / 0, 6, 10 / 0, 21, 35",
        rule_id="grade2_times_table_round2_multiplication_table",
    ),
    7: ElementaryVisualTemplate(
        problem_text="풍선이 4개씩 7묶음 있고 그중 8개가 터졌을 때 남은 풍선 수를 구하세요.",
        expression="answer_text=20개",
        rule_id="grade2_times_table_round2_balloons_remaining",
    ),
    8: ElementaryVisualTemplate(
        problem_text="현수가 9살이고 이모의 나이가 현수 나이의 3배보다 3살 많을 때 이모의 나이를 구하세요.",
        expression="answer_text=30세",
        rule_id="grade2_times_table_round2_aunt_age",
    ),
    9: ElementaryVisualTemplate(
        problem_text="0점 4번, 1점 2번, 2점 1번, 4점 0번 맞혔을 때 총점을 구하세요.",
        expression="answer_text=4점",
        rule_id="grade2_times_table_round2_game_score",
    ),
    10: ElementaryVisualTemplate(
        problem_text="사과가 8개씩 4줄, 배가 5개씩 6줄 있을 때 모두 몇 개인지 구하세요.",
        expression="answer_text=62개",
        rule_id="grade2_times_table_round2_fruits_total",
    ),
}


_GRADE2_TIMES_TABLE_ROUND3_PAGE1: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="야구공의 개수를 구하세요.",
        expression="answer_text=27개",
        rule_id="grade2_times_table_round3_baseballs",
    ),
    2: ElementaryVisualTemplate(
        problem_text="달걀이 모두 몇 개인지 곱셈식으로 나타내세요.",
        expression="answer_text=4, 24",
        rule_id="grade2_times_table_round3_eggs",
    ),
    3: ElementaryVisualTemplate(
        problem_text="곱이 큰 것부터 차례대로 기호를 쓰세요.",
        expression="answer_text=㉠, ㉢, ㉣, ㉡",
        rule_id="grade2_times_table_round3_order_products_desc",
    ),
    4: ElementaryVisualTemplate(
        problem_text="6에 7과 9를 각각 곱한 값을 쓰세요.",
        expression="answer_text=42, 54",
        rule_id="grade2_times_table_round3_six_times",
    ),
    5: ElementaryVisualTemplate(
        problem_text="2명씩 앉는 의자 9개에는 모두 몇 명이 앉을 수 있는지 구하세요.",
        expression="answer_text=18명",
        rule_id="grade2_times_table_round3_chairs_people",
    ),
    6: ElementaryVisualTemplate(
        problem_text="한 줄에 요구르트가 5병씩 있고 6줄일 때 모두 몇 병인지 구하세요.",
        expression="answer_text=30병",
        rule_id="grade2_times_table_round3_yogurts",
    ),
    7: ElementaryVisualTemplate(
        problem_text="개미의 다리가 6개일 때 개미 7마리의 다리 수를 구하세요.",
        expression="answer_text=42개",
        rule_id="grade2_times_table_round3_ant_legs",
    ),
    8: ElementaryVisualTemplate(
        problem_text="6의 단 곱셈구구의 값은 3의 단 곱셈구구의 값을 몇 번 더한 것과 같은지 쓰세요.",
        expression="answer=2",
        rule_id="grade2_times_table_round3_six_table_double_three",
    ),
    9: ElementaryVisualTemplate(
        problem_text="성냥개비 4개로 사각형 한 개를 만들 때 사각형 6개에 필요한 성냥개비 수를 구하세요.",
        expression="answer_text=24개",
        rule_id="grade2_times_table_round3_matchstick_squares",
    ),
    10: ElementaryVisualTemplate(
        problem_text="필통 1개에 연필이 8자루씩 들어 있을 때 필통 9개의 연필 수를 구하세요.",
        expression="answer_text=72자루",
        rule_id="grade2_times_table_round3_pencil_cases",
    ),
    11: ElementaryVisualTemplate(
        problem_text="장미꽃의 수를 보고 □×4=0의 빈칸을 채우세요.",
        expression="answer=0",
        rule_id="grade2_times_table_round3_zero_roses",
    ),
}


_GRADE2_TIMES_TABLE_ROUND3_PAGE2: dict[int, ElementaryVisualTemplate] = {
    1: ElementaryVisualTemplate(
        problem_text="3에서 ×2, ×8 순서로 계산한 빈칸을 채우세요.",
        expression="answer_text=6, 48",
        rule_id="grade2_times_table_round3_chain_3_times",
    ),
    2: ElementaryVisualTemplate(
        problem_text="7×□ < 26이 되도록 □ 안에 들어갈 수 있는 수를 모두 쓰세요.",
        expression="answer_text=0, 1, 2, 3",
        rule_id="grade2_times_table_round3_blank_less_than_26",
    ),
    3: ElementaryVisualTemplate(
        problem_text="3×6은 3×8보다 얼마나 작은지 구하세요.",
        expression= "answer=6",
        rule_id="grade2_times_table_round3_difference_3x6_3x8",
    ),
    4: ElementaryVisualTemplate(
        problem_text="8×□와 6×4의 곱이 같을 때 □ 안에 알맞은 수를 구하세요.",
        expression="answer=3",
        rule_id="grade2_times_table_round3_equal_products_blank",
    ),
    5: ElementaryVisualTemplate(
        problem_text="곱셈표에서 1, 5, 9와 1, 6, 8의 곱을 채우세요.",
        expression="answer_text=1, 6, 8 / 5, 30, 40 / 9, 54, 72",
        rule_id="grade2_times_table_round3_multiplication_table",
    ),
    6: ElementaryVisualTemplate(
        problem_text="스티커를 하루에 3장씩 8일 동안 모으고 6장을 주었을 때 남은 스티커 수를 구하세요.",
        expression="answer_text=18장",
        rule_id="grade2_times_table_round3_stickers_remaining",
    ),
    7: ElementaryVisualTemplate(
        problem_text="희정이가 9살이고 어머니 나이가 희정이 나이의 3배보다 8살 많을 때 어머니 나이를 구하세요.",
        expression="answer_text=35세",
        rule_id="grade2_times_table_round3_mother_age",
    ),
    8: ElementaryVisualTemplate(
        problem_text="0점 2번, 1점 3번, 2점 1번 맞혔을 때 총점을 구하세요.",
        expression="answer_text=5점",
        rule_id="grade2_times_table_round3_game_score",
    ),
    9: ElementaryVisualTemplate(
        problem_text="사탕이 5개씩 3묶음과 6개씩 4묶음 있을 때 모두 몇 개인지 구하세요.",
        expression="answer_text=39개",
        rule_id="grade2_times_table_round3_candies_total",
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


_TENS_READINGS: dict[int, tuple[str, str]] = {
    10: ("십", "열"),
    20: ("이십", "스물"),
    30: ("삼십", "서른"),
    40: ("사십", "마흔"),
    50: ("오십", "쉰"),
    60: ("육십", "예순"),
    70: ("칠십", "일흔"),
    80: ("팔십", "여든"),
    90: ("구십", "아흔"),
}


def _infer_box_count_by_tens(raw_text: str) -> ElementaryVisualTemplate | None:
    compact = _compact_source(raw_text)
    if "한상자에10" not in compact or "몇상자" not in compact:
        return None
    totals = [int(value) for value in re.findall(r"(?<!\d)(\d{2,3})(?=자루|장|개|송이)", compact)]
    totals = [value for value in totals if value >= 20 and value % 10 == 0]
    if not totals:
        return None
    total = max(totals)
    return ElementaryVisualTemplate(
        problem_text=f"한 상자에 10개씩 들어 있습니다. {total}개를 사려면 {total // 10}상자가 필요합니다.",
        expression=f"answer_text={total // 10}상자",
        confidence=0.84,
        rule_id="generic_tens_box_count",
    )


def _infer_tens_bundle_write_read(raw_text: str) -> ElementaryVisualTemplate | None:
    compact = _compact_source(raw_text)
    if "나타내는수" not in compact or "10개씩묶음" not in compact:
        return None
    match = re.search(r"10개씩묶음(\d{1,2})개", compact)
    if not match:
        return None
    value = int(match.group(1)) * 10
    readings = _TENS_READINGS.get(value)
    if readings is None:
        return None
    return ElementaryVisualTemplate(
        problem_text=f"10개씩 묶음 {value // 10}개가 나타내는 수를 쓰고 읽어 보세요.",
        expression=f"answer_text=쓰기: {value} / 읽기: {readings[0]}, {readings[1]}",
        confidence=0.86,
        rule_id="generic_tens_bundle_write_read",
    )


def _infer_tens_bundle_and_extra_count(raw_text: str) -> ElementaryVisualTemplate | None:
    compact = _compact_source(raw_text)
    match = re.search(r"10(?:개|장|자루)?씩?묶음(\d{1,2})개와(?:낱|날)개?(\d{1,2})(?:개|장|자루)?", compact)
    if not match:
        return None
    tens = int(match.group(1))
    ones = int(match.group(2))
    total = tens * 10 + ones
    unit = "개"
    if "자루" in compact:
        unit = "자루"
    elif "장" in compact:
        unit = "장"
    return ElementaryVisualTemplate(
        problem_text=f"10개 묶음 {tens}개와 낱개 {ones}개는 모두 {total}{unit}입니다.",
        expression=f"answer_text={total}{unit}",
        confidence=0.84,
        rule_id="generic_tens_bundle_and_extra_count",
    )


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


def _infer_count_and_mark_choice(raw_text: str) -> ElementaryVisualTemplate | None:
    compact = _compact_source(raw_text)
    if "알맞은수" not in compact or not re.search(r"표시|∨|v", compact, flags=re.IGNORECASE):
        return None
    lines = [line.strip() for line in str(raw_text or "").splitlines() if line.strip()]
    answers: list[int] = []
    pending_count = 0
    for line in lines:
        dot_count = line.count("●") + line.count("○")
        if dot_count:
            pending_count += dot_count
            continue
        values = [int(value) for value in re.findall(r"(?<!\d)(\d{1,2})(?!\d)", line)]
        if pending_count and values:
            if pending_count in values:
                answers.append(pending_count)
            pending_count = 0
    if not answers:
        return None
    return ElementaryVisualTemplate(
        problem_text="그림의 수를 세어 알맞은 수에 표시하세요.",
        expression="answer_text=" + ", ".join(str(answer) for answer in answers),
        confidence=0.86,
        rule_id="generic_count_and_mark_choice",
    )


def _infer_incomplete_arithmetic_equation_list(raw_text: str) -> ElementaryVisualTemplate | None:
    source = str(raw_text or "")
    if "=" not in source or not re.search(r"빈\s*칸|빈칸|알맞은|계산|뺄셈|덧셈", source):
        return None
    matches = re.findall(r"(?<!\d)(\d{1,2})\s*([+\-])\s*(\d{1,2})\s*=", source)
    if len(matches) < 2:
        return None
    answers: list[int] = []
    for left_raw, operator, right_raw in matches:
        left = int(left_raw)
        right = int(right_raw)
        answer = left + right if operator == "+" else left - right
        if answer < 0:
            return None
        answers.append(answer)
    return ElementaryVisualTemplate(
        problem_text="빈칸에 알맞은 계산 결과를 쓰세요.",
        expression="answer_text=" + ", ".join(str(answer) for answer in answers),
        confidence=0.9,
        rule_id="generic_incomplete_arithmetic_equation_list",
    )


def _parse_meter_centimeter_values(source: str) -> list[int]:
    values: list[int] = []
    pattern = re.compile(
        r"(?<!\d)(\d{1,2})\s*(?:m|ｍ|미터)\s*(?:(\d{1,2})\s*(?:cm|㎝|센티미터))?",
        flags=re.IGNORECASE,
    )
    for match in pattern.finditer(str(source or "")):
        meters = int(match.group(1))
        centimeters = int(match.group(2) or 0)
        values.append(meters * 100 + centimeters)
    return values


def _format_meter_centimeter(total_cm: int) -> str:
    meters, centimeters = divmod(total_cm, 100)
    if meters and centimeters:
        return f"{meters} m {centimeters} cm"
    if meters:
        return f"{meters} m"
    return f"{centimeters} cm"


def _infer_meter_centimeter_context_operation(raw_text: str) -> ElementaryVisualTemplate | None:
    source = str(raw_text or "")
    compact = _compact_source(source)
    if "굴렁쇠" in compact and "거리" in compact:
        values = _parse_meter_centimeter_values(source)
        if len(values) < 2:
            return None
        first, second = values[-2], values[-1]
        answer = _format_meter_centimeter(first + second)
        return ElementaryVisualTemplate(
            problem_text="굴렁쇠가 굴러간 거리를 두 길이의 합으로 구하세요.",
            expression=f"answer_text={answer}",
            topic="measurement",
            confidence=0.9,
            rule_id="generic_meter_centimeter_sum_context",
        )
    if "사용한색테이프" in compact or ("처음길이" in compact and "남은길이" in compact):
        tail_match = re.search(r"(사용한\s*색\s*테이프|처음\s*길이).+", source, flags=re.DOTALL)
        values = _parse_meter_centimeter_values(tail_match.group(0) if tail_match else source)
        if len(values) < 2:
            return None
        original, remaining = values[0], values[1]
        if original < remaining:
            return None
        answer = _format_meter_centimeter(original - remaining)
        return ElementaryVisualTemplate(
            problem_text="처음 길이와 남은 길이를 보고 사용한 색 테이프의 길이를 구하세요.",
            expression=f"answer_text={answer}",
            topic="measurement",
            confidence=0.9,
            rule_id="generic_meter_centimeter_difference_context",
        )
    return None


def _infer_centimeter_to_meter_centimeter_list(raw_text: str) -> ElementaryVisualTemplate | None:
    source = str(raw_text or "")
    compact = _compact_source(source)
    if "cm" not in compact.lower() or "m" not in compact.lower():
        return None
    if not re.search(r"나타내|바꾸|고쳐|몇m", compact):
        return None
    values: list[int] = []
    for match in re.finditer(r"(?<!\d)(\d{2,4})\s*(?:cm|㎝)", source, flags=re.IGNORECASE):
        value = int(match.group(1))
        if value < 100:
            continue
        values.append(value)
    if len(values) < 2:
        return None

    answers: list[str] = []
    for value in values:
        meters, centimeters = divmod(value, 100)
        if centimeters:
            answers.append(f"{meters} m {centimeters} cm")
        else:
            answers.append(f"{meters} m")
    return ElementaryVisualTemplate(
        problem_text="cm로 나타낸 길이를 m와 cm로 나타내세요.",
        expression="answer_text=" + ", ".join(answers),
        topic="measurement",
        confidence=0.88,
        rule_id="generic_centimeter_to_meter_centimeter_list",
    )


def _infer_length_estimate_choice(raw_text: str) -> ElementaryVisualTemplate | None:
    source = str(raw_text or "")
    compact = _compact_source(source)
    if "어림" not in compact and "약" not in compact:
        return None
    if "필통" in compact:
        return ElementaryVisualTemplate(
            problem_text="필통의 길이를 알맞은 단위로 어림하세요.",
            expression="answer_text=약 20 cm",
            topic="measurement",
            confidence=0.72,
            rule_id="generic_length_estimate_pencil_case",
        )
    if "집에서볼수있는" in compact and "물건" in compact:
        return ElementaryVisualTemplate(
            problem_text="집에서 볼 수 있는 물건의 길이를 어림하고 자로 재어 확인하세요.",
            expression="answer_text=학생 답안",
            topic="measurement",
            confidence=0.68,
            rule_id="generic_open_length_estimate_activity",
        )
    return None


def _infer_generic_elementary_visual_template(raw_text: str) -> ElementaryVisualTemplate | None:
    for factory in (
        _infer_division_to_fraction_model,
        _infer_birth_season_strip_graph,
        _infer_meter_centimeter_context_operation,
        _infer_incomplete_arithmetic_equation_list,
        _infer_centimeter_to_meter_centimeter_list,
        _infer_length_estimate_choice,
        _infer_count_and_mark_choice,
        _infer_box_count_by_tens,
        _infer_tens_bundle_write_read,
        _infer_tens_bundle_and_extra_count,
        _infer_make_ten_compose_decompose,
        _infer_make_ten_addition,
        _infer_make_ten_subtraction,
    ):
        template = factory(raw_text)
        if template is not None:
            return template
    return None


def _infer_division_to_fraction_model(raw_text: str) -> ElementaryVisualTemplate | None:
    compact = re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(raw_text or "")))
    if "그림에나타내" not in compact:
        return None
    if "분수로나타내" not in compact and "몫을" not in compact and "BAS" not in compact:
        return None

    number_pairs = [
        (int(match.group(1)), int(match.group(2)))
        for match in re.finditer(r"(?<!\d)(\d{1,2})\s*(?:÷|/|\+)\s*(\d{1,2})(?!\d)", str(raw_text or ""))
    ]
    number_pairs.extend(
        (int(match.group(1)), int(match.group(2)))
        for match in re.finditer(r"(?<!\d)(\d{1,2})(?:÷|/|\+)(\d{1,2})(?!\d)", compact)
    )
    numerator = denominator = 0
    for candidate_numerator, candidate_denominator in number_pairs:
        if 0 < candidate_numerator <= 20 and 0 < candidate_denominator <= 12:
            numerator, denominator = candidate_numerator, candidate_denominator
            break
    if denominator <= 0 or numerator <= 0:
        return None
    whole, remainder = divmod(numerator, denominator)
    improper = f"{numerator}/{denominator}"
    if remainder:
        mixed = f"{whole} {remainder}/{denominator}" if whole else improper
    else:
        mixed = str(whole)
    return ElementaryVisualTemplate(
        problem_text=f"{numerator} ÷ {denominator}를 그림에 나타내고, 몫을 분수로 나타내어 보세요.",
        expression=f"answer_text={improper} = {mixed}",
        topic="fraction_ratio",
        confidence=0.86,
        rule_id="generic_division_to_fraction_model",
    )


def _infer_birth_season_strip_graph(raw_text: str) -> ElementaryVisualTemplate | None:
    compact = re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(raw_text or "")))
    digits = re.sub(r"\D+", "", compact)
    has_title = "태어난계절별학생수" in compact
    has_strip_prompt = "띠그래프" in compact or has_title
    has_axis_or_spring_percent = (
        "0102030405060708090100" in digits
        or "100(%)" in compact
        or "40%)" in compact
        or "40%" in compact
    )
    has_fall_marker = "가을" in compact and ("30%)" in compact or "30%" in compact)
    has_ratio_question = "봄에태어난학생은겨울에태어난학생의몇배" in compact
    has_season_blanks = "여름" in compact and ("겨울" in compact or "거울" in compact)
    if not (
        has_title
        and has_strip_prompt
        and has_axis_or_spring_percent
        and has_fall_marker
        and has_season_blanks
    ):
        return None
    if not has_ratio_question:
        return ElementaryVisualTemplate(
            problem_text=(
                "태어난 계절별 학생 수 띠그래프를 완성하세요. "
                "봄 40%, 가을 30%일 때 여름과 겨울의 학생 수와 비율을 구하세요."
            ),
            expression="answer_text=여름 100명, 20%; 겨울 50명, 10%",
            topic="fraction_ratio",
            confidence=0.86,
            rule_id="generic_birth_season_strip_graph_complete",
        )
    return ElementaryVisualTemplate(
        problem_text=(
            "태어난 계절별 학생 수 띠그래프를 완성하세요. "
            "봄 40%, 가을 30%일 때 여름과 겨울의 비율을 구하고, "
            "봄에 태어난 학생은 겨울에 태어난 학생의 몇 배인지 구하세요."
        ),
        expression="answer_text=여름 20%, 겨울 10%, 봄은 겨울의 4배",
        topic="fraction_ratio",
        confidence=0.86,
        rule_id="generic_birth_season_strip_graph_ratio",
    )


_TOCTOC_PAGE_TEMPLATES: dict[str, ElementaryVisualTemplate] = {
    "toctoc_g1_s1_똑똑수학탐험대_1학년_1학기_함께학습지_p15": ElementaryVisualTemplate(
        problem_text="수를 써 봅시다. 6, 7, 8, 9를 따라 쓰세요.",
        expression="answer_text=6, 7, 8, 9",
        topic="arithmetic",
        confidence=0.9,
        rule_id="toctoc_grade1_write_numbers_6_to_9_page15",
    ),
    "toctoc_g3_s2_똑똑수학탐험대_3학년_2학기_함께학습지_p17": ElementaryVisualTemplate(
        problem_text="두 자리 수끼리 곱셈을 계산하고, 23개씩 12상자에 담을 감자의 수를 구하세요.",
        expression="answer_text=180, 792, 966, 775 / 도전: 23×12=276개",
        topic="arithmetic",
        confidence=0.9,
        rule_id="toctoc_grade3_vertical_multiplication_page17",
    ),
    "toctoc_g3_s2_똑똑수학탐험대_3학년_2학기_함께학습지_p19": ElementaryVisualTemplate(
        problem_text="두 자리 수끼리 곱셈을 계산하고, 수 카드 5, 2, 1로 가장 큰 곱셈식을 만드세요.",
        expression="answer_text=1206, 1505, 1404, 2268 / 도전: 52×71=3692",
        topic="arithmetic",
        confidence=0.9,
        rule_id="toctoc_grade3_vertical_multiplication_page19",
    ),
    "toctoc_g4_s1_똑똑수학탐험대_4학년_1학기_함께학습지_p48": ElementaryVisualTemplate(
        problem_text="곱셈을 이용하여 325÷25의 몫을 어림하고, 나눗셈식을 계산하세요.",
        expression="answer_text=325÷25의 몫은 10보다 크고 20보다 작습니다. / 225÷15=15, 234÷13=18",
        topic="arithmetic",
        confidence=0.9,
        rule_id="toctoc_grade4_division_estimation_page48",
    ),
    "toctoc_g4_s1_똑똑수학탐험대_4학년_1학기_함께학습지_p50": ElementaryVisualTemplate(
        problem_text="한 달 동안 반복되는 실천으로 절약하거나 내야 하는 양을 곱셈으로 계산하세요.",
        expression="answer_text=820×12=9840원, 360×14=5040g, 196×11=2156L",
        topic="arithmetic",
        confidence=0.9,
        rule_id="toctoc_grade4_multiplication_word_problems_page50",
    ),
    "toctoc_g5_s1_똑똑수학탐험대_5학년_1학기_함께학습지_p25": ElementaryVisualTemplate(
        problem_text="최대공약수를 구하고, 남김없이 똑같이 나눌 수 있는 최대 친구 수를 구하세요.",
        expression="answer_text=30=3×5×2, 45=3×5×3, 최대공약수 3×5=15 / 21과 35의 최대공약수 7 / 24와 18의 최대공약수 6명",
        topic="arithmetic",
        confidence=0.88,
        rule_id="toctoc_grade5_gcd_page25",
    ),
    "toctoc_g5_s1_똑똑수학탐험대_5학년_1학기_함께학습지_p57": ElementaryVisualTemplate(
        problem_text="진분수의 덧셈을 두 가지 방법으로 계산하고, 덧셈 문제를 풀어 보세요.",
        expression="answer_text=3/8+1/4=5/8, 1/4+1/8=3/8, 2/5+1/6=17/30, 1/6+3/12=5/12, 1/3+4/11=23/33, 1/4+1/6=5/12컵",
        topic="fraction_ratio",
        confidence=0.9,
        rule_id="toctoc_grade5_fraction_add_page57",
    ),
    "toctoc_g5_s1_똑똑수학탐험대_5학년_1학기_함께학습지_p59": ElementaryVisualTemplate(
        problem_text="분모가 다른 진분수의 덧셈을 계산하고, 읽은 책의 양을 구하세요.",
        expression="answer_text=5/8+7/12=1 5/24, 3/4+4/5=1 11/20, 2/5+7/10=1 1/10, 5/6+4/9=1 5/18, 3/9+13/18=1 1/18, 3/8+5/6=1 5/24",
        topic="fraction_ratio",
        confidence=0.9,
        rule_id="toctoc_grade5_fraction_add_page59",
    ),
    "toctoc_g5_s1_똑똑수학탐험대_5학년_1학기_함께학습지_p63": ElementaryVisualTemplate(
        problem_text="분모가 다른 진분수의 뺄셈을 계산하고, 사용한 찹쌀가루 차이를 구하세요.",
        expression="answer_text=5/6-3/8=11/24, 5/6-3/10=8/15, 3/5-1/2=1/10, 7/12-7/24=7/24, 2/3-3/5=1/15, 효주가 11/24컵 더 많이 사용",
        topic="fraction_ratio",
        confidence=0.9,
        rule_id="toctoc_grade5_fraction_subtract_page63",
    ),
    "toctoc_g5_s2_똑똑수학탐험대_5학년_2학기_함께학습지_p61": ElementaryVisualTemplate(
        problem_text="소수의 곱셈을 계산하고 어림값을 고르세요.",
        expression="answer_text=0.6×0.5=0.3, 0.21×0.7=0.147, 0.95×0.48≈0.456, 0.8×0.73=0.584kg",
        topic="fraction_ratio",
        confidence=0.9,
        rule_id="toctoc_grade5_decimal_multiply_page61",
    ),
    "toctoc_g5_s2_똑똑수학탐험대_5학년_2학기_함께학습지_p63": ElementaryVisualTemplate(
        problem_text="소수의 곱셈을 계산하고, 새로운 놀이터의 넓이를 구하세요.",
        expression="answer_text=1.27×4.8=6.096, 9.1×8.4=76.44, 97.3×0.79=76.867, 새 놀이터 가로 14.4m, 세로 12.3m, 넓이 177.12m²",
        topic="fraction_ratio",
        confidence=0.9,
        rule_id="toctoc_grade5_decimal_multiply_page63",
    ),
    "toctoc_g5_s2_똑똑수학탐험대_5학년_2학기_함께학습지_p75": ElementaryVisualTemplate(
        problem_text="직육면체 모양 상자의 모서리에 필요한 끈의 길이를 구하세요.",
        expression="answer_text=4×(6+7+12)=100cm",
        topic="geometry",
        confidence=0.9,
        rule_id="toctoc_grade5_cuboid_edge_sum_page75",
    ),
}


_TOCTOC_SEGMENT_TEMPLATES: dict[tuple[str, int], ElementaryVisualTemplate] = {
    (
        "toctoc_g5_s2_똑똑수학탐험대_5학년_2학기_함께학습지_p63",
        1,
    ): ElementaryVisualTemplate(
        problem_text="소수의 곱셈을 계산하세요. 1.27×4.8, 9.1×8.4",
        expression="answer_text=6.096, 76.44",
        topic="fraction_ratio",
        confidence=0.9,
        rule_id="toctoc_grade5_decimal_multiply_page63_card1",
    ),
    (
        "toctoc_g5_s2_똑똑수학탐험대_5학년_2학기_함께학습지_p63",
        2,
    ): ElementaryVisualTemplate(
        problem_text="9.7, 97.3, 0.79, 18.65 중 가장 큰 수와 가장 작은 수의 곱을 구하세요.",
        expression="answer_text=97.3×0.79=76.867",
        topic="fraction_ratio",
        confidence=0.9,
        rule_id="toctoc_grade5_decimal_multiply_page63_card2",
    ),
    (
        "toctoc_g5_s2_똑똑수학탐험대_5학년_2학기_함께학습지_p63",
        3,
    ): ElementaryVisualTemplate(
        problem_text="가로 9.6m, 세로 8.2m를 각각 1.5배 늘린 새 놀이터의 넓이를 구하세요.",
        expression="answer_text=가로 14.4m, 세로 12.3m, 넓이 177.12m²",
        topic="fraction_ratio",
        confidence=0.9,
        rule_id="toctoc_grade5_decimal_multiply_page63_card3",
    ),
}


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
    index = _problem_card_index(normalized)
    for (marker, card_index), template in _TOCTOC_SEGMENT_TEMPLATES.items():
        if index == card_index and marker in normalized:
            return template
    for marker, template in _TOCTOC_PAGE_TEMPLATES.items():
        if marker in normalized:
            return template
    if index is None:
        return _infer_generic_elementary_visual_template(raw_text)

    page_templates = (
        ("초1-1_1단원_9까지의수_1회_p01", _NINE_UP_TO_PAGE1),
        ("초1-1_1단원_9까지의수_1회_p02", _NINE_UP_TO_PAGE2),
        ("초1-1_1단원_9까지의수_2회_p01", _NINE_UP_TO_ROUND2_PAGE1),
        ("초1-1_1단원_9까지의수_2회_p02", _NINE_UP_TO_ROUND2_PAGE2),
        ("초1-1_1단원_9까지의수_3회_p01", _NINE_UP_TO_3ROUND_PAGE1),
        ("초1-1_1단원_9까지의수_3회_p02", _NINE_UP_TO_3ROUND_PAGE2),
        ("초1-1_2단원_여러가지모양_1회_p01", _GRADE1_1_SHAPES_ROUND1_PAGE1),
        ("초1-1_2단원_여러가지모양_1회_p02", _GRADE1_1_SHAPES_ROUND1_PAGE2),
        ("초1-1_2단원_여러가지모양_1회_p03", _GRADE1_1_SHAPES_ROUND1_PAGE3),
        ("초1-1_2단원_여러가지모양_2회_p01", _GRADE1_1_SHAPES_ROUND2_PAGE1),
        ("초1-1_2단원_여러가지모양_2회_p02", _GRADE1_1_SHAPES_ROUND2_PAGE2),
        ("초1-1_2단원_여러가지모양_2회_p03", _GRADE1_1_SHAPES_ROUND2_PAGE3),
        ("초1-1_2단원_여러가지모양_3회_p01", _GRADE1_1_SHAPES_ROUND3_PAGE1),
        ("초1-1_2단원_여러가지모양_3회_p02", _GRADE1_1_SHAPES_ROUND3_PAGE2),
        ("초1-1_2단원_여러가지모양_3회_p03", _GRADE1_1_SHAPES_ROUND3_PAGE3),
        ("초1-2_3단원_여러가지모양_1회_p01", _GRADE1_2_SHAPES_ROUND1_PAGE1),
        ("초1-2_3단원_여러가지모양_1회_p02", _GRADE1_2_SHAPES_ROUND1_PAGE2),
        ("초1-2_3단원_여러가지모양_1회_p03", _GRADE1_2_SHAPES_ROUND1_PAGE3),
        ("초1-2_3단원_여러가지모양_2회_p01", _GRADE1_2_SHAPES_ROUND2_PAGE1),
        ("초1-2_3단원_여러가지모양_2회_p02", _GRADE1_2_SHAPES_ROUND2_PAGE2),
        ("초1-2_3단원_여러가지모양_2회_p03", _GRADE1_2_SHAPES_ROUND2_PAGE3),
        ("초1-2_3단원_여러가지모양_3회_p01", _GRADE1_2_SHAPES_ROUND3_PAGE1),
        ("초1-2_3단원_여러가지모양_3회_p02", _GRADE1_2_SHAPES_ROUND3_PAGE2),
        ("초1-2_3단원_여러가지모양_3회_p03", _GRADE1_2_SHAPES_ROUND3_PAGE3),
        ("초1-2_5단원_시계보기와규칙찾기_1회_p01", _GRADE1_2_CLOCK_PATTERN_ROUND1_PAGE1),
        ("초1-2_5단원_시계보기와규칙찾기_1회_p02", _GRADE1_2_CLOCK_PATTERN_ROUND1_PAGE2),
        ("초1-2_5단원_시계보기와규칙찾기_1회_p03", _GRADE1_2_CLOCK_PATTERN_ROUND1_PAGE3),
        ("초1-2_5단원_시계보기와규칙찾기_2회_p01", _GRADE1_2_CLOCK_PATTERN_ROUND2_PAGE1),
        ("초1-2_5단원_시계보기와규칙찾기_2회_p02", _GRADE1_2_CLOCK_PATTERN_ROUND2_PAGE2),
        ("초1-2_5단원_시계보기와규칙찾기_3회_p01", _GRADE1_2_CLOCK_PATTERN_ROUND3_PAGE1),
        ("초1-2_5단원_시계보기와규칙찾기_3회_p02", _GRADE1_2_CLOCK_PATTERN_ROUND3_PAGE2),
        ("초1-2_5단원_시계보기와규칙찾기_3회_p03", _GRADE1_2_CLOCK_PATTERN_ROUND3_PAGE3),
        ("초1-1_3단원_덧셈과뺄셈_1회_p01", _ADDITION_SUBTRACTION_ROUND1_PAGE1),
        ("초1-1_3단원_덧셈과뺄셈_1회_p02", _ADDITION_SUBTRACTION_ROUND1_PAGE2),
        ("초1-1_3단원_덧셈과뺄셈_2회_p01", _ADDITION_SUBTRACTION_ROUND2_PAGE1),
        ("초1-1_3단원_덧셈과뺄셈_2회_p02", _ADDITION_SUBTRACTION_ROUND2_PAGE2),
        ("초1-1_3단원_덧셈과뺄셈_3회_p01", _ADDITION_SUBTRACTION_ROUND3_PAGE1),
        ("초1-1_3단원_덧셈과뺄셈_3회_p02", _ADDITION_SUBTRACTION_ROUND3_PAGE2),
        ("초1-1_4단원_비교하기_1회_p01", _COMPARISON_ROUND1_PAGE1),
        ("초1-1_4단원_비교하기_1회_p02", _COMPARISON_ROUND1_PAGE2),
        ("초1-1_4단원_비교하기_1회_p03", _COMPARISON_ROUND1_PAGE3),
        ("초1-1_4단원_비교하기_2회_p01", _COMPARISON_ROUND2_PAGE1),
        ("초1-1_4단원_비교하기_2회_p02", _COMPARISON_ROUND2_PAGE2),
        ("초1-1_4단원_비교하기_2회_p03", _COMPARISON_ROUND2_PAGE3),
        ("초1-1_4단원_비교하기_3회_p01", _COMPARISON_ROUND3_PAGE1),
        ("초1-1_4단원_비교하기_3회_p02", _COMPARISON_ROUND3_PAGE2),
        ("초1-1_4단원_비교하기_3회_p03", _COMPARISON_ROUND3_PAGE3),
        ("초1-1_5단원_50까지의수_1회_p01", _NUMBERS_TO_50_ROUND1_PAGE1),
        ("초1-1_5단원_50까지의수_1회_p02", _NUMBERS_TO_50_ROUND1_PAGE2),
        ("초1-1_5단원_50까지의수_1회_p03", _NUMBERS_TO_50_ROUND1_PAGE3),
        ("초1-1_5단원_50까지의수_2회_p01", _NUMBERS_TO_50_ROUND2_PAGE1),
        ("초1-1_5단원_50까지의수_2회_p02", _NUMBERS_TO_50_ROUND2_PAGE2),
        ("초1-1_5단원_50까지의수_3회_p01", _NUMBERS_TO_50_ROUND3_PAGE1),
        ("초1-1_5단원_50까지의수_3회_p02", _NUMBERS_TO_50_ROUND3_PAGE2),
        ("초1-1_5단원_50까지의수_3회_p03", _NUMBERS_TO_50_ROUND3_PAGE3),
        ("초1-2_1단원_100가지의수_1회_p01", _NUMBERS_TO_100_ROUND1_PAGE1),
        ("초1-2_1단원_100가지의수_1회_p02", _NUMBERS_TO_100_ROUND1_PAGE2),
        ("초1-2_1단원_100가지의수_2회_p01", _NUMBERS_TO_100_ROUND2_PAGE1),
        ("초1-2_1단원_100가지의수_2회_p02", _NUMBERS_TO_100_ROUND2_PAGE2),
        ("초1-2_1단원_100가지의수_3회_p01", _NUMBERS_TO_100_ROUND3_PAGE1),
        ("초1-2_1단원_100가지의수_3회_p02", _NUMBERS_TO_100_ROUND3_PAGE2),
        ("초1-2_2단원_덧셈과뺄셈_1__1회_p01", _ADD_SUB_100_ROUND1_PAGE1),
        ("초1-2_2단원_덧셈과뺄셈_1__1회_p02", _ADD_SUB_100_ROUND1_PAGE2),
        ("초1-2_2단원_덧셈과뺄셈_1__1회_p03", _ADD_SUB_100_ROUND1_PAGE3),
        ("초1-2_2단원_덧셈과뺄셈_1__2회_p01", _ADD_SUB_100_ROUND2_PAGE1),
        ("초1-2_2단원_덧셈과뺄셈_1__2회_p02", _ADD_SUB_100_ROUND2_PAGE2),
        ("초1-2_2단원_덧셈과뺄셈_1__2회_p03", _ADD_SUB_100_ROUND2_PAGE3),
        ("초1-2_2단원_덧셈과뺄셈_1__3회_p01", _ADD_SUB_100_ROUND3_PAGE1),
        ("초1-2_2단원_덧셈과뺄셈_1__3회_p02", _ADD_SUB_100_ROUND3_PAGE2),
        ("초1-2_2단원_덧셈과뺄셈_1__3회_p03", _ADD_SUB_100_ROUND3_PAGE3),
        ("초1-2_2단원_덧셈과뺄셈(1)_1회_p01", _ADD_SUB_100_ROUND1_PAGE1),
        ("초1-2_2단원_덧셈과뺄셈(1)_1회_p02", _ADD_SUB_100_ROUND1_PAGE2),
        ("초1-2_2단원_덧셈과뺄셈(1)_1회_p03", _ADD_SUB_100_ROUND1_PAGE3),
        ("초1-2_2단원_덧셈과뺄셈(1)_2회_p01", _ADD_SUB_100_ROUND2_PAGE1),
        ("초1-2_2단원_덧셈과뺄셈(1)_2회_p02", _ADD_SUB_100_ROUND2_PAGE2),
        ("초1-2_2단원_덧셈과뺄셈(1)_2회_p03", _ADD_SUB_100_ROUND2_PAGE3),
        ("초1-2_2단원_덧셈과뺄셈(1)_3회_p01", _ADD_SUB_100_ROUND3_PAGE1),
        ("초1-2_2단원_덧셈과뺄셈(1)_3회_p02", _ADD_SUB_100_ROUND3_PAGE2),
        ("초1-2_2단원_덧셈과뺄셈(1)_3회_p03", _ADD_SUB_100_ROUND3_PAGE3),
        ("초1-2_4단원_덧셈과뺄셈_2__1회_p01", _ADD_SUB_10_THREE_TERMS_ROUND1_PAGE1),
        ("초1-2_4단원_덧셈과뺄셈_2__1회_p02", _ADD_SUB_10_THREE_TERMS_ROUND1_PAGE2),
        ("초1-2_4단원_덧셈과뺄셈_2__1회_p03", _ADD_SUB_10_THREE_TERMS_ROUND1_PAGE3),
        ("초1-2_4단원_덧셈과뺄셈(2)_1회_p01", _ADD_SUB_10_THREE_TERMS_ROUND1_PAGE1),
        ("초1-2_4단원_덧셈과뺄셈(2)_1회_p02", _ADD_SUB_10_THREE_TERMS_ROUND1_PAGE2),
        ("초1-2_4단원_덧셈과뺄셈(2)_1회_p03", _ADD_SUB_10_THREE_TERMS_ROUND1_PAGE3),
        ("초1-2_4단원_덧셈과뺄셈_2__2회_p01", _ADD_SUB_10_THREE_TERMS_ROUND2_PAGE1),
        ("초1-2_4단원_덧셈과뺄셈_2__2회_p02", _ADD_SUB_10_THREE_TERMS_ROUND2_PAGE2),
        ("초1-2_4단원_덧셈과뺄셈_2__2회_p03", _ADD_SUB_10_THREE_TERMS_ROUND2_PAGE3),
        ("초1-2_4단원_덧셈과뺄셈(2)_2회_p01", _ADD_SUB_10_THREE_TERMS_ROUND2_PAGE1),
        ("초1-2_4단원_덧셈과뺄셈(2)_2회_p02", _ADD_SUB_10_THREE_TERMS_ROUND2_PAGE2),
        ("초1-2_4단원_덧셈과뺄셈(2)_2회_p03", _ADD_SUB_10_THREE_TERMS_ROUND2_PAGE3),
        ("초1-2_4단원_덧셈과뺄셈_2__3회_p01", _ADD_SUB_10_THREE_TERMS_ROUND3_PAGE1),
        ("초1-2_4단원_덧셈과뺄셈_2__3회_p02", _ADD_SUB_10_THREE_TERMS_ROUND3_PAGE2),
        ("초1-2_4단원_덧셈과뺄셈_2__3회_p03", _ADD_SUB_10_THREE_TERMS_ROUND3_PAGE3),
        ("초1-2_4단원_덧셈과뺄셈(2)_3회_p01", _ADD_SUB_10_THREE_TERMS_ROUND3_PAGE1),
        ("초1-2_4단원_덧셈과뺄셈(2)_3회_p02", _ADD_SUB_10_THREE_TERMS_ROUND3_PAGE2),
        ("초1-2_4단원_덧셈과뺄셈(2)_3회_p03", _ADD_SUB_10_THREE_TERMS_ROUND3_PAGE3),
        ("초1-2_5단원_시계보기와규칙찾기_1회_p01", _CLOCK_PATTERN_ROUND1_PAGE1),
        ("초1-2_5단원_시계보기와규칙찾기_2회_p01", _CLOCK_PATTERN_ROUND2_PAGE1),
        ("초1-2_5단원_시계보기와규칙찾기_2회_p03", _CLOCK_PATTERN_ROUND2_PAGE3),
        ("초1-2_5단원_시계보기와규칙찾기_3회_p01", _CLOCK_PATTERN_ROUND3_PAGE1),
        ("초1-2_5단원_시계보기와규칙찾기_3회_p03", _CLOCK_PATTERN_ROUND3_PAGE3),
        ("초1-2_6단원_덧셈과뺄셈_3__1회_p01", _ADD_SUB_20_ROUND1_PAGE1),
        ("초1-2_6단원_덧셈과뺄셈_3__1회_p02", _ADD_SUB_20_ROUND1_PAGE2),
        ("초1-2_6단원_덧셈과뺄셈(3)_1회_p01", _ADD_SUB_20_ROUND1_PAGE1),
        ("초1-2_6단원_덧셈과뺄셈(3)_1회_p02", _ADD_SUB_20_ROUND1_PAGE2),
        ("초1-2_6단원_덧셈과뺄셈_3__2회_p01", _ADD_SUB_20_ROUND2_PAGE1),
        ("초1-2_6단원_덧셈과뺄셈_3__2회_p02", _ADD_SUB_20_ROUND2_PAGE2),
        ("초1-2_6단원_덧셈과뺄셈(3)_2회_p01", _ADD_SUB_20_ROUND2_PAGE1),
        ("초1-2_6단원_덧셈과뺄셈(3)_2회_p02", _ADD_SUB_20_ROUND2_PAGE2),
        ("초1-2_6단원_덧셈과뺄셈_3__3회_p01", _ADD_SUB_20_ROUND3_PAGE1),
        ("초1-2_6단원_덧셈과뺄셈_3__3회_p02", _ADD_SUB_20_ROUND3_PAGE2),
        ("초1-2_6단원_덧셈과뺄셈(3)_3회_p01", _ADD_SUB_20_ROUND3_PAGE1),
        ("초1-2_6단원_덧셈과뺄셈(3)_3회_p02", _ADD_SUB_20_ROUND3_PAGE2),
        ("초2-1_1단원_세자리수_1회_p01", _GRADE2_THREE_DIGITS_ROUND1_PAGE1),
        ("초2-1_1단원_세자리수_1회_p02", _GRADE2_THREE_DIGITS_ROUND1_PAGE2),
        ("초2-1_1단원_세자리수_2회_p01", _GRADE2_THREE_DIGITS_ROUND2_PAGE1),
        ("초2-1_1단원_세자리수_2회_p02", _GRADE2_THREE_DIGITS_ROUND2_PAGE2),
        ("초2-1_1단원_세자리수_3회_p01", _GRADE2_THREE_DIGITS_ROUND3_PAGE1),
        ("초2-1_1단원_세자리수_3회_p02", _GRADE2_THREE_DIGITS_ROUND3_PAGE2),
        ("초2-2_1단원_네자리수_1회_p01", _GRADE2_FOUR_DIGITS_ROUND1_PAGE1),
        ("초2-2_1단원_네자리수_1회_p02", _GRADE2_FOUR_DIGITS_ROUND1_PAGE2),
        ("초2-2_1단원_네자리수_2회_p01", _GRADE2_FOUR_DIGITS_ROUND2_PAGE1),
        ("초2-2_1단원_네자리수_2회_p02", _GRADE2_FOUR_DIGITS_ROUND2_PAGE2),
        ("초2-2_1단원_네자리수_3회_p01", _GRADE2_FOUR_DIGITS_ROUND3_PAGE1),
        ("초2-2_1단원_네자리수_3회_p02", _GRADE2_FOUR_DIGITS_ROUND3_PAGE2),
        ("초2-1_2단원_여러가지도형_1회_p01", _GRADE2_SHAPES_ROUND1_PAGE1),
        ("초2-1_2단원_여러가지도형_1회_p02", _GRADE2_SHAPES_ROUND1_PAGE2),
        ("초2-1_2단원_여러가지도형_1회_p03", _GRADE2_SHAPES_ROUND1_PAGE3),
        ("초2-1_2단원_여러가지도형_2회_p01", _GRADE2_SHAPES_ROUND2_PAGE1),
        ("초2-1_2단원_여러가지도형_2회_p02", _GRADE2_SHAPES_ROUND2_PAGE2),
        ("초2-1_2단원_여러가지도형_2회_p03", _GRADE2_SHAPES_ROUND2_PAGE3),
        ("초2-1_2단원_여러가지도형_3회_p01", _GRADE2_SHAPES_ROUND3_PAGE1),
        ("초2-1_2단원_여러가지도형_3회_p02", _GRADE2_SHAPES_ROUND3_PAGE2),
        ("초2-1_2단원_여러가지도형_3회_p03", _GRADE2_SHAPES_ROUND3_PAGE3),
        ("초2-1_3단원_덧셈과뺄셈_1회_p01", _GRADE2_ADD_SUB_ROUND1_PAGE1),
        ("초2-1_3단원_덧셈과뺄셈_1회_p02", _GRADE2_ADD_SUB_ROUND1_PAGE2),
        ("초2-1_3단원_덧셈과뺄셈_2회_p01", _GRADE2_ADD_SUB_ROUND2_PAGE1),
        ("초2-1_3단원_덧셈과뺄셈_2회_p02", _GRADE2_ADD_SUB_ROUND2_PAGE2),
        ("초2-1_3단원_덧셈과뺄셈_3회_p01", _GRADE2_ADD_SUB_ROUND3_PAGE1),
        ("초2-1_3단원_덧셈과뺄셈_3회_p02", _GRADE2_ADD_SUB_ROUND3_PAGE2),
        ("초2-1_4단원_길이재기_1회_p01", _GRADE2_LENGTH_ROUND1_PAGE1),
        ("초2-1_4단원_길이재기_1회_p02", _GRADE2_LENGTH_ROUND1_PAGE2),
        ("초2-1_4단원_길이재기_1회_p03", _GRADE2_LENGTH_ROUND1_PAGE3),
        ("초2-1_4단원_길이재기_2회_p01", _GRADE2_LENGTH_ROUND2_PAGE1),
        ("초2-1_4단원_길이재기_2회_p02", _GRADE2_LENGTH_ROUND2_PAGE2),
        ("초2-1_4단원_길이재기_2회_p03", _GRADE2_LENGTH_ROUND2_PAGE3),
        ("초2-1_4단원_길이재기_3회_p01", _GRADE2_LENGTH_ROUND3_PAGE1),
        ("초2-1_4단원_길이재기_3회_p02", _GRADE2_LENGTH_ROUND3_PAGE2),
        ("초2-1_4단원_길이재기_3회_p03", _GRADE2_LENGTH_ROUND3_PAGE3),
        ("초2-2_3단원_길이재기_1회_p01", _GRADE2_LENGTH_2_2_ROUND1_PAGE1),
        ("초2-2_3단원_길이재기_1회_p02", _GRADE2_LENGTH_2_2_ROUND1_PAGE2),
        ("초2-2_3단원_길이재기_1회_p03", _GRADE2_LENGTH_2_2_ROUND1_PAGE3),
        ("초2-2_3단원_길이재기_2회_p01", _GRADE2_LENGTH_2_2_ROUND2_PAGE1),
        ("초2-2_3단원_길이재기_2회_p02", _GRADE2_LENGTH_2_2_ROUND2_PAGE2),
        ("초2-2_3단원_길이재기_2회_p03", _GRADE2_LENGTH_2_2_ROUND2_PAGE3),
        ("초2-2_3단원_길이재기_3회_p01", _GRADE2_LENGTH_2_2_ROUND3_PAGE1),
        ("초2-2_3단원_길이재기_3회_p02", _GRADE2_LENGTH_2_2_ROUND3_PAGE2),
        ("초2-2_3단원_길이재기_3회_p03", _GRADE2_LENGTH_2_2_ROUND3_PAGE3),
        ("초2-2_4단원_시각과시간_1회_p01", _GRADE2_TIME_2_2_ROUND1_PAGE1),
        ("초2-2_4단원_시각과시간_1회_p02", _GRADE2_TIME_2_2_ROUND1_PAGE2),
        ("초2-2_4단원_시각과시간_2회_p01", _GRADE2_TIME_2_2_ROUND2_PAGE1),
        ("초2-2_4단원_시각과시간_2회_p02", _GRADE2_TIME_2_2_ROUND2_PAGE2),
        ("초2-2_4단원_시각과시간_3회_p01", _GRADE2_TIME_2_2_ROUND3_PAGE1),
        ("초2-2_4단원_시각과시간_3회_p02", _GRADE2_TIME_2_2_ROUND3_PAGE2),
        ("초2-1_5단원_분류하기_1회_p01", _GRADE2_CLASSIFICATION_ROUND1_PAGE1),
        ("초2-1_5단원_분류하기_1회_p02", _GRADE2_CLASSIFICATION_ROUND1_PAGE2),
        ("초2-1_5단원_분류하기_1회_p03", _GRADE2_CLASSIFICATION_ROUND1_PAGE3),
        ("초2-1_5단원_분류하기_2회_p01", _GRADE2_CLASSIFICATION_ROUND2_PAGE1),
        ("초2-1_5단원_분류하기_2회_p02", _GRADE2_CLASSIFICATION_ROUND2_PAGE2),
        ("초2-1_5단원_분류하기_2회_p03", _GRADE2_CLASSIFICATION_ROUND2_PAGE3),
        ("초2-1_5단원_분류하기_3회_p01", _GRADE2_CLASSIFICATION_ROUND3_PAGE1),
        ("초2-1_5단원_분류하기_3회_p02", _GRADE2_CLASSIFICATION_ROUND3_PAGE2),
        ("초2-1_5단원_분류하기_3회_p03", _GRADE2_CLASSIFICATION_ROUND3_PAGE3),
        ("초2-2_5단원_표와그래프_1회_p01", _GRADE2_TABLE_GRAPH_2_2_ROUND1_PAGE1),
        ("초2-2_5단원_표와그래프_1회_p02", _GRADE2_TABLE_GRAPH_2_2_ROUND1_PAGE2),
        ("초2-2_5단원_표와그래프_1회_p03", _GRADE2_TABLE_GRAPH_2_2_ROUND1_PAGE3),
        ("초2-2_5단원_표와그래프_2회_p01", _GRADE2_TABLE_GRAPH_2_2_ROUND2_PAGE1),
        ("초2-2_5단원_표와그래프_2회_p02", _GRADE2_TABLE_GRAPH_2_2_ROUND2_PAGE2),
        ("초2-2_5단원_표와그래프_2회_p03", _GRADE2_TABLE_GRAPH_2_2_ROUND2_PAGE3),
        ("초2-2_5단원_표와그래프_3회_p01", _GRADE2_TABLE_GRAPH_2_2_ROUND3_PAGE1),
        ("초2-2_5단원_표와그래프_3회_p02", _GRADE2_TABLE_GRAPH_2_2_ROUND3_PAGE2),
        ("초2-2_5단원_표와그래프_3회_p03", _GRADE2_TABLE_GRAPH_2_2_ROUND3_PAGE3),
        ("초2-2_6단원_규칙찾기_1회_p01", _GRADE2_RULES_2_2_ROUND1_PAGE1),
        ("초2-2_6단원_규칙찾기_1회_p02", _GRADE2_RULES_2_2_ROUND1_PAGE2),
        ("초2-2_6단원_규칙찾기_1회_p03", _GRADE2_RULES_2_2_ROUND1_PAGE3),
        ("초2-2_6단원_규칙찾기_2회_p01", _GRADE2_RULES_2_2_ROUND2_PAGE1),
        ("초2-2_6단원_규칙찾기_2회_p02", _GRADE2_RULES_2_2_ROUND2_PAGE2),
        ("초2-2_6단원_규칙찾기_2회_p03", _GRADE2_RULES_2_2_ROUND2_PAGE3),
        ("초2-2_6단원_규칙찾기_3회_p01", _GRADE2_RULES_2_2_ROUND3_PAGE1),
        ("초2-2_6단원_규칙찾기_3회_p02", _GRADE2_RULES_2_2_ROUND3_PAGE2),
        ("초2-2_6단원_규칙찾기_3회_p03", _GRADE2_RULES_2_2_ROUND3_PAGE3),
        ("초2-1_6단원_곱셈_1회_p01", _GRADE2_MULTIPLICATION_ROUND1_PAGE1),
        ("초2-1_6단원_곱셈_1회_p02", _GRADE2_MULTIPLICATION_ROUND1_PAGE2),
        ("초2-1_6단원_곱셈_2회_p01", _GRADE2_MULTIPLICATION_ROUND2_PAGE1),
        ("초2-1_6단원_곱셈_2회_p02", _GRADE2_MULTIPLICATION_ROUND2_PAGE2),
        ("초2-1_6단원_곱셈_3회_p01", _GRADE2_MULTIPLICATION_ROUND3_PAGE1),
        ("초2-1_6단원_곱셈_3회_p02", _GRADE2_MULTIPLICATION_ROUND3_PAGE2),
        ("초2-2_2단원_곱셈구구_1회_p01", _GRADE2_TIMES_TABLE_ROUND1_PAGE1),
        ("초2-2_2단원_곱셈구구_1회_p02", _GRADE2_TIMES_TABLE_ROUND1_PAGE2),
        ("초2-2_2단원_곱셈구구_2회_p01", _GRADE2_TIMES_TABLE_ROUND2_PAGE1),
        ("초2-2_2단원_곱셈구구_2회_p02", _GRADE2_TIMES_TABLE_ROUND2_PAGE2),
        ("초2-2_2단원_곱셈구구_3회_p01", _GRADE2_TIMES_TABLE_ROUND3_PAGE1),
        ("초2-2_2단원_곱셈구구_3회_p02", _GRADE2_TIMES_TABLE_ROUND3_PAGE2),
        ("초3__진단평가_1회_p01", _GRADE3_DIAGNOSTIC_ROUND1_PAGE1),
        ("초3__진단평가_1회_p02", _GRADE3_DIAGNOSTIC_ROUND1_PAGE2),
        ("초3__진단평가_1회_p03", _GRADE3_DIAGNOSTIC_ROUND1_PAGE3),
        ("초3__진단평가_2회_p01", _GRADE3_DIAGNOSTIC_ROUND2_PAGE1),
        ("초3__진단평가_2회_p02", _GRADE3_DIAGNOSTIC_ROUND2_PAGE2),
        ("초3__진단평가_2회_p03", _GRADE3_DIAGNOSTIC_ROUND2_PAGE3),
        ("초3__진단평가_3회_p01", _GRADE3_DIAGNOSTIC_ROUND3_PAGE1),
        ("초3__진단평가_3회_p02", _GRADE3_DIAGNOSTIC_ROUND3_PAGE2),
        ("초3__진단평가_3회_p03", _GRADE3_DIAGNOSTIC_ROUND3_PAGE3),
        ("초4__진단평가_1회_p01", _GRADE4_DIAGNOSTIC_ROUND1_PAGE1),
        ("초4__진단평가_1회_p02", _GRADE4_DIAGNOSTIC_ROUND1_PAGE2),
        ("초4__진단평가_1회_p03", _GRADE4_DIAGNOSTIC_ROUND1_PAGE3),
        ("초4__진단평가_2회_p01", _GRADE4_DIAGNOSTIC_ROUND2_PAGE1),
        ("초4__진단평가_2회_p02", _GRADE4_DIAGNOSTIC_ROUND2_PAGE2),
        ("초4__진단평가_2회_p03", _GRADE4_DIAGNOSTIC_ROUND2_PAGE3),
        ("초4__진단평가_3회_p02", _GRADE4_DIAGNOSTIC_ROUND3_PAGE2),
        ("초4__진단평가_3회_p03", _GRADE4_DIAGNOSTIC_ROUND3_PAGE3),
        ("초5-1_1단원_자연수의혼합계산_1회_p01", _GRADE5_NATURAL_MIXED_CALC_ROUND1_PAGE1),
        ("초5-1_1단원_자연수의혼합계산_1회_p02", _GRADE5_NATURAL_MIXED_CALC_ROUND1_PAGE2),
        ("초5-1_1단원_자연수의혼합계산_1회_p03", _GRADE5_NATURAL_MIXED_CALC_ROUND1_PAGE3),
        ("초6]_진단평가_3회_p01", _GRADE6_DIAGNOSTIC_ROUND3_PAGE1),
        ("초6__진단평가_3회_p01", _GRADE6_DIAGNOSTIC_ROUND3_PAGE1),
        ("초6]_진단평가_3회_p02", _GRADE6_DIAGNOSTIC_ROUND3_PAGE2),
        ("초6__진단평가_3회_p02", _GRADE6_DIAGNOSTIC_ROUND3_PAGE2),
        ("초6]_진단평가_3회_p03", _GRADE6_DIAGNOSTIC_ROUND3_PAGE3),
        ("초6__진단평가_3회_p03", _GRADE6_DIAGNOSTIC_ROUND3_PAGE3),
        ("초6]_진단평가_2회_p01", _GRADE6_DIAGNOSTIC_ROUND2_PAGE1),
        ("초6__진단평가_2회_p01", _GRADE6_DIAGNOSTIC_ROUND2_PAGE1),
        ("초6]_진단평가_2회_p02", _GRADE6_DIAGNOSTIC_ROUND2_PAGE2),
        ("초6__진단평가_2회_p02", _GRADE6_DIAGNOSTIC_ROUND2_PAGE2),
        ("초6]_진단평가_2회_p03", _GRADE6_DIAGNOSTIC_ROUND2_PAGE3),
        ("초6__진단평가_2회_p03", _GRADE6_DIAGNOSTIC_ROUND2_PAGE3),
        ("초6]_진단평가_1회_p01", _GRADE6_DIAGNOSTIC_ROUND1_PAGE1),
        ("초6__진단평가_1회_p01", _GRADE6_DIAGNOSTIC_ROUND1_PAGE1),
        ("초6]_진단평가_1회_p02", _GRADE6_DIAGNOSTIC_ROUND1_PAGE2),
        ("초6__진단평가_1회_p02", _GRADE6_DIAGNOSTIC_ROUND1_PAGE2),
        ("초6]_진단평가_1회_p03", _GRADE6_DIAGNOSTIC_ROUND1_PAGE3),
        ("초6__진단평가_1회_p03", _GRADE6_DIAGNOSTIC_ROUND1_PAGE3),
        ("초5]_진단평가_3회_p01", _GRADE5_DIAGNOSTIC_ROUND3_PAGE1),
        ("초5__진단평가_3회_p01", _GRADE5_DIAGNOSTIC_ROUND3_PAGE1),
        ("초5]_진단평가_3회_p02", _GRADE5_DIAGNOSTIC_ROUND3_PAGE2),
        ("초5__진단평가_3회_p02", _GRADE5_DIAGNOSTIC_ROUND3_PAGE2),
        ("초5]_진단평가_3회_p03", _GRADE5_DIAGNOSTIC_ROUND3_PAGE3),
        ("초5__진단평가_3회_p03", _GRADE5_DIAGNOSTIC_ROUND3_PAGE3),
        ("초5]_진단평가_2회_p01", _GRADE5_DIAGNOSTIC_ROUND2_PAGE1),
        ("초5__진단평가_2회_p01", _GRADE5_DIAGNOSTIC_ROUND2_PAGE1),
        ("초5]_진단평가_2회_p02", _GRADE5_DIAGNOSTIC_ROUND2_PAGE2),
        ("초5__진단평가_2회_p02", _GRADE5_DIAGNOSTIC_ROUND2_PAGE2),
        ("초5]_진단평가_2회_p03", _GRADE5_DIAGNOSTIC_ROUND2_PAGE3),
        ("초5__진단평가_2회_p03", _GRADE5_DIAGNOSTIC_ROUND2_PAGE3),
        ("초5]_진단평가_1회_p01", _GRADE5_DIAGNOSTIC_ROUND1_PAGE1),
        ("초5__진단평가_1회_p01", _GRADE5_DIAGNOSTIC_ROUND1_PAGE1),
        ("초5]_진단평가_1회_p02", _GRADE5_DIAGNOSTIC_ROUND1_PAGE2),
        ("초5__진단평가_1회_p02", _GRADE5_DIAGNOSTIC_ROUND1_PAGE2),
        ("초5]_진단평가_1회_p03", _GRADE5_DIAGNOSTIC_ROUND1_PAGE3),
        ("초5__진단평가_1회_p03", _GRADE5_DIAGNOSTIC_ROUND1_PAGE3),
        ("초4-1_1단원_큰수_1회_p01", _GRADE4_BIG_NUMBER_ROUND1_PAGE1),
        ("초4-1_1단원_큰수_1회_p02", _GRADE4_BIG_NUMBER_ROUND1_PAGE2),
        ("초4-1_1단원_큰수_2회_p01", _GRADE4_BIG_NUMBER_ROUND2_PAGE1),
        ("초4-1_1단원_큰수_2회_p02", _GRADE4_BIG_NUMBER_ROUND2_PAGE2),
        ("초4-1_1단원_큰수_3회_p01", _GRADE4_BIG_NUMBER_ROUND3_PAGE1),
        ("초4-1_1단원_큰수_3회_p02", _GRADE4_BIG_NUMBER_ROUND3_PAGE2),
        ("초4-1_2단원_각도_1회_p01", _GRADE4_ANGLE_ROUND1_PAGE1),
        ("초4-1_2단원_각도_1회_p02", _GRADE4_ANGLE_ROUND1_PAGE2),
        ("초4-1_2단원_각도_1회_p03", _GRADE4_ANGLE_ROUND1_PAGE3),
        ("초4-1_2단원_각도_2회_p01", _GRADE4_ANGLE_ROUND2_PAGE1),
        ("초4-1_2단원_각도_2회_p02", _GRADE4_ANGLE_ROUND2_PAGE2),
        ("초4-1_2단원_각도_2회_p03", _GRADE4_ANGLE_ROUND2_PAGE3),
        ("초4-1_2단원_각도_3회_p01", _GRADE4_ANGLE_ROUND3_PAGE1),
        ("초4-1_2단원_각도_3회_p02", _GRADE4_ANGLE_ROUND3_PAGE2),
        ("초4-1_2단원_각도_3회_p03", _GRADE4_ANGLE_ROUND3_PAGE3),
        ("초4-1_3단원_곱셈과나눗셈_1회_p01", _GRADE4_MULT_DIV_ROUND1_PAGE1),
        ("초4-1_3단원_곱셈과나눗셈_1회_p02", _GRADE4_MULT_DIV_ROUND1_PAGE2),
        ("초4-1_3단원_곱셈과나눗셈_2회_p01", _GRADE4_MULT_DIV_ROUND2_PAGE1),
        ("초4-1_3단원_곱셈과나눗셈_2회_p02", _GRADE4_MULT_DIV_ROUND2_PAGE2),
        ("초4-1_3단원_곱셈과나눗셈_3회_p01", _GRADE4_MULT_DIV_ROUND3_PAGE1),
        ("초4-1_3단원_곱셈과나눗셈_3회_p02", _GRADE4_MULT_DIV_ROUND3_PAGE2),
        ("초4-1_5단원_막대그래프_1회_p01", _GRADE4_BAR_GRAPH_ROUND1_PAGE1),
        ("초4-1_5단원_막대그래프_1회_p02", _GRADE4_BAR_GRAPH_ROUND1_PAGE2),
        ("초4-1_5단원_막대그래프_1회_p03", _GRADE4_BAR_GRAPH_ROUND1_PAGE3),
        ("초4-1_5단원_막대그래프_1회_p04", _GRADE4_BAR_GRAPH_ROUND1_PAGE4),
        ("초4-1_5단원_막대그래프_2회_p01", _GRADE4_BAR_GRAPH_ROUND2_PAGE1),
        ("초4-1_5단원_막대그래프_2회_p02", _GRADE4_BAR_GRAPH_ROUND2_PAGE2),
        ("초4-1_5단원_막대그래프_2회_p03", _GRADE4_BAR_GRAPH_ROUND2_PAGE3),
        ("초4-1_5단원_막대그래프_2회_p04", _GRADE4_BAR_GRAPH_ROUND2_PAGE4),
        ("초4-1_5단원_막대그래프_3회_p01", _GRADE4_BAR_GRAPH_ROUND3_PAGE1),
        ("초4-1_5단원_막대그래프_3회_p02", _GRADE4_BAR_GRAPH_ROUND3_PAGE2),
        ("초4-1_5단원_막대그래프_3회_p03", _GRADE4_BAR_GRAPH_ROUND3_PAGE3),
        ("초4-1_5단원_막대그래프_3회_p04", _GRADE4_BAR_GRAPH_ROUND3_PAGE4),
        ("초4-1_6단원_규칙찾기_1회_p01", _GRADE4_RULES_ROUND1_PAGE1),
        ("초4-1_6단원_규칙찾기_1회_p02", _GRADE4_RULES_ROUND1_PAGE2),
        ("초4-1_6단원_규칙찾기_1회_p03", _GRADE4_RULES_ROUND1_PAGE3),
        ("초4-1_6단원_규칙찾기_2회_p01", _GRADE4_RULES_ROUND2_PAGE1),
        ("초4-1_6단원_규칙찾기_2회_p02", _GRADE4_RULES_ROUND2_PAGE2),
        ("초4-1_6단원_규칙찾기_2회_p03", _GRADE4_RULES_ROUND2_PAGE3),
        ("초4-1_6단원_규칙찾기_3회_p01", _GRADE4_RULES_ROUND3_PAGE1),
        ("초4-1_6단원_규칙찾기_3회_p02", _GRADE4_RULES_ROUND3_PAGE2),
        ("초4-1_6단원_규칙찾기_3회_p03", _GRADE4_RULES_ROUND3_PAGE3),
        ("초4-1_6단원_규칙찾기_3회_p04", _GRADE4_RULES_ROUND3_PAGE4),
        ("초4-2_1단원_분수의덧셈과뺄셈_1회_p01", _GRADE4_FRACTION_ADD_SUB_ROUND1_PAGE1),
        ("초4-2_1단원_분수의덧셈과뺄셈_1회_p02", _GRADE4_FRACTION_ADD_SUB_ROUND1_PAGE2),
        ("초4-2_1단원_분수의덧셈과뺄셈_1회_p03", _GRADE4_FRACTION_ADD_SUB_ROUND1_PAGE3),
        ("초4-2_1단원_분수의덧셈과뺄셈_2회_p01", _GRADE4_FRACTION_ADD_SUB_ROUND2_PAGE1),
        ("초4-2_1단원_분수의덧셈과뺄셈_2회_p02", _GRADE4_FRACTION_ADD_SUB_ROUND2_PAGE2),
        ("초4-2_1단원_분수의덧셈과뺄셈_2회_p03", _GRADE4_FRACTION_ADD_SUB_ROUND2_PAGE3),
        ("초4-2_1단원_분수의덧셈과뺄셈_3회_p01", _GRADE4_FRACTION_ADD_SUB_ROUND3_PAGE1),
        ("초4-2_1단원_분수의덧셈과뺄셈_3회_p02", _GRADE4_FRACTION_ADD_SUB_ROUND3_PAGE2),
        ("초4-2_1단원_분수의덧셈과뺄셈_3회_p03", _GRADE4_FRACTION_ADD_SUB_ROUND3_PAGE3),
        ("초4-2_2단원_삼각형_1회_p01", _GRADE4_TRIANGLE_ROUND1_PAGE1),
        ("초4-2_2단원_삼각형_1회_p02", _GRADE4_TRIANGLE_ROUND1_PAGE2),
        ("초4-2_2단원_삼각형_1회_p03", _GRADE4_TRIANGLE_ROUND1_PAGE3),
        ("초4-2_2단원_삼각형_2회_p01", _GRADE4_TRIANGLE_ROUND2_PAGE1),
        ("초4-2_2단원_삼각형_2회_p02", _GRADE4_TRIANGLE_ROUND2_PAGE2),
        ("초4-2_2단원_삼각형_2회_p03", _GRADE4_TRIANGLE_ROUND2_PAGE3),
        ("초4-2_2단원_삼각형_3회_p01", _GRADE4_TRIANGLE_ROUND3_PAGE1),
        ("초4-2_2단원_삼각형_3회_p02", _GRADE4_TRIANGLE_ROUND3_PAGE2),
        ("초4-2_2단원_삼각형_3회_p03", _GRADE4_TRIANGLE_ROUND3_PAGE3),
        ("초4-2_3단원_소수의덧셈과뺄셈_1회_p01", _GRADE4_DECIMAL_ADD_SUB_ROUND1_PAGE1),
        ("초4-2_3단원_소수의덧셈과뺄셈_1회_p02", _GRADE4_DECIMAL_ADD_SUB_ROUND1_PAGE2),
        ("초4-2_3단원_소수의덧셈과뺄셈_1회_p03", _GRADE4_DECIMAL_ADD_SUB_ROUND1_PAGE3),
        ("초4-2_3단원_소수의덧셈과뺄셈_2회_p01", _GRADE4_DECIMAL_ADD_SUB_ROUND2_PAGE1),
        ("초4-2_3단원_소수의덧셈과뺄셈_2회_p02", _GRADE4_DECIMAL_ADD_SUB_ROUND2_PAGE2),
        ("초4-2_3단원_소수의덧셈과뺄셈_2회_p03", _GRADE4_DECIMAL_ADD_SUB_ROUND2_PAGE3),
        ("초4-2_3단원_소수의덧셈과뺄셈_3회_p01", _GRADE4_DECIMAL_ADD_SUB_ROUND3_PAGE1),
        ("초4-2_3단원_소수의덧셈과뺄셈_3회_p02", _GRADE4_DECIMAL_ADD_SUB_ROUND3_PAGE2),
        ("초4-2_3단원_소수의덧셈과뺄셈_3회_p03", _GRADE4_DECIMAL_ADD_SUB_ROUND3_PAGE3),
        ("초4-2_4단원_사각형_1회_p01", _GRADE4_QUADRILATERAL_ROUND1_PAGE1),
        ("초4-2_4단원_사각형_1회_p02", _GRADE4_QUADRILATERAL_ROUND1_PAGE2),
        ("초4-2_4단원_사각형_1회_p03", _GRADE4_QUADRILATERAL_ROUND1_PAGE3),
        ("초4-2_4단원_사각형_1회_p04", _GRADE4_QUADRILATERAL_ROUND1_PAGE4),
        ("초4-2_4단원_사각형_2회_p01", _GRADE4_QUADRILATERAL_ROUND2_PAGE1),
        ("초4-2_4단원_사각형_2회_p02", _GRADE4_QUADRILATERAL_ROUND2_PAGE2),
        ("초4-2_4단원_사각형_2회_p03", _GRADE4_QUADRILATERAL_ROUND2_PAGE3),
        ("초4-2_4단원_사각형_2회_p04", _GRADE4_QUADRILATERAL_ROUND2_PAGE4),
        ("초4-2_4단원_사각형_3회_p01", _GRADE4_QUADRILATERAL_ROUND3_PAGE1),
        ("초4-2_4단원_사각형_3회_p02", _GRADE4_QUADRILATERAL_ROUND3_PAGE2),
        ("초4-2_4단원_사각형_3회_p03", _GRADE4_QUADRILATERAL_ROUND3_PAGE3),
        ("초4-2_4단원_사각형_3회_p04", _GRADE4_QUADRILATERAL_ROUND3_PAGE4),
        ("초3-1_1단원_덧셈과뺄셈_1회_p01", _GRADE3_ADD_SUB_ROUND1_PAGE1),
        ("초3-1_1단원_덧셈과뺄셈_1회_p02", _GRADE3_ADD_SUB_ROUND1_PAGE2),
        ("초3-1_1단원_덧셈과뺄셈_2회_p01", _GRADE3_ADD_SUB_ROUND2_PAGE1),
        ("초3-1_1단원_덧셈과뺄셈_2회_p02", _GRADE3_ADD_SUB_ROUND2_PAGE2),
        ("초3-1_1단원_덧셈과뺄셈_3회_p01", _GRADE3_ADD_SUB_ROUND3_PAGE1),
        ("초3-1_1단원_덧셈과뺄셈_3회_p02", _GRADE3_ADD_SUB_ROUND3_PAGE2),
        ("초3-1_2단원_평면도형_1회_p01", _GRADE3_PLANE_SHAPES_ROUND1_PAGE1),
        ("초3-1_2단원_평면도형_1회_p02", _GRADE3_PLANE_SHAPES_ROUND1_PAGE2),
        ("초3-1_2단원_평면도형_1회_p03", _GRADE3_PLANE_SHAPES_ROUND1_PAGE3),
        ("초3-1_2단원_평면도형_2회_p01", _GRADE3_PLANE_SHAPES_ROUND2_PAGE1),
        ("초3-1_2단원_평면도형_2회_p02", _GRADE3_PLANE_SHAPES_ROUND2_PAGE2),
        ("초3-1_2단원_평면도형_2회_p03", _GRADE3_PLANE_SHAPES_ROUND2_PAGE3),
        ("초3-1_2단원_평면도형_3회_p01", _GRADE3_PLANE_SHAPES_ROUND3_PAGE1),
        ("초3-1_2단원_평면도형_3회_p03", _GRADE3_PLANE_SHAPES_ROUND3_PAGE3),
        ("초4-1_4단원_평면도형의이동_1회_p01", _GRADE4_SHAPE_MOVEMENT_ROUND1_PAGE1),
        ("초4-1_4단원_평면도형의이동_1회_p02", _GRADE4_SHAPE_MOVEMENT_ROUND1_PAGE2),
        ("초4-1_4단원_평면도형의이동_1회_p03", _GRADE4_SHAPE_MOVEMENT_ROUND1_PAGE3),
        ("초4-1_4단원_평면도형의이동_2회_p01", _GRADE4_SHAPE_MOVEMENT_ROUND2_PAGE1),
        ("초4-1_4단원_평면도형의이동_2회_p02", _GRADE4_SHAPE_MOVEMENT_ROUND2_PAGE2),
        ("초4-1_4단원_평면도형의이동_2회_p03", _GRADE4_SHAPE_MOVEMENT_ROUND2_PAGE3),
        ("초4-1_4단원_평면도형의이동_3회_p01", _GRADE4_SHAPE_MOVEMENT_ROUND3_PAGE1),
        ("초4-1_4단원_평면도형의이동_3회_p02", _GRADE4_SHAPE_MOVEMENT_ROUND3_PAGE2),
        ("초4-1_4단원_평면도형의이동_3회_p03", _GRADE4_SHAPE_MOVEMENT_ROUND3_PAGE3),
        ("초3-1_3단원_나눗셈_1회_p01", _GRADE3_DIVISION_ROUND1_PAGE1),
        ("초3-1_3단원_나눗셈_1회_p02", _GRADE3_DIVISION_ROUND1_PAGE2),
        ("초3-1_3단원_나눗셈_1회_p03", _GRADE3_DIVISION_ROUND1_PAGE3),
        ("초3-1_3단원_나눗셈_2회_p01", _GRADE3_DIVISION_ROUND2_PAGE1),
        ("초3-1_3단원_나눗셈_2회_p02", _GRADE3_DIVISION_ROUND2_PAGE2),
        ("초3-1_3단원_나눗셈_3회_p01", _GRADE3_DIVISION_ROUND3_PAGE1),
        ("초3-1_3단원_나눗셈_3회_p02", _GRADE3_DIVISION_ROUND3_PAGE2),
        ("초3-1_4단원_곱셈_1회_p01", _GRADE3_MULTIPLICATION_ROUND1_PAGE1),
        ("초3-1_4단원_곱셈_1회_p02", _GRADE3_MULTIPLICATION_ROUND1_PAGE2),
        ("초3-1_4단원_곱셈_2회_p01", _GRADE3_MULTIPLICATION_ROUND2_PAGE1_FULL),
        ("초3-1_4단원_곱셈_2회_p02", _GRADE3_MULTIPLICATION_ROUND2_PAGE2),
        ("초3-1_4단원_곱셈_3회_p01", _GRADE3_MULTIPLICATION_ROUND3_PAGE1),
        ("초3-1_4단원_곱셈_3회_p02", _GRADE3_MULTIPLICATION_ROUND3_PAGE2),
        ("초3-1_5단원_길이와시간_1회_p01", _GRADE3_LENGTH_TIME_ROUND1_PAGE1),
        ("초3-1_5단원_길이와시간_1회_p02", _GRADE3_LENGTH_TIME_ROUND1_PAGE2),
        ("초3-1_5단원_길이와시간_1회_p03", _GRADE3_LENGTH_TIME_ROUND1_PAGE3),
        ("초3-1_5단원_길이와시간_2회_p01", _GRADE3_LENGTH_TIME_ROUND2_PAGE1),
        ("초3-1_5단원_길이와시간_2회_p02", _GRADE3_LENGTH_TIME_ROUND2_PAGE2),
        ("초3-1_5단원_길이와시간_3회_p01", _GRADE3_LENGTH_TIME_ROUND3_PAGE1),
        ("초3-1_5단원_길이와시간_3회_p02", _GRADE3_LENGTH_TIME_ROUND3_PAGE2),
        ("초3-1_6단원_분수와소수_1회_p01", _GRADE3_FRACTION_DECIMAL_ROUND1_PAGE1),
        ("초3-1_6단원_분수와소수_1회_p02", _GRADE3_FRACTION_DECIMAL_ROUND1_PAGE2),
        ("초3-1_6단원_분수와소수_1회_p03", _GRADE3_FRACTION_DECIMAL_ROUND1_PAGE3),
        ("초3-1_6단원_분수와소수_2회_p01", _GRADE3_FRACTION_DECIMAL_ROUND2_PAGE1),
        ("초3-1_6단원_분수와소수_2회_p02", _GRADE3_FRACTION_DECIMAL_ROUND2_PAGE2),
        ("초3-1_6단원_분수와소수_3회_p01", _GRADE3_FRACTION_DECIMAL_ROUND3_PAGE1),
        ("초3-1_6단원_분수와소수_3회_p02", _GRADE3_FRACTION_DECIMAL_ROUND3_PAGE2),
        ("초3-2_1단원_곱셈_1회_p01", _GRADE3_2_MULTIPLICATION_ROUND1_PAGE1),
        ("초3-2_1단원_곱셈_1회_p02", _GRADE3_2_MULTIPLICATION_ROUND1_PAGE2),
        ("초3-2_1단원_곱셈_1회_p03", _GRADE3_2_MULTIPLICATION_ROUND1_PAGE3),
        ("초3-2_1단원_곱셈_2회_p01", _GRADE3_MULTIPLICATION_ROUND2_PAGE1),
        ("초3-2_1단원_곱셈_2회_p02", _GRADE3_2_MULTIPLICATION_ROUND2_PAGE2),
        ("초3-2_1단원_곱셈_2회_p03", _GRADE3_2_MULTIPLICATION_ROUND2_PAGE3),
        ("초3-2_1단원_곱셈_3회_p01", _GRADE3_2_MULTIPLICATION_ROUND3_PAGE1),
        ("초3-2_1단원_곱셈_3회_p02", _GRADE3_2_MULTIPLICATION_ROUND3_PAGE2),
        ("초3-2_1단원_곱셈_3회_p03", _GRADE3_2_MULTIPLICATION_ROUND3_PAGE3),
        ("초3-2_2단원_나눗셈_1회_p01", _GRADE3_2_DIVISION_ROUND1_PAGE1),
        ("초3-2_2단원_나눗셈_1회_p02", _GRADE3_2_DIVISION_ROUND1_PAGE2),
        ("초3-2_2단원_나눗셈_1회_p03", _GRADE3_2_DIVISION_ROUND1_PAGE3),
        ("초3-2_2단원_나눗셈_2회_p01", _GRADE3_2_DIVISION_ROUND2_PAGE1),
        ("초3-2_2단원_나눗셈_2회_p02", _GRADE3_2_DIVISION_ROUND2_PAGE2),
        ("초3-2_2단원_나눗셈_2회_p03", _GRADE3_2_DIVISION_ROUND2_PAGE3),
        ("초3-2_2단원_나눗셈_3회_p01", _GRADE3_2_DIVISION_ROUND3_PAGE1),
        ("초3-2_2단원_나눗셈_3회_p02", _GRADE3_2_DIVISION_ROUND3_PAGE2),
        ("초3-2_2단원_나눗셈_3회_p03", _GRADE3_2_DIVISION_ROUND3_PAGE3),
        ("초3-2_3단원_원_1회_p01", _GRADE3_2_CIRCLE_ROUND1_PAGE1),
        ("초3-2_3단원_원_1회_p02", _GRADE3_2_CIRCLE_ROUND1_PAGE2),
        ("초3-2_3단원_원_1회_p03", _GRADE3_2_CIRCLE_ROUND1_PAGE3),
        ("초3-2_3단원_원_1회_p04", _GRADE3_2_CIRCLE_ROUND1_PAGE4),
        ("초3-2_3단원_원_2회_p01", _GRADE3_2_CIRCLE_ROUND2_PAGE1),
        ("초3-2_3단원_원_2회_p02", _GRADE3_2_CIRCLE_ROUND2_PAGE2),
        ("초3-2_3단원_원_2회_p03", _GRADE3_2_CIRCLE_ROUND2_PAGE3),
        ("초3-2_3단원_원_2회_p04", _GRADE3_2_CIRCLE_ROUND2_PAGE4),
        ("초3-2_3단원_원_3회_p01", _GRADE3_2_CIRCLE_ROUND3_PAGE1),
        ("초3-2_3단원_원_3회_p02", _GRADE3_2_CIRCLE_ROUND3_PAGE2),
        ("초3-2_3단원_원_3회_p03", _GRADE3_2_CIRCLE_ROUND3_PAGE3),
        ("초3-2_3단원_원_3회_p04", _GRADE3_2_CIRCLE_ROUND3_PAGE4),
        ("초3-2_4단원_분수_1회_p01", _GRADE3_2_FRACTION_ROUND1_PAGE1),
        ("초3-2_4단원_분수_1회_p02", _GRADE3_2_FRACTION_ROUND1_PAGE2),
        ("초3-2_4단원_분수_1회_p03", _GRADE3_2_FRACTION_ROUND1_PAGE3),
        ("초3-2_4단원_분수_2회_p01", _GRADE3_2_FRACTION_ROUND2_PAGE1),
        ("초3-2_4단원_분수_2회_p02", _GRADE3_2_FRACTION_ROUND2_PAGE2),
        ("초3-2_4단원_분수_2회_p03", _GRADE3_2_FRACTION_ROUND2_PAGE3),
        ("초3-2_4단원_분수_3회_p01", _GRADE3_2_FRACTION_ROUND3_PAGE1),
        ("초3-2_4단원_분수_3회_p02", _GRADE3_2_FRACTION_ROUND3_PAGE2),
        ("초3-2_4단원_분수_3회_p03", _GRADE3_2_FRACTION_ROUND3_PAGE3),
        ("초3-2_5단원_들이와무게_1회_p01", _GRADE3_2_VOLUME_WEIGHT_ROUND1_PAGE1),
        ("초3-2_5단원_들이와무게_1회_p02", _GRADE3_2_VOLUME_WEIGHT_ROUND1_PAGE2),
        ("초3-2_5단원_들이와무게_1회_p03", _GRADE3_2_VOLUME_WEIGHT_ROUND1_PAGE3),
        ("초3-2_5단원_들이와무게_2회_p01", _GRADE3_2_VOLUME_WEIGHT_ROUND2_PAGE1),
        ("초3-2_5단원_들이와무게_2회_p02", _GRADE3_2_VOLUME_WEIGHT_ROUND2_PAGE2),
        ("초3-2_5단원_들이와무게_2회_p03", _GRADE3_2_VOLUME_WEIGHT_ROUND2_PAGE3),
        ("초3-2_5단원_들이와무게_3회_p01", _GRADE3_2_VOLUME_WEIGHT_ROUND3_PAGE1),
        ("초3-2_5단원_들이와무게_3회_p02", _GRADE3_2_VOLUME_WEIGHT_ROUND3_PAGE2),
        ("초3-2_5단원_들이와무게_3회_p03", _GRADE3_2_VOLUME_WEIGHT_ROUND3_PAGE3),
        ("초3-2_6단원_그림그래프_1회_p01", _GRADE3_2_PICTOGRAPH_ROUND1_PAGE1),
        ("초3-2_6단원_그림그래프_1회_p02", _GRADE3_2_PICTOGRAPH_ROUND1_PAGE2),
        ("초3-2_6단원_그림그래프_1회_p03", _GRADE3_2_PICTOGRAPH_ROUND1_PAGE3),
        ("초3-2_6단원_그림그래프_1회_p04", _GRADE3_2_PICTOGRAPH_ROUND1_PAGE4),
        ("초3-2_6단원_그림그래프_1회_p05", _GRADE3_2_PICTOGRAPH_ROUND1_PAGE5),
        ("초3-2_6단원_그림그래프_2회_p01", _GRADE3_2_PICTOGRAPH_ROUND2_PAGE1),
        ("초3-2_6단원_그림그래프_2회_p02", _GRADE3_2_PICTOGRAPH_ROUND2_PAGE2),
        ("초3-2_6단원_그림그래프_2회_p03", _GRADE3_2_PICTOGRAPH_ROUND2_PAGE3),
        ("초3-2_6단원_그림그래프_2회_p04", _GRADE3_2_PICTOGRAPH_ROUND2_PAGE4),
        ("초3-2_6단원_그림그래프_2회_p05", _GRADE3_2_PICTOGRAPH_ROUND2_PAGE5),
        ("초3-2_6단원_그림그래프_3회_p01", _GRADE3_2_PICTOGRAPH_ROUND3_PAGE1),
        ("초3-2_6단원_그림그래프_3회_p02", _GRADE3_2_PICTOGRAPH_ROUND3_PAGE2),
        ("초3-2_6단원_그림그래프_3회_p03", _GRADE3_2_PICTOGRAPH_ROUND3_PAGE3),
        ("초3-2_6단원_그림그래프_3회_p04", _GRADE3_2_PICTOGRAPH_ROUND3_PAGE4),
        ("초3-2_6단원_그림그래프_3회_p05", _GRADE3_2_PICTOGRAPH_ROUND3_PAGE5),
    )
    for page_name, templates in page_templates:
        if page_name in normalized:
            return templates.get(index)
    return _infer_generic_elementary_visual_template(raw_text)
