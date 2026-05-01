from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from app.core.pipeline import run_service_image_analysis


router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("")
async def upload_image(file: UploadFile = File(...), debug: bool = False):
    suffix = Path(file.filename or "upload.png").suffix or ".png"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp:
        temp.write(await file.read())
        temp_path = temp.name

    analysis = run_service_image_analysis(temp_path, user_query="", debug=debug)
    result = {
        "route": "solver",
        "analysis_engine": analysis.get("analysis_engine", {}),
        "structured_problem": analysis["structured_problem"],
        "solve_result": analysis["solve_result"],
    }
    if debug:
        result["debug"] = analysis.get("debug", {})
    return result
