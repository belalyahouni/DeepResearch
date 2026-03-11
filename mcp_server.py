"""DeepResearch MCP Server — exposes the research assistant as MCP tools and resources.

Runs alongside the existing FastAPI app. Designed for Claude Desktop via stdio transport.
Reuses existing agents, services, and database layer directly (no HTTP calls).
"""

import json
import os
from pathlib import Path

# Ensure working directory is the project root so the SQLite path resolves correctly
os.chdir(Path(__file__).parent)

from dotenv import load_dotenv

load_dotenv()

from mcp.server.fastmcp import FastMCP
from sqlalchemy import func, select

from app.agents.classifier_optimiser import classify_and_optimise
from app.agents.summariser import summarise_text as _summarise_text
from app.database import async_session
from app.models.arxiv_paper import ArxivPaper
from app.models.community_paper import CommunityPaper
from app.models.paper_note import PaperNote
from app.services.community import track_interaction
from app.services.vector_search import find_related, search_by_query

mcp = FastMCP(
    "DeepResearch",
    instructions=(
        "An academic research assistant. Search a local arXiv AI/ML corpus, "
        "summarise text, find related work, and engage with community features. "
        "Paper discovery uses BGE embeddings with ChromaDB vector search, powered "
        "by an agentic classification and query optimisation pipeline (Gemini). "
        "Community tools let you see which papers are trending by interaction count "
        "and read or add public notes that other users and agents can see."
    ),
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _paper_to_dict(paper: ArxivPaper, *, similarity_score: float | None = None) -> dict:
    """Convert an ArxivPaper ORM instance to a serialisable dict."""
    return {
        "arxiv_id": paper.arxiv_id,
        "title": paper.title,
        "authors": paper.authors,
        "abstract": paper.abstract,
        "categories": paper.categories,
        "year": paper.year,
        "doi": paper.doi,
        "url": paper.url,
        "similarity_score": similarity_score,
    }


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@mcp.resource("arxiv://{arxiv_id}")
async def get_paper(arxiv_id: str) -> str:
    """Get full details of an arXiv paper from the corpus by its arXiv ID."""
    async with async_session() as db:
        result = await db.execute(
            select(ArxivPaper).where(ArxivPaper.arxiv_id == arxiv_id)
        )
        paper = result.scalar_one_or_none()

        if not paper:
            return f"Paper with arXiv ID {arxiv_id} not found in the corpus."

        await track_interaction(arxiv_id, db)

    return json.dumps(_paper_to_dict(paper), indent=2, default=str)


@mcp.resource("arxiv://stats")
async def corpus_stats() -> str:
    """Get statistics about the local arXiv corpus (total papers and year range)."""
    async with async_session() as db:
        count_result = await db.execute(select(func.count()).select_from(ArxivPaper))
        total = count_result.scalar()

        min_year_result = await db.execute(select(func.min(ArxivPaper.year)))
        min_year = min_year_result.scalar()

        max_year_result = await db.execute(select(func.max(ArxivPaper.year)))
        max_year = max_year_result.scalar()

    return json.dumps({
        "total_papers": total,
        "year_range": {"min": min_year, "max": max_year},
    }, indent=2)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def search_papers(query: str) -> str:
    """Search for academic papers using the agentic pipeline.

    Classifies the query into an arXiv AI/ML category, optimises it for semantic search,
    then performs BGE vector similarity search over the local arXiv AI/ML corpus.
    Returns up to 10 results with title, authors, year, abstract, and metadata.
    """
    try:
        classification = await classify_and_optimise(query)
        optimised_query = classification.get("optimised_query", query)

        hits = search_by_query(optimised_query)

        # Look up full metadata from SQLite
        arxiv_ids = [h["arxiv_id"] for h in hits]
        score_map = {h["arxiv_id"]: h["similarity_score"] for h in hits}

        async with async_session() as db:
            result = await db.execute(
                select(ArxivPaper).where(ArxivPaper.arxiv_id.in_(arxiv_ids))
            )
            papers = {p.arxiv_id: p for p in result.scalars().all()}

        results = []
        for aid in arxiv_ids:
            paper = papers.get(aid)
            if paper:
                results.append(_paper_to_dict(paper, similarity_score=score_map.get(aid)))

        output = {
            "original_query": query,
            "field": classification.get("field"),
            "optimised_query": optimised_query,
            "result_count": len(results),
            "results": results,
        }
        return json.dumps(output, indent=2, default=str)

    except Exception as exc:
        return f"Error searching papers: {exc}"


@mcp.tool()
async def summarise_text(text: str) -> str:
    """Summarise academic text (abstract or full paper) using the Gemini summariser agent.

    For abstracts (short text): returns a 1-sentence summary.
    For full papers (long text): returns a 2-sentence summary.
    """
    try:
        summary = await _summarise_text(text)
        if summary is None:
            return "Error: summarisation failed — Gemini unavailable or returned an error."
        return summary
    except Exception as exc:
        return f"Error summarising text: {exc}"


@mcp.tool()
async def find_related_papers(arxiv_id: str) -> str:
    """Find papers related to a given arXiv paper using BGE vector similarity.

    Looks up the paper's embedding in ChromaDB and returns up to 5 similar papers
    from the corpus.
    """
    try:
        # Verify paper exists in SQLite
        async with async_session() as db:
            result = await db.execute(
                select(ArxivPaper).where(ArxivPaper.arxiv_id == arxiv_id)
            )
            paper = result.scalar_one_or_none()
            if not paper:
                return f"Paper with arXiv ID {arxiv_id} not found in the corpus."

        hits = find_related(arxiv_id, n_results=5)

        # Look up full metadata and track interaction
        related_ids = [h["arxiv_id"] for h in hits]
        score_map = {h["arxiv_id"]: h["similarity_score"] for h in hits}

        async with async_session() as db:
            await track_interaction(arxiv_id, db)
            result = await db.execute(
                select(ArxivPaper).where(ArxivPaper.arxiv_id.in_(related_ids))
            )
            papers = {p.arxiv_id: p for p in result.scalars().all()}

        results = []
        for aid in related_ids:
            p = papers.get(aid)
            if p:
                results.append(_paper_to_dict(p, similarity_score=score_map.get(aid)))

        return json.dumps(results, indent=2, default=str)

    except Exception as exc:
        return f"Error finding related papers: {exc}"


@mcp.tool()
async def get_community_papers(limit: int = 10) -> str:
    """Get the most actively engaged papers in the community, ranked by interaction count.

    Papers enter the community index when they are looked up, summarised, or used
    in a related-papers query — by any user or agent. Useful for discovering what
    the community is currently reading and researching.
    """
    try:
        async with async_session() as db:
            result = await db.execute(
                select(CommunityPaper, ArxivPaper)
                .join(ArxivPaper, CommunityPaper.arxiv_id == ArxivPaper.arxiv_id)
                .order_by(CommunityPaper.interaction_count.desc())
                .limit(max(1, min(limit, 100)))
            )
            rows = result.all()

        if not rows:
            return "No papers in the community index yet."

        output = [
            {
                "arxiv_id": community.arxiv_id,
                "interaction_count": community.interaction_count,
                "last_interacted_at": str(community.last_interacted_at),
                "title": paper.title,
                "authors": paper.authors,
                "year": paper.year,
                "url": paper.url,
            }
            for community, paper in rows
        ]
        return json.dumps(output, indent=2, default=str)

    except Exception as exc:
        return f"Error retrieving community papers: {exc}"


@mcp.tool()
async def get_paper_notes(arxiv_id: str) -> str:
    """Get all public notes attached to a specific arXiv paper.

    Notes are community-contributed annotations visible to all API consumers
    and agents. Useful for seeing what others have observed about a paper.
    """
    try:
        async with async_session() as db:
            result = await db.execute(
                select(PaperNote).where(PaperNote.arxiv_id == arxiv_id)
            )
            notes = result.scalars().all()

        if not notes:
            return f"No notes found for paper {arxiv_id}."

        output = [
            {
                "id": note.id,
                "content": note.content,
                "created_at": str(note.created_at),
                "updated_at": str(note.updated_at),
            }
            for note in notes
        ]
        return json.dumps(output, indent=2)

    except Exception as exc:
        return f"Error retrieving notes: {exc}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
