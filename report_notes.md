# Technical Report — Source Notes
# DeepResearch API — COMP3011 Coursework 1
# Student: Belal Yahouni | ID: 201736144
#
# This document is a comprehensive reference for writing the technical report.
# It captures all decisions, justifications, context, and answers from the student.
# It is NOT the report itself — it is the raw material to write from.

---

## 1. STUDENT & PROJECT IDENTITY

- **Name:** Belal Yahouni
- **Student ID:** 201736144
- **Module:** COMP3011 — Web Services and Web Data, University of Leeds
- **Project title:** DeepResearch API
- **GitHub:** https://github.com/belalyahouni/DeepResearch
- **API docs PDF:** in repo at `docs/openapi.pdf`
- **Presentation slides:** link TBD (Google Drive / OneDrive — to be added before submission)

---

## 2. MOTIVATION & PROBLEM STATEMENT

The problem is personal and real. Belal encountered it during his dissertation and during an internship doing independent research: **finding relevant academic papers is unnecessarily hard**.

The core issue: different research papers describing the same concept use completely different terminology and keywords. Even when two papers are semantically related, they may share no keywords. Traditional keyword search (e.g. Google Scholar, arXiv search) fails in this situation because you must already know the precise vocabulary the authors used. For a student exploring a new topic, this is a catch-22: you need to know the field to search it, but you're searching to learn the field.

The goal of DeepResearch is to remove this barrier: allow users to search using natural language — describe a concept, ask a question, use plain English — and get semantically relevant papers back. This is especially useful for students researching AI/ML topics for the first time who don't yet know the correct academic vocabulary.

Additionally, Belal uses Claude/Claude Code heavily in his day-to-day work. Integrating the API as an MCP server means he (and other users) can invoke the research pipeline directly from within Claude without switching tools, copying text, or manually formatting requests.

---

## 3. STACK JUSTIFICATION

### 3.1 Python
- Fastest language for rapid development at this scale.
- Belal knows Python better than the alternatives (Node.js, Go), so he could review, understand, and correct the code Claude produced.
- Claude Code (the AI tool used throughout this project) is highly optimised for Python — it produces more accurate, higher-quality, and more reliable Python code than in other languages. Since the development workflow relied heavily on AI-assisted coding, choosing Python maximised the quality of the generated output and reduced errors.

### 3.2 FastAPI (not Django, not Flask)
- FastAPI provides Swagger UI and OpenAPI documentation out of the box at `/docs` with zero additional configuration — critical for this coursework.
- It is async-native, which fits naturally with async SQLAlchemy and async I/O throughout.
- Belal had prior experience with FastAPI, so he could understand, review, and extend what Claude produced without being dependent on the AI for comprehension.
- Django is heavier and more opinionated — it is better suited to full-stack web applications with templates, ORM migrations via Django's built-in system, and admin panels. DeepResearch is a pure API with no frontend layer, making FastAPI a better fit.
- Flask is lighter than Django but does not have the same async support or built-in schema validation as FastAPI.
- FastAPI's Pydantic integration provides automatic request validation and serialisation — reducing boilerplate and catching bad input at the boundary without writing explicit validators.

### 3.3 SQLite (not PostgreSQL, not MySQL)
- SQLite is simple, requires no server process, and is sufficient for the volume of data in this project.
- PostgreSQL is production-grade — it handles high concurrency, distributed access, and very large datasets. For a local academic project with a single-user API, it adds unnecessary complexity and setup overhead.
- SQLite is perfectly adequate for persisting paper metadata (~521k rows), community interaction logs, and notes — all predominantly read-heavy workloads.
- Alembic handles schema migrations cleanly on top of SQLAlchemy regardless of the underlying database, so switching to PostgreSQL in future would be straightforward.

### 3.4 ChromaDB — the NoSQL justification (required by the brief)
**The brief explicitly states:** "you should not use NoSQL databases except with clear reasoning in your supporting report document."

