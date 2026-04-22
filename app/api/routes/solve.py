from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.pipeline import run_solve_pipeline
from app.models.problem_schema import ProblemSchema


router = APIRouter(tags=["solve"])


class SolveRequest(BaseModel):
    image_path: str = ""
    user_query: str = ""
    structured_problem: ProblemSchema | None = None
    debug: bool = False


@router.post("/solve")
async def solve_problem(request: SolveRequest):
    payload = run_solve_pipeline(
        image_path=request.image_path or None,
        structured_problem=request.structured_problem,
        user_query=request.user_query,
        debug=request.debug,
    )
    result = {
        "structured_problem": payload["structured_problem"].model_dump(),
        "solve_result": payload["solve_result"].model_dump(),
        "response": payload["solve_result"].explanation,
    }
    if request.debug:
        result["debug"] = payload.get("debug", {})
    return result


@router.post("/debug")
async def debug_problem(request: SolveRequest):
    payload = run_solve_pipeline(
        image_path=request.image_path or None,
        structured_problem=request.structured_problem,
        user_query=request.user_query,
        debug=True,
    )
    return payload.get("debug", {})
