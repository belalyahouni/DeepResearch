"""Combined classifier + prompt optimiser agent.

Uses Gemini to classify a user query into an arXiv AI/ML category and rewrite
it as an optimised academic query for semantic search.
"""

import json
import os

from google import genai

SYSTEM_PROMPT = """\
You are an academic search assistant specialising in AI and machine learning research.
Given a user's research query, you must:

1. **Classify** it into exactly one arXiv category from the list below.
2. **Optimise** the query for semantic search — rewrite it using precise academic
   terminology that would appear in paper titles and abstracts. Keep the query
   descriptive and natural (not a keyword list). Remove filler words, personal
   context, and off-topic qualifiers.

## arXiv AI/ML Categories (pick exactly one)

cs.AI  — Artificial Intelligence (knowledge representation, planning, search)
cs.LG  — Machine Learning (learning algorithms, deep learning, statistical ML)
cs.CL  — Computation and Language (NLP, text processing, language models)
cs.CV  — Computer Vision and Pattern Recognition (image/video understanding)
cs.NE  — Neural and Evolutionary Computing (neural networks, genetic algorithms)
cs.MA  — Multiagent Systems (multi-agent learning, game theory, coordination)
stat.ML — Statistics and Machine Learning (probabilistic methods, Bayesian ML)

## Response format

Return ONLY valid JSON, no markdown fences, no extra text:

{"category": "<arXiv category code>", "field": "<category label>", "optimised_query": "<rewritten query>"}
"""


async def classify_and_optimise(query: str) -> dict:
    """Classify the query into an arXiv AI/ML category and optimise it for semantic search.

    Returns a dict with keys: category, field, optimised_query.
    Falls back to the original query (no category) if Gemini fails.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"category": None, "field": None, "optimised_query": query}

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
        if not all(k in result for k in ("category", "field", "optimised_query")):
            raise ValueError("Missing keys in Gemini response")

        return result

    except Exception as exc:
        # Graceful fallback — search without classification
        return {
            "category": None,
            "field": None,
            "optimised_query": query,
            "error": str(exc),
        }
