from __future__ import annotations

from .contracts import ConceptSearchResult, GroundingResult

_CONCEPT_FOLLOWUP_DETAILS: dict[str, str] = {
    "수학": "조금 더 풀어서 말하면, 수학은 숫자를 계산하는 기술만이 아니라 어떤 규칙이 왜 성립하는지 이해하고 관계를 설명하는 방식에 가까워요. 그래서 문제를 푸는 도구이기도 하지만, 세상을 구조적으로 보는 훈련이 되기도 해요.",
    "함수": "조금 더 풀어서 말하면, 함수는 입력과 출력 사이의 약속이라고 볼 수 있어요. 같은 입력이 들어오면 항상 같은 결과가 나온다는 점이 핵심이라서, 변화의 규칙을 다룰 때 자주 쓰여요.",
    "미분": "조금 더 풀어서 말하면, 미분은 순간적인 변화율을 보는 개념이에요. 어떤 값이 지금 이 순간 얼마나 빠르게 바뀌는지 알고 싶을 때 쓰는 도구라고 보면 돼요.",
    "적분": "조금 더 풀어서 말하면, 적분은 잘게 나눈 변화를 모아서 전체를 이해하는 개념이에요. 작은 조각들을 차곡차곡 더해서 전체 양을 본다고 생각하면 쉬워요.",
    "관행": "조금 더 풀어서 말하면, 관행은 사람들이 한 사회나 집단 안에서 오래 반복하다 보니 자연스럽게 굳어진 방식이라고 보면 돼요. 꼭 문서로 정해져 있지 않아도 실제 현장에서는 거의 기준처럼 작동하는 경우가 많아요.",
    "관습": "조금 더 풀어서 말하면, 관습은 사람들이 오랫동안 반복하면서 익숙하게 따르게 된 생활 방식이나 질서를 말해요. 눈에 보이는 규칙표가 없어도, 그 공동체 안에서는 자연스러운 기준처럼 받아들여지곤 해요.",
    "관례": "조금 더 풀어서 말하면, 관례는 예전부터 이어져 와서 이제는 자연스러운 절차처럼 여겨지는 방식이에요. 공식 규정이 아니어도 실제로는 늘 그렇게 처리하는 흐름을 설명할 때 자주 쓰여요.",
}

_CONCEPT_SIMPLE_DETAILS: dict[str, str] = {
    "수학": "아주 쉽게 말하면, 수학은 세상이 어떤 규칙으로 움직이는지 읽어보는 언어에 가까워요.",
    "함수": "아주 쉽게 말하면, 함수는 값을 넣으면 결과가 정해져 나오는 약속이에요.",
    "미분": "아주 쉽게 말하면, 미분은 지금 얼마나 빠르게 변하는지 보는 거예요.",
    "적분": "아주 쉽게 말하면, 적분은 작은 변화를 모아서 전체를 보는 거예요.",
    "관행": "아주 쉽게 말하면, 관행은 사람들이 오래 하다 보니 자연스럽게 굳어진 방식이에요.",
    "관습": "아주 쉽게 말하면, 관습은 사람들이 오래 반복해서 익숙해진 생활 방식이에요.",
    "관례": "아주 쉽게 말하면, 관례는 예전부터 늘 그렇게 해오던 익숙한 절차예요.",
}

