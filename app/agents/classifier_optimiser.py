"""Combined classifier + prompt optimiser agent.

Uses Gemini to classify a user query into an OpenAlex field and rewrite it
as an optimised academic query for semantic search.
"""

import json
import os

from google import genai

SYSTEM_PROMPT = """\
You are an academic search assistant. Given a user's research query, you must:

1. **Classify** it into exactly one OpenAlex field from the list below.
2. **Optimise** the query for semantic search — rewrite it using precise academic
   terminology that would appear in paper titles and abstracts. Keep the query
   descriptive and natural (not a keyword list). Remove filler words, personal
   context, and off-topic qualifiers.

## OpenAlex Fields (pick exactly one)

ID 11 — Agricultural and Biological Sciences
ID 12 — Arts and Humanities
ID 13 — Biochemistry, Genetics and Molecular Biology
ID 14 — Business, Management and Accounting
ID 15 — Chemical Engineering
ID 16 — Chemistry
ID 17 — Computer Science
ID 18 — Decision Sciences
ID 19 — Earth and Planetary Sciences
ID 20 — Economics, Econometrics and Finance
ID 21 — Energy
ID 22 — Engineering
ID 23 — Environmental Science
ID 24 — Immunology and Microbiology
ID 25 — Materials Science
ID 26 — Mathematics
ID 27 — Medicine
ID 28 — Neuroscience
ID 29 — Nursing
ID 30 — Pharmacology, Toxicology and Pharmaceutics
ID 31 — Physics and Astronomy
ID 32 — Psychology
ID 33 — Social Sciences
ID 34 — Veterinary
ID 35 — Dentistry
ID 36 — Health Professions

## Response format

Return ONLY valid JSON, no markdown fences, no extra text:

{"field_id": <int>, "field": "<field name>", "optimised_query": "<rewritten query>"}
"""


async def classify_and_optimise(query: str) -> dict:
    """Classify the query into an OpenAlex field and optimise it for semantic search.

    Returns a dict with keys: field_id, field, optimised_query.
    Falls back to the original query (no field filter) if Gemini fails.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"field_id": None, "field": None, "optimised_query": query}

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=query,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
            ),
        )

        raw = response.text.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        result = json.loads(raw)

        # Validate expected keys
        if not all(k in result for k in ("field_id", "field", "optimised_query")):
            raise ValueError("Missing keys in Gemini response")

        return result

    except Exception as exc:
        # Graceful fallback — search without classification
        return {
            "field_id": None,
            "field": None,
            "optimised_query": query,
            "error": str(exc),
        }
