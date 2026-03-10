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


async def get_related_papers(
    openalex_id: str,
    *,
    per_page: int = 5,
) -> list[dict[str, Any]]:
    """Find papers related to *openalex_id* by fetching its topics from
    OpenAlex and filtering by the same domain, field, and subfield.

    The OpenAlex topics hierarchy is: domain → field → subfield → topic.
    We extract all three levels from the paper's primary topic and combine
    them into a single filter so results stay within the same narrow area
    of research.

    Raises ``RuntimeError`` if the API call fails.
    """
    api_key = os.getenv("OPEN_ALEX_API_KEY")

    # Step 1: Fetch the source work to get its topics
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            params: dict[str, Any] = {}
            if api_key:
                params["api_key"] = api_key
            resp = await client.get(
                f"{OPENALEX_BASE_URL}/works/{openalex_id.split('/')[-1]}",
                params=params,
            )
            resp.raise_for_status()
    except (httpx.HTTPStatusError, httpx.RequestError) as exc:
        raise RuntimeError(f"Failed to fetch work from OpenAlex: {exc}") from exc

    work = resp.json()

    # Build topic-hierarchy filter from the primary topic
    primary_topic = work.get("primary_topic") or {}
    filter_parts: list[str] = []

    domain = primary_topic.get("domain", {})
    field = primary_topic.get("field", {})
    subfield = primary_topic.get("subfield", {})

    if domain.get("id"):
        filter_parts.append(f"topics.domain.id:{domain['id']}")
    if field.get("id"):
        filter_parts.append(f"topics.field.id:{field['id']}")
    if subfield.get("id"):
        filter_parts.append(f"topics.subfield.id:{subfield['id']}")

    # Fallback: if no primary_topic, try legacy concepts
    if not filter_parts:
        concepts = work.get("concepts") or []
        if concepts:
            filter_parts.append(f"concepts.id:{concepts[0].get('id', '')}")

    if not filter_parts:
        return []

    # Step 2: Search for related works within the same domain/field/subfield
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            search_params: dict[str, Any] = {
                "filter": ",".join(filter_parts),
                "per_page": per_page + 1,  # extra to allow excluding self
                "select": SELECT_FIELDS,
                "sort": "cited_by_count:desc",
            }
            if api_key:
                search_params["api_key"] = api_key
            resp = await client.get(
                f"{OPENALEX_BASE_URL}/works",
                params=search_params,
            )
            resp.raise_for_status()
    except (httpx.HTTPStatusError, httpx.RequestError) as exc:
        raise RuntimeError(f"Failed to search related works: {exc}") from exc

    data = resp.json()
    results: list[dict[str, Any]] = data.get("results", [])

    # Exclude the source paper and limit to per_page
    cleaned = [
        _clean_paper(r) for r in results
        if r.get("id") != openalex_id
    ]
    return cleaned[:per_page]
