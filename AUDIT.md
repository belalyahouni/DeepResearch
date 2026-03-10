# DeepResearch — Full Marking Audit (Code Only)

Audit date: 10 March 2026
Based on: COMP3011 Coursework 1 Brief marking criteria (pages 11–15)

Marks are cumulative — to score 90+ you must satisfy EVERY band below.

---

## BAND 40–49 (Pass) — ALL ACHIEVED

| Requirement | Status | Evidence |
|---|---|---|
| Working CRUD operations with database | DONE | `POST/GET/PUT/DELETE /papers` — full CRUD on `Paper` model via SQLAlchemy async ORM, SQLite DB |
| At least 4 API endpoints via HTTP | DONE | 11 endpoints total: `/health`, `/search`, `/summarise`, 5x `/papers`, 3x `/papers/{id}/chat` |
| Handle user inputs, return JSON responses | DONE | All endpoints accept/return JSON, Pydantic validation on all request bodies |
| Correct HTTP status/error codes | DONE | 200, 201, 204, 404, 409, 422, 500 — all used correctly per convention |
| Demonstrable via local execution | DONE | `uvicorn app.main:app --reload` works |
| Commit history visible | DONE | Multiple descriptive commits on `main` branch |
| GenAI used (even if unsystematic) | DONE | Claude used throughout development |

**Nothing to do for this band.**

---

## BAND 50–59 (Satisfactory) — 2 GAPS

| Requirement | Status | Detail |
|---|---|---|
| Complete API with documentation | DONE | Swagger UI auto-generated at `/docs`, all endpoints have docstrings |
| **Basic authentication present** | NOT DONE | No auth whatsoever — no API key, no token, no middleware. The spec mentions "basic authentication" at 50-59 and "authentication" at 60-69 |
| Demonstrates understanding of architecture | DONE | 3-agent pipeline (classifier + summariser + chat), modular routers/schemas/models/services/agents |
| Clear technical report | N/A (non-code) | — |
| Regular commit history | DONE | Multiple commits with descriptive messages |
| **Hosted on external web server** | NOT DONE | No deployment config. Spec says "e.g. PythonAnywhere". No Docker, no Procfile, no deployment files |

### What needs to be built:
1. **API key authentication** — add a simple API key middleware or dependency. Every endpoint (except maybe `/health` and `/docs`) should require an `X-API-Key` header or `?api_key=` query parameter. This is mentioned in THREE bands (50-59, 60-69, 80-89) so it's clearly important.
   - Create `app/auth.py` with a `get_api_key` dependency
   - Add it to all routers
   - Store valid API key(s) in `.env`
   - Add tests for 401/403 on missing/invalid key

2. **Deployment to PythonAnywhere** (or similar) — the spec explicitly says "Hosted on an external web server, e.g. PythonAnywhere" at the 50-59 band, and "Professional deployment" at 70-79. This means the API must be accessible online, not just locally.

---

## BAND 60–69 (Good) — MOSTLY ACHIEVED

| Requirement | Status | Detail |
|---|---|---|
| Well-documented API with authentication | PARTIAL | Swagger UI exists with docstrings, but no auth (see above). Swagger lacks example request/response bodies and detailed error code documentation |
| Effective error handling | DONE | All endpoints have try/except, graceful fallbacks on Gemini/PDF failure, proper HTTP codes for all error cases |
| Clear stack choice justification | N/A (report) | — |
| Evidence of testing approach | DONE | 42 tests across 6 files, in-memory SQLite, mocked externals |
| Consistent version control | DONE | Regular commits with descriptive messages |
| GenAI used methodologically | DONE | Claude used as primary development tool |

### What needs to be built:
1. **Swagger polish** — the spec says "Clearly describes all available endpoints, parameters, and response formats" and "Includes example requests and expected responses" and "Documents authentication process and error codes where applicable". Currently:
   - Endpoint docstrings exist but are minimal (1-line)
   - No `response_description` on any endpoint
   - No `responses={404: ..., 422: ...}` error documentation on endpoints
   - No `example` values on Pydantic schema fields
   - No `summary` vs `description` distinction on endpoints
   - Search endpoint has no `response_model` (returns raw dict)

---

## BAND 70–79 (Very Good) — 1 GAP

| Requirement | Status | Detail |
|---|---|---|
| Clean, modular code design | DONE | `app/routers/`, `app/schemas/`, `app/models/`, `app/agents/`, `app/services/` — one responsibility per file, type hints on everything, async throughout |
| **Advanced features, e.g. MCP-compatible** | NOT DONE | No MCP server. The spec explicitly calls out "advanced features, e.g. MCP-compatible" at this band. An MCP server would expose the API tools to Claude Desktop or similar |
| Comprehensive documentation | PARTIAL | Swagger UI auto-generated, but no README.md (pass/fail gate), no exported PDF |
| Strong version-control discipline | DONE | Descriptive commit messages, incremental history |
| Thorough testing demonstrated | DONE | 42 tests covering: happy path, invalid input (422), not found (404), external failure (500), graceful fallback, edge cases (message limits, duplicates, empty results) |
| Professional deployment | NOT DONE | See 50-59 above |
| Medium-level GenAI use | DONE | — |

