"""Public paper notes endpoints — create, read, update, and delete notes on arXiv papers."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_api_key
from app.database import get_db
from app.limiter import limiter
from app.models.arxiv_paper import ArxivPaper
from app.models.paper_note import PaperNote
from app.schemas.paper_note import NoteCreate, NoteResponse, NoteUpdate

# Two routers — notes are both paper-scoped and top-level
papers_router = APIRouter(prefix="/papers", tags=["Notes"], dependencies=[Depends(get_api_key)])
notes_router = APIRouter(prefix="/notes", tags=["Notes"], dependencies=[Depends(get_api_key)])


@papers_router.post(
    "/{arxiv_id}/notes",
    response_model=NoteResponse,
    status_code=201,
    summary="Add a public note to a paper",
    responses={
        401: {"description": "Missing or invalid API key"},
        404: {"description": "Paper not found in corpus"},
        422: {"description": "Validation error — content is required"},
        429: {"description": "Rate limit exceeded — max 10 notes per minute"},
    },
)
@limiter.limit("10/minute")
async def create_note(
    request: Request,
    arxiv_id: str,
    body: NoteCreate,
    db: AsyncSession = Depends(get_db),
) -> PaperNote:
    """Add a public note to an arXiv paper. Notes are visible to all API consumers and agents."""
    result = await db.execute(
        select(ArxivPaper).where(ArxivPaper.arxiv_id == arxiv_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Paper not found in corpus")

    note = PaperNote(arxiv_id=arxiv_id, content=body.content)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@papers_router.get(
    "/{arxiv_id}/notes",
    response_model=list[NoteResponse],
    summary="Get all notes for a paper",
    responses={
        401: {"description": "Missing or invalid API key"},
        404: {"description": "Paper not found in corpus"},
    },
)
async def list_notes(
    arxiv_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[PaperNote]:
    """Retrieve all public notes attached to a specific arXiv paper."""
    result = await db.execute(
        select(ArxivPaper).where(ArxivPaper.arxiv_id == arxiv_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Paper not found in corpus")

    notes_result = await db.execute(
        select(PaperNote).where(PaperNote.arxiv_id == arxiv_id)
    )
    return list(notes_result.scalars().all())


@notes_router.patch(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Update a note",
    responses={
        401: {"description": "Missing or invalid API key"},
        404: {"description": "Note not found"},
        422: {"description": "Validation error — content is required"},
        429: {"description": "Rate limit exceeded — max 10 updates per minute"},
    },
)
@limiter.limit("10/minute")
async def update_note(
    request: Request,
    note_id: int,
    body: NoteUpdate,
    db: AsyncSession = Depends(get_db),
) -> PaperNote:
    """Update the content of an existing note by its ID."""
    result = await db.execute(
        select(PaperNote).where(PaperNote.id == note_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.content = body.content
    await db.commit()
    await db.refresh(note)
    return note


@notes_router.delete(
    "/{note_id}",
    status_code=204,
    summary="Delete a note",
    responses={
        401: {"description": "Missing or invalid API key"},
        404: {"description": "Note not found"},
    },
)
async def delete_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Permanently delete a note by its ID."""
    result = await db.execute(
        select(PaperNote).where(PaperNote.id == note_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    await db.delete(note)
    await db.commit()
