"""Tests for the papers CRUD endpoints."""

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

SAMPLE_PAPER = {
    "openalex_id": "https://openalex.org/W4415109130",
    "title": "Mixture of Weight-shared Heterogeneous Group Attention Experts for Dynamic Token-wise KV Optimization",
    "authors": "Guoqiang Song, D. Z. Liao, Yijiao Zhao, Kejiang Ye, Chunxiang Xu, Xiang Gao",
    "abstract": "Transformer models face scalability challenges in causal language modeling (CLM) due to inefficient memory allocation for growing key-value (KV) caches...",
    "year": 2025,
    "url": "http://arxiv.org/abs/2506.13541",
    "open_access_pdf_url": "https://arxiv.org/pdf/2506.13541",
    "citation_count": 0,
}


# --- CREATE ---

async def test_create_paper(client: AsyncClient):
    response = await client.post("/papers", json=SAMPLE_PAPER)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == SAMPLE_PAPER["title"]
    assert data["openalex_id"] == SAMPLE_PAPER["openalex_id"]
    assert data["id"] is not None
    assert data["tags"] is None
    assert data["notes"] is None


async def test_create_duplicate_paper_returns_409(client: AsyncClient):
    await client.post("/papers", json=SAMPLE_PAPER)
    response = await client.post("/papers", json=SAMPLE_PAPER)
    assert response.status_code == 409


async def test_create_paper_missing_fields_returns_422(client: AsyncClient):
    response = await client.post("/papers", json={"title": "Incomplete"})
    assert response.status_code == 422


# --- READ ---

async def test_list_papers_empty(client: AsyncClient):
    response = await client.get("/papers")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_papers(client: AsyncClient):
    await client.post("/papers", json=SAMPLE_PAPER)
    response = await client.get("/papers")
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_get_paper_by_id(client: AsyncClient):
    create = await client.post("/papers", json=SAMPLE_PAPER)
    paper_id = create.json()["id"]
    response = await client.get(f"/papers/{paper_id}")
    assert response.status_code == 200
    assert response.json()["title"] == SAMPLE_PAPER["title"]


async def test_get_paper_not_found(client: AsyncClient):
    response = await client.get("/papers/999")
    assert response.status_code == 404


# --- FILTER ---

async def test_filter_papers_by_tag(client: AsyncClient):
    await client.post("/papers", json={**SAMPLE_PAPER, "tags": "transformers, attention"})
    second = {**SAMPLE_PAPER, "openalex_id": "https://openalex.org/W000", "title": "Other"}
    await client.post("/papers", json={**second, "tags": "biology"})

    response = await client.get("/papers?tags=transformers")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["title"] == SAMPLE_PAPER["title"]


async def test_filter_papers_no_match(client: AsyncClient):
    await client.post("/papers", json=SAMPLE_PAPER)
    response = await client.get("/papers?tags=nonexistent")
    assert response.status_code == 200
    assert response.json() == []


# --- UPDATE ---

async def test_update_paper(client: AsyncClient):
    create = await client.post("/papers", json=SAMPLE_PAPER)
    paper_id = create.json()["id"]

    response = await client.put(
        f"/papers/{paper_id}",
        json={"tags": "deep learning", "notes": "Foundational paper"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tags"] == "deep learning"
    assert data["notes"] == "Foundational paper"
    # Other fields unchanged
    assert data["title"] == SAMPLE_PAPER["title"]


async def test_update_paper_not_found(client: AsyncClient):
    response = await client.put("/papers/999", json={"tags": "test"})
    assert response.status_code == 404


# --- DELETE ---

async def test_delete_paper(client: AsyncClient):
    create = await client.post("/papers", json=SAMPLE_PAPER)
    paper_id = create.json()["id"]

    response = await client.delete(f"/papers/{paper_id}")
    assert response.status_code == 204

    # Confirm gone
    response = await client.get(f"/papers/{paper_id}")
    assert response.status_code == 404


async def test_delete_paper_not_found(client: AsyncClient):
    response = await client.delete("/papers/999")
    assert response.status_code == 404


# --- PDF EXTRACTION ON SAVE ---

async def test_create_paper_extracts_pdf_text(client: AsyncClient):
    """When a paper is saved with a PDF URL, full text is extracted and stored."""
    with patch(
        "app.routers.papers.extract_text_from_pdf",
        return_value="Extracted full text of the paper.",
    ):
        response = await client.post("/papers", json=SAMPLE_PAPER)
    assert response.status_code == 201
    data = response.json()
    assert data["full_text"] == "Extracted full text of the paper."


async def test_create_paper_pdf_extraction_fails_gracefully(client: AsyncClient):
    """Paper is still saved when PDF extraction fails."""
    with patch(
        "app.routers.papers.extract_text_from_pdf",
        return_value=None,
    ):
        response = await client.post("/papers", json=SAMPLE_PAPER)
    assert response.status_code == 201
    data = response.json()
    assert data["full_text"] is None


# --- RELATED PAPERS ---

MOCK_RELATED_RESULTS = [
    {
        "openalex_id": "https://openalex.org/W000001",
        "doi": None,
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "authors": "Jacob Devlin",
        "abstract": "We introduce BERT...",
        "year": 2019,
        "url": None,
        "open_access_pdf_url": None,
        "citation_count": 80000,
        "relevance_score": None,
    },
]


async def test_related_papers(client: AsyncClient):
    """Happy path: returns related papers from OpenAlex."""
    create = await client.post("/papers", json=SAMPLE_PAPER)
    paper_id = create.json()["id"]

    with patch(
        "app.routers.papers.get_related_papers",
        new_callable=AsyncMock,
        return_value=MOCK_RELATED_RESULTS,
    ):
        response = await client.get(f"/papers/{paper_id}/related")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "BERT: Pre-training of Deep Bidirectional Transformers"


async def test_related_papers_not_found(client: AsyncClient):
    """Returns 404 when the paper does not exist."""
    response = await client.get("/papers/999/related")
    assert response.status_code == 404


async def test_related_papers_openalex_failure(client: AsyncClient):
    """Returns 500 when OpenAlex fails."""
    create = await client.post("/papers", json=SAMPLE_PAPER)
    paper_id = create.json()["id"]

    with patch(
        "app.routers.papers.get_related_papers",
        new_callable=AsyncMock,
        side_effect=RuntimeError("OpenAlex API down"),
    ):
        response = await client.get(f"/papers/{paper_id}/related")
    assert response.status_code == 500
