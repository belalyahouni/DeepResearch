from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

load_dotenv()

from app.routers import conversation, papers, search, summary

app = FastAPI(
    title="DeepResearch API",
    description="An agentic research assistant API for discovering, saving, and interacting with academic papers.",
    version="0.1.0",
)

# Security: only allow requests from trusted hosts
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])

# Security: restrict cross-origin requests to the local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["X-API-Key", "Content-Type"],
    allow_credentials=False,
)

app.include_router(papers.router)
app.include_router(search.router)
app.include_router(summary.router)
app.include_router(conversation.router)


@app.get("/health", tags=["Utility"])
async def health_check():
    """Check the API is running."""
    return {"status": "healthy"}
