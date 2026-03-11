"""Search endpoint — classify, optimise, and vector search the arXiv corpus."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.classifier_optimiser import classify_and_optimise
from app.auth import get_api_key
from app.database import get_db
from app.models.arxiv_paper import ArxivPaper
from app.schemas.search import SearchResponse
from app.services.vector_search import search_by_query

router = APIRouter(tags=["Search"], dependencies=[Depends(get_api_key)])


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Search for academic papers",
    responses={
        401: {"description": "Missing or invalid API key"},
        422: {"description": "Validation error — query parameter is required"},
        500: {"description": "Vector search or Gemini agent failure"},
    },
)
async def search(
    query: str = Query(..., min_length=1, description="Search query for academic papers"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Run the full agentic search pipeline: classify the arXiv AI/ML category,
    optimise the query, then perform BGE vector similarity search
    over the local arXiv AI/ML corpus.
    """
    # Step 1: Classify and optimise via Gemini
    agent_result = await classify_and_optimise(query)

    # Step 2: Vector search with optimised query
    try:
        hits = search_by_query(agent_result["optimised_query"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Step 3: Look up full metadata from SQLite
    arxiv_ids = [h["arxiv_id"] for h in hits]
    score_map = {h["arxiv_id"]: h["similarity_score"] for h in hits}

    result = await db.execute(
        select(ArxivPaper).where(ArxivPaper.arxiv_id.in_(arxiv_ids))
    )
    papers = {p.arxiv_id: p for p in result.scalars().all()}

    # Build results preserving the ranked order from ChromaDB
    results = []
    for aid in arxiv_ids:
        paper = papers.get(aid)
        if paper:
            results.append({
                "arxiv_id": paper.arxiv_id,
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "categories": paper.categories,
                "year": paper.year,
                "doi": paper.doi,
                "url": paper.url,
                "similarity_score": score_map.get(aid),
            })

    return {
        "original_query": query,
        "field": agent_result.get("field"),
        "optimised_query": agent_result["optimised_query"],
        "result_count": len(results),
        "results": results,
    }
