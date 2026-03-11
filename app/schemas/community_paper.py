"""Pydantic schemas for the community papers endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class CommunityPaperResponse(BaseModel):
    """A paper entry in the community activity index."""

    arxiv_id: str = Field(..., description="arXiv paper ID")
    interaction_count: int = Field(..., description="Total number of times this paper has been accessed or summarised")
    last_interacted_at: datetime = Field(..., description="Timestamp of the most recent interaction")
    title: str = Field(..., description="Paper title")
    authors: str = Field(..., description="Comma-separated author names")
    categories: str = Field(..., description="Space-separated arXiv categories")
    year: int | None = Field(None, description="Publication year")
    url: str = Field(..., description="arXiv URL")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "arxiv_id": "1706.03762",
                    "interaction_count": 14,
                    "last_interacted_at": "2025-03-10T11:42:00Z",
                    "title": "Attention Is All You Need",
                    "authors": "Ashish Vaswani, Noam Shazeer",
                    "categories": "cs.CL cs.LG",
                    "year": 2017,
                    "url": "https://arxiv.org/abs/1706.03762",
                }
            ]
        },
    }


class CommunityListResponse(BaseModel):
    """Response from the community popular papers endpoint."""

    total: int = Field(..., description="Number of papers returned")
    papers: list[CommunityPaperResponse] = Field(..., description="Papers ranked by interaction count")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total": 1,
                    "papers": [
                        {
                            "arxiv_id": "1706.03762",
                            "interaction_count": 14,
                            "last_interacted_at": "2025-03-10T11:42:00Z",
                            "title": "Attention Is All You Need",
                            "authors": "Ashish Vaswani, Noam Shazeer",
                            "categories": "cs.CL cs.LG",
                            "year": 2017,
                            "url": "https://arxiv.org/abs/1706.03762",
                        }
                    ],
                }
            ]
        }
    }
