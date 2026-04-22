from __future__ import annotations


def build_math_handoff_reply(has_documents: bool) -> str:
    if has_documents:
        return "지금도 간단히 같이 볼 수는 있는데, 학습리스트를 선택하면 더 깊게 분석할 수 있어요."
    return "지금도 가볍게 같이 볼 수는 있어요. 다만 학습리스트를 생성하면 더 깊게 분석할 수 있어요."
