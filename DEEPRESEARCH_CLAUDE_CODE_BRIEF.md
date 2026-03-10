# DeepResearch API — Claude Code Project Brief

## Overview

You are helping build **DeepResearch API**, an agentic research assistant API that allows users to discover, save, and interact with academic research papers. This is a university coursework project (FastAPI + SQLite + Gemini + OpenAlex).

The approach is **MVP first, then iterate**. Follow the build order in this document strictly. Do not jump ahead to later phases until the current phase is working and tested.

---

## Tech Stack

| Component | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ | |
| Framework | FastAPI | Auto-generates Swagger UI at `/docs` |
| Database | SQLite | Via SQLAlchemy ORM, file-based, zero setup |
| Migrations | Alembic | For DB schema versioning |
| LLM | Google Gemini (`google-genai` SDK) | See model table below |
| Paper Retrieval | OpenAlex API | Free key, semantic search built in |
| PDF Parsing | PyMuPDF (`fitz`) | For extracting full text from open access PDFs |
| HTTP Client | `httpx` | Async HTTP requests |
| Environment | `python-dotenv` | For `.env` file loading |
| OS | macOS | Developer is on macOS |

### LLM Model Strategy

| Agent | Model | Rationale |
|---|---|---|
| Query Intelligence (classify + optimise) | `gemini-2.5-flash-lite` | Simple structured task, needs to be fast, runs on every search |
| Summariser | `gemini-2.5-pro` | Complex task — reading full PDF, producing structured output, quality matters |
| Chat | `gemini-2.5-flash` | Balanced — conversational but needs to reason about paper content |

---

## Project Structure

```
deepresearch-api/
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI app entry point
│   ├── database.py           # SQLAlchemy engine + session
│   ├── models/
│   │   ├── __init__.py
│   │   ├── paper.py          # Paper model
│   │   ├── search_session.py # SearchSession model
│   │   └── conversation.py   # Conversation model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── paper.py          # Pydantic schemas for Paper
│   │   ├── search_session.py # Pydantic schemas for SearchSession
│   │   └── conversation.py   # Pydantic schemas for Conversation
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── papers.py         # CRUD endpoints for papers
│   │   ├── search.py         # Search pipeline endpoint
│   │   └── conversation.py   # Chat endpoints
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── classifier.py     # Topic classification agent
│   │   ├── prompt_optimizer.py # Query refinement agent
│   │   ├── summariser.py     # Paper summarisation agent
│   │   └── chat.py           # Conversational chat agent
│   └── services/
│       ├── __init__.py
│       ├── openalex.py # OpenAlex API client
│       └── pdf_parser.py     # PDF text extraction
├── alembic/                  # DB migrations
├── .env                      # API keys (never commit this)
├── .env.example              # Template with empty keys
├── .gitignore
├── requirements.txt
├── README.md
└── deepresearch.db           # SQLite file (auto-created, never commit)
```

---

## Environment Variables

`.env` file (provide this to examiner):
```
GEMINI_API_KEY=your_gemini_api_key_here
OPEN_ALEX_API_KEY=your_semantic_scholar_api_key_here
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
created_at: datetime
updated_at: datetime
```

### SearchSession
Stores each search the user performs, including how agents transformed the query.

```
id: int (primary key)
original_query: str
topic_category: str (nullable, from classifier agent)
refined_query: str (nullable, from prompt optimizer agent)
result_count: int
created_at: datetime
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

### Papers (CRUD)

| Method | Endpoint | Operation | Description |
|---|---|---|---|
| POST | `/papers` | **Create** | Save a paper to library |
| GET | `/papers` | **Read** | List all saved papers (supports ?tags= filter) |
| GET | `/papers/{id}` | **Read** | Get a specific saved paper |
| PUT | `/papers/{id}` | **Update** | Update notes or tags on a paper |
| DELETE | `/papers/{id}` | **Delete** | Remove a paper from library |

### Search

| Method | Endpoint | Description |
|---|---|---|
| POST | `/search` | Run full agent pipeline and return results |
| GET | `/search/sessions` | List past search sessions |
| GET | `/search/sessions/{id}` | Get a specific session and its results |

### Conversation (per saved paper)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/papers/{id}/chat` | Send a message about a saved paper |
| GET | `/papers/{id}/chat` | Get full conversation history for a paper |
| DELETE | `/papers/{id}/chat` | Clear conversation history for a paper |

### Utility

| Method | Endpoint | Description |
|---|---|---|
| POST | `/papers/{id}/summary` | Generate and return AI summary of a saved paper |
| GET | `/health` | Health check |

---

## Build Order (MVP First — Follow This Strictly)

### Phase 1 — Project Skeleton
1. Create the project directory structure
2. Set up `requirements.txt` and virtual environment
3. Create `.env`, `.env.example`, `.gitignore`
4. Create `app/main.py` with basic FastAPI app and `/health` endpoint
5. Verify it runs: `uvicorn app.main:app --reload`

### Phase 2 — Database
1. Set up `app/database.py` with SQLAlchemy engine pointing to `deepresearch.db`
2. Create all three models in `app/models/`
3. Set up Alembic and create initial migration
4. Run migration to create tables
5. Verify tables exist in SQLite

### Phase 3 — Papers CRUD (Core Requirement)
1. Create Pydantic schemas for Paper in `app/schemas/paper.py`
2. Build all 5 CRUD endpoints in `app/routers/papers.py`
3. Register router in `main.py`
4. Test all endpoints via Swagger UI at `http://localhost:8000/docs`
5. Verify Create, Read, Update, Delete all work correctly

