"""Chat endpoints — multi-turn conversation per paper."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.chat import MAX_MESSAGES, chat
from app.auth import get_api_key
from app.database import get_db
from app.models.conversation import Conversation
from app.models.paper import Paper
from app.schemas.conversation import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
)

router = APIRouter(prefix="/papers/{paper_id}/chat", tags=["Chat"], dependencies=[Depends(get_api_key)])


async def _get_paper_or_404(paper_id: int, db: AsyncSession) -> Paper:
    """Fetch a paper by ID or raise 404."""
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@router.post("", response_model=ChatResponse, status_code=201)
async def send_message(
    paper_id: int,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Send a message and get an AI response about the paper."""
    paper = await _get_paper_or_404(paper_id, db)

    # Check message limit
    count_result = await db.execute(
        select(func.count()).select_from(Conversation).where(
            Conversation.paper_id == paper_id
        )
    )
    message_count = count_result.scalar()
    if message_count >= MAX_MESSAGES:
        raise HTTPException(
            status_code=409,
            detail=f"Conversation limit reached ({MAX_MESSAGES} messages). Clear the chat to continue.",
        )

    # Load conversation history
    history_result = await db.execute(
        select(Conversation)
        .where(Conversation.paper_id == paper_id)
        .order_by(Conversation.created_at)
    )
    history = [
        {"role": msg.role, "message": msg.message}
        for msg in history_result.scalars().all()
    ]

    # Save user message to DB first (preserved even if Gemini fails)
    user_msg = Conversation(paper_id=paper_id, role="user", message=body.message)
    db.add(user_msg)
    await db.flush()

    # Get paper text for context
    paper_text = paper.full_text or paper.abstract or paper.title

    # Call chat agent
    response_text = await chat(paper_text, history, body.message)
    if response_text is None:
        await db.commit()  # commit user message even on failure
        raise HTTPException(
            status_code=500,
            detail="Chat failed — Gemini unavailable or returned an error",
        )

    # Save assistant response to DB
    assistant_msg = Conversation(paper_id=paper_id, role="assistant", message=response_text)
    db.add(assistant_msg)
    await db.commit()

    return {"role": "assistant", "message": response_text}


@router.get("", response_model=ConversationResponse)
async def get_conversation(
    paper_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the full conversation history for a paper."""
    await _get_paper_or_404(paper_id, db)

    result = await db.execute(
        select(Conversation)
        .where(Conversation.paper_id == paper_id)
        .order_by(Conversation.created_at)
    )
    messages = list(result.scalars().all())
    return {"paper_id": paper_id, "messages": messages}


@router.delete("", status_code=204)
async def clear_conversation(
    paper_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Clear all conversation messages for a paper."""
    await _get_paper_or_404(paper_id, db)

    await db.execute(
        delete(Conversation).where(Conversation.paper_id == paper_id)
    )
    await db.commit()
