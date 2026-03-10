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
| LLM | Google Gemini (`google-genai` SDK) | See model table below |

## LLM Model Strategy

| Agent | Model | Rationale |
|---|---|---|
| Query Intelligence (classify + optimise) | `gemini-2.5-flash-lite` | Simple structured task, needs to be fast, runs on every search |
| Summariser | `gemini-2.5-pro` | Complex task — reading full PDF, producing structured output, quality matters |
| Chat | `gemini-2.5-flash` | Balanced — conversational but needs to reason about paper content |
| Papers | OpenAlex API | Free key, semantic search (beta) |
| PDF Parsing | PyMuPDF (`fitz`) | Full text extraction |
| HTTP Client | `httpx` | Async requests |
| Environment | `python-dotenv` | `.env` file loading |

## Project Structure

```
app/
├── main.py               # FastAPI entry point
├── database.py           # SQLAlchemy engine + session
├── models/               # SQLAlchemy models (paper, search_session, conversation)
├── schemas/              # Pydantic schemas
├── routers/              # Endpoint routers (papers, search, conversation)
├── agents/               # LLM agents (classifier, prompt_optimizer, summariser, chat)
└── services/             # External services (openalex, pdf_parser)
```

## Build Phases & Status

Follow strictly in order. Do not skip ahead.

- [x] **Phase 1** — Project Skeleton (directory structure, venv, `.env`, health endpoint)
- [x] **Phase 2** — Database (SQLAlchemy engine, 3 models, Alembic migration)
- [x] **Phase 3** — Papers CRUD (Pydantic schemas, 5 endpoints, register router)
- [x] **Phase 4** — OpenAlex Integration (API client, semantic search, `/search` endpoint)
- [x] **Phase 5+6** — Classifier + Optimiser Agent (combined Gemini agent: field classification + query optimisation, wired into search pipeline)
- [ ] **Phase 7** — Search Sessions (session schemas, GET endpoints for past sessions)
- [ ] **Phase 8** — PDF Parser (PyMuPDF extraction, graceful fallback to abstract)
- [ ] **Phase 9** — Summarisation Agent (structured summary, `POST /papers/{id}/summary`)
- [ ] **Phase 10** — Chat Agent (conversation history, chat CRUD endpoints)

## Key Commands

```bash
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
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
- **Never commit** `.env` or `deepresearch.db`

## Workflow Rules

1. Follow build phases in order — never skip ahead
2. Commit after each completed phase with a descriptive message
3. Confirm what was built and what to test before moving on
4. Ask before making architectural decisions not in the brief
5. See `DEEPRESEARCH_CLAUDE_CODE_BRIEF.md` for full specs (models, endpoints, agent prompts)
6. **Validate after every implementation** — after building any feature, run the server and test ALL existing endpoints end-to-end (not just the new ones). Confirm correct responses, error handling, and that nothing is broken before moving on.

## Quality Bar — Targeting 90-100 (Outstanding)

The code-related marks break down as:

**API Functionality & Implementation (25/75)**
- All 10 phases fully implemented and working end-to-end
- Full CRUD on Papers with database integration
- Multi-agent search pipeline (classify → optimise → search)
- Search session persistence and retrieval
- PDF parsing with graceful fallback
- AI summarisation with structured output
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
- Novel agentic pipeline (4 LLM agents working together)
- Integration of contemporary technologies (Gemini, OpenAlex, PyMuPDF)
- Originality in how agents compose (classify → optimise → search → summarise → chat)

## What NOT to Build

- Authentication / API key protection
- Rate limiting
- Frontend / UI
- Citation graph / recommendations
- User accounts
- Docker
- Deployment (local execution is sufficient for top marks)
