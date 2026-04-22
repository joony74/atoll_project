from __future__ import annotations


def build_progression_reply(problem_context: dict, document_bundle: dict) -> dict:
    concepts = problem_context.get("concepts") or []
    unit = str(problem_context.get("unit") or "").strip()
    if concepts:
        suggestion = f"다음에는 {concepts[0]}를 같은 형식으로 한 문제 더 이어가면 좋습니다."
    elif unit:
        suggestion = f"다음에는 {unit} 단원 안에서 비슷한 유형을 한 문제 더 이어가면 좋습니다."
    else:
        suggestion = "다음에는 같은 유형 문제를 한 단계만 더 이어서 연습하면 좋습니다."
    return {
        "mode": "problem",
        "answer": suggestion,
        "summary": suggestion,
        "next_questions": ["원하면 비슷한 문제 방향으로 바로 이어갈 수 있어요."],
        "confidence": 0.66,
        "used_sources": ["progression"],
        "missing_fields": [],
    }

