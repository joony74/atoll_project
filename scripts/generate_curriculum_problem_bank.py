from __future__ import annotations

import argparse
import json
import math
import random
import shutil
import textwrap
from dataclasses import asdict, dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROBLEM_ROOT = PROJECT_ROOT / "02.학습문제" / "05.문제은행"
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "data" / "problem_bank" / "learned" / "coco_curriculum_problem_bank_manifest.json"

FONT_CANDIDATES = (
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
)

BANDS = (
    ("01.초등", "초등", range(1, 7)),
    ("02.중등", "중등", range(1, 4)),
    ("03.고등", "고등", range(1, 4)),
)

DIFFICULTY_LABELS = {"easy": "기본", "medium": "응용", "hard": "심화"}


@dataclass(frozen=True, slots=True)
class ProblemSpec:
    problem_id: str
    band: str
    grade: int
    difficulty: str
    layout: str
    area: str
    unit: str
    topic: str
    folder: str
    file_name: str
    title: str
    lines: tuple[str, ...]
    expected_answer: str
    expected_expression: str
    table: tuple[tuple[str, ...], ...] = ()
    diagram: dict[str, Any] = field(default_factory=dict)
    source_basis: str = "2022 개정 수학과 교육과정 단원 흐름 기반 자체 생성"


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _difficulty(index: int) -> str:
    if index <= 34:
        return "easy"
    if index <= 67:
        return "medium"
    return "hard"


def _difficulty_label(index: int) -> str:
    return DIFFICULTY_LABELS[_difficulty(index)]


def _fmt(value: int | float | Fraction) -> str:
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, float):
        rounded = round(value)
        if abs(value - rounded) < 1e-9:
            return str(int(rounded))
        return f"{value:.6g}"
    return str(value)


def _clean_signed(value: int) -> str:
    return f"+ {value}" if value >= 0 else f"- {abs(value)}"


def _unit_specs(band: str, grade: int) -> list[dict[str, str]]:
    if band == "초등":
        elementary = {
            1: [
                ("수와 연산", "9까지의 수와 덧셈·뺄셈", "arithmetic"),
                ("도형과 측정", "여러 가지 모양과 길이 비교", "geometry"),
                ("변화와 관계", "규칙 찾기", "pattern"),
                ("자료와 가능성", "분류하고 세기", "statistics"),
            ],
            2: [
                ("수와 연산", "세 자리 수와 곱셈구구", "arithmetic"),
                ("도형과 측정", "길이와 시각", "measurement"),
                ("변화와 관계", "규칙과 대응", "pattern"),
                ("자료와 가능성", "표와 그래프", "statistics"),
            ],
            3: [
                ("수와 연산", "곱셈·나눗셈과 분수", "arithmetic"),
                ("도형과 측정", "평면도형과 원", "geometry"),
                ("변화와 관계", "규칙 배열", "pattern"),
                ("자료와 가능성", "막대그래프", "statistics"),
            ],
            4: [
                ("수와 연산", "큰 수와 분수·소수 계산", "fraction_ratio"),
                ("도형과 측정", "각도와 삼각형·사각형", "geometry"),
                ("변화와 관계", "규칙과 대응 관계", "pattern"),
                ("자료와 가능성", "꺾은선그래프", "statistics"),
            ],
            5: [
                ("수와 연산", "약수와 배수·분수의 계산", "fraction_ratio"),
                ("도형과 측정", "다각형의 둘레와 넓이", "geometry"),
                ("변화와 관계", "대응 관계와 비", "function"),
                ("자료와 가능성", "평균과 가능성", "statistics"),
            ],
            6: [
                ("수와 연산", "분수·소수의 나눗셈", "fraction_ratio"),
                ("도형과 측정", "원과 입체도형", "geometry"),
                ("변화와 관계", "비례식과 비율", "function"),
                ("자료와 가능성", "여러 그래프와 가능성", "statistics"),
            ],
        }
        return [{"area": area, "unit": unit, "topic": topic} for area, unit, topic in elementary[grade]]

    if band == "중등":
        middle = {
            1: [
                ("수와 연산", "정수와 유리수", "arithmetic"),
                ("변화와 관계", "문자의 사용과 일차방정식", "linear_equation"),
                ("변화와 관계", "좌표평면과 그래프", "function"),
                ("도형과 측정", "기본도형과 작도", "geometry"),
                ("자료와 가능성", "자료의 정리와 해석", "statistics"),
            ],
            2: [
                ("수와 연산", "유리수와 순환소수", "fraction_ratio"),
                ("변화와 관계", "연립방정식과 일차함수", "function"),
                ("도형과 측정", "삼각형과 사각형의 성질", "geometry"),
                ("자료와 가능성", "확률의 기본", "probability"),
            ],
            3: [
                ("수와 연산", "제곱근과 실수", "radical_power"),
                ("변화와 관계", "다항식과 이차방정식", "quadratic"),
                ("변화와 관계", "이차함수와 그래프", "quadratic_function"),
                ("도형과 측정", "피타고라스와 삼각비", "geometry"),
                ("자료와 가능성", "대푯값과 산포도", "statistics"),
            ],
        }
        return [{"area": area, "unit": unit, "topic": topic} for area, unit, topic in middle[grade]]

    high = {
        1: [
            ("공통수학", "다항식과 나머지정리", "polynomial"),
            ("공통수학", "방정식과 부등식", "quadratic"),
            ("공통수학", "좌표평면과 도형", "coordinate_geometry"),
            ("공통수학", "함수와 그래프", "function"),
            ("공통수학", "경우의 수", "probability"),
        ],
        2: [
            ("수학 I", "지수함수와 로그함수", "logarithm"),
            ("수학 I", "삼각함수", "trigonometry"),
            ("수학 I", "수열", "sequence"),
            ("확률과 통계", "확률분포와 자료", "statistics"),
        ],
        3: [
            ("수학 II", "함수의 극한과 연속", "calculus_limit"),
            ("수학 II", "미분", "calculus_derivative"),
            ("수학 II", "적분", "calculus_integral"),
            ("기하", "벡터와 이차곡선", "coordinate_geometry"),
            ("확률과 통계", "통계적 추정", "statistics"),
        ],
    }
    return [{"area": area, "unit": unit, "topic": topic} for area, unit, topic in high[grade]]


