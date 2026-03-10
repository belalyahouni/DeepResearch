"""OpenAlex API client — semantic and keyword search for academic papers."""

import os
from typing import Any

import httpx


OPENALEX_BASE_URL = "https://api.openalex.org"
SELECT_FIELDS = "id,doi,display_name,publication_year,cited_by_count,authorships,open_access,primary_location,abstract_inverted_index,relevance_score"


def _reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
    """Convert OpenAlex inverted-index abstract back to plain text."""
    if not inverted_index:
        return None
    word_positions: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort()
    return " ".join(word for _, word in word_positions)


def _clean_paper(raw: dict[str, Any]) -> dict[str, Any]:
    """Transform a raw OpenAlex work object into a clean paper dict."""
    # Extract author names as comma-separated string (matches Paper model)
    authors = ", ".join(
        authorship.get("author", {}).get("display_name", "")
        for authorship in raw.get("authorships", [])
    )

    # PDF / landing page URLs
    primary = raw.get("primary_location") or {}
    oa = raw.get("open_access") or {}

    return {
        "openalex_id": raw.get("id", ""),
        "doi": raw.get("doi"),
        "title": raw.get("display_name", ""),
        "authors": authors,
        "abstract": _reconstruct_abstract(raw.get("abstract_inverted_index")),
        "year": raw.get("publication_year"),
        "url": primary.get("landing_page_url"),
        "open_access_pdf_url": primary.get("pdf_url") or oa.get("oa_url"),
        "citation_count": raw.get("cited_by_count", 0),
        "relevance_score": raw.get("relevance_score"),
    }


async def search_papers(
    query: str,
    *,
    semantic: bool = True,
    field_id: int | None = None,
    per_page: int = 10,
) -> list[dict[str, Any]]:
    """Search OpenAlex for papers matching *query*.

    Uses semantic search (AI embeddings) when *semantic* is True and an API key
    is available, otherwise falls back to keyword search.
    Optionally filters by OpenAlex field ID.

    Raises ``RuntimeError`` if the API call fails.
    """
    api_key = os.getenv("OPEN_ALEX_API_KEY")

    params: dict[str, Any] = {
        "per_page": per_page,
        "select": SELECT_FIELDS,
    }

    if semantic and api_key:
        params["search.semantic"] = query
        params["api_key"] = api_key
    elif api_key:
        params["search"] = query
        params["api_key"] = api_key
    else:
        # No key — keyword search still works with limited quota
        params["search"] = query

    # Semantic search only supports a limited set of filters — topics.field.id
    # is not one of them. Only apply field filter for keyword search.
    if field_id and not (semantic and api_key):
        params["filter"] = f"topics.field.id:{field_id}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{OPENALEX_BASE_URL}/works",
                params=params,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"OpenAlex API returned {exc.response.status_code}: {exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError(
            f"Failed to reach OpenAlex API: {exc}"
        ) from exc

    data = response.json()
    results: list[dict[str, Any]] = data.get("results", [])

    return [_clean_paper(r) for r in results]


async def _generate_related_query(title: str, abstract: str | None) -> str | None:
    """Use Gemini to extract key concepts from a paper and build a semantic
    search query for finding related works.

    Returns an optimised query string, or None if Gemini is unavailable.
    """
    from google import genai

    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        return None

    prompt = (
        "Given this academic paper, extract the 3-5 core research concepts and "
        "produce a single semantic search query (one natural sentence, no bullet "
        "points) that would find closely related papers. Focus on methods, "
        "techniques, and the specific problem being solved — not generic field terms.\n\n"
        f"Title: {title}\n"
    )
    if abstract:
        prompt += f"Abstract: {abstract[:1500]}\n"
    prompt += "\nReturn ONLY the search query, nothing else."

    try:
        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=genai.types.GenerateContentConfig(temperature=0.2),
        )
        query = response.text.strip().strip('"')
        return query if query else None
    except Exception:
        return None


async def get_related_papers(
    openalex_id: str,
    title: str,
    abstract: str | None,
    *,
    per_page: int = 5,
) -> list[dict[str, Any]]:
    """Find papers related to a saved paper using the Gemini agent to build a
    semantic search query from the paper's title and abstract, then running
    that query through OpenAlex semantic search.

    This is an agent-powered feature — Gemini extracts the core research
    concepts and formulates an optimised query, rather than simply proxying
    OpenAlex metadata filters.

    Falls back to a title-based keyword search if Gemini is unavailable.

    Raises ``RuntimeError`` if the OpenAlex API call fails.
    """
    # Step 1: Use Gemini to generate an intelligent search query
    query = await _generate_related_query(title, abstract)

    # Fallback: use the paper title directly
    if not query:
        query = title

    # Step 2: Run semantic search via OpenAlex, excluding the source paper
    results = await search_papers(query, semantic=True, per_page=per_page + 1)

    # Exclude the source paper
    filtered = [r for r in results if r.get("openalex_id") != openalex_id]
    return filtered[:per_page]