ChromaDB is a purpose-built vector database — a category of NoSQL store. The justification for using it is architectural, not a preference:

A relational database like SQLite cannot efficiently perform approximate nearest-neighbour (ANN) search over 768-dimensional vectors. This kind of cosine similarity search is the entire basis of the semantic search pipeline. The SQL paradigm (exact matching, indexed lookups, joins) is fundamentally the wrong tool for high-dimensional vector retrieval.

A vector database is therefore **required** to implement semantic search — it is not a NoSQL preference, it is a necessity dictated by the problem.

**Why ChromaDB specifically over alternatives:**
- **FAISS (Facebook AI Similarity Search):** Was considered first, as Belal had prior experience with it. FAISS is an extremely performant and customisable vector index library. However, it is a very low-level C++ library with a Python wrapper. It requires manual management of index construction, serialisation, ID-to-metadata mapping, and persistence. All of this is functionality ChromaDB provides natively. FAISS is the right tool when you need fine-grained control over index type (IVF, HNSW, PQ) and performance at massive scale. For this project — local, single-process, ~521k vectors — this level of control is unnecessary and adds significant implementation complexity.
- **Pinecone:** Cloud-hosted, paid at scale, adds network latency, requires an API key and external dependency. This project runs fully locally, so a managed cloud vector store is the wrong fit.
- **Weaviate:** Production-grade, runs as a separate Docker service, heavier operational footprint. Overkill for a local research project.
- **pgvector (PostgreSQL extension):** Would allow keeping everything in SQL, but requires PostgreSQL (abandoning SQLite) and is less optimised for pure vector retrieval than a dedicated vector store.
- **ChromaDB:** Local, persistent on-disk, free, installs with pip, and provides a simple Python API. Natively supports HNSW indexing with cosine similarity out of the box. Handles ID management, metadata storage, and persistence automatically. The simplest and most appropriate tool for a local, self-contained vector search system.

ChromaDB is configured with cosine similarity (`hnsw:space: cosine`) which is the standard metric for dense retrieval with normalised embeddings.

### 3.5 BAAI/bge-base-en-v1.5 Embedding Model
Claude advised on this model choice and provided the reasoning. Key factors:

- **BGE (BAAI General Embeddings)** is a family of embedding models from the Beijing Academy of Artificial Intelligence, specifically designed for retrieval tasks.
- It consistently ranks among the top open-source embedding models on the **MTEB (Massive Text Embedding Benchmark)** leaderboard, particularly for retrieval tasks.
- **bge-base-en-v1.5** is the "base" variant: 768-dimensional embeddings, ~110M parameters. This is the sweet spot — large enough to produce high-quality semantic representations of academic text, small enough to run efficiently on a laptop (Apple Silicon MPS gives ~168 papers/second during ingest).
- **Asymmetric query/document encoding:** BGE uses a retrieval prefix (`"Represent this sentence for searching relevant passages: "`) at query time but NOT at indexing time. This asymmetric approach is the recommended BGE retrieval pattern (documented in the model card) and correctly implemented in `embeddings.py`. The prefix helps the model understand that the input is a retrieval query, not a document to be indexed. This is a subtle but important correctness detail.
- **Why not OpenAI embeddings (text-embedding-3-small/ada-002):** These require API calls for every query and every document indexed. That means network latency per search, API cost, and an external dependency. With ~521k papers to index, using the OpenAI embedding API would cost money and take far longer than local inference.
- **Why not all-MiniLM-L6-v2:** A smaller, faster model but less accurate for academic retrieval. BGE was fine-tuned specifically for retrieval using hard negative mining, making it better at distinguishing semantically similar vs semantically relevant documents.
- The model is cached on first load (`lru_cache`) so it is loaded once per process and reused, avoiding repeated model initialisation overhead.

