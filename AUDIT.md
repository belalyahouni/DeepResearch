# DeepResearch — Full Marking Audit (Code Only)

Audit date: 10 March 2026
Based on: COMP3011 Coursework 1 Brief marking criteria (pages 11–15)

Marks are cumulative — to score 90+ you must satisfy EVERY band below.

---

## BAND 40–49 (Pass) — ALL ACHIEVED

| Requirement | Status | Evidence |
|---|---|---|
| Working CRUD operations with database | DONE | `POST/GET/PUT/DELETE /papers` — full CRUD on `Paper` model via SQLAlchemy async ORM, SQLite DB |
| At least 4 API endpoints via HTTP | DONE | 9 endpoints total: `/health`, `/search`, `/summarise`, 5x `/papers`, `/papers/{id}/related` |
| Handle user inputs, return JSON responses | DONE | All endpoints accept/return JSON, Pydantic validation on all request bodies |
| Correct HTTP status/error codes | DONE | 200, 201, 204, 404, 409, 422, 500 — all used correctly per convention |
| Demonstrable via local execution | DONE | `uvicorn app.main:app --reload` works |
| Commit history visible | DONE | Multiple descriptive commits on `main` branch |
| GenAI used (even if unsystematic) | DONE | Claude used throughout development |

**Nothing to do for this band.**

---

## BAND 50–59 (Satisfactory) — 1 GAP

| Requirement | Status | Detail |
|---|---|---|
| Complete API with documentation | DONE | Swagger UI at `/docs` with descriptions, examples, and error codes on all 9 endpoints |
| **Basic authentication present** | DONE | API key auth via `X-API-Key` header, `app/auth.py`, timing-safe comparison with `secrets.compare_digest`. See `AUTHENTICATION.md` |
| Demonstrates understanding of architecture | DONE | 4-agent pipeline (classifier + summariser + chat + related papers), modular routers/schemas/models/services/agents |
| Clear technical report | N/A (non-code) | — |
| Regular commit history | DONE | Multiple commits with descriptive messages |
| **Hosted on external web server** | NOT DONE | No deployment config. Spec says "e.g. PythonAnywhere". No Docker, no Procfile, no deployment files |

### What needs to be built:
1. **Deployment to PythonAnywhere** (or similar) — the spec explicitly says "Hosted on an external web server, e.g. PythonAnywhere" at the 50-59 band, and "Professional deployment" at 70-79. This means the API must be accessible online, not just locally.

---

## BAND 60–69 (Good) — ALL ACHIEVED

| Requirement | Status | Detail |
|---|---|---|
| Well-documented API with authentication | DONE | Swagger UI with descriptions, examples, error codes on all endpoints. API key auth via `X-API-Key` header |
| Effective error handling | DONE | All endpoints have try/except, graceful fallbacks on Gemini/PDF failure, proper HTTP codes for all error cases |
| Clear stack choice justification | N/A (report) | — |
| Evidence of testing approach | DONE | 38 tests across 6 files, in-memory SQLite, mocked externals |
| Consistent version control | DONE | Regular commits with descriptive messages |
| GenAI used methodologically | DONE | Claude used as primary development tool |

**Nothing to do for this band.**

---

## BAND 70–79 (Very Good) — 2 GAPS

| Requirement | Status | Detail |
|---|---|---|
| Clean, modular code design | DONE | `app/routers/`, `app/schemas/`, `app/models/`, `app/agents/`, `app/services/` — one responsibility per file, type hints on everything, async throughout |
| **Advanced features, e.g. MCP-compatible** | DONE | MCP server (`mcp_server.py`) exposes 7 tools and 2 resources for Claude Desktop via stdio transport. Reuses existing agents, services, and database |
| Comprehensive documentation | DONE | README.md with setup instructions, Swagger UI polished with examples and error codes, OpenAPI spec exported as PDF (`docs/openapi.pdf`) |
| Strong version-control discipline | DONE | Descriptive commit messages, incremental history |
| Thorough testing demonstrated | DONE | 38 tests covering: happy path, invalid input (422), not found (404), external failure (500), graceful fallback, auth (401), edge cases (duplicates, empty results) |
| Professional deployment | NOT DONE | See 50-59 above |
| Medium-level GenAI use | DONE | — |

