from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class CommandSchema:
    intent: str
    target_problem_id: str | None
    payload: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

