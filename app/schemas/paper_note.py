"""Pydantic schemas for the paper notes endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    """Request body for creating a note."""

    content: str = Field(..., min_length=1, max_length=2000, description="Note text (max 2000 characters)")

    model_config = {
        "json_schema_extra": {
            "examples": [{"content": "Key contribution: introduces multi-head attention as a drop-in replacement for RNNs."}]
        }
    }


class NoteUpdate(BaseModel):
    """Request body for updating a note."""

    content: str = Field(..., min_length=1, max_length=2000, description="Updated note text (max 2000 characters)")

    model_config = {
        "json_schema_extra": {
            "examples": [{"content": "Updated: also introduces positional encoding to preserve sequence order."}]
        }
    }


class NoteResponse(BaseModel):
    """A single note on a paper."""

    id: int = Field(..., description="Note ID")
    arxiv_id: str = Field(..., description="arXiv paper ID this note belongs to")
    content: str = Field(..., description="Note text")
    created_at: datetime = Field(..., description="When the note was created")
    updated_at: datetime = Field(..., description="When the note was last updated")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "arxiv_id": "1706.03762",
                    "content": "Key contribution: introduces multi-head attention as a drop-in replacement for RNNs.",
                    "created_at": "2025-03-10T10:00:00Z",
                    "updated_at": "2025-03-10T10:00:00Z",
                }
            ]
        },
    }