_CONCEPT_EXAMPLE_DETAILS: dict[str, str] = {
    "수학": "예를 들면, 장을 보면서 예산을 맞추거나 시간을 계산하거나 길이를 재는 것도 다 수학 감각과 연결돼 있어요. 멀게 느껴질 수 있지만 사실은 일상에서 규칙을 읽고 판단하는 순간마다 수학적인 사고가 들어가요.",
    "함수": "예를 들면, 자판기에 돈을 넣으면 음료가 나오는 규칙처럼 어떤 입력이 들어오면 정해진 결과가 나오는 관계를 함수처럼 볼 수 있어요.",
    "미분": "예를 들면, 차가 지금 이 순간 얼마나 빠르게 달리고 있는지를 보는 느낌이 미분과 비슷해요.",
    "적분": "예를 들면, 빗방울이 조금씩 쌓여서 전체 물의 양이 되는 모습을 생각하면 적분을 조금 더 쉽게 떠올릴 수 있어요.",
    "관행": "예를 들면, 어떤 회사에서 회의 전에 늘 같은 순서로 보고를 하거나, 어떤 동네에서 명절마다 비슷한 방식으로 인사하는 것도 관행처럼 볼 수 있어요. 굳이 누가 강제로 시키지 않아도 다들 자연스럽게 그렇게 하게 되는 흐름이에요.",
    "관습": "예를 들면, 명절에 어른께 먼저 인사하거나 결혼식에서 일정한 순서를 따르는 것도 관습으로 볼 수 있어요. 오래 이어져 와서 사람들에게 익숙한 방식이 된 경우예요.",
    "관례": "예를 들면, 어떤 조직에서 발표 전에 먼저 간단한 보고를 하고 본안을 설명하는 순서가 늘 반복된다면 그건 관례라고 볼 수 있어요. 문서보다 실제 흐름에서 먼저 느껴지는 기준에 가까워요.",
}

_CONCEPT_USAGE_DETAILS: dict[str, str] = {
    "수학": "그래서 수학이 중요한 이유는 정답 하나를 맞히는 데만 있지 않고, 복잡한 상황을 구조적으로 나눠서 보는 힘을 길러준다는 데 있어요. 한마디로 계산보다 사고방식에 더 가까운 면이 있어요.",
    "함수": "그래서 함수는 변화의 규칙을 다루는 거의 모든 곳에서 쓰여요. 그래프, 과학, 경제, 프로그래밍까지 전부 입력과 출력 관계를 다룰 때 함수 관점이 들어가요.",
    "미분": "그래서 미분은 속도, 성장, 변화처럼 계속 달라지는 것을 읽을 때 중요해요. 지금 얼마나 변하는지를 잡아낼 수 있다는 게 핵심이에요.",
    "적분": "그래서 적분은 면적, 거리, 누적량처럼 작은 것을 쌓아 전체를 봐야 할 때 중요해요. 부분을 모아 전체를 이해하는 사고에 가까워요.",
    "관행": "그래서 관행이라는 말은 공식 규칙은 아니지만, 실제 현장에서는 많은 사람이 자연스럽게 따르고 있는 익숙한 방식이나 흐름을 설명할 때 자주 써요.",
    "관습": "그래서 관습이라는 말은 사람들이 오래 반복해 오면서 공동체 안에 자연스럽게 자리 잡은 생활 방식이나 질서를 말할 때 자주 써요.",
    "관례": "그래서 관례라는 말은 원칙이나 규정과 별개로, 실제로는 늘 그렇게 처리해 오던 익숙한 절차나 순서를 설명할 때 자주 써요.",
}


def _generic_concept_followup_summary(term: str, summary: str, style: str) -> str:
    compact = str(summary or "").strip().rstrip(". ")
    if not compact:
        compact = f"{term}에 대한 설명을 조금 더 자연스럽게 이어서 보면 돼요"

    if style == "simple":
        if compact.startswith(term):
            return f"아주 짧게 다시 잡아보면, {compact}예요."
        return f"아주 짧게 다시 잡아보면, {term}은 {compact}예요."
    if style == "example":
        return f"예시로 붙여서 보면, {compact}라는 느낌으로 이해하면 조금 더 쉬워요."
    if style == "usage":
        if compact.startswith(term):
            return f"핵심만 다시 잡아보면, {compact}라고 이해하면 돼요."
        return f"핵심만 다시 잡아보면, {term}은 {compact}라고 이해하면 돼요."
    return f"조금 더 풀어서 말하면, {compact}."


def _grounding_prefix(grounding: GroundingResult | None) -> str:
    if not grounding:
        return ""
    summary = str(grounding.get("summary") or "").strip()
    if not summary:
        return ""
    return f"{summary} "


def is_image_capability_prompt(normalized: str) -> bool:
    text = str(normalized or "").strip()
    if not text:
        return False
    return any(token in text for token in ("이미지", "사진", "캡처", "스크린샷")) and any(
        token in text for token in ("해석", "인식", "읽", "분석", "볼 수", "가능", "할 수")
    )