def _table_problem(rng: random.Random, *, band: str, grade: int, unit: dict[str, str], difficulty: str) -> dict[str, Any]:
    if unit["topic"] == "function":
        a = rng.choice([2, 3, 4, 5, -2])
        b = rng.randint(-5, 8)
        xs = [1, 2, 3, 4]
        target = rng.choice(xs)
        ys = [a * x + b for x in xs]
        return {
            "layout": "table",
            "lines": ("아래 표는 일차함수 y = ax + b의 일부입니다.", f"x = {target}일 때 y의 값을 구하시오."),
            "answer": _fmt(a * target + b),
            "expression": f"y={a}x{_clean_signed(b)}; x={target}",
            "table": (("x", *(str(x) for x in xs)), ("y", *(str(y) for y in ys))),
            "diagram": {},
        }
    if unit["topic"] == "probability":
        red = rng.randint(3, 12)
        blue = rng.randint(4, 15)
        total = red + blue
        return {
            "layout": "table",
            "lines": ("아래 표는 상자 안 공의 색깔별 개수입니다.", "공 하나를 뽑을 때 빨간 공일 확률을 구하시오."),
            "answer": _fmt(Fraction(red, total)),
            "expression": f"{red}/{total}",
            "table": (("색깔", "빨간 공", "파란 공", "전체"), ("개수", str(red), str(blue), str(total))),
            "diagram": {},
        }
    if unit["topic"] == "pattern":
        start = rng.randint(2, 8)
        diff = rng.randint(2, 6)
        xs = [1, 2, 3, 4]
        values = [start + diff * (x - 1) for x in xs]
        return {
            "layout": "table",
            "lines": ("아래 표의 규칙을 보고 5번째 값을 구하시오.",),
            "answer": str(start + diff * 4),
            "expression": f"{values[-1]}+{diff}",
            "table": (("순서", *(str(x) for x in xs)), ("값", *(str(v) for v in values))),
            "diagram": {},
        }
    values = [rng.randint(12, 46) for _ in range(4)]
    if difficulty == "hard":
        answer = _fmt(Fraction(sum(values), len(values)))
        expression = f"({'+'.join(str(v) for v in values)})/{len(values)}"
        prompt = "아래 표의 자료에서 평균을 구하시오."
    elif unit["topic"] in {"statistics", "probability"}:
        answer = str(max(values) - min(values))
        expression = f"{max(values)}-{min(values)}"
        prompt = "아래 표에서 가장 큰 값과 가장 작은 값의 차를 구하시오."
    else:
        answer = str(sum(values))
        expression = "+".join(str(v) for v in values)
        prompt = "아래 표의 수량은 모두 몇 개인지 구하시오."
    return {
        "layout": "table",
        "lines": (prompt,),
        "answer": answer,
        "expression": expression,
        "table": (("항목", "A", "B", "C", "D"), ("값", *(str(v) for v in values))),
        "diagram": {},
    }


