"""Tests for paper notes endpoints — full CRUD."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_note(client: AsyncClient, sample_papers) -> None:
    """POST /papers/{arxiv_id}/notes creates a note and returns 201."""
    response = await client.post(
        "/papers/1706.03762/notes",
        json={"content": "Introduces multi-head attention."},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["arxiv_id"] == "1706.03762"
    assert data["content"] == "Introduces multi-head attention."
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_note_paper_not_found(client: AsyncClient) -> None:
    """POST /papers/{arxiv_id}/notes returns 404 for unknown paper."""
    response = await client.post(
        "/papers/unknown-id/notes",
        json={"content": "Some note."},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_note_empty_content(client: AsyncClient, sample_papers) -> None:
    """POST /papers/{arxiv_id}/notes returns 422 for empty content."""
    response = await client.post(
        "/papers/1706.03762/notes",
        json={"content": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_notes(client: AsyncClient, sample_papers) -> None:
    """GET /papers/{arxiv_id}/notes returns all notes for a paper."""
    await client.post("/papers/1706.03762/notes", json={"content": "Note one."})
    await client.post("/papers/1706.03762/notes", json={"content": "Note two."})

    response = await client.get("/papers/1706.03762/notes")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 2
    contents = {n["content"] for n in notes}
    assert contents == {"Note one.", "Note two."}


@pytest.mark.asyncio
async def test_list_notes_empty(client: AsyncClient, sample_papers) -> None:
    """GET /papers/{arxiv_id}/notes returns empty list when no notes exist."""
    response = await client.get("/papers/1706.03762/notes")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_notes_paper_not_found(client: AsyncClient) -> None:
    """GET /papers/{arxiv_id}/notes returns 404 for unknown paper."""
    response = await client.get("/papers/unknown-id/notes")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_note(client: AsyncClient, sample_papers) -> None:
    """PATCH /notes/{id} updates note content and returns the updated note."""
    create = await client.post(
        "/papers/1706.03762/notes",
        json={"content": "Original content."},
    )
    note_id = create.json()["id"]

    response = await client.patch(f"/notes/{note_id}", json={"content": "Updated content."})
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Updated content."
    assert data["id"] == note_id


@pytest.mark.asyncio
async def test_update_note_not_found(client: AsyncClient) -> None:
    """PATCH /notes/{id} returns 404 for unknown note."""
    response = await client.patch("/notes/99999", json={"content": "Updated."})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_note(client: AsyncClient, sample_papers) -> None:
    """DELETE /notes/{id} removes the note and returns 204."""
    create = await client.post(
        "/papers/1706.03762/notes",
        json={"content": "To be deleted."},
    )
    note_id = create.json()["id"]

    response = await client.delete(f"/notes/{note_id}")
    assert response.status_code == 204

    # Verify it's gone
    notes = await client.get("/papers/1706.03762/notes")
    assert notes.json() == []


@pytest.mark.asyncio
async def test_delete_note_not_found(client: AsyncClient) -> None:
    """DELETE /notes/{id} returns 404 for unknown note."""
    response = await client.delete("/notes/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_notes_require_auth(client: AsyncClient, sample_papers) -> None:
    """Notes endpoints require a valid API key."""
    response = await client.post(
        "/papers/1706.03762/notes",
        json={"content": "Unauthorised."},
        headers={"X-API-Key": "wrong"},
    )
    assert response.status_code == 401