### 3.6 Google Gemini (not OpenAI, not open-source LLMs)
- **Free with generous rate limits:** Gemini provides a free tier with limits high enough for this project's usage. OpenAI's API is paid from the first token.
- **Range of model sizes for different tasks:** The project uses two Gemini models, matched to task complexity:
  - `gemini-2.5-flash-lite`: Used for the classifier and optimiser agents. These are prompt-engineering tasks requiring speed and moderate intelligence. Flash-lite is fast and cheap.
  - `gemini-2.5-pro`: Used for the summariser agent. Summarising academic text requires deeper reasoning and comprehension — the pro model produces noticeably higher quality output here.
- **Why not open-source LLMs (Llama, Mistral, etc.):** Running open-source LLMs locally means running models small enough to fit in RAM/VRAM on a consumer machine. Models at that size (7B, 13B) are not smart enough for reliable prompt classification and academic summarisation. The Gemini API gives access to models orders of magnitude larger and smarter with no local compute cost.
- **Graceful fallback:** All Gemini calls are wrapped in try/except. If the API is unavailable (key missing, quota exceeded, network error), the pipeline degrades gracefully: the classifier returns the original query unchanged, and the summariser returns None (surfaced as a 500 with a clear error message).

### 3.7 REST (not GraphQL)
- REST is the industry-standard for data APIs. All endpoints are straightforward resource-based reads and writes with clear HTTP semantics (GET for retrieval, POST for creation, PATCH for update, DELETE for deletion).
- GraphQL's strengths are flexible querying (clients request exactly the fields they need), batching, and deeply nested data traversal. DeepResearch's data model is not deeply nested — a paper has notes, and community stats. The overhead of defining a GraphQL schema, resolvers, and a query language is not justified by the problem.
- REST also pairs naturally with Swagger/OpenAPI documentation and is more familiar to API consumers.

### 3.8 arXiv Dataset (HuggingFace: davanstrien/arxiv-cs-papers-classified)
**Why arXiv:**
- arXiv is the primary pre-print server for cutting-edge AI/ML research. The most important papers in NLP, computer vision, reinforcement learning, etc. are published here before (or instead of) appearing in journals.
- The dataset is STEM-focused and filtered to CS/AI/ML categories — exactly the domain this API targets.
- Metadata is rich enough to be useful (title, authors, abstract, categories, year, DOI, URL) but not excessive — no need to parse full paper PDFs.
- The HuggingFace dataset (`davanstrien/arxiv-cs-papers-classified`) provides the data in a structured, streamable format, filtered and classified by CS category, making ingestion straightforward.

**Dataset licence:**
- The underlying arXiv paper metadata is released under **CC0 (Creative Commons Zero / Public Domain)**. arXiv makes bulk metadata access available under these terms for non-commercial and research use.
- The HuggingFace dataset inherits these terms. It is appropriate for academic use.

**Ingest pipeline:**
- Pass 1: Stream from HuggingFace (streaming mode, no full download needed), filter to 7 AI/ML categories (`cs.AI`, `cs.LG`, `cs.CL`, `cs.CV`, `cs.NE`, `cs.MA`, `stat.ML`), batch insert into SQLite using `INSERT OR IGNORE` (safe to re-run/resume).
- Pass 2: Load all papers from SQLite, embed `title + abstract` in batches of 64 with BGE, upsert into ChromaDB.
- Speed: ~168 papers/second on Apple Silicon MPS. Full corpus (~521k papers) completes in approximately 1 hour.

---

## 4. ARCHITECTURE & DESIGN

### 4.1 The 3-Agent Search Pipeline
The search pipeline is the core novelty of the project. It consists of three sequential stages:

**Stage 1 — Classifier Agent (Gemini 2.5 Flash-Lite)**
- Takes a raw natural language query from the user.
- Classifies it into one of 7 arXiv AI/ML categories: `cs.AI`, `cs.LG`, `cs.CL`, `cs.CV`, `cs.NE`, `cs.MA`, `stat.ML`.
- Returns a `category` code and human-readable `field` label.
- Rationale: by knowing which sub-field the query belongs to, the vector search can be scoped to a subset of the corpus (e.g. searching only `cs.CV` papers for a computer vision query). This reduces the number of vectors compared against, improving both latency and precision.

