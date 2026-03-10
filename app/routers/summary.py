"""Summarisation endpoint — single API for all summarisation needs.

Accepts any text (abstract for preview, or full paper text for detailed summary).
No database interaction — callers decide what to do with the result.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.agents.summariser import summarise_text
from app.auth import get_api_key
from app.schemas.summary import SummariseRequest, SummariseResponse

router = APIRouter(tags=["Summarisation"], dependencies=[Depends(get_api_key)])


@router.post(
    "/summarise",
    response_model=SummariseResponse,
    summary="Summarise academic text",
    responses={
        401: {"description": "Missing or invalid API key"},
        422: {"description": "Validation error — text field is required and must not be empty"},
        500: {"description": "Gemini summarisation agent failure"},
    },
)
async def summarise(body: SummariseRequest) -> dict:
    """Summarise any academic text using the Gemini summariser agent.
    Pass an abstract for a quick preview, or the full paper text for a
    comprehensive summary.
    """
    summary = await summarise_text(body.text)
    if summary is None:
        raise HTTPException(
            status_code=500,
            detail="Summarisation failed — Gemini unavailable or returned an error",
        )
    return {"summary": summary}
