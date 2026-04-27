from __future__ import annotations

import argparse
import json
import random
import shutil
import textwrap
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROBLEM_ROOT = PROJECT_ROOT / "02.학습문제"
MANIFEST_PATH = PROJECT_ROOT / "data" / "learning_test" / "school_math_bank_manifest.json"

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


@dataclass(frozen=True, slots=True)
class ProblemSpec:
    problem_id: str
    band: str
    grade: int
    difficulty: str
    layout: str
    topic: str
    folder: str
    file_name: str
    title: str
    lines: tuple[str, ...]
    expected_answer: str
    expected_expression: str
    table: tuple[tuple[str, ...], ...] = ()


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


def _layout(index: int) -> str:
    mod = index % 5
    if mod == 0:
        return "table"
    if mod in {2, 4}:
        return "word"
    return "expression"


def _frac_text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _clean_number(value: float) -> str:
    rounded = round(value)
    if abs(value - rounded) < 1e-9:
        return str(int(rounded))
    return f"{value:.6g}"


def _make_elementary(grade: int, index: int, rng: random.Random) -> tuple[str, tuple[str, ...], str, str, str, tuple[tuple[str, ...], ...]]:
    layout = _layout(index)
    difficulty = _difficulty(index)
    topic = "arithmetic"
    table: tuple[tuple[str, ...], ...] = ()

    if grade <= 2:
        a = rng.randint(8 + grade * 4, 38 + grade * 22)
        b = rng.randint(3, 18 + grade * 8)
        if difficulty == "hard":
            c = rng.randint(2, 9 + grade)
            expr = f"{a} + {b} - {c}"
            answer = str(a + b - c)
            operation = "mix"
        elif index % 2:
            expr = f"{a} + {b}"
            answer = str(a + b)
            operation = "add"
        else:
            a, b = max(a, b), min(a, b)
            expr = f"{a} - {b}"
            answer = str(a - b)
            operation = "sub"
        if layout == "word":
            if operation == "add":
                return (
                    topic,
                    (f"연필이 {a}자루 있고 {b}자루를 더 샀습니다.", "연필은 모두 몇 자루입니까?"),
                    answer,
                    expr,
                    "서술형",
                    table,
                )
            if operation == "sub":
                return (
                    topic,
                    (f"연필이 {a}자루 있습니다.", f"그중 {b}자루를 친구에게 주었습니다.", "남은 연필은 몇 자루입니까?"),
                    answer,
                    expr,
                    "서술형",
                    table,
                )
            return (
                topic,
                (f"연필이 {a}자루 있고 {b}자루를 더 샀습니다.", f"그중 {c}자루를 사용했습니다.", "남은 연필은 몇 자루입니까?"),
                answer,
                expr,
                "서술형",
                table,
            )
        if layout == "table":
            x = rng.randint(5, 14)
            y = rng.randint(6, 16)
            z = rng.randint(3, 12)
            answer = str(x + y + z)
            table = (("종류", "사과", "배", "귤"), ("개수", str(x), str(y), str(z)))
            return (topic, ("아래 표의 과일은 모두 몇 개입니까?",), answer, f"{x}+{y}+{z}", "표", table)
        return (topic, ("다음 식의 값을 구하시오.", f"{expr} = ?"), answer, expr, "식", table)

    if grade <= 4:
        if index % 3 == 0:
            a = rng.randint(3, 9)
            b = rng.randint(12, 36)
            expr = f"{a} * {b}"
            answer = str(a * b)
            topic = "arithmetic"
        elif index % 3 == 1:
            d = rng.randint(2, 9)
            q = rng.randint(4, 18)
            expr = f"{d * q} / {d}"
            answer = str(q)
            topic = "arithmetic"
        else:
            denominator = rng.choice([4, 5, 6, 8, 10, 12])
            n1 = rng.randint(1, denominator - 2)
            n2 = rng.randint(1, denominator - n1 - 1)
            expr = f"{n1}/{denominator} + {n2}/{denominator}"
            answer = _frac_text(Fraction(n1, denominator) + Fraction(n2, denominator))
            topic = "fraction_ratio"
        if layout == "word":
            a = rng.randint(4, 9)
            b = rng.randint(7, 15)
            answer = str(a * b)
            return (
                "arithmetic",
                (f"한 상자에 공책이 {b}권씩 들어 있습니다.", f"{a}상자에는 공책이 모두 몇 권입니까?"),
                answer,
                f"{a}*{b}",
                "서술형",
                table,
            )
        if layout == "table":
            rows = [rng.randint(8, 24) for _ in range(3)]
            answer = str(sum(rows))
            table = (("요일", "월", "화", "수"), ("읽은 쪽수", *(str(item) for item in rows)))
            return ("statistics", ("아래 표에서 3일 동안 읽은 쪽수의 합을 구하시오.",), answer, "+".join(map(str, rows)), "표", table)
        return (topic, ("다음 식의 값을 구하시오.", f"{expr} = ?"), answer, expr, "식", table)

    if index % 4 == 0:
        a = Fraction(rng.randint(1, 5), rng.choice([6, 8, 10, 12]))
        b = Fraction(rng.randint(1, 5), rng.choice([6, 8, 10, 12]))
        expr = f"{a.numerator}/{a.denominator} + {b.numerator}/{b.denominator}"
        answer = _frac_text(a + b)
        topic = "fraction_ratio"
    elif index % 4 == 1:
        price = rng.randint(12, 48) * 100
        percent = rng.choice([10, 20, 25, 30, 40])
        expr = f"{price} * {percent} / 100"
        answer = str(price * percent // 100)
        topic = "fraction_ratio"
    elif index % 4 == 2:
        width = rng.randint(6, 18)
        height = rng.randint(4, 14)
        expr = f"{width} * {height}"
        answer = str(width * height)
        topic = "geometry"
    else:
        values = [rng.randint(60, 95) for _ in range(3)]
        expr = f"({values[0]} + {values[1]} + {values[2]}) / 3"
        answer = _clean_number(sum(values) / 3)
        topic = "statistics"
    if layout == "word":
        speed = rng.randint(40, 80)
        hours = rng.randint(2, 5)
        answer = str(speed * hours)
        return (
            "fraction_ratio",
            (f"시속 {speed} km로 {hours}시간 동안 이동했습니다.", "이동한 거리는 몇 km입니까?"),
            answer,
            f"{speed}*{hours}",
            "서술형",
            table,
        )
    if layout == "table":
        values = [rng.randint(10, 40) for _ in range(4)]
        answer = str(max(values) - min(values))
        table = (("반", "1반", "2반", "3반", "4반"), ("인원", *(str(item) for item in values)))
        return ("statistics", ("아래 표에서 가장 많은 반과 가장 적은 반의 인원 차를 구하시오.",), answer, f"{max(values)}-{min(values)}", "표", table)
    return (topic, ("다음 문제를 계산하시오.", f"{expr} = ?"), answer, expr, "식", table)


def _make_middle(grade: int, index: int, rng: random.Random) -> tuple[str, tuple[str, ...], str, str, str, tuple[tuple[str, ...], ...]]:
    layout = _layout(index)
    topic = "linear_equation"
    table: tuple[tuple[str, ...], ...] = ()

    if grade == 1:
        x = rng.randint(-9, 12)
        a = rng.choice([2, 3, 4, 5, 6])
        b = rng.randint(-12, 18)
        c = a * x + b
        expr = f"{a}x + {b} = {c}"
        answer = str(x)
        if layout == "word":
            return (
                topic,
                (f"어떤 수 x에 {a}를 곱하고 {b}를 더했더니 {c}가 되었습니다.", "x의 값을 구하시오."),
                answer,
                expr,
                "서술형",
                table,
            )
        if layout == "table":
            xs = [x - 1, x, x + 1]
            ys = [a * item + b for item in xs]
            table = (("x", *(str(item) for item in xs)), ("y", *(str(item) for item in ys)))
            return ("function", (f"일차식 y = {a}x + {b}의 값 표입니다.", f"y가 {c}일 때 x의 값은?"), answer, expr, "표", table)
        return (topic, ("다음 방정식을 푸시오.", expr), answer, expr, "식", table)

    if grade == 2:
        a = rng.choice([2, 3, 4, 5])
        b = rng.randint(-7, 9)
        x = rng.randint(-5, 8)
        y = a * x + b
        expr = f"y = {a}x + {b}"
        answer = str(y)
        if layout == "word":
            return (
                "function",
                (f"일차함수 {expr}에서 x = {x}입니다.", "이때 y의 값을 구하시오."),
                answer,
                f"{expr}; x={x}",
                "서술형",
                table,
            )
        if layout == "table":
            xs = [x - 1, x, x + 1]
            ys = [a * item + b for item in xs]
            table = (("x", *(str(item) for item in xs)), ("y", *(str(item) for item in ys)))
            return ("function", ("아래 표는 일차함수의 일부입니다.", f"x = {x}일 때 y의 값은?"), answer, expr, "표", table)
        return ("function", (f"일차함수 {expr}에서", f"x = {x}일 때 y의 값을 구하시오."), answer, expr, "식", table)

    if index % 3 == 0:
        r = rng.randint(2, 9)
        expr = f"sqrt({r * r}) + {rng.randint(1, 8)}"
        answer = str(r + int(expr.rsplit("+", 1)[1]))
        topic = "radical_power"
    elif index % 3 == 1:
        x = rng.randint(-6, 6) or 3
        p = rng.randint(-5, 5)
        q = x * x + p * x
        expr = f"x^2 + {p}x = {q}"
        roots = sorted({x, -p - x})
        answer = ", ".join(str(item) for item in roots)
        topic = "quadratic"
    else:
        a = rng.randint(3, 9)
        b = rng.randint(4, 12)
        c = int((a * a + b * b) ** 0.5)
        if c * c != a * a + b * b:
            a, b, c = 3, 4, 5
        expr = f"sqrt({a*a} + {b*b})"
        answer = str(c)
        topic = "geometry"
    if layout == "word":
        if topic == "quadratic":
            return (topic, ("다음 이차방정식의 해를 모두 구하시오.", expr), answer, expr, "서술형", table)
        return (topic, ("다음 조건을 만족하는 값을 구하시오.", expr), answer, expr, "서술형", table)
    if layout == "table":
        values = [rng.randint(1, 6) for _ in range(3)]
        answer = str(sum(values) * 2)
        table = (("항목", "A", "B", "C"), ("개수", *(str(item) for item in values)))
        return ("statistics", ("표의 개수 합의 2배를 구하시오.",), answer, f"({'+'.join(map(str, values))})*2", "표", table)
    return (topic, ("다음 식의 값을 구하시오.", expr), answer, expr, "식", table)


def _make_high(grade: int, index: int, rng: random.Random) -> tuple[str, tuple[str, ...], str, str, str, tuple[tuple[str, ...], ...]]:
    layout = _layout(index)
    table: tuple[tuple[str, ...], ...] = ()

    if grade == 1:
        if index % 3 == 0:
            x = rng.randint(-5, 6) or 2
            a = rng.choice([1, 2, 3])
            b = rng.randint(-6, 6)
            c = rng.randint(-8, 8)
            expr = f"{a}x^2 + {b}x + {c}"
            answer = str(a * x * x + b * x + c)
            topic = "quadratic"
            lines = (f"다항식 f(x) = {expr}에서", f"f({x})의 값을 구하시오.")
            expected_expr = f"{expr}; x={x}"
        elif index % 3 == 1:
            n = rng.randint(4, 12)
            a1 = rng.randint(1, 9)
            d = rng.randint(2, 6)
            answer = str(a1 + (n - 1) * d)
            topic = "sequence"
            lines = (f"등차수열의 첫째항이 {a1}, 공차가 {d}입니다.", f"제 {n}항을 구하시오.")
            expected_expr = f"{a1}+({n}-1)*{d}"
        else:
            a = rng.randint(2, 8)
            b = rng.randint(2, 5)
            expr = f"sqrt({a*a}) + {b}^2"
            answer = str(a + b * b)
            topic = "radical_power"
            lines = ("다음 식의 값을 구하시오.", expr)
            expected_expr = expr
    elif grade == 2:
        if index % 3 == 0:
            k = rng.choice([2, 3, 4, 5])
            n = rng.randint(2, 4)
            expr = f"log_{k}({k**n})"
            answer = str(n)
            topic = "logarithm"
            lines = ("다음 로그의 값을 구하시오.", expr)
            expected_expr = expr
        elif index % 3 == 1:
            trig = rng.choice([("sin(pi/6)", "1/2"), ("cos(pi/3)", "1/2"), ("tan(pi/4)", "1")])
            add = rng.choice([("sin(pi/6)", "1/2"), ("cos(pi/3)", "1/2")])
            expr = f"{trig[0]} + {add[0]}"
            answer = _frac_text(Fraction(trig[1]) + Fraction(add[1]))
            topic = "trigonometry"
            lines = ("다음 삼각함수 값을 구하시오.", expr)
            expected_expr = expr
        else:
            total = rng.randint(20, 40)
            chosen = rng.randint(4, total - 4)
            answer = _frac_text(Fraction(chosen, total))
            topic = "probability"
            lines = (f"공 {total}개 중 빨간 공이 {chosen}개입니다.", "임의로 하나를 뽑을 때 빨간 공일 확률은?")
            expected_expr = f"{chosen}/{total}"
    else:
        if index % 3 == 0:
            a = rng.randint(2, 6)
            b = rng.randint(-5, 5)
            x = rng.randint(-3, 5)
            expr = f"{a}x^2 + {b}x"
            answer = str(2 * a * x + b)
            topic = "calculus_derivative"
            lines = (f"f(x) = {expr}일 때", f"f'({x})의 값을 구하시오.")
            expected_expr = f"2*{a}*{x}+{b}"
        elif index % 3 == 1:
            a = rng.randint(1, 5)
            b = rng.randint(1, 6)
            answer = str(a * b)
            topic = "calculus_integral"
            lines = (f"함수 f(x) = {a}의 그래프와 x축 사이의", f"0 <= x <= {b} 구간 넓이를 구하시오.")
            expected_expr = f"{a}*{b}"
        else:
            values = [rng.randint(60, 100) for _ in range(5)]
            answer = _clean_number(sum(values) / len(values))
            topic = "statistics"
            lines = ("다음 자료의 평균을 구하시오.", ", ".join(map(str, values)))
            expected_expr = f"({'+'.join(map(str, values))})/5"

    if layout == "table":
        xs = [1, 2, 3, 4]
        ys = [rng.randint(2, 8) * x + rng.randint(0, 4) for x in xs]
        answer = str(max(ys) - min(ys))
        table = (("x", *(str(item) for item in xs)), ("y", *(str(item) for item in ys)))
        return ("statistics", ("아래 표에서 y의 최댓값과 최솟값의 차를 구하시오.",), answer, f"{max(ys)}-{min(ys)}", "표", table)
    if layout == "word":
        return (topic, lines, answer, expected_expr, "서술형", table)
    return (topic, lines, answer, expected_expr, "식", table)


def make_problem(band: str, folder_name: str, grade: int, index: int, seed: int) -> ProblemSpec:
    rng = random.Random(seed + grade * 1000 + index)
    if band == "초등":
        topic, lines, answer, expr, layout_label, table = _make_elementary(grade, index, rng)
    elif band == "중등":
        topic, lines, answer, expr, layout_label, table = _make_middle(grade, index, rng)
    else:
        topic, lines, answer, expr, layout_label, table = _make_high(grade, index, rng)

    difficulty = _difficulty(index)
    layout = _layout(index)
    prefix = {"초등": "elementary", "중등": "middle", "고등": "high"}[band]
    problem_id = f"{prefix}_g{grade:02d}_{index:03d}"
    file_name = f"{problem_id}_{difficulty}_{layout}.png"
    folder = f"{folder_name}/{grade}학년"
    title = f"{band} {grade}학년 {layout_label} 문제 · {difficulty}"
    return ProblemSpec(
        problem_id=problem_id,
        band=band,
        grade=grade,
        difficulty=difficulty,
        layout=layout,
        topic=topic,
        folder=folder,
        file_name=file_name,
        title=title,
        lines=tuple(lines),
        expected_answer=answer,
        expected_expression=expr,
        table=table,
    )


def generate_specs(count_per_grade: int, seed: int) -> list[ProblemSpec]:
    specs: list[ProblemSpec] = []
    for folder_name, band, grades in BANDS:
        for grade in grades:
            for index in range(1, count_per_grade + 1):
                specs.append(make_problem(band, folder_name, grade, index, seed))
    return specs


def _wrap_lines(lines: tuple[str, ...], width: int = 34) -> list[str]:
    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(textwrap.wrap(line, width=width, break_long_words=False, replace_whitespace=False) or [line])
    return wrapped


def render_problem(spec: ProblemSpec, force: bool = False, problem_root: Path | None = None) -> Path:
    root = problem_root or PROBLEM_ROOT
    target_dir = root / spec.folder
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / spec.file_name
    if target_path.exists() and not force:
        return target_path

    body_font = _font(54)
    small_font = _font(36)
    lines = _wrap_lines(spec.lines)
    table_height = 0 if not spec.table else len(spec.table) * 58 + 28
    height = max(380, 90 + len(lines) * 78 + table_height + 70)
    width = 1180
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((34, 34, width - 34, height - 34), radius=12, outline=(205, 213, 225), width=2)
    y = 76
    for line in lines:
        draw.text((84, y), line, font=body_font, fill=(0, 0, 0))
        y += 78

    if spec.table:
        y += 16
        rows = len(spec.table)
        cols = max(len(row) for row in spec.table)
        cell_w = min(210, (width - 168) // max(cols, 1))
        cell_h = 58
        x0 = 84
        for r in range(rows):
            for c in range(cols):
                x1 = x0 + c * cell_w
                y1 = y + r * cell_h
                fill = (244, 247, 251) if r == 0 or c == 0 else (255, 255, 255)
                draw.rectangle((x1, y1, x1 + cell_w, y1 + cell_h), outline=(120, 132, 150), fill=fill, width=2)
                value = spec.table[r][c] if c < len(spec.table[r]) else ""
                draw.text((x1 + 18, y1 + 10), value, font=small_font, fill=(0, 0, 0))

    image.save(target_path)
    return target_path


def clean_generated_files(problem_root: Path | None = None) -> None:
    root = problem_root or PROBLEM_ROOT
    for folder_name, _, grades in BANDS:
        for grade in grades:
            folder = root / folder_name / f"{grade}학년"
            if folder.exists():
                shutil.rmtree(folder)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a grade-by-grade school math image bank.")
    parser.add_argument("--count-per-grade", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260425)
    parser.add_argument("--force", action="store_true", help="Overwrite existing images.")
    parser.add_argument("--clean", action="store_true", help="Remove generated grade folders before rendering.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--problem-root", type=Path, default=PROBLEM_ROOT)
    args = parser.parse_args()

    if args.count_per_grade <= 0:
        raise SystemExit("--count-per-grade must be positive")
    if args.clean:
        clean_generated_files(args.problem_root)

    specs = generate_specs(args.count_per_grade, args.seed)
    records = []
    for spec in specs:
        image_path = render_problem(spec, force=args.force, problem_root=args.problem_root)
        record = asdict(spec)
        record["image_path"] = str(image_path)
        record["relative_path"] = str(image_path.relative_to(PROJECT_ROOT))
        records.append(record)

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    by_grade: dict[str, int] = {}
    for spec in specs:
        key = f"{spec.band}{spec.grade}"
        by_grade[key] = by_grade.get(key, 0) + 1
    print(f"generated_images={len(records)}")
    print(f"manifest={args.manifest}")
    for key in sorted(by_grade):
        print(f"{key}: {by_grade[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
