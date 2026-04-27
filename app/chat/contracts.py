from __future__ import annotations

from typing import Literal, TypedDict


ChatMode = Literal["main", "study"]
ChatRole = Literal["assistant", "user"]
ChatIntent = Literal["smalltalk", "self_info", "opinion", "emotional", "app_help", "content_request", "concept", "math", "general"]
GroundingConfidence = Literal["low", "medium", "high"]


class ChatMessage(TypedDict, total=False):
    role: ChatRole
    content: str
    doc_id: str | None
    created_at: float
    kind: str
    preview_image_path: str
    preview_image_label: str


class StoredDocument(TypedDict, total=False):
    doc_id: str
    file_name: str
    file_path: str
    created_at: float
    registered_at: float
    last_opened_at: float
    latest_user_query: str


class MainChatContext(TypedDict, total=False):
    last_intent: ChatIntent
    last_concept_term: str | None
    last_concept_stage: str | None
    last_updated_at: float


class StoredConcept(TypedDict, total=False):
    term: str
    summary: str
    confidence: GroundingConfidence
    source: str
    updated_at: float


class AppState(TypedDict, total=False):
    documents: list[StoredDocument]
    selected_doc_id: str | None
    chat_mode: ChatMode
    last_active_chat_mode: ChatMode
    last_active_doc_id: str | None
    last_active_at: float
    main_chat_history: list[ChatMessage]
    main_chat_context: MainChatContext
    custom_concepts: dict[str, StoredConcept]
    chat_history: list[ChatMessage]
    booted_at: float


class ChatContextPacket(TypedDict, total=False):
    prompt: str
    normalized_prompt: str
    recent_messages: list[ChatMessage]
    active_mode: ChatMode
    has_documents: bool
    document_count: int
    custom_concept_count: int
    last_intent: str
    last_concept_term: str | None
    last_concept_stage: str | None
    intent_hint: ChatIntent | None
    content_theme: str | None
    ambiguity_score: int
    ambiguity_reasons: list[str]
    llm_candidate: bool
    selected_doc_id: str | None
    selected_doc_name: str | None
    study_problem_text: str | None
    study_math_topic: str | None
    study_answer_candidate: str | None
    study_steps: list[str]
    study_expressions: list[str]
    study_question_type: str | None
    study_latest_user_query: str | None
    study_reference_solution: str | None
    study_source: str | None


class GroundingResult(TypedDict, total=False):
    confidence: GroundingConfidence
    facts: list[str]
    summary: str
    active_mode: ChatMode
    document_count: int
    selected_doc_id: str | None
    selected_doc_name: str | None


class ConceptSearchResult(TypedDict, total=False):
    term: str
    summary: str
    confidence: GroundingConfidence
    source: str
