from __future__ import annotations

from typing import Any


def _problem_text(problem: dict[str, Any]) -> str:
    return str(problem.get("problem_text") or problem.get("question_text") or "문제 내용을 확인하지 못했습니다.").strip()


def _steps(problem: dict[str, Any]) -> list[str]:
    return [str(step).strip() for step in (problem.get("solution_steps") or []) if str(step).strip()]


def re_explain(problem: dict[str, Any], mode: str = "normal") -> dict[str, Any]:
    steps = _steps(problem)
    answer = str(problem.get("answer") or "").strip()
    question = _problem_text(problem)

    if not steps:
        return {
            "status": "failed",
            "mode": "error",
            "response": "현재 문제의 검증된 풀이 단계가 아직 없어 다시 설명하기 어렵습니다.",
        }

    if mode == "simple":
        picked = steps[:2] if len(steps) >= 2 else steps
        response = "\n".join(
            [
                f"문제는 {question}",
                "쉽게 다시 말하면,",
                *[f"- {step}" for step in picked],
                f"그래서 정답은 {answer or '아직 계산되지 않았습니다'}입니다.",
            ]
        )
        return {"status": "completed", "mode": "re_explain_simple", "response": response}

    if mode == "summary":
        summary_line = steps[0]
        if answer:
            summary_line = f"{summary_line} 그래서 정답은 {answer}입니다."
        return {"status": "completed", "mode": "re_explain_summary", "response": summary_line}

    response = "\n".join(
        [
            f"문제: {question}",
            "풀이를 다시 설명하면,",
            *[f"{idx}. {step}" for idx, step in enumerate(steps, start=1)],
            f"정답: {answer or '아직 계산되지 않았습니다.'}",
        ]
    )
    return {"status": "completed", "mode": "re_explain", "response": response}

