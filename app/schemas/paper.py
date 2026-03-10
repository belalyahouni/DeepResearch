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
                    "openalex_id": "https://openalex.org/W4415109130",
                    "title": "Mixture of Weight-shared Heterogeneous Group Attention Experts for Dynamic Token-wise KV Optimization",
                    "authors": "Guoqiang Song, D. Z. Liao, Yijiao Zhao, Kejiang Ye, Chunxiang Xu, Xiang Gao",
                    "abstract": "Transformer models face scalability challenges in causal language modeling (CLM) due to inefficient memory allocation for growing key-value (KV) caches...",
                    "year": 2025,
                    "url": "http://arxiv.org/abs/2506.13541",
                    "open_access_pdf_url": "https://arxiv.org/pdf/2506.13541",
                    "citation_count": 0,
                    "tags": "transformers, KV cache, MoE",
                    "notes": "Novel MoE approach to dynamic KV optimisation",
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
                    "openalex_id": "https://openalex.org/W4415109130",
                    "title": "Mixture of Weight-shared Heterogeneous Group Attention Experts for Dynamic Token-wise KV Optimization",
                    "authors": "Guoqiang Song, D. Z. Liao, Yijiao Zhao, Kejiang Ye, Chunxiang Xu, Xiang Gao",
                    "abstract": "Transformer models face scalability challenges in causal language modeling (CLM) due to inefficient memory allocation for growing key-value (KV) caches...",
                    "year": 2025,
                    "url": "http://arxiv.org/abs/2506.13541",
                    "open_access_pdf_url": "https://arxiv.org/pdf/2506.13541",
                    "citation_count": 0,
                    "tags": "transformers, KV cache, MoE",
                    "notes": "Novel MoE approach to dynamic KV optimisation",
                    "full_text": "Transformer models face scalability challenges in causal language modeling...",
                    "summary": "This paper proposes mixSGA, a mixture-of-expert approach that dynamically optimises token-wise computation and memory allocation for KV caches...",
                    "created_at": "2025-01-15T10:30:00",
                    "updated_at": "2025-01-15T10:30:00",
                }
            ]
        },
    }
