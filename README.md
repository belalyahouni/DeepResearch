# DeepResearch API

An agentic research assistant API for discovering, saving, and interacting with academic papers. Features a novel 3-agent pipeline powered by Google Gemini, with paper discovery via OpenAlex semantic search.

Built for COMP3011 coursework (University of Leeds).

## Tech Stack

| Component | Choice |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Database | SQLite (SQLAlchemy async ORM) |
| Migrations | Alembic |
| LLM | Google Gemini (`google-genai` SDK) |
| Papers | OpenAlex API (semantic search) |
| PDF Parsing | PyMuPDF (`fitz`) |
| HTTP Client | `httpx` (async) |
| Testing | pytest + pytest-asyncio |

## Architecture

The API uses a **3-agent pipeline** powered by Google Gemini:

1. **Classifier + Optimiser Agent** (`gemini-2.5-flash-lite`) — classifies the user's query into an academic field and rewrites it for optimal retrieval.
2. **Summariser Agent** (`gemini-2.5-pro`) — generates structured summaries of paper abstracts or full texts.
3. **Chat Agent** (`gemini-2.5-flash`) — answers questions about a saved paper using its full text as context.
4. **Related Papers Agent** (`gemini-2.5-flash-lite`) — generates semantic search queries from a saved paper to discover related work via OpenAlex (250M+ works).

When a paper is saved, the system automatically extracts the full text from the open-access PDF (via PyMuPDF) and generates an AI summary — both best-effort, never blocking the save operation.

## Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/research-agent.git
cd research-agent

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your keys:
#   GEMINI_API_KEY=your-gemini-key
#   OPEN_ALEX_API_KEY=your-openalex-key (optional)
#   API_KEY=your-api-key

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive documentation is at `http://localhost:8000/docs`.

## API Endpoints

All endpoints (except `/health`) require the `X-API-Key` header.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/search?query=...` | Agentic search: classify → optimise → semantic search |
| POST | `/summarise` | Summarise any academic text |
| POST | `/papers` | Save paper (auto-extracts PDF + generates summary) |
| GET | `/papers` | List saved papers (`?tags=` filter) |
| GET | `/papers/{id}` | Get a saved paper |
| PUT | `/papers/{id}` | Update tags/notes |
| DELETE | `/papers/{id}` | Remove paper |
| GET | `/papers/{id}/related` | Find related papers (agent-powered semantic search) |

## Authentication

All endpoints except `/health` and `/docs` are protected by API key authentication. Include the key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/papers
```

The Swagger UI at `/docs` includes an **Authorise** button for interactive testing.

## MCP Server (Claude Desktop)

The project also includes an MCP (Model Context Protocol) server for integration with Claude Desktop. It exposes the same functionality as the REST API — search, save, summarise, chat, and related papers — as MCP tools and resources.

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
| `search_papers` | Agentic classify + optimise + semantic search |
| `summarise_text` | Gemini-powered summarisation |
| `save_paper` | Save with auto PDF extraction + summary |
| `update_paper` | Update tags/notes |
| `delete_paper` | Remove from library |
| `chat_with_paper` | Stateless Q&A about a saved paper |
| `find_related_papers` | Agent-powered related paper discovery |

### Testing the MCP Server

```bash
mcp dev mcp_server.py
```

This opens the MCP Inspector — a web UI for calling tools and reading resources interactively.

## Testing

Tests use an in-memory SQLite database and mock all external APIs (Gemini, OpenAlex).

```bash
pytest tests/ -v
```

38 tests across 6 test files covering: happy paths, validation errors (422), not found (404), duplicate detection (409), external service failures (500), and authentication (401).

## API Documentation

- Interactive Swagger UI: `http://localhost:8000/docs`
- OpenAPI spec: [`docs/openapi.json`](docs/openapi.json)
- Exported PDF: [`docs/openapi.pdf`](docs/openapi.pdf)
