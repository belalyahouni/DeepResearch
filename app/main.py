from fastapi import FastAPI

app = FastAPI(
    title="DeepResearch API",
    description="An agentic research assistant API for discovering, saving, and interacting with academic papers.",
    version="0.1.0",
)


@app.get("/health", tags=["Utility"])
async def health_check():
    """Check the API is running."""
    return {"status": "healthy"}
