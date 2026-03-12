# DeepResearch API

An agentic research assistant API for discovering and exploring AI/ML academic papers. Features a novel 3-agent pipeline (classifier → query optimiser → BGE vector search) powered by Google Gemini, over a local arXiv corpus of ~521k papers.

Built for COMP3011 coursework (University of Leeds).

## Tech Stack

| Component | Choice |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Database | SQLite (SQLAlchemy async ORM) |
| Migrations | Alembic |
| Vector DB | ChromaDB (persistent, cosine similarity) |
| Embeddings | `BAAI/bge-base-en-v1.5` (768-dim, MPS-accelerated) |
| LLM | Google Gemini (`google-genai` SDK) |
| Corpus | arXiv AI/ML papers (HuggingFace dataset) |
| MCP | FastMCP (Claude Desktop integration) |
| Rate Limiting | slowapi (per-IP) |
| Testing | pytest + pytest-asyncio |

## Architecture

The API is built around a **3-stage agentic pipeline**:

1. **Classifier Agent** (`gemini-2.5-flash-lite`) — classifies the user's natural language query into an arXiv AI/ML category (`cs.AI`, `cs.LG`, `cs.CL`, `cs.CV`, etc.).
2. **Optimiser Agent** (`gemini-2.5-flash-lite`) — rewrites the query into precise academic retrieval terms for better vector search results.
3. **BGE Vector Search** — embeds the optimised query with `BAAI/bge-base-en-v1.5` and performs cosine similarity search over ChromaDB, returning ranked results from the arXiv corpus.

Summarisation is handled separately by a **Summariser Agent** (`gemini-2.5-pro`). All Gemini calls have graceful fallbacks — the pipeline degrades safely if the LLM is unavailable.

Community interaction tracking is automatic: every paper access via lookup, summarisation, or related-papers search is recorded as a timestamped event in a `community_interactions` log. This enables both all-time rankings and rolling time-window queries (`week` / `month` / `year`) on `GET /community`.

## Setup

```bash
# Clone the repository
git clone https://github.com/belalyahouni/DeepResearch.git
cd DeepResearch

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and set:
#   GEMINI_API_KEY=your-gemini-key
#   API_KEY=your-api-key

# Run database migrations
alembic upgrade head

# (Optional) Ingest the arXiv corpus into SQLite + ChromaDB
python scripts/ingest_arxiv.py --limit 10000   # quick test run
python scripts/ingest_arxiv.py                  # full ~521k papers (~1hr on Apple Silicon)

# Start the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive documentation is at `http://localhost:8000/docs`.

## API Endpoints

All endpoints except `/health` require the `X-API-Key` header.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/search?query=...` | Classify → optimise → BGE vector search over arXiv corpus |
| POST | `/summarise` | Summarise any academic text via Gemini. Rate limited 5/min |
| GET | `/papers/{arxiv_id}` | Get a paper from the corpus by arXiv ID |
| GET | `/papers/{arxiv_id}/related` | Find related papers via BGE vector similarity |
| GET | `/community` | List most popular papers ranked by interaction count. Optional `period=week\|month\|year` for rolling window |
| GET | `/community/{arxiv_id}` | Get community interaction stats for a specific paper |
| POST | `/papers/{arxiv_id}/notes` | Add a public note to a paper. Rate limited 10/min |
| GET | `/papers/{arxiv_id}/notes` | List all public notes on a paper |
| PATCH | `/notes/{id}` | Update a note by ID. Rate limited 10/min |
| DELETE | `/notes/{id}` | Delete a note by ID |

## Authentication

All endpoints except `/health` and `/docs` require API key authentication via the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/search?query=transformers
```

The Swagger UI at `/docs` includes an **Authorise** button for interactive testing.

## Running Tests

Tests use an in-memory SQLite database and mock all external APIs (Gemini, ChromaDB).

```bash
pytest tests/ -v
```

42 tests across 7 test files covering: happy paths, validation errors (422), not found (404), external service failures (500), rate limiting, authentication (401), and community period filtering.

## MCP Server (Claude Desktop)

The project exposes an MCP (Model Context Protocol) server that gives Claude Desktop direct access to the same pipeline — no HTTP calls, same agents and database.

### Setup

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "deepresearch": {
      "command": "/path/to/research-agent/venv/bin/python",
      "args": ["/path/to/research-agent/mcp_server.py"]
    }
  }
}
```

Restart Claude Desktop. The tools will appear in the tools menu.

### MCP Tools

| Tool | Description |
|---|---|
| `search_papers` | Agentic classify + optimise + BGE vector search |
| `summarise_text` | Gemini-powered summarisation. Optional `arxiv_id` tracks community interaction |
| `find_related_papers` | BGE vector similarity search for related papers. Tracks community interaction |
| `get_community_papers` | List trending papers ranked by interaction count |
| `get_paper_notes` | Retrieve all public notes for a paper |

### MCP Resources

| URI | Description |
|---|---|
| `arxiv://{arxiv_id}` | Full paper details (tracks community interaction) |
| `arxiv://stats` | Corpus stats (total papers, year range) |

### Testing the MCP Server

```bash
mcp dev mcp_server.py
```

This opens the MCP Inspector — a web UI for calling tools and reading resources interactively.

## API Documentation

- Interactive Swagger UI: `http://localhost:8000/docs`
- OpenAPI spec: [`docs/openapi.json`](docs/openapi.json)
- Exported PDF: [`docs/API_Swagger_UI.pdf`](docs/API_Swagger_UI.pdf)
