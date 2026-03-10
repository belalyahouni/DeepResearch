"""Pydantic schemas for Paper CRUD operations."""

from datetime import datetime

from pydantic import BaseModel, Field


class PaperCreate(BaseModel):
    """Schema for saving a paper to the library."""
    openalex_id: str = Field(..., description="OpenAlex work ID")
    title: str
    authors: str = Field(..., description="Comma-separated author names")
    abstract: str | None = None
    year: int | None = None
    url: str | None = None
    open_access_pdf_url: str | None = None
    citation_count: int = 0
    tags: str | None = Field(None, description="Comma-separated tags")
    notes: str | None = None


class PaperUpdate(BaseModel):
    """Schema for updating a saved paper (tags and notes only)."""
    tags: str | None = None
    notes: str | None = None


class PaperResponse(BaseModel):
    """Schema for returning a saved paper."""
    id: int
    openalex_id: str
    title: str
    authors: str
    abstract: str | None
    year: int | None
    url: str | None
    open_access_pdf_url: str | None
    citation_count: int
    tags: str | None
    notes: str | None
    full_text: str | None
    summary: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
