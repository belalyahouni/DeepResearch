"""Tests for API key authentication."""

from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_missing_api_key_returns_401():
    """Request without X-API-Key header returns 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        response = await ac.get("/search?query=test")
    assert response.status_code == 401
    assert "Missing API key" in response.json()["detail"]


async def test_invalid_api_key_returns_401():
    """Request with wrong X-API-Key returns 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://localhost",
        headers={"X-API-Key": "wrong-key"},
    ) as ac:
        response = await ac.get("/search?query=test")
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]


async def test_health_does_not_require_api_key():
    """GET /health works without an API key."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
