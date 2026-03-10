# DeepResearch API — Claude Code Project Brief

## Overview

You are helping build **DeepResearch API**, an agentic research assistant API that allows users to discover, save, and interact with academic research papers. This is a university coursework project (FastAPI + SQLite + Gemini + OpenAlex).

The approach is **feature-by-feature MVP**. Each feature is built, tested, and validated before moving on.

---

## Tech Stack

| Component | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ | |
| Framework | FastAPI | Auto-generates Swagger UI at `/docs` |
| Database | SQLite | Via SQLAlchemy ORM, file-based, zero setup |
| Migrations | Alembic | For DB schema versioning |
| LLM | Google Gemini (`google-genai` SDK) | See model table below |
| Paper Retrieval | OpenAlex API | Free key, semantic search (beta) |
| PDF Parsing | PyMuPDF (`fitz`) | For extracting full text from open access PDFs |
| HTTP Client | `httpx` | Async HTTP requests |
| Environment | `python-dotenv` | For `.env` file loading |
| Testing | pytest + pytest-asyncio | In-memory SQLite, mocked external APIs |
| OS | macOS | Developer is on macOS |

### LLM Model Strategy

| Agent | Model | Rationale |
|---|---|---|
| Query Intelligence (classify + optimise) | `gemini-2.5-flash-lite` | Simple structured task, needs to be fast, runs on every search |
| Summariser | `gemini-2.5-pro` | Complex task — reading full PDF, producing structured output, quality matters |
| Chat | `gemini-2.5-flash` | Balanced — conversational but needs to reason about paper content |

---

## User Workflow

1. **Search** — user searches for a topic → query is classified + optimised by Gemini → semantic search via OpenAlex returns top results
2. **Preview** — user can request a summary of any search result to check relevance before saving
3. **Save** — user saves interesting papers to their library (summary is stored on the Paper model so it persists)
4. **Library** — user views all saved papers with summaries, tags, and notes
5. **Deep dive** — user selects a saved paper → full PDF text loaded → multi-turn chat with LLM about the paper + user can add notes

---

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
│   ├── search.py                    # GET /search — full agent pipeline
│   └── conversation.py              # Chat endpoints (Phase 9)
├── agents/
│   ├── classifier_optimiser.py      # Query Intelligence: field classification + query optimisation
│   ├── summariser.py                # Paper summarisation (Phase 8)
│   └── chat.py                      # Conversational chat (Phase 9)
└── services/
    ├── openalex.py                  # OpenAlex API client (semantic + keyword search)
    └── pdf_parser.py                # PDF text extraction (Phase 7)
