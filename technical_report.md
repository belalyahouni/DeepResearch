# DeepResearch API — Technical Report
**COMP3011: Web Services and Web Data** | University of Leeds
**Student:** Belal Yahouni | **ID:** 201736144

| Resource | Link |
|---|---|
| GitHub Repository | https://github.com/belalyahouni/DeepResearch |
| API Documentation (PDF) | https://github.com/belalyahouni/DeepResearch/blob/main/docs/openapi.pdf |
| Presentation Slides | https://docs.google.com/presentation/d/1B8lSFLUzY_b4ehkRaAyDCXZhu-i7uHN_1G08rRB3m0s/edit?usp=share_link |

---

## 1. Introduction & Motivation

Finding relevant academic papers is harder than it should be. During independent research — both during a dissertation and across an internship — a recurring problem emerged: keyword search is fundamentally broken for anyone new to a field. Different authors describing the same concept use completely different terminology, meaning two semantically related papers may share no keywords at all. To search effectively, you must already know the vocabulary of the field you are trying to learn. This is a catch-22 that keyword-based search engines such as standard arXiv search and Google Scholar do not resolve.

DeepResearch addresses this directly. It is an agentic research assistant API that accepts natural language queries and returns semantically relevant AI/ML papers from a local arXiv corpus of approximately 521,000 papers. Users can describe a concept in plain English — without knowing the correct academic terminology — and receive ranked results via cosine similarity search over dense vector embeddings. The pipeline is further extended by a collaborative layer: a public notes system allows users to annotate papers, and a community interaction index surfaces which papers are being most actively engaged with across the API, providing a real-time proxy for research trends.

The API is also exposed as a Model Context Protocol (MCP) server for Claude Desktop, enabling seamless integration into AI-assisted research workflows without requiring users to interact with HTTP endpoints directly.

---

## 2. Technology Stack & Justification

### 2.1 Language: Python

Python was selected over the alternatives named in the brief (Node.js, Go) for two reasons. First, it is the language in which the developer has the deepest working knowledge, which was essential for reviewing, understanding, and correcting AI-generated code — a critical part of the development workflow described in Section 5. Second, Claude Code, the primary AI tool used throughout the project, produces demonstrably more accurate and reliable Python code than in other languages. Given that the development process relied heavily on AI-assisted implementation, choosing Python directly improved the quality and correctness of the output.

### 2.2 Framework: FastAPI

