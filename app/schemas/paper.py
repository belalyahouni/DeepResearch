"""Pydantic schemas for Paper CRUD operations."""

from datetime import datetime

from pydantic import BaseModel, Field


class PaperCreate(BaseModel):
    """Schema for saving a paper to the library."""
    openalex_id: str = Field(..., description="OpenAlex work ID (e.g. https://openalex.org/W2963403868)")
    title: str = Field(..., description="Paper title")
    authors: str = Field(..., description="Comma-separated author names")
    abstract: str | None = Field(None, description="Paper abstract text")
    year: int | None = Field(None, description="Publication year")
    url: str | None = Field(None, description="Landing page URL")
    open_access_pdf_url: str | None = Field(None, description="Direct URL to the open-access PDF")
    citation_count: int = Field(0, description="Number of citations")
    tags: str | None = Field(None, description="Comma-separated tags for organisation")
    notes: str | None = Field(None, description="Personal notes about the paper")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "openalex_id": "https://openalex.org/W2963403868",
                    "title": "Attention Is All You Need",
                    "authors": "Ashish Vaswani, Noam Shazeer, Niki Parmar",
                    "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
                    "year": 2017,
                    "url": "https://arxiv.org/abs/1706.03762",
                    "open_access_pdf_url": "https://arxiv.org/pdf/1706.03762",
                    "citation_count": 100000,
                    "tags": "transformers, attention, NLP",
                    "notes": "Foundational transformer paper",
                }
            ]
        }
    }


class PaperUpdate(BaseModel):
    """Schema for updating a saved paper (tags and notes only)."""
    tags: str | None = Field(None, description="New comma-separated tags (replaces existing)")
    notes: str | None = Field(None, description="Updated personal notes")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tags": "deep learning, transformers",
                    "notes": "Foundational paper — introduced the transformer architecture",
                }
            ]
        }
    }


class PaperResponse(BaseModel):
    """Schema for returning a saved paper."""
    id: int = Field(..., description="Internal database ID")
    openalex_id: str = Field(..., description="OpenAlex work ID")
    title: str = Field(..., description="Paper title")
    authors: str = Field(..., description="Comma-separated author names")
    abstract: str | None = Field(None, description="Paper abstract text")
    year: int | None = Field(None, description="Publication year")
    url: str | None = Field(None, description="Landing page URL")
    open_access_pdf_url: str | None = Field(None, description="Direct URL to the open-access PDF")
    citation_count: int = Field(..., description="Number of citations")
    tags: str | None = Field(None, description="Comma-separated tags")
    notes: str | None = Field(None, description="Personal notes")
    full_text: str | None = Field(None, description="Extracted full text from the PDF (if available)")
    summary: str | None = Field(None, description="AI-generated summary of the paper")
    created_at: datetime = Field(..., description="When the paper was saved")
    updated_at: datetime = Field(..., description="When the paper was last modified")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "openalex_id": "https://openalex.org/W2963403868",
                    "title": "Attention Is All You Need",
                    "authors": "Ashish Vaswani, Noam Shazeer, Niki Parmar",
                    "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
                    "year": 2017,
                    "url": "https://arxiv.org/abs/1706.03762",
                    "open_access_pdf_url": "https://arxiv.org/pdf/1706.03762",
                    "citation_count": 100000,
                    "tags": "transformers, attention",
                    "notes": "Foundational paper",
                    "full_text": "We propose a new simple network architecture, the Transformer...",
                    "summary": "This paper introduces the Transformer architecture...",
                    "created_at": "2025-01-15T10:30:00",
                    "updated_at": "2025-01-15T10:30:00",
                }
            ]
        },
    }
