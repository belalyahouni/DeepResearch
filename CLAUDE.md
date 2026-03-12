# CLAUDE.md — DeepResearch API

Agentic research assistant API — discover and search academic AI/ML papers.
FastAPI + SQLite + ChromaDB + Gemini + arXiv corpus. University coursework (COMP3011, Leeds).

**Student:** Belal Yahouni | **ID:** 201736144
**GitHub:** https://github.com/belalyahouni/DeepResearch
**Submission deadline:** 13 March 2026 (Minerva)

## Tech Stack

| Component | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ | |
| Framework | FastAPI | Swagger UI at `/docs` |
| Database | SQLite | SQLAlchemy async ORM, file `deepresearch.db` |
| Migrations | Alembic | DB schema versioning |
| Vector DB | ChromaDB | Persistent on-disk at `chroma_db/`, cosine similarity |
| Embeddings | `BAAI/bge-base-en-v1.5` | sentence-transformers, 768-dim, MPS-accelerated |
| LLM | Google Gemini | `google-genai` SDK |
| Corpus | arXiv AI/ML dataset | HuggingFace `davanstrien/arxiv-cs-papers-classified` |
| Testing | pytest + pytest-asyncio | In-memory SQLite, mocked external APIs |
| MCP | `mcp` (FastMCP) | Claude Desktop integration via stdio |
| Rate Limiting | `slowapi` | Per-IP, in-memory, applied to write endpoints |

## LLM Models

| Agent | Model | Reason |
|---|---|---|
| Classifier + Optimiser | `gemini-2.5-flash-lite` | Speed — lightweight structured output task |
| Summariser | `gemini-2.5-pro` | Quality — deep reasoning over academic text |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check (no auth) |
| GET | `/search?query=...` | Classify → optimise → BGE vector search over arXiv corpus |
| POST | `/summarise` | Summarise any text; optional `arxiv_id` tracks community interaction. Rate limited 5/min |
| GET | `/papers/{arxiv_id}` | Get a paper from the corpus by arXiv ID. Tracks community interaction |
| GET | `/papers/{arxiv_id}/related` | Find related papers via BGE vector similarity. Tracks community interaction |
| GET | `/community` | List most popular papers ranked by interaction count. Optional `period=week\|month\|year` |
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
| `summarise_text` | Gemini-powered summarisation. Optional `arxiv_id` tracks community interaction |
| `find_related_papers` | BGE vector similarity search for related papers. Tracks community interaction |
| `get_community_papers` | List trending papers ranked by interaction count. Optional `period` param |
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
- **Licence:** CC0 (Public Domain) — arXiv metadata
- **Filter:** `cs.AI, cs.LG, cs.CL, cs.CV, cs.NE, cs.MA, stat.ML` → ~521k AI/ML papers
- **Pass 1:** Stream, filter, batch insert into SQLite (`arxiv_papers` table)
- **Pass 2:** Embed `title + abstract` with `bge-base-en-v1.5`, upsert into ChromaDB
- **Speed:** ~168 papers/sec on Apple Silicon MPS (~1hr for full corpus)
- **Resumable:** Uses `INSERT OR IGNORE` — safe to re-run, skips existing papers
- **Current state:** Full ~521k corpus ingested overnight

## Embedding Architecture

- **Model:** `BAAI/bge-base-en-v1.5` (768-dim, sentence-transformers)
- **Documents:** Embedded as `title + abstract` — no prefix
- **Queries:** Embedded with BGE retrieval prefix at query time only (`"Represent this sentence for searching relevant passages: "`)
- **Device:** Auto-detects MPS (Apple Silicon) → falls back to CPU
- **ChromaDB:** Cosine similarity (`hnsw:space: cosine`), persistent at `chroma_db/`

## Community Interaction Tracking

Two-table design:
- `community_interactions` — one timestamped row per event (raw log, enables period filtering)
- `community_papers` — aggregated count + last_interacted_at (for all-time ranking)

Triggered by: `GET /papers/{id}`, `POST /summarise` (with arxiv_id), `GET /papers/{id}/related`, `arxiv://{id}` MCP resource, `summarise_text` MCP tool (with arxiv_id), `find_related_papers` MCP tool.

`GET /community` supports optional `period=week|month|year` — queries the raw interactions log with a timestamp cutoff for rolling window rankings.

## Classifier Agent

- Combined classifier + optimiser in a single LLM call (one JSON response, minimal latency)
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
- Cover: happy path, invalid input (422), not found (404), external failure (500), graceful fallback, community period filtering, auth (401)
- 42 tests across 7 test files

## Security

- **API key auth** — `app/auth.py`, `X-API-Key` header, timing-safe comparison via `secrets.compare_digest`
- **CORS middleware** — restricts origins to `localhost:8000`, whitelists only used methods and headers (`GET`, `POST`, `PATCH`, `DELETE`)
- **Trusted host middleware** — rejects requests with forged `Host` headers
- **Rate limiting** — `slowapi` per-IP limits on expensive/write endpoints: `POST /summarise` (5/min), `POST /notes` and `PATCH /notes` (10/min each)
- **`/health` excluded** from auth (standard practice for monitoring)
- See `AUTHENTICATION.md` for full details

## Project Files

| File | Purpose |
|---|---|
| `technical_report.md` | Draft technical report (convert to PDF for submission) |
| `report_notes.md` | Comprehensive source notes for the report — all decisions, justifications, context |
| `docs/openapi.pdf` | Exported Swagger API documentation PDF |
| `docs/openapi.json` | OpenAPI spec |
| `AUTHENTICATION.md` | Auth and security details |
| `mcp_server.py` | MCP server entry point |
| `scripts/ingest_arxiv.py` | One-time corpus ingest script |

## Submission Status

### Code & API
- [x] README.md — project overview, setup, endpoints, tests
- [x] Swagger polish — descriptions, parameter docs, error codes on all endpoints
- [x] Export Swagger to PDF — `docs/openapi.json` + `docs/openapi.pdf`
- [x] CRUD — `PaperNote` (full CRUD) + `CommunityPaper` (create/read/update via interaction tracking)
- [x] Full corpus ingest — ~521k papers in SQLite + ChromaDB
- [x] Community period filtering — `period=week|month|year` on `GET /community`

### Written Deliverables
- [x] **Technical report** — `technical_report.md` (convert to PDF, attach conversation logs as appendix)
- [x] **GenAI conversation logs** — `chat_claude_code.txt` + `chat_gemini_Research.txt` (attach as appendix)
- [ ] **Presentation slides** — https://docs.google.com/presentation/d/1B8lSFLUzY_b4ehkRaAyDCXZhu-i7uHN_1G08rRB3m0s/edit?usp=share_link

### Submission Checklist (pass/fail gates)
- [x] Public GitHub repo with visible commit history
- [x] README.md present
- [x] API documentation exported as PDF (in repo at `docs/openapi.pdf`)
- [ ] Technical report PDF submitted via Minerva (with GenAI declaration + conversation logs appendix)
- [x] Code runs locally (`uvicorn app.main:app --reload`)
- [x] All tests pass (`pytest tests/ -v`)

### What NOT to Build
- Docker, deployment
- Citation graph, user accounts, per-user saved papers
- Frontend (not required for submission)