FastAPI was chosen over Django (the module's primary taught framework) and Flask. Django is better suited to full-stack applications with templating, an admin panel, and tightly coupled ORM tooling — none of which are relevant to a pure API. It also introduces significant boilerplate for a project of this scope. Flask is lighter but lacks async support and built-in schema validation. FastAPI provides automatic Swagger UI and OpenAPI documentation at `/docs` with no additional configuration, native async support throughout, and automatic request validation and serialisation via Pydantic integration. It also aligns with prior experience, enabling meaningful code review alongside AI-generated output.

### 2.3 Database: SQLite with SQLAlchemy and Alembic

SQLite was selected over PostgreSQL and MySQL. PostgreSQL is production-grade and designed for high-concurrency, distributed, or very large-scale deployments — all of which are out of scope for a locally hosted academic API. SQLite requires no server process, runs entirely as a file, and handles the read-heavy workloads of this project (paper metadata lookup, community stats, notes) without issue. SQLAlchemy provides an async ORM layer, and Alembic handles schema migrations. If a production deployment were required in future, the underlying database could be swapped to PostgreSQL with minimal changes to application code.

### 2.4 Vector Database: ChromaDB

The brief states that NoSQL databases should not be used without clear justification. ChromaDB is a purpose-built vector database — a category of NoSQL store — and its use here is architecturally necessary rather than a matter of preference.

A relational database cannot efficiently perform approximate nearest-neighbour (ANN) search over 768-dimensional vectors. Cosine similarity search across hundreds of thousands of high-dimensional embeddings is the mechanism by which semantic search is implemented. SQL's paradigm — exact matching, indexed lookups, joins — is the wrong tool for this task. A vector database is therefore a requirement of the problem, not a stylistic choice.

Among vector database options, two were seriously considered. FAISS (Facebook AI Similarity Search), with which the developer had prior experience, is a highly performant and customisable vector index library. However, it operates at a very low level: it provides no persistence, no ID-to-metadata mapping, and no Python-native management layer. All of this must be implemented manually. FAISS is the right choice when fine-grained control over index type and retrieval performance at extreme scale is needed. For a local, single-process system indexing ~521k papers, this level of complexity is unnecessary. ChromaDB provides HNSW indexing with cosine similarity, persistent on-disk storage, and a simple Python API out of the box. It is local, free, installs via pip, and requires no external services. It was the most appropriate tool for the problem.

### 2.5 Embeddings: BAAI/bge-base-en-v1.5

The BGE (BAAI General Embeddings) family of models from the Beijing Academy of Artificial Intelligence is specifically designed for retrieval tasks and consistently ranks among the top open-source embedding models on the MTEB (Massive Text Embedding Benchmark) leaderboard [Muennighoff et al., 2023]. The `bge-base-en-v1.5` variant produces 768-dimensional embeddings with approximately 110 million parameters. At this size it achieves strong retrieval quality while remaining efficient enough for local inference — achieving approximately 168 papers per second on Apple Silicon MPS during corpus ingestion.

A key implementation detail is BGE's asymmetric encoding convention: the retrieval prefix `"Represent this sentence for searching relevant passages: "` is applied at query time but not at document indexing time. This is the recommended usage pattern documented in the model card and is correctly implemented in `app/services/embeddings.py`. The alternative of using OpenAI's embedding API was rejected because it would introduce per-query API cost, network latency on every search, and an external dependency — none of which are acceptable for a locally self-contained system.

### 2.6 LLM: Google Gemini

Google Gemini was selected over OpenAI's models and locally hosted open-source LLMs. The free tier provides generous rate limits sufficient for this project. Critically, Gemini offers a range of model sizes that map naturally onto the different task complexities within the pipeline: `gemini-2.5-flash-lite` is used for the classifier and optimiser agents, where speed and a straightforward structured output are required; `gemini-2.5-pro` is used for the summariser, where deeper reasoning over academic text is needed and output quality is the priority. Running open-source LLMs locally (Llama, Mistral) was considered but rejected — models small enough to run on consumer hardware are not sufficiently capable for reliable query classification and academic summarisation. The Gemini API provides access to much larger models at no cost within the project's usage levels.

All Gemini calls are wrapped in try/except blocks with graceful fallbacks: the classifier returns the original query unchanged if the API is unavailable, and the summariser returns a 500 with a descriptive error. The pipeline degrades safely rather than failing entirely.

### 2.7 API Style: REST

A RESTful design was chosen over GraphQL. GraphQL's strengths — flexible field selection, batching, and nested query traversal — are most valuable when the data model is deeply nested and clients have highly variable data requirements. DeepResearch's resources (papers, notes, community stats) are shallow and well-defined. The overhead of a GraphQL schema, resolver layer, and query language is not justified. REST maps cleanly onto the resource structure and pairs naturally with OpenAPI/Swagger documentation.

### 2.8 Dataset

The arXiv corpus is sourced from the HuggingFace dataset `davanstrien/arxiv-cs-papers-classified` [van Strien, 2024], a structured and streamed subset of arXiv CS paper metadata. It was chosen because arXiv is the primary pre-print server for cutting-edge AI/ML research — the most significant papers in NLP, computer vision, reinforcement learning, and related fields appear here first. The metadata (title, authors, abstract, categories, year, DOI, URL) is rich enough to support search, summarisation, and community tracking without requiring full paper text. The dataset is filtered to seven AI/ML categories: `cs.AI`, `cs.LG`, `cs.CL`, `cs.CV`, `cs.NE`, `cs.MA`, and `stat.ML`, yielding approximately 521,000 papers. The underlying arXiv metadata is released under **CC0 (Creative Commons Zero — Public Domain)** [arXiv, 2025], making it appropriate for academic use without restriction.

---

## 3. Architecture & Design

*See Figure 1 (architecture diagram) — submitted alongside this report.*

### 3.1 The Three-Stage Agentic Search Pipeline

The central contribution of DeepResearch is its search pipeline. Rather than accepting a raw query and performing direct keyword or vector search, the pipeline passes the query through three sequential stages.

**Stage 1 — Classifier and Optimiser Agent.** A single call to `gemini-2.5-flash-lite` performs two tasks simultaneously, returning a structured JSON response: it classifies the query into one of the seven arXiv AI/ML categories, and it rewrites the query into precise academic retrieval terminology — removing personal context, filler words, and off-topic qualifiers. For example, a user query such as "how do transformers pay attention to words" is rewritten to "self-attention mechanisms in transformer architectures for sequence modelling". This optimised form matches the vocabulary actually present in paper titles and abstracts, improving the subsequent cosine similarity search. Combining classification and optimisation into one LLM call minimises latency and API usage.

**Stage 2 — BGE Vector Embedding.** The optimised query is embedded using `bge-base-en-v1.5` with the BGE retrieval prefix. The result is a 768-dimensional normalised vector.

**Stage 3 — ChromaDB Cosine Similarity Search.** The query vector is compared against the ~521k indexed paper embeddings using HNSW approximate nearest-neighbour search with cosine similarity. The top-N matching arXiv IDs and similarity scores are returned, and paper metadata is fetched from SQLite to produce the final ranked response.

The motivation for building this pipeline, rather than calling an external search API, stems from experience with the OpenAlex semantic search API. Its limitations were: broad coverage across all academic disciplines (not focused on AI/ML), external API dependency with rate limits, and no ability to customise any component. A self-built pipeline allows independent improvement of each stage — embedding model, LLM prompts, similarity metric — and is entirely locally self-contained.

### 3.2 Community Interaction Index

The community feature provides a real-time proxy for research trends. Inspiration came from social media: on platforms such as Twitter or Reddit, trending content is easy to identify from interaction signals (likes, shares, recency). In academic research, equivalent signals do not exist for pre-prints — citation counts only accumulate over years, long after a paper's initial relevance. The community index fills this gap organically: every paper access via `GET /papers/{arxiv_id}`, `POST /summarise` (with an arxiv_id), or `GET /papers/{arxiv_id}/related` is logged as a timestamped event in the `community_interactions` table. These events are aggregated into `community_papers` (total count and last activity timestamp).

The `GET /community` endpoint supports an optional `period` parameter (`week`, `month`, `year`) that queries the raw interaction log with a timestamp cutoff, enabling rolling time-window rankings rather than static all-time counts. This allows users to distinguish what is trending this week from what has been consistently popular over the past year — a more nuanced and practically useful signal.

### 3.3 MCP Server Integration

The API is also exposed as a Model Context Protocol (MCP) server, enabling direct integration with Claude Desktop. The motivation is practical: AI-assisted research workflows increasingly take place within tools like Claude, where context from previous messages is available. Through the HTTP API alone, workflows are awkward — to summarise a paper, a user must manually copy its abstract and POST it to `/summarise`. Within Claude via MCP, the same operation is natural: Claude retrieves the paper using `arxiv://{arxiv_id}`, passes its content to `summarise_text`, and returns the result in conversation, without any manual data transfer. The MCP server reuses all the same agents, services, and database as the HTTP API with no code duplication and no HTTP calls between layers.

### 3.4 Security

Security was designed in from the outset rather than added retrospectively. API key authentication (`app/auth.py`) protects all endpoints except `/health`, using `secrets.compare_digest()` for timing-safe comparison — preventing timing attacks where an attacker could infer the correct key character by character from response time variance. Rate limiting via `slowapi` is applied to two categories of endpoint: `POST /summarise` (5 requests/minute) to protect Gemini API credits from exhaustion, and the notes write endpoints (10 requests/minute each) to prevent database flooding with spam content. CORS middleware restricts cross-origin requests to localhost origins with only the required methods and headers whitelisted. TrustedHostMiddleware rejects requests with forged Host headers.

---

## 4. Testing

### 4.1 Automated Tests

The automated test suite comprises 42 tests across 7 files, written with pytest and pytest-asyncio. Tests use an in-memory SQLite database and mock all external dependencies (Gemini API, ChromaDB), ensuring fast, deterministic execution with no API keys required. Coverage spans: all happy paths, authentication failures (401), input validation errors (422), not-found responses (404), external service failures (500), graceful fallback behaviour (search returning results when Gemini is unavailable), and community period filtering. Claude Code generated the initial test suite; the developer reviewed each test, directed additional cases for edge conditions, and ran the full suite after every change. The passing rate has remained at 100% throughout development.

### 4.2 Manual Testing

Automated tests verify functional correctness but cannot evaluate output quality. Manual testing covered three areas: API usability (are the endpoint designs intuitive, are error messages informative), LLM output quality (are the classifier, optimiser, and summariser producing genuinely useful results for real queries), and MCP integration (does the conversational research workflow within Claude Desktop function naturally end-to-end). Manual testing directly drove architectural changes — system prompt refinements for both agents, the decision to consolidate a duplicated summariser implementation, and the decision to replace the earlier OpenAlex API dependency with a self-built pipeline, all emerged from observing real behaviour rather than from automated checks.

---

## 5. Challenges & Lessons Learned

The most significant challenge was architectural design rather than implementation. Decisions about which LLM model to use for each task, what data to persist in which store, how the pipeline stages should compose, and which features to build or cut all required careful trade-off reasoning that AI tools do not surface automatically. For example, the need for rate limiting on write endpoints was identified proactively by the developer — thinking through what could go wrong under real usage — rather than being flagged by any tool. Similarly, the classifier and optimiser were initially two separate LLM calls; consolidating them into a single structured call required understanding the system as a whole and directing the implementation accordingly.

A secondary challenge was maintaining code modularity with AI-assisted development. Claude Code produced working code but did not always structure it cleanly — the summariser logic was initially duplicated across two parts of the codebase. Active code review and architectural correction were necessary throughout.

The principal lesson is that AI-assisted development shifts the primary challenge from writing code to making good decisions: which problem to solve, how to structure the solution, and where the generated output needs correction. A second lesson is that automated and manual testing serve fundamentally different purposes: the former verifies correctness, the latter verifies quality. For systems involving LLM agents, manual evaluation of actual model outputs is not optional.

---

## 6. Limitations & Future Work

The current implementation has four notable limitations. First, the notes system has no moderation: any holder of a valid API key can add or update any note with any content, including irrelevant or misleading material. Second, the `community_interactions` table grows without bound — each paper access appends a new row, and there is no archiving or pruning mechanism. Third, the corpus is static: papers published after the ingestion date are not discoverable without re-running the ingest script. Fourth, the system has no concept of user identity, meaning notes cannot be attributed to their authors and there is no personalisation.

The most valuable future development would be an AI moderation agent for the notes system. An LLM-based reviewer that evaluates submitted notes for relevance and quality before committing them to the database — and similarly reviews update requests — would make the collaborative layer genuinely trustworthy and useful. This would transform the notes system from an open write surface into a curated, high-signal annotation layer. Beyond this, incremental corpus updates (a scheduled ingest of new arXiv papers), interaction log archiving, and a cross-encoder re-ranking stage applied to the top BGE results (for higher precision retrieval) are the most impactful improvements identified.

---

## 7. Generative AI Declaration

### 7.1 Tools Used

| Tool | Provider | Purpose |
|---|---|---|
| Claude Code | Anthropic | Architecture design, planning, implementation, testing, code review, report analysis |
| Google Gemini (gemini.google.com) | Google DeepMind | Technology research, framework comparison, trade-off analysis |

### 7.2 How AI Was Used

Claude Code was the primary tool throughout the project and was used at three distinct levels. At the implementation level, it generated code for agents, services, routers, schemas, and tests — all of which was reviewed, understood, and where necessary corrected by the developer before being accepted. At the planning level, extended conversations were used to design the system architecture before writing code: the structure of the 3-agent pipeline, the ChromaDB vs FAISS decision, the community interaction data model, and the MCP integration strategy were all worked through collaboratively. A `CLAUDE.md` context file was maintained in the project root to give Claude persistent awareness of the stack, conventions, and current state across sessions. At the analytical level, Claude Code was used to review the coursework requirements against the project state — identifying gaps, assessing scope, and ensuring deliverables were complete.

Google Gemini was used for technology research and comparative analysis: evaluating FAISS against ChromaDB, understanding the BGE embedding model and its retrieval conventions, comparing FastAPI against Flask and Django, and identifying appropriate rate limiting approaches for FastAPI. This research directly informed the stack decisions described in Section 2.

### 7.3 Reflective Analysis

The use of AI in this project was not limited to writing or debugging code. The most valuable applications were architectural: using Claude to think through design alternatives, evaluate trade-offs, and identify consequences of choices before implementing them. For example, the decision to combine the classifier and optimiser into a single LLM call emerged from a conversation about latency and API cost rather than from writing code. The decision to build a self-contained pipeline rather than rely on OpenAlex was similarly reached through structured discussion about the long-term limitations of external API dependency. Claude Code was also used to review the coursework brief thoroughly, map its requirements onto the project, and identify what remained outstanding — effectively acting as a critical reviewer of the work in progress.

The conversation logs attached as Appendix A are representative examples of this usage: one demonstrates a coding session, the other a technology research and comparison session. They illustrate that AI was used as a thinking partner and research assistant rather than solely as a code generator — consistent with the high-level GenAI usage described in the 80–89 and 90–100 grade bands.

---

## References

arXiv (2025). *arXiv Bulk Data Access*. https://arxiv.org/help/bulk_data

Google DeepMind (2025). *Gemini API Documentation*. https://ai.google.dev

Muennighoff, N., Tazi, N., Magne, L., & Reimers, N. (2023). MTEB: Massive Text Embedding Benchmark. *EACL 2023*. https://arxiv.org/abs/2210.07316

Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *EMNLP 2019*. https://arxiv.org/abs/1908.10084

Slowapi (2024). *Rate Limiting for Starlette and FastAPI*. https://github.com/laurentS/slowapi

SQLAlchemy (2024). *SQLAlchemy Documentation*. https://docs.sqlalchemy.org

Tiangolo, S. (2019–2025). *FastAPI Documentation*. https://fastapi.tiangolo.com

Trychroma (2024). *ChromaDB: The Open-Source Embedding Database*. https://www.trychroma.com

van Strien, D. (2024). *arxiv-cs-papers-classified*. HuggingFace Datasets. https://huggingface.co/datasets/davanstrien/arxiv-cs-papers-classified

Xiao, S. et al. (2023). *C-Pack: Packaged Resources To Advance General Chinese Embedding*. arXiv. https://arxiv.org/abs/2309.07597 [BGE model paper]

---

## Appendix A — Generative AI Conversation Logs

The following exported conversation logs are attached as supplementary material in accordance with the GenAI declaration requirements of this assessment.

**Log 1:** `chat_claude_code.txt` — Claude Code session covering coding, architecture design, and planning decisions.

**Log 2:** `chat_gemini_Research.txt` — Google Gemini session covering technology research and framework comparison (ChromaDB vs FAISS, embedding model selection, stack trade-offs).
