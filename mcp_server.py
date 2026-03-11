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
from sqlalchemy import select

from app.agents.chat import chat
from app.agents.classifier_optimiser import classify_and_optimise
from app.agents.summariser import summarise_text as _summarise_text
from app.database import async_session
from app.models.paper import Paper
from app.services.openalex import get_related_papers, search_papers as _search_papers
from app.services.pdf_parser import extract_text_from_pdf

mcp = FastMCP(
    "DeepResearch",
    instructions=(
        "An academic research assistant. Search for papers, save them to your library, "
        "summarise text, ask questions about saved papers, and find related work. "
        "All paper discovery uses OpenAlex with an agentic classification and query "
        "optimisation pipeline powered by Gemini."
    ),
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _paper_to_dict(paper: Paper, *, compact: bool = False) -> dict:
    """Convert a Paper ORM instance to a serialisable dict."""
    d = {
        "id": paper.id,
        "title": paper.title,
        "authors": paper.authors,
        "year": paper.year,
        "tags": paper.tags,
        "summary": paper.summary,
    }
    if not compact:
        d.update({
            "openalex_id": paper.openalex_id,
            "abstract": paper.abstract,
            "url": paper.url,
            "open_access_pdf_url": paper.open_access_pdf_url,
            "citation_count": paper.citation_count,
            "notes": paper.notes,
            "full_text": paper.full_text,
            "created_at": str(paper.created_at),
            "updated_at": str(paper.updated_at),
        })
    return d


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@mcp.resource("papers://library")
async def list_library() -> str:
    """List all saved papers in the library (compact view: id, title, authors, year, tags, summary)."""
    async with async_session() as db:
        result = await db.execute(select(Paper).order_by(Paper.created_at.desc()))
        papers = result.scalars().all()

    if not papers:
        return "The library is empty. Use the search_papers and save_paper tools to add papers."

    return json.dumps([_paper_to_dict(p, compact=True) for p in papers], indent=2, default=str)


@mcp.resource("papers://{paper_id}")
async def get_paper(paper_id: int) -> str:
    """Get full details of a saved paper by its database ID."""
    async with async_session() as db:
        result = await db.execute(select(Paper).where(Paper.id == paper_id))
        paper = result.scalar_one_or_none()

    if not paper:
        return f"Paper with ID {paper_id} not found."

    return json.dumps(_paper_to_dict(paper), indent=2, default=str)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def search_papers(query: str) -> str:
    """Search for academic papers using the agentic pipeline.

    Classifies the query into an academic field, optimises it for semantic search,
    then queries OpenAlex. Returns up to 10 results with title, authors, year,
    abstract, and metadata.
    """
    try:
        classification = await classify_and_optimise(query)
        field_id = classification.get("field_id")
        optimised_query = classification.get("optimised_query", query)

        results = await _search_papers(optimised_query, semantic=True, field_id=field_id)

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
async def save_paper(
    openalex_id: str,
    title: str,
    authors: str,
    abstract: str | None = None,
    year: int | None = None,
    url: str | None = None,
    open_access_pdf_url: str | None = None,
    citation_count: int = 0,
    tags: str | None = None,
    notes: str | None = None,
) -> str:
    """Save a paper to the library.

    Automatically extracts full text from the PDF (if available) and generates
    an AI summary. Use the results from search_papers to fill in the parameters.
    """
    try:
        async with async_session() as db:
            # Check for duplicate
            existing = await db.execute(
                select(Paper).where(Paper.openalex_id == openalex_id)
            )
            if existing.scalar_one_or_none():
                return f"Paper already saved (openalex_id: {openalex_id})."

            paper = Paper(
                openalex_id=openalex_id,
                title=title,
                authors=authors,
                abstract=abstract,
                year=year,
                url=url,
                open_access_pdf_url=open_access_pdf_url,
                citation_count=citation_count,
                tags=tags,
                notes=notes,
            )

            # Extract full text from PDF (best-effort)
            full_text = await extract_text_from_pdf(open_access_pdf_url)
            paper.full_text = full_text

            # Generate summary (best-effort)
            source_text = full_text or abstract
            if source_text:
                try:
                    paper.summary = await _summarise_text(source_text)
                except Exception:
                    pass

            db.add(paper)
            await db.commit()
            await db.refresh(paper)

        summary_note = f" Summary: {paper.summary}" if paper.summary else ""
        return f"Saved paper (ID: {paper.id}): {paper.title}.{summary_note}"

    except Exception as exc:
        return f"Error saving paper: {exc}"


@mcp.tool()
async def update_paper(
    paper_id: int,
    tags: str | None = None,
    notes: str | None = None,
) -> str:
    """Update tags or notes on a saved paper. Only provided fields are changed."""
    try:
        async with async_session() as db:
            result = await db.execute(select(Paper).where(Paper.id == paper_id))
            paper = result.scalar_one_or_none()
            if not paper:
                return f"Paper with ID {paper_id} not found."

            if tags is not None:
                paper.tags = tags
            if notes is not None:
                paper.notes = notes

            await db.commit()
            await db.refresh(paper)

        return f"Updated paper {paper_id}: tags={paper.tags!r}, notes={paper.notes!r}"

    except Exception as exc:
        return f"Error updating paper: {exc}"


@mcp.tool()
async def delete_paper(paper_id: int) -> str:
    """Remove a paper from the library by its database ID."""
    try:
        async with async_session() as db:
            result = await db.execute(select(Paper).where(Paper.id == paper_id))
            paper = result.scalar_one_or_none()
            if not paper:
                return f"Paper with ID {paper_id} not found."

            title = paper.title
            await db.delete(paper)
            await db.commit()

        return f"Deleted paper {paper_id}: {title}"

    except Exception as exc:
        return f"Error deleting paper: {exc}"


@mcp.tool()
async def chat_with_paper(paper_id: int, question: str) -> str:
    """Ask a question about a saved paper.

    Stateless — uses the paper's full text or abstract as context with no
    conversation history. The LLM client manages multi-turn context naturally.
    """
    try:
        async with async_session() as db:
            result = await db.execute(select(Paper).where(Paper.id == paper_id))
            paper = result.scalar_one_or_none()
            if not paper:
                return f"Paper with ID {paper_id} not found."

            paper_text = paper.full_text or paper.abstract or paper.title

        response = await chat(paper_text, history=[], user_message=question)
        if response is None:
            return "Error: chat failed — Gemini unavailable or returned an error."
        return response

    except Exception as exc:
        return f"Error chatting about paper: {exc}"


@mcp.tool()
async def find_related_papers(paper_id: int) -> str:
    """Find papers related to a saved paper.

    Uses the Gemini agent to extract core research concepts and build an optimised
    semantic search query, then queries OpenAlex. Returns up to 5 related papers.
    """
    try:
        async with async_session() as db:
            result = await db.execute(select(Paper).where(Paper.id == paper_id))
            paper = result.scalar_one_or_none()
            if not paper:
                return f"Paper with ID {paper_id} not found."

            openalex_id = paper.openalex_id
            title = paper.title
            abstract = paper.abstract

        results = await get_related_papers(openalex_id, title, abstract)
        return json.dumps(results, indent=2, default=str)

    except Exception as exc:
        return f"Error finding related papers: {exc}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
