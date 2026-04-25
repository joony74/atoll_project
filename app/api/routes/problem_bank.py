from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.problem_bank.repository import (
    ProblemBankError,
    list_banks,
    load_manifest,
    load_problem,
    record_to_analysis,
    record_to_document,
    search_problems,
)


router = APIRouter(prefix="/problem-bank", tags=["problem-bank"])


class ProblemBankSearchRequest(BaseModel):
    query: str = ""
    bank_id: str = "competition_math"
    subject_slug: str | None = None
    level_number: int | None = None
    include_review: bool = False
    include_asy: bool = True
    limit: int = 20


def _problem_bank_error(exc: ProblemBankError) -> HTTPException:
    return HTTPException(status_code=404, detail=str(exc))


@router.get("/banks")
async def banks():
    return {"banks": list_banks()}


@router.get("/banks/{bank_id}/manifest")
async def bank_manifest(bank_id: str):
    try:
        manifest = dict(load_manifest(bank_id))
    except ProblemBankError as exc:
        raise _problem_bank_error(exc) from exc
    manifest.pop("_manifest_path", None)
    manifest.pop("_bank_root", None)
    return manifest


@router.post("/search")
async def search(request: ProblemBankSearchRequest):
    try:
        results = search_problems(
            request.query,
            bank_id=request.bank_id,
            subject_slug=request.subject_slug,
            level_number=request.level_number,
            include_review=request.include_review,
            include_asy=request.include_asy,
            limit=request.limit,
        )
    except ProblemBankError as exc:
        raise _problem_bank_error(exc) from exc
    return {"results": results}


@router.get("/problems/{problem_id}")
async def problem(problem_id: str, bank_id: str = "competition_math"):
    try:
        return load_problem(problem_id, bank_id=bank_id)
    except ProblemBankError as exc:
        raise _problem_bank_error(exc) from exc


@router.get("/problems/{problem_id}/analysis")
async def problem_analysis(problem_id: str, bank_id: str = "competition_math", user_query: str = ""):
    try:
        record = load_problem(problem_id, bank_id=bank_id)
        return record_to_analysis(record, user_query=user_query)
    except ProblemBankError as exc:
        raise _problem_bank_error(exc) from exc


@router.get("/problems/{problem_id}/document")
async def problem_document(problem_id: str, bank_id: str = "competition_math", user_query: str = ""):
    try:
        record = load_problem(problem_id, bank_id=bank_id)
        return record_to_document(record, user_query=user_query)
    except ProblemBankError as exc:
        raise _problem_bank_error(exc) from exc
