from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from app.core.pipeline import run_upload_pipeline


router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("")
async def upload_image(file: UploadFile = File(...), debug: bool = False):
    suffix = Path(file.filename or "upload.png").suffix or ".png"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp:
        temp.write(await file.read())
        temp_path = temp.name

    payload = run_upload_pipeline(temp_path, user_query="", debug=debug)
    result = {
        "route": payload["route"],
        "structured_problem": payload["structured_problem"].model_dump(),
    }
    if debug:
        result["debug"] = payload.get("debug", {})
    return result