**Stage 2 — Optimiser Agent (Gemini 2.5 Flash-Lite)**
- Takes the raw query and rewrites it into precise academic retrieval terminology.
- Removes personal context ("I'm a student looking for..."), filler words, and off-topic qualifiers.
- The optimised query is phrased the way paper titles and abstracts are written — improving cosine similarity matching.
- Rationale: a user might type "how do transformers pay attention to words", but the optimised query is "self-attention mechanisms in transformer architectures for sequence modelling". The second query will retrieve more relevant papers because it matches the academic vocabulary actually used in the corpus.
- Both Stage 1 and Stage 2 are implemented as a single combined LLM call in `classifier_optimiser.py` returning a single JSON object with `category`, `field`, and `optimised_query` keys — minimising API calls and latency.

**Stage 3 — BGE Vector Search (ChromaDB)**
- Embeds the optimised query using `BAAI/bge-base-en-v1.5` with the BGE retrieval prefix.
- Performs approximate nearest-neighbour cosine similarity search over the ChromaDB collection.
- Returns the top-N papers ranked by similarity score (1 - cosine distance).
- Paper metadata is then fetched from SQLite by arxiv_id and returned.

**Origin of the pipeline design:**
Belal knew from the start he wanted a prompt optimiser — the insight was that users shouldn't have to think carefully about crafting a perfect search query; natural language input should work. The classifier was added to narrow the search space and improve latency. The combined single-LLM-call approach (returning both category and optimised query in one request) was a deliberate efficiency decision.

The decision to build a self-contained corpus (rather than calling an external search API like OpenAlex) was also deliberate. Belal had previously used the OpenAlex API with its semantic search beta. The limitations were:
- Too broad (all academic disciplines, not just AI/ML).
- An external API dependency — not self-contained, constrained by their rate limits and API design.
- No room for customisation: bigger embedding models, different similarity metrics, better prompts, etc.
- Building it self-contained allows improvement at every layer.

### 4.2 Community Interaction Tracking
**Design:** Every time a paper is accessed via `GET /papers/{arxiv_id}`, `POST /summarise` (with an `arxiv_id`), or `GET /papers/{arxiv_id}/related`, the event is:
- Logged as a timestamped row in `community_interactions` (one row per event).
- Aggregated into `community_papers` (total interaction count + last interacted timestamp).

**Rationale / motivation:**
The inspiration was social media: on Twitter/Instagram/Reddit, it is easy to see what is trending — likes, shares, recency all signal popularity. In academic research, this is much harder. You can see citation counts, but only after a paper has been published and cited for years. For cutting-edge pre-prints, there is no signal.

The community index creates a proxy for "what is the research community actively reading right now". Papers with the most lookups, summarisations, and related-paper queries are the ones people are actively engaged with. This surfaces trends organically from API usage.

**Period filtering (week / month / year):**
The `GET /community` endpoint supports an optional `period` parameter (`week`, `month`, `year`). When provided, it queries the `community_interactions` table directly with a timestamp cutoff — counting only interactions within the rolling window. This allows users to see:
- What was popular this week (very recent trends).
- What was popular this month / year (medium-term trends).
- What is popular all-time (established hot topics).

This is a more nuanced and useful signal than just all-time counts, as it avoids old papers dominating the ranking indefinitely.

### 4.3 MCP Server (Model Context Protocol)
**Why an MCP server:**
Belal increasingly works in Claude and Claude Code for most of his development and research workflows. The MCP server allows the DeepResearch pipeline to be available as a set of tools that Claude can call directly, in the same environment where he already works.

