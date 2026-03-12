# DeepResearch API — Technical Report
**COMP3011: Web Services and Web Data** | University of Leeds
**Student:** Belal Yahouni | **ID:** 201736144

| Resource | Link |
|---|---|
| GitHub Repository | https://github.com/belalyahouni/DeepResearch |
| API Documentation (PDF) | https://github.com/belalyahouni/DeepResearch/blob/main/docs/openapi.pdf |
| Presentation Slides | https://docs.google.com/presentation/d/1B8lSFLUzY_b4ehkRaAyDCXZhu-i7uHN_1G08rRB3m0s/edit?usp=share_link |

---

## 1. Introduction and Motivation

Finding relevant research papers is harder than it should be. During a dissertation and later an internship, the same problem kept appearing: keyword search fails for anyone new to a field. Different authors writing about the same concept use different words, so two closely related papers may share no keywords at all. To search well, you already need to know the vocabulary of the field you are trying to learn. Standard tools like arXiv search and Google Scholar do not solve this.

DeepResearch is a research assistant API built around this problem. It accepts natural language queries and returns semantically relevant AI/ML papers from a local arXiv corpus of around 521,000 papers. Users can describe what they are looking for in plain English and get ranked results back via cosine similarity search over dense vector embeddings. The system also includes a public notes layer for annotating papers, and a community interaction index that tracks which papers are being accessed most, giving a real-time signal for what the research community is currently interested in.

The API is additionally exposed as a Model Context Protocol (MCP) server for Claude Desktop. This lets the full research pipeline be used conversationally inside Claude, without touching HTTP endpoints directly.

---

## 2. Technology Stack and Justification

### 2.1 Python

Python was chosen over Node.js and Go for two practical reasons. It is the language the developer knows best, which made it possible to review and correct AI-generated code with confidence. It is also the language Claude Code performs best in. Since AI-assisted coding was central to the workflow, using Python directly improved the reliability of the output.

### 2.2 FastAPI

FastAPI was chosen over Django and Flask. Django is designed for full-stack applications with templating and admin tooling, none of which apply to a pure API. Flask lacks native async support and automatic request validation. FastAPI gives Swagger UI and OpenAPI documentation at `/docs` out of the box, has first-class async support, and handles request validation through Pydantic automatically. Prior experience with it also made code review straightforward.

### 2.3 SQLite with SQLAlchemy and Alembic

SQLite was chosen over PostgreSQL and MySQL. PostgreSQL is built for high-concurrency production systems, which is more than this project needs. SQLite runs as a single file with no server process, and handles the workloads here (paper lookups, community stats, notes reads and writes) without issue. SQLAlchemy provides an async ORM on top of it, and Alembic manages schema migrations. Switching to PostgreSQL in future would require minimal changes to application code.

### 2.4 ChromaDB (NoSQL justification)

The brief flags that NoSQL databases require justification. ChromaDB is a vector database, a type of NoSQL store, and it is used here because there is no practical alternative for this task.

A relational database cannot perform efficient approximate nearest-neighbour search over 768-dimensional vectors. Cosine similarity across hundreds of thousands of high-dimensional embeddings is how semantic search works. SQL is the wrong tool for this, so a vector database is a requirement of the problem rather than a preference.

Two options were considered. FAISS (Facebook AI Similarity Search) was familiar from prior work and is highly performant, but it operates at a very low level. It has no built-in persistence, no ID-to-metadata mapping, and no management layer, all of which need to be implemented manually. FAISS makes sense when you need fine-grained control at extreme scale. For a local system indexing around 521k papers, that complexity is unnecessary. ChromaDB provides HNSW indexing with cosine similarity, persistent on-disk storage, and a simple Python API. It is free, installs via pip, and needs no external services. It was the right fit for this project.

### 2.5 BAAI/bge-base-en-v1.5 Embeddings

