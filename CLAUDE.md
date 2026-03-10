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
| LLM | Google Gemini | `google-genai` SDK, see model table below |
| Papers | OpenAlex API | Free key, semantic search (beta) |
| PDF Parsing | PyMuPDF (`fitz`) | Full text extraction |
| HTTP Client | `httpx` | Async requests |
| Environment | `python-dotenv` | `.env` file loading |
| Testing | pytest + pytest-asyncio | In-memory SQLite, mocked external APIs |

## LLM Model Strategy

| Agent | Model | Rationale |
|---|---|---|
| Query Intelligence (classify + optimise) | `gemini-2.5-flash-lite` | Simple structured task, needs to be fast, runs on every search |
| Summariser | `gemini-2.5-pro` | Complex task — reading full PDF, producing structured output, quality matters |
| Chat | `gemini-2.5-flash` | Balanced — conversational but needs to reason about paper content |

## User Workflow

1. **Search** — user searches for a topic → query is classified + optimised → semantic search returns top results
2. **Preview** — user can summarise any search result to check relevance (without saving)
3. **Save** — user saves interesting papers to their library (summary stored on Paper so it's not re-generated)
4. **Library** — user views all saved papers with summaries and notes
5. **Deep dive** — user selects a paper → full PDF text loaded → chat with LLM about it + take notes

## Project Structure

```
app/
├── main.py                          # FastAPI entry point, loads .env, registers routers
├── database.py                      # SQLAlchemy async engine + session dependency
├── models/
│   ├── paper.py                     # Paper model (openalex_id, title, authors, summary, etc.)
│   └── conversation.py              # Conversation model (paper_id, role, message)
├── schemas/
│   └── paper.py                     # PaperCreate, PaperUpdate, PaperResponse
├── routers/
│   ├── papers.py                    # CRUD: POST/GET/PUT/DELETE /papers
│   └── search.py                    # GET /search — full agent pipeline
├── agents/
│   ├── classifier_optimiser.py      # Gemini agent: field classification + query optimisation
│   ├── summariser.py                # Paper summarisation (Phase 8)
│   └── chat.py                      # Conversational chat (Phase 9)
└── services/
    ├── openalex.py                  # OpenAlex API client (semantic + keyword search)
    └── pdf_parser.py               # PDF text extraction (Phase 7)
tests/
├── conftest.py                      # Fixtures: in-memory DB, async test client
├── test_health.py                   # Health endpoint test
├── test_papers.py                   # 13 tests: full CRUD + edge cases
└── test_search.py                   # 5 tests: pipeline, validation, errors, fallback
```

## Current Implementation Status

### Implemented (working + tested)
- **Health endpoint** — `GET /health`
- **Papers CRUD** — `POST/GET/PUT/DELETE /papers` with Pydantic validation, tag filtering, duplicate detection (409)
- **OpenAlex search** — `GET /search` with semantic search (AI embeddings) + keyword fallback
- **Query Intelligence agent** — Gemini classifies query into OpenAlex field + optimises for semantic search
- **Search pipeline** — query → classify → optimise → semantic search → results (with field/optimised query in response)
- **Database** — async SQLAlchemy, 2 models (Paper, Conversation), Alembic migration
- **Test suite** — 19 tests, in-memory DB, mocked external APIs

### Remaining Phases
- [ ] **Phase 7** — PDF Parser (PyMuPDF extraction from open access URLs, fallback to abstract)
- [ ] **Phase 8** — Summariser Agent (`gemini-2.5-pro`, `POST /papers/{id}/summary`, summary stored on Paper)
- [ ] **Phase 9** — Chat Agent (`gemini-2.5-flash`, `POST/GET/DELETE /papers/{id}/chat`, multi-turn conversation)

## Key Commands

```bash
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
pytest tests/ -v
```

## Environment Variables

```
GEMINI_API_KEY=
OPEN_ALEX_API_KEY=
```

## Coding Conventions

- **British English** in code, comments, and docs (summariser, optimiser, etc.)
- **Async** endpoints and async SQLAlchemy throughout
- **One responsibility per file** — keep code modular
- **Type hints** on all functions
- **Pydantic schemas** for all request/response validation
- **Wrap Gemini/external calls** in try/except with meaningful error messages
- **Proper HTTP status codes** on all endpoints (200, 201, 404, 422, 500)
- **PDF parsing** always falls back to abstract if unavailable or parsing fails
- **Chat agent** loads full conversation history from DB on each call
- **Summary stored on Paper model** — generate once, serve from DB thereafter
- **Never commit** `.env` or `deepresearch.db`

## Workflow Rules

1. Follow build phases in order — never skip ahead
2. **After each phase** — add new tests for the feature, then run `pytest tests/ -v` to confirm both new tests and all existing regression tests pass (0 failures allowed)
3. Commit after each completed phase with a descriptive message
4. Confirm what was built and what to test before moving on
5. Ask before making architectural decisions not in the brief
6. See `DEEPRESEARCH_CLAUDE_CODE_BRIEF.md` for full specs (models, endpoints, agent prompts)
7. **Validate after every implementation** — after building any feature, run the server and test ALL existing endpoints end-to-end (not just the new ones). Confirm correct responses, error handling, and that nothing is broken before moving on.

## Testing

### Running Tests
```bash
source venv/bin/activate
pytest tests/ -v
```

### When to Run
- **After every implementation** — before telling the user it's done
- **After any refactor** — even "safe" changes can break things
- **Before every commit** — never commit with failing tests

### What Must Pass
- All existing tests must pass (regression) — 0 failures allowed
- New features must include new tests covering happy path + error cases
- Tests use in-memory SQLite (isolated from real DB) and mock all external APIs (Gemini, OpenAlex) — no API quota used

### If Tests Fail
1. **Do not move on** — fix the failure first
2. Read the failure output carefully — identify if it's the new code or a regression
3. If a new feature broke an existing test, the new code is wrong — fix it
4. If a test itself is outdated (e.g. response shape changed intentionally), update the test
5. Re-run the full suite after fixing — confirm everything passes

### Adding Tests for New Features
- Add tests to the relevant `tests/test_*.py` file or create a new one
- Mock all external API calls (Gemini, OpenAlex) — tests must run offline and fast
- Cover: valid input (200/201), invalid input (422), not found (404), external failure (500), graceful fallback

## Quality Bar — Targeting 90-100 (Outstanding)

The code-related marks break down as:

**API Functionality & Implementation (25/75)**
- All phases fully implemented and working end-to-end
- Full CRUD on Papers with database integration
- Multi-agent search pipeline (classify → optimise → search)
- PDF parsing with graceful fallback
- AI summarisation with structured output, persisted on Paper
- Multi-turn conversational chat per paper
- All endpoints return appropriate JSON responses

**Code Quality & Architecture (20/75)**
- Clean, modular structure — one responsibility per file
- Async throughout (endpoints + SQLAlchemy)
- Consistent error handling with try/except on all external calls
- Pydantic schemas for all request/response validation
- No code duplication — shared utilities where appropriate
- Type hints on all functions
- Clear naming conventions (British English)

**API Documentation (part of 12/75)**
- Swagger UI with descriptions on all endpoints, parameters, and response formats
- Example requests and responses visible in Swagger
- Error codes documented per endpoint
- Export Swagger to PDF and include in repo
- Reference API docs in README.md

**Version Control (part of 6/75)**
- Descriptive commit after every phase — visible incremental history
- Meaningful commit messages explaining what was built
- README.md with setup instructions and project overview (**fail without it**)

**Testing & Error Handling (6/75)**
- Comprehensive error handling on every endpoint
- Graceful degradation (PDF fallback, Gemini error handling)
- All edge cases handled (not found, invalid input, external API failures)
- Correct status codes for every error scenario

**Creativity & Innovation (6/75)**
- Novel agentic pipeline (3 LLM agents working together)
- Integration of contemporary technologies (Gemini, OpenAlex, PyMuPDF)
- Originality in how agents compose (classify + optimise → search → summarise → chat)

## What NOT to Build

- Authentication / API key protection
- Rate limiting
- Frontend / UI
- Citation graph / recommendations
- User accounts
- Docker
- Deployment (local execution is sufficient for top marks)
