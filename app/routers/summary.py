"""Summarisation endpoint — single API for all summarisation needs.

Accepts any text (abstract for preview, or full paper text for detailed summary).
Optionally tracks community interactions when an arxiv_id is provided.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.summariser import summarise_text
from app.auth import get_api_key
from app.database import get_db
from app.limiter import limiter
from app.schemas.summary import SummariseRequest, SummariseResponse
from app.services.community import track_interaction

router = APIRouter(tags=["Summarisation"], dependencies=[Depends(get_api_key)])


@router.post(
    "/summarise",
    response_model=SummariseResponse,
    summary="Summarise academic text",
    responses={
        401: {"description": "Missing or invalid API key"},
        422: {"description": "Validation error — text field is required and must not be empty"},
        429: {"description": "Rate limit exceeded — max 5 requests per minute"},
        500: {"description": "Gemini summarisation agent failure"},
    },
)
@limiter.limit("5/minute")
async def summarise(
    request: Request,
    body: SummariseRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Summarise any academic text using the Gemini summariser agent.
    Pass an abstract for a quick preview, or the full paper text for a
    comprehensive summary. Provide arxiv_id to record this interaction in
    the community index.
    """
    summary = await summarise_text(body.text)
    if summary is None:
        raise HTTPException(
            status_code=500,
            detail="Summarisation failed — Gemini unavailable or returned an error",
        )

    if body.arxiv_id:
        await track_interaction(body.arxiv_id, db)

    return {"summary": summary}
