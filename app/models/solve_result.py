from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class SolveResult:
    solver_name: str = "unsolved"
    computed_answer: str = ""
    steps: list[str] = field(default_factory=list)
    matched_choice: str = ""
    confidence: float = 0.0
    validation_status: str = "failed"
    explanation: str = ""
    debug: dict[str, Any] = field(default_factory=dict)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)