def build_image_capability_reply(has_documents: bool, grounding: GroundingResult | None = None) -> str:
    prefix = _grounding_prefix(grounding)
    if has_documents:
        return (
            f"{prefix}응, 이미지도 같이 볼 수 있어요. "
            "이미지를 등록하면 식이나 문제 흐름을 더 정리해서, 지금보다 더 깊게 풀이를 이어갈 수 있어요."
        )
    return (
        f"{prefix}응, 이미지를 등록하면 더 깊은 풀이가 가능해요. "
        "문제 이미지나 캡처를 올려주면 그 내용을 바탕으로 더 자세히 같이 볼 수 있어요."
    )


def build_smalltalk_reply(normalized: str) -> str:
    if any(token in normalized for token in ("안녕", "하이", "반가", "헬로")):
        return "안녕, 전 코코예요. 여기서는 편하게 일상적인 대화를 이어가도 좋고, 필요하면 학습 흐름으로도 자연스럽게 이어갈 수 있어요. 요즘은 어떤 이야기가 제일 편해요?"
    if any(token in normalized for token in ("고마워", "감사")):
        return "천만에요. 이렇게 편하게 이어가면 돼요. 지금 더 이야기해보고 싶은 게 있어요?"
    return "응, 편하게 말 걸어줘도 돼요. 지금 흐름 그대로 같이 이야기해볼게요. 어디서부터 풀어보면 좋을까요?"


def build_self_info_reply(normalized: str, has_documents: bool) -> str:
    if any(token in normalized for token in ("어떻게 만들어", "만들어졌", "어떻게 작동", "원리")):
        if has_documents:
            return (
                "나는 코코앱 안에서 대화를 돕도록 설계된 AI예요. 메인챗에서는 일상적인 대화를 자연스럽게 이어가고, "
                "필요하면 학습리스트 기반 분석 흐름으로 연결되도록 만들어졌어요. 궁금한 건 기술적으로 어떻게 구성됐는지 쪽이에요, "
                "아니면 여기서 어떤 역할을 하도록 설계됐는지 쪽이에요?"
            )
        return (
            "나는 코코앱 안에서 대화를 돕도록 설계된 AI예요. 지금은 메인챗 쪽에서 일상적인 대화를 자연스럽게 이어가고, "
            "문제 이미지를 올려 학습리스트가 생기면 더 깊은 분석 흐름으로 연결되도록 만들어졌어요. 궁금한 건 기술적인 구조 쪽이에요, "
            "아니면 내가 여기서 어떤 역할을 하는지 쪽이에요?"
        )
    if any(token in normalized for token in ("사람이야", "ai야", "정체")):
        return (
            "나는 사람이라기보다 코코앱 안에서 대화를 돕는 AI예요. 다만 말투는 너무 딱딱하지 않게, 실제로 같이 대화하는 느낌이 들도록 설계돼 있어요. "
            "내 정체가 궁금한 건지, 아니면 어떤 방식으로 답을 만드는지가 궁금한 건지 말해주면 더 깊게 이어볼게요."
        )
    return (
        "전 코코예요. 여기서는 편하게 이야기하다가, 필요할 때는 학습리스트 기반 대화로 자연스럽게 이어지도록 설계돼 있어요. "
        "저라는 존재가 궁금한 건지, 아니면 여기서 무엇을 도와줄 수 있는지가 궁금한 건지 말해주면 더 자연스럽게 이어갈게요."
    )


def build_opinion_reply(normalized: str) -> str:
    return (
        "내가 보기엔 지금 질문은 맥락이 조금 더 붙을수록 훨씬 또렷해져요. 지금 정보만으로 단정하긴 이르지만, "
        "내 답변이 정확하지 않을 수 있다는 걸 전제로 보면 같이 생각해볼 수는 있어요. 네가 가장 고민하는 포인트 하나만 말해주면 그걸 기준으로 더 깊게 이어볼게요."
    )


