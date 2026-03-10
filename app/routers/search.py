"""Search endpoint — classify, optimise, and query OpenAlex for academic papers."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.agents.classifier_optimiser import classify_and_optimise
from app.auth import get_api_key
from app.services.openalex import search_papers

router = APIRouter(tags=["Search"], dependencies=[Depends(get_api_key)])


@router.get("/search")
async def search(
    query: str = Query(..., min_length=1, description="Search query for academic papers"),
) -> dict[str, Any]:
    """Run the full agent pipeline: classify → optimise → semantic search.

    Returns the agent analysis alongside the search results.
    """
    # Step 1: Classify field and optimise query via Gemini
    agent_result = await classify_and_optimise(query)

    # Step 2: Search OpenAlex with optimised query + field filter
    try:
        results = await search_papers(
            agent_result["optimised_query"],
            semantic=True,
            field_id=agent_result.get("field_id"),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "original_query": query,
        "field_id": agent_result.get("field_id"),
        "field": agent_result.get("field"),
        "optimised_query": agent_result["optimised_query"],
        "result_count": len(results),
        "results": results,
    }
