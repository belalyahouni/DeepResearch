"""Tests for the search endpoint — mocks vector search, uses test DB for metadata."""

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

MOCK_AGENT_RESULT = {
    "category": "cs.CL",
    "field": "Computation and Language",
    "optimised_query": "Transformer attention mechanisms",
}

MOCK_VECTOR_HITS = [
    {"arxiv_id": "1706.03762", "distance": 0.08, "similarity_score": 0.92},
]


@patch("app.routers.search.search_by_query", return_value=MOCK_VECTOR_HITS)
@patch("app.routers.search.classify_and_optimise", new_callable=AsyncMock, return_value=MOCK_AGENT_RESULT)
async def test_search_full_pipeline(mock_agent, mock_search, client: AsyncClient, sample_papers):
    response = await client.get("/search?query=attention in transformers")
    assert response.status_code == 200
    data = response.json()

    assert data["original_query"] == "attention in transformers"
    assert data["field"] == "Computation and Language"
    assert data["optimised_query"] == "Transformer attention mechanisms"
    assert data["result_count"] == 1
    assert data["results"][0]["arxiv_id"] == "1706.03762"
    assert data["results"][0]["similarity_score"] == 0.92

    mock_agent.assert_called_once_with("attention in transformers")
    mock_search.assert_called_once_with("Transformer attention mechanisms")


async def test_search_empty_query_returns_422(client: AsyncClient):
    response = await client.get("/search?query=")
    assert response.status_code == 422


async def test_search_missing_query_returns_422(client: AsyncClient):
    response = await client.get("/search")
    assert response.status_code == 422


@patch("app.routers.search.search_by_query", side_effect=RuntimeError("ChromaDB down"))
@patch("app.routers.search.classify_and_optimise", new_callable=AsyncMock, return_value=MOCK_AGENT_RESULT)
async def test_search_vector_failure_returns_500(mock_agent, mock_search, client: AsyncClient):
    response = await client.get("/search?query=test")
    assert response.status_code == 500


@patch("app.routers.search.search_by_query", return_value=MOCK_VECTOR_HITS)
@patch(
    "app.routers.search.classify_and_optimise",
    new_callable=AsyncMock,
    return_value={"category": None, "field": None, "optimised_query": "fallback query", "error": "Gemini failed"},
)
async def test_search_gemini_fallback(mock_agent, mock_search, client: AsyncClient, sample_papers):
    response = await client.get("/search?query=test")
    assert response.status_code == 200
    data = response.json()
    assert data["field"] is None
    assert data["result_count"] == 1
