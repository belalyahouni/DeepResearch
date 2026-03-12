"""Tests for community papers endpoints and interaction tracking."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.models.community_interaction import CommunityInteraction
from app.models.community_paper import CommunityPaper
from tests.conftest import test_session


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


@pytest.mark.asyncio
async def test_community_period_week(client: AsyncClient, sample_papers) -> None:
    """period=week only counts interactions from the last 7 days."""
    await client.get("/papers/1706.03762")

    response = await client.get("/community?period=week")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["papers"][0]["arxiv_id"] == "1706.03762"
    assert data["papers"][0]["interaction_count"] == 1


@pytest.mark.asyncio
async def test_community_period_excludes_old_interactions(client: AsyncClient, sample_papers) -> None:
    """Interactions older than the period window are excluded from period rankings."""
    old_timestamp = datetime.now(timezone.utc) - timedelta(days=60)

    async with test_session() as session:
        # Paper A has 5 interactions but all 60 days ago (outside month window)
        session.add(CommunityPaper(arxiv_id="1706.03762", interaction_count=5, last_interacted_at=old_timestamp))
        for _ in range(5):
            session.add(CommunityInteraction(arxiv_id="1706.03762", interacted_at=old_timestamp))
        # Paper B has 1 recent interaction
        session.add(CommunityPaper(arxiv_id="1810.04805", interaction_count=1, last_interacted_at=datetime.now(timezone.utc)))
        session.add(CommunityInteraction(arxiv_id="1810.04805"))
        await session.commit()

    response = await client.get("/community?period=month")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["papers"][0]["arxiv_id"] == "1810.04805"


@pytest.mark.asyncio
async def test_community_period_ranking(client: AsyncClient, sample_papers) -> None:
    """period ranking reflects interaction count within the window, not all-time."""
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=400)  # outside year window

    async with test_session() as session:
        # Paper A: 10 all-time but 9 are over a year old, 1 recent
        session.add(CommunityPaper(arxiv_id="1706.03762", interaction_count=10, last_interacted_at=now))
        for _ in range(9):
            session.add(CommunityInteraction(arxiv_id="1706.03762", interacted_at=old))
        session.add(CommunityInteraction(arxiv_id="1706.03762", interacted_at=now))
        # Paper B: 3 all-time, all recent
        session.add(CommunityPaper(arxiv_id="1810.04805", interaction_count=3, last_interacted_at=now))
        for _ in range(3):
            session.add(CommunityInteraction(arxiv_id="1810.04805", interacted_at=now))
        await session.commit()

    # All-time: paper A wins (10 vs 3)
    alltime = await client.get("/community")
    assert alltime.json()["papers"][0]["arxiv_id"] == "1706.03762"

    # Year window: paper B wins (3 vs 1)
    year = await client.get("/community?period=year")
    assert year.json()["papers"][0]["arxiv_id"] == "1810.04805"


@pytest.mark.asyncio
async def test_community_period_empty(client: AsyncClient) -> None:
    """period filter returns empty list when no interactions fall within the window."""
    response = await client.get("/community?period=week")
    assert response.status_code == 200
    assert response.json()["total"] == 0
