from __future__ import annotations

import json
import os
import re
from urllib.request import Request, urlopen

from app.core.config import settings

from .contracts import ChatContextPacket


_REQUEST_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}

_HAN_CHAR_PATTERN = re.compile(r"[\u4e00-\u9fff]")
_KOREAN_CHAR_PATTERN = re.compile(r"[가-힣]")
_LEADING_ACK_PATTERN = re.compile(
    r"^\s*(?:(?:(?i:great|good|sure|okay|alright)|그(?i:reat|ood))|"
    r"(?:그런|이런|좋은|재밌는|흥미로운)?\s*질문\s*(?:감사합니다|고마워요|좋네요)|"
    r"(?:그런|이런|좋은|재밌는|흥미로운)?\s*질문(?:을|를)?\s*해주셔서\s*(?:기쁩니다|반갑습니다)|"
    r"(?:네|네에|좋네요|좋아요|좋습니다|그렇네요|알겠어요)"
    r"(?:\s*,\s*(?:좋네요|좋아요|좋습니다|그렇네요))?)"
    r"[!,.~\s:：-]*"
)
_TRAILING_EMOJI_AFTER_PUNCT_PATTERN = re.compile(
    r"([?!.,~:：;])(?:[\uFE0F\u200D]|[\U0001F300-\U0001FAFF\u2600-\u27BF])+\s*$"
)
_TRAILING_EMOJI_PATTERN = re.compile(
    r"\s*(?:[\uFE0F\u200D]|[\U0001F300-\U0001FAFF\u2600-\u27BF])+\s*$"
)
_TRAILING_ENGLISH_GARBAGE_PATTERN = re.compile(
    r"(?:\s|[가-힣])+(?:understand|understood|yourself|yourselves|ok|okay|alright|right)\??\s*$",
    re.IGNORECASE,
)
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?。！？])\s*|\n+")
_PAREN_HAN_PATTERN = re.compile(r"\([\u4e00-\u9fff][^)]*\)|（[\u4e00-\u9fff][^）]*）")
_HAN_SUFFIX_AFTER_PUNCT_PATTERN = re.compile(r"\s*[,;:：，、]\s*[\u4e00-\u9fff].*$")
_HAN_SUFFIX_PATTERN = re.compile(r"\s*[\u4e00-\u9fff].*$")
_CODE_BLOCK_PATTERN = re.compile(r"```|`[^`]+`")
_PROGRAMMING_PATTERN = re.compile(
    r"\b(public\s+class|private\s+\w+|System\.out|import\s+\w|def\s+\w+\(|class\s+\w+|return\s+\w+\s*;)\b"
)
_MAIN_FAST_LOCAL_INTENTS = {"smalltalk", "self_info", "app_help", "emotional", "opinion", "math"}


