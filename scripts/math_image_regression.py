from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROBLEM_ROOT = PROJECT_ROOT / "02.학습문제"
REPORT_PATH = PROJECT_ROOT / "data" / "learning_test" / "math_image_regression_report.json"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image, ImageDraw, ImageFont

from app.core.pipeline import run_solve_pipeline
FONT_CANDIDATES = (
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
)


@dataclass(frozen=True, slots=True)
class ImageCase:
    case_id: str
    band: str
    folder: str
    file_name: str
    lines: tuple[str, ...]
    expected_answer: str
    expected_topic: str
    expected_expression_hint: str


@dataclass(slots=True)
class CaseResult:
    case_id: str
    image_path: str
    passed: bool
    expected_answer: str
    computed_answer: str
    matched_choice: str
    expected_topic: str
    topic: str
    recognized_text: str
    expressions: list[str]
    solver_name: str
    validation_status: str
    confidence: float
    bottlenecks: list[str]


CASES: tuple[ImageCase, ...] = (
    ImageCase(
        case_id="elementary_arithmetic_01",
        band="초등",
        folder="01.초등/3학년",
        file_name="auto_초등_사칙연산_01.png",
        lines=("다음 식의 값을 구하시오.", "12 + 8 = ?"),
        expected_answer="20",
        expected_topic="arithmetic",
        expected_expression_hint="12 + 8",
    ),
    ImageCase(
        case_id="middle_linear_equation_01",
        band="중등",
        folder="02.중등",
        file_name="auto_중등_일차방정식_01.png",
        lines=("다음 방정식을 푸시오.", "2x + 3 = 11", "x의 값은?"),
        expected_answer="4",
        expected_topic="linear_equation",
        expected_expression_hint="2x + 3 = 11",
    ),
    ImageCase(
        case_id="high_radical_power_01",
        band="고등",
        folder="03.고등",
        file_name="auto_고등_루트거듭제곱_01.png",
        lines=("다음 식의 값을 구하시오.", "sqrt(16) + 2^3"),
        expected_answer="12",
        expected_topic="radical_power",
        expected_expression_hint="sqrt(16) + 2^3",
    ),
)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap_lines(lines: tuple[str, ...], width: int = 26) -> list[str]:
    wrapped: list[str] = []
    for line in lines:
        parts = textwrap.wrap(line, width=width, break_long_words=False, replace_whitespace=False)
        wrapped.extend(parts or [line])
    return wrapped


def generate_case_image(case: ImageCase, force: bool = False) -> Path:
    target_dir = PROBLEM_ROOT / case.folder
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / case.file_name
    if target_path.exists() and not force:
        return target_path

    title_font = _font(34)
    body_font = _font(46)
    lines = _wrap_lines(case.lines)
    width = 980
    height = max(360, 130 + len(lines) * 72)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((28, 28, width - 28, height - 28), radius=18, outline=(190, 198, 210), width=3)
    draw.text((64, 58), f"{case.band} 자동 점검 문제", font=title_font, fill=(20, 28, 40))
    y = 126
    for line in lines:
        draw.text((78, y), line, font=body_font, fill=(0, 0, 0))
        y += 72
    image.save(target_path)
    return target_path


def _normalize_answer(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\.0+$", "", text)
    return text


def _contains_expression_hint(expressions: list[str], hint: str) -> bool:
    compact_hint = re.sub(r"\s+", "", hint).lower()
    for expression in expressions:
        compact = re.sub(r"\s+", "", str(expression or "")).lower()
        if compact_hint in compact or compact in compact_hint:
            return True
    return False


def _diagnose(case: ImageCase, problem: Any, solved: Any) -> list[str]:
    bottlenecks: list[str] = []
    expressions = list(problem.expressions or [])
    computed_answer = _normalize_answer(getattr(solved, "computed_answer", "") or "")
    matched_choice = _normalize_answer(getattr(solved, "matched_choice", "") or "")
    topic = str(problem.math_topic or "")

    if not _contains_expression_hint(expressions, case.expected_expression_hint):
        bottlenecks.append("expression_recognition")
    if topic != case.expected_topic:
        bottlenecks.append("topic_classification")
    if computed_answer != case.expected_answer and matched_choice != case.expected_answer:
        bottlenecks.append("solver_or_answer")
    if getattr(solved, "validation_status", "") == "failed":
        bottlenecks.append("validation_failed")
    return bottlenecks


def run_case(case: ImageCase, force_generate: bool = False) -> CaseResult:
    image_path = generate_case_image(case, force=force_generate)
    payload = run_solve_pipeline(image_path=str(image_path), debug=True)
    problem = payload["structured_problem"]
    solved = payload["solve_result"]

    computed_answer = _normalize_answer(getattr(solved, "computed_answer", "") or "")
    matched_choice = _normalize_answer(getattr(solved, "matched_choice", "") or "")
    bottlenecks = _diagnose(case, problem, solved)
    passed = not bottlenecks
    return CaseResult(
        case_id=case.case_id,
        image_path=str(image_path),
        passed=passed,
        expected_answer=case.expected_answer,
        computed_answer=computed_answer,
        matched_choice=matched_choice,
        expected_topic=case.expected_topic,
        topic=str(problem.math_topic or ""),
        recognized_text=str(problem.normalized_problem_text or ""),
        expressions=list(problem.expressions or []),
        solver_name=str(getattr(solved, "solver_name", "") or ""),
        validation_status=str(getattr(solved, "validation_status", "") or ""),
        confidence=float(getattr(solved, "confidence", 0.0) or 0.0),
        bottlenecks=bottlenecks,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate school math images and run CocoAi image-analysis regression.")
    parser.add_argument("--force-generate", action="store_true", help="Regenerate PNG fixtures even when files already exist.")
    parser.add_argument("--report", type=Path, default=REPORT_PATH, help="JSON report path.")
    args = parser.parse_args()

    results = [run_case(case, force_generate=args.force_generate) for case in CASES]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps([asdict(item) for item in results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for result in results:
        mark = "PASS" if result.passed else "FAIL"
        print(f"{mark} {result.case_id}")
        print(f"  image: {result.image_path}")
        print(f"  text: {result.recognized_text}")
        print(f"  expressions: {result.expressions}")
        print(f"  topic: {result.topic} expected={result.expected_topic}")
        print(f"  answer: {result.computed_answer or result.matched_choice} expected={result.expected_answer}")
        if result.bottlenecks:
            print(f"  bottlenecks: {', '.join(result.bottlenecks)}")
    print(f"report: {args.report}")
    return 0 if all(item.passed for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