The BGE model family from the Beijing Academy of Artificial Intelligence is designed for retrieval tasks and ranks among the top open-source embedding models on the MTEB benchmark [Muennighoff et al., 2023]. The base variant produces 768-dimensional embeddings and runs efficiently on local hardware, achieving around 168 papers per second on Apple Silicon MPS during corpus ingestion.

BGE uses an asymmetric encoding convention: a retrieval prefix is applied to queries at search time, but not to documents at indexing time. This is the recommended usage from the model card and is implemented correctly in `app/services/embeddings.py`. Using the OpenAI embedding API was ruled out because it adds per-query cost, network latency, and an external dependency to every search request.

### 2.6 Google Gemini

Gemini was chosen over OpenAI and locally hosted open-source models. The free tier has generous enough rate limits for this project. More importantly, Gemini offers different model sizes that map well onto the two different tasks in the pipeline. `gemini-2.5-flash-lite` is used for the classifier and optimiser, where speed matters and the output is structured JSON. `gemini-2.5-pro` is used for summarisation, where output quality over academic text is the priority. Running open-source models locally was considered, but models small enough to fit on consumer hardware are not capable enough for reliable classification and summarisation. The Gemini API gives access to much larger models at no cost within the project's usage.

All Gemini calls have try/except blocks with graceful fallbacks. If the API is unavailable, the classifier returns the original query unchanged and the search still runs. The pipeline degrades safely rather than breaking.

### 2.7 REST over GraphQL

GraphQL's advantages (flexible field selection, nested query traversal) are most useful when data is deeply nested and client requirements vary significantly. DeepResearch's resources are shallow and well-defined. REST was the simpler and more appropriate choice, and pairs naturally with OpenAPI documentation.

### 2.8 arXiv Dataset

The corpus comes from the HuggingFace dataset `davanstrien/arxiv-cs-papers-classified` [van Strien, 2024], a structured subset of arXiv CS paper metadata. arXiv is where cutting-edge AI/ML research appears first, often before journal publication. The metadata available (title, authors, abstract, categories, year, DOI, URL) is enough to support search, summarisation, and community tracking without needing full paper text. The dataset is filtered to seven AI/ML categories (`cs.AI`, `cs.LG`, `cs.CL`, `cs.CV`, `cs.NE`, `cs.MA`, `stat.ML`), giving around 521,000 papers. The underlying arXiv metadata is released under CC0 (Public Domain) [arXiv, 2025], making it freely usable for academic purposes.

---

## 3. Architecture and Design

*See Figure 1 (architecture diagram) submitted alongside this report.*

### 3.1 Three-Stage Search Pipeline

The search pipeline is the core of DeepResearch. Instead of searching the corpus directly with a raw query, it passes the input through three stages.

**Stage 1: Classifier and Optimiser.** A single call to `gemini-2.5-flash-lite` both classifies the query into one of the seven arXiv AI/ML categories and rewrites it into precise academic language. For example, "how do transformers pay attention to words" becomes "self-attention mechanisms in transformer architectures for sequence modelling". The rewritten query matches the vocabulary in paper abstracts much more closely, improving retrieval quality. Doing both tasks in one LLM call keeps latency low and reduces API usage.

**Stage 2: BGE Embedding.** The optimised query is embedded with `bge-base-en-v1.5` using the BGE retrieval prefix, producing a 768-dimensional normalised vector.

**Stage 3: ChromaDB Similarity Search.** The query vector is compared against the indexed corpus using HNSW cosine similarity search. The top-N arxiv IDs and similarity scores are returned, and full paper metadata is fetched from SQLite to build the final response.

This pipeline was built rather than calling an external search API because of direct experience with the OpenAlex semantic search API. Its limitations were: coverage across all academic disciplines (not focused on AI/ML), external rate limits, and no ability to customise any part of it. A self-built pipeline gives full control over every component and room to improve each one independently.

### 3.2 Community Interaction Index

