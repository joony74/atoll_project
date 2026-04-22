from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engines.knowledge_engine import KnowledgeManager


def record_feedback(
    problem_text: str,
    concept_analysis: dict,
    understanding_result: dict | None,
    feedback_text: str,
    knowledge_manager: "KnowledgeManager",
) -> dict:
    payload = {
        "problem_text": problem_text,
        "concepts": concept_analysis.get("core_concepts", []),
        "understanding_result": understanding_result,
        "feedback_text": feedback_text,
    }
    knowledge_manager.save_feedback(payload)
    knowledge_manager.record_stat("feedback_saved", {"concepts": concept_analysis.get("core_concepts", [])})
    return {"status": "saved", "message": "피드백을 저장했고 다음 설명에 반영할 준비를 마쳤어요."}
