from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ProblemSchema:
    source_text_candidates: list[str] = field(default_factory=list)
    normalized_problem_text: str = ""
    expressions: list[str] = field(default_factory=list)
    choices: list[str] = field(default_factory=list)
    question_type: str = "subjective"
    math_topic: str = "unknown"
    target_question: str = "문제 풀이"
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)
