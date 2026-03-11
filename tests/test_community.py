"""Tests for community papers endpoints and interaction tracking."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_community_empty(client: AsyncClient) -> None:
    """GET /community returns empty list when no interactions have occurred."""
    response = await client.get("/community")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["papers"] == []


@pytest.mark.asyncio
async def test_community_populated_after_paper_lookup(client: AsyncClient, sample_papers) -> None:
    """Accessing a paper via GET /papers/{arxiv_id} adds it to the community index."""
    await client.get("/papers/1706.03762")

    response = await client.get("/community")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["papers"][0]["arxiv_id"] == "1706.03762"
    assert data["papers"][0]["interaction_count"] == 1


@pytest.mark.asyncio
async def test_community_interaction_count_increments(client: AsyncClient, sample_papers) -> None:
    """Multiple lookups of the same paper increment the interaction count."""
    for _ in range(3):
        await client.get("/papers/1706.03762")

    response = await client.get("/community")
    assert response.status_code == 200
    paper = response.json()["papers"][0]
    assert paper["interaction_count"] == 3


@pytest.mark.asyncio
async def test_community_ranked_by_interaction_count(client: AsyncClient, sample_papers) -> None:
    """Papers are returned in descending interaction count order."""
    await client.get("/papers/1706.03762")
    await client.get("/papers/1706.03762")
    await client.get("/papers/1810.04805")

    response = await client.get("/community")
    papers = response.json()["papers"]
    assert papers[0]["arxiv_id"] == "1706.03762"
    assert papers[1]["arxiv_id"] == "1810.04805"


@pytest.mark.asyncio
async def test_community_get_paper(client: AsyncClient, sample_papers) -> None:
    """GET /community/{arxiv_id} returns stats for a specific paper."""
    await client.get("/papers/1706.03762")
    await client.get("/papers/1706.03762")

    response = await client.get("/community/1706.03762")
    assert response.status_code == 200
    data = response.json()
    assert data["arxiv_id"] == "1706.03762"
    assert data["interaction_count"] == 2
    assert data["title"] == "Attention Is All You Need"


@pytest.mark.asyncio
async def test_community_get_paper_not_found(client: AsyncClient) -> None:
    """GET /community/{arxiv_id} returns 404 for a paper with no interactions."""
    response = await client.get("/community/unknown-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_community_limit_parameter(client: AsyncClient, sample_papers) -> None:
    """limit query parameter caps the number of results returned."""
    await client.get("/papers/1706.03762")
    await client.get("/papers/1810.04805")

    response = await client.get("/community?limit=1")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_community_requires_auth(client: AsyncClient) -> None:
    """Community endpoints require a valid API key."""
    response = await client.get("/community", headers={"X-API-Key": "wrong"})
    assert response.status_code == 401