def _env_flag(name: str, default: bool = False) -> bool:
    raw = str(os.getenv(name, "") or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _llm_endpoint() -> str:
    return str(
        os.getenv("COCO_LOCAL_LLM_ENDPOINT")
        or os.getenv("COCO_LLM_ENDPOINT")
        or "http://127.0.0.1:11434/api/chat"
    ).strip()


def _llm_model() -> str:
    return str(
        os.getenv("COCO_LOCAL_LLM_MODEL")
        or os.getenv("COCO_LLM_MODEL")
        or "qwen2.5:7b"
    ).strip()


def _recent_dialogue(packet: ChatContextPacket) -> str:
    lines: list[str] = []
    for item in packet.get("recent_messages") or []:
        role = str(item.get("role") or "").strip()
        content = str(item.get("content") or "").strip()
        if not role or not content:
            continue
        speaker = "사용자" if role == "user" else "코코"
        lines.append(f"{speaker}: {content}")
    return "\n".join(lines[-8:])


def _system_prompt() -> str:
    return (
        "너는 코코앱 안에서 대화하는 한국어 도우미 코코다. "
        "답변은 자연스럽고 사람처럼 이어가되, 내부 라우팅이나 모델, 검색, 규칙 엔진 이야기는 절대 꺼내지 않는다. "
        "반드시 자연스러운 한국어로만 답하고, 중국어/일본어/영어를 섞지 않는다. "
        "단정이 어렵다면 부드럽게 여지를 두고 말하되, 사용자를 다시 시험하듯 되묻지 말고 먼저 맥락을 이어서 정리한다. "
        "질문이 조금 애매해도 가장 가능성 높은 뜻으로 먼저 도와주고, 필요한 경우에만 마지막에 짧게 방향을 좁혀 묻는다. "
        "이미지 해석 가능 여부를 묻는 질문에는 '이미지를 등록하면 더 깊은 풀이가 가능해요'라는 방향으로 안내하고, "
        "'이미지를 해석하지 못합니다'처럼 단정적으로 막지 않는다. "
        "학습리스트가 선택된 상태에서는 현재 자료에서 복원된 문제 문장, 식 후보, 답 후보를 참고해 설명하되, "
        "정보가 불완전하면 현재 확인된 범위 안에서만 분명하게 말한다. "
        "수학 질문은 간단히 받을 수 있지만 학습리스트가 없으면 '학습리스트를 생성하면 더 깊게 분석할 수 있어요' 정도로만 가볍게 연결한다. "
        "무례하거나 감정 섞인 입력도 지나치게 방어적으로 반응하지 말고, 문맥을 읽어 부드럽게 이어간다."
    )


def _safe_text(value: str | None, fallback: str = "없음", limit: int = 180) -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    if len(text) <= limit:
        return text
    return f"{text[:limit - 1]}…"


def _safe_join(values: list[str] | None, fallback: str = "없음", limit: int = 4, item_limit: int = 70) -> str:
    cleaned: list[str] = []
    for item in values or []:
        text = str(item or "").strip()
        if not text or text in cleaned:
            continue
        cleaned.append(_safe_text(text, fallback="", limit=item_limit))
        if len(cleaned) >= limit:
            break
    return " / ".join(cleaned) if cleaned else fallback


def _main_developer_prompt(packet: ChatContextPacket) -> str:
    active_mode = str(packet.get("active_mode") or "main")
    has_documents = bool(packet.get("has_documents"))
    last_intent = str(packet.get("last_intent") or "").strip() or "general"
    last_concept_term = str(packet.get("last_concept_term") or "").strip() or "없음"
    intent_hint = str(packet.get("intent_hint") or "").strip() or "general"
    content_theme = str(packet.get("content_theme") or "").strip() or "없음"
    ambiguity = ", ".join(packet.get("ambiguity_reasons") or []) or "없음"
    return (
        "답변 원칙:\n"
        "- 한국어로 답한다.\n"
        "- 2~4문장 안에서 먼저 자연스럽게 이어받는다.\n"
        "- 최근 맥락이 있으면 그 흐름을 우선 해석한다.\n"
        "- '그래', '몰라', '응' 같은 짧은 답은 직전 문맥을 이어가는 신호일 수 있다.\n"
        "- 개념 설명과 콘텐츠 요청(예: 사랑 노래) 같은 단어 조합은 다르게 해석한다.\n"
        "- 이미지, 사진, 캡처, 스크린샷을 해석할 수 있는지 묻는 질문은 앱 기능 안내로 보고, 이미지를 등록하면 더 깊은 풀이가 가능하다고 자연스럽게 설명한다.\n"
        "- 콘텐츠 요청은 먼저 가장 자연스러운 예시나 방향을 제안하고, 꼭 필요할 때만 짧게 되묻는다.\n"
        "- 콘텐츠 요청으로 보이면 개념 정의로 되돌아가지 않는다. 특히 노래/음악/영화/책 요청은 추천이나 분위기 제안으로 답한다.\n"
        "- 사용자가 수학을 어려워한다고 말하면 설명보다 먼저 부담을 덜어주고, 무엇이 어려운지 같이 정리하는 방향으로 답한다.\n"
        "- 사용자가 코드/프로그래밍을 묻지 않았다면 코드블록, 자바/파이썬 예시, 클래스 예시는 절대 넣지 않는다.\n"
        "- 설명보다 추천이나 예시가 더 맞는 문장이라면 개념 정의로 되돌아가지 않는다.\n"
        "- 반드시 한국어만 사용한다. 중국어 한자식 문장이나 영어 혼용 문장을 만들지 않는다.\n"
        "- 사용자를 다시 훈계하거나 메타 설명으로 빠지지 않는다.\n\n"
        f"현재 모드: {active_mode}\n"
        f"학습리스트 존재: {'예' if has_documents else '아니오'}\n"
        f"추정 intent: {intent_hint}\n"
        f"콘텐츠 주제: {content_theme}\n"
        f"직전 intent: {last_intent}\n"
        f"직전 개념: {last_concept_term}\n"
        f"애매함 신호: {ambiguity}"
    )


def _study_developer_prompt(packet: ChatContextPacket) -> str:
    selected_doc_name = _safe_text(packet.get("selected_doc_name"), limit=80)
    problem_text = _safe_text(packet.get("study_problem_text"), fallback="문제 문장을 아직 선명하게 복원하는 중입니다.", limit=220)
    math_topic = _safe_text(packet.get("study_math_topic"))
    answer_candidate = _safe_text(packet.get("study_answer_candidate"), fallback="아직 정답 후보를 확정하는 중입니다.")
    expressions = _safe_join(packet.get("study_expressions"), fallback="복원된 식 후보가 아직 충분하지 않습니다.")
    steps = _safe_join(packet.get("study_steps"), fallback="풀이 단서를 정리하는 중입니다.")
    question_type = _safe_text(packet.get("study_question_type"))
    latest_user_query = _safe_text(packet.get("study_latest_user_query"))
    reference_solution = _safe_text(packet.get("study_reference_solution"), limit=900)
    study_source = _safe_text(packet.get("study_source"))
    ambiguity = ", ".join(packet.get("ambiguity_reasons") or []) or "없음"

    return (
        "답변 원칙:\n"
        "- 한국어로 답한다.\n"
        "- 현재 선택된 학습자료를 기준으로 답한다.\n"
        "- 먼저 사용자의 질문에 바로 답하고, 필요하면 현재 자료와 연결해 짧게 설명을 보강한다.\n"
        "- 복원 정보가 불완전하면 확인된 정보만 분명하게 말하고, 없는 내용을 지어내지 않는다.\n"
        "- 내부 튜터, OCR, 파이프라인, 모델 선택 같은 시스템 설명은 하지 않는다.\n"
        "- 사용자가 풀이를 물으면 현재 문제 문장, 식 후보, 답 후보, 풀이 단서를 바탕으로 차분하게 설명한다.\n"
        "- 문제은행 원풀이가 제공되면 그것을 신뢰 기준으로 삼아 한국어로 풀어 설명한다.\n"
        "- 정답이 아직 확실하지 않으면 '현재 복원 정보 기준'이라고 자연스럽게 밝혀라.\n"
        "- 문서와 직접 관련 없는 짧은 질문도 현재 자료 흐름 안에서 이해하고 너무 딱딱하게 끊지 않는다.\n"
        "- 코드블록, 자바/파이썬 예시는 넣지 않는다.\n"
        "- 반드시 자연스러운 한국어만 사용한다.\n\n"
        "현재 모드: study\n"
        f"선택 자료명: {selected_doc_name}\n"
        f"문제 유형: {question_type}\n"
        f"수학 주제: {math_topic}\n"
        f"복원된 문제 문장: {problem_text}\n"
        f"식 후보: {expressions}\n"
        f"현재 답 후보: {answer_candidate}\n"
        f"풀이 단서: {steps}\n"
        f"학습자료 출처: {study_source}\n"
        f"문제은행 원풀이: {reference_solution}\n"
        f"직전 학습 질문: {latest_user_query}\n"
        f"애매함 신호: {ambiguity}"
    )


def _developer_prompt(packet: ChatContextPacket) -> str:
    active_mode = str(packet.get("active_mode") or "main")
    if active_mode == "study":
        return _study_developer_prompt(packet)
    return _main_developer_prompt(packet)


def _build_payload(packet: ChatContextPacket, *, retry_korean_only: bool = False) -> dict:
    history = _recent_dialogue(packet)
    user_prompt = str(packet.get("normalized_prompt") or packet.get("prompt") or "").strip()
    user_block = "최근 대화:\n"
    user_block += f"{history}\n\n" if history else "없음\n\n"
    user_block += f"현재 사용자 입력:\n{user_prompt}"
    if retry_korean_only:
        user_block += "\n\n중요: 방금 답변은 언어가 섞였거나 부자연스러웠다. 이번에는 자연스러운 한국어만 사용해서 다시 답해줘."
    return {
        "model": _llm_model(),
        "stream": False,
        "keep_alive": settings.llm_keep_alive,
        "messages": [
            {"role": "system", "content": _system_prompt()},
            {"role": "system", "content": _developer_prompt(packet)},
            {"role": "user", "content": user_block},
        ],
        "options": {
            "temperature": 0.5,
            "num_ctx": settings.ollama_num_ctx,
        },
    }


def _post_json(url: str, payload: dict) -> dict | None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=body, headers=_REQUEST_HEADERS, method="POST")
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def _extract_content(result: dict | None) -> str | None:
    if not result:
        return None
    message = result.get("message") if isinstance(result, dict) else None
    if isinstance(message, dict):
        content = str(message.get("content") or "").strip()
        return content or None
    content = str((result or {}).get("response") or "").strip()
    return content or None


