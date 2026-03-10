"""CRUD endpoints for saved papers."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.paper import Paper
from app.schemas.paper import PaperCreate, PaperResponse, PaperUpdate

router = APIRouter(prefix="/papers", tags=["Papers"])


@router.post("", response_model=PaperResponse, status_code=201)
async def create_paper(
    body: PaperCreate,
    db: AsyncSession = Depends(get_db),
) -> Paper:
    """Save a paper to the library."""
    # Check for duplicate
    existing = await db.execute(
        select(Paper).where(Paper.openalex_id == body.openalex_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Paper already saved")

    paper = Paper(**body.model_dump())
    db.add(paper)
    await db.commit()
    await db.refresh(paper)
    return paper


@router.get("", response_model=list[PaperResponse])
async def list_papers(
    tags: str | None = Query(None, description="Filter by tag (substring match)"),
    db: AsyncSession = Depends(get_db),
) -> list[Paper]:
    """List all saved papers, optionally filtered by tag."""
    stmt = select(Paper).order_by(Paper.created_at.desc())
    if tags:
        stmt = stmt.where(Paper.tags.contains(tags))
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: int,
    db: AsyncSession = Depends(get_db),
) -> Paper:
    """Get a specific saved paper by ID."""
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@router.put("/{paper_id}", response_model=PaperResponse)
async def update_paper(
    paper_id: int,
    body: PaperUpdate,
    db: AsyncSession = Depends(get_db),
) -> Paper:
    """Update tags or notes on a saved paper."""
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


@router.delete("/{paper_id}", status_code=204)
async def delete_paper(
    paper_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a paper from the library."""
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    await db.delete(paper)
    await db.commit()
