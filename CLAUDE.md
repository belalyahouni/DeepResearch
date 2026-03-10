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

## LLM Models

| Agent | Model |
|---|---|
| Classifier + Optimiser | `gemini-2.5-flash-lite` |
| Summariser | `gemini-2.5-pro` |
| Chat | `gemini-2.5-flash` |

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
| POST | `/papers/{id}/chat` | Send chat message about paper (201) |
| GET | `/papers/{id}/chat` | Get conversation history |
| DELETE | `/papers/{id}/chat` | Clear conversation (204) |

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
- **One responsibility per file** — modular structure
- **Type hints** on all functions
- **Pydantic schemas** for all request/response validation
- **Wrap Gemini/external calls** in try/except — graceful fallback on failure
- **Proper HTTP status codes** — 200, 201, 204, 404, 409, 422, 500
- **Never commit** `.env` or `deepresearch.db`

## Testing

- Run `pytest tests/ -v` after every change — 0 failures allowed
- Tests use in-memory SQLite and mock all external APIs (Gemini, OpenAlex)
- Cover: happy path, invalid input (422), not found (404), external failure (500), graceful fallback
- 42 tests across 6 test files

## Quality Bar — Targeting 90-100

- All endpoints working end-to-end with proper error handling
- Swagger UI with descriptions on all endpoints — export to PDF for submission
- Descriptive commits with visible incremental history
- README.md with setup instructions (**required**)
- Novel 3-agent pipeline: classify + optimise → search → summarise → chat

## Submission TODO

All core API functionality is complete (42 tests passing). Remaining work is polish, documentation, and presentation.

### Code & API (do first)
- [ ] **README.md** — project overview, setup instructions, endpoint summary, how to run tests. Pass/fail gate.
- [ ] **Swagger polish** — add descriptions, parameter docs, example requests/responses, and error codes to all endpoints
- [ ] **Export Swagger to PDF** — save `openapi.json` + exported PDF to repo
- [ ] **Frontend** — simple UI for demo and presentation (search, save, library, chat)

### Written Deliverables
- [ ] **Technical report** (max 5 pages) — stack justification, architecture, testing approach, limitations, GenAI declaration
- [ ] **GenAI conversation logs** — export and include Claude conversation examples
- [ ] **Presentation slides** (PowerPoint, 5 min) — version control, API docs, technical highlights, live demo plan

### Submission Checklist (pass/fail gates)
- [ ] Public GitHub repo with visible commit history
- [ ] README.md present
- [ ] API documentation exported as PDF
- [ ] Technical report with GenAI declaration
- [ ] Code runs locally (`uvicorn app.main:app --reload`)
- [ ] All tests pass (`pytest tests/ -v`)

### What NOT to Build
- Auth, rate limiting, Docker, deployment
- Citation graph, recommendations, user accounts
