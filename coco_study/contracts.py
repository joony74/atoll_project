from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProblemRecord:
    problem_id: str
    file_id: str = ""
    parent_problem_id: str | None = None
    display_number: int = 0
    question_text: str = ""
    equation_text: str = ""
    problem_text: str = ""
    problem_type: str = ""
    concept_tags: list[str] = field(default_factory=list)
    difficulty: int | str = "medium"
    status: str = "needs_review"
    answer: str = ""
    solution_steps: list[str] = field(default_factory=list)
    followup_history: list[dict[str, Any]] = field(default_factory=list)
    generated_next: list[str] = field(default_factory=list)
    solver: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    generation_mode: str | None = None
    created_at: float | None = None


@dataclass(slots=True)
class CommandIntent:
    intent: str
    target_problem_id: str | None = None
    payload: Any = None
    learning_offset: int | None = None
    learning_badge: str | None = None


@dataclass(slots=True)
class CommandRouteResult:
    answer: str
    router: CommandIntent


@dataclass(slots=True)
class PersistedDocument:
    file_id: str
    file_name: str
    file_path: str
    uploaded_at: float | None = None
    analysis_result: dict[str, Any] = field(default_factory=dict)
    problems: list[dict[str, Any]] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    active_problem_id: str | None = None