**Why this matters vs. raw HTTP API:**
The raw HTTP API is functional but awkward for conversational research workflows. For example:
- To summarise a paper, you'd need to manually copy the abstract and POST it to `/summarise`.
- To find papers related to one you just discussed, you'd need to know its arXiv ID and make another request.

With the MCP server, Claude handles the orchestration naturally. If a user says "summarise the paper we just found", Claude takes the paper from the conversation context and passes it directly to the `summarise_text` tool — no manual copying. This makes the research workflow feel seamless and conversational.

**MCP tools implemented:**
- `search_papers`: full 3-agent pipeline (classify → optimise → BGE search).
- `summarise_text`: Gemini summarisation.
- `find_related_papers`: BGE vector similarity on a known paper.
- `get_community_papers`: trending papers index.
- `get_paper_notes`: community notes for a paper.

**MCP resources implemented:**
- `arxiv://{arxiv_id}`: full paper details (also triggers community interaction tracking).
- `arxiv://stats`: corpus statistics.

The MCP server reuses all the same agents, services, and database as the HTTP API — no code duplication, no HTTP calls between them.

### 4.4 Public Notes System (Full CRUD)
**Data model:**
`PaperNote` — id, arxiv_id (FK to arxiv_papers), content (text), created_at, updated_at.

**Endpoints:**
- `POST /papers/{arxiv_id}/notes` — create (201), rate limited 10/min.
- `GET /papers/{arxiv_id}/notes` — list all notes for a paper.
- `PATCH /notes/{id}` — update note content, rate limited 10/min.
- `DELETE /notes/{id}` — delete permanently (204).

**Rationale:**
Notes extend the API into a collaborative layer. Users can annotate papers with context, summaries, insights, or links. Because all data is shared (no user accounts), notes are public to all consumers. This makes the API feel like a shared research workspace, not just a search tool.

**The collaborative angle was an evolution:** Initially the notes feature was the only CRUD model. But the platform felt too generic. The community interaction tracking was added alongside notes to make the platform feel like a living, social research index — not just a database lookup.

### 4.5 Security Implementation
**API key authentication (`app/auth.py`):**
- All endpoints except `/health` require an `X-API-Key` header.
- Key is stored in the `API_KEY` environment variable (not hardcoded).
- Comparison uses `secrets.compare_digest()` — a timing-safe comparison that prevents timing attacks (where an attacker could measure response time to guess the key character by character).
- Missing key → 401. Invalid key → 401. Key not configured server-side → 500.

**Rate limiting (`slowapi`):**
- Rate limiting was added proactively to protect two types of resources:
  - **Gemini API credits:** `POST /summarise` is rate limited to 5/min. Gemini pro is the most expensive model in the pipeline; unlimited summarisation could burn through credits quickly.
  - **Database integrity:** `POST /papers/{arxiv_id}/notes` and `PATCH /notes/{id}` are rate limited to 10/min each. Without this, users could flood the database with spam notes.
- Rate limiting was a conscious decision made by Belal — AI tools don't always flag this kind of abuse concern automatically.

**CORS middleware:**
- Restricts cross-origin requests to `localhost:8000` / `127.0.0.1:8000`.
- Only allows the HTTP methods the API actually uses.
- Only whitelists the headers the API needs (`X-API-Key`, `Content-Type`).

**TrustedHostMiddleware:**
- Rejects requests with forged or unexpected `Host` headers.
- Prevents host header injection attacks.

---

## 5. CHALLENGES & DESIGN EVOLUTION

### 5.1 Architecture Design Was the Hardest Part
The most difficult challenge was not writing code — it was making the right architectural decisions. Deciding which LLMs to use for which tasks, what to store in which database, how the pipeline flows together, which features to build and which to cut. These decisions all involved trade-offs that had to be reasoned through carefully.

Claude did not always produce perfectly modular code. For example, the summarisation logic was initially implemented twice — once in the search pipeline and once in the dedicated summarise endpoint. Belal identified this and directed Claude to consolidate into a single `summariser.py` agent reused by both paths. This kind of architectural review required Belal to read and understand what was built and make corrections.

