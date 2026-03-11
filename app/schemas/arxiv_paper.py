"""Pydantic schemas for arXiv paper responses."""

from pydantic import BaseModel, Field


class ArxivPaperResponse(BaseModel):
    """Schema for returning an arXiv paper from the corpus."""

    arxiv_id: str = Field(..., description="arXiv paper ID (e.g. 1706.03762)")
    title: str = Field(..., description="Paper title")
    authors: str = Field(..., description="Comma-separated author names")
    abstract: str | None = Field(None, description="Paper abstract")
    categories: str = Field(..., description="Space-separated arXiv categories")
    year: int | None = Field(None, description="Publication year")
    doi: str | None = Field(None, description="Digital Object Identifier")
    url: str = Field(..., description="arXiv URL")
    similarity_score: float | None = Field(None, description="Cosine similarity score from vector search (0-1)")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "arxiv_id": "1706.03762",
                    "title": "Attention Is All You Need",
                    "authors": "Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin",
                    "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
                    "categories": "cs.CL cs.LG",
                    "year": 2017,
                    "doi": "10.48550/arXiv.1706.03762",
                    "url": "https://arxiv.org/abs/1706.03762",
                    "similarity_score": 0.92,
                }
            ]
        },
    }