The idea came from social media. On platforms like Twitter or Reddit, it is easy to see what is trending from interaction signals. In academic research, this signal barely exists for pre-prints. Citation counts take years to accumulate. The community index creates a proxy for it: every time a paper is accessed via direct lookup, summarisation, or related-papers search, the event is logged with a timestamp. These events are aggregated into per-paper interaction counts.

The `GET /community` endpoint supports an optional `period` parameter (`week`, `month`, `year`) that filters the raw interaction log by a rolling time window. This lets users see what is trending right now, rather than just what has been popular since the corpus was ingested.

### 3.3 MCP Server

The API is also available as an MCP server for Claude Desktop. The reason is practical. Most research work now happens inside AI tools like Claude, where conversation context is already available. Using the raw HTTP API is awkward for this: to summarise a paper, you would need to manually copy its abstract and POST it. Through the MCP server, Claude handles this naturally. It retrieves the paper, passes the content to the summariser, and returns the result in conversation. The MCP server shares the same agents, services, and database as the HTTP API with no duplication.

### 3.4 Security

Security was built in from the start. API key authentication in `app/auth.py` uses `secrets.compare_digest()` for timing-safe comparison, which prevents timing attacks where response time could be used to guess the key. Rate limiting via `slowapi` protects two areas: the summarise endpoint (5 requests/minute) to avoid burning through Gemini credits, and the notes write endpoints (10 requests/minute) to prevent spam. CORS middleware restricts cross-origin access to localhost only. TrustedHostMiddleware rejects requests with forged Host headers.

---

## 4. Testing

### 4.1 Automated Tests

The test suite has 42 tests across 7 files using pytest and pytest-asyncio. All tests run against an in-memory SQLite database with Gemini and ChromaDB mocked out, so they are fast and require no API keys. Coverage includes happy paths, auth failures (401), validation errors (422), not-found responses (404), external service failures (500), graceful fallback behaviour, and community period filtering. Claude Code wrote the initial suite; the developer reviewed, extended, and ran it after every change. It has stayed at 100% passing throughout.

### 4.2 Manual Testing

Automated tests check that the code runs correctly, but they cannot check whether the output is actually good. Manual testing covered: whether the API endpoints felt intuitive to use, whether the classifier and summariser were producing genuinely useful outputs on real queries, and whether the MCP integration worked naturally inside Claude Desktop. Most architectural decisions came from this kind of testing. System prompt refinements, consolidating a duplicated summariser implementation, and moving away from the OpenAlex API dependency all came from noticing problems in real use, not from test failures.

---

## 5. Challenges and Lessons Learned

The hardest part of the project was not writing code, it was making architectural decisions. Choosing which model to use for which task, how the pipeline stages should connect, what to store in which database, which features to build. These decisions involve trade-offs that AI tools do not always surface. Rate limiting is a good example: the need to protect the summarise and notes endpoints was identified by thinking through what could go wrong with real users, not from any automated suggestion. The classifier and optimiser were also initially two separate LLM calls, and consolidating them into one required stepping back and looking at the system as a whole.

Maintaining code modularity also required active effort. Claude Code produced working code but not always well-structured code. The summariser was initially implemented in two places. Catching this, understanding why it was a problem, and directing a fix required the developer to understand the codebase deeply rather than just accept what was generated.

The main lesson from the project is that AI-assisted development moves the challenge from writing code to making good decisions. The code gets written quickly. The hard work is knowing what to build, how to structure it, and where the generated output needs to be corrected. A second lesson is that automated and manual testing do different things. Automated tests verify correctness. Manual tests verify quality. For a system with LLM components, skipping manual evaluation of actual outputs is not an option.

---

## 6. Limitations and Future Work

The notes system currently has no moderation. Any valid API key holder can write any content to any paper, including irrelevant or misleading notes. Related to this, note updates have no ownership concept, so any user can overwrite any note. The `community_interactions` table also grows indefinitely since every paper access is logged as a new row with no pruning. Finally, the corpus is static. Papers published after the ingest date are not searchable without re-running the ingest script.

