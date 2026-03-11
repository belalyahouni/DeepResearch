"""Tests for arXiv corpus lookup endpoints."""

from unittest.mock import patch

from httpx import AsyncClient


# --- GET /papers/{arxiv_id} ---

async def test_get_paper_from_corpus(client: AsyncClient, sample_papers):
    response = await client.get("/papers/1706.03762")
    assert response.status_code == 200
    data = response.json()
    assert data["arxiv_id"] == "1706.03762"
    assert data["title"] == "Attention Is All You Need"
    assert data["similarity_score"] is None


async def test_get_paper_not_found(client: AsyncClient):
    response = await client.get("/papers/9999.99999")
    assert response.status_code == 404


# --- GET /papers/{arxiv_id}/related ---

MOCK_RELATED_HITS = [
    {"arxiv_id": "1810.04805", "distance": 0.15, "similarity_score": 0.85},
]


@patch("app.routers.papers.find_related", return_value=MOCK_RELATED_HITS)
async def test_related_papers(mock_find, client: AsyncClient, sample_papers):
    response = await client.get("/papers/1706.03762/related")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["arxiv_id"] == "1810.04805"
    assert data[0]["similarity_score"] == 0.85
    mock_find.assert_called_once_with("1706.03762", n_results=5)


async def test_related_papers_not_found(client: AsyncClient):
    response = await client.get("/papers/9999.99999/related")
    assert response.status_code == 404


@patch("app.routers.papers.find_related", side_effect=ValueError("Not in vector store"))
async def test_related_papers_not_in_vector_store(mock_find, client: AsyncClient, sample_papers):
    response = await client.get("/papers/1706.03762/related")
    assert response.status_code == 404


@patch("app.routers.papers.find_related", side_effect=RuntimeError("ChromaDB error"))
async def test_related_papers_vector_failure(mock_find, client: AsyncClient, sample_papers):
    response = await client.get("/papers/1706.03762/related")
    assert response.status_code == 500
