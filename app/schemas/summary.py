"""Pydantic schemas for the summarise preview endpoint."""

from pydantic import BaseModel, Field


class SummariseRequest(BaseModel):
    """Request body for previewing a summary."""
    text: str = Field(..., min_length=1, description="Text to summarise (abstract or full paper text)")


class SummariseResponse(BaseModel):
    """Response from the summarise preview endpoint."""
    summary: str