def _graph_problem(rng: random.Random, *, band: str, grade: int, unit: dict[str, str], difficulty: str) -> dict[str, Any]:
    if unit["topic"] in {"quadratic", "quadratic_function"}:
        h = rng.randint(-2, 2)
        k = rng.randint(-3, 3)
        x = rng.randint(-2, 4)
        answer = (x - h) ** 2 + k
        return {
            "layout": "graph",
            "lines": (f"오른쪽 그래프는 y = (x {_clean_signed(-h)})^2 {_clean_signed(k)}입니다.", f"x = {x}일 때 y의 값을 구하시오."),
            "answer": _fmt(answer),
            "expression": f"(x-{h})^2+{k}; x={x}",
            "table": (),
            "diagram": {"type": "parabola", "h": h, "k": k, "x": x},
        }
    a = rng.choice([-3, -2, 1, 2, 3, 4])
    b = rng.randint(-5, 5)
    x = rng.randint(-3, 5)
    y = a * x + b
    question = rng.choice(["value", "slope"])
    if question == "slope" and band != "초등":
        return {
            "layout": "graph",
            "lines": (f"오른쪽 직선의 식은 y = {a}x {_clean_signed(b)}입니다.", "이 직선의 기울기를 구하시오."),
            "answer": _fmt(a),
            "expression": f"y={a}x{_clean_signed(b)}",
            "table": (),
            "diagram": {"type": "line", "a": a, "b": b, "x": x},
        }
    return {
        "layout": "graph",
        "lines": (f"오른쪽 직선의 식은 y = {a}x {_clean_signed(b)}입니다.", f"x = {x}일 때 y의 값을 구하시오."),
        "answer": _fmt(y),
        "expression": f"y={a}x{_clean_signed(b)}; x={x}",
        "table": (),
        "diagram": {"type": "line", "a": a, "b": b, "x": x},
    }


def _geometry_problem(rng: random.Random, *, band: str, grade: int, unit: dict[str, str], difficulty: str) -> dict[str, Any]:
    if unit["topic"] in {"radical_power", "geometry"} and band == "중등" and grade >= 3:
        a, b, c = rng.choice([(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17)])
        return {
            "layout": "geometry",
            "lines": ("오른쪽 직각삼각형에서 빗변의 길이를 구하시오.",),
            "answer": str(c),
            "expression": f"sqrt({a*a}+{b*b})",
            "table": (),
            "diagram": {"type": "right_triangle", "a": a, "b": b, "c": c, "show_hypotenuse": False},
        }
    if unit["topic"] == "coordinate_geometry":
        x1, y1 = rng.randint(-4, 1), rng.randint(-3, 2)
        dx, dy = rng.choice([(3, 4), (5, 12), (6, 8)])
        x2, y2 = x1 + dx, y1 + dy
        distance = int(math.sqrt(dx * dx + dy * dy))
        return {
            "layout": "geometry",
            "lines": (f"좌표평면의 두 점 A({x1}, {y1}), B({x2}, {y2}) 사이의 거리를 구하시오.",),
            "answer": str(distance),
            "expression": f"sqrt(({x2}-{x1})^2+({y2}-{y1})^2)",
            "table": (),
            "diagram": {"type": "coordinate_segment", "x1": x1, "y1": y1, "x2": x2, "y2": y2},
        }
    width = rng.randint(5, 18)
    height = rng.randint(4, 14)
    if difficulty == "easy":
        return {
            "layout": "geometry",
            "lines": ("오른쪽 직사각형의 넓이를 구하시오.",),
            "answer": str(width * height),
            "expression": f"{width}*{height}",
            "table": (),
            "diagram": {"type": "rectangle", "width": width, "height": height},
        }
    radius = rng.choice([3, 4, 5, 6])
    return {
        "layout": "geometry",
        "lines": ("원주율을 3.14로 하여 오른쪽 원의 둘레를 구하시오.",),
        "answer": _fmt(2 * 3.14 * radius),
        "expression": f"2*3.14*{radius}",
        "table": (),
        "diagram": {"type": "circle", "radius": radius},
    }