### 5.2 Iterating to the Right Features
The platform evolved significantly through iteration. Initially, the feature set was simpler — just notes and search. But Belal felt the platform lacked a distinctive angle. The community interaction tracking emerged from thinking about what makes research hard (spotting trends) and what makes social platforms effective (surfacing popular content). The period filtering (`week`/`month`/`year`) was added to make the trending feature more practically useful.

### 5.3 Previously Used OpenAlex API
An earlier version used the OpenAlex semantic search API. Reasons for moving away:
- Too broad (covers all academic disciplines, not just AI/ML).
- External API dependency — constrained by OpenAlex's rate limits, API design, and availability.
- No customisation: couldn't swap embedding models, tune prompts, or modify the pipeline.
- Self-building enables future improvement at every layer.

### 5.4 Rate Limiting as a Proactive Decision
Belal identified the need for rate limiting before it became a problem. The concern was twofold: (1) burning through Gemini API credits with unrestricted summarisation, (2) flooding the database with spam notes. AI coding assistants don't always surface these concerns automatically — this came from thinking carefully about what could go wrong in production use.

### 5.5 System Prompt Iteration
The system prompts for the classifier/optimiser and summariser agents were iterated through manual testing. The initial prompts produced inconsistent output (e.g. markdown fences in JSON responses from the classifier, or overly verbose summaries). These were refined based on observed output quality. The classifier now explicitly strips markdown fences from the response and validates expected JSON keys before using the result.

---

## 6. TESTING APPROACH

### 6.1 Automated Testing (Claude Code)
Claude Code wrote the automated test suite (38 tests, 7 files). Belal reviewed the tests, ran them, and directed Claude to add additional tests for edge cases he identified. Every test uses:
- In-memory SQLite (no persistent state between tests).
- Mocked external APIs (Gemini, ChromaDB) — so tests run fast and don't require API keys.

Coverage:
- Happy paths for all endpoints.
- Authentication (401 for missing/invalid key).
- Validation errors (422 for empty or missing required fields).
- Not found (404 for nonexistent papers/notes).
- External service failure (500 when Gemini or ChromaDB fails).
- Graceful fallback (search still returns results when Gemini is unavailable).

### 6.2 Manual Testing (Belal)
Belal manually tested:
- **API usability and intuitiveness:** Does the endpoint design make sense? Are the responses helpful? Are error messages clear?
- **LLM quality:** Ran the search, summarise, and classify endpoints against real queries and evaluated whether the outputs were actually good — not just that they returned 200.
- **MCP integration:** Used the MCP server within Claude Desktop and tested whether the conversational research workflow (find paper → read it → ask Claude to summarise → find related papers) worked naturally.

**Manual testing drove architecture changes.** For example:
- System prompt refinements for the classifier and summariser came from observing poor output quality in real use.
- Feature ideas (period filtering on community, MCP resources) emerged from asking "what would actually be useful in practice?".
- The decision to remove the earlier OpenAlex integration came from experiencing its limitations in real use.

### 6.3 Lesson from Dual Testing Approach
The automated tests ensured functional correctness (does it run, does it return the right HTTP status, does it handle errors properly). Manual testing ensured quality (is the output actually useful, is the pipeline producing good results, does the conversational MCP flow work well). Both were necessary and complementary.

---

## 7. LESSONS LEARNED

1. **Architecture decisions are harder than coding.** Choosing the right tools, defining the right data model, and designing the right pipeline requires more thought than writing the code. AI can help implement, but the design choices are the developer's responsibility.
2. **Dual testing (automated + manual) is essential for AI-integrated systems.** Automated tests can verify that code runs correctly, but they cannot evaluate whether an LLM agent produces good output. Manual testing of the actual LLM calls was critical for quality.
3. **Rate limiting and abuse prevention should be designed in early, not added later.** Thinking proactively about what could go wrong (spam, credit burning) saved effort vs. patching it reactively.
4. **Self-contained systems are easier to improve.** Using the OpenAlex API was fast to get started, but switching to a self-built pipeline gave full control over every component. Each layer (embedding model, LLM prompt, similarity metric) is now independently improvable.
5. **Modularity requires active review.** Claude Code tends to get things working rather than elegantly structured. Code review and architectural direction (e.g. "the summariser is implemented twice, consolidate it") was essential.

