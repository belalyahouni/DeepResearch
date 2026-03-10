"""Summariser agent — generates concise plain-text summaries of academic papers.

Uses Gemini to produce short, direct summaries. Output length depends on
whether the input is an abstract (1 sentence) or a full paper (2 sentences).
"""

import os

from google import genai

SYSTEM_PROMPT = """\
You summarise academic papers. Go straight into the summary — no introduction, \
no headings, no bullet points, no markdown, just plain sentences.

First, determine whether the input is a short abstract or a full paper:

- If it is an ABSTRACT (short text, typically under 500 words): write exactly \
1 sentence explaining in simple, high-level terms what the paper does and the \
problem it is trying to solve.

- If it is a FULL PAPER (long text, typically over 500 words): write exactly \
2 sentences covering what the paper does, what problem it is trying to solve, \
and the overall result.

Be super concise. No filler. No preamble. Start directly with the content.
"""


async def summarise_text(text: str) -> str | None:
    """Summarise academic text using Gemini.

    Returns a markdown summary string, or None if summarisation fails.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=text,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
            ),
        )
        return response.text.strip()

    except Exception:
        return None
