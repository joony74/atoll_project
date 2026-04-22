from __future__ import annotations

import json
import re
import time
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .contracts import AppState, ConceptSearchResult, GroundingResult, StoredConcept
from .state import active_chat_mode


_APP_STATE_KEYWORDS = (
    "현재",
    "지금",
    "최근",
    "마지막",
    "학습리스트",
    "파일",
    "업로드",
    "문서",
    "메인챗",
    "채팅",
    "로고",
    "분석",
    "상태",
)

_LOCAL_CONCEPTS: dict[str, str] = {
    "수학": "수학은 수, 구조, 변화, 관계 같은 패턴을 이해하고 설명하는 학문이에요. 아주 넓게 보면 세상을 규칙과 관계로 읽는 언어에 가깝다고 볼 수 있어요.",
    "함수": "함수는 어떤 입력을 넣었을 때 그에 따라 하나의 출력을 정해주는 대응 규칙이에요. 쉽게 말하면 값이 어떻게 바뀌는지를 정해둔 약속이라고 이해하면 돼요.",
    "미분": "미분은 어떤 값이 아주 짧은 순간에 얼마나 빠르게 변하는지를 보는 개념이에요. 그래프에서는 한 점에서의 기울기를 본다고 이해하면 쉬워요.",
    "적분": "적분은 작은 변화를 차곡차곡 모아서 전체 양을 보는 개념이에요. 그래프에서는 넓이를 쌓아 전체를 구하는 느낌으로 이해할 수 있어요.",
    "확률": "확률은 어떤 일이 일어날 가능성을 수로 표현하는 개념이에요. 불확실한 상황을 비교하고 판단할 때 쓰는 기준이라고 볼 수 있어요.",
    "통계": "통계는 여러 데이터를 모아서 경향과 의미를 읽어내는 방법이에요. 많은 사례 속에서 공통된 패턴을 찾는 데 쓰여요.",
    "그래프": "그래프는 값 사이의 관계를 눈에 보이게 나타낸 그림이에요. 숫자만 볼 때보다 변화와 흐름을 더 직관적으로 이해하게 도와줘요.",
    "관행": "관행은 어떤 집단이나 사회 안에서 오래 반복되면서 자연스럽게 자리 잡은 방식이나 흐름을 말해요. 법처럼 강제되지는 않아도, 실제로는 많은 사람이 당연하게 따르는 경우가 많아요.",
    "관습": "관습은 사람들이 오랫동안 반복해서 자연스럽게 따르게 된 생활 방식이나 질서를 말해요. 제도처럼 딱 정해져 있지는 않아도, 그 집단 안에서는 익숙한 기준처럼 작동해요.",
    "관례": "관례는 예전부터 반복돼 와서 자연스럽게 기준처럼 여겨지는 처리 방식이나 순서를 말해요. 특히 공식 절차와 함께 늘 따라오는 익숙한 흐름을 설명할 때 자주 써요.",
}

_CONCEPT_ALIASES: dict[str, str] = {
    "수학": "수학",
    "math": "수학",
    "매쓰": "수학",
    "함수": "함수",
    "function": "함수",
    "미분": "미분",
    "derivative": "미분",
    "적분": "적분",
    "integral": "적분",
    "확률": "확률",
    "probability": "확률",
    "통계": "통계",
    "statistics": "통계",
    "그래프": "그래프",
    "graph": "그래프",
    "관행": "관행",
    "관습": "관습",
    "관례": "관례",
    "custom": "관행",
    "convention": "관행",
}

_WIKI_SEARCH_ENDPOINT = "https://ko.wikipedia.org/w/api.php"
_REQUEST_HEADERS = {
    "User-Agent": "CocoAIStudy/1.0 (concept-search)",
    "Accept": "application/json",
}
_LEARN_TRIM_MARKERS = (
    "내가 조금",
    "내 설명이",
    "내 답변이",
    "원하면",
    "필요하면",
    "학습리스트를 생성",
    "학습리스트를 만들",
)
_LEARN_PREFIXES = (
    "조금 더 풀어서 말하면,",
    "예를 들면,",
    "그래서 ",
    "핵심만 다시 잡아보면,",
    "아주 짧게 다시 잡아보면,",
)


def _selected_document_from_state(state: AppState) -> dict | None:
    selected_doc_id = str(state.get("selected_doc_id") or "").strip()
    if not selected_doc_id:
        return None
    for item in state.get("documents", []):
        if not isinstance(item, dict):
            continue
        if str(item.get("doc_id") or "").strip() == selected_doc_id:
            return item
    return None


