"""Tests for the search endpoint — mocks external APIs."""

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

MOCK_AGENT_RESULT = {
    "field_id": 17,
    "field": "Computer Science",
    "optimised_query": "Transformer attention mechanisms",
}

MOCK_PAPERS = [
    {
        "openalex_id": "https://openalex.org/W123",
        "doi": "https://doi.org/10.1234/test",
        "title": "Attention Is All You Need",
        "authors": "Vaswani et al.",
        "abstract": "We propose a new architecture...",
        "year": 2017,
        "url": "https://arxiv.org/abs/1706.03762",
        "open_access_pdf_url": "https://arxiv.org/pdf/1706.03762",
        "citation_count": 100000,
        "relevance_score": 1.5,
    },
]


@patch("app.routers.search.search_papers", new_callable=AsyncMock, return_value=MOCK_PAPERS)
@patch("app.routers.search.classify_and_optimise", new_callable=AsyncMock, return_value=MOCK_AGENT_RESULT)
async def test_search_full_pipeline(mock_agent, mock_search, client: AsyncClient):
    response = await client.get("/search?query=attention in transformers")
    assert response.status_code == 200
    data = response.json()

    assert data["original_query"] == "attention in transformers"
    assert data["field_id"] == 17
    assert data["field"] == "Computer Science"
    assert data["optimised_query"] == "Transformer attention mechanisms"
    assert data["result_count"] == 1
    assert data["results"][0]["title"] == "Attention Is All You Need"

    # Verify agent was called with original query
    mock_agent.assert_called_once_with("attention in transformers")
    # Verify search was called with optimised query and field
    mock_search.assert_called_once_with(
        "Transformer attention mechanisms", semantic=True, field_id=17
    )


async def test_search_empty_query_returns_422(client: AsyncClient):
    response = await client.get("/search?query=")
    assert response.status_code == 422


async def test_search_missing_query_returns_422(client: AsyncClient):
    response = await client.get("/search")
    assert response.status_code == 422


@patch("app.routers.search.search_papers", new_callable=AsyncMock, side_effect=RuntimeError("API down"))
@patch("app.routers.search.classify_and_optimise", new_callable=AsyncMock, return_value=MOCK_AGENT_RESULT)
async def test_search_openalex_failure_returns_500(mock_agent, mock_search, client: AsyncClient):
    response = await client.get("/search?query=test")
    assert response.status_code == 500
    assert "API down" in response.json()["detail"]


@patch("app.routers.search.search_papers", new_callable=AsyncMock, return_value=MOCK_PAPERS)
@patch(
    "app.routers.search.classify_and_optimise",
    new_callable=AsyncMock,
    return_value={"field_id": None, "field": None, "optimised_query": "fallback query", "error": "Gemini failed"},
)
async def test_search_gemini_fallback(mock_agent, mock_search, client: AsyncClient):
    """When Gemini fails, search should still work with original-ish query and no field filter."""
    response = await client.get("/search?query=test")
    assert response.status_code == 200
    data = response.json()
    assert data["field_id"] is None
    assert data["result_count"] == 1
