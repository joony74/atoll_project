from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = os.getenv("COCO_OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip()
    ollama_vision_model: str = os.getenv("COCO_OLLAMA_VISION_MODEL", "llama3.2-vision").strip() or "llama3.2-vision"
    ollama_text_model: str = os.getenv("COCO_OLLAMA_TEXT_MODEL", "mistral").strip() or "mistral"
    request_timeout_seconds: int = int(os.getenv("COCO_ENGINE_TIMEOUT", "25"))
    debug_enabled: bool = os.getenv("COCO_DEBUG_MODE", "").strip().lower() in {"1", "true", "yes", "on"}
    image_cache_dir: str = os.getenv("COCO_ENGINE_IMAGE_CACHE_DIR", "data/image_cache")
    math_min_signal_score: float = float(os.getenv("COCO_MATH_MIN_SIGNAL_SCORE", "0.2"))
    low_confidence_threshold: float = float(os.getenv("COCO_LOW_CONFIDENCE_THRESHOLD", "0.45"))


settings = Settings()
