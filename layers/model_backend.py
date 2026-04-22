from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


@dataclass
class ModelBackendConfig:
    family: str = "llama"
    model_name: str = "llama-instruct-local"
    endpoint: str = ""
    mode: str = "local"


class TextModelBackend(Protocol):
    config: ModelBackendConfig

    def generate(self, system_prompt: str, developer_prompt: str, user_prompt: str) -> str:
        ...


class NullBackend:
    def __init__(self, config: ModelBackendConfig | None = None) -> None:
        self.config = config or ModelBackendConfig()

    def generate(self, system_prompt: str, developer_prompt: str, user_prompt: str) -> str:
        return ""


class OpenAIStyleLocalBackend(NullBackend):
    """
    로컬 OpenAI-style endpoint용 자리.
    현재 프로젝트에서는 외부 호출 없이 추후 교체 가능하도록 인터페이스만 고정한다.
    """


def _env_flag(name: str, default: bool = False) -> bool:
    raw = str(os.getenv(name, "") or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def get_default_backend() -> TextModelBackend:
    allow_remote = _env_flag("COCO_ALLOW_REMOTE_LLM", default=False)
    family = os.getenv("COCO_LLM_FAMILY", "llama").strip().lower() or "llama"
    model_name = os.getenv("COCO_LLM_MODEL", f"{family}-instruct-local").strip() or f"{family}-instruct-local"
    endpoint = os.getenv("COCO_LLM_ENDPOINT", "").strip() if allow_remote else ""
    config = ModelBackendConfig(
        family=family if family in {"llama", "mistral"} else "llama",
        model_name=model_name,
        endpoint=endpoint,
        mode="openai_style" if endpoint else "local",
    )
    return OpenAIStyleLocalBackend(config)