### What needs to be built:
1. **MCP server** — create an MCP (Model Context Protocol) server that exposes the API's tools. This could be a separate file `mcp_server.py` that registers tools like `search_papers`, `save_paper`, `summarise`, `chat`. The spec explicitly mentions MCP at this band.

---

## BAND 80–89 (Excellent) — 2 GAPS

| Requirement | Status | Detail |
|---|---|---|
| Exemplary code quality and architecture | DONE | Clean separation of concerns, async throughout, type hints everywhere, Pydantic validation, SQLAlchemy ORM with mapped columns, graceful error handling patterns |
| **Advanced security implementation** | NOT DONE | No auth (see above), no CORS configuration in `main.py`, no input sanitisation beyond Pydantic, no rate limiting headers. The spec says "Advanced security implementation" which goes beyond basic auth — think CORS, request validation, security headers |
| Comprehensive testing suite | DONE | 42 tests, all external APIs mocked, covers happy path + error cases + edge cases + graceful degradation |
| Creative data design | DONE | 3-agent LLM pipeline (classify→optimise→search→summarise→chat), PDF extraction, multi-turn conversation with history |
| Excellent documentation | PARTIAL | See gaps above |
| High-level GenAI use | DONE | — |

### What needs to be built:
1. **CORS middleware** — add `CORSMiddleware` to `main.py`. Required both for security (80-89 band) and for the frontend to work.
2. **Security hardening** — beyond auth:
   - CORS with specific allowed origins
   - Consider adding request size limits
   - The Pydantic validation already handles input validation well

---

## BAND 90–100 (Outstanding) — 3 GAPS

| Requirement | Status | Detail |
|---|---|---|
| Exceptional originality and innovation | DONE | 3-agent LLM pipeline is genuinely novel — classify/optimise queries with one model, summarise with another, chat with a third. PDF extraction + automatic summarisation on save. Multi-turn conversation with history and limits |
| **Novel data integration or features** | PARTIAL | Uses OpenAlex API (good), but could be strengthened with additional data sources or analytics features. Ideas: citation network data from OpenAlex, related papers endpoint, paper similarity, usage analytics |
| **Publication-quality documentation** | NOT DONE | No README.md (pass/fail gate!), no API PDF export, Swagger needs polish (see 60-69) |
| Demonstrates genuine research curiosity | DONE | The entire project concept (agentic research assistant) demonstrates this |
| **Creative application of GenAI** | DONE | 3 different Gemini models for 3 different tasks, structured JSON output from classifier, graceful fallback chains |

### What needs to be built:
1. **README.md** — CRITICAL pass/fail gate. Must include: project overview, setup instructions, endpoint summary, how to run tests. Without this, the entire submission fails regardless of marks elsewhere.
2. **API documentation PDF** — CRITICAL pass/fail gate. Export OpenAPI spec and/or Swagger UI to PDF. Must be in the repo and referenced in README.
3. **Novel feature addition** — to truly hit 90+, consider adding something like:
   - `GET /papers/{id}/related` — fetch related papers from OpenAlex using the saved paper's concepts
   - Analytics endpoint — citation trends, field distribution of saved papers
   - Export endpoint — export saved papers as BibTeX or CSV

---

## PASS/FAIL GATES (instant fail without these)

| Gate | Status | Action |
|---|---|---|
| Public GitHub repo with visible commit history | DONE | — |
| **README.md present** | NOT DONE | Must create with setup instructions and project overview |
| **API documentation exported as PDF** | NOT DONE | Must export and add to repo |
| **Technical report with GenAI declaration** | N/A (non-code) | Written deliverable |
| Code runs locally | DONE | — |
| All tests pass | DONE | 42/42 passing |

---

## SUMMARY: WHAT TO BUILD (code only, priority order)

### Critical (pass/fail gates)
1. **README.md** — project overview, setup, endpoints, how to test
2. **API docs PDF** — export OpenAPI spec to PDF, add to repo

### High Priority (covers 50-59 through 80-89 bands)
3. **API key authentication** — `app/auth.py`, dependency on all endpoints, `.env` config, tests
4. **CORS middleware** — add to `main.py`
5. **Swagger polish** — example values on schemas, error response docs on endpoints, response models on all endpoints
6. **Deployment** — host on PythonAnywhere or similar

### Medium Priority (strengthens 70-79 and 90-100)
7. **MCP server** — expose API tools via Model Context Protocol
8. **Novel feature** — related papers endpoint, analytics, or export

### Current Codebase Strengths (already scoring well)
- Clean modular architecture (routers/schemas/models/agents/services)
- Full CRUD with proper status codes
- 3-agent LLM pipeline (novel, creative)
- 42 tests with comprehensive coverage
- Async throughout, type hints everywhere
- Graceful error handling and fallback chains
- PDF extraction with fallback
- Multi-turn chat with message limits
- Pydantic validation on all inputs
