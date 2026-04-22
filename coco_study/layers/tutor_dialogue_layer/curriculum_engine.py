from __future__ import annotations

from typing import Any


def decide_curriculum_action(memory: dict[str, Any], understanding_result: dict[str, Any]) -> dict[str, str]:
    level = str(understanding_result.get("level") or "partial")
    understood_streak = int(memory.get("understood_streak", 0) or 0)
    partial_streak = int(memory.get("partial_streak", 0) or 0)
    misunderstood_streak = int(memory.get("misunderstood_streak", 0) or 0)
    unit_attempts = int(memory.get("unit_attempts", 0) or 0)

    if level == "understood" and understood_streak >= 2:
        return {
            "action": "advance",
            "reason": "같은 단원에서 이해 신호가 두 번 이어져 다음 단원으로 넘어갈 준비가 됐어요.",
        }
    if level == "partial" and partial_streak >= 2:
        return {
            "action": "reinforce",
            "reason": "방향은 맞지만 아직 불안정해서 같은 단원을 한 번 더 단단하게 잡는 게 좋아요.",
        }
    if level == "misunderstood" or misunderstood_streak >= 1:
        return {
            "action": "repeat",
            "reason": "핵심 개념을 다시 세우는 쪽이 더 좋아 보여요.",
        }
    if unit_attempts >= 4:
        return {
            "action": "reinforce",
            "reason": "같은 단원에 오래 머물렀으니 질문 강도를 낮추고 설명 방식을 바꾸는 게 좋아요.",
        }
    return {
        "action": "continue",
        "reason": "아직은 같은 흐름으로 한 번 더 이어가면 돼요.",
    }