tests/
├── conftest.py                      # Fixtures: in-memory DB, async test client
├── test_health.py                   # Health endpoint test
├── test_papers.py                   # 13 tests: full CRUD + edge cases
├── test_search.py                   # 5 tests: pipeline, validation, errors, fallback
├── test_pdf_parser.py               # PDF parser tests (Phase 7)
├── test_summariser.py               # Summariser tests (Phase 8)
└── test_chat.py                     # Chat tests (Phase 9)
```

---

## Environment Variables

`.env` file (provide this to examiner):
```
GEMINI_API_KEY=your_gemini_api_key_here
OPEN_ALEX_API_KEY=your_openalex_api_key_here
```

`.env.example` (commit this to GitHub):
```
GEMINI_API_KEY=
OPEN_ALEX_API_KEY=
```

---

## Database Models

### Paper
Stores papers the user has explicitly saved to their library.

```
id: int (primary key)
openalex_id: str (unique, from OpenAlex)
title: str
authors: str (comma-separated)
abstract: str (nullable)
year: int (nullable)
url: str (nullable)
open_access_pdf_url: str (nullable)
citation_count: int (default 0)
tags: str (nullable, comma-separated user tags)
notes: str (nullable, user notes)
summary: str (nullable, AI-generated summary — stored so it's only generated once)
created_at: datetime
updated_at: datetime
```

### Conversation
Stores chat history for a specific saved paper.

```
id: int (primary key)
paper_id: int (foreign key → Paper)
role: str ("user" or "assistant")
message: str
created_at: datetime
```

---

## API Endpoints

### Papers (CRUD) — IMPLEMENTED

| Method | Endpoint | Operation | Description |
|---|---|---|---|
| POST | `/papers` | **Create** | Save a paper to library (409 if duplicate) |
| GET | `/papers` | **Read** | List all saved papers (supports `?tags=` filter) |
| GET | `/papers/{id}` | **Read** | Get a specific saved paper |
| PUT | `/papers/{id}` | **Update** | Update notes, tags, or summary on a paper |
| DELETE | `/papers/{id}` | **Delete** | Remove a paper from library |

### Search — IMPLEMENTED

| Method | Endpoint | Description |
|---|---|---|
| GET | `/search?query=...` | Full agent pipeline: classify → optimise → semantic search. Returns agent metadata + results |

Search response format:
```json
{
  "original_query": "how do transformers handle long sequences",
  "field_id": 17,
  "field": "Computer Science",
  "optimised_query": "Transformer models for long sequence processing",
  "result_count": 10,
  "results": [...]
}
```

### Summarisation — Phase 8

| Method | Endpoint | Description |
|---|---|---|
| POST | `/papers/{id}/summary` | Generate AI summary of a saved paper. Parses PDF (or falls back to abstract), generates structured summary via Gemini, stores result on Paper. Returns cached summary if already generated. |

### Conversation (per saved paper) — Phase 9

| Method | Endpoint | Description |
|---|---|---|
| POST | `/papers/{id}/chat` | Send a message about a saved paper |
| GET | `/papers/{id}/chat` | Get full conversation history for a paper |
| DELETE | `/papers/{id}/chat` | Clear conversation history for a paper |

### Utility

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check — IMPLEMENTED |

---

## Implementation Status

### Done
- **Phase 1** — Project skeleton, venv, `.env`, health endpoint
- **Phase 2** — Database: async SQLAlchemy, 2 models (Paper, Conversation), Alembic migration
- **Phase 3** — Papers CRUD: 5 endpoints with Pydantic schemas, tag filtering, duplicate detection
- **Phase 4** — OpenAlex integration: semantic search (AI embeddings) + keyword fallback
- **Phase 5+6** — Combined Query Intelligence agent: Gemini classifies into OpenAlex field + optimises query for semantic search
- **Test suite** — 19 tests (pytest), in-memory DB, mocked external APIs

### Remaining

- **Phase 7** — PDF Parser
- **Phase 8** — Summariser Agent + `summary` field on Paper
- **Phase 9** — Chat Agent + conversation endpoints

---

## Phase 7 — PDF Parser

**Goal:** Extract full text from open access PDFs so the summariser and chat agents have real paper content to work with.

### What to build
- `app/services/pdf_parser.py` — async service that:
  1. Takes a PDF URL (from `paper.open_access_pdf_url`)
  2. Downloads the PDF via `httpx` (async, with timeout)
  3. Extracts full text using PyMuPDF (`fitz`)
  4. Returns the extracted text as a string
- Graceful fallback: if the PDF URL is `None`, download fails, or parsing fails → return `None` (callers fall back to abstract)

### Implementation details
- Use `httpx.AsyncClient` with a reasonable timeout (30s)
- Write PDF bytes to a temporary file, open with `fitz.open()`, iterate pages, extract text
- Clean up temp file after extraction
- Wrap everything in try/except — never let PDF failures crash the API

### Tests (`tests/test_pdf_parser.py`)
- Mock `httpx` responses (don't download real PDFs in tests)
- Test: successful extraction returns text
- Test: `None` URL returns `None`
- Test: download failure (HTTP error) returns `None`
- Test: corrupt/unparseable PDF returns `None`

---

## Phase 8 — Summariser Agent

**Goal:** Generate structured AI summaries of saved papers using Gemini, with summaries persisted on the Paper model.

### What to build

#### 1. Add `summary` column to Paper model
- Add `summary: Mapped[str | None] = mapped_column(String, nullable=True)` to `app/models/paper.py`
- Create new Alembic migration to add the column
- Update `PaperResponse` schema to include `summary`

#### 2. Summariser agent (`app/agents/summariser.py`)
- Uses `gemini-2.5-pro`
- System prompt:
  ```
  You are an expert academic paper summariser. Given the text of a research
  paper, produce a structured summary with these sections:
  - Key Findings (2-3 sentences)
  - Methodology (1-2 sentences)
  - Main Contributions (bullet points)
  - Limitations (1-2 sentences)
  Be concise and precise.
  ```
- Input: paper text (full PDF text from Phase 7, or abstract as fallback)
- Output: structured markdown summary string

#### 3. Endpoint: `POST /papers/{id}/summary`
- If `paper.summary` already exists → return it immediately (cached)
- Otherwise:
  1. Use PDF parser to extract full text from `paper.open_access_pdf_url`
  2. If PDF extraction fails or URL is `None` → fall back to `paper.abstract`
  3. If neither available → return 422 with message "No content available to summarise"
  4. Call summariser agent with the text
  5. Store the summary on `paper.summary` in the DB
  6. Return the summary
- Error handling: if Gemini fails → return 500 with meaningful error

### Tests (`tests/test_summariser.py`)
- Mock Gemini API responses
- Mock PDF parser
- Test: successful summary generation + stored on paper
- Test: cached summary returned without calling Gemini again
- Test: fallback to abstract when no PDF
- Test: 404 when paper not found
- Test: 422 when no content available (no PDF, no abstract)
- Test: 500 when Gemini fails

---

## Phase 9 — Chat Agent

**Goal:** Multi-turn conversational chat about a specific saved paper, backed by DB-stored conversation history.

### What to build

#### 1. Chat agent (`app/agents/chat.py`)
- Uses `gemini-2.5-flash`
- System prompt:
  ```
  You are a research assistant helping a user understand a specific academic
  paper. You have access to the full paper text. Answer questions accurately,
  cite specific sections when relevant, and acknowledge when something is not
  covered in the paper. Be concise but thorough.
  ```
- Input: paper context (full PDF text or abstract) + full conversation history from DB + new user message
- Output: assistant response string

#### 2. Chat router (`app/routers/conversation.py`)

**POST `/papers/{id}/chat`**
- Request body: `{ "message": "string" }`
- Flow:
  1. Verify paper exists (404 if not)
  2. Load paper text (PDF parser → fallback to abstract)
  3. Load full conversation history from DB for this paper
  4. Save the new user message to DB
  5. Call chat agent with paper text + history + new message
  6. Save assistant response to DB
  7. Return `{ "role": "assistant", "message": "..." }`
- Error handling: if Gemini fails → return 500 (but user message is already saved)

**GET `/papers/{id}/chat`**
- Returns full conversation history for the paper
- Response: `{ "paper_id": int, "messages": [{ "role": "...", "message": "...", "created_at": "..." }, ...] }`
- 404 if paper not found

**DELETE `/papers/{id}/chat`**
- Clears all conversation messages for the paper
- Returns 204 No Content
- 404 if paper not found

#### 3. Register router in `app/main.py`

### Tests (`tests/test_chat.py`)
- Mock Gemini API responses
- Mock PDF parser
- Test: send message and get response
- Test: conversation history builds up correctly (multi-turn)
- Test: GET returns full history
- Test: DELETE clears history
- Test: 404 when paper not found (POST, GET, DELETE)
- Test: 500 when Gemini fails (user message still saved)

---

## Agent Specifications

### Query Intelligence Agent (classify + optimise) — `gemini-2.5-flash-lite` — IMPLEMENTED

Runs on every search. Classifies query into one of 26 OpenAlex fields and rewrites it for semantic search.

```
System prompt: See app/agents/classifier_optimiser.py

Input: raw query string
Output: JSON {"field_id": <int>, "field": "<name>", "optimised_query": "<rewritten>"}

Fallback: if Gemini fails, returns original query with no field filter
```

Note: OpenAlex semantic search does not support `topics.field.id` filter, so the field is returned in the response metadata but not used for filtering in semantic mode. Field filter is applied only in keyword search mode.

### Summariser Agent — `gemini-2.5-pro` — Phase 8

```
System prompt:
"You are an expert academic paper summariser. Given the text of a research
paper, produce a structured summary with these sections:
- Key Findings (2-3 sentences)
- Methodology (1-2 sentences)
- Main Contributions (bullet points)
- Limitations (1-2 sentences)
Be concise and precise."

Input: paper text (full PDF text via PyMuPDF, or abstract as fallback)
Output: structured markdown summary
```

### Chat Agent — `gemini-2.5-flash` — Phase 9

```
System prompt:
"You are a research assistant helping a user understand a specific academic
paper. You have access to the full paper text. Answer questions accurately,
cite specific sections when relevant, and acknowledge when something is not
covered in the paper. Be concise but thorough."

Input: paper context + full conversation history from DB + new user message
Output: assistant response string
```

---

## Key Implementation Notes

- **Always use async** FastAPI endpoints and async SQLAlchemy
- **Never commit** `.env` or `deepresearch.db` to GitHub
- **Error handling**: all endpoints return appropriate HTTP status codes (200, 201, 204, 404, 409, 422, 500)
- **Gemini calls**: wrap in try/except, graceful fallback on failure
- **OpenAlex calls**: use API key from `.env`, semantic search requires key
- **PDF parsing**: always fall back to abstract if PDF unavailable or parsing fails
- **Summary caching**: store on Paper model, only generate once per paper
- **Conversation context**: load ALL previous messages for the paper from DB
- **Search output matches Paper schema**: search results can be directly posted to `POST /papers`
- **Testing**: run `pytest tests/ -v` after every change, all tests must pass before moving on

---

## Running the App

```bash
# Clone and setup
git clone <repo>
cd research-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Add API keys to .env
cp .env.example .env
# Edit .env and add your keys

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v

# Open Swagger UI
open http://localhost:8000/docs
```

---

## What NOT to Build

- Authentication / API key protection for your own API
- Rate limiting
- Frontend / UI
- Citation graph features
- Paper recommendations
- User accounts
- Docker
- Deployment (local execution is sufficient for top marks)

---

## Coursework Context

- Module: COMP3011 Web Services and Web Data, University of Leeds
- Submission deadline: 13 March 2026
- Oral exam: week of 23 March 2026
- GenAI use must be declared — log all Claude conversations
- GitHub must have visible commit history
- Swagger UI auto-generated by FastAPI satisfies the API documentation requirement (export to PDF for submission)
- Technical report: max 5 pages, justify stack choices, reflect on challenges

---

## Instructions for Claude Code

1. **Read this entire brief before writing any code**
2. **Follow the remaining phases in order** — do not skip ahead
3. **After each phase**, confirm what was built and what to test before moving on
4. **Run `pytest tests/ -v` after every implementation** — all tests must pass
5. **Commit after each phase** with a descriptive commit message
6. **Ask before making architectural decisions** not covered in this brief
7. **Keep code modular** — one responsibility per file
8. The developer will continue to converse with you after each phase to guide direction