---

## 8. LIMITATIONS

1. **No note moderation.** Any user can add any note to any paper — including irrelevant, incorrect, or trolling content. In the current system, notes are not validated for relevance before being stored.
2. **Note update trust.** Anyone with an API key can update any note, which risks collaborative sabotage. There is no concept of note ownership.
3. **Community interaction table grows unbounded.** Every lookup is logged as a new row in `community_interactions`. Over a long period of heavy use, this table will grow very large. There is currently no archiving, pruning, or TTL mechanism.
4. **No user accounts.** All data (notes, community stats) is global. There is no per-user context, saved searches, or personalisation.
5. **Corpus is static.** The arXiv corpus is ingested once and does not automatically update. New papers published after the ingest date are not searchable. An automated ingestion schedule would be needed for a production deployment.

---

## 9. FUTURE WORK

1. **AI moderation agent for notes.** An LLM-based agent that reviews notes before they are committed — checking for relevance, quality, and appropriateness. Similarly, note update requests could be reviewed before being applied. This would make the collaborative notes layer genuinely useful and trustworthy.
2. **Incremental corpus updates.** A scheduled job that ingests new arXiv papers (e.g. daily), keeping the corpus current.
3. **Community interaction archiving.** A background task that periodically aggregates old `community_interactions` rows into the `community_papers` counters and prunes the raw log, keeping the table size manageable.
4. **Re-ranking layer.** A cross-encoder re-ranking step (e.g. using a small BERT-based cross-encoder) applied to the top-N BGE results for higher precision. Bi-encoder retrieval (BGE) is fast but less precise than cross-encoder re-ranking.

---

## 10. GENAI USAGE

### 10.1 Tools Used
| Tool | Purpose |
|---|---|
| Claude Code (Anthropic) | Primary development tool — architecture design, planning, implementation, testing, code review |
| Google Gemini (via gemini.google.com) | Research into latest frameworks and technologies, comparing alternatives, understanding trade-offs |

### 10.2 How Claude Code Was Used
Claude Code was used as a coding assistant, a thinking partner, and a research tool — not just a code generator.

**Architecture & planning:**
- Extended conversations discussing system design before writing code. For example, designing the 3-agent pipeline (what stages, what models, what fallbacks), the ChromaDB vs FAISS decision, the community interaction tracking data model.
- Belal maintained a `CLAUDE.md` file in the project root giving Claude persistent context about the stack, conventions, and current state. Temporary planning documents and to-do lists were also created collaboratively.
- After each major implementation phase, Belal had Claude analyse the project state against the coursework requirements — identifying what was missing or out of scope.

**Implementation:**
- Claude wrote the bulk of the code. Belal reviewed every output, directed architectural changes, identified problems (like the duplicate summariser), and guided the implementation towards the design.
- Code was not blindly accepted — Belal understood the architecture well enough to spot and correct issues.

**Testing:**
- Claude Code wrote the automated test suite. Belal reviewed, ran, and extended it.

**This report:**
- Claude Code was used to analyse the coursework brief thoroughly, identify all requirements, and help plan and draft the technical report content.

### 10.3 How Gemini Was Used for Research
Google Gemini was used for researching and comparing technology choices before making decisions:
- Comparing FAISS vs ChromaDB for vector storage — understanding the trade-offs (low-level control vs simplicity).
- Understanding the BGE embedding model and why it is recommended for retrieval tasks.
- Exploring framework options (FastAPI vs Flask vs Django) and mapping their characteristics onto the project requirements.
- Identifying rate limiting approaches for FastAPI.