### Phase 4 — OpenAlex Integration
1. Build `app/services/openalex.py` client
2. Key method: `search_papers(query: str, limit: int, fields_of_study: list) -> list`
3. Returns: title, authors, abstract, year, url, open_access_pdf_url, citation_count, openalex_id
4. Test the client in isolation first (simple script or test)
5. Build basic `/search` endpoint that calls OpenAlex directly (no agents yet)
6. Verify search returns real papers

### Phase 5 — Classifier Agent (First Agent)
1. Build `app/agents/classifier.py` using Gemini 2.5 Flash
2. Input: raw user query string
3. Output: topic category string (e.g. "machine learning", "computer vision", "NLP")
4. Use this category to filter OpenAlex search by field of study
5. Wire into `/search` endpoint: query → classify → search
6. Test end-to-end

### Phase 6 — Prompt Optimiser Agent (Second Agent)
1. Build `app/agents/prompt_optimizer.py` using Gemini 2.5 Flash
2. Input: raw user query string + topic category
3. Output: refined academic search query string
4. Wire into `/search` endpoint: query → classify → optimise → search
5. Store original_query, topic_category, refined_query in SearchSession
6. Test end-to-end, compare search results with/without optimisation

### Phase 7 — Search Sessions
1. Create Pydantic schemas for SearchSession
2. Build `GET /search/sessions` and `GET /search/sessions/{id}` endpoints
3. Every `/search` call saves a SearchSession to DB
4. Test retrieval of past sessions

### Phase 8 — PDF Parser
1. Build `app/services/pdf_parser.py` using PyMuPDF
2. Input: PDF URL (open access URL from OpenAlex)
3. Output: extracted text string (first N pages or full)
4. Handle cases where PDF is unavailable gracefully (fall back to abstract)
5. Test with a real open access paper URL

### Phase 9 — Summarisation Agent (Third Agent)
1. Build `app/agents/summariser.py` using Gemini 2.5 Flash
2. Input: paper text (full PDF text if available, abstract as fallback)
3. Output: structured summary (key findings, methodology, contributions, limitations)
4. Build `POST /papers/{id}/summary` endpoint
5. Test on a saved paper that has an open access PDF

### Phase 10 — Chat Agent (Fourth Agent)
1. Build `app/agents/chat.py` using Gemini 2.5 Flash
2. Maintains conversation context by loading full history from DB on each call
3. Input: paper context (full PDF text or abstract) + conversation history + new user message
4. Output: assistant response string
5. Create Pydantic schemas for Conversation
6. Build `POST /papers/{id}/chat`, `GET /papers/{id}/chat`, `DELETE /papers/{id}/chat`
7. Test multi-turn conversation about a saved paper

---

## Agent Specifications

### Query Intelligence Agent (classify + optimise) — `gemini-2.5-flash-lite`
```
System prompt:
"You are an academic search assistant. Given a user's research query, you must:
1. Classify it into exactly one OpenAlex field (from 26 fields).
2. Optimise the query for semantic search — rewrite using precise academic
   terminology. Keep descriptive and natural, not a keyword list."

Input: raw query string
Output: JSON {"field_id": <int>, "field": "<name>", "optimised_query": "<rewritten>"}
```

### Summariser Agent — `gemini-2.5-pro`
```
System prompt:
"You are an expert academic paper summariser. Given the text of a research
paper, produce a structured summary with these sections:
- Key Findings (2-3 sentences)
- Methodology (1-2 sentences)
- Main Contributions (bullet points)
- Limitations (1-2 sentences)
Be concise and precise."

Input: paper text (PDF or abstract)
Output: structured markdown summary
```

### Chat Agent — `gemini-2.5-flash`
```
System prompt:
"You are a research assistant helping a user understand a specific academic
paper. You have access to the full paper text. Answer questions accurately,
cite specific sections when relevant, and acknowledge when something is not
covered in the paper. Be concise but thorough."

Input: paper context + conversation history + new message
Output: assistant response
```

---

## Key Implementation Notes

- **Always use async** FastAPI endpoints and async SQLAlchemy where possible
- **Never commit** `.env` or `deepresearch.db` to GitHub — add both to `.gitignore`
- **Error handling**: all endpoints must return appropriate HTTP status codes (404 for not found, 422 for validation errors, 500 for server errors)
- **Gemini calls**: wrap in try/except, return meaningful error messages
- **OpenAlex calls**: respect rate limits, use the API key from `.env`
- **PDF parsing**: always have an abstract fallback if PDF is unavailable or parsing fails
- **Conversation context**: for the chat agent, load ALL previous messages for the paper and pass them to Gemini as conversation history
- **SQLite**: the `deepresearch.db` file is auto-created on first run — no manual setup needed

---

## Running the App

```bash
# Clone and setup
git clone <repo>
cd deepresearch-api
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

# Open Swagger UI
open http://localhost:8000/docs
```

---

## Requirements.txt (starting point)

```
fastapi
uvicorn[standard]
sqlalchemy
alembic
pydantic
pydantic-settings
python-dotenv
httpx
google-genai
pymupdf
```

---

## What NOT to build yet (post-MVP)

- Authentication / API key protection for your own API
- Rate limiting
- Deployment to PythonAnywhere
- Frontend / UI
- Citation graph features
- Paper recommendations
- User accounts
- Docker

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
2. **Follow the build phases in order** — do not implement Phase 5 before Phase 3 is working
3. **After each phase**, confirm what was built and what to test before moving on
4. **Commit after each phase** with a descriptive commit message
5. **Ask before making architectural decisions** not covered in this brief
6. **Keep code modular** — one responsibility per file
7. The developer will continue to converse with you after each phase to guide direction
