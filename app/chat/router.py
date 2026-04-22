from __future__ import annotations

import re

from .contracts import ChatIntent
from .contracts import StoredConcept
from .grounding import resolve_known_concept_term


_SMALLTALK_KEYWORDS = (
    "안녕",
    "하이",
    "헬로",
    "반가",
    "잘 지내",
    "고마워",
    "감사",
)

_SELF_INFO_KEYWORDS = (
    "이름",
    "누구",
    "소개",
    "정체",
    "ai야",
    "ai 인가",
    "사람이야",
    "어떻게 만들어",
    "만들어졌",
    "어떻게 작동",
    "원리",
    "어떻게 태어",
)

_EMOTIONAL_KEYWORDS = (
    "힘들",
    "피곤",
    "지쳤",
    "우울",
    "슬퍼",
    "불안",
    "걱정",
    "속상",
    "무서워",
    "외롭",
    "떨려",
    "짜증",
    "답답",
    "혼란",
)

_APP_HELP_KEYWORDS = (
    "코코",
    "앱",
    "기능",
    "상태",
    "모드",
    "무엇을 할 수",
    "뭐 할 수",
    "업로드",
    "학습리스트",
    "메인챗",
    "채팅",
    "로고",
    "파일",
    "분석",
    "이미지",
    "사진",
    "캡처",
    "스크린샷",
    "해석",
    "인식",
    "설정",
)

_OPINION_KEYWORDS = (
    "어떻게 생각",
    "네 생각",
    "의견",
    "어떻게 봐",
    "어때 보여",
    "맞는 것 같",
    "괜찮아 보여",
    "좋아 보여",
)

_CONTENT_OBJECT_KEYWORDS = (
    "노래",
    "음악",
    "플레이리스트",
    "가사",
    "영화",
    "드라마",
    "책",
    "소설",
    "시",
    "영상",
)

_CONTENT_REQUEST_HINTS = (
    "있어",
    "있나",
    "추천",
    "알아",
    "찾아",
    "들려",
    "보여",
    "같은",
)

_CONCEPT_PATTERNS = (
    re.compile(
        r"(?P<term>.+?)(?:이|가|은|는)?\s*(?:뭐야|뭐지|뭐냐|무엇이야|무엇인지|무엇인데|뭔지|뭔데)\s*(?:알려줘|설명해줘)?$",
        re.IGNORECASE,
    ),
    re.compile(r"(?P<term>.+?)(?:이란|란)\s*$", re.IGNORECASE),
    re.compile(r"(?P<term>.+?)\s*(?:뜻|의미)\s*(?:이|가)?\s*(?:뭐야|뭐지|알려줘|설명해줘)?$", re.IGNORECASE),
    re.compile(r"(?P<term>.+?)\s*(?:설명해줘|정의해줘|알려줘)$", re.IGNORECASE),
)

_CONCEPT_STOPWORDS = {
    "이거",
    "그거",
    "이것",
    "저것",
    "그것",
    "이거는",
    "그거는",
    "그게",
}

_CONCEPT_CLARIFIER_TOKENS = (
    "이란",
    "란",
    "뭔데",
    "뭐지",
    "뭐야",
    "무슨 뜻",
    "뜻",
    "의미",
    "정의",
    "설명",
    "쉽게",
    "다시",
    "한마디로",
    "정리",
    "무슨 말",
)

_MATH_KEYWORDS = (
    "수학",
    "문제",
    "풀이",
    "공식",
    "함수",
    "방정식",
    "그래프",
    "기하",
    "확률",
    "통계",
    "미분",
    "적분",
    "삼각",
    "sin",
    "cos",
    "tan",
    "log",
    "lim",
)

_MATH_PATTERN = re.compile(
    r"(\d+\s*[\+\-\*/=]\s*\d+)|([xy]\s*=\s*.+)|(\b[fgh]\s*\()|(\([\-\d\s,]+\))",
    re.IGNORECASE,
)


def extract_concept_term(prompt: str) -> str | None:
    normalized = str(prompt or "").strip().rstrip("?.! ")
    if not normalized:
        return None

    for pattern in _CONCEPT_PATTERNS:
        matched = pattern.search(normalized)
        if not matched:
            continue
        term = str(matched.group("term") or "").strip(" \"'`")
        term = re.sub(r"\s+", " ", term).strip()
        if not term or len(term) > 40:
            continue
        if term in _CONCEPT_STOPWORDS:
            continue
        return term
    return None


def extract_content_theme(prompt: str) -> str | None:
    normalized = str(prompt or "").strip().rstrip("?.! ")
    if not normalized:
        return None

    compact = re.sub(r"\s+", "", normalized)
    for keyword in _CONTENT_OBJECT_KEYWORDS:
        if keyword in compact:
            theme = compact.replace(keyword, " ")
            theme = re.sub(
                r"(있어|있나|추천|알아|찾아|들려|보여|같은|관련|좀|하나|있니|있냐|있을까)$",
                "",
                theme,
            )
            theme = re.sub(r"(이|가|은|는|을|를|도|만)$", "", theme)
            theme = re.sub(r"\s+", " ", theme).strip(" ?!.,")
            if theme and len(theme) <= 30:
                return theme
    return None


def is_content_request_prompt(prompt: str) -> bool:
    normalized = str(prompt or "").strip()
    if not normalized:
        return False
    compact = re.sub(r"\s+", "", normalized)
    has_object = any(keyword in compact for keyword in _CONTENT_OBJECT_KEYWORDS)
    if not has_object:
        return False
    if any(token in normalized for token in _CONTENT_REQUEST_HINTS):
        return True
    if extract_content_theme(normalized):
        return True
    return False


def is_concept_clarification_prompt(prompt: str, custom_concepts: dict[str, StoredConcept] | None = None) -> bool:
    normalized = str(prompt or "").strip()
    if not normalized:
        return False
    if extract_concept_term(normalized):
        return True
    if any(token in normalized for token in _CONCEPT_CLARIFIER_TOKENS):
        return True
    if resolve_known_concept_term(normalized, custom_concepts=custom_concepts) and len(normalized) <= 14:
        return True
    return False


def classify_main_chat_intent(prompt: str, custom_concepts: dict[str, StoredConcept] | None = None) -> ChatIntent:
    normalized = str(prompt or "").strip()
    lowered = normalized.lower()
    if not normalized:
        return "general"

    if any(token in normalized for token in _SMALLTALK_KEYWORDS):
        return "smalltalk"

    if any(token in lowered for token in _SELF_INFO_KEYWORDS):
        return "self_info"

    if any(token in normalized for token in _EMOTIONAL_KEYWORDS):
        return "emotional"

    if any(token in normalized for token in _APP_HELP_KEYWORDS):
        return "app_help"

    if is_content_request_prompt(normalized):
        return "content_request"

    if extract_concept_term(normalized) or (
        resolve_known_concept_term(normalized, custom_concepts=custom_concepts)
        and is_concept_clarification_prompt(normalized, custom_concepts=custom_concepts)
    ):
        return "concept"

    if any(token in lowered for token in _MATH_KEYWORDS) or _MATH_PATTERN.search(normalized):
        return "math"

    if any(token in normalized for token in _OPINION_KEYWORDS):
        return "opinion"

    return "general"
