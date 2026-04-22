from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SolveResult(BaseModel):
    solver_name: str = "unsolved"
    computed_answer: str = ""
    steps: list[str] = Field(default_factory=list)
    matched_choice: str = ""
    confidence: float = 0.0
    validation_status: str = "failed"
    explanation: str = ""
    debug: dict[str, Any] = Field(default_factory=dict)
