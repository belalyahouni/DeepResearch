"""Community papers endpoints — surface the most actively engaged papers."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_api_key
from app.database import get_db
from app.models.arxiv_paper import ArxivPaper
from app.models.community_paper import CommunityPaper
from app.schemas.community_paper import CommunityListResponse, CommunityPaperResponse

router = APIRouter(prefix="/community", tags=["Community"], dependencies=[Depends(get_api_key)])


@router.get(
    "",
    response_model=CommunityListResponse,
    summary="List most popular papers",
    description=(
        "Returns papers ranked by community interaction count. "
        "A paper enters this index the first time it is directly accessed or summarised. "
        "Count increments on: direct paper lookup, summarisation, and related-papers queries."
    ),
    responses={
        401: {"description": "Missing or invalid API key"},
    },
)
async def list_community_papers(
    limit: int = Query(default=20, ge=1, le=100, description="Number of papers to return (max 100)"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the top papers by interaction count, joined with corpus metadata."""
    result = await db.execute(
        select(CommunityPaper)
        .order_by(desc(CommunityPaper.interaction_count))
        .limit(limit)
    )
    community_rows = result.scalars().all()

    if not community_rows:
        return {"total": 0, "papers": []}

    arxiv_ids = [row.arxiv_id for row in community_rows]
    paper_result = await db.execute(
        select(ArxivPaper).where(ArxivPaper.arxiv_id.in_(arxiv_ids))
    )
    papers = {p.arxiv_id: p for p in paper_result.scalars().all()}

    response_papers = []
    for row in community_rows:
        paper = papers.get(row.arxiv_id)
        if paper:
            response_papers.append(CommunityPaperResponse(
                arxiv_id=row.arxiv_id,
                interaction_count=row.interaction_count,
                last_interacted_at=row.last_interacted_at,
                title=paper.title,
                authors=paper.authors,
                categories=paper.categories,
                year=paper.year,
                url=paper.url,
            ))

    return {"total": len(response_papers), "papers": response_papers}


@router.get(
    "/{arxiv_id}",
    response_model=CommunityPaperResponse,
    summary="Get community stats for a paper",
    description=(
        "Returns the interaction count and last activity timestamp for a specific paper. "
        "A paper only appears here once it has been accessed via GET /papers/{arxiv_id}, "
        "POST /summarise (with arxiv_id), or GET /papers/{arxiv_id}/related."
    ),
    responses={
        401: {"description": "Missing or invalid API key"},
        404: {"description": "Paper has not been interacted with yet — not in the community index"},
    },
)
async def get_community_paper(
    arxiv_id: str,
    db: AsyncSession = Depends(get_db),
) -> CommunityPaperResponse:
    """Get the community interaction stats for a specific paper."""
    result = await db.execute(
        select(CommunityPaper, ArxivPaper)
        .join(ArxivPaper, CommunityPaper.arxiv_id == ArxivPaper.arxiv_id)
        .where(CommunityPaper.arxiv_id == arxiv_id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Paper not found in community index")

    community, paper = row
    return CommunityPaperResponse(
        arxiv_id=community.arxiv_id,
        interaction_count=community.interaction_count,
        last_interacted_at=community.last_interacted_at,
        title=paper.title,
        authors=paper.authors,
        categories=paper.categories,
        year=paper.year,
        url=paper.url,
    )
