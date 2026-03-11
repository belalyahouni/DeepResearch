# CLAUDE.md — DeepResearch API

Agentic research assistant API — discover and search academic AI/ML papers.
FastAPI + SQLite + ChromaDB + Gemini + arXiv corpus. University coursework (COMP3011, Leeds).

## Tech Stack

| Component | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ | |
| Framework | FastAPI | Swagger UI at `/docs` |
| Database | SQLite | SQLAlchemy ORM, file `deepresearch.db` |
| Migrations | Alembic | DB schema versioning |
| Vector DB | ChromaDB | Persistent on-disk at `chroma_db/`, cosine similarity |
| Embeddings | `BAAI/bge-base-en-v1.5` | sentence-transformers, 768-dim, MPS-accelerated |
| LLM | Google Gemini | `google-genai` SDK |
| Corpus | arXiv AI/ML dataset | HuggingFace `davanstrien/arxiv-cs-papers-classified` |
| Testing | pytest + pytest-asyncio | In-memory SQLite, mocked external APIs |
| MCP | `mcp` (FastMCP) | Claude Desktop integration via stdio |
| Rate Limiting | `slowapi` | Per-IP, in-memory, applied to write endpoints |

## LLM Models

| Agent | Model |
|---|---|
| Classifier + Optimiser | `gemini-2.5-flash-lite` |
| Summariser | `gemini-2.5-pro` |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/search?query=...` | Classify → optimise → BGE vector search over arXiv corpus |
| POST | `/summarise` | Summarise any text; optional `arxiv_id` tracks community interaction. Rate limited 5/min |
| GET | `/papers/{arxiv_id}` | Get a paper from the corpus by arXiv ID. Tracks community interaction |
| GET | `/papers/{arxiv_id}/related` | Find related papers via BGE vector similarity. Tracks community interaction |
| GET | `/community` | List most popular papers ranked by interaction count |
| GET | `/community/{arxiv_id}` | Get community interaction stats for a specific paper |
| POST | `/papers/{arxiv_id}/notes` | Add a public note to a paper. Rate limited 10/min |
| GET | `/papers/{arxiv_id}/notes` | List all public notes on a paper |
| PATCH | `/notes/{id}` | Update a note by ID. Rate limited 10/min |
| DELETE | `/notes/{id}` | Delete a note by ID |

## MCP Server (Claude Desktop)

The project exposes an MCP (Model Context Protocol) server for use with Claude Desktop. It reuses the same agents, services, and database — no HTTP calls to the FastAPI app.

**Entry point:** `mcp_server.py` (project root), stdio transport.

### MCP Tools

| Tool | Description |
|---|---|
| `search_papers` | Agentic classify + optimise + BGE vector search |
| `summarise_text` | Gemini-powered summarisation |
| `find_related_papers` | BGE vector similarity search for related papers. Tracks community interaction |
| `get_community_papers` | List trending papers ranked by interaction count |
| `get_paper_notes` | Retrieve all public community notes for a paper |

### MCP Resources

| URI | Description |
|---|---|
| `arxiv://{arxiv_id}` | Full paper details. Tracks community interaction |
| `arxiv://stats` | Corpus stats (total papers, year range) |

## Key Commands

```bash
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python scripts/ingest_arxiv.py           # Ingest full arXiv AI/ML corpus (~521k papers, ~1hr on MPS)
python scripts/ingest_arxiv.py --limit N # Ingest N papers (for testing)
uvicorn app.main:app --reload            # FastAPI server
python mcp_server.py                     # MCP server (stdio, for Claude Desktop)
mcp dev mcp_server.py                    # MCP Inspector (interactive testing)
pytest tests/ -v
```

## Corpus Ingestion

- **Source:** HuggingFace `davanstrien/arxiv-cs-papers-classified` (1.14M CS papers)
- **Filter:** `cs.AI, cs.LG, cs.CL, cs.CV, cs.NE, cs.MA, stat.ML` → ~521k AI/ML papers
- **Pass 1:** Stream, filter, batch insert into SQLite (`arxiv_papers` table)
- **Pass 2:** Embed `title + abstract` with `bge-base-en-v1.5`, upsert into ChromaDB
- **Speed:** ~168 papers/sec on Apple Silicon MPS (~1hr for full corpus)
- **Resumable:** Uses `INSERT OR IGNORE` — safe to re-run, skips existing papers
- **Current state:** 10k papers ingested (2019 vintage); full run pending

## Embedding Architecture

- **Model:** `BAAI/bge-base-en-v1.5` (768-dim, sentence-transformers)
- **Documents:** Embedded as `title + abstract` — no prefix
- **Queries:** Embedded with BGE retrieval prefix at query time only
- **Device:** Auto-detects MPS (Apple Silicon) → falls back to CPU
- **ChromaDB:** Cosine similarity (`hnsw:space: cosine`), persistent at `chroma_db/`

## Classifier Agent

- Classifies queries into arXiv AI/ML categories: `cs.AI, cs.LG, cs.CL, cs.CV, cs.NE, cs.MA, stat.ML`
- Returns: `category` (code), `field` (human-readable label), `optimised_query`
- Graceful fallback if Gemini unavailable — returns original query, null category

## Environment Variables

```
GEMINI_API_KEY=
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
- **Never commit** `.env` or `deepresearch.db` or `chroma_db/`

## Testing

- Run `pytest tests/ -v` after every change — 0 failures allowed
- Tests use in-memory SQLite and mock all external APIs (Gemini, ChromaDB)
- Cover: happy path, invalid input (422), not found (404), external failure (500), graceful fallback
- 38 tests across 7 test files

## Quality Bar — Targeting 90-100

- All endpoints working end-to-end with proper error handling and authentication
- Swagger UI with descriptions on all endpoints — export to PDF for submission
- Descriptive commits with visible incremental history
- README.md with setup instructions (**required**)
- Novel pipeline: arXiv classifier + query optimiser → BGE vector search → Gemini summariser

## Submission TODO

### Code & API (do first)
- [x] **README.md** — project overview, setup instructions, endpoint summary, how to run tests. Pass/fail gate.
- [x] **Swagger polish** — add descriptions, parameter docs, example requests/responses, and error codes to all endpoints
- [x] **Export Swagger to PDF** — save `openapi.json` + exported PDF to repo
- [x] **CRUD** — `PaperNote` (full CRUD) + `CommunityPaper` (create/read/update via interaction tracking)
- [ ] **Re-export Swagger to PDF** — new endpoints need to be included in the docs PDF
- [ ] **Full corpus ingest** — run `python scripts/ingest_arxiv.py` overnight for ~521k papers
- [ ] **Frontend** — simple UI for demo and presentation (search, library, related papers)

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
- **CORS middleware** — restricts origins to `localhost:8000`, whitelists only used methods and headers (`GET`, `POST`, `PATCH`, `DELETE`)
- **Trusted host middleware** — rejects requests with forged `Host` headers
- **Rate limiting** — `slowapi` per-IP limits on expensive/write endpoints: `POST /summarise` (5/min), `POST /notes` and `PATCH /notes` (10/min each)
- **`/health` excluded** from auth (standard practice for monitoring)
- See `AUTHENTICATION.md` for full details

### What NOT to Build
- Docker, deployment
- Citation graph, recommendations, user accounts
- Per-user saved papers — the API is public, all data is shared
