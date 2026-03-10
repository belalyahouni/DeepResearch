"""Tests for the chat conversation endpoints."""

from unittest.mock import patch

from httpx import AsyncClient

SAMPLE_PAPER = {
    "openalex_id": "https://openalex.org/W2963403868",
    "title": "Attention Is All You Need",
    "authors": "Ashish Vaswani, Noam Shazeer",
    "abstract": "The dominant sequence transduction models...",
    "year": 2017,
    "url": "https://arxiv.org/abs/1706.03762",
    "citation_count": 100000,
}


async def _create_paper(client: AsyncClient) -> int:
    """Helper — create a paper and return its ID."""
    response = await client.post("/papers", json=SAMPLE_PAPER)
    return response.json()["id"]


# --- POST /papers/{id}/chat ---

async def test_send_message(client: AsyncClient):
    """Send a message and get an AI response."""
    paper_id = await _create_paper(client)
    with patch("app.routers.conversation.chat", return_value="The paper proposes the Transformer."):
        response = await client.post(
            f"/papers/{paper_id}/chat",
            json={"message": "What is this paper about?"},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "assistant"
    assert "Transformer" in data["message"]


async def test_send_message_paper_not_found(client: AsyncClient):
    """POST chat on non-existent paper returns 404."""
    response = await client.post(
        "/papers/999/chat",
        json={"message": "Hello"},
    )
    assert response.status_code == 404


async def test_send_message_empty_returns_422(client: AsyncClient):
    """POST chat with empty message returns 422."""
    paper_id = await _create_paper(client)
    response = await client.post(
        f"/papers/{paper_id}/chat",
        json={"message": ""},
    )
    assert response.status_code == 422


async def test_send_message_gemini_fails_returns_500(client: AsyncClient):
    """POST chat returns 500 when Gemini fails, but user message is saved."""
    paper_id = await _create_paper(client)
    with patch("app.routers.conversation.chat", return_value=None):
        response = await client.post(
            f"/papers/{paper_id}/chat",
            json={"message": "What is this about?"},
        )
    assert response.status_code == 500

    # User message should still be saved in history
    history = await client.get(f"/papers/{paper_id}/chat")
    messages = history.json()["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["message"] == "What is this about?"


async def test_multi_turn_conversation(client: AsyncClient):
    """Conversation history builds up across multiple exchanges."""
    paper_id = await _create_paper(client)
    with patch("app.routers.conversation.chat", return_value="It uses self-attention."):
        await client.post(
            f"/papers/{paper_id}/chat",
            json={"message": "What is the key mechanism?"},
        )
    with patch("app.routers.conversation.chat", return_value="It replaced recurrence entirely."):
        await client.post(
            f"/papers/{paper_id}/chat",
            json={"message": "How does it differ from RNNs?"},
        )

    history = await client.get(f"/papers/{paper_id}/chat")
    messages = history.json()["messages"]
    assert len(messages) == 4  # 2 user + 2 assistant
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "user"
    assert messages[3]["role"] == "assistant"


# --- GET /papers/{id}/chat ---

async def test_get_conversation_empty(client: AsyncClient):
    """GET chat on a paper with no messages returns empty list."""
    paper_id = await _create_paper(client)
    response = await client.get(f"/papers/{paper_id}/chat")
    assert response.status_code == 200
    data = response.json()
    assert data["paper_id"] == paper_id
    assert data["messages"] == []


async def test_get_conversation_paper_not_found(client: AsyncClient):
    """GET chat on non-existent paper returns 404."""
    response = await client.get("/papers/999/chat")
    assert response.status_code == 404


# --- DELETE /papers/{id}/chat ---

async def test_clear_conversation(client: AsyncClient):
    """DELETE clears all messages for a paper."""
    paper_id = await _create_paper(client)
    with patch("app.routers.conversation.chat", return_value="Response."):
        await client.post(
            f"/papers/{paper_id}/chat",
            json={"message": "Hello"},
        )

    response = await client.delete(f"/papers/{paper_id}/chat")
    assert response.status_code == 204

    # Confirm empty
    history = await client.get(f"/papers/{paper_id}/chat")
    assert history.json()["messages"] == []


async def test_clear_conversation_paper_not_found(client: AsyncClient):
    """DELETE chat on non-existent paper returns 404."""
    response = await client.delete("/papers/999/chat")
    assert response.status_code == 404


# --- Message limit ---

async def test_message_limit_enforced(client: AsyncClient):
    """Exceeding the message limit returns 409."""
    paper_id = await _create_paper(client)

    # Fill up to the limit (20 messages = 10 exchanges)
    for i in range(10):
        with patch("app.routers.conversation.chat", return_value=f"Response {i}"):
            await client.post(
                f"/papers/{paper_id}/chat",
                json={"message": f"Question {i}"},
            )

    # Next message should be rejected
    response = await client.post(
        f"/papers/{paper_id}/chat",
        json={"message": "One too many"},
    )
    assert response.status_code == 409
