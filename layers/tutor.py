from __future__ import annotations


def compose_tutor_reply(
    command: dict,
    solver_result: dict,
    problem_context: dict,
    document_bundle: dict,
    memory_snapshot: dict,
) -> str:
    intent = command.get("intent")
    mode = solver_result.get("mode")
    answer = str(solver_result.get("answer") or "").strip()
    next_question = ""
    next_questions = solver_result.get("next_questions") or []
    if next_questions:
        next_question = str(next_questions[0]).strip()

    if mode == "problem":
        if intent == "greeting":
            opening = "좋아요. 지금 선택된 파일은 문제 문맥으로 이어서 볼 수 있어요."
        elif intent == "hint_request":
            opening = "힌트부터 짧게 잡아보면 이렇게 갈 수 있어요."
        elif intent == "answer_request":
            opening = "현재 저장된 풀이 자산 기준으로 보면 이렇게 정리됩니다."
        elif intent in {"re_explain_request", "explain_request"}:
            opening = "현재 문제를 기준으로 핵심 풀이만 다시 정리해볼게요."
        elif intent == "low_confidence_followup":
            opening = "지금 파일 기준으로 확인되는 문제 상태부터 잡아보면 이렇습니다."
        else:
            opening = "현재 문제 기준으로 바로 이어서 정리해볼게요."
    elif mode == "document":
        if intent == "greeting":
            opening = "좋아요. 현재 문서 기준으로 핵심 내용부터 짧게 볼게요."
        else:
            opening = "현재 문서에 저장된 분석 결과를 기준으로 정리해보면 이렇습니다."
    else:
        opening = "현재 저장된 분석 범위에서 먼저 확인되는 내용은 이렇습니다."

    parts = [opening]
    if answer:
        parts.append(answer)
    if document_bundle.get("text_quality_message") and not answer:
        parts.append(document_bundle["text_quality_message"])
    if next_question:
        parts.append(next_question)
    return "\n\n".join([part for part in parts if str(part).strip()]).strip()

