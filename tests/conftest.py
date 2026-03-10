"""Shared test fixtures — in-memory DB and async test client."""

import os
from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set test API key before importing app (so auth dependency picks it up)
os.environ["API_KEY"] = "test-api-key"

from app.database import Base, get_db
from app.main import app

# In-memory SQLite for tests — isolated from the real database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_session() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_db():
    """Create tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def _mock_pdf_parser():
    """Mock PDF parser globally so tests never make real HTTP requests for PDFs."""
    with patch("app.routers.papers.extract_text_from_pdf", return_value=None):
        yield


@pytest.fixture(autouse=True)
def _mock_summariser():
    """Mock summariser globally so tests never call Gemini."""
    with patch("app.routers.summary.summarise_text", return_value=None):
        yield


@pytest.fixture(autouse=True)
def _mock_chat_agent():
    """Mock chat agent globally so tests never call Gemini."""
    with patch("app.routers.conversation.chat", return_value=None):
        yield


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://localhost",
        headers={"X-API-Key": "test-api-key"},
    ) as ac:
        yield ac
