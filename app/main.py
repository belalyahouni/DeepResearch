from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from app.routers import conversation, papers, search, summary

app = FastAPI(
    title="DeepResearch API",
    description="An agentic research assistant API for discovering, saving, and interacting with academic papers.",
    version="0.1.0",
)

app.include_router(papers.router)
app.include_router(search.router)
app.include_router(summary.router)
app.include_router(conversation.router)


@app.get("/health", tags=["Utility"])
async def health_check():
    """Check the API is running."""
    return {"status": "healthy"}