def _build_summary(
    document_count: int,
    current_mode: str,
    selected_doc_name: str | None,
) -> str:
    if document_count <= 0:
        return "지금은 저장된 학습리스트가 없어서 메인챗으로 보고 있어요."
    if current_mode == "study" and selected_doc_name:
        return f"지금은 학습리스트가 {document_count}개 저장돼 있고, 최근 기준으로는 {selected_doc_name} 쪽 흐름이 이어져 있어요."
    if current_mode == "study":
        return f"지금은 학습리스트가 {document_count}개 저장돼 있고, 학습리스트 기준 대화 흐름으로 이어져 있어요."
    return f"지금은 학습리스트가 {document_count}개 저장돼 있고, 메인챗 흐름으로 보고 있어요."


def _normalize_concept_key(term: str) -> str:
    normalized = str(term or "").strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def resolve_known_concept_term(text: str, custom_concepts: dict[str, StoredConcept] | None = None) -> str | None:
    normalized = _normalize_concept_key(text)
    if not normalized:
        return None

    compact = re.sub(r"\s+", "", normalized.lower())
    matches: list[tuple[int, str]] = []
    for key, payload in dict(custom_concepts or {}).items():
        candidate = str((payload or {}).get("term") or key or "").strip()
        candidate_compact = re.sub(r"\s+", "", candidate.lower())
        if candidate_compact and candidate_compact in compact:
            matches.append((len(candidate_compact), candidate))
    for alias, target in _CONCEPT_ALIASES.items():
        alias_compact = re.sub(r"\s+", "", alias.lower())
        if alias_compact and alias_compact in compact:
            matches.append((len(alias_compact), target))

    if not matches:
        return None

    matches.sort(key=lambda item: item[0], reverse=True)
    return matches[0][1]


def _lookup_local_concept(term: str) -> ConceptSearchResult | None:
    normalized = _normalize_concept_key(term)
    if normalized in _LOCAL_CONCEPTS:
        return {
            "term": normalized,
            "summary": _LOCAL_CONCEPTS[normalized],
            "confidence": "high",
            "source": "local",
        }
    return None


def _lookup_custom_concept(term: str, custom_concepts: dict[str, StoredConcept] | None = None) -> ConceptSearchResult | None:
    normalized = _normalize_concept_key(term)
    if not normalized or not custom_concepts:
        return None

    direct = custom_concepts.get(normalized)
    if isinstance(direct, dict):
        summary = str(direct.get("summary") or "").strip()
        if summary:
            return {
                "term": str(direct.get("term") or normalized).strip() or normalized,
                "summary": summary,
                "confidence": str(direct.get("confidence") or "low").strip() or "low",
                "source": f"custom:{str(direct.get('source') or 'chat').strip() or 'chat'}",
            }

    compact = re.sub(r"\s+", "", normalized.lower())
    matches: list[tuple[int, str, dict]] = []
    for key, payload in custom_concepts.items():
        if not isinstance(payload, dict):
            continue
        candidate = str(payload.get("term") or key or "").strip()
        candidate_compact = re.sub(r"\s+", "", candidate.lower())
        if candidate_compact and candidate_compact in compact:
            matches.append((len(candidate_compact), candidate, payload))
    if not matches:
        return None
    matches.sort(key=lambda item: item[0], reverse=True)
    _, candidate, payload = matches[0]
    summary = str(payload.get("summary") or "").strip()
    if not summary:
        return None
    return {
        "term": candidate,
        "summary": summary,
        "confidence": str(payload.get("confidence") or "low").strip() or "low",
        "source": f"custom:{str(payload.get('source') or 'chat').strip() or 'chat'}",
    }


