from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class SessionState:
    current_file_id: str | None = None
    current_problem_id: str | None = None
    active_problem_stack: list[str] = field(default_factory=list)
    last_action: str | None = None
    last_opened_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_session_state() -> dict[str, Any]:
    return SessionState().to_dict()
