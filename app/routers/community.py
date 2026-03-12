"""Community papers endpoints — surface the most actively engaged papers."""

from datetime import datetime, timedelta, timezone
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_api_key
from app.database import get_db
from app.models.arxiv_paper import ArxivPaper
from app.models.community_interaction import CommunityInteraction
from app.models.community_paper import CommunityPaper
from app.schemas.community_paper import CommunityListResponse, CommunityPaperResponse

router = APIRouter(prefix="/community", tags=["Community"], dependencies=[Depends(get_api_key)])

_PERIOD_DAYS = {"week": 7, "month": 30, "year": 365}


class Period(str, Enum):
    week = "week"
    month = "month"
    year = "year"


@router.get(
    "",
    response_model=CommunityListResponse,
    summary="List most popular papers",
    description=(
        "Returns papers ranked by community interaction count. "
        "Use the `period` parameter to filter by a rolling time window: "
        "`week` (last 7 days), `month` (last 30 days), `year` (last 365 days). "
        "Omit `period` for all-time rankings. "
        "A paper enters this index the first time it is directly accessed or summarised. "
        "Count increments on: direct paper lookup, summarisation, and related-papers queries."
    ),
    responses={
        401: {"description": "Missing or invalid API key"},
    },
)
async def list_community_papers(
    limit: int = Query(default=20, ge=1, le=100, description="Number of papers to return (max 100)"),
    period: Period | None = Query(
        default=None,
        description="Rolling time window: week (7d), month (30d), year (365d). Omit for all-time.",
    ),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the top papers by interaction count for the given period (or all-time)."""
    if period is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=_PERIOD_DAYS[period])

        result = await db.execute(
            select(CommunityInteraction.arxiv_id, func.count().label("count"))
            .where(CommunityInteraction.interacted_at >= cutoff)
            .group_by(CommunityInteraction.arxiv_id)
            .order_by(desc("count"))
            .limit(limit)
        )
        period_rows = result.all()

        if not period_rows:
            return {"total": 0, "papers": []}

        arxiv_ids = [row.arxiv_id for row in period_rows]

        paper_result = await db.execute(
            select(ArxivPaper).where(ArxivPaper.arxiv_id.in_(arxiv_ids))
        )
        papers = {p.arxiv_id: p for p in paper_result.scalars().all()}

        community_result = await db.execute(
            select(CommunityPaper).where(CommunityPaper.arxiv_id.in_(arxiv_ids))
        )
        community_map = {c.arxiv_id: c for c in community_result.scalars().all()}

        response_papers = []
        for row in period_rows:
            paper = papers.get(row.arxiv_id)
            community = community_map.get(row.arxiv_id)
            if paper and community:
                response_papers.append(CommunityPaperResponse(
                    arxiv_id=row.arxiv_id,
                    interaction_count=row.count,
                    last_interacted_at=community.last_interacted_at,
                    title=paper.title,
                    authors=paper.authors,
                    categories=paper.categories,
                    year=paper.year,
                    url=paper.url,
                ))

        return {"total": len(response_papers), "papers": response_papers}

    # All-time: rank by CommunityPaper.interaction_count
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