The most useful future addition would be an AI moderation agent for notes. An LLM reviewer that checks a note for relevance and quality before it is saved, and applies the same check to updates, would make the collaborative layer genuinely trustworthy. This is the natural next step for the platform. Beyond that, incremental corpus updates on a schedule, interaction log archiving, and a cross-encoder re-ranking step on top of the BGE results would all meaningfully improve the system.

---

## 7. Generative AI Declaration

### 7.1 Tools Used

| Tool | Provider | Purpose |
|---|---|---|
| Claude Code | Anthropic | Architecture design, planning, implementation, testing, code review, requirements analysis |
| Google Gemini (gemini.google.com) | Google DeepMind | Technology research, comparing frameworks and tools, understanding trade-offs |

### 7.2 How AI Was Used

Claude Code was used at three levels throughout the project.

At the implementation level, it generated code for agents, services, routers, schemas, and tests. All output was reviewed, understood, and corrected where needed before being accepted. At the planning level, extended conversations shaped the system design before any code was written. The three-stage pipeline structure, the ChromaDB vs FAISS decision, the community interaction data model, and the MCP integration strategy were all worked through in conversation. A `CLAUDE.md` file was maintained in the project root to give Claude persistent context about the stack, conventions, and current state across sessions. At the analytical level, Claude Code was used to review the coursework requirements against the project, find gaps, and check that the work stayed within scope.

Google Gemini was used separately for researching technology choices before making them: comparing FAISS and ChromaDB, understanding the BGE model and its retrieval conventions, and comparing FastAPI against Flask and Django. This informed the decisions in Section 2.

### 7.3 Reflection

The most valuable use of AI in this project was not generating code. It was using Claude as a thinking partner during architectural decisions: working through alternatives, understanding trade-offs, and thinking about consequences before writing anything. The decision to combine the classifier and optimiser into a single LLM call came from a conversation about latency, not from implementation. The decision to build a self-contained pipeline rather than rely on OpenAlex came from discussing the long-term costs of external API dependency.

Claude Code was also used to analyse the coursework brief in detail, map requirements onto the project, and identify what was missing. This kind of critical review of work in progress was as useful as the coding assistance.

The conversation logs in Appendix A illustrate this. They show AI being used as a research and design tool, not just a code generator.

---

## References

arXiv (2025). *arXiv Bulk Data Access*. https://arxiv.org/help/bulk_data

Google DeepMind (2025). *Gemini API Documentation*. https://ai.google.dev

Muennighoff, N., Tazi, N., Magne, L. and Reimers, N. (2023). MTEB: Massive Text Embedding Benchmark. *EACL 2023*. https://arxiv.org/abs/2210.07316

Reimers, N. and Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *EMNLP 2019*. https://arxiv.org/abs/1908.10084

Slowapi (2024). *Rate Limiting for Starlette and FastAPI*. https://github.com/laurentS/slowapi

SQLAlchemy (2024). *SQLAlchemy Documentation*. https://docs.sqlalchemy.org

Tiangolo, S. (2019-2025). *FastAPI Documentation*. https://fastapi.tiangolo.com

Trychroma (2024). *ChromaDB: The Open-Source Embedding Database*. https://www.trychroma.com

van Strien, D. (2024). *arxiv-cs-papers-classified*. HuggingFace Datasets. https://huggingface.co/datasets/davanstrien/arxiv-cs-papers-classified

Xiao, S. et al. (2023). *C-Pack: Packaged Resources To Advance General Chinese Embedding*. arXiv. https://arxiv.org/abs/2309.07597

---

## Appendix A: Generative AI Conversation Logs

The following conversation logs are attached as supplementary material per the GenAI declaration requirements.

**Log 1:** `chat_claude_code.txt` — Claude Code session covering architecture design, planning, and implementation.

**Log 2:** `chat_gemini_Research.txt` — Gemini session covering technology research and comparison (ChromaDB vs FAISS, embedding model selection, stack trade-offs).
