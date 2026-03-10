from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

load_dotenv()

from app.routers import conversation, papers, search, summary

tags_metadata = [
    {"name": "Search", "description": "Agentic search pipeline: classify the academic field, optimise the query, and retrieve papers from OpenAlex via semantic search."},
    {"name": "Papers", "description": "CRUD operations for the saved paper library — save, list, retrieve, update, and delete academic papers."},
    {"name": "Summarisation", "description": "AI-powered summarisation of academic text using the Gemini summariser agent."},
    {"name": "Chat", "description": "Multi-turn conversation about a saved paper, powered by the Gemini chat agent."},
    {"name": "Utility", "description": "System health and status checks."},
]

app = FastAPI(
    title="DeepResearch API",
    description=(
        "An agentic research assistant API for discovering, saving, and interacting "
        "with academic papers. Features a novel 3-agent pipeline (classifier + optimiser "
        "→ summariser → chat) powered by Google Gemini, with paper discovery via "
        "OpenAlex semantic search. Built with FastAPI, SQLAlchemy, and SQLite."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
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


@app.get("/health", tags=["Utility"], summary="Health check")
async def health_check():
    """Check the API is running and responsive."""
    return {"status": "healthy"}