### 10.4 GenAI Grade Band Justification
The use of GenAI in this project extends well beyond debugging or code writing (50-59 band). Claude was used to:
- **Explore architectural alternatives** — ChromaDB vs FAISS, Gemini vs OpenAI, BGE vs other embeddings (80-89 band: "high level use of GenAI to aid creative thinking and solution exploration").
- **Reimagine the solution design** — the 3-agent pipeline, the MCP integration, the community interaction design were all shaped through extended collaborative conversations with Claude (90-100 direction: "exploring high-level alternatives and reimagining the design of cutting-edge solutions").
- **Maintain persistent project context** (`CLAUDE.md`) so Claude could reason about the project as a whole, not just isolated tasks.

### 10.5 Conversation Log Examples (to attach as appendix)
Two exported conversation logs to include:
1. `chat_claude_code.txt` — Claude Code session (coding, architecture, planning).
2. `chat_gemini_Research.txt` — Gemini session (technology research, framework comparison, trade-off analysis).

---

## 11. DATASET CITATION

**HuggingFace dataset:** `davanstrien/arxiv-cs-papers-classified`
**Source:** Filtered and classified subset of arXiv CS paper metadata.
**Underlying data licence:** arXiv paper metadata is released under **CC0 (Creative Commons Zero — Public Domain)**. arXiv makes bulk metadata access available for non-commercial and research use under these terms.
**URL:** https://huggingface.co/datasets/davanstrien/arxiv-cs-papers-classified
**Usage in this project:** Filtered to 7 AI/ML categories (~521k papers), ingested into SQLite and ChromaDB via `scripts/ingest_arxiv.py`.

---

## 12. REFERENCES (to include in report)

- Bianchi, F. et al. (2023). *BAAI/bge-base-en-v1.5*. HuggingFace Model Hub. https://huggingface.co/BAAI/bge-base-en-v1.5
- Ramé, M. et al. (2023). *MTEB: Massive Text Embedding Benchmark*. https://huggingface.co/spaces/mteb/leaderboard
- Tiangolo, S. (2019–present). *FastAPI*. https://fastapi.tiangolo.com
- SQLAlchemy (2024). *SQLAlchemy Documentation*. https://docs.sqlalchemy.org
- Trabelsi, A. et al. (2025). *ChromaDB: The Open-Source Embedding Database*. https://www.trychroma.com
- Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *EMNLP*. https://arxiv.org/abs/1908.10084
- Google DeepMind (2025). *Gemini API Documentation*. https://ai.google.dev
- van Strien, D. (2024). *arxiv-cs-papers-classified*. HuggingFace Datasets. https://huggingface.co/datasets/davanstrien/arxiv-cs-papers-classified
- arXiv (2025). *arXiv Bulk Data Access*. https://arxiv.org/help/bulk_data
- Slowapi (2024). *Rate limiting for FastAPI*. https://github.com/laurentS/slowapi

---

## 13. SUBMISSION LINKS (to embed in the report PDF)

- **GitHub:** https://github.com/belalyahouni/DeepResearch
- **API docs PDF:** https://github.com/belalyahouni/DeepResearch/blob/main/docs/openapi.pdf
- **Presentation slides:** https://docs.google.com/presentation/d/1B8lSFLUzY_b4ehkRaAyDCXZhu-i7uHN_1G08rRB3m0s/edit?usp=share_link

---

## 14. PASS/FAIL CHECKLIST

- [x] GitHub repo public with commit history
- [x] README.md present
- [x] API documentation PDF in repo
- [ ] Technical report (this document → to be written as PDF)
- [ ] GenAI declaration in report
- [ ] Conversation logs as appendix
- [ ] Links to GitHub, API docs, slides in report
- [ ] Presentation slides (PPTX)
- [ ] Slides link hosted and linkable
