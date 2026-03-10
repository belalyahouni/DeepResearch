"""Pydantic schemas for the chat conversation endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for sending a chat message."""
    message: str = Field(..., min_length=1, description="User message to send to the chat agent")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "What is the main contribution of this paper?"
                }
            ]
        }
    }


class ChatMessageResponse(BaseModel):
    """A single message in the conversation."""
    role: str = Field(..., description="Message author: 'user' or 'assistant'")
    message: str = Field(..., description="Message content")
    created_at: datetime = Field(..., description="When the message was sent")

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    """Response after sending a chat message."""
    role: str = Field(..., description="Always 'assistant' for chat responses")
    message: str = Field(..., description="AI-generated response about the paper")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "role": "assistant",
                    "message": "The main contribution of this paper is the Transformer architecture, which replaces recurrence with self-attention for sequence modelling.",
                }
            ]
        }
    }


class ConversationResponse(BaseModel):
    """Full conversation history for a paper."""
    paper_id: int = Field(..., description="ID of the paper this conversation belongs to")
    messages: list[ChatMessageResponse] = Field(..., description="Ordered list of messages in the conversation")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "paper_id": 1,
                    "messages": [
                        {
                            "role": "user",
                            "message": "What is the main contribution?",
                            "created_at": "2025-01-15T10:30:00",
                        },
                        {
                            "role": "assistant",
                            "message": "The main contribution is the Transformer architecture.",
                            "created_at": "2025-01-15T10:30:01",
                        },
                    ],
                }
            ]
        }
    }
