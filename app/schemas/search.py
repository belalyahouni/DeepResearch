"""Pydantic schemas for the search endpoint response."""

from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """A single paper result from the arXiv corpus vector search."""

    arxiv_id: str = Field(..., description="arXiv paper ID")
    title: str = Field(..., description="Paper title")
    authors: str = Field(..., description="Comma-separated author names")
    abstract: str | None = Field(None, description="Paper abstract")
    categories: str = Field(..., description="Space-separated arXiv categories")
    year: int | None = Field(None, description="Publication year")
    doi: str | None = Field(None, description="Digital Object Identifier")
    url: str = Field(..., description="arXiv URL")
    similarity_score: float | None = Field(None, description="Cosine similarity score (0-1, higher is more similar)")


class SearchResponse(BaseModel):
    """Response from the agentic search pipeline."""

    original_query: str = Field(..., description="The raw query submitted by the user")
    field: str | None = Field(None, description="Human-readable label of the detected arXiv AI/ML category")
    optimised_query: str = Field(..., description="Query rewritten by the optimiser agent for better retrieval")
    result_count: int = Field(..., description="Number of papers returned")
    results: list[SearchResultItem] = Field(..., description="List of matching papers from the arXiv corpus")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "original_query": "KV cache optimisation for transformers",
                    "field": "Machine Learning",
                    "optimised_query": "key-value cache memory optimisation transformer language models",
                    "result_count": 1,
                    "results": [
                        {
                            "arxiv_id": "1706.03762",
                            "title": "Attention Is All You Need",
                            "authors": "Ashish Vaswani, Noam Shazeer",
                            "abstract": "The dominant sequence transduction models...",
                            "categories": "cs.CL cs.LG",
                            "year": 2017,
                            "doi": None,
                            "url": "https://arxiv.org/abs/1706.03762",
                            "similarity_score": 0.92,
                        }
                    ],
                }
            ]
        }
    }
