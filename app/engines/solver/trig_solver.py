from __future__ import annotations

import re

from app.models.problem_schema import ProblemSchema


TRIG_TABLE = {
    ("cos", "0"): "1",
    ("sin", "0"): "0",
    ("tan", "0"): "0",
    ("cos", "pi/6"): "√3/2",
    ("sin", "pi/6"): "1/2",
    ("tan", "pi/6"): "√3/3",
    ("cos", "pi/4"): "√2/2",
    ("sin", "pi/4"): "√2/2",
    ("tan", "pi/4"): "1",
    ("cos", "pi/3"): "1/2",
    ("sin", "pi/3"): "√3/2",
    ("tan", "pi/3"): "√3",
    ("cos", "pi/2"): "0",
    ("sin", "pi/2"): "1",
    ("cos", "pi"): "-1",
    ("sin", "pi"): "0",
    ("tan", "pi"): "0",
    ("cos", "3pi/2"): "0",
    ("sin", "3pi/2"): "-1",
    ("cos", "2pi"): "1",
    ("sin", "2pi"): "0",
    ("tan", "2pi"): "0",
}


def solve(problem: ProblemSchema) -> dict:
    text = " ".join(problem.expressions or [problem.normalized_problem_text])
    match = re.search(r"(cos|sin|tan)\(([^)]+)\)", text, flags=re.IGNORECASE)
    if not match:
        return {"computed_answer": "", "steps": [], "confidence": 0.0}
    trig_name = match.group(1).lower()
    angle = match.group(2).replace(" ", "")
    angle = angle.replace("1pi", "pi")
    answer = TRIG_TABLE.get((trig_name, angle), "")
    if not answer:
        return {"computed_answer": "", "steps": [], "confidence": 0.0}
    return {
        "computed_answer": answer,
        "steps": [
            "이건 삼각함수 값 문제야.",
            f"{trig_name}({angle.replace('pi', 'π')})를 단위원에서 보면 바로 읽을 수 있어.",
            f"그래서 값은 {answer}야.",
        ],
        "confidence": 0.96,
    }
