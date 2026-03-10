"""Pydantic schemas for the summarise preview endpoint."""

from pydantic import BaseModel, Field


class SummariseRequest(BaseModel):
    """Request body for previewing a summary."""
    text: str = Field(..., min_length=1, description="Text to summarise (abstract or full paper text)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely..."
                }
            ]
        }
    }


class SummariseResponse(BaseModel):
    """Response from the summarise preview endpoint."""
    summary: str = Field(..., description="AI-generated summary of the input text")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "summary": "This paper introduces the Transformer, a novel architecture that relies entirely on self-attention mechanisms. It achieves state-of-the-art results on machine translation benchmarks while being more parallelisable and requiring significantly less training time."
                }
            ]
        }
    }
