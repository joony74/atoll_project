from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProblemSchema(BaseModel):
    source_text_candidates: list[str] = Field(default_factory=list)
    normalized_problem_text: str = ""
    expressions: list[str] = Field(default_factory=list)
    choices: list[str] = Field(default_factory=list)
    question_type: str = "subjective"
    math_topic: str = "unknown"
    target_question: str = "문제 풀이"
    confidence: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