def _symbolic_problem(rng: random.Random, *, band: str, grade: int, unit: dict[str, str], difficulty: str) -> dict[str, Any]:
    topic = unit["topic"]
    if topic == "linear_equation":
        x = rng.randint(-9, 12)
        a = rng.choice([2, 3, 4, 5, 6])
        b = rng.randint(-10, 14)
        c = a * x + b
        return {"lines": ("다음 일차방정식의 해를 구하시오.", f"{a}x {_clean_signed(b)} = {c}"), "answer": str(x), "expression": f"{a}x{_clean_signed(b)}={c}"}
    if topic in {"quadratic", "quadratic_function"}:
        r1 = rng.randint(-5, 2)
        r2 = rng.randint(3, 8)
        s = r1 + r2
        p = r1 * r2
        answer = ", ".join(str(v) for v in sorted({r1, r2}))
        return {"lines": ("다음 이차방정식의 해를 모두 구하시오.", f"x^2 {_clean_signed(-s)}x {_clean_signed(p)} = 0"), "answer": answer, "expression": f"x^2{_clean_signed(-s)}x{_clean_signed(p)}=0"}
    if topic == "polynomial":
        x = rng.randint(-3, 5)
        a, b, c = rng.choice([1, 2, 3]), rng.randint(-5, 5), rng.randint(-6, 8)
        return {"lines": (f"다항식 f(x) = {a}x^2 {_clean_signed(b)}x {_clean_signed(c)}에서", f"f({x})의 값을 구하시오."), "answer": str(a*x*x + b*x + c), "expression": f"{a}x^2{_clean_signed(b)}x{_clean_signed(c)}; x={x}"}
    if topic == "logarithm":
        base = rng.choice([2, 3, 5])
        power = rng.randint(2, 5)
        return {"lines": ("다음 로그의 값을 구하시오.", f"log_{base}({base ** power})"), "answer": str(power), "expression": f"log_{base}({base ** power})"}
    if topic == "trigonometry":
        left, lval = rng.choice([("sin(pi/6)", Fraction(1, 2)), ("cos(pi/3)", Fraction(1, 2)), ("tan(pi/4)", Fraction(1, 1))])
        right, rval = rng.choice([("sin(pi/6)", Fraction(1, 2)), ("cos(pi/3)", Fraction(1, 2))])
        return {"lines": ("다음 삼각함수 값을 구하시오.", f"{left} + {right}"), "answer": _fmt(lval + rval), "expression": f"{left}+{right}"}
    if topic == "sequence":
        a1 = rng.randint(1, 8)
        d = rng.randint(2, 7)
        n = rng.randint(5, 12)
        return {"lines": (f"등차수열의 첫째항이 {a1}, 공차가 {d}입니다.", f"제 {n}항을 구하시오."), "answer": str(a1 + (n - 1) * d), "expression": f"{a1}+({n}-1)*{d}"}
    if topic == "calculus_derivative":
        a, b, x = rng.randint(1, 5), rng.randint(-6, 6), rng.randint(-3, 5)
        return {"lines": (f"f(x) = {a}x^2 {_clean_signed(b)}x일 때", f"f'({x})의 값을 구하시오."), "answer": str(2*a*x + b), "expression": f"2*{a}*{x}+{b}"}
    if topic == "calculus_integral":
        height, width = rng.randint(1, 7), rng.randint(2, 8)
        return {"lines": (f"함수 f(x) = {height}의 그래프와 x축 사이의", f"0 <= x <= {width} 구간 넓이를 구하시오."), "answer": str(height * width), "expression": f"{height}*{width}"}
    if topic == "calculus_limit":
        a, b, x = rng.randint(1, 5), rng.randint(-4, 4), rng.randint(-3, 4)
        return {"lines": (f"f(x) = {a}x {_clean_signed(b)}일 때", f"lim x->{x} f(x)의 값을 구하시오."), "answer": str(a*x + b), "expression": f"{a}*{x}+{b}"}
    if topic == "probability":
        total = rng.randint(12, 36)
        good = rng.randint(3, total - 3)
        return {"lines": (f"공 {total}개 중 빨간 공이 {good}개입니다.", "임의로 하나를 뽑을 때 빨간 공일 확률은?"), "answer": _fmt(Fraction(good, total)), "expression": f"{good}/{total}"}
    if topic in {"fraction_ratio", "statistics"}:
        if topic == "statistics":
            values = [rng.randint(60, 100) for _ in range(5)]
            return {"lines": ("다음 자료의 평균을 구하시오.", ", ".join(str(v) for v in values)), "answer": _fmt(Fraction(sum(values), len(values))), "expression": f"({'+'.join(str(v) for v in values)})/{len(values)}"}
        a = Fraction(rng.randint(1, 5), rng.choice([4, 5, 6, 8, 10, 12]))
        b = Fraction(rng.randint(1, 5), rng.choice([4, 5, 6, 8, 10, 12]))
        return {"lines": ("다음 분수 계산을 하시오.", f"{a.numerator}/{a.denominator} + {b.numerator}/{b.denominator}"), "answer": _fmt(a + b), "expression": f"{a.numerator}/{a.denominator}+{b.numerator}/{b.denominator}"}
    if topic == "radical_power":
        n = rng.randint(3, 10)
        add = rng.randint(1, 8)
        return {"lines": ("다음 식의 값을 구하시오.", f"sqrt({n*n}) + {add}"), "answer": str(n + add), "expression": f"sqrt({n*n})+{add}"}
    if topic == "pattern":
        start = rng.randint(2, 9)
        diff = rng.randint(2, 7)
        seq = [start + diff * i for i in range(4)]
        return {"lines": ("규칙을 찾아 빈칸에 알맞은 수를 쓰시오.", f"{seq[0]}, {seq[1]}, {seq[2]}, {seq[3]}, □"), "answer": str(start + diff * 4), "expression": f"{seq[3]}+{diff}"}
    a, b, c = rng.randint(12, 90), rng.randint(5, 40), rng.randint(2, 25)
    if difficulty == "hard":
        return {"lines": ("다음 식의 값을 구하시오.", f"{a} + {b} - {c}"), "answer": str(a + b - c), "expression": f"{a}+{b}-{c}"}
    return {"lines": ("다음 식의 값을 구하시오.", f"{a} + {b}"), "answer": str(a + b), "expression": f"{a}+{b}"}


