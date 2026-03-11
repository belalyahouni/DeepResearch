# CLAUDE.md — DeepResearch API

Agentic research assistant API — discover, save, and chat with academic papers.
FastAPI + SQLite + Gemini + OpenAlex. University coursework (COMP3011, Leeds).

## Tech Stack

| Component | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ | |
| Framework | FastAPI | Swagger UI at `/docs` |
| Database | SQLite | SQLAlchemy ORM, file `deepresearch.db` |
| Migrations | Alembic | DB schema versioning |
| LLM | Google Gemini | `google-genai` SDK |
| Papers | OpenAlex API | Semantic search (beta) |
| PDF Parsing | PyMuPDF (`fitz`) | Full text extraction |
| HTTP Client | `httpx` | Async requests |
| Testing | pytest + pytest-asyncio | In-memory SQLite, mocked external APIs |
| MCP | `mcp` (FastMCP) | Claude Desktop integration via stdio |

## LLM Models

| Agent | Model |
|---|---|
| Classifier + Optimiser | `gemini-2.5-flash-lite` |
| Summariser | `gemini-2.5-pro` |
| Chat | `gemini-2.5-flash` |
| Related Papers | `gemini-2.5-flash-lite` |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/search?query=...` | Classify → optimise → semantic search via OpenAlex |
| POST | `/summarise` | Summarise any text (abstract or full paper) |
| POST | `/papers` | Save paper (auto-extracts PDF + generates summary) |
| GET | `/papers` | List saved papers (`?tags=` filter) |
| GET | `/papers/{id}` | Get a saved paper |
| PUT | `/papers/{id}` | Update tags/notes |
| DELETE | `/papers/{id}` | Remove paper |
| GET | `/papers/{id}/related` | Find related papers (agent-powered semantic search) |

## MCP Server (Claude Desktop)

The project also exposes an MCP (Model Context Protocol) server for use with Claude Desktop. It reuses the same agents, services, and database — no HTTP calls to the FastAPI app.

**Entry point:** `mcp_server.py` (project root), stdio transport.

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

### MCP Resources

| URI | Description |
|---|---|
| `papers://library` | List all saved papers (compact) |
| `papers://{paper_id}` | Full paper details |

## Key Commands

```bash
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload        # FastAPI server
python mcp_server.py                  # MCP server (stdio, for Claude Desktop)
mcp dev mcp_server.py                 # MCP Inspector (interactive testing)
pytest tests/ -v
```

## Environment Variables

```
GEMINI_API_KEY=
OPEN_ALEX_API_KEY=
API_KEY=
```

## Coding Conventions

- **British English** in code, comments, and docs (summariser, optimiser, etc.)
- **Async** endpoints and async SQLAlchemy throughout
- **One responsibility per file** — modular structure
- **Type hints** on all functions
- **Pydantic schemas** for all request/response validation
- **Wrap Gemini/external calls** in try/except — graceful fallback on failure
- **Proper HTTP status codes** — 200, 201, 204, 401, 404, 409, 422, 500
- **API key auth** on all endpoints except `/health` and `/docs` — via `X-API-Key` header, `app/auth.py`
- **Never commit** `.env` or `deepresearch.db`

## Testing

- Run `pytest tests/ -v` after every change — 0 failures allowed
- Tests use in-memory SQLite and mock all external APIs (Gemini, OpenAlex)
- Cover: happy path, invalid input (422), not found (404), external failure (500), graceful fallback
- 38 tests across 6 test files (includes `test_auth.py`)

## Quality Bar — Targeting 90-100

- All endpoints working end-to-end with proper error handling and authentication
- Swagger UI with descriptions on all endpoints — export to PDF for submission
- Descriptive commits with visible incremental history
- README.md with setup instructions (**required**)
- Novel 3-agent pipeline: classify + optimise → search → summarise → chat

## Submission TODO

All core API functionality is complete (38 tests passing). MCP server added for Claude Desktop. Remaining work is frontend, written deliverables, and presentation.

### Code & API (do first)
- [x] **README.md** — project overview, setup instructions, endpoint summary, how to run tests. Pass/fail gate.
- [x] **Swagger polish** — add descriptions, parameter docs, example requests/responses, and error codes to all endpoints
- [x] **Export Swagger to PDF** — save `openapi.json` + exported PDF to repo
- [ ] **Frontend** — simple UI for demo and presentation (search, save, library, chat)

### Written Deliverables
- [ ] **Technical report** (max 5 pages) — stack justification, architecture, testing approach, limitations, GenAI declaration
- [ ] **GenAI conversation logs** — export and include Claude conversation examples
- [ ] **Presentation slides** (PowerPoint, 5 min) — version control, API docs, technical highlights, live demo plan

### Submission Checklist (pass/fail gates)
- [ ] Public GitHub repo with visible commit history
- [x] README.md present
- [x] API documentation exported as PDF
- [ ] Technical report with GenAI declaration
- [x] Code runs locally (`uvicorn app.main:app --reload`)
- [x] All tests pass (`pytest tests/ -v`)

## Security

- **API key auth** — `app/auth.py`, `X-API-Key` header, timing-safe comparison via `secrets.compare_digest`
- **CORS middleware** — restricts origins to `localhost:8000`, whitelists only used methods and headers
- **Trusted host middleware** — rejects requests with forged `Host` headers
- **`/health` excluded** from auth (standard practice for monitoring)
- See `AUTHENTICATION.md` for full details

### What NOT to Build
- Rate limiting, Docker, deployment
- Citation graph, recommendations, user accounts