---

## BAND 80–89 (Excellent) — ALL ACHIEVED

| Requirement | Status | Detail |
|---|---|---|
| Exemplary code quality and architecture | DONE | Clean separation of concerns, async throughout, type hints everywhere, Pydantic validation, SQLAlchemy ORM with mapped columns, graceful error handling patterns |
| **Advanced security implementation** | DONE | API key auth with timing-safe comparison (`secrets.compare_digest`), CORS middleware with restricted origins/methods/headers, Trusted Host middleware. See `AUTHENTICATION.md` |
| Comprehensive testing suite | DONE | 38 tests, all external APIs mocked, covers happy path + error cases + edge cases + graceful degradation + auth (401) |
| Creative data design | DONE | 4-agent LLM pipeline (classify→optimise→search→summarise→chat→related), PDF extraction, MCP server for Claude Desktop |
| Excellent documentation | DONE | README.md, Swagger UI with examples and error codes, OpenAPI PDF export |
| High-level GenAI use | DONE | — |

**Nothing to do for this band.**

---

## BAND 90–100 (Outstanding) — MOSTLY ACHIEVED

| Requirement | Status | Detail |
|---|---|---|
| Exceptional originality and innovation | DONE | 4-agent LLM pipeline is genuinely novel — classify/optimise queries with one model, summarise with another, chat with a third, discover related papers with a fourth. PDF extraction + automatic summarisation on save. Multi-turn conversation with history and limits |
| **Novel data integration or features** | DONE | Uses OpenAlex API (250M+ works), agent-powered related papers discovery via `GET /papers/{id}/related` |
| **Publication-quality documentation** | DONE | README.md with setup instructions, Swagger UI polished with examples and error codes, OpenAPI spec exported as PDF (`docs/openapi.pdf`) |
| Demonstrates genuine research curiosity | DONE | The entire project concept (agentic research assistant) demonstrates this |
| **Creative application of GenAI** | DONE | 4 Gemini agents for 4 different tasks, structured JSON output from classifier, graceful fallback chains |

**Nothing to do for this band.**

---

## PASS/FAIL GATES (instant fail without these)

| Gate | Status | Action |
|---|---|---|
| Public GitHub repo with visible commit history | DONE | — |
| **README.md present** | DONE | Includes setup instructions, endpoint summary, testing instructions |
| **API documentation exported as PDF** | DONE | `docs/openapi.json` + `docs/openapi.pdf` in repo |
| **Technical report with GenAI declaration** | N/A (non-code) | Written deliverable |
| Code runs locally | DONE | — |
| All tests pass | DONE | 38/38 passing |

---

## SUMMARY: WHAT'S LEFT TO BUILD (code only, priority order)

### Remaining Gaps
1. **Deployment** — host on PythonAnywhere or similar (50-59, 70-79 bands)
2. **Frontend** — simple UI for demo and presentation (search, save, library)

### Written Deliverables (non-code)
4. **Technical report** (max 5 pages) — stack justification, architecture, testing approach, limitations, GenAI declaration
5. **Presentation slides** (PowerPoint, 5 min) — version control, API docs, technical highlights, live demo plan
6. **GenAI conversation logs** — export and include Claude conversation examples

### Current Codebase Strengths (already scoring well)
- Clean modular architecture (routers/schemas/models/agents/services)
- Full CRUD with proper status codes
- 4-agent LLM pipeline (novel, creative)
- 38 tests with comprehensive coverage
- Async throughout, type hints everywhere
- Graceful error handling and fallback chains
- PDF extraction with fallback
- Pydantic validation on all inputs
- API key auth + CORS + Trusted Host security
- README.md + Swagger polish + OpenAPI PDF export
- Related papers discovery (agent-powered semantic search)
- MCP server for Claude Desktop (7 tools + 2 resources)
