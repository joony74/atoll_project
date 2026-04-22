from __future__ import annotations

import base64
from pathlib import Path

import requests

from coco_engine.core.config import settings
from coco_engine.utils.text_normalizer import normalize_math_text


class OllamaVisionClient:
    def __init__(self, base_url: str | None = None, model_name: str | None = None, timeout: int | None = None) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model_name = model_name or settings.ollama_vision_model
        self.timeout = timeout or settings.request_timeout_seconds

    def _prompt(self) -> str:
        return (
            "수학 문제 이미지를 보고 보이는 문제 문장, 수식, 보기, 좌표, 함수 표기를 최대한 복원해라. "
            "OCR이 깨져 보여도 수학 문제 후보를 추정해서 한국어 평문으로 반환해라. "
            "정답을 풀지는 말고, 문제 본문과 수식 후보만 복원해라."
        )

    def interpret_math_image(self, image_path: str) -> dict:
        if not image_path or not Path(image_path).exists():
            return {"engine": "ollama_vision", "available": False, "text": "", "confidence": 0.0, "error": "missing_image"}
        try:
            encoded = base64.b64encode(Path(image_path).read_bytes()).decode("utf-8")
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": self._prompt(),
                    "images": [encoded],
                    "stream": False,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            text = normalize_math_text(payload.get("response") or "")
            return {
                "engine": "ollama_vision",
                "available": True,
                "text": text,
                "confidence": 0.68 if text else 0.0,
                "raw": payload,
            }
        except Exception as exc:
            return {
                "engine": "ollama_vision",
                "available": False,
                "text": "",
                "confidence": 0.0,
                "error": str(exc),
            }