def _fetch_json(url: str) -> dict | None:
    request = Request(url, headers=_REQUEST_HEADERS)
    try:
        with urlopen(request, timeout=3.5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def _search_wikipedia_title(term: str) -> str | None:
    params = urlencode(
        {
            "action": "query",
            "list": "search",
            "srsearch": term,
            "utf8": 1,
            "format": "json",
            "srlimit": 1,
        }
    )
    payload = _fetch_json(f"{_WIKI_SEARCH_ENDPOINT}?{params}")
    if not payload:
        return None
    results = (((payload.get("query") or {}).get("search")) or [])
    if not results:
        return None
    title = str((results[0] or {}).get("title") or "").strip()
    return title or None


def _fetch_wikipedia_extract(title: str) -> str | None:
    params = urlencode(
        {
            "action": "query",
            "prop": "extracts",
            "exintro": 1,
            "explaintext": 1,
            "redirects": 1,
            "titles": title,
            "utf8": 1,
            "format": "json",
        }
    )
    payload = _fetch_json(f"{_WIKI_SEARCH_ENDPOINT}?{params}")
    if not payload:
        return None
    pages = (((payload.get("query") or {}).get("pages")) or {})
    for page in pages.values():
        extract = str((page or {}).get("extract") or "").strip()
        if extract:
            first_lines = re.split(r"(?<=[.!?다])\s+", extract)
            compact = " ".join(part.strip() for part in first_lines[:2] if part.strip())
            return compact or extract
    return None


def search_concept(term: str, custom_concepts: dict[str, StoredConcept] | None = None) -> ConceptSearchResult | None:
    custom_result = _lookup_custom_concept(term, custom_concepts=custom_concepts)
    if custom_result:
        return custom_result

    local_result = _lookup_local_concept(term)
    if local_result:
        return local_result

    normalized = _normalize_concept_key(term)
    if not normalized:
        return None

    title = _search_wikipedia_title(normalized)
    if not title:
        return None

    summary = _fetch_wikipedia_extract(title)
    if not summary:
        return None

    return {
        "term": normalized,
        "summary": summary,
        "confidence": "medium",
        "source": f"wikipedia:{quote(title)}",
    }


def _clean_learned_summary(term: str, summary: str) -> str:
    text = str(summary or "").strip()
    if not text:
        return ""
    for prefix in (f"{term}에 대해 쉽게 말하면,", * _LEARN_PREFIXES):
        if text.startswith(prefix):
            text = text[len(prefix) :].strip()
            break
    for marker in _LEARN_TRIM_MARKERS:
        index = text.find(marker)
        if index > 0:
            text = text[:index].strip()
            break
    text = re.sub(r"\s+", " ", text).strip(" ,.")
    return text


def remember_custom_concept(
    state: AppState,
    term: str,
    summary: str,
    source: str = "chat",
    confidence: str = "low",
) -> None:
    normalized_term = _normalize_concept_key(term)
    cleaned_summary = _clean_learned_summary(normalized_term, summary)
    if not normalized_term or not cleaned_summary:
        return

    bucket = state.setdefault("custom_concepts", {})
    if not isinstance(bucket, dict):
        bucket = {}
        state["custom_concepts"] = bucket

    existing = bucket.get(normalized_term) if isinstance(bucket.get(normalized_term), dict) else None
    priority = {"low": 1, "medium": 2, "high": 3}
    new_priority = priority.get(str(confidence or "low"), 1)
    old_priority = priority.get(str((existing or {}).get("confidence") or "low"), 1)
    old_summary = str((existing or {}).get("summary") or "").strip()
    if existing and new_priority < old_priority:
        return
    if existing and new_priority == old_priority and len(cleaned_summary) <= len(old_summary):
        return

    bucket[normalized_term] = {
        "term": normalized_term,
        "summary": cleaned_summary,
        "confidence": "high" if new_priority >= 3 else "medium" if new_priority == 2 else "low",
        "source": str(source or "chat").strip() or "chat",
        "updated_at": time.time(),
    }


def build_main_chat_grounding(prompt: str, state: AppState) -> GroundingResult:
    normalized = str(prompt or "").strip()
    documents = [item for item in state.get("documents", []) if isinstance(item, dict)]
    document_count = len(documents)
    current_mode = active_chat_mode(state)
    selected_document = _selected_document_from_state(state)
    selected_doc_id = str(state.get("selected_doc_id") or "").strip() or None
    selected_doc_name = None
    if selected_document:
        selected_doc_name = str(selected_document.get("file_name") or "").strip() or None

    result: GroundingResult = {
        "confidence": "low",
        "facts": [],
        "summary": "",
        "active_mode": "study" if current_mode == "study" else "main",
        "document_count": document_count,
        "selected_doc_id": selected_doc_id,
        "selected_doc_name": selected_doc_name,
    }

    should_ground = any(token in normalized for token in _APP_STATE_KEYWORDS)
    if not should_ground:
        return result

    facts: list[str] = []
    if document_count <= 0:
        facts.append("지금은 저장된 학습리스트가 없어요.")
    else:
        facts.append(f"지금은 학습리스트가 {document_count}개 저장돼 있어요.")

    if current_mode == "study":
        facts.append("현재는 학습리스트 기준 대화 흐름이에요.")
        if selected_doc_name:
            facts.append(f"최근 기준으로는 {selected_doc_name} 쪽이 연결돼 있어요.")
    else:
        facts.append("현재는 메인챗 흐름이에요.")

    result["facts"] = facts
    result["summary"] = _build_summary(document_count, current_mode, selected_doc_name)
    result["confidence"] = "high" if facts else "low"
    return result
