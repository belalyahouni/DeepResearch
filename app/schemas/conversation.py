"""Pydantic schemas for the chat conversation endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for sending a chat message."""
    message: str = Field(..., min_length=1, description="User message")


class ChatMessageResponse(BaseModel):
    """A single message in the conversation."""
    role: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    """Response after sending a chat message."""
    role: str
    message: str


class ConversationResponse(BaseModel):
    """Full conversation history for a paper."""
    paper_id: int
    messages: list[ChatMessageResponse]
