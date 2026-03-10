"""Tests for the papers CRUD endpoints."""

from unittest.mock import patch

from httpx import AsyncClient

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


# --- CREATE ---

async def test_create_paper(client: AsyncClient):
    response = await client.post("/papers", json=SAMPLE_PAPER)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Attention Is All You Need"
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
    assert response.json()["title"] == "Attention Is All You Need"


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
    assert results[0]["title"] == "Attention Is All You Need"


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
    assert data["title"] == "Attention Is All You Need"


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