def _word_problem(rng: random.Random, *, band: str, grade: int, unit: dict[str, str], difficulty: str) -> dict[str, Any]:
    topic = unit["topic"]
    if topic == "calculus_derivative":
        a, b, t = rng.randint(1, 4), rng.randint(-5, 6), rng.randint(1, 5)
        velocity_a = 2 * a
        return {
            "layout": "word",
            "lines": (f"물체의 속도 함수가 v(t) = {velocity_a}t {_clean_signed(b)}입니다.", f"t = {t}에서의 순간속도를 구하시오."),
            "answer": str(velocity_a * t + b),
            "expression": f"{velocity_a}*{t}{_clean_signed(b)}",
            "table": (),
            "diagram": {},
        }
    if topic == "calculus_integral":
        speed, seconds = rng.randint(2, 9), rng.randint(3, 10)
        return {
            "layout": "word",
            "lines": (f"속도 함수가 v(t) = {speed}인 물체가 있습니다.", f"0 <= t <= {seconds} 동안 이동한 거리를 구하시오."),
            "answer": str(speed * seconds),
            "expression": f"{speed}*{seconds}",
            "table": (),
            "diagram": {},
        }
    if topic == "calculus_limit":
        a, b, target = rng.randint(1, 5), rng.randint(-4, 4), rng.randint(-3, 4)
        return {
            "layout": "word",
            "lines": (f"함수 f(x) = {a}x {_clean_signed(b)}가 있습니다.", f"x가 {target}에 가까워질 때 f(x)의 극한값을 구하시오."),
            "answer": str(a * target + b),
            "expression": f"{a}*{target}+{b}",
            "table": (),
            "diagram": {},
        }
    if topic == "function":
        a, b, x = rng.choice([2, 3, 4, 5]), rng.randint(-4, 8), rng.randint(1, 6)
        return {"layout": "word", "lines": (f"한 묶음에 {a}개씩 들어 있는 물건이 x묶음 있고, 낱개 {b}개가 더 있습니다.", f"x = {x}일 때 전체 개수를 식 y = {a}x {_clean_signed(b)}로 구하시오."), "answer": str(a*x+b), "expression": f"y={a}x{_clean_signed(b)};x={x}", "table": (), "diagram": {}}
    if topic == "measurement":
        length = rng.randint(18, 75)
        cut = rng.randint(4, min(30, length - 1))
        return {"layout": "word", "lines": (f"끈의 길이가 {length} cm입니다.", f"그중 {cut} cm를 잘라 사용했습니다. 남은 길이는 몇 cm입니까?"), "answer": str(length-cut), "expression": f"{length}-{cut}", "table": (), "diagram": {}}
    if topic == "geometry":
        width, height = rng.randint(6, 16), rng.randint(4, 12)
        return {"layout": "word", "lines": (f"가로가 {width} cm, 세로가 {height} cm인 직사각형 모양 밭이 있습니다.", "이 밭의 넓이를 구하시오."), "answer": str(width*height), "expression": f"{width}*{height}", "table": (), "diagram": {"type": "rectangle", "width": width, "height": height}}
    if topic == "probability":
        total, good = rng.randint(10, 30), rng.randint(2, 9)
        total = max(total, good + 3)
        return {"layout": "word", "lines": (f"상자에 공이 {total}개 있고 그중 당첨 공은 {good}개입니다.", "공 하나를 뽑을 때 당첨될 확률을 구하시오."), "answer": _fmt(Fraction(good, total)), "expression": f"{good}/{total}", "table": (), "diagram": {}}
    if topic == "statistics":
        values = [rng.randint(60, 100) for _ in range(5)]
        return {
            "layout": "word",
            "lines": ("다섯 번의 점수가 다음과 같습니다.", f"{', '.join(str(value) for value in values)}의 평균을 구하시오."),
            "answer": _fmt(Fraction(sum(values), len(values))),
            "expression": f"({'+'.join(str(value) for value in values)})/{len(values)}",
            "table": (),
            "diagram": {},
        }
    if topic == "pattern":
        start = rng.randint(2, 8)
        diff = rng.randint(2, 6)
        count = rng.randint(5, 8)
        return {
            "layout": "word",
            "lines": (f"첫째 날 {start}개를 만들고 매일 {diff}개씩 더 많이 만듭니다.", f"{count}째 날에는 몇 개를 만듭니까?"),
            "answer": str(start + (count - 1) * diff),
            "expression": f"{start}+({count}-1)*{diff}",
            "table": (),
            "diagram": {},
        }
    if topic == "fraction_ratio":
        a = Fraction(rng.randint(1, 5), rng.choice([4, 5, 6, 8, 10, 12]))
        b = Fraction(rng.randint(1, 5), rng.choice([4, 5, 6, 8, 10, 12]))
        return {
            "layout": "word",
            "lines": (f"물 {a.numerator}/{a.denominator} L와 {b.numerator}/{b.denominator} L를 합쳤습니다.", "전체 물의 양을 구하시오."),
            "answer": _fmt(a + b),
            "expression": f"{a.numerator}/{a.denominator}+{b.numerator}/{b.denominator}",
            "table": (),
            "diagram": {},
        }
    a, b, c = rng.randint(20, 90), rng.randint(8, 44), rng.randint(3, 28)
    return {"layout": "word", "lines": (f"민지는 스티커를 {a}장 가지고 있었습니다.", f"{b}장을 더 받고, 그중 {c}장을 사용했습니다. 남은 스티커는 몇 장입니까?"), "answer": str(a+b-c), "expression": f"{a}+{b}-{c}", "table": (), "diagram": {}}