def build_emotional_reply(normalized: str) -> str:
    if any(token in normalized for token in ("피곤", "지쳤")):
        return "그럴 수 있어요. 오늘 하루가 꽤 길었거나, 생각보다 에너지를 많이 쓴 것 같아요. 지금은 무리해서 정리하려 하기보다 뭐가 제일 피곤한지 한 가지만 말해주면 거기부터 같이 볼게요."
    if any(token in normalized for token in ("불안", "걱정", "무서워", "떨려")):
        return "그 마음이 올라오면 머릿속이 더 복잡해질 수 있어요. 지금 당장 해결하려 하기보다, 뭐가 제일 걱정되는지만 먼저 말해줘도 괜찮아요. 그 지점부터 같이 정리해볼게요."
    if any(token in normalized for token in ("우울", "슬퍼", "외롭", "속상")):
        return "그렇게 느껴질 만한 이유가 있었던 것 같아요. 억지로 괜찮아지려고 하기보다, 지금 제일 크게 남아 있는 감정이 뭔지부터 천천히 말해줘도 괜찮아요."
    return "지금 마음이 조금 복잡한 상태처럼 들려요. 바로 결론을 내리기보다, 어떤 점이 가장 크게 걸리는지부터 같이 꺼내보면 조금 더 편해질 수 있어요."


def build_app_help_reply(normalized: str, has_documents: bool, grounding: GroundingResult | None = None) -> str:
    prefix = _grounding_prefix(grounding)
    if is_image_capability_prompt(normalized):
        return build_image_capability_reply(has_documents=has_documents, grounding=grounding)
    if any(token in normalized for token in ("상태", "모드", "지금 어때", "현재 어때")):
        if has_documents:
            return (
                "지금은 메인챗과 학습 흐름을 같이 쓸 수 있는 상태예요. "
                "필요하면 학습리스트를 선택해서 더 깊게 이어서 볼 수 있어요."
            )
        return "지금은 메인챗 중심으로 보고 있어요. 문제 이미지를 올리면 학습 흐름으로도 자연스럽게 이어갈 수 있어요."
    if any(token in normalized for token in ("뭐 할 수", "무엇을 할 수", "기능", "도움")):
        if has_documents:
            return (
                f"{prefix}메인챗에서는 편하게 일상적인 대화를 이어갈 수 있고, "
                "학습리스트를 선택하면 등록한 문제를 바탕으로 더 깊게 이어서 볼 수 있어요."
            )
        return (
            f"{prefix}메인챗에서는 편하게 대화할 수 있고, "
            "문제 이미지를 올려 학습리스트를 만들면 더 깊게 분석하는 흐름으로 이어갈 수 있어요."
        )
    if any(token in normalized for token in ("업로드", "파일", "분석")):
        return f"{prefix}이미지를 올리면 학습리스트가 생성되고, 그다음부터는 문제를 기준으로 더 깊게 이어서 볼 수 있어요."
    if any(token in normalized for token in ("로고", "메인챗", "채팅")):
        return (
            f"{prefix}코코 로고 쪽은 메인챗 흐름으로 돌아오는 역할이라고 보면 돼요. "
            "여기서는 가볍게 이야기하고, 필요하면 다시 학습 흐름으로 넘어갈 수 있어요."
        )
    return (
        f"{prefix}제가 보기엔 지금은 앱 사용 흐름을 물어보는 것 같아요. "
        "내 답변이 정확하지 않을 수 있는데, 더 구체적으로 말해주면 바로 이어서 정리해볼게요."
    )


