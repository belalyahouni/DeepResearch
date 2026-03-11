"""Corpus lookup endpoints — get a paper or find related papers from the arXiv corpus."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_api_key
from app.database import get_db
from app.models.arxiv_paper import ArxivPaper
from app.schemas.arxiv_paper import ArxivPaperResponse
from app.services.community import track_interaction
from app.services.vector_search import find_related

router = APIRouter(prefix="/papers", tags=["Papers"], dependencies=[Depends(get_api_key)])


@router.get(
    "/{arxiv_id}",
    response_model=ArxivPaperResponse,
    summary="Get a paper from the corpus",
    responses={
        401: {"description": "Missing or invalid API key"},
        404: {"description": "Paper not found in the corpus"},
    },
)
async def get_paper(
    arxiv_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Look up an arXiv paper by its ID from the local AI/ML corpus."""
    result = await db.execute(
        select(ArxivPaper).where(ArxivPaper.arxiv_id == arxiv_id)
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found in corpus")

    await track_interaction(arxiv_id, db)

    return {
        "arxiv_id": paper.arxiv_id,
        "title": paper.title,
        "authors": paper.authors,
        "abstract": paper.abstract,
        "categories": paper.categories,
        "year": paper.year,
        "doi": paper.doi,
        "url": paper.url,
        "similarity_score": None,
    }


@router.get(
    "/{arxiv_id}/related",
    response_model=list[ArxivPaperResponse],
    summary="Find related papers",
    responses={
        401: {"description": "Missing or invalid API key"},
        404: {"description": "Paper not found in the corpus or vector store"},
        500: {"description": "Vector search failure"},
    },
)
async def related_papers(
    arxiv_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Find papers related to the given arXiv paper using BGE vector similarity.
    Returns up to 5 related papers from the corpus.
    """
    # Verify paper exists in SQLite
    result = await db.execute(
        select(ArxivPaper).where(ArxivPaper.arxiv_id == arxiv_id)
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found in corpus")

    await track_interaction(arxiv_id, db)

    try:
        hits = find_related(arxiv_id, n_results=5)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Look up full metadata
    related_ids = [h["arxiv_id"] for h in hits]
    score_map = {h["arxiv_id"]: h["similarity_score"] for h in hits}

    result = await db.execute(
        select(ArxivPaper).where(ArxivPaper.arxiv_id.in_(related_ids))
    )
    papers = {p.arxiv_id: p for p in result.scalars().all()}

    results = []
    for aid in related_ids:
        p = papers.get(aid)
        if p:
            results.append({
                "arxiv_id": p.arxiv_id,
                "title": p.title,
                "authors": p.authors,
                "abstract": p.abstract,
                "categories": p.categories,
                "year": p.year,
                "doi": p.doi,
                "url": p.url,
                "similarity_score": score_map.get(aid),
            })
    return results