def _make_payload(band: str, grade: int, index: int, rng: random.Random, unit: dict[str, str]) -> dict[str, Any]:
    difficulty = _difficulty(index)
    cycle = (index - 1) % 10
    table_topics = {"function", "statistics", "probability", "pattern", "arithmetic", "measurement"}
    word_topics = {
        "function",
        "measurement",
        "geometry",
        "probability",
        "statistics",
        "pattern",
        "fraction_ratio",
        "arithmetic",
        "calculus_derivative",
        "calculus_integral",
        "calculus_limit",
    }
    if cycle in {3, 8} and unit["topic"] in {"function", "quadratic_function", "coordinate_geometry", "quadratic"}:
        return _graph_problem(rng, band=band, grade=grade, unit=unit, difficulty=difficulty)
    if cycle in {4, 9} and unit["topic"] in {"geometry", "coordinate_geometry", "radical_power"}:
        return _geometry_problem(rng, band=band, grade=grade, unit=unit, difficulty=difficulty)
    if cycle in {2, 7} and unit["topic"] in table_topics:
        return _table_problem(rng, band=band, grade=grade, unit=unit, difficulty=difficulty)
    if cycle in {1, 6} and unit["topic"] in word_topics:
        return _word_problem(rng, band=band, grade=grade, unit=unit, difficulty=difficulty)
    symbolic = _symbolic_problem(rng, band=band, grade=grade, unit=unit, difficulty=difficulty)
    return {"layout": "expression", "table": (), "diagram": {}, **symbolic}


def make_problem(band: str, folder_name: str, grade: int, index: int, seed: int) -> ProblemSpec:
    rng = random.Random(seed + grade * 1009 + index * 37 + len(band) * 97)
    units = _unit_specs(band, grade)
    unit = units[(index - 1) % len(units)]
    payload = _make_payload(band, grade, index, rng, unit)
    difficulty = _difficulty(index)
    layout = str(payload["layout"])
    prefix = {"초등": "elementary", "중등": "middle", "고등": "high"}[band]
    problem_id = f"{prefix}_g{grade:02d}_{index:03d}"
    file_name = f"{problem_id}_{difficulty}_{layout}_{unit['topic']}.png"
    folder = f"{folder_name}/{grade}학년/{unit['area']}/{unit['unit']}"
    title = f"{band} {grade}학년 · {unit['unit']} · {_difficulty_label(index)}"
    return ProblemSpec(
        problem_id=problem_id,
        band=band,
        grade=grade,
        difficulty=difficulty,
        layout=layout,
        area=unit["area"],
        unit=unit["unit"],
        topic=unit["topic"],
        folder=folder,
        file_name=file_name,
        title=title,
        lines=tuple(payload["lines"]),
        expected_answer=str(payload["answer"]),
        expected_expression=str(payload["expression"]),
        table=tuple(tuple(str(cell) for cell in row) for row in payload.get("table") or ()),
        diagram=dict(payload.get("diagram") or {}),
    )


def generate_specs(count_per_grade: int, seed: int) -> list[ProblemSpec]:
    specs: list[ProblemSpec] = []
    for folder_name, band, grades in BANDS:
        for grade in grades:
            for index in range(1, count_per_grade + 1):
                specs.append(make_problem(band, folder_name, grade, index, seed))
    return specs


def _wrap_lines(lines: tuple[str, ...], width: int = 38) -> list[str]:
    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(textwrap.wrap(line, width=width, break_long_words=False, replace_whitespace=False) or [line])
    return wrapped


