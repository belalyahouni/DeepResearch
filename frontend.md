## DeepResearch Frontend — Implementation Brief

### Base URL
```
http://localhost:8000
```

### User Flow (5 screens)

**1. Search → 2. Results → 3. Library → 4. Paper Detail → 5. Chat**

---

### Screen 1: Search Page (landing page)

**Purpose:** Search for academic papers.

**UI:** Search bar with a submit button. Clean, centred layout.

**API Call:**
```
GET /search?query={user_input}
```
**Response:**
```json
{
  "original_query": "how do transformers work",
  "field_id": 17,
  "field": "Computer Science",
  "optimised_query": "Transformer architecture self-attention mechanism",
  "result_count": 10,
  "results": [
    {
      "openalex_id": "https://openalex.org/W2963403868",
      "doi": "https://doi.org/10.48550/arxiv.1706.03762",
      "title": "Attention Is All You Need",
      "authors": "Ashish Vaswani, Noam Shazeer",
      "abstract": "The dominant sequence transduction models...",
      "year": 2017,
      "url": "https://arxiv.org/abs/1706.03762",
      "open_access_pdf_url": "https://arxiv.org/pdf/1706.03762",
      "citation_count": 100000,
      "relevance_score": 0.95
    }
  ]
}
```
**Notes:** Show `field` and `optimised_query` as a small info badge above results (e.g. "Searched Computer Science for: Transformer architecture self-attention mechanism"). Results flow into Screen 2 on the same page or below.

---

### Screen 2: Search Results (part of search page)

**Purpose:** Browse results, preview summaries, save papers.

**UI per result card:**
- Title (clickable link to `url` if present)
- Authors, year, citation count
- Abstract (truncated, expandable)
- "Summarise" button — quick preview without saving
- "Save" button — saves to library

**Summarise button API call:**
```
POST /summarise
Body: { "text": "{abstract}" }
```
**Response:**
```json
{ "summary": "This paper proposes the Transformer, a model based entirely on attention mechanisms..." }
```
**Display:** Show summary inline below the result card. This is a 1-sentence preview.

**Save button API call:**
```
POST /papers
Body: {
  "openalex_id": "...",
  "title": "...",
  "authors": "...",
  "abstract": "...",
  "year": 2017,
  "url": "...",
  "open_access_pdf_url": "...",
  "citation_count": 100000
}
```
**Response:** `201` with full `PaperResponse`. **`409`** means already saved — show "Already in library" message.

**Notes:** The result fields from `/search` map directly to the `POST /papers` body. Just forward `openalex_id`, `title`, `authors`, `abstract`, `year`, `url`, `open_access_pdf_url`, `citation_count`. Omit `doi` and `relevance_score` (not in the Paper model).

---

### Screen 3: Library Page

**Purpose:** View all saved papers.

**API Call:**
```
GET /papers
```
**Optional filter:**
```
GET /papers?tags=machine+learning
```
**Response:** Array of `PaperResponse` objects (same shape as save response).

**UI:**
- List/grid of saved papers
- Each card: title, authors, year, citation count, tags, summary (1-2 sentences)
- Tag filter input at top
- Click a paper → goes to Paper Detail (Screen 4)
- Delete button per paper

**Delete API call:**
```
DELETE /papers/{id}
```
**Response:** `204` No Content. Remove card from UI.

---

### Screen 4: Paper Detail Page

**Purpose:** View a single paper in full, edit tags/notes, access chat.

**API Call:**
```
GET /papers/{id}
```
**Response:** Single `PaperResponse`:
```json
{
  "id": 1,
  "openalex_id": "...",
  "title": "Attention Is All You Need",
  "authors": "Ashish Vaswani, Noam Shazeer",
  "abstract": "The dominant sequence...",
  "year": 2017,
  "url": "https://arxiv.org/abs/1706.03762",
  "open_access_pdf_url": "https://arxiv.org/pdf/1706.03762",
  "citation_count": 100000,
  "tags": "transformers, attention",
  "notes": "Foundational paper on attention",
  "full_text": "... (long string or null) ...",
  "summary": "This paper proposes the Transformer...",
  "created_at": "2026-03-10T12:00:00",
  "updated_at": "2026-03-10T12:00:00"
}
```

**UI:**
- Paper metadata (title, authors, year, citations, link to original)
- Summary displayed prominently
- Editable tags field (comma-separated)
- Editable notes field (free text)
- Save button for tags/notes
- "Chat about this paper" button → opens Screen 5
- Related Papers section (see below)

**Related Papers section:**

Below the paper metadata, show a "Related Papers" section. Load on page open or via a "Find Related" button.

**API Call:**
```
GET /papers/{id}/related
```
**Response:**
```json
{
  "paper_id": 1,
  "paper_title": "mixSGA: a stochastic genetic algorithm...",
  "search_queries": ["stochastic genetic algorithm optimisation", "metaheuristic hybrid search"],
  "result_count": 10,
  "results": [
    {
      "openalex_id": "https://openalex.org/W...",
      "title": "A related paper title",
      "authors": "Author One, Author Two",
      "abstract": "...",
      "year": 2022,
      "citation_count": 50,
      "relevance_score": 0.85
    }
  ]
}
```
**UI:** List of related paper cards (similar to search results). Each card can have a "Save" button to add to the library.

**Update tags/notes API call:**
```
PUT /papers/{id}
Body: { "tags": "transformers, attention", "notes": "Key paper for my thesis" }
```
**Response:** Updated `PaperResponse`. Both fields optional — only send what changed.

---

### Screen 5: Chat Page (per paper)

**Purpose:** Multi-turn conversation about the paper.

**Load existing conversation:**
```
GET /papers/{id}/chat
```
**Response:**
```json
{
  "paper_id": 1,
  "messages": [
    { "role": "user", "message": "What is this paper about?", "created_at": "..." },
    { "role": "assistant", "message": "The paper proposes...", "created_at": "..." }
  ]
}
```

**UI:** Chat interface — message bubbles, input field at bottom, send button.

**Send message API call:**
```
POST /papers/{id}/chat
Body: { "message": "What methodology did they use?" }
```
**Response (201):**
```json
{ "role": "assistant", "message": "They used self-attention layers..." }
```

**Error states:**
- `409` — message limit reached (20 messages). Show "Conversation limit reached. Clear chat to continue."
- `500` — Gemini failed. Show "AI unavailable, try again later." User message was still saved.

**Clear chat button API call:**
```
DELETE /papers/{id}/chat
```
**Response:** `204`. Clear all messages from UI.

**Notes:** Show paper title at top of chat for context. Display message limit indicator (e.g. "4/20 messages").

---

### HTTP Status Codes to Handle

| Code | Meaning | UI Action |
|---|---|---|
| `200` | Success | Display data |
| `201` | Created | Success toast/message |
| `204` | Deleted/cleared | Remove from UI |
| `404` | Not found | "Paper not found" message |
| `409` | Duplicate save or chat limit | "Already saved" or "Limit reached" |
| `422` | Validation error | Show field-level errors |
| `500` | Server/Gemini error | "Something went wrong" message |

### Tech Recommendation

Simple static frontend served alongside FastAPI. Options:
- **Vanilla HTML/CSS/JS** in a `static/` folder — simplest, no build step
- **React/Vue SPA** — nicer but requires build tooling

FastAPI can serve static files with `app.mount("/static", StaticFiles(directory="static"))` and serve `index.html` at the root.

### File Structure
```
static/
├── index.html          # SPA entry point
├── styles.css          # Styling
└── app.js              # All frontend logic + API calls
```
