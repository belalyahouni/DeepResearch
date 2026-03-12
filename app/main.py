import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

load_dotenv()

from app.limiter import limiter
from app.routers import community, papers, search, summary
from app.routers.notes import notes_router, papers_router as notes_papers_router

tags_metadata = [
    {"name": "Search", "description": "Agentic search pipeline: classify the query, optimise it for retrieval, then perform BGE vector similarity search over a local arXiv AI/ML corpus."},
    {"name": "Papers", "description": "Look up arXiv papers from the local corpus and find related papers via BGE vector similarity."},
    {"name": "Summarisation", "description": "AI-powered summarisation of academic text using the Gemini summariser agent. Rate limited to 5 requests/minute."},
    {"name": "Community", "description": "Community activity index — discover papers trending by interaction count across the API."},
    {"name": "Notes", "description": "Public notes on arXiv papers — readable by all consumers and agents. Full CRUD. Write endpoints rate limited to 10 requests/minute."},
    {"name": "Utility", "description": "System health and status checks."},
]

app = FastAPI(
    title="DeepResearch API",
    description=(
        "An agentic research assistant API for discovering and exploring AI/ML academic "
        "papers. Features a 3-agent pipeline (classifier → query optimiser → BGE vector search) "
        "powered by Google Gemini, with `BAAI/bge-base-en-v1.5` cosine similarity search "
        "over a local arXiv AI/ML corpus (~521k papers). Summarisation via Gemini. "
        "Built with FastAPI, SQLAlchemy, ChromaDB, and SQLite. "
        "Authenticate via the `X-API-Key` header on all endpoints except `/health`."
    ),
    version="2.0.0",
    openapi_tags=tags_metadata,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security: only allow requests from trusted hosts
# ALLOWED_HOSTS env var overrides the default (comma-separated, use * for all)
_allowed_hosts = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts)

# Security: restrict cross-origin requests
# ALLOWED_ORIGINS env var overrides the default (comma-separated)
_allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["X-API-Key", "Content-Type"],
    allow_credentials=False,
)

app.include_router(papers.router)
app.include_router(search.router)
app.include_router(summary.router)
app.include_router(community.router)
app.include_router(notes_papers_router)
app.include_router(notes_router)


@app.get("/health", tags=["Utility"], summary="Health check")
async def health_check():
    """Check the API is running and responsive."""
    return {"status": "healthy"}