def _looks_mixed_non_korean(content: str) -> bool:
    return bool(_HAN_CHAR_PATTERN.search(content or ""))


def _strip_han_segments(content: str) -> str:
    text = _PAREN_HAN_PATTERN.sub("", str(content or ""))
    parts = [part.strip() for part in _SENTENCE_SPLIT_PATTERN.split(text) if part.strip()]
    cleaned_parts: list[str] = []

    for part in parts:
        han_count = len(_HAN_CHAR_PATTERN.findall(part))
        korean_count = len(_KOREAN_CHAR_PATTERN.findall(part))
        if han_count == 0:
            cleaned_parts.append(part)
            continue
        if korean_count == 0:
            continue

        trimmed = _HAN_SUFFIX_AFTER_PUNCT_PATTERN.sub("", part).strip()
        if _HAN_CHAR_PATTERN.search(trimmed):
            trimmed = _HAN_SUFFIX_PATTERN.sub("", trimmed).strip()
        trimmed = re.sub(r"\s+", " ", trimmed).strip(" ,;:：，、")
        if trimmed:
            cleaned_parts.append(trimmed)

    cleaned = " ".join(cleaned_parts).strip()
    cleaned = re.sub(r"\s+([?!.,])", r"\1", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned


def _sanitize_reply(content: str | None) -> str | None:
    if not content:
        return None
    cleaned = str(content).strip()
    if _KOREAN_CHAR_PATTERN.search(cleaned):
        cleaned = _LEADING_ACK_PATTERN.sub("", cleaned, count=1).lstrip()
    if _HAN_CHAR_PATTERN.search(cleaned):
        cleaned = _strip_han_segments(cleaned)
    cleaned = _TRAILING_EMOJI_AFTER_PUNCT_PATTERN.sub(r"\1", cleaned)
    cleaned = _TRAILING_EMOJI_PATTERN.sub("", cleaned)
    cleaned = _TRAILING_ENGLISH_GARBAGE_PATTERN.sub("", cleaned).rstrip(" ,;:：")
    return cleaned or None


def _contains_unsolicited_code(content: str, prompt: str) -> bool:
    prompt_text = str(prompt or "")
    if any(
        token in prompt_text.lower()
        for token in ("코드", "프로그래밍", "자바", "python", "파이썬", "c++", "c#", "javascript", "js", "개발")
    ):
        return False
    return bool(_CODE_BLOCK_PATTERN.search(content) or _PROGRAMMING_PATTERN.search(content))


def _looks_invalid_for_packet(packet: ChatContextPacket, content: str) -> bool:
    intent_hint = str(packet.get("intent_hint") or "").strip() or "general"
    prompt = str(packet.get("normalized_prompt") or packet.get("prompt") or "").strip()
    content_theme = str(packet.get("content_theme") or "").strip()

    if _looks_mixed_non_korean(content):
        return True

    if _contains_unsolicited_code(content, prompt):
        return True

    if intent_hint == "content_request" and any(token in prompt for token in ("노래", "음악", "플레이리스트", "가사", "영화", "드라마", "책", "소설", "영상")):
        if re.search(r"(에 대해 쉽게 말하면|뜻은|의미는|정의하자면|라고 볼 수 있어요)", content):
            return True
        if content_theme and content_theme not in prompt and re.search(r"(감정적 상태|개념|정의)", content):
            return True

    if intent_hint == "math" and any(token in prompt for token in ("못해", "어려워", "힘들", "싫어", "무서워")):
        if re.search(r"(구체적으로 말씀해|예를 들어 식 풀이|기하학)", content) and _contains_unsolicited_code(content, prompt):
            return True

    if intent_hint in {"smalltalk", "emotional"} and _contains_unsolicited_code(content, prompt):
        return True

    return False


def _call_ollama(packet: ChatContextPacket) -> str | None:
    payload = _build_payload(packet)
    result = _post_json(_llm_endpoint(), payload)
    content = _sanitize_reply(_extract_content(result))
    if content and _looks_mixed_non_korean(content):
        retry_result = _post_json(_llm_endpoint(), _build_payload(packet, retry_korean_only=True))
        retry_content = _sanitize_reply(_extract_content(retry_result))
        if retry_content:
            if _looks_invalid_for_packet(packet, retry_content):
                return None
            return retry_content
        return None
    if content and _looks_invalid_for_packet(packet, content):
        return None
    return content or None


def _should_skip_main_chat_llm(packet: ChatContextPacket) -> bool:
    if str(packet.get("active_mode") or "main").strip() != "main":
        return False
    if _env_flag("COCO_MAIN_CHAT_LLM_ALWAYS", default=False):
        return False

    intent_hint = str(packet.get("intent_hint") or "").strip() or "general"
    normalized = str(packet.get("normalized_prompt") or packet.get("prompt") or "").strip()
    recent_messages = packet.get("recent_messages") or []
    llm_candidate = bool(packet.get("llm_candidate"))

    if not recent_messages and intent_hint in _MAIN_FAST_LOCAL_INTENTS:
        return True
    if not recent_messages and not llm_candidate:
        return True
    if len(recent_messages) <= 1 and intent_hint in _MAIN_FAST_LOCAL_INTENTS and len(normalized) <= 24:
        return True
    return False


def can_use_chat_llm(packet: ChatContextPacket | None = None) -> bool:
    active_mode = str((packet or {}).get("active_mode") or "main").strip()
    if active_mode == "study":
        main_default = _env_flag("COCO_ENABLE_MAIN_CHAT_LLM", default=True)
        return _env_flag("COCO_ENABLE_STUDY_CHAT_LLM", default=main_default)
    return _env_flag("COCO_ENABLE_MAIN_CHAT_LLM", default=True)


def can_use_main_chat_llm(packet: ChatContextPacket | None = None) -> bool:
    return can_use_chat_llm(packet)


def maybe_generate_chat_reply(packet: ChatContextPacket) -> str | None:
    if not can_use_chat_llm(packet):
        return None
    if _should_skip_main_chat_llm(packet):
        return None
    return _call_ollama(packet)


def maybe_generate_main_chat_reply(packet: ChatContextPacket) -> str | None:
    return maybe_generate_chat_reply(packet)


def warmup_chat_llm(active_mode: str = "main") -> bool:
    packet: ChatContextPacket = {"active_mode": "study" if str(active_mode).strip() == "study" else "main"}
    if not can_use_chat_llm(packet):
        return False

    payload = {
        "model": _llm_model(),
        "stream": False,
        "keep_alive": settings.llm_keep_alive,
        "messages": [
            {"role": "system", "content": "간단한 준비 요청이다. 한 글자만 답해라."},
            {"role": "user", "content": "준비"},
        ],
        "options": {
            "temperature": 0,
            "num_predict": 1,
            "num_ctx": settings.ollama_num_ctx,
        },
    }
    return _post_json(_llm_endpoint(), payload) is not None
