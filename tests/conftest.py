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
def _mock_summariser():
    """Mock summariser globally so tests never call Gemini."""
    with patch("app.routers.summary.summarise_text", return_value=None):
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


@pytest.fixture
async def sample_papers():
    """Insert sample arXiv papers into the test database."""
    from app.models.arxiv_paper import ArxivPaper

    papers_data = [
        ArxivPaper(
            arxiv_id="1706.03762",
            title="Attention Is All You Need",
            authors="Ashish Vaswani, Noam Shazeer",
            abstract="The dominant sequence transduction models...",
            categories="cs.CL cs.LG",
            year=2017,
            doi=None,
            url="https://arxiv.org/abs/1706.03762",
        ),
        ArxivPaper(
            arxiv_id="1810.04805",
            title="BERT: Pre-training of Deep Bidirectional Transformers",
            authors="Jacob Devlin, Ming-Wei Chang",
            abstract="We introduce a new language representation model...",
            categories="cs.CL",
            year=2018,
            doi=None,
            url="https://arxiv.org/abs/1810.04805",
        ),
    ]
    async with test_session() as session:
        session.add_all(papers_data)
        await session.commit()
    return papers_data
