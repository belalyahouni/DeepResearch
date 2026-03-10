"""Tests for the summariser agent and /summarise endpoint."""

from unittest.mock import patch

from httpx import AsyncClient

SAMPLE_TEXT = (
    "The dominant sequence transduction models are based on complex recurrent or "
    "convolutional neural networks that include an encoder and a decoder."
)


# --- POST /summarise ---

async def test_summarise_valid(client: AsyncClient):
    """POST /summarise with valid text returns a summary."""
    with patch(
        "app.routers.summary.summarise_text",
        return_value="## Key Findings\n- Transformers work well",
    ):
        response = await client.post("/summarise", json={"text": SAMPLE_TEXT})
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "Key Findings" in data["summary"]


async def test_summarise_empty_text_returns_422(client: AsyncClient):
    """POST /summarise with empty text returns 422."""
    response = await client.post("/summarise", json={"text": ""})
    assert response.status_code == 422


async def test_summarise_missing_text_returns_422(client: AsyncClient):
    """POST /summarise with no text field returns 422."""
    response = await client.post("/summarise", json={})
    assert response.status_code == 422


async def test_summarise_gemini_fails_returns_500(client: AsyncClient):
    """POST /summarise returns 500 when Gemini fails."""
    with patch("app.routers.summary.summarise_text", return_value=None):
        response = await client.post("/summarise", json={"text": SAMPLE_TEXT})
    assert response.status_code == 500


# --- Summary generation on paper save (via /summarise internally) ---

SAMPLE_PAPER = {
    "openalex_id": "https://openalex.org/W2963403868",
    "title": "Attention Is All You Need",
    "authors": "Ashish Vaswani, Noam Shazeer",
    "abstract": "The dominant sequence transduction models...",
    "year": 2017,
    "url": "https://arxiv.org/abs/1706.03762",
    "open_access_pdf_url": "https://arxiv.org/pdf/1706.03762",
    "citation_count": 100000,
}


async def test_create_paper_generates_summary(client: AsyncClient):
    """Paper saved via POST /papers gets an auto-generated summary via /summarise."""
    with patch(
        "app.routers.summary.summarise_text",
        return_value="## Key Findings\n- Great paper",
    ):
        response = await client.post("/papers", json=SAMPLE_PAPER)
    assert response.status_code == 201
    data = response.json()
    assert data["summary"] == "## Key Findings\n- Great paper"


async def test_create_paper_summary_fails_gracefully(client: AsyncClient):
    """Paper is still saved when summariser fails."""
    with patch("app.routers.summary.summarise_text", return_value=None):
        response = await client.post("/papers", json=SAMPLE_PAPER)
    assert response.status_code == 201
    data = response.json()
    assert data["summary"] is None
