"""CRUD endpoints for saved papers."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_api_key
from app.database import get_db
from app.models.paper import Paper
from app.schemas.paper import PaperCreate, PaperResponse, PaperUpdate
from app.schemas.search import SearchResultItem
from app.routers.summary import summarise
from app.schemas.summary import SummariseRequest
from app.services.openalex import get_related_papers
from app.services.pdf_parser import extract_text_from_pdf

router = APIRouter(prefix="/papers", tags=["Papers"], dependencies=[Depends(get_api_key)])


@router.post(
    "",
    response_model=PaperResponse,
    status_code=201,
    summary="Save a paper to the library",
    responses={
        401: {"description": "Missing or invalid API key"},
        409: {"description": "Paper with this OpenAlex ID already saved"},
        422: {"description": "Validation error — missing required fields"},
        500: {"description": "Internal server error"},
    },
)
async def create_paper(
    body: PaperCreate,
    db: AsyncSession = Depends(get_db),
) -> Paper:
    """Save a paper to the library. Automatically extracts full text from the
    PDF (if available) and generates an AI summary via the Gemini summariser.
    Both extraction and summarisation are best-effort and never block the save.
    """
    # Check for duplicate
    existing = await db.execute(
        select(Paper).where(Paper.openalex_id == body.openalex_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Paper already saved")

    paper = Paper(**body.model_dump())

    # Extract full text from PDF if available (best-effort, never blocks save)
    full_text = await extract_text_from_pdf(paper.open_access_pdf_url)
    paper.full_text = full_text

    # Generate summary via the /summarise API (best-effort, never blocks save)
    source_text = full_text or paper.abstract
    if source_text:
        try:
            result = await summarise(SummariseRequest(text=source_text))
            paper.summary = result["summary"]
        except Exception:
            pass  # summarisation failure must not block paper save

    db.add(paper)
    await db.commit()
    await db.refresh(paper)
    return paper


@router.get(
    "",
    response_model=list[PaperResponse],
    summary="List saved papers",
    responses={
        401: {"description": "Missing or invalid API key"},
    },
)
async def list_papers(
    tags: str | None = Query(None, description="Filter by tag (substring match)"),
    db: AsyncSession = Depends(get_db),
) -> list[Paper]:
    """List all saved papers, optionally filtered by tag. Results are ordered
    by creation date (newest first).
    """
    stmt = select(Paper).order_by(Paper.created_at.desc())
    if tags:
        stmt = stmt.where(Paper.tags.contains(tags))
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get(
    "/{paper_id}",
    response_model=PaperResponse,
    summary="Get a saved paper",
    responses={
        401: {"description": "Missing or invalid API key"},
        404: {"description": "Paper not found"},
    },
)
async def get_paper(
    paper_id: int,
    db: AsyncSession = Depends(get_db),
) -> Paper:
    """Get a specific saved paper by its database ID. Returns the full paper
    record including extracted text and AI summary.
    """
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@router.put(
    "/{paper_id}",
    response_model=PaperResponse,
    summary="Update paper tags or notes",
    responses={
        401: {"description": "Missing or invalid API key"},
        404: {"description": "Paper not found"},
        422: {"description": "Validation error"},
    },
)
async def update_paper(
    paper_id: int,
    body: PaperUpdate,
    db: AsyncSession = Depends(get_db),
) -> Paper:
    """Update the tags or notes on a saved paper. Only fields included in the
    request body are updated; omitted fields remain unchanged.
    """
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(paper, field, value)

    await db.commit()
    await db.refresh(paper)
    return paper


@router.delete(
    "/{paper_id}",
    status_code=204,
    summary="Delete a saved paper",
    responses={
        401: {"description": "Missing or invalid API key"},
        404: {"description": "Paper not found"},
    },
)
async def delete_paper(
    paper_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a paper from the library. This also deletes any associated
    conversation history.
    """
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    await db.delete(paper)
    await db.commit()


@router.get(
    "/{paper_id}/related",
    response_model=list[SearchResultItem],
    summary="Find related papers",
    responses={
        401: {"description": "Missing or invalid API key"},
        404: {"description": "Paper not found"},
        500: {"description": "OpenAlex API failure"},
    },
)
async def related_papers(
    paper_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Find papers related to a saved paper using the Gemini agent to extract
    core research concepts and build an optimised semantic search query.
    Returns up to 5 related works from OpenAlex, excluding the original.
    """
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    try:
        results = await get_related_papers(paper.openalex_id, paper.title, paper.abstract)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return results
