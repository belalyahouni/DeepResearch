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
                    "original_query": "KV cache optimisation for transformers",
                    "field_id": 154945302,
                    "field": "Artificial Intelligence",
                    "optimised_query": "key-value cache memory optimisation transformer language models",
                    "result_count": 1,
                    "results": [
                        {
                            "openalex_id": "https://openalex.org/W4415109130",
                            "doi": "https://doi.org/10.48550/arxiv.2506.13541",
                            "title": "Mixture of Weight-shared Heterogeneous Group Attention Experts for Dynamic Token-wise KV Optimization",
                            "authors": "Guoqiang Song, D. Z. Liao, Yijiao Zhao, Kejiang Ye, Chunxiang Xu, Xiang Gao",
                            "abstract": "Transformer models face scalability challenges in causal language modeling (CLM) due to inefficient memory allocation for growing key-value (KV) caches...",
                            "year": 2025,
                            "url": "http://arxiv.org/abs/2506.13541",
                            "open_access_pdf_url": "https://arxiv.org/pdf/2506.13541",
                            "citation_count": 0,
                            "relevance_score": 0.896,
                        }
                    ],
                }
            ]
        }
    }
