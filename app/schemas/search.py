"""Pydantic schemas for the search endpoint response."""

from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """A single paper result from an OpenAlex search."""
    openalex_id: str = Field(..., description="OpenAlex work ID")
    doi: str | None = Field(None, description="Digital Object Identifier")
    title: str = Field(..., description="Paper title")
    authors: str = Field(..., description="Comma-separated author names")
    abstract: str | None = Field(None, description="Reconstructed abstract text")
    year: int | None = Field(None, description="Publication year")
    url: str | None = Field(None, description="Landing page URL")
    open_access_pdf_url: str | None = Field(None, description="Direct URL to the open-access PDF")
    citation_count: int = Field(..., description="Number of citations")
    relevance_score: float | None = Field(None, description="OpenAlex relevance score (semantic search only)")


class SearchResponse(BaseModel):
    """Response from the agentic search pipeline."""
    original_query: str = Field(..., description="The raw query submitted by the user")
    field_id: int | None = Field(None, description="OpenAlex field ID detected by the classifier agent")
    field: str | None = Field(None, description="Human-readable name of the detected academic field")
    optimised_query: str = Field(..., description="Query rewritten by the optimiser agent for better retrieval")
    result_count: int = Field(..., description="Number of papers returned")
    results: list[SearchResultItem] = Field(..., description="List of matching papers from OpenAlex")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "original_query": "how do transformers work",
                    "field_id": 154945302,
                    "field": "Artificial Intelligence",
                    "optimised_query": "transformer architecture self-attention mechanism neural networks",
                    "result_count": 1,
                    "results": [
                        {
                            "openalex_id": "https://openalex.org/W2963403868",
                            "doi": "https://doi.org/10.48550/arXiv.1706.03762",
                            "title": "Attention Is All You Need",
                            "authors": "Ashish Vaswani, Noam Shazeer",
                            "abstract": "The dominant sequence transduction models...",
                            "year": 2017,
                            "url": "https://arxiv.org/abs/1706.03762",
                            "open_access_pdf_url": "https://arxiv.org/pdf/1706.03762",
                            "citation_count": 100000,
                            "relevance_score": 0.95,
                        }
                    ],
                }
            ]
        }
    }