def build_content_request_reply(normalized: str) -> str:
    compact = "".join(str(normalized or "").split())
    if any(token in compact for token in ("노래", "음악", "플레이리스트", "가사")):
        if "사랑" in compact:
            return (
                "있죠. 사랑을 담은 노래는 정말 많아서, 어떤 결의 사랑을 떠올리는지가 더 중요해요. "
                "설레는 느낌인지, 잔잔한 느낌인지, 이별처럼 먹먹한 느낌인지 말해주면 그 분위기에 맞춰 더 자연스럽게 이어볼게요."
            )
        return (
            "있을 수 있어요. 다만 지금은 어떤 분위기나 주제를 떠올리는지에 따라 완전히 달라질 수 있어서, "
            "조금만 더 붙여주면 그 결에 맞춰 자연스럽게 이어볼게요."
        )
    if any(token in compact for token in ("영화", "드라마", "영상")):
        return (
            "있을 수 있어요. 다만 영화나 드라마는 장르와 분위기에 따라 추천 결이 많이 달라져서, "
            "가볍게 보고 싶은지 아니면 조금 진한 흐름을 원하는지 말해주면 더 정확하게 이어볼게요."
        )
    if any(token in compact for token in ("책", "소설", "시")):
        return (
            "있죠. 책이나 글 쪽은 주제는 같아도 문체와 분위기에 따라 느낌이 꽤 달라져요. "
            "지금은 편하게 읽히는 쪽이 좋은지, 조금 더 깊게 잠기는 쪽이 좋은지 말해주면 그 방향으로 이어볼게요."
        )
    return (
        "있을 수 있어요. 다만 지금 문장만으로는 어떤 종류를 원하는지까지는 아직 또렷하지 않아요. "
        "분위기나 형태를 한 단어만 더 붙여주면 그 조합으로 자연스럽게 이어볼게요."
    )


def build_general_reply(normalized: str, grounding: GroundingResult | None = None) -> str:
    prefix = _grounding_prefix(grounding)
    if normalized.endswith("?") or any(token in normalized for token in ("왜", "어떻게", "뭐야", "무슨", "맞아", "가능해")):
        return (
            f"{prefix}{normalized}에 대해 바로 답하자면, 지금은 맥락이 조금 더 필요해 보여요. "
            "다만 내 답변이 정확하지 않을 수 있다는 걸 전제로 하면 같이 생각을 이어갈 수는 있어요. "
            "네가 알고 싶은 방향을 한 줄만 더 붙여주면 더 자연스럽고 깊게 이어서 볼게요."
        )
    return (
        f"{prefix}{normalized}라는 말에서 시작해볼 수 있을 것 같아요. "
        "제가 잘못 이해했을 수도 있어서, 네가 지금 가장 중요하게 보는 포인트를 조금만 더 말해주면 흐름에 맞게 같이 정리해볼게요."
    )


def build_concept_reply(
    normalized: str,
    concept: ConceptSearchResult | None,
    has_documents: bool,
    followup: bool = False,
    followup_style: str = "detail",
) -> str:
    if concept:
        term = str(concept.get("term") or normalized).strip()
        summary = str(concept.get("summary") or "").strip()
        if followup:
            if followup_style == "simple":
                summary = _CONCEPT_SIMPLE_DETAILS.get(term, _generic_concept_followup_summary(term, summary, "simple"))
            elif followup_style == "example":
                summary = _CONCEPT_EXAMPLE_DETAILS.get(term, _generic_concept_followup_summary(term, summary, "example"))
            elif followup_style == "usage":
                summary = _CONCEPT_USAGE_DETAILS.get(term, _generic_concept_followup_summary(term, summary, "usage"))
            else:
                summary = _CONCEPT_FOLLOWUP_DETAILS.get(term, _generic_concept_followup_summary(term, summary, "detail"))
        tail = "내가 조금 거칠게 풀어 말했을 수도 있는데, 원하면 더 쉬운 예시로도 이어서 설명해볼게요."
        if any(token in term for token in ("수학", "함수", "미분", "적분", "확률", "통계", "그래프")):
            if has_documents:
                tail = "내가 조금 거칠게 풀어 말했을 수도 있는데, 원하면 관련 개념을 학습리스트 기준으로도 더 깊게 이어볼 수 있어요."
            else:
                tail = "내가 조금 거칠게 풀어 말했을 수도 있는데, 원하면 학습리스트를 생성해서 관련 개념을 더 깊게 이어볼 수도 있어요."
        if followup:
            return f"{summary} {tail}"
        return f"{term}에 대해 쉽게 말하면, {summary} {tail}"

    return (
        f"{normalized}라는 말을 지금 바로 또렷하게 설명하고 싶은데, 내가 찾은 정보만으로는 아직 충분하지 않을 수 있어요. "
        "내 답변이 정확하지 않을 수 있으니, 용어 하나만 더 짧게 보내주면 다시 찾아서 더 자연스럽게 풀어볼게요."
    )