def _draw_table(draw: ImageDraw.ImageDraw, spec: ProblemSpec, x: int, y: int, width: int) -> int:
    if not spec.table:
        return y
    small = _font(34)
    rows = len(spec.table)
    cols = max(len(row) for row in spec.table)
    cell_w = min(190, width // max(cols, 1))
    cell_h = 58
    for r in range(rows):
        for c in range(cols):
            x1 = x + c * cell_w
            y1 = y + r * cell_h
            fill = (244, 247, 251) if r == 0 or c == 0 else (255, 255, 255)
            draw.rectangle((x1, y1, x1 + cell_w, y1 + cell_h), outline=(118, 130, 148), fill=fill, width=2)
            value = spec.table[r][c] if c < len(spec.table[r]) else ""
            draw.text((x1 + 15, y1 + 10), value, font=small, fill=(17, 24, 39))
    return y + rows * cell_h + 20


def _graph_xy(diagram: dict[str, Any], x: float, y: float, box: tuple[int, int, int, int]) -> tuple[int, int]:
    left, top, right, bottom = box
    scale_x = (right - left) / 12
    scale_y = (bottom - top) / 12
    return int(left + (x + 6) * scale_x), int(bottom - (y + 6) * scale_y)


def _draw_axes(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    left, top, right, bottom = box
    draw.rectangle(box, outline=(203, 213, 225), width=2)
    for i in range(13):
        x = left + i * (right - left) / 12
        y = top + i * (bottom - top) / 12
        color = (226, 232, 240)
        draw.line((x, top, x, bottom), fill=color, width=1)
        draw.line((left, y, right, y), fill=color, width=1)
    ox, oy = _graph_xy({}, 0, 0, box)
    draw.line((left, oy, right, oy), fill=(71, 85, 105), width=2)
    draw.line((ox, top, ox, bottom), fill=(71, 85, 105), width=2)
    small = _font(20)
    draw.text((right - 18, oy + 4), "x", font=small, fill=(71, 85, 105))
    draw.text((ox + 5, top + 2), "y", font=small, fill=(71, 85, 105))


def _draw_diagram(draw: ImageDraw.ImageDraw, spec: ProblemSpec, x: int, y: int) -> int:
    diagram = spec.diagram or {}
    if not diagram:
        return y
    kind = str(diagram.get("type") or "")
    box = (x, y, x + 430, y + 300)
    small = _font(30)
    tiny = _font(22)

    if kind == "line":
        _draw_axes(draw, box)
        a = float(diagram["a"])
        b = float(diagram["b"])
        points = [_graph_xy(diagram, t, a * t + b, box) for t in [-6, 6]]
        draw.line((*points[0], *points[1]), fill=(37, 99, 235), width=4)
        draw.text((x + 12, y + 12), f"y={int(a)}x{_clean_signed(int(b))}", font=tiny, fill=(37, 99, 235))
        return y + 322

    if kind == "parabola":
        _draw_axes(draw, box)
        h = float(diagram["h"])
        k = float(diagram["k"])
        points = []
        for step in range(-60, 61):
            t = step / 10
            points.append(_graph_xy(diagram, t, (t - h) ** 2 + k, box))
        draw.line(points, fill=(220, 38, 38), width=4)
        vx, vy = _graph_xy(diagram, h, k, box)
        draw.ellipse((vx - 5, vy - 5, vx + 5, vy + 5), fill=(220, 38, 38))
        return y + 322

    if kind == "rectangle":
        w, h = int(diagram["width"]), int(diagram["height"])
        draw.rectangle((x + 52, y + 42, x + 348, y + 210), outline=(30, 64, 175), width=4, fill=(239, 246, 255))
        draw.text((x + 170, y + 218), f"{w} cm", font=small, fill=(17, 24, 39))
        draw.text((x + 360, y + 112), f"{h} cm", font=small, fill=(17, 24, 39))
        return y + 280

    if kind == "circle":
        r = int(diagram["radius"])
        cx, cy = x + 210, y + 150
        draw.ellipse((cx - 110, cy - 110, cx + 110, cy + 110), outline=(124, 58, 237), width=4, fill=(245, 243, 255))
        draw.line((cx, cy, cx + 110, cy), fill=(124, 58, 237), width=3)
        draw.text((cx + 36, cy + 8), f"r={r} cm", font=small, fill=(17, 24, 39))
        return y + 300

    if kind == "right_triangle":
        a, b = int(diagram["a"]), int(diagram["b"])
        p1, p2, p3 = (x + 70, y + 230), (x + 70, y + 70), (x + 330, y + 230)
        draw.polygon((p1, p2, p3), outline=(5, 150, 105), fill=(236, 253, 245))
        draw.line((p1, p2, p3, p1), fill=(5, 150, 105), width=4)
        draw.text((x + 26, y + 142), str(a), font=small, fill=(17, 24, 39))
        draw.text((x + 186, y + 238), str(b), font=small, fill=(17, 24, 39))
        draw.text((x + 93, y + 204), "□", font=tiny, fill=(17, 24, 39))
        return y + 300

    if kind == "coordinate_segment":
        _draw_axes(draw, box)
        p1 = _graph_xy(diagram, float(diagram["x1"]), float(diagram["y1"]), box)
        p2 = _graph_xy(diagram, float(diagram["x2"]), float(diagram["y2"]), box)
        draw.line((*p1, *p2), fill=(14, 165, 233), width=4)
        for label, point in (("A", p1), ("B", p2)):
            draw.ellipse((point[0] - 6, point[1] - 6, point[0] + 6, point[1] + 6), fill=(14, 165, 233))
            draw.text((point[0] + 8, point[1] - 24), label, font=tiny, fill=(17, 24, 39))
        return y + 322

    return y


def render_problem(spec: ProblemSpec, force: bool = False, problem_root: Path | None = None) -> Path:
    root = problem_root or DEFAULT_PROBLEM_ROOT
    target_dir = root / spec.folder
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / spec.file_name
    if target_path.exists() and not force:
        return target_path

    width = 1280
    body_font = _font(48)
    meta_font = _font(26)
    lines = _wrap_lines(spec.lines, width=35 if spec.diagram else 42)
    left_height = 128 + len(lines) * 66 + (len(spec.table) * 64 if spec.table else 0) + 110
    diagram_height = 360 if spec.diagram else 0
    height = max(420, max(left_height, 142 + diagram_height) + 50)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((34, 34, width - 34, height - 34), radius=14, outline=(203, 213, 225), width=2)
    draw.text((72, 58), spec.title, font=meta_font, fill=(71, 85, 105))
    draw.text((width - 230, 58), f"{spec.layout} · {spec.topic}", font=meta_font, fill=(100, 116, 139))
    y = 116
    text_right = 710 if spec.diagram else width - 90
    for line in lines:
        draw.text((84, y), line, font=body_font, fill=(15, 23, 42))
        y += 66
    y += 12
    if spec.table:
        y = _draw_table(draw, spec, 84, y, text_right - 84)
    if spec.diagram:
        _draw_diagram(draw, spec, 780, 126)
    image.save(target_path)
    return target_path


def clean_generated_files(problem_root: Path | None = None) -> None:
    root = problem_root or DEFAULT_PROBLEM_ROOT
    if root.exists():
        shutil.rmtree(root)


def write_manifest(path: Path, records: list[dict[str, Any]], *, output_root: Path, count_per_grade: int, seed: int) -> None:
    by_grade: dict[str, int] = {}
    by_unit: dict[str, int] = {}
    by_layout: dict[str, int] = {}
    for item in records:
        by_grade[f"{item['band']}{item['grade']}"] = by_grade.get(f"{item['band']}{item['grade']}", 0) + 1
        by_unit[str(item["unit"])] = by_unit.get(str(item["unit"]), 0) + 1
        by_layout[str(item["layout"])] = by_layout.get(str(item["layout"]), 0) + 1
    payload = {
        "schema_version": "coco_curriculum_problem_bank_manifest.v1",
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(microsecond=0).isoformat(),
        "source_basis": "2022 개정 수학과 교육과정 단원 흐름 + 자체 생성 문항",
        "external_pdf_policy": "PDF는 로컬 OCR/레이아웃 검증용으로만 사용하고 원문 문항은 복제하지 않음",
        "output_root": str(output_root),
        "count_per_grade": count_per_grade,
        "seed": seed,
        "total": len(records),
        "coverage": {"by_grade": dict(sorted(by_grade.items())), "by_layout": dict(sorted(by_layout.items())), "by_unit": dict(sorted(by_unit.items()))},
        "records": records,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate curriculum-shaped Korean school math problem images.")
    parser.add_argument("--count-per-grade", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260425)
    parser.add_argument("--problem-root", type=Path, default=DEFAULT_PROBLEM_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    if args.count_per_grade <= 0:
        raise SystemExit("--count-per-grade must be positive")
    if args.clean:
        clean_generated_files(args.problem_root)
    specs = generate_specs(args.count_per_grade, args.seed)
    records: list[dict[str, Any]] = []
    for spec in specs:
        image_path = render_problem(spec, force=args.force, problem_root=args.problem_root)
        record = asdict(spec)
        record["image_path"] = str(image_path)
        try:
            record["relative_path"] = str(image_path.relative_to(PROJECT_ROOT))
        except ValueError:
            record["relative_path"] = str(image_path)
        records.append(record)
    write_manifest(args.manifest, records, output_root=args.problem_root, count_per_grade=args.count_per_grade, seed=args.seed)
    print(f"generated_images={len(records)}")
    print(f"manifest={args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
